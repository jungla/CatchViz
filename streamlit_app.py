import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import streamlit as st
import plotly.express as px
from datetime import date, datetime, timedelta

# --- Page Configuration ---
st.set_page_config(
    page_title="Artisanal Landings Data Visualization",
    page_icon="🎣",
    layout="wide" # Use wide layout for more space for charts
)


landing_sites = ['moa','ndumbani','mkokotoni','fumba','kizimkazi','msuka','wesha','mkoani']
landing_sites = ['msuka','kojani','mvumoni_furaha','mtangani','sahare','tongoni','kigombe']

# --- Function to Load Data from Excel File ---
@st.cache_data(ttl=6000) # Cache the data for 10 minutes to avoid re-reading on every rerun
def load_data_from_excel_file(file_path="CATCH_kobo_data.xlsx"): # Explicitly load 'catch_catch' sheet

 catch = pd.read_excel(file_path, engine = 'openpyxl', sheet_name=1)

 
 trips = pd.read_excel(file_path, engine = 'openpyxl', sheet_name=0)
 catch = trips.merge(catch, left_on = '_uuid', right_on='_submission__uuid')

 catch = catch[catch['survey_real'] == 'real']
 catch = catch[catch['survey_type'] == 'catch']
 
 catch.loc[catch['Fishing_Trip/gear_type_other'] == 'Handline', 'Fishing_Trip/gear_type/pole_line'] = 1
 catch.loc[catch['Fishing_Trip/gear_type_other'] == 'Handline', 'Fishing_Trip/gear_type'] = 'hand_line'
 catch.loc[catch['Fishing_Trip/gear_type'] == 'pole_line', 'Fishing_Trip/gear_type'] = 'hand_line'
 catch = catch.rename(columns={'Fishing_Trip/gear_type/pole_line': 'Fishing_Trip/gear_type/hand_line'})
 
 
 catch = catch[catch['landing_site'].isin(landing_sites)]
 
 catch['Fishing_Trip/fishing_duration'] = catch['Fishing_Trip/fishing_duration'].replace({'>3': 4})
 
 catch.loc[catch['Fishing_Trip/fishing_duration'] == '>3', 'Fishing_Trip/fishing_duration'] = 4
 catch.loc[catch['Fishing_Trip/fishing_duration'] != catch['Fishing_Trip/fishing_duration'], 'Fishing_Trip/fishing_duration'] = 1
 
 catch['people'] = catch['people'].astype('float') 
 catch['boats_landed'] = catch['boats_landed'] + 1 # to include also the boat that was sampled
 catch['gear_type'] = catch['Fishing_Trip/gear_type']
 catch['boat_type'] = catch['Fishing_Trip/boat_type']
 catch['weight_catch'] = catch['Total_Catch_Survey/catch_catch/weight_catch']
 catch['group_catch'] = catch['Total_Catch_Survey/catch_catch/group_catch'] 
 # fishing effort per day [fishers/day]

 return catch

# --- Load Data ---
# Call the function to load data from the Excel file's 'catch_catch' sheet
df = load_data_from_excel_file(file_path="CATCH_kobo_data.xlsx")

# --- Sidebar Filters ---
st.sidebar.header("Filters ⚙️")

# Check if DataFrame is empty before attempting to filter
if df.empty:
    st.warning("No data loaded. Please check your Excel file, sheet name, and column headers.")
    # Display an empty DataFrame or a message
    st.header("Filtered Data Records")
    st.dataframe(pd.DataFrame(), use_container_width=True) # Display an empty DataFrame
    st.stop() # Stop further execution if no data

# date filter

df['today'] = df['today'].dt.date

min_date = df['today'].min()
max_date = df['today'].max()

date_range = st.sidebar.date_input(
    "Select today Range:",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
    key='date_filter'
)

start_date = min_date
end_date = max_date
if len(date_range) == 2:
    start_date, end_date = date_range

# site filter

all_sites = sorted(df['landing_site'].unique())
selected_sites = st.sidebar.multiselect(
    "Select Site(s):",
    options=all_sites,
    default=all_sites,
    key='site_filter'
)

# type catch filter

all_groups = sorted(df['group_catch'].dropna().unique())
selected_groups = st.sidebar.multiselect(
    "Select Group(s):",
    options=all_groups,
    default=['reef_fish','tuna_like','small_pelagic'],
    key='group_filter'
)

# --- Apply Filters ---
filtered_df = df[
    (df['today'] >= date(2022,1,1)) &
    (df['today'] <= end_date) &
    (df['landing_site'].isin(selected_sites)) &
    (df['group_catch'].isin(selected_groups))
]

# --- Main Page Content ---

col1, mid, col2 = st.columns([20,1,5])

with col1:
 st.markdown("""
     <style>
     .custom-font {
         font-family: 'Futura', serif;
         font-size: 60px !important;
         font-weight: bold;
     }
     </style>
     <p class="custom-font">Artisanal Fishing Landings</p>
     """, unsafe_allow_html=True)
#    st.write('Artisanal Landings Data Visualization')

with col2:
 if st.context.theme.type == 'dark':
  st.image('./img/WCS-logo_white.png', width=300)
 else:
  st.image('./img/WCS-logo.png', width=300)

#st.title("🎣 Fishery Catch Data Visualization")
st.markdown(f"Visualizing data from **{start_date.strftime('%Y-%m-%d')}** to **{end_date.strftime('%Y-%m-%d')}** for sites: **{', '.join(selected_sites) if selected_sites else 'None'}**.")
st.markdown("---") # Separator


# --- Display Metrics/KPIs ---

# I would add a time series of sampling days for the landing sites

if not filtered_df.empty:
    total_catch = filtered_df['weight_catch'].sum()
    num_records_filtered = len(filtered_df)
    avg_catch_per_record = filtered_df['weight_catch'].mean()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Total Catch (kg)", value=f"{total_catch:,.2f}")
    with col2:
        st.metric(label="Number of Records", value=f"{num_records_filtered:,}")
    with col3:
        st.metric(label="Average Catch per Record (kg)", value=f"{avg_catch_per_record:,.2f}")
    st.markdown("---")
else:
    st.warning("No data available for the selected filters.")



# --- Visualizations ---

if not filtered_df.empty:
 st.header("Landing Records")

 # 1. Catch Weight Over Time (Line Chart)
 st.subheader('Sampling Effort')
 effort_time = filtered_df.groupby(['today','landing_site'])['_uuid'].count().reset_index()
 fig_effort = alt.Chart(effort_time).mark_bar().encode(
  x=alt.X('today', title='Date'),
  y=alt.Y('_uuid', title='Number of Records', stack='zero'),
  color='landing_site'
  )
 
 st.altair_chart(fig_effort, use_container_width=True)


 #st.plotly_chart(fig_time, use_container_width=True)

 # Split into two columns for side-by-side charts
 col_viz1, col_viz2 = st.columns(2)

 with col_viz1:

  # landings by boat
  st.subheader("Landings by type of boat")
  boat_type = filtered_df.groupby('boat_type').count().sort_values(by='_uuid').reset_index()

  fig_boat = alt.Chart(boat_type).mark_bar().encode(
   x=alt.X('boat_type', title='Type of Fishing Vessel', sort=None),
   y=alt.Y('_uuid', title='Number of Records')
   )
  st.altair_chart(fig_boat, use_container_width=True)

  # landings by gear

  # 2. Catch by Site (Bar Chart)
  st.subheader("Landings by Group")
  site_catch_df = filtered_df.groupby('group_catch')['_uuid'].count().reset_index().sort_values(by='_uuid', ascending=False)

  fig_group = alt.Chart(site_catch_df).mark_arc().encode(
    theta='_uuid',
    color='group_catch'
  )

  st.altair_chart(fig_group, use_container_width=True)

 with col_viz2:

  # 4. Catch by Gear Type (Pie Chart)

  st.subheader("Landings by Gear Type")
  #gear_type = filtered_df.groupby('gear_type')['_uuid'].count().reset_index().sort_values(by='_uuid')[-10:]

  s = pd.Series(filtered_df['gear_type'].dropna()).astype(str)
  exploded_words = s.str.split(expand=False).explode() # expand=False keeps lists in each row
  gear_type = pd.DataFrame(exploded_words.value_counts()).reset_index()
  fig_gear = alt.Chart(gear_type).mark_bar().encode(
   x=alt.X('gear_type', title='Type of Gear', sort=None),
   y=alt.Y('count', title='Number of Records')
   )

  st.altair_chart(fig_gear, use_container_width=True)

    # --- Display Filtered Data Table ---

#    st.markdown("---")
#    st.header("Filtered Data Records")
#    st.dataframe(filtered_df, use_container_width=True) # Display the filtered dataframe


 st.header("Catch and Yield Analysis")

 col_viz1, col_viz2 = st.columns(2)

 #with col_viz1:

else:
    # This block is executed if filtered_df is empty (e.g., no data, or filters result in empty set)
    st.markdown("---")
    st.warning("No data available for the selected filters. Showing a preview of all loaded data.")
    st.header("Original Data Preview (Top 10 rows)")
    st.dataframe(df.head(10), use_container_width=True) # Show head of the full dataset if filters yielded no results


st.sidebar.markdown("---")
st.sidebar.info("Data collected with Kobotoolbox at landing sites in Tanzani and updated every 10 days. Raw data can be found at https://zenodo.org/records/15229813")


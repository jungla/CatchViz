import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import streamlit as st
import plotly.express as px
from datetime import date, datetime, timedelta

@st.cache_data
def read_data(filename):
 #df = pd.read_parquet(filename)
 df = pd.read_csv(filename, low_memory=False) # parquet loses some data
 return df

#df = read_data('CATCH_kobo_data.parquet')
df = read_data('CATCH_kobo_data.csv') # parquet loses some data


#landing_sites = ['moa','ndumbani','mkokotoni','fumba','kizimkazi','msuka','wesha','mkoani']
landing_sites = ['msuka','kojani','mvumoni_furaha','mtangani','sahare','tongoni','kigombe']
df = df[df['landing_site'].isin(landing_sites)]

# --- Sidebar Filters ---


#st.sidebar.header("Type of fishery")
#st.sidebar.success("Select a demo above.")


st.sidebar.header("Filters ⚙️")

# Check if DataFrame is empty before attempting to filter
if df.empty:
    st.warning("No data loaded. Please check your Excel file, sheet name, and column headers.")
    # Display an empty DataFrame or a message
    st.header("Filtered Data Records")
    st.dataframe(pd.DataFrame(), width='stretch') # Display an empty DataFrame
    st.stop() # Stop further execution if no data

# date filter

df['today'] = pd.to_datetime(df['today'],format='mixed')

df['today'] = df['today'].dt.date

min_date = date(2022,1,1)
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
    (df['today'] >= start_date) &
    (df['today'] <= end_date) &
    (df['landing_site'].isin(selected_sites)) &
    (df['group_catch'].isin(selected_groups))
]

# --- Main Page Content ---

col1, mid, col2 = st.columns([20,1,5])

with col1:
 st.markdown("""
     <style>
     .h1-custom {
         font-family: 'Futura', serif;
         font-size: 30px !important;
         font-weight: bold;
     }
     </style>

     <style>
     .h2-custom {
         font-family: 'Futura', serif;
         font-size: 50px !important;
         font-color: silver;
         font-weight: bold;
     }
     </style>

     <h1 class="h1-custom">Kobotoolbox Data Visualization Platform</h1>
     <h2 class="h2-custom">Landings of Bony Fishes</h2>
     """, unsafe_allow_html=True)

with col2:
# if st.context.theme == 'dark':
 #st.image('./img/WCS-logo_white.png', width=300)
# else:
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

 coords = pd.merge(filtered_df[['landing_site','_gps_latitude']].groupby('landing_site').median(), filtered_df[['landing_site','_gps_longitude']].groupby('landing_site').median(), right_index=True, left_index=True)
 coords = pd.merge(coords, filtered_df[['landing_site','_gps_latitude']].groupby('landing_site').count(), right_index=True, left_index=True)
 coords = coords.rename(columns = {'_gps_latitude_x' : 'lat', '_gps_longitude' : 'lon', '_gps_latitude_y' : 'count'})
 
 st.map(coords.dropna(), size='count')

 # 1. Catch Weight Over Time (Line Chart)
 con0 = st.container(border=True)

 con0.subheader('Sampling Effort')
 effort_time = filtered_df.groupby(['today','landing_site'])['_uuid'].count().reset_index()
 fig_effort = alt.Chart(effort_time).mark_bar().encode(
  x=alt.X('today', title='Date'),
  y=alt.Y('_uuid', title='Number of Records', stack='zero'),
  color='landing_site'
  )
 
 con0.altair_chart(fig_effort, width='stretch')




 # Split into two columns for side-by-side charts
 col_viz1, col_viz2 = st.columns(2)

 with col_viz1:

  con1 = col_viz1.container(border=True)

  # Landings by Boat Type
  con1.subheader("Landings by type of boat")
  boat_type = filtered_df.groupby('boat_type').count().sort_values(by='_uuid').reset_index()

  fig_boat = alt.Chart(boat_type).mark_bar().encode(
   x=alt.X('boat_type', title='Type of Fishing Vessel', sort=None),
   y=alt.Y('_uuid', title='Number of Records')
   )
  con1.altair_chart(fig_boat, width='stretch')


  con2 = col_viz1.container(border=True)
  # Landings by Species Group

  con2.subheader("Landings by Species Group")
  site_catch_df = filtered_df.groupby(['group_catch','landing_site'])['_uuid'].count().reset_index().sort_values(by='_uuid', ascending=False)


  fig_group = alt.Chart(site_catch_df).mark_bar().encode(
    x = alt.X('landing_site', title='Landing Site'),
    y = alt.Y('_uuid', title='Number of landings'),
    color='group_catch'
  )

  con2.altair_chart(fig_group, width='stretch')



 with col_viz2:

  # Landings by Gear Type

  con3 = col_viz2.container(border=True)

  con3.subheader("Landings by Gear Type")

  s = pd.Series(filtered_df['gear_type'].dropna()).astype(str)
  exploded_words = s.str.split(expand=False).explode() # expand=False keeps lists in each row
  gear_type = pd.DataFrame(exploded_words.value_counts()).reset_index()

  fig_gear = alt.Chart(gear_type).mark_bar().encode(
   x=alt.X('gear_type', title='Type of Gear', sort=None),
   y=alt.Y('count', title='Number of Records')
   )

  con3.altair_chart(fig_gear, width='stretch')

  # Effort by Vessel

  con4 = col_viz2.container(border=True)

  con4.subheader("Effort by Type of Vessel")
 
  mean_ppl_day = filtered_df.groupby(['today','landing_site','boat_type'])['people'].mean()
  effort = filtered_df.groupby(['today','landing_site','boat_type'])['people'].sum() + mean_ppl_day * filtered_df.groupby(['today','landing_site','boat_type'])['boats_landed'].median()
  #effort_df = pd.DataFrame(effort.reset_index(), columns=['today','landing_site','boat_type','effort']) 
  effort_df = pd.DataFrame(effort.reset_index())
  effort_df['effort'] = pd.DataFrame(effort).values
  effort_df.drop(0,axis=1)

  effort_df = effort_df[['landing_site','boat_type','effort']].groupby(['landing_site','boat_type']).sum().reset_index()
 
#  site_catch_df = filtered_df.groupby(['group_catch','landing_site'])['_uuid'].count().reset_index().sort_values(by='_uuid', ascending=False)

  fig_group = alt.Chart(effort_df).mark_bar().encode(
   x = alt.X('landing_site', title='Landing Site'),
   y = alt.Y('effort', title='Number of landings'),
   color='boat_type'
  )

  con4.altair_chart(fig_group, width='stretch')


 st.header("Catch and Yield Analysis")

   # Landings by Gear Type

 st.subheader("Catch Per Unit Effort")

 filtered_df.loc[:,'CPUE'] = filtered_df['weight_catch']/filtered_df['people']/filtered_df['fishing_duration']
 
 CPUE = pd.DataFrame(filtered_df)
 CPUE.replace([np.inf, -np.inf], np.nan, inplace=True)
 #CPUE.index = pd.to_datetime(CPUE['today'])

 #CPUE_M = pd.DataFrame(CPUE.groupby('landing_site').resample('M')['CPUE'].mean())
 CPUE = CPUE.groupby(['today','landing_site'])['CPUE'].mean().reset_index()
 CPUE = CPUE.dropna()

# filtered_df.dropna(inplace=True)

 #print(np.nanmax(filtered_df['CPUE']))
 #print(filtered_df)
 #print(np.max(CPUE['CPUE']))

 fig_CPUE_scatter = alt.Chart(CPUE).mark_circle().encode(
  x=alt.X('today', title='Date'),
  y=alt.Y('CPUE', title='CPUE [kg/fisher/day]'),
  color='landing_site'
 )

 # Create trendline layer using linear regression
 fig_CPUE_scatter = fig_CPUE_scatter + fig_CPUE_scatter.transform_regression('today', 'CPUE', method='linear', groupby=['landing_site']).mark_line(size=4)  #transform_loess #alt.Chart(CPUE).mark_line(color='red').transform_regression('today', 'CPUE', method='linear')

 # Combine layers
 fig_chart_CPUE = fig_CPUE_scatter #+ fig_CPUE_trendline

 st.altair_chart(fig_chart_CPUE, width='stretch')

 #col_viz1, col_viz2 = st.columns(2)
 #with col_viz1:

else:
    # This block is executed if filtered_df is empty (e.g., no data, or filters result in empty set)
    st.markdown("---")
    st.warning("No data available for the selected filters. Showing a preview of all loaded data.")
    st.header("Original Data Preview (Top 10 rows)")
    st.dataframe(df.head(10), width='stretch') # Show head of the full dataset if filters yielded no results


st.sidebar.markdown("---")
st.sidebar.info("Data collected with Kobotoolbox at landing sites in Tanzani and updated every 10 days. Raw data can be found at https://zenodo.org/records/15229813")


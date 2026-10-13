import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import streamlit as st
import plotly.express as px
from datetime import date, datetime, timedelta
import pydeck as pdk

@st.cache_data
def read_data(filename):
 #df = pd.read_parquet(filename)
 df = pd.read_csv(filename, low_memory=False) # parquet loses some data
 return df

df = pd.read_csv('RESTORATION_kobo_data.csv', low_memory=False) # parquet loses some data

#df['today'] = pd.to_datetime(df['Date'],format='mixed')

df['date'] = pd.to_datetime(df['Date'],format='mixed').dt.date
df['datetime'] = pd.to_datetime(df['Date'],format='mixed')

df = df[df['test'] != 'yes']

coords = [
['nursery_kirui',-4.77763, 39.19956],
['transplanting_kirui_shangani',-4.75601,39.21939],
['transplanting_kirui_corner',-4.77067,39.21169],
['transplanting_kirui_exp',-4.75253,39.23363],
['nursery_kigombe',-5.26431,39.07310],
['transplanting_kigombe_taa',-5.27990,39.07984],
['transplanting_kigome_makome',-5.29569,39.09755],
['nursery_msuka',-4.90274,39.72391],
['transplanting_msuka_panga_punge',-4.8703,39.8054]
]

coords = pd.DataFrame(coords, columns=['site_name', 'latitude', 'longitude'])

df = pd.merge(df, coords)

# --- Sidebar Filters ---

st.sidebar.header("Filters ⚙️")

# Check if DataFrame is empty before attempting to filter
if df.empty:
    st.warning("No data loaded. Please check your Excel file, sheet name, and column headers.")
    # Display an empty DataFrame or a message
    st.header("Filtered Data Records")
    st.dataframe(pd.DataFrame(), width='stretch') # Display an empty DataFrame
    st.stop() # Stop further execution if no data

min_date = df['date'].min() #date(2019,1,1)
max_date = df['date'].max()

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

all_sites = sorted(df['site_name'].dropna().unique())
selected_site_name= st.sidebar.multiselect(
    "Select Site(s):",
    options=all_sites,
    default=all_sites,
    key='site_filter'
)

# --- Apply Filters ---

filtered_df = df[(df['date'] >= start_date) & (df['date'] <= end_date) & (df['site_name'].isin(selected_site_name))]


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

     <h1 class="h1-custom">Data Visualization Platform</h1>
     <h2 class="h2-custom">Coral Restoration Projects</h2>
     """, unsafe_allow_html=True)

#print(st.get_option("theme.style"))

#with col2:
# if st.context.theme == 'dark':
 #st.image('./img/WCS-logo_white.png', width=300)
# else:
# st.image('./img/WCS-logo.png', width=300)

st.markdown(f"Visualizing data from **{start_date.strftime('%Y-%m-%d')}** to **{end_date.strftime('%Y-%m-%d')}** for sites: **{', '.join(selected_site_name) if selected_site_name else 'None'}**.")
st.markdown("---") # Separator

# Time series of activities per site

if not filtered_df.empty:
    total_transplanted_corals = np.sum(filtered_df.groupby('site_name').max()['total_fragments_transplanted_to_date']) # I am counting transplanted fragments from the reported totals since not all the past filtered_df was entered in Kobo.
    total_transplanted_corals_areas = total_transplanted_corals * 0.25 # estimating one coral every 50cm x 50cm plot 

    total_reefstars = np.sum(filtered_df.groupby('site_name').max()['total_reef_starts_deployed_to_date']) # I am counting reefstars from the reported totals since not all the past filtered_df was entered in Kobo.
    total_reefstars_area = total_reefstars * 2 # 1.5m x 1.5m per reefstar? 

    total_fencewires =  np.sum(filtered_df.groupby('site_name').max()['total_fence_wires_deployed_to_date'])
    total_fencewires_area = total_fencewires * 30 # 10m x 3m per fence wire?

    total_nursery_tables = np.nansum(filtered_df.groupby('site_name')['total_tables_in_nursery_to_date'].max())

    total_coralclips = np.sum(filtered_df.groupby('site_name').max()['total_fragments_on_clips_to_date'])
    total_coralclips_area = total_coralclips * 0.25 # estimating one coral every 50cm x 50cm plot 

    total_area_restored = (total_transplanted_corals / 2)/1e4
#    total_area_restored = (total_reefstars_area + total_fencewires_area + total_coralclips_area)/1e4

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label="Coral Fragments Transplanted", value=int(total_transplanted_corals))
    with col2:
        st.metric(label="Number of Reef Stars Installed", value=int(total_reefstars))
    with col3:
        st.metric(label="Number of Tables in Nurseries", value=int(total_nursery_tables))
    with col4:
        st.metric(label="Total Area Restored (ha)", value=f"{total_area_restored:,.2f}")
    st.markdown("---")
else:
    st.warning("No data available for the selected filters.")

# --- Visualizations ---

if not filtered_df.empty:

 st.header("Coral Restoration Records")

 # map shows the size of plot based on number of fragments in nursery or transplated

# coords = pd.merge(coords, filtered_df.groupby(['site_name'])['total_fragments_in_nursery_to_date'].max().reset_index())
# coords = pd.merge(coords, filtered_df.groupby(['site_name'])['total_fragments_transplanted_to_date'].max().reset_index())
# coords = pd.merge(filtered_df[['site_name','site_type']], coords).drop_duplicates()
 
 # 2. Define the Dot Layers


# 2. Define Layer Data with reset_index()
 nursery_data = (
     filtered_df[filtered_df['site_type'] == 'nursery']
     .groupby('site_name')
     .max()
     .reset_index()
 )
 nursery_data['fragment_count'] = nursery_data['total_fragments_in_nursery_to_date']

 transplanting_data = (
     filtered_df[filtered_df['site_type'] == 'transplanting']
     .groupby('site_name')
     .max()
     .reset_index()
 )

 transplanting_data['fragment_count'] = transplanting_data['total_fragments_transplanted_to_date']

 from pydeck.types import String
 

 # 3. Define the Dot Layers
 dots_layer_nursery = pdk.Layer(
     'ScatterplotLayer',
     data=nursery_data,
     get_position='[longitude, latitude]',
     get_radius="total_fragments_in_nursery_to_date / 1e3",
     radius_units=String('pixels'),
#     radius_min_pixels=3,
#     radius_max_pixels=600,
     pickable=True,
     get_fill_color='[100, 100, 0, 160]',
 )
 

 dots_layer_transplanting = pdk.Layer(
     'ScatterplotLayer',
     data=transplanting_data,
     get_position='[longitude, latitude]',
     get_radius="total_fragments_transplanted_to_date/1e3",
     radius_units=String('pixels'), # do not touch
     #point_radius_units='pixels',
     #radius_min_pixels=3,
     #radius_max_pixels=600,
     get_fill_color='[200, 30, 60, 120]',
     pickable=True,
 )

 # 4. Render the Map
 st.pydeck_chart(pdk.Deck(
     map_style='light',
     layers=[dots_layer_nursery, dots_layer_transplanting],
     initial_view_state=pdk.ViewState(
         latitude=np.mean(filtered_df.latitude),
         longitude=np.mean(filtered_df.longitude),
         zoom=7,
         pitch=0,
     ),
     tooltip={"html": """<h4>{project_site}, {site_type}</h4>
            <p>
            Fragments, </br>
            in Nursery: <b>{total_fragments_in_nursery_to_date}</b><br/>
            Transplanted: <b>{total_fragments_transplanted_to_date}</b>
            </p>
            """,
             "style": {
             "position": "relative",
             "marginTop": "20%",
             "width":"20%"
             }
    }
 ))



 con0 = st.container(border=True)

 # Landings by Boat Type
 con0.subheader("Activity by Site")
 activity_site = filtered_df[['_uuid','project_site','datetime']].drop_duplicates().groupby('project_site').resample('W', on='datetime').count().reset_index()

#  boat_type = filtered_df.groupby('boat_type').count().sort_values(by='_uuid').reset_index()

 fig_activity = alt.Chart(activity_site).mark_bar(size=20).encode(
  x=alt.X('datetime', title='Time', sort=None),
  y=alt.Y('_uuid', title='Number of Records'),
  color='project_site'
  )
 con0.altair_chart(fig_activity, width='stretch')


#  con2 = col_viz1.container(border=True)
#  # Landings by Species Group
#
#  con2.subheader("Landings by Species Group")
#  site_catch_df = filtered_df.groupby(['group_catch','landing_site'])['_uuid'].count().reset_index().sort_values(by='_uuid', ascending=False)
#
#
#  fig_group = alt.Chart(site_catch_df).mark_bar().encode(
#    x = alt.X('landing_site', title='Landing Site'),
#    y = alt.Y('_uuid', title='Number of landings'),
#    color='group_catch'
#  )
#
#  con2.altair_chart(fig_group, width='stretch')



# with col_viz2:
#
#  # Landings by Gear Type
#
#  con3 = col_viz2.container(border=True)
#
#  con3.subheader("Landings by Gear Type")





# html_string = deck.to_html(as_string=True)
# components.html(html_string, height=600)  # 👈 Replaces st.pydeck_chart

# labels_layer = pdk.Layer(
#     "TextLayer",
#     data = concat_df, 
#     get_position='[longitude, latitude]',
#     get_text='site_name',
#     get_size=10,
#     size_units="'pixels'",
#     get_color=[0, 0, 0, 255],
#     get_alignment_baseline="'bottom'",
#     get_text_anchor="'middle'",
# )
 
# import sys
# sys.exit()


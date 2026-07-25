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

df['today'] = pd.to_datetime(df['Date'],format='mixed')

df['date'] = pd.to_datetime(df['today'],format='mixed').dt.date
df['month'] = df['today'].dt.month
df['year'] = df['today'].dt.year
df = df.set_index('today')

# merge coordinates of the sites

coords = [
['nursery_kirui',-4.77763, 39.19956],
['transplanting_kirui_shangani',-4.75601,39.21939],
['transplanting_kirui_corner',-4.77067,39.21169],
['transplanting_kirui_exp',-4.75253,39.23363],
['nursery_kigombe',-5.26431,39.07310],
['transplanting_kigombe_taa',-5.27990,39.07984],
['transplanting_kigome_makome',-5.29569,39.09755],
['nursery_msuka',-4.90274,39.72391],
['transplanting_msuka_panga_pung',-4.8703,39.8054]
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
    total_transplanted_corals = sum(filtered_df.groupby('site_name')['total_fragments_transplanted_to_date'].max())
    total_nursery_corals = sum(filtered_df.groupby('site_name')['total_fragments_in_nursery_to_date'].max())
    total_reefstar_area = sum(filtered_df.groupby('site_name')['total_reef_starts_deployed_to_date'].max()) * 1 # 1x1 m per reef star?
    total_fencewire_area = sum(filtered_df.groupby('site_name')['total_fence_wires_deployed_to_date'].max()) * 30 # 5x2 m per fence wire?
    total_coralclips_area = sum(filtered_df.groupby('site_name')['total_fragments_on_clips_to_date'].max()) * 0.25 # 1 fragment on half a 50x50 cm tile?
    total_area_restored = (total_reefstar_area + total_fencewire_area + total_coralclips_area)/1e4

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Number of Corals Transplanted to Date", value=total_transplanted_corals)
    with col2:
        st.metric(label="Number Corals in Nursery to Date", value=total_nursery_corals)
    with col3:
        st.metric(label="Total Area Restored (ha)", value=f"{total_area_restored:,.2f}")
    st.markdown("---")
else:
    st.warning("No data available for the selected filters.")

# --- Visualizations ---

if not filtered_df.empty:

 st.header("Coral Restoration Records")

 # map shows the size of plot based on number of fragments in nursery or transplated

 coords = pd.merge(coords, filtered_df.groupby(['site_name'])['total_fragments_in_nursery_to_date'].max().reset_index())
 coords = pd.merge(coords, filtered_df.groupby(['site_name'])['total_fragments_transplanted_to_date'].max().reset_index())
 coords = pd.merge(filtered_df[['site_name','site_type']], coords).drop_duplicates()
 
 # 2. Define the Dot Layers
 
 dots_layer_nursery = pdk.Layer(
     'ScatterplotLayer',
     data = coords[coords['site_type'] == 'nursery'].dropna(),
     get_position = '[longitude, latitude]',
     get_radius = 'total_fragments_in_nursery_to_date',
     radius_scale=2,      # Multiplies the base radius by 2 (effectively 100 meters)
     radius_min_pixels=2, # Prevents points from disappearing when zoomed far out
     radius_max_pixels=60,#     #radius_units="pixels",
     get_fill_color = '[200, 30, 100, 160]',
 )

 dots_layer_transplanting = pdk.Layer(
     'ScatterplotLayer',
     data = coords[coords['site_type'] == 'transplanting'].dropna(),
     get_position = '[longitude, latitude]',
     get_radius = 'total_fragments_transplanted_to_date',
     radius_scale=2,      # Multiplies the base radius by 2 (effectively 100 meters)
     radius_min_pixels=2, # Prevents points from disappearing when zoomed far out
     radius_max_pixels=60,#     #radius_units="pixels",
     get_color = '[200, 30, 60, 120]',
 )
 
 
 # 3. Define the Label Layer
 labels_layer = pdk.Layer(
     "TextLayer",
     data = coords.dropna(),
     get_position='[longitude, latitude]',
     get_text='site_name',
     get_size=10,
     size_units="'pixels'",
     get_color=[0, 0, 0, 255],
     get_alignment_baseline="'bottom'",
     get_text_anchor="'middle'",
 )
 
 # 4. Render the Map
 st.pydeck_chart(pdk.Deck(
     map_style='light',
     layers=[dots_layer_nursery, dots_layer_transplanting, labels_layer],
     #layers=[dots_layer_nursery],
     initial_view_state=pdk.ViewState(
         latitude=np.mean(coords.latitude),
         longitude=np.mean(coords.longitude),
         zoom=7,
         pitch=0,
     ),
 ))


 import sys
 sys.exit()

 # 1. Catch Weight Over Time (Line Chart)
 con0 = st.container(border=True)

 con0.subheader('Sampling Effort')
 effort_time = filtered_df.groupby('landing_site')['_uuid'].resample('ME').count().reset_index() 
 fig_effort = alt.Chart(effort_time).mark_bar().encode(
  x=alt.X('yearmonth(today):O', title='Date'),
  y=alt.Y('_uuid', title='Number of Records', stack='zero'),
  color='landing_site'
  )
 
 con0.altair_chart(fig_effort, width='stretch')


 st.header('Life History Traits and IUCN Categories')
 df_IUCN


 # Split into two columns for side-by-side charts
 col_viz1, col_viz2 = st.columns(2)

 with col_viz1:

  con1 = col_viz1.container(border=True)

  # Landings by Species 

  con1.subheader("Top Landings by Species")

  landings_species = filtered_df.groupby(['Red_List_Status','IUCN_color','Scientific_name']).count().sort_values('_uuid')['_uuid'].reset_index() 
  landings_species = landings_species[landings_species['_uuid'] > np.percentile(landings_species['_uuid'],50)].sort_values('_uuid')

  IUCN_status = ['Critically Endangered', 'Endangered', 'Vulnerable', 'Near Threatened', 'Least Concern', 'Data Deficient']
  IUCN_status = ['CR', 'EN', 'VU', 'NT', 'LC', 'DD', 'NE']
  IUCN_hex_colors = ['#D40000', '#FF7C00', '#FFD800', '#00A859', '#0085C8', '#CCCCCC', '#CCCCCC'] # Red, Orange, Yellow, Green, Blue, Gray
  
  IUCN_color = pd.DataFrame({
      'Red_List_Status': IUCN_status,
      'Color': IUCN_hex_colors
  })

  color_scale = alt.Scale(
   domain=IUCN_color['Red_List_Status'].tolist(),
   range=IUCN_color['Color'].tolist()
   )

  fig_species = alt.Chart(landings_species).mark_bar().encode(
   x=alt.X('Scientific_name', title='Scientific Name', sort=None),
   y=alt.Y('_uuid', title='Number of Records'),
   color=alt.Color('Red_List_Status:N', scale=color_scale, legend=alt.Legend(title="IUCN Red List Status"))).properties().configure_axis(labelLimit=1000)

  con1.altair_chart(fig_species, width='stretch')


  con2 = col_viz1.container(border=True)

  # Landings by IUCN Category

  con2.subheader("Maturity Ratio")
  con2.markdown('Distribution of the ratios of the number of adults and juveniles landed for each species.')

  #matrity_df = filtered_df.groupby(['group_catch','landing_site'])['_uuid'].count().reset_index().sort_values(by='_uuid', ascending=False)

  filtered_df.loc[(filtered_df['sex'] == 'Male') & (filtered_df['Shark_or_Ray'] == 'Ray'),'maturity'] = filtered_df.loc[(filtered_df['sex'] == 'Male') & (filtered_df['Shark_or_Ray'] == 'Ray'), 'disc_width'].astype('float')/filtered_df.loc[(filtered_df['sex'] == 'Male') & (filtered_df['Shark_or_Ray'] == 'Ray'), 'Male_size_at_maturity_cm_DW_TL'].astype('float')

  filtered_df.loc[(filtered_df['sex'] == 'Female') & (filtered_df['Shark_or_Ray'] == 'Ray'),'maturity'] = filtered_df.loc[(filtered_df['sex'] == 'Female') & (filtered_df['Shark_or_Ray'] == 'Ray'), 'disc_width'].astype('float')/filtered_df.loc[(filtered_df['sex'] == 'Female') & (filtered_df['Shark_or_Ray'] == 'Ray'), 'Female_size_at_maturity_cm_DW_TL'].astype('float')

  filtered_df.loc[(filtered_df['sex'] == 'Male') & (filtered_df['Shark_or_Ray'] == 'Shark'),'maturity'] = filtered_df.loc[(filtered_df['sex'] == 'Male') & (filtered_df['Shark_or_Ray'] == 'Shark'), 'total_length'].astype('float')/filtered_df.loc[(filtered_df['sex'] == 'Male') & (filtered_df['Shark_or_Ray'] == 'Shark'), 'Male_size_at_maturity_cm_DW_TL'].astype('float')

  filtered_df.loc[(filtered_df['sex'] == 'Female') & (filtered_df['Shark_or_Ray'] == 'Shark'),'maturity'] = filtered_df.loc[(filtered_df['sex'] == 'Female') & (filtered_df['Shark_or_Ray'] == 'Shark'), 'total_length'].astype('float')/filtered_df.loc[(filtered_df['sex'] == 'Female') & (filtered_df['Shark_or_Ray'] == 'Shark'), 'Female_size_at_maturity_cm_DW_TL'].astype('float')

  line = alt.Chart(filtered_df).mark_rule(color='black', size=2).encode(
    x=alt.X(datum=1) # Draws a vertical line at x=10
  )

  fig_maturity = alt.Chart(filtered_df).mark_bar().encode(
    x = alt.X('maturity:Q', title='Maturity Ratio', bin=alt.Bin(extent=[0,3], step=0.2)),
    y = alt.Y('count():Q', title='Individuals')
#    color='group_catch'
  )

  con2.altair_chart(fig_maturity + line, width='stretch')


 # Fishing Gear

  con5 = col_viz1.container(border=True)

  con5.subheader('Fishing Gear')
  con5.markdown('Count of the fishing gear used. In some cases, multiple gears were used during the same fishing trip.')
#  con5.markdown('Type of gear used')
 

  gears = ['gear_type/basket_traps',
       'gear_type/hook_line', 'gear_type/spear_gun', 'gear_type/beach_seines',
       'gear_type/ring_nets', 'gear_type/gill_nets_3', 'gear_type/gill_nets_6',
       'gear_type/longline', 'gear_type/reef_seine_set_net',
       'gear_type/drift_net']

  gear_df = []

  for gear in gears:
   gear_df_t = filtered_df[filtered_df[gear] == 1]
  
   gear_df.append([gear[10:],gear_df_t.count()['_uuid']])

  gear_df = pd.DataFrame(gear_df, columns=['gear_type','count']) 
  gear_df = gear_df.sort_values(by='count')[-7:]

  base = alt.Chart(gear_df).encode(
    alt.Theta("count:Q").stack(True),
    alt.Color("gear_type:N").legend(None)
 )

 fig_pie = base.mark_arc(outerRadius=120)
 text = base.mark_text(radius=140, size=12, fill='black').encode(text="gear_type:N")
  
 con5.altair_chart(fig_pie + text, width='stretch')






 # Fishing Gear Targetted









 with col_viz2:

  # Landings by Gear Type

  con3 = col_viz2.container(border=True)

  con3.subheader("IUCN Status of Landings")

  IUCN_status_df = filtered_df.groupby(['Red_List_Status'])['_uuid'].count().reset_index().sort_values(by='_uuid', ascending=False).drop(0)

  fig_IUCN = alt.Chart(IUCN_status_df).mark_bar().encode(
   x = alt.X('Red_List_Status', title='Red_List_Status', sort=None),
   y = alt.Y('_uuid', title='Number of landings'), 
   color=alt.Color( 'Red_List_Status:N', scale=color_scale, legend=alt.Legend(title="IUCN Red List Status"))).properties().configure_axis(labelLimit=1000) 

  con3.altair_chart(fig_IUCN, width='stretch')

  # Sex Ratio 

  con4 = col_viz2.container(border=True)

  con4.subheader('Sex Ratio')
  con4.markdown('Distribution of the ratios of the number of females and males landed for each species.')

  sex_ratio_df = filtered_df[filtered_df['sex'] == 'Female'].groupby('Scientific_name')['_uuid'].count()/filtered_df[filtered_df['sex'] == 'Male'].groupby('Scientific_name')['_uuid'].count()
  sex_ratio_df = sex_ratio_df.reset_index()
 
#  site_catch_df = filtered_df.groupby(['group_catch','landing_site'])['_uuid'].count().reset_index().sort_values(by='_uuid', ascending=False)

  fig_sex_ratio = alt.Chart(sex_ratio_df).mark_bar().encode(
   x = alt.X('_uuid:Q', title='Sex Ratio (female/male)', bin=alt.Bin(extent=[0,3], step=0.2)),
   y = alt.Y('count():Q', title='Individuals')
  )

  line = alt.Chart(filtered_df).mark_rule(color='black', size=2).encode(
   x=alt.X(datum=1) # Draws a vertical line at x=10
  )

  con4.altair_chart(fig_sex_ratio + line, width='stretch')


 # Targetted


  con6 = col_viz2.container(border=True)

  con6.subheader('Targeted')
  con6.markdown('Count of whether elasmobranchs were targeted during the fishing trip.')

  targeted_df = filtered_df.groupby('targeted').count().reset_index()

  base = alt.Chart(targeted_df).encode(
    alt.Theta("_uuid:Q").stack(True),
    alt.Color("targeted:N").legend(None)
  )

  fig_pie = base.mark_arc(outerRadius=120)
  text = base.mark_text(radius=140, size=12, fill='black').encode(text="targeted:N")
  
  con6.altair_chart(fig_pie + text, width='stretch')


else:
    # This block is executed if filtered_df is empty (e.g., no data, or filters result in empty set)
    st.markdown("---")
    st.warning("No data available for the selected filters. Showing a preview of all loaded data.")
    st.header("Original Data Preview (Top 10 rows)")
    st.dataframe(df.head(10), width='stretch') # Show head of the full dataset if filters yielded no results


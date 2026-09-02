import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import streamlit as st
import plotly.express as px
from datetime import date, datetime, timedelta
import pydeck as pdk

IUCN_columns = [
    'Shark_or_Ray', 
    'Scientific_name', 
    'Male_size_at_maturity_cm_DW_TL', 
    'Female_size_at_maturity_cm_DW_TL', 
    'Red_List_Status', 
    'IUCN_color'
]

IUCN_values = [
    ['Ray', 'Acroteriobatus zanzibarensis', np.nan, np.nan, 'NT', 'seagreen'],
    ['Ray', 'Aetobatus ocellatus', 100, 150, 'VU', 'lime'],
    ['Ray', 'Aetomylaeus vespertilio', 170, np.nan, 'EN', 'darkorange'],
    ['Shark', 'Alopias pelagicus', 250, 250, 'EN', 'darkorange'],
    ['Shark', 'Alopias superciliosus', 245, 280, 'VU', 'lime'],
    ['Ray', 'Bathytoshia lata', 100, 110, 'LC', 'blue'],
    ['Shark', 'Carcharhinus albimarginatus', 160, 160, 'VU', 'lime'],
    ['Shark', 'Carcharhinus altimus', 215, 225, 'NT', 'seagreen'],
    ['Shark', 'Carcharhinus amblyrhynchos', 110, 120, 'EN', 'darkorange'],
    ['Shark', 'Carcharhinus brevipinna', np.nan, np.nan, 'VU', 'lime'],
    ['Shark', 'Carcharhinus falciformis', 180, 180, 'VU', 'lime'],
    ['Shark', 'Carcharhinus humani', 75, np.nan, 'DD', 'grey'],
    ['Shark', 'Carcharhinus leucas', 160, 180, 'NT', 'seagreen'],
    ['Shark', 'Carcharhinus limbatus', np.nan, np.nan, 0, np.nan],
    ['Shark', 'Carcharhinus longimanus', 170, 175, 'CR', 'red'],
    ['Shark', 'Carcharhinus melanopterus', 90, 95, 'VU', 'lime'],
    ['Shark', 'Carcharhinus obscurus', 215, 220, 'EN', 'darkorange'],
    ['Shark', 'Carcharhinus plumbeus', np.nan, np.nan, 0, np.nan],
    ['Shark', 'Carcharhinus sealei', np.nan, np.nan, 0, np.nan],
    ['Shark', 'Carcharhinus sorrah', 90, 95, 'NT', 'seagreen'],
    ['Shark', 'Carcharhinus spp', np.nan, np.nan, 'NE', 'grey'],
    ['Shark', 'Carcharodon carcharias', 310, 400, 'VU', 'lime'],
    ['Shark', 'Centrophorus spp', np.nan, np.nan, 'NE', 'grey'],
    ['Shark', 'Cirrhigaleus asper', 90, 85, 'DD', 'grey'],
    ['Ray', 'Dasyatidae', np.nan, np.nan, 'NE', 'grey'],
    ['Shark', 'Echinorhinus brucus', np.nan, np.nan, 0, np.nan],
    ['Shark', 'Galeocerdo cuvier', 250, 275, 'NT', 'seagreen'],
    ['Shark', 'Hemipristis elongata', 110, 120, 'VU', 'lime'],
    ['Shark', 'Heptranchias perlo', 75, 90, 'NT', 'seagreen'],
    ['Shark', 'Heterodontus ramalheira', np.nan, np.nan, 'DD', 'grey'],
    ['Shark', 'Hexanchus griseus', 125, 400, 'NT', 'seagreen'],
    ['Shark', 'Hexanchus nakamurai', 140, 125, 'NT', 'seagreen'],
    ['Ray', 'Himantura leoparda', 70, np.nan, 'VU', 'lime'],
    ['Ray', 'Himantura uarnak', 80, np.nan, 'VU', 'lime'],
    ['Shark', 'Hypogaleus hyugaensis', 100, 100, 'LC', 'blue'],
    ['Shark', 'Isurus oxyrinchus', 165, 265, 'EN', 'darkorange'],
    ['Shark', 'Isurus paucus', 165, 265, 'EN', 'darkorange'],
    ['Shark', 'Loxodon macrorhinus', 60, 80, 'LC', 'blue'],
    ['Ray', 'Maculabatis ambigua', 60, 60, 'NT', 'seagreen'],
    ['Ray', 'Megatrygon microps', np.nan, np.nan, 'DD', 'grey'],
    ['Ray', 'Mobula eregoodoo', 100, 90, 'EN', 'darkorange'],
    ['Ray', 'Mobula kuhlii', 115, 115, 'EN', 'darkorange'],
    ['Ray', 'Mobula mobular', 200, 235, 'EN', 'darkorange'],
    ['Ray', 'Mobula tarapacana', 235, 270, 'EN', 'darkorange'],
    ['Ray', 'Mobula thurstoni', 150, 150, 'EN', 'darkorange'],
    ['Shark', 'Mustelus manazo', 55, 60, 'EN', 'darkorange'],
    ['Shark', 'Mustelus mosis', 65, 75, 'NT', 'seagreen'],
    ['Ray', 'Neotrygon caeruleopunctata', 30, np.nan, 'NE', 'grey'],
    ['Shark', 'Odontaspis ferox', 200, 300, 'VU', 'lime'],
    ['Ray', 'Pastinachus ater', np.nan, np.nan, 'LC', 'blue'],
    ['Ray', 'Pateobatis fai', 110, np.nan, 'VU', 'lime'],
    ['Ray', 'Pateobatis jenkinsii', 75, np.nan, 'VU', 'lime'],
    ['Shark', 'Prionace glauca', 185, 185, 'NT', 'seagreen'],
    ['Shark', 'Pseudoginglymostoma brevicaudatum', 60, 55, 'CR', 'red'],
    ['Ray', 'Rhina ancylostoma', np.nan, np.nan, 0, np.nan],
    ['Ray', 'Rhina ancylostomus', 150, 180, 'CR', 'red'],
    ['Ray', 'Rhinobatos austini', np.nan, np.nan, 'DD', 'grey'],
    ['Ray', 'Rhinoptera jayakari', 80, np.nan, 'NE', 'grey'],
    ['Shark', 'Rhizoprionodon acutus', 55, 60, 'VU', 'lime'],
    ['Ray', 'Rhynchobatus australiae', 125, 155, 'CR', 'red'],
    ['Shark', 'Sphyrna lewini', 140, 210, 'CR', 'red'],
    ['Shark', 'Sphyrna mokarran', 225, 210, 'CR', 'red'],
    ['Shark', 'Sphyrna spp', np.nan, np.nan, 0, np.nan],
    ['Shark', 'Sphyrna zygaena', 250, 265, 'VU', 'lime'],
    ['Shark', 'Squalus mitsukurii', np.nan, np.nan, 0, np.nan],
    ['Shark', 'Squalus spp', 90, 85, 'NE', 'grey'],
    ['Shark', 'Stegostoma tigrinum', 150, 170, 'EN', 'darkorange'],
    ['Ray', 'Taeniura lymma', 20, np.nan, 'NT', 'seagreen'],
    ['Ray', 'Taeniurops meyeni', 100, np.nan, 'VU', 'lime'],
    ['Ray', 'Torpedo fuscomaculata', np.nan, np.nan, 'DD', 'grey'],
    ['Shark', 'Triaenodon obesus', 105, 105, 'VU', 'lime'],
    ['Ray', 'Urogymnus asperrimus', 90, 100, 'VU', 'lime']
]

df_IUCN = pd.DataFrame(IUCN_values, columns=IUCN_columns)

@st.cache_data
def read_data(filename):
 #df = pd.read_parquet(filename)
 df = pd.read_csv(filename, low_memory=False) # parquet loses some data
 return df

df = read_data('SHARK_kobo_data.csv') # parquet loses some data

df = pd.read_csv('SHARK_kobo_data.csv', low_memory=True) # parquet loses some data
df = pd.merge(df, df_IUCN, left_on='Scientific_name', right_on = 'Scientific_name', how='left')

df['today'] = pd.to_datetime(df['today'],format='mixed')

#df['Index'] = pd.to_datetime(df['today'],format='mixed')

# merge with data in field Date coming from import of old data
#df.loc[df['Date'] != '', 'today'] = df['Date']
#df = df.drop('Date', axis=1)

df['date'] = pd.to_datetime(df['today'],format='mixed').dt.date
df['month'] = df['today'].dt.month
df['year'] = df['today'].dt.year
df = df.set_index('today')

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

# market filter

all_markets = sorted(df['market'].dropna().unique())
selected_markets = st.sidebar.multiselect(
    "Select Market(s):",
    options=all_markets,
    default=all_markets,
    key='market_filter'
)

# site filter

all_sites = sorted(df['landing_site'].dropna().unique())
selected_sites = st.sidebar.multiselect(
    "Select Landing Site(s):",
    options=all_sites,
    default=all_sites,
    key='site_filter'
)

# type catch filter

#if 'secondary_options' not in st.session_state:
#    # Start with the options corresponding to the first category by default
##    default_category = df_IUCN['Scientific_name'].to_list()
#    st.session_state.secondary_options = df_IUCN['Scientific_name'].to_list()
#    st.session_state.secondary_selection = [st.session_state.secondary_options[0]] 
#
#def update_species_menu():
#    """Callback function executed when the primary menu changes."""
#    # Read the new primary selection's key
#    selected_category = st.session_state.primary_selection 
#
#    # Update the list of options for the secondary menu
#    st.session_state.secondary_options = df_IUCN[df_IUCN['Shark_or_Ray'].isin(selected_category)]['Scientific_name'].to_list()
#
#    new_options = st.session_state.secondary_options
#    st.session_state.secondary_selection = [new_options[:]] if new_options else []


all_groups = ['Ray', 'Shark'] #sorted(df['Type of catch'].dropna().unique())
selected_groups = st.sidebar.multiselect(
    "Select Group(s):",
    options=all_groups,
    default=['Ray', 'Shark'],
    key='selected_groups'
)

# species filter
 

#top_species = df.groupby(['Scientific_name'])['_uuid'].count().sort_values()
#top_species = top_species[top_species > np.percentile(top_species,80)].sort_index()
#
#selected_species = st.sidebar.multiselect(
#    "Select Top Species(s):",
#    options=st.session_state.secondary_options,
#    default=st.session_state.secondary_options,
#    key='secondary_selection',
#)

# --- Apply Filters ---

filtered_df = df[(df['date'] >= start_date) & (df['date'] <= end_date) & (df['landing_site'].isin(selected_sites) | df['market'].isin(selected_markets)) & (df['type'].isin(selected_groups))]


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
     <h2 class="h2-custom">Landings of Sharks and Rays</h2>
     """, unsafe_allow_html=True)

#    st.write('Artisanal Landings Data Visualization')

#print(st.get_option("theme.style"))

#with col2:
# if st.context.theme == 'dark':
 #st.image('./img/WCS-logo_white.png', width=300)
# else:
# st.image('./img/WCS-logo.png', width=300)

st.markdown(f"Visualizing data from **{start_date.strftime('%Y-%m-%d')}** to **{end_date.strftime('%Y-%m-%d')}** for sites: **{', '.join(selected_sites) if selected_sites else 'None'}**.")
st.markdown("---") # Separator


# I would add a time series of sampling days for the landing sites

if not filtered_df.empty:
    total_records = len(filtered_df['Scientific_name'])
    total_species = len(filtered_df['Scientific_name'].unique())
    total_weight = filtered_df['weight'].sum()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Number of Records", value=total_records)
    with col2:
        st.metric(label="Number of Species Landed", value=total_species)
    with col3:
        st.metric(label="Total Catch (kg)", value=f"{total_weight:,.2f}")
    st.markdown("---")
else:
    st.warning("No data available for the selected filters.")

# --- Visualizations ---

if not filtered_df.empty:

 st.header("Landing Records")

 coords = pd.merge(filtered_df[['landing_site','_gps_latitude']].groupby('landing_site').median(), filtered_df[['landing_site','_gps_longitude']].groupby('landing_site').median(), right_index=True, left_index=True)
 coords = pd.merge(coords, filtered_df[['landing_site','_gps_latitude']].groupby('landing_site').count(), right_index=True, left_index=True)
 coords = coords.rename(columns = {'_gps_latitude_x' : 'lat', '_gps_longitude' : 'lon', '_gps_latitude_y' : 'count'})
 coords['count'] = coords['count']*10 

 coords = coords.dropna().reset_index()
 
 # 2. Define the Dot Layer
 dots_layer = pdk.Layer(
     'ScatterplotLayer',
     coords.dropna(),
     get_position='[lon, lat]',
     get_radius='count',
     get_color='[200, 30, 0, 160]',
 )
 
 # 3. Define the Label Layer
 labels_layer = pdk.Layer(
     "TextLayer",
     coords.dropna(),
     get_position='[lon, lat]',
     get_text='landing_site',
     get_size=12,
     get_color=[1, 1, 1],
     get_alignment_baseline="'bottom'",
 )
 
 # 4. Render the Map
 st.pydeck_chart(pdk.Deck(
     map_style='light',
     layers=[dots_layer, labels_layer],
     #layers=[dots_layer],
     initial_view_state=pdk.ViewState(
         latitude=np.mean(coords.lat),
         longitude=np.mean(coords.lon),
         zoom=7,
         pitch=0,
     ),
 ))




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


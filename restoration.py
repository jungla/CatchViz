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



# Time Aggregation Filter
time_agg = st.sidebar.selectbox(
    "Select Time Aggregation:",
    options=["Daily", "Weekly", "Monthly", "Yearly"],
    index=1  # Default to Weekly
)
freq_map = {"Daily": "D", "Weekly": "W", "Monthly": "ME", "Yearly": "YE"}
freq = freq_map[time_agg]



# Check if DataFrame is empty before attempting to filter
if df.empty:
    st.warning("No data loaded. Please check your Excel file, sheet name, and column headers.")
    # Display an empty DataFrame or a message
    st.header("Filtered Data Records")
    st.dataframe(pd.DataFrame(), width='stretch') # Display an empty DataFrame
    st.stop() # Stop further execution if no data

min_date = df['date'].min() #date(2019,1,1)
max_date = df['date'].max()

#df_date_range = pd.DataFrame({'date' : pd.date_range(start=min_date, end=max_date, freq='D')})
df_date_range = pd.DataFrame({'date' : pd.date_range(start=min_date, end=max_date, freq=freq)})

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
        st.metric(label="Total Area Transplanted (ha)", value=f"{total_area_restored:,.2f}")
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
                <p>Fragments,<br/>
                in Nursery: <b>{total_fragments_in_nursery_to_date}</b><br/>
                Transplanted: <b>{total_fragments_transplanted_to_date}</b></p>"""}
    ))

    st.header('Restoration Effort')

    # Aactivity Days by Site - all activities

    con0 = st.container(border=True)
    con0.subheader("Total days of activity")
    activity_site = filtered_df[['_uuid','project_site','datetime']].drop_duplicates().groupby('project_site').resample(freq, on='datetime').count().reset_index()

    #  boat_type = filtered_df.groupby('boat_type').count().sort_values(by='_uuid').reset_index()

    fig_activity = alt.Chart(activity_site).mark_bar().encode(
    x=alt.X('datetime', title='Time ['+str(freq)+']', sort=None),
    y=alt.Y('_uuid', title='Number of Days in the Field'),
    color='project_site'
    )
    con0.altair_chart(fig_activity, width='stretch')

# Activity by site in time. Activities are: 'select_activity/fragmentation', 'select_activity/transplantation', 'select_activity/monitoring', 'select_activity/cleaning_and_maintaining' 

# for 'select_activity/fragmentation'

    col_viz1, col_viz2 = st.columns(2)

    with col_viz1:
        for activity in ['select_activity/fragmentation', 'select_activity/transplantation']:
            title = activity.split('/')[1].title()
            title = title.replace("_"," ")
            conN = st.container(border=True)
            conN.subheader(title)
            
            activity_df = filtered_df[filtered_df[activity] == 1]
            activity_site = activity_df[['_uuid','project_site','datetime']].drop_duplicates().groupby('project_site').resample(freq, on='datetime').count().reset_index()

            activity_site = pd.merge(activity_site, df_date_range, left_on='datetime', right_on='date', how='right')
            activity_site['_uuid'] = activity_site['_uuid'].fillna(0)

            fig_act = alt.Chart(activity_site).mark_bar().encode(
            x=alt.X('date', title='Time ['+str(freq)+']'),  
            y=alt.Y('_uuid', title='Number of Days doing '+title),       
            color=alt.Color('project_site:N',
                    scale=alt.Scale(
                        domain=list(activity_site['project_site'].unique().dropna()),  # Only maps colors to these real categories
                    )
                )
            )
            conN.altair_chart(fig_act, width='stretch')

    with col_viz2:
        for activity in ['select_activity/monitoring', 'select_activity/cleaning_and_maintaining']:

            title = activity.split('/')[1].title()
            title = title.replace("_"," ")
            conN = st.container(border=True)
            conN.subheader(title)
            
            activity_df = filtered_df[filtered_df[activity] == 1]
            activity_site = activity_df[['_uuid','project_site','datetime']].drop_duplicates().groupby('project_site').resample(freq, on='datetime').count().reset_index()

            activity_site = pd.merge(activity_site, df_date_range, left_on='datetime', right_on='date', how='right')
            activity_site['_uuid'] = activity_site['_uuid'].fillna(0)

            fig_act = alt.Chart(activity_site).mark_bar().encode(
            x=alt.X('date', title='Time ['+str(freq)+']'),  
            y=alt.Y('_uuid', title='Number of Days doing '+title),       
            color=alt.Color('project_site:N',
                    scale=alt.Scale(
                        domain=list(activity_site['project_site'].unique().dropna()),  # Only maps colors to these real categories
                    )
                )
            )
            conN.altair_chart(fig_act, width='stretch')
    
    st.header('Restoration Impact')

    con0 = st.container(border=True)
    con0.subheader("Total area restored [ha]")

    total_transplanted_corals = filtered_df[['_uuid','project_site','datetime','total_fragments_transplanted_to_date']].groupby('project_site').resample(freq, on='datetime').max().ffill().reset_index()
    total_transplanted_corals['total_area_transplanted_to_date'] = total_transplanted_corals['total_fragments_transplanted_to_date'] / 2 / 1e4
    #  boat_type = filtered_df.groupby('boat_type').count().sort_values(by='_uuid').reset_index()

    fig_activity = alt.Chart(total_transplanted_corals).mark_line(point=True, interpolate='natural').encode(
    x=alt.X('datetime', title='Time ['+str(freq)+']', sort=None),
    y=alt.Y('total_area_transplanted_to_date', title='Transplanted Area to Date'),
    color='project_site'
    )
    con0.altair_chart(fig_activity, width='stretch')

    col_viz1, col_viz2 = st.columns(2)

    with col_viz1:
        for metric in ['total_fragments_transplanted_to_date', 'total_fragments_on_reef_stars_to_date']:
            title = metric.replace("_"," ")
            conN = st.container(border=True)
            conN.subheader(title)
            
            metric_site = filtered_df[['_uuid','project_site','datetime',metric]].groupby('project_site').resample(freq, on='datetime').max().ffill().reset_index()

            metric_site = pd.merge(metric_site, df_date_range, left_on='datetime', right_on='date', how='right')
            
            fig_act = alt.Chart(metric_site).mark_line(interpolate='natural', point=True).encode(
            x=alt.X('date', title='Time ['+str(freq)+']'),  
            y=alt.Y(metric, title=title),       
            color=alt.Color('project_site:N',
                    scale=alt.Scale(
                        domain=list(metric_site['project_site'].unique().dropna()),  # Only maps colors to these real categories
                    )
                )
            )
            conN.altair_chart(fig_act, width='stretch')

    with col_viz2:
        for metric in ['total_fragments_on_fence_wires_to_date', 'total_fragments_on_clips_to_date']:
            title = metric.replace("_"," ")
            conN = st.container(border=True)
            conN.subheader(title)
            
            metric_site = filtered_df[['_uuid','project_site','datetime',metric]].groupby('project_site').resample(freq, on='datetime').max().ffill().reset_index()

            metric_site = pd.merge(metric_site, df_date_range, left_on='datetime', right_on='date', how='right')
            
            fig_act = alt.Chart(metric_site).mark_line(interpolate='natural', point=True).encode(
            x=alt.X('date', title='Time ['+str(freq)+']'),  
            y=alt.Y(metric, title=title),       
            color=alt.Color('project_site:N',
                    scale=alt.Scale(
                        domain=list(metric_site['project_site'].unique().dropna()),  # Only maps colors to these real categories
                    )
                )
            )
            conN.altair_chart(fig_act, width='stretch')

    st.header('Restoration Performance')

    con0 = st.container(border=True)
    con0.subheader("Fragments transplanted")

    session_transplanted_corals = filtered_df[['_uuid','project_site','datetime','total_number_of_fragments_transplanted']].groupby('project_site').resample(freq, on='datetime').sum().dropna().reset_index()
    
    session_transplanted_corals = pd.merge(session_transplanted_corals, df_date_range, left_on='datetime', right_on='date', how='right')
            
    fig_activity = alt.Chart(session_transplanted_corals).mark_bar().encode(
    x=alt.X('datetime', title='Time ['+str(freq)+']', sort=None),
    y=alt.Y('total_number_of_fragments_transplanted', title='Transplanted Fragments per Session'),
    color='project_site'
    )
    con0.altair_chart(fig_activity, width='stretch')

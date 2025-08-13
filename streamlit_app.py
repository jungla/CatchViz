import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta

# --- Page Configuration ---
st.set_page_config(
    page_title="Fishery Catch Data Visualization",
    page_icon="🎣",
    layout="wide" # Use wide layout for more space for charts
)

# --- Helper Function to Generate Sample Data ---
# In a real scenario, you would load your data here, e.g., using pd.read_csv('your_data.csv')
# Make sure your CSV has columns like 'Date', 'Site', 'Species', 'Catch_Weight_kg', etc.
# IMPORTANT: Ensure the 'Date' column is converted to datetime objects:
# df['Date'] = pd.to_datetime(df['Date'])

@st.cache_data # Cache the data generation/loading
def generate_sample_data(num_records=500):
    """Generates a DataFrame with sample fishery catch data."""
    start_date = datetime(2024, 1, 1)
    dates = [start_date + timedelta(days=np.random.randint(0, 365*1.2)) for _ in range(num_records)] # Spread over ~1 year
    sites = ['Fumba Bay', 'Nungwi Reef', 'Kizimkazi Channel', 'Mnemba Atoll', 'Paje Kelp Beds']
    species = ['Tuna', 'Snapper', 'Grouper', 'Mackerel', 'Sardines', 'Octopus', 'Lobster']
    gear = ['Longline', 'Handline', 'Net', 'Trap', 'Spear']

    data = {
        'Date': dates,
        'Site': np.random.choice(sites, num_records),
        'Species': np.random.choice(species, num_records),
        'Catch_Weight_kg': np.random.uniform(5, 150, num_records).round(2), # Random weights
        'Gear_Type': np.random.choice(gear, num_records)
    }
    df = pd.DataFrame(data)
    df['Date'] = pd.to_datetime(df['Date']).dt.date # Keep only the date part for filtering simplicity
    df = df.sort_values(by='Date').reset_index(drop=True)
    return df

# --- Load Data ---
df = generate_sample_data()

# --- Sidebar Filters ---
st.sidebar.header("Filters ⚙️")

# Date Filter
min_date = df['Date'].min()
max_date = df['Date'].max()

# st.date_input requires datetime.date objects
date_range = st.sidebar.date_input(
    "Select Date Range:",
    value=(min_date, max_date), # Default range
    min_value=min_date,
    max_value=max_date,
    key='date_filter'
)

# Handle case where date_input might return fewer than 2 dates briefly
start_date = min_date
end_date = max_date
if len(date_range) == 2:
    start_date, end_date = date_range

# Site Filter
all_sites = sorted(df['Site'].unique())
selected_sites = st.sidebar.multiselect(
    "Select Site(s):",
    options=all_sites,
    default=all_sites, # Default to all sites selected
    key='site_filter'
)

# --- Apply Filters ---
# Filter logic needs to handle datetime.date objects
filtered_df = df[
    (df['Date'] >= start_date) &
    (df['Date'] <= end_date) &
    (df['Site'].isin(selected_sites))
]

# --- Main Page Content ---
st.title("🎣 Fishery Catch Data Visualization")
st.markdown(f"Visualizing data from **{start_date.strftime('%Y-%m-%d')}** to **{end_date.strftime('%Y-%m-%d')}** for sites: **{', '.join(selected_sites) if selected_sites else 'None'}**.")
st.markdown("---") # Separator

# --- Display Metrics/KPIs ---
if not filtered_df.empty:
    total_catch = filtered_df['Catch_Weight_kg'].sum()
    num_records_filtered = len(filtered_df)
    avg_catch_per_record = filtered_df['Catch_Weight_kg'].mean()

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
    st.header("Catch Analysis")

    # 1. Catch Weight Over Time (Line Chart)
    st.subheader("Catch Weight Over Time")
    # Group by date and sum the catch
    time_series_df = filtered_df.groupby('Date')['Catch_Weight_kg'].sum().reset_index()
    fig_time = px.line(
        time_series_df,
        x='Date',
        y='Catch_Weight_kg',
        title="Total Catch Weight per Day",
        markers=True,
        labels={'Catch_Weight_kg': 'Total Catch (kg)'}
        )
    fig_time.update_layout(hovermode="x unified")
    st.plotly_chart(fig_time, use_container_width=True)

    # Split into two columns for side-by-side charts
    col_viz1, col_viz2 = st.columns(2)

    with col_viz1:
        # 2. Catch by Site (Bar Chart)
        st.subheader("Catch by Site")
        site_catch_df = filtered_df.groupby('Site')['Catch_Weight_kg'].sum().reset_index().sort_values(by='Catch_Weight_kg', ascending=False)
        fig_site = px.bar(
            site_catch_df,
            x='Site',
            y='Catch_Weight_kg',
            title="Total Catch Weight per Site",
            color='Site', # Color bars by site
            labels={'Catch_Weight_kg': 'Total Catch (kg)'}
        )
        fig_site.update_layout(xaxis_title=None) # Hide x-axis title if sites are obvious
        st.plotly_chart(fig_site, use_container_width=True)

        # 4. Catch by Gear Type (Pie Chart)
        st.subheader("Catch Distribution by Gear Type")
        gear_catch_df = filtered_df.groupby('Gear_Type')['Catch_Weight_kg'].sum().reset_index()
        fig_gear = px.pie(
            gear_catch_df,
            names='Gear_Type',
            values='Catch_Weight_kg',
            title="Proportion of Catch by Gear Type",
            hole=0.3 # Make it a donut chart
        )
        st.plotly_chart(fig_gear, use_container_width=True)


    with col_viz2:
        # 3. Catch by Species (Bar Chart)
        st.subheader("Catch by Species")
        species_catch_df = filtered_df.groupby('Species')['Catch_Weight_kg'].sum().reset_index().sort_values(by='Catch_Weight_kg', ascending=False)
        fig_species = px.bar(
            species_catch_df,
            x='Species',
            y='Catch_Weight_kg',
            title="Total Catch Weight per Species",
            color='Species', # Color bars by species
            labels={'Catch_Weight_kg': 'Total Catch (kg)'}
        )
        fig_species.update_layout(xaxis_title=None)
        st.plotly_chart(fig_species, use_container_width=True)

        # 5. Catch Composition Site vs Species (Heatmap - Optional, needs density)
        # A heatmap might be complex without more detailed data, but a grouped bar chart is good:
        st.subheader("Species Catch per Site")
        site_species_df = filtered_df.groupby(['Site', 'Species'])['Catch_Weight_kg'].sum().reset_index()
        fig_site_species = px.bar(
            site_species_df,
            x='Site',
            y='Catch_Weight_kg',
            color='Species', # Stack or group bars by species
            title='Species Catch Breakdown by Site',
            barmode='stack', # or 'group'
            labels={'Catch_Weight_kg': 'Total Catch (kg)'}
        )
        st.plotly_chart(fig_site_species, use_container_width=True)


    # --- Display Filtered Data Table ---
    st.markdown("---")
    st.header("Filtered Data Records")
    st.dataframe(filtered_df, use_container_width=True) # Display the filtered dataframe

else:
    # Only show the raw data view if filters result in empty set
    st.header("Original Sample Data (Top 100 rows)")
    st.dataframe(df.head(100), use_container_width=True)


st.sidebar.markdown("---")
st.sidebar.info("This app uses sample data. Replace `generate_sample_data()` with your data loading logic (e.g., `pd.read_csv`).")

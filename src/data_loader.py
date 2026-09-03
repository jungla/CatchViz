from pathlib import Path
import pandas as pd
import streamlit as st
from config.settings import (
    get_data_filepath,
    REFERENCE_DIR,
    PROTECTED_SPECIES_URL,
)

@st.cache_data(show_spinner="Loading Catch data...")
def load_catch_data() -> pd.DataFrame:
    """Load and prepare bony fishes catch dataset."""
    filepath = get_data_filepath("CATCH_kobo_data.csv")
    if not filepath.exists():
        return pd.DataFrame()
    df = pd.read_csv(filepath, low_memory=False)
    if "today" in df.columns:
        df["today"] = pd.to_datetime(df["today"], format="mixed").dt.date
    return df

@st.cache_data(show_spinner="Loading IUCN reference data...")
def load_iucn_reference() -> pd.DataFrame:
    """Load IUCN Red List and maturity size reference table."""
    ref_file = REFERENCE_DIR / "iucn_species.csv"
    if ref_file.exists():
        return pd.read_csv(ref_file)
    return pd.DataFrame()

@st.cache_data(show_spinner="Loading Sharks & Rays data...")
def load_shark_data() -> pd.DataFrame:
    """Load and prepare sharks and rays landing dataset merged with IUCN reference data."""
    filepath = get_data_filepath("SHARK_kobo_data.csv")
    if not filepath.exists():
        return pd.DataFrame()
    df = pd.read_csv(filepath, low_memory=False)

    # Merge with IUCN reference
    iucn_df = load_iucn_reference()
    if not iucn_df.empty and "Scientific_name" in df.columns:
        df = pd.merge(df, iucn_df, on="Scientific_name", how="left")

    if "today" in df.columns:
        df["today_raw"] = pd.to_datetime(df["today"], format="mixed")
        df["date"] = df["today_raw"].dt.date
        df["month"] = df["today_raw"].dt.month
        df["year"] = df["today_raw"].dt.year
        df["today"] = df["today_raw"]
    return df

@st.cache_data(show_spinner="Loading Restoration sites reference...")
def load_restoration_sites_reference() -> pd.DataFrame:
    """Load restoration nursery and transplanting site GPS coordinates."""
    ref_file = REFERENCE_DIR / "restoration_sites.csv"
    if ref_file.exists():
        return pd.read_csv(ref_file)
    return pd.DataFrame()

@st.cache_data(show_spinner="Loading Coral Reef Restoration data...")
def load_restoration_data() -> pd.DataFrame:
    """Load and prepare coral reef restoration dataset merged with site coordinates."""
    filepath = get_data_filepath("RESTORATION_kobo_data.csv")
    if not filepath.exists():
        return pd.DataFrame()
    df = pd.read_csv(filepath, low_memory=False)

    if "Date" in df.columns:
        df["today"] = pd.to_datetime(df["Date"], format="mixed")
        df["date"] = df["today"].dt.date
        df["month"] = df["today"].dt.month
        df["year"] = df["today"].dt.year

    coords_df = load_restoration_sites_reference()
    if not coords_df.empty and "site_name" in df.columns:
        df = pd.merge(df, coords_df, on="site_name", how="left")

    return df

@st.cache_data(show_spinner="Loading Protected Species catalog...")
def load_protected_species_data() -> pd.DataFrame:
    """Load Zanzibar marine protected species list from remote source."""
    return pd.read_csv(PROTECTED_SPECIES_URL)

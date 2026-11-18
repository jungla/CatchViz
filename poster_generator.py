"""
poster_generator.py
===================
Self-contained generator for A0 scientific/management report posters formatted with Typst.
Designed for the WCS Tanzania CatchViz Streamlit platform.

Supports:
- Bony Fishes landings reports (CATCH dataset)
- Sharks and Rays landings reports (SHARK dataset)

Can be:
1. Imported and rendered inside Streamlit via `render_poster_export_ui(...)`
2. Executed via CLI: `python poster_generator.py --type bony_fishes --csv CATCH_kobo_data.csv --output poster.pdf`
3. Used programmatically via `generate_poster(...)`
"""

import os
import sys
import shutil
import subprocess
import tempfile
import zipfile
from datetime import datetime, date
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

import pandas as pd
import numpy as np

# Use non-interactive backend for matplotlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

# Optional Streamlit import for UI components
try:
    import streamlit as st
    HAS_STREAMLIT = True
except ImportError:
    HAS_STREAMLIT = False


# ==============================================================================
# IUCN Reference Data for Sharks and Rays
# ==============================================================================
IUCN_COLUMNS = [
    'Shark_or_Ray', 
    'Scientific_name', 
    'Male_size_at_maturity_cm_DW_TL', 
    'Female_size_at_maturity_cm_DW_TL', 
    'Red_List_Status', 
    'IUCN_color'
]

IUCN_VALUES = [
    ['Ray', 'Acroteriobatus zanzibarensis', np.nan, np.nan, 'NT', '#00A859'],
    ['Ray', 'Aetobatus ocellatus', 100, 150, 'VU', '#FFD800'],
    ['Ray', 'Aetomylaeus vespertilio', 170, np.nan, 'EN', '#FF7C00'],
    ['Shark', 'Alopias pelagicus', 250, 250, 'EN', '#FF7C00'],
    ['Shark', 'Alopias superciliosus', 245, 280, 'VU', '#FFD800'],
    ['Ray', 'Bathytoshia lata', 100, 110, 'LC', '#0085C8'],
    ['Shark', 'Carcharhinus albimarginatus', 160, 160, 'VU', '#FFD800'],
    ['Shark', 'Carcharhinus altimus', 215, 225, 'NT', '#00A859'],
    ['Shark', 'Carcharhinus amblyrhynchos', 110, 120, 'EN', '#FF7C00'],
    ['Shark', 'Carcharhinus brevipinna', np.nan, np.nan, 'VU', '#FFD800'],
    ['Shark', 'Carcharhinus falciformis', 180, 180, 'VU', '#FFD800'],
    ['Shark', 'Carcharhinus humani', 75, np.nan, 'DD', '#888888'],
    ['Shark', 'Carcharhinus leucas', 160, 180, 'NT', '#00A859'],
    ['Shark', 'Carcharhinus limbatus', np.nan, np.nan, 'VU', '#FFD800'],
    ['Shark', 'Carcharhinus longimanus', 170, 175, 'CR', '#D40000'],
    ['Shark', 'Carcharhinus melanopterus', 90, 95, 'VU', '#FFD800'],
    ['Shark', 'Carcharhinus obscurus', 215, 220, 'EN', '#FF7C00'],
    ['Shark', 'Carcharhinus plumbeus', np.nan, np.nan, 'EN', '#FF7C00'],
    ['Shark', 'Carcharhinus sealei', np.nan, np.nan, 'VU', '#FFD800'],
    ['Shark', 'Carcharhinus sorrah', 90, 95, 'NT', '#00A859'],
    ['Shark', 'Carcharhinus spp', np.nan, np.nan, 'NE', '#AAAAAA'],
    ['Shark', 'Carcharodon carcharias', 310, 400, 'VU', '#FFD800'],
    ['Shark', 'Centrophorus spp', np.nan, np.nan, 'NE', '#AAAAAA'],
    ['Shark', 'Cirrhigaleus asper', 90, 85, 'DD', '#888888'],
    ['Ray', 'Dasyatidae', np.nan, np.nan, 'NE', '#AAAAAA'],
    ['Shark', 'Echinorhinus brucus', np.nan, np.nan, 'EN', '#FF7C00'],
    ['Shark', 'Galeocerdo cuvier', 250, 275, 'NT', '#00A859'],
    ['Shark', 'Hemipristis elongata', 110, 120, 'VU', '#FFD800'],
    ['Shark', 'Heptranchias perlo', 75, 90, 'NT', '#00A859'],
    ['Shark', 'Heterodontus ramalheira', np.nan, np.nan, 'DD', '#888888'],
    ['Shark', 'Hexanchus griseus', 125, 400, 'NT', '#00A859'],
    ['Shark', 'Hexanchus nakamurai', 140, 125, 'NT', '#00A859'],
    ['Ray', 'Himantura leoparda', 70, np.nan, 'VU', '#FFD800'],
    ['Ray', 'Himantura uarnak', 80, np.nan, 'VU', '#FFD800'],
    ['Shark', 'Hypogaleus hyugaensis', 100, 100, 'LC', '#0085C8'],
    ['Shark', 'Isurus oxyrinchus', 165, 265, 'EN', '#FF7C00'],
    ['Shark', 'Isurus paucus', 165, 265, 'EN', '#FF7C00'],
    ['Shark', 'Loxodon macrorhinus', 60, 80, 'LC', '#0085C8'],
    ['Ray', 'Maculabatis ambigua', 60, 60, 'NT', '#00A859'],
    ['Ray', 'Megatrygon microps', np.nan, np.nan, 'DD', '#888888'],
    ['Ray', 'Mobula eregoodoo', 100, 90, 'EN', '#FF7C00'],
    ['Ray', 'Mobula kuhlii', 115, 115, 'EN', '#FF7C00'],
    ['Ray', 'Mobula mobular', 200, 235, 'EN', '#FF7C00'],
    ['Ray', 'Mobula tarapacana', 235, 270, 'EN', '#FF7C00'],
    ['Ray', 'Mobula thurstoni', 150, 150, 'EN', '#FF7C00'],
    ['Shark', 'Mustelus manazo', 55, 60, 'EN', '#FF7C00'],
    ['Shark', 'Mustelus mosis', 65, 75, 'NT', '#00A859'],
    ['Ray', 'Neotrygon caeruleopunctata', 30, np.nan, 'NE', '#AAAAAA'],
    ['Shark', 'Odontaspis ferox', 200, 300, 'VU', '#FFD800'],
    ['Ray', 'Pastinachus ater', np.nan, np.nan, 'LC', '#0085C8'],
    ['Ray', 'Pateobatis fai', 110, np.nan, 'VU', '#FFD800'],
    ['Ray', 'Pateobatis jenkinsii', 75, np.nan, 'VU', '#FFD800'],
    ['Shark', 'Prionace glauca', 185, 185, 'NT', '#00A859'],
    ['Shark', 'Pseudoginglymostoma brevicaudatum', 60, 55, 'CR', '#D40000'],
    ['Ray', 'Rhina ancylostoma', np.nan, np.nan, 'CR', '#D40000'],
    ['Ray', 'Rhina ancylostomus', 150, 180, 'CR', '#D40000'],
    ['Ray', 'Rhinobatos austini', np.nan, np.nan, 'DD', '#888888'],
    ['Ray', 'Rhinoptera jayakari', 80, np.nan, 'NE', '#AAAAAA'],
    ['Shark', 'Rhizoprionodon acutus', 55, 60, 'VU', '#FFD800'],
    ['Ray', 'Rhynchobatus australiae', 125, 155, 'CR', '#D40000'],
    ['Shark', 'Sphyrna lewini', 140, 210, 'CR', '#D40000'],
    ['Shark', 'Sphyrna mokarran', 225, 210, 'CR', '#D40000'],
    ['Shark', 'Sphyrna spp', np.nan, np.nan, 'VU', '#FFD800'],
    ['Shark', 'Sphyrna zygaena', 250, 265, 'VU', '#FFD800'],
    ['Shark', 'Squalus mitsukurii', np.nan, np.nan, 'LC', '#0085C8'],
    ['Shark', 'Squalus spp', 90, 85, 'NE', '#AAAAAA'],
    ['Shark', 'Stegostoma tigrinum', 150, 170, 'EN', '#FF7C00'],
    ['Ray', 'Taeniura lymma', 20, np.nan, 'NT', '#00A859'],
    ['Ray', 'Taeniurops meyeni', 100, np.nan, 'VU', '#FFD800'],
    ['Ray', 'Torpedo fuscomaculata', np.nan, np.nan, 'DD', '#888888'],
    ['Shark', 'Triaenodon obesus', 105, 105, 'VU', '#FFD800'],
    ['Ray', 'Urogymnus asperrimus', 90, 100, 'VU', '#FFD800']
]

DF_IUCN = pd.DataFrame(IUCN_VALUES, columns=IUCN_COLUMNS)

IUCN_PALETTE = {
    'CR': '#D40000', # Critically Endangered (Red)
    'EN': '#FF7C00', # Endangered (Orange)
    'VU': '#FFD800', # Vulnerable (Yellow)
    'NT': '#00A859', # Near Threatened (Green)
    'LC': '#0085C8', # Least Concern (Blue)
    'DD': '#888888', # Data Deficient (Gray)
    'NE': '#CCCCCC', # Not Evaluated
}

# ==============================================================================
# Restoration Coordinates & Sites
# ==============================================================================
RESTORATION_COORDS = [
    ['nursery_kirui', -4.77763, 39.19956],
    ['transplanting_kirui_shangani', -4.75601, 39.21939],
    ['transplanting_kirui_corner', -4.77067, 39.21169],
    ['transplanting_kirui_exp', -4.75253, 39.23363],
    ['nursery_kigombe', -5.26431, 39.07310],
    ['transplanting_kigombe_taa', -5.27990, 39.07984],
    ['transplanting_kigome_makome', -5.29569, 39.09755],
    ['nursery_msuka', -4.90274, 39.72391],
    ['transplanting_msuka_panga_punge', -4.87030, 39.80540]
]
DF_RESTORATION_COORDS = pd.DataFrame(RESTORATION_COORDS, columns=['site_name', 'latitude', 'longitude'])


# ==============================================================================
# Helpers: Formatting & Typst Escaping
# ==============================================================================
def typst_escape(value: Any) -> str:
    """Escapes strings for safe inclusion in Typst markup."""
    if value is None or pd.isna(value):
        return ""
    text = str(value)
    # Replace special Typst characters
    for ch in ['\\', '#', '$', '@', '*', '`', '<', '>']:
        text = text.replace(ch, f'\\{ch}')
    # Replace underscores with escaped form
    text = text.replace('_', '\\_')
    return text


def clean_label(value: Any) -> str:
    """Creates a human-readable clean title label from snake_case strings."""
    if value is None or pd.isna(value):
        return ""
    text = str(value).replace('_', ' ').strip()
    return text.title()


def find_typst_binary() -> Optional[str]:
    """Finds the Typst binary on system PATH or common macOS/Linux locations."""
    # Check PATH first
    path_binary = shutil.which("typst")
    if path_binary:
        return path_binary
        
    candidates = [
        "/opt/homebrew/bin/typst",
        "/usr/local/bin/typst",
        os.path.expanduser("~/.cargo/bin/typst"),
        os.path.expanduser("~/.local/bin/typst"),
        "/opt/local/bin/typst",
        "/usr/bin/typst",
    ]
    for c in candidates:
        if os.path.isfile(c) and os.access(c, os.X_OK):
            return c
    return None


def check_typst_available() -> Tuple[bool, str]:
    """Checks whether Typst CLI or Python package is available."""
    # 1. Try python library
    try:
        import typst
        return True, "python-typst"
    except ImportError:
        pass
        
    # 2. Try CLI binary
    binary = find_typst_binary()
    if binary:
        return True, binary
        
    return False, "Not found"


def compile_typst(typst_file: Path, output_pdf: Path) -> Tuple[bool, Optional[str]]:
    """
    Compiles a Typst source file to PDF.
    Returns (success_bool, error_message_or_none).
    """
    # 1. Try Python typst library
    try:
        import typst
        typst.compile(str(typst_file), output=str(output_pdf))
        if output_pdf.exists() and output_pdf.stat().st_size > 0:
            return True, None
    except ImportError:
        pass
    except Exception as e:
        return False, f"Python typst compile error: {str(e)}"

    # 2. Try CLI binary
    binary = find_typst_binary()
    if binary:
        try:
            cmd = [binary, "compile", str(typst_file), str(output_pdf)]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0 and output_pdf.exists() and output_pdf.stat().st_size > 0:
                return True, None
            else:
                return False, f"Typst CLI error (code {result.returncode}): {result.stderr or result.stdout}"
        except Exception as e:
            return False, f"Typst execution error: {str(e)}"

    return False, (
        "Typst compiler not found. Please install Typst via `brew install typst` (macOS), "
        "`pip install typst`, or cargo `cargo install --locked typst-cli`."
    )


# ==============================================================================
# Matplotlib Figure Styling and Generators
# ==============================================================================
def setup_mpl_style():
    """Sets professional publication styling for figures."""
    plt.rcParams.update({
        'figure.autolayout': False,
        'figure.dpi': 300,
        'font.sans-serif': ['DejaVu Sans', 'Arial', 'Helvetica', 'Liberation Sans'],
        'font.family': 'sans-serif',
        'font.size': 13,
        'axes.labelsize': 14,
        'axes.titlesize': 16,
        'axes.titleweight': 'bold',
        'axes.labelweight': 'bold',
        'axes.edgecolor': '#cbd5e1',
        'axes.linewidth': 1.2,
        'xtick.labelsize': 12,
        'ytick.labelsize': 12,
        'legend.fontsize': 12,
        'legend.frameon': True,
        'legend.edgecolor': '#e2e8f0',
        'figure.titlesize': 18,
    })


def plot_bony_fishes_figures(df: pd.DataFrame, output_dir: Path) -> Dict[str, Path]:
    """Generates all high-resolution figures for the Bony Fishes poster."""
    setup_mpl_style()
    figures = {}
    
    # --------------------------------------------------------------------------
    # 1. Geographic Distribution Map
    # --------------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(9, 6.5))
    if '_gps_latitude' in df.columns and '_gps_longitude' in df.columns and 'landing_site' in df.columns:
        coords = pd.merge(
            df[['landing_site', '_gps_latitude']].groupby('landing_site').median(),
            df[['landing_site', '_gps_longitude']].groupby('landing_site').median(),
            right_index=True, left_index=True
        )
        counts = df[['landing_site', '_gps_latitude']].groupby('landing_site').count()
        coords = pd.merge(coords, counts, right_index=True, left_index=True)
        coords = coords.rename(columns={'_gps_latitude_x': 'lat', '_gps_longitude': 'lon', '_gps_latitude_y': 'count'}).dropna().reset_index()
        
        if not coords.empty:
            scatter = ax.scatter(
                coords['lon'], coords['lat'],
                s=coords['count'] * 4 + 80,
                c='#0284c7', alpha=0.75, edgecolors='#0369a1', linewidth=1.8, zorder=3
            )
            for _, row in coords.iterrows():
                site_name = clean_label(row['landing_site'])
                ax.annotate(
                    f"{site_name} (n={int(row['count'])})",
                    (row['lon'], row['lat']),
                    textcoords="offset points", xytext=(0, 10), ha='center',
                    fontsize=11, fontweight='bold', color='#0f172a',
                    bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="#94a3b8", alpha=0.85)
                )
            ax.set_xlabel('Longitude (°E)')
            ax.set_ylabel('Latitude (°S)')
            ax.set_title('Landing Sites & Spatial Sampling Density', pad=12)
            ax.grid(True, linestyle='--', alpha=0.4, color='#94a3b8')
        else:
            ax.text(0.5, 0.5, 'No GPS coordinates available', ha='center', va='center')
    else:
        ax.text(0.5, 0.5, 'GPS data not found', ha='center', va='center')
        
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()
    map_path = output_dir / "fig_map.png"
    plt.savefig(map_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    figures['map'] = map_path

    # --------------------------------------------------------------------------
    # 2. Sampling Effort Over Time
    # --------------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(9, 5.5))
    if 'today' in df.columns:
        df_time = df.copy()
        df_time['today'] = pd.to_datetime(df_time['today'], errors='coerce')
        df_time = df_time.dropna(subset=['today'])
        if not df_time.empty:
            # Group by month and site
            df_time['period'] = df_time['today'].dt.to_period('M')
            effort_time = df_time.groupby(['period', 'landing_site'])['_uuid'].count().unstack(fill_value=0)
            
            # Use colormap for landing sites
            colors = plt.cm.tab10(np.linspace(0, 1, max(1, len(effort_time.columns))))
            effort_time.plot(kind='bar', stacked=True, ax=ax, color=colors, width=0.85, edgecolor='#334155', linewidth=0.5)
            
            ax.set_xlabel('Sampling Month')
            ax.set_ylabel('Number of Landings')
            ax.set_title('Sampling Effort Over Time by Landing Site', pad=12)
            
            # Format x labels
            labels = [p.strftime('%b %Y') for p in effort_time.index]
            ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=10)
            ax.legend(title='Landing Site', bbox_to_anchor=(1.02, 1), loc='upper left', frameon=True)
            ax.grid(axis='y', linestyle='--', alpha=0.4)
        else:
            ax.text(0.5, 0.5, 'No valid dates for effort timeline', ha='center', va='center')
    plt.tight_layout()
    effort_path = output_dir / "fig_effort.png"
    plt.savefig(effort_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    figures['effort'] = effort_path

    # --------------------------------------------------------------------------
    # 3. Landings by Boat Type
    # --------------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(8.5, 5))
    if 'boat_type' in df.columns:
        boat_type = df.groupby('boat_type')['_uuid'].count().sort_values(ascending=True)
        if not boat_type.empty:
            y_labels = [clean_label(x) for x in boat_type.index]
            bars = ax.barh(y_labels, boat_type.values, color='#0284c7', edgecolor='#0369a1', height=0.65)
            for bar in bars:
                w = bar.get_width()
                ax.text(w + max(boat_type.values) * 0.015, bar.get_y() + bar.get_height()/2, f"{int(w):,}",
                        va='center', fontsize=11, fontweight='bold', color='#1e293b')
            ax.set_xlabel('Number of Landings Recorded')
            ax.set_title('Landings by Type of Fishing Vessel', pad=12)
            ax.grid(axis='x', linestyle='--', alpha=0.4)
            ax.set_xlim(0, max(boat_type.values) * 1.15)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()
    boat_path = output_dir / "fig_boat.png"
    plt.savefig(boat_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    figures['boat'] = boat_path

    # --------------------------------------------------------------------------
    # 4. Landings by Species Group
    # --------------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    if 'group_catch' in df.columns and 'landing_site' in df.columns:
        site_group = df.groupby(['landing_site', 'group_catch'])['_uuid'].count().unstack(fill_value=0)
        if not site_group.empty:
            palette = ['#0d9488', '#f59e0b', '#0284c7', '#ec4899', '#8b5cf6']
            colors = palette[:len(site_group.columns)]
            x_labels = [clean_label(x) for x in site_group.index]
            site_group.index = x_labels
            site_group.plot(kind='bar', stacked=True, ax=ax, color=colors, edgecolor='#334155', linewidth=0.5, width=0.7)
            
            clean_cols = [clean_label(c) for c in site_group.columns]
            ax.legend(clean_cols, title='Species Group', frameon=True)
            ax.set_xlabel('Landing Site')
            ax.set_ylabel('Number of Landings')
            ax.set_title('Landings Composition by Species Group & Site', pad=12)
            plt.xticks(rotation=30, ha='right')
            ax.grid(axis='y', linestyle='--', alpha=0.4)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()
    group_path = output_dir / "fig_species_group.png"
    plt.savefig(group_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    figures['species_group'] = group_path

    # --------------------------------------------------------------------------
    # 5. Landings by Gear Type
    # --------------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(8.5, 5))
    if 'gear_type' in df.columns:
        s = pd.Series(df['gear_type'].dropna()).astype(str)
        exploded = s.str.split(expand=False).explode()
        gear_counts = exploded.value_counts().head(8).sort_values(ascending=True)
        if not gear_counts.empty:
            y_labels = [clean_label(x) for x in gear_counts.index]
            bars = ax.barh(y_labels, gear_counts.values, color='#0d9488', edgecolor='#115e59', height=0.65)
            for bar in bars:
                w = bar.get_width()
                ax.text(w + max(gear_counts.values) * 0.015, bar.get_y() + bar.get_height()/2, f"{int(w):,}",
                        va='center', fontsize=11, fontweight='bold', color='#1e293b')
            ax.set_xlabel('Number of Records')
            ax.set_title('Landings by Fishing Gear Type', pad=12)
            ax.grid(axis='x', linestyle='--', alpha=0.4)
            ax.set_xlim(0, max(gear_counts.values) * 1.15)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()
    gear_path = output_dir / "fig_gear.png"
    plt.savefig(gear_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    figures['gear'] = gear_path

    # --------------------------------------------------------------------------
    # 6. Effort by Vessel & Site
    # --------------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    if {'people', 'boats_landed', 'landing_site', 'boat_type'}.issubset(df.columns):
        try:
            mean_ppl = df.groupby(['today', 'landing_site', 'boat_type'])['people'].mean()
            sum_ppl = df.groupby(['today', 'landing_site', 'boat_type'])['people'].sum()
            med_boats = df.groupby(['today', 'landing_site', 'boat_type'])['boats_landed'].median()
            effort_raw = sum_ppl + mean_ppl * med_boats
            
            effort_df = effort_raw.reset_index(name='effort')
            effort_grouped = effort_df.groupby(['landing_site', 'boat_type'])['effort'].sum().unstack(fill_value=0)
            
            if not effort_grouped.empty:
                effort_grouped.index = [clean_label(x) for x in effort_grouped.index]
                clean_boats = [clean_label(b) for b in effort_grouped.columns]
                colors = plt.cm.Spectral(np.linspace(0.1, 0.9, len(effort_grouped.columns)))
                effort_grouped.plot(kind='bar', stacked=True, ax=ax, color=colors, edgecolor='#334155', linewidth=0.5)
                ax.legend(clean_boats, title='Vessel Type', bbox_to_anchor=(1.02, 1), loc='upper left')
                ax.set_xlabel('Landing Site')
                ax.set_ylabel('Total Effort Index (crew x boats)')
                ax.set_title('Cumulative Fishing Effort by Vessel Type & Site', pad=12)
                plt.xticks(rotation=30, ha='right')
                ax.grid(axis='y', linestyle='--', alpha=0.4)
        except Exception as e:
            ax.text(0.5, 0.5, f'Effort calculation: {str(e)}', ha='center', va='center')
    else:
        ax.text(0.5, 0.5, 'Effort parameters unavailable', ha='center', va='center')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()
    vessel_path = output_dir / "fig_vessel_effort.png"
    plt.savefig(vessel_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    figures['vessel_effort'] = vessel_path

    # --------------------------------------------------------------------------
    # 7. CPUE Trends
    # --------------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(9, 5.5))
    if {'weight_catch', 'people', 'fishing_duration', 'landing_site'}.issubset(df.columns):
        df_cpue = df.copy()
        duration = pd.to_numeric(df_cpue['fishing_duration'], errors='coerce')
        people = pd.to_numeric(df_cpue['people'], errors='coerce')
        weight = pd.to_numeric(df_cpue['weight_catch'], errors='coerce')
        
        valid = (duration > 0) & (people > 0) & (weight >= 0)
        df_cpue = df_cpue[valid].copy()
        df_cpue['CPUE'] = weight / people / duration
        df_cpue.replace([np.inf, -np.inf], np.nan, inplace=True)
        df_cpue['today'] = pd.to_datetime(df_cpue['today'], errors='coerce')
        df_cpue = df_cpue.dropna(subset=['today', 'CPUE'])
        
        # Aggregate daily mean CPUE per site
        cpue_agg = df_cpue.groupby(['today', 'landing_site'])['CPUE'].mean().reset_index()
        
        if not cpue_agg.empty:
            sites = cpue_agg['landing_site'].unique()
            colors = plt.cm.tab10(np.linspace(0, 1, max(1, len(sites))))
            
            for i, site in enumerate(sites):
                site_data = cpue_agg[cpue_agg['landing_site'] == site].sort_values('today')
                site_label = clean_label(site)
                ax.scatter(site_data['today'], site_data['CPUE'], color=colors[i], alpha=0.55, s=35, label=site_label)
                
                # Fit linear regression line if sufficient points
                if len(site_data) > 5:
                    x_numeric = (site_data['today'] - site_data['today'].min()).dt.days.values
                    y_vals = site_data['CPUE'].values
                    m, b = np.polyfit(x_numeric, y_vals, 1)
                    ax.plot(site_data['today'], m * x_numeric + b, color=colors[i], linewidth=2.5)

            ax.set_xlabel('Date')
            ax.set_ylabel('CPUE (kg / fisher / hour)')
            ax.set_title('Catch Per Unit Effort (CPUE) Trends & Linear Fits', pad=12)
            ax.grid(True, linestyle='--', alpha=0.4)
            ax.legend(title='Landing Site', bbox_to_anchor=(1.02, 1), loc='upper left')
        else:
            ax.text(0.5, 0.5, 'Insufficient data to compute CPUE', ha='center', va='center')
    else:
        ax.text(0.5, 0.5, 'CPUE columns missing', ha='center', va='center')
        
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()
    cpue_path = output_dir / "fig_cpue.png"
    plt.savefig(cpue_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    figures['cpue'] = cpue_path

    return figures


def plot_sharks_rays_figures(df: pd.DataFrame, output_dir: Path) -> Dict[str, Path]:
    """Generates all high-resolution figures for the Sharks and Rays poster."""
    setup_mpl_style()
    figures = {}
    
    # Merge with IUCN dataset
    df_merged = df.copy()
    if 'Scientific_name' in df_merged.columns:
        df_merged = pd.merge(df_merged, DF_IUCN, on='Scientific_name', how='left')

    # --------------------------------------------------------------------------
    # 1. Geographic Map (Landing Sites and Markets)
    # --------------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(9, 6.5))
    if '_gps_latitude' in df_merged.columns and '_gps_longitude' in df_merged.columns:
        loc_col = 'landing_site' if 'landing_site' in df_merged.columns else 'market'
        coords = pd.merge(
            df_merged[[loc_col, '_gps_latitude']].groupby(loc_col).median(),
            df_merged[[loc_col, '_gps_longitude']].groupby(loc_col).median(),
            right_index=True, left_index=True
        )
        counts = df_merged[[loc_col, '_gps_latitude']].groupby(loc_col).count()
        coords = pd.merge(coords, counts, right_index=True, left_index=True)
        coords = coords.rename(columns={'_gps_latitude_x': 'lat', '_gps_longitude': 'lon', '_gps_latitude_y': 'count'}).dropna().reset_index()
        
        if not coords.empty:
            ax.scatter(
                coords['lon'], coords['lat'],
                s=coords['count'] * 6 + 100,
                c='#ea580c', alpha=0.75, edgecolors='#9a3412', linewidth=1.8, zorder=3
            )
            for _, row in coords.iterrows():
                site_name = clean_label(row[loc_col])
                ax.annotate(
                    f"{site_name} (n={int(row['count'])})",
                    (row['lon'], row['lat']),
                    textcoords="offset points", xytext=(0, 10), ha='center',
                    fontsize=11, fontweight='bold', color='#0f172a',
                    bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="#94a3b8", alpha=0.85)
                )
            ax.set_xlabel('Longitude (°E)')
            ax.set_ylabel('Latitude (°S)')
            ax.set_title('Elasmobranch Landing Sites & Monitoring Locations', pad=12)
            ax.grid(True, linestyle='--', alpha=0.4)
        else:
            ax.text(0.5, 0.5, 'No coordinates available', ha='center', va='center')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()
    map_path = output_dir / "fig_map.png"
    plt.savefig(map_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    figures['map'] = map_path

    # --------------------------------------------------------------------------
    # 2. Top Landed Species by IUCN Status
    # --------------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(9, 6.5))
    if 'Scientific_name' in df_merged.columns and 'Red_List_Status' in df_merged.columns:
        sp_counts = df_merged.groupby(['Scientific_name', 'Red_List_Status'])['_uuid'].count().reset_index()
        top_sp = sp_counts.sort_values(by='_uuid', ascending=True).tail(12)
        
        if not top_sp.empty:
            colors = [IUCN_PALETTE.get(status, '#888888') for status in top_sp['Red_List_Status']]
            bars = ax.barh(top_sp['Scientific_name'], top_sp['_uuid'], color=colors, edgecolor='#1e293b', height=0.65)
            
            for bar, status in zip(bars, top_sp['Red_List_Status']):
                w = bar.get_width()
                ax.text(w + max(top_sp['_uuid']) * 0.015, bar.get_y() + bar.get_height()/2,
                        f"{int(w):,} [{status}]", va='center', fontsize=11, fontweight='bold', color='#0f172a')
            
            ax.set_xlabel('Number of Landings Recorded')
            ax.set_title('Top Landed Shark & Ray Species (Color = IUCN Status)', pad=12)
            ax.grid(axis='x', linestyle='--', alpha=0.4)
            ax.set_xlim(0, max(top_sp['_uuid']) * 1.25)
            
            # Custom IUCN legend
            from matplotlib.patches import Patch
            legend_elements = [
                Patch(facecolor=IUCN_PALETTE['CR'], edgecolor='#333', label='Critically Endangered (CR)'),
                Patch(facecolor=IUCN_PALETTE['EN'], edgecolor='#333', label='Endangered (EN)'),
                Patch(facecolor=IUCN_PALETTE['VU'], edgecolor='#333', label='Vulnerable (VU)'),
                Patch(facecolor=IUCN_PALETTE['NT'], edgecolor='#333', label='Near Threatened (NT)'),
                Patch(facecolor=IUCN_PALETTE['LC'], edgecolor='#333', label='Least Concern (LC)'),
            ]
            ax.legend(handles=legend_elements, loc='lower right', frameon=True, fontsize=10)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()
    species_path = output_dir / "fig_species.png"
    plt.savefig(species_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    figures['species'] = species_path

    # --------------------------------------------------------------------------
    # 3. IUCN Red List Status Composition
    # --------------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(8.5, 5))
    if 'Red_List_Status' in df_merged.columns:
        iucn_order = ['CR', 'EN', 'VU', 'NT', 'LC', 'DD', 'NE']
        counts = df_merged['Red_List_Status'].value_counts()
        ordered_counts = [counts.get(s, 0) for s in iucn_order if counts.get(s, 0) > 0]
        ordered_statuses = [s for s in iucn_order if counts.get(s, 0) > 0]
        
        if ordered_counts:
            colors = [IUCN_PALETTE.get(s, '#888888') for s in ordered_statuses]
            bars = ax.bar(ordered_statuses, ordered_counts, color=colors, edgecolor='#1e293b', width=0.65)
            for bar in bars:
                h = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2, h + max(ordered_counts)*0.015, f"{int(h):,}",
                        ha='center', va='bottom', fontsize=11, fontweight='bold')
            ax.set_ylabel('Number of Landings')
            ax.set_xlabel('IUCN Red List Category')
            ax.set_title('Catch Distribution by Extinction Risk Category', pad=12)
            ax.grid(axis='y', linestyle='--', alpha=0.4)
            ax.set_ylim(0, max(ordered_counts) * 1.15)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()
    iucn_path = output_dir / "fig_iucn.png"
    plt.savefig(iucn_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    figures['iucn'] = iucn_path

    # --------------------------------------------------------------------------
    # 4. Maturity Ratio Distribution
    # --------------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(8.5, 5))
    df_mat = df_merged.copy()
    df_mat['maturity'] = np.nan
    
    # Calculate maturity for rays
    ray_male = (df_mat['sex'] == 'Male') & (df_mat['Shark_or_Ray'] == 'Ray')
    if 'disc_width' in df_mat.columns and 'Male_size_at_maturity_cm_DW_TL' in df_mat.columns:
        df_mat.loc[ray_male, 'maturity'] = pd.to_numeric(df_mat.loc[ray_male, 'disc_width'], errors='coerce') / pd.to_numeric(df_mat.loc[ray_male, 'Male_size_at_maturity_cm_DW_TL'], errors='coerce')
        
    ray_female = (df_mat['sex'] == 'Female') & (df_mat['Shark_or_Ray'] == 'Ray')
    if 'disc_width' in df_mat.columns and 'Female_size_at_maturity_cm_DW_TL' in df_mat.columns:
        df_mat.loc[ray_female, 'maturity'] = pd.to_numeric(df_mat.loc[ray_female, 'disc_width'], errors='coerce') / pd.to_numeric(df_mat.loc[ray_female, 'Female_size_at_maturity_cm_DW_TL'], errors='coerce')
        
    # Calculate maturity for sharks
    shark_male = (df_mat['sex'] == 'Male') & (df_mat['Shark_or_Ray'] == 'Shark')
    if 'total_length' in df_mat.columns and 'Male_size_at_maturity_cm_DW_TL' in df_mat.columns:
        df_mat.loc[shark_male, 'maturity'] = pd.to_numeric(df_mat.loc[shark_male, 'total_length'], errors='coerce') / pd.to_numeric(df_mat.loc[shark_male, 'Male_size_at_maturity_cm_DW_TL'], errors='coerce')
        
    shark_female = (df_mat['sex'] == 'Female') & (df_mat['Shark_or_Ray'] == 'Shark')
    if 'total_length' in df_mat.columns and 'Female_size_at_maturity_cm_DW_TL' in df_mat.columns:
        df_mat.loc[shark_female, 'maturity'] = pd.to_numeric(df_mat.loc[shark_female, 'total_length'], errors='coerce') / pd.to_numeric(df_mat.loc[shark_female, 'Female_size_at_maturity_cm_DW_TL'], errors='coerce')
        
    valid_mat = df_mat['maturity'].dropna()
    valid_mat = valid_mat[(valid_mat >= 0) & (valid_mat <= 3)]
    
    if not valid_mat.empty:
        bins = np.linspace(0, 3, 16)
        n, _, patches = ax.hist(valid_mat, bins=bins, color='#0284c7', edgecolor='white', linewidth=1.2)
        # Color immature (< 1.0) red, mature (>= 1.0) green
        for p, b in zip(patches, bins[:-1]):
            if b < 1.0:
                p.set_facecolor('#ef4444')
            else:
                p.set_facecolor('#10b981')
                
        ax.axvline(1.0, color='black', linestyle='--', linewidth=2.5, label='Maturity Threshold (1.0)')
        immature_pct = (valid_mat < 1.0).mean() * 100
        ax.text(0.45, max(n)*0.85, f"Immature:\n{immature_pct:.1f}%", fontsize=12, fontweight='bold', color='#b91c1c')
        ax.text(1.5, max(n)*0.85, f"Mature Adult:\n{100-immature_pct:.1f}%", fontsize=12, fontweight='bold', color='#047857')
        
        ax.set_xlabel('Maturity Ratio (Body Size / Size at Maturity)')
        ax.set_ylabel('Number of Individuals')
        ax.set_title('Proportion of Landed Immature vs. Mature Specimens', pad=12)
        ax.grid(axis='y', linestyle='--', alpha=0.4)
        ax.legend(loc='upper right')
    else:
        ax.text(0.5, 0.5, 'No maturity measurements available', ha='center', va='center')
        
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()
    mat_path = output_dir / "fig_maturity.png"
    plt.savefig(mat_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    figures['maturity'] = mat_path

    # --------------------------------------------------------------------------
    # 5. Fishing Gear Utilization
    # --------------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(8.5, 5))
    gears = [
        'gear_type/basket_traps', 'gear_type/hook_line', 'gear_type/spear_gun',
        'gear_type/beach_seines', 'gear_type/ring_nets', 'gear_type/gill_nets_3',
        'gear_type/gill_nets_6', 'gear_type/longline', 'gear_type/reef_seine_set_net',
        'gear_type/drift_net'
    ]
    gear_data = []
    for g in gears:
        if g in df_merged.columns:
            cnt = (pd.to_numeric(df_merged[g], errors='coerce') == 1).sum()
            if cnt > 0:
                name = clean_label(g.replace('gear_type/', ''))
                gear_data.append((name, cnt))
                
    if gear_data:
        gear_data.sort(key=lambda x: x[1])
        names, vals = zip(*gear_data)
        bars = ax.barh(names, vals, color='#0d9488', edgecolor='#115e59', height=0.65)
        for bar in bars:
            w = bar.get_width()
            ax.text(w + max(vals) * 0.015, bar.get_y() + bar.get_height()/2, f"{int(w):,}",
                    va='center', fontsize=11, fontweight='bold', color='#1e293b')
        ax.set_xlabel('Number of Landings Involving Gear')
        ax.set_title('Fishing Gear Types Capturing Elasmobranchs', pad=12)
        ax.grid(axis='x', linestyle='--', alpha=0.4)
        ax.set_xlim(0, max(vals) * 1.15)
    else:
        ax.text(0.5, 0.5, 'No specific gear flags recorded', ha='center', va='center')
        
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()
    gear_path = output_dir / "fig_gear.png"
    plt.savefig(gear_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    figures['gear'] = gear_path

    # --------------------------------------------------------------------------
    # 6. Targeted vs Bycatch Donut Chart
    # --------------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(6.5, 5))
    if 'targeted' in df_merged.columns:
        targeted_counts = df_merged['targeted'].value_counts()
        if not targeted_counts.empty:
            labels = [clean_label(x) for x in targeted_counts.index]
            colors = ['#f59e0b', '#0284c7', '#94a3b8'][:len(targeted_counts)]
            wedges, texts, autotexts = ax.pie(
                targeted_counts.values,
                labels=labels,
                autopct='%1.1f%%',
                startangle=140,
                colors=colors,
                wedgeprops=dict(width=0.45, edgecolor='white', linewidth=2),
                pctdistance=0.75
            )
            for at in autotexts:
                at.set_color('white')
                at.set_fontweight('bold')
                at.set_fontsize(12)
            for t in texts:
                t.set_fontsize(12)
                t.set_fontweight('bold')
            ax.set_title('Targeted vs. Incidental Bycatch', pad=12)
    plt.tight_layout()
    targeted_path = output_dir / "fig_targeted.png"
    plt.savefig(targeted_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    figures['targeted'] = targeted_path

    # --------------------------------------------------------------------------
    # 7. Sex Ratio Distribution
    # --------------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(8.5, 5))
    if 'sex' in df_merged.columns and 'Scientific_name' in df_merged.columns:
        females = df_merged[df_merged['sex'] == 'Female'].groupby('Scientific_name')['_uuid'].count()
        males = df_merged[df_merged['sex'] == 'Male'].groupby('Scientific_name')['_uuid'].count()
        sex_ratio = (females / males).dropna()
        sex_ratio = sex_ratio[(sex_ratio >= 0) & (sex_ratio <= 3)]
        
        if not sex_ratio.empty:
            bins = np.linspace(0, 3, 16)
            ax.hist(sex_ratio, bins=bins, color='#ec4899', edgecolor='white', linewidth=1.2)
            ax.axvline(1.0, color='black', linestyle='--', linewidth=2.5, label='1:1 Parity')
            ax.set_xlabel('Sex Ratio (Female / Male)')
            ax.set_ylabel('Number of Species')
            ax.set_title('Sex Ratio Distribution Across Landed Species', pad=12)
            ax.grid(axis='y', linestyle='--', alpha=0.4)
            ax.legend()
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()
    sex_path = output_dir / "fig_sex_ratio.png"
    plt.savefig(sex_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    figures['sex_ratio'] = sex_path

    # --------------------------------------------------------------------------
    # 8. Sampling Effort Over Time
    # --------------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(9, 5))
    date_col = 'date' if 'date' in df_merged.columns else ('today' if 'today' in df_merged.columns else None)
    if date_col:
        df_time = df_merged.copy()
        df_time['dt'] = pd.to_datetime(df_time[date_col], errors='coerce')
        df_time = df_time.dropna(subset=['dt'])
        if not df_time.empty:
            df_time['period'] = df_time['dt'].dt.to_period('M')
            loc_col = 'landing_site' if 'landing_site' in df_time.columns else 'market'
            effort_time = df_time.groupby(['period', loc_col])['_uuid'].count().unstack(fill_value=0)
            
            colors = plt.cm.tab10(np.linspace(0, 1, max(1, len(effort_time.columns))))
            effort_time.plot(kind='bar', stacked=True, ax=ax, color=colors, width=0.85, edgecolor='#334155', linewidth=0.5)
            labels = [p.strftime('%b %Y') for p in effort_time.index]
            ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=10)
            ax.set_xlabel('Month')
            ax.set_ylabel('Number of Landings')
            ax.set_title('Monthly Elasmobranch Monitoring Effort', pad=12)
            ax.legend(title='Location', bbox_to_anchor=(1.02, 1), loc='upper left', frameon=True)
            ax.grid(axis='y', linestyle='--', alpha=0.4)
    plt.tight_layout()
    effort_path = output_dir / "fig_effort.png"
    plt.savefig(effort_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    figures['effort'] = effort_path

    return figures


def plot_restoration_figures(df: pd.DataFrame, output_dir: Path) -> Dict[str, Path]:
    """Generates all high-resolution figures for the Coral Reef Restoration poster."""
    setup_mpl_style()
    figures = {}
    
    # Ensure coordinates exist and prepare numeric columns
    df_plot = df.copy()
    if 'latitude' not in df_plot.columns or 'longitude' not in df_plot.columns:
        if 'site_name' in df_plot.columns:
            df_plot = pd.merge(df_plot, DF_RESTORATION_COORDS, on='site_name', how='left')

    # Convert numeric columns
    num_cols = [
        'total_fragments_transplanted_to_date',
        'total_fragments_in_nursery_to_date',
        'total_reef_starts_deployed_to_date',
        'total_tables_in_nursery_to_date',
        'total_number_of_fragments_transplanted',
        'total_fragments_on_reef_stars_to_date',
        'total_fragments_on_fence_wires_to_date',
        'total_fragments_on_clips_to_date'
    ]
    for nc in num_cols:
        if nc in df_plot.columns:
            df_plot[nc] = pd.to_numeric(df_plot[nc], errors='coerce')

    # Date handling
    date_col = 'datetime' if 'datetime' in df_plot.columns else ('date' if 'date' in df_plot.columns else ('Date' if 'Date' in df_plot.columns else None))
    if date_col and not df_plot.empty:
        df_plot['dt'] = pd.to_datetime(df_plot[date_col], errors='coerce')
    else:
        df_plot['dt'] = pd.NaT

    # 1. Map of Restoration & Nursery Sites
    fig, ax = plt.subplots(figsize=(8, 5.5))
    if not df_plot.empty and 'latitude' in df_plot.columns and 'longitude' in df_plot.columns and 'site_name' in df_plot.columns:
        cols_for_agg = ['site_name', 'latitude', 'longitude']
        if 'site_type' in df_plot.columns:
            cols_for_agg.append('site_type')
        
        site_agg = df_plot.groupby(cols_for_agg).agg({
            'total_fragments_in_nursery_to_date': 'max',
            'total_fragments_transplanted_to_date': 'max',
            '_uuid': 'count'
        }).reset_index()
        
        if not site_agg.empty:
            for _, r in site_agg.iterrows():
                is_nursery = (r.get('site_type') == 'nursery')
                col = '#0d9488' if is_nursery else '#f43f5e'
                val = r.get('total_fragments_in_nursery_to_date') if is_nursery else r.get('total_fragments_transplanted_to_date')
                sz = max(100, min(1200, (float(val) if pd.notna(val) else 100) / 10 + 120))
                
                ax.scatter(r['longitude'], r['latitude'], s=sz, c=col, alpha=0.75, edgecolors='#1e293b', linewidth=1.5, zorder=3)
                label_txt = clean_label(r['site_name'])
                frag_txt = f"{int(val):,} frags" if pd.notna(val) and val > 0 else f"{int(r['_uuid'])} records"
                ax.annotate(
                    f"{label_txt}\n({frag_txt})",
                    (r['longitude'], r['latitude']),
                    textcoords="offset points", xytext=(0, 8), ha='center',
                    fontsize=9, fontweight='bold', color='#0f172a',
                    bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="#94a3b8", alpha=0.85)
                )
            
            from matplotlib.lines import Line2D
            legend_elements = [
                Line2D([0], [0], marker='o', color='w', label='Nursery Site', markerfacecolor='#0d9488', markersize=11, markeredgecolor='#1e293b'),
                Line2D([0], [0], marker='o', color='w', label='Transplanting Site', markerfacecolor='#f43f5e', markersize=11, markeredgecolor='#1e293b'),
            ]
            ax.legend(handles=legend_elements, loc='lower right', frameon=True, fontsize=9)
            ax.set_xlabel('Longitude (°E)', fontsize=11)
            ax.set_ylabel('Latitude (°S)', fontsize=11)
            ax.set_title('Coral Nurseries & Outplanting Reef Sites', pad=10, fontsize=13)
            ax.grid(True, linestyle='--', alpha=0.4)
        else:
            ax.text(0.5, 0.5, 'No site coordinates available', ha='center', va='center')
    else:
        ax.text(0.5, 0.5, 'No records for current filters', ha='center', va='center')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()
    map_p = output_dir / "fig_map.png"
    plt.savefig(map_p, dpi=300, bbox_inches='tight')
    plt.close(fig)
    figures['map'] = map_p

    # 2. Cumulative Area Restored Over Time
    fig, ax = plt.subplots(figsize=(8, 4.8))
    if not df_plot.empty and 'dt' in df_plot.columns and 'total_fragments_transplanted_to_date' in df_plot.columns and 'project_site' in df_plot.columns:
        valid_df = df_plot.dropna(subset=['dt', 'total_fragments_transplanted_to_date']).sort_values('dt')
        if not valid_df.empty:
            for site in valid_df['project_site'].dropna().unique():
                sdf = valid_df[valid_df['project_site'] == site].copy()
                sdf['area_ha'] = (sdf['total_fragments_transplanted_to_date'] / 2) / 1e4
                sdf['area_ha_cum'] = sdf['area_ha'].cummax()
                ax.plot(sdf['dt'], sdf['area_ha_cum'], marker='o', markersize=4, linewidth=2.2, label=clean_label(site))
            ax.set_xlabel('Date', fontsize=11)
            ax.set_ylabel('Cumulative Area (ha)', fontsize=11)
            ax.set_title('Progressive Reef Area Restored Over Time (ha)', pad=10, fontsize=13)
            ax.grid(True, linestyle='--', alpha=0.4)
            ax.legend(title='Project Area', frameon=True, fontsize=9)
        else:
            ax.text(0.5, 0.5, 'No time-series transplantation data', ha='center', va='center')
    else:
        ax.text(0.5, 0.5, 'No records for current filters', ha='center', va='center')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()
    area_p = output_dir / "fig_area_restored.png"
    plt.savefig(area_p, dpi=300, bbox_inches='tight')
    plt.close(fig)
    figures['area_restored'] = area_p

    # 3. Field Activity Effort
    fig, axes = plt.subplots(2, 2, figsize=(8.5, 6))
    act_map = [
        ('select_activity/fragmentation', 'Fragmentation', '#0284c7'),
        ('select_activity/transplantation', 'Transplantation', '#f43f5e'),
        ('select_activity/monitoring', 'Monitoring', '#0d9488'),
        ('select_activity/cleaning_and_maintaining', 'Nursery Cleaning', '#f59e0b')
    ]
    for idx, (col_name, title, bar_col) in enumerate(act_map):
        ax_curr = axes[idx // 2, idx % 2]
        if not df_plot.empty and col_name in df_plot.columns and 'project_site' in df_plot.columns:
            act_df = df_plot[df_plot[col_name] == 1]
            if not act_df.empty:
                counts = act_df.groupby('project_site')['_uuid'].count()
                labels = [clean_label(x) for x in counts.index]
                bars = ax_curr.bar(labels, counts.values, color=bar_col, edgecolor='#1e293b', width=0.55)
                for b in bars:
                    h = b.get_height()
                    ax_curr.text(b.get_x() + b.get_width()/2, h + max(counts.values)*0.02, f"{int(h)}",
                                 ha='center', va='bottom', fontsize=9, fontweight='bold')
                ax_curr.set_title(title, fontsize=11, pad=5)
                ax_curr.set_ylabel('Field Days', fontsize=9)
                ax_curr.grid(axis='y', linestyle='--', alpha=0.35)
                ax_curr.set_ylim(0, max(counts.values) * 1.25 if len(counts) > 0 else 10)
            else:
                ax_curr.text(0.5, 0.5, '0 days', ha='center', va='center')
                ax_curr.set_title(title, fontsize=11)
        else:
            ax_curr.text(0.5, 0.5, 'No records', ha='center', va='center')
            ax_curr.set_title(title, fontsize=11)
        ax_curr.spines['top'].set_visible(False)
        ax_curr.spines['right'].set_visible(False)
    plt.suptitle('Field Operational Days by Restoration Activity', fontsize=13, fontweight='bold', y=0.98)
    plt.tight_layout()
    act_p = output_dir / "fig_activities.png"
    plt.savefig(act_p, dpi=300, bbox_inches='tight')
    plt.close(fig)
    figures['activities'] = act_p

    # 4. Cumulative Fragments by Substrate Type
    fig, ax = plt.subplots(figsize=(8, 4.8))
    sub_cols = [
        ('total_fragments_on_reef_stars_to_date', 'Reef Stars', '#f59e0b'),
        ('total_fragments_on_fence_wires_to_date', 'Fence Wires', '#0284c7'),
        ('total_fragments_on_clips_to_date', 'Coral Clips', '#0d9488')
    ]
    has_sub = False
    if not df_plot.empty and 'dt' in df_plot.columns:
        valid_time = df_plot.dropna(subset=['dt']).sort_values('dt')
        for cname, label, clr in sub_cols:
            if cname in valid_time.columns:
                series = valid_time.dropna(subset=[cname])
                if not series.empty:
                    has_sub = True
                    cum_max = series[cname].cummax()
                    ax.plot(series['dt'], cum_max, marker='s', markersize=3.5, linewidth=2.2, color=clr, label=label)
    if has_sub:
        ax.set_xlabel('Date', fontsize=11)
        ax.set_ylabel('Outplanted Fragments', fontsize=11)
        ax.set_title('Outplanted Corals by Artificial Substrate Type', pad=10, fontsize=13)
        ax.grid(True, linestyle='--', alpha=0.4)
        ax.legend(title='Substrate Type', frameon=True, fontsize=9)
    else:
        ax.text(0.5, 0.5, 'No substrate counts recorded', ha='center', va='center')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()
    sub_p = output_dir / "fig_substrate.png"
    plt.savefig(sub_p, dpi=300, bbox_inches='tight')
    plt.close(fig)
    figures['substrate'] = sub_p

    # 5. Session Outplanting Output
    fig, ax = plt.subplots(figsize=(8, 4.8))
    if not df_plot.empty and 'dt' in df_plot.columns and 'total_number_of_fragments_transplanted' in df_plot.columns and 'project_site' in df_plot.columns:
        valid_sess = df_plot.dropna(subset=['dt', 'total_number_of_fragments_transplanted']).copy()
        if not valid_sess.empty:
            valid_sess['period'] = valid_sess['dt'].dt.to_period('M')
            sess_agg = valid_sess.groupby(['period', 'project_site'])['total_number_of_fragments_transplanted'].sum().unstack(fill_value=0)
            colors = plt.cm.Set2(np.linspace(0, 1, max(1, len(sess_agg.columns))))
            sess_agg.plot(kind='bar', stacked=True, ax=ax, color=colors, width=0.75, edgecolor='#334155', linewidth=0.5)
            labels = [p.strftime('%b %Y') for p in sess_agg.index]
            ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=9)
            ax.set_xlabel('Monitoring Period', fontsize=11)
            ax.set_ylabel('Fragments Outplanted', fontsize=11)
            ax.set_title('Monthly Coral Fragments Outplanted per Site', pad=10, fontsize=13)
            ax.legend(title='Project Site', frameon=True, fontsize=9)
            ax.grid(axis='y', linestyle='--', alpha=0.4)
        else:
            ax.text(0.5, 0.5, 'No session outplanting records', ha='center', va='center')
    else:
        ax.text(0.5, 0.5, 'No records for current filters', ha='center', va='center')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()
    sess_p = output_dir / "fig_session_transplanted.png"
    plt.savefig(sess_p, dpi=300, bbox_inches='tight')
    plt.close(fig)
    figures['session_transplanted'] = sess_p

    # 6. Coral Nursery Stock & Table Capacity
    fig, ax = plt.subplots(figsize=(8, 4.8))
    if not df_plot.empty and 'site_name' in df_plot.columns and 'total_fragments_in_nursery_to_date' in df_plot.columns:
        nursery_df = df_plot[df_plot['site_type'] == 'nursery'] if 'site_type' in df_plot.columns else df_plot
        if not nursery_df.empty:
            nurs_agg = nursery_df.groupby('site_name')['total_fragments_in_nursery_to_date'].max().dropna().sort_values(ascending=True)
            if not nurs_agg.empty:
                y_labels = [clean_label(x) for x in nurs_agg.index]
                bars = ax.barh(y_labels, nurs_agg.values, color='#0d9488', edgecolor='#115e59', height=0.55)
                for b in bars:
                    w = b.get_width()
                    ax.text(w + max(nurs_agg.values)*0.015, b.get_y() + b.get_height()/2, f"{int(w):,}",
                            va='center', fontsize=10, fontweight='bold', color='#1e293b')
                ax.set_xlabel('Active Fragments in Nursery', fontsize=11)
                ax.set_title('Coral Stock Capacity Across Mid-Water Nurseries', pad=10, fontsize=13)
                ax.grid(axis='x', linestyle='--', alpha=0.4)
                ax.set_xlim(0, max(nurs_agg.values) * 1.25)
            else:
                ax.text(0.5, 0.5, 'Nursery fragments not reported', ha='center', va='center')
        else:
            ax.text(0.5, 0.5, 'No nursery records', ha='center', va='center')
    else:
        ax.text(0.5, 0.5, 'No records for current filters', ha='center', va='center')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()
    nurs_p = output_dir / "fig_nursery_stock.png"
    plt.savefig(nurs_p, dpi=300, bbox_inches='tight')
    plt.close(fig)
    figures['nursery_stock'] = nurs_p

    return figures


# ==============================================================================
# Typst Template Engine
# ==============================================================================
TEMPLATES_DIR = (Path(__file__).resolve().parent / "templates") if '__file__' in globals() else Path("templates")

def load_and_fill_template(template_candidates: list, replacements: Dict[str, str]) -> str:
    """
    Loads a Typst template file from TEMPLATES_DIR, updates all {{PLACEHOLDER}}
    values with dynamic data (dates, landing sites, KPIs, tables), and returns
    the customized Typst markup.
    """
    target_path = None
    for name in template_candidates:
        p = TEMPLATES_DIR / name
        if p.exists():
            target_path = p
            break
            
    if target_path is None:
        raise FileNotFoundError(
            f"Typst template not found in {TEMPLATES_DIR}. Looked for: {template_candidates}. "
            "Please ensure template files exist in the 'templates/' subfolder."
        )

    content = target_path.read_text(encoding='utf-8')
    for key, val in replacements.items():
        content = content.replace(f"{{{{{key}}}}}", str(val))

    return content


def build_bony_fishes_typst(
    df: pd.DataFrame,
    figures: Dict[str, Path],
    metadata: Dict[str, Any],
    logo_filename: str
) -> str:
    """Builds complete Typst markup for the Bony Fishes A0 poster."""
    total_catch = df['weight_catch'].sum() if 'weight_catch' in df.columns else 0.0
    num_records = len(df)
    avg_catch = df['weight_catch'].mean() if ('weight_catch' in df.columns and num_records > 0) else 0.0
    num_sites = len(df['landing_site'].dropna().unique()) if 'landing_site' in df.columns else 0

    start_date = metadata.get('start_date', 'N/A')
    end_date = metadata.get('end_date', 'N/A')
    sites = metadata.get('selected_sites', [])
    sites_str = ", ".join(sites) if sites else "All Landing Sites"
    if len(sites_str) > 70:
        sites_str = f"{len(sites)} sites selected ({', '.join(sites[:4])}...)"

    # Compute site summary table rows
    site_table_rows = []
    if 'landing_site' in df.columns and 'weight_catch' in df.columns:
        site_agg = df.groupby('landing_site').agg({
            '_uuid': 'count',
            'weight_catch': 'sum'
        }).reset_index().sort_values(by='weight_catch', ascending=False).head(6)
        
        for _, row in site_agg.iterrows():
            s_name = typst_escape(clean_label(row['landing_site']))
            s_recs = f"{int(row['_uuid']):,}"
            s_wgt = f"{row['weight_catch']:,.1f}"
            site_table_rows.append(f"  [{s_name}], [{s_recs}], [{s_wgt}],")

    site_table_markup = "\n".join(site_table_rows) if site_table_rows else "  [All Sites], [0], [0.0],"

    replacements = {
        'START_DATE': typst_escape(str(start_date)),
        'END_DATE': typst_escape(str(end_date)),
        'SELECTED_SITES': typst_escape(sites_str),
        'TOTAL_CATCH': f"{total_catch:,.1f} kg",
        'NUM_RECORDS': f"{num_records:,}",
        'AVG_CATCH': f"{avg_catch:,.2f} kg",
        'NUM_SITES': f"{num_sites}",
        'SITE_TABLE_ROWS': site_table_markup,
        'LOGO_FILENAME': logo_filename,
        'GENERATED_TIME': datetime.now().strftime("%Y-%m-%d %H:%M"),
    }

    return load_and_fill_template(["catch_template.typ"], replacements)


def build_sharks_rays_typst(
    df: pd.DataFrame,
    figures: Dict[str, Path],
    metadata: Dict[str, Any],
    logo_filename: str
) -> str:
    """Builds complete Typst markup for the Sharks & Rays A0 poster."""
    # Compute summary stats
    num_records = len(df)
    num_species = len(df['Scientific_name'].dropna().unique()) if 'Scientific_name' in df.columns else 0
    total_weight = df['weight'].sum() if 'weight' in df.columns else 0.0
    
    # Merge for threat count
    threat_pct = 0.0
    threat_count = 0
    if 'Scientific_name' in df.columns:
        merged = pd.merge(df, DF_IUCN, on='Scientific_name', how='left')
        threat_mask = merged['Red_List_Status'].isin(['CR', 'EN', 'VU'])
        threat_count = int(threat_mask.sum())
        threat_pct = (threat_count / max(1, num_records)) * 100

    start_date = metadata.get('start_date', 'N/A')
    end_date = metadata.get('end_date', 'N/A')
    sites = metadata.get('selected_sites', [])
    sites_str = ", ".join(sites) if sites else "All Sites & Markets"
    if len(sites_str) > 70:
        sites_str = f"{len(sites)} sites selected ({', '.join(sites[:4])}...)"

    replacements = {
        'START_DATE': typst_escape(str(start_date)),
        'END_DATE': typst_escape(str(end_date)),
        'SELECTED_SITES': typst_escape(sites_str),
        'NUM_RECORDS': f"{num_records:,}",
        'NUM_SPECIES': f"{num_species}",
        'TOTAL_WEIGHT': f"{total_weight:,.1f} kg",
        'THREAT_PCT': f"{threat_pct:.1f}%",
        'THREAT_COUNT': f"{threat_count:,}",
        'LOGO_FILENAME': logo_filename,
        'GENERATED_TIME': datetime.now().strftime("%Y-%m-%d %H:%M"),
    }

    return load_and_fill_template(["elasmobranchs_template.typ"], replacements)


def build_restoration_typst(
    df: pd.DataFrame,
    figures: Dict[str, Path],
    metadata: Dict[str, Any],
    logo_filename: str
) -> str:
    """Builds complete Typst markup for the Coral Reef Restoration A0 poster."""
    total_transplanted = 0
    total_reefstars = 0
    total_nursery_tables = 0
    total_area_ha = 0.0

    if not df.empty and 'site_name' in df.columns:
        if 'total_fragments_transplanted_to_date' in df.columns:
            total_transplanted = int(np.nansum(df.groupby('site_name')['total_fragments_transplanted_to_date'].apply(lambda x: pd.to_numeric(x, errors='coerce').max())))
        if 'total_reef_starts_deployed_to_date' in df.columns:
            total_reefstars = int(np.nansum(df.groupby('site_name')['total_reef_starts_deployed_to_date'].apply(lambda x: pd.to_numeric(x, errors='coerce').max())))
        if 'total_tables_in_nursery_to_date' in df.columns:
            total_nursery_tables = int(np.nansum(df.groupby('site_name')['total_tables_in_nursery_to_date'].apply(lambda x: pd.to_numeric(x, errors='coerce').max())))
        total_area_ha = (total_transplanted / 2) / 1e4

    start_date = metadata.get('start_date', 'N/A')
    end_date = metadata.get('end_date', 'N/A')
    sites = metadata.get('selected_sites', [])
    sites_str = ", ".join(sites) if sites else "All Restoration Sites"
    if len(sites_str) > 70:
        sites_str = f"{len(sites)} sites selected ({', '.join(sites[:4])}...)"

    # Build site summary table
    site_table_rows = []
    if not df.empty and 'site_name' in df.columns:
        cols_present = ['site_name']
        if 'site_type' in df.columns:
            cols_present.append('site_type')
        site_grp = df.groupby(cols_present).agg({
            'total_fragments_in_nursery_to_date': lambda x: pd.to_numeric(x, errors='coerce').max(),
            'total_fragments_transplanted_to_date': lambda x: pd.to_numeric(x, errors='coerce').max(),
            '_uuid': 'count'
        }).reset_index()
        for _, row in site_grp.iterrows():
            s_name = typst_escape(clean_label(row['site_name']))
            s_type = typst_escape(clean_label(row.get('site_type', 'Site')))
            if str(row.get('site_type', '')).lower() == 'transplanting' and pd.notna(row['total_fragments_transplanted_to_date']):
                s_frags = f"{int(row['total_fragments_transplanted_to_date']):,}"
            elif pd.notna(row['total_fragments_in_nursery_to_date']):
                s_frags = f"{int(row['total_fragments_in_nursery_to_date']):,}"
            else:
                s_frags = f"{int(row['_uuid']):,} recs"
            site_table_rows.append(f"        [{s_name}], [{s_type}], [{s_frags}],")

    site_table_markup = "\n".join(site_table_rows) if site_table_rows else "        [All Sites], [Restoration], [—],"

    replacements = {
        'START_DATE': typst_escape(str(start_date)),
        'END_DATE': typst_escape(str(end_date)),
        'SELECTED_SITES': typst_escape(sites_str),
        'TOTAL_TRANSPLANTED': f"{total_transplanted:,}",
        'RESTORED_AREA_HA': f"{total_area_ha:,.2f} ha",
        'TOTAL_REEFSTARS': f"{total_reefstars:,}",
        'TOTAL_NURSERY_TABLES': f"{total_nursery_tables:,}",
        'SITE_TABLE_ROWS': site_table_markup,
        'LOGO_FILENAME': logo_filename,
        'GENERATED_TIME': datetime.now().strftime("%Y-%m-%d %H:%M"),
    }

    return load_and_fill_template(["restoration_template.typ"], replacements)


# ==============================================================================
# Master Generator Function
# ==============================================================================
def generate_poster(
    df: pd.DataFrame,
    report_type: str = "bony_fishes",
    metadata: Optional[Dict[str, Any]] = None,
    output_dir: Optional[Path] = None,
    keep_temp: bool = False
) -> Dict[str, Any]:
    """
    Main entry point for generating the A0 poster.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Filtered dataframe containing the landing records.
    report_type : str
        Either 'bony_fishes', 'sharks_rays', or 'restoration'.
    metadata : dict, optional
        Dictionary containing filters, dates, and title info.
    output_dir : Path, optional
        Directory where outputs should be saved. If None, a temporary directory is created.
    keep_temp : bool
        Whether to keep the temporary directory after generation.

    Returns:
    --------
    dict with keys:
        'success': bool
        'pdf_path': Path or None
        'pdf_bytes': bytes or None
        'typ_path': Path
        'zip_path': Path or None
        'zip_bytes': bytes or None
        'message': str
        'typst_available': bool
    """
    if metadata is None:
        metadata = {}

    # Setup directories
    if output_dir is None:
        base_dir = Path(__file__).resolve().parent if '__file__' in globals() else Path.cwd()
        work_dir = base_dir / "posters" / report_type
    else:
        work_dir = Path(output_dir)
    work_dir.mkdir(parents=True, exist_ok=True)

    figures_dir = work_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    # Copy logo
    logo_filename = "wcs_logo.png"
    target_logo = figures_dir / logo_filename
    
    # Locate candidate logos
    base_script_dir = Path(__file__).resolve().parent
    candidate_logos = [
        base_script_dir / "img" / "WCS-logo_only.png",
        base_script_dir / "img" / "WCS-logo.png",
        base_script_dir / "img" / "WCS-logo_white.png",
    ]
    logo_copied = False
    for cand in candidate_logos:
        if cand.exists():
            shutil.copy(cand, target_logo)
            logo_copied = True
            break
            
    if not logo_copied:
        # Generate placeholder blank logo if not found
        fig, ax = plt.subplots(figsize=(2, 2))
        ax.text(0.5, 0.5, "WCS", fontsize=30, ha='center', va='center', fontweight='bold', color='#0284c7')
        ax.axis('off')
        plt.savefig(target_logo, bbox_inches='tight', transparent=True)
        plt.close(fig)

    # 1. Generate Figures
    if report_type == "sharks_rays" or "shark" in report_type.lower():
        figures = plot_sharks_rays_figures(df, figures_dir)
        typst_markup = build_sharks_rays_typst(df, figures, metadata, logo_filename)
        prefix = "sharks_rays_poster"
    elif report_type == "restoration" or "resto" in report_type.lower():
        figures = plot_restoration_figures(df, figures_dir)
        typst_markup = build_restoration_typst(df, figures, metadata, logo_filename)
        prefix = "restoration_poster"
    else:
        figures = plot_bony_fishes_figures(df, figures_dir)
        typst_markup = build_bony_fishes_typst(df, figures, metadata, logo_filename)
        prefix = "bony_fishes_poster"

    # 2. Write Typst File
    typ_path = work_dir / f"{prefix}.typ"
    typ_path.write_text(typst_markup, encoding='utf-8')

    # 3. Create Source Bundle (.zip) containing .typ and figures
    zip_path = work_dir / f"{prefix}_bundle.zip"
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(typ_path, arcname=typ_path.name)
        for fig_file in figures_dir.glob("*.png"):
            zipf.write(fig_file, arcname=f"figures/{fig_file.name}")
            
    zip_bytes = zip_path.read_bytes()

    # 4. Compile with Typst
    pdf_path = work_dir / f"{prefix}.pdf"
    typst_available, typst_info = check_typst_available()
    
    result = {
        'success': False,
        'pdf_path': None,
        'pdf_bytes': None,
        'typ_path': typ_path,
        'figures_dir': figures_dir,
        'zip_path': zip_path,
        'zip_bytes': zip_bytes,
        'message': '',
        'typst_available': typst_available,
        'work_dir': work_dir
    }

    if typst_available:
        success, error_msg = compile_typst(typ_path, pdf_path)
        if success and pdf_path.exists():
            result['success'] = True
            result['pdf_path'] = pdf_path
            result['pdf_bytes'] = pdf_path.read_bytes()
            result['message'] = f"Successfully generated A0 PDF poster ({pdf_path.stat().st_size / 1024 / 1024:.2f} MB)"
        else:
            result['message'] = f"Typst compilation error: {error_msg}"
    else:
        result['message'] = (
            "Typst compiler not found on system. Generated Typst markup and figures bundle (.zip). "
            "Install Typst via `brew install typst` or `pip install typst` to enable direct PDF compilation."
        )

    return result


# ==============================================================================
# Standalone CLI Interface
# ==============================================================================
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate an A0 scientific poster using Typst from CatchViz CSV data.")
    parser.add_argument("--type", choices=["bony_fishes", "sharks_rays", "restoration"], default="bony_fishes", help="Report type")
    parser.add_argument("--csv", type=str, required=True, help="Path to input CSV file")
    parser.add_argument("--output-dir", type=str, default="./poster_output", help="Output directory")
    
    args = parser.parse_args()
    
    print(f"Loading data from {args.csv}...")
    df_data = pd.read_csv(args.csv, low_memory=False)
    print(f"Loaded {len(df_data)} records.")
    
    out_dir = Path(args.output_dir)
    print(f"Generating {args.type} poster in {out_dir}...")
    
    result = generate_poster(
        df=df_data,
        report_type=args.type,
        output_dir=out_dir,
        metadata={
            'start_date': 'All available dates',
            'end_date': 'Latest records',
            'selected_sites': df_data['landing_site'].dropna().unique().tolist() if 'landing_site' in df_data.columns else []
        }
    )
    
    print(result['message'])
    if result['pdf_path']:
        print(f"PDF Output: {result['pdf_path']}")
    print(f"Typst Source: {result['typ_path']}")
    print(f"Source Bundle: {result['zip_path']}")


"""
poster_generator.py
===================
Self-contained generator for A0 scientific/management report posters formatted with Typst.
Designed for the WCS Tanzania CatchViz Streamlit platform.

Supports:
- Bony Fishes landings reports (CATCH dataset)
- Sharks and Rays landings reports (SHARK dataset)
- Coral Reef Restoration reports (RESTORATION dataset)
"""

import json
import math
import os
import re
import sys
import shutil
import ssl
import subprocess
import tempfile
import urllib.request
import zipfile
from datetime import datetime, date
from io import BytesIO
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List

import pandas as pd
import numpy as np
from PIL import Image

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
import matplotlib.ticker as ticker
from matplotlib.collections import PatchCollection
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Polygon

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
    'CR': '#D40000',
    'EN': '#FF7C00',
    'VU': '#FFD800',
    'NT': '#00A859',
    'LC': '#0085C8',
    'DD': '#888888',
    'NE': '#CCCCCC',
}

# ==============================================================================
# Restoration Coordinates & Sites (Aligned with restoration.py)
# ==============================================================================
RESTORATION_PROJECT_COORDS = [
    ['moa', -4.77763, 39.19956],
    ['kigombe', -5.26431, 39.07310],
    ['msuka', -4.90274, 39.72391]
]
DF_RESTORATION_PROJECT_COORDS = pd.DataFrame(
    RESTORATION_PROJECT_COORDS,
    columns=['project_site', 'latitude', 'longitude']
)

RESTORATION_SUBSITE_COORDS = [
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
DF_RESTORATION_COORDS = pd.DataFrame(
    RESTORATION_SUBSITE_COORDS,
    columns=['site_name', 'latitude', 'longitude']
)

# Built-in offline fallback rings for Mainland Tanzania, Unguja, Pemba, and Mafia
BUILTIN_TZ_COASTLINE_RINGS: List[List[Tuple[float, float]]] = [
    # Mainland Tanzania & Kenya border coast (closed inland to west)
    [
        (35.00, -3.50), (39.60, -3.50), (39.68, -4.05), (39.45, -4.35),
        (39.22, -4.66), (39.18, -4.78), (39.12, -4.95), (39.11, -5.07),
        (39.06, -5.26), (38.98, -5.43), (38.89, -5.65), (38.80, -5.88),
        (38.78, -6.05), (38.85, -6.28), (38.91, -6.44), (39.06, -6.58),
        (39.22, -6.72), (39.29, -6.82), (39.38, -6.87), (39.54, -6.99),
        (39.48, -7.22), (39.42, -7.45), (39.36, -7.68), (39.35, -7.85),
        (39.32, -8.08), (39.28, -8.32), (39.35, -8.55), (39.42, -8.75),
        (39.51, -8.93), (39.48, -9.15), (39.55, -9.42), (39.62, -9.70),
        (39.72, -9.99), (39.95, -10.12), (40.12, -10.28), (40.25, -10.27),
        (40.44, -10.48), (40.55, -10.80), (40.55, -12.00), (35.00, -12.00),
        (35.00, -3.50),
    ],
    # Unguja (Zanzibar Island)
    [
        (39.295, -5.725), (39.335, -5.785), (39.355, -5.860), (39.375, -5.990),
        (39.425, -6.100), (39.430, -6.170), (39.490, -6.140), (39.535, -6.270),
        (39.550, -6.320), (39.555, -6.420), (39.465, -6.475), (39.385, -6.405),
        (39.330, -6.335), (39.270, -6.305), (39.245, -6.225), (39.185, -6.162),
        (39.210, -6.100), (39.185, -5.985), (39.245, -5.875), (39.275, -5.785),
        (39.295, -5.725),
    ],
    # Pemba Island
    [
        (39.685, -4.875), (39.725, -4.910), (39.785, -4.965), (39.845, -5.035),
        (39.865, -5.085), (39.845, -5.210), (39.830, -5.310), (39.765, -5.425),
        (39.690, -5.465), (39.645, -5.360), (39.685, -5.285), (39.735, -5.250),
        (39.695, -5.175), (39.715, -5.060), (39.655, -5.020), (39.665, -4.930),
        (39.685, -4.875),
    ],
    # Mafia Island
    [
        (39.915, -7.640), (39.925, -7.740), (39.885, -7.865), (39.835, -7.965),
        (39.725, -7.995), (39.655, -7.915), (39.695, -7.825), (39.760, -7.750),
        (39.845, -7.685), (39.915, -7.640),
    ],
]

_COASTLINE_RINGS_CACHE: Optional[List[List[Tuple[float, float]]]] = None

TILE_PROVIDERS = [
    (
        "carto_positron",
        "https://basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png",
        "© OpenStreetMap contributors, © CARTO",
    ),
    (
        "osm_standard",
        "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
        "© OpenStreetMap contributors",
    ),
]


# ==============================================================================
# Helpers: GPS Sanitization, Basemap Tiles & Offline Coastline Fallback
# ==============================================================================
def _filter_valid_tz_coords(df: pd.DataFrame, lat_col: str, lon_col: str) -> pd.DataFrame:
    """Filters out (0, 0) Kobo GPS defaults and non-East Africa outliers."""
    out = df.copy()
    out[lat_col] = pd.to_numeric(out[lat_col], errors='coerce')
    out[lon_col] = pd.to_numeric(out[lon_col], errors='coerce')
    valid = (
        out[lat_col].between(-15.0, 2.0)
        & out[lon_col].between(28.0, 45.0)
        & ~((out[lat_col].abs() < 0.01) & (out[lon_col].abs() < 0.01))
    )
    return out[valid]


def _lonlat_to_mercator(lon: float, lat: float) -> Tuple[float, float]:
    """Converts WGS84 (lon, lat) to Web Mercator (EPSG:3857) meters."""
    R = 6378137.0
    x = math.radians(lon) * R
    lat_clamped = max(min(lat, 85.05112878), -85.05112878)
    y = math.log(math.tan(math.pi / 4.0 + math.radians(lat_clamped) / 2.0)) * R
    return x, y


def _tile_bounds_mercator(xtile: int, ytile: int, zoom: int) -> Tuple[float, float, float, float]:
    """Returns (xmin, xmax, ymin, ymax) in EPSG:3857 meters for an XYZ tile."""
    R = 6378137.0
    origin = math.pi * R
    tile_size = (2.0 * origin) / (2 ** zoom)
    xmin = -origin + xtile * tile_size
    xmax = xmin + tile_size
    ymax = origin - ytile * tile_size
    ymin = ymax - tile_size
    return xmin, xmax, ymin, ymax


def _fetch_basemap_tiles(
    xmin_m: float, xmax_m: float, ymin_m: float, ymax_m: float, zoom: int = 8
):
    """
    Fetches, caches, and stitches XYZ raster map tiles (CartoDB Positron primary,
    OpenStreetMap fallback) in Web Mercator (EPSG:3857).
    """
    R = 6378137.0
    origin = math.pi * R
    n = 2 ** zoom
    tile_span = (2.0 * origin) / n

    x_min_tile = max(0, int((xmin_m + origin) / tile_span))
    x_max_tile = min(n - 1, int((xmax_m + origin) / tile_span))
    y_min_tile = max(0, int((origin - ymax_m) / tile_span))
    y_max_tile = min(n - 1, int((origin - ymin_m) / tile_span))

    if (x_max_tile - x_min_tile + 1) * (y_max_tile - y_min_tile + 1) > 49:
        return None, None, None

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    headers = {
        "User-Agent": "CatchViz-WCS-Tanzania-Marine-Program/1.0 (https://tanzania.wcs.org)",
        "Accept": "image/png,image/*;q=0.8",
    }

    base_dir = Path(__file__).resolve().parent if '__file__' in globals() else Path.cwd()
    cache_root = base_dir / "posters" / ".tile_cache"

    tile_px = 256
    cols = x_max_tile - x_min_tile + 1
    rows = y_max_tile - y_min_tile + 1

    west_m, _, _, north_m = _tile_bounds_mercator(x_min_tile, y_min_tile, zoom)
    _, east_m, south_m, _ = _tile_bounds_mercator(x_max_tile, y_max_tile, zoom)
    extent_m = (west_m, east_m, south_m, north_m)

    for provider_id, url_tmpl, attribution in TILE_PROVIDERS:
        canvas = Image.new("RGBA", (cols * tile_px, rows * tile_px))
        provider_ok = True

        for ix, xt in enumerate(range(x_min_tile, x_max_tile + 1)):
            for iy, yt in enumerate(range(y_min_tile, y_max_tile + 1)):
                cache_file = cache_root / provider_id / str(zoom) / str(xt) / f"{yt}.png"
                tile_bytes = None

                if cache_file.exists() and cache_file.stat().st_size > 0:
                    tile_bytes = cache_file.read_bytes()
                else:
                    url = url_tmpl.format(z=zoom, x=xt, y=yt)
                    try:
                        req = urllib.request.Request(url, headers=headers)
                        with urllib.request.urlopen(req, timeout=8, context=ctx) as resp:
                            tile_bytes = resp.read()
                        cache_file.parent.mkdir(parents=True, exist_ok=True)
                        cache_file.write_bytes(tile_bytes)
                    except Exception:
                        provider_ok = False
                        break

                try:
                    tile_img = Image.open(BytesIO(tile_bytes)).convert("RGBA")
                    if tile_img.size != (tile_px, tile_px):
                        tile_img = tile_img.resize((tile_px, tile_px), Image.Resampling.LANCZOS)
                    canvas.paste(tile_img, (ix * tile_px, iy * tile_px))
                except Exception:
                    if cache_file.exists():
                        cache_file.unlink(missing_ok=True)
                    provider_ok = False
                    break

            if not provider_ok:
                break

        if provider_ok:
            return np.asarray(canvas), extent_m, attribution

    return None, None, None


def _ring_intersects_bbox(
    ring: List[Tuple[float, float]],
    xmin: float, xmax: float, ymin: float, ymax: float
) -> bool:
    lons = [pt[0] for pt in ring]
    lats = [pt[1] for pt in ring]
    return not (max(lons) < xmin or min(lons) > xmax or max(lats) < ymin or min(lats) > ymax)


def _extract_rings_from_geojson(
    geojson_obj: Dict[str, Any],
    xmin: float = 35.0, xmax: float = 42.5,
    ymin: float = -12.5, ymax: float = -3.0
) -> List[List[Tuple[float, float]]]:
    rings: List[List[Tuple[float, float]]] = []
    features = geojson_obj.get("features", [])
    if not features and geojson_obj.get("type") in ("Polygon", "MultiPolygon"):
        features = [{"geometry": geojson_obj}]

    for feat in features:
        geom = feat.get("geometry") or {}
        gtype = geom.get("type")
        coords = geom.get("coordinates") or []
        if gtype == "Polygon":
            if coords and coords[0]:
                ring = [(float(p[0]), float(p[1])) for p in coords[0]]
                if _ring_intersects_bbox(ring, xmin, xmax, ymin, ymax):
                    rings.append(ring)
        elif gtype == "MultiPolygon":
            for poly in coords:
                if poly and poly[0]:
                    ring = [(float(p[0]), float(p[1])) for p in poly[0]]
                    if _ring_intersects_bbox(ring, xmin, xmax, ymin, ymax):
                        rings.append(ring)
    return rings


def get_coastline_rings() -> List[List[Tuple[float, float]]]:
    """
    Offline coastline fallback: checks local GeoJSON files first, then falls
    back immediately to BUILTIN_TZ_COASTLINE_RINGS.
    """
    global _COASTLINE_RINGS_CACHE
    if _COASTLINE_RINGS_CACHE is not None:
        return _COASTLINE_RINGS_CACHE

    base_dir = Path(__file__).resolve().parent if '__file__' in globals() else Path.cwd()
    candidates = [
        base_dir / "data" / "tz_coast.geojson",
        base_dir / "data" / "tanzania_coastline.geojson",
        base_dir / "data" / "zanzibar_coast.geojson",
        base_dir / "data" / "tz_coast_10m_cache.geojson",
        Path("data/tz_coast.geojson"),
        Path("tz_coast.geojson"),
    ]

    for cand in candidates:
        if cand.exists():
            try:
                data = json.loads(cand.read_text(encoding="utf-8"))
                rings = _extract_rings_from_geojson(data)
                if rings:
                    _COASTLINE_RINGS_CACHE = rings
                    return rings
            except Exception:
                continue

    _COASTLINE_RINGS_CACHE = BUILTIN_TZ_COASTLINE_RINGS
    return _COASTLINE_RINGS_CACHE


def render_clean_map(
    ax,
    coords_df: pd.DataFrame,
    lon_col: str,
    lat_col: str,
    label_col: str,
    count_col: str,
    marker_color: str = "#1d6fa5",
    edge_color: str = "#ffffff",
    label_formatter=None,
    size_series=None,
    color_series=None,
):
    """
    Renders a static 300 DPI map using CartoDB Positron / OpenStreetMap tiles
    with guaranteed offline coastline fallback.
    """
    lon_span = coords_df[lon_col].max() - coords_df[lon_col].min()
    lat_span = coords_df[lat_col].max() - coords_df[lat_col].min()
    pad_lon = max(0.45, lon_span * 0.38)
    pad_lat = max(0.45, lat_span * 0.38)

    xmin = coords_df[lon_col].min() - pad_lon
    xmax = coords_df[lon_col].max() + pad_lon
    ymin = coords_df[lat_col].min() - pad_lat
    ymax = coords_df[lat_col].max() + pad_lat

    max_span = max(xmax - xmin, ymax - ymin)
    zoom = 9 if max_span < 1.3 else (8 if max_span < 2.8 else (7 if max_span < 5.5 else 6))

    xmin_m, ymin_m = _lonlat_to_mercator(xmin, ymin)
    xmax_m, ymax_m = _lonlat_to_mercator(xmax, ymax)

    basemap_img, extent_m, attribution = _fetch_basemap_tiles(xmin_m, xmax_m, ymin_m, ymax_m, zoom=zoom)

    if basemap_img is not None:
        pts_m = [_lonlat_to_mercator(float(r[lon_col]), float(r[lat_col])) for _, r in coords_df.iterrows()]
        xs = [p[0] for p in pts_m]
        ys = [p[1] for p in pts_m]

        ax.imshow(basemap_img, extent=extent_m, interpolation="bilinear", zorder=1)
        ax.set_xlim(xmin_m, xmax_m)
        ax.set_ylim(ymin_m, ymax_m)
        ax.text(
            0.995, 0.01, attribution,
            transform=ax.transAxes, ha="right", va="bottom",
            fontsize=7.5, color="#334155",
            bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.75, edgecolor="none"),
            zorder=5,
        )
    else:
        ax.figure.patch.set_facecolor("#e8f3fa")
        ax.set_facecolor("#e8f3fa")
        xs = coords_df[lon_col].tolist()
        ys = coords_df[lat_col].tolist()

        rings = get_coastline_rings()
        if rings:
            patches = [Polygon(ring, closed=True) for ring in rings]
            pc = PatchCollection(
                patches,
                facecolor="#f8fafc",
                edgecolor="#64748b",
                linewidth=1.25,
                zorder=1,
            )
            ax.add_collection(pc)
        ax.set_xlim(xmin, xmax)
        ax.set_ylim(ymin, ymax)

    if size_series is not None:
        sizes = size_series
    else:
        max_n = max(float(coords_df[count_col].max()), 1.0)
        sizes = 240 + (coords_df[count_col] / max_n) * 900

    colors = color_series if color_series is not None else marker_color

    ax.scatter(
        xs,
        ys,
        s=sizes,
        c=colors,
        alpha=0.88,
        edgecolors=edge_color,
        linewidth=2.0,
        zorder=3,
    )

    for (_, row), px, py in zip(coords_df.iterrows(), xs, ys):
        if label_formatter is not None:
            label_txt = label_formatter(row)
        else:
            site_name = clean_label(row[label_col])
            label_txt = f"{site_name} (n={int(row[count_col]):,})"

        txt = ax.annotate(
            label_txt,
            (px, py),
            textcoords="offset points",
            xytext=(0, 14),
            ha="center",
            va="bottom",
            fontsize=11,
            fontweight="bold",
            color="#0f172a",
            zorder=4,
        )
        txt.set_path_effects([pe.withStroke(linewidth=3.2, foreground="white")])

    ax.set_aspect("equal")
    ax.grid(False)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)


# ==============================================================================
# Helpers: Formatting & Typst Escaping
# ==============================================================================
def typst_escape(value: Any) -> str:
    """Escapes strings for safe inclusion in Typst markup."""
    if value is None or pd.isna(value):
        return ""
    text = str(value)
    for ch in ['\\', '#', '$', '@', '*', '`', '<', '>']:
        text = text.replace(ch, f'\\{ch}')
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
    try:
        import typst
        return True, "python-typst"
    except ImportError:
        pass

    binary = find_typst_binary()
    if binary:
        return True, binary

    return False, "Not found"

def compile_typst(typst_file: Path, output_pdf: Path) -> Tuple[bool, Optional[str]]:
    """Compiles a Typst source file to PDF using PROJECT_ROOT as the Typst root."""
    root_dir = str(PROJECT_ROOT)

    try:
        import typst
        typst.compile(str(typst_file), output=str(output_pdf), root=root_dir)
        if output_pdf.exists() and output_pdf.stat().st_size > 0:
            return True, None
    except ImportError:
        pass
    except Exception as e:
        return False, f"Python typst compile error: {str(e)}"

    binary = find_typst_binary()
    if binary:
        try:
            cmd = [binary, "compile", "--root", root_dir, str(typst_file), str(output_pdf)]
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
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

    # 1. Geographic Distribution Map
    fig, ax = plt.subplots(figsize=(9, 6.5))
    if '_gps_latitude' in df.columns and '_gps_longitude' in df.columns and 'landing_site' in df.columns:
        df_gps = _filter_valid_tz_coords(df, '_gps_latitude', '_gps_longitude')
        med_coords = df_gps.groupby('landing_site')[['_gps_latitude', '_gps_longitude']].median().dropna()
        total_counts = df.groupby('landing_site').size().rename('count')
        coords = med_coords.join(total_counts).rename(
            columns={'_gps_latitude': 'lat', '_gps_longitude': 'lon'}
        ).reset_index()

        if not coords.empty:
            render_clean_map(
                ax=ax,
                coords_df=coords,
                lon_col='lon',
                lat_col='lat',
                label_col='landing_site',
                count_col='count',
                marker_color='#0284c7',
                edge_color='#ffffff',
            )
            plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
            map_path = output_dir / "fig_map.png"
            plt.savefig(map_path, dpi=300, bbox_inches='tight', pad_inches=0)
            plt.close(fig)
            figures['map'] = map_path
        else:
            ax.text(0.5, 0.5, 'No valid GPS coordinates available', ha='center', va='center')
            ax.axis('off')
            map_path = output_dir / "fig_map.png"
            plt.savefig(map_path, dpi=300, bbox_inches='tight')
            plt.close(fig)
            figures['map'] = map_path
    else:
        ax.text(0.5, 0.5, 'GPS data not found', ha='center', va='center')
        ax.axis('off')
        map_path = output_dir / "fig_map.png"
        plt.savefig(map_path, dpi=300, bbox_inches='tight')
        plt.close(fig)
        figures['map'] = map_path

    # 2. Sampling Effort Over Time
    fig, ax = plt.subplots(figsize=(9, 5.5))
    if 'today' in df.columns:
        df_time = df.copy()
        df_time['today'] = pd.to_datetime(df_time['today'], errors='coerce')
        df_time = df_time.dropna(subset=['today'])
        if not df_time.empty:
            df_time['period'] = df_time['today'].dt.to_period('M')
            effort_time = df_time.groupby(['period', 'landing_site'])['_uuid'].count().unstack(fill_value=0)

            colors = plt.cm.tab10(np.linspace(0, 1, max(1, len(effort_time.columns))))
            effort_time.plot(kind='bar', stacked=True, ax=ax, color=colors, width=0.85, edgecolor='#334155', linewidth=0.5)

            ax.set_xlabel('Sampling Month')
            ax.set_ylabel('Number of Landings')
            ax.set_title('Sampling Effort Over Time by Landing Site', pad=12)

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

    # 3. Landings by Boat Type
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

    # 4. Landings by Species Group
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

    # 5. Landings by Gear Type
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

    # 6. Effort by Vessel & Site
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

    # 7. CPUE Trends
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

        cpue_agg = df_cpue.groupby(['today', 'landing_site'])['CPUE'].mean().reset_index()

        if not cpue_agg.empty:
            sites = cpue_agg['landing_site'].unique()
            colors = plt.cm.tab10(np.linspace(0, 1, max(1, len(sites))))

            for i, site in enumerate(sites):
                site_data = cpue_agg[cpue_agg['landing_site'] == site].sort_values('today')
                site_label = clean_label(site)
                ax.scatter(site_data['today'], site_data['CPUE'], color=colors[i], alpha=0.55, s=35, label=site_label)

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


def plot_sharks_rays_size_distribution(df_merged: pd.DataFrame, output_dir: Path) -> Path:
    """
    Generates a multi-panel size-frequency distribution (Total Length for sharks,
    Disc Width for rays) for the top landed species overlaid with published
    sex-specific size-at-maturity (Lm) thresholds.
    """
    setup_mpl_style()
    size_dist_path = output_dir / "fig_size_dist.png"

    df_size = df_merged.copy()
    df_size['size_cm'] = np.nan
    df_size['metric_label'] = 'Length (cm)'

    if 'Shark_or_Ray' in df_size.columns:
        is_shark = df_size['Shark_or_Ray'] == 'Shark'
        is_ray = df_size['Shark_or_Ray'] == 'Ray'

        if 'total_length' in df_size.columns:
            df_size.loc[is_shark, 'size_cm'] = pd.to_numeric(df_size.loc[is_shark, 'total_length'], errors='coerce')
            df_size.loc[is_shark, 'metric_label'] = 'Total Length (cm)'

        if 'disc_width' in df_size.columns:
            df_size.loc[is_ray, 'size_cm'] = pd.to_numeric(df_size.loc[is_ray, 'disc_width'], errors='coerce')
            df_size.loc[is_ray, 'metric_label'] = 'Disc Width (cm)'
    else:
        tl = pd.to_numeric(df_size['total_length'], errors='coerce') if 'total_length' in df_size.columns else pd.Series(np.nan, index=df_size.index)
        dw = pd.to_numeric(df_size['disc_width'], errors='coerce') if 'disc_width' in df_size.columns else pd.Series(np.nan, index=df_size.index)
        df_size['size_cm'] = tl.fillna(dw)

    df_valid = df_size.dropna(subset=['Scientific_name', 'size_cm'])
    df_valid = df_valid[(df_valid['size_cm'] > 0) & (df_valid['size_cm'] < 800)]

    if df_valid.empty:
        fig, ax = plt.subplots(figsize=(9, 5))
        ax.text(0.5, 0.5, 'No morphometric size measurements available', ha='center', va='center')
        ax.axis('off')
        plt.tight_layout()
        plt.savefig(size_dist_path, dpi=300, bbox_inches='tight')
        plt.close(fig)
        return size_dist_path

    top_species = df_valid['Scientific_name'].value_counts().head(6).index.tolist()
    n_sp = len(top_species)
    ncols = 2
    nrows = math.ceil(n_sp / ncols)

    fig, axes = plt.subplots(nrows, ncols, figsize=(10, 3.4 * nrows))
    axes = np.atleast_1d(axes).flatten()

    for idx, sp in enumerate(top_species):
        ax = axes[idx]
        sp_df = df_valid[df_valid['Scientific_name'] == sp]
        metric_lbl = sp_df['metric_label'].iloc[0]

        if 'sex' in sp_df.columns and sp_df['sex'].isin(['Female', 'Male']).any():
            f_sizes = sp_df[sp_df['sex'] == 'Female']['size_cm']
            m_sizes = sp_df[sp_df['sex'] == 'Male']['size_cm']
            u_sizes = sp_df[~sp_df['sex'].isin(['Female', 'Male'])]['size_cm']

            bins = np.histogram_bin_edges(sp_df['size_cm'], bins=12)
            series_list, colors_list, labels_list = [], [], []
            if not f_sizes.empty:
                series_list.append(f_sizes)
                colors_list.append('#ec4899')
                labels_list.append(f'Female (n={len(f_sizes)})')
            if not m_sizes.empty:
                series_list.append(m_sizes)
                colors_list.append('#0284c7')
                labels_list.append(f'Male (n={len(m_sizes)})')
            if not u_sizes.empty:
                series_list.append(u_sizes)
                colors_list.append('#94a3b8')
                labels_list.append(f'Unsexed (n={len(u_sizes)})')

            ax.hist(series_list, bins=bins, stacked=True, color=colors_list,
                    edgecolor='white', linewidth=0.8, label=labels_list)
        else:
            ax.hist(sp_df['size_cm'], bins=12, color='#0284c7', edgecolor='white',
                    linewidth=0.8, label=f'All (n={len(sp_df)})')

        lm_f = pd.to_numeric(sp_df['Female_size_at_maturity_cm_DW_TL'].iloc[0], errors='coerce') if 'Female_size_at_maturity_cm_DW_TL' in sp_df.columns else np.nan
        lm_m = pd.to_numeric(sp_df['Male_size_at_maturity_cm_DW_TL'].iloc[0], errors='coerce') if 'Male_size_at_maturity_cm_DW_TL' in sp_df.columns else np.nan

        if pd.notna(lm_f) and pd.notna(lm_m) and np.isclose(lm_f, lm_m):
            ax.axvline(lm_f, color='#b91c1c', linestyle='--', linewidth=2.0, label=f'Lm: {int(lm_f)} cm')
        else:
            if pd.notna(lm_f):
                ax.axvline(lm_f, color='#be185d', linestyle='--', linewidth=2.0, label=f'Lm ♀: {int(lm_f)} cm')
            if pd.notna(lm_m):
                ax.axvline(lm_m, color='#1d4ed8', linestyle=':', linewidth=2.2, label=f'Lm ♂: {int(lm_m)} cm')

        ax.set_title(sp, fontsize=12, fontstyle='italic', fontweight='bold', pad=6)
        ax.set_xlabel(metric_lbl, fontsize=10)
        ax.set_ylabel('Count', fontsize=10)
        ax.tick_params(labelsize=9)
        ax.grid(axis='y', linestyle='--', alpha=0.35)
        ax.legend(loc='upper right', fontsize=8.5, frameon=True)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

    for j in range(n_sp, len(axes)):
        axes[j].set_visible(False)

    plt.suptitle('Size-Frequency Distributions vs. Size at Maturity (Lm)', fontsize=14, fontweight='bold', y=1.01)
    plt.tight_layout()
    plt.savefig(size_dist_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    return size_dist_path


def plot_sharks_rays_figures(df: pd.DataFrame, output_dir: Path) -> Dict[str, Path]:
    """Generates all high-resolution figures for the Sharks and Rays poster."""
    setup_mpl_style()
    figures = {}

    df_merged = df.copy()
    if 'Scientific_name' in df_merged.columns:
        df_merged = pd.merge(df_merged, DF_IUCN, on='Scientific_name', how='left')

    # 1. Geographic Map
    fig, ax = plt.subplots(figsize=(9, 6.5))
    if '_gps_latitude' in df_merged.columns and '_gps_longitude' in df_merged.columns:
        loc_col = 'landing_site' if 'landing_site' in df_merged.columns else 'market'
        df_gps = _filter_valid_tz_coords(df_merged, '_gps_latitude', '_gps_longitude')

        med_coords = df_gps.groupby(loc_col)[['_gps_latitude', '_gps_longitude']].median().dropna()
        total_counts = df_merged.groupby(loc_col).size().rename('count')
        coords = med_coords.join(total_counts).rename(
            columns={'_gps_latitude': 'lat', '_gps_longitude': 'lon'}
        ).reset_index()

        if not coords.empty:
            render_clean_map(
                ax=ax,
                coords_df=coords,
                lon_col='lon',
                lat_col='lat',
                label_col=loc_col,
                count_col='count',
                marker_color='#ea580c',
                edge_color='#ffffff',
            )
            plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
            map_path = output_dir / "fig_map.png"
            plt.savefig(map_path, dpi=300, bbox_inches='tight', pad_inches=0)
            plt.close(fig)
            figures['map'] = map_path
        else:
            ax.text(0.5, 0.5, 'No valid coordinates available', ha='center', va='center')
            ax.axis('off')
            map_path = output_dir / "fig_map.png"
            plt.savefig(map_path, dpi=300, bbox_inches='tight')
            plt.close(fig)
            figures['map'] = map_path
    else:
        ax.axis('off')
        map_path = output_dir / "fig_map.png"
        plt.savefig(map_path, dpi=300, bbox_inches='tight')
        plt.close(fig)
        figures['map'] = map_path

    # 2. Top Landed Species by IUCN Status
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

    # 3. IUCN Red List Status Composition
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

    # 4. Maturity Ratio Distribution
    fig, ax = plt.subplots(figsize=(8.5, 5))
    df_mat = df_merged.copy()
    df_mat['maturity'] = np.nan

    ray_male = (df_mat['sex'] == 'Male') & (df_mat['Shark_or_Ray'] == 'Ray')
    if 'disc_width' in df_mat.columns and 'Male_size_at_maturity_cm_DW_TL' in df_mat.columns:
        df_mat.loc[ray_male, 'maturity'] = pd.to_numeric(df_mat.loc[ray_male, 'disc_width'], errors='coerce') / pd.to_numeric(df_mat.loc[ray_male, 'Male_size_at_maturity_cm_DW_TL'], errors='coerce')

    ray_female = (df_mat['sex'] == 'Female') & (df_mat['Shark_or_Ray'] == 'Ray')
    if 'disc_width' in df_mat.columns and 'Female_size_at_maturity_cm_DW_TL' in df_mat.columns:
        df_mat.loc[ray_female, 'maturity'] = pd.to_numeric(df_mat.loc[ray_female, 'disc_width'], errors='coerce') / pd.to_numeric(df_mat.loc[ray_female, 'Female_size_at_maturity_cm_DW_TL'], errors='coerce')

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

    # 5. Fishing Gear Utilization
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

    # 6. Targeted vs Bycatch Donut Chart
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

    # 7. Sex Ratio Distribution
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

    # 8. Sampling Effort Over Time
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

    # 9. Size-Frequency Distribution vs. Size at Maturity (Lm)
    figures['size_dist'] = plot_sharks_rays_size_distribution(df_merged, output_dir)

    return figures


def plot_restoration_figures(df: pd.DataFrame, output_dir: Path) -> Dict[str, Path]:
    """Generates all high-resolution figures for the Coral Reef Restoration poster."""
    setup_mpl_style()
    figures = {}

    df_plot = df.copy()
    if 'test' in df_plot.columns:
        df_plot = df_plot[df_plot['test'] != 'yes']

    if 'project_site' in df_plot.columns:
        if 'latitude' not in df_plot.columns or 'longitude' not in df_plot.columns:
            df_plot = pd.merge(df_plot, DF_RESTORATION_PROJECT_COORDS, on='project_site', how='left')
    elif 'site_name' in df_plot.columns and ('latitude' not in df_plot.columns or 'longitude' not in df_plot.columns):
        df_plot = pd.merge(df_plot, DF_RESTORATION_COORDS, on='site_name', how='left')

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

    date_col = 'datetime' if 'datetime' in df_plot.columns else ('Date' if 'Date' in df_plot.columns else ('date' if 'date' in df_plot.columns else None))
    if date_col and not df_plot.empty:
        df_plot['dt'] = pd.to_datetime(df_plot[date_col], format='mixed', errors='coerce')
    else:
        df_plot['dt'] = pd.NaT

    # 1. Map of Restoration Project Sites
    fig, ax = plt.subplots(figsize=(8, 5.5))
    map_group_col = 'project_site' if 'project_site' in df_plot.columns else 'site_name'
    if not df_plot.empty and 'latitude' in df_plot.columns and 'longitude' in df_plot.columns and map_group_col in df_plot.columns:
        df_gps = _filter_valid_tz_coords(df_plot, 'latitude', 'longitude')
        site_agg = df_gps.groupby([map_group_col, 'latitude', 'longitude'], as_index=False).agg({
            'total_fragments_in_nursery_to_date': 'max',
            'total_fragments_transplanted_to_date': 'max',
            '_uuid': 'count'
        })

        if not site_agg.empty:
            sizes_list = []
            for _, r in site_agg.iterrows():
                nurs_val = r['total_fragments_in_nursery_to_date'] if pd.notna(r['total_fragments_in_nursery_to_date']) else 0
                trans_val = r['total_fragments_transplanted_to_date'] if pd.notna(r['total_fragments_transplanted_to_date']) else 0
                sizes_list.append(max(180, min(1300, (nurs_val + trans_val) / 12 + 180)))

            def resto_proj_label(r):
                nurs_val = r['total_fragments_in_nursery_to_date'] if pd.notna(r['total_fragments_in_nursery_to_date']) else 0
                trans_val = r['total_fragments_transplanted_to_date'] if pd.notna(r['total_fragments_transplanted_to_date']) else 0
                tot = nurs_val + trans_val
                detail = f"Nursery: {int(nurs_val):,} | Transplanted: {int(trans_val):,}" if tot > 0 else f"{int(r['_uuid'])} records"
                return f"{clean_label(r[map_group_col])}\n({detail})"

            render_clean_map(
                ax=ax,
                coords_df=site_agg,
                lon_col='longitude',
                lat_col='latitude',
                label_col=map_group_col,
                count_col='_uuid',
                marker_color='#0d9488',
                edge_color='#1e293b',
                label_formatter=resto_proj_label,
                size_series=sizes_list,
            )
            legend_elements = [
                Line2D([0], [0], marker='o', color='w', label='Restoration Project Site (Scaled by Total Fragments)', markerfacecolor='#0d9488', markersize=11, markeredgecolor='#1e293b'),
            ]
            ax.legend(handles=legend_elements, loc='lower right', frameon=True, fontsize=9)
        else:
            ax.text(0.5, 0.5, 'No site coordinates available', ha='center', va='center')
            ax.axis('off')
    else:
        ax.text(0.5, 0.5, 'No records for current filters', ha='center', va='center')
        ax.axis('off')
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    map_p = output_dir / "fig_map.png"
    plt.savefig(map_p, dpi=300, bbox_inches='tight', pad_inches=0)
    plt.close(fig)
    figures['map'] = map_p

    # 2. Cumulative Area Restored Over Time
    fig, ax = plt.subplots(figsize=(8, 4.8))
    series_group_col = 'site_name' if 'site_name' in df_plot.columns else 'project_site'
    if not df_plot.empty and 'dt' in df_plot.columns and 'total_fragments_transplanted_to_date' in df_plot.columns and series_group_col in df_plot.columns:
        valid_df = df_plot.dropna(subset=['dt', 'total_fragments_transplanted_to_date']).sort_values('dt')
        if not valid_df.empty:
            for site in valid_df[series_group_col].dropna().unique():
                sdf = valid_df[valid_df[series_group_col] == site].copy()
                sdf['area_ha'] = (sdf['total_fragments_transplanted_to_date'] / 2) / 1e4
                sdf['area_ha_cum'] = sdf['area_ha'].cummax()
                ax.plot(sdf['dt'], sdf['area_ha_cum'], marker='o', markersize=4, linewidth=2.2, label=clean_label(site))
            ax.set_xlabel('Date', fontsize=11)
            ax.set_ylabel('Cumulative Area (ha)', fontsize=11)
            ax.set_title('Progressive Reef Area Restored Over Time (ha)', pad=10, fontsize=13)
            ax.grid(True, linestyle='--', alpha=0.4)
            ax.legend(title='Restoration Site', frameon=True, fontsize=8.5)
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
    act_group_col = 'site_name' if 'site_name' in df_plot.columns else 'project_site'
    for idx, (col_name, title, bar_col) in enumerate(act_map):
        ax_curr = axes[idx // 2, idx % 2]
        if not df_plot.empty and col_name in df_plot.columns and act_group_col in df_plot.columns:
            act_df = df_plot[pd.to_numeric(df_plot[col_name], errors='coerce') == 1]
            if not act_df.empty:
                counts = act_df.drop_duplicates(subset=['_uuid', act_group_col]).groupby(act_group_col)['_uuid'].count().sort_values(ascending=False)
                labels = [clean_label(x) for x in counts.index]
                bars = ax_curr.bar(labels, counts.values, color=bar_col, edgecolor='#1e293b', width=0.55)
                for b in bars:
                    h = b.get_height()
                    ax_curr.text(b.get_x() + b.get_width()/2, h + max(counts.values)*0.02, f"{int(h)}",
                                 ha='center', va='bottom', fontsize=8.5, fontweight='bold')
                ax_curr.set_title(title, fontsize=11, pad=5)
                ax_curr.set_ylabel('Field Days', fontsize=9)
                ax_curr.tick_params(axis='x', rotation=25, labelsize=8)
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
    plt.suptitle('Field Operational Days by Restoration Activity & Site', fontsize=13, fontweight='bold', y=0.98)
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
    sess_group_col = 'site_name' if 'site_name' in df_plot.columns else 'project_site'
    if not df_plot.empty and 'dt' in df_plot.columns and 'total_number_of_fragments_transplanted' in df_plot.columns and sess_group_col in df_plot.columns:
        valid_sess = df_plot.dropna(subset=['dt', 'total_number_of_fragments_transplanted']).copy()
        if not valid_sess.empty:
            valid_sess['period'] = valid_sess['dt'].dt.to_period('M')
            sess_agg = valid_sess.groupby(['period', sess_group_col])['total_number_of_fragments_transplanted'].sum().unstack(fill_value=0)
            sess_agg.columns = [clean_label(c) for c in sess_agg.columns]
            colors = plt.cm.Set2(np.linspace(0, 1, max(1, len(sess_agg.columns))))
            sess_agg.plot(kind='bar', stacked=True, ax=ax, color=colors, width=0.75, edgecolor='#334155', linewidth=0.5)
            labels = [p.strftime('%b %Y') for p in sess_agg.index]
            ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=9)
            ax.set_xlabel('Monitoring Period', fontsize=11)
            ax.set_ylabel('Fragments Outplanted', fontsize=11)
            ax.set_title('Monthly Coral Fragments Outplanted per Site', pad=10, fontsize=13)
            ax.legend(title='Restoration Site', frameon=True, fontsize=8.5)
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
            nurs_agg = nursery_df.groupby('site_name')['total_fragments_in_nursery_to_date'].max().dropna()
            nurs_agg = nurs_agg[nurs_agg > 0].sort_values(ascending=True)
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
PROJECT_ROOT = Path(__file__).resolve().parent if '__file__' in globals() else Path.cwd()
TEMPLATES_DIR = PROJECT_ROOT / "templates"


def load_and_fill_template(template_candidates: list, replacements: Dict[str, str]) -> str:
    """Loads a Typst template file from TEMPLATES_DIR and populates placeholders."""
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
        content = content.replace(f"/*{{{{{key}}}}}*/", str(val))
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
    num_records = len(df)
    num_species = len(df['Scientific_name'].dropna().unique()) if 'Scientific_name' in df.columns else 0
    total_weight = df['weight'].sum() if 'weight' in df.columns else 0.0

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
    df_clean = df[df['test'] != 'yes'].copy() if 'test' in df.columns else df.copy()

    total_transplanted = 0
    total_reefstars = 0
    total_nursery_tables = 0
    total_area_ha = 0.0

    if not df_clean.empty and 'site_name' in df_clean.columns:
        if 'total_fragments_transplanted_to_date' in df_clean.columns:
            total_transplanted = int(np.nansum(df_clean.groupby('site_name')['total_fragments_transplanted_to_date'].apply(lambda x: pd.to_numeric(x, errors='coerce').max())))
        if 'total_reef_starts_deployed_to_date' in df_clean.columns:
            total_reefstars = int(np.nansum(df_clean.groupby('site_name')['total_reef_starts_deployed_to_date'].apply(lambda x: pd.to_numeric(x, errors='coerce').max())))
        if 'total_tables_in_nursery_to_date' in df_clean.columns:
            total_nursery_tables = int(np.nansum(df_clean.groupby('site_name')['total_tables_in_nursery_to_date'].apply(lambda x: pd.to_numeric(x, errors='coerce').max())))
        total_area_ha = (total_transplanted / 2) / 1e4

    start_date = metadata.get('start_date', 'N/A')
    end_date = metadata.get('end_date', 'N/A')
    sites = metadata.get('selected_sites', [])
    cleaned_sites = [clean_label(s) for s in sites]
    sites_str = ", ".join(cleaned_sites) if cleaned_sites else "All Restoration Project Sites"
    if len(sites_str) > 70:
        sites_str = f"{len(cleaned_sites)} sites selected ({', '.join(cleaned_sites[:4])}...)"

    site_table_rows = []
    if not df_clean.empty and 'site_name' in df_clean.columns:
        agg_dict = {
            'total_fragments_in_nursery_to_date': lambda x: pd.to_numeric(x, errors='coerce').max(),
            'total_fragments_transplanted_to_date': lambda x: pd.to_numeric(x, errors='coerce').max(),
            '_uuid': 'count'
        }
        if 'site_type' in df_clean.columns:
            agg_dict['site_type'] = 'first'

        site_grp = df_clean.groupby('site_name', as_index=False).agg(agg_dict)
        for _, row in site_grp.iterrows():
            raw_name = str(row['site_name'])
            s_name = typst_escape(clean_label(raw_name))
            raw_type = row.get('site_type')
            if pd.isna(raw_type) or not str(raw_type).strip():
                raw_type = 'nursery' if 'nursery' in raw_name.lower() else 'transplanting'
            s_type = typst_escape(clean_label(raw_type))

            if str(raw_type).lower() == 'transplanting' and pd.notna(row['total_fragments_transplanted_to_date']):
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
    """Main entry point for generating the A0 poster."""
    if metadata is None:
        metadata = {}

    if output_dir is None:
        base_dir = Path(__file__).resolve().parent if '__file__' in globals() else Path.cwd()
        work_dir = base_dir / "posters" / report_type
    else:
        work_dir = Path(output_dir)
    work_dir.mkdir(parents=True, exist_ok=True)

    figures_dir = work_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    logo_filename = "wcs_logo.png"
    target_logo = figures_dir / logo_filename

    base_script_dir = Path(__file__).resolve().parent if '__file__' in globals() else Path.cwd()
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
        fig, ax = plt.subplots(figsize=(2, 2))
        ax.text(0.5, 0.5, "WCS", fontsize=30, ha='center', va='center', fontweight='bold', color='#0284c7')
        ax.axis('off')
        plt.savefig(target_logo, bbox_inches='tight', transparent=True)
        plt.close(fig)

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

    typ_path = work_dir / f"{prefix}.typ"
    typ_path.write_text(typst_markup, encoding='utf-8')

    master_tpl = TEMPLATES_DIR / "master_template.typ"
    if not master_tpl.exists():
        master_tpl = work_dir.parent.parent / "templates" / "master_template.typ"

    master_dst = work_dir / "master_template.typ"
    if master_tpl.exists():
        shutil.copy2(master_tpl, master_dst)
    else:
        raise FileNotFoundError(f"Could not find master_template.typ in {TEMPLATES_DIR}")

    zip_path = work_dir / f"{prefix}_bundle.zip"
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(typ_path, arcname=typ_path.name)
        zipf.write(master_dst, arcname="master_template.typ")
        for fig_file in figures_dir.glob("*.png"):
            zipf.write(fig_file, arcname=f"figures/{fig_file.name}")

    zip_bytes = zip_path.read_bytes()

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


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate an A0 scientific poster using Typst from CatchViz CSV data.")
    parser.add_argument("--type", choices=["bony_fishes", "sharks_rays", "restoration"], default="bony_fishes", help="Report type")
    parser.add_argument("--csv", type=str, required=True, help="Path to input CSV file")
    parser.add_argument("--output-dir", type=str, default="./poster_output", help="Output directory")

    args = parser.parse_args()

    df_data = pd.read_csv(args.csv, low_memory=False)
    if args.type == "restoration" and 'test' in df_data.columns:
        df_data = df_data[df_data['test'] != 'yes']

    out_dir = Path(args.output_dir)
    if args.type == "restoration" and 'project_site' in df_data.columns:
        cli_sites = df_data['project_site'].dropna().unique().tolist()
    elif 'landing_site' in df_data.columns:
        cli_sites = df_data['landing_site'].dropna().unique().tolist()
    else:
        cli_sites = []

    result = generate_poster(
        df=df_data,
        report_type=args.type,
        output_dir=out_dir,
        metadata={
            'start_date': 'All available dates',
            'end_date': 'Latest records',
            'selected_sites': cli_sites
        }
    )

    print(result['message'])
    if result['pdf_path']:
        print(f"PDF Output: {result['pdf_path']}")
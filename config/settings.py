from pathlib import Path
import os

# Base Directories
BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "config"
REFERENCE_DIR = CONFIG_DIR / "reference"
DATA_DIR = BASE_DIR / "data"
DATA_RAW_DIR = DATA_DIR / "raw"
DATA_PROCESSED_DIR = DATA_DIR / "processed"
ASSETS_DIR = BASE_DIR / "assets"
IMG_DIR = ASSETS_DIR / "img"
CSS_DIR = ASSETS_DIR / "css"

# KoboToolbox API Settings
KOBO_BASE_URL = "https://kf.kobotoolbox.org/api/v2/assets"
ASSET_UIDS = {
    "SHARK": "aaknL3DQQgkgZ8iay89X5P",
    "CATCH": "a7bZivgzH5Y6kxP2nhG98w",
    "RESTORATION": "aCCZTXLPwc4am5GfuAa7qV"
}

# GitHub Sync Settings
DEFAULT_GITHUB_REPO = "jungla/CatchViz"

# Protected Species Catalog URL
PROTECTED_SPECIES_URL = (
    "https://docs.google.com/spreadsheets/d/1N8ts_6x-zI2QYiQt7HwX3cyvZaWtUTaU2IlxqRY5qzY/export?format=csv&gid=1557232272"
)

def get_data_filepath(filename: str) -> Path:
    """Resolve file path prioritizing data/processed/, falling back to project root."""
    processed_path = DATA_PROCESSED_DIR / filename
    if processed_path.is_file():
        return processed_path
    root_path = BASE_DIR / filename
    if root_path.is_file():
        return root_path
    return processed_path

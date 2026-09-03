import os
import requests
import datetime
from pathlib import Path
from typing import Tuple
from config.settings import KOBO_BASE_URL

class KoboClient:
    def __init__(self, api_token: str = None):
        self.api_token = api_token or os.environ.get("KOBO_TOKEN", "")
        if not self.api_token:
            raise ValueError("KOBO_TOKEN is not set. Please set the KOBO_TOKEN environment variable.")
        self.headers = {"Authorization": f"Token {self.api_token}"}

    def get_total_records(self, asset_uid: str) -> int:
        """Fetch total record count for an asset."""
        endpoint = f"{KOBO_BASE_URL}/{asset_uid}/data/?limit=1"
        resp = requests.get(endpoint, headers=self.headers)
        resp.raise_for_status()
        return resp.json().get("count", 0)

    def get_boundary_ids(self, asset_uid: str, start_idx: int, end_idx: int) -> Tuple[int, int]:
        """Fetch the database _id for start and end record positions."""
        endpoint = f"{KOBO_BASE_URL}/{asset_uid}/data/"
        
        start_resp = requests.get(f"{endpoint}?limit=1&start={start_idx}", headers=self.headers)
        start_resp.raise_for_status()
        start_id = start_resp.json().get("results", [{}])[0].get("_id")

        end_resp = requests.get(f"{endpoint}?limit=1&start={end_idx}", headers=self.headers)
        end_resp.raise_for_status()
        end_id = end_resp.json().get("results", [{}])[0].get("_id")

        return start_id, end_id

    def create_export_setting(self, asset_uid: str, start_id: int, end_id: int) -> str:
        """Create an export task for given record ID bounds and return download URL."""
        payload = {
            "name": str(datetime.datetime.now()),
            "source": f"{KOBO_BASE_URL}/{asset_uid}/",
            "type": "xls",
            "export_settings": {
                "lang": "_xml",
                "fields_from_all_versions": False,
                "group_sep": "/",
                "hierarchy_in_labels": False,
                "multiple_select": "both",
                "type": "xls",
                "query": {
                    "_id": {
                        "$gte": start_id,
                        "$lte": end_id,
                    }
                }
            }
        }
        resp = requests.post(f"{KOBO_BASE_URL}/{asset_uid}/export-settings/", headers=self.headers, json=payload)
        resp.raise_for_status()
        return resp.json().get("url")

    def download_data(self, download_url: str, output_path: Path):
        """Stream download the export xlsx file."""
        api_url = download_url if download_url.endswith("data.xlsx") else download_url + "data.xlsx"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with requests.get(api_url, headers=self.headers, stream=True) as r:
            r.raise_for_status()
            with open(output_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

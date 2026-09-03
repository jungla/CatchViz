import os
import glob
import argparse
from pathlib import Path
import pandas as pd
from config.settings import (
    ASSET_UIDS,
    DATA_RAW_DIR,
    DATA_PROCESSED_DIR,
    BASE_DIR,
    DEFAULT_GITHUB_REPO
)
from src.etl.kobo_client import KoboClient
from src.etl.transformers import transform_chunk
from src.etl.github_sync import upload_to_github

def run_dataset_sync(
    dataset: str,
    client: KoboClient = None,
    chunk_size: int = 5000,
    upload: bool = False
):
    """Sync a single dataset from KoboToolbox, process chunks, and save to CSV."""
    print(f"\n==================== Syncing Dataset: {dataset} ====================")
    asset_uid = ASSET_UIDS.get(dataset)
    if not asset_uid:
        print(f"Unknown dataset: {dataset}. Available: {list(ASSET_UIDS.keys())}")
        return

    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Clean incomplete/partial chunks only if client is connected to re-fetch them
    if client:
        existing_chunks = glob.glob(str(DATA_RAW_DIR / f"{dataset}*kobo_data.xlsx"))
        for f in existing_chunks:
            if not f.endswith("999_kobo_data.xlsx"):
                try:
                    os.remove(f)
                    print(f"Deleted incomplete chunk: {Path(f).name}")
                except OSError:
                    pass

    # 2. Check total records and download new chunks
    if client:
        trec = client.get_total_records(asset_uid)
        print(f"Total remote records: {trec}")

        if trec >= chunk_size:
            num_full_chunks = int(trec / chunk_size)
            for i in range(num_full_chunks):
                start_rec = i * chunk_size
                end_rec = (i + 1) * chunk_size - 1
                chunk_name = f"{dataset}_{start_rec}_{end_rec}_kobo_data.xlsx"
                chunk_file = DATA_RAW_DIR / chunk_name

                if not chunk_file.exists():
                    print(f"Downloading chunk: {chunk_name}")
                    start_id, end_id = client.get_boundary_ids(asset_uid, start_rec, end_rec)
                    url = client.create_export_setting(asset_uid, start_id, end_id)
                    client.download_data(url, chunk_file)

            # Last partial chunk
            start_rec = num_full_chunks * chunk_size
            end_rec = num_full_chunks * chunk_size + (trec % chunk_size)
            chunk_name = f"{dataset}_{start_rec}_{end_rec}_kobo_data.xlsx"
            chunk_file = DATA_RAW_DIR / chunk_name
            print(f"Downloading final chunk: {chunk_name}")
            start_id, end_id = client.get_boundary_ids(asset_uid, start_rec, max(start_rec, end_rec - 1))
            url = client.create_export_setting(asset_uid, start_id, end_id)
            client.download_data(url, chunk_file)
        else:
            start_rec = 0
            end_rec = max(0, trec - 1)
            chunk_name = f"{dataset}_{start_rec}_{end_rec}_kobo_data.xlsx"
            chunk_file = DATA_RAW_DIR / chunk_name
            if not chunk_file.exists():
                print(f"Downloading short chunk: {chunk_name}")
                start_id, end_id = client.get_boundary_ids(asset_uid, start_rec, end_rec)
                url = client.create_export_setting(asset_uid, start_id, end_id)
                client.download_data(url, chunk_file)

    # 3. Process all downloaded xlsx files into one CSV
    chunk_files = sorted(glob.glob(str(DATA_RAW_DIR / f"{dataset}*xlsx")))
    print(f"Processing {len(chunk_files)} chunk files into CSV...")

    all_data = pd.DataFrame()
    for fpath in chunk_files:
        print(f" - Processing: {Path(fpath).name}")
        chunk_df = transform_chunk(dataset, Path(fpath))
        all_data = pd.concat([all_data, chunk_df], ignore_index=True)

    csv_name = f"{dataset}_kobo_data.csv"
    processed_out = DATA_PROCESSED_DIR / csv_name
    all_data.to_csv(processed_out, index=False)
    print(f"Saved processed data to: {processed_out} ({len(all_data)} rows)")

    # Keep a copy in base dir for backward compatibility
    legacy_out = BASE_DIR / csv_name
    all_data.to_csv(legacy_out, index=False)

    # 4. Optional GitHub Upload
    if upload:
        upload_to_github(processed_out, repo_name=DEFAULT_GITHUB_REPO)

def main():
    parser = argparse.ArgumentParser(description="KoboToolbox Data Sync & ETL Pipeline")
    parser.add_argument(
        "--dataset",
        choices=["ALL", "CATCH", "SHARK", "RESTORATION"],
        default="ALL",
        help="Dataset to sync"
    )
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Skip API download and process existing raw xlsx files in data/raw/"
    )
    parser.add_argument(
        "--upload",
        action="store_true",
        help="Upload generated CSVs to GitHub"
    )
    args = parser.parse_args()

    client = None
    if not args.skip_download:
        kobo_token = os.environ.get("KOBO_TOKEN")
        if kobo_token:
            client = KoboClient(kobo_token)
        else:
            print("WARNING: KOBO_TOKEN not found in environment. Running in offline/process-only mode.")

    datasets_to_sync = (
        ["CATCH", "SHARK", "RESTORATION"]
        if args.dataset == "ALL"
        else [args.dataset]
    )

    for ds in datasets_to_sync:
        run_dataset_sync(ds, client=client, upload=args.upload)

if __name__ == "__main__":
    main()

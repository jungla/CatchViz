"""
Legacy entrypoint for KoboToolbox data sync.
Delegates to `src.etl.pipeline`.
Usage:
    python get_kobo_data.py
    python -m src.etl.pipeline --dataset CATCH
"""
from src.etl.pipeline import main

if __name__ == "__main__":
    main()

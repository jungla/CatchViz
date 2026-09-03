# 🎣 WCS Tanzania Marine CatchViz Platform

An interactive **Streamlit** visualization platform for the Wildlife Conservation Society (WCS) Tanzania Marine Program. The application monitors and visualizes fisheries landings, shark and ray catches with IUCN Red List indicators, marine protected species, and coral reef restoration projects along the coast of Tanzania and Zanzibar.

---

## 🌟 Modules & Dashboards

1. **🐠 Bony Fishes Landings** ([pages/1_bony_fishes.py](pages/1_bony_fishes.py)):
   - Interactive landing site maps using PyDeck
   - Catch Per Unit Effort (CPUE) analysis with regression trends
   - Sampling effort, gear types, vessel types, and species group breakdowns
2. **🦈 Sharks and Rays** ([pages/2_sharks_and_rays.py](pages/2_sharks_and_rays.py)):
   - IUCN Red List threat classification analysis
   - Size-at-maturity ratios (juvenile vs. adult distribution)
   - Sex ratios, targeted fishery indicators, and fishing gear types
3. **🐋 Marine Protected Species List** ([pages/3_protected_species.py](pages/3_protected_species.py)):
   - Inventory catalog of Zanzibar marine protected taxa
   - Filter by provision status (*Always Release*, *Only Consumption*, *Research Only*)
   - Grid and table views with search and images
4. **🌊 Coral Reef Restoration** ([pages/4_restoration.py](pages/4_restoration.py)):
   - GPS mapping of nursery and transplanting sites
   - Cumulative counts of transplanted corals and nursery stock
   - Total restored reef area estimates (ha)

---

## 📁 Project Structure

```text
CatchViz/
├── .streamlit/
│   ├── config.toml               # Streamlit theme & UI settings
│   └── secrets.toml.example      # Example secrets template
├── assets/
│   ├── css/                      # Centralized stylesheets (typography, cards)
│   └── img/                      # WCS logos & visual assets
├── config/
│   ├── settings.py               # Application paths, constants, and API endpoints
│   └── reference/                # Domain reference data
│       ├── iucn_species.csv      # IUCN Red List & size-at-maturity benchmarks
│       └── restoration_sites.csv # Restoration nursery & transplant GPS coordinates
├── data/
│   ├── raw/                      # Temporary batch download chunks (*.xlsx) [gitignored]
│   └── processed/                # Curated CSV files consumed by dashboard
├── pages/                        # Multi-page Streamlit dashboards
│   ├── 1_bony_fishes.py
│   ├── 2_sharks_and_rays.py
│   ├── 3_protected_species.py
│   └── 4_restoration.py
├── src/                          # Core reusable application packages
│   ├── data_loader.py            # Cached data loaders (@st.cache_data)
│   ├── components/               # Reusable UI headers, filters, and PyDeck maps
│   └── etl/                      # Standalone KoboToolbox ETL sync pipeline
│       ├── kobo_client.py        # API client for KoboToolbox v2
│       ├── transformers.py       # Data cleaning & schema alignment
│       ├── github_sync.py        # GitHub publishing integration
│       └── pipeline.py           # Sync pipeline runner
├── .env.example                  # Template for environment variables
├── .gitignore                    # Git hygiene rules
├── app.py                        # Main Streamlit application entrypoint
├── requirements.txt              # Python dependencies
└── README.md
```

---

## 🚀 Quickstart

### 1. Installation

Clone the repository and install required packages:

```bash
git clone https://github.com/jungla/CatchViz.git
cd CatchViz
pip install -r requirements.txt
```

### 2. Run the Dashboard

Launch the application using Streamlit:

```bash
streamlit run app.py
```

*(Note: `streamlit run home.py` also continues to work as a backward-compatible alias.)*

---

## 🔄 Data Ingestion & ETL (KoboToolbox Sync)

The project includes an automated ETL pipeline that downloads survey submissions from KoboToolbox in 5,000-row chunks, processes survey data, and saves production-ready CSVs into `data/processed/`.

### Configuration

Copy `.env.example` to `.env` or set environment variables:

```bash
export KOBO_TOKEN="your_kobotoolbox_api_token"
export GIT_TOKEN="your_github_token" # optional, for pushing daily updates to GitHub
```

### Running Sync

Sync all datasets (`CATCH`, `SHARK`, `RESTORATION`):

```bash
python -m src.etl.pipeline
```

Sync a specific dataset:

```bash
python -m src.etl.pipeline --dataset CATCH
```

Process existing raw files without re-downloading from API:

```bash
python -m src.etl.pipeline --skip-download
```

---

## 📄 License & Attribution

- Data collected via [KoboToolbox](https://www.kobotoolbox.org/) by the Wildlife Conservation Society (WCS) Tanzania Marine Program.
- Raw data repository: [Zenodo 15229813](https://zenodo.org/records/15229813).

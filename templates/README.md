# CatchViz Typst Poster Templates

This directory contains strictly **three** Typst (`.typ`) templates for generating A0 scientific posters:

| Template File | Dataset | Description |
|---|---|---|
| [`catch_template.typ`](file:///Users/jeanmensa/My%20Drive%20(jmensa@wcs.org)/WCS%20Tanzania%20Marine%20Program/Research/Analysis/Streamlit/CatchViz/templates/catch_template.typ) | **Catch Data** (Artisanal Bony Fishes) | 2-column A0 poster for artisanal fish catches, vessels, gears, and CPUE. |
| [`elasmobranchs_template.typ`](file:///Users/jeanmensa/My%20Drive%20(jmensa@wcs.org)/WCS%20Tanzania%20Marine%20Program/Research/Analysis/Streamlit/CatchViz/templates/elasmobranchs_template.typ) | **Elasmobranchs Data** (Sharks & Rays) | 2-column A0 poster for shark and ray landings, sizes, and IUCN threat status. |
| [`restoration_template.typ`](file:///Users/jeanmensa/My%20Drive%20(jmensa@wcs.org)/WCS%20Tanzania%20Marine%20Program/Research/Analysis/Streamlit/CatchViz/templates/restoration_template.typ) | **Restoration Data** (Coral Reefs) | 3-column A0 single-page poster for nursery capacity, outplanting, and reef stars. |

---

## How to Customize

You can open any of these 3 template files in your editor and freely modify:
- **Fonts & Typography**: change font families (e.g. `font: ("Liberation Sans", ...)`), text size, weights.
- **Colors & Styles**: modify RGB colors for header banners, cards, text, and borders.
- **Static Text & Descriptions**: customize program background, study site descriptions, citations, or policy notes.
- **Layout & Structure**: alter grid dimensions, add/remove cards, or adjust padding and margins.

---

## Dynamic Data Placeholders (Injected by CatchViz)

During poster generation, CatchViz creates the high-resolution charts in `figures/` and automatically populates the placeholders below with the currently filtered data:

### Common to All Templates
- `{{START_DATE}}`: Earliest date in the filtered dataset
- `{{END_DATE}}`: Latest date in the filtered dataset
- `{{SELECTED_SITES}}`: Summary string of selected landing/restoration sites
- `{{LOGO_FILENAME}}`: WCS logo (`wcs_logo.png`)
- `{{GENERATED_TIME}}`: Date and time of export

### Catch Data (`catch_template.typ`)
- `{{TOTAL_CATCH}}`: Total recorded weight with units (e.g. `12,450.5 kg`)
- `{{NUM_RECORDS}}`: Total landing records (e.g. `3,200`)
- `{{AVG_CATCH}}`: Average catch per trip (e.g. `14.85 kg`)
- `{{NUM_SITES}}`: Number of monitored landing sites
- `{{SITE_TABLE_ROWS}}`: Top landing sites summary table rows

### Elasmobranchs Data (`elasmobranchs_template.typ`)
- `{{NUM_RECORDS}}`: Total sampled individuals (e.g. `1,420`)
- `{{NUM_SPECIES}}`: Number of distinct species identified (e.g. `24`)
- `{{TOTAL_WEIGHT}}`: Total sampled biomass (e.g. `8,920.0 kg`)
- `{{THREAT_PCT}}`: Percentage of sampled catch in IUCN threatened categories (CR / EN / VU)
- `{{THREAT_COUNT}}`: Total count of threatened individuals

### Restoration Data (`restoration_template.typ`)
- `{{TOTAL_TRANSPLANTED}}`: Cumulative coral fragments transplanted
- `{{RESTORED_AREA_HA}}`: Estimated restored reef area in hectares
- `{{TOTAL_REEFSTARS}}`: Cumulative reef stars deployed
- `{{TOTAL_NURSERY_TABLES}}`: Active mid-water nursery tables
- `{{SITE_TABLE_ROWS}}`: Restoration sites summary table rows

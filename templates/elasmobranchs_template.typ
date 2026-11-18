// CatchViz - Elasmobranchs (Sharks & Rays) Landings A0 Poster Template
// You can freely edit this file to customize fonts, colors, text, styles, and layout.
// Dynamic values inside {{...}} are populated automatically by CatchViz during poster export.

// =============================================================================
// PAGE & TYPOGRAPHY SETUP
// =============================================================================
#set page(
  paper: "a0",
  flipped: false,
  margin: (x: 2.2cm, top: 2.2cm, bottom: 2.2cm),
  fill: rgb("#f8fafc")
)

#set text(
  font: ("Liberation Sans", "DejaVu Sans", "Helvetica", "Arial"),
  size: 21pt,
  fill: rgb("#0f172a")
)

// =============================================================================
// DYNAMIC METADATA & DATA VARIABLES (Updated automatically on export)
// =============================================================================
#let start_date = "{{START_DATE}}"
#let end_date = "{{END_DATE}}"
#let selected_sites = "{{SELECTED_SITES}}"
#let num_records = "{{NUM_RECORDS}}"
#let num_species = "{{NUM_SPECIES}}"
#let total_weight = "{{TOTAL_WEIGHT}}"
#let threat_pct = "{{THREAT_PCT}}"
#let threat_count = "{{THREAT_COUNT}}"
#let logo_filename = "{{LOGO_FILENAME}}"

// =============================================================================
// REUSABLE COMPONENTS
// =============================================================================
#let card(title: none, icon: none, body) = block(
  width: 100%,
  fill: white,
  inset: 24pt,
  radius: 14pt,
  stroke: 1.5pt + rgb("#e2e8f0"),
  [
    #if title != none [
      #block(
        width: 100%,
        inset: (bottom: 12pt),
        stroke: (bottom: 2.5pt + rgb("#ea580c")),
        [
          #text(weight: "bold", size: 28pt, fill: rgb("#c2410c"))[
            #if icon != none [#icon ] #title
          ]
        ]
      )
      #v(10pt)
    ]
    #body
  ]
)

#let kpi_card(value: "", label: "", icon: "", sublabel: none, border_color: rgb("#ea580c"), num_color: rgb("#c2410c")) = block(
  fill: white,
  inset: 22pt,
  radius: 12pt,
  stroke: 2pt + border_color,
  width: 100%,
  align(center)[
    #if icon != "" [#text(size: 28pt)[#icon] \ #v(4pt)]
    #text(weight: "extrabold", size: 52pt, fill: num_color)[#value] \
    #v(4pt)
    #text(weight: "bold", size: 22pt, fill: rgb("#1e293b"))[#label]
    #if sublabel != none [
      \ #v(2pt)
      #text(size: 16pt, fill: rgb("#64748b"))[#sublabel]
    ]
  ]
)

// =============================================================================
// HEADER BANNER
// =============================================================================
#block(
  fill: rgb("#0b2545"),
  inset: (x: 32pt, y: 26pt),
  radius: 16pt,
  width: 100%,
  [
    #grid(
      columns: (180pt, 1fr, 180pt),
      align: (center + horizon, left + horizon, center + horizon),
      image("figures/" + logo_filename, width: 150pt),
      pad(left: 20pt)[
        #text(fill: rgb("#fed7aa"), weight: "bold", size: 24pt)[WCS TANZANIA MARINE PROGRAM • ELASMOBRANCH MONITORING] \
        #v(6pt)
        #text(fill: white, weight: "extrabold", size: 52pt)[Sharks & Rays Landings] \
        #v(8pt)
        #text(fill: rgb("#e2e8f0"), size: 22pt)[
          *Reporting Period:* #start_date to #end_date #h(18pt) | #h(18pt) *Sites & Markets:* #selected_sites
        ]
      ],
      align(center)[
        #block(
          fill: rgb("#ea580c"),
          inset: 16pt,
          radius: 10pt,
          text(fill: white, weight: "bold", size: 20pt)[A0 SUMMARY\nREPORT]
        )
      ]
    )
  ]
)

#v(18pt)

// =============================================================================
// KPI STATS ROW
// =============================================================================
#grid(
  columns: (1fr, 1fr, 1fr, 1fr),
  gutter: 18pt,
  kpi_card(value: num_records, label: "Total Landings Sampled", icon: "🦈", border_color: rgb("#ea580c"), num_color: rgb("#ea580c")),
  kpi_card(value: num_species, label: "Identified Species", icon: "🧬", border_color: rgb("#0284c7"), num_color: rgb("#0284c7")),
  kpi_card(value: total_weight, label: "Total Weight Recorded", icon: "⚖️", border_color: rgb("#0d9488"), num_color: rgb("#0d9488")),
  kpi_card(value: threat_pct, label: "Threatened (CR / EN / VU)", icon: "⚠️", sublabel: threat_count + " IUCN Red List Individuals", border_color: rgb("#dc2626"), num_color: rgb("#dc2626"))
)

#v(20pt)

// =============================================================================
// MAIN CONTENT GRID (2 COLUMNS)
// =============================================================================
#grid(
  columns: (1fr, 1fr),
  gutter: 22pt,
  [
    // COLUMN 1
    #card(title: "Geographic Landings & Sampling Footprint", icon: "🗺️")[
      #image("figures/fig_map.png", width: 100%)
      #v(6pt)
      #text(size: 18pt, fill: rgb("#475569"))[
        Artisanal elasmobranch monitoring locations along mainland Tanzania and Zanzibar. Marker sizes indicate sampling intensity and landed volumes.
      ]
    ]

    #v(16pt)
    #card(title: "IUCN Red List Conservation Status", icon: "🚨")[
      #image("figures/fig_iucn.png", width: 100%)
      #v(6pt)
      #text(size: 18pt, fill: rgb("#475569"))[
        Distribution of sampled individuals across IUCN Red List categories (Critically Endangered, Endangered, Vulnerable, Near Threatened, Least Concern).
      ]
    ]

    #v(16pt)
    #card(title: "Top Landed Elasmobranch Species", icon: "📋")[
      #image("figures/fig_top_species.png", width: 100%)
      #v(6pt)
      #text(size: 18pt, fill: rgb("#475569"))[
        Most frequently recorded shark and ray taxa in the artisanal fishery, ranked by specimen count and aggregated landed biomass.
      ]
    ]

    #v(16pt)
    #card(title: "Maturity & Size-Frequency Distribution", icon: "📐")[
      #image("figures/fig_size_dist.png", width: 100%)
      #v(6pt)
      #text(size: 18pt, fill: rgb("#475569"))[
        Morphometric size distributions (Total Length, Disc Width) relative to published size-at-maturity (Lm) thresholds.
      ]
    ]
  ],
  [
    // COLUMN 2
    #card(title: "Survey Effort & Seasonality", icon: "📈")[
      #image("figures/fig_effort.png", width: 100%)
      #v(6pt)
      #text(size: 18pt, fill: rgb("#475569"))[
        Temporal monitoring frequency across sampling sites, capturing seasonality and sampling intensity throughout the survey period.
      ]
    ]

    #v(16pt)
    #card(title: "Fishing Gear Composition", icon: "🕸️")[
      #image("figures/fig_gear.png", width: 100%)
      #v(6pt)
      #text(size: 18pt, fill: rgb("#475569"))[
        Key gear types associated with elasmobranch captures, with small-mesh and large-mesh gill nets and hook & line predominating.
      ]
    ]

    #v(16pt)
    #card(title: "Sex Ratio (Female / Male)", icon: "⚖️")[
      #image("figures/fig_sex_ratio.png", width: 100%)
      #v(6pt)
      #text(size: 18pt, fill: rgb("#475569"))[
        Ratio of landed female to male specimens across species, providing critical insights into reproductive population structure.
      ]
    ]

    #v(16pt)
    #card(title: "Conservation & Policy Implications", icon: "🛡️")[
      #text(size: 19pt, fill: rgb("#334155"))[
        *Prevalence of Immature Catches:* The significant fraction of juvenile individuals reinforces the urgent need to delineate and protect critical coastal nursery areas. \
        *CITES & National Action:* Several landed species (e.g. Hammerheads, Wedgefish, Guitarfish) are listed under CITES Appendix II. Strengthening collaborative management with BMUs is vital for long-term population sustainability.
      ]
    ]
  ]
)

#v(20pt)

// =============================================================================
// FOOTER BANNER
// =============================================================================
#block(
  fill: rgb("#0b2545"),
  inset: 18pt,
  radius: 12pt,
  width: 100%,
  [
    #grid(
      columns: (1fr, 1fr),
      align: (left + horizon, right + horizon),
      text(fill: rgb("#cbd5e1"), size: 18pt)[
        Wildlife Conservation Society (WCS) Tanzania • Marine Program \
        Science-based conservation for sharks, rays, and coastal marine habitats.
      ],
      text(fill: rgb("#94a3b8"), size: 16pt)[
        Exported from CatchViz • Formatted with Typst • Generated: {{GENERATED_TIME}}
      ]
    )
  ]
)

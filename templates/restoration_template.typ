// CatchViz - Coral Reef Restoration A0 Poster Template
// You can freely edit this file to customize fonts, colors, text, styles, and layout.
// Dynamic values inside {{...}} are populated automatically by CatchViz during poster export.

// =============================================================================
// PAGE & TYPOGRAPHY SETUP
// =============================================================================
#set page(
  paper: "a0",
  flipped: false,
  margin: (x: 2cm, top: 2cm, bottom: 2cm),
  fill: rgb("#f8fafc")
)

#set text(
  font: ("Liberation Sans", "DejaVu Sans", "Helvetica", "Arial"),
  size: 20pt,
  fill: rgb("#0f172a")
)

// =============================================================================
// DYNAMIC METADATA & DATA VARIABLES (Updated automatically on export)
// =============================================================================
#let start_date = "{{START_DATE}}"
#let end_date = "{{END_DATE}}"
#let selected_sites = "{{SELECTED_SITES}}"
#let total_transplanted = "{{TOTAL_TRANSPLANTED}}"
#let total_reefstars = "{{TOTAL_REEFSTARS}}"
#let total_nursery_tables = "{{TOTAL_NURSERY_TABLES}}"
#let total_area_ha = "{{RESTORED_AREA_HA}}"
#let logo_filename = "{{LOGO_FILENAME}}"

// =============================================================================
// REUSABLE COMPONENTS
// =============================================================================
#let card(title: none, icon: none, body) = block(
  width: 100%,
  fill: white,
  inset: 18pt,
  radius: 12pt,
  stroke: 1.5pt + rgb("#e2e8f0"),
  [
    #if title != none [
      #block(
        width: 100%,
        inset: (bottom: 10pt),
        stroke: (bottom: 2.5pt + rgb("#0d9488")),
        [
          #text(weight: "bold", size: 24pt, fill: rgb("#0f766e"))[
            #if icon != none [#icon ] #title
          ]
        ]
      )
      #v(8pt)
    ]
    #body
  ]
)

#let kpi_card(value: "", label: "", icon: "", sublabel: none, border_color: rgb("#0d9488"), num_color: rgb("#0f766e")) = block(
  fill: white,
  inset: 16pt,
  radius: 10pt,
  stroke: 2pt + border_color,
  width: 100%,
  align(center)[
    #if icon != "" [#text(size: 24pt)[#icon] \ #v(2pt)]
    #text(weight: "extrabold", size: 42pt, fill: num_color)[#value] \
    #v(2pt)
    #text(weight: "bold", size: 19pt, fill: rgb("#1e293b"))[#label]
    #if sublabel != none [
      \ #v(1pt)
      #text(size: 15pt, fill: rgb("#64748b"))[#sublabel]
    ]
  ]
)

// =============================================================================
// HEADER BANNER
// =============================================================================
#block(
  fill: rgb("#042f2e"),
  inset: (x: 28pt, y: 20pt),
  radius: 14pt,
  width: 100%,
  [
    #grid(
      columns: (160pt, 1fr, 170pt),
      align: (center + horizon, left + horizon, center + horizon),
      image("figures/" + logo_filename, width: 130pt),
      pad(left: 18pt)[
        #text(fill: rgb("#99f6e4"), weight: "bold", size: 22pt)[WCS TANZANIA MARINE PROGRAM • CORAL REEF RESTORATION INITIATIVE] \
        #v(4pt)
        #text(fill: white, weight: "extrabold", size: 46pt)[Coral Reef Restoration Program] \
        #v(6pt)
        #text(fill: rgb("#e2e8f0"), size: 20pt)[
          *Reporting Period:* #start_date to #end_date #h(14pt) | #h(14pt) *Sites:* #selected_sites
        ]
      ],
      align(center)[
        #block(
          fill: rgb("#0d9488"),
          inset: 14pt,
          radius: 8pt,
          text(fill: white, weight: "bold", size: 18pt)[A0 SUMMARY\nREPORT]
        )
      ]
    )
  ]
)

#v(14pt)

// =============================================================================
// KPI STATS ROW
// =============================================================================
#grid(
  columns: (1fr, 1fr, 1fr, 1fr),
  gutter: 14pt,
  kpi_card(value: total_transplanted, label: "Corals Transplanted", icon: "🪸", border_color: rgb("#0d9488"), num_color: rgb("#0f766e")),
  kpi_card(value: total_area_ha, label: "Total Area Restored", icon: "📐", border_color: rgb("#0284c7"), num_color: rgb("#0284c7")),
  kpi_card(value: total_reefstars, label: "Reef Stars Deployed", icon: "⭐", border_color: rgb("#ea580c"), num_color: rgb("#ea580c")),
  kpi_card(value: total_nursery_tables, label: "Nursery Tables Active", icon: "🪵", border_color: rgb("#8b5cf6"), num_color: rgb("#7c3aed"))
)

#v(14pt)

// =============================================================================
// MAIN CONTENT GRID (3 COLUMNS)
// =============================================================================
#grid(
  columns: (1fr, 1fr, 1fr),
  gutter: 16pt,
  [
    // COLUMN 1
    #card(title: "Restoration Project Footprint", icon: "🗺️")[
      #image("figures/fig_map.png", width: 100%)
      #v(4pt)
      #text(size: 16pt, fill: rgb("#475569"))[
        Active coral restoration sites along the Tanzanian coastline including nursery tables and outplanting reefs.
      ]
    ]

    #v(12pt)
    #card(title: "Cumulative Restored Area (ha)", icon: "📈")[
      #image("figures/fig_area_trend.png", width: 100%)
      #v(4pt)
      #text(size: 16pt, fill: rgb("#475569"))[
        Progression of restored coral area (hectares) over time across monitored project locations.
      ]
    ]

    #v(12pt)
    #card(title: "Active Restoration Sites Overview", icon: "📋")[
      #table(
        columns: (1.5fr, 1.2fr, 1fr),
        align: (left, left, right),
        stroke: (x, y) => if y == 0 { (bottom: 2pt + rgb("#0d9488")) } else { (bottom: 0.5pt + rgb("#e2e8f0")) },
        fill: (col, row) => if row == 0 { rgb("#ccfbf1") } else if calc.even(row) { rgb("#f8fafc") } else { white },
        table.header(
          [*Site Name*], [*Site Type*], [*Fragments*]
        ),
{{SITE_TABLE_ROWS}}
      )
    ]
  ],
  [
    // COLUMN 2
    #card(title: "Field Activities Breakdown", icon: "⏱️")[
      #image("figures/fig_activity_days.png", width: 100%)
      #v(4pt)
      #text(size: 16pt, fill: rgb("#475569"))[
        Effort allocation across fragmentation, nursery maintenance, outplanting, and ecological monitoring.
      ]
    ]

    #v(12pt)
    #card(title: "Artificial Substrates Deployed", icon: "⭐")[
      #image("figures/fig_structures.png", width: 100%)
      #v(4pt)
      #text(size: 16pt, fill: rgb("#475569"))[
        Quantity of structural restoration units deployed to stabilize loose rubble and promote natural recruitment.
      ]
    ]

    #v(12pt)
    #card(title: "Substrate Attachment Methods", icon: "🪸")[
      #image("figures/fig_attachment.png", width: 100%)
      #v(4pt)
      #text(size: 16pt, fill: rgb("#475569"))[
        Coral fragment distributions across reef stars, mesh fence wires, and nursery tables.
      ]
    ]
  ],
  [
    // COLUMN 3
    #card(title: "Monthly Outplanting Output", icon: "🌿")[
      #image("figures/fig_session_transplanted.png", width: 100%)
      #v(4pt)
      #text(size: 16pt, fill: rgb("#475569"))[
        Monthly volume of coral colonies outplanted onto natural degraded reef substrate.
      ]
    ]

    #v(12pt)
    #card(title: "Mid-Water Nursery Capacity", icon: "🪸")[
      #image("figures/fig_nursery_stock.png", width: 100%)
      #v(4pt)
      #text(size: 16pt, fill: rgb("#475569"))[
        Active fragment inventories maintained across community nursery tables.
      ]
    ]

    #v(12pt)
    #card(title: "Restoration Framework", icon: "🛡️")[
      #text(size: 17pt, fill: rgb("#334155"))[
        *Community Stewardship:* Activities are co-managed with local Beach Management Units (BMUs) and coral reef committees. \
        *Ecosystem Resilience:* Outplanting thermally resilient genotypes accelerates recovery of damaged reefs, protecting shorelines and biodiversity.
      ]
    ]
  ]
)

#v(14pt)

// =============================================================================
// FOOTER BANNER
// =============================================================================
#block(
  fill: rgb("#042f2e"),
  inset: 14pt,
  radius: 10pt,
  width: 100%,
  [
    #grid(
      columns: (1fr, 1fr),
      align: (left + horizon, right + horizon),
      text(fill: rgb("#cbd5e1"), size: 16pt)[
        Wildlife Conservation Society (WCS) Tanzania • Marine Program \
        Coral Reef Restoration & Conservation Initiative • Monitored via KoboToolbox
      ],
      text(fill: rgb("#94a3b8"), size: 15pt)[
        Exported from CatchViz • Formatted with Typst A0 • Generated: {{GENERATED_TIME}}
      ]
    )
  ]
)

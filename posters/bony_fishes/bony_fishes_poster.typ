// CatchViz - Artisanal Bony Fishes Landings A0 Poster
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

// Reusable card container
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
        stroke: (bottom: 2.5pt + rgb("#0284c7")),
        [
          #text(weight: "bold", size: 28pt, fill: rgb("#0369a1"))[
            #if icon != none [#icon ] #title
          ]
        ]
      )
      #v(10pt)
    ]
    #body
  ]
)

// KPI Stat Box
#let kpi_card(value: "", label: "", icon: "", sublabel: none, border_color: rgb("#0284c7"), num_color: rgb("#0369a1")) = block(
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
      image("figures/wcs_logo.png", width: 150pt),
      pad(left: 20pt)[
        #text(fill: rgb("#93c5fd"), weight: "bold", size: 24pt)[WCS TANZANIA MARINE PROGRAM • CATCH MONITORING PLATFORM] \
        #v(6pt)
        #text(fill: white, weight: "extrabold", size: 52pt)[Landings of Bony Fishes] \
        #v(8pt)
        #text(fill: rgb("#e2e8f0"), size: 22pt)[
          *Reporting Period:* 2010-01-01 to 2026-10-29 #h(18pt) | #h(18pt) *Sites:* 28 sites selected (bwawani, chole, chwaka, fumba...)
        ]
      ],
      align(center)[
        #block(
          fill: rgb("#0284c7"),
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
  kpi_card(value: "345,939.8 kg", label: "Total Catch Recorded", icon: "⚖️", border_color: rgb("#0284c7"), num_color: rgb("#0284c7")),
  kpi_card(value: "36,350", label: "Landing Records", icon: "📋", border_color: rgb("#0d9488"), num_color: rgb("#0d9488")),
  kpi_card(value: "14.83 kg", label: "Average Catch / Trip", icon: "📊", border_color: rgb("#3b82f6"), num_color: rgb("#1d4ed8")),
  kpi_card(value: "28", label: "Monitored Landing Sites", icon: "📍", border_color: rgb("#8b5cf6"), num_color: rgb("#6d28d9"))
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
    #card(title: "Geographic Distribution of Landings", icon: "🗺️")[
      #image("figures/fig_map.png", width: 100%)
      #v(6pt)
      #text(size: 18pt, fill: rgb("#475569"))[
        Spatial distribution of artisanal landings along the Tanzanian coast. Circle sizes reflect the relative number of sampling records recorded at each landing site.
      ]
    ]

    #v(16pt)
    #card(title: "Sampling Effort Over Time", icon: "📈")[
      #image("figures/fig_effort.png", width: 100%)
      #v(6pt)
      #text(size: 18pt, fill: rgb("#475569"))[
        Monthly record counts across active monitoring sites, illustrating temporal survey coverage and landing intensity.
      ]
    ]

    #v(16pt)
    #card(title: "Catch Per Unit Effort (CPUE) Trends", icon: "⚡")[
      #image("figures/fig_cpue.png", width: 100%)
      #v(6pt)
      #text(size: 18pt, fill: rgb("#475569"))[
        CPUE (kg / fisher / hour) calculated across landing events with fitted linear regression trajectories.
      ]
    ]

    #v(16pt)
    #card(title: "Top Landing Sites Overview", icon: "📋")[
      #table(
        columns: (2fr, 1fr, 1fr),
        align: (left, right, right),
        stroke: (x, y) => if y == 0 { (bottom: 2pt + rgb("#0284c7")) } else { (bottom: 0.5pt + rgb("#e2e8f0")) },
        fill: (col, row) => if row == 0 { rgb("#e0f2fe") } else if calc.even(row) { rgb("#f8fafc") } else { white },
        table.header(
          [*Landing Site*], [*Records*], [*Total Catch (kg)*]
        ),
  [Moa], [5,343], [71,283.6],
  [Msuka], [3,602], [46,617.0],
  [Tongoni], [1,339], [39,310.4],
  [Sahare], [3,751], [36,752.0],
  [Mazizini], [2,400], [23,506.1],
  [Mkoani], [2,082], [19,154.6],
      )
    ]
  ],
  [
    // COLUMN 2
    #card(title: "Landings by Fishing Vessel Type", icon: "⛵")[
      #image("figures/fig_boat.png", width: 100%)
      #v(6pt)
      #text(size: 18pt, fill: rgb("#475569"))[
        Artisanal fleet composition categorized by vessel type across active landing operations.
      ]
    ]

    #v(16pt)
    #card(title: "Species Group Breakdown by Site", icon: "🐠")[
      #image("figures/fig_species_group.png", width: 100%)
      #v(6pt)
      #text(size: 18pt, fill: rgb("#475569"))[
        Composition of catch groups (reef fish, small pelagic, tuna-like) across monitored coastal landing locations.
      ]
    ]

    #v(16pt)
    #card(title: "Landings by Fishing Gear Type", icon: "🎣")[
      #image("figures/fig_gear.png", width: 100%)
      #v(6pt)
      #text(size: 18pt, fill: rgb("#475569"))[
        Frequency of fishing gears utilized across recorded artisanal fishing operations.
      ]
    ]

    #v(16pt)
    #card(title: "Effort Index by Vessel & Site", icon: "⏱️")[
      #image("figures/fig_vessel_effort.png", width: 100%)
      #v(6pt)
      #text(size: 18pt, fill: rgb("#475569"))[
        Composite fishing effort index accounting for fisher crew sizes and landed vessel frequency.
      ]
    ]

    #v(16pt)
    #card(title: "Program Methodology & Data Citation", icon: "ℹ️")[
      #text(size: 19pt, fill: rgb("#334155"))[
        *Monitoring Protocol:* Catch data are gathered via standardized KoboToolbox digital surveys by trained community data enumerators in collaboration with Beach Management Units (BMUs) and Fisheries Officers. \
        *Open Access Archive:* Datasets are curated and synchronized every 10 days. Primary records are deposited and openly accessible via Zenodo (DOI: 10.5281/zenodo.15229813).
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
        Protecting coral reefs, key marine ecosystems, and sustainable coastal livelihoods.
      ],
      text(fill: rgb("#94a3b8"), size: 16pt)[
        Exported from CatchViz • Formatted with Typst • Generated: 2026-11-18 16:04
      ]
    )
  ]
)

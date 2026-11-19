// CatchViz - Coral Reef Restoration A0 Poster Template
#import "master_template.typ": *

#let start_date = "2026-04-02"
#let end_date = "2026-10-30"
#let selected_sites = "Kigombe, Moa, Msuka"
#let total_transplanted = "120,400"
#let total_reefstars = "2,201"
#let total_nursery_tables = "11,724"
#let total_area_ha = "6.02 ha"
#let logo_filename = "wcs_logo.png"
#let site_rows = (
          [Nursery Kigombe], [Nursery], [13,612],
        [Nursery Kirui], [Nursery], [11,382],
        [Nursery Msuka], [Nursery], [15,271],
        [Transplanting Kigombe Taa], [Transplanting], [37,074],
        [Transplanting Kigome Makome], [Transplanting], [36,674],
        [Transplanting Kirui Corner], [Transplanting], [6,395],
        [Transplanting Kirui Shangani], [Transplanting], [15,467],
        [Transplanting Msuka Panga Punge], [Transplanting], [24,790],
)

#wcs_poster(
  rows: (1fr, 1fr, 1fr),
  gutter: 18pt,

  header: poster_header(
    logo_filename: logo_filename,
    kicker: "WCS TANZANIA MARINE PROGRAM  •  CORAL REEF RESTORATION INITIATIVE",
    title: "Coral Reef Restoration — Outplanting Progress, Nursery Stock & Field Effort",
    meta_items: (
      [*Program:* Reef Rehabilitation],
      [*Period:* #start_date to #end_date],
      [*Sites:* #selected_sites],
    ),
    badge_text: "A0 RESTORATION\nBRIEF",
    kpis: (
      banner_kpi(value: total_transplanted, label: "Corals Transplanted"),
      banner_kpi(value: total_area_ha, label: "Total Area Restored"),
      banner_kpi(value: total_reefstars, label: "Reef Stars Deployed"),
      banner_kpi(value: total_nursery_tables, label: "Nursery Tables Active"),
    ),
  ),

  footer: poster_footer(
    protocol_title: "Restoration Framework & Community Co-Management",
    protocol_body: [
      *Community Stewardship:* Activities are co-managed with local Beach Management Units (BMUs) and coral reef committees via KoboToolbox field tracking.
      #h(16pt) • #h(16pt)
      *Ecosystem Resilience:* Outplanting thermally resilient genotypes accelerates structural recovery of degraded reefs, supporting coastal fisheries and shoreline protection.
    ],
    generated_time: "2026-11-19 13:34",
  ),

  // ROW 1, COL 1
  card(
    title: "Where are coral nurseries and outplanting reefs located?",
    subtitle: "Active restoration project footprints scaled by nursery and outplanted fragment volumes.",
    takeaway: [
      *What this shows:* Spatial pairing of mid-water coral nurseries with nearby degraded reef sites minimizes fragment transport stress during outplanting.
    ],
  )[
    #image("figures/fig_map.png", width: 100%, height: 1fr, fit: "contain")
  ],

  // ROW 1, COL 2
  card(
    title: "How do individual nursery and outplanting sites compare?",
    subtitle: "Site-level fragment counts alongside active mid-water nursery stock capacity.",
    takeaway: [
      *What this shows:* Maintaining healthy fragment inventories across community nursery tables ensures a continuous supply of acclimatized colonies for reef outplanting.
    ],
  )[
    #stack(
      dir: ttb,
      spacing: 10pt,
      wcs_table(
        columns: (1.5fr, 1.2fr, 1fr),
        align: (left, left, right),
        header: ([*Site Name*], [*Site Type*], [*Fragments*]),
        ..site_rows,
      ),
      image("figures/fig_nursery_stock.png", width: 100%, height: 1fr, fit: "contain"),
    )
  ],

  // ROW 2, COL 1
  card(
    title: "How rapidly is restored reef area expanding over time?",
    subtitle: "Cumulative coral reef surface area restored (hectares) across monitored project zones.",
    takeaway: [
      *What this shows:* Upward trajectories reflect sustained outplanting campaigns across priority reef patches, converting rubble fields into complex three-dimensional habitat.
    ],
  )[
    #image("figures/fig_area_restored.png", width: 100%, height: 1fr, fit: "contain")
  ],

  // ROW 2, COL 2
  card(
    title: "How is field effort distributed across restoration activities?",
    subtitle: "Operational field days logged for fragmentation, transplantation, monitoring, and nursery cleaning.",
    takeaway: [
      *What this shows:* Regular nursery cleaning and maintenance days are essential to prevent algal overgrowth and maximize fragment survival prior to outplanting.
    ],
  )[
    #image("figures/fig_activities.png", width: 100%, height: 1fr, fit: "contain")
  ],

  // ROW 3, COL 1
  card(
    title: "What is the monthly outplanting output per project site?",
    subtitle: "Monthly volume of coral colonies transplanted onto natural and stabilized reef substrates.",
    takeaway: [
      *What this shows:* Outplanting pulses align with calm sea conditions and optimal thermal windows to maximize colony attachment and survival.
    ],
  )[
    #image("figures/fig_session_transplanted.png", width: 100%, height: 1fr, fit: "contain")
  ],

  // ROW 3, COL 2
  card(
    title: "Which artificial substrate technologies support outplanted corals?",
    subtitle: "Cumulative outplanted fragments across Reef Stars, fence wires, and coral clips.",
    takeaway: [
      *What this shows:* Reef Stars stabilize unconsolidated coral rubble on high-energy reefs, whereas clips and wires secure fragments onto consolidated reef framework.
    ],
  )[
    #image("figures/fig_substrate.png", width: 100%, height: 1fr, fit: "contain")
  ],
)

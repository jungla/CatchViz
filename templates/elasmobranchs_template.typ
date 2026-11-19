// CatchViz - Elasmobranchs (Sharks & Rays) Landings A0 Poster Template
#import "master_template.typ": *

#let start_date = "{{START_DATE}}"
#let end_date = "{{END_DATE}}"
#let selected_sites = "{{SELECTED_SITES}}"
#let num_records = "{{NUM_RECORDS}}"
#let num_species = "{{NUM_SPECIES}}"
#let total_weight = "{{TOTAL_WEIGHT}}"
#let threat_pct = "{{THREAT_PCT}}"
#let threat_count = "{{THREAT_COUNT}}"
#let logo_filename = "{{LOGO_FILENAME}}"

#wcs_poster(
  rows: (1fr, 1fr, 1fr, 0.85fr),
  gutter: 16pt,

  header: poster_header(
    logo_filename: logo_filename,
    kicker: "WCS TANZANIA MARINE PROGRAM  •  ELASMOBRANCH MONITORING",
    title: "Sharks & Rays Landings — Species Risk, Size Structure & Gear Pressure",
    meta_items: (
      [*Target Group:* Sharks & Rays],
      [*Period:* #start_date to #end_date],
      [*Sites & Markets:* #selected_sites],
    ),
    badge_text: "A0 ELASMOBRANCH\nBRIEF",
    kpis: (
      banner_kpi(value: num_records, label: "Total Landings Sampled"),
      banner_kpi(value: num_species, label: "Identified Species"),
      banner_kpi(value: total_weight, label: "Total Weight Recorded"),
      banner_kpi(
        value: threat_pct,
        label: "Threatened (CR / EN / VU)",
        sublabel: threat_count + " IUCN Red List Individuals",
        num_color: rgb("#dc2626"),
        top_color: rgb("#dc2626"),
      ),
    ),
  ),

  footer: poster_footer(
    protocol_title: "Conservation & Policy Implications",
    protocol_body: [
      *Prevalence of Immature Catches:* High proportions of juvenile individuals underscore the urgent need to protect critical coastal nursery habitats.
      #h(16pt) • #h(16pt)
      *CITES & National Action:* Several landed taxa (Hammerheads, Wedgefish, Guitarfish) are CITES Appendix II listed, requiring coordinated BMU gear and landing compliance.
    ],
    generated_time: "{{GENERATED_TIME}}",
  ),

  // ROW 1, COL 1
  card(
    title: "Where are elasmobranch landings concentrated along the coast?",
    subtitle: "Artisanal shark and ray monitoring locations across mainland Tanzania and Zanzibar.",
    takeaway: [
      *What this shows:* Circle area reflects sampling volume per landing site or market, identifying key coastal hotspots for elasmobranch trade and bycatch.
    ],
  )[
    #image("figures/fig_map.png", width: 100%, height: 1fr, fit: "contain")
  ],

  // ROW 1, COL 2
  card(
    title: "How has elasmobranch survey effort varied across seasons?",
    subtitle: "Monthly record counts across active landing sites and wholesale markets.",
    takeaway: [
      *What this shows:* Seasonal spikes reflect monsoon-driven shifts in offshore driftnet and longline effort as well as enumerator coverage.
    ],
  )[
    #image("figures/fig_effort.png", width: 100%, height: 1fr, fit: "contain")
  ],

  // ROW 2, COL 1
  card(
    title: "What share of landings belong to threatened IUCN Red List categories?",
    subtitle: "Distribution across Critically Endangered (CR), Endangered (EN), Vulnerable (VU), NT, and LC.",
    takeaway: [
      *What this shows:* Heavy representation of CR, EN, and VU species highlights severe local fishing pressure on globally declining shark and ray populations.
    ],
  )[
    #image("figures/fig_iucn.png", width: 100%, height: 1fr, fit: "contain")
  ],

  // ROW 2, COL 2
  card(
    title: "Which fishing gears capture the highest number of sharks and rays?",
    subtitle: "Frequency of gear types associated with recorded elasmobranch landings.",
    takeaway: [
      *What this shows:* Gill nets and hook-and-line operations drive most captures, pointing to priority gears for bycatch mitigation and mesh-size regulation.
    ],
  )[
    #image("figures/fig_gear.png", width: 100%, height: 1fr, fit: "contain")
  ],

  // ROW 3, COL 1
  card(
    title: "Which shark and ray species dominate artisanal catches?",
    subtitle: "Most frequently documented taxa ranked by specimen count and color-coded by IUCN status.",
    takeaway: [
      *What this shows:* Identifying dominant species enables targeted species-specific protection and CITES trade monitoring at primary landing hubs.
    ],
  )[
    #image("figures/fig_species.png", width: 100%, height: 1fr, fit: "contain")
  ],

  // ROW 3, COL 2
  card(
    title: "How do female-to-male sex ratios vary across landed species?",
    subtitle: "Ratio of landed female to male specimens relative to 1:1 parity.",
    takeaway: [
      *What this shows:* Skewed sex ratios can indicate spatial sexual segregation or disproportionate harvest of breeding females in coastal pupping grounds.
    ],
  )[
    #image("figures/fig_sex_ratio.png", width: 100%, height: 1fr, fit: "contain")
  ],

  // ROW 4, COL 1
  card(
    title: "Are landed specimens mature adults or immature juveniles?",
    subtitle: "Morphometric size distributions (Total Length, Disc Width) relative to size-at-maturity (Lm).",
    takeaway: [
      *What this shows:* Specimens falling below published Lm thresholds indicate capture prior to first reproduction, threatening stock replenishment.
    ],
  )[
    #image("figures/fig_size_dist.png", width: 100%, height: 1fr, fit: "contain")
  ],

  // ROW 4, COL 2
  card(
    title: "What proportion of all measured catches are below maturity?",
    subtitle: "Aggregate maturity ratio (Body Size / Lm) across sexed elasmobranch specimens.",
    takeaway: [
      *What this shows:* Ratios below 1.0 represent immature juveniles; high juvenile share confirms coastal fishing grounds overlap with nursery habitats.
    ],
  )[
    #image("figures/fig_maturity.png", width: 100%, height: 1fr, fit: "contain")
  ],
)

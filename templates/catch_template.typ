// CatchViz - Artisanal Bony Fishes Landings A0 Poster Template
#import "master_template.typ": *

#let start_date = "{{START_DATE}}"
#let end_date = "{{END_DATE}}"
#let selected_sites = "{{SELECTED_SITES}}"
#let total_catch = "{{TOTAL_CATCH}}"
#let num_records = "{{NUM_RECORDS}}"
#let avg_catch = "{{AVG_CATCH}}"
#let logo_filename = "{{LOGO_FILENAME}}"
#let site_rows = (
  /*{{SITE_TABLE_ROWS}}*/
)

#wcs_poster(
  header: poster_header(
    logo_filename: logo_filename,
    kicker: "WCS TANZANIA MARINE PROGRAM  •  CATCH MONITORING PLATFORM",
    title: selected_sites + " Landing Site",
    meta_items: (
      [*Period:* #start_date to #end_date],
    ),
    badge_text: "A0 FISHERY\nBRIEF",
    kpis: (
      banner_kpi(value: total_catch, label: "Total Catch Recorded"),
      banner_kpi(value: num_records, label: "Landing Records"),
      banner_kpi(value: avg_catch, label: "Average Catch / Trip"),
    ),
  ),

  footer: poster_footer(
    protocol_title: "Monitoring Protocol & Open-Access Data Citation",
    protocol_body: [
      *Field Protocol:* Catch data are gathered via standardized KoboToolbox digital surveys by trained community enumerators in collaboration with Beach Management Units (BMUs) and Fisheries Officers.
      #h(16pt) • #h(16pt)
      *Data Archive:* Curated and synchronized every 10 days via Zenodo (*DOI: 10.5281/zenodo.15229813*).
    ],
    generated_time: "{{GENERATED_TIME}}",
  ),

  // ROW 1, COL 1
  card(
    title: "Where are artisanal landings concentrated along the coast?",
    subtitle: "Spatial distribution of monitored landings across Tanzania and Zanzibar. Circle area reflects relative sampling volume per landing site. Concentration around key coastal hubs highlights where monitoring coverage and fishing pressure are highest.",
  )[
    #image("figures/fig_map.png", width: 100%, height: 1fr, fit: "contain")
  ],

  // ROW 1, COL 2
  card(
    title: "How do landing sites compare, and which species groups dominate?",
    subtitle: "Site-level catch volume and composition across reef fish, small pelagics, and tuna-like species.",
    takeaway: [
      *What this shows:* High dominance of reef-associated fishes indicates strong reliance on nearshore coral reef habitats, underscoring the importance of local BMU reef closures and gear rules.
    ],
  )[
    #stack(
      dir: ttb,
      spacing: 10pt,
      wcs_table(
        columns: (2fr, 1fr, 1fr),
        align: (left, right, right),
        header: ([*Landing Site*], [*Records*], [*Total Catch (kg)*]),
        ..site_rows,
      ),
      image("figures/fig_species_group.png", width: 100%, height: 1fr, fit: "contain"),
    )
  ],

  // ROW 2, COL 1
  card(
    title: "Which fishing vessels drive the bulk of artisanal landings?",
    subtitle: "Recorded landing trips categorized by vessel class across active operations.",
    takeaway: [
      *What this shows:* Traditional small sail boats (ngalawa/mashua) account for the vast majority of trips, meaning fisheries interventions must remain accessible to non-motorized small-scale fishers.
    ],
  )[
    #image("figures/fig_boat.png", width: 100%, height: 1fr, fit: "contain")
  ],

  // ROW 2, COL 2
  card(
    title: "Which gears catch the most fish — and which risk juvenile harvest?",
    subtitle: "Frequency of fishing gears utilized across recorded artisanal operations.",
    takeaway: [
      *What this shows:* Basket traps (madema) and lines dominate bony fish landings, whereas fine-mesh nets and spearguns warrant close size-selectivity tracking to prevent juvenile depletion.
    ],
  )[
    #image("figures/fig_gear.png", width: 100%, height: 1fr, fit: "contain")
  ],

  // ROW 3, COL 1
  card(
    title: "How has monitoring effort and landing intensity changed over time?",
    subtitle: "Monthly record counts illustrating temporal survey coverage and seasonal shifts.",
    takeaway: [
      *What this shows:* Monthly fluctuations reflect both seasonal monsoon fishing patterns (Kaskazi vs. Kusi) and enumerator survey consistency across reporting periods.
    ],
  )[
    #image("figures/fig_effort.png", width: 100%, height: 1fr, fit: "contain")
  ],

  // ROW 3, COL 2
  card(
    title: "Is catch per unit effort (CPUE) declining, stable, or recovering?",
    subtitle: "Trip-level CPUE (kg / fisher / hour) with fitted linear regression trajectory.",
    takeaway: [
      *What this shows:* CPUE standardizes catch by crew size and hours fished—a flat or rising trend suggests stable stock availability, whereas a sustained downward slope signals local overfishing.
    ],
  )[
    #image("figures/fig_cpue.png", width: 100%, height: 1fr, fit: "contain")
  ],
)

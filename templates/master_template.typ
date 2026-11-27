// CatchViz - Master A0 Poster Theme & Layout Components (WCS Tanzania Marine Program)
// Shared across Bony Fishes, Elasmobranchs, and Coral Reef Restoration templates.

// =============================================================================
// WCS TANZANIA MARINE PROGRAM PALETTE
// =============================================================================
#let wcs_sky = rgb("#58a6dc")       // Signature WCS banner sky blue
#let wcs_ocean = rgb("#1d6fa5")     // Deep coastal blue for full-bleed banners
#let wcs_bg = rgb("#f4f7f9")        // Soft cool page background
#let wcs_slate = rgb("#1e293b")     // Primary dark charcoal text
#let wcs_muted = rgb("#475569")     // Secondary subtitle text
#let wcs_line = rgb("#cbd5e1")      // Minimalist hairline border
#let wcs_tint = rgb("#eef6fc")      // Soft blue highlight fill

// =============================================================================
// PAGE & TYPOGRAPHY SETUP FUNCTION
// =============================================================================
#let setup_poster(body) = {
  set page(
    paper: "a0",
    flipped: false,
    margin: 0pt,
    fill: wcs_bg,
  )

  set text(
    font: ("Futura", "DejaVu Sans", "Helvetica", "Arial"),
    size: 20pt,
    fill: wcs_slate,
  )

  body
}

// =============================================================================
// REUSABLE COMPONENTS
// =============================================================================
#let banner_kpi(value: "", label: "", sublabel: none, num_color: wcs_ocean, top_color: wcs_sky) = block(
  fill: white,
  inset: (x: 20pt, y: 16pt),
  radius: 0pt,
  stroke: (top: 4pt + top_color),
  width: 100%,
  align(center)[
    #text(weight: "bold", size: 44pt, fill: num_color)[#value] \
    #v(4pt)
    #text(weight: "semibold", size: 20pt, fill: wcs_slate)[#label]
    #if sublabel != none [
      \ #v(2pt)
      #text(size: 15pt, fill: wcs_muted)[#sublabel]
    ]
  ],
)

#let card(title: none, subtitle: none, takeaway: none, accent: wcs_sky, body) = block(
  width: 100%,
  height: 100%,
  fill: white,
  inset: 22pt,
  radius: 0pt,
  stroke: (
    top: 2pt + accent,
    bottom: 0.75pt + wcs_line,
    left: 0.75pt + wcs_line,
    right: 0.75pt + wcs_line,
  ),
  breakable: false,
  {
    grid(
      columns: (1fr,),
      rows: (auto, auto, 1fr),
      row-gutter: 10pt,
      if title != none [
        #text(weight: "bold", size: 25pt, fill: wcs_slate)[#title]
        #if subtitle != none [
          \ #v(3pt)
          #text(size: 18pt, fill: wcs_muted)[#subtitle]
        ]
      ],
      if takeaway != none [
        #block(
          width: 100%,
          fill: wcs_tint,
          inset: (x: 16pt, y: 11pt),
          stroke: (left: 4pt + wcs_ocean),
          text(size: 19pt, fill: wcs_slate)[#takeaway],
        )
      ],
      align(center + horizon)[#body],
    )
  },
)

#let wcs_table(columns: (), align: auto, inset: (x: 12pt, y: 7pt), accent: wcs_sky, header: (), ..rows) = {
  table(
    columns: columns,
    align: align,
    inset: inset,
    stroke: (x, y) => if y == 0 { (bottom: 1.5pt + accent) } else { (bottom: 0.5pt + rgb("#e2e8f0")) },
    fill: (col, row) => if row == 0 { wcs_tint } else if calc.even(row) { rgb("#f8fafc") } else { white },
    table.header(..header),
    ..rows,
  )
}

// =============================================================================
// FULL-BLEED TOP HEADER BANNER
// =============================================================================
#let poster_header(
  logo_filename: "wcs_logo.png",
  kicker: "WCS TANZANIA MARINE PROGRAM  •  MONITORING PROGRAM",
  title: "",
  meta_items: (),
  badge_text: "A0 BRIEF",
  banner_fill: wcs_ocean,
  badge_fill: wcs_sky,
  kpis: (),
) = block(
  fill: banner_fill,
  inset: (x: 1.8cm, top: 1.3cm, bottom: 1.2cm),
  radius: 0pt,
  width: 100%,
  {
    grid(
      columns: (150pt, 1fr, 180pt),
      align: (center + horizon, left + horizon, right + horizon),
      image("figures/" + logo_filename, width: 130pt),
      pad(left: 22pt)[
        #text(fill: rgb("#bae6fd"), weight: "bold", size: 20pt, tracking: 1pt)[#kicker]
        #v(8pt)
        #text(fill: white, weight: "bold", size: 39pt)[#title]
        #v(10pt)
        #text(fill: rgb("#e0f2fe"), size: 20.5pt)[
          #meta_items.join([ #h(16pt) | #h(16pt) ])
        ]
      ],
      align(right)[
        #block(
          fill: badge_fill,
          inset: (x: 16pt, y: 12pt),
          radius: 0pt,
          text(fill: white, weight: "bold", size: 19pt)[#badge_text],
        )
      ],
    )
    if kpis.len() > 0 {
      v(20pt)
      grid(
        columns: (1fr,) * kpis.len(),
        gutter: 20pt,
        ..kpis,
      )
    }
  },
)

// =============================================================================
// FULL-BLEED BOTTOM FOOTER BANNER
// =============================================================================
#let poster_footer(
  protocol_title: "Monitoring Protocol & Data Attribution",
  protocol_body: [],
  generated_time: "",
  banner_fill: wcs_ocean,
  accent: wcs_sky,
) = block(
  fill: banner_fill,
  inset: (x: 1.8cm, top: 1.1cm, bottom: 1.3cm),
  radius: 0pt,
  stroke: (top: 4pt + accent),
  width: 100%,
  {
    text(fill: rgb("#bae6fd"), weight: "bold", size: 21pt)[#protocol_title]
    v(6pt)
    text(fill: white, size: 19.5pt)[#protocol_body]
    v(12pt)
    line(length: 100%, stroke: 1.5pt + accent)
    v(12pt)
    grid(
      columns: (1.05fr, 2.25fr, 1.1fr),
      gutter: 22pt,
      align: (left + horizon, left + horizon, right + horizon),
      [
        #text(weight: "bold", size: 27pt, fill: white)[Wildlife Conservation Society] \
        #v(4pt)
        #text(weight: "semibold", size: 21pt, fill: rgb("#bae6fd"))[WCS Tanzania Marine Program]
      ],
      text(size: 19pt, fill: rgb("#e0f2fe"))[
        • Working in Tanzania since 1956 \
        • Helping communities achieve equitable and sustainable resource management \
        • Supporting MPAs in Mainland and Zanzibar to safeguard natural heritage \
        • Informing decision-making and policy through monitoring and science
      ],
      text(size: 19pt, fill: white)[
        *www.tanzania.wcs.org* \
        \@wcs\_marine\_program\_tanzania \
        f wcstanzania \
        #v(6pt)
        #text(size: 16.5pt, fill: rgb("#bae6fd"))[Exported from CatchViz • #generated_time]
      ],
    )
  },
)

// =============================================================================
// MASTER SINGLE-PAGE POSTER SHELL (Strict 1-Page A0 Lock)
// =============================================================================
#let wcs_poster(
  header: none,
  footer: none,
  rows: (1fr, 1fr, 1fr),
  columns: (1fr, 1fr),
  gutter: 18pt,
  ..cards,
) = setup_poster[
  #grid(
    columns: (1fr,),
    rows: (auto, 1fr, auto),
    row-gutter: 0pt,
    header,
    pad(
      x: 1.8cm,
      y: 1.1cm,
      grid(
        columns: columns,
        rows: rows,
        gutter: gutter,
        ..cards,
      ),
    ),
    footer,
  )
]

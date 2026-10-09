// Resume layout. Data comes from content/resume.yaml via portfolio.render.pdf.
#let data = json(bytes(sys.inputs.data))
// Shrink factor chosen by portfolio.render.pdf to fit the page budget. Every size and
// gap below is in `em`, so this one number scales the whole layout.
#let scale = float(sys.inputs.at("scale", default: "1.0"))

// The site's light-theme palette (portfolio.render.pdf.PDF_COLORS). Like the site:
// section headings are orange, subheadings and links teal, bullets and rules neon orange.
#let colors = json(bytes(sys.inputs.colors))
#let fg = rgb(colors.fg)
#let muted = rgb(colors.muted)
#let teal = rgb(colors.teal)
#let orange-text = rgb(colors.at("orange-text"))
#let orange = rgb(colors.orange)

#set document(title: data.name + " – Resume", author: data.name)
#set page(paper: "us-letter", margin: (x: 0.65in, y: 0.55in))
#set text(font: "Libertinus Serif", size: 10.5pt * scale, fill: fg)

// Expose the final page count so the build can enforce a page budget.
#context [#metadata(counter(page).final().first()) <page-count>]
#set par(leading: 0.55em)
#set list(indent: 0.6em, spacing: 0.45em, marker: text(fill: orange)[•])
#show link: set text(fill: teal)

#let section(title) = {
  v(0.8em)
  text(size: 1.05em, weight: "bold", fill: orange-text, upper(title))
  v(-0.65em)
  line(length: 100%, stroke: 0.75pt + orange)
  v(0.1em)
}

#let subhead(body) = text(weight: "bold", fill: teal, body)

// Left-aligned main text with a muted right-aligned aside (dates, years).
#let entry(main, aside) = grid(columns: (1fr, auto), column-gutter: 1em, main, text(fill: muted, aside))

// Header
#align(center)[
  #text(size: 2.1em, weight: "bold", data.name) \
  #v(-0.3em)
  #text(size: 1.1em, fill: muted, data.headline) \
  #{
    let items = ()
    if data.location != none { items.push(data.location) }
    if data.email != none { items.push(link("mailto:" + data.email, data.email)) }
    for l in data.links { items.push(link(l.url, l.label)) }
    items.join([ #h(0.3em)·#h(0.3em) ])
  }
]

#data.summary

#if data.experience.len() > 0 {
  section("Experience")
  for role in data.experience {
    entry([#subhead(role.title) · #role.organization], role.dates)
    if role.location != none { v(-0.4em); text(size: 0.9em, fill: muted, role.location) }
    list(..role.highlights)
    if role.skills.len() > 0 {
      v(-0.2em)
      text(size: 0.9em)[#h(0.6em)_Tools:_ #role.skills.join(", ")]
    }
    v(0.25em)
  }
}

#if data.education.len() > 0 {
  section("Education")
  for edu in data.education {
    let place = edu.institution + if edu.location != none { " (" + edu.location + ")" }
    let aside = edu.dates + if edu.honors != none { [ · _#edu.honors _] }
    edu.degrees.map(subhead).join(linebreak())
    v(-0.2em)
    entry(place, aside)
  }
}

#if data.skills.len() > 0 {
  section("Skills")
  grid(
    columns: (auto, 1fr),
    column-gutter: 1em,
    row-gutter: 0.6em,
    ..data.skills.map(g => ([*#g.category*], g.items.join(", "))).flatten(),
  )
}

#if data.publications.len() > 0 {
  section("Research")
  set par(hanging-indent: 1.2em)
  for pub in data.publications {
    let authors = pub.authors.map(a => if a.me { subhead(a.name) } else { a.name }).join(", ")
    let title = if pub.url != none { link(pub.url, pub.title) } else { pub.title }
    par[#authors (#str(pub.year)). #title. #emph(pub.venue).]
  }
}

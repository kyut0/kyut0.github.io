// Resume layout. Data comes from content/resume.yaml via portfolio.render.pdf.
#let data = json(bytes(sys.inputs.data))

#let accent = rgb("#2f6f5e")
#let muted = luma(90)

#set document(title: data.name + " – Resume", author: data.name)
#set page(paper: "us-letter", margin: (x: 0.7in, y: 0.6in))
#set text(font: "Libertinus Serif", size: 10.5pt)
#set par(leading: 0.55em)
#set list(indent: 0.6em, spacing: 0.45em)
#show link: set text(fill: accent)

#let section(title) = {
  v(0.9em)
  text(size: 11pt, weight: "bold", fill: accent, upper(title))
  v(-0.65em)
  line(length: 100%, stroke: 0.5pt + accent)
  v(0.15em)
}

// Header
#align(center)[
  #text(size: 22pt, weight: "bold", data.name) \
  #v(-0.3em)
  #text(size: 11.5pt, fill: muted, data.headline) \
  #{
    let items = ()
    if data.location != none { items.push(data.location) }
    for l in data.links { items.push(link(l.url, l.label)) }
    items.join([ #h(0.3em)·#h(0.3em) ])
  }
]

#data.summary

#if data.experience.len() > 0 {
  section("Experience")
  for role in data.experience {
    grid(
      columns: (1fr, auto),
      [*#role.title* · #role.organization],
      text(fill: muted, role.dates),
    )
    if role.location != none { v(-0.4em); text(size: 9.5pt, fill: muted, role.location) }
    list(..role.highlights)
    v(0.3em)
  }
}

#if data.education.len() > 0 {
  section("Education")
  for edu in data.education {
    grid(
      columns: (1fr, auto),
      [*#edu.degree*, #edu.institution],
      text(fill: muted, str(edu.year)),
    )
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

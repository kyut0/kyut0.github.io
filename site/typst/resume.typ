// Resume layout. Data comes from content/resume.yaml via portfolio.render.pdf.
#import "common.typ": *
#show: setup.with("Resume")

#set list(indent: 0.6em, spacing: 0.45em, marker: text(fill: accent)[•])

#let section(title) = {
  v(0.8em)
  text(size: 1.05em, weight: "bold", fill: heading, upper(title))
  v(-0.65em)
  line(length: 100%, stroke: 0.75pt + accent)
  v(0.1em)
}

#let subhead(body) = text(weight: "bold", fill: link-color, body)

// Left-aligned main text with a muted right-aligned aside (dates, years).
#let entry(main, aside) = grid(columns: (1fr, auto), column-gutter: 1em, main, text(fill: muted, aside))

#letterhead()

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

#if data.skills.len() > 0 or data.strengths.len() > 0 {
  section("Skills")
  let rows = data.skills.map(g => ([*#g.category*], g.items.join(", ")))
  if data.strengths.len() > 0 { rows.push(([*Strengths*], data.strengths.join(", "))) }
  grid(
    columns: (auto, 1fr),
    column-gutter: 1em,
    row-gutter: 0.6em,
    ..rows.flatten(),
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

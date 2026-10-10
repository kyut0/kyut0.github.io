// Shared by resume.typ and cover-letter.typ: inputs, palette, page setup, and letterhead.
// Data comes from portfolio.render.pdf via sys.inputs.
#let data = json(bytes(sys.inputs.data))
// Shrink factor chosen by portfolio.render.pdf to fit the page budget. Every size and
// gap in the templates is in `em`, so this one number scales the whole layout.
#let scale = float(sys.inputs.at("scale", default: "1.0"))

// The site's light-theme palette (portfolio.render.pdf.PDF_COLORS). Like the site:
// section headings use the heading color, subheadings and links the link color, and
// bullets and rules the accent color. (`fg` because `text` is a Typst function.)
#let colors = json(bytes(sys.inputs.colors))
#let fg = rgb(colors.text)
#let muted = rgb(colors.muted)
#let heading = rgb(colors.heading)
#let link-color = rgb(colors.link)
#let accent = rgb(colors.accent)

// Page, text, and link styling for a document titled `title` (e.g. "Resume").
#let setup(title, body) = {
  set document(title: data.name + " – " + title, author: data.name)
  set page(paper: "us-letter", margin: (x: 0.65in, y: 0.55in))
  set text(font: "Libertinus Serif", size: 10.5pt * scale, fill: fg)
  set par(leading: 0.55em)
  show link: set text(fill: link-color)
  // Expose the final page count so the build can enforce a page budget.
  context [#metadata(counter(page).final().first()) <page-count>]
  body
}

// Name, headline, and a contact line of location, email, and links.
#let letterhead() = align(center)[
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

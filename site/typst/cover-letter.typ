// Cover letter layout: the resume's letterhead over the paragraphs of
// content/cover-letter.md, passed in as plain text by portfolio.render.pdf.
#import "common.typ": *
#show: setup.with("Cover Letter")

#set text(size: 11pt * scale)
#set par(leading: 0.7em, spacing: 1.2em, justify: true)

#letterhead()
#v(0.2em)
#line(length: 100%, stroke: 0.75pt + pop)
#v(1.2em)

#for paragraph in data.paragraphs {
  par(paragraph)
}

#v(0.6em)
Best, \
#text(weight: "bold", fill: heading, data.name)

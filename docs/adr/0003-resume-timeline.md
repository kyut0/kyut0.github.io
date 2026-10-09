# ADR 0003: Show the resume as a skills timeline, not a copy of the PDF

- **Status:** Accepted
- **Date:** 2026-10-09

## Context

The resume page was the PDF retyped as HTML, and the cover letter page was the letter
pasted into a card. Both added nothing over the PDFs themselves, which are already one
click away.

## Decision

- The resume page is a vertical timeline, newest first, built by `render/timeline.py`
  from the same validated data as the PDF: roles and education become dated events.
- Each step appears once. Project write-ups name the `organization` they came out of
  and are linked from that role or school's card instead of being separate events.
  When an organization has several roles, the one active at the time wins. Unknown
  organizations fail validation. Projects without one (personal work) live only on the
  Projects page.
- Publications are not on the timeline: nesting them in cards made it too busy. They
  have their own page (`publications.html`), where `organization` is shown as context.
- Colors: work and education share one blue (dots, labels, titles, bullets), with
  "Sample work" links in cyan. Pink is reserved for years and tool chips. Cards carry no
  colored side stripes, to keep the page calm.
- Each event lists its tools. Walking events oldest first, a tool is marked new on the
  first event that uses it. Spellings are matched by `skill_key` ("R Shiny" = "RShiny" =
  "r-shiny"), and labels prefer the resume's spelling over project tag slugs.
- A toolbox (the resume's skill tiers) sits above the timeline. `site/static/timeline.js`
  lets visitors click a tool to trace it, filter event types, and fades events in on
  scroll. Without JavaScript the full timeline still renders.
- Roles can set `in_pdf: false` to appear on the timeline but not in the one-page PDF,
  so early internships don't push the PDF onto a second page.
- The cover letter is published only as `cover-letter.pdf`, downloaded from the resume
  page. `content/cover-letter.md` stays the source.

## Consequences

- Tools only show on the timeline if a role's or school's `skills` list them (project
  tags mix tools with topics, so they stay on the Projects page).
- The toolbox and the timeline must agree exactly (`Resume._toolbox_matches_cards`):
  every toolbox tool is used on some card, and every tool on a card is in a toolbox
  tier. A mismatch fails validation, naming each offending tool. Soft skills live in a
  separate `strengths` list that only the PDF prints.

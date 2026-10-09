# ADR 0003: Show the resume as a skills timeline, not a copy of the PDF

- **Status:** Accepted
- **Date:** 2026-10-09

## Context

The resume page was the PDF retyped as HTML, and the cover letter page was the letter
pasted into a card. Both added nothing over the PDFs themselves, which are already one
click away.

## Decision

- The resume page is a vertical timeline, newest first, built by `render/timeline.py`
  from the same validated data as the PDF: roles, education, projects, and publications
  become dated events.
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

- Tools only show on the timeline if a role's `skills` or a project's `tags` list them;
  toolbox entries no event uses render as plain dashed chips, which flags gaps in the
  data.
- Publications have no month, so they sort as January of their year.

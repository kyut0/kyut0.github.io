---
title: Resume as Code
summary: >-
  This site. Resume and project content live as YAML and Markdown, are validated against
  typed schemas, and are compiled to a static site and a one-page PDF on every push.
date: 2026-10-08
tags: [python, pydantic, typst, github-actions, ci-cd]
repo: https://github.com/kyut0/kyut0.github.io
---

I wanted my portfolio to show how I build data systems, not just describe it. So the
site itself is a small pipeline: content is the data, and the website and PDF resume are
outputs.

## How it works

1. **Extract:** resume, bio, and project pages are plain YAML and Markdown files.
2. **Validate:** every file is checked against strict [pydantic](https://docs.pydantic.dev/)
   models before anything renders. Unknown fields, impossible date ranges, malformed
   citations, and missing images all fail the build.
3. **Render:** Jinja templates produce the HTML pages, and [Typst](https://typst.app/)
   compiles the same resume data into a PDF. One source of truth means the site and
   the PDF can't drift apart.
4. **Deploy:** GitHub Actions lints, type-checks, tests, and publishes to GitHub Pages on
   every push to `main`.

## Design choices

- **Content as data, not markup.** The resume is handed to the Typst template as JSON,
  so characters like `#`, `*`, and `$` in my content render literally with no escaping
  logic.
- **A one-page budget, enforced.** The PDF build measures its own page count and steps the
  layout down (100% to 88%) until it fits. If it still doesn't fit, the build fails
  instead of publishing a two-page resume, and a test enforces the same in CI.
- **Reproducible output.** The PDF uses only Typst's bundled fonts, so my laptop and
  CI produce identical files.
- **Decisions are written down.** Architecture decisions live as
  [ADRs](https://github.com/kyut0/kyut0.github.io/tree/main/docs/adr) in the repo.

**Stack:** Python 3.13, Poetry, pydantic, Jinja, Typst, pytest, ruff, mypy (strict),
pre-commit, GitHub Actions, GitHub Pages.

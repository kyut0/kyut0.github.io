# ADR 0002: Render the PDF resume with Typst

- **Status:** Accepted
- **Date:** 2026-10-08

## Context

The resume needs a downloadable PDF that always matches the HTML resume. Options considered:

- **WeasyPrint (HTML → PDF):** reuses Jinja/CSS, but needs Pango and other system
  libraries locally and in CI, and print CSS is fiddly to get right.
- **LaTeX:** excellent typesetting, but a heavy toolchain and painful escaping.
- **Typst:** modern typesetting language whose compiler ships as a self-contained Python
  wheel (`typst` on PyPI).

## Decision

Use Typst. `render/pdf.py` serializes the validated `Resume` model to JSON and passes it
to `site/typst/resume.typ` through `sys.inputs`. Dates are formatted in Python
(`render/formatting.py`) so the site and PDF match exactly. Only Typst's bundled fonts are
used (`ignore_system_fonts=True`) so local and CI builds are identical.

## Consequences

- No system dependencies: `poetry install` is all it takes, locally and in CI.
- Because content is handed to the template as data rather than interpolated into
  markup, characters like `#`, `*`, `$` and `//` render literally with no escaping
  logic (covered by `tests/test_pdf.py`).
- Layout changes happen in one `.typ` file; content changes stay in `content/resume.yaml`.
- Custom fonts would need to be committed under `site/typst/fonts/` and passed via
  `font_paths`.

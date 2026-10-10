# ADR 0004: Named color themes from seed colors

- **Status:** Accepted
- **Date:** 2026-10-09

## Context

Palettes were hand-written CSS custom properties in `style.css`, and trying a new one
meant editing a dozen tokens per mode and re-running contrast tests by hand. Visitors
had a light/dark toggle but no way to pick a look.

## Decision

- Themes live in `site/themes.yaml`, keyed by name, each with a light and dark mode. A
  mode needs only `bg`, `heading`, `link`, and `pop`; `portfolio.theme` derives the rest
  (card, border, body and muted text, button text, second accent).
- Every text color is checked against both the page background and cards (WCAG AA,
  4.5:1). Colors that fail are blended toward black (light mode) or white (dark mode)
  until they pass, and each change is recorded as a note. Vivid backgrounds or body
  text produce warnings, not failures, since a colorful theme can be deliberate.
- The build writes `static/themes.css`: the first (default) theme on bare `:root`, the
  others behind `:root[data-palette="name"]`, each with a `[data-theme="light"]` variant.
- A single gear menu in the header lists every theme in both modes ("Ember (dark)",
  "Ember (light)", ...) with swatches; it replaced the separate light/dark toggle. A
  choice saves the mode and theme in `localStorage`, applied before first paint. Until a
  visitor picks, they get the default theme in their system's light or dark mode.
- `make themes` prints every adjustment and writes `_site/themes-preview.html`, a
  side-by-side mockup of each theme in both modes, for reviewing a palette before use.

## Consequences

- Adding a theme is a few lines of YAML; the build refuses one that can't be made
  readable.
- The PDF still prints with the default theme's light palette (`PDF_COLORS`, checked
  in `tests/test_theme.py`).
- `pop-2` is decorative and not contrast-checked, so it should not carry small text.

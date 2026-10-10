# ADR 0005: An easter-egg trail that never gets in a recruiter's way

- **Status:** Accepted
- **Date:** 2026-10-10

## Context

The site is a resume first, so anything playful has to stay out of the way of someone
scanning it for five minutes. But a portfolio that only lists skills says little about
the person, and the kind of visitor who opens devtools or reads a toolbox closely is
exactly who a few hidden details are for.

## Decision

- **A trail, not scattered trivia.** Each stop hides a clue to the next, and the trail
  leaves the site and comes back:
  1. Two ways in: a welcome in the devtools console (`static/console.js`), and a
     "touch typing" chip in the toolbox, which links to the typing test instead of
     tracing the timeline (`skill_links` in `resume.yaml`, dashed border, hover hint).
  2. `/type.html`: a 15-second typing test against my Monkeytype personal best. Its
     results point to the blog.
  3. The blog's footer points to the GitHub profile README.
  4. The profile README's collapsed riddle says to type ❌ three times on the site.
  5. Typing `xxx` (or the Konami code) anywhere outside a text box opens a celebration
     and unlocks the Moka Pot Magic themes and the `/treasure.html` gallery.
- **Hidden, not secret.** Hidden pages are built like any other (`HIDDEN_PAGES` in
  `render/site.py`) but linked from no menu. The code is public, so the hunt rewards
  digging rather than defending against it.
- **No network in the build.** The typing test's personal best comes from
  `content/typing.yaml`, a validated snapshot that `portfolio typing` refreshes from
  Monkeytype's public API, so the build stays reproducible and never depends on
  Monkeytype being up.
- **Treasure themes are ordinary themes.** `site/treasure-themes.yaml` uses the
  seedpalette format and `themes.py` merges it into the theme set, so treasure themes get
  the same contrast checks, CSS, preview, and PDFs. Only visibility differs: their menu
  entries, the footer trophy, and the gallery are `.treasure-only`, which CSS hides until
  `<html data-treasure="found">`. That flag lives in `localStorage` and is restored
  before first paint, and a saved treasure palette is ignored without it.
- **Linked chips are site-only.** Tools in `skill_links` are left off the PDF resume, so
  an easter egg never costs space on the one-page budget.

## Consequences

- Recruiters see a normal site: no extra navigation, no layout changes, no motion
  (the celebration skips its animation under `prefers-reduced-motion`).
- Clues span three repos (this one, the blog, and `kyut0/kyut0`), so changing a stop
  means updating the clue that points to it. The README's Easter eggs section lists
  where each stop lives.
- Photos of the artwork came from a phone, and one carried GPS coordinates.
  `test_published_photos_carry_no_location` now fails the build if any published JPEG
  has EXIF GPS tags.

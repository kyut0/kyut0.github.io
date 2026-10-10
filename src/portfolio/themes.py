"""Load the site's color themes: site/themes.yaml plus the hidden treasure themes.

site/treasure-themes.yaml holds themes in the same seedpalette format (a `themes:`
mapping) that stay out of the color menu until a visitor finds the treasure (see
static/treasure.js). They're merged into one ThemeSet, so they get the same contrast
checks, CSS, and themed PDFs as every other theme.
"""

from dataclasses import dataclass
from pathlib import Path

import seedpalette
import yaml

THEMES_FILE = "themes.yaml"
TREASURE_FILE = "treasure-themes.yaml"


@dataclass(frozen=True)
class SiteThemes:
    themes: seedpalette.ThemeSet
    treasure: frozenset[str]  # names of the themes that unlock with the treasure


def load_themes(site_dir: Path) -> SiteThemes:
    data = yaml.safe_load((site_dir / THEMES_FILE).read_text(encoding="utf-8"))
    treasure_path = site_dir / TREASURE_FILE
    if not treasure_path.is_file():
        return SiteThemes(seedpalette.parse(data), frozenset())

    extra = yaml.safe_load(treasure_path.read_text(encoding="utf-8")) or {}
    if not isinstance(extra, dict) or set(extra) != {"themes"}:
        raise ValueError(f"{treasure_path}: expected only a `themes:` mapping")
    treasure = extra["themes"]
    clashes = set(treasure) & set(data["themes"])
    if clashes:
        raise ValueError(f"{treasure_path}: theme name(s) already used: {', '.join(clashes)}")
    merged = {**data, "themes": {**data["themes"], **treasure}}
    return SiteThemes(seedpalette.parse(merged), frozenset(treasure))

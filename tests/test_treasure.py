from pathlib import Path
import re
import shutil

import pytest

from portfolio.load import load_site
from portfolio.render import build_site
from portfolio.themes import TREASURE_FILE, load_themes


def test_treasure_themes_join_the_theme_set(site_dir: Path) -> None:
    site_themes = load_themes(site_dir)
    names = [t.name for t in site_themes.themes.themes]
    assert site_themes.treasure, "expected at least one treasure theme"
    assert site_themes.treasure <= set(names)
    assert names[0] not in site_themes.treasure  # the default theme is never hidden
    # Treasure themes come after the regular ones, so they're last in the menu.
    regular = [n for n in names if n not in site_themes.treasure]
    assert names[: len(regular)] == regular


def test_without_treasure_file_there_are_no_treasure_themes(
    site_dir: Path, tmp_path: Path
) -> None:
    shutil.copy(site_dir / "themes.yaml", tmp_path / "themes.yaml")
    assert load_themes(tmp_path).treasure == frozenset()


def test_treasure_theme_names_must_be_new(site_dir: Path, tmp_path: Path) -> None:
    shutil.copy(site_dir / "themes.yaml", tmp_path / "themes.yaml")
    (tmp_path / TREASURE_FILE).write_text(
        "themes:\n  ember:\n    label: X\n    description: X\n"
        "    light: {bg: '#ffffff', heading: '#000000', link: '#0000ee', accent: '#ff0000'}\n"
        "    dark: {bg: '#000000', heading: '#ffffff', link: '#99ccff', accent: '#ff0000'}\n"
    )
    with pytest.raises(ValueError, match="already used: ember"):
        load_themes(tmp_path)


def test_treasure_themes_are_hidden_until_found(
    content_dir: Path, site_dir: Path, tmp_path: Path
) -> None:
    site_themes = load_themes(site_dir)
    build_site(load_site(content_dir), tmp_path, site_dir / "templates", site_dir / "static")
    index = (tmp_path / "index.html").read_text()
    for name in site_themes.treasure:
        option = rf'<li class="treasure-only">\s*<button [^>]*data-palette="{name}"'
        assert re.search(option, index), f"{name} isn't marked treasure-only"
        assert f':root[data-palette="{name}"]' in (tmp_path / "static" / "themes.css").read_text()
    assert 'src="static/treasure.js?v=' in index
    css = (tmp_path / "static" / "style.css").read_text()
    assert ':root:not([data-treasure="found"]) .treasure-only' in css

from pathlib import Path
import re
import shutil
from typing import Literal

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


def test_every_treasure_theme_has_its_painting(site_dir: Path) -> None:
    art = site_dir / "static" / "treasure"
    for name in load_themes(site_dir).treasure:
        assert (art / f"{name}.jpg").is_file(), f"{name}: missing painting"


def _has_gps(jpeg: bytes) -> bool:
    """Whether a JPEG's EXIF block points to GPS data (tag 0x8825 in its first IFD)."""
    i = 2  # skip the SOI marker
    while i + 4 <= len(jpeg) and jpeg[i] == 0xFF:
        marker, size = jpeg[i + 1], int.from_bytes(jpeg[i + 2 : i + 4], "big")
        segment = jpeg[i + 4 : i + 2 + size]
        if marker == 0xE1 and segment.startswith(b"Exif\x00\x00"):
            tiff = segment[6:]
            order: Literal["little", "big"] = "little" if tiff[:2] == b"II" else "big"
            ifd = int.from_bytes(tiff[4:8], order)
            count = int.from_bytes(tiff[ifd : ifd + 2], order)
            tags = (
                int.from_bytes(tiff[ifd + 2 + 12 * n : ifd + 4 + 12 * n], order)
                for n in range(count)
            )
            return 0x8825 in tags
        if marker == 0xDA:  # image data starts; no more metadata
            break
        i += 2 + size
    return False


def test_published_photos_carry_no_location(site_dir: Path, content_dir: Path) -> None:
    """Phone photos can embed where they were taken (EXIF GPS); those must be stripped."""
    photos = [
        p
        for folder in (site_dir / "static", content_dir)
        for p in folder.rglob("*")
        if p.suffix.lower() in (".jpg", ".jpeg")
    ]
    located = [str(p) for p in photos if _has_gps(p.read_bytes())]
    assert not located, f"strip location data from: {', '.join(located)}"


def test_gallery_page_shows_each_painting_once_found(
    content_dir: Path, site_dir: Path, tmp_path: Path
) -> None:
    site_themes = load_themes(site_dir)
    build_site(load_site(content_dir), tmp_path, site_dir / "templates", site_dir / "static")
    gallery = (tmp_path / "treasure.html").read_text()
    assert 'class="treasure-locked"' in gallery  # what visitors see before finding it
    for name in site_themes.treasure:
        assert f'src="static/treasure/{name}.jpg?v=' in gallery
        assert f'class="button wear-theme" type="button" data-palette="{name}"' in gallery
    index = (tmp_path / "index.html").read_text()
    assert 'class="treasure-only treasure-mark" href="treasure.html"' in index

"""Guard the site's color themes. seedpalette derives and contrast-checks them (and tests
its own color math); these tests pin down what this site relies on."""

from pathlib import Path

import pytest
import seedpalette
from seedpalette.color import TEXT_MIN, chroma, contrast_ratio
from seedpalette.palette import CHROMA_MAX

from portfolio.render.pdf import PDF_COLORS


@pytest.fixture(scope="module")
def themes() -> seedpalette.ThemeSet:
    site_dir = Path(__file__).resolve().parent.parent / "site"
    return seedpalette.load(site_dir / "themes.yaml")


def test_every_theme_passes_contrast(themes: seedpalette.ThemeSet) -> None:
    for theme in themes.themes:
        failing = [c for c in theme.checks if not c.ok]
        assert not failing, f"{theme.name}: {failing}"


def test_site_tokens_are_defined(themes: seedpalette.ThemeSet) -> None:
    """style.css uses these beyond seedpalette's core tokens."""
    assert {"card-link", "thumb-bg"} <= set(themes.tokens)
    for theme in themes.themes:
        for mode in ("light", "dark"):
            assert set(theme.palette(mode)) == set(themes.tokens), f"{theme.name} {mode}"


def test_default_theme_is_calm(themes: seedpalette.ThemeSet) -> None:
    """The default theme keeps large surfaces and body text low in saturation."""
    default = themes.themes[0]
    for mode in ("light", "dark"):
        for token, limit in CHROMA_MAX.items():
            assert chroma(default.palette(mode)[token]) <= limit, f"{mode} --{token}"


def test_default_theme_is_used_as_given(themes: seedpalette.ThemeSet) -> None:
    """Ember spells out every color, so seedpalette should change nothing."""
    assert themes.themes[0].notes == []


def test_pdf_colors_match_default_light_theme(themes: seedpalette.ThemeSet) -> None:
    """The PDF prints on white with the default theme's light palette."""
    for token, value in PDF_COLORS.items():
        assert themes.themes[0].light[token].lower() == value.lower(), f"--{token} differs"


@pytest.mark.parametrize("token", ["text", "muted", "link", "heading"])
def test_pdf_text_colors_readable_on_white(token: str) -> None:
    assert contrast_ratio(PDF_COLORS[token], "#ffffff") >= TEXT_MIN

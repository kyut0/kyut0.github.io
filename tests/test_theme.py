"""Guard the site's color themes. seedpalette derives and contrast-checks them (and tests
its own color math); these tests pin down what this site relies on."""

from pathlib import Path

import pytest
import seedpalette
from seedpalette.color import chroma, contrast_ratio, to_oklch
from seedpalette.palette import CHROMA_MAX

from portfolio.render.pdf import PAPER, PDF_TOKENS, pdf_colors


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


def test_pdf_colors_are_default_light_theme_as_given(themes: seedpalette.ThemeSet) -> None:
    """Ember's light palette already reads well on white, so its PDFs use it unchanged."""
    for token, value in pdf_colors(themes.themes[0]).items():
        assert themes.themes[0].light[token].lower() == value.lower(), f"--{token} differs"


def test_pdf_colors_readable_on_white(themes: seedpalette.ThemeSet) -> None:
    for theme in themes.themes:
        colors = pdf_colors(theme)
        for token, minimum in PDF_TOKENS.items():
            ratio = contrast_ratio(colors[token], PAPER)
            assert ratio >= minimum, f"{theme.name} --{token}: {ratio:.2f}"


def test_faint_pdf_accent_is_darkened_keeping_its_hue(themes: seedpalette.ThemeSet) -> None:
    """Tokyo Night's light accent is too pale for white paper on its own."""
    tokyo = next(t for t in themes.themes if t.name == "tokyo-night")
    given, used = tokyo.palette("light")["accent"], pdf_colors(tokyo)["accent"]
    assert contrast_ratio(given, PAPER) < PDF_TOKENS["accent"]
    assert used != given
    assert abs(to_oklch(used).h - to_oklch(given).h) < 5

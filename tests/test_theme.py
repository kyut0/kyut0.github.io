"""Guard the site theme: every text color must stay readable in both light and dark mode,
and the large surfaces must stay calm (low saturation)."""

from pathlib import Path
import re

import pytest

from portfolio.color import TEXT_MIN, UI_MIN, chroma, contrast_ratio
from portfolio.render.pdf import PDF_COLORS

# (foreground token, background token, minimum ratio)
PAIRS = [
    ("fg", "bg", TEXT_MIN),
    ("fg", "card", TEXT_MIN),
    ("muted", "bg", TEXT_MIN),
    ("muted", "card", TEXT_MIN),
    ("link", "bg", TEXT_MIN),  # links, subheadings, own name in citations
    ("link", "card", TEXT_MIN),
    ("heading", "bg", TEXT_MIN),  # main headings
    ("heading", "card", TEXT_MIN),
    ("on-pop", "pop", TEXT_MIN),  # button text
    ("link", "bg", UI_MIN),  # focus ring
    ("card-link", "card", TEXT_MIN),  # "Sample work" links in timeline cards
]

# Maximum chroma (0 = gray, 1 = pure color) for surfaces and running text, so vivid
# color is saved for headings, links and the pops.
CHROMA_MAX = {"bg": 0.15, "card": 0.15, "fg": 0.20, "muted": 0.25}


def _tokens(block: str) -> dict[str, str]:
    return dict(re.findall(r"--([\w-]+):\s*(#[0-9a-fA-F]{6})\s*;", block))


@pytest.fixture(scope="module")
def palettes(site_dir: Path) -> dict[str, dict[str, str]]:
    css = (site_dir / "static" / "style.css").read_text()
    dark = re.search(r"^:root\s*\{(.*?)\}", css, re.S | re.M)  # the default theme
    light = re.search(r'^:root\[data-theme="light"\]\s*\{(.*?)\}', css, re.S | re.M)
    assert dark and light, 'expected a :root block and a :root[data-theme="light"] block'
    return {"light": _tokens(light.group(1)), "dark": _tokens(dark.group(1))}


@pytest.fixture(scope="module")
def site_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "site"


def test_light_mode_overrides_every_dark_token(palettes: dict[str, dict[str, str]]) -> None:
    assert palettes["light"].keys() == palettes["dark"].keys()


@pytest.mark.parametrize("mode", ["light", "dark"])
@pytest.mark.parametrize(("fg", "bg", "minimum"), PAIRS)
def test_theme_contrast(
    palettes: dict[str, dict[str, str]], mode: str, fg: str, bg: str, minimum: float
) -> None:
    p = palettes[mode]
    ratio = contrast_ratio(p[fg], p[bg])
    assert ratio >= minimum, f"{mode}: --{fg} on --{bg} is {ratio:.2f}:1 (need {minimum}:1)"


@pytest.mark.parametrize("mode", ["light", "dark"])
@pytest.mark.parametrize(("token", "limit"), CHROMA_MAX.items())
def test_theme_saturation(
    palettes: dict[str, dict[str, str]], mode: str, token: str, limit: float
) -> None:
    value = chroma(palettes[mode][token])
    assert value <= limit, f"{mode}: --{token} chroma is {value:.2f} (max {limit})"


def test_chroma_known_values() -> None:
    assert chroma("#808080") == 0
    assert chroma("#ff0000") == 1
    assert chroma("#0b1530") == pytest.approx(0.145, abs=0.001)


def test_contrast_ratio_known_values() -> None:
    assert contrast_ratio("#000000", "#ffffff") == pytest.approx(21.0)
    assert contrast_ratio("#777777", "#777777") == pytest.approx(1.0)
    with pytest.raises(ValueError):
        contrast_ratio("teal", "#ffffff")


def test_pdf_colors_match_site_light_theme(palettes: dict[str, dict[str, str]]) -> None:
    """The PDF prints on white with the site's light palette; they must not drift apart."""
    for token, value in PDF_COLORS.items():
        assert palettes["light"][token].lower() == value.lower(), f"--{token} differs"


@pytest.mark.parametrize("token", ["fg", "muted", "link", "heading"])
def test_pdf_text_colors_readable_on_white(token: str) -> None:
    assert contrast_ratio(PDF_COLORS[token], "#ffffff") >= TEXT_MIN

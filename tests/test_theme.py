"""Guard the color themes: every theme in site/themes.yaml must stay readable in both
light and dark mode, and the derivation in portfolio.theme must keep it that way."""

from pathlib import Path

from pydantic import ValidationError
import pytest

from portfolio.color import TEXT_MIN, chroma, contrast_ratio
from portfolio.render.pdf import PDF_COLORS
from portfolio.theme import (
    CHROMA_MAX,
    TOKENS,
    Theme,
    ThemeSpec,
    ensure_contrast,
    load_themes,
    mix,
    resolve,
    themes_css,
)


@pytest.fixture(scope="module")
def site_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "site"


@pytest.fixture(scope="module")
def themes(site_dir: Path) -> list[Theme]:
    return load_themes(site_dir / "themes.yaml")


def _spec(light: dict[str, str], dark: dict[str, str]) -> ThemeSpec:
    return ThemeSpec.model_validate({"label": "Test", "light": light, "dark": dark})


SEEDS = {"heading": "#700808", "link": "#059ea1", "pop": "#d80aad"}


# ---- the site's themes -------------------------------------------------------------


def test_every_theme_passes_contrast(themes: list[Theme]) -> None:
    for theme in themes:
        failing = [c for c in theme.checks if not c.ok]
        assert not failing, f"{theme.name}: {failing}"


def test_every_theme_defines_every_token(themes: list[Theme]) -> None:
    for theme in themes:
        for mode in ("light", "dark"):
            assert set(theme.palette(mode)) == set(TOKENS), f"{theme.name} {mode}"


def test_default_theme_is_calm(themes: list[Theme]) -> None:
    """The default theme keeps large surfaces and body text low in saturation."""
    default = themes[0]
    for mode in ("light", "dark"):
        for token, limit in CHROMA_MAX.items():
            assert chroma(default.palette(mode)[token]) <= limit, f"{mode} --{token}"


def test_pdf_colors_match_default_light_theme(themes: list[Theme]) -> None:
    """The PDF prints on white with the default theme's light palette."""
    for token, value in PDF_COLORS.items():
        assert themes[0].light[token].lower() == value.lower(), f"--{token} differs"


@pytest.mark.parametrize("token", ["fg", "muted", "link", "heading"])
def test_pdf_text_colors_readable_on_white(token: str) -> None:
    assert contrast_ratio(PDF_COLORS[token], "#ffffff") >= TEXT_MIN


# ---- derivation --------------------------------------------------------------------


def test_mix_endpoints() -> None:
    assert mix("#000000", "#ffffff", 0) == "#000000"
    assert mix("#000000", "#ffffff", 1) == "#ffffff"
    assert mix("#000000", "#ffffff", 0.5) == "#808080"


def test_ensure_contrast_keeps_passing_colors() -> None:
    assert ensure_contrast("#000000", ["#ffffff"], TEXT_MIN, "#000000") == "#000000"


def test_ensure_contrast_darkens_until_readable() -> None:
    fixed = ensure_contrast("#059ea1", ["#9dcca8"], TEXT_MIN, "#000000")
    assert fixed != "#059ea1"
    assert contrast_ratio(fixed, "#9dcca8") >= TEXT_MIN


def test_missing_tokens_are_derived_and_readable() -> None:
    theme = resolve("t", _spec({"bg": "#9dcca8", **SEEDS}, {"bg": "#001c07", **SEEDS}))
    assert theme.ok
    for mode in ("light", "dark"):
        assert set(theme.palette(mode)) == set(TOKENS)


def test_faint_text_is_adjusted_with_a_note() -> None:
    theme = resolve("t", _spec({"bg": "#9dcca8", **SEEDS}, {"bg": "#001c07", **SEEDS}))
    assert theme.light["link"] != "#059ea1"
    note = next(n for n in theme.notes if n.mode == "light" and n.token == "link")
    assert "darkened" in note.message
    assert not note.warning


def test_dark_mode_lightens_instead() -> None:
    theme = resolve("t", _spec({"bg": "#f8f1e3", **SEEDS}, {"bg": "#001c07", **SEEDS}))
    note = next(n for n in theme.notes if n.mode == "dark" and n.token == "heading")
    assert "lightened" in note.message


def test_vivid_background_is_a_warning_not_a_failure() -> None:
    theme = resolve("t", _spec({"bg": "#9dcca8", **SEEDS}, {"bg": "#001c07", **SEEDS}))
    assert theme.ok
    assert any(n.warning and n.token == "bg" for n in theme.notes)


def test_button_text_picks_the_readable_option() -> None:
    theme = resolve("t", _spec({"bg": "#f8f1e3", **SEEDS}, {"bg": "#001c07", **SEEDS}))
    assert contrast_ratio(theme.light["on-pop"], theme.light["pop"]) >= TEXT_MIN


# ---- spec validation ---------------------------------------------------------------


def test_unknown_token_is_rejected() -> None:
    with pytest.raises(ValidationError, match="unknown token"):
        _spec({"bg": "#ffffff", "sparkle": "#ff00ff", **SEEDS}, {"bg": "#000000", **SEEDS})


def test_missing_required_token_is_rejected() -> None:
    with pytest.raises(ValidationError, match="missing required"):
        _spec({"bg": "#ffffff"}, {"bg": "#000000", **SEEDS})


def test_bad_hex_is_rejected() -> None:
    with pytest.raises(ValidationError):
        _spec({"bg": "white", **SEEDS}, {"bg": "#000000", **SEEDS})


def test_empty_theme_file_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "themes.yaml"
    path.write_text("{}\n")
    with pytest.raises(ValidationError, match="no themes"):
        load_themes(path)


# ---- CSS ---------------------------------------------------------------------------


def test_css_puts_default_on_root_and_others_behind_data_palette(themes: list[Theme]) -> None:
    css = themes_css(themes)
    assert css.count(":root {") == 1
    assert ':root[data-theme="light"] {' in css
    for theme in themes[1:]:
        assert f':root[data-palette="{theme.name}"] {{' in css
        assert f':root[data-palette="{theme.name}"][data-theme="light"] {{' in css
    assert f"--bg: {themes[0].dark['bg']};" in css

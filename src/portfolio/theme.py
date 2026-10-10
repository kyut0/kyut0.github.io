"""Named color themes: seed colors in site/themes.yaml become full, readable palettes.

Each theme gives a light and a dark mode. A mode needs only a few seed colors (bg,
heading, link, pop); every other token is derived from them. Every text color is then
checked against WCAG contrast minimums on both the page background and cards, and any
that fail are nudged darker (light mode) or lighter (dark mode) until they pass. Each
nudge is recorded as a note, so `make themes` can report exactly what changed and why.

The first theme in the file is the site default. The build writes every theme to
static/themes.css; the gear menu in the site header switches between them.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, RootModel, StringConstraints, model_validator
import yaml

from portfolio.color import TEXT_MIN, chroma, contrast_ratio

HexColor = Annotated[str, StringConstraints(pattern=r"^#[0-9a-fA-F]{6}$")]
Mode = Literal["light", "dark"]

# Every CSS custom property a palette defines, in output order.
TOKENS = (
    "bg",
    "card",
    "border",
    "fg",
    "muted",
    "heading",
    "link",
    "pop",
    "pop-2",
    "on-pop",
    "thumb-bg",
    "card-link",
)
REQUIRED = ("bg", "heading", "link", "pop")

# Tokens used as text on the page background and on cards.
TEXT_TOKENS = ("fg", "muted", "heading", "link", "card-link")

# Maximum chroma (0 = gray, 1 = pure color) for large surfaces and running text, so
# vivid color is saved for headings, links, and pops. Exceeding these is a warning, not
# an error: a deliberately colorful background is a design choice.
CHROMA_MAX = {"bg": 0.15, "card": 0.15, "fg": 0.20, "muted": 0.25}

WHITE = "#ffffff"
BLACK = "#000000"


# ---- color math --------------------------------------------------------------------


def _rgb(color: str) -> tuple[int, int, int]:
    return int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)


def mix(a: str, b: str, t: float) -> str:
    """Blend a toward b: t=0 is a, t=1 is b."""
    return "#" + "".join(
        f"{round(x + (y - x) * t):02x}" for x, y in zip(_rgb(a), _rgb(b), strict=True)
    )


def worst_contrast(color: str, backgrounds: list[str]) -> float:
    return min(contrast_ratio(color, bg) for bg in backgrounds)


def ensure_contrast(color: str, backgrounds: list[str], minimum: float, toward: str) -> str:
    """Blend color toward `toward` (black or white) in small steps until it reaches
    minimum contrast against every background. Returns the first passing color."""
    for step in range(51):
        candidate = mix(color, toward, step / 50)
        if worst_contrast(candidate, backgrounds) >= minimum:
            return candidate
    return mix(color, toward, 1.0)


# ---- spec (what themes.yaml says) --------------------------------------------------


class ModeSpec(RootModel[dict[str, HexColor]]):
    """Seed colors for one mode: token name -> #rrggbb. bg, heading, link, and pop are
    required; anything else left out is derived."""

    @model_validator(mode="after")
    def _known_tokens(self) -> "ModeSpec":
        unknown = sorted(set(self.root) - set(TOKENS))
        if unknown:
            raise ValueError(f"unknown token(s) {unknown}; expected some of {list(TOKENS)}")
        missing = [t for t in REQUIRED if t not in self.root]
        if missing:
            raise ValueError(f"missing required token(s) {missing}")
        return self


class ThemeSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    label: str
    description: str = ""
    light: ModeSpec
    dark: ModeSpec


ThemeName = Annotated[str, StringConstraints(pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$")]


class ThemeFile(RootModel[dict[ThemeName, ThemeSpec]]):
    @model_validator(mode="after")
    def _not_empty(self) -> "ThemeFile":
        if not self.root:
            raise ValueError("themes file defines no themes")
        return self


# ---- resolved palettes -------------------------------------------------------------


@dataclass(frozen=True)
class Note:
    """One change made while deriving a palette, or a warning about it."""

    mode: Mode
    token: str
    message: str
    warning: bool = False


@dataclass(frozen=True)
class Check:
    mode: Mode
    token: str
    against: str  # token name
    ratio: float
    minimum: float

    @property
    def ok(self) -> bool:
        return self.ratio >= self.minimum


@dataclass(frozen=True)
class Theme:
    name: str
    label: str
    description: str
    light: dict[str, str]
    dark: dict[str, str]
    notes: list[Note] = field(default_factory=list)
    checks: list[Check] = field(default_factory=list)

    def palette(self, mode: Mode) -> dict[str, str]:
        return self.light if mode == "light" else self.dark

    @property
    def ok(self) -> bool:
        return all(c.ok for c in self.checks)


def _derive(spec: dict[str, str], mode: Mode) -> tuple[dict[str, str], list[Note]]:
    dark = mode == "dark"
    toward_text = WHITE if dark else BLACK  # the direction that adds contrast
    bg = spec["bg"]
    notes: list[Note] = []

    defaults = {
        "card": mix(bg, WHITE, 0.06 if dark else 0.45),
        "border": mix(bg, WHITE, 0.16) if dark else mix(bg, BLACK, 0.12),
        "fg": mix(bg, toward_text, 0.88),
        "muted": mix(bg, toward_text, 0.62),
        "pop-2": spec["pop"],
        "thumb-bg": WHITE,
        "card-link": spec["link"],
    }
    palette = {t: spec.get(t) or defaults.get(t, "") for t in TOKENS}

    for token in TEXT_TOKENS:
        given = palette[token]
        fixed = ensure_contrast(given, [palette["bg"], palette["card"]], TEXT_MIN, toward_text)
        if fixed != given:
            before = worst_contrast(given, [palette["bg"], palette["card"]])
            after = worst_contrast(fixed, [palette["bg"], palette["card"]])
            verb = "lightened" if dark else "darkened"
            source = "given" if token in spec else "derived"
            notes.append(
                Note(
                    mode,
                    token,
                    f"{source} {given} reads at {before:.2f}:1; {verb} to {fixed} ({after:.2f}:1)",
                )
            )
            palette[token] = fixed

    if "on-pop" not in spec:
        # Button text: whichever of white or the darkest page color reads better.
        darkest = palette["bg"] if dark else palette["fg"]
        palette["on-pop"] = max((WHITE, darkest), key=lambda c: contrast_ratio(c, palette["pop"]))

    for token, limit in CHROMA_MAX.items():
        value = chroma(palette[token])
        if value > limit:
            notes.append(
                Note(
                    mode,
                    token,
                    f"{palette[token]} is vivid for a {token} color "
                    f"(chroma {value:.2f}, calm limit {limit})",
                    warning=True,
                )
            )
    return palette, notes


def _checks(palette: dict[str, str], mode: Mode) -> list[Check]:
    pairs = [(t, s, TEXT_MIN) for t in TEXT_TOKENS for s in ("bg", "card")]
    pairs.append(("on-pop", "pop", TEXT_MIN))
    return [
        Check(mode, fg, bg, contrast_ratio(palette[fg], palette[bg]), minimum)
        for fg, bg, minimum in pairs
    ]


def resolve(name: str, spec: ThemeSpec) -> Theme:
    light, light_notes = _derive(spec.light.root, "light")
    dark, dark_notes = _derive(spec.dark.root, "dark")
    return Theme(
        name=name,
        label=spec.label,
        description=spec.description,
        light=light,
        dark=dark,
        notes=light_notes + dark_notes,
        checks=_checks(light, "light") + _checks(dark, "dark"),
    )


def load_themes(path: Path) -> list[Theme]:
    """Read, validate, and resolve every theme in path. The first is the default."""
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    spec = ThemeFile.model_validate(raw)
    return [resolve(name, theme) for name, theme in spec.root.items()]


# ---- CSS ---------------------------------------------------------------------------


def _block(selector: str, palette: dict[str, str], mode: Mode) -> str:
    lines = [f"  --{t}: {palette[t]};" for t in TOKENS]
    return f"{selector} {{\n" + "\n".join(lines) + f"\n  color-scheme: {mode};\n}}\n"


def themes_css(themes: list[Theme]) -> str:
    """Custom properties for every theme. The default theme's dark palette sits on bare
    :root (so pages without JavaScript still get a full palette); data-theme picks
    light/dark and data-palette picks a non-default theme."""
    default, *others = themes
    parts = [
        "/* Generated from site/themes.yaml by portfolio.theme. Do not edit. */\n",
        _block(":root", default.dark, "dark"),
        _block(':root[data-theme="light"]', default.light, "light"),
    ]
    for theme in others:
        sel = f':root[data-palette="{theme.name}"]'
        parts.append(_block(sel, theme.dark, "dark"))
        parts.append(_block(f'{sel}[data-theme="light"]', theme.light, "light"))
    return "\n".join(parts)


def report(themes: list[Theme]) -> str:
    """Plain-text summary of each theme: what was derived or adjusted, and any failures."""
    out = []
    for i, theme in enumerate(themes):
        default = " (default)" if i == 0 else ""
        status = "ok" if theme.ok else "FAILS CONTRAST"
        out.append(f"{theme.name}{default}: {theme.label} [{status}]")
        for note in theme.notes:
            mark = "warning" if note.warning else "adjusted"
            out.append(f"  {note.mode:5} {mark:8} --{note.token}: {note.message}")
        for check in theme.checks:
            if not check.ok:
                out.append(
                    f"  {check.mode:5} FAIL     --{check.token} on --{check.against}: "
                    f"{check.ratio:.2f}:1 (need {check.minimum})"
                )
        if not theme.notes and theme.ok:
            out.append("  every color passes as given")
    return "\n".join(out)

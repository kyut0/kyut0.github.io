"""Color utilities: WCAG 2 contrast ratios for checking theme palettes."""

import re

_HEX = re.compile(r"^#([0-9a-fA-F]{6})$")

# WCAG 2 AA minimums.
TEXT_MIN = 4.5  # normal-size text
UI_MIN = 3.0  # focus rings, borders that carry meaning, large text


def _channel(value: int) -> float:
    c = value / 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def relative_luminance(hex_color: str) -> float:
    match = _HEX.match(hex_color)
    if match is None:
        raise ValueError(f"expected a #rrggbb color, got {hex_color!r}")
    digits = match.group(1)
    r, g, b = (_channel(int(digits[i : i + 2], 16)) for i in (0, 2, 4))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def chroma(hex_color: str) -> float:
    """How far a color is from gray: max channel minus min channel, 0 (gray) to 1.

    Unlike HSL saturation, this stays low for very dark colors such as navy, which read
    as calm even though HSL would call them highly saturated.
    """
    relative_luminance(hex_color)  # validates the format
    channels = [int(hex_color[i : i + 2], 16) / 255 for i in (1, 3, 5)]
    return max(channels) - min(channels)


def contrast_ratio(a: str, b: str) -> float:
    """WCAG contrast ratio between two colors, from 1 (identical) to 21 (black/white)."""
    hi, lo = sorted((relative_luminance(a), relative_luminance(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)

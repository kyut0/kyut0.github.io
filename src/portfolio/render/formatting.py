"""Display formatting shared by every renderer, so the site and PDF read the same."""

from datetime import date


def month_year(value: date | None) -> str:
    return "Present" if value is None else value.strftime("%b %Y")


def date_range(start: date, end: date | None) -> str:
    return f"{month_year(start)} – {month_year(end)}"

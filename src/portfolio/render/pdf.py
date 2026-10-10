"""Render the resume and cover letter to PDF with Typst, and combine them into one.

The validated content is handed to the Typst template as JSON through `sys.inputs`, so
content is always treated as plain text and never interpreted as Typst markup.
"""

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from pypdf import PdfWriter
import seedpalette
from seedpalette.color import TEXT_MIN, UI_MIN, ensure_contrast
import typst

from portfolio.models import Resume, Site
from portfolio.render.formatting import date_range, month_year

# Non-default themes' PDFs go in pdf/<theme name>/, next to the default theme's copies at
# the site root. site/static/download.js links the visitor's selected theme.
THEMED_DIR = "pdf"

# Layout scales tried in order until the resume fits its page budget. The floor keeps the
# body text at ~9.2pt: past that, content should be trimmed rather than shrunk further.
SCALES = (1.0, 0.97, 0.94, 0.91, 0.88)

# Theme tokens the Typst templates use, and the contrast each needs on white paper:
# text tokens must be readable; the accent only colors bullets and rules.
PDF_TOKENS = {
    "text": TEXT_MIN,
    "muted": TEXT_MIN,
    "heading": TEXT_MIN,
    "link": TEXT_MIN,
    "accent": UI_MIN,
}
PAPER = "#ffffff"


def pdf_colors(theme: seedpalette.Theme) -> dict[str, str]:
    """A theme's colors for a PDF, which always prints on white.

    Uses the theme's light palette (even for visitors browsing in dark mode), darkening
    any color too faint against white while keeping its hue.
    """
    palette = theme.palette("light")
    return {
        token: ensure_contrast(palette[token], [PAPER], minimum, darker=True)
        for token, minimum in PDF_TOKENS.items()
    }


def resume_data(resume: Resume) -> dict[str, Any]:
    """Serialize the resume to JSON-ready data, pre-formatted for display."""
    data = resume.model_dump(mode="json")
    for role, raw in zip(resume.experience, data["experience"], strict=True):
        raw["dates"] = date_range(role.start, role.end)
    data["experience"] = [raw for raw in data["experience"] if raw["in_pdf"]]
    for edu, raw in zip(resume.education, data["education"], strict=True):
        raw["dates"] = date_range(edu.start, edu.end) if edu.start else month_year(edu.end)
    for raw in data["publications"]:
        raw["authors"] = [
            {"name": author, "me": author == resume.citation_name} for author in raw["authors"]
        ]
    return data


class PdfOverflowError(RuntimeError):
    """Raised when a document can't fit its page budget even at the smallest scale."""


@dataclass(frozen=True)
class RenderedPdf:
    path: Path
    pages: int
    scale: float


def _page_count(template: Path, inputs: dict[str, str]) -> int:
    """Lay out the document and read back the page count the template exposes."""
    result = typst.query(
        str(template),
        "<page-count>",
        field="value",
        one=True,
        root=str(template.parent),
        sys_inputs=inputs,
        ignore_system_fonts=True,
    )
    return int(json.loads(result))


def _compile_to_fit(
    data: dict[str, Any],
    template: Path,
    out: Path,
    *,
    colors: dict[str, str],
    max_pages: int,
    source: str,
) -> RenderedPdf:
    """Compile at the largest scale that fits max_pages and write the PDF to out.

    source names the content file to trim if nothing fits, for the error message.
    """
    base = {"data": json.dumps(data), "colors": json.dumps(colors)}
    for scale in SCALES:
        inputs = {**base, "scale": str(scale)}
        pages = _page_count(template, inputs)
        if pages <= max_pages:
            break
    else:
        raise PdfOverflowError(
            f"{out.name} is {pages} pages even at {SCALES[-1]:.0%} scale "
            f"(limit: {max_pages}); trim content in {source}"
        )

    pdf = typst.compile(
        str(template),
        root=str(template.parent),
        sys_inputs=inputs,
        # Only use Typst's bundled fonts so local and CI builds are identical.
        ignore_system_fonts=True,
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(pdf)
    return RenderedPdf(path=out, pages=pages, scale=scale)


def build_resume_pdf(
    resume: Resume, template: Path, out: Path, *, colors: dict[str, str], max_pages: int = 1
) -> RenderedPdf:
    """Compile the resume at the largest scale that fits max_pages and write it to out."""
    return _compile_to_fit(
        resume_data(resume),
        template,
        out,
        colors=colors,
        max_pages=max_pages,
        source="content/resume.yaml",
    )


def build_cover_letter_pdf(
    resume: Resume,
    paragraphs: list[str],
    template: Path,
    out: Path,
    *,
    colors: dict[str, str],
    max_pages: int = 1,
) -> RenderedPdf:
    """Compile the cover letter under the resume's letterhead and write it to out."""
    data = {**resume_data(resume), "paragraphs": paragraphs}
    return _compile_to_fit(
        data, template, out, colors=colors, max_pages=max_pages, source="content/cover-letter.md"
    )


def combine_pdfs(parts: list[Path], out: Path, *, title: str) -> Path:
    """Concatenate parts, in order, into one PDF titled title and write it to out."""
    writer = PdfWriter()
    for part in parts:
        writer.append(part)
    writer.add_metadata({"/Title": title})
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("wb") as f:
        writer.write(f)
    return out


@dataclass(frozen=True)
class ThemedPdfs:
    theme: str
    resume: RenderedPdf
    cover_letter: RenderedPdf
    both: Path


def build_pdfs(
    site: Site, typst_dir: Path, out_dir: Path, themes: seedpalette.ThemeSet
) -> list[ThemedPdfs]:
    """Build the resume, cover letter, and both-in-one PDF in every theme's colors.

    The default (first) theme's go in out_dir itself, at the URLs the site links;
    the rest go in out_dir/pdf/<theme name>/.
    """
    built = []
    for i, theme in enumerate(themes.themes):
        folder = out_dir if i == 0 else out_dir / THEMED_DIR / theme.name
        colors = pdf_colors(theme)
        resume = build_resume_pdf(
            site.resume, typst_dir / "resume.typ", folder / "resume.pdf", colors=colors
        )
        letter = build_cover_letter_pdf(
            site.resume,
            site.cover_letter_paragraphs,
            typst_dir / "cover-letter.typ",
            folder / "cover-letter.pdf",
            colors=colors,
        )
        # The "Both" download: cover letter first, then resume.
        both = combine_pdfs(
            [letter.path, resume.path],
            folder / "cover-letter-and-resume.pdf",
            title=f"{site.resume.name} – Cover Letter and Resume",
        )
        built.append(ThemedPdfs(theme.name, resume, letter, both))
    return built

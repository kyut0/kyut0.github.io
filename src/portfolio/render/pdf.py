"""Render the resume to PDF with Typst.

The validated resume is handed to the Typst template as JSON through `sys.inputs`, so
content is always treated as plain text and never interpreted as Typst markup.
"""

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

import typst

from portfolio.models import Resume
from portfolio.render.formatting import date_range, month_year

# Layout scales tried in order until the resume fits its page budget. The floor keeps the
# body text at ~9.2pt: past that, content should be trimmed rather than shrunk further.
SCALES = (1.0, 0.97, 0.94, 0.91, 0.88)


def resume_data(resume: Resume) -> dict[str, Any]:
    """Serialize the resume to JSON-ready data, pre-formatted for display."""
    data = resume.model_dump(mode="json")
    for role, raw in zip(resume.experience, data["experience"], strict=True):
        raw["dates"] = date_range(role.start, role.end)
    for edu, raw in zip(resume.education, data["education"], strict=True):
        raw["dates"] = date_range(edu.start, edu.end) if edu.start else month_year(edu.end)
    for raw in data["publications"]:
        raw["authors"] = [
            {"name": author, "me": author == resume.citation_name} for author in raw["authors"]
        ]
    return data


class ResumeOverflowError(RuntimeError):
    """Raised when the resume can't fit the page budget even at the smallest scale."""


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


def build_resume_pdf(
    resume: Resume, template: Path, out: Path, *, max_pages: int = 1
) -> RenderedPdf:
    """Compile the resume at the largest scale that fits max_pages and write it to out."""
    data = json.dumps(resume_data(resume))
    for scale in SCALES:
        inputs = {"data": data, "scale": str(scale)}
        pages = _page_count(template, inputs)
        if pages <= max_pages:
            break
    else:
        raise ResumeOverflowError(
            f"resume is {pages} pages even at {SCALES[-1]:.0%} scale (limit: {max_pages}); "
            "trim content in content/resume.yaml"
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

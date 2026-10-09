"""Render the resume to PDF with Typst.

The validated resume is handed to the Typst template as JSON through `sys.inputs`, so
content is always treated as plain text and never interpreted as Typst markup.
"""

import json
from pathlib import Path
from typing import Any

import typst

from portfolio.models import Resume
from portfolio.render.formatting import date_range, month_year


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


def build_resume_pdf(resume: Resume, template: Path, out: Path) -> Path:
    """Compile template with the resume's data and write the PDF to out."""
    pdf = typst.compile(
        str(template),
        root=str(template.parent),
        sys_inputs={"data": json.dumps(resume_data(resume))},
        # Only use Typst's bundled fonts so local and CI builds are identical.
        ignore_system_fonts=True,
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(pdf)
    return out

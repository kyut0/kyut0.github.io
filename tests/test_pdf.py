from datetime import date
from pathlib import Path

from pypdf import PdfReader

from portfolio.load import load_resume
from portfolio.models import Resume, Role
from portfolio.render.pdf import build_resume_pdf, resume_data


def _resume(**overrides: object) -> Resume:
    fields: dict[str, object] = {"name": "Test Person", "headline": "H", "summary": "S"}
    return Resume.model_validate({**fields, **overrides})


def test_resume_data_formats_dates() -> None:
    role = Role(title="T", organization="O", start=date(2023, 3, 1))
    data = resume_data(_resume(experience=[role]))
    assert data["experience"][0]["dates"] == "Mar 2023 – Present"


def test_pdf_contains_resume_text(content_dir: Path, site_dir: Path, tmp_path: Path) -> None:
    resume = load_resume(content_dir / "resume.yaml")
    out = build_resume_pdf(resume, site_dir / "typst" / "resume.typ", tmp_path / "resume.pdf")

    reader = PdfReader(out)
    text = "".join(page.extract_text() for page in reader.pages)
    assert resume.name in text
    assert resume.experience[0].organization in text
    assert reader.metadata is not None
    assert reader.metadata.title == f"{resume.name} – Resume"


def test_markup_characters_are_rendered_literally(site_dir: Path, tmp_path: Path) -> None:
    """Content is passed as data, so Typst syntax in it must not be interpreted."""
    tricky = "C# & *bold* #let x = 1 $math$ [brackets] // not a comment"
    resume = _resume(summary=tricky)
    out = build_resume_pdf(resume, site_dir / "typst" / "resume.typ", tmp_path / "resume.pdf")
    text = PdfReader(out).pages[0].extract_text()
    assert "#let x = 1" in text
    assert "// not a comment" in text


def test_empty_sections_still_compile(site_dir: Path, tmp_path: Path) -> None:
    out = build_resume_pdf(_resume(), site_dir / "typst" / "resume.typ", tmp_path / "r.pdf")
    assert out.read_bytes().startswith(b"%PDF")

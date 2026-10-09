from datetime import date
from pathlib import Path

from pypdf import PdfReader
import pytest

from portfolio.load import load_resume
from portfolio.models import Resume, Role
from portfolio.render.pdf import SCALES, ResumeOverflowError, build_resume_pdf, resume_data


def _resume(**overrides: object) -> Resume:
    fields: dict[str, object] = {"name": "Test Person", "headline": "H", "summary": "S"}
    return Resume.model_validate({**fields, **overrides})


def _long_resume(n_roles: int) -> Resume:
    role = Role(
        title="Title",
        organization="Org",
        start=date(2020, 1, 1),
        highlights=["A fairly long highlight that takes up most of one line of text."] * 3,
    )
    return _resume(experience=[role] * n_roles)


def test_resume_data_formats_dates() -> None:
    role = Role(title="T", organization="O", start=date(2023, 3, 1))
    data = resume_data(_resume(experience=[role]))
    assert data["experience"][0]["dates"] == "Mar 2023 – Present"


def test_repo_resume_is_exactly_one_page(
    content_dir: Path, site_dir: Path, tmp_path: Path
) -> None:
    """The published resume must fit on one page: CI fails if content outgrows it."""
    resume = load_resume(content_dir / "resume.yaml")
    pdf = build_resume_pdf(resume, site_dir / "typst" / "resume.typ", tmp_path / "resume.pdf")

    reader = PdfReader(pdf.path)
    assert len(reader.pages) == pdf.pages == 1
    text = "".join(page.extract_text() for page in reader.pages)
    assert resume.name in text
    assert resume.experience[0].organization in text
    assert reader.metadata is not None
    assert reader.metadata.title == f"{resume.name} – Resume"


def test_short_resume_renders_at_full_scale(site_dir: Path, tmp_path: Path) -> None:
    pdf = build_resume_pdf(_resume(), site_dir / "typst" / "resume.typ", tmp_path / "r.pdf")
    assert pdf.scale == 1.0
    assert pdf.path.read_bytes().startswith(b"%PDF")


def test_slightly_long_resume_is_scaled_to_fit(site_dir: Path, tmp_path: Path) -> None:
    """Grow the resume until it no longer fits at full scale; it should shrink to one page."""
    template = site_dir / "typst" / "resume.typ"
    for n_roles in range(1, 20):
        pdf = build_resume_pdf(_long_resume(n_roles), template, tmp_path / "r.pdf")
        if pdf.scale < 1.0:
            assert len(PdfReader(pdf.path).pages) == 1
            return
    pytest.fail("no resume length triggered scaling")


def test_resume_too_long_at_min_scale_raises(site_dir: Path, tmp_path: Path) -> None:
    with pytest.raises(ResumeOverflowError, match=f"{SCALES[-1]:.0%}"):
        build_resume_pdf(_long_resume(40), site_dir / "typst" / "resume.typ", tmp_path / "r.pdf")
    assert not (tmp_path / "r.pdf").exists()


def test_markup_characters_are_rendered_literally(site_dir: Path, tmp_path: Path) -> None:
    """Content is passed as data, so Typst syntax in it must not be interpreted."""
    tricky = "C# & *bold* #let x = 1 $math$ [brackets] // not a comment"
    resume = _resume(summary=tricky)
    pdf = build_resume_pdf(resume, site_dir / "typst" / "resume.typ", tmp_path / "resume.pdf")
    text = PdfReader(pdf.path).pages[0].extract_text()
    assert "#let x = 1" in text
    assert "// not a comment" in text

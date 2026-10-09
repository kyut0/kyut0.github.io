from datetime import date
from pathlib import Path

from markupsafe import escape

from portfolio.cli import main
from portfolio.load import load_site
from portfolio.models import Resume
from portfolio.render import build_site
from portfolio.render.site import download_name


def test_build_writes_every_page(content_dir: Path, site_dir: Path, tmp_path: Path) -> None:
    site = load_site(content_dir)
    build_site(site, tmp_path, site_dir / "templates", site_dir / "static")

    for page in ("index.html", "resume.html", "projects.html", ".nojekyll"):
        assert (tmp_path / page).exists()
    for project in site.projects:
        assert (tmp_path / "projects" / f"{project.slug}.html").exists()
        if project.image:
            assert (tmp_path / "projects" / project.image).is_file()
    assert (tmp_path / "static" / "style.css").exists()
    index = (tmp_path / "index.html").read_text()
    assert f"<h1>{site.resume.display_name}</h1>" in index
    assert f'<p class="pronouns">{site.resume.pronouns}</p>' in index
    assert f"&copy; {date.today().year} {site.resume.display_name}" in index
    assert '<a class="brand" href="index.html">' in index


def test_project_pages_link_back_to_root(
    content_dir: Path, site_dir: Path, tmp_path: Path
) -> None:
    site = load_site(content_dir)
    build_site(site, tmp_path, site_dir / "templates", site_dir / "static")
    html = (tmp_path / "projects" / f"{site.projects[0].slug}.html").read_text()
    assert 'href="../static/style.css"' in html


def test_resume_page_bolds_own_name_in_citations(
    content_dir: Path, site_dir: Path, tmp_path: Path
) -> None:
    site = load_site(content_dir)
    build_site(site, tmp_path, site_dir / "templates", site_dir / "static")
    html = (tmp_path / "resume.html").read_text()
    assert f'<strong class="me">{site.resume.citation_name}</strong>' in html


def test_download_name_uses_citation_name_and_date() -> None:
    resume = Resume(
        name="Katherine (Katy) Yut", headline="H", summary="S", citation_name="Yut, K."
    )
    assert download_name(resume, "Resume", date(2026, 10, 9)) == "YutK_Resume_20261009.pdf"
    assert download_name(resume, "CoverLetter", date(2026, 10, 9)) == (
        "YutK_CoverLetter_20261009.pdf"
    )
    no_citation = Resume(name="Katherine (Katy) Yut", headline="H", summary="S")
    assert download_name(no_citation, "Resume", date(2026, 1, 2)) == (
        "KatherineKatyYut_Resume_20260102.pdf"
    )


def test_resume_page_sets_dated_download_name(
    content_dir: Path, site_dir: Path, tmp_path: Path
) -> None:
    site = load_site(content_dir)
    build_site(site, tmp_path, site_dir / "templates", site_dir / "static")
    html = (tmp_path / "resume.html").read_text()
    expected = download_name(site.resume, "Resume", date.today())
    assert f'href="resume.pdf" download="{expected}" data-download-stem="YutK_Resume"' in html
    assert 'src="static/download.js"' in html


def test_resume_page_links_cover_letter_pdf(
    content_dir: Path, site_dir: Path, tmp_path: Path
) -> None:
    """The cover letter is published only as a PDF, downloaded from the resume page."""
    site = load_site(content_dir)
    build_site(site, tmp_path, site_dir / "templates", site_dir / "static")
    html = (tmp_path / "resume.html").read_text()
    expected = download_name(site.resume, "CoverLetter", date.today())
    assert f'href="cover-letter.pdf" download="{expected}"' in html
    assert 'data-download-stem="YutK_CoverLetter"' in html
    assert not (tmp_path / "cover-letter.html").exists()


def test_resume_page_renders_timeline(content_dir: Path, site_dir: Path, tmp_path: Path) -> None:
    site = load_site(content_dir)
    build_site(site, tmp_path, site_dir / "templates", site_dir / "static")
    html = (tmp_path / "resume.html").read_text()
    for role in site.resume.experience:  # including roles left out of the PDF
        assert str(escape(role.title)) in html
    for project in site.projects:
        assert f'href="projects/{project.slug}.html"' in html
    assert 'src="static/timeline.js"' in html


def test_resume_page_shows_updated_date(content_dir: Path, site_dir: Path, tmp_path: Path) -> None:
    site = load_site(content_dir).model_copy(update={"resume_updated": date(2026, 10, 9)})
    build_site(site, tmp_path, site_dir / "templates", site_dir / "static")
    html = (tmp_path / "resume.html").read_text()
    assert 'Updated <time datetime="2026-10-09">Oct 9, 2026</time>' in html


def test_resume_page_omits_updated_line_without_history(
    content_dir: Path, site_dir: Path, tmp_path: Path
) -> None:
    site = load_site(content_dir).model_copy(update={"resume_updated": None})
    build_site(site, tmp_path, site_dir / "templates", site_dir / "static")
    assert "Updated" not in (tmp_path / "resume.html").read_text()


def test_cli_validate_reports_content_errors(tmp_path: Path) -> None:
    assert main(["--content", str(tmp_path), "validate"]) == 1


def test_cli_build(content_dir: Path, site_dir: Path, tmp_path: Path) -> None:
    out = tmp_path / "out"
    args = ["--content", str(content_dir), "--site-dir", str(site_dir), "--out", str(out)]
    assert main([*args, "build"]) == 0
    assert (out / "index.html").exists()
    assert (out / "resume.pdf").exists()
    assert (out / "cover-letter.pdf").exists()

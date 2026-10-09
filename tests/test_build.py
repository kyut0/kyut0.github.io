from datetime import date
from pathlib import Path

from portfolio.cli import main
from portfolio.load import load_site
from portfolio.models import Resume
from portfolio.render import build_site
from portfolio.render.site import resume_download_name


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
    assert site.resume.name in (tmp_path / "index.html").read_text()


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


def test_resume_download_name_uses_citation_name_and_date() -> None:
    resume = Resume(
        name="Katherine (Katy) Yut", headline="H", summary="S", citation_name="Yut, K."
    )
    assert resume_download_name(resume, date(2026, 10, 9)) == "YutK_Resume_20261009.pdf"
    no_citation = Resume(name="Katherine (Katy) Yut", headline="H", summary="S")
    assert resume_download_name(no_citation, date(2026, 1, 2)) == (
        "KatherineKatyYut_Resume_20260102.pdf"
    )


def test_resume_page_sets_dated_download_name(
    content_dir: Path, site_dir: Path, tmp_path: Path
) -> None:
    site = load_site(content_dir)
    build_site(site, tmp_path, site_dir / "templates", site_dir / "static")
    html = (tmp_path / "resume.html").read_text()
    expected = resume_download_name(site.resume, date.today())
    assert f'href="resume.pdf" download="{expected}" data-download-stem="YutK_Resume"' in html
    assert 'src="static/download.js"' in html


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

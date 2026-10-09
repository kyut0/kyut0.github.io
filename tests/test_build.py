from pathlib import Path

from portfolio.cli import main
from portfolio.load import load_site
from portfolio.render import build_site


def test_build_writes_every_page(content_dir: Path, site_dir: Path, tmp_path: Path) -> None:
    site = load_site(content_dir)
    build_site(site, tmp_path, site_dir / "templates", site_dir / "static")

    for page in ("index.html", "resume.html", "projects.html", ".nojekyll"):
        assert (tmp_path / page).exists()
    for project in site.projects:
        assert (tmp_path / "projects" / f"{project.slug}.html").exists()
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
    assert f"<strong>{site.resume.citation_name}</strong>" in html


def test_cli_validate_reports_content_errors(tmp_path: Path) -> None:
    assert main(["--content", str(tmp_path), "validate"]) == 1


def test_cli_build(content_dir: Path, site_dir: Path, tmp_path: Path) -> None:
    out = tmp_path / "out"
    args = ["--content", str(content_dir), "--site-dir", str(site_dir), "--out", str(out)]
    assert main([*args, "build"]) == 0
    assert (out / "index.html").exists()

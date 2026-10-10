from datetime import date
from pathlib import Path
import re
import shutil

from markupsafe import escape
from pypdf import PdfReader

from portfolio.cli import main
from portfolio.load import load_site
from portfolio.models import Resume
from portfolio.render import build_site
from portfolio.render.site import download_name


def test_build_writes_every_page(content_dir: Path, site_dir: Path, tmp_path: Path) -> None:
    site = load_site(content_dir)
    build_site(site, tmp_path, site_dir / "templates", site_dir / "static")

    for page in (
        "index.html",
        "experience.html",
        "projects.html",
        "publications.html",
        "about.html",
        ".nojekyll",
    ):
        assert (tmp_path / page).exists()
    for project in site.projects:
        assert (tmp_path / "projects" / f"{project.slug}.html").exists()
        if project.image:
            assert (tmp_path / "projects" / project.image).is_file()
    assert (tmp_path / "static" / "style.css").exists()
    assert ":root {" in (tmp_path / "static" / "themes.css").read_text()
    index = (tmp_path / "index.html").read_text()
    assert "<h1>Howdy!</h1>" in index
    assert f'<p class="pronouns">{site.resume.pronouns}</p>' in index  # in the bio panel
    assert f"&copy; {date.today().year} {site.resume.display_name}" in index
    assert '<a class="brand" href="index.html">' in index


def test_project_pages_link_back_to_root(
    content_dir: Path, site_dir: Path, tmp_path: Path
) -> None:
    site = load_site(content_dir)
    build_site(site, tmp_path, site_dir / "templates", site_dir / "static")
    html = (tmp_path / "projects" / f"{site.projects[0].slug}.html").read_text()
    assert 'href="../static/style.css?v=' in html


def test_publications_page_bolds_own_name(
    content_dir: Path, site_dir: Path, tmp_path: Path
) -> None:
    site = load_site(content_dir)
    build_site(site, tmp_path, site_dir / "templates", site_dir / "static")
    html = (tmp_path / "publications.html").read_text()
    assert f'<strong class="me">{site.resume.citation_name}</strong>' in html
    for pub in site.resume.publications:
        assert str(escape(pub.title)) in html


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


def test_experience_page_sets_dated_download_name(
    content_dir: Path, site_dir: Path, tmp_path: Path
) -> None:
    site = load_site(content_dir)
    build_site(site, tmp_path, site_dir / "templates", site_dir / "static")
    html = (tmp_path / "experience.html").read_text()
    expected = download_name(site.resume, "Resume", date.today())
    assert f'href="resume.pdf" download="{expected}" data-download-stem="YutK_Resume"' in html
    assert 'src="static/download.js?v=' in html


def test_experience_page_links_cover_letter_pdf(
    content_dir: Path, site_dir: Path, tmp_path: Path
) -> None:
    """The cover letter is published only as a PDF, downloaded from the Experience page."""
    site = load_site(content_dir)
    build_site(site, tmp_path, site_dir / "templates", site_dir / "static")
    html = (tmp_path / "experience.html").read_text()
    expected = download_name(site.resume, "CoverLetter", date.today())
    assert f'href="cover-letter.pdf" download="{expected}"' in html
    assert 'data-download-stem="YutK_CoverLetter"' in html
    assert not (tmp_path / "cover-letter.html").exists()


def test_experience_page_renders_timeline(
    content_dir: Path, site_dir: Path, tmp_path: Path
) -> None:
    site = load_site(content_dir)
    build_site(site, tmp_path, site_dir / "templates", site_dir / "static")
    html = (tmp_path / "experience.html").read_text()
    for role in site.resume.experience:  # including roles left out of the PDF
        assert str(escape(role.title)) in html
    for project in site.projects:  # write-ups link from the role they came out of
        if project.organization:
            assert f'href="projects/{project.slug}.html"' in html
    assert 'src="static/timeline.js?v=' in html


def test_footer_shows_updated_date_on_every_page(
    content_dir: Path, site_dir: Path, tmp_path: Path
) -> None:
    site = load_site(content_dir).model_copy(update={"updated": date(2026, 10, 9)})
    pages = build_site(site, tmp_path, site_dir / "templates", site_dir / "static")
    for page in pages:
        assert 'Updated <time datetime="2026-10-09">Oct 9, 2026</time>' in page.read_text()


def test_footer_omits_updated_date_without_history(
    content_dir: Path, site_dir: Path, tmp_path: Path
) -> None:
    site = load_site(content_dir).model_copy(update={"updated": None})
    build_site(site, tmp_path, site_dir / "templates", site_dir / "static")
    assert 'class="updated"' not in (tmp_path / "index.html").read_text()


def test_bio_panel_links_pdfs_from_every_page(
    content_dir: Path, site_dir: Path, tmp_path: Path
) -> None:
    site = load_site(content_dir)
    build_site(site, tmp_path, site_dir / "templates", site_dir / "static")
    project = (tmp_path / "projects" / f"{site.projects[0].slug}.html").read_text()
    assert '<aside class="bio-panel"' in project
    assert 'href="../resume.pdf"' in project
    assert 'href="../cover-letter.pdf"' in project
    assert 'href="../cover-letter-and-resume.pdf"' in project
    assert 'data-download-stem="YutK_CoverLetter_and_Resume"' in project
    assert 'src="../static/download.js?v=' in project


def test_footer_email_link_copies_address(
    content_dir: Path, site_dir: Path, tmp_path: Path
) -> None:
    site = load_site(content_dir)
    build_site(site, tmp_path, site_dir / "templates", site_dir / "static")
    html = (tmp_path / "index.html").read_text()
    email = site.resume.email
    assert f'<a href="mailto:{email}" data-copy-email="{email}"' in html
    assert ">Email</a>" in html
    assert 'src="static/copy-email.js?v=' in html


def test_bio_panel_shows_logo_links(content_dir: Path, site_dir: Path, tmp_path: Path) -> None:
    site = load_site(content_dir)
    build_site(site, tmp_path, site_dir / "templates", site_dir / "static")
    project = (tmp_path / "projects" / f"{site.projects[0].slug}.html").read_text()
    for link in site.resume.links:
        assert f'<a href="{link.url}" title="{link.label}"><img src="../static/icons/' in project
    assert 'alt="Email"' in project
    assert '<img class="bio-photo" src="../static/profile.png?v=' in project


def test_cli_validate_reports_content_errors(tmp_path: Path) -> None:
    assert main(["--content", str(tmp_path), "validate"]) == 1


def test_cli_build(content_dir: Path, site_dir: Path, tmp_path: Path) -> None:
    out = tmp_path / "out"
    args = ["--content", str(content_dir), "--site-dir", str(site_dir), "--out", str(out)]
    assert main([*args, "build"]) == 0
    assert (out / "index.html").exists()
    assert (out / "resume.pdf").exists()
    assert (out / "cover-letter.pdf").exists()
    both = PdfReader(out / "cover-letter-and-resume.pdf")
    letter, resume = PdfReader(out / "cover-letter.pdf"), PdfReader(out / "resume.pdf")
    assert [p.extract_text() for p in both.pages] == [
        p.extract_text() for p in (*letter.pages, *resume.pages)
    ]


def test_about_page_copies_its_photos(content_dir: Path, site_dir: Path, tmp_path: Path) -> None:
    content = tmp_path / "content"
    shutil.copytree(content_dir, content)
    (content / "about").mkdir(exist_ok=True)
    (content / "about" / "kiddo.jpg").write_bytes(b"jpg")
    (content / "about.md").write_text("![Me, age 5](about/kiddo.jpg)\n")
    out = tmp_path / "out"
    build_site(load_site(content), out, site_dir / "templates", site_dir / "static")
    assert 'src="about/kiddo.jpg"' in (out / "about.html").read_text()
    assert (out / "about" / "kiddo.jpg").is_file()


def test_header_lists_every_theme(content_dir: Path, site_dir: Path, tmp_path: Path) -> None:
    build_site(load_site(content_dir), tmp_path, site_dir / "templates", site_dir / "static")
    html = (tmp_path / "index.html").read_text()
    for label in ("Ember (dark)", "Ember (light)", "Sage (dark)", "Sage (light)"):
        assert f'<span class="palette-label">{label}</span>' in html
    assert 'data-palette="sage" data-mode="light"' in html
    assert "theme-toggle" not in html  # light/dark lives in the same menu now
    assert 'href="static/themes.css?v=' in html


def test_cli_themes_writes_preview(site_dir: Path, tmp_path: Path) -> None:
    preview = tmp_path / "preview.html"
    assert main(["--site-dir", str(site_dir), "themes", "--preview", str(preview)]) == 0
    assert "Sage" in preview.read_text()


def test_asset_links_change_when_files_change(
    content_dir: Path, site_dir: Path, tmp_path: Path
) -> None:
    """Fingerprinted links bust browser caches only when a file's content changes."""
    static = tmp_path / "static"
    shutil.copytree(site_dir / "static", static)
    site = load_site(content_dir)

    def style_link(out: Path) -> str:
        build_site(site, out, site_dir / "templates", static)
        match = re.search(r'href="static/style\.css\?v=(\w+)"', (out / "index.html").read_text())
        assert match
        return match.group(1)

    first = style_link(tmp_path / "a")
    assert style_link(tmp_path / "b") == first
    with (static / "style.css").open("a") as css:
        css.write("\n/* changed */\n")
    assert style_link(tmp_path / "c") != first


def test_old_resume_url_redirects(content_dir: Path, site_dir: Path, tmp_path: Path) -> None:
    build_site(load_site(content_dir), tmp_path, site_dir / "templates", site_dir / "static")
    html = (tmp_path / "resume.html").read_text()
    assert 'http-equiv="refresh" content="0; url=experience.html"' in html

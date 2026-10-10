"""Render a validated Site to static HTML with Jinja templates."""

from datetime import date
from pathlib import Path
import re
import shutil

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

from portfolio.models import Resume, Site
from portfolio.render.formatting import date_range, long_date, month_year
from portfolio.render.timeline import build_timeline
from portfolio.theme import Theme, load_themes, themes_css

PAGES = ("index.html", "experience.html", "projects.html", "publications.html", "about.html")


# Downloadable PDFs: the file each is published as, and the label in its saved name.
DOWNLOADS = {"resume": "Resume", "cover_letter": "CoverLetter"}


def download_stem(resume: Resume, label: str) -> str:
    """Saved-file prefix for a PDF, e.g. "YutK_Resume" from citation name "Yut, K."."""
    return re.sub(r"[^A-Za-z0-9]", "", resume.citation_name or resume.name) + f"_{label}"


def download_name(resume: Resume, label: str, on: date) -> str:
    """Filename visitors' browsers save a PDF as, e.g. YutK_Resume_20261009.pdf.

    The file stays at a stable URL (e.g. /resume.pdf); only the saved name carries the
    date. site/static/download.js swaps in the visitor's date at click time; this
    build-date name is the no-JavaScript fallback.
    """
    return f"{download_stem(resume, label)}_{on:%Y%m%d}.pdf"


def _environment(templates_dir: Path) -> Environment:
    env = Environment(
        loader=FileSystemLoader(templates_dir),
        autoescape=select_autoescape(["html"]),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters["month_year"] = month_year
    env.filters["long_date"] = long_date
    env.globals["date_range"] = date_range
    return env


def build_theme_preview(themes: list[Theme], templates_dir: Path, out: Path) -> Path:
    """Write a standalone page previewing every theme in both modes."""
    out.parent.mkdir(parents=True, exist_ok=True)
    html = _environment(templates_dir).get_template("themes-preview.html").render(themes=themes)
    out.write_text(html, encoding="utf-8")
    return out


def build_site(
    site: Site,
    out_dir: Path,
    templates_dir: Path,
    static_dir: Path,
    themes: list[Theme] | None = None,
) -> list[Path]:
    """Write every page plus static assets to out_dir and return the written page paths.

    themes defaults to the ones in themes.yaml next to templates_dir (i.e. site/).
    """
    if themes is None:
        themes = load_themes(templates_dir.parent / "themes.yaml")
    env = _environment(templates_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    today = date.today()
    context = {
        "site": site,
        "resume": site.resume,
        "timeline": build_timeline(site),
        "themes": themes,
        "year": today.year,
        "downloads": {
            key: {
                "name": download_name(site.resume, label, today),
                "stem": download_stem(site.resume, label),
            }
            for key, label in DOWNLOADS.items()
        },
    }
    written: list[Path] = []

    for page in PAGES:
        target = out_dir / page
        target.write_text(env.get_template(page).render(**context), encoding="utf-8")
        written.append(target)

    project_dir = out_dir / "projects"
    project_dir.mkdir(exist_ok=True)
    project_template = env.get_template("project.html")
    for project in site.projects:
        target = project_dir / f"{project.slug}.html"
        target.write_text(project_template.render(project=project, **context), encoding="utf-8")
        written.append(target)
        if project.asset_dir is not None:
            shutil.copytree(project.asset_dir, project_dir / project.slug, dirs_exist_ok=True)

    if site.about_asset_dir is not None:
        shutil.copytree(site.about_asset_dir, out_dir / "about", dirs_exist_ok=True)

    if static_dir.is_dir():
        shutil.copytree(static_dir, out_dir / "static", dirs_exist_ok=True)
    (out_dir / "static").mkdir(exist_ok=True)
    (out_dir / "static" / "themes.css").write_text(themes_css(themes), encoding="utf-8")
    # Tell GitHub Pages to serve files as-is rather than running Jekyll.
    (out_dir / ".nojekyll").touch()
    return written

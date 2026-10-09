"""Render a validated Site to static HTML with Jinja templates."""

from datetime import date
from pathlib import Path
import re
import shutil

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

from portfolio.models import Resume, Site
from portfolio.render.formatting import date_range, long_date, month_year

PAGES = ("index.html", "resume.html", "projects.html")


def resume_download_stem(resume: Resume) -> str:
    """Saved-file prefix for the PDF, e.g. "YutK_Resume" from citation name "Yut, K."."""
    return re.sub(r"[^A-Za-z0-9]", "", resume.citation_name or resume.name) + "_Resume"


def resume_download_name(resume: Resume, on: date) -> str:
    """Filename visitors' browsers save the PDF as, e.g. YutK_Resume_20261009.pdf.

    The file stays at a stable /resume.pdf URL; only the saved name carries the date.
    site/static/download.js swaps in the visitor's date at click time; this build-date
    name is the no-JavaScript fallback.
    """
    return f"{resume_download_stem(resume)}_{on:%Y%m%d}.pdf"


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


def build_site(site: Site, out_dir: Path, templates_dir: Path, static_dir: Path) -> list[Path]:
    """Write every page plus static assets to out_dir and return the written page paths."""
    env = _environment(templates_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    today = date.today()
    context = {
        "site": site,
        "resume": site.resume,
        "year": today.year,
        "resume_download_name": resume_download_name(site.resume, today),
        "resume_download_stem": resume_download_stem(site.resume),
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

    if static_dir.is_dir():
        shutil.copytree(static_dir, out_dir / "static", dirs_exist_ok=True)
    # Tell GitHub Pages to serve files as-is rather than running Jekyll.
    (out_dir / ".nojekyll").touch()
    return written

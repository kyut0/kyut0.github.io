"""Render a validated Site to static HTML with Jinja templates."""

from datetime import date
from pathlib import Path
import shutil

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

from portfolio.models import Site
from portfolio.render.formatting import date_range, month_year

PAGES = ("index.html", "resume.html", "projects.html")


def _environment(templates_dir: Path) -> Environment:
    env = Environment(
        loader=FileSystemLoader(templates_dir),
        autoescape=select_autoescape(["html"]),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters["month_year"] = month_year
    env.globals["date_range"] = date_range
    return env


def build_site(site: Site, out_dir: Path, templates_dir: Path, static_dir: Path) -> list[Path]:
    """Write every page plus static assets to out_dir and return the written page paths."""
    env = _environment(templates_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    context = {"site": site, "resume": site.resume, "year": date.today().year}
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

    if static_dir.is_dir():
        shutil.copytree(static_dir, out_dir / "static", dirs_exist_ok=True)
    # Tell GitHub Pages to serve files as-is rather than running Jekyll.
    (out_dir / ".nojekyll").touch()
    return written

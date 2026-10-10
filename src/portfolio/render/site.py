"""Render a validated Site to static HTML with Jinja templates."""

from datetime import date
import hashlib
from pathlib import Path
import re
import shutil

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape
import seedpalette

from portfolio.models import Resume, Site
from portfolio.render.formatting import date_range, long_date, month_year
from portfolio.render.timeline import build_timeline

PAGES = ("index.html", "experience.html", "projects.html", "publications.html", "about.html")


# Old page URLs that now live elsewhere; each gets a tiny redirect page.
REDIRECTS = {"resume.html": "experience.html"}

_REDIRECT_PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Moved</title>
<link rel="canonical" href="{target}">
<meta http-equiv="refresh" content="0; url={target}">
</head>
<body><p>This page moved to <a href="{target}">{target}</a>.</p></body>
</html>
"""

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


def _fingerprints(static_out: Path) -> dict[str, str]:
    """Short content hash of every file under static_out, keyed by its relative path."""
    return {
        path.relative_to(static_out).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()[:8]
        for path in sorted(static_out.rglob("*"))
        if path.is_file()
    }


def build_theme_preview(themes: seedpalette.ThemeSet, out: Path) -> Path:
    """Write seedpalette's standalone page previewing every theme in both modes."""
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(seedpalette.preview_html(themes, "Portfolio themes"), encoding="utf-8")
    return out


def build_site(
    site: Site,
    out_dir: Path,
    templates_dir: Path,
    static_dir: Path,
    themes: seedpalette.ThemeSet | None = None,
) -> list[Path]:
    """Write every page plus static assets to out_dir and return the written page paths.

    themes defaults to the ones in themes.yaml next to templates_dir (i.e. site/).
    """
    if themes is None:
        themes = seedpalette.load(templates_dir.parent / "themes.yaml")
    env = _environment(templates_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Static assets first, so pages can link them with a content fingerprint
    # (style.css?v=3f2a91c0): a changed file gets a new URL, so browsers never serve a
    # stale copy from cache after a deploy.
    static_out = out_dir / "static"
    if static_dir.is_dir():
        shutil.copytree(static_dir, static_out, dirs_exist_ok=True)
    static_out.mkdir(exist_ok=True)
    (static_out / "themes.css").write_text(seedpalette.to_css(themes), encoding="utf-8")
    versions = _fingerprints(static_out)

    def asset(path: str) -> str:
        return f"static/{path}?v={versions[path]}"

    env.globals["asset"] = asset
    today = date.today()
    context = {
        "site": site,
        "resume": site.resume,
        "timeline": build_timeline(site),
        "themes": themes.themes,
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

    for old, new in REDIRECTS.items():
        (out_dir / old).write_text(_REDIRECT_PAGE.format(target=new), encoding="utf-8")

    # Tell GitHub Pages to serve files as-is rather than running Jekyll.
    (out_dir / ".nojekyll").touch()
    return written

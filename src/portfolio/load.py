"""Read content files from disk and validate them into models."""

from pathlib import Path
from typing import Any

from markdown_it import MarkdownIt
import yaml

from portfolio.gitinfo import last_commit_date
from portfolio.models import Project, Resume, Site

_md = MarkdownIt("commonmark")


class ContentError(ValueError):
    """Raised when a content file is missing or malformed."""


def render_markdown(text: str) -> str:
    return str(_md.render(text))


def parse_front_matter(text: str) -> tuple[dict[str, Any], str]:
    """Split a Markdown document into its YAML front matter and body."""
    if not text.startswith("---\n"):
        return {}, text
    try:
        _, header, body = text.split("---\n", 2)
    except ValueError as exc:
        raise ContentError("front matter is not closed with '---'") from exc
    meta = yaml.safe_load(header) or {}
    if not isinstance(meta, dict):
        raise ContentError("front matter must be a YAML mapping")
    return meta, body


def load_resume(path: Path) -> Resume:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return Resume.model_validate(data)


def _local_image_paths(body: str) -> list[str]:
    """Return the src of every non-URL image referenced in a Markdown body."""
    paths = []
    for token in _md.parse(body):
        for child in token.children or []:
            src = child.attrGet("src")
            if child.type == "image" and isinstance(src, str) and "://" not in src:
                paths.append(src)
    return paths


def load_project(path: Path) -> Project:
    """Load a project page. Image paths are relative to the Markdown file, which mirrors
    where the page and its asset folder land in the built site."""
    meta, body = parse_front_matter(path.read_text(encoding="utf-8"))
    images = _local_image_paths(body)
    if isinstance(meta.get("image"), str):
        images.append(meta["image"])
    missing = [src for src in images if not (path.parent / src).is_file()]
    if missing:
        raise ContentError(f"{path}: image(s) not found: {', '.join(missing)}")

    asset_dir = path.parent / path.stem
    return Project.model_validate(
        {
            "slug": path.stem,
            **meta,
            "body_html": render_markdown(body),
            "asset_dir": asset_dir if asset_dir.is_dir() else None,
        }
    )


def load_site(content_dir: Path) -> Site:
    """Load and validate everything under content_dir."""
    resume_path = content_dir / "resume.yaml"
    bio_path = content_dir / "bio.md"
    for required in (resume_path, bio_path):
        if not required.is_file():
            raise ContentError(f"missing required content file: {required}")

    projects = [load_project(p) for p in sorted((content_dir / "projects").glob("*.md"))]
    projects.sort(key=lambda p: p.date, reverse=True)

    return Site(
        resume=load_resume(resume_path),
        projects=projects,
        bio_html=render_markdown(bio_path.read_text(encoding="utf-8")),
        resume_updated=last_commit_date(resume_path),
    )

"""Read content files from disk and validate them into models."""

from pathlib import Path
from typing import Any

from markdown_it import MarkdownIt
import yaml

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


def load_project(path: Path) -> Project:
    meta, body = parse_front_matter(path.read_text(encoding="utf-8"))
    return Project.model_validate({"slug": path.stem, **meta, "body_html": render_markdown(body)})


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
    )

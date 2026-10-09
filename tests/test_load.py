from pathlib import Path

import pytest

from portfolio.load import ContentError, load_project, load_site, parse_front_matter


def test_parse_front_matter_splits_meta_and_body() -> None:
    meta, body = parse_front_matter("---\ntitle: Hi\n---\nBody text\n")
    assert meta == {"title": "Hi"}
    assert body == "Body text\n"


def test_parse_front_matter_without_header_returns_body() -> None:
    assert parse_front_matter("just text") == ({}, "just text")


def test_parse_front_matter_rejects_unclosed_header() -> None:
    with pytest.raises(ContentError):
        parse_front_matter("---\ntitle: Hi\n")


def test_load_project_uses_filename_as_slug(tmp_path: Path) -> None:
    path = tmp_path / "flood-mapping.md"
    path.write_text("---\ntitle: Flood\nsummary: S\ndate: 2024-05-01\n---\n# Heading\n")
    project = load_project(path)
    assert project.slug == "flood-mapping"
    assert "<h1>Heading</h1>" in project.body_html


def test_missing_required_file_raises(tmp_path: Path) -> None:
    with pytest.raises(ContentError, match=r"resume\.yaml"):
        load_site(tmp_path)


def test_repo_content_is_valid(content_dir: Path) -> None:
    """The real content in content/ must always validate."""
    site = load_site(content_dir)
    assert site.resume.name

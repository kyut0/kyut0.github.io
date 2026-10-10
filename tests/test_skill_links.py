"""Linked tools (resume.yaml skill_links): chips that link to a page instead of tracing
the timeline, kept off the PDF. "touch typing" uses this as an easter-egg breadcrumb."""

from datetime import date
from pathlib import Path
from typing import Any

import pytest

from portfolio.load import load_site
from portfolio.models import Resume, skill_key
from portfolio.render import build_site
from portfolio.render.pdf import resume_data


def _resume(**overrides: Any) -> Resume:
    data: dict[str, Any] = {
        "name": "K",
        "headline": "H",
        "summary": "S",
        "experience": [
            {
                "title": "Analyst",
                "organization": "BEG",
                "start": date(2022, 5, 1),
                "skills": ["R", "touch typing"],
            }
        ],
        "skills": [{"category": "Expert", "items": ["R", "touch typing"]}],
        "skill_links": {"touch typing": "type.html"},
    }
    return Resume.model_validate({**data, **overrides})


def test_linked_skills_match_any_spelling() -> None:
    assert _resume().linked_skills() == {"touchtyping": "type.html"}


def test_link_must_name_a_toolbox_tool() -> None:
    with pytest.raises(ValueError, match="'speed reading', which isn't in the toolbox"):
        _resume(skill_links={"speed reading": "type.html"})


@pytest.mark.parametrize("target", ["https://monkeytype.com", "/type.html", "type"])
def test_link_must_be_a_site_page(target: str) -> None:
    with pytest.raises(ValueError, match="must be a site page"):
        _resume(skill_links={"touch typing": target})


def test_linked_skills_stay_off_the_pdf() -> None:
    data = resume_data(_resume())
    assert data["experience"][0]["skills"] == ["R"]
    assert data["skills"] == [{"category": "Expert", "items": ["R"]}]
    assert "skill_links" not in data


def test_a_toolbox_group_of_only_linked_skills_is_dropped_from_the_pdf() -> None:
    resume = _resume(
        skills=[
            {"category": "Expert", "items": ["R"]},
            {"category": "Secret", "items": ["touch typing"]},
        ]
    )
    assert [g["category"] for g in resume_data(resume)["skills"]] == ["Expert"]


def test_experience_page_links_linked_chips(
    content_dir: Path, site_dir: Path, tmp_path: Path
) -> None:
    site = load_site(content_dir)
    build_site(site, tmp_path, site_dir / "templates", site_dir / "static")
    html = (tmp_path / "experience.html").read_text()
    for name, target in site.resume.skill_links.items():
        assert (tmp_path / target).is_file(), f"{name} links to a page that isn't built"
        assert f'<a class="chip chip-link" href="{target}"' in html  # toolbox
        # ...and on every card that uses it, never as a timeline-tracing button.
        assert f'data-skill="{skill_key(name)}"' not in html

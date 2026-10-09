from datetime import date
from pathlib import Path

from pydantic import ValidationError
import pytest

from portfolio.load import load_site
from portfolio.models import (
    Education,
    Project,
    Publication,
    Resume,
    Role,
    Site,
    SkillGroup,
    skill_key,
)
from portfolio.render.timeline import build_timeline


def _site(projects: list[Project] | None = None, **resume_fields: object) -> Site:
    resume = Resume.model_validate(
        {"name": "Test Person", "headline": "H", "summary": "S", **resume_fields}
    )
    return Site(resume=resume, projects=projects or [], bio_html="", cover_letter_paragraphs=[])


def _roles() -> list[Role]:
    return [
        Role(
            title="New",
            organization="B",
            start=date(2024, 1, 1),
            skills=["Python", "SQL", "Google Earth Engine"],
        ),
        Role(
            title="Old",
            organization="A",
            start=date(2020, 1, 1),
            end=date(2021, 6, 1),
            skills=["R", "Python"],
        ),
    ]


def _pub(year: int, organization: str | None = None) -> Publication:
    return Publication(
        authors=["Person, T."],
        year=year,
        title=f"Paper {year}",
        venue="Journal",
        organization=organization,
    )


def _project(organization: str | None, on: date = date(2021, 3, 1)) -> Project:
    return Project(slug="maps", title="Maps", summary="S", date=on, organization=organization)


def test_skill_key_matches_spellings() -> None:
    assert skill_key("R Shiny") == skill_key("RShiny") == skill_key("r-shiny") == "rshiny"
    assert skill_key("Google Earth Engine") == skill_key("google-earth-engine")


def test_events_are_newest_first_without_projects_or_papers() -> None:
    site = _site(
        projects=[_project(None)],
        experience=_roles(),
        education=[Education(degrees=["BS"], institution="U", end=date(2019, 5, 1))],
        publications=[_pub(2022, "A")],
    )
    timeline = build_timeline(site)
    assert [e.title for e in timeline.events] == ["New", "Old", "U"]
    assert timeline.kinds == {"work": "Work", "education": "Education"}


def test_write_up_after_role_ends_links_from_nearest_role() -> None:
    older = Role(title="Older", organization="A", start=date(2015, 1, 1), end=date(2016, 1, 1))
    site = _site(projects=[_project("A", on=date(2023, 1, 1))], experience=[*_roles(), older])
    events = {e.title: e for e in build_timeline(site).events}
    assert [w.title for w in events["Old"].write_ups] == ["Maps"]
    assert events["Older"].write_ups == []


def test_project_write_ups_link_from_their_role() -> None:
    site = _site(projects=[_project("A")], experience=_roles())
    events = {e.title: e for e in build_timeline(site).events}
    assert [w.url for w in events["Old"].write_ups] == ["projects/maps.html"]
    assert events["New"].write_ups == []


def test_unknown_organizations_are_rejected() -> None:
    with pytest.raises(ValidationError, match="matches no role or school"):
        _site(experience=_roles(), publications=[_pub(2021, "Nowhere")])
    with pytest.raises(ValidationError, match="matches no role or school"):
        _site(projects=[_project("Nowhere")], experience=_roles())


def test_tools_are_new_only_at_first_use() -> None:
    timeline = build_timeline(_site(experience=_roles()))
    new = {e.title: [s.label for s in e.skills if s.new] for e in timeline.events}
    assert new == {"Old": ["R", "Python"], "New": ["SQL", "Google Earth Engine"]}


def _toolbox(*extra: str, gee: str = "Google Earth Engine") -> list[SkillGroup]:
    """A toolbox matching _roles(), plus any extra tools."""
    return [SkillGroup(category="Expert", items=["R", "Python", "SQL", gee, *extra])]


def test_labels_prefer_toolbox_spelling() -> None:
    site = _site(experience=_roles(), skills=_toolbox(gee="Google earth engine"))
    new_role = next(e for e in build_timeline(site).events if e.title == "New")
    assert new_role.skills[-1].label == "Google earth engine"


def test_toolbox_counts_events_using_each_skill() -> None:
    site = _site(experience=_roles(), skills=_toolbox())
    counts = {s.label: s.count for s in build_timeline(site).toolbox[0].skills}
    assert counts == {"R": 1, "Python": 2, "SQL": 1, "Google Earth Engine": 1}


def test_education_tools_join_the_timeline() -> None:
    school = Education(degrees=["BS"], institution="U", end=date(2019, 5, 1), skills=["Fortran"])
    site = _site(experience=_roles(), education=[school], skills=_toolbox("Fortran"))
    events = {e.title: e for e in build_timeline(site).events}
    assert [(s.label, s.new) for s in events["U"].skills] == [("Fortran", True)]


def test_toolbox_tool_on_no_card_is_rejected() -> None:
    with pytest.raises(ValidationError, match="'Fortran' is in the toolbox but on no role"):
        _site(experience=_roles(), skills=_toolbox("Fortran"))


def test_card_tool_missing_from_toolbox_is_rejected() -> None:
    toolbox = [SkillGroup(category="Expert", items=["R", "Python", "SQL"])]
    with pytest.raises(ValidationError, match="'Google Earth Engine' is used on a role"):
        _site(experience=_roles(), skills=toolbox)


def test_repo_timeline_has_no_duplicates(content_dir: Path) -> None:
    """Every role and school appears exactly once."""
    site = load_site(content_dir)
    titles = [e.title for e in build_timeline(site).events]
    assert len(titles) == len(set(titles))
    assert {r.title for r in site.resume.experience} <= set(titles)

from datetime import date
from pathlib import Path

from portfolio.load import load_site
from portfolio.models import Education, Project, Publication, Resume, Role, Site, SkillGroup
from portfolio.render.timeline import build_timeline, skill_key


def _site(**resume_fields: object) -> Site:
    resume = Resume.model_validate(
        {"name": "Test Person", "headline": "H", "summary": "S", **resume_fields}
    )
    project = Project(
        slug="maps",
        title="Maps",
        summary="A map project.",
        date=date(2023, 6, 1),
        tags=["python", "google-earth-engine"],
    )
    return Site(resume=resume, projects=[project], bio_html="", cover_letter_paragraphs=[])


def _roles() -> list[Role]:
    return [
        Role(title="New", organization="B", start=date(2024, 1, 1), skills=["Python", "SQL"]),
        Role(title="Old", organization="A", start=date(2020, 1, 1), skills=["R", "Python"]),
    ]


def test_skill_key_matches_spellings() -> None:
    assert skill_key("R Shiny") == skill_key("RShiny") == skill_key("r-shiny") == "rshiny"
    assert skill_key("Google Earth Engine") == skill_key("google-earth-engine")


def test_events_are_newest_first_across_kinds() -> None:
    site = _site(
        experience=_roles(),
        education=[Education(degrees=["BS"], institution="U", end=date(2019, 5, 1))],
        publications=[
            Publication(authors=["Person, T."], year=2021, title="Paper", venue="Journal")
        ],
    )
    timeline = build_timeline(site)
    assert [e.title for e in timeline.events] == ["New", "Maps", "Paper", "Old", "U"]
    assert list(timeline.kinds) == ["work", "education", "project", "research"]


def test_tools_are_new_only_at_first_use() -> None:
    timeline = build_timeline(_site(experience=_roles()))
    new = {e.title: [s.label for s in e.skills if s.new] for e in timeline.events}
    assert new == {"Old": ["R", "Python"], "Maps": ["google-earth-engine"], "New": ["SQL"]}


def test_labels_prefer_resume_spelling_over_tag_slugs() -> None:
    site = _site(
        experience=_roles(),
        skills=[SkillGroup(category="Expert", items=["Google Earth Engine"])],
    )
    maps = next(e for e in build_timeline(site).events if e.title == "Maps")
    assert [s.label for s in maps.skills] == ["Python", "Google Earth Engine"]


def test_toolbox_counts_events_using_each_skill() -> None:
    site = _site(
        experience=_roles(),
        skills=[SkillGroup(category="Expert", items=["Python", "Fortran"])],
    )
    counts = {s.label: s.count for s in build_timeline(site).toolbox[0].skills}
    assert counts == {"Python": 3, "Fortran": 0}


def test_repo_timeline_includes_every_role(content_dir: Path) -> None:
    site = load_site(content_dir)
    titles = {e.title for e in build_timeline(site).events}
    assert {r.title for r in site.resume.experience} <= titles

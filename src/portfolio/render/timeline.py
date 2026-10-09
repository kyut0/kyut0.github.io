"""Turn the resume and projects into one dated timeline for the site.

Roles, education, projects, and publications become events, newest first. Walking them
oldest first, each tool is marked "new" on the first event that uses it, so the timeline
shows where every skill was picked up along the way.
"""

from dataclasses import dataclass, field
from datetime import date
import re

from portfolio.models import Site
from portfolio.render.formatting import date_range, month_year

KINDS = {
    "work": "Work",
    "education": "Education",
    "project": "Projects",
    "research": "Research",
}


def skill_key(name: str) -> str:
    """Match spellings of the same tool: "R Shiny", "RShiny" and "r-shiny" -> "rshiny"."""
    return re.sub(r"[^a-z0-9]", "", name.lower())


@dataclass(frozen=True)
class SkillUse:
    key: str
    label: str
    new: bool  # first event (oldest first) to use this tool


@dataclass
class Event:
    kind: str
    when: date  # sort date; for ranges, the start
    date_label: str
    title: str
    subtitle: str = ""
    location: str | None = None
    url: str | None = None  # relative to the site root
    details: list[str] = field(default_factory=list)
    raw_skills: list[str] = field(default_factory=list)
    skills: list[SkillUse] = field(default_factory=list)
    authors: list[tuple[str, bool]] = field(default_factory=list)  # (name, is_me)


@dataclass(frozen=True)
class ToolboxSkill:
    key: str
    label: str
    count: int  # timeline events that use it


@dataclass(frozen=True)
class ToolboxGroup:
    category: str
    skills: list[ToolboxSkill]


@dataclass(frozen=True)
class Timeline:
    events: list[Event]  # newest first
    toolbox: list[ToolboxGroup]
    kinds: dict[str, str]  # kinds present, in KINDS order: key -> label


def _events(site: Site) -> list[Event]:
    resume = site.resume
    events = [
        Event(
            kind="work",
            when=role.start,
            date_label=date_range(role.start, role.end),
            title=role.title,
            subtitle=role.organization,
            location=role.location,
            details=role.highlights,
            raw_skills=role.skills,
        )
        for role in resume.experience
    ]
    events += [
        Event(
            kind="education",
            when=edu.start or edu.end,
            date_label=date_range(edu.start, edu.end) if edu.start else month_year(edu.end),
            title=edu.institution,
            subtitle=edu.honors or "",
            location=edu.location,
            details=edu.degrees,
        )
        for edu in resume.education
    ]
    events += [
        Event(
            kind="project",
            when=project.date,
            date_label=month_year(project.date),
            title=project.title,
            url=f"projects/{project.slug}.html",
            details=[project.summary],
            raw_skills=project.tags,
        )
        for project in site.projects
    ]
    events += [
        Event(
            kind="research",
            when=date(pub.year, 1, 1),
            date_label=str(pub.year),
            title=pub.title,
            subtitle=pub.venue,
            url=str(pub.url) if pub.url else None,
            authors=[(a, a == resume.citation_name) for a in pub.authors],
        )
        for pub in resume.publications
    ]
    return events


def build_timeline(site: Site) -> Timeline:
    events = _events(site)

    # Display labels: prefer the resume's spelling ("Google Earth Engine") over project
    # tag slugs ("google-earth-engine").
    labels: dict[str, str] = {}
    for group in site.resume.skills:
        for item in group.items:
            labels.setdefault(skill_key(item), item)
    for event in sorted(events, key=lambda e: e.kind == "project"):
        for name in event.raw_skills:
            labels.setdefault(skill_key(name), name)

    # Oldest first so "new" lands on the first use. Stable sort keeps file order on ties.
    seen: set[str] = set()
    counts: dict[str, int] = {}
    for event in sorted(events, key=lambda e: e.when):
        for name in event.raw_skills:
            key = skill_key(name)
            if any(s.key == key for s in event.skills):
                continue
            event.skills.append(SkillUse(key=key, label=labels[key], new=key not in seen))
            seen.add(key)
            counts[key] = counts.get(key, 0) + 1

    toolbox = [
        ToolboxGroup(
            category=group.category,
            skills=[
                ToolboxSkill(skill_key(i), i, counts.get(skill_key(i), 0)) for i in group.items
            ],
        )
        for group in site.resume.skills
    ]
    present = {e.kind for e in events}
    return Timeline(
        events=sorted(events, key=lambda e: e.when, reverse=True),
        toolbox=toolbox,
        kinds={k: v for k, v in KINDS.items() if k in present},
    )

"""Turn the resume into one dated timeline for the site.

Roles and education become events, newest first. Project write-ups that name an
`organization` are linked from that role or school's event. (Publications have their own
page.) Walking the events oldest first, each tool is marked "new" on the first event that
uses it, so the timeline shows where every skill was picked up along the way.
"""

from dataclasses import dataclass, field
from datetime import date

from portfolio.models import Site, skill_key
from portfolio.render.formatting import date_range, month_year

KINDS = {
    "work": "Work",
    "education": "Education",
}


@dataclass(frozen=True)
class SkillUse:
    key: str
    label: str
    new: bool  # first event (oldest first) to use this tool


@dataclass(frozen=True)
class WriteUp:
    title: str
    url: str  # relative to the site root


@dataclass
class Event:
    kind: str
    when: date  # sort date; for ranges, the start
    until: date | None  # end of the range; None for ongoing or single dates
    date_label: str
    title: str
    subtitle: str = ""
    organization: str | None = None  # what project write-ups attach by
    location: str | None = None
    details: list[str] = field(default_factory=list)
    raw_skills: list[str] = field(default_factory=list)
    skills: list[SkillUse] = field(default_factory=list)
    write_ups: list[WriteUp] = field(default_factory=list)

    def covers(self, day: date) -> bool:
        return self.when <= day <= (self.until or date.max)


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


def _host(events: list[Event], organization: str, on: date) -> Event:
    """The event for organization covering `on`, or the one starting closest to it when
    none does (e.g. a write-up dated after the role ended)."""
    candidates = [e for e in events if e.organization == organization]
    covering = [e for e in candidates if e.covers(on)]
    return (covering or sorted(candidates, key=lambda e: abs((e.when - on).days)))[0]


def _events(site: Site) -> list[Event]:
    resume = site.resume
    events = [
        Event(
            kind="work",
            when=role.start,
            until=role.end,
            date_label=date_range(role.start, role.end),
            title=role.title,
            subtitle=role.organization,
            organization=role.organization,
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
            until=edu.end,
            date_label=date_range(edu.start, edu.end) if edu.start else month_year(edu.end),
            title=edu.institution,
            subtitle=edu.honors or "",
            organization=edu.institution,
            location=edu.location,
            details=edu.degrees,
            raw_skills=edu.skills,
        )
        for edu in resume.education
    ]

    for project in site.projects:
        if project.organization:
            host = _host(events, project.organization, project.date)
            host.write_ups.append(WriteUp(project.title, f"projects/{project.slug}.html"))
    return events


def build_timeline(site: Site) -> Timeline:
    events = _events(site)

    # Display labels: prefer the toolbox's spelling, then the first role's.
    labels: dict[str, str] = {}
    for group in site.resume.skills:
        for item in group.items:
            labels.setdefault(skill_key(item), item)
    for event in events:
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

"""Typed schemas for portfolio content.

Every content file is validated against these models before anything is rendered, so a
malformed date or a misspelled field fails the build (and CI) instead of shipping.
"""

from datetime import date
from pathlib import Path
import re
from typing import Annotated, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    StringConstraints,
    model_validator,
)


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


def skill_key(name: str) -> str:
    """Match spellings of the same tool: "R Shiny", "RShiny" and "r-shiny" -> "rshiny"."""
    return re.sub(r"[^a-z0-9]", "", name.lower())


class Link(_Model):
    label: str
    url: HttpUrl


class Role(_Model):
    title: str
    organization: str
    location: str | None = None
    start: date
    end: date | None = None  # None means current role
    highlights: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)  # tools used in this role
    in_pdf: bool = True  # False: on the site's timeline only, to keep the PDF to one page

    @model_validator(mode="after")
    def _end_after_start(self) -> Self:
        if self.end is not None and self.end < self.start:
            raise ValueError(f"role '{self.title}' ends ({self.end}) before it starts")
        return self


class Education(_Model):
    degrees: list[str] = Field(min_length=1)
    institution: str
    location: str | None = None
    start: date | None = None
    end: date
    honors: str | None = None
    skills: list[str] = Field(default_factory=list)  # tools used while studying


# "Last, F. M." -- also catches YAML flow lists like [Smye, K. M.] silently splitting names.
Author = Annotated[str, StringConstraints(pattern=r"^[^,]+, (?:[A-Z]\.\s?)+$")]


class Publication(_Model):
    authors: list[Author] = Field(min_length=1)
    year: int
    title: str
    venue: str
    url: HttpUrl | None = None
    # The role's organization or school's institution this came out of; shown as context
    # on the publications page.
    organization: str | None = None


class SkillGroup(_Model):
    category: str
    items: list[str] = Field(min_length=1)


class Resume(_Model):
    name: str
    # Shorter name for casual spots (home page, footer); falls back to name.
    short_name: str | None = None
    pronouns: str | None = None
    headline: str
    summary: str
    location: str | None = None
    email: str | None = None
    # How your name appears in author lists, so renderers can bold it.
    citation_name: str | None = None
    links: list[Link] = Field(default_factory=list)
    experience: list[Role] = Field(default_factory=list)
    education: list[Education] = Field(default_factory=list)
    publications: list[Publication] = Field(default_factory=list)
    # Tool tiers (the site's toolbox). When set, they must match the tools listed on roles
    # and education exactly: see _toolbox_matches_cards.
    skills: list[SkillGroup] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)  # soft skills; PDF only

    @property
    def display_name(self) -> str:
        return self.short_name or self.name

    @model_validator(mode="after")
    def _citation_name_is_used(self) -> Self:
        if (
            self.citation_name
            and self.publications
            and not any(self.citation_name in p.authors for p in self.publications)
        ):
            raise ValueError(f"citation_name '{self.citation_name}' is in no author list")
        return self

    @model_validator(mode="after")
    def _toolbox_matches_cards(self) -> Self:
        """Every toolbox tool is used on some role or school, and every tool used there is
        in the toolbox, so the site's toolbox and timeline always agree."""
        if not self.skills:
            return self
        toolbox = {skill_key(i): i for g in self.skills for i in g.items}
        used: dict[str, str] = {}
        card_tools = [r.skills for r in self.experience] + [e.skills for e in self.education]
        for tools in card_tools:
            for name in tools:
                used.setdefault(skill_key(name), name)
        problems = [
            f"'{name}' is in the toolbox but on no role or school"
            for key, name in toolbox.items()
            if key not in used
        ]
        problems += [
            f"'{name}' is used on a role or school but missing from the toolbox"
            for key, name in used.items()
            if key not in toolbox
        ]
        if problems:
            raise ValueError("toolbox and timeline disagree: " + "; ".join(problems))
        return self

    def organizations(self) -> set[str]:
        return {r.organization for r in self.experience} | {e.institution for e in self.education}

    @model_validator(mode="after")
    def _publication_organizations_exist(self) -> Self:
        known = self.organizations()
        for pub in self.publications:
            if pub.organization and pub.organization not in known:
                raise ValueError(
                    f"publication '{pub.title}' names organization '{pub.organization}', "
                    "which matches no role or school"
                )
        return self


class Project(_Model):
    slug: str = Field(pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$")
    title: str
    summary: str
    date: date
    tags: list[str] = Field(default_factory=list)
    repo: HttpUrl | None = None
    # The role's organization (or school) this was done for; the site timeline links the
    # write-up from that entry.
    organization: str | None = None
    # Card thumbnail, relative to the project's Markdown file (e.g. "my-project/thumb.png").
    image: str | None = None
    body_html: str = ""
    # content/projects/<slug>/, if it exists; copied next to the rendered page.
    asset_dir: Path | None = Field(default=None, exclude=True)


class Site(_Model):
    resume: Resume
    projects: list[Project]
    bio_html: str
    about_html: str = ""
    # content/about/, if it exists: photos and art for the About page, copied alongside it.
    about_asset_dir: Path | None = Field(default=None, exclude=True)
    cover_letter_paragraphs: list[str]  # plain text; the letter is published only as a PDF
    resume_updated: date | None = None  # last commit to content/resume.yaml

    @model_validator(mode="after")
    def _project_organizations_exist(self) -> Self:
        known = self.resume.organizations()
        for project in self.projects:
            if project.organization and project.organization not in known:
                raise ValueError(
                    f"project '{project.slug}' names organization '{project.organization}', "
                    "which matches no role or school"
                )
        return self

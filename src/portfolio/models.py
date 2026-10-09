"""Typed schemas for portfolio content.

Every content file is validated against these models before anything is rendered, so a
malformed date or a misspelled field fails the build (and CI) instead of shipping.
"""

from datetime import date
from pathlib import Path
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


# "Last, F. M." -- also catches YAML flow lists like [Smye, K. M.] silently splitting names.
Author = Annotated[str, StringConstraints(pattern=r"^[^,]+, (?:[A-Z]\.\s?)+$")]


class Publication(_Model):
    authors: list[Author] = Field(min_length=1)
    year: int
    title: str
    venue: str
    url: HttpUrl | None = None


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
    skills: list[SkillGroup] = Field(default_factory=list)

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


class Project(_Model):
    slug: str = Field(pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$")
    title: str
    summary: str
    date: date
    tags: list[str] = Field(default_factory=list)
    repo: HttpUrl | None = None
    # Card thumbnail, relative to the project's Markdown file (e.g. "my-project/thumb.png").
    image: str | None = None
    body_html: str = ""
    # content/projects/<slug>/, if it exists; copied next to the rendered page.
    asset_dir: Path | None = Field(default=None, exclude=True)


class Site(_Model):
    resume: Resume
    projects: list[Project]
    bio_html: str
    cover_letter_html: str
    cover_letter_paragraphs: list[str]  # plain text, for the PDF
    resume_updated: date | None = None  # last commit to content/resume.yaml

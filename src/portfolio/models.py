"""Typed schemas for portfolio content.

Every content file is validated against these models before anything is rendered, so a
malformed date or a misspelled field fails the build (and CI) instead of shipping.
"""

from datetime import date
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator


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

    @model_validator(mode="after")
    def _end_after_start(self) -> Self:
        if self.end is not None and self.end < self.start:
            raise ValueError(f"role '{self.title}' ends ({self.end}) before it starts")
        return self


class Education(_Model):
    degree: str
    institution: str
    year: int


class SkillGroup(_Model):
    category: str
    items: list[str] = Field(min_length=1)


class Resume(_Model):
    name: str
    headline: str
    summary: str
    location: str | None = None
    links: list[Link] = Field(default_factory=list)
    experience: list[Role] = Field(default_factory=list)
    education: list[Education] = Field(default_factory=list)
    skills: list[SkillGroup] = Field(default_factory=list)


class Project(_Model):
    slug: str = Field(pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$")
    title: str
    summary: str
    date: date
    tags: list[str] = Field(default_factory=list)
    repo: HttpUrl | None = None
    image: str | None = None  # path relative to site/static/
    body_html: str = ""


class Site(_Model):
    resume: Resume
    projects: list[Project]
    bio_html: str

from datetime import date

from pydantic import ValidationError
import pytest

from portfolio.models import Project, Publication, Resume, Role


def test_role_rejects_end_before_start() -> None:
    with pytest.raises(ValidationError, match="ends"):
        Role(title="T", organization="O", start=date(2024, 1, 1), end=date(2023, 1, 1))


def test_role_without_end_is_current() -> None:
    assert Role(title="T", organization="O", start=date(2024, 1, 1)).end is None


def test_unknown_fields_are_rejected() -> None:
    with pytest.raises(ValidationError, match="extra"):
        Role.model_validate(
            {"title": "T", "organization": "O", "start": "2024-01-01", "titel": "typo"}
        )


def _publication(authors: list[str]) -> Publication:
    return Publication(authors=authors, year=2024, title="T", venue="V")


@pytest.mark.parametrize("author", ["Smye, K. M.", "Maraggi, L. M. R.", "Yut, K."])
def test_publication_accepts_last_first_initials(author: str) -> None:
    assert _publication([author]).authors == [author]


@pytest.mark.parametrize("author", ["Smye", "K. M.", "KM Smye", "Smye, KM"])
def test_publication_rejects_malformed_authors(author: str) -> None:
    """Catches YAML flow lists like [Smye, K. M.] splitting one name into two."""
    with pytest.raises(ValidationError):
        _publication([author])


def test_citation_name_must_appear_in_some_publication() -> None:
    with pytest.raises(ValidationError, match="citation_name"):
        Resume(
            name="N",
            headline="H",
            summary="S",
            citation_name="Yut, K.",
            publications=[_publication(["Smye, K. M."])],
        )


@pytest.mark.parametrize("slug", ["Bad Slug", "trailing-", "UPPER"])
def test_project_slug_must_be_kebab_case(slug: str) -> None:
    with pytest.raises(ValidationError):
        Project(slug=slug, title="T", summary="S", date=date(2024, 1, 1))


def test_display_name_prefers_short_name() -> None:
    fields = {"name": "Katherine (Katy) Yut", "headline": "H", "summary": "S"}
    assert Resume.model_validate(fields).display_name == "Katherine (Katy) Yut"
    short = Resume.model_validate({**fields, "short_name": "Katy Yut"})
    assert short.display_name == "Katy Yut"

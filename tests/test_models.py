from datetime import date

from pydantic import ValidationError
import pytest

from portfolio.models import Project, Role


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


@pytest.mark.parametrize("slug", ["Bad Slug", "trailing-", "UPPER"])
def test_project_slug_must_be_kebab_case(slug: str) -> None:
    with pytest.raises(ValidationError):
        Project(slug=slug, title="T", summary="S", date=date(2024, 1, 1))

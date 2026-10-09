from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def content_dir() -> Path:
    return REPO_ROOT / "content"


@pytest.fixture
def site_dir() -> Path:
    return REPO_ROOT / "site"

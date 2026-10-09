from datetime import date
import os
from pathlib import Path
import subprocess

import pytest

from portfolio.gitinfo import last_commit_date


def _git(repo: Path, *args: str, when: str = "2026-01-15T12:00:00") -> None:
    env = {**os.environ, "GIT_AUTHOR_DATE": when, "GIT_COMMITTER_DATE": when}
    subprocess.run(
        ["git", "-c", "user.name=T", "-c", "user.email=t@example.com", *args],
        cwd=repo,
        env=env,
        check=True,
        capture_output=True,
    )


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A repo where resume.yaml last changed on 2026-01-15 and other.txt on 2026-03-01."""
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init", "-q")
    (root / "resume.yaml").write_text("v1")
    _git(root, "add", "resume.yaml")
    _git(root, "commit", "-qm", "resume", when="2026-01-15T12:00:00")
    (root / "other.txt").write_text("x")
    _git(root, "add", "other.txt")
    _git(root, "commit", "-qm", "other", when="2026-03-01T12:00:00")
    return root


def test_uses_last_commit_that_touched_the_file(repo: Path) -> None:
    assert last_commit_date(repo / "resume.yaml") == date(2026, 1, 15)


def test_uncommitted_file_has_no_date(repo: Path) -> None:
    (repo / "new.yaml").write_text("x")
    assert last_commit_date(repo / "new.yaml") is None


def test_outside_a_repo_has_no_date(tmp_path: Path) -> None:
    (tmp_path / "resume.yaml").write_text("x")
    assert last_commit_date(tmp_path / "resume.yaml") is None


def test_shallow_clone_has_no_date(repo: Path, tmp_path: Path) -> None:
    """A depth-1 clone would wrongly report the newest commit's date for every file."""
    clone = tmp_path / "shallow"
    subprocess.run(
        ["git", "clone", "-q", "--depth", "1", f"file://{repo}", str(clone)],
        check=True,
        capture_output=True,
    )
    assert last_commit_date(clone / "resume.yaml") is None

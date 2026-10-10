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
    """A repo committed to on 2026-01-15 and last on 2026-03-01, outside content/."""
    root = tmp_path / "repo"
    (root / "content").mkdir(parents=True)
    _git(root, "init", "-q")
    (root / "content" / "resume.yaml").write_text("v1")
    _git(root, "add", ".")
    _git(root, "commit", "-qm", "resume", when="2026-01-15T12:00:00")
    (root / "other.txt").write_text("x")
    _git(root, "add", "other.txt")
    _git(root, "commit", "-qm", "other", when="2026-03-01T12:00:00")
    return root


def test_uses_newest_commit_anywhere_in_the_repo(repo: Path) -> None:
    assert last_commit_date(repo / "content") == date(2026, 3, 1)


def test_repo_without_commits_has_no_date(tmp_path: Path) -> None:
    _git(tmp_path, "init", "-q")
    assert last_commit_date(tmp_path) is None


def test_outside_a_repo_has_no_date(tmp_path: Path) -> None:
    assert last_commit_date(tmp_path) is None


def test_shallow_clone_still_has_newest_commit(repo: Path, tmp_path: Path) -> None:
    clone = tmp_path / "shallow"
    subprocess.run(
        ["git", "clone", "-q", "--depth", "1", f"file://{repo}", str(clone)],
        check=True,
        capture_output=True,
    )
    assert last_commit_date(clone) == date(2026, 3, 1)

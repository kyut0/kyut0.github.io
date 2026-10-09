"""Read facts about content from git history."""

from datetime import date
from pathlib import Path
import subprocess


def _git(path: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=path.parent, capture_output=True, text=True, check=True
    )
    return result.stdout.strip()


def last_commit_date(path: Path) -> date | None:
    """Date of the last commit that changed path, or None if it can't be known.

    Returns None outside a git repo, for uncommitted files, and in shallow clones, where
    the history is cut off and every file looks like it changed in the newest commit.
    """
    try:
        if _git(path, "rev-parse", "--is-shallow-repository") == "true":
            return None
        stamp = _git(path, "log", "-1", "--format=%cs", "--", path.name)
    except (OSError, subprocess.CalledProcessError):
        return None
    return date.fromisoformat(stamp) if stamp else None

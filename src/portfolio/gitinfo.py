"""Read facts about content from git history."""

from datetime import date
from pathlib import Path
import subprocess


def last_commit_date(directory: Path) -> date | None:
    """Date of the newest commit in the git repo containing directory, or None if there
    isn't one (outside a repo, or before the first commit).

    Shallow clones are fine: they always include the newest commit.
    """
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%cs"],
            cwd=directory,
            capture_output=True,
            text=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    stamp = result.stdout.strip()
    return date.fromisoformat(stamp) if stamp else None

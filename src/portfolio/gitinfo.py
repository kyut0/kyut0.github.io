"""Read facts about content from git history."""

from datetime import date
from pathlib import Path
import re
import subprocess


def _git(directory: Path, *args: str) -> str | None:
    """Output of a git command run in directory, or None if it fails (outside a repo,
    before the first commit, no such remote, git not installed)."""
    try:
        result = subprocess.run(
            ["git", *args], cwd=directory, capture_output=True, text=True, check=True
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip() or None


def last_commit_date(directory: Path) -> date | None:
    """Date of the newest commit in the git repo containing directory, or None if there
    isn't one (outside a repo, or before the first commit).

    Shallow clones are fine: they always include the newest commit.
    """
    stamp = _git(directory, "log", "-1", "--format=%cs")
    return date.fromisoformat(stamp) if stamp else None


def last_commit_hash(directory: Path) -> str | None:
    """Full hash of the commit the site is built from (HEAD), or None if there isn't one."""
    return _git(directory, "rev-parse", "--verify", "-q", "HEAD")


# git@github.com:owner/repo(.git) or https://github.com/owner/repo(.git)
_GITHUB_REMOTE = re.compile(
    r"^(?:git@github\.com:|(?:https|ssh)://(?:[^@/]+@)?github\.com/)"
    r"(?P<repo>[\w.-]+/[\w.-]+?)(?:\.git)?/?$"
)


def github_repo_url(directory: Path, remote: str = "origin") -> str | None:
    """Web URL of the repo's GitHub remote, e.g. https://github.com/kyut0/kyut0.github.io,
    or None if that remote doesn't exist or isn't on GitHub."""
    url = _git(directory, "remote", "get-url", remote)
    match = _GITHUB_REMOTE.match(url) if url else None
    return f"https://github.com/{match['repo']}" if match else None

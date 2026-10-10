"""Snapshot a Monkeytype profile into content/typing.yaml (`portfolio typing`).

Monkeytype's profile endpoint is public, so no API key is needed. Fetching is a separate
step from building on purpose: the build reads the committed snapshot and never depends on
Monkeytype being up.
"""

from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any
from urllib.parse import quote
from urllib.request import Request, urlopen

import yaml

from portfolio.models import Typing, TypingBest

API = "https://api.monkeytype.com/users/{username}/profile"
PROFILE = "https://monkeytype.com/profile/{username}"


def fetch_profile(username: str, timeout: float = 10) -> dict[str, Any]:
    """Return the `data` object of a user's public Monkeytype profile."""
    request = Request(
        API.format(username=quote(username)),
        headers={"Accept": "application/json", "User-Agent": "kyut0.github.io portfolio"},
    )
    with urlopen(request, timeout=timeout) as response:
        payload: dict[str, Any] = json.load(response)
    return dict(payload["data"])


def typing_from_profile(data: dict[str, Any]) -> Typing:
    """Keep each test's personal bests (plain settings only: no punctuation, numbers, or
    lazy mode, since that's what the /type page's test is)."""
    bests = []
    for mode, by_length in data.get("personalBests", {}).items():
        for length, runs in by_length.items():
            for run in runs:
                if run.get("punctuation") or run.get("numbers") or run.get("lazyMode"):
                    continue
                bests.append(
                    TypingBest(
                        mode=mode,
                        length=int(length),
                        language=run["language"],
                        wpm=run["wpm"],
                        accuracy=run["acc"],
                        set_on=datetime.fromtimestamp(run["timestamp"] / 1000, UTC).date(),
                    )
                )
    bests.sort(key=lambda b: (b.mode, b.length, b.language))
    return Typing(
        username=data["name"], profile=PROFILE.format(username=data["name"]), bests=bests
    )


def write_typing(typing: Typing, path: Path) -> None:
    header = "# Monkeytype snapshot for the hidden /type page. Refresh with `portfolio typing`.\n"
    body = yaml.safe_dump(typing.model_dump(mode="json"), sort_keys=False)
    path.write_text(header + body, encoding="utf-8")

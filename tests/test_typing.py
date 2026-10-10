from datetime import date
from pathlib import Path

import pytest

from portfolio.load import load_site, load_typing
from portfolio.monkeytype import typing_from_profile, write_typing
from portfolio.render import build_site


def _run(wpm: float, **settings: bool) -> dict[str, object]:
    return {
        "acc": 99.5,
        "language": "english",
        "wpm": wpm,
        "timestamp": 1664841600000,  # 2022-10-04 UTC
        "punctuation": False,
        "numbers": False,
        "lazyMode": False,
        **settings,
    }


PROFILE = {
    "name": "yutbutt",
    "personalBests": {
        "time": {"15": [_run(128.8), _run(140.0, punctuation=True)], "60": [_run(108.4)]},
        "words": {"10": [_run(144.7)]},
    },
}


def test_typing_from_profile_keeps_plain_bests() -> None:
    typing = typing_from_profile(PROFILE)
    assert str(typing.profile) == "https://monkeytype.com/profile/yutbutt"
    assert len(typing.bests) == 3  # the punctuation run is dropped
    best = typing.best("time", 15)
    assert best is not None
    assert best.wpm == 128.8
    assert best.set_on == date(2022, 10, 4)
    assert typing.best("time", 30) is None


def test_typing_snapshot_round_trips(tmp_path: Path) -> None:
    typing = typing_from_profile(PROFILE)
    path = tmp_path / "typing.yaml"
    write_typing(typing, path)
    assert load_typing(path) == typing
    assert load_typing(tmp_path / "missing.yaml") is None


def test_typing_profile_without_plain_bests_is_rejected() -> None:
    with pytest.raises(ValueError):
        typing_from_profile({"name": "x", "personalBests": {}})


def test_type_page_is_built_but_hidden(content_dir: Path, site_dir: Path, tmp_path: Path) -> None:
    site = load_site(content_dir)
    build_site(site, tmp_path, site_dir / "templates", site_dir / "static")

    page = (tmp_path / "type.html").read_text()
    assert 'src="static/type.js?v=' in page
    if site.typing and (best := site.typing.best("time", 15)):
        assert f'data-best="{best.wpm}"' in page
    index = (tmp_path / "index.html").read_text()
    assert 'src="static/console.js?v=' in index
    assert "type.html" not in index  # only the console points to it

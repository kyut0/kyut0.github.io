"""Command-line entry point: `portfolio validate | build | serve | themes | typing`."""

import argparse
import contextlib
from functools import partial
import http.server
from pathlib import Path
import sys
from urllib.error import URLError

from pydantic import ValidationError
import seedpalette
import yaml

from portfolio.load import ContentError, load_site
from portfolio.monkeytype import fetch_profile, typing_from_profile, write_typing
from portfolio.render import build_pdfs, build_site
from portfolio.render.pdf import THEMED_DIR, PdfOverflowError
from portfolio.render.site import build_theme_preview
from portfolio.themes import SiteThemes, load_themes


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="portfolio", description=__doc__)
    parser.add_argument("--content", type=Path, default=Path("content"))
    parser.add_argument("--site-dir", type=Path, default=Path("site"))
    parser.add_argument("--out", type=Path, default=Path("_site"))
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("validate", help="validate content without writing anything")
    sub.add_parser("build", help="validate content and render the site and PDFs")
    serve = sub.add_parser("serve", help="build, then serve the site locally")
    serve.add_argument("--port", type=int, default=8000)
    themes = sub.add_parser(
        "themes", help="check every color theme and write a preview page of them all"
    )
    themes.add_argument("--preview", type=Path, default=Path("_site/themes-preview.html"))
    typing = sub.add_parser(
        "typing", help="refresh content/typing.yaml from a public Monkeytype profile"
    )
    typing.add_argument("--user", default="yutbutt", help="Monkeytype username")
    return parser


def _refresh_typing(username: str, content_dir: Path) -> int:
    try:
        typing = typing_from_profile(fetch_profile(username))
    except (URLError, KeyError, ValueError) as exc:
        print(f"monkeytype error: {exc}", file=sys.stderr)
        return 1
    path = content_dir / "typing.yaml"
    write_typing(typing, path)
    print(f"wrote {path} ({len(typing.bests)} personal best(s) for {typing.username})")
    return 0


def _load_themes(site_dir: Path) -> SiteThemes | None:
    """Load site/themes.yaml (plus the treasure themes) with seedpalette, printing why it
    failed if it did."""
    try:
        site_themes = load_themes(site_dir)
    except (OSError, yaml.YAMLError, ValueError) as exc:  # ValidationError is a ValueError
        print(f"theme error:\n{exc}", file=sys.stderr)
        return None
    themes = site_themes.themes
    failing = [t.name for t in themes.themes if not t.ok]
    if failing:
        print(seedpalette.report(themes), file=sys.stderr)
        print(f"theme error: {', '.join(failing)} fail contrast", file=sys.stderr)
        return None
    return site_themes


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "typing":
        return _refresh_typing(args.user, args.content)

    site_themes = _load_themes(args.site_dir)
    if site_themes is None:
        return 1
    themes = site_themes.themes
    if args.command == "themes":
        print(seedpalette.report(themes))
        preview = build_theme_preview(themes, args.preview)
        print(f"wrote {preview}")
        return 0

    try:
        site = load_site(args.content)
    except (ContentError, ValidationError) as exc:
        print(f"content error:\n{exc}", file=sys.stderr)
        return 1

    if args.command == "validate":
        print(f"ok: resume + {len(site.projects)} project(s) are valid")
        return 0

    pages = build_site(
        site, args.out, args.site_dir / "templates", args.site_dir / "static", site_themes
    )
    try:
        pdfs = build_pdfs(site, args.site_dir / "typst", args.out, themes)
    except PdfOverflowError as exc:
        print(f"pdf error: {exc}", file=sys.stderr)
        return 1
    print(f"built {len(pages)} page(s) into {args.out}/")
    default = pdfs[0]
    for pdf in (default.resume, default.cover_letter):
        scaled = "" if pdf.scale == 1.0 else f", scaled to {pdf.scale:.0%} to fit"
        print(f"built {pdf.path} ({pdf.pages} page{scaled})")
    print(f"built {default.both} (cover letter + resume)")
    if len(pdfs) > 1:
        others = ", ".join(p.theme for p in pdfs[1:])
        print(f"built the same PDFs in {args.out}/{THEMED_DIR}/ for: {others}")

    if args.command == "serve":
        handler = partial(http.server.SimpleHTTPRequestHandler, directory=str(args.out))
        with http.server.ThreadingHTTPServer(("127.0.0.1", args.port), handler) as server:
            print(f"serving at http://127.0.0.1:{args.port} (Ctrl+C to stop)")
            with contextlib.suppress(KeyboardInterrupt):
                server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

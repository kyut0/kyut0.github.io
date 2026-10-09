"""Command-line entry point: `portfolio validate | build | serve`."""

import argparse
import contextlib
from functools import partial
import http.server
from pathlib import Path
import sys

from pydantic import ValidationError

from portfolio.load import ContentError, load_site
from portfolio.render import build_resume_pdf, build_site


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="portfolio", description=__doc__)
    parser.add_argument("--content", type=Path, default=Path("content"))
    parser.add_argument("--site-dir", type=Path, default=Path("site"))
    parser.add_argument("--out", type=Path, default=Path("_site"))
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("validate", help="validate content without writing anything")
    sub.add_parser("build", help="validate content and render the site and PDF resume")
    serve = sub.add_parser("serve", help="build, then serve the site locally")
    serve.add_argument("--port", type=int, default=8000)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)

    try:
        site = load_site(args.content)
    except (ContentError, ValidationError) as exc:
        print(f"content error:\n{exc}", file=sys.stderr)
        return 1

    if args.command == "validate":
        print(f"ok: resume + {len(site.projects)} project(s) are valid")
        return 0

    pages = build_site(site, args.out, args.site_dir / "templates", args.site_dir / "static")
    template = args.site_dir / "typst" / "resume.typ"
    pdf = build_resume_pdf(site.resume, template, args.out / "resume.pdf")
    print(f"built {len(pages)} page(s) and {pdf.name} into {args.out}/")

    if args.command == "serve":
        handler = partial(http.server.SimpleHTTPRequestHandler, directory=str(args.out))
        with http.server.ThreadingHTTPServer(("127.0.0.1", args.port), handler) as server:
            print(f"serving at http://127.0.0.1:{args.port} (Ctrl+C to stop)")
            with contextlib.suppress(KeyboardInterrupt):
                server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

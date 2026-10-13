"""单用途 verified artifact 归档 CLI。"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence

from engine import __version__
from engine.archive import PUBLIC_EXCEPTIONS, archive_verified_artifact


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        self.print_usage(sys.stderr)
        self.exit(2, f"{self.prog}: error: {message}\n")


def _parser() -> argparse.ArgumentParser:
    parser = _Parser(
        prog="python -m tools.archive_verified_artifact",
        add_help=False,
    )
    parser.add_argument("SOURCE", nargs="?")
    parser.add_argument("--archive-root", dest="archive_root", action="append")
    parser.add_argument("--help", action="store_true")
    parser.add_argument("--version", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    parser = _parser()
    if args not in (["--help"], ["--version"]):
        if len(args) != 3 or args[1] != "--archive-root":
            parser.error("expected SOURCE --archive-root ARCHIVE_ROOT")
    namespace, extras = parser.parse_known_args(args)
    if extras:
        parser.error("unrecognized arguments: " + " ".join(extras))
    if namespace.help or namespace.version:
        if len(args) != 1:
            parser.error("--help and --version are exclusive forms")
        if namespace.help:
            parser.print_help(sys.stdout)
        else:
            print(__version__)
        return 0
    if namespace.SOURCE is None:
        parser.error("SOURCE is required")
    if namespace.archive_root is None:
        parser.error("--archive-root is required")
    if len(namespace.archive_root) != 1:
        parser.error("--archive-root must appear exactly once")
    try:
        result = archive_verified_artifact(namespace.SOURCE, namespace.archive_root[0])
    except PUBLIC_EXCEPTIONS as exc:
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print(
        json.dumps(
            {
                "status": result.status,
                "target": str(result.target),
                "artifact_id": result.artifact_id,
                "payload_digest": result.payload_digest,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

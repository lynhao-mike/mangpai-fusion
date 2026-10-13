from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from collections.abc import Mapping
from pathlib import Path

import engine.evaluation.prospective_asof as _prospective_asof
from engine.evaluation.prospective_asof import (
    _AsOfError,
    _is_link,
    _workspace_path,
    build_asof_feedback_release,
    build_asof_frozen_artifact,
    collect_asof_verification,
)


_ERRORS = frozenset((
    "ASOF_SCHEMA_ERROR",
    "ASOF_IDENTITY_ERROR",
    "ASOF_PATH_ERROR",
    "ASOF_PARENT_ERROR",
    "ASOF_HASH_ERROR",
    "ASOF_TIME_ERROR",
    "ASOF_STATE_ERROR",
    "ASOF_LINK_ERROR",
    "ASOF_CONFLICT_ERROR",
    "ASOF_CUSTODY_ERROR",
    "ASOF_DOMAIN_ERROR",
    "ASOF_IO_ERROR",
))


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise _AsOfError("ASOF_SCHEMA_ERROR")


def _trusted_path(path: Path) -> Path:
    return _workspace_path(path)


def _check_no_links(path: Path) -> None:
    _trusted_path(path)


def _read_mapping(path: Path, category: str) -> dict[str, object]:
    candidate = _trusted_path(path)
    _check_no_links(candidate)
    if not candidate.is_file():
        raise _AsOfError(category)
    try:
        raw = candidate.read_bytes()
        value = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        raise _AsOfError(category) from None
    if type(value) is not dict:
        raise _AsOfError("ASOF_SCHEMA_ERROR")
    return value


def _sealed_input(path: Path) -> dict[str, object]:
    candidate = _trusted_path(path)
    value = _read_mapping(candidate, "ASOF_IO_ERROR")
    stored = value.get("artifact_path")
    if type(stored) is not str:
        raise _AsOfError("ASOF_SCHEMA_ERROR")
    if stored != candidate.relative_to(_prospective_asof._TRUSTED_WORKSPACE_ROOT).as_posix():
        raise _AsOfError("ASOF_PATH_ERROR")
    return value


def _check_output_target(path: Path) -> None:
    target = _trusted_path(path)
    _check_no_links(target)
    if _is_link(target):
        raise _AsOfError("ASOF_LINK_ERROR")
    if target.exists():
        raise _AsOfError("ASOF_CONFLICT_ERROR")
    if not target.parent.is_dir():
        raise _AsOfError("ASOF_PATH_ERROR")


def _canonical_output(path: Path, artifact: Mapping[str, object]) -> None:
    stored = artifact.get("artifact_path")
    if type(stored) is not str:
        raise _AsOfError("ASOF_SCHEMA_ERROR")
    relative = _trusted_path(path).relative_to(
        _prospective_asof._TRUSTED_WORKSPACE_ROOT
    ).as_posix()
    if relative != stored:
        raise _AsOfError("ASOF_PATH_ERROR")


def publish_new_json_artifact(path: Path, artifact: Mapping[str, object]) -> None:
    target = _trusted_path(path)
    _check_output_target(target)
    try:
        document = (json.dumps(artifact, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")
    except (TypeError, ValueError):
        raise _AsOfError("ASOF_SCHEMA_ERROR") from None
    descriptor = -1
    temporary: Path | None = None
    try:
        descriptor, name = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".part", dir=target.parent)
        temporary = Path(name)
        with os.fdopen(descriptor, "wb") as stream:
            descriptor = -1
            stream.write(document)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary, target)
        except FileExistsError:
            raise _AsOfError("ASOF_CONFLICT_ERROR") from None
    except _AsOfError:
        raise
    except OSError:
        raise _AsOfError("ASOF_IO_ERROR") from None
    finally:
        if descriptor >= 0:
            try:
                os.close(descriptor)
            except OSError:
                pass
        if temporary is not None:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass


def _parser() -> argparse.ArgumentParser:
    parser = _Parser(add_help=False)
    commands = parser.add_subparsers(dest="command", required=True, parser_class=_Parser)

    freeze = commands.add_parser("freeze", add_help=False)
    freeze.add_argument("--bundle-root", required=True)
    freeze.add_argument("--out", required=True)

    release = commands.add_parser("release", add_help=False)
    release.add_argument("--frozen", required=True)
    release.add_argument("--created-at", required=True)
    release.add_argument("--out", required=True)

    verify = commands.add_parser("verify", add_help=False)
    verify.add_argument("--release", required=True)
    verify.add_argument("--custody", required=True)
    verify.add_argument("--collected-at", required=True)
    verify.add_argument("--out", required=True)
    return parser


def main() -> int:
    try:
        arguments = _parser().parse_args()
        output = _trusted_path(Path(arguments.out))
        input_paths = [_trusted_path(Path(arguments.bundle_root))] if arguments.command == "freeze" else (
            [_trusted_path(Path(arguments.frozen))] if arguments.command == "release" else
            [_trusted_path(Path(arguments.release)), _trusted_path(Path(arguments.custody))]
        )
        for input_path in input_paths:
            _check_no_links(input_path)
        _check_output_target(output)
        if arguments.command == "freeze":
            artifact = build_asof_frozen_artifact(bundle_root=input_paths[0])
        elif arguments.command == "release":
            frozen = _sealed_input(input_paths[0])
            artifact = build_asof_feedback_release(frozen_artifact=frozen, created_at=arguments.created_at)
        else:
            release = _sealed_input(input_paths[0])
            custody_path = input_paths[1]
            artifact = collect_asof_verification(
                release=release,
                custody_reader=lambda: _read_mapping(custody_path, "ASOF_CUSTODY_ERROR"),
                collected_at=arguments.collected_at,
            )
        _canonical_output(output, artifact)
        publish_new_json_artifact(output, artifact)
        return 0
    except _AsOfError as error:
        category = error.category if error.category in _ERRORS else "ASOF_DOMAIN_ERROR"
    except Exception:
        category = "ASOF_DOMAIN_ERROR"
    sys.stderr.write(category + "\n")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

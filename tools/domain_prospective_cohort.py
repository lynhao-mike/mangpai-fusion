"""三领域 prospective 盲测 intake / freeze / reveal / score / status CLI。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

from engine.evaluation.domain_prospective import (
    DomainFreeze,
    DomainProspectiveIntake,
    DomainScore,
    RevealedDomainLabels,
    build_intake,
    freeze_snapshot,
    reveal_labels,
    score_revealed,
    summarize_status,
)
from engine.evaluation.prospective_artifacts import canonical_artifact_sha256, publish_new_json
from engine.v5.domain import V5RunSnapshot


def _read_json(path: Path) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"input must be a regular file: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid UTF-8 JSON input: {path}") from exc
    if not isinstance(value, dict):
        raise ValueError("input JSON must be an object")
    stored_digest = value.get("artifact_sha256")
    if stored_digest is not None:
        if not isinstance(stored_digest, str) or canonical_artifact_sha256(value) != stored_digest:
            raise ValueError(f"artifact_sha256 mismatch: {path}")
        value = {key: item for key, item in value.items() if key != "artifact_sha256"}
    return value


def _publish(path: Path, payload: Mapping[str, Any]) -> None:
    publish_new_json(path, payload, dry_run=False)


def _print(payload: Mapping[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))


def _intake(args: argparse.Namespace) -> dict[str, Any]:
    payload = _read_json(args.input)
    discovered = [path for path in args.out.parent.glob("*.json") if path != args.out]
    candidate_paths = list(dict.fromkeys([*args.existing, *discovered]))
    existing: list[DomainProspectiveIntake] = []
    for path in candidate_paths:
        try:
            raw_document = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(raw_document, dict) or "artifact_sha256" not in raw_document:
                continue
            document = _read_json(path)
            if document.get("schema_version") == "domain-prospective-intake/v1":
                existing.append(DomainProspectiveIntake.from_dict(document))
        except ValueError:
            if path in args.existing:
                raise
    result = build_intake(payload, existing=existing)
    _publish(args.out, result.to_dict())
    return result.to_dict()


def _freeze(args: argparse.Namespace) -> dict[str, Any]:
    intake = DomainProspectiveIntake.from_dict(_read_json(args.intake))
    snapshot = V5RunSnapshot.from_dict(_read_json(args.snapshot))
    result = freeze_snapshot(intake, snapshot)
    _publish(args.out, result.to_dict())
    return result.to_dict()


def _reveal(args: argparse.Namespace) -> dict[str, Any]:
    frozen = DomainFreeze.from_dict(_read_json(args.freeze))
    result = reveal_labels(frozen, _read_json(args.labels))
    _publish(args.out, result.to_dict())
    return result.to_dict()


def _score(args: argparse.Namespace) -> dict[str, Any]:
    frozen = DomainFreeze.from_dict(_read_json(args.freeze))
    revealed = RevealedDomainLabels.from_dict(_read_json(args.reveal))
    result = score_revealed(frozen, revealed)
    _publish(args.out, result.to_dict())
    return result.to_dict()


def _status(args: argparse.Namespace) -> dict[str, Any]:
    scores = [DomainScore.from_dict(_read_json(path)) for path in args.score]
    result = summarize_status(scores)
    if args.out is not None:
        _publish(args.out, result)
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Three-domain prospective blind evaluation artifacts")
    subparsers = parser.add_subparsers(dest="command", required=True)

    intake = subparsers.add_parser("intake")
    intake.add_argument("--input", type=Path, required=True)
    intake.add_argument("--existing", type=Path, nargs="*", default=[])
    intake.add_argument("--out", type=Path, required=True)
    intake.set_defaults(handler=_intake)

    freeze = subparsers.add_parser("freeze")
    freeze.add_argument("--intake", type=Path, required=True)
    freeze.add_argument("--snapshot", type=Path, required=True)
    freeze.add_argument("--out", type=Path, required=True)
    freeze.set_defaults(handler=_freeze)

    reveal = subparsers.add_parser("reveal")
    reveal.add_argument("--freeze", type=Path, required=True)
    reveal.add_argument("--labels", type=Path, required=True)
    reveal.add_argument("--out", type=Path, required=True)
    reveal.set_defaults(handler=_reveal)

    score = subparsers.add_parser("score")
    score.add_argument("--freeze", type=Path, required=True)
    score.add_argument("--reveal", type=Path, required=True)
    score.add_argument("--out", type=Path, required=True)
    score.set_defaults(handler=_score)

    status = subparsers.add_parser("status")
    status.add_argument("--score", type=Path, nargs="*", default=[])
    status.add_argument("--out", type=Path)
    status.set_defaults(handler=_status)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    try:
        args = build_parser().parse_args(argv)
        result = args.handler(args)
        _print(result)
        return 1 if args.command == "status" and result["status"] == "not_ready" else 0
    except (OSError, KeyError, TypeError, ValueError) as exc:
        print(f"domain prospective error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

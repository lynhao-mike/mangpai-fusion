"""L9 条件化学习的离线治理 CLI adapter。"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Sequence

from engine.learning import (
    ConditionalLearningRepository,
    ConditionalLearningSignal,
    load_learning_thresholds,
    process_learning_signals,
)


def _read_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read valid JSON from {path}: {exc}") from exc


def _load_signals(path: Path) -> tuple[ConditionalLearningSignal, ...]:
    payload = _read_json(path)
    rows = payload.get("signals") if isinstance(payload, dict) else payload
    if not isinstance(rows, list):
        raise ValueError("signals file must be a JSON array or an object with a signals array")
    try:
        return tuple(ConditionalLearningSignal.from_dict(row) for row in rows)
    except (TypeError, ValueError, KeyError) as exc:
        raise ValueError(f"invalid learning signal: {exc}") from exc


def _load_approvals(path: Path) -> set[str]:
    payload = _read_json(path)
    rows = payload.get("approved_decision_ids") if isinstance(payload, dict) else payload
    if not isinstance(rows, list) or any(not isinstance(item, str) or not item for item in rows):
        raise ValueError("approval file must contain an approved_decision_ids string array")
    return set(rows)


def _copy_repository(source: Path, destination: Path) -> None:
    if source.exists():
        if not source.is_dir():
            raise ValueError(f"repository root is not a directory: {source}")
        shutil.copytree(source, destination)


def _process(args: argparse.Namespace, repository_root: Path, approvals: set[str]):
    repository = ConditionalLearningRepository(repository_root)
    return process_learning_signals(
        _load_signals(args.signals_file),
        repository=repository,
        thresholds=load_learning_thresholds(args.config),
        task_catalog_path=args.task_catalog,
        approval_decision_ids=approvals,
        created_at=args.created_at,
    )


def _preview(args: argparse.Namespace, approvals: set[str]):
    with tempfile.TemporaryDirectory(prefix="conditional-learning-") as temporary:
        staged_root = Path(temporary) / "repository"
        _copy_repository(args.repository_root, staged_root)
        return _process(args, staged_root, approvals)


def _emit(payload: object) -> None:
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))


def _decide(args: argparse.Namespace) -> int:
    decisions = _preview(args, set()) if args.dry_run else _process(args, args.repository_root, set())
    _emit({"dry_run": args.dry_run, "decisions": [item.to_dict() for item in decisions]})
    return 0


def _apply(args: argparse.Namespace) -> int:
    approvals = _load_approvals(args.approval_file)
    preview = _preview(args, approvals)
    missing = [
        decision.decision_id
        for decision in preview
        if decision.requires_human_approval and decision.decision_id not in approvals
    ]
    if missing:
        raise PermissionError(
            "explicit approval required for governed decisions: " + ", ".join(missing)
        )
    decisions = preview if args.dry_run else _process(args, args.repository_root, approvals)
    _emit({"dry_run": args.dry_run, "decisions": [item.to_dict() for item in decisions]})
    return 0


def _rollback(args: argparse.Namespace) -> int:
    if args.dry_run:
        with tempfile.TemporaryDirectory(prefix="conditional-learning-") as temporary:
            staged_root = Path(temporary) / "repository"
            _copy_repository(args.repository_root, staged_root)
            active = ConditionalLearningRepository(staged_root).rollback(args.snapshot_ref)
    else:
        active = ConditionalLearningRepository(args.repository_root).rollback(args.snapshot_ref)
    _emit({"dry_run": args.dry_run, "active_snapshot_ref": active})
    return 0


def _add_process_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--repository-root", type=Path, required=True)
    parser.add_argument("--signals-file", type=Path, required=True)
    parser.add_argument("--config", type=Path, default=Path("engine/conditional-learning.yaml"))
    parser.add_argument(
        "--task-catalog",
        type=Path,
        default=Path("mapping/school-capability-task-catalog-v1.yaml"),
    )
    parser.add_argument("--created-at", required=True)
    parser.add_argument("--dry-run", action="store_true")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Offline conditional learning governance")
    commands = parser.add_subparsers(dest="command", required=True)

    decide = commands.add_parser("decide", help="govern signals and emit decisions")
    _add_process_arguments(decide)
    decide.set_defaults(handler=_decide)

    apply = commands.add_parser("apply", help="apply governed decisions")
    _add_process_arguments(apply)
    apply.add_argument("--approval-file", type=Path, required=True)
    apply.set_defaults(handler=_apply)

    rollback = commands.add_parser("rollback", help="restore a snapshot's parent")
    rollback.add_argument("--repository-root", type=Path, required=True)
    rollback.add_argument("--snapshot-ref", required=True)
    rollback.add_argument("--dry-run", action="store_true")
    rollback.set_defaults(handler=_rollback)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.handler(args))
    except (FileNotFoundError, OSError, PermissionError, TypeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

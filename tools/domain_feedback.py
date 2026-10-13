"""六源三领域命题级结构化反馈与只读校准候选 CLI。

提供 ``prepare / ingest / status / candidates``。仅 ``prepare`` 与 ``ingest``
创建独立反馈制品，且均为 create-only；其余命令只读。任何命令都不修改理论、
静态权重、生产路由、规则或历史 run snapshot，也不自动 promotion。
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Sequence

from engine.v5.domain import V5RunSnapshot
from engine.v5.domain_feedback import (
    DomainClaimFeedback,
    aggregate_calibration_candidates,
    build_feedback_draft,
    validate_feedback,
    validate_snapshot,
)


def _reject_symlink_chain(path: Path, *, allow_missing_leaf: bool = False) -> None:
    candidate = path.absolute()
    if candidate.exists() or candidate.is_symlink():
        if candidate.is_symlink():
            raise ValueError(f"symlink is forbidden: {path}")
    elif not allow_missing_leaf:
        raise ValueError(f"path not found: {path}")
    current = candidate.parent if allow_missing_leaf and not candidate.exists() else candidate.parent
    while True:
        if current.is_symlink():
            raise ValueError(f"symlink path component is forbidden: {current}")
        parent = current.parent
        if parent == current:
            break
        current = parent


def _read_json(path: Path) -> object:
    _reject_symlink_chain(path)
    if not path.is_file():
        raise ValueError(f"regular file required: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid JSON file {path}: {exc}") from exc


def _load_snapshot(path: Path) -> V5RunSnapshot:
    payload = _read_json(path)
    if not isinstance(payload, dict):
        raise ValueError(f"run snapshot must be a JSON object: {path}")
    try:
        snapshot = V5RunSnapshot.from_dict(payload)
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"invalid run snapshot {path}: {exc}") from exc
    validate_snapshot(snapshot)
    return snapshot


def _load_feedback(path: Path) -> DomainClaimFeedback:
    payload = _read_json(path)
    if not isinstance(payload, dict):
        raise ValueError(f"feedback artifact must be a JSON object: {path}")
    return DomainClaimFeedback.from_dict(payload)


def _store_files(store: Path) -> list[Path]:
    _reject_symlink_chain(store)
    if not store.is_dir():
        raise ValueError(f"feedback store must be a directory: {store}")
    files = sorted(store.glob("*.domain-feedback.json"))
    for path in files:
        _reject_symlink_chain(path)
        if not path.is_file():
            raise ValueError(f"regular feedback artifact required: {path}")
    return files


def _load_store(store: Path) -> list[DomainClaimFeedback]:
    return [_load_feedback(path) for path in _store_files(store)]


def _create_json(path: Path, payload: object) -> None:
    _reject_symlink_chain(path, allow_missing_leaf=True)
    if path.exists() or path.is_symlink():
        raise FileExistsError(f"create-only target already exists: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def _prepare(args: argparse.Namespace) -> int:
    snapshot = _load_snapshot(args.snapshot)
    draft = build_feedback_draft(snapshot, args.claim_id)
    _create_json(args.out, draft.to_dict())
    print(json.dumps({"artifact_path": args.out.as_posix(), "feedback_id": draft.feedback_id}, ensure_ascii=False))
    return 0


def _ingest(args: argparse.Namespace) -> int:
    snapshot = _load_snapshot(args.snapshot)
    feedback = _load_feedback(args.feedback)
    if args.store.exists() or args.store.is_symlink():
        existing = _load_store(args.store)
    else:
        _reject_symlink_chain(args.store, allow_missing_leaf=True)
        existing = []
    validate_feedback(feedback, snapshot, existing_feedback=existing)
    target = args.store / f"{feedback.feedback_id}.domain-feedback.json"
    _create_json(target, feedback.to_dict())
    print(
        json.dumps(
            {
                "artifact_path": target.as_posix(),
                "feedback_id": feedback.feedback_id,
                "read_only_calibration_only": True,
                "automatic_promotion": False,
            },
            ensure_ascii=False,
        )
    )
    return 0


def _validated_store(args: argparse.Namespace) -> tuple[list[DomainClaimFeedback], list[V5RunSnapshot]]:
    feedback_rows = _load_store(args.store)
    snapshots = [_load_snapshot(path) for path in args.snapshot]
    by_run = {snapshot.run_id: snapshot for snapshot in snapshots}
    seen: list[DomainClaimFeedback] = []
    for feedback in feedback_rows:
        snapshot = by_run.get(feedback.run_id)
        if snapshot is None:
            raise ValueError(f"run snapshot not found for feedback run_id: {feedback.run_id}")
        validate_feedback(feedback, snapshot, existing_feedback=seen)
        seen.append(feedback)
    return feedback_rows, snapshots


def _status(args: argparse.Namespace) -> int:
    feedback_rows, _ = _validated_store(args)
    counts = Counter(feedback.status for feedback in feedback_rows)
    print(
        json.dumps(
            {
                "schema_version": "domain-feedback-status-v1",
                "read_only": True,
                "valid_feedback_count": len(feedback_rows),
                "status_counts": dict(sorted(counts.items())),
                "automatic_promotion": False,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def _candidates(args: argparse.Namespace) -> int:
    feedback_rows, snapshots = _validated_store(args)
    payload = aggregate_calibration_candidates(feedback_rows, snapshots)
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def _add_read_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--store", type=Path, required=True)
    parser.add_argument("--snapshot", type=Path, action="append", required=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="命题级结构化反馈与只读 calibration candidates")
    commands = parser.add_subparsers(dest="command", required=True)

    prepare = commands.add_parser("prepare", help="为冻结 run 中一个 claim 创建反馈草稿")
    prepare.add_argument("--snapshot", type=Path, required=True)
    prepare.add_argument("--claim-id", required=True)
    prepare.add_argument("--out", type=Path, required=True)
    prepare.set_defaults(handler=_prepare)

    ingest = commands.add_parser("ingest", help="校验并 create-only 摄入一条反馈")
    ingest.add_argument("--snapshot", type=Path, required=True)
    ingest.add_argument("--feedback", type=Path, required=True)
    ingest.add_argument("--store", type=Path, required=True)
    ingest.set_defaults(handler=_ingest)

    status = commands.add_parser("status", help="只读校验并汇总反馈状态")
    _add_read_arguments(status)
    status.set_defaults(handler=_status)

    candidates = commands.add_parser("candidates", help="只读输出人工校准候选")
    _add_read_arguments(candidates)
    candidates.set_defaults(handler=_candidates)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(list(argv) if argv is not None else None)
    try:
        return int(args.handler(args))
    except (FileExistsError, FileNotFoundError, OSError, KeyError, TypeError, ValueError) as exc:
        print(f"domain feedback error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

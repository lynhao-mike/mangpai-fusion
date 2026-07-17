"""Prospective high-risk independent review and adjudication governance CLI."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Sequence

from engine.evaluation.high_risk_review import (
    HIGH_RISK_TASK_IDS,
    finalize_reviews,
    prepare_review_packets,
    review_from_packet,
    validate_adjudication,
    validate_review,
)


from engine.evaluation.prospective_artifacts import canonical_artifact_sha256


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read valid JSON from {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return value


def _reject_symlink_chain(path: Path, description: str) -> None:
    absolute = path.absolute()
    for candidate in (absolute, *absolute.parents):
        if candidate.is_symlink():
            raise ValueError(f"{description} must not be or traverse a symlink: {path}")


def _write_new_json(path: Path, payload: object, *, dry_run: bool) -> None:
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if dry_run:
        return
    _reject_symlink_chain(path.parent, "output parent")
    if path.exists() or path.is_symlink():
        raise ValueError(f"output target must not exist: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() or path.is_symlink():
        raise ValueError(f"output target must not exist: {path}")
    descriptor, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        if path.exists() or path.is_symlink():
            raise ValueError(f"output target must not exist: {path}")
        os.rename(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def _emit(payload: object) -> None:
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))


def _prepare(args: argparse.Namespace) -> int:
    blocked = {
        args.witness, args.intake_operator, args.runner_operator, args.outcome_custodian,
    }
    packets = prepare_review_packets(
        _read_json(args.observation), evidence_class=args.evidence_class,
        label_identity=args.label_identity, reviewer_a=args.reviewer_a,
        reviewer_b=args.reviewer_b, disallowed_reviewers=blocked,
    )
    if not args.dry_run:
        if args.out_dir.exists() or args.out_dir.is_symlink():
            raise ValueError(f"output directory must not exist: {args.out_dir}")
        _reject_symlink_chain(args.out_dir.parent, "output parent")
        temporary = Path(tempfile.mkdtemp(prefix=f".{args.out_dir.name}.", dir=args.out_dir.parent))
        try:
            (temporary / "reviewer-a-packet.json").write_text(
                json.dumps(packets["reviewer_a"], ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            (temporary / "reviewer-b-packet.json").write_text(
                json.dumps(packets["reviewer_b"], ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            if args.out_dir.exists() or args.out_dir.is_symlink():
                raise ValueError(f"output directory must not exist: {args.out_dir}")
            os.rename(temporary, args.out_dir)
        except BaseException:
            if temporary.exists():
                for child in temporary.iterdir():
                    child.unlink()
                temporary.rmdir()
            raise
    _emit({"dry_run": args.dry_run, "packets": packets})
    return 0


def _submit(args: argparse.Namespace) -> int:
    review = review_from_packet(_read_json(args.packet), _read_json(args.decision))
    _write_new_json(args.out, review, dry_run=args.dry_run)
    _emit({"dry_run": args.dry_run, "review": review})
    return 0


def _adjudicate(args: argparse.Namespace) -> int:
    review_a = validate_review(_read_json(args.review_a))
    review_b = validate_review(_read_json(args.review_b))
    if review_a["decision"] == review_b["decision"]:
        raise ValueError("adjudication is only allowed for conflicting reviews")
    decision = _read_json(args.decision)
    adjudication = {
        "schema_version": "school-capability-high-risk-adjudication/v2",
        "case_id": review_a["case_id"], "task_id": review_a["task_id"],
        "observation_sha256": review_a["observation_sha256"],
        "evidence_class": review_a["evidence_class"],
        "label_identity": review_a["label_identity"],
        "review_packet_sha256": [
            review_a["review_packet_sha256"], review_b["review_packet_sha256"],
        ],
        **decision,
    }
    clean = validate_adjudication(adjudication)
    blocked = {
        review_a["reviewer"], review_b["reviewer"], args.witness,
        args.intake_operator, args.runner_operator, args.outcome_custodian,
    }
    if clean["adjudicator"] in blocked:
        raise ValueError("adjudicator violates required role separation")
    _write_new_json(args.out, clean, dry_run=args.dry_run)
    _emit({"dry_run": args.dry_run, "adjudication": clean})
    return 0


def _raw_parent(path: Path) -> dict[str, str]:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"parent must be a regular non-symlink file: {path}")
    return {
        "artifact_path": path.as_posix(),
        "artifact_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def _finalize(args: argparse.Namespace) -> int:
    review_a = _read_json(args.review_a)
    review_b = _read_json(args.review_b)
    adjudication = _read_json(args.adjudication) if args.adjudication else None
    operational_roles = {
        value for value in (
            args.witness, args.intake_operator, args.runner_operator, args.outcome_custodian,
        ) if value
    }
    result = finalize_reviews(
        str(review_a.get("case_id", "")), str(review_a.get("task_id", "")),
        review_a, review_b, adjudication,
        evidence_class=args.evidence_class or review_a.get("evidence_class"),
        label_identity=args.label_identity or review_a.get("label_identity"),
        disallowed_adjudicators=operational_roles,
        disallowed_reviewers=operational_roles,
    )
    unsigned = {
        "schema_version": "school-capability-high-risk-finalization/v2",
        "created_at": max(
            review_a["signed_at"], review_b["signed_at"],
            adjudication["signed_at"] if adjudication else "",
        ),
        "artifact_path": args.out.as_posix(),
        "parents": [
            _raw_parent(path) for path in (
                args.review_a, args.review_b, *([args.adjudication] if args.adjudication else []),
            )
        ],
        "result": result,
    }
    payload = {**unsigned, "artifact_sha256": canonical_artifact_sha256(unsigned)}
    _write_new_json(args.out, payload, dry_run=args.dry_run)
    _emit({"dry_run": args.dry_run, "result": result})
    return 0


def _audit(args: argparse.Namespace) -> int:
    if not args.reviews_dir.is_dir():
        raise ValueError(f"reviews directory does not exist: {args.reviews_dir}")
    reviews: dict[tuple[str, str], list[dict[str, Any]]] = {}
    invalid = 0
    duplicate_reviewers = 0
    for path in sorted(args.reviews_dir.rglob("*.json")):
        try:
            document = _read_json(path)
            if document.get("schema_version") != "school-capability-high-risk-review/v1":
                continue
            review = validate_review(document)
            reviews.setdefault((review["case_id"], review["task_id"]), []).append(review)
        except ValueError:
            invalid += 1
    task_summary = {
        task_id: {"pairs": 0, "agreements": 0, "conflicts": 0, "a_grade_labels": 0, "unassessable": 0}
        for task_id in sorted(HIGH_RISK_TASK_IDS)
    }
    for (_, task_id), rows in reviews.items():
        if task_id not in task_summary:
            continue
        if len(rows) != 2:
            task_summary[task_id]["unassessable"] += 1
            continue
        if rows[0]["reviewer"] == rows[1]["reviewer"]:
            duplicate_reviewers += 1
            task_summary[task_id]["unassessable"] += 1
            continue
        task_summary[task_id]["pairs"] += 1
        key = "agreements" if rows[0]["decision"] == rows[1]["decision"] else "conflicts"
        task_summary[task_id][key] += 1

    if args.labels:
        labels = _read_json(args.labels).get("labels", [])
        if not isinstance(labels, list):
            raise ValueError("labels must contain a list")
        for label in labels:
            if (
                isinstance(label, dict)
                and label.get("task_id") in task_summary
                and label.get("confidence_grade") == "A"
            ):
                task_summary[label["task_id"]]["a_grade_labels"] += 1
    result = {
        "schema_version": "school-capability-high-risk-review-audit/v1",
        "tasks": task_summary,
        "invalid_reviews": invalid,
        "duplicate_reviewers": duplicate_reviewers,
        "unresolved_conflicts": sum(
            row["conflicts"] for row in task_summary.values()
        ),
    }
    _emit(result)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Govern independent high-risk observation reviews")
    commands = parser.add_subparsers(dest="command", required=True)

    prepare = commands.add_parser("prepare", help="create two isolated review packets")
    prepare.add_argument("--observation", type=Path, required=True)
    prepare.add_argument("--evidence-class", default="legacy_non_prospective")
    prepare.add_argument("--label-identity")
    prepare.add_argument("--reviewer-a", required=True)
    prepare.add_argument("--reviewer-b", required=True)
    prepare.add_argument("--witness", default="human-witness-unspecified")
    prepare.add_argument("--intake-operator", required=True)
    prepare.add_argument("--runner-operator", required=True)
    prepare.add_argument("--outcome-custodian", required=True)
    prepare.add_argument("--out-dir", type=Path, required=True)
    prepare.add_argument("--dry-run", action="store_true")
    prepare.set_defaults(handler=_prepare)

    submit = commands.add_parser("submit", help="bind a human decision to one packet")
    submit.add_argument("--packet", type=Path, required=True)
    submit.add_argument("--decision", type=Path, required=True)
    submit.add_argument("--out", type=Path, required=True)
    submit.add_argument("--dry-run", action="store_true")
    submit.set_defaults(handler=_submit)

    adjudicate = commands.add_parser("adjudicate", help="resolve two conflicting reviews")
    adjudicate.add_argument("--review-a", type=Path, required=True)
    adjudicate.add_argument("--review-b", type=Path, required=True)
    adjudicate.add_argument("--decision", type=Path, required=True)
    adjudicate.add_argument("--witness", default="human-witness-unspecified")
    adjudicate.add_argument("--intake-operator", default="human-intake-unspecified")
    adjudicate.add_argument("--runner-operator", default="human-runner-unspecified")
    adjudicate.add_argument("--outcome-custodian", default="human-custodian-unspecified")
    adjudicate.add_argument("--out", type=Path, required=True)
    adjudicate.add_argument("--dry-run", action="store_true")
    adjudicate.set_defaults(handler=_adjudicate)

    finalize = commands.add_parser("finalize", help="produce an A-grade ledger-bound label when allowed")
    finalize.add_argument("--review-a", type=Path, required=True)
    finalize.add_argument("--review-b", type=Path, required=True)
    finalize.add_argument("--adjudication", type=Path)
    finalize.add_argument("--evidence-class")
    finalize.add_argument("--label-identity")
    finalize.add_argument("--witness", required=True)
    finalize.add_argument("--intake-operator", required=True)
    finalize.add_argument("--runner-operator", required=True)
    finalize.add_argument("--outcome-custodian", required=True)
    finalize.add_argument("--out", type=Path, required=True)
    finalize.add_argument("--dry-run", action="store_true")
    finalize.set_defaults(handler=_finalize)

    audit = commands.add_parser("audit", help="summarize review coverage and conflicts")
    audit.add_argument("--reviews-dir", type=Path, required=True)
    audit.add_argument("--labels", type=Path)
    audit.set_defaults(handler=_audit)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return int(args.handler(args))
    except (FileNotFoundError, OSError, TypeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

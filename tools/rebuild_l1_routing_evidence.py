"""重建 L1 路由留出证据：重新冻结 runner 输出、揭示既有标签并评分。

只消费已隔离的命盘汇总和既有人工标签。不会读取反馈原文、不会写生产权重。
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from engine.evaluation.models import BlindTask
from engine.evaluation.task_catalog import load_task_catalog
from tools.school_capability_batch import (
    build_historical_blind_artifacts,
    build_historical_reviewed_manifest,
    score_historical_batch,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--tasks", type=Path, required=True)
    parser.add_argument("--labels", type=Path, required=True)
    parser.add_argument("--batch-out", type=Path, required=True)
    parser.add_argument("--scores-out", type=Path, required=True)
    parser.add_argument("--manifest-out", type=Path, required=True)
    parser.add_argument("--frozen-at", required=True)
    parser.add_argument("--reviewer", default="human-reviewer-01")
    args = parser.parse_args()

    tasks = load_task_catalog(args.tasks)
    labels_payload = json.loads(args.labels.read_text(encoding="utf-8"))
    labels = labels_payload.get("labels")
    if not isinstance(labels, list):
        raise ValueError("labels artifact requires labels array")

    artifact = build_historical_blind_artifacts(
        args.source,
        tasks,
        schools=("ziping", "ren"),
        task_catalog_version="school-capability-tasks/v1-l1-routing-refreeze",
        rule_snapshot_id="l2-engine-rules/v2-ren-binary-career",
        frozen_at=args.frozen_at,
    )
    case_ids = {row["case_id"] for row in artifact["cases"]}
    eligible_labels = [row for row in labels if row.get("case_id") in case_ids]
    scores = score_historical_batch(
        artifact,
        tasks,
        labels=eligible_labels,
        reviewer=args.reviewer,
        evaluated_at=args.frozen_at,
    )
    manifest = build_historical_reviewed_manifest(
        artifact,
        tasks,
        labels=eligible_labels,
        reviewer=args.reviewer,
        generated_at=args.frozen_at,
    )

    for path, payload in (
        (args.batch_out, artifact),
        (args.scores_out, scores),
        (args.manifest_out, manifest),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    by_case_task: dict[tuple[str, str], set[str]] = {}
    for row in scores["scores"]:
        if row.get("utility") is None:
            continue
        by_case_task.setdefault((row["case_id"], row["task_id"]), set()).add(row["school_id"])
    competitive = sum(len(schools) >= 2 for schools in by_case_task.values())
    print(json.dumps({
        "cases": len(artifact["cases"]),
        "outputs": len(artifact["frozen_run"]["outputs"]),
        "labels": len(eligible_labels),
        "competitive_case_tasks": competitive,
        "freeze_hash": artifact["frozen_run"]["freeze_hash"],
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""生成 L1 learned/static 无泄漏留出集竞争覆盖审计制品。

本工具只读取冻结历史 batch 与评分制品，不重新读取反馈、不改生产权重。
只有同一留出 case/task 至少两派均有 utility 时，才算可用于路由对照。
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from engine.decision.routing_holdout_artifacts import (
    audit_competitive_coverage,
    build_deterministic_case_split,
    rewrite_score_prototypes,
)


def build_audit_artifact(
    batch: dict[str, Any],
    scores: dict[str, Any],
    *,
    holdout_fraction: float,
    salt: str,
    minimum_competitive_cases: int,
) -> dict[str, Any]:
    if batch.get("schema_version") != "school-capability-historical-batch/v1":
        raise ValueError("invalid historical batch schema")
    if scores.get("schema_version") != "school-capability-historical-scores/v1":
        raise ValueError("invalid historical scores schema")
    if batch["frozen_run"]["freeze_hash"] != scores.get("freeze_hash"):
        raise ValueError("batch/scores freeze_hash mismatch")

    labelled_ids = {
        str(row["case_id"])
        for row in scores.get("scores", [])
        if row.get("utility") is not None
    }
    eligible_cases = [row for row in batch["cases"] if row["case_id"] in labelled_ids]
    split = build_deterministic_case_split(eligible_cases, holdout_fraction=holdout_fraction, salt=salt)
    rewritten = rewrite_score_prototypes(scores["scores"], batch["cases"])
    audit = audit_competitive_coverage(
        rewritten,
        holdout_case_ids=frozenset(split.holdout_case_ids),
        minimum_competitive_cases=minimum_competitive_cases,
    )
    prototype_by_case: dict[str, str] = {}
    for row in rewritten:
        if row["case_id"] in labelled_ids:
            prototype_by_case[row["case_id"]] = row["chart_prototype_id"]
    return {
        "schema_version": "l1-routing-holdout-audit/v1",
        "source_freeze_hash": scores["freeze_hash"],
        "split": {
            "salt": split.salt,
            "holdout_fraction": split.holdout_fraction,
            "training_case_ids": list(split.training_case_ids),
            "holdout_case_ids": list(split.holdout_case_ids),
        },
        "prototype_by_case": dict(sorted(prototype_by_case.items())),
        "competitive_coverage": {
            "status": audit.status,
            "holdout_case_count": audit.holdout_case_count,
            "scored_case_task_count": audit.scored_case_task_count,
            "competitive_case_task_count": audit.competitive_case_task_count,
            "competitive_identities": list(audit.competitive_identities),
            "reasons": list(audit.reasons),
        },
        "gate_status": "HOLD" if audit.status != "READY" else "READY_FOR_COMPARISON",
    }


def render_audit_report(artifact: dict[str, Any]) -> str:
    split = artifact["split"]
    coverage = artifact["competitive_coverage"]
    reasons = coverage["reasons"] or ["竞争覆盖达到最低要求，可进入 static/learned 同案对照。"]
    return "\n".join([
        "# L1 可学习路由留出集对照",
        "",
        f"**门禁结论：{artifact['gate_status']}**",
        "",
        "## 无泄漏切分",
        f"- 训练案例：{len(split['training_case_ids'])}",
        f"- 留出案例：{len(split['holdout_case_ids'])}",
        f"- 切分盐：`{split['salt']}`",
        "- 同性别、同四柱的别名案例按命主分组，不允许跨集合。",
        "",
        "## 竞争覆盖",
        f"- 留出集中已有评分的 case/task：{coverage['scored_case_task_count']}",
        f"- 同案同任务至少两派均可评分：{coverage['competitive_case_task_count']}",
        "- 只有后一类记录才允许比较 static 与 learned 路由，单派可评分记录不得冒充路由增益。",
        "",
        "## 判定依据",
        *(f"- {reason}" for reason in reasons),
        "",
        "## 结论",
        "当前若为 HOLD，阻塞点不是代码连线，而是冻结盲测输出的同任务多流派能力覆盖不足。"
        "必须扩充至少两派能对同一可量化任务独立产生命题/克制且可评分的前瞻留出案例，之后才能计算真实路由效用、校准误差和高风险假阳性。",
        "",
    ])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch", type=Path, required=True)
    parser.add_argument("--scores", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--holdout-fraction", type=float, default=0.25)
    parser.add_argument("--salt", default="l1-routing-holdout-v1")
    parser.add_argument("--minimum-competitive-cases", type=int, default=5)
    args = parser.parse_args()
    batch = json.loads(args.batch.read_text(encoding="utf-8"))
    scores = json.loads(args.scores.read_text(encoding="utf-8"))
    artifact = build_audit_artifact(
        batch, scores,
        holdout_fraction=args.holdout_fraction,
        salt=args.salt,
        minimum_competitive_cases=args.minimum_competitive_cases,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.report.write_text(render_audit_report(artifact), encoding="utf-8")
    print(json.dumps({"status": artifact["gate_status"], "out": str(args.out), "report": str(args.report)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

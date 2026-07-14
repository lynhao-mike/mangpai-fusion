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
    compare_static_learned_routes,
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
    comparison = compare_static_learned_routes(
        rewritten,
        training_case_ids=set(split.training_case_ids),
        holdout_case_ids=set(split.holdout_case_ids),
        static_school_by_task={"career.role_change": "ziping"},
        minimum_holdout_cases=minimum_competitive_cases,
    )
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
        "route_comparison": {
            "status": comparison.status,
            "record_count": len(comparison.records),
            "static_mean_utility": comparison.static_mean_utility,
            "learned_mean_utility": comparison.learned_mean_utility,
            "reasons": list(comparison.reasons),
        },
        "gate_status": comparison.status if audit.status == "READY" else "HOLD",
    }


def render_audit_report(artifact: dict[str, Any]) -> str:
    split = artifact["split"]
    coverage = artifact["competitive_coverage"]
    comparison = artifact["route_comparison"]
    reasons = [*coverage["reasons"], *comparison["reasons"]]
    reasons.extend([
        "本批是 historical blind candidate，不是前瞻 untouched 测试集。",
        "当前 career.role_change 标签均为 occurred 正例，无法检验负例判别力与假阳性。",
        "本次仅覆盖一个任务、两个流派；不得外推为全领域路由能力。",
        "早期探索曾检查多个 seed；当前批次只作方法修复证据，不能用于 GO。",
    ])
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
        "- claim 与有标签的 abstain 都是合法可评分决策；unsupported/no_data 不计竞争覆盖。",
        "",
        "## 路由效用对照",
        f"- 可比较记录：{comparison['record_count']}",
        f"- 静态基线平均效用：{comparison['static_mean_utility']:.4f}",
        f"- learned 平均效用：{comparison['learned_mean_utility']:.4f}",
        f"- 来源冻结哈希：`{artifact['source_freeze_hash']}`",
        "",
        "## 判定依据",
        *(f"- {reason}" for reason in reasons),
        "",
        "## 结论",
        "GO 仅在 learned 至少改变一个路由选择且留出效用不低于静态基线时成立；"
        "若两者选择完全相同则保持 HOLD，不把等价重放冒充学习增量。",
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

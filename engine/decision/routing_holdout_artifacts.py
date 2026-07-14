"""从冻结历史评估制品构建无泄漏 L1 留出审计数据。"""

from __future__ import annotations

import hashlib
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from engine.decision.chart_prototype import classify_prototype
from engine.decision.models import ChartFactLedger
from engine.features.chart_feature_vector import build_chart_feature_vector


@dataclass(frozen=True)
class DeterministicCaseSplit:
    training_case_ids: tuple[str, ...]
    holdout_case_ids: tuple[str, ...]
    salt: str
    holdout_fraction: float


@dataclass(frozen=True)
class CompetitiveCoverageAudit:
    status: str
    holdout_case_count: int
    scored_case_task_count: int
    competitive_case_task_count: int
    competitive_identities: tuple[str, ...]
    reasons: tuple[str, ...]


def _subject_key(case: Mapping[str, Any]) -> str:
    sex = str(case.get("sex_marker", ""))
    pillars = case.get("four_pillars", ())
    if not isinstance(pillars, (list, tuple)) or len(pillars) != 4:
        raise ValueError(f"case {case.get('case_id', '<unknown>')} requires four_pillars")
    return f"{sex}|{''.join(str(item) for item in pillars)}"


def build_deterministic_case_split(
    cases: Iterable[Mapping[str, Any]],
    *,
    holdout_fraction: float = 0.25,
    salt: str = "l1-routing-holdout-v1",
) -> DeterministicCaseSplit:
    """按性别+四柱分组切分，杜绝同命主别名跨训练/留出。"""
    if not 0.0 < holdout_fraction < 1.0:
        raise ValueError("holdout_fraction must be between 0 and 1")
    grouped: dict[str, list[str]] = defaultdict(list)
    for case in cases:
        case_id = str(case.get("case_id", ""))
        if not case_id:
            raise ValueError("case_id is required")
        grouped[_subject_key(case)].append(case_id)
    if len(grouped) < 2:
        raise ValueError("at least two unique subjects are required")

    ranked = sorted(
        grouped,
        key=lambda key: (hashlib.sha256(f"{salt}|{key}".encode("utf-8")).hexdigest(), key),
    )
    holdout_subject_count = max(1, min(len(ranked) - 1, round(len(ranked) * holdout_fraction)))
    holdout_subjects = set(ranked[:holdout_subject_count])
    holdout = sorted(case_id for subject in holdout_subjects for case_id in grouped[subject])
    training = sorted(case_id for subject in ranked if subject not in holdout_subjects for case_id in grouped[subject])
    return DeterministicCaseSplit(tuple(training), tuple(holdout), salt, holdout_fraction)


def _chart_from_case(case: Mapping[str, Any]) -> ChartFactLedger:
    pillars = tuple(str(item) for item in case["four_pillars"])
    dayun = [{"ganzhi": str(item)} for item in case.get("dayun_sequence", ())]
    return ChartFactLedger(
        sex_marker=str(case.get("sex_marker", "")),
        solar_datetime=str(case.get("solar_datetime", "")),
        four_pillars=dict(zip(("year", "month", "day", "hour"), pillars)),
        dayun_steps=dayun,
    )


def rewrite_score_prototypes(
    scores: Iterable[Mapping[str, Any]],
    cases: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """用冻结命盘事实重算 cfv-v1 原型，不改评分、标签或输出状态。"""
    case_map = {str(case["case_id"]): case for case in cases}
    assignments: dict[str, str] = {}
    rewritten: list[dict[str, Any]] = []
    for score in scores:
        case_id = str(score.get("case_id", ""))
        case = case_map.get(case_id)
        if case is None:
            raise ValueError(f"score references unknown case: {case_id}")
        if case_id not in assignments:
            vector = build_chart_feature_vector(_chart_from_case(case))
            assignments[case_id] = classify_prototype(vector).prototype_id
        rewritten.append({**dict(score), "chart_prototype_id": assignments[case_id]})
    return rewritten


def audit_competitive_coverage(
    scores: Iterable[Mapping[str, Any]],
    *,
    holdout_case_ids: set[str] | frozenset[str],
    minimum_competitive_cases: int = 5,
) -> CompetitiveCoverageAudit:
    """检查留出集是否有同 case/task 至少两派可评分，防止伪对照。"""
    if minimum_competitive_cases < 1:
        raise ValueError("minimum_competitive_cases must be positive")
    grouped: dict[tuple[str, str], set[str]] = defaultdict(set)
    scored_identities: set[tuple[str, str]] = set()
    for row in scores:
        case_id = str(row.get("case_id", ""))
        if case_id not in holdout_case_ids or row.get("utility") is None:
            continue
        task_id = str(row.get("task_id", ""))
        school_id = str(row.get("school_id", ""))
        scored_identities.add((case_id, task_id))
        grouped[(case_id, task_id)].add(school_id)
    competitive = tuple(
        f"{case_id}|{task_id}"
        for (case_id, task_id), schools in sorted(grouped.items())
        if len(schools) >= 2
    )
    reasons: list[str] = []
    if len(competitive) < minimum_competitive_cases:
        reasons.append(
            f"同案同任务多流派可评分竞争样本不足：{len(competitive)} < {minimum_competitive_cases}。"
        )
    return CompetitiveCoverageAudit(
        status="READY" if not reasons else "HOLD",
        holdout_case_count=len(holdout_case_ids),
        scored_case_task_count=len(scored_identities),
        competitive_case_task_count=len(competitive),
        competitive_identities=competitive,
        reasons=tuple(reasons),
    )

"""任派 L2 应期 runner：从岁运事实推导可证伪时间窗命题。"""

from __future__ import annotations

import hashlib
from typing import Any

from engine.claims import Claim, Evidence, TaskUnsupported, TimeWindow, stable_claim_id, validate_claim_evidence
from engine.decision.models import ChartFactLedger
from engine.evaluation.models import BlindTask
from engine.features import ChartFeatureVector
from engine.predicates.relations import zhi_chong, zhi_chuan, zhi_liuhe, zhi_xing

_SUPPORTED_TASKS = {
    "career.change_window": "职业变化",
    "marriage.event_window": "婚恋重大变化",
    "wealth.major_loss_window": "重大财务变化",
    "health.event_window": "显著健康变化",
}


def _ganzhi(step: dict[str, Any]) -> str:
    return str(step.get("ganzhi") or step.get("干支") or step.get("liunian") or "").strip()


def _year(step: dict[str, Any]) -> int | None:
    value = step.get("year", step.get("年份"))
    return value if type(value) is int else None


def _relation(left: str, right: str) -> str | None:
    if zhi_chong(left, right):
        return "冲"
    if zhi_xing(left, right) is not None:
        return "刑"
    if zhi_chuan(left, right):
        return "穿"
    # 午未六合无固定化神，谓词返回 None；这里显式保留关系事实。
    if zhi_liuhe(left, right) is not None or frozenset((left, right)) == frozenset(("午", "未")):
        return "合"
    if left == right:
        return "伏吟"
    return None


def _trigger(step: dict[str, Any], chart: ChartFactLedger) -> tuple[str, tuple[str, ...]] | None:
    ganzhi = _ganzhi(step)
    if len(ganzhi) < 2:
        return None
    branch = ganzhi[1]
    refs: list[str] = []
    descriptions: list[str] = []
    for palace in ("year", "month", "day", "hour"):
        pillar = str(chart.four_pillars.get(palace, ""))
        if len(pillar) < 2:
            continue
        relation = _relation(branch, pillar[1])
        if relation:
            refs.append(f"four_pillars.{palace}")
            descriptions.append(f"流年{branch}与{palace}支{pillar[1]}{relation}")
    dayun = str(step.get("dayun") or step.get("大运") or "")
    if len(dayun) >= 2:
        relation = _relation(branch, dayun[1])
        if relation:
            descriptions.append(f"流年{branch}与大运支{dayun[1]}{relation}")
    if not descriptions:
        return None
    return "；".join(descriptions), tuple(refs)


def generate_claims(
    chart: ChartFactLedger,
    features: ChartFeatureVector,
    task: BlindTask,
) -> list[Claim]:
    """按输入岁运列表生成最多一条最强年度触发命题；无触发即 abstain。"""
    if task.task_id not in _SUPPORTED_TASKS:
        raise TaskUnsupported(f"ren does not support task: {task.task_id}")
    if not chart.liunian_steps:
        return []

    candidates: list[tuple[int, int, dict[str, Any], str, tuple[str, ...]]] = []
    for index, step in enumerate(chart.liunian_steps):
        year = _year(step)
        trigger = _trigger(step, chart)
        if year is None or trigger is None:
            continue
        description, fact_refs = trigger
        strength = sum(description.count(token) for token in ("冲", "刑", "穿", "伏吟", "合"))
        candidates.append((-strength, year, step, description, fact_refs))
    if not candidates:
        return []

    _, year, step, description, referenced_pillars = min(candidates, key=lambda item: (item[0], item[1]))
    index = chart.liunian_steps.index(step)
    rule_id = "REN-SUIYUN-RELATION-V1"
    evidence_raw = f"{features.chart_id}|{task.task_id}|{year}|{description}"
    evidence = Evidence(
        evidence_id="evidence-" + hashlib.sha256(evidence_raw.encode("utf-8")).hexdigest()[:20],
        fact_refs=(f"liunian_steps.{index}", *referenced_pillars),
        feature_refs=("branch_conflict_intensity", "evidence_completeness"),
        rule_id=rule_id,
        text=f"{year} 年岁运触发：{description}。",
    )
    window = TimeWindow(start_year=year, end_year=year, label="annual")
    event_label = _SUPPORTED_TASKS[task.task_id]
    claim = Claim(
        claim_id=stable_claim_id("ren", task.task_id, features.chart_id, f"{rule_id}:{year}"),
        school_id="ren",
        task_id=task.task_id,
        claim_type="timing_claim",
        stance="support",
        statement=f"{year} 年出现{event_label}的岁运触发窗口：{description}。",
        evidence=(evidence,),
        falsifier=f"该时间窗内未发生{event_label}即证伪本命题。",
        time_window=window,
        confidence_basis="时间窗来自输入流年与原局/大运的可计算冲合刑穿或伏吟，不使用固定年份文案。",
        applicability_snapshot={
            "year": year,
            "liunian": _ganzhi(step),
            "branch_conflict_intensity": features.branch_conflict_intensity,
            "evidence_completeness": features.evidence_completeness,
        },
    )
    validate_claim_evidence(claim, chart, features)
    return [claim]

"""杨派 L2 婚姻事件 runner；从性别、配偶星、夫妻宫与结构冲突独立推导。"""

from __future__ import annotations

import hashlib

from engine.claims import Claim, Evidence, TaskUnsupported, TimeWindow, stable_claim_id, validate_claim_evidence
from engine.decision.models import ChartFactLedger
from engine.evaluation.models import BlindTask
from engine.features import ChartFeatureVector

_SUPPORTED_TASK = "marriage.divorce_or_remarriage"
_LIFETIME = TimeWindow(start_year=1900, end_year=2100, label="lifetime")
_HIGH_RISK_CONFIDENCE_CAP = 0.62
_MALE_MARKERS = {"乾", "男", "男命", "乾造", "M", "male"}
_FEMALE_MARKERS = {"坤", "女", "女命", "坤造", "F", "female"}


def _count(features: ChartFeatureVector, *names: str) -> int:
    return sum(int(features.ten_god_counts.get(name, 0)) for name in names)


def _sex(marker: str) -> str | None:
    normalized = marker.strip()
    if normalized in _MALE_MARKERS:
        return "male"
    if normalized in _FEMALE_MARKERS:
        return "female"
    return None


def _day_branch(chart: ChartFactLedger) -> str:
    day = str(chart.four_pillars.get("day", chart.four_pillars.get("日柱", ""))).strip()
    return day[1] if len(day) == 2 else ""


def _palace_disruption(features: ChartFeatureVector, day_branch: str) -> tuple[bool, bool, int]:
    chong_pairs = {frozenset(pair) for pair in features.chong_pairs if day_branch in pair}
    xing_hai_pairs = {frozenset(pair) for pair in features.xing_hai_pairs if day_branch in pair}
    distinct_pairs = chong_pairs | xing_hai_pairs
    # 同一底层 pair 同时被分类时只计一次；复合只在确有两个不同 pair 时成立。
    return bool(chong_pairs), bool(xing_hai_pairs), len(distinct_pairs)


def generate_claims(
    chart: ChartFactLedger,
    features: ChartFeatureVector,
    task: BlindTask,
) -> list[Claim]:
    """生成最多一条杨派离婚/再婚风险命题；一般关系压力不升格为事件。"""
    if task.task_id != _SUPPORTED_TASK:
        raise TaskUnsupported(f"yang does not support task: {task.task_id}")
    if features.evidence_completeness != "full":
        return []
    sex = _sex(chart.sex_marker)
    if sex is None:
        return []

    day_branch = _day_branch(chart)
    if not day_branch:
        return []
    palace_chong, palace_xing_hai, palace_pair_count = _palace_disruption(features, day_branch)
    palace_disrupted = palace_chong or palace_xing_hai

    if sex == "male":
        spouse_star_basis = "wealth"
        spouse_count = _count(features, "正财", "偏财")
        spouse_present = features.has_wealth and spouse_count > 0
    else:
        spouse_star_basis = "official"
        spouse_count = _count(features, "正官", "七杀")
        spouse_present = features.has_official and spouse_count > 0

    peer_competition = _count(features, "比肩", "劫财") >= 3
    output_heavy = _count(features, "食神", "伤官") >= 4
    spouse_weak = not spouse_present or spouse_count <= 1
    output_spouse_conflict = output_heavy and spouse_present
    female_mixed_official = sex == "female" and features.mixed_official_kill
    palace_compound = palace_pair_count >= 2 and palace_chong and palace_xing_hai

    # 单一关系压力、单一宫冲或单一配偶星弱均不触发；每项来自不同结构家族。
    signals = {
        "spouse_palace_disrupted": palace_disrupted,
        "spouse_star_weak": spouse_weak,
        "peer_competition": peer_competition,
        "output_spouse_conflict": output_spouse_conflict,
        "female_mixed_official": female_mixed_official,
        "compound_distinct_palace_pairs": palace_compound,
    }
    independent_signal_count = sum(int(value) for value in signals.values())
    if independent_signal_count < 2:
        return []

    rule_id = "YANG-MARRIAGE-DIVORCE-REMARRIAGE-RISK-V1"
    refs = (
        "ten_god_counts.正财", "ten_god_counts.偏财", "ten_god_counts.正官", "ten_god_counts.七杀",
        "ten_god_counts.比肩", "ten_god_counts.劫财", "ten_god_counts.食神", "ten_god_counts.伤官",
        "has_wealth", "has_official", "mixed_official_kill", "chong_pairs", "xing_hai_pairs",
        "evidence_completeness",
    )
    evidence_raw = f"yang|{task.task_id}|{features.chart_id}|{rule_id}|{sex}|{independent_signal_count}"
    evidence = Evidence(
        evidence_id="evidence-" + hashlib.sha256(evidence_raw.encode("utf-8")).hexdigest()[:20],
        fact_refs=("sex_marker", "four_pillars.day"),
        feature_refs=refs,
        rule_id=rule_id,
        text=(
            f"性别口径={spouse_star_basis}，配偶星数={spouse_count}，日支={day_branch}，"
            f"去重后的独立信号={independent_signal_count}。"
        ),
    )
    claim = Claim(
        claim_id=stable_claim_id("yang", task.task_id, features.chart_id, rule_id),
        school_id="yang",
        task_id=task.task_id,
        claim_type="event_claim",
        stance="support",
        statement="杨派原局至少两类独立婚姻事件信号同向，存在离婚或再婚事件风险，但不作必然判断。",
        evidence=(evidence,),
        falsifier="若婚姻史中没有离婚或再婚记录，则命题证伪。",
        time_window=_LIFETIME,
        confidence_basis="按性别选取配偶星，并要求夫妻宫、配偶星、比劫、食伤冲突或女命官杀混杂中至少两类独立信号同向；高风险任务保守封顶。",
        applicability_snapshot={
            "sex": sex,
            "spouse_star_basis": spouse_star_basis,
            "spouse_star_count": spouse_count,
            "day_branch": day_branch,
            "palace_pair_count": palace_pair_count,
            "independent_signal_count": independent_signal_count,
            **signals,
            "evidence_completeness": features.evidence_completeness,
        },
        domain=task.domain,
        polarity="negative",
        magnitude=min(1.0, 0.42 + 0.08 * independent_signal_count),
        confidence=min(0.60, _HIGH_RISK_CONFIDENCE_CAP) if task.high_risk else 0.60,
        high_risk=task.high_risk,
    )
    validate_claim_evidence(claim, chart, features)
    return [claim]

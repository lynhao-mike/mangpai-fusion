"""高派第二批 L2 应期增强：领域结构成立后，以有根流年引动关键宫位。"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any

from engine.claims import Claim, Evidence, TaskUnsupported, TimeWindow, stable_claim_id, validate_claim_evidence
from engine.decision.models import ChartFactLedger
from engine.evaluation.models import BlindTask
from engine.features import ChartFeatureVector
from engine.predicates.relations import zhi_chong, zhi_chuan, zhi_xing

_SUPPORTED_TASKS = {
    "career.change_window",
    "marriage.event_window",
    "health.event_window",
    "wealth.major_loss_window",
}
_GANS = frozenset("甲乙丙丁戊己庚辛壬癸")
_BRANCHES = frozenset("子丑寅卯辰巳午未申酉戌亥")
_BRANCH_ELEMENTS = {
    "寅": "木", "卯": "木",
    "巳": "火", "午": "火",
    "辰": "土", "戌": "土", "丑": "土", "未": "土",
    "申": "金", "酉": "金",
    "亥": "水", "子": "水",
}
_LIUHE_PAIRS = {
    frozenset(("子", "丑")),
    frozenset(("寅", "亥")),
    frozenset(("卯", "戌")),
    frozenset(("辰", "酉")),
    frozenset(("巳", "申")),
    frozenset(("午", "未")),
}
_RELATION_SCORES = {"冲": 1.0, "穿": 0.9, "刑": 0.7, "合": 0.6, "伏吟": 0.55}
_HIGH_RISK_CONFIDENCE_CAP = 0.55


@dataclass(frozen=True)
class _DomainAnchor:
    label: str
    key_palaces: tuple[str, ...]
    feature_refs: tuple[str, ...]
    strength: float
    detail: str


@dataclass(frozen=True)
class _TimingCandidate:
    year: int
    ganzhi: str
    input_index: int
    score: float
    relation_types: tuple[str, ...]
    descriptions: tuple[str, ...]
    fact_refs: tuple[str, ...]


def _count(features: ChartFeatureVector, *names: str) -> int:
    return sum(int(features.ten_god_counts.get(name, 0)) for name in names)


def _ganzhi(step: dict[str, Any]) -> str:
    value = str(step.get("ganzhi") or step.get("干支") or step.get("liunian") or "").strip()
    if len(value) != 2 or value[0] not in _GANS or value[1] not in _BRANCHES:
        return ""
    return value


def _year(step: dict[str, Any]) -> int | None:
    value = step.get("year", step.get("年份"))
    return value if type(value) is int else None


def _pillar(chart: ChartFactLedger, palace: str) -> str:
    aliases = {"year": "年柱", "month": "月柱", "day": "日柱", "hour": "时柱"}
    value = str(chart.four_pillars.get(palace, chart.four_pillars.get(aliases[palace], ""))).strip()
    return value if len(value) == 2 and value[0] in _GANS and value[1] in _BRANCHES else ""


def _relation(left_branch: str, right_branch: str) -> str | None:
    if left_branch not in _BRANCHES or right_branch not in _BRANCHES:
        return None
    if zhi_chong(left_branch, right_branch):
        return "冲"
    if zhi_chuan(left_branch, right_branch):
        return "穿"
    if zhi_xing(left_branch, right_branch) is not None:
        return "刑"
    if frozenset((left_branch, right_branch)) in _LIUHE_PAIRS:
        return "合"
    if left_branch == right_branch:
        return "伏吟"
    return None


def _original_branches(chart: ChartFactLedger) -> tuple[str, ...]:
    return tuple(
        pillar[1]
        for palace in ("year", "month", "day", "hour")
        if (pillar := _pillar(chart, palace))
    )


def _has_same_element_root(branch: str, chart: ChartFactLedger) -> bool:
    element = _BRANCH_ELEMENTS.get(branch)
    return element is not None and any(_BRANCH_ELEMENTS.get(root) == element for root in _original_branches(chart))


def _gao_domain_anchor(
    features: ChartFeatureVector,
    task_id: str,
    chart: ChartFactLedger,
) -> _DomainAnchor | None:
    if features.evidence_completeness != "full":
        return None

    if task_id == "career.change_window":
        if not (features.has_official and features.has_output and features.branch_conflict_intensity >= 0.35):
            return None
        return _DomainAnchor(
            label="官杀与食伤并见的事业变动结构",
            key_palaces=("month", "year"),
            feature_refs=("has_official", "has_output", "branch_conflict_intensity"),
            strength=min(1.0, 0.5 + 0.25 * features.branch_conflict_intensity),
            detail=f"官杀存在={features.has_official}，食伤存在={features.has_output}，支冲突强度={features.branch_conflict_intensity:.2f}",
        )

    if task_id == "marriage.event_window":
        day_pillar = _pillar(chart, "day")
        if not day_pillar:
            return None
        day_branch = day_pillar[1]
        day_disrupted = any(day_branch in pair for pair in (*features.chong_pairs, *features.xing_hai_pairs))
        official_or_wealth = _count(features, "正官", "七杀", "正财", "偏财") >= 1
        if not (day_disrupted and official_or_wealth):
            return None
        return _DomainAnchor(
            label="夫妻宫受扰且配偶星存在",
            key_palaces=("day",),
            feature_refs=(
                "chong_pairs", "xing_hai_pairs", "ten_god_counts.正官",
                "ten_god_counts.七杀", "ten_god_counts.正财", "ten_god_counts.偏财",
            ),
            strength=0.62,
            detail=f"日支={day_branch}，日支冲刑害={day_disrupted}，官杀或财星存在={official_or_wealth}",
        )

    if task_id == "health.event_window":
        imbalance = features.draining_count - features.supporting_count
        if not (imbalance >= 4 and features.climate_extreme):
            return None
        return _DomainAnchor(
            label="克泄耗严重失衡且气候极端",
            key_palaces=("month", "day"),
            feature_refs=("supporting_count", "draining_count", "climate_extreme"),
            strength=min(1.0, 0.5 + 0.05 * imbalance),
            detail=f"克泄耗减生扶={imbalance}，气候极端={features.climate_extreme}",
        )

    if task_id == "wealth.major_loss_window":
        wealth = _count(features, "正财", "偏财")
        peers = _count(features, "比肩", "劫财")
        imbalance = features.draining_count - features.supporting_count
        if not (wealth >= 2 and peers >= 3 and imbalance >= 3):
            return None
        return _DomainAnchor(
            label="财星、比劫竞争与失衡压力并见",
            key_palaces=("year", "hour"),
            feature_refs=(
                "ten_god_counts.正财", "ten_god_counts.偏财", "ten_god_counts.比肩",
                "ten_god_counts.劫财", "supporting_count", "draining_count",
            ),
            strength=min(1.0, 0.45 + 0.04 * (wealth + peers)),
            detail=f"财星={wealth}，比劫={peers}，克泄耗减生扶={imbalance}",
        )

    return None


def _collect_gao_candidates(
    chart: ChartFactLedger,
    features: ChartFeatureVector,
    task: BlindTask,
    anchor: _DomainAnchor,
) -> list[_TimingCandidate]:
    del features, task
    candidates: list[_TimingCandidate] = []
    for index, step in enumerate(chart.liunian_steps):
        year = _year(step)
        ganzhi = _ganzhi(step)
        if year is None or not ganzhi:
            continue
        branch = ganzhi[1]
        if not _has_same_element_root(branch, chart):
            continue

        relations: list[str] = []
        descriptions: list[str] = []
        fact_refs: list[str] = [f"liunian_steps.{index}"]
        relation_score = 0.0
        for palace in anchor.key_palaces:
            pillar = _pillar(chart, palace)
            if not pillar:
                continue
            relation = _relation(branch, pillar[1])
            if relation is None:
                continue
            relations.append(relation)
            descriptions.append(f"流年{branch}与{palace}支{pillar[1]}{relation}")
            fact_refs.append(f"four_pillars.{palace}")
            relation_score += _RELATION_SCORES[relation]

        if len(fact_refs) == 1:
            continue
        score = round(anchor.strength + relation_score + 0.2, 6)
        candidates.append(
            _TimingCandidate(
                year=year,
                ganzhi=ganzhi,
                input_index=index,
                score=score,
                relation_types=tuple(relations),
                descriptions=tuple(descriptions),
                fact_refs=tuple(dict.fromkeys(fact_refs)),
            )
        )
    return candidates


def _select_candidate(candidates: list[_TimingCandidate]) -> _TimingCandidate | None:
    return min(candidates, key=lambda item: (-item.score, item.year, item.input_index)) if candidates else None


def _statement(task_id: str, candidate: _TimingCandidate) -> str:
    year = candidate.year
    if task_id == "career.change_window":
        return f"{year} 年为高派事业角色、职责或职业路径变化的关注窗口。"
    if task_id == "marriage.event_window":
        return f"{year} 年为高派婚恋事件关注窗口，可能表现为结婚、分合或关系重组，不预设单一结果。"
    if task_id == "health.event_window":
        return f"{year} 年为高派健康风险窗口，需关注可核验的显著状态变化，但不构成医学诊断。"
    return f"{year} 年为高派财富承压风险窗口，需关注可核验的显著损失事件。"


def _falsifier(task_id: str) -> str:
    event = {
        "career.change_window": "显著岗位、职责或职业路径变化",
        "marriage.event_window": "结婚、分合或关系重组等婚恋重大变化",
        "health.event_window": "显著健康状态变化",
        "wealth.major_loss_window": "显著财富损失事件",
    }[task_id]
    return f"若窗口内没有可核验的{event}，则本命题证伪。"


def generate_timing_claims(
    chart: ChartFactLedger,
    features: ChartFeatureVector,
    task: BlindTask,
) -> list[Claim]:
    """生成每任务每盘最多一条有根流年 Claim；事实不足时 abstain。"""
    if task.task_id not in _SUPPORTED_TASKS:
        raise TaskUnsupported(f"gao timing does not support task: {task.task_id}")
    if features.evidence_completeness != "full" or not chart.liunian_steps:
        return []
    anchor = _gao_domain_anchor(features, task.task_id, chart)
    if anchor is None:
        return []
    candidate = _select_candidate(_collect_gao_candidates(chart, features, task, anchor))
    if candidate is None:
        return []

    rule_id = {
        "career.change_window": "GAO-TIMING-CAREER-SUIYUN-ROOT-V1",
        "marriage.event_window": "GAO-TIMING-MARRIAGE-PALACE-ROOT-V1",
        "health.event_window": "GAO-TIMING-HEALTH-SYSTEM-ROOT-V1",
        "wealth.major_loss_window": "GAO-TIMING-WEALTH-PRESSURE-ROOT-V1",
    }[task.task_id]
    relation_text = "；".join(candidate.descriptions)
    evidence_raw = f"gao|{task.task_id}|{features.chart_id}|{rule_id}|{candidate.year}|{relation_text}"
    evidence = Evidence(
        evidence_id="evidence-" + hashlib.sha256(evidence_raw.encode("utf-8")).hexdigest()[:20],
        fact_refs=candidate.fact_refs,
        feature_refs=anchor.feature_refs,
        rule_id=rule_id,
        text=f"领域锚点：{anchor.detail}；有根流年引动：{relation_text}。",
    )
    confidence = min(0.64, 0.46 + 0.06 * candidate.score)
    if task.task_id in {"health.event_window", "wealth.major_loss_window"}:
        confidence = min(confidence, _HIGH_RISK_CONFIDENCE_CAP)
    claim = Claim(
        claim_id=stable_claim_id("gao", task.task_id, features.chart_id, f"{rule_id}:{candidate.year}"),
        school_id="gao",
        task_id=task.task_id,
        claim_type="timing_claim",
        stance="support",
        statement=_statement(task.task_id, candidate),
        evidence=(evidence,),
        falsifier=_falsifier(task.task_id),
        time_window=TimeWindow(candidate.year, candidate.year, "annual"),
        confidence_basis="高派第二批旁证先确认领域结构，再以流年支在原局有同类根气且引动关键宫位选择风险窗口；不以神煞名称单独构造事件概率。",
        applicability_snapshot={
            "trigger_year": candidate.year,
            "liunian_ganzhi": candidate.ganzhi,
            "rooted_liunian": True,
            "domain_anchor": anchor.label,
            "key_palaces": anchor.key_palaces,
            "relation_types": candidate.relation_types,
            "candidate_score": candidate.score,
            "input_index": candidate.input_index,
            "evidence_completeness": features.evidence_completeness,
        },
        domain=task.domain,
        polarity="negative" if task.high_risk else "neutral",
        magnitude=min(1.0, 0.35 + 0.12 * candidate.score),
        confidence=confidence,
        high_risk=task.high_risk,
    )
    validate_claim_evidence(claim, chart, features)
    return [claim]

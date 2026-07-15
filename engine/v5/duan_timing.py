"""段派 L2 应期 runner：先锁定领域事件锚点，再选择可计算岁运窗口。"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any

from engine.claims import Claim, Evidence, TaskUnsupported, TimeWindow, stable_claim_id, validate_claim_evidence
from engine.decision.models import ChartFactLedger
from engine.evaluation.models import BlindTask
from engine.features import ChartFeatureVector
from engine.predicates.relations import zhi_chong, zhi_chuan, zhi_liuhe, zhi_xing

_SUPPORTED_TASKS = {
    "career.change_window",
    "marriage.event_window",
    "health.event_window",
    "wealth.major_loss_window",
}
_GANS = frozenset("甲乙丙丁戊己庚辛壬癸")
_BRANCHES = frozenset("子丑寅卯辰巳午未申酉戌亥")
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


def _ganzhi(step: dict[str, Any]) -> str:
    value = str(step.get("ganzhi") or step.get("干支") or step.get("liunian") or "").strip()
    if len(value) != 2 or value[0] not in _GANS or value[1] not in _BRANCHES:
        return ""
    return value


def _year(step: dict[str, Any]) -> int | None:
    value = step.get("year", step.get("年份"))
    return value if type(value) is int else None


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
        zhi_liuhe(left_branch, right_branch)
        return "合"
    if left_branch == right_branch:
        return "伏吟"
    return None


def _count(features: ChartFeatureVector, *names: str) -> int:
    return sum(int(features.ten_god_counts.get(name, 0)) for name in names)


def _pillar(chart: ChartFactLedger, palace: str) -> str:
    aliases = {"year": "年柱", "month": "月柱", "day": "日柱", "hour": "时柱"}
    value = str(chart.four_pillars.get(palace, chart.four_pillars.get(aliases[palace], ""))).strip()
    return value if len(value) == 2 and value[0] in _GANS and value[1] in _BRANCHES else ""


def _domain_anchor(
    features: ChartFeatureVector,
    task_id: str,
    chart: ChartFactLedger,
) -> _DomainAnchor | None:
    if features.evidence_completeness != "full":
        return None

    if task_id == "career.change_window":
        official = _count(features, "正官", "七杀")
        output = _count(features, "食神", "伤官")
        action_signal = features.mixed_official_kill or features.branch_conflict_intensity >= 0.35
        if not (features.has_official and features.has_output and official >= 1 and output >= 2 and action_signal):
            return None
        return _DomainAnchor(
            label="官杀食伤事业结构与段派做功代理同向",
            key_palaces=("month", "hour"),
            feature_refs=(
                "ten_god_counts.正官", "ten_god_counts.七杀", "ten_god_counts.食神",
                "ten_god_counts.伤官", "mixed_official_kill", "branch_conflict_intensity",
            ),
            strength=min(1.0, 0.45 + 0.05 * (official + output)),
            detail=f"官杀={official}，食伤={output}，做功代理={action_signal}",
        )

    if task_id == "marriage.event_window":
        day_pillar = _pillar(chart, "day")
        if not day_pillar:
            return None
        day_branch = day_pillar[1]
        day_disrupted = any(day_branch in pair for pair in (*features.chong_pairs, *features.xing_hai_pairs))
        compound_pressure = bool(features.chong_pairs) and bool(features.xing_hai_pairs)
        signal_count = int(day_disrupted) + int(features.mixed_official_kill) + int(compound_pressure)
        if signal_count < 2:
            return None
        return _DomainAnchor(
            label="夫妻宫受扰与婚恋结构压力同向",
            key_palaces=("day",),
            feature_refs=("chong_pairs", "xing_hai_pairs", "mixed_official_kill", "branch_conflict_intensity"),
            strength=min(1.0, 0.45 + 0.12 * signal_count),
            detail=f"日支={day_branch}，日支受扰={day_disrupted}，独立压力信号={signal_count}",
        )

    if task_id == "health.event_window":
        imbalance = features.draining_count - features.supporting_count
        system_risk = imbalance >= 4 and (features.climate_extreme or features.element_concentration >= 0.55)
        if not system_risk:
            return None
        return _DomainAnchor(
            label="克泄耗失衡与系统性结构风险同向",
            key_palaces=("month", "day"),
            feature_refs=(
                "supporting_count", "draining_count", "climate_extreme",
                "element_concentration", "branch_conflict_intensity",
            ),
            strength=min(1.0, 0.5 + 0.05 * imbalance),
            detail=f"克泄耗减生扶={imbalance}，气候极端={features.climate_extreme}，五行集中度={features.element_concentration:.2f}",
        )

    if task_id == "wealth.major_loss_window":
        wealth = _count(features, "正财", "偏财")
        peers = _count(features, "比肩", "劫财")
        imbalance = features.draining_count - features.supporting_count
        pressure = (
            features.has_wealth
            and wealth >= 2
            and peers >= 3
            and imbalance >= 3
            and features.branch_conflict_intensity >= 0.35
        )
        if not pressure:
            return None
        return _DomainAnchor(
            label="财星承压、比劫竞争与做功受阻同向",
            key_palaces=("year", "hour"),
            feature_refs=(
                "ten_god_counts.正财", "ten_god_counts.偏财", "ten_god_counts.比肩",
                "ten_god_counts.劫财", "supporting_count", "draining_count", "branch_conflict_intensity",
            ),
            strength=min(1.0, 0.45 + 0.04 * (wealth + peers)),
            detail=f"财星={wealth}，比劫={peers}，克泄耗减生扶={imbalance}",
        )

    return None


def _dayun_index(chart: ChartFactLedger, step: dict[str, Any]) -> int | None:
    named = str(step.get("dayun") or step.get("大运") or "").strip()
    if named:
        for index, dayun in enumerate(chart.dayun_steps):
            if _ganzhi(dayun) == named:
                return index
    year = _year(step)
    if year is None:
        return None
    for index, dayun in enumerate(chart.dayun_steps):
        start = dayun.get("start_year")
        end = dayun.get("end_year")
        if type(start) is int and type(end) is int and start <= year <= end and _ganzhi(dayun):
            return index
    return None


def _collect_candidates(
    chart: ChartFactLedger,
    features: ChartFeatureVector,
    task: BlindTask,
    anchor: _DomainAnchor,
) -> list[_TimingCandidate]:
    candidates: list[_TimingCandidate] = []
    for index, step in enumerate(chart.liunian_steps):
        year = _year(step)
        ganzhi = _ganzhi(step)
        if year is None or not ganzhi:
            continue
        branch = ganzhi[1]
        relations: list[str] = []
        descriptions: list[str] = []
        refs: list[str] = [f"liunian_steps.{index}"]
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
            refs.append(f"four_pillars.{palace}")
            relation_score += _RELATION_SCORES[relation]

        # 段派窗口必须先真正引动该领域关键宫位；只有大运关系不能替代领域落点。
        if len(refs) == 1:
            continue

        dayun_index = _dayun_index(chart, step)
        if dayun_index is not None:
            dayun_ganzhi = _ganzhi(chart.dayun_steps[dayun_index])
            dayun_relation = _relation(branch, dayun_ganzhi[1]) if dayun_ganzhi else None
            if dayun_relation is not None:
                relations.append(f"岁运{dayun_relation}")
                descriptions.append(f"流年{branch}与大运支{dayun_ganzhi[1]}{dayun_relation}")
                refs.append(f"dayun_steps.{dayun_index}")
                relation_score += 0.35 * _RELATION_SCORES[dayun_relation]

        score = round(anchor.strength + relation_score, 6)
        candidates.append(
            _TimingCandidate(
                year=year,
                ganzhi=ganzhi,
                input_index=index,
                score=score,
                relation_types=tuple(relations),
                descriptions=tuple(descriptions),
                fact_refs=tuple(dict.fromkeys(refs)),
            )
        )
    return candidates


def _select_candidate(candidates: list[_TimingCandidate]) -> _TimingCandidate | None:
    if not candidates:
        return None
    return min(candidates, key=lambda item: (-item.score, item.year, item.input_index))


def _statement(task_id: str, candidate: _TimingCandidate) -> str:
    year = candidate.year
    if task_id == "career.change_window":
        return f"{year} 年为段派事业角色、职责或职业路径变化的关注窗口。"
    if task_id == "marriage.event_window":
        return f"{year} 年为段派婚恋重大变化窗口，事件类别可能表现为结婚、分合或关系重组，不预设单一结果。"
    if task_id == "health.event_window":
        return f"{year} 年为段派健康系统风险窗口，需关注可核验的显著状态变化，但不构成医学诊断。"
    return f"{year} 年为段派重大财富承压风险窗口，需关注可核验的显著损失事件。"


def _falsifier(task_id: str) -> str:
    labels = {
        "career.change_window": "显著岗位、职责或职业路径变化",
        "marriage.event_window": "结婚、分合或关系重组等婚恋重大变化",
        "health.event_window": "相应显著健康状态变化",
        "wealth.major_loss_window": "相应显著财富损失事件",
    }
    if task_id in {"health.event_window", "wealth.major_loss_window"}:
        return f"窗口内没有可核验的{labels[task_id]}，则本命题证伪。"
    return f"若窗口内没有可核验的{labels[task_id]}，则本命题证伪。"


def generate_timing_claims(
    chart: ChartFactLedger,
    features: ChartFeatureVector,
    task: BlindTask,
) -> list[Claim]:
    """为四个白名单任务生成每盘最多一条年度 Claim；证据不足时 abstain。"""
    if task.task_id not in _SUPPORTED_TASKS:
        raise TaskUnsupported(f"duan timing does not support task: {task.task_id}")
    if not chart.liunian_steps:
        return []
    anchor = _domain_anchor(features, task.task_id, chart)
    if anchor is None:
        return []
    candidate = _select_candidate(_collect_candidates(chart, features, task, anchor))
    if candidate is None:
        return []

    rule_id = {
        "career.change_window": "DUAN-TIMING-CAREER-BINZHU-V1",
        "marriage.event_window": "DUAN-TIMING-MARRIAGE-PALACE-V1",
        "health.event_window": "DUAN-TIMING-HEALTH-IMBALANCE-V1",
        "wealth.major_loss_window": "DUAN-TIMING-WEALTH-PRESSURE-V1",
    }[task.task_id]
    relation_text = "；".join(candidate.descriptions)
    evidence_raw = f"duan|{task.task_id}|{features.chart_id}|{rule_id}|{candidate.year}|{relation_text}"
    evidence = Evidence(
        evidence_id="evidence-" + hashlib.sha256(evidence_raw.encode("utf-8")).hexdigest()[:20],
        fact_refs=candidate.fact_refs,
        feature_refs=anchor.feature_refs,
        rule_id=rule_id,
        text=f"领域锚点：{anchor.detail}；岁运引动：{relation_text}。",
    )
    confidence = min(0.66, 0.48 + 0.06 * candidate.score)
    if task.high_risk:
        confidence = min(confidence, _HIGH_RISK_CONFIDENCE_CAP)
    claim = Claim(
        claim_id=stable_claim_id("duan", task.task_id, features.chart_id, f"{rule_id}:{candidate.year}"),
        school_id="duan",
        task_id=task.task_id,
        claim_type="timing_claim",
        stance="support",
        statement=_statement(task.task_id, candidate),
        evidence=(evidence,),
        falsifier=_falsifier(task.task_id),
        time_window=TimeWindow(candidate.year, candidate.year, "annual"),
        confidence_basis="段派先确认领域锚点，再以宾主体用关键宫位的可计算岁运引动选择年度窗口；不以通用冲合直接套用各领域。",
        applicability_snapshot={
            "trigger_year": candidate.year,
            "liunian_ganzhi": candidate.ganzhi,
            "domain_anchor": anchor.label,
            "anchor_detail": anchor.detail,
            "key_palaces": anchor.key_palaces,
            "relation_types": candidate.relation_types,
            "candidate_score": candidate.score,
            "input_index": candidate.input_index,
            "evidence_completeness": features.evidence_completeness,
        },
        domain=task.domain,
        polarity="negative" if task.high_risk else "neutral",
        magnitude=min(1.0, 0.35 + 0.15 * candidate.score),
        confidence=confidence,
        high_risk=task.high_risk,
    )
    validate_claim_evidence(claim, chart, features)
    return [claim]

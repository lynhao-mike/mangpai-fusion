"""ZiPing Fusion Engine v5 最小 runner 骨架。

该 runner 只建立五派命题图最小闭环，不实现具体命理断语。
真实规则应在后续 school runner 中独立产出 V5Claim，再交给本模块建图与仲裁。
"""

from __future__ import annotations

import hashlib
from collections import defaultdict
from typing import Any

from engine.v5.domain import (
    V5ArbitrationResult,
    V5Claim,
    V5Confidence,
    V5Evidence,
    V5LearningSignal,
    V5Output,
    V5Prediction,
    V5PredictionLedger,
    V5StructureGraph,
    V5_SCHOOLS,
)

PROBABILISTIC_DOMAIN_WHITELIST = {"学业", "事业", "财富", "婚姻", "健康"}
STRUCTURE_SCHOOLS = {"ziping", "ditiansui", "gao_dechen"}
EVENT_SCHOOLS = {"gao_dechen", "duan_jianye", "yang_qingjuan"}


def _stable_id(prefix: str, *parts: object) -> str:
    raw = "|".join(str(part) for part in parts)
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]
    return f"{prefix}-{digest}"


def _chart_label(chart: dict[str, Any]) -> str:
    pillars = chart.get("pillars") or chart.get("四柱") or chart.get("bazi") or "未提供四柱"
    if isinstance(pillars, dict):
        return "".join(str(pillars.get(key, "")) for key in ("year", "month", "day", "hour")) or str(pillars)
    if isinstance(pillars, list):
        return "".join(str(item) for item in pillars)
    return str(pillars)


def build_abstain_claims(chart: dict[str, Any], case_id: str) -> list[V5Claim]:
    """为五派生成独立占位命题，保证 v5 骨架可运行。

    后续真实 school runner 接入后，应传入实际 claims 覆盖该占位输出。
    """

    label = _chart_label(chart)
    school_claim_text = {
        "ziping": "子平类 runner 尚未接入生产规则；当前仅登记结构法度待判。",
        "ditiansui": "滴天髓类 runner 尚未接入生产规则；当前仅登记气势清浊待判。",
        "gao_dechen": "高德臣 runner 尚未接入生产规则；当前仅登记做功转化待判。",
        "duan_jianye": "段建业 runner 尚未接入生产规则；当前仅登记事件框架待判。",
        "yang_qingjuan": "杨清娟 runner 尚未接入生产规则；当前仅登记象法细节待判。",
    }
    claim_type = {
        "ziping": "structure_claim",
        "ditiansui": "structure_claim",
        "gao_dechen": "event_claim",
        "duan_jianye": "event_claim",
        "yang_qingjuan": "event_claim",
    }
    claims: list[V5Claim] = []
    for school in V5_SCHOOLS:
        evidence = V5Evidence(
            evidence_id=_stable_id("v5ev", case_id, school, label),
            source="chart_model",
            text=f"五派共用同一 Chart Model：{label}",
            node_refs=["chart:root"],
            metadata={"runner_state": "stub"},
        )
        claims.append(
            V5Claim(
                claim_id=_stable_id("v5cl", case_id, school, label),
                school=school,  # type: ignore[arg-type]
                domain="总体",
                claim=school_claim_text[school],
                claim_type=claim_type[school],  # type: ignore[arg-type]
                stance="abstain",
                polarity="neutral",
                confidence=V5Confidence(tier="★", score=0.1, note="runner 骨架占位，不进入正式断语"),
                evidence=[evidence],
                probabilistic=False,
                falsifiable="接入真实五派 runner 后，占位命题应消失。",
                metadata={"case_id": case_id, "school_role": "see V5_SCHOOL_ROLES"},
            )
        )
    return claims


def build_structure_graph(case_id: str, chart: dict[str, Any], claims: list[V5Claim]) -> V5StructureGraph:
    """把 chart、五派命题、证据与领域挂入最小结构图。"""

    nodes: list[dict[str, Any]] = [
        {"id": "chart:root", "type": "chart", "label": _chart_label(chart), "payload": dict(chart)},
    ]
    edges: list[dict[str, Any]] = []
    seen_domains: set[str] = set()

    for claim in claims:
        claim_node_id = f"claim:{claim.claim_id}"
        domain_node_id = f"domain:{claim.domain}"
        if claim.domain not in seen_domains:
            nodes.append({"id": domain_node_id, "type": "domain", "label": claim.domain})
            seen_domains.add(claim.domain)
        nodes.append(
            {
                "id": claim_node_id,
                "type": "claim",
                "label": claim.claim,
                "school": claim.school,
                "school_role": claim.role,
                "claim_type": claim.claim_type,
            }
        )
        edges.append({"source": "chart:root", "target": claim_node_id, "type": "feeds"})
        edges.append({"source": claim_node_id, "target": domain_node_id, "type": "targets"})

        for evidence in claim.evidence:
            evidence_node_id = f"evidence:{evidence.evidence_id}"
            nodes.append({"id": evidence_node_id, "type": "evidence", "label": evidence.text, "source": evidence.source})
            edges.append({"source": evidence_node_id, "target": claim_node_id, "type": "supports"})

        for evidence in claim.counter_evidence:
            evidence_node_id = f"evidence:{evidence.evidence_id}"
            nodes.append({"id": evidence_node_id, "type": "evidence", "label": evidence.text, "source": evidence.source})
            edges.append({"source": evidence_node_id, "target": claim_node_id, "type": "weakens"})

    return V5StructureGraph(case_id=case_id, nodes=nodes, edges=edges)


def arbitrate_claims(claims: list[V5Claim]) -> list[V5ArbitrationResult]:
    """生成最小三段式仲裁结果。

    MVP 只根据 claim_type、stance、school role 形成可解释骨架；真实权重、生命周期、
    历史命中率与冲突分类后续接入。
    """

    claims_by_domain: dict[str, list[V5Claim]] = defaultdict(list)
    for claim in claims:
        claims_by_domain[claim.domain].append(claim)

    results: list[V5ArbitrationResult] = []
    for domain, domain_claims in sorted(claims_by_domain.items()):
        support_claims = [c for c in domain_claims if c.stance == "support"]
        oppose_claims = [c for c in domain_claims if c.stance == "oppose"]
        abstain_claims = [c for c in domain_claims if c.stance == "abstain"]
        structure_claims = [c for c in domain_claims if c.school in STRUCTURE_SCHOOLS or c.claim_type == "structure_claim"]
        event_claims = [c for c in domain_claims if c.school in EVENT_SCHOOLS or c.claim_type == "event_claim"]
        probabilistic_allowed = domain in PROBABILISTIC_DOMAIN_WHITELIST and any(c.probabilistic for c in domain_claims)
        conflict_type = "stance_conflict" if support_claims and oppose_claims else "none"

        structure_winners = [c.school for c in structure_claims if c.stance != "abstain"]
        event_winners = [c.school for c in event_claims if c.stance != "abstain"]
        minority = [c.claim_id for c in oppose_claims]

        if len(abstain_claims) == len(domain_claims):
            structure_conclusion = "五派 runner 尚未产生可仲裁结构命题。"
            event_conclusion = "五派 runner 尚未产生可仲裁事件命题。"
            confidence = V5Confidence(tier="★", score=0.1, note="全员弃权，占位输出")
        else:
            structure_conclusion = "结构合法性仲裁已形成候选结论。"
            event_conclusion = "事件落地仲裁已形成候选结论。"
            confidence = V5Confidence(tier="★★★", score=0.6, note="MVP 仲裁，尚未接入历史校准")

        results.append(
            V5ArbitrationResult(
                domain=domain,
                stage="structure_legality",
                conclusion=structure_conclusion,
                winning_schools=structure_winners,
                minority_claims=minority,
                support_score=float(len([c for c in structure_claims if c.stance == "support"])),
                opposition_score=float(len([c for c in structure_claims if c.stance == "oppose"])),
                conflict_type=conflict_type,
                confidence=confidence,
                rationale="子平类、滴天髓类与高德臣优先参与结构合法性判断。",
                probabilistic_allowed=False,
            )
        )
        results.append(
            V5ArbitrationResult(
                domain=domain,
                stage="event_realization",
                conclusion=event_conclusion,
                winning_schools=event_winners,
                minority_claims=minority,
                support_score=float(len([c for c in event_claims if c.stance == "support"])),
                opposition_score=float(len([c for c in event_claims if c.stance == "oppose"])),
                conflict_type=conflict_type,
                confidence=confidence,
                rationale="高德臣、段建业、杨清娟优先参与事件落地判断，子平/滴天髓提供结构约束。",
                probabilistic_allowed=probabilistic_allowed,
            )
        )
        results.append(
            V5ArbitrationResult(
                domain=domain,
                stage="probability_timing",
                conclusion="仅白名单事件且具备时间窗与反馈标签时允许概率化。",
                winning_schools=[c.school for c in domain_claims if c.probabilistic],
                minority_claims=[],
                support_score=float(len([c for c in domain_claims if c.probabilistic])),
                opposition_score=0.0,
                conflict_type="none",
                confidence=V5Confidence(tier="★★", score=0.4, note="概率层 MVP 只登记许可，不伪精确"),
                rationale="性格、格局高低、宽泛气质描述不进入概率层。",
                probabilistic_allowed=probabilistic_allowed,
            )
        )
    return results


def build_prediction_ledger(case_id: str, claims: list[V5Claim]) -> V5PredictionLedger:
    """从可概率化命题生成受限概率 ledger。

    v5 概率层只登记具体、可反馈、处于白名单领域的事件命题；
    性格、总体结构、无时间窗的宽泛判断不生成概率条目。
    """

    predictions: list[V5Prediction] = []
    for claim in claims:
        if not claim.probabilistic or claim.domain not in PROBABILISTIC_DOMAIN_WHITELIST:
            continue
        time_window = dict(claim.timing_hints[0]) if claim.timing_hints else {}
        predictions.append(
            V5Prediction(
                prediction_id=_stable_id("v5pred", case_id, claim.claim_id, claim.domain),
                domain=claim.domain,
                event_label=claim.claim,
                probability_range=(0.35, 0.55),
                confidence=V5Confidence(tier="★★", score=0.4, note="MVP 概率范围，需反馈校准"),
                time_window=time_window,
                calibration_note="由可概率化 V5Claim 登记；样本不足，暂不伪精确。",
            )
        )
    return V5PredictionLedger(case_id=case_id, predictions=predictions)


def build_learning_signals(case_id: str, claims: list[V5Claim], ledger: V5PredictionLedger) -> list[V5LearningSignal]:
    """生成学习信号占位，确保反馈回归有稳定挂载点。"""

    signals: list[V5LearningSignal] = []
    for claim in claims:
        signals.append(
            V5LearningSignal(
                signal_id=_stable_id("v5sig", case_id, claim.claim_id),
                case_id=case_id,
                target_id=claim.claim_id,
                signal_type="claim_trace_registered",
                value="pending_feedback",
                note="命题已进入 v5 图谱，等待 feedback.md 或 prediction ledger 绑定。",
            )
        )
    for prediction in ledger.predictions:
        signals.append(
            V5LearningSignal(
                signal_id=_stable_id("v5sig", case_id, prediction.prediction_id),
                case_id=case_id,
                target_id=prediction.prediction_id,
                signal_type="prediction_registered",
                value="pending_feedback",
                note="受限概率预测已登记，等待反馈校准。",
            )
        )
    return signals


def run_v5(
    chart: dict[str, Any],
    *,
    case_id: str = "",
    claims: list[V5Claim] | None = None,
) -> V5Output:
    """运行 v5 五派命题图最小闭环。

    参数：
    - chart：五派共享的标准命盘对象。
    - case_id：案例 ID；缺省时从 chart.case_id 推断。
    - claims：外部真实 school runner 产出的命题；缺省时生成五派弃权占位命题。
    """

    resolved_case_id = case_id or str(chart.get("case_id", "V5-UNTRACKED"))
    resolved_claims = list(claims) if claims is not None else build_abstain_claims(chart, resolved_case_id)
    graph = build_structure_graph(resolved_case_id, chart, resolved_claims)
    arbitration_results = arbitrate_claims(resolved_claims)
    ledger = build_prediction_ledger(resolved_case_id, resolved_claims)
    learning_signals = build_learning_signals(resolved_case_id, resolved_claims, ledger)
    return V5Output(
        case_id=resolved_case_id,
        chart=dict(chart),
        claims=resolved_claims,
        structure_graph=graph,
        arbitration_results=arbitration_results,
        prediction_ledger=ledger,
        learning_signals=learning_signals,
    )

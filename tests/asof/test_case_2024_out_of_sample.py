from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date

from engine.asof.daiyun_context import NatalRelation, PathChange, adapt_daiyun_segment
from engine.asof.event_candidate import (
    AnnualInteractionTrace,
    CompletionMode,
    RootLevel,
    VerificationStatus,
    evaluate_event_candidate,
)
from engine.asof.natal_capacity import (
    CapacityNode,
    EvidenceRef,
    PathRef,
    SourceCitation,
    build_natal_capacity_graph,
)
from engine.asof.state_ledger import (
    AsOfRequest,
    EventImpactAssessment,
    EventLedgerEntry,
    ImpactLevel,
    ImpactScope,
    Persistence,
    admit_hypothesis_branch,
    build_verified_state,
)
from engine.asof.wealth_propagation import WealthPropagationEdge, propagate_career_event_to_wealth


CASE_ID = "C-2026-024-坤-己巳壬申辛亥壬辰"
INPUT_PATH = f"cases/{CASE_ID}/input.md"
FEEDBACK_PATH = f"cases/{CASE_ID}/feedback.md"


@dataclass(frozen=True)
class _Segment:
    seq: int
    ganzhi: str
    age_range: tuple[int, int]
    year_range: tuple[int, int]
    feature: str
    typical_domains: list[str]


def _chart(locator: str, excerpt: str) -> EvidenceRef:
    return EvidenceRef(INPUT_PATH, locator, excerpt)


OUTPUT = _chart("四柱明细.月柱/时柱.十神", "月柱壬伤官；时柱壬伤官")
AUTHORITY = _chart("四柱明细.年柱.藏干十神", "巳藏正官、劫财、正印")
SUPPORT = _chart("四柱明细.藏干十神", "巳、申、辰均见印星")
CHART = _chart("四柱", "己巳 壬申 辛亥 壬辰")
START_LUCK = _chart("大运.起运年", "1996，顺行")


def _natal_graph():
    nodes = (
        CapacityNode("career-output", "语言与知识输出", (OUTPUT,)),
        CapacityNode("career-authority", "规则与管理职责", (AUTHORITY,)),
        CapacityNode("career-support", "资质与组织承接", (SUPPORT,)),
    )
    path = PathRef(
        "education-to-management",
        "教育输出经组织承接进入基层管理",
        tuple(node.node_id for node in nodes),
        (OUTPUT, AUTHORITY, SUPPORT),
    )
    return build_natal_capacity_graph(
        case_id=CASE_ID,
        capacity_nodes=nodes,
        structural_features=(OUTPUT, AUTHORITY, SUPPORT),
        vulnerabilities=(_chart("四柱明细", "伤官两透，官星仅藏"),),
        feasible_paths=(path,),
        constraints=(_chart("四柱明细", "管理落点须由官印与组织环境承接"),),
        chart_evidence=(CHART, START_LUCK),
        source_citations=(
            SourceCitation(INPUT_PATH, 41, "年柱十神：偏印"),
            SourceCitation(INPUT_PATH, 50, "月柱十神：伤官"),
        ),
        competing_explanations=("专业教学而不进入管理",),
    )


def _stages():
    path_change_2014 = PathChange(
        "education-to-management",
        "甲戌运仅显式开放教育职业入口，不读取现实履历",
        (START_LUCK, OUTPUT, SUPPORT),
    )
    path_change_2024 = PathChange(
        "education-to-management",
        "乙亥运放大既有教育输出路径，管理兑现仍须年度候选门",
        (START_LUCK, OUTPUT, AUTHORITY),
    )
    relation = NatalRelation("career-output", "大运信号作用于既有输出节点", (OUTPUT,))
    return (
        adapt_daiyun_segment(
            _Segment(2, "甲戌", (18, 28), (2006, 2016), "", []),
            opened_paths=(path_change_2014,),
            natal_relations=(relation,),
            domain_tendency="open",
            applicability_conditions=("仅用于2006-2015闭区间回放",),
        ),
        adapt_daiyun_segment(
            _Segment(3, "乙亥", (28, 38), (2016, 2026), "", []),
            amplified_paths=(path_change_2024,),
            natal_relations=(relation,),
            domain_tendency="mixed",
            applicability_conditions=("仅用于2016-2025闭区间回放",),
        ),
    )


def _decision(
    event_id: str,
    *,
    event_type: str,
    year: int,
    liunian: str,
    dayun: str,
    window_start: date,
    window_end: date,
):
    trace = AnnualInteractionTrace(
        year=year,
        liunian=liunian,
        dayun_ganzhi=dayun,
        relations=(OUTPUT, AUTHORITY, SUPPORT),
        activated_node_ids=("career-output", "career-authority", "career-support"),
        domains=("career",),
        supporting_evidence=(OUTPUT, AUTHORITY, SUPPORT),
        counter_evidence=(),
        trigger_strength="high",
        crossed_candidate_gate=True,
    )
    return evaluate_event_candidate(
        candidate_id=event_id,
        event_type=event_type,
        window_start=window_start,
        window_end=window_end,
        annual_trace=trace,
        root_level=RootLevel.STRONG_ROOT,
        completion_mode=CompletionMode.ACTIVATE_EXISTING,
        natal_evidence=(OUTPUT, AUTHORITY, SUPPORT),
        daiyun_evidence=(START_LUCK,),
        root_evidence=(OUTPUT, AUTHORITY, SUPPORT),
        source_citations=(
            SourceCitation(INPUT_PATH, 41, "年柱十神：偏印"),
            SourceCitation(INPUT_PATH, 50, "月柱十神：伤官"),
        ),
        supporting_evidence=(OUTPUT, AUTHORITY, SUPPORT),
        alternative_hypotheses=("同一结构只兑现为专业教学",),
        frozen_version="asof-prototype-v1-g6-oos",
    )


def _confirmed_entry(
    event_id: str,
    *,
    event_type: str,
    year: int,
    liunian: str,
    dayun: str,
    window_start: date,
    window_end: date,
    normalized_event_date: date,
    state_value: str,
    impact: ImpactLevel,
    persistence: Persistence,
    opened_path_ids: tuple[str, ...] = (),
) -> EventLedgerEntry:
    decision = _decision(
        event_id,
        event_type=event_type,
        year=year,
        liunian=liunian,
        dayun=dayun,
        window_start=window_start,
        window_end=window_end,
    )
    assert decision.accepted and decision.candidate is not None
    candidate = replace(
        decision.candidate,
        verification_status=VerificationStatus.CONFIRMED,
        supporting_evidence=decision.candidate.supporting_evidence
        + (EvidenceRef(FEEDBACK_PATH, f"事业反馈:{window_start.year}-{window_end.year}", state_value),),
    )
    assessment = EventImpactAssessment(
        event_id=event_id,
        event_date=normalized_event_date,
        event_type=event_type,
        root_level=candidate.root_level,
        completion_mode=candidate.completion_mode,
        system_suggested_impact=impact,
        system_suggested_persistence=persistence,
        system_suggested_scope=ImpactScope.PRIMARY_DOMAIN,
        state_value=state_value,
        opened_path_ids=opened_path_ids,
    )
    return EventLedgerEntry(candidate, assessment)


def _history() -> tuple[EventLedgerEntry, ...]:
    return (
        _confirmed_entry(
            "career-2014-2015-teacher-entry",
            event_type="career_entry",
            year=2015,
            liunian="乙未",
            dayun="甲戌",
            window_start=date(2014, 1, 1),
            window_end=date(2015, 12, 31),
            normalized_event_date=date(2015, 12, 31),
            state_value="入职小学教师，实际教英语",
            impact=ImpactLevel.MAJOR,
            persistence=Persistence.CROSS_DAIYUN,
        ),
        _confirmed_entry(
            "career-2024-2025-school-principal",
            event_type="promotion",
            year=2025,
            liunian="乙巳",
            dayun="乙亥",
            window_start=date(2024, 1, 1),
            window_end=date(2025, 12, 31),
            normalized_event_date=date(2025, 12, 31),
            state_value="升职为校长",
            impact=ImpactLevel.TURNING_POINT,
            persistence=Persistence.CROSS_DAIYUN,
            opened_path_ids=("education-management-realized",),
        ),
    )


def _replay(as_of_date: date):
    return build_verified_state(
        AsOfRequest(CASE_ID, as_of_date),
        entries=_history(),
        daiyun_end=date(2025, 12, 31),
        current_center="教育系统职业路径",
        reasonable_range=("专业教学", "基层教育管理"),
    )


def test_case_2024_builds_traceable_natal_graph_and_two_frozen_daiyun_stages() -> None:
    graph = _natal_graph()
    stages = _stages()

    assert {node.node_id for node in graph.capacity_nodes} == {
        "career-output",
        "career-authority",
        "career-support",
    }
    assert graph.feasible_paths[0].node_ids == (
        "career-output",
        "career-authority",
        "career-support",
    )
    assert [(stage.ganzhi, stage.start_date, stage.end_date) for stage in stages] == [
        ("甲戌", date(2006, 1, 1), date(2015, 12, 31)),
        ("乙亥", date(2016, 1, 1), date(2025, 12, 31)),
    ]


def test_case_2024_feedback_events_cross_the_frozen_double_evidence_gate() -> None:
    entries = _history()

    assert tuple(entry.candidate.verification_status for entry in entries) == (
        VerificationStatus.CONFIRMED,
        VerificationStatus.CONFIRMED,
    )
    assert tuple(entry.candidate.root_level for entry in entries) == (
        RootLevel.STRONG_ROOT,
        RootLevel.STRONG_ROOT,
    )
    assert tuple(entry.candidate.completion_mode for entry in entries) == (
        CompletionMode.ACTIVATE_EXISTING,
        CompletionMode.ACTIVATE_EXISTING,
    )


def test_case_2024_three_cutoffs_differ_and_never_leak_later_feedback() -> None:
    before_entry = _replay(date(2013, 12, 31))
    after_entry = _replay(date(2015, 12, 31))
    after_promotion = _replay(date(2025, 12, 31))

    assert before_entry.verified_event_ids == ()
    assert after_entry.verified_event_ids == ("career-2014-2015-teacher-entry",)
    assert after_promotion.verified_event_ids == (
        "career-2014-2015-teacher-entry",
        "career-2024-2025-school-principal",
    )
    assert "升职为校长" not in tuple(state.value for state in after_entry.reality_track.active_states)
    assert before_entry != after_entry != after_promotion


def test_case_2024_window_end_dates_are_normalization_boundaries_not_claimed_fact_dates() -> None:
    teacher, principal = _history()

    assert teacher.candidate.window_start == date(2014, 1, 1)
    assert teacher.candidate.window_end == teacher.assessment.event_date == date(2015, 12, 31)
    assert principal.candidate.window_start == date(2024, 1, 1)
    assert principal.candidate.window_end == principal.assessment.event_date == date(2025, 12, 31)
    assert all("normalized" not in evidence.excerpt.lower() for entry in (teacher, principal) for evidence in entry.candidate.supporting_evidence)


def test_case_2024_verified_state_and_unverified_hypothesis_are_physically_separate() -> None:
    decision = _decision(
        "career-2024-2025-school-principal-hypothesis",
        event_type="promotion",
        year=2025,
        liunian="乙巳",
        dayun="乙亥",
        window_start=date(2024, 1, 1),
        window_end=date(2025, 12, 31),
    )
    assert decision.candidate is not None
    assessment = EventImpactAssessment(
        event_id=decision.candidate.candidate_id,
        event_date=date(2025, 12, 31),
        event_type="promotion",
        root_level=decision.candidate.root_level,
        completion_mode=decision.candidate.completion_mode,
        system_suggested_impact=ImpactLevel.MAJOR,
        system_suggested_persistence=Persistence.CROSS_DAIYUN,
        system_suggested_scope=ImpactScope.PRIMARY_DOMAIN,
        state_value="条件分支：升职为校长",
    )
    request = AsOfRequest(CASE_ID, date(2023, 12, 31))
    verified = _replay(request.as_of_date)
    hypothesis = admit_hypothesis_branch(
        request,
        candidate=decision.candidate,
        assessment=assessment,
        condition="若2024-2025发生教育管理职责升级",
        difference_from_verified="从专业教学中心转为基层教育管理",
        changed_fundamentals=("现实职责层级",),
        changed_future_conclusions=("管理路径成为后运起点",),
        minimum_question="是否已经正式承担校长职责？",
        falsifier="截至2025年底仍仅承担教学职责",
    )

    assert hypothesis is not None
    assert hypothesis.candidate_id not in verified.verified_event_ids
    assert not hasattr(verified, "candidate_id")
    assert not hasattr(hypothesis, "reality_track")


def test_case_2024_wealth_abstains_on_both_g4_synthetic_edges_without_required_feedback() -> None:
    promotion_edge = WealthPropagationEdge(
        edge_id="synthetic-promotion-to-income-capacity",
        source_event_type="promotion",
        target_state="稳定收入能力提高",
        required_conditions=("薪酬制度随职级调整",),
        delay_days=30,
        persistence=Persistence.CROSS_DAIYUN,
        falsifiers=("晋升不伴随收入变化",),
        verified=True,
    )
    entrepreneurship_edge = WealthPropagationEdge(
        edge_id="synthetic-entrepreneurship-to-risk-exposure",
        source_event_type="entrepreneurship",
        target_state="收入结构变化与资产风险暴露",
        required_conditions=("经营主体已实际运行",),
        delay_days=0,
        persistence=Persistence.SHORT_TERM,
        falsifiers=("未发生资金投入",),
        verified=True,
        short_term_days=365,
    )
    decision = propagate_career_event_to_wealth(
        event_id="career-2024-2025-school-principal",
        event_type="promotion",
        event_date=date(2025, 12, 31),
        verified_event=True,
        observed_conditions=(),
        edges=(promotion_edge, entrepreneurship_edge),
    )

    assert decision.changed is False
    assert decision.reason_code == "PROPAGATION_CONDITIONS_NOT_MET"
    assert decision.state is None

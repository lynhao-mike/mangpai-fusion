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


CASE_ID = "C-2026-027-乾-丁卯壬寅甲午乙丑"
INPUT_PATH = f"cases/{CASE_ID}/input.md"
FEEDBACK_PATH = f"cases/{CASE_ID}/feedback.md"
FEEDBACK_DATE = date(2026, 6, 1)
WINDOW_START = date(2018, 1, 1)
NORMALIZED_EVENT_DATE = date(2020, 12, 31)


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


TECHNICAL_OUTPUT = _chart("四柱及藏干十神", "丁伤官；寅藏丙食神")
APPLIED_RESOURCE = _chart("四柱及藏干十神", "壬偏印；丑藏癸正印")
INSTITUTION = _chart("藏干.时支", "丑藏辛正官")
CHART = _chart("四柱", "丁卯 壬寅 甲午 乙丑")
START_LUCK = _chart("大运", "1990年起运，逆排；己亥运后接戊戌运")


def _natal_graph():
    nodes = (
        CapacityNode("career-technical-output", "设计绘图与工艺输出", (TECHNICAL_OUTPUT,)),
        CapacityNode("career-applied-resource", "应用技能与图纸学习", (APPLIED_RESOURCE,)),
        CapacityNode("career-institutional-constraint", "制度与保障承载", (INSTITUTION,)),
    )
    path = PathRef(
        "mechanical-design-specialization",
        "应用技能与技术输出形成机械制造设计路径",
        tuple(node.node_id for node in nodes),
        (TECHNICAL_OUTPUT, APPLIED_RESOURCE, INSTITUTION),
    )
    return build_natal_capacity_graph(
        case_id=CASE_ID,
        capacity_nodes=nodes,
        structural_features=(TECHNICAL_OUTPUT, APPLIED_RESOURCE, INSTITUTION),
        vulnerabilities=(_chart("四柱及藏干十神", "正官仅藏，制度保障须现实核验"),),
        feasible_paths=(path,),
        constraints=(_chart("大运", "职业专业化须经阶段和年度候选门"),),
        chart_evidence=(CHART, START_LUCK),
        source_citations=(
            SourceCitation(INPUT_PATH, 25, "四柱：丁卯、壬寅、甲午、乙丑"),
            SourceCitation(INPUT_PATH, 33, "藏干及十神完整列示"),
        ),
        competing_explanations=("一般制造岗位而非设计专业化",),
    )


def _stages():
    opened = PathChange(
        "mechanical-design-specialization",
        "己亥运开放既有应用技能路径，不读取现实履历",
        (START_LUCK, TECHNICAL_OUTPUT, APPLIED_RESOURCE),
    )
    amplified = PathChange(
        "mechanical-design-specialization",
        "戊戌运放大既有技术输出路径，不读取卖房反馈",
        (START_LUCK, TECHNICAL_OUTPUT, INSTITUTION),
    )
    relation = NatalRelation(
        "career-technical-output",
        "大运信号作用于既有技术输出节点",
        (TECHNICAL_OUTPUT,),
    )
    return (
        adapt_daiyun_segment(
            _Segment(3, "己亥", (24, 34), (2010, 2020), "", []),
            opened_paths=(opened,),
            natal_relations=(relation,),
            domain_tendency="open",
            applicability_conditions=("仅用于2010-2019闭区间回放",),
        ),
        adapt_daiyun_segment(
            _Segment(4, "戊戌", (34, 44), (2020, 2030), "", []),
            amplified_paths=(amplified,),
            natal_relations=(relation,),
            domain_tendency="mixed",
            applicability_conditions=("仅用于2020-2029闭区间回放",),
        ),
    )


def _decision():
    trace = AnnualInteractionTrace(
        year=2020,
        liunian="庚子",
        dayun_ganzhi="戊戌",
        relations=(TECHNICAL_OUTPUT, APPLIED_RESOURCE, INSTITUTION),
        activated_node_ids=(
            "career-technical-output",
            "career-applied-resource",
            "career-institutional-constraint",
        ),
        domains=("career",),
        supporting_evidence=(TECHNICAL_OUTPUT, APPLIED_RESOURCE, INSTITUTION),
        counter_evidence=(),
        trigger_strength="high",
        crossed_candidate_gate=True,
    )
    return evaluate_event_candidate(
        candidate_id="career-2018-2020-mechanical-design-specialization",
        event_type="career_specialization",
        window_start=WINDOW_START,
        window_end=NORMALIZED_EVENT_DATE,
        annual_trace=trace,
        root_level=RootLevel.STRONG_ROOT,
        completion_mode=CompletionMode.ACTIVATE_EXISTING,
        natal_evidence=(TECHNICAL_OUTPUT, APPLIED_RESOURCE, INSTITUTION),
        daiyun_evidence=(START_LUCK,),
        root_evidence=(TECHNICAL_OUTPUT, APPLIED_RESOURCE),
        source_citations=(
            SourceCitation(INPUT_PATH, 33, "藏干及十神完整列示"),
            SourceCitation(FEEDBACK_PATH, 17, "最近7年左右开始从事机箱厂设计、绘图、拆图工作"),
        ),
        supporting_evidence=(TECHNICAL_OUTPUT, APPLIED_RESOURCE, INSTITUTION),
        alternative_hypotheses=("仍属一般制造岗位而非职业专业化",),
        frozen_version="asof-prototype-v1-g7-oos",
    )


def _confirmed_entry() -> EventLedgerEntry:
    decision = _decision()
    assert decision.accepted and decision.candidate is not None
    candidate = replace(
        decision.candidate,
        verification_status=VerificationStatus.CONFIRMED,
        supporting_evidence=decision.candidate.supporting_evidence
        + (EvidenceRef(FEEDBACK_PATH, "事业反馈:最近7年左右", "开始从事机箱厂设计、绘图、拆图工作"),),
    )
    assessment = EventImpactAssessment(
        event_id=candidate.candidate_id,
        event_date=NORMALIZED_EVENT_DATE,
        event_type=candidate.event_type,
        root_level=candidate.root_level,
        completion_mode=candidate.completion_mode,
        system_suggested_impact=ImpactLevel.MAJOR,
        system_suggested_persistence=Persistence.CROSS_DAIYUN,
        system_suggested_scope=ImpactScope.PRIMARY_DOMAIN,
        state_value="从事机箱厂设计、绘图、拆图工作",
        opened_path_ids=("mechanical-design-specialization-realized",),
    )
    return EventLedgerEntry(candidate, assessment)


def _replay(as_of_date: date):
    return build_verified_state(
        AsOfRequest(CASE_ID, as_of_date),
        entries=(_confirmed_entry(),),
        daiyun_end=date(2029, 12, 31),
        current_center="机械制造技术岗位",
        reasonable_range=("一般制造岗位", "机械设计专业化"),
    )


def _synthetic_edges() -> tuple[WealthPropagationEdge, ...]:
    return (
        WealthPropagationEdge(
            edge_id="synthetic-promotion-to-income-capacity",
            source_event_type="promotion",
            target_state="稳定收入能力提高",
            required_conditions=("薪酬制度随职级调整",),
            delay_days=30,
            persistence=Persistence.CROSS_DAIYUN,
            falsifiers=("晋升不伴随收入变化",),
            verified=True,
        ),
        WealthPropagationEdge(
            edge_id="synthetic-entrepreneurship-to-risk-exposure",
            source_event_type="entrepreneurship",
            target_state="收入结构变化与资产风险暴露",
            required_conditions=("经营主体已实际运行",),
            delay_days=0,
            persistence=Persistence.SHORT_TERM,
            falsifiers=("未发生资金投入",),
            verified=True,
            short_term_days=365,
        ),
    )


def test_case_2027_builds_traceable_natal_graph_and_two_frozen_daiyun_stages() -> None:
    graph = _natal_graph()
    stages = _stages()

    assert {node.node_id for node in graph.capacity_nodes} == {
        "career-technical-output",
        "career-applied-resource",
        "career-institutional-constraint",
    }
    assert graph.feasible_paths[0].node_ids == (
        "career-technical-output",
        "career-applied-resource",
        "career-institutional-constraint",
    )
    assert [(stage.ganzhi, stage.start_date, stage.end_date) for stage in stages] == [
        ("己亥", date(2010, 1, 1), date(2019, 12, 31)),
        ("戊戌", date(2020, 1, 1), date(2029, 12, 31)),
    ]


def test_case_2027_career_specialization_crosses_the_frozen_double_evidence_gate() -> None:
    entry = _confirmed_entry()

    assert entry.candidate.verification_status is VerificationStatus.CONFIRMED
    assert entry.candidate.root_level is RootLevel.STRONG_ROOT
    assert entry.candidate.completion_mode is CompletionMode.ACTIVATE_EXISTING


def test_case_2027_three_cutoffs_never_turn_the_wealth_fact_into_a_career_event() -> None:
    before = _replay(date(2017, 12, 31))
    at_boundary = _replay(NORMALIZED_EVENT_DATE)
    after_house_sale_window = _replay(date(2021, 12, 31))

    assert before.verified_event_ids == ()
    assert at_boundary.verified_event_ids == ("career-2018-2020-mechanical-design-specialization",)
    assert after_house_sale_window.verified_event_ids == at_boundary.verified_event_ids
    assert before != at_boundary
    assert all("卖" not in state.value and "房" not in state.value for state in after_house_sale_window.reality_track.active_states)


def test_case_2027_relative_feedback_is_anchored_to_a_wide_normalization_window() -> None:
    entry = _confirmed_entry()

    assert FEEDBACK_DATE == date(2026, 6, 1)
    assert entry.candidate.window_start == WINDOW_START
    assert entry.candidate.window_end == entry.assessment.event_date == NORMALIZED_EVENT_DATE
    assert "最近7年左右" in entry.candidate.supporting_evidence[-1].locator
    assert "12月31日" not in entry.candidate.supporting_evidence[-1].excerpt


def test_case_2027_verified_state_and_unverified_hypothesis_are_physically_separate() -> None:
    decision = _decision()
    assert decision.candidate is not None
    assessment = EventImpactAssessment(
        event_id=decision.candidate.candidate_id,
        event_date=NORMALIZED_EVENT_DATE,
        event_type=decision.candidate.event_type,
        root_level=decision.candidate.root_level,
        completion_mode=decision.candidate.completion_mode,
        system_suggested_impact=ImpactLevel.MAJOR,
        system_suggested_persistence=Persistence.CROSS_DAIYUN,
        system_suggested_scope=ImpactScope.PRIMARY_DOMAIN,
        state_value="条件分支：形成机械设计专业化路径",
    )
    request = AsOfRequest(CASE_ID, date(2017, 12, 31))
    verified = _replay(request.as_of_date)
    hypothesis = admit_hypothesis_branch(
        request,
        candidate=decision.candidate,
        assessment=assessment,
        condition="若2018-2020形成机箱设计专业化路径",
        difference_from_verified="从一般制造岗位转为设计绘图专业岗位",
        changed_fundamentals=("职业技能中心",),
        changed_future_conclusions=("机械设计经验成为后续现实起点",),
        minimum_question="是否已稳定从事机箱设计、绘图、拆图？",
        falsifier="截至2020年底仍未从事相关设计工作",
    )

    assert hypothesis is not None
    assert hypothesis.candidate_id not in verified.verified_event_ids
    assert not hasattr(verified, "candidate_id")
    assert not hasattr(hypothesis, "reality_track")


def test_case_2027_house_sale_does_not_create_an_unregistered_wealth_edge() -> None:
    decision = propagate_career_event_to_wealth(
        event_id="career-2018-2020-mechanical-design-specialization",
        event_type="career_specialization",
        event_date=NORMALIZED_EVENT_DATE,
        verified_event=True,
        observed_conditions=("2021年前后卖掉婚房",),
        edges=_synthetic_edges(),
    )

    assert decision.changed is False
    assert decision.reason_code == "NO_EXPLICIT_EDGE"
    assert decision.state is None

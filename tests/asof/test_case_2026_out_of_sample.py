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


CASE_ID = "C-2026-026-坤-癸未甲寅壬戌丙午"
INPUT_PATH = f"cases/{CASE_ID}/input.md"
FEEDBACK_PATH = f"cases/{CASE_ID}/feedback.md"
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


OUTPUT = _chart("藏干.月支", "寅藏甲食神")
AUTHORITY = _chart("藏干.年支/日支/时支", "未、午藏己正官；戌藏戊七杀")
RESOURCE = _chart("藏干.日支", "戌藏辛正印")
CHART = _chart("四柱", "癸未 甲寅 壬戌 丙午")
START_LUCK = _chart("大运", "2008年起运，顺排；2018-2028丙辰")


def _natal_graph():
    nodes = (
        CapacityNode("career-output", "教学与知识输出", (OUTPUT,)),
        CapacityNode("career-authority", "制度职责承载", (AUTHORITY,)),
        CapacityNode("career-resource", "资质与组织承接", (RESOURCE,)),
    )
    path = PathRef(
        "education-to-establishment",
        "教学输出经资质与制度节点承接进入学校编制路径",
        tuple(node.node_id for node in nodes),
        (OUTPUT, AUTHORITY, RESOURCE),
    )
    return build_natal_capacity_graph(
        case_id=CASE_ID,
        capacity_nodes=nodes,
        structural_features=(OUTPUT, AUTHORITY, RESOURCE),
        vulnerabilities=(_chart("四柱及藏干十神", "财官并见，制度兑现仍须现实核验"),),
        feasible_paths=(path,),
        constraints=(_chart("大运", "路径兑现须经大运与年度候选门"),),
        chart_evidence=(CHART, START_LUCK),
        source_citations=(
            SourceCitation(INPUT_PATH, 25, "四柱：癸未、甲寅、壬戌、丙午"),
            SourceCitation(INPUT_PATH, 33, "藏干及十神完整列示"),
        ),
        competing_explanations=("教育相关工作但不进入编制",),
    )


def _stage():
    path_change = PathChange(
        "education-to-establishment",
        "丙辰运放大既有教育与制度承接路径，不读取现实履历",
        (START_LUCK, OUTPUT, AUTHORITY, RESOURCE),
    )
    relation = NatalRelation("career-authority", "大运信号作用于既有制度节点", (AUTHORITY,))
    return adapt_daiyun_segment(
        _Segment(2, "丙辰", (11, 21), (2018, 2028), "", []),
        amplified_paths=(path_change,),
        natal_relations=(relation,),
        domain_tendency="mixed",
        applicability_conditions=("仅用于2018-2027闭区间回放",),
    )


def _decision():
    trace = AnnualInteractionTrace(
        year=2020,
        liunian="庚子",
        dayun_ganzhi="丙辰",
        relations=(OUTPUT, AUTHORITY, RESOURCE),
        activated_node_ids=("career-output", "career-authority", "career-resource"),
        domains=("career",),
        supporting_evidence=(OUTPUT, AUTHORITY, RESOURCE),
        counter_evidence=(),
        trigger_strength="high",
        crossed_candidate_gate=True,
    )
    return evaluate_event_candidate(
        candidate_id="career-2020-teacher-establishment",
        event_type="career_entry",
        window_start=date(2020, 1, 1),
        window_end=NORMALIZED_EVENT_DATE,
        annual_trace=trace,
        root_level=RootLevel.STRONG_ROOT,
        completion_mode=CompletionMode.ACTIVATE_EXISTING,
        natal_evidence=(OUTPUT, AUTHORITY, RESOURCE),
        daiyun_evidence=(START_LUCK,),
        root_evidence=(OUTPUT, AUTHORITY, RESOURCE),
        source_citations=(
            SourceCitation(INPUT_PATH, 33, "藏干及十神完整列示"),
            SourceCitation(FEEDBACK_PATH, 15, "2020年考入乡镇中学，成为在编教师"),
        ),
        supporting_evidence=(OUTPUT, AUTHORITY, RESOURCE),
        alternative_hypotheses=("进入学校但不具备编制身份",),
        frozen_version="asof-prototype-v1-g7-oos",
    )


def _confirmed_entry() -> EventLedgerEntry:
    decision = _decision()
    assert decision.accepted and decision.candidate is not None
    candidate = replace(
        decision.candidate,
        verification_status=VerificationStatus.CONFIRMED,
        supporting_evidence=decision.candidate.supporting_evidence
        + (EvidenceRef(FEEDBACK_PATH, "事业反馈:2020", "2020年考入青县一乡镇中学，成为在编教师"),),
    )
    assessment = EventImpactAssessment(
        event_id=candidate.candidate_id,
        event_date=NORMALIZED_EVENT_DATE,
        event_type=candidate.event_type,
        root_level=candidate.root_level,
        completion_mode=candidate.completion_mode,
        system_suggested_impact=ImpactLevel.TURNING_POINT,
        system_suggested_persistence=Persistence.CROSS_DAIYUN,
        system_suggested_scope=ImpactScope.PRIMARY_DOMAIN,
        state_value="考入乡镇中学并成为在编教师",
        opened_path_ids=("education-establishment-realized",),
    )
    return EventLedgerEntry(candidate, assessment)


def _replay(as_of_date: date):
    return build_verified_state(
        AsOfRequest(CASE_ID, as_of_date),
        entries=(_confirmed_entry(),),
        daiyun_end=date(2027, 12, 31),
        current_center="学校教育职业路径",
        reasonable_range=("学校教学", "在编教师"),
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


def test_case_2026_builds_traceable_natal_graph_and_frozen_daiyun_stage() -> None:
    graph = _natal_graph()
    stage = _stage()

    assert {node.node_id for node in graph.capacity_nodes} == {
        "career-output",
        "career-authority",
        "career-resource",
    }
    assert graph.feasible_paths[0].node_ids == (
        "career-output",
        "career-authority",
        "career-resource",
    )
    assert (stage.ganzhi, stage.start_date, stage.end_date) == (
        "丙辰",
        date(2018, 1, 1),
        date(2027, 12, 31),
    )


def test_case_2026_teacher_establishment_crosses_the_frozen_double_evidence_gate() -> None:
    entry = _confirmed_entry()

    assert entry.candidate.verification_status is VerificationStatus.CONFIRMED
    assert entry.candidate.root_level is RootLevel.STRONG_ROOT
    assert entry.candidate.completion_mode is CompletionMode.ACTIVATE_EXISTING


def test_case_2026_three_cutoffs_never_leak_or_invent_later_feedback() -> None:
    before = _replay(date(2019, 12, 31))
    at_boundary = _replay(NORMALIZED_EVENT_DATE)
    later = _replay(date(2026, 5, 31))

    assert before.verified_event_ids == ()
    assert at_boundary.verified_event_ids == ("career-2020-teacher-establishment",)
    assert later.verified_event_ids == at_boundary.verified_event_ids
    assert before != at_boundary
    assert tuple(state.value for state in later.reality_track.active_states) == (
        "考入乡镇中学并成为在编教师",
    )


def test_case_2026_year_end_is_a_normalization_boundary_not_a_claimed_fact_date() -> None:
    entry = _confirmed_entry()

    assert entry.candidate.window_start == date(2020, 1, 1)
    assert entry.candidate.window_end == entry.assessment.event_date == NORMALIZED_EVENT_DATE
    assert "2020年" in entry.candidate.supporting_evidence[-1].excerpt
    assert "12月31日" not in entry.candidate.supporting_evidence[-1].excerpt


def test_case_2026_verified_state_and_unverified_hypothesis_are_physically_separate() -> None:
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
        state_value="条件分支：进入学校编制",
    )
    request = AsOfRequest(CASE_ID, date(2019, 12, 31))
    verified = _replay(request.as_of_date)
    hypothesis = admit_hypothesis_branch(
        request,
        candidate=decision.candidate,
        assessment=assessment,
        condition="若2020年正式进入学校编制",
        difference_from_verified="从既有职业位置转入制度化学校岗位",
        changed_fundamentals=("职业制度身份",),
        changed_future_conclusions=("学校编制成为后续现实起点",),
        minimum_question="是否已正式成为在编教师？",
        falsifier="截至2020年底仍未进入学校编制",
    )

    assert hypothesis is not None
    assert hypothesis.candidate_id not in verified.verified_event_ids
    assert not hasattr(verified, "candidate_id")
    assert not hasattr(hypothesis, "reality_track")


def test_case_2026_property_losses_do_not_invent_a_career_to_wealth_edge() -> None:
    decision = propagate_career_event_to_wealth(
        event_id="career-2020-teacher-establishment",
        event_type="career_entry",
        event_date=NORMALIZED_EVENT_DATE,
        verified_event=True,
        observed_conditions=("2025年手机丢失", "2026年戒指丢失"),
        edges=_synthetic_edges(),
    )

    assert decision.changed is False
    assert decision.reason_code == "NO_EXPLICIT_EDGE"
    assert decision.state is None

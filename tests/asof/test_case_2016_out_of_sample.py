from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date
from pathlib import Path

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
from engine.predicates.palace import get_shishen


CASE_ID = "C-2026-016-坤-甲子丙子丙戌戊子"
INPUT_PATH = f"cases/{CASE_ID}/input.md"
FEEDBACK_PATH = f"cases/{CASE_ID}/feedback.md"
ENGINE_PATH = "engine/predicates/palace.py"
SERVICE_EVENT_DATE = date(2012, 12, 31)
ESTABLISHMENT_EVENT_DATE = date(2020, 12, 31)


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


def _derived(hidden_stem: str, locator: str) -> EvidenceRef:
    ten_god = get_shishen(hidden_stem, "丙")
    return EvidenceRef(
        ENGINE_PATH,
        f"get_shishen(藏干.{locator}.{hidden_stem}, 日主.丙)",
        f"由案例原文藏干{hidden_stem}经冻结引擎派生为{ten_god}；非原文手写事实",
    )


AUTHORITY = _derived("癸", "年支/月支/时支")
OUTPUT = _derived("戊", "日支")
WEALTH = _derived("辛", "日支")
PEER = _derived("丁", "日支")
RESOURCE = _chart("四柱.年干", "甲为偏印（人读排盘主星显式列示）")
CHART = _chart("四柱", "甲子 丙子 丙戌 戊子")
START_LUCK = _chart("大运", "1988年起运，逆排")


def _natal_graph():
    nodes = (
        CapacityNode("career-output", "服务与教学输出承载", (OUTPUT,)),
        CapacityNode("career-authority", "制度职业承载", (AUTHORITY,)),
        CapacityNode("career-resource", "学习与资质承接", (RESOURCE,)),
        CapacityNode("career-wealth", "会计与经营接口", (WEALTH,)),
    )
    paths = (
        PathRef(
            "service-transition",
            "财星接口经食神输出进入学生服务经营路径",
            ("career-wealth", "career-output"),
            (WEALTH, OUTPUT),
        ),
        PathRef(
            "service-to-establishment",
            "服务与教学输出经印星和官星承接进入教师编制路径",
            ("career-output", "career-resource", "career-authority"),
            (OUTPUT, RESOURCE, AUTHORITY),
        ),
    )
    return build_natal_capacity_graph(
        case_id=CASE_ID,
        capacity_nodes=nodes,
        structural_features=(AUTHORITY, OUTPUT, WEALTH, PEER, RESOURCE),
        vulnerabilities=(_chart("四柱", "官星虽多但现实制度身份仍须事件核验"),),
        feasible_paths=paths,
        constraints=(_chart("大运", "路径兑现须经大运与年度候选门"),),
        chart_evidence=(CHART, START_LUCK),
        source_citations=(
            SourceCitation(INPUT_PATH, 23, "四柱：甲子、丙子、丙戌、戊子"),
            SourceCitation(INPUT_PATH, 31, "藏干干名、气类与力量显式列示"),
            SourceCitation(ENGINE_PATH, 148, "get_shishen 依据日主与目标天干确定十神"),
        ),
        competing_explanations=("服务行业延续但不进入教师编制",),
    )


def _stages():
    wealth_change = PathChange(
        "service-transition",
        "癸酉运放大财星接口与服务输出路径，不读取现实履历",
        (START_LUCK, WEALTH, OUTPUT),
    )
    establishment_change = PathChange(
        "service-to-establishment",
        "壬申运放大既有教学、资质与制度承接路径，不读取现实履历",
        (START_LUCK, OUTPUT, RESOURCE, AUTHORITY),
    )
    return (
        adapt_daiyun_segment(
            _Segment(3, "癸酉", (25, 35), (2008, 2018), "", []),
            opened_paths=(wealth_change,),
            natal_relations=(NatalRelation("career-wealth", "大运作用于既有财星接口", (WEALTH,)),),
            domain_tendency="mixed",
            applicability_conditions=("仅用于2008-2017闭区间回放",),
        ),
        adapt_daiyun_segment(
            _Segment(4, "壬申", (35, 45), (2018, 2028), "", []),
            amplified_paths=(establishment_change,),
            natal_relations=(NatalRelation("career-authority", "大运作用于既有制度节点", (AUTHORITY,)),),
            domain_tendency="mixed",
            applicability_conditions=("仅用于2018-2027闭区间回放",),
        ),
    )


def _decision(*, event: str):
    if event == "service":
        event_date = SERVICE_EVENT_DATE
        trace = AnnualInteractionTrace(
            year=2012,
            liunian="壬辰",
            dayun_ganzhi="癸酉",
            relations=(WEALTH, OUTPUT),
            activated_node_ids=("career-wealth", "career-output"),
            domains=("career",),
            supporting_evidence=(WEALTH, OUTPUT),
            counter_evidence=(),
            trigger_strength="high",
            crossed_candidate_gate=True,
        )
        return evaluate_event_candidate(
            candidate_id="career-2012-student-service-center",
            event_type="entrepreneurship",
            window_start=date(2012, 1, 1),
            window_end=event_date,
            annual_trace=trace,
            root_level=RootLevel.STRONG_ROOT,
            completion_mode=CompletionMode.ACTIVATE_EXISTING,
            natal_evidence=(WEALTH, OUTPUT),
            daiyun_evidence=(START_LUCK,),
            root_evidence=(WEALTH, OUTPUT),
            source_citations=(
                SourceCitation(INPUT_PATH, 31, "辛、戊藏干由原文显式列示"),
                SourceCitation(ENGINE_PATH, 148, "藏干十神由冻结引擎确定"),
                SourceCitation(FEEDBACK_PATH, 20, "2012年换行业，开学生服务中心"),
            ),
            supporting_evidence=(WEALTH, OUTPUT),
            alternative_hypotheses=("只换到学生服务行业但未实际经营",),
            frozen_version="asof-prototype-v1-g7-oos-derived-ten-gods",
        )

    trace = AnnualInteractionTrace(
        year=2020,
        liunian="庚子",
        dayun_ganzhi="壬申",
        relations=(OUTPUT, RESOURCE, AUTHORITY),
        activated_node_ids=("career-output", "career-resource", "career-authority"),
        domains=("career",),
        supporting_evidence=(OUTPUT, RESOURCE, AUTHORITY),
        counter_evidence=(),
        trigger_strength="high",
        crossed_candidate_gate=True,
    )
    return evaluate_event_candidate(
        candidate_id="career-2020-teacher-establishment",
        event_type="career_entry",
        window_start=date(2020, 1, 1),
        window_end=ESTABLISHMENT_EVENT_DATE,
        annual_trace=trace,
        root_level=RootLevel.STRONG_ROOT,
        completion_mode=CompletionMode.ACTIVATE_EXISTING,
        natal_evidence=(OUTPUT, RESOURCE, AUTHORITY),
        daiyun_evidence=(START_LUCK,),
        root_evidence=(OUTPUT, RESOURCE, AUTHORITY),
        source_citations=(
            SourceCitation(INPUT_PATH, 31, "癸、戊藏干由原文显式列示"),
            SourceCitation(ENGINE_PATH, 148, "藏干十神由冻结引擎确定"),
            SourceCitation(FEEDBACK_PATH, 23, "2020年成功上岸教师编制"),
        ),
        supporting_evidence=(OUTPUT, RESOURCE, AUTHORITY),
        alternative_hypotheses=("劳务派遣教师身份延续但未入编",),
        frozen_version="asof-prototype-v1-g7-oos-derived-ten-gods",
    )


def _confirmed_entry(*, event: str) -> EventLedgerEntry:
    decision = _decision(event=event)
    assert decision.accepted and decision.candidate is not None
    candidate = replace(decision.candidate, verification_status=VerificationStatus.CONFIRMED)
    is_service = event == "service"
    assessment = EventImpactAssessment(
        event_id=candidate.candidate_id,
        event_date=SERVICE_EVENT_DATE if is_service else ESTABLISHMENT_EVENT_DATE,
        event_type=candidate.event_type,
        root_level=candidate.root_level,
        completion_mode=candidate.completion_mode,
        system_suggested_impact=ImpactLevel.MAJOR if is_service else ImpactLevel.TURNING_POINT,
        system_suggested_persistence=Persistence.CROSS_DAIYUN,
        system_suggested_scope=ImpactScope.PRIMARY_DOMAIN,
        state_value="换行业并开学生服务中心" if is_service else "成功进入教师编制",
        opened_path_ids=("student-service-realized",) if is_service else ("teacher-establishment-realized",),
    )
    return EventLedgerEntry(candidate, assessment)


def _replay(as_of_date: date):
    return build_verified_state(
        AsOfRequest(CASE_ID, as_of_date),
        entries=(_confirmed_entry(event="service"), _confirmed_entry(event="establishment")),
        daiyun_end=date(2027, 12, 31),
        current_center="服务到教师编制的职业路径",
        reasonable_range=("学生服务经营", "教师岗位", "教师编制"),
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


def test_case_2016_derives_hidden_stem_ten_gods_with_frozen_engine_and_labels_provenance() -> None:
    source = Path(INPUT_PATH).read_text(encoding="utf-8")

    assert "日柱: 丙戌" in source
    assert "- {干: 癸" in source and "- {干: 戊" in source
    assert {stem: get_shishen(stem, "丙") for stem in ("癸", "戊", "辛", "丁")} == {
        "癸": "正官",
        "戊": "食神",
        "辛": "正财",
        "丁": "劫财",
    }
    assert all(ref.source == ENGINE_PATH for ref in (AUTHORITY, OUTPUT, WEALTH, PEER))
    assert all("非原文手写事实" in ref.excerpt for ref in (AUTHORITY, OUTPUT, WEALTH, PEER))


def test_case_2016_builds_traceable_natal_graph_and_two_frozen_daiyun_stages() -> None:
    graph = _natal_graph()
    stages = _stages()

    assert {node.node_id for node in graph.capacity_nodes} == {
        "career-output",
        "career-authority",
        "career-resource",
        "career-wealth",
    }
    assert tuple((stage.ganzhi, stage.start_date, stage.end_date) for stage in stages) == (
        ("癸酉", date(2008, 1, 1), date(2017, 12, 31)),
        ("壬申", date(2018, 1, 1), date(2027, 12, 31)),
    )


def test_case_2016_feedback_events_cross_the_double_evidence_gate() -> None:
    service = _confirmed_entry(event="service")
    establishment = _confirmed_entry(event="establishment")

    assert service.candidate.verification_status is VerificationStatus.CONFIRMED
    assert establishment.candidate.verification_status is VerificationStatus.CONFIRMED
    assert service.candidate.root_level is establishment.candidate.root_level is RootLevel.STRONG_ROOT


def test_case_2016_three_cutoffs_never_leak_later_feedback() -> None:
    before = _replay(date(2011, 12, 31))
    after_service = _replay(SERVICE_EVENT_DATE)
    after_establishment = _replay(ESTABLISHMENT_EVENT_DATE)

    assert before.verified_event_ids == ()
    assert after_service.verified_event_ids == ("career-2012-student-service-center",)
    assert after_establishment.verified_event_ids == (
        "career-2012-student-service-center",
        "career-2020-teacher-establishment",
    )


def test_case_2016_year_end_dates_are_normalization_boundaries_not_claimed_fact_dates() -> None:
    service = _confirmed_entry(event="service")
    establishment = _confirmed_entry(event="establishment")

    assert service.assessment.event_date == SERVICE_EVENT_DATE
    assert establishment.assessment.event_date == ESTABLISHMENT_EVENT_DATE
    assert "12月31日" not in service.candidate.source_citations[-1].excerpt
    assert "12月31日" not in establishment.candidate.source_citations[-1].excerpt


def test_case_2016_verified_state_and_unverified_hypothesis_are_physically_separate() -> None:
    decision = _decision(event="establishment")
    assert decision.candidate is not None
    assessment = EventImpactAssessment(
        event_id=decision.candidate.candidate_id,
        event_date=ESTABLISHMENT_EVENT_DATE,
        event_type=decision.candidate.event_type,
        root_level=decision.candidate.root_level,
        completion_mode=decision.candidate.completion_mode,
        system_suggested_impact=ImpactLevel.MAJOR,
        system_suggested_persistence=Persistence.CROSS_DAIYUN,
        system_suggested_scope=ImpactScope.PRIMARY_DOMAIN,
        state_value="条件分支：成功进入教师编制",
    )
    request = AsOfRequest(CASE_ID, date(2019, 12, 31))
    verified = _replay(request.as_of_date)
    hypothesis = admit_hypothesis_branch(
        request,
        candidate=decision.candidate,
        assessment=assessment,
        condition="若2020年成功进入教师编制",
        difference_from_verified="从劳务派遣教师转为正式编制",
        changed_fundamentals=("职业制度身份",),
        changed_future_conclusions=("教师编制成为后续现实起点",),
        minimum_question="是否已正式进入教师编制？",
        falsifier="截至2020年底仍未进入教师编制",
    )

    assert hypothesis is not None
    assert hypothesis.candidate_id not in verified.verified_event_ids
    assert not hasattr(verified, "candidate_id")
    assert not hasattr(hypothesis, "reality_track")


def test_case_2016_wealth_abstains_without_verified_propagation_conditions() -> None:
    decision = propagate_career_event_to_wealth(
        event_id="career-2012-student-service-center",
        event_type="entrepreneurship",
        event_date=SERVICE_EVENT_DATE,
        verified_event=True,
        observed_conditions=("2012年换行业，开学生服务中心",),
        edges=_synthetic_edges(),
    )

    assert decision.changed is False
    assert decision.reason_code == "PROPAGATION_CONDITIONS_NOT_MET"
    assert decision.state is None

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from engine.asof.career_state_builder import (
    CAREER_IMPACT_SUGGESTION_SCHEMA_VERSION,
    CareerFundamentalAdjudication,
    CareerImpactAdjudication,
    CareerImpactSuggestion,
)
from engine.asof.consultation_freeze import (
    FREEZE_PACKAGE_SCHEMA_VERSION,
    VERIFICATION_SCHEMA_VERSION,
    CareerBlindDraft,
    CareerFreezePackage,
    FrozenCareerEvent,
    FrozenCareerFundamental,
    VerificationInput,
    VerificationVerdict,
    compute_freeze_package_sha256,
)
from engine.asof.daiyun_context import NatalRelation, PathChange, adapt_daiyun_segment
from engine.asof.event_candidate import (
    AnnualInteractionTrace,
    CompletionMode,
    RootLevel,
    evaluate_event_candidate,
)
from engine.asof.natal_capacity import (
    CapacityNode,
    EvidenceRef,
    PathRef,
    SourceCitation,
    build_natal_capacity_graph,
)
from engine.asof.reality_translation import FrozenLandingSet, LandingPoint
from engine.asof.session_contract import (
    BLIND_INPUT_SCHEMA_VERSION,
    SESSION_SCHEMA_VERSION,
    BlindChartInput,
    ChartGender,
    ChartSource,
    ConsultationState,
    DaiyunInput,
    FourPillarsInput,
    PillarInput,
    SessionIdentity,
    compute_blind_input_sha256,
)
from engine.asof.session_runner import run_career_session
from engine.asof.state_ledger import ImpactLevel, ImpactScope, Persistence


CASE_ID = "C-2026-024-坤-己巳壬申辛亥壬辰"
INPUT_PATH = f"cases/{CASE_ID}/input.md"
TEACHER_ID = "career-2014-2015-teacher-entry"
PRINCIPAL_ID = "career-2024-2025-school-principal"


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


def _blind_input() -> BlindChartInput:
    return BlindChartInput(
        BLIND_INPUT_SCHEMA_VERSION,
        ChartSource.WENZHEN_STRUCTURED_V1,
        ChartGender.KUN,
        FourPillarsInput(
            PillarInput("己", "巳", ("丙", "庚", "戊"), "死"),
            PillarInput("壬", "申", ("庚", "壬", "戊"), "帝旺"),
            PillarInput("辛", "亥", ("壬", "甲"), "沐浴"),
            PillarInput("壬", "辰", ("戊", "乙", "癸"), "墓"),
        ),
        (
            DaiyunInput(1, "癸", "酉", date(1996, 1, 1), date(2006, 1, 1)),
            DaiyunInput(2, "甲", "戌", date(2006, 1, 1), date(2016, 1, 1)),
            DaiyunInput(3, "乙", "亥", date(2016, 1, 1), date(2026, 1, 1)),
        ),
    )


def _build_blind_draft(as_of_date: date) -> CareerBlindDraft:
    output = _chart("四柱明细.月柱/时柱.十神", "月柱壬伤官；时柱壬伤官")
    authority = _chart("四柱明细.年柱.藏干十神", "巳藏正官、劫财、正印")
    support = _chart("四柱明细.藏干十神", "巳、申、辰均见印星")
    chart = _chart("四柱", "己巳 壬申 辛亥 壬辰")
    luck = _chart("大运.起运年", "1996，顺行")
    nodes = (
        CapacityNode("career-output", "语言与知识输出", (output,)),
        CapacityNode("career-authority", "规则与管理职责", (authority,)),
        CapacityNode("career-support", "资质与组织承接", (support,)),
    )
    graph = build_natal_capacity_graph(
        case_id=CASE_ID,
        capacity_nodes=nodes,
        structural_features=(output, authority, support),
        vulnerabilities=(_chart("四柱明细", "伤官两透，官星仅藏"),),
        feasible_paths=(
            PathRef(
                "education-to-management",
                "教育输出经组织承接进入基层管理",
                tuple(node.node_id for node in nodes),
                (output, authority, support),
            ),
        ),
        constraints=(_chart("四柱明细", "管理落点须由官印与组织环境承接"),),
        chart_evidence=(chart, luck),
        source_citations=(
            SourceCitation(INPUT_PATH, 41, "年柱十神：偏印"),
            SourceCitation(INPUT_PATH, 50, "月柱十神：伤官"),
        ),
        competing_explanations=("专业教学而不进入管理",),
    )
    relation = NatalRelation("career-output", "大运信号作用于既有输出节点", (output,))
    stages = (
        adapt_daiyun_segment(
            _Segment(2, "甲戌", (18, 28), (2006, 2016), "", []),
            opened_paths=(
                PathChange(
                    "education-to-management",
                    "甲戌运开放教育职业入口",
                    (luck, output, support),
                ),
            ),
            natal_relations=(relation,),
            domain_tendency="open",
            applicability_conditions=("仅用于2006-2015闭区间回放",),
        ),
        adapt_daiyun_segment(
            _Segment(3, "乙亥", (28, 38), (2016, 2026), "", []),
            amplified_paths=(
                PathChange(
                    "education-to-management",
                    "乙亥运放大既有教育输出路径",
                    (luck, output, authority),
                ),
            ),
            natal_relations=(relation,),
            domain_tendency="mixed",
            applicability_conditions=("仅用于2016-2025闭区间回放",),
        ),
    )
    assert graph.feasible_paths[0].path_id == "education-to-management"
    assert tuple(stage.end_date for stage in stages) == (date(2015, 12, 31), date(2025, 12, 31))

    fundamental = FrozenCareerFundamental(
        "career-education-system-baseline",
        date(2006, 1, 1),
        as_of_date,
        date(2006, 1, 1) + (as_of_date - date(2006, 1, 1)) // 2,
        "教育与知识输出路径由组织环境承接",
        ("专业教学", "教育系统基层管理"),
        "语言与知识输出型专业岗位",
        ("长期不承担教育、知识输出或组织职责",),
    )

    def event(
        candidate_id: str,
        event_type: str,
        year: int,
        liunian: str,
        dayun: str,
        window_start: date,
        window_end: date,
        center: LandingPoint,
        alternative: LandingPoint,
        falsifier: str,
    ) -> FrozenCareerEvent:
        trace = AnnualInteractionTrace(
            year,
            liunian,
            dayun,
            (output, authority, support),
            ("career-output", "career-authority", "career-support"),
            ("career",),
            (output, authority, support),
            (),
            "high",
            True,
        )
        decision = evaluate_event_candidate(
            candidate_id=candidate_id,
            event_type=event_type,
            window_start=window_start,
            window_end=window_end,
            annual_trace=trace,
            root_level=RootLevel.STRONG_ROOT,
            completion_mode=CompletionMode.ACTIVATE_EXISTING,
            natal_evidence=(output, authority, support),
            daiyun_evidence=(luck,),
            root_evidence=(output, authority, support),
            source_citations=(
                SourceCitation(INPUT_PATH, 41, "年柱十神：偏印"),
                SourceCitation(INPUT_PATH, 50, "月柱十神：伤官"),
            ),
            supporting_evidence=(output, authority, support),
            alternative_hypotheses=(alternative.name,),
            frozen_version="asof-prototype-v1-unit8",
        )
        assert decision.accepted and decision.candidate is not None
        return FrozenCareerEvent(
            decision.candidate,
            FrozenLandingSet(
                event_type,
                center,
                (alternative,),
                "仅有短期或名义变化视为弱命中",
                (falsifier,),
                ("财富变化不属于本事业落点",),
                "landing-v1-unit8-blind",
            ),
        )

    events: list[FrozenCareerEvent] = []
    if as_of_date >= date(2015, 12, 31):
        events.append(
            event(
                TEACHER_ID,
                "career_entry",
                2015,
                "乙未",
                "甲戌",
                date(2014, 1, 1),
                date(2015, 12, 31),
                LandingPoint("教育系统内的岗位承接", "career", "career_entry"),
                LandingPoint("语言与知识输出型稳定岗位", "career", "career_entry"),
                "截止窗口末仍未进入稳定职业",
            )
        )
    if as_of_date >= date(2025, 12, 31):
        events.append(
            event(
                PRINCIPAL_ID,
                "promotion",
                2025,
                "乙巳",
                "乙亥",
                date(2024, 1, 1),
                date(2025, 12, 31),
                LandingPoint("教育系统内的管理职责提升", "career", "authority_up"),
                LandingPoint("教育系统内职责扩大但职级未变", "career", "authority_up"),
                "截止窗口末职责层级未提升",
            )
        )
    return CareerBlindDraft((fundamental,), tuple(events))


def _expected_package(as_of_date: date, session_id: str, draft: CareerBlindDraft) -> CareerFreezePackage:
    identity = SessionIdentity(SESSION_SCHEMA_VERSION, CASE_ID, as_of_date, session_id)
    return CareerFreezePackage(
        FREEZE_PACKAGE_SCHEMA_VERSION,
        identity,
        compute_blind_input_sha256(_blind_input()),
        draft.fundamentals,
        draft.events,
    )


def _build_verification_from_feedback(
    package: CareerFreezePackage,
    as_of_date: date,
) -> tuple[
    tuple[VerificationInput, ...],
    tuple[CareerImpactSuggestion, ...],
    tuple[CareerImpactAdjudication, ...],
    CareerFundamentalAdjudication,
]:
    feedback_path = f"cases/{CASE_ID}/feedback.md"
    digest = compute_freeze_package_sha256(package)
    feedback_excerpt_by_id = {
        TEACHER_ID: "2014-2015 年入职小学语文教师，实际教英语",
        PRINCIPAL_ID: "2024-2025 年升职为校长",
    }
    values = {
        TEACHER_ID: (
            date(2015, 12, 31),
            ImpactLevel.MAJOR,
            "入职小学教师，实际教英语",
            (),
        ),
        PRINCIPAL_ID: (
            date(2025, 12, 31),
            ImpactLevel.TURNING_POINT,
            "升职为校长",
            ("education-management-realized",),
        ),
    }
    verifications: list[VerificationInput] = []
    suggestions: list[CareerImpactSuggestion] = []
    adjudications: list[CareerImpactAdjudication] = []
    for frozen_event in package.events:
        item_id = frozen_event.candidate.candidate_id
        event_date, impact, state_value, opened_paths = values[item_id]
        excerpt = feedback_excerpt_by_id[item_id]
        taxonomy_evidence = (f"{feedback_path}: {excerpt}",)
        verifications.append(
            VerificationInput(
                VERIFICATION_SCHEMA_VERSION,
                digest,
                item_id,
                VerificationVerdict.CONFIRMED,
                frozen_event.landing_set.center,
                None,
                taxonomy_evidence,
            )
        )
        suggestions.append(
            CareerImpactSuggestion(
                schema_version=CAREER_IMPACT_SUGGESTION_SCHEMA_VERSION,
                freeze_package_sha256=digest,
                item_id=item_id,
                event_date=event_date,
                suggested_impact=impact,
                suggested_persistence=Persistence.CROSS_DAIYUN,
                suggested_scope=ImpactScope.PRIMARY_DOMAIN,
                suggested_short_term_until=None,
                state_value=state_value,
                opened_path_ids=opened_paths,
                closed_path_ids=(),
            )
        )
        adjudications.append(
            CareerImpactAdjudication(
                digest,
                item_id,
                impact,
                Persistence.CROSS_DAIYUN,
                ImpactScope.PRIMARY_DOMAIN,
                None,
                "命理师依据后置核验记录确认现实影响",
                "",
                "",
                (),
                (),
                "",
                "",
            )
        )
    assert all(item.event_date <= as_of_date for item in suggestions)
    fundamental = CareerFundamentalAdjudication(
        digest,
        "career-education-system-baseline",
        "核验后选择最符合截止日现实的冻结基本面",
    )
    return tuple(verifications), tuple(suggestions), tuple(adjudications), fundamental


def test_unit8_cutoff_2013_has_no_blind_or_verified_events() -> None:
    as_of_date = date(2013, 12, 31)
    session_id = "S-20131231T000000Z-00000001"
    draft = _build_blind_draft(as_of_date)
    package = _expected_package(as_of_date, session_id, draft)
    verifications, suggestions, adjudications, fundamental = _build_verification_from_feedback(package, as_of_date)
    result = run_career_session(
        session_schema_version=SESSION_SCHEMA_VERSION,
        case_id=CASE_ID,
        as_of_date=as_of_date,
        session_id=session_id,
        blind_input=_blind_input(),
        draft=draft,
        verifications=verifications,
        suggestions=suggestions,
        impact_adjudications=adjudications,
        fundamental_adjudication=fundamental,
        daiyun_end=date(2015, 12, 31),
        career_candidates=None,
        wealth_bindings=None,
    )
    assert result.freeze_package.events == ()
    assert result.state_result.verified_state.verified_event_ids == ()
    assert result.final_envelope.state is ConsultationState.STATE_BUILT
    assert result.projection is None


def test_unit8_cutoff_2015_contains_only_teacher_entry() -> None:
    as_of_date = date(2015, 12, 31)
    session_id = "S-20151231T000000Z-00000002"
    draft = _build_blind_draft(as_of_date)
    package = _expected_package(as_of_date, session_id, draft)
    verifications, suggestions, adjudications, fundamental = _build_verification_from_feedback(package, as_of_date)
    result = run_career_session(
        session_schema_version=SESSION_SCHEMA_VERSION,
        case_id=CASE_ID,
        as_of_date=as_of_date,
        session_id=session_id,
        blind_input=_blind_input(),
        draft=draft,
        verifications=verifications,
        suggestions=suggestions,
        impact_adjudications=adjudications,
        fundamental_adjudication=fundamental,
        daiyun_end=date(2015, 12, 31),
        career_candidates=None,
        wealth_bindings=None,
    )
    expected = (TEACHER_ID,)
    assert tuple(item.candidate.candidate_id for item in result.freeze_package.events) == expected
    assert result.state_result.verified_state.verified_event_ids == expected
    assert result.final_envelope.state is ConsultationState.STATE_BUILT
    assert result.projection is None


def test_unit8_cutoff_2025_contains_teacher_entry_and_principal_promotion() -> None:
    as_of_date = date(2025, 12, 31)
    session_id = "S-20251231T000000Z-00000003"
    draft = _build_blind_draft(as_of_date)
    package = _expected_package(as_of_date, session_id, draft)
    verifications, suggestions, adjudications, fundamental = _build_verification_from_feedback(package, as_of_date)
    result = run_career_session(
        session_schema_version=SESSION_SCHEMA_VERSION,
        case_id=CASE_ID,
        as_of_date=as_of_date,
        session_id=session_id,
        blind_input=_blind_input(),
        draft=draft,
        verifications=verifications,
        suggestions=suggestions,
        impact_adjudications=adjudications,
        fundamental_adjudication=fundamental,
        daiyun_end=date(2025, 12, 31),
        career_candidates=None,
        wealth_bindings=None,
    )
    expected = (TEACHER_ID, PRINCIPAL_ID)
    assert tuple(item.candidate.candidate_id for item in result.freeze_package.events) == expected
    assert result.state_result.verified_state.verified_event_ids == expected
    assert result.final_envelope.state is ConsultationState.STATE_BUILT
    assert result.projection is None

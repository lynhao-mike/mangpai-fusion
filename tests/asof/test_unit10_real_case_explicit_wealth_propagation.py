from __future__ import annotations

import ast
from copy import deepcopy
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from engine.asof import SourceCitation
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
from engine.asof.event_candidate import (
    AnnualInteractionTrace,
    CompletionMode,
    RootLevel,
    VerificationStatus,
    evaluate_event_candidate,
)
from engine.asof.future_projection import (
    CareerFutureCandidate,
    WealthEventBinding,
    project_future_from_state,
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
from engine.asof.wealth_propagation import WealthPropagationEdge
from tests.asof.test_unit8_real_case_blind_verification import (
    _chart as unit8_chart,
)


CASE_ID = "C-2026-RF000475-坤-戊辰辛酉己巳乙丑"
INPUT_PATH = f"cases/{CASE_ID}/input.md"
FEEDBACK_PATH = f"cases/{CASE_ID}/feedback.md"
AS_OF_DATE = date(2023, 12, 31)
SESSION_ID = "S-20231231T000000Z-00000010"
EVENT_2014 = "career-2014-liked-professional-low-pay"
EVENT_2017 = "career-2017-left-for-lower-pay"
EVENT_2018 = "career-2018-state-owned-double-pay"
EVENT_2023 = "career-2023-forced-promotion-raise"
CONFIRMED_IDS = (EVENT_2014, EVENT_2017, EVENT_2018, EVENT_2023)
REAL_EDGE_ID = "real-2023-promotion-role-change-to-pay-raise"
REAL_REQUIRED_CONDITIONS = ("升岗级", "换岗位", "加了工资")
REAL_FALSIFIER = "未加工资"
FUTURE_CANDIDATE_ID = "career-future-from-verified-2023-state"

REAL_EDGE = WealthPropagationEdge(
    edge_id=REAL_EDGE_ID,
    source_event_type="promotion",
    target_state="加了工资",
    required_conditions=REAL_REQUIRED_CONDITIONS,
    delay_days=0,
    persistence=Persistence.INSTANT,
    falsifiers=(REAL_FALSIFIER,),
    verified=True,
)


@dataclass(frozen=True)
class _Segment:
    seq: int
    ganzhi: str
    age_range: tuple[int, int]
    year_range: tuple[int, int]
    feature: str
    typical_domains: list[str]


def _evidence(locator: str, excerpt: str):
    base = unit8_chart(INPUT_PATH, excerpt)
    return type(base)(INPUT_PATH, locator, excerpt)


def _blind_input() -> BlindChartInput:
    return BlindChartInput(
        BLIND_INPUT_SCHEMA_VERSION,
        ChartSource.WENZHEN_STRUCTURED_V1,
        ChartGender.KUN,
        FourPillarsInput(
            PillarInput("戊", "辰", ("戊", "乙", "癸"), "衰"),
            PillarInput("辛", "酉", ("辛",), "长生"),
            PillarInput("己", "巳", ("丙", "庚", "戊"), "帝旺"),
            PillarInput("乙", "丑", ("己", "癸", "辛"), "墓"),
        ),
        (
            DaiyunInput(1, "庚", "申", date(1989, 1, 1), date(1999, 1, 1)),
            DaiyunInput(2, "己", "未", date(1999, 1, 1), date(2009, 1, 1)),
            DaiyunInput(3, "戊", "午", date(2009, 1, 1), date(2019, 1, 1)),
            DaiyunInput(4, "丁", "巳", date(2019, 1, 1), date(2029, 1, 1)),
        ),
    )


def _build_blind_draft() -> CareerBlindDraft:
    chart = _evidence("四柱", "戊辰 辛酉 己巳 乙丑")
    luck = _evidence("大运.排布", "戊午 2009-2019；丁巳 2019-2029")
    career = _evidence("known_facts.职业", "2014、2017、2018、2023 职业与工资事实")
    fundamental = FrozenCareerFundamental(
        "career-real-feedback-baseline",
        date(2014, 1, 1),
        AS_OF_DATE,
        date(2018, 12, 31),
        "真实反馈显示职业单位、岗位与工资发生过变化",
        ("单位变化", "岗位变化", "工资变化"),
        "法务职业现实状态",
        ("反馈年表未出现任何职业或工资变化",),
    )
    rows = (
        (
            EVENT_2014,
            "career_entry",
            2014,
            "甲午",
            "戊午",
            LandingPoint("进了专业对口自己喜欢的单位，但工资低", "career", "career_entry"),
            LandingPoint("进入单位但专业不对口", "career", "career_entry"),
            "未进入专业对口单位",
        ),
        (
            EVENT_2017,
            "job_change",
            2017,
            "丁酉",
            "戊午",
            LandingPoint("离职后去不喜欢的单位，工资更低", "career", "job_change"),
            LandingPoint("留在原单位", "career", "job_change"),
            "未离职或工资未降低",
        ),
        (
            EVENT_2018,
            "job_change",
            2018,
            "戊戌",
            "戊午",
            LandingPoint("去国企，工资翻倍", "career", "job_change"),
            LandingPoint("换单位但工资未翻倍", "career", "job_change"),
            "未去国企或工资未翻倍",
        ),
        (
            EVENT_2023,
            "promotion",
            2023,
            "癸卯",
            "丁巳",
            LandingPoint("升岗级、换岗位、加了工资", "career", "promotion"),
            LandingPoint("只换岗位但未升岗级", "career", "promotion"),
            "未升岗级、未换岗位或未加工资",
        ),
    )
    events = []
    for candidate_id, event_type, year, liunian, dayun, center, alternative, falsifier in rows:
        trace = AnnualInteractionTrace(
            year,
            liunian,
            dayun,
            (chart, luck, career),
            ("career-real-feedback",),
            ("career",),
            (chart, luck, career),
            (),
            "high",
            True,
        )
        decision = evaluate_event_candidate(
            candidate_id=candidate_id,
            event_type=event_type,
            window_start=date(year, 1, 1),
            window_end=date(year, 12, 31),
            annual_trace=trace,
            root_level=RootLevel.STRONG_ROOT,
            completion_mode=CompletionMode.ACTIVATE_EXISTING,
            natal_evidence=(chart, career),
            daiyun_evidence=(luck,),
            root_evidence=(chart, luck, career),
            source_citations=(
                SourceCitation(INPUT_PATH, 40, "四柱:"),
                SourceCitation(INPUT_PATH, 97 if year < 2019 else 102, dayun),
            ),
            supporting_evidence=(career,),
            alternative_hypotheses=(alternative.name,),
            frozen_version="asof-prototype-v1-unit10",
        )
        assert decision.accepted and decision.candidate is not None
        events.append(
            FrozenCareerEvent(
                decision.candidate,
                FrozenLandingSet(
                    event_type,
                    center,
                    (alternative,),
                    "仅有名义变化而无反馈所述现实结果视为弱命中",
                    (falsifier,),
                    ("不把工资事实自动推广到其他财富结论",),
                    "landing-v1-unit10-real-feedback",
                ),
            )
        )
    return CareerBlindDraft((fundamental,), tuple(events))


def _expected_package(draft: CareerBlindDraft) -> CareerFreezePackage:
    identity = SessionIdentity(SESSION_SCHEMA_VERSION, CASE_ID, AS_OF_DATE, SESSION_ID)
    return CareerFreezePackage(
        FREEZE_PACKAGE_SCHEMA_VERSION,
        identity,
        compute_blind_input_sha256(_blind_input()),
        draft.fundamentals,
        draft.events,
    )


def _build_verification_from_feedback(package: CareerFreezePackage):
    digest = compute_freeze_package_sha256(package)
    values = {
        EVENT_2014: (
            "2014,进了专业对口自己喜欢的单位，但工资低",
            ImpactLevel.MAJOR,
            "进了专业对口自己喜欢的单位，但工资低",
        ),
        EVENT_2017: (
            "2017,离职，去了一家不喜欢的单位，工资更低",
            ImpactLevel.MAJOR,
            "离职去不喜欢的单位，工资更低",
        ),
        EVENT_2018: (
            "2018,去了一家国企，工资翻倍",
            ImpactLevel.MAJOR,
            "去国企，工资翻倍",
        ),
        EVENT_2023: (
            "2023,被迫升岗级，换岗位，工作内容少，加了工资，配了助理",
            ImpactLevel.MAJOR,
            "升岗级、换岗位、加了工资",
        ),
    }
    verifications = []
    suggestions = []
    adjudications = []
    for frozen_event in package.events:
        event_id = frozen_event.candidate.candidate_id
        excerpt, impact, state_value = values[event_id]
        verifications.append(
            VerificationInput(
                VERIFICATION_SCHEMA_VERSION,
                digest,
                event_id,
                VerificationVerdict.CONFIRMED,
                frozen_event.landing_set.center,
                None,
                (f"{FEEDBACK_PATH}: {excerpt}",),
            )
        )
        year = int(event_id.split("-")[1])
        suggestions.append(
            CareerImpactSuggestion(
                schema_version=CAREER_IMPACT_SUGGESTION_SCHEMA_VERSION,
                freeze_package_sha256=digest,
                item_id=event_id,
                event_date=date(year, 12, 31),
                suggested_impact=impact,
                suggested_persistence=Persistence.CROSS_DAIYUN,
                suggested_scope=ImpactScope.PRIMARY_DOMAIN,
                suggested_short_term_until=None,
                state_value=state_value,
                opened_path_ids=(),
                closed_path_ids=(),
            )
        )
        adjudications.append(
            CareerImpactAdjudication(
                digest,
                event_id,
                impact,
                Persistence.CROSS_DAIYUN,
                ImpactScope.PRIMARY_DOMAIN,
                None,
                "命理师依据真实反馈年表确认现实影响",
                "",
                "",
                (),
                (),
                "",
                "",
            )
        )
    fundamental = CareerFundamentalAdjudication(
        digest,
        "career-real-feedback-baseline",
        "核验后选择符合截止日真实职业年表的冻结基本面",
    )
    return tuple(verifications), tuple(suggestions), tuple(adjudications), fundamental


def _state_built_inputs():
    draft = _build_blind_draft()
    package = _expected_package(draft)
    verifications, suggestions, adjudications, fundamental = _build_verification_from_feedback(package)
    result = run_career_session(
        session_schema_version=SESSION_SCHEMA_VERSION,
        case_id=CASE_ID,
        as_of_date=AS_OF_DATE,
        session_id=SESSION_ID,
        blind_input=_blind_input(),
        draft=draft,
        verifications=verifications,
        suggestions=suggestions,
        impact_adjudications=adjudications,
        fundamental_adjudication=fundamental,
        daiyun_end=date(2028, 12, 31),
        career_candidates=None,
        wealth_bindings=None,
    )
    assert result.final_envelope.state is ConsultationState.STATE_BUILT
    assert tuple(
        entry.candidate.candidate_id
        for entry in result.state_result.ledger_entries
        if entry.candidate.verification_status is VerificationStatus.CONFIRMED
    ) == CONFIRMED_IDS
    return result, draft, verifications, suggestions, adjudications, fundamental


def _candidate(active_state_ids: tuple[str, ...]) -> CareerFutureCandidate:
    return CareerFutureCandidate(
        case_id=CASE_ID,
        as_of_date=AS_OF_DATE,
        candidate_id=FUTURE_CANDIDATE_ID,
        conclusion="已核验职业现实状态作为后续事业推演起点",
        required_active_state_ids=(active_state_ids[-1],),
        required_open_path_ids=(),
    )


def _bindings(
    *,
    observed_2023: tuple[str, ...] = REAL_REQUIRED_CONDITIONS,
    falsifiers_2023: tuple[str, ...] = (),
) -> tuple[WealthEventBinding, ...]:
    return (
        WealthEventBinding(EVENT_2014, (), (), ()),
        WealthEventBinding(EVENT_2017, (), (), ()),
        WealthEventBinding(EVENT_2018, (), (), ()),
        WealthEventBinding(EVENT_2023, observed_2023, falsifiers_2023, (REAL_EDGE,)),
    )


def test_unit10_real_feedback_edge_propagates_only_2023_raise() -> None:
    state_built, draft, verifications, suggestions, adjudications, fundamental = _state_built_inputs()
    active_ids = state_built.state_result.verified_state.active_state_ids
    candidates = (_candidate(active_ids),)
    bindings = _bindings()
    result = run_career_session(
        session_schema_version=SESSION_SCHEMA_VERSION,
        case_id=CASE_ID,
        as_of_date=AS_OF_DATE,
        session_id=SESSION_ID,
        blind_input=_blind_input(),
        draft=draft,
        verifications=verifications,
        suggestions=suggestions,
        impact_adjudications=adjudications,
        fundamental_adjudication=fundamental,
        daiyun_end=date(2028, 12, 31),
        career_candidates=candidates,
        wealth_bindings=bindings,
    )

    assert tuple(binding.event_id for binding in bindings) == CONFIRMED_IDS
    assert result.final_envelope.state is ConsultationState.PROJECTED
    assert result.projection is not None
    assert result.projection.career_mainline == candidates
    assert tuple(item.event_id for item in result.projection.wealth_decisions) == CONFIRMED_IDS
    for item in result.projection.wealth_decisions[:3]:
        assert item.decision.reason_code == "NO_EXPLICIT_EDGE"
        assert item.decision.changed is False
        assert item.decision.state is None
        assert item.decision.edge_id is None

    decision = result.projection.wealth_decisions[3].decision
    assert decision.reason_code == "WEALTH_STATE_PROPAGATED"
    assert decision.changed is True
    assert decision.state is not None
    assert decision.edge_id is not None
    assert decision.edge_id == REAL_EDGE_ID
    assert decision.state.domain == "wealth"
    assert decision.state.value == "加了工资"
    assert decision.state.source_event_id == EVENT_2023
    assert decision.state.verified is True
    assert result.projection.wealth_states == (decision.state,)


def test_unit10_missing_real_required_condition_does_not_propagate() -> None:
    state_result = _state_built_inputs()[0].state_result
    before = deepcopy(state_result)
    candidate = _candidate(state_result.verified_state.active_state_ids)
    projected = project_future_from_state(
        result=state_result,
        career_candidates=(candidate,),
        wealth_bindings=_bindings(observed_2023=("升岗级", "换岗位")),
    )

    decision = projected.wealth_decisions[3].decision
    assert decision.changed is False
    assert decision.reason_code == "PROPAGATION_CONDITIONS_NOT_MET"
    assert decision.state is None
    assert decision.edge_id == REAL_EDGE_ID
    assert projected.wealth_states == ()
    assert state_result == before
    assert state_result.envelope.state is ConsultationState.STATE_BUILT


def test_unit10_active_falsifier_blocks_otherwise_matching_real_edge() -> None:
    state_result = _state_built_inputs()[0].state_result
    projected = project_future_from_state(
        result=state_result,
        career_candidates=(_candidate(state_result.verified_state.active_state_ids),),
        wealth_bindings=_bindings(falsifiers_2023=(REAL_FALSIFIER,)),
    )

    decision = projected.wealth_decisions[3].decision
    assert decision.changed is False
    assert decision.reason_code == "PROPAGATION_FALSIFIED"
    assert decision.state is None
    assert decision.edge_id == REAL_EDGE_ID
    assert projected.wealth_states == ()


def test_unit10_unverified_items_do_not_pollute_success_semantics() -> None:
    state_result = _state_built_inputs()[0].state_result
    candidate = _candidate(state_result.verified_state.active_state_ids)
    bindings = _bindings()
    semantic_payload = repr(
        (
            (
                candidate.conclusion,
                candidate.required_active_state_ids,
                candidate.required_open_path_ids,
            ),
            tuple(
                (
                    binding.event_id,
                    binding.observed_conditions,
                    binding.active_falsifiers,
                    tuple(
                        (
                            edge.edge_id,
                            edge.source_event_type,
                            edge.target_state,
                            edge.required_conditions,
                            edge.falsifiers,
                            edge.verified,
                            edge.delay_days,
                            edge.persistence,
                            edge.short_term_days,
                        )
                        for edge in binding.edges
                    ),
                )
                for binding in bindings
            ),
        )
    )
    forbidden = (
        "待追踪",
        "2024待核验",
        "2025待核验",
        "2026待核验",
        "2027待核验",
    )

    assert not any(token in semantic_payload for token in forbidden)
    assert all(binding.active_falsifiers == () for binding in bindings)
    assert set(candidate.required_active_state_ids) <= set(
        state_result.verified_state.active_state_ids
    )
    assert candidate.required_open_path_ids == ()
    assert tuple(binding.event_id for binding in bindings) == CONFIRMED_IDS
    assert all(binding.edges == () for binding in bindings[:3])
    assert bindings[3].observed_conditions == REAL_EDGE.required_conditions


def test_unit10_fresh_ast_import_and_filename_boundaries() -> None:
    path = Path(__file__)
    assert not path.name.endswith("future_projection.py")
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imported = []
    for node in tree.body:
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module)
    forbidden_prefixes = (
        "engine.pipeline",
        "engine.v5.runner",
        "engine.v5.preprod",
        "tools.render_report",
        "tools.feedback",
        "engine.asof.natal_capacity",
        "engine.asof.structural_track",
        "engine.asof.daiyun_context",
    )

    assert not any(name.startswith(forbidden_prefixes) for name in imported)

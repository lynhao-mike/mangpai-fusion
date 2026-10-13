from __future__ import annotations

import ast
from dataclasses import fields, is_dataclass
from datetime import date
from pathlib import Path

import pytest

from engine.asof.event_candidate import (
    AnnualInteractionTrace,
    CompletionMode,
    ExtensionBoundary,
    LifeEventCandidate,
    RootLevel,
    VerificationStatus,
)
from engine.asof.natal_capacity import EvidenceRef, SourceCitation
from engine.asof.reality_track import RealityTrack
from engine.asof.state_ledger import (
    AsOfRequest,
    DecisionAction,
    EventImpactAssessment,
    EventLedgerEntry,
    HypothesisState,
    ImpactLevel,
    ImpactScope,
    Persistence,
    VerifiedState,
    admit_hypothesis_branch,
    build_verified_state,
)
from engine.asof.structural_track import StructuralTrack


CASE_ID = "C-2026-028-乾-壬戌癸卯壬子乙巳"


def _evidence(locator: str = "四柱.年柱", excerpt: str = "壬戌") -> EvidenceRef:
    return EvidenceRef(f"cases/{CASE_ID}/input.md", locator, excerpt)


def _candidate(
    candidate_id: str,
    *,
    status: VerificationStatus = VerificationStatus.CONFIRMED,
) -> LifeEventCandidate:
    evidence = _evidence()
    trace = AnnualInteractionTrace(
        year=2020,
        liunian="庚子",
        dayun_ganzhi="丙寅",
        relations=(evidence,),
        activated_node_ids=("career-authority",),
        domains=("career",),
        supporting_evidence=(evidence,),
        counter_evidence=(),
        trigger_strength="high",
        crossed_candidate_gate=True,
    )
    return LifeEventCandidate(
        candidate_id=candidate_id,
        domain="career",
        event_type="responsibility_level_change",
        window_start=date(2020, 1, 1),
        window_end=date(2020, 12, 31),
        natal_evidence=(evidence,),
        daiyun_evidence=(_evidence("大运.排布[4]", "丙寅"),),
        annual_trace=trace,
        root_level=RootLevel.STRONG_ROOT,
        root_evidence=(evidence,),
        source_citations=(
            SourceCitation("sources/gao/2018弟子班_大运流年篇_55页.md", 139, "大运完成原局未尽组合"),
        ),
        completion_mode=CompletionMode.ACTIVATE_EXISTING,
        supporting_evidence=(evidence,),
        counter_evidence=(),
        alternative_hypotheses=(),
        frozen_version="asof-prototype-v1",
        verification_status=status,
        extension_boundary=ExtensionBoundary.CROSS_DAIYUN_ELIGIBLE,
        is_primary_event=True,
    )


def _assessment(
    event_id: str,
    *,
    event_date: date = date(2020, 9, 1),
    impact: ImpactLevel = ImpactLevel.SIGNIFICANT,
    persistence: Persistence = Persistence.CROSS_DAIYUN,
    short_term_until: date | None = None,
    opened_path_ids: tuple[str, ...] = (),
) -> EventImpactAssessment:
    return EventImpactAssessment(
        event_id=event_id,
        event_date=event_date,
        event_type="responsibility_level_change",
        root_level=RootLevel.STRONG_ROOT,
        completion_mode=CompletionMode.ACTIVATE_EXISTING,
        system_suggested_impact=impact,
        system_suggested_persistence=persistence,
        system_suggested_scope=ImpactScope.PRIMARY_DOMAIN,
        short_term_until=short_term_until,
        state_value="校长职责层级扩大",
        opened_path_ids=opened_path_ids,
    )


def _entry(
    event_id: str,
    *,
    status: VerificationStatus = VerificationStatus.CONFIRMED,
    event_date: date = date(2020, 9, 1),
    impact: ImpactLevel = ImpactLevel.SIGNIFICANT,
    persistence: Persistence = Persistence.CROSS_DAIYUN,
    short_term_until: date | None = None,
    opened_path_ids: tuple[str, ...] = (),
) -> EventLedgerEntry:
    return EventLedgerEntry(
        _candidate(event_id, status=status),
        _assessment(
            event_id,
            event_date=event_date,
            impact=impact,
            persistence=persistence,
            short_term_until=short_term_until,
            opened_path_ids=opened_path_ids,
        ),
    )


def _snapshot(as_of: date, *entries: EventLedgerEntry, daiyun_end: date = date(2024, 12, 31)) -> VerifiedState:
    return build_verified_state(
        AsOfRequest(CASE_ID, as_of),
        entries=tuple(entries),
        daiyun_end=daiyun_end,
        current_center="教育管理岗位",
        reasonable_range=("同域权责调整",),
    )


def test_fact_and_hypothesis_snapshots_and_tracks_are_physically_separate() -> None:
    assert is_dataclass(VerifiedState)
    assert is_dataclass(HypothesisState)
    assert VerifiedState is not HypothesisState
    assert StructuralTrack is not RealityTrack

    verified_fields = {field.name for field in fields(VerifiedState)}
    assert not verified_fields & {"candidate", "candidates", "hypothesis", "unverified_candidates"}
    assert "reality_track" in verified_fields


@pytest.mark.parametrize(
    "status",
    (
        VerificationStatus.CANDIDATE,
        VerificationStatus.FROZEN,
        VerificationStatus.UNKNOWN,
        VerificationStatus.WITHHELD,
        VerificationStatus.REJECTED,
    ),
)
def test_unverified_or_rejected_candidate_never_contaminates_verified_state(
    status: VerificationStatus,
) -> None:
    snapshot = _snapshot(date(2021, 12, 31), _entry(f"event-{status.value}", status=status))
    assert snapshot.verified_event_ids == ()
    assert snapshot.active_state_ids == ()
    assert snapshot.reality_track.active_states == ()


def test_post_cutoff_confirmed_event_does_not_enter_verified_state() -> None:
    snapshot = _snapshot(
        date(2019, 12, 31),
        _entry("event-after-cutoff", event_date=date(2020, 9, 1)),
    )
    assert snapshot.verified_event_ids == ()


@pytest.mark.parametrize(
    ("persistence", "as_of", "short_term_until", "expected"),
    (
        (Persistence.SHORT_TERM, date(2020, 12, 31), date(2021, 6, 30), True),
        (Persistence.SHORT_TERM, date(2021, 12, 31), date(2021, 6, 30), False),
        (Persistence.REMAINDER_OF_DAIYUN, date(2024, 12, 31), None, True),
        (Persistence.REMAINDER_OF_DAIYUN, date(2025, 1, 1), None, False),
        (Persistence.CROSS_DAIYUN, date(2025, 12, 31), None, True),
        (Persistence.PERMANENT, date(2025, 12, 31), None, True),
    ),
)
def test_synthetic_persistence_boundaries_are_explicit(
    persistence: Persistence,
    as_of: date,
    short_term_until: date | None,
    expected: bool,
) -> None:
    """合成持续期边界；不是案例 C-2026-028 的真实历史归类。"""
    snapshot = _snapshot(
        as_of,
        _entry(
            f"event-{persistence.value}",
            persistence=persistence,
            short_term_until=short_term_until,
        ),
    )
    assert bool(snapshot.active_state_ids) is expected


@pytest.mark.parametrize(
    ("impact", "persistence"),
    (
        (ImpactLevel.MINOR, Persistence.CROSS_DAIYUN),
        (ImpactLevel.SIGNIFICANT, Persistence.INSTANT),
    ),
)
def test_minor_or_instant_event_does_not_form_stable_state(
    impact: ImpactLevel,
    persistence: Persistence,
) -> None:
    """合成状态门边界；不是案例 C-2026-028 的真实历史归类。"""
    snapshot = _snapshot(
        date(2021, 12, 31),
        _entry("event-no-stable-state", impact=impact, persistence=persistence),
    )
    assert snapshot.active_state_ids == ()


def test_turning_point_writes_explicit_path_state() -> None:
    snapshot = _snapshot(
        date(2021, 12, 31),
        _entry(
            "event-turning",
            impact=ImpactLevel.TURNING_POINT,
            persistence=Persistence.PERMANENT,
            opened_path_ids=("career-management",),
        ),
    )
    assert snapshot.reality_track.path_states[0].path_id == "career-management"
    assert snapshot.reality_track.path_states[0].status == "open"


def test_manual_final_assessment_preserves_frozen_system_suggestion() -> None:
    assessment = EventImpactAssessment(
        event_id="event-manual",
        event_date=date(2022, 1, 1),
        event_type="responsibility_level_change",
        root_level=RootLevel.STRONG_ROOT,
        completion_mode=CompletionMode.ACTIVATE_EXISTING,
        system_suggested_impact=ImpactLevel.SIGNIFICANT,
        system_suggested_persistence=Persistence.SHORT_TERM,
        system_suggested_scope=ImpactScope.PRIMARY_DOMAIN,
        practitioner_final_impact=ImpactLevel.MAJOR,
        practitioner_final_persistence=Persistence.CROSS_DAIYUN,
        practitioner_final_scope=ImpactScope.RELATED_DOMAINS,
        adjustment_reason="核验后确认跨运持续",
    )
    assert assessment.system_suggested_impact is ImpactLevel.SIGNIFICANT
    assert assessment.system_suggested_persistence is Persistence.SHORT_TERM
    assert assessment.system_suggested_scope is ImpactScope.PRIMARY_DOMAIN
    assert assessment.effective_impact is ImpactLevel.MAJOR
    assert assessment.effective_persistence is Persistence.CROSS_DAIYUN
    assert assessment.effective_scope is ImpactScope.RELATED_DOMAINS


@pytest.mark.parametrize(
    "kwargs",
    (
        {"practitioner_final_impact": ImpactLevel.MAJOR},
        {
            "practitioner_final_impact": ImpactLevel.MAJOR,
            "practitioner_final_persistence": Persistence.CROSS_DAIYUN,
            "practitioner_final_scope": ImpactScope.RELATED_DOMAINS,
        },
    ),
)
def test_manual_final_assessment_requires_complete_dimensions_and_reason(kwargs: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        EventImpactAssessment(
            event_id="event-invalid-manual",
            event_date=date(2022, 1, 1),
            event_type="responsibility_level_change",
            root_level=RootLevel.STRONG_ROOT,
            completion_mode=CompletionMode.ACTIVATE_EXISTING,
            system_suggested_impact=ImpactLevel.SIGNIFICANT,
            system_suggested_persistence=Persistence.CROSS_DAIYUN,
            system_suggested_scope=ImpactScope.PRIMARY_DOMAIN,
            **kwargs,
        )


def test_eligible_unverified_major_candidate_enters_only_hypothesis_branch() -> None:
    candidate = _candidate("event-hypothesis", status=VerificationStatus.FROZEN)
    assessment = _assessment(
        "event-hypothesis",
        impact=ImpactLevel.MAJOR,
        persistence=Persistence.CROSS_DAIYUN,
    )
    request = AsOfRequest(CASE_ID, date(2021, 12, 31))
    branch = admit_hypothesis_branch(
        request,
        candidate=candidate,
        assessment=assessment,
        condition="若权责晋升已实际发生",
        difference_from_verified="职业基点上移",
        changed_fundamentals=("职责层级",),
        changed_future_conclusions=("后续事业起点",),
        minimum_question="是否已正式任命？",
        falsifier="无任命文件且当事人否认",
    )
    snapshot = _snapshot(date(2021, 12, 31), EventLedgerEntry(candidate, assessment))

    assert isinstance(branch, HypothesisState)
    assert branch.decision_action is DecisionAction.CONDITIONAL
    assert snapshot.verified_event_ids == ()


@pytest.mark.parametrize(
    ("impact", "persistence", "fundamentals", "future"),
    (
        (ImpactLevel.SIGNIFICANT, Persistence.CROSS_DAIYUN, ("职责层级",), ("未来起点",)),
        (ImpactLevel.MAJOR, Persistence.SHORT_TERM, ("职责层级",), ("未来起点",)),
        (ImpactLevel.MAJOR, Persistence.CROSS_DAIYUN, (), ("未来起点",)),
        (ImpactLevel.MAJOR, Persistence.CROSS_DAIYUN, ("职责层级",), ()),
    ),
)
def test_hypothesis_gate_rejects_non_fundamental_branch(
    impact: ImpactLevel,
    persistence: Persistence,
    fundamentals: tuple[str, ...],
    future: tuple[str, ...],
) -> None:
    candidate = _candidate("event-rejected-branch", status=VerificationStatus.FROZEN)
    assessment = _assessment(
        "event-rejected-branch",
        impact=impact,
        persistence=persistence,
        short_term_until=date(2021, 6, 30) if persistence is Persistence.SHORT_TERM else None,
    )
    branch = admit_hypothesis_branch(
        AsOfRequest(CASE_ID, date(2021, 12, 31)),
        candidate=candidate,
        assessment=assessment,
        condition="若事件成立",
        difference_from_verified="与事实主线不同",
        changed_fundamentals=fundamentals,
        changed_future_conclusions=future,
        minimum_question="事件是否发生？",
        falsifier="当事人否认",
    )
    assert branch is None


def test_state_ledger_uses_classification_not_weighted_sum() -> None:
    tree = ast.parse(Path("engine/asof/state_ledger.py").read_text(encoding="utf-8"))
    forbidden_calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "sum"
    ]
    forbidden_names = {
        node.id.lower()
        for node in ast.walk(tree)
        if isinstance(node, ast.Name)
        and any(token in node.id.lower() for token in ("weight", "weighted", "score"))
    }
    weighted_multiplications = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.BinOp)
        and isinstance(node.op, ast.Mult)
        and any(
            isinstance(part, ast.Name) and "weight" in part.id.lower()
            for part in (node.left, node.right)
        )
    ]
    score_additions = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.BinOp)
        and isinstance(node.op, ast.Add)
        and any(
            isinstance(part, ast.Name) and "score" in part.id.lower()
            for part in (node.left, node.right)
        )
    ]

    assert forbidden_calls == []
    assert forbidden_names == set()
    assert weighted_multiplications == []
    assert score_additions == []

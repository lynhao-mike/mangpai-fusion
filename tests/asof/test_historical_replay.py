from __future__ import annotations

from datetime import date

from engine.asof.event_candidate import (
    AnnualInteractionTrace,
    CompletionMode,
    ExtensionBoundary,
    LifeEventCandidate,
    RootLevel,
    VerificationStatus,
)
from engine.asof.natal_capacity import EvidenceRef, SourceCitation
from engine.asof.state_ledger import (
    AsOfRequest,
    EventImpactAssessment,
    EventLedgerEntry,
    ImpactLevel,
    ImpactScope,
    Persistence,
    build_verified_state,
)


CASE_ID = "C-2026-028-乾-壬戌癸卯壬子乙巳"
CASE_FEEDBACK = f"cases/{CASE_ID}/feedback.md"


def _event(
    event_id: str,
    *,
    event_date: date,
    event_type: str,
    state_value: str,
    locator: str,
    excerpt: str,
    impact: ImpactLevel,
    persistence: Persistence,
    opened_path_ids: tuple[str, ...] = (),
    closed_path_ids: tuple[str, ...] = (),
) -> EventLedgerEntry:
    chart = EvidenceRef(f"cases/{CASE_ID}/input.md", "四柱", "壬戌 癸卯 壬子 乙巳")
    feedback = EvidenceRef(CASE_FEEDBACK, locator, excerpt)
    trace = AnnualInteractionTrace(
        year=event_date.year,
        liunian="历史回放年度",
        dayun_ganzhi="历史回放大运",
        relations=(chart,),
        activated_node_ids=("career-authority",),
        domains=("career",),
        supporting_evidence=(chart,),
        counter_evidence=(),
        trigger_strength="high",
        crossed_candidate_gate=True,
    )
    candidate = LifeEventCandidate(
        candidate_id=event_id,
        domain="career",
        event_type=event_type,
        window_start=event_date,
        window_end=event_date,
        natal_evidence=(chart,),
        daiyun_evidence=(chart,),
        annual_trace=trace,
        root_level=RootLevel.STRONG_ROOT,
        root_evidence=(chart,),
        source_citations=(SourceCitation(CASE_FEEDBACK, 1, excerpt),),
        completion_mode=CompletionMode.ACTIVATE_EXISTING,
        supporting_evidence=(feedback,),
        counter_evidence=(),
        alternative_hypotheses=(),
        frozen_version="asof-prototype-v1-historical-replay",
        verification_status=VerificationStatus.CONFIRMED,
        extension_boundary=ExtensionBoundary.CROSS_DAIYUN_ELIGIBLE,
        is_primary_event=True,
    )
    assessment = EventImpactAssessment(
        event_id=event_id,
        event_date=event_date,
        event_type=event_type,
        root_level=RootLevel.STRONG_ROOT,
        completion_mode=CompletionMode.ACTIVATE_EXISTING,
        system_suggested_impact=impact,
        system_suggested_persistence=persistence,
        system_suggested_scope=ImpactScope.PRIMARY_DOMAIN,
        state_value=state_value,
        opened_path_ids=opened_path_ids,
        closed_path_ids=closed_path_ids,
    )
    return EventLedgerEntry(candidate, assessment)


def _verified_history() -> tuple[EventLedgerEntry, ...]:
    """只用于 G5 回放的已核验履历；不得反向参与原局根源判定。"""
    return (
        _event(
            "career-2020-dual-school",
            event_date=date(2020, 9, 1),
            event_type="responsibility_level_change",
            state_value="兼任小学和初中两校校长",
            locator="2020事业反馈",
            excerpt="学校拆分，兼任小学和初中两校校长",
            impact=ImpactLevel.MAJOR,
            persistence=Persistence.CROSS_DAIYUN,
        ),
        _event(
            "career-2022-grade-promotion",
            event_date=date(2022, 7, 1),
            event_type="responsibility_level_change",
            state_value="晋升正股级",
            locator="2022事业反馈",
            excerpt="晋升正股级",
            impact=ImpactLevel.MAJOR,
            persistence=Persistence.PERMANENT,
        ),
        _event(
            "career-2025-transfer",
            event_date=date(2025, 8, 1),
            event_type="workplace_migration_path_change",
            state_value="专任较大初中校长",
            locator="2025事业反馈",
            excerpt="调任较大初中校长，后卸任原初中兼职并专任",
            impact=ImpactLevel.TURNING_POINT,
            persistence=Persistence.CROSS_DAIYUN,
            opened_path_ids=("larger-middle-school-leadership",),
            closed_path_ids=("dual-school-concurrent-role",),
        ),
    )


def _replay(as_of_date: date):
    return build_verified_state(
        AsOfRequest(CASE_ID, as_of_date),
        entries=_verified_history(),
        daiyun_end=date(2034, 12, 31),
        current_center="教育管理岗位",
        reasonable_range=("校级管理职责调整",),
    )


def test_three_frozen_cutoffs_produce_different_verified_snapshots() -> None:
    before = _replay(date(2019, 12, 31))
    after_2020 = _replay(date(2021, 12, 31))
    after_2025 = _replay(date(2025, 12, 31))

    assert before.verified_event_ids == ()
    assert after_2020.verified_event_ids == ("career-2020-dual-school",)
    assert after_2025.verified_event_ids == (
        "career-2020-dual-school",
        "career-2022-grade-promotion",
        "career-2025-transfer",
    )
    assert before != after_2020 != after_2025


def test_historical_replay_never_reads_post_cutoff_facts() -> None:
    snapshot = _replay(date(2021, 12, 31))
    values = tuple(state.value for state in snapshot.reality_track.active_states)

    assert "兼任小学和初中两校校长" in values
    assert "晋升正股级" not in values
    assert "专任较大初中校长" not in values
    assert snapshot.reality_track.path_states == ()


def test_turning_point_paths_appear_only_after_2025_cutoff() -> None:
    before = _replay(date(2021, 12, 31))
    after = _replay(date(2025, 12, 31))

    assert before.reality_track.path_states == ()
    assert {(path.path_id, path.status) for path in after.reality_track.path_states} == {
        ("larger-middle-school-leadership", "open"),
        ("dual-school-concurrent-role", "closed"),
    }

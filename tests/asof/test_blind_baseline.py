from __future__ import annotations

import ast
import json
from dataclasses import replace
from datetime import date
from pathlib import Path
from typing import Any, Callable

import pytest

from engine.asof.blind_baseline import (
    CURRENT_STATE_SCHEMA_VERSION,
    FUTURE_PROJECTION_SCHEMA_VERSION,
    QUESTION_SNAPSHOT_SCHEMA_VERSION,
    RUNTIME_SNAPSHOT_SCHEMA_VERSION,
    ArtifactKind,
    ArtifactReference,
    BaselineQuestionSnapshot,
    BaselineRuntimeSnapshot,
    BlindBaselineError,
    BlindCurrentStateSnapshot,
    BlindFutureCandidate,
    BlindHypothesisRole,
    BlindProjectionInput,
    BlindStateHypothesis,
    BlindWealthBinding,
    blind_baseline_payload_sha256,
    run_blind_baseline,
    serialize_blind_baseline_payload,
)
from engine.asof.blind_baseline_archive import (
    BlindBaselineArchiveError,
    BlindBaselineLineageContext,
    load_blind_baseline_lineage_context,
    publish_blind_baseline,
)
from engine.asof.consultation_freeze import (
    CareerBlindDraft,
    FrozenCareerEvent,
    FrozenCareerFundamental,
)
from engine.asof.event_candidate import (
    AnnualInteractionTrace,
    CompletionMode,
    ExtensionBoundary,
    LifeEventCandidate,
    RootLevel,
    VerificationStatus,
)
from engine.asof.natal_capacity import EvidenceRef, SourceCitation
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
)
from engine.asof.state_ledger import DecisionAction
from engine.evaluation.prospective_artifacts import publish_new_json


CASE_ID = "C-2026-001-乾-庚申戊寅壬子辛丑"
AS_OF = date(2020, 1, 1)
SESSION_ID = "S-20260930T120000Z-0123abcd"


def _pillar(stem: str, branch: str, hidden: tuple[str, ...]) -> PillarInput:
    return PillarInput(stem, branch, hidden, "长生")


def _blind_input() -> BlindChartInput:
    return BlindChartInput(
        BLIND_INPUT_SCHEMA_VERSION,
        ChartSource.WENZHEN_STRUCTURED_V1,
        ChartGender.QIAN,
        FourPillarsInput(
            _pillar("庚", "申", ("庚", "壬", "戊")),
            _pillar("戊", "寅", ("甲", "丙", "戊")),
            _pillar("壬", "子", ("癸",)),
            _pillar("辛", "丑", ("己", "癸", "辛")),
        ),
        (DaiyunInput(1, "己", "卯", date(2010, 1, 1), AS_OF),),
    )


def _evidence() -> EvidenceRef:
    return EvidenceRef("cases/C-2026-001/input.md", "四柱.年柱", "庚申")


def _fundamental(**changes: Any) -> FrozenCareerFundamental:
    values = {
        "fundamental_id": "career-baseline",
        "window_start": date(2019, 1, 1),
        "window_end": AS_OF,
        "window_center": date(2019, 7, 2),
        "center": "mid-level professional",
        "reasonable_range": ("skilled individual contributor", "team lead"),
        "strongest_alternative": "independent specialist",
        "falsifiers": ("no sustained professional responsibility",),
    }
    values.update(changes)
    return FrozenCareerFundamental(**values)


def _point(name: str = "internal promotion") -> LandingPoint:
    return LandingPoint(name, "career", "authority_up")


def _event() -> FrozenCareerEvent:
    evidence = _evidence()
    candidate = LifeEventCandidate(
        "career-event-2019",
        "career",
        "responsibility_level_change",
        date(2019, 1, 1),
        date(2019, 12, 31),
        (evidence,),
        (evidence,),
        AnnualInteractionTrace(
            2019,
            "己亥",
            "庚辰",
            (evidence,),
            ("career-authority",),
            ("career",),
            (evidence,),
            (),
            "high",
            True,
        ),
        RootLevel.STRONG_ROOT,
        (evidence,),
        (SourceCitation("sources/gao/example.md", 1, "原局有根，岁运引动"),),
        CompletionMode.ACTIVATE_EXISTING,
        (evidence,),
        (),
        ("scope changed without title",),
        "asof-prototype-v1",
        VerificationStatus.FROZEN,
        ExtensionBoundary.CROSS_DAIYUN_ELIGIBLE,
        True,
    )
    return FrozenCareerEvent(
        candidate,
        FrozenLandingSet(
            "responsibility_level_change",
            _point(),
            (_point("team scope expanded"),),
            "title-only change is weak",
            ("responsibility unchanged",),
            ("income-only change",),
            "landing-v1-before-outcome",
        ),
    )


def _draft(**changes: Any) -> CareerBlindDraft:
    values = {"fundamentals": (_fundamental(),), "events": (_event(),)}
    values.update(changes)
    return CareerBlindDraft(**values)


def _question() -> BaselineQuestionSnapshot:
    return BaselineQuestionSnapshot(
        QUESTION_SNAPSHOT_SCHEMA_VERSION,
        "FQ-2026-001",
        "career-future-001",
        "未来三年是否发生职责层级上升？",
        "binary",
        "职责范围或决策权发生可验证上升",
        "未发生职责范围或决策权上升",
        "2020-01-02T00:00:00Z",
        "2023-01-01T00:00:00Z",
        ArtifactReference("future-question.json", "1" * 64),
    )


def _runtime() -> BaselineRuntimeSnapshot:
    return BaselineRuntimeSnapshot(
        RUNTIME_SNAPSHOT_SCHEMA_VERSION,
        "RULE-SNAPSHOT-2026-001",
        "2" * 64,
        "phase1-proof",
        "human-practitioner-v1",
    )


def _state_hypothesis(
    hypothesis_id: str,
    role: BlindHypothesisRole,
    *,
    decision_action: DecisionAction,
    source_fundamental_ids: tuple[str, ...] = ("career-baseline",),
    source_event_ids: tuple[str, ...] = ("career-event-2019",),
) -> BlindStateHypothesis:
    conditional = role is BlindHypothesisRole.CONDITIONAL
    return BlindStateHypothesis(
        CASE_ID,
        AS_OF,
        hypothesis_id,
        "career",
        role,
        "external transition remains open" if conditional else "responsibility is expanding internally",
        ("role scope expands", "decision authority rises"),
        "external specialist path" if not conditional else "internal scope expansion",
        source_fundamental_ids,
        source_event_ids,
        ("frozen structure", "frozen historical event"),
        ("external-transition",) if conditional else ("internal-advancement",),
        ("external offer becomes executable",) if conditional else (),
        ("responsibility remains unchanged",),
        58 if conditional else 72,
        decision_action,
    )


def _state(*, include_conditional: bool = True) -> BlindCurrentStateSnapshot:
    hypotheses = (
        _state_hypothesis(
            "state-primary",
            BlindHypothesisRole.PRIMARY,
            decision_action=DecisionAction.OUTPUT,
        ),
    )
    if include_conditional:
        hypotheses += (
            _state_hypothesis(
                "state-external",
                BlindHypothesisRole.CONDITIONAL,
                decision_action=DecisionAction.CONDITIONAL,
            ),
        )
    return BlindCurrentStateSnapshot(
        CURRENT_STATE_SCHEMA_VERSION,
        CASE_ID,
        AS_OF,
        "state-primary",
        hypotheses,
    )


def _candidate(
    candidate_id: str,
    domain: str,
    hypothesis_id: str,
    conclusion: str,
    action: DecisionAction,
) -> BlindFutureCandidate:
    return BlindFutureCandidate(
        CASE_ID,
        AS_OF,
        candidate_id,
        domain,
        hypothesis_id,
        conclusion,
        date(2020, 1, 2),
        date(2022, 12, 31),
        "2021 is the center of the observation window",
        ("timing may shift by one year",),
        ("frozen structure", "blind current-state path"),
        ("path remains open",),
        ("opposite path becomes verified",),
        68 if action is DecisionAction.OUTPUT else 52,
        action,
    )


def _projection_input(*, include_wealth_binding: bool = True) -> BlindProjectionInput:
    candidates = (
        _candidate(
            "career-mainline",
            "career",
            "state-primary",
            "internal responsibility expands",
            DecisionAction.OUTPUT,
        ),
        _candidate(
            "wealth-mainline",
            "wealth",
            "state-primary",
            "income stability improves after responsibility expansion",
            DecisionAction.OUTPUT,
        ),
        _candidate(
            "career-external",
            "career",
            "state-external",
            "external specialist transition replaces internal advancement",
            DecisionAction.CONDITIONAL,
        ),
    )
    bindings = (
        BlindWealthBinding(
            "edge-mainline-wealth",
            "career-mainline",
            "wealth-mainline",
            ("responsibility expansion materializes",),
            ("income remains flat after role expansion",),
        ),
    )
    return BlindProjectionInput(candidates, bindings if include_wealth_binding else ())


def _run(**changes: Any):
    values = {
        "session_schema_version": SESSION_SCHEMA_VERSION,
        "case_id": CASE_ID,
        "as_of_date": AS_OF,
        "session_id": SESSION_ID,
        "blind_input": _blind_input(),
        "draft": _draft(),
        "question_snapshot": _question(),
        "current_state": _state(),
        "projection_input": _projection_input(),
        "runtime_snapshot": _runtime(),
    }
    values.update(changes)
    return run_blind_baseline(**values)


def _assert_error(code: str, operation: Callable[[], object]) -> None:
    with pytest.raises(BlindBaselineError) as caught:
        operation()
    assert caught.value.code == code


def test_no_feedback_baseline_freezes_projects_and_serializes_stably() -> None:
    result = _run()
    assert result.artifact_kind is ArtifactKind.BLIND_BASELINE
    assert result.final_envelope.state is ConsultationState.FROZEN
    assert result.input_access.feedback_accessed is False
    assert result.input_access.verification_accessed is False
    assert result.input_access.known_facts_accessed is False
    assert result.projection.schema_version == FUTURE_PROJECTION_SCHEMA_VERSION
    assert [item.candidate_id for item in result.projection.career_mainline] == [
        "career-mainline"
    ]
    assert [item.candidate_id for item in result.projection.wealth_mainline] == [
        "wealth-mainline"
    ]
    assert [
        item.state_hypothesis.hypothesis_id
        for item in result.projection.conditional_branches
    ] == ["state-external"]
    assert [item.domain for item in result.projection.unsupported_domains] == [
        "family",
        "education",
        "marriage",
        "health",
    ]

    payload = serialize_blind_baseline_payload(result)
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    readback = json.loads(encoded)
    assert readback == payload
    assert blind_baseline_payload_sha256(readback) == blind_baseline_payload_sha256(
        payload
    )
    assert payload["artifact_kind"] == "BLIND_BASELINE"
    assert payload["envelope"]["state"] == "FROZEN"


def test_question_window_compares_parsed_instants_not_timestamp_spelling() -> None:
    _assert_error(
        "INVALID_VALUE",
        lambda: BaselineQuestionSnapshot(
            QUESTION_SNAPSHOT_SCHEMA_VERSION,
            "FQ-equal-window",
            "career-future-equal-window",
            "测试等值时间戳",
            "binary",
            "positive",
            "negative",
            "2020-01-02T00:00:00.1Z",
            "2020-01-02T00:00:00.10Z",
            ArtifactReference("future-question.json", "1" * 64),
        ),
    )


def test_structural_probe_marker_cannot_be_promoted_to_prediction() -> None:
    probe = _draft(
        fundamentals=(
            _fundamental(center="STRUCTURAL_PROBE_ONLY: NO_CAREER_INFERENCE"),
        )
    )
    _assert_error("PROBE_NOT_PREDICTION", lambda: _run(draft=probe))


def test_unknown_frozen_source_id_is_rejected() -> None:
    state = BlindCurrentStateSnapshot(
        CURRENT_STATE_SCHEMA_VERSION,
        CASE_ID,
        AS_OF,
        "state-primary",
        (
            _state_hypothesis(
                "state-primary",
                BlindHypothesisRole.PRIMARY,
                decision_action=DecisionAction.OUTPUT,
                source_fundamental_ids=("unknown-fundamental",),
            ),
        ),
    )
    _assert_error("REFERENCE_MISMATCH", lambda: _run(current_state=state))


def test_wealth_prediction_without_explicit_edge_is_rejected() -> None:
    _assert_error(
        "INVALID_PROJECTION",
        lambda: _run(projection_input=_projection_input(include_wealth_binding=False)),
    )


def test_more_than_two_conditional_states_are_rejected() -> None:
    hypotheses = (
        _state_hypothesis(
            "state-primary",
            BlindHypothesisRole.PRIMARY,
            decision_action=DecisionAction.OUTPUT,
        ),
        _state_hypothesis(
            "state-c1",
            BlindHypothesisRole.CONDITIONAL,
            decision_action=DecisionAction.CONDITIONAL,
        ),
        _state_hypothesis(
            "state-c2",
            BlindHypothesisRole.CONDITIONAL,
            decision_action=DecisionAction.ASK,
        ),
        _state_hypothesis(
            "state-c3",
            BlindHypothesisRole.CONDITIONAL,
            decision_action=DecisionAction.CONDITIONAL,
        ),
    )
    _assert_error(
        "INVALID_VALUE",
        lambda: BlindCurrentStateSnapshot(
            CURRENT_STATE_SCHEMA_VERSION,
            CASE_ID,
            AS_OF,
            "state-primary",
            hypotheses,
        ),
    )


def test_conditional_branch_must_change_primary_career_conclusion() -> None:
    projection = _projection_input()
    candidates = tuple(
        replace(
            item,
            conclusion="internal responsibility expands",
        )
        if item.candidate_id == "career-external"
        else item
        for item in projection.candidates
    )
    _assert_error(
        "INVALID_PROJECTION",
        lambda: _run(
            projection_input=BlindProjectionInput(candidates, projection.wealth_bindings)
        ),
    )


def test_blind_runner_has_no_verification_or_adjudication_call_path() -> None:
    path = Path("engine/asof/blind_baseline.py")
    tree = ast.parse(path.read_text(encoding="utf-8"))
    forbidden = {
        "open_verification",
        "record_career_verification",
        "adjudicate_career_verifications",
        "build_career_states",
        "project_future_from_state",
    }
    imported: set[str] = set()
    called: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                called.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                called.add(node.func.attr)
    assert not forbidden.intersection(imported)
    assert not forbidden.intersection(called)


def _lineage_context(tmp_path: Path, result: object) -> BlindBaselineLineageContext:
    parent_path = (tmp_path.absolute() / "lineage" / "asof-bundle-manifest.json")
    parent = publish_new_json(
        parent_path,
        {
            "schema_version": "test-asof-parent/v1",
            "artifact_path": parent_path.as_posix(),
            "parents": [],
        },
        dry_run=False,
        admitted_root=tmp_path.absolute(),
    )
    return BlindBaselineLineageContext(
        _blind_input(),
        result.final_envelope.identity,
        result.final_envelope.blind_input_sha256,
        result.question_snapshot,
        result.runtime_snapshot,
        ArtifactReference(parent.artifact_path, parent.artifact_sha256),
    )


def _assert_archive_error(code: str, operation: Callable[[], object]) -> None:
    with pytest.raises(BlindBaselineArchiveError) as caught:
        operation()
    assert caught.value.code == code


def test_immutable_baseline_publication_reads_back_and_refuses_overwrite(
    tmp_path: Path,
) -> None:
    result = _run()
    context = _lineage_context(tmp_path, result)
    root = tmp_path.absolute()
    target = root / "baseline" / "blind-baseline-v001.json"

    published = publish_blind_baseline(
        result=result,
        context=context,
        artifact_path=target,
        admitted_root=root,
    )

    assert published.readback_verified is True
    assert published.artifact_path == target.as_posix()
    document = json.loads(target.read_text(encoding="utf-8"))
    assert document == published.document
    assert document["artifact_sha256"] == published.artifact_sha256
    assert document["artifact_kind"] == "BLIND_BASELINE"
    assert document["baseline_payload_sha256"] == blind_baseline_payload_sha256(
        document["baseline"]
    )
    original = target.read_bytes()

    _assert_archive_error(
        "PUBLICATION_ERROR",
        lambda: publish_blind_baseline(
            result=result,
            context=context,
            artifact_path=target,
            admitted_root=root,
        ),
    )
    assert target.read_bytes() == original


def test_archive_rejects_lineage_snapshot_mismatch_before_writing(
    tmp_path: Path,
) -> None:
    result = _run()
    context = _lineage_context(tmp_path, result)
    mismatched = replace(
        context,
        runtime_snapshot=replace(context.runtime_snapshot, model_id="other-model"),
    )
    target = tmp_path.absolute() / "baseline" / "blind-baseline-v001.json"

    _assert_archive_error(
        "LINEAGE_MISMATCH",
        lambda: publish_blind_baseline(
            result=result,
            context=mismatched,
            artifact_path=target,
            admitted_root=tmp_path.absolute(),
        ),
    )
    assert not target.exists()


def test_lineage_loader_uses_sealed_question_rule_and_asof_identity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result = _run()
    root = tmp_path.absolute()
    single_root = root / "single-case-bundle"
    single_root.mkdir()
    rule_path = single_root / "rule-snapshot.json"
    rule_path.write_text(
        json.dumps(
            {"rule_snapshot_id": "sealed-rules-v1", "sha256": "7" * 64},
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    rule_digest = __import__("hashlib").sha256(rule_path.read_bytes()).hexdigest()
    single_manifest_path = single_root / "bundle-manifest.json"
    single_ref = {
        "artifact_path": single_manifest_path.as_posix(),
        "artifact_sha256": "8" * 64,
    }
    question = {
        "future_task_id": "career-future-sealed",
        "artifact_path": (root / "future-question-v001.json").as_posix(),
        "artifact_sha256": "9" * 64,
        "question_text_redacted": "未来窗口是否发生职责层级上升？",
        "outcome_type": "binary",
        "positive_definition": "发生可核验的职责层级上升",
        "negative_definition": "完整窗口内未发生",
        "observation_window": {
            "start_at": "2020-01-02T00:00:00Z",
            "end_at": "2020-04-02T00:00:00Z",
        },
    }
    asof_manifest = {
        "artifact_path": (root / "asof-bundle" / "bundle-manifest.json").as_posix(),
        "artifact_sha256": "a" * 64,
        "parents": [single_ref, {"artifact_path": "request.json", "artifact_sha256": "b" * 64}],
    }

    monkeypatch.setattr(
        "engine.asof.blind_baseline_archive._verify_asof_bundle",
        lambda bundle_root: {
            "manifest": asof_manifest,
            "blind_input": _blind_input(),
            "identity": result.final_envelope.identity,
            "initial_envelope": result.final_envelope,
        },
    )
    monkeypatch.setattr(
        "engine.asof.blind_baseline_archive._verify_single_bundle",
        lambda bundle_root: {
            "manifest": {
                **single_ref,
                "files": {"rule-snapshot.json": rule_digest},
            },
            "future_question": question,
        },
    )

    context = load_blind_baseline_lineage_context(
        asof_bundle_root=root / "asof-bundle",
        code_version="phase1-proof",
        model_id="human-practitioner-v1",
    )

    assert context.identity == result.final_envelope.identity
    assert context.blind_input_sha256 == result.final_envelope.blind_input_sha256
    assert context.question_snapshot.task_id == "career-future-sealed"
    assert context.question_snapshot.source.artifact_sha256 == "9" * 64
    assert context.runtime_snapshot.rule_snapshot_id == "sealed-rules-v1"
    assert context.runtime_snapshot.rule_snapshot_sha256 == "7" * 64
    assert context.parent == ArtifactReference(asof_manifest["artifact_path"], "a" * 64)

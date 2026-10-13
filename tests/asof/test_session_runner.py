from __future__ import annotations

import ast
import importlib
import inspect
from dataclasses import FrozenInstanceError, fields, is_dataclass
from datetime import date
from pathlib import Path
from types import ModuleType
from typing import Any, get_type_hints

import pytest

from engine.asof.career_state_builder import (
    CAREER_IMPACT_SUGGESTION_SCHEMA_VERSION,
    CareerFundamentalAdjudication,
    CareerImpactAdjudication,
    CareerImpactSuggestion,
    CareerStateBuilderError,
)
from engine.asof.consultation_freeze import (
    VERIFICATION_SCHEMA_VERSION,
    CareerBlindDraft,
    ConsultationFreezeError,
    FrozenCareerEvent,
    FrozenCareerFundamental,
    VerificationInput,
    VerificationVerdict,
    compute_freeze_package_sha256,
    freeze_career_draft,
)
from engine.asof.event_candidate import (
    AnnualInteractionTrace,
    CompletionMode,
    ExtensionBoundary,
    LifeEventCandidate,
    RootLevel,
    VerificationStatus,
)
from engine.asof.future_projection import CareerFutureCandidate, FutureProjectionError
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
    SessionContractError,
    SessionIdentity,
    create_initial_envelope,
    transition_session,
)
from engine.asof.state_ledger import ImpactLevel, ImpactScope, Persistence


MODULE_NAME = "engine.asof.session_runner"
CASE_ID = "C-2026-001-乾-庚申戊寅壬子辛丑"
AS_OF = date(2020, 1, 1)
SESSION_ID = "S-20260727T120000Z-0123abcd"


def _api() -> ModuleType:
    """执行期加载 wished-for Unit-7 API，使 RED 完成 collection 后失败。"""

    return importlib.import_module(MODULE_NAME)


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
        (DaiyunInput(1, "己", "卯", date(2010, 1, 1), date(2020, 1, 1)),),
    )


def _identity() -> SessionIdentity:
    return SessionIdentity(SESSION_SCHEMA_VERSION, CASE_ID, AS_OF, SESSION_ID)


def _evidence() -> EvidenceRef:
    return EvidenceRef("cases/C-2026-001/input.md", "四柱.年柱", "庚申")


def _fundamental() -> FrozenCareerFundamental:
    return FrozenCareerFundamental(
        "career-baseline",
        date(2019, 1, 1),
        AS_OF,
        date(2019, 7, 2),
        "mid-level professional",
        ("skilled individual contributor", "team lead"),
        "independent specialist",
        ("no sustained professional responsibility",),
    )


def _point(name: str = "internal promotion", direction: str = "authority_up") -> LandingPoint:
    return LandingPoint(name, "career", direction)


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
    landing_set = FrozenLandingSet(
        "responsibility_level_change",
        _point(),
        (_point("team scope expanded"),),
        "title-only change is weak",
        ("responsibility unchanged",),
        ("income-only change",),
        "landing-v1-before-outcome",
    )
    return FrozenCareerEvent(candidate, landing_set)


def _draft() -> CareerBlindDraft:
    return CareerBlindDraft((_fundamental(),), (_event(),))


def _freeze_digest(blind_input: BlindChartInput, draft: CareerBlindDraft) -> str:
    envelope = transition_session(
        create_initial_envelope(_identity(), blind_input),
        ConsultationState.BLIND_DRAFTED,
    )
    _, package = freeze_career_draft(envelope, draft)
    return compute_freeze_package_sha256(package)


def _run_kwargs(*, verdict: VerificationVerdict = VerificationVerdict.CONFIRMED) -> dict[str, Any]:
    blind_input = _blind_input()
    draft = _draft()
    digest = _freeze_digest(blind_input, draft)
    rejected = verdict is VerificationVerdict.REJECTED
    actual = _point("career exit", "career_down") if rejected else _point()
    verification = VerificationInput(
        VERIFICATION_SCHEMA_VERSION,
        digest,
        "career-event-2019",
        verdict,
        actual,
        None,
        (),
    )
    suggestions: tuple[CareerImpactSuggestion, ...] = ()
    adjudications: tuple[CareerImpactAdjudication, ...] = ()
    if not rejected:
        suggestions = (
            CareerImpactSuggestion(
                schema_version=CAREER_IMPACT_SUGGESTION_SCHEMA_VERSION,
                freeze_package_sha256=digest,
                item_id="career-event-2019",
                event_date=date(2019, 7, 1),
                suggested_impact=ImpactLevel.MAJOR,
                suggested_persistence=Persistence.CROSS_DAIYUN,
                suggested_scope=ImpactScope.PRIMARY_DOMAIN,
                suggested_short_term_until=None,
                state_value="career responsibility expanded",
                opened_path_ids=(),
                closed_path_ids=(),
            ),
        )
        adjudications = (
            CareerImpactAdjudication(
                digest,
                "career-event-2019",
                ImpactLevel.MAJOR,
                Persistence.CROSS_DAIYUN,
                ImpactScope.PRIMARY_DOMAIN,
                None,
                "practitioner reviewed frozen evidence",
                "",
                "",
                (),
                (),
                "",
                "",
            ),
        )
    return {
        "session_schema_version": SESSION_SCHEMA_VERSION,
        "case_id": CASE_ID,
        "as_of_date": AS_OF,
        "session_id": SESSION_ID,
        "blind_input": blind_input,
        "draft": draft,
        "verifications": (verification,),
        "suggestions": suggestions,
        "impact_adjudications": adjudications,
        "fundamental_adjudication": CareerFundamentalAdjudication(
            digest,
            "career-baseline",
            "best fit after verification",
        ),
        "daiyun_end": date(2024, 12, 31),
    }


def test_public_signature_return_contract_and_immutability() -> None:
    api = _api()
    signature = inspect.signature(api.run_career_session)
    assert tuple(signature.parameters) == (
        "session_schema_version",
        "case_id",
        "as_of_date",
        "session_id",
        "blind_input",
        "draft",
        "verifications",
        "suggestions",
        "impact_adjudications",
        "fundamental_adjudication",
        "daiyun_end",
        "career_candidates",
        "wealth_bindings",
    )
    assert all(parameter.kind is inspect.Parameter.KEYWORD_ONLY for parameter in signature.parameters.values())
    assert signature.parameters["career_candidates"].default is None
    assert signature.parameters["wealth_bindings"].default is None
    hints = get_type_hints(api.run_career_session)
    assert hints["return"] is api.SessionRunResult
    assert is_dataclass(api.SessionRunResult)
    assert api.SessionRunResult.__dataclass_params__.frozen is True
    assert "__dict__" not in api.SessionRunResult.__dict__
    assert tuple(field.name for field in fields(api.SessionRunResult)) == (
        "final_envelope",
        "freeze_package",
        "adjudication_bundle",
        "state_result",
        "projection",
    )
    result = api.run_career_session(**_run_kwargs())
    with pytest.raises(FrozenInstanceError):
        result.projection = None


def test_full_success_stops_at_state_built_without_future_inputs() -> None:
    api = _api()
    result = api.run_career_session(**_run_kwargs())
    assert result.final_envelope.state is ConsultationState.STATE_BUILT
    assert result.state_result.envelope == result.final_envelope
    assert result.projection is None
    assert result.adjudication_bundle.envelope.state is ConsultationState.ADJUDICATED
    assert result.freeze_package.identity == result.final_envelope.identity


def test_future_candidates_produce_projected_result() -> None:
    api = _api()
    kwargs = _run_kwargs(verdict=VerificationVerdict.REJECTED)
    kwargs["career_candidates"] = (
        CareerFutureCandidate(CASE_ID, AS_OF, "future-mainline", "事业路径继续展开", (), ()),
    )
    result = api.run_career_session(**kwargs)
    assert result.final_envelope.state is ConsultationState.PROJECTED
    assert result.projection is not None
    assert result.projection.envelope == result.final_envelope
    assert tuple(item.candidate_id for item in result.projection.career_mainline) == ("future-mainline",)
    assert result.state_result.envelope.state is ConsultationState.STATE_BUILT


def test_explicitly_omitted_future_inputs_never_call_projection(monkeypatch: pytest.MonkeyPatch) -> None:
    api = _api()
    calls = 0

    def forbidden_projection(**_: object) -> object:
        nonlocal calls
        calls += 1
        raise AssertionError("projection must not be called")

    monkeypatch.setattr(api, "project_future_from_state", forbidden_projection)
    result = api.run_career_session(**_run_kwargs())
    assert result.projection is None
    assert calls == 0


@pytest.mark.parametrize(
    ("stage", "error"),
    (
        ("initial", SessionContractError("TEST", "initial")),
        ("freeze", ConsultationFreezeError("TEST", "freeze")),
        ("adjudicate", CareerStateBuilderError("TEST", "adjudicate")),
        ("project", FutureProjectionError("INVALID_VALUE", "project")),
    ),
    ids=("session-contract", "consultation-freeze", "career-state-builder", "future-projection"),
)
def test_stage_exceptions_are_same_instances(
    stage: str,
    error: Exception,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api = _api()
    function_name = {
        "initial": "create_initial_envelope",
        "freeze": "freeze_career_draft",
        "adjudicate": "adjudicate_career_verifications",
        "project": "project_future_from_state",
    }[stage]

    def fail(*_: object, **__: object) -> object:
        raise error

    monkeypatch.setattr(api, function_name, fail)
    kwargs = _run_kwargs(verdict=VerificationVerdict.REJECTED if stage == "project" else VerificationVerdict.CONFIRMED)
    if stage == "project":
        kwargs["career_candidates"] = ()
    with pytest.raises(type(error)) as caught:
        api.run_career_session(**kwargs)
    assert caught.value is error


def test_runner_ast_has_only_authorized_boundaries_and_public_names() -> None:
    api = _api()
    target = Path("engine/asof/session_runner.py")
    assert target.is_file()
    tree = ast.parse(target.read_text(encoding="utf-8"))
    imported = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }
    forbidden_tokens = (
        "runner_registry",
        "pipeline_runner",
        "render_report",
        "production_service",
        "production_api",
        "production_as_of_cli",
        "engine.archive",
        "engine.asof.archive_integration",
    )
    assert not any(token in module for token in forbidden_tokens for module in imported)
    assert not any(isinstance(node, ast.Try) for node in ast.walk(tree))
    assert api.__all__ == ("SessionRunResult", "run_career_session")

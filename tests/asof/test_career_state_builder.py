from __future__ import annotations

import ast
import hashlib
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import date, datetime
from pathlib import Path
from types import ModuleType
from typing import Any, Callable

import pytest

from engine.asof.consultation_freeze import (
    FREEZE_PACKAGE_SCHEMA_VERSION,
    VERIFICATION_SCHEMA_VERSION,
    CareerBlindDraft,
    CareerFreezePackage,
    CareerVerificationRecord,
    FrozenCareerEvent,
    FrozenCareerFundamental,
    VerificationInput,
    VerificationVerdict,
    compute_freeze_package_sha256,
    freeze_career_draft,
    open_verification,
    record_career_verification,
)
from engine.asof.event_candidate import (
    AnnualInteractionTrace,
    CompletionMode,
    ExtensionBoundary,
    LifeEventCandidate,
    RootLevel,
    VerificationStatus,
)
from engine.asof.reality_translation import (
    FrozenLandingSet,
    LandingPoint,
    LandingVerdict,
    RealityConstraint,
)
from engine.asof.session_contract import (
    SESSION_SCHEMA_VERSION,
    ConsultationState,
    SessionEnvelope,
    SessionIdentity,
)
from engine.asof.state_ledger import (
    DecisionAction,
    EventLedgerEntry,
    HypothesisState,
    ImpactLevel,
    ImpactScope,
    Persistence,
    VerifiedState,
)
from engine.asof.natal_capacity import EvidenceRef, SourceCitation


MODULE_NAME = "engine.asof.career_state_builder"
CASE_ID = "C-2026-001-乾-庚申戊寅壬子辛丑"
ERROR_CODES = {
    "INVALID_TYPE",
    "INVALID_VALUE",
    "SCHEMA_MISMATCH",
    "DUPLICATE_ID",
    "INVALID_STATE",
    "HASH_MISMATCH",
    "UNKNOWN_FIELD",
    "ITEM_NOT_FOUND",
}
CAREER_IMPACT_SUGGESTION_SCHEMA_VERSION = "asof-career-impact-suggestion/v1"
PROTECTED_BASELINE = {
    "engine/asof/consultation_freeze.py": "12f82f56aa1b04e1af68a8e664dceee10b2bb21610f31051dc64fbc09aecfd27",
    "engine/asof/state_ledger.py": "ea44d41939c0a64f168b516f0bfdbf29816663ab6289cfc4db5b1eaccd3861a0",
    "engine/asof/session_contract.py": "1e2d67b09b20548c9ad728fb52e8ae9810844118dc2320e5b9412410573ae33e",
    "engine/asof/event_candidate.py": "ba7a7cb26ab65f277db7e8a0514264c73b779c7aaf0cf4270512caf581d7ef65",
    "engine/asof/reality_translation.py": "08f5b55ecff673e87ff8fc8dd6fc054b211b3f27473f3468c3f52f6f132bdf8d",
    "engine/asof/__init__.py": "e823e161de220edd62978ef6fb445d2fd39f4f064408002ae1d38fb3ed09ed3a",
    "tests/asof/test_consultation_freeze.py": "b105f5e550529a61833b7a0dcc358958295a2a3b1adfe944ff4f8bf579d5db79",
    "tests/asof/test_state_ledger.py": "2ca9e31891dea8a55d675e74603a084a9e03669ac27ee4e9c76abdb369a7403a",
}


def _api() -> ModuleType:
    """执行期才加载 wished-for Unit-3 API，保证 RED 可完整收集。"""

    return importlib.import_module(MODULE_NAME)


def _identity(**changes: Any) -> SessionIdentity:
    values = {
        "schema_version": SESSION_SCHEMA_VERSION,
        "case_id": CASE_ID,
        "as_of_date": date(2020, 1, 1),
        "session_id": "S-20260727T120000Z-0123abcd",
    }
    values.update(changes)
    return SessionIdentity(**values)


def _envelope(state: ConsultationState = ConsultationState.BLIND_DRAFTED, **changes: Any) -> SessionEnvelope:
    values = {"identity": _identity(), "blind_input_sha256": "1" * 64, "state": state}
    values.update(changes)
    return SessionEnvelope(**values)


def _unchecked_replace(value: Any, **changes: Any) -> Any:
    clone = object.__new__(type(value))
    for field in fields(value):
        object.__setattr__(clone, field.name, changes.get(field.name, getattr(value, field.name)))
    return clone


def _evidence(locator: str = "四柱.年柱") -> EvidenceRef:
    return EvidenceRef("cases/C-2026-001/input.md", locator, "庚申")


def _fundamental(identifier: str = "career-baseline") -> FrozenCareerFundamental:
    return FrozenCareerFundamental(
        fundamental_id=identifier,
        window_start=date(2019, 1, 1),
        window_end=date(2020, 1, 1),
        window_center=date(2019, 7, 2),
        center="mid-level professional",
        reasonable_range=("skilled individual contributor", "team lead"),
        strongest_alternative="independent specialist",
        falsifiers=("no sustained professional responsibility",),
    )


def _candidate(identifier: str = "career-event-2019") -> LifeEventCandidate:
    evidence = _evidence()
    trace = AnnualInteractionTrace(
        year=2019,
        liunian="己亥",
        dayun_ganzhi="庚辰",
        relations=(evidence,),
        activated_node_ids=("career-authority",),
        domains=("career",),
        supporting_evidence=(evidence,),
        counter_evidence=(),
        trigger_strength="high",
        crossed_candidate_gate=True,
    )
    return LifeEventCandidate(
        candidate_id=identifier,
        domain="career",
        event_type="responsibility_level_change",
        window_start=date(2019, 1, 1),
        window_end=date(2019, 12, 31),
        natal_evidence=(evidence,),
        daiyun_evidence=(evidence,),
        annual_trace=trace,
        root_level=RootLevel.STRONG_ROOT,
        root_evidence=(evidence,),
        source_citations=(SourceCitation("sources/gao/example.md", 1, "原局有根，岁运引动"),),
        completion_mode=CompletionMode.ACTIVATE_EXISTING,
        supporting_evidence=(evidence,),
        counter_evidence=(),
        alternative_hypotheses=("scope changed without title",),
        frozen_version="asof-prototype-v1",
        verification_status=VerificationStatus.FROZEN,
        extension_boundary=ExtensionBoundary.CROSS_DAIYUN_ELIGIBLE,
        is_primary_event=True,
    )


def _point(name: str = "internal promotion", direction: str = "authority_up") -> LandingPoint:
    return LandingPoint(name=name, domain="career", direction=direction)


def _event(identifier: str = "career-event-2019") -> FrozenCareerEvent:
    return FrozenCareerEvent(
        candidate=_candidate(identifier),
        landing_set=FrozenLandingSet(
            function_candidate="responsibility_level_change",
            center=_point(),
            alternatives=(_point("team scope expanded"),),
            weak_hit_boundary="title-only change is weak",
            falsifiers=("responsibility unchanged",),
            exclusions=("income-only change",),
            frozen_version="landing-v1-before-outcome",
        ),
    )


def _frozen(*, two_fundamentals: bool = False) -> tuple[SessionEnvelope, CareerFreezePackage]:
    fundamentals = (_fundamental(),)
    if two_fundamentals:
        fundamentals += (_fundamental("career-alternative"),)
    return freeze_career_draft(
        _envelope(),
        CareerBlindDraft(fundamentals=fundamentals, events=(_event(),)),
    )


def _verification(package: CareerFreezePackage, verdict: VerificationVerdict) -> VerificationInput:
    actual: LandingPoint | None = None
    constraint: RealityConstraint | None = None
    taxonomy: tuple[str, ...] = ()
    if verdict is VerificationVerdict.CONFIRMED:
        actual = _point()
    elif verdict is VerificationVerdict.PARTIAL_HIT:
        actual = _point("team scope expanded")
    elif verdict is VerificationVerdict.REJECTED:
        actual = _point("career exit", "career_down")
    elif verdict is VerificationVerdict.UNKNOWN:
        actual = _point("portfolio career")
        constraint = RealityConstraint("career-path", "verified career path", (), ("internal promotion",), True)
        taxonomy = ("source", "chart", "case")
    return VerificationInput(
        schema_version=VERIFICATION_SCHEMA_VERSION,
        freeze_package_sha256=compute_freeze_package_sha256(package),
        item_id="career-event-2019",
        verdict=verdict,
        actual_landing=actual,
        reality_constraint=constraint,
        taxonomy_evidence=taxonomy,
    )


def _record(verdict: VerificationVerdict = VerificationVerdict.CONFIRMED) -> tuple[CareerFreezePackage, CareerVerificationRecord]:
    frozen, package = _frozen()
    opened = open_verification(frozen, package, compute_freeze_package_sha256(package))
    return package, record_career_verification(opened, package, _verification(package, verdict))


def _suggestion(api: ModuleType, package: CareerFreezePackage, **changes: Any) -> Any:
    values = {
        "schema_version": CAREER_IMPACT_SUGGESTION_SCHEMA_VERSION,
        "freeze_package_sha256": compute_freeze_package_sha256(package),
        "item_id": "career-event-2019",
        "event_date": date(2019, 7, 1),
        "suggested_impact": ImpactLevel.MAJOR,
        "suggested_persistence": Persistence.CROSS_DAIYUN,
        "suggested_scope": ImpactScope.PRIMARY_DOMAIN,
        "suggested_short_term_until": None,
        "state_value": "career responsibility expanded",
        "opened_path_ids": (),
        "closed_path_ids": (),
    }
    values.update(changes)
    return api.CareerImpactSuggestion(**values)


def _adjudication(
    api: ModuleType,
    package: CareerFreezePackage,
    verdict: VerificationVerdict = VerificationVerdict.CONFIRMED,
    **changes: Any,
) -> Any:
    hypothesis_fields = {
        "condition": "若职责扩张已实际发生",
        "difference_from_verified": "职业责任范围高于已核验基点",
        "changed_fundamental_ids": ("career-baseline",),
        "changed_future_conclusions": ("后续事业起点上移",),
        "minimum_question": "职责范围是否已正式扩大？",
        "falsifier": "职责与权限均未变化",
    }
    values = {
        "freeze_package_sha256": compute_freeze_package_sha256(package),
        "item_id": "career-event-2019",
        "final_impact": ImpactLevel.MAJOR,
        "final_persistence": Persistence.CROSS_DAIYUN,
        "final_scope": ImpactScope.PRIMARY_DOMAIN,
        "final_short_term_until": None,
        "adjustment_reason": "practitioner reviewed frozen evidence",
        **({key: "" if isinstance(value, str) else () for key, value in hypothesis_fields.items()}
           if verdict is VerificationVerdict.CONFIRMED else hypothesis_fields),
    }
    values.update(changes)
    return api.CareerImpactAdjudication(**values)


def _fundamental_adjudication(
    api: ModuleType,
    package: CareerFreezePackage,
    selected: str = "career-baseline",
) -> Any:
    return api.CareerFundamentalAdjudication(
        freeze_package_sha256=compute_freeze_package_sha256(package),
        selected_fundamental_id=selected,
        reason="best fit after verification",
    )


def _adjudicate(
    api: ModuleType,
    *,
    verdict: VerificationVerdict = VerificationVerdict.CONFIRMED,
    suggestion: Any | None = None,
    adjudication: Any | None = None,
    fundamental: Any | None = None,
) -> Any:
    package, record = _record(verdict)
    rejected = verdict is VerificationVerdict.REJECTED
    suggestions = () if rejected else (_suggestion(api, package) if suggestion is None else suggestion,)
    adjudications = () if rejected else (
        _adjudication(api, package, verdict) if adjudication is None else adjudication,
    )
    return api.adjudicate_career_verifications(
        record.envelope,
        package,
        (record,),
        suggestions,
        adjudications,
        _fundamental_adjudication(api, package) if fundamental is None else fundamental,
    )


def _assert_builder_error(api: ModuleType, code: str, operation: Callable[[], Any]) -> None:
    with pytest.raises(api.CareerStateBuilderError) as caught:
        operation()
    assert caught.value.code == code
    assert caught.value.code in ERROR_CODES


@pytest.mark.parametrize(
    ("verdict", "landing", "writes_ledger", "writes_fact", "allows_hypothesis"),
    [
        (VerificationVerdict.CONFIRMED, LandingVerdict.CENTER_HIT, True, True, False),
        (VerificationVerdict.PARTIAL_HIT, LandingVerdict.ALTERNATIVE_HIT, True, False, True),
        (VerificationVerdict.REJECTED, LandingVerdict.MISS, False, False, False),
        (VerificationVerdict.UNKNOWN, LandingVerdict.TAXONOMY_GAP, True, False, True),
        (VerificationVerdict.WITHHELD, None, True, False, True),
    ],
    ids=("confirmed", "partial", "rejected", "unknown", "withheld"),
)
def test_verdict_matrix_controls_ledger_fact_and_hypothesis(
    verdict: VerificationVerdict,
    landing: LandingVerdict | None,
    writes_ledger: bool,
    writes_fact: bool,
    allows_hypothesis: bool,
) -> None:
    api = _api()
    package, record = _record(verdict)
    assert record.landing_verdict is landing
    bundle = _adjudicate(api, verdict=verdict)
    result = api.build_career_states(bundle, date(2024, 12, 31))
    assert bool(result.ledger_entries) is writes_ledger
    assert ("career-event-2019" in result.verified_state.verified_event_ids) is writes_fact
    assert bool(result.hypothesis_states) is allows_hypothesis
    assert bundle.freeze_package_sha256 == compute_freeze_package_sha256(package)


@pytest.mark.parametrize(
    ("suggested_persistence", "suggested_until", "final_persistence", "final_until"),
    [
        (Persistence.SHORT_TERM, None, Persistence.CROSS_DAIYUN, None),
        (Persistence.CROSS_DAIYUN, None, Persistence.SHORT_TERM, None),
        (Persistence.CROSS_DAIYUN, date(2020, 6, 30), Persistence.CROSS_DAIYUN, None),
        (Persistence.CROSS_DAIYUN, None, Persistence.PERMANENT, date(2020, 9, 30)),
    ],
    ids=("suggested-short-missing", "final-short-missing", "suggested-non-short-has", "final-non-short-has"),
)
def test_suggested_and_final_expiry_are_independent_without_fallback(
    suggested_persistence: Persistence,
    suggested_until: date | None,
    final_persistence: Persistence,
    final_until: date | None,
) -> None:
    api = _api()
    package, record = _record()
    operation = lambda: api.adjudicate_career_verifications(
        record.envelope,
        package,
        (record,),
        (_suggestion(
            api,
            package,
            suggested_persistence=suggested_persistence,
            suggested_short_term_until=suggested_until,
        ),),
        (_adjudication(
            api,
            package,
            final_persistence=final_persistence,
            final_short_term_until=final_until,
        ),),
        _fundamental_adjudication(api, package),
    )
    _assert_builder_error(api, "INVALID_VALUE", operation)


@pytest.mark.parametrize(
    ("selected", "expected_code"),
    [
        ("career-baseline", None),
        (None, "INVALID_VALUE"),
        ("not-frozen", "ITEM_NOT_FOUND"),
    ],
    ids=("exactly-one", "missing", "outside-package"),
)
def test_fundamental_selection_is_exactly_one_frozen_choice(selected: str | None, expected_code: str | None) -> None:
    api = _api()
    package, record = _record()
    operation = lambda: api.adjudicate_career_verifications(
        record.envelope,
        package,
        (record,),
        (_suggestion(api, package),),
        (_adjudication(api, package),),
        api.CareerFundamentalAdjudication(
            freeze_package_sha256=compute_freeze_package_sha256(package),
            selected_fundamental_id=selected,
            reason="best fit after verification",
        ),
    )
    if expected_code is not None:
        _assert_builder_error(api, expected_code, operation)
    else:
        bundle = operation()
        assert bundle.fundamental.fundamental_id == selected
        assert sum(item.fundamental_id == selected for item in package.fundamentals) == 1


@pytest.mark.parametrize(
    ("case", "expected_code"),
    (
        ("valid", None),
        ("foreign-package", "INVALID_VALUE"),
        ("wrong-hash", "HASH_MISMATCH"),
        ("wrong-record-id", "ITEM_NOT_FOUND"),
        ("wrong-suggestion-id", "ITEM_NOT_FOUND"),
        ("wrong-adjudication-id", "ITEM_NOT_FOUND"),
    ),
)
def test_record_package_hash_and_item_id_binding(case: str, expected_code: str | None) -> None:
    api = _api()
    package, record = _record()
    suggestion = _suggestion(api, package)
    adjudication = _adjudication(api, package)
    if case == "foreign-package":
        foreign_identity = replace(package.identity, session_id="S-20260727T120000Z-deadbeef")
        package = replace(package, identity=foreign_identity, schema_version=FREEZE_PACKAGE_SCHEMA_VERSION)
    elif case == "wrong-hash":
        record = replace(record, freeze_package_sha256="0" * 64)
    elif case == "wrong-record-id":
        record = replace(record, item_id="foreign-event")
    elif case == "wrong-suggestion-id":
        suggestion = _suggestion(api, package, item_id="foreign-event")
    elif case == "wrong-adjudication-id":
        adjudication = _adjudication(api, package, item_id="foreign-event")
    operation = lambda: api.adjudicate_career_verifications(
        record.envelope,
        package,
        (record,),
        (suggestion,),
        (adjudication,),
        _fundamental_adjudication(api, package),
    )
    if expected_code is None:
        assert operation().freeze_package_sha256 == compute_freeze_package_sha256(package)
    else:
        _assert_builder_error(api, expected_code, operation)


@pytest.mark.parametrize(
    ("case", "code"),
    [
        ("state-before-type", "INVALID_STATE"),
        ("package-before-hash", "INVALID_TYPE"),
        ("hash-before-id", "HASH_MISMATCH"),
        ("record-id-before-duplicate", "ITEM_NOT_FOUND"),
        ("duplicate-before-adjudication", "DUPLICATE_ID"),
        ("suggestion-schema-before-final", "SCHEMA_MISMATCH"),
        ("final-shape-before-fundamental", "INVALID_TYPE"),
        ("fundamental-last", "INVALID_VALUE"),
    ],
)
def test_competing_errors_have_deterministic_precedence(case: str, code: str) -> None:
    api = _api()
    package, record = _record()
    envelope: Any = record.envelope
    records: Any = (record,)
    suggestions: Any = (_suggestion(api, package),)
    adjudications: Any = (_adjudication(api, package),)
    fundamental: Any = _fundamental_adjudication(api, package)
    if case == "state-before-type":
        envelope, package = replace(envelope, state=ConsultationState.FROZEN), object()
    elif case == "package-before-hash":
        package = object.__new__(CareerFreezePackage)
        records = (replace(record, freeze_package_sha256="0" * 64),)
    elif case == "hash-before-id":
        records = (replace(record, freeze_package_sha256="0" * 64, item_id="foreign"),)
    elif case == "record-id-before-duplicate":
        bad = replace(record, item_id="foreign")
        records = (bad, bad)
    elif case == "duplicate-before-adjudication":
        records, adjudications = (record, record), (object(),)
    elif case == "suggestion-schema-before-final":
        suggestions = (replace(suggestions[0], schema_version="foreign-schema"),)
        adjudications = (object(),)
    elif case == "final-shape-before-fundamental":
        adjudications, fundamental = (object.__new__(api.CareerImpactAdjudication),), None
    elif case == "fundamental-last":
        fundamental = api.CareerFundamentalAdjudication(
            freeze_package_sha256=compute_freeze_package_sha256(package),
            selected_fundamental_id=None,
            reason="none",
        )
    operation = lambda: api.adjudicate_career_verifications(
        envelope, package, records, suggestions, adjudications, fundamental
    )
    _assert_builder_error(api, code, operation)


@pytest.mark.parametrize(
    "case",
    ("date-vs-datetime", "tuple-vs-list", "enum-exact-type", "unknown-field-closed-slots", "duplicate-id"),
)
def test_public_models_use_exact_types_closed_slots_and_unique_ids(case: str) -> None:
    api = _api()
    package, record = _record()
    suggestion: Any = _suggestion(api, package)
    suggestions: Any = (suggestion,)
    code = "INVALID_TYPE"
    if case == "date-vs-datetime":
        object.__setattr__(suggestion, "event_date", datetime(2019, 7, 1))
    elif case == "tuple-vs-list":
        object.__setattr__(suggestion, "opened_path_ids", [])
    elif case == "enum-exact-type":
        object.__setattr__(suggestion, "suggested_impact", ImpactLevel.MAJOR.value)
    elif case == "unknown-field-closed-slots":
        assert all(
            is_dataclass(model) and "__slots__" in model.__dict__
            for model in (
                api.CareerImpactSuggestion,
                api.CareerImpactAdjudication,
                api.CareerFundamentalAdjudication,
                api.CareerAdjudicationBundle,
                api.CareerStateBuildResult,
            )
        )
        with pytest.raises(AttributeError):
            suggestion.uncontracted_field = "forbidden"
        _assert_builder_error(
            api,
            "UNKNOWN_FIELD",
            lambda: api.CareerImpactSuggestion(
                **{field.name: getattr(suggestion, field.name) for field in fields(suggestion)},
                uncontracted_field="forbidden",
            ),
        )
        return
    else:
        suggestions = (suggestion, suggestion)
        code = "DUPLICATE_ID"
    _assert_builder_error(
        api,
        code,
        lambda: api.adjudicate_career_verifications(
            record.envelope,
            package,
            (record,),
            suggestions,
            (_adjudication(api, package),),
            _fundamental_adjudication(api, package),
        ),
    )


@pytest.mark.parametrize(
    "case",
    (
        "wrong-source-state",
        "wrong-package-type",
        "record-hash",
        "record-id",
        "duplicate-record",
        "suggestion-type",
        "suggestion-id",
        "adjudication-type",
        "adjudication-id",
        "fundamental-missing",
        "build-wrong-state",
    ),
)
def test_every_failure_leaves_input_session_state_unchanged(case: str) -> None:
    api = _api()
    package, record = _record()
    envelope: Any = record.envelope
    records: Any = (record,)
    suggestions: Any = (_suggestion(api, package),)
    adjudications: Any = (_adjudication(api, package),)
    fundamental: Any = _fundamental_adjudication(api, package)
    if case == "wrong-source-state":
        envelope = replace(envelope, state=ConsultationState.FROZEN)
    elif case == "wrong-package-type":
        package = object()
    elif case == "record-hash":
        records = (replace(record, freeze_package_sha256="0" * 64),)
    elif case == "record-id":
        records = (replace(record, item_id="foreign"),)
    elif case == "duplicate-record":
        records = (record, record)
    elif case == "suggestion-type":
        suggestions = (object(),)
    elif case == "suggestion-id":
        suggestions = (_suggestion(api, package, item_id="foreign"),)
    elif case == "adjudication-type":
        adjudications = (object.__new__(api.CareerImpactAdjudication),)
    elif case == "adjudication-id":
        adjudications = (_adjudication(api, package, item_id="foreign"),)
    elif case == "fundamental-missing":
        fundamental = object.__new__(api.CareerFundamentalAdjudication)
    before = (envelope, package, records, suggestions, adjudications, fundamental)
    if case == "build-wrong-state":
        forged_record = _unchecked_replace(record, landing_verdict=LandingVerdict.MISS)
        forged_inputs = (envelope, package, forged_record, suggestions, adjudications, fundamental)
        _assert_builder_error(
            api,
            "INVALID_VALUE",
            lambda: api.adjudicate_career_verifications(
                envelope,
                package,
                (forged_record,),
                suggestions,
                adjudications,
                fundamental,
            ),
        )
        assert (envelope, package, forged_record, suggestions, adjudications, fundamental) == forged_inputs

        bundle = _adjudicate(api)
        foreign_identity = replace(bundle.envelope.identity, session_id="S-20260727T120000Z-deadbeef")
        decision = bundle.impact_adjudications[0]
        partial_bundle = _adjudicate(api, verdict=VerificationVerdict.PARTIAL_HIT)
        partial_decision = partial_bundle.impact_adjudications[0]
        forged_bundles = (
            (replace(bundle, envelope=replace(bundle.envelope, state=ConsultationState.VERIFICATION_OPEN)), "INVALID_STATE"),
            (replace(bundle, envelope=replace(bundle.envelope, identity=foreign_identity)), "INVALID_VALUE"),
            (replace(bundle, records=()), "ITEM_NOT_FOUND"),
            (replace(bundle, impact_adjudications=()), "ITEM_NOT_FOUND"),
            (replace(bundle, records=(_unchecked_replace(bundle.records[0], landing_verdict=LandingVerdict.MISS),)), "INVALID_VALUE"),
            (replace(bundle, records=(_unchecked_replace(bundle.records[0], envelope=object()),)), "INVALID_TYPE"),
            (
                replace(
                    bundle,
                    impact_adjudications=(
                        replace(decision, suggestion=replace(decision.suggestion, event_date=date(2018, 12, 31))),
                    ),
                ),
                "INVALID_VALUE",
            ),
            (replace(bundle, impact_adjudications=(replace(decision, final_impact=ImpactLevel.TURNING_POINT),)), "INVALID_VALUE"),
            (
                replace(
                    partial_bundle,
                    impact_adjudications=(replace(partial_decision, difference_from_verified=""),),
                ),
                "INVALID_VALUE",
            ),
            (
                replace(bundle, impact_adjudications=(replace(decision, condition="unexpected hypothesis"),)),
                "INVALID_VALUE",
            ),
        )
        for bad_bundle, expected_code in forged_bundles:
            snapshot = bad_bundle
            _assert_builder_error(
                api,
                expected_code,
                lambda bad_bundle=bad_bundle: api.build_career_states(bad_bundle, date(2024, 12, 31)),
            )
            assert bad_bundle == snapshot
    else:
        operation = lambda: api.adjudicate_career_verifications(
            envelope, package, records, suggestions, adjudications, fundamental
        )
        with pytest.raises(api.CareerStateBuilderError):
            operation()
        assert (envelope, package, records, suggestions, adjudications, fundamental) == before


def test_only_adjacent_verification_to_adjudicated_to_state_built_transitions() -> None:
    api = _api()
    bundle = _adjudicate(api)
    assert bundle.envelope.state is ConsultationState.ADJUDICATED
    result = api.build_career_states(bundle, date(2024, 12, 31))
    assert result.envelope.state is ConsultationState.STATE_BUILT
    package, record = _record()
    _assert_builder_error(
        api,
        "INVALID_STATE",
        lambda: api.adjudicate_career_verifications(
            replace(record.envelope, state=ConsultationState.ADJUDICATED),
            package,
            (record,),
            (_suggestion(api, package),),
            (_adjudication(api, package),),
            _fundamental_adjudication(api, package),
        ),
    )


def test_verified_fact_and_hypothesis_outputs_are_physically_separate() -> None:
    api = _api()
    confirmed = api.build_career_states(
        _adjudicate(api, verdict=VerificationVerdict.CONFIRMED), date(2024, 12, 31)
    )
    partial = api.build_career_states(
        _adjudicate(api, verdict=VerificationVerdict.PARTIAL_HIT), date(2024, 12, 31)
    )
    assert type(confirmed.verified_state) is VerifiedState
    assert all(type(branch) is HypothesisState for branch in partial.hypothesis_states)
    assert "career-event-2019" in confirmed.verified_state.verified_event_ids
    assert "career-event-2019" not in partial.verified_state.verified_event_ids
    assert not set(fields(VerifiedState)) == set(fields(HypothesisState))


def test_adjudication_and_state_build_are_deterministic_and_immutable() -> None:
    api = _api()
    package, record = _record()
    suggestion = _suggestion(
        api,
        package,
        suggested_persistence=Persistence.SHORT_TERM,
        suggested_short_term_until=date(2020, 6, 30),
    )
    adjudication = _adjudication(
        api,
        package,
        final_persistence=Persistence.SHORT_TERM,
        final_short_term_until=date(2020, 9, 30),
    )
    operation = lambda: api.adjudicate_career_verifications(
        record.envelope,
        package,
        (record,),
        (suggestion,),
        (adjudication,),
        _fundamental_adjudication(api, package),
    )
    _assert_builder_error(
        api,
        "INVALID_VALUE",
        lambda: api.adjudicate_career_verifications(
            record.envelope,
            package,
            (record,),
            (replace(suggestion, suggested_short_term_until=date(2019, 7, 1)),),
            (adjudication,),
            _fundamental_adjudication(api, package),
        ),
    )
    _assert_builder_error(
        api,
        "INVALID_VALUE",
        lambda: api.adjudicate_career_verifications(
            record.envelope,
            package,
            (record,),
            (suggestion,),
            (replace(adjudication, final_short_term_until=date(2019, 7, 1)),),
            _fundamental_adjudication(api, package),
        ),
    )
    _assert_builder_error(
        api,
        "INVALID_VALUE",
        lambda: api.adjudicate_career_verifications(
            record.envelope,
            package,
            (record,),
            (suggestion,),
            (replace(adjudication, final_short_term_until=date(2020, 3, 31)),),
            _fundamental_adjudication(api, package),
        ),
    )
    first_bundle = operation()
    second_bundle = operation()
    assert first_bundle == second_bundle
    decision = first_bundle.impact_adjudications[0]
    assert decision.suggestion.suggested_short_term_until == date(2020, 6, 30)
    assert decision.final_short_term_until == date(2020, 9, 30)
    first = api.build_career_states(first_bundle, date(2024, 12, 31))
    second = api.build_career_states(second_bundle, date(2024, 12, 31))
    assert first == second
    assert first.ledger_entries[0].assessment.short_term_until == date(2020, 9, 30)
    assert type(first.ledger_entries) is tuple
    assert all(type(entry) is EventLedgerEntry for entry in first.ledger_entries)
    with pytest.raises(FrozenInstanceError):
        first.envelope = _envelope()


def test_unit2_hash_proves_package_binding_not_suggestion_provenance() -> None:
    api = _api()
    package, record = _record()
    original = _suggestion(api, package, state_value="original suggestion")
    altered = replace(original, state_value="altered after verification")
    assert record.freeze_package_sha256 == compute_freeze_package_sha256(package)
    assert original != altered
    assert not hasattr(original, "sha256")
    assert not hasattr(original, "suggestion_id")
    original_bundle = api.adjudicate_career_verifications(
        record.envelope,
        package,
        (record,),
        (original,),
        (_adjudication(api, package),),
        _fundamental_adjudication(api, package),
    )
    altered_bundle = api.adjudicate_career_verifications(
        record.envelope,
        package,
        (record,),
        (altered,),
        (_adjudication(api, package),),
        _fundamental_adjudication(api, package),
    )
    assert original_bundle.freeze_package_sha256 == altered_bundle.freeze_package_sha256
    assert original_bundle != altered_bundle


def test_import_boundary_unit3_paths_and_protected_hashes() -> None:
    target = Path("tests/asof/test_career_state_builder.py")
    production_target = Path(MODULE_NAME.replace(".", "/") + ".py")
    assert target.is_file() and production_target.is_file()
    unit3_named_paths = {
        path.as_posix()
        for root in (Path("engine/asof"), Path("tests/asof"))
        for path in root.glob("*career_state_builder*")
        if path.is_file()
    }
    assert unit3_named_paths == {target.as_posix(), production_target.as_posix()}
    assert {path for path in PROTECTED_BASELINE if Path(path).is_file()} == set(PROTECTED_BASELINE)
    for path, expected in PROTECTED_BASELINE.items():
        assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == expected
    tree = ast.parse(target.read_text(encoding="utf-8"))
    production_tree = ast.parse(production_target.read_text(encoding="utf-8"))
    forbidden_import_prefixes = ("tools", "engine.pipeline", "engine.application", "engine.infrastructure")
    production_imports = {
        alias.name
        for node in ast.walk(production_tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        node.module
        for node in ast.walk(production_tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }
    assert not {
        imported
        for imported in production_imports
        if imported == forbidden_import_prefixes or imported.startswith(tuple(f"{prefix}." for prefix in forbidden_import_prefixes))
    }
    top_level_tests = [
        node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_")
    ]
    assert len(top_level_tests) == 12
    assert not any(
        isinstance(node, (ast.Import, ast.ImportFrom))
        and (
            any(alias.name == MODULE_NAME for alias in node.names)
            if isinstance(node, ast.Import)
            else node.module == MODULE_NAME
        )
        for node in tree.body
    )
    forbidden_unit3_names = {
        "suggestion_id",
        "adjudication_id",
        "bundle_id",
        "canonical_bytes",
        "canonical_json",
        "compute_sha256",
        "compute_career_bundle_sha256",
    }
    production = _api()
    public_fields = {
        field.name
        for model in (
            production.CareerImpactSuggestion,
            production.CareerImpactAdjudication,
            production.CareerFundamentalAdjudication,
            production.CareerAdjudicationBundle,
            production.CareerStateBuildResult,
        )
        for field in fields(model)
    }
    assert not (public_fields & forbidden_unit3_names)
    assert set(production.CareerStateBuilderError.CODES) == ERROR_CODES

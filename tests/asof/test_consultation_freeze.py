from __future__ import annotations

import ast
import hashlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import date, datetime
from pathlib import Path
from types import MappingProxyType
from typing import Any, Callable

import pytest

from engine.asof.consultation_freeze import (
    FREEZE_PACKAGE_SCHEMA_VERSION,
    VERIFICATION_SCHEMA_VERSION,
    CareerBlindDraft,
    CareerFreezePackage,
    CareerVerificationRecord,
    ConsultationFreezeError,
    FrozenCareerEvent,
    FrozenCareerFundamental,
    VerificationInput,
    VerificationVerdict,
    compute_freeze_package_sha256,
    freeze_career_draft,
    freeze_package_to_canonical_bytes,
    open_verification,
    record_career_verification,
    verification_input_from_mapping,
    verify_freeze_package_hash,
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
from engine.asof.reality_translation import FrozenLandingSet, LandingPoint, LandingVerdict, RealityConstraint
from engine.asof.session_contract import (
    SESSION_SCHEMA_VERSION,
    ConsultationState,
    SessionEnvelope,
    SessionIdentity,
)


EXPECTED_CANONICAL_BYTES = (
    b'{"blind_input_sha256":"1111111111111111111111111111111111111111111111111111111111111111",'
    b'"events":[],"fundamentals":[{"center":"mid-level professional",'
    b'"falsifiers":["no sustained professional responsibility"],"fundamental_id":"career-baseline",'
    b'"reasonable_range":["skilled individual contributor","team lead"],'
    b'"strongest_alternative":"independent specialist","window_center":"2019-07-02",'
    b'"window_end":"2020-01-01","window_start":"2019-01-01"}],'
    b'"identity":{"as_of_date":"2020-01-01","case_id":"C-2026-001-\xe4\xb9\xbe-\xe5\xba\x9a\xe7\x94\xb3\xe6\x88\x8a\xe5\xaf\x85\xe5\xa3\xac\xe5\xad\x90\xe8\xbe\x9b\xe4\xb8\x91",'
    b'"schema_version":"asof-session/v1","session_id":"S-20260727T120000Z-0123abcd"},'
    b'"schema_version":"asof-career-freeze-package/v1"}'
)
EXPECTED_DIGEST = hashlib.sha256(EXPECTED_CANONICAL_BYTES).hexdigest()

PROTECTED_BASELINE = {
    "engine/asof/session_contract.py": "1e2d67b09b20548c9ad728fb52e8ae9810844118dc2320e5b9412410573ae33e",
    "engine/asof/event_candidate.py": "ba7a7cb26ab65f277db7e8a0514264c73b779c7aaf0cf4270512caf581d7ef65",
    "engine/asof/reality_translation.py": "08f5b55ecff673e87ff8fc8dd6fc054b211b3f27473f3468c3f52f6f132bdf8d",
    "engine/asof/__init__.py": "e823e161de220edd62978ef6fb445d2fd39f4f064408002ae1d38fb3ed09ed3a",
    "engine/application/pipeline_runner.py": "b60c3e768b42f77fd108ad04cbc3e3cbc81018533309e67ffd942a5d80358dd4",
    "engine/claims/runner_registry.py": "42289b1c91a41d87c78a1d1e034e25749d816137156190f4cf66dc6c86de1431",
    "theory/production/claim-rules-v1.yaml": "6396883d8db0b8d24c6c15435c130c6f9ae045c8c6d1fe8d2a84748c5b0bebef",
}


def _identity(**changes: Any) -> SessionIdentity:
    values = {
        "schema_version": SESSION_SCHEMA_VERSION,
        "case_id": "C-2026-001-乾-庚申戊寅壬子辛丑",
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
    """构造只供边界测试使用的旧领域对象，绕过其非本单元校验。"""

    clone = object.__new__(type(value))
    for field in fields(value):
        object.__setattr__(clone, field.name, changes.get(field.name, getattr(value, field.name)))
    return clone


def _fundamental(**changes: Any) -> FrozenCareerFundamental:
    values = {
        "fundamental_id": "career-baseline",
        "window_start": date(2019, 1, 1),
        "window_end": date(2020, 1, 1),
        "window_center": date(2019, 7, 2),
        "center": "mid-level professional",
        "reasonable_range": ("skilled individual contributor", "team lead"),
        "strongest_alternative": "independent specialist",
        "falsifiers": ("no sustained professional responsibility",),
    }
    values.update(changes)
    return FrozenCareerFundamental(**values)


def _evidence(locator: str = "四柱.年柱") -> EvidenceRef:
    return EvidenceRef("cases/C-2026-001/input.md", locator, "庚申")


def _candidate(**changes: Any) -> LifeEventCandidate:
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
    values = {
        "candidate_id": "career-event-2019",
        "domain": "career",
        "event_type": "responsibility_level_change",
        "window_start": date(2019, 1, 1),
        "window_end": date(2019, 12, 31),
        "natal_evidence": (evidence,),
        "daiyun_evidence": (evidence,),
        "annual_trace": trace,
        "root_level": RootLevel.STRONG_ROOT,
        "root_evidence": (evidence,),
        "source_citations": (SourceCitation("sources/gao/example.md", 1, "原局有根，岁运引动"),),
        "completion_mode": CompletionMode.ACTIVATE_EXISTING,
        "supporting_evidence": (evidence,),
        "counter_evidence": (),
        "alternative_hypotheses": ("scope changed without title",),
        "frozen_version": "asof-prototype-v1",
        "verification_status": VerificationStatus.FROZEN,
        "extension_boundary": ExtensionBoundary.CROSS_DAIYUN_ELIGIBLE,
        "is_primary_event": True,
    }
    values.update(changes)
    return LifeEventCandidate(**values)


def _point(name: str = "internal promotion", **changes: Any) -> LandingPoint:
    values = {"name": name, "domain": "career", "direction": "authority_up"}
    values.update(changes)
    return LandingPoint(**values)


def _landing_set(**changes: Any) -> FrozenLandingSet:
    values = {
        "function_candidate": "responsibility_level_change",
        "center": _point(),
        "alternatives": (_point("team scope expanded"),),
        "weak_hit_boundary": "title-only change is weak",
        "falsifiers": ("responsibility unchanged",),
        "exclusions": ("income-only change",),
        "frozen_version": "landing-v1-before-outcome",
    }
    values.update(changes)
    return FrozenLandingSet(**values)


def _event(**changes: Any) -> FrozenCareerEvent:
    values = {"candidate": _candidate(), "landing_set": _landing_set()}
    values.update(changes)
    return FrozenCareerEvent(**values)


def _draft(**changes: Any) -> CareerBlindDraft:
    values = {"fundamentals": (_fundamental(),), "events": (_event(),)}
    values.update(changes)
    return CareerBlindDraft(**values)


def _frozen(*, events: bool = True) -> tuple[SessionEnvelope, CareerFreezePackage]:
    return freeze_career_draft(_envelope(), _draft(events=(_event(),) if events else ()))


def _actual(name: str = "internal promotion") -> LandingPoint:
    return _point(name)


def _constraint() -> RealityConstraint:
    return RealityConstraint("career-path", "verified career path", (), ("internal promotion",), True)


def _verification(
    package: CareerFreezePackage,
    *,
    item_id: str = "career-event-2019",
    verdict: VerificationVerdict = VerificationVerdict.CONFIRMED,
    actual_landing: LandingPoint | None = None,
    reality_constraint: RealityConstraint | None = None,
    taxonomy_evidence: tuple[str, ...] = (),
) -> VerificationInput:
    return VerificationInput(
        schema_version=VERIFICATION_SCHEMA_VERSION,
        freeze_package_sha256=compute_freeze_package_sha256(package),
        item_id=item_id,
        verdict=verdict,
        actual_landing=_actual() if actual_landing is None and verdict is VerificationVerdict.CONFIRMED else actual_landing,
        reality_constraint=reality_constraint,
        taxonomy_evidence=taxonomy_evidence,
    )


def _assert_error(code: str, operation: Callable[[], Any]) -> None:
    with pytest.raises(ConsultationFreezeError) as caught:
        operation()
    assert caught.value.code == code


def _valid_mapping(package: CareerFreezePackage) -> dict[str, Any]:
    return {
        "schema_version": VERIFICATION_SCHEMA_VERSION,
        "freeze_package_sha256": compute_freeze_package_sha256(package),
        "item_id": "career-event-2019",
        "verdict": "CONFIRMED",
        "actual_landing": {"name": "internal promotion", "domain": "career", "direction": "authority_up"},
        "reality_constraint": None,
        "taxonomy_evidence": [],
    }


@pytest.mark.parametrize("container", ["mapping-proxy"], ids=["mapping-proxy"])
def test_valid_freeze_is_immutable_and_transitions_to_frozen(container: str) -> None:
    envelope, package = _frozen()
    assert container == "mapping-proxy"
    assert envelope.state is ConsultationState.FROZEN
    assert package.schema_version == FREEZE_PACKAGE_SCHEMA_VERSION
    assert package.identity == envelope.identity == _identity()
    assert package.identity.as_of_date == date(2020, 1, 1)
    assert package.blind_input_sha256 == "1" * 64
    assert package.fundamentals == (_fundamental(),)
    assert package.events == (_event(),)
    assert is_dataclass(package)
    with pytest.raises((FrozenInstanceError, AttributeError, TypeError)):
        package.events = ()


@pytest.mark.parametrize("case", ["oracle", "tamper"], ids=["oracle", "tamper"])
def test_canonical_literal_oracle_and_hash_tamper_fail_closed(case: str) -> None:
    _, package = _frozen(events=False)
    if case == "oracle":
        assert freeze_package_to_canonical_bytes(package) == EXPECTED_CANONICAL_BYTES
        assert compute_freeze_package_sha256(package) == EXPECTED_DIGEST
        assert verify_freeze_package_hash(package, EXPECTED_DIGEST) is None
    else:
        tampered = replace(package, fundamentals=(replace(package.fundamentals[0], center="executive"),))
        _assert_error("HASH_MISMATCH", lambda: verify_freeze_package_hash(tampered, EXPECTED_DIGEST))
        _assert_error("INVALID_VALUE", lambda: verify_freeze_package_hash(package, "A" * 64))


@pytest.mark.parametrize(
    ("changes", "code"),
    [
        ({"fundamental_id": ""}, "INVALID_VALUE"),
        ({"window_start": date(2020, 1, 2)}, "INVALID_VALUE"),
        ({"window_center": date(2018, 12, 31)}, "INVALID_VALUE"),
        ({"window_start": datetime(2019, 1, 1)}, "INVALID_TYPE"),
        ({"center": ""}, "INVALID_VALUE"),
        ({"reasonable_range": ()}, "INVALID_VALUE"),
        ({"strongest_alternative": "mid-level professional"}, "INVALID_VALUE"),
        ({"falsifiers": ()}, "INVALID_VALUE"),
    ],
    ids=["empty-id", "reversed-window", "center-outside-window", "datetime-not-date", "empty-center", "empty-range", "alternative-equals-center", "empty-falsifiers"],
)
def test_fundamental_validation(changes: dict[str, Any], code: str) -> None:
    _assert_error(code, lambda: _fundamental(**changes))


@pytest.mark.parametrize(
    ("case", "code"),
    [
        ("candidate-type", "INVALID_TYPE"),
        ("landing-type", "INVALID_TYPE"),
        ("candidate-domain", "INVALID_VALUE"),
        ("candidate-not-frozen", "INVALID_VALUE"),
        ("candidate-withheld", "INVALID_VALUE"),
        ("not-primary", "INVALID_VALUE"),
        ("function-mismatch", "INVALID_VALUE"),
        ("landing-domain", "INVALID_VALUE"),
        ("window-after-as-of", "INVALID_VALUE"),
        ("event-after-as-of", "INVALID_VALUE"),
    ],
    ids=["candidate-type", "landing-type", "candidate-domain", "candidate-not-frozen", "candidate-withheld", "not-primary", "function-mismatch", "landing-domain", "window-after-as-of", "event-after-as-of"],
)
def test_event_binding_validation(case: str, code: str) -> None:
    if case == "candidate-type":
        operation = lambda: _event(candidate=object())
    elif case == "landing-type":
        operation = lambda: _event(landing_set=object())
    elif case == "candidate-domain":
        operation = lambda: _event(candidate=_unchecked_replace(_candidate(), domain="wealth"))
    elif case == "candidate-not-frozen":
        operation = lambda: _event(candidate=replace(_candidate(), verification_status=VerificationStatus.CANDIDATE))
    elif case == "candidate-withheld":
        operation = lambda: _event(candidate=replace(_candidate(), verification_status=VerificationStatus.WITHHELD))
    elif case == "not-primary":
        operation = lambda: _event(candidate=replace(_candidate(), is_primary_event=False))
    elif case == "function-mismatch":
        operation = lambda: _event(landing_set=_landing_set(function_candidate="career_exit"))
    elif case == "landing-domain":
        operation = lambda: _event(landing_set=_landing_set(center=_point(domain="wealth"), alternatives=()))
    elif case == "window-after-as-of":
        operation = lambda: freeze_career_draft(_envelope(), _draft(events=(_event(candidate=replace(_candidate(), window_end=date(2020, 2, 1))),)))
    else:
        operation = lambda: freeze_career_draft(
            _envelope(identity=_identity(as_of_date=date(2018, 12, 31))),
            _draft(fundamentals=(_fundamental(
                window_start=date(2018, 1, 1),
                window_center=date(2018, 6, 1),
                window_end=date(2018, 12, 31),
            ),)),
        )
    _assert_error(code, operation)


@pytest.mark.parametrize(
    ("changes", "code"),
    [
        ({"fundamentals": ()}, "INVALID_VALUE"),
        ({"fundamentals": [_fundamental()]}, "INVALID_TYPE"),
        ({"fundamentals": (_fundamental(), _fundamental())}, "DUPLICATE_ID"),
        ({"events": (_event(), _event())}, "DUPLICATE_ID"),
    ],
    ids=["no-fundamentals", "fundamentals-not-tuple", "duplicate-fundamental-id", "duplicate-event-id"],
)
def test_draft_cardinality_and_duplicate_ids(changes: dict[str, Any], code: str) -> None:
    _assert_error(code, lambda: _draft(**changes))


@pytest.mark.parametrize(
    ("case", "code"),
    [
        ("envelope-before-draft", "INVALID_TYPE"),
        ("draft-type", "INVALID_TYPE"),
        ("state-before-empty-fundamentals", "INVALID_STATE"),
        ("state-before-bad-event", "INVALID_STATE"),
        ("identity-before-cardinality", "INVALID_TYPE"),
        ("hash-before-cardinality", "INVALID_VALUE"),
        ("fundamental-before-event", "INVALID_VALUE"),
        ("event-after-fundamental", "INVALID_TYPE"),
    ],
    ids=["envelope-before-draft", "draft-type", "state-before-empty-fundamentals", "state-before-bad-event", "identity-before-cardinality", "hash-before-cardinality", "fundamental-before-event", "event-after-fundamental"],
)
def test_freeze_state_type_and_competing_error_order(case: str, code: str) -> None:
    if case == "envelope-before-draft":
        operation = lambda: freeze_career_draft(object(), object())
    elif case == "draft-type":
        operation = lambda: freeze_career_draft(_envelope(), object())
    elif case == "state-before-empty-fundamentals":
        operation = lambda: freeze_career_draft(_envelope(ConsultationState.STRICT_BLIND_INPUT), object())
    elif case == "state-before-bad-event":
        operation = lambda: freeze_career_draft(_envelope(ConsultationState.FROZEN), object())
    elif case == "identity-before-cardinality":
        operation = lambda: freeze_career_draft(_unchecked_replace(_envelope(), identity=object()), object())
    elif case == "hash-before-cardinality":
        operation = lambda: freeze_career_draft(_unchecked_replace(_envelope(), blind_input_sha256="bad"), object())
    elif case == "fundamental-before-event":
        operation = lambda: CareerBlindDraft((_fundamental(center=""),), (object(),))
    else:
        operation = lambda: freeze_career_draft(_envelope(), CareerBlindDraft((_fundamental(),), (object(),)))
    _assert_error(code, operation)


MAPPING_IDS = [
    "top-not-mapping", "top-unknown-key", "top-missing-key", "bad-schema",
    "bad-hash-type-or-format", "empty-item", "bad-verdict", "actual-not-mapping",
    "actual-unknown-key", "actual-missing-name", "constraint-not-mapping", "constraint-and-leaf-types",
]


@pytest.mark.parametrize("case", MAPPING_IDS, ids=MAPPING_IDS)
def test_mapping_closed_allowlist_and_scalar_rejection(case: str) -> None:
    _, package = _frozen()
    payload: Any = _valid_mapping(package)
    code = "INVALID_VALUE"
    if case == "top-not-mapping":
        payload, code = [], "INVALID_TYPE"
    elif case == "top-unknown-key":
        payload["unknown"] = 1
        code = "UNKNOWN_FIELD"
    elif case == "top-missing-key":
        del payload["item_id"]
    elif case == "bad-schema":
        payload["schema_version"] = "wrong"
        code = "SCHEMA_MISMATCH"
    elif case == "bad-hash-type-or-format":
        payload["freeze_package_sha256"] = 1
        code = "INVALID_TYPE"
    elif case == "empty-item":
        payload["item_id"] = ""
    elif case == "bad-verdict":
        payload["verdict"] = "MAYBE"
    elif case == "actual-not-mapping":
        payload["actual_landing"] = []
        code = "INVALID_TYPE"
    elif case == "actual-unknown-key":
        payload["actual_landing"]["unknown"] = "x"
        code = "UNKNOWN_FIELD"
    elif case == "actual-missing-name":
        del payload["actual_landing"]["name"]
    elif case == "constraint-not-mapping":
        payload["reality_constraint"] = []
        code = "INVALID_TYPE"
    else:
        payload["actual_landing"]["name"] = 1
        payload["taxonomy_evidence"] = ()
        code = "INVALID_TYPE"
    _assert_error(code, lambda: verification_input_from_mapping(MappingProxyType(payload) if isinstance(payload, dict) else payload))


ORDER_IDS = [
    "unknown-before-missing", "missing-before-schema", "schema-before-hash", "hash-before-item",
    "item-before-verdict", "verdict-before-actual", "actual-before-constraint", "constraint-before-taxonomy",
]


@pytest.mark.parametrize("case", ORDER_IDS, ids=ORDER_IDS)
def test_mapping_competing_error_order(case: str) -> None:
    _, package = _frozen()
    payload = _valid_mapping(package)
    expected = "INVALID_VALUE"
    if case == "unknown-before-missing":
        payload["unknown"] = 1
        del payload["item_id"]
        expected = "UNKNOWN_FIELD"
    elif case == "missing-before-schema":
        del payload["item_id"]
        payload["schema_version"] = "wrong"
    elif case == "schema-before-hash":
        payload["schema_version"] = "wrong"
        payload["freeze_package_sha256"] = 1
        expected = "SCHEMA_MISMATCH"
    elif case == "hash-before-item":
        payload["freeze_package_sha256"] = 1
        payload["item_id"] = ""
        expected = "INVALID_TYPE"
    elif case == "item-before-verdict":
        payload["item_id"] = ""
        payload["verdict"] = "MAYBE"
    elif case == "verdict-before-actual":
        payload["verdict"] = "MAYBE"
        payload["actual_landing"] = []
    elif case == "actual-before-constraint":
        payload["actual_landing"] = []
        payload["reality_constraint"] = []
        expected = "INVALID_TYPE"
    else:
        payload["reality_constraint"] = []
        payload["taxonomy_evidence"] = ()
        expected = "INVALID_TYPE"
    _assert_error(expected, lambda: verification_input_from_mapping(payload))


@pytest.mark.parametrize(
    ("case", "code"),
    [
        ("valid", None),
        ("envelope-type", "INVALID_TYPE"),
        ("package-type", "INVALID_TYPE"),
        ("state", "INVALID_STATE"),
        ("identity", "INVALID_VALUE"),
        ("blind-hash", "HASH_MISMATCH"),
        ("package-hash-format", "INVALID_VALUE"),
        ("package-tamper", "HASH_MISMATCH"),
    ],
    ids=["valid", "envelope-type", "package-type", "state", "identity", "blind-hash", "package-hash-format", "package-tamper"],
)
def test_open_verification_binding_and_hash(case: str, code: str | None) -> None:
    frozen_envelope, package = _frozen()
    digest = compute_freeze_package_sha256(package)
    envelope: Any = frozen_envelope
    candidate_package: Any = package
    if case == "envelope-type":
        envelope = object()
    elif case == "package-type":
        candidate_package = object()
    elif case == "state":
        envelope = replace(frozen_envelope, state=ConsultationState.BLIND_DRAFTED)
    elif case == "identity":
        envelope = _unchecked_replace(
            frozen_envelope,
            identity=_identity(session_id="S-20260727T120000Z-deadbeef"),
        )
    elif case == "blind-hash":
        envelope = _unchecked_replace(frozen_envelope, blind_input_sha256="2" * 64)
    elif case == "package-hash-format":
        digest = "A" * 64
    elif case == "package-tamper":
        candidate_package = replace(package, fundamentals=(replace(package.fundamentals[0], center="tampered"),))
    operation = lambda: open_verification(envelope, candidate_package, digest)
    if code is None:
        opened = operation()
        assert opened.state is ConsultationState.VERIFICATION_OPEN
        assert frozen_envelope.state is ConsultationState.FROZEN
    else:
        _assert_error(code, operation)


VERDICT_CASES = [
    "valid-confirmed-center", "valid-partial-alternative", "valid-rejected-miss", "valid-unknown-gap", "valid-withheld",
    "confirmed-missing-actual", "partial-missing-actual", "rejected-missing-actual", "unknown-missing-constraint",
    "withheld-forbids-actual", "confirmed-rejects-alternative", "partial-rejects-center", "rejected-rejects-center",
    "unknown-rejects-miss", "item-not-found",
]


@pytest.mark.parametrize("case", VERDICT_CASES, ids=VERDICT_CASES)
def test_record_verdict_matrix(case: str) -> None:
    frozen_envelope, package = _frozen()
    opened = open_verification(frozen_envelope, package, compute_freeze_package_sha256(package))
    alternative = _actual("team scope expanded")
    outside = _actual("unfrozen same-direction role")
    gap_constraint = RealityConstraint("path-closed", "verified path constraint", ("internal promotion",), (outside.name,), True)
    verdict = VerificationVerdict.CONFIRMED
    actual: LandingPoint | None = _actual()
    constraint: RealityConstraint | None = None
    taxonomy: tuple[str, ...] = ()
    expected_landing: LandingVerdict | None = LandingVerdict.CENTER_HIT
    error: str | None = None
    item_id = "career-event-2019"
    if case == "valid-partial-alternative":
        verdict, actual, expected_landing = VerificationVerdict.PARTIAL_HIT, alternative, LandingVerdict.ALTERNATIVE_HIT
    elif case == "valid-rejected-miss":
        verdict, actual, expected_landing = VerificationVerdict.REJECTED, _point("career exit", direction="career_down"), LandingVerdict.MISS
    elif case == "valid-unknown-gap":
        verdict, actual, constraint, taxonomy, expected_landing = VerificationVerdict.UNKNOWN, outside, gap_constraint, ("source", "chart", "case"), LandingVerdict.TAXONOMY_GAP
    elif case == "valid-withheld":
        verdict, actual, expected_landing = VerificationVerdict.WITHHELD, None, None
    elif case == "confirmed-missing-actual":
        actual, error = None, "INVALID_VALUE"
    elif case == "partial-missing-actual":
        verdict, actual, error = VerificationVerdict.PARTIAL_HIT, None, "INVALID_VALUE"
    elif case == "rejected-missing-actual":
        verdict, actual, error = VerificationVerdict.REJECTED, None, "INVALID_VALUE"
    elif case == "unknown-missing-constraint":
        verdict, actual, taxonomy, error = VerificationVerdict.UNKNOWN, outside, ("source",), "INVALID_VALUE"
    elif case == "withheld-forbids-actual":
        verdict, error = VerificationVerdict.WITHHELD, "INVALID_VALUE"
    elif case == "confirmed-rejects-alternative":
        actual, error = alternative, "INVALID_VALUE"
    elif case == "partial-rejects-center":
        verdict, error = VerificationVerdict.PARTIAL_HIT, "INVALID_VALUE"
    elif case == "rejected-rejects-center":
        verdict, error = VerificationVerdict.REJECTED, "INVALID_VALUE"
    elif case == "unknown-rejects-miss":
        verdict, actual, error = VerificationVerdict.UNKNOWN, _point("career exit", direction="career_down"), "INVALID_VALUE"
    elif case == "item-not-found":
        item_id, error = "missing-event", "ITEM_NOT_FOUND"
    verification = VerificationInput(
        VERIFICATION_SCHEMA_VERSION,
        compute_freeze_package_sha256(package),
        item_id,
        verdict,
        actual,
        constraint,
        taxonomy,
    )
    operation = lambda: record_career_verification(opened, package, verification)
    if error is not None:
        _assert_error(error, operation)
    else:
        record = operation()
        assert type(record) is CareerVerificationRecord
        assert record.verdict is verdict
        assert record.landing_verdict is expected_landing
        assert record.envelope.state is ConsultationState.VERIFICATION_OPEN


@pytest.mark.parametrize("run", [1], ids=["repeat"])
def test_freeze_and_record_are_deterministic_immutable_and_never_adjudicate(run: int) -> None:
    assert run == 1
    left_envelope, left_package = _frozen()
    right_envelope, right_package = _frozen()
    assert left_package == right_package and left_package is not right_package
    assert freeze_package_to_canonical_bytes(left_package) == freeze_package_to_canonical_bytes(right_package)
    left_open = open_verification(left_envelope, left_package, compute_freeze_package_sha256(left_package))
    right_open = open_verification(right_envelope, right_package, compute_freeze_package_sha256(right_package))
    left_record = record_career_verification(left_open, left_package, _verification(left_package))
    right_record = record_career_verification(right_open, right_package, _verification(right_package))
    assert left_record == right_record and left_record is not right_record
    assert left_record.envelope == left_open
    assert left_record.envelope.state is ConsultationState.VERIFICATION_OPEN
    assert left_record.envelope.state is not ConsultationState.ADJUDICATED
    with pytest.raises((FrozenInstanceError, AttributeError, TypeError)):
        left_record.verdict = VerificationVerdict.REJECTED

    incomplete_envelope = object.__new__(SessionEnvelope)
    _assert_error(
        "INVALID_VALUE",
        lambda: freeze_career_draft(incomplete_envelope, _draft()),
    )
    _assert_error(
        "INVALID_VALUE",
        lambda: open_verification(
            incomplete_envelope,
            left_package,
            compute_freeze_package_sha256(left_package),
        ),
    )
    _assert_error(
        "INVALID_VALUE",
        lambda: record_career_verification(
            incomplete_envelope,
            left_package,
            _verification(left_package),
        ),
    )


@pytest.mark.parametrize(
    "path",
    [
        "engine/asof/session_contract.py",
        "engine/asof/event_candidate.py",
        "engine/asof/reality_translation.py",
        "engine/asof/__init__.py",
        "engine/application/pipeline_runner.py",
        "engine/claims/runner_registry.py",
        "theory/production/claim-rules-v1.yaml",
    ],
    ids=["session-contract", "event-candidate", "reality-translation", "asof-init", "pipeline-runner", "runner-registry", "claim-rules"],
)
def test_import_boundary_and_protected_hashes(path: str) -> None:
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == PROTECTED_BASELINE[path]
    tree = ast.parse(Path("engine/asof/consultation_freeze.py").read_text(encoding="utf-8"))
    forbidden_prefixes = ("tools", "engine.application", "engine.claims", "engine.reports")
    forbidden_top_level = {"pathlib", "io", "os", "random", "uuid", "time"}
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
    assert not [name for name in imports if name.startswith(forbidden_prefixes) or name.split(".")[0] in forbidden_top_level]
    assert not [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        and node.func.id in {"open", "exec", "eval", "compile", "__import__"}
    ]

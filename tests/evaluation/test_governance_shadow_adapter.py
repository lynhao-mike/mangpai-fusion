from __future__ import annotations

import ast
import copy
import inspect
from dataclasses import fields, replace
from pathlib import Path
from typing import Any

import pytest

from engine.application.governance_shadow_types import (
    CompositionTrace,
    GovernanceShadowResult,
    ShadowArbitrationTrace,
    ShadowClaimTrace,
    ShadowIssue,
    TriggerTrace,
    UnavailableSchool,
    shadow_result_digest,
)
from engine.evaluation.governance_shadow_adapter import (
    GovernanceShadowTaskProjection,
    ShadowPredictionBinding,
    adapt_governance_shadow_to_blind_outputs,
)
from engine.evaluation.models import BlindTask
from tests.application.test_governance_yang_marriage_adapter import (
    _adapt as adapt_yang_fixture,
    _catalog as yang_catalog_fixture,
    _result as yang_result_fixture,
)

TASK_ID = "marriage.divorce_or_remarriage"
SCHOOL_ID = "yang_qingjuan"
CONCLUSION_ID = "yang.divorce_or_remarriage_event_risk/v1"
CONCLUSION = (
    "杨派原局夫妻宫事件锚与独立配偶结构交互同向，"
    "支持存在离婚或再婚事件风险，但不作必然判断。"
)
MODULE_PATH = Path("engine/evaluation/governance_shadow_adapter.py")


def _claim() -> Any:
    claim = adapt_yang_fixture(yang_result_fixture(), yang_catalog_fixture()).claim
    assert claim is not None
    return claim


def _task(**changes: object) -> BlindTask:
    values: dict[str, object] = {
        "task_id": TASK_ID,
        "domain": "婚姻",
        "claim_type": "binary_event",
        "scoring_method": "binary_probability",
        "quantifiable": True,
        "high_risk": True,
        "allowed_time_horizons": ["lifetime", "ten_year"],
        "required_input_fields": ["four_pillars", "sex_marker"],
        "label_schema": {
            "type": "boolean",
            "positive_label": "occurred",
            "negative_label": "not_observed",
        },
        "evaluation_note": "只评价是否发生，不把关系压力自动等同离婚",
    }
    values.update(changes)
    return BlindTask(**values)  # type: ignore[arg-type]


def _redigest(result: GovernanceShadowResult, **changes: object) -> GovernanceShadowResult:
    changed = replace(result, **changes, result_digest="pending")
    return replace(changed, result_digest=shadow_result_digest(changed))


def _shadow(
    claim: Any | None = None,
    *,
    unavailable: tuple[UnavailableSchool, ...] = (),
    excluded: tuple[str, ...] = (),
    arbitration: ShadowArbitrationTrace | None | object = ...,
    triggers: tuple[TriggerTrace, ...] = (),
    compositions: tuple[CompositionTrace, ...] = (),
    issues: tuple[ShadowIssue, ...] = (),
) -> GovernanceShadowResult:
    source = _claim() if claim is None else claim
    trace = ShadowClaimTrace.from_claim(source)
    retained = ShadowArbitrationTrace("retained", "arb-digest", (source.claim_id,), ())
    selected_arbitration = retained if arbitration is ... else arbitration
    result = GovernanceShadowResult(
        schema_version="governance.shadow-result.v1",
        runner_version="governance-shadow-runner/v1",
        status="ok",
        fact_snapshot_id="snapshot-1",
        fact_snapshot_digest="snapshot-digest-1",
        input_digest="input-digest-1",
        fact_kinds=("four_pillars", "sex_marker"),
        claims=(trace,),
        unavailable_schools=unavailable,
        excluded_claim_refs=excluded,
        trigger_results=triggers,
        composition_results=compositions,
        arbitration=selected_arbitration,  # type: ignore[arg-type]
        issues=issues,
        result_digest="pending",
    )
    return replace(result, result_digest=shadow_result_digest(result))


def _binding(claim: Any, **changes: object) -> ShadowPredictionBinding:
    values: dict[str, object] = {
        "source_claim": claim,
        "event_conclusion_id": CONCLUSION_ID,
        "probability": 0.63,
        "horizon": "lifetime",
        "start_year": None,
        "end_year": None,
        "evidence_refs": (
            "theory/yang/index.yaml#M2-Y-088",
            "theory/yang/index.yaml#M2-Y-068",
        ),
        "fact_refs": ("sex_marker", "four_pillars.day"),
        "falsifier": claim.falsifier,
    }
    values.update(changes)
    return ShadowPredictionBinding(**values)  # type: ignore[arg-type]


def _projection(
    result: GovernanceShadowResult,
    claim: Any,
    **changes: object,
) -> GovernanceShadowTaskProjection:
    values: dict[str, object] = {
        "schema_version": "governance-shadow-task-projection/v1",
        "case_id": "CASE-W2-C2",
        "school_id": SCHOOL_ID,
        "task_id": TASK_ID,
        "task_catalog_version": "task-catalog/v1",
        "rule_version": "rule-snapshot/v1",
        "calculator_version": "calculator/v1",
        "expected_result_digest": result.result_digest,
        "expected_fact_snapshot_id": result.fact_snapshot_id,
        "expected_fact_snapshot_digest": result.fact_snapshot_digest,
        "expected_input_digest": result.input_digest,
        "source_execution_state": "executed",
        "capability_state": "certified",
        "rationale": "显式投影提供完整事件绑定。",
        "prediction": _binding(claim),
    }
    values.update(changes)
    return GovernanceShadowTaskProjection(**values)  # type: ignore[arg-type]


def _adapt(
    result: GovernanceShadowResult,
    *projections: GovernanceShadowTaskProjection,
    task: BlindTask | None = None,
):
    return adapt_governance_shadow_to_blind_outputs(
        result, task or _task(), projections
    )


def _mutated(value: Any, **changes: object) -> Any:
    changed = copy.copy(value)
    for name, replacement in changes.items():
        object.__setattr__(changed, name, replacement)
    return changed


# 1. exact valid claim conversion
def test_exact_valid_claim_conversion() -> None:
    claim = _claim()
    result = _shadow(claim)

    (output,) = _adapt(result, _projection(result, claim))

    assert (output.case_id, output.school_id, output.task_id) == (
        "CASE-W2-C2",
        SCHOOL_ID,
        TASK_ID,
    )
    assert output.state == "claim"
    assert output.rationale == "显式投影提供完整事件绑定。"
    assert output.counter_evidence == ()
    assert len(output.predictions) == 1
    prediction = output.predictions[0]
    assert prediction.event_label == "occurred"
    assert prediction.probability == 0.63
    assert prediction.time_window == {"label": "lifetime"}
    assert prediction.evidence_refs == tuple(sorted((
        "theory/yang/index.yaml#M2-Y-088",
        "theory/yang/index.yaml#M2-Y-068",
    )))
    assert prediction.fact_refs == ("four_pillars.day", "sex_marker")
    assert prediction.falsifier == claim.falsifier


# 2. deterministic output ordering and prediction identity
@pytest.mark.parametrize(
    "binding_change",
    (
        {"probability": 0.64},
        {"horizon": "ten_year", "start_year": 2030, "end_year": 2039},
        {"evidence_refs": ("theory/yang/index.yaml#M2-Y-068",)},
        {"fact_refs": ("four_pillars.day",)},
    ),
)
def test_deterministic_ordering_and_source_bound_prediction_identity(
    binding_change: dict[str, object],
) -> None:
    claim = _claim()
    result = _shadow(claim)
    base = _projection(result, claim)
    changed_projection = replace(base, prediction=_binding(claim, **binding_change))
    # Compare prediction identities in separate calls; source reuse within one call is forbidden.
    first = _adapt(result, base)[0].predictions[0]
    replay = _adapt(result, base)[0].predictions[0]
    changed = _adapt(result, changed_projection)[0].predictions[0]
    abstain_z = replace(base, school_id="z-school", prediction=None)
    abstain_a = replace(base, school_id="a-school", prediction=None)

    ordered = _adapt(result, abstain_z, abstain_a)

    assert tuple(item.school_id for item in ordered) == ("a-school", "z-school")
    assert replay.prediction_id == first.prediction_id
    assert changed.prediction_id != first.prediction_id


# 3. exact accepted shadow schema/runner versions
@pytest.mark.parametrize(
    ("field", "value"),
    (("schema_version", "governance.shadow-result.v2"), ("runner_version", "runner/v2")),
)
def test_exact_shadow_schema_and_runner_are_required(field: str, value: str) -> None:
    claim = _claim()
    result = _redigest(_shadow(claim), **{field: value})
    with pytest.raises(ValueError, match="schema or runner"):
        _adapt(result, _projection(result, claim))


# 4. result digest tamper rejection
def test_result_digest_tamper_is_rejected() -> None:
    claim = _claim()
    result = replace(_shadow(claim), input_digest="tampered-without-redigest")
    with pytest.raises(ValueError, match="digest mismatch"):
        _adapt(result, _projection(result, claim))


# 5. fail-closed status rejection
def test_fail_closed_status_is_never_adapted() -> None:
    claim = _claim()
    result = _redigest(_shadow(claim), status="fail_closed")
    with pytest.raises(ValueError, match="fail-closed"):
        _adapt(result, _projection(result, claim))


# 6. result-visible identity checks and external-attestation boundary
@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("expected_result_digest", "wrong"),
        ("expected_fact_snapshot_id", "wrong"),
        ("expected_fact_snapshot_digest", "wrong"),
        ("expected_input_digest", "wrong"),
    ),
)
def test_result_visible_projection_identity_mismatch_is_rejected(
    field: str, value: str
) -> None:
    claim = _claim()
    result = _shadow(claim)
    with pytest.raises(ValueError, match="shadow identity mismatch"):
        _adapt(result, _projection(result, claim, **{field: value}))


def test_case_and_versions_are_preserved_attestations_not_result_authenticated() -> None:
    claim = _claim()
    result = _shadow(claim)
    projection = _projection(
        result,
        claim,
        case_id="EXTERNALLY-ATTESTED-CASE",
        task_catalog_version="external-catalog/v9",
        rule_version="external-rules/v9",
        calculator_version="external-calculator/v9",
    )

    (output,) = _adapt(result, projection)

    assert output.case_id == "EXTERNALLY-ATTESTED-CASE"
    assert output.predictions[0].prediction_id


# 7. exact all-field task predicate and assertion validation
_TASK_MUTATIONS = (
    {"task_id": "marriage.pressure"},
    {"domain": "关系"},
    {"claim_type": "ordinal"},
    {"scoring_method": "ordinal"},
    {"quantifiable": False},
    {"high_risk": False},
    {"allowed_time_horizons": ["ten_year", "lifetime"]},
    {"required_input_fields": ["sex_marker", "four_pillars"]},
    {"label_schema": {"type": "boolean", "positive_label": "occurred"}},
    {"label_schema": {
        "type": "boolean", "positive_label": "occurred",
        "negative_label": "not_observed", "extra": "forbidden",
    }},
    {"evaluation_note": "关系压力可视作离婚"},
)


@pytest.mark.parametrize("task_change", _TASK_MUTATIONS)
def test_every_task_field_is_an_exact_predicate(task_change: dict[str, object]) -> None:
    claim = _claim()
    result = _shadow(claim)
    with pytest.raises(ValueError, match="exact admitted predicate|projection task mismatch"):
        _adapt(result, _projection(result, claim), task=_task(**task_change))


@pytest.mark.parametrize(
    "projection_change",
    (
        {"schema_version": "projection/v2"},
        {"case_id": ""},
        {"school_id": " school "},
        {"task_catalog_version": ""},
        {"rule_version": ""},
        {"calculator_version": ""},
        {"source_execution_state": "unknown"},
        {"capability_state": "unknown"},
    ),
)
def test_projection_schema_and_assertions_require_exact_nonempty_values(
    projection_change: dict[str, object],
) -> None:
    claim = _claim()
    result = _shadow(claim)
    with pytest.raises(ValueError):
        _adapt(result, _projection(result, claim, **projection_change))


def test_projection_assertions_must_share_one_attested_source_context() -> None:
    claim = _claim()
    result = _shadow(claim)
    first = _projection(result, claim, prediction=None)
    second = replace(first, school_id="other-school", rule_version="other-rules/v2")

    with pytest.raises(ValueError, match="one attested source context"):
        _adapt(result, first, second)


# 8. exact concrete boundary types, including typed source claim
@pytest.mark.parametrize("boundary", ("result", "task", "projection", "binding", "claim"))
def test_duck_types_are_rejected_at_every_typed_boundary(boundary: str) -> None:
    claim = _claim()
    result = _shadow(claim)
    projection = _projection(result, claim)

    class Lookalike:
        pass

    if boundary == "result":
        with pytest.raises(TypeError, match="exact GovernanceShadowResult"):
            adapt_governance_shadow_to_blind_outputs(Lookalike(), _task(), (projection,))  # type: ignore[arg-type]
    elif boundary == "task":
        with pytest.raises(TypeError, match="BlindTask"):
            adapt_governance_shadow_to_blind_outputs(result, Lookalike(), (projection,))  # type: ignore[arg-type]
    elif boundary == "projection":
        with pytest.raises(TypeError, match="GovernanceShadowTaskProjection"):
            adapt_governance_shadow_to_blind_outputs(result, _task(), (Lookalike(),))  # type: ignore[arg-type]
    elif boundary == "binding":
        with pytest.raises(ValueError, match="exact prediction binding"):
            _adapt(result, replace(projection, prediction=Lookalike()))  # type: ignore[arg-type]
    else:
        claim_subclass = type("ClaimSubclass", (type(claim),), {})
        subclass_claim = object.__new__(claim_subclass)
        for item in fields(claim):
            object.__setattr__(subclass_claim, item.name, getattr(claim, item.name))
        with pytest.raises(ValueError, match="exact GovernanceClaim"):
            _adapt(
                result,
                replace(projection, prediction=_binding(subclass_claim)),
            )


def test_subclasses_are_rejected_at_all_public_boundary_types() -> None:
    claim = _claim()
    result = _shadow(claim)
    projection = _projection(result, claim)

    def subclass_copy(value: Any) -> Any:
        subclass = type(f"{type(value).__name__}Subclass", (type(value),), {})
        copied = object.__new__(subclass)
        for item in fields(value):
            object.__setattr__(copied, item.name, getattr(value, item.name))
        return copied

    with pytest.raises(TypeError, match="exact GovernanceShadowResult"):
        adapt_governance_shadow_to_blind_outputs(
            subclass_copy(result), _task(), (projection,)
        )
    with pytest.raises(TypeError, match="BlindTask"):
        adapt_governance_shadow_to_blind_outputs(
            result, subclass_copy(_task()), (projection,)
        )
    with pytest.raises(TypeError, match="GovernanceShadowTaskProjection"):
        adapt_governance_shadow_to_blind_outputs(
            result, _task(), (subclass_copy(projection),)
        )
    with pytest.raises(ValueError, match="exact prediction binding"):
        _adapt(
            result,
            replace(projection, prediction=subclass_copy(projection.prediction)),
        )


def test_empty_or_text_projection_sequences_fail_closed() -> None:
    claim = _claim()
    result = _shadow(claim)
    with pytest.raises(ValueError, match="non-empty"):
        adapt_governance_shadow_to_blind_outputs(result, _task(), ())
    with pytest.raises(TypeError, match="non-empty sequence"):
        adapt_governance_shadow_to_blind_outputs(result, _task(), "projection")


# 9. duplicate output identity and source-claim reuse rejection
@pytest.mark.parametrize("collision", ("identity", "claim"))
def test_duplicate_output_identity_and_source_claim_reuse_fail_closed(
    collision: str,
) -> None:
    claim = _claim()
    result = _shadow(claim)
    first = _projection(result, claim)
    second = replace(
        first,
        school_id=first.school_id if collision == "identity" else "another-school",
    )
    with pytest.raises(ValueError):
        _adapt(result, first, second)


# 10. unavailable -> unsupported and exact trace matching
@pytest.mark.parametrize("trace_school", (SCHOOL_ID, "other-school", None, "duplicate"))
def test_unavailable_maps_to_unsupported_only_with_one_exact_trace(
    trace_school: str | None,
) -> None:
    claim = _claim()
    unavailable = (
        ()
        if trace_school is None
        else (
            UnavailableSchool(SCHOOL_ID, "first", "trace"),
            UnavailableSchool(SCHOOL_ID, "second", "trace"),
        )
        if trace_school == "duplicate"
        else (UnavailableSchool(trace_school, "runner_unavailable", "explicit trace"),)
    )
    result = _shadow(claim, unavailable=unavailable)
    projection = _projection(
        result,
        claim,
        source_execution_state="unavailable",
        prediction=None,
        rationale="该来源执行不可用。",
    )
    if trace_school == SCHOOL_ID:
        (output,) = _adapt(result, projection)
        assert output.state == "unsupported"
        assert output.predictions == ()
    else:
        with pytest.raises(ValueError, match="exactly one trace"):
            _adapt(result, projection)


def test_executed_projection_conflicting_with_unavailable_trace_is_rejected() -> None:
    claim = _claim()
    result = _shadow(
        claim,
        unavailable=(UnavailableSchool(SCHOOL_ID, "unavailable", "trace"),),
    )
    with pytest.raises(ValueError, match="conflicts with unavailable"):
        _adapt(result, _projection(result, claim))


# 11. uncertified -> unsupported
def test_uncertified_projection_is_external_attestation_and_maps_to_unsupported() -> None:
    claim = _claim()
    result = _shadow(claim)
    projection = _projection(
        result,
        claim,
        capability_state="uncertified",
        prediction=None,
        rationale="能力尚未认证。",
    )

    (output,) = _adapt(result, projection)

    assert output.state == "unsupported"
    assert output.rationale == "能力尚未认证。"


# 12. attested executed+certified+no binding -> abstain
def test_executed_certified_without_binding_is_attested_abstain_not_trace_proof() -> None:
    claim = _claim()
    result = _redigest(_shadow(claim), claims=(), arbitration=None)
    projection = _projection(
        result,
        claim,
        prediction=None,
        rationale="执行和认证由外部投影声明，本次主动弃权。",
    )

    (output,) = _adapt(result, projection)

    assert output.state == "abstain"
    assert output.predictions == ()


# 13. rationale required in all states; non-claims cannot carry predictions
@pytest.mark.parametrize(
    ("state", "projection_change"),
    (
        ("claim", {"rationale": ""}),
        ("claim-trim", {"rationale": " padded rationale "}),
        ("abstain", {"rationale": "", "prediction": None}),
        ("unsupported", {
            "rationale": "", "prediction": None, "capability_state": "uncertified",
        }),
        ("unsupported-prediction", {"capability_state": "uncertified"}),
        ("unavailable-prediction", {"source_execution_state": "unavailable"}),
    ),
)
def test_all_states_require_projection_rationale_and_nonclaims_reject_predictions(
    state: str, projection_change: dict[str, object]
) -> None:
    claim = _claim()
    unavailable = (
        (UnavailableSchool(SCHOOL_ID, "unavailable", "trace"),)
        if state == "unavailable-prediction" else ()
    )
    result = _shadow(claim, unavailable=unavailable)
    with pytest.raises(ValueError, match="rationale|cannot carry"):
        _adapt(result, _projection(result, claim, **projection_change))


# 14. typed claim ownership and exact event predicate
@pytest.mark.parametrize(
    ("mutation", "value"),
    (
        ("missing_trace", None),
        ("duplicate_trace", None),
        ("task_id", "marriage.pressure"),
        ("claim_kind", "pressure"),
        ("stance", "oppose"),
        ("school_id", "other-school"),
        ("trace_school", "other-school"),
        ("content_digest", "different-content-digest"),
        ("source_ref", "different-source-ref"),
        ("source_ref", None),
        ("falsifier", ""),
        ("blockers", ("pressure_only",)),
        ("event_conclusion_id", "similar-event/v1"),
        ("conclusion", "仅见关系压力，不代表离婚或再婚事件。"),
        ("conclusion", CONCLUSION[:-1]),
        ("conclusion", f" {CONCLUSION}"),
    ),
)
def test_typed_claim_ownership_and_exact_event_conclusion_fail_closed(
    mutation: str, value: object
) -> None:
    claim = _claim()
    result = _shadow(claim)
    bound_claim = claim
    binding_changes: dict[str, object] = {}
    if mutation == "missing_trace":
        result = _redigest(result, claims=())
    elif mutation == "duplicate_trace":
        result = _redigest(result, claims=result.claims + result.claims)
    elif mutation == "trace_school":
        result = _redigest(
            result,
            claims=(replace(result.claims[0], school_id=str(value)),),
        )
    elif mutation == "content_digest":
        result = _redigest(
            result,
            claims=(replace(result.claims[0], content_digest=str(value)),),
        )
    elif mutation == "source_ref":
        provenance = _mutated(claim.adapter_provenance, source_claim_ref=value)
        bound_claim = _mutated(claim, adapter_provenance=provenance)
    elif mutation == "event_conclusion_id":
        binding_changes[mutation] = value
    elif mutation in {"task_id", "claim_kind", "stance", "school_id", "conclusion"}:
        specification = _mutated(claim.specification, **{mutation: value})
        bound_claim = _mutated(claim, specification=specification)
    else:
        bound_claim = _mutated(claim, **{mutation: value})
    projection = _projection(
        result,
        claim,
        prediction=_binding(bound_claim, **binding_changes),
    )

    with pytest.raises(ValueError):
        _adapt(result, projection)


def test_event_conclusion_id_and_complete_conclusion_pair_is_accepted_exactly() -> None:
    claim = _claim()
    assert claim.specification.conclusion == CONCLUSION
    result = _shadow(claim)
    output = _adapt(result, _projection(result, claim))[0]
    assert output.predictions[0].event_label == "occurred"


# 15. arbitration retention and exclusion
@pytest.mark.parametrize("state", ("missing", "unretained", "excluded_id", "excluded_ref"))
def test_missing_unretained_or_excluded_arbitration_source_is_rejected(
    state: str,
) -> None:
    claim = _claim()
    if state == "missing":
        result = _shadow(claim, arbitration=None)
    elif state == "unretained":
        result = _shadow(
            claim,
            arbitration=ShadowArbitrationTrace("rejected", "arb", (), ()),
        )
    elif state == "excluded_id":
        result = _shadow(claim, excluded=(claim.claim_id,))
    else:
        result = _shadow(claim, excluded=(claim.adapter_provenance.source_claim_ref,))
    with pytest.raises(ValueError, match="eligible retained"):
        _adapt(result, _projection(result, claim))


# 16. probability validation
@pytest.mark.parametrize(
    "probability",
    (None, True, False, float("nan"), float("inf"), float("-inf"), -0.01, 1.01),
)
def test_probability_must_be_present_numeric_finite_and_bounded(
    probability: object,
) -> None:
    claim = _claim()
    result = _shadow(claim)
    projection = _projection(
        result, claim, prediction=_binding(claim, probability=probability)
    )
    with pytest.raises(ValueError, match="probability"):
        _adapt(result, projection)


@pytest.mark.parametrize("probability", (0, 0.0, 1, 1.0, 0.425))
def test_probability_boundary_values_come_from_explicit_binding(
    probability: float,
) -> None:
    claim = _claim()
    result = _shadow(claim)
    projection = _projection(
        result, claim, prediction=_binding(claim, probability=probability)
    )
    assert _adapt(result, projection)[0].predictions[0].probability == float(probability)


# 17. lifetime and ten-year horizon/window validation
@pytest.mark.parametrize(
    ("binding_change", "expected"),
    (
        ({"horizon": "lifetime"}, {"label": "lifetime"}),
        ({"horizon": "ten_year", "start_year": 2030, "end_year": 2039},
         {"label": "ten_year", "start_year": 2030, "end_year": 2039}),
    ),
)
def test_valid_horizon_windows_emit_exact_shape(
    binding_change: dict[str, object], expected: dict[str, object]
) -> None:
    claim = _claim()
    result = _shadow(claim)
    projection = _projection(
        result, claim, prediction=_binding(claim, **binding_change)
    )
    assert _adapt(result, projection)[0].predictions[0].time_window == expected


@pytest.mark.parametrize(
    "binding_change",
    (
        {"horizon": "lifetime", "start_year": 2030},
        {"horizon": "lifetime", "end_year": 2039},
        {"horizon": "month"},
        {"horizon": "ten_year", "start_year": None, "end_year": 2039},
        {"horizon": "ten_year", "start_year": 2030, "end_year": None},
        {"horizon": "ten_year", "start_year": True, "end_year": 2039},
        {"horizon": "ten_year", "start_year": 2040, "end_year": 2039},
    ),
)
def test_invalid_horizon_windows_fail_closed(binding_change: dict[str, object]) -> None:
    claim = _claim()
    result = _shadow(claim)
    with pytest.raises(ValueError, match="lifetime|horizon|ten_year"):
        _adapt(
            result,
            _projection(result, claim, prediction=_binding(claim, **binding_change)),
        )


# 18. exact refs, falsifier, and rationale semantics
@pytest.mark.parametrize(
    "binding_change",
    (
        {"evidence_refs": ()},
        {"evidence_refs": ["a#b"]},
        {"evidence_refs": ("a#b", "a#b")},
        {"evidence_refs": (" a#b",)},
        {"evidence_refs": ("a b#c",)},
        {"evidence_refs": ("a",)},
        {"evidence_refs": ("a#b#c",)},
        {"fact_refs": ()},
        {"fact_refs": ["four_pillars.day"]},
        {"fact_refs": ("fact.x", "fact.x")},
        {"fact_refs": (" fact.x",)},
        {"fact_refs": ("1fact.x",)},
        {"fact_refs": ("fact#anchor",)},
        {"fact_refs": ("fact..x",)},
        {"falsifier": ""},
        {"falsifier": " mismatched falsifier"},
        {"falsifier": "different but trimmed falsifier"},
    ),
)
def test_reference_grammar_trim_duplicates_and_falsifier_fail_closed(
    binding_change: dict[str, object],
) -> None:
    claim = _claim()
    result = _shadow(claim)
    with pytest.raises(ValueError):
        _adapt(
            result,
            _projection(result, claim, prediction=_binding(claim, **binding_change)),
        )


def test_refs_are_canonically_sorted_without_changing_projection_rationale() -> None:
    claim = _claim()
    result = _shadow(claim)
    rationale = "投影理由保持原文，不取自预测或报告。"
    projection = _projection(result, claim, rationale=rationale)
    output = _adapt(result, projection)[0]
    assert output.rationale == rationale
    assert output.predictions[0].evidence_refs == tuple(
        sorted(output.predictions[0].evidence_refs)
    )
    assert output.predictions[0].fact_refs == tuple(sorted(output.predictions[0].fact_refs))


# 19. pressure/excluded/minority/arbitration-only material cannot manufacture claims
@pytest.mark.parametrize("material", ("trigger", "composition", "issue", "arbitration_only", "excluded"))
def test_non_prediction_shadow_material_cannot_manufacture_a_claim(material: str) -> None:
    claim = _claim()
    kwargs: dict[str, object] = {}
    if material == "trigger":
        kwargs["triggers"] = (TriggerTrace("relationship_pressure", True, ()),)
    elif material == "composition":
        kwargs["compositions"] = (
            CompositionTrace("minority", "v1", "retained", "digest", None),
        )
    elif material == "issue":
        kwargs["issues"] = (ShadowIssue("pressure", "claims", "similar wording"),)
    elif material == "excluded":
        kwargs["excluded"] = ("minority-pressure-claim",)
    result = _shadow(claim, **kwargs)
    if material == "arbitration_only":
        result = _redigest(result, claims=())
    projection = _projection(
        result,
        claim,
        prediction=None,
        rationale="没有显式预测绑定，保持弃权。",
    )

    (output,) = _adapt(result, projection)

    assert output.state == "abstain"
    assert output.predictions == ()
    assert output.counter_evidence == ()


# 20. static AST/API isolation

def test_static_ast_and_public_api_are_isolated_from_forbidden_surfaces() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imports = {
        node.module or ""
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    } | {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    allowed_imports = {
        "__future__",
        "math",
        "re",
        "dataclasses",
        "typing",
        "engine.application.governance_shadow_types",
        "engine.evaluation.models",
        "engine.governance.canonical",
        "engine.governance.governance_claim",
        "engine.governance.governance_claim_values",
    }
    forbidden_fragments = {
        "freeze", "scor", "label", "observation", "feedback", "report",
        "weight", "capability", "review", "prospective", "custody", "gate",
        "runner.py", "registry_loader", "yaml", "pathlib", "datetime", "time",
        "random", "socket", "urllib", "http", "requests", "subprocess", "git",
    }
    calls = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    } | {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    public_classes = {
        node.name
        for node in tree.body
        if isinstance(node, ast.ClassDef) and not node.name.startswith("_")
    }
    public_functions = {
        node.name: tuple(argument.arg for argument in node.args.args)
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and not node.name.startswith("_")
    }

    assert imports == allowed_imports
    assert not any(fragment in imported.lower() for imported in imports for fragment in forbidden_fragments)
    assert calls.isdisjoint({
        "open", "read_text", "write_text", "from_dict", "freeze_outputs",
        "score_outputs", "system", "popen", "run", "sleep", "now", "utcnow",
        "getenv", "environ", "random", "randint", "urlopen", "request",
    })
    assert public_classes == {"ShadowPredictionBinding", "GovernanceShadowTaskProjection"}
    assert public_functions == {
        "adapt_governance_shadow_to_blind_outputs": ("result", "task", "projections")
    }
    assert tuple(inspect.signature(adapt_governance_shadow_to_blind_outputs).parameters) == (
        "result", "task", "projections"
    )
    source_text = MODULE_PATH.read_text(encoding="utf-8").lower()
    assert all(token not in source_text for token in (
        "revealedlabel", "frozenblindrun", "capabilityposterior", "from_dict(",
        "github", "gitlab", "outcome document", "feedback_ingest",
    ))

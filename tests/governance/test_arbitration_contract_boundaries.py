from __future__ import annotations

import pytest

from engine.governance import ClaimReference, ClaimReferenceCategory
from engine.governance.arbitration import ArbitrationContractError, arbitrate
from engine.governance.arbitration_contracts import (
    ClaimAudit,
    CounterevidenceTrace,
    EvidenceGroup,
    GateName,
    GateRecord,
    TemporalGroup,
    ArbitrationIssueCode,
)
from tests.governance.test_arbitration_gates import _arena, _claim


def test_nested_public_values_reject_mutable_and_forged_inputs() -> None:
    # Given: a valid result supplies trusted nested construction material.
    result = arbitrate(_arena(_claim()))
    variant = result.retained_variants[0]
    reference = ClaimReference(ClaimReferenceCategory.FACT, "fact", "v1")

    # When / Then: every public nested value rejects its mutable or forged field.
    constructors = (
        lambda: TemporalGroup(result.temporal_groups[0].scope, []),
        lambda: EvidenceGroup(("source",), []),
        lambda: ClaimAudit(
            "forged", GateName.EVIDENCE, ArbitrationIssueCode.EVIDENCE_BLOCKED
        ),
        lambda: GateRecord(GateName.EVIDENCE, [], ()),
        lambda: CounterevidenceTrace(variant, [reference]),
    )
    for constructor in constructors:
        with pytest.raises(ArbitrationContractError):
            constructor()


def test_result_rejects_object_new_forged_nested_values_before_digesting() -> None:
    # Given: an audit object bypassed with a raw owner through object.__new__.
    result = arbitrate(_arena(_claim()))
    forged = object.__new__(ClaimAudit)
    object.__setattr__(forged, "owner", "forged")
    object.__setattr__(forged, "gate", GateName.EVIDENCE)
    object.__setattr__(forged, "issue_code", ArbitrationIssueCode.EVIDENCE_BLOCKED)

    # When / Then: recursive result validation gives a typed error, never AttributeError.
    with pytest.raises(ArbitrationContractError):
        result.__class__.build(
            result.decision,
            result.retained_variants,
            result.applicable_variants,
            result.minority_variants,
            result.preserved_variants,
            result.temporal_groups,
            result.evidence_groups,
            result.counterevidence_traces,
            (forged,),
            result.gates,
        )


def test_result_rejects_object_new_nested_value_with_missing_field() -> None:
    # Given: a precise nested type bypassed its constructor and lacks a required field.
    result = arbitrate(_arena(_claim()))
    forged = object.__new__(ClaimAudit)
    object.__setattr__(forged, "owner", result.retained_variants[0])

    # When / Then: recursive validation translates the malformed object into a contract error.
    with pytest.raises(ArbitrationContractError):
        result.__class__.build(
            result.decision,
            result.retained_variants,
            result.applicable_variants,
            result.minority_variants,
            result.preserved_variants,
            result.temporal_groups,
            result.evidence_groups,
            result.counterevidence_traces,
            (forged,),
            result.gates,
        )

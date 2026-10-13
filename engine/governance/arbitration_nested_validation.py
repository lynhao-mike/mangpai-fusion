from __future__ import annotations

from engine.governance.arbitration_contracts import (
    ArbitrationIssueCode,
    ClaimAudit,
    ClaimVariantRef,
    CounterevidenceTrace,
    EvidenceGroup,
    GateName,
    GateRecord,
    TemporalGroup,
    variant_key,
)
from engine.governance.arbitration_values import (
    ArbitrationContractError,
    canonical_references,
    validate_variant,
)
from engine.governance.fact_values import TemporalScope


def variants(
    field_path: str, values: tuple[ClaimVariantRef, ...], required: bool
) -> None:
    if type(values) is not tuple or (required and not values):
        raise ArbitrationContractError(field_path, "must be an exact tuple")
    if any(type(value) is not ClaimVariantRef for value in values):
        raise ArbitrationContractError(field_path, "must contain exact variants")
    if tuple(sorted(values, key=variant_key)) != values or len(values) != len(
        set(values)
    ):
        raise ArbitrationContractError(field_path, "must be sorted and unique")
    for value in values:
        validate_variant(value.claim_id, value.content_digest)


def temporal(group: TemporalGroup) -> None:
    if not hasattr(group, "scope") or not hasattr(group, "variants"):
        raise ArbitrationContractError("temporal_group", "must define every field")
    if type(group.scope) is not TemporalScope:
        raise ArbitrationContractError("scope", "must be an exact TemporalScope")
    variants("variants", group.variants, True)


def evidence(group: EvidenceGroup) -> None:
    if not hasattr(group, "source_keys") or not hasattr(group, "variants"):
        raise ArbitrationContractError("evidence_group", "must define every field")
    if type(group.source_keys) is not tuple or not group.source_keys:
        raise ArbitrationContractError("source_keys", "must be a nonempty exact tuple")
    if any(type(key) is not str for key in group.source_keys):
        raise ArbitrationContractError("source_keys", "must contain exact strings")
    if tuple(sorted(group.source_keys)) != group.source_keys or len(
        group.source_keys
    ) != len(set(group.source_keys)):
        raise ArbitrationContractError("source_keys", "must be sorted and unique")
    variants("variants", group.variants, True)


def audit(value: ClaimAudit) -> None:
    if (
        not hasattr(value, "owner")
        or not hasattr(value, "gate")
        or not hasattr(value, "issue_code")
    ):
        raise ArbitrationContractError("audit", "must define every field")
    if type(value.owner) is not ClaimVariantRef:
        raise ArbitrationContractError("owner", "must be an exact ClaimVariantRef")
    if (
        type(value.gate) is not GateName
        or type(value.issue_code) is not ArbitrationIssueCode
    ):
        raise ArbitrationContractError("audit", "must use closed gate and issue values")
    validate_variant(value.owner.claim_id, value.owner.content_digest)


def record(value: GateRecord) -> None:
    if (
        not hasattr(value, "gate")
        or not hasattr(value, "retained_variants")
        or not hasattr(value, "rejected_variants")
    ):
        raise ArbitrationContractError("gate_record", "must define every field")
    if type(value.gate) is not GateName:
        raise ArbitrationContractError("gate", "must be an exact GateName")
    variants("retained_variants", value.retained_variants, False)
    variants("rejected_variants", value.rejected_variants, False)


def trace(value: CounterevidenceTrace) -> None:
    if not hasattr(value, "owner") or not hasattr(value, "references"):
        raise ArbitrationContractError(
            "counterevidence_trace", "must define every field"
        )
    if type(value.owner) is not ClaimVariantRef:
        raise ArbitrationContractError("owner", "must be an exact ClaimVariantRef")
    validate_variant(value.owner.claim_id, value.owner.content_digest)
    canonical_references(value.references)


def nested(
    temporal_groups: tuple[TemporalGroup, ...],
    evidence_groups: tuple[EvidenceGroup, ...],
    traces: tuple[CounterevidenceTrace, ...],
    audits: tuple[ClaimAudit, ...],
    gates: tuple[GateRecord, ...],
) -> None:
    for field_path, values, expected, validator in (
        ("temporal_groups", temporal_groups, TemporalGroup, temporal),
        ("evidence_groups", evidence_groups, EvidenceGroup, evidence),
        ("counterevidence_traces", traces, CounterevidenceTrace, trace),
        ("audits", audits, ClaimAudit, audit),
        ("gates", gates, GateRecord, record),
    ):
        if type(values) is not tuple or any(
            type(value) is not expected for value in values
        ):
            raise ArbitrationContractError(field_path, "must be an exact typed tuple")
        for value in values:
            validator(value)

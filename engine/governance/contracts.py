from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from engine.governance.canonical import CanonicalValue, stable_object_id
from engine.governance.fact_values import (
    ConflictingFactIdError,
    DigestRef,
    DuplicateFactIdError,
    FactContractError,
    FactId,
    FactIntegrityError,
    FactLevel,
    FactSpec,
    FrozenJson,
    SnapshotId,
    SnapshotSpec,
    TemporalLayer,
    TemporalScope,
    freeze_payload,
)


_FACT_SCHEMA: Final = "governance.fact.v1"
_SNAPSHOT_SCHEMA: Final = "governance.fact-snapshot-content.v1"


def _scope_material(scope: TemporalScope) -> CanonicalValue:
    return (
        scope.layer.value,
        scope.dayun_start_year,
        scope.dayun_end_year,
        scope.target_year,
    )


def _digest_material(digest: DigestRef) -> CanonicalValue:
    return (digest.algorithm, digest.canonicalization, digest.value)


def _identity_material(spec: FactSpec) -> CanonicalValue:
    return (
        _FACT_SCHEMA,
        spec.fact_kind,
        _scope_material(spec.temporal_scope),
        spec.source_positions,
        spec.input_refs,
    )


@dataclass(frozen=True, slots=True)
class GovernanceFact:
    fact_id: FactId
    fact_kind: str
    fact_level: FactLevel
    temporal_scope: TemporalScope
    source_positions: tuple[str, ...]
    input_refs: tuple[str, ...]
    calculator_id: str
    calculator_version: str
    payload: FrozenJson
    content_digest: DigestRef

    def __post_init__(self) -> None:
        spec = FactSpec(
            fact_kind=self.fact_kind,
            fact_level=self.fact_level,
            temporal_scope=self.temporal_scope,
            source_positions=self.source_positions,
            input_refs=self.input_refs,
            calculator_id=self.calculator_id,
            calculator_version=self.calculator_version,
        )
        frozen = freeze_payload(self.payload)
        expected_id = FactId(str(stable_object_id("fact", _identity_material(spec))))
        expected_digest = DigestRef.from_material(
            _fact_material_values(expected_id, spec, frozen),
        )
        if self.fact_id != expected_id or self.content_digest != expected_digest:
            raise FactIntegrityError(
                "FACT.INTEGRITY_MISMATCH",
                "fact_id",
                "fact identity or content digest does not match canonical material",
            )
        object.__setattr__(self, "source_positions", spec.source_positions)
        object.__setattr__(self, "input_refs", spec.input_refs)
        object.__setattr__(self, "payload", frozen)


def _fact_material_values(
    fact_id: FactId,
    spec: FactSpec,
    payload: FrozenJson,
) -> CanonicalValue:
    return (
        _FACT_SCHEMA,
        str(fact_id),
        spec.fact_kind,
        spec.fact_level.value,
        _scope_material(spec.temporal_scope),
        spec.source_positions,
        spec.input_refs,
        spec.calculator_id,
        spec.calculator_version,
        payload,
    )


def _fact_material(fact: GovernanceFact) -> CanonicalValue:
    spec = FactSpec(
        fact_kind=fact.fact_kind,
        fact_level=fact.fact_level,
        temporal_scope=fact.temporal_scope,
        source_positions=fact.source_positions,
        input_refs=fact.input_refs,
        calculator_id=fact.calculator_id,
        calculator_version=fact.calculator_version,
    )
    return _fact_material_values(fact.fact_id, spec, fact.payload)


def build_governance_fact(spec: FactSpec, payload: CanonicalValue) -> GovernanceFact:
    frozen = freeze_payload(payload)
    fact_id = FactId(str(stable_object_id("fact", _identity_material(spec))))
    content_digest = DigestRef.from_material(
        _fact_material_values(fact_id, spec, frozen),
    )
    return GovernanceFact(
        fact_id=fact_id,
        fact_kind=spec.fact_kind,
        fact_level=spec.fact_level,
        temporal_scope=spec.temporal_scope,
        source_positions=spec.source_positions,
        input_refs=spec.input_refs,
        calculator_id=spec.calculator_id,
        calculator_version=spec.calculator_version,
        payload=frozen,
        content_digest=content_digest,
    )


def _sorted_unique_facts(
    facts: tuple[GovernanceFact, ...],
) -> tuple[GovernanceFact, ...]:
    if type(facts) is not tuple:
        raise FactContractError("FACT.SNAPSHOT_FACTS", "facts", "facts must be a tuple")
    if any(type(fact) is not GovernanceFact for fact in facts):
        raise FactContractError(
            "FACT.SNAPSHOT_FACT_TYPE",
            "facts",
            "facts must contain GovernanceFact values",
        )
    ordered = tuple(sorted(facts, key=lambda fact: fact.fact_id))
    for previous, current in zip(ordered, ordered[1:], strict=False):
        if previous.fact_id != current.fact_id:
            continue
        if previous == current:
            raise DuplicateFactIdError(
                "FACT.DUPLICATE_ID",
                "facts",
                f"duplicate fact ID: {current.fact_id}",
                current.fact_id,
            )
        raise ConflictingFactIdError(
            "FACT.CONFLICTING_ID",
            "facts",
            f"conflicting content for fact ID: {current.fact_id}",
            current.fact_id,
            previous.content_digest,
            current.content_digest,
        )
    return ordered


@dataclass(frozen=True, slots=True)
class FactSnapshot:
    snapshot_id: SnapshotId
    schema_version: str
    case_id: str
    facts: tuple[GovernanceFact, ...]
    input_digest: DigestRef
    content_digest: DigestRef

    def __post_init__(self) -> None:
        spec = SnapshotSpec(self.schema_version, self.case_id, self.input_digest)
        ordered = _sorted_unique_facts(self.facts)
        expected_id, expected_digest = _snapshot_bindings(spec, ordered)
        if self.snapshot_id != expected_id or self.content_digest != expected_digest:
            raise FactIntegrityError(
                "FACT.SNAPSHOT_INTEGRITY_MISMATCH",
                "snapshot_id",
                "snapshot identity or digest does not match canonical material",
            )
        object.__setattr__(self, "facts", ordered)


def _snapshot_bindings(
    spec: SnapshotSpec,
    facts: tuple[GovernanceFact, ...],
) -> tuple[SnapshotId, DigestRef]:
    identity = (
        spec.schema_version,
        spec.case_id,
        _digest_material(spec.input_digest),
        tuple(str(fact.fact_id) for fact in facts),
    )
    snapshot_id = SnapshotId(str(stable_object_id("fact_snapshot", identity)))
    material = (
        _SNAPSHOT_SCHEMA,
        str(snapshot_id),
        spec.schema_version,
        spec.case_id,
        _digest_material(spec.input_digest),
        tuple(_fact_material(fact) for fact in facts),
    )
    return snapshot_id, DigestRef.from_material(material)


def build_fact_snapshot(
    spec: SnapshotSpec, facts: tuple[GovernanceFact, ...]
) -> FactSnapshot:
    ordered = _sorted_unique_facts(facts)
    snapshot_id, content_digest = _snapshot_bindings(spec, ordered)
    return FactSnapshot(
        snapshot_id=snapshot_id,
        schema_version=spec.schema_version,
        case_id=spec.case_id,
        facts=ordered,
        input_digest=spec.input_digest,
        content_digest=content_digest,
    )


__all__ = (
    "ConflictingFactIdError",
    "DigestRef",
    "DuplicateFactIdError",
    "FactContractError",
    "FactId",
    "FactIntegrityError",
    "FactLevel",
    "FactSnapshot",
    "FactSpec",
    "GovernanceFact",
    "SnapshotId",
    "SnapshotSpec",
    "TemporalLayer",
    "TemporalScope",
    "build_fact_snapshot",
    "build_governance_fact",
)

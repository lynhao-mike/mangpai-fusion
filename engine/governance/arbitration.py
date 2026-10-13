from __future__ import annotations

from engine.governance.arbitration_contracts import (
    ArbitrationArena,
    ArbitrationContractError,
    ArbitrationContext,
    ArbitrationDecision,
    ArbitrationIntegrityError,
    ArbitrationIssueCode,
    ClaimVariantRef,
    CounterevidenceTrace,
    FactConflictContext,
    GateName,
)
from engine.governance.arbitration_result import ArbitrationResult
from engine.governance.composition import execute_composition
from engine.governance.arbitration_decision import decision_gate
from engine.governance.arbitration_gates import (
    applicability_gate,
    counterevidence_gate,
    eligibility_gate,
    evidence_gate,
    independence_gate,
    initial_progress,
    temporal_gate,
)


def arbitrate(arena: ArbitrationArena) -> ArbitrationResult:
    if arena.fact_conflicts:
        first = sorted(arena.fact_conflicts, key=lambda conflict: conflict.fact_id)[0]
        raise ArbitrationIntegrityError(
            code=ArbitrationIssueCode.FACT_CONFLICT,
            fact_id=first.fact_id,
        )
    progress = initial_progress(arena)
    progress = eligibility_gate(arena, progress)
    progress = temporal_gate(progress)
    progress = evidence_gate(arena, progress)
    progress = independence_gate(progress)
    progress = counterevidence_gate(progress)
    progress = applicability_gate(arena, progress)
    return decision_gate(progress)


__all__ = (
    "ArbitrationArena",
    "ArbitrationContractError",
    "ArbitrationContext",
    "ArbitrationDecision",
    "ArbitrationIntegrityError",
    "ClaimVariantRef",
    "CounterevidenceTrace",
    "FactConflictContext",
    "GateName",
    "arbitrate",
    "execute_composition",
    "applicability_gate",
    "counterevidence_gate",
    "decision_gate",
    "eligibility_gate",
    "evidence_gate",
    "independence_gate",
    "temporal_gate",
)

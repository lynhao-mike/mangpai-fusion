from __future__ import annotations

from typing import Final

from engine.governance.arbitration_contracts import (
    ClaimVariantRef,
    GateName,
    GateRecord,
)
from engine.governance.arbitration_values import ArbitrationContractError


_GATE_SEQUENCE: Final = tuple(GateName)
_APPLICABILITY_INDEX: Final = 5
_DECISION_INDEX: Final = 6


def gate_history(
    gates: tuple[GateRecord, ...],
    preserved_variants: tuple[ClaimVariantRef, ...],
    applicable_variants: tuple[ClaimVariantRef, ...],
) -> None:
    if tuple(record.gate for record in gates) != _GATE_SEQUENCE:
        raise ArbitrationContractError(
            "gates", "must contain the seven gates once in order"
        )
    expected_input = frozenset(preserved_variants)
    for record in gates:
        retained = frozenset(record.retained_variants)
        rejected = frozenset(record.rejected_variants)
        if retained & rejected:
            raise ArbitrationContractError(
                "gates", "cannot retain and reject one variant in the same gate"
            )
        if retained | rejected != expected_input:
            raise ArbitrationContractError(
                "gates", "must account for every variant from the preceding gate"
            )
        expected_input = retained
    applicable = frozenset(applicable_variants)
    if frozenset(gates[_APPLICABILITY_INDEX].retained_variants) != applicable:
        raise ArbitrationContractError(
            "applicable_variants", "must equal applicability gate retained variants"
        )
    if frozenset(gates[_DECISION_INDEX].retained_variants) != applicable:
        raise ArbitrationContractError(
            "gates", "decision gate must retain the applicable variants"
        )

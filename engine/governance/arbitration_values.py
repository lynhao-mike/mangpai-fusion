from __future__ import annotations

import re
from dataclasses import dataclass

from engine.governance.fact_values import DigestRef
from engine.governance.governance_claim_values import ClaimReference


_CLAIM_ID = re.compile(r"governance_claim:[0-9a-f]{64}")


@dataclass(frozen=True, slots=True)
class ArbitrationContractError(Exception):
    field_path: str
    diagnostic: str

    def __str__(self) -> str:
        return f"ARBITRATION.CONTRACT: {self.field_path}: {self.diagnostic}"


def validate_variant(claim_id: str, content_digest: DigestRef) -> None:
    if type(claim_id) is not str or _CLAIM_ID.fullmatch(claim_id) is None:
        raise ArbitrationContractError("claim_id", "must be an exact claim identity")
    if type(content_digest) is not DigestRef:
        raise ArbitrationContractError("content_digest", "must be an exact DigestRef")


def canonical_references(
    references: tuple[ClaimReference, ...],
) -> tuple[ClaimReference, ...]:
    if type(references) is not tuple or not references:
        raise ArbitrationContractError("references", "must be a nonempty exact tuple")
    if any(type(reference) is not ClaimReference for reference in references):
        raise ArbitrationContractError(
            "references", "must contain exact ClaimReference"
        )
    ordered = tuple(
        sorted(
            references,
            key=lambda reference: (
                reference.category.value,
                reference.reference_id,
                reference.version,
            ),
        )
    )
    if ordered != references or len(ordered) != len(set(ordered)):
        raise ArbitrationContractError("references", "must be sorted and unique")
    return ordered

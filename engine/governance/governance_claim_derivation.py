from __future__ import annotations

from typing import Final

from engine.governance.fact_values import DigestRef
from engine.governance.governance_claim_values import AdapterProvenance


_DERIVATION_SCHEMA: Final = "governance.claim.derivation.v1"


def derivation_chain_digest(
    source_claim_refs: tuple[str, ...],
    provenance: AdapterProvenance,
    source_metadata: tuple[tuple[str, str], ...],
) -> DigestRef:
    return DigestRef.from_material(
        (
            _DERIVATION_SCHEMA,
            source_claim_refs,
            provenance.adapter_id,
            provenance.adapter_version,
            source_metadata,
        )
    )

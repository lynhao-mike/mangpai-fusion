from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Mapping

from engine.decision.models import (
    ChartFactLedger,
    SchoolClaim,
    SchoolRole,
    StructuralVerdict,
)
from engine.decision.ziping_career_rules import (
    load_ziping_career_rule_mapping,
    mapping_digest,
)
from engine.decision.ziping_career_structure import (
    PublicationState,
    ZipingCareerDiscrimination,
    discriminate_ziping_career_structure,
)
from engine.features.types import ChartFeatureVector


MAPPING = load_ziping_career_rule_mapping()
_REQUIRED_FAMILIES = {
    "official_path_anchor",
    "output_interference",
    "geju_direction",
}


def _stable_id(prefix: str, *parts: object) -> str:
    raw = "|".join(str(part) for part in parts)
    return f"{prefix}-{hashlib.sha256(raw.encode('utf-8')).hexdigest()[:12]}"


@dataclass(frozen=True)
class ZipingCareerSliceRun:
    case_id: str
    result: ZipingCareerDiscrimination
    claims: tuple[SchoolClaim, ...]
    verdicts: tuple[StructuralVerdict, ...]
    events: tuple[object, ...] = ()
    timings: tuple[object, ...] = ()


def to_ziping_career_school_claim(
    result: ZipingCareerDiscrimination,
    role: SchoolRole,
    chart_signature: str,
) -> SchoolClaim:
    if result.publication_state is not PublicationState.EMIT:
        raise ValueError("emit publication state required for Ziping career L2 adapter")
    if role == "abstain":
        raise ValueError("non-abstain L1 role required")
    matched = tuple(item for item in result.families if item.matched)
    if not _REQUIRED_FAMILIES <= {item.family_key for item in matched}:
        raise ValueError("required evidence families are missing")
    evidence_refs = sorted(
        {
            *(f"family:{item.family_key}" for item in matched),
            *(f"fact:{ref}" for item in matched for ref in item.fact_refs),
            *(f"feature:{ref}" for item in matched for ref in item.feature_refs),
            *(
                f"rule:{ref}"
                for item in matched
                for ref in item.production_rule_refs
            ),
        }
    )
    return SchoolClaim(
        claim_id=_stable_id(
            "ziping-career-claim",
            "ziping",
            result.task_id,
            chart_signature,
            result.task_rule_id,
        ),
        school="ziping",
        role_granted_by_l1=role,
        domain="事业",
        claim_type="structure_claim",
        statement=MAPPING.conclusion_template,
        evidence_refs=evidence_refs,
        confidence=MAPPING.base_confidence,
        falsifier=MAPPING.falsifier,
        dependencies=[f"mapping:{result.mapping_digest}"],
        metadata={
            "task_id": result.task_id,
            "task_rule_id": result.task_rule_id,
            "publication_state": result.publication_state.value,
            "local_state": result.local_state.value,
            "mapping_digest": result.mapping_digest,
            "family_keys": sorted(item.family_key for item in matched),
        },
    )


def to_ziping_career_structural_verdict(
    case_id: str,
    result: ZipingCareerDiscrimination,
    claim: SchoolClaim,
) -> StructuralVerdict:
    if result.publication_state is not PublicationState.EMIT:
        raise ValueError("emit publication state required for Ziping career L3 adapter")
    if (
        result.task_rule_id != MAPPING.task_rule_id
        or claim.metadata.get("task_rule_id") != result.task_rule_id
    ):
        raise ValueError("task rule identity mismatch")
    expected_digest = mapping_digest(MAPPING)
    if (
        result.mapping_digest != expected_digest
        or claim.metadata.get("mapping_digest") != result.mapping_digest
        or claim.dependencies != [f"mapping:{result.mapping_digest}"]
    ):
        raise ValueError("mapping digest mismatch")
    result_families = {item.family_key for item in result.families if item.matched}
    claim_families = set(claim.metadata.get("family_keys", ()))
    if not _REQUIRED_FAMILIES <= result_families or not _REQUIRED_FAMILIES <= claim_families:
        raise ValueError("required evidence families are missing")
    if len(claim.evidence_refs) != len(set(claim.evidence_refs)):
        raise ValueError("duplicate evidence ref")
    if claim.claim_type != MAPPING.claim_type:
        raise ValueError("structure claim type required")
    if claim.school != MAPPING.school_id:
        raise ValueError("ziping school required")
    if claim.domain != MAPPING.domain:
        raise ValueError("career domain required")
    if "time_window" in claim.metadata:
        raise ValueError("time_window is forbidden in L3")
    return StructuralVerdict(
        verdict_id=_stable_id(
            "ziping-career-l3", case_id, claim.claim_id, result.mapping_digest
        ),
        claim_id=claim.claim_id,
        verdict="pass",
        structural_reason="官杀路径锚点、食伤介入与任务专属结构资格门均通过。",
        blocking_factors=[],
        required_support=[],
        confidence=min(0.7, claim.confidence),
    )


def build_ziping_career_structure_slice(
    case_id: str,
    chart: ChartFactLedger,
    features: ChartFeatureVector,
    geju_profile: Mapping[str, object],
    *,
    role: SchoolRole,
) -> ZipingCareerSliceRun:
    result = discriminate_ziping_career_structure(chart, features, geju_profile)
    if result.publication_state is not PublicationState.EMIT:
        return ZipingCareerSliceRun(case_id, result, (), ())
    claim = to_ziping_career_school_claim(result, role, features.chart_id)
    verdict = to_ziping_career_structural_verdict(case_id, result, claim)
    return ZipingCareerSliceRun(case_id, result, (claim,), (verdict,))

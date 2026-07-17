from __future__ import annotations

import hashlib
from dataclasses import dataclass, replace
from typing import Any, Mapping

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
from engine.evaluation.freeze import canonical_json, compute_freeze_hash
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


def _sorted_mapping(value: Mapping[str, object]) -> dict[str, object]:
    return {key: value[key] for key in sorted(value)}


def _sorted_claim(claim: SchoolClaim) -> dict[str, Any]:
    payload = claim.to_dict()
    payload["evidence_refs"] = sorted(payload["evidence_refs"])
    payload["dependencies"] = sorted(payload["dependencies"])
    metadata = payload["metadata"]
    if isinstance(metadata, dict):
        payload["metadata"] = _sorted_mapping(metadata)
        family_keys = payload["metadata"].get("family_keys")
        if isinstance(family_keys, (list, tuple)):
            payload["metadata"]["family_keys"] = sorted(family_keys)
    return payload


def _sorted_verdict(verdict: StructuralVerdict) -> dict[str, Any]:
    payload = verdict.to_dict()
    payload["blocking_factors"] = sorted(payload["blocking_factors"])
    payload["required_support"] = sorted(payload["required_support"])
    return payload


@dataclass(frozen=True)
class FrozenZipingCareerSlice:
    schema_version: str
    case_id: str
    task_id: str
    task_rule_id: str
    mapping_digest: str
    local_state: str
    publication_state: str
    families: tuple[dict[str, Any], ...]
    gates: tuple[tuple[str, bool], ...]
    claims: tuple[dict[str, Any], ...]
    verdicts: tuple[dict[str, Any], ...]
    events: tuple[dict[str, Any], ...]
    timings: tuple[dict[str, Any], ...]
    freeze_hash: str

    @classmethod
    def from_run(
        cls, run: ZipingCareerSliceRun, *, freeze_hash: str
    ) -> FrozenZipingCareerSlice:
        if run.events or run.timings:
            raise ValueError("Ziping career staged slice must stop at L3")
        families = tuple(
            {
                "family_key": family.family_key,
                "matched": family.matched,
                "fact_refs": sorted(family.fact_refs),
                "feature_refs": sorted(family.feature_refs),
                "production_rule_refs": sorted(family.production_rule_refs),
                "reason_codes": sorted(family.reason_codes),
                "detail": family.detail,
            }
            for family in sorted(run.result.families, key=lambda item: item.family_key)
        )
        return cls(
            schema_version="ziping-career-staged-slice/v1",
            case_id=run.case_id,
            task_id=run.result.task_id,
            task_rule_id=run.result.task_rule_id,
            mapping_digest=run.result.mapping_digest,
            local_state=run.result.local_state.value,
            publication_state=run.result.publication_state.value,
            families=families,
            gates=tuple(sorted(run.result.gates.items())),
            claims=tuple(
                _sorted_claim(claim)
                for claim in sorted(run.claims, key=lambda item: item.claim_id)
            ),
            verdicts=tuple(
                _sorted_verdict(verdict)
                for verdict in sorted(run.verdicts, key=lambda item: item.verdict_id)
            ),
            events=(),
            timings=(),
            freeze_hash=freeze_hash,
        )

    def to_dict(self) -> dict[str, object]:
        payload = {
            "schema_version": self.schema_version,
            "case_id": self.case_id,
            "task_id": self.task_id,
            "task_rule_id": self.task_rule_id,
            "mapping_digest": self.mapping_digest,
            "local_state": self.local_state,
            "publication_state": self.publication_state,
            "families": sorted(self.families, key=lambda item: item["family_key"]),
            "gates": {key: value for key, value in sorted(self.gates)},
            "claims": sorted(self.claims, key=lambda item: item["claim_id"]),
            "verdicts": sorted(self.verdicts, key=lambda item: item["verdict_id"]),
            "events": list(self.events),
            "timings": list(self.timings),
            "freeze_hash": self.freeze_hash,
        }
        canonical_json(payload)
        return payload


def freeze_ziping_career_slice(
    run: ZipingCareerSliceRun,
) -> FrozenZipingCareerSlice:
    provisional = FrozenZipingCareerSlice.from_run(run, freeze_hash="")
    payload = provisional.to_dict()
    payload.pop("freeze_hash")
    return replace(provisional, freeze_hash=compute_freeze_hash(payload))


def verify_frozen_ziping_career_slice(frozen: FrozenZipingCareerSlice) -> None:
    if frozen.events or frozen.timings:
        raise ValueError("Ziping career staged slice must stop at L3")
    payload = frozen.to_dict()
    claimed = payload.pop("freeze_hash")
    if compute_freeze_hash(payload) != claimed:
        raise ValueError("freeze hash mismatch")


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

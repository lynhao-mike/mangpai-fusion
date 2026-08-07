"""三领域运行时能力元数据的版本化完整性封装。"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping, Sequence

from engine.v5.domain import V5Claim, V5_SCHOOLS

CAPABILITY_INTEGRITY_SCHEMA = "domain-capability-integrity/v1"
DOMAIN_EVALUATION_INTEGRITY_SCHEMA = "domain-evaluation-integrity/v1"
_PROTECTED_FIELDS = (
    "requested_domains",
    "slice_coverage",
    "domain_evaluation_claims",
    "domain_evaluation_exclusions",
    "domain_evaluation_integrity",
)
_DOMAIN_IDS = {"事业": "career", "财富": "wealth", "婚姻": "marriage"}
_EVALUABLE_CLAIM_TYPES = frozenset({"structure_claim", "event_claim", "timing_claim"})


def _canonical_sha256(payload: object) -> str:
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _digest(metadata: Mapping[str, Any]) -> str:
    protected = {key: metadata.get(key) for key in _PROTECTED_FIELDS}
    return _canonical_sha256(protected)


def build_domain_evaluation_metadata(claims: Sequence[V5Claim]) -> dict[str, Any]:
    """从真实 runtime claim 确定性投影保守的 prospective 可评估子集。"""

    manifest: list[dict[str, str]] = []
    exclusions: list[dict[str, str]] = []
    for claim in claims:
        domain = _DOMAIN_IDS.get(claim.domain, "")
        task_id = str(claim.metadata.get("task_id", "")).strip()
        reason = ""
        if not task_id:
            reason = "missing_task_id"
        elif claim.stance == "abstain":
            reason = "abstain"
        elif domain == "" or not task_id.startswith(domain + "."):
            reason = "unstable_domain_task_target"
        elif claim.school not in V5_SCHOOLS:
            reason = "invalid_school"
        elif claim.claim_type not in _EVALUABLE_CLAIM_TYPES:
            reason = "non_evaluable_claim_type"
        elif not claim.evidence:
            reason = "missing_evidence"
        elif not claim.falsifiable.strip():
            reason = "missing_falsifier"

        source_claim_hash = _canonical_sha256(claim.to_dict())
        if reason:
            exclusions.append(
                {
                    "source_claim_id": claim.claim_id,
                    "source_claim_hash": source_claim_hash,
                    "school": claim.school,
                    "domain": domain,
                    "task_id": task_id,
                    "claim_type": claim.claim_type,
                    "stance": claim.stance,
                    "reason": reason,
                }
            )
            continue

        identity = {
            "source_claim_id": claim.claim_id,
            "source_claim_hash": source_claim_hash,
            "school": claim.school,
            "domain": domain,
            "task_id": task_id,
            "claim_type": claim.claim_type,
        }
        manifest.append(
            {
                "claim_id": "domain-eval-" + _canonical_sha256(identity)[:20],
                **identity,
                "state": "claim",
            }
        )

    evaluation_payload = {
        "domain_evaluation_claims": manifest,
        "domain_evaluation_exclusions": exclusions,
    }
    return {
        **evaluation_payload,
        "domain_evaluation_integrity": {
            "schema_version": DOMAIN_EVALUATION_INTEGRITY_SCHEMA,
            "sha256": _canonical_sha256(evaluation_payload),
        },
    }


def validate_domain_evaluation_metadata(
    claims: Sequence[V5Claim], metadata: Mapping[str, Any]
) -> None:
    """重算 producer 投影，拒绝 shape-valid 篡改与重新封印。"""

    expected = build_domain_evaluation_metadata(claims)
    actual = {key: metadata.get(key) for key in expected}
    if actual != expected:
        raise ValueError("domain evaluation manifest integrity or projection mismatch")


def seal_capability_metadata(metadata: Mapping[str, Any]) -> dict[str, Any]:
    """返回带版本化摘要的元数据副本。"""

    result = dict(metadata)
    result["capability_integrity"] = {
        "schema_version": CAPABILITY_INTEGRITY_SCHEMA,
        "sha256": _digest(result),
    }
    return result


def validate_capability_metadata(metadata: Mapping[str, Any]) -> None:
    """失败关闭验证能力统计依赖的运行时元数据。"""

    integrity = metadata.get("capability_integrity")
    if not isinstance(integrity, Mapping):
        raise ValueError("runtime capability metadata integrity is unavailable")
    if integrity.get("schema_version") != CAPABILITY_INTEGRITY_SCHEMA:
        raise ValueError("runtime capability metadata integrity schema is unsupported")
    digest = integrity.get("sha256")
    if not isinstance(digest, str) or digest != _digest(metadata):
        raise ValueError("runtime capability metadata integrity hash mismatch")

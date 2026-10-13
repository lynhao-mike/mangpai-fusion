from __future__ import annotations

from typing import Final

from engine.application.governance_claim_adapter_values import (
    AdaptationResult,
    catalog_loss,
    loss,
)
from engine.decision.yang_marriage import YangMarriageDiscrimination
from engine.governance import (
    AdapterProvenance,
    ClaimEvidenceGrade,
    ClaimIssueCode,
    ClaimKind,
    ClaimReference,
    ClaimReferenceCategory,
    ClaimStance,
    GovernanceClaimContractError,
    GovernanceClaimSpec,
    GovernanceReferenceCatalog,
    TemporalLayer,
    TemporalScope,
    build_governance_claim,
    stable_object_id,
)
from engine.governance.governance_claim_derivation import derivation_chain_digest

_SCHOOL_ID: Final = "yang_qingjuan"
_TASK_ID: Final = "marriage.divorce_or_remarriage"
_ADAPTER_ID: Final = "yang_marriage_discrimination"
_ADAPTER_VERSION: Final = "yang-marriage-discrimination/v1"
_SOURCE_VERSION: Final = (
    "sha256:e8be77f67246ff056770a35d618b4b3fc5694ba5fdec2f65c8d674708355e768"
)
_SOURCE_RULE_REFS: Final = (
    "theory/yang/index.yaml#M2-Y-068",
    "theory/yang/index.yaml#M2-Y-088",
)
_CONFIDENCE: Final = 0.60
_CONCLUSION: Final = (
    "杨派原局夫妻宫事件锚与独立配偶结构交互同向，"
    "支持存在离婚或再婚事件风险，但不作必然判断。"
)


def adapt_yang_marriage_discrimination(
    result: YangMarriageDiscrimination,
    catalog: GovernanceReferenceCatalog,
) -> AdaptationResult:
    if type(result) is not YangMarriageDiscrimination:
        return loss(
            ClaimIssueCode.ADAPTER_INPUT_INVALID,
            "expected YangMarriageDiscrimination",
        )
    if result.state == "pressure":
        return loss(
            ClaimIssueCode.INSUFFICIENT_EVIDENCE,
            "pressure state does not support a divorce or remarriage event claim",
        )
    if result.state == "abstain":
        blockers = ", ".join(result.blocking_reason_codes)
        return loss(
            ClaimIssueCode.INSUFFICIENT_EVIDENCE,
            f"abstain state retains blockers: {blockers}",
        )
    if result.source_rule_refs != _SOURCE_RULE_REFS:
        return loss(
            ClaimIssueCode.LEGACY_REFERENCE_INVALID,
            "event source rules must match the frozen Yang marriage anchors exactly",
        )

    references = tuple(
        ClaimReference(ClaimReferenceCategory.SOURCE_RULE, reference, _SOURCE_VERSION)
        for reference in _SOURCE_RULE_REFS
    )
    source_claim_ref = str(
        stable_object_id("yang_marriage_discrimination", result.to_dict())
    )
    provenance = AdapterProvenance(
        adapter_id=_ADAPTER_ID,
        adapter_version=_ADAPTER_VERSION,
        source_claim_ref=source_claim_ref,
    )
    source_metadata = (
        ("school_id", _SCHOOL_ID),
        ("task_id", _TASK_ID),
        ("claim_kind", ClaimKind.EVENT.value),
        ("stance", ClaimStance.SUPPORT.value),
        ("temporal_layer", TemporalLayer.NATAL.value),
        ("evidence_grade", ClaimEvidenceGrade.INFERENTIAL.value),
        ("confidence", f"{_CONFIDENCE:.2f}"),
        ("adapter_version", _ADAPTER_VERSION),
        ("source_version", _SOURCE_VERSION),
        ("source_rule_ref_0", _SOURCE_RULE_REFS[0]),
        ("source_rule_ref_1", _SOURCE_RULE_REFS[1]),
    )
    spec = GovernanceClaimSpec(
        school_id=_SCHOOL_ID,
        task_id=_TASK_ID,
        claim_kind=ClaimKind.EVENT,
        stance=ClaimStance.SUPPORT,
        conclusion=_CONCLUSION,
        public_fact_refs=(),
        certified_fact_refs=(),
        school_reason_refs=(),
        source_rule_refs=references,
        temporal_scope=TemporalScope(layer=TemporalLayer.NATAL),
        blockers=(),
        counterevidence=(),
        falsifier=result.falsifier,
        confidence=_CONFIDENCE,
        evidence_grade=ClaimEvidenceGrade.INFERENTIAL,
        derivation_chain_digest=derivation_chain_digest(
            (source_claim_ref,),
            provenance,
            source_metadata,
        ),
        adapter_provenance=provenance,
    )
    try:
        claim = build_governance_claim(spec, catalog)
    except GovernanceClaimContractError as error:
        return catalog_loss(error)
    return AdaptationResult(claim, ())

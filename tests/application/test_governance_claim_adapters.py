from __future__ import annotations

from dataclasses import fields

from engine.claims.domain import Claim, Evidence
from engine.decision.models import SchoolClaim
from engine.governance import (
    ClaimReferenceCategory,
    GovernanceReferenceCatalog,
    ClaimStance,
    ReferenceRegistration,
    TemporalLayer,
    TemporalScope,
)


def _catalog() -> GovernanceReferenceCatalog:
    return GovernanceReferenceCatalog(
        registrations=(
            ReferenceRegistration(
                ClaimReferenceCategory.SCHOOL_REASON, "family:signal", "legacy-v1"
            ),
            ReferenceRegistration(
                ClaimReferenceCategory.SOURCE_RULE, "rule:yang.rule", "legacy-v1"
            ),
            ReferenceRegistration(
                ClaimReferenceCategory.SCHOOL_REASON, "evidence:legacy", "legacy-v1"
            ),
            ReferenceRegistration(
                ClaimReferenceCategory.SOURCE_RULE, "yang.rule", "legacy-v1"
            ),
        )
    )


def test_legacy_school_claim_fields_remain_frozen_for_compatibility() -> None:
    # Given / When: the legacy decision model is inspected without adaptation.
    names = tuple(field.name for field in fields(SchoolClaim))

    # Then: its compatibility surface is exact.
    assert names == (
        "claim_id",
        "school",
        "role_granted_by_l1",
        "domain",
        "claim_type",
        "statement",
        "evidence_refs",
        "confidence",
        "falsifier",
        "dependencies",
        "metadata",
    )


def test_legacy_claim_fields_remain_frozen_for_compatibility() -> None:
    # Given / When: the legacy domain model is inspected without adaptation.
    names = tuple(field.name for field in fields(Claim))

    # Then: its compatibility surface is exact.
    assert names == (
        "claim_id",
        "school_id",
        "task_id",
        "claim_type",
        "stance",
        "statement",
        "evidence",
        "falsifier",
        "time_window",
        "confidence_basis",
        "applicability_snapshot",
        "domain",
        "polarity",
        "magnitude",
        "confidence",
        "high_risk",
        "target_id",
    )


def test_school_claim_adapter_does_not_guess_missing_temporal_scope() -> None:
    from engine.application.governance_claim_adapters import adapt_decision_school_claim

    # Given: a Yang event support claim that lacks a whitelisted temporal scope.
    legacy = SchoolClaim(
        claim_id="legacy-yang",
        school="yang",
        role_granted_by_l1="lead",
        domain="marriage",
        claim_type="event_claim",
        statement="support only",
        evidence_refs=["family:signal", "rule:yang.rule"],
        confidence=0.6,
        falsifier="contrary registered result",
        metadata={"task_id": "marriage.divorce_or_remarriage", "stance": "support"},
    )

    # When: the explicit legacy adapter is used.
    result = adapt_decision_school_claim(legacy, _catalog())

    # Then: it returns a typed loss instead of assuming natal scope or support.
    assert result.claim is None
    assert {issue.code.value for issue in result.issues} == {"TEMPORAL_SCOPE_MISSING"}


def test_school_claim_adapter_maps_alias_only_at_boundary_with_explicit_scope() -> None:
    from engine.application.governance_claim_adapters import adapt_decision_school_claim

    # Given: an alias-bearing legacy school claim with only whitelisted metadata.
    legacy = SchoolClaim(
        claim_id="legacy-yang",
        school="yang",
        role_granted_by_l1="lead",
        domain="marriage",
        claim_type="event_claim",
        statement="support only",
        evidence_refs=["family:signal", "rule:yang.rule"],
        confidence=0.6,
        falsifier="contrary registered result",
        metadata={
            "task_id": "marriage.divorce_or_remarriage",
            "stance": "support",
            "temporal_scope": "natal",
            "reference_version": "legacy-v1",
        },
    )

    # When: it crosses the named adapter boundary.
    result = adapt_decision_school_claim(legacy, _catalog())

    # Then: the governance core receives only the canonical school ID.
    assert result.claim is not None
    assert result.claim.school_id == "yang_qingjuan"


def test_claim_adapter_marks_unrepresentable_legacy_semantics_as_losses() -> None:
    from engine.application.governance_claim_adapters import adapt_domain_claim

    # Given: a legacy model that cannot represent conditional or abstain stance.
    legacy = Claim(
        claim_id="legacy-claim",
        school_id="ziping",
        task_id="structure.assessment",
        claim_type="structure_claim",
        stance="support",
        statement="legacy assertion",
        evidence=(
            Evidence(
                evidence_id="evidence:legacy",
                fact_refs=(),
                feature_refs=("feature",),
                rule_id="yang.rule",
                text="legacy evidence",
            ),
        ),
        falsifier="contrary result",
        time_window=None,
        confidence_basis="legacy",
        applicability_snapshot={},
    )

    # When: metadata requests a governance-only stance.
    result = adapt_domain_claim(
        legacy,
        _catalog(),
        temporal_scope=TemporalScope(layer=TemporalLayer.NATAL),
        requested_stance=ClaimStance.CONDITIONAL,
    )

    # Then: the adapter reports a concrete downgrade rather than inventing support.
    assert result.claim is None
    assert {issue.code.value for issue in result.issues} == {"LEGACY_CONDITIONAL_LOSS"}


def test_yang_pressure_is_not_adapted_into_event_support() -> None:
    from engine.application.governance_claim_adapters import adapt_decision_school_claim

    # Given: an old Yang pressure claim, which must not become an event vote.
    legacy = SchoolClaim(
        claim_id="yang-pressure",
        school="yang_qingjuan",
        role_granted_by_l1="lead",
        domain="marriage",
        claim_type="pressure",
        statement="pressure only",
        evidence_refs=["family:signal", "rule:yang.rule"],
        confidence=0.2,
        falsifier="",
        metadata={
            "task_id": "marriage.divorce_or_remarriage",
            "stance": "support",
            "temporal_scope": "natal",
            "reference_version": "legacy-v1",
        },
    )

    # When: the exact legacy adapter receives it.
    result = adapt_decision_school_claim(legacy, _catalog())

    # Then: no event-support GovernanceClaim is produced.
    assert result.claim is None
    assert {issue.code.value for issue in result.issues} == {"UNSUPPORTED_LEGACY_CLAIM"}

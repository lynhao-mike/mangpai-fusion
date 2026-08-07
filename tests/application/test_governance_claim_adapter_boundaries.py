from __future__ import annotations

from engine.claims.domain import Claim, Evidence
from engine.decision.models import SchoolClaim
from engine.governance import (
    ClaimReferenceCategory,
    GovernanceReferenceCatalog,
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


def test_adapters_reject_duck_typed_fake_claims() -> None:
    from engine.application.governance_claim_adapters import (
        adapt_decision_school_claim,
        adapt_domain_claim,
    )

    # Given: structural lookalikes that are not legacy contract instances.
    class FakeSchoolClaim:
        pass

    class FakeClaim:
        pass

    # When: both named adapters receive a fake object.
    school_result = adapt_decision_school_claim(FakeSchoolClaim(), _catalog())
    domain_result = adapt_domain_claim(
        FakeClaim(), _catalog(), TemporalScope(layer=TemporalLayer.NATAL)
    )

    # Then: the boundary returns typed losses rather than dereferencing it.
    assert school_result.claim is None
    assert domain_result.claim is None
    assert {issue.code.value for issue in school_result.issues} == {
        "ADAPTER_INPUT_INVALID"
    }
    assert {issue.code.value for issue in domain_result.issues} == {
        "ADAPTER_INPUT_INVALID"
    }


def test_school_claim_adapter_never_admits_abstain_role_as_support() -> None:
    from engine.application.governance_claim_adapters import adapt_decision_school_claim

    # Given: a legacy abstaining role with contradictory support metadata.
    legacy = SchoolClaim(
        claim_id="legacy-abstain",
        school="yang_qingjuan",
        role_granted_by_l1="abstain",
        domain="marriage",
        claim_type="event_claim",
        statement="must not be emitted",
        evidence_refs=["family:signal", "rule:yang.rule"],
        confidence=0.6,
        falsifier="contrary result",
        metadata={
            "task_id": "marriage.divorce_or_remarriage",
            "stance": "support",
            "temporal_scope": "natal",
            "reference_version": "legacy-v1",
        },
    )

    # When: the concrete legacy claim is adapted.
    result = adapt_decision_school_claim(legacy, _catalog())

    # Then: its granted abstention wins over metadata.
    assert result.claim is None
    assert {issue.code.value for issue in result.issues} == {"LEGACY_ROLE_ABSTAIN"}


def test_adapters_reject_unapproved_legacy_context() -> None:
    from engine.application.governance_claim_adapters import (
        adapt_decision_school_claim,
        adapt_domain_claim,
    )

    # Given: a SchoolClaim metadata injection and Claim applicability context.
    school = SchoolClaim(
        claim_id="legacy-injected",
        school="yang_qingjuan",
        role_granted_by_l1="lead",
        domain="marriage",
        claim_type="event_claim",
        statement="injected context",
        evidence_refs=["family:signal", "rule:yang.rule"],
        confidence=0.6,
        falsifier="contrary result",
        metadata={
            "task_id": "marriage.divorce_or_remarriage",
            "stance": "support",
            "temporal_scope": "natal",
            "reference_version": "legacy-v1",
            "source_scope": "legacy-hidden-context",
        },
    )
    domain = Claim(
        claim_id="legacy-context",
        school_id="ziping",
        task_id="structure.assessment",
        claim_type="structure_claim",
        stance="support",
        statement="unapproved context",
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
        applicability_snapshot={"source_scope": "legacy-hidden-context"},
    )

    # When: the adapters receive values outside their explicit allowlists.
    school_result = adapt_decision_school_claim(school, _catalog())
    domain_result = adapt_domain_claim(
        domain, _catalog(), TemporalScope(layer=TemporalLayer.NATAL)
    )

    # Then: neither unreviewed context can reach a governance claim.
    assert school_result.claim is None
    assert domain_result.claim is None
    assert {issue.code.value for issue in school_result.issues} == {
        "LEGACY_METADATA_UNAPPROVED"
    }
    assert {issue.code.value for issue in domain_result.issues} == {
        "LEGACY_CONTEXT_UNAPPROVED"
    }


def test_adapters_convert_catalog_rejections_to_auditable_losses() -> None:
    from engine.application.governance_claim_adapters import (
        adapt_decision_school_claim,
        adapt_domain_claim,
    )

    # Given: valid legacy claims whose references have no catalog registration.
    school = SchoolClaim(
        claim_id="legacy-empty-catalog",
        school="yang_qingjuan",
        role_granted_by_l1="lead",
        domain="marriage",
        claim_type="event_claim",
        statement="unregistered evidence",
        evidence_refs=["family:signal", "rule:yang.rule"],
        confidence=0.6,
        falsifier="contrary result",
        metadata={
            "task_id": "marriage.divorce_or_remarriage",
            "stance": "support",
            "temporal_scope": "natal",
            "reference_version": "legacy-v1",
        },
    )
    domain = Claim(
        claim_id="legacy-wrong-version",
        school_id="ziping",
        task_id="structure.assessment",
        claim_type="structure_claim",
        stance="support",
        statement="wrong version",
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
    wrong_version_catalog = GovernanceReferenceCatalog(
        registrations=(
            ReferenceRegistration(
                ClaimReferenceCategory.SCHOOL_REASON, "evidence:legacy", "legacy-v2"
            ),
            ReferenceRegistration(
                ClaimReferenceCategory.SOURCE_RULE, "yang.rule", "legacy-v2"
            ),
        )
    )

    # When: reference validation rejects their exact catalog identities.
    school_result = adapt_decision_school_claim(school, GovernanceReferenceCatalog(()))
    domain_result = adapt_domain_claim(
        domain, wrong_version_catalog, TemporalScope(layer=TemporalLayer.NATAL)
    )

    # Then: the original catalog issue is preserved without leaking an exception.
    assert school_result.claim is None
    assert domain_result.claim is None
    assert school_result.issues[0].code.value == "LEGACY_REFERENCE_REJECTED"
    assert domain_result.issues[0].code.value == "LEGACY_REFERENCE_REJECTED"
    assert "CLAIM.REFERENCE_UNKNOWN" in school_result.issues[0].detail
    assert "CLAIM.REFERENCE_VERSION" in domain_result.issues[0].detail


def test_adapters_preserve_non_reference_contract_rejection_classification() -> None:
    from engine.application.governance_claim_adapters import adapt_decision_school_claim

    # Given: a concrete legacy claim with valid references but invalid confidence.
    legacy = SchoolClaim(
        claim_id="legacy-invalid-confidence",
        school="yang_qingjuan",
        role_granted_by_l1="lead",
        domain="marriage",
        claim_type="event_claim",
        statement="invalid confidence",
        evidence_refs=["family:signal", "rule:yang.rule"],
        confidence=1.5,
        falsifier="contrary result",
        metadata={
            "task_id": "marriage.divorce_or_remarriage",
            "stance": "support",
            "temporal_scope": "natal",
            "reference_version": "legacy-v1",
        },
    )

    # When: the adapter encounters the governance claim contract failure.
    result = adapt_decision_school_claim(legacy, _catalog())

    # Then: the loss retains its non-reference source classification.
    assert result.claim is None
    assert result.issues[0].code.value == "LEGACY_CLAIM_REJECTED"
    assert "CLAIM.CONFIDENCE" in result.issues[0].detail

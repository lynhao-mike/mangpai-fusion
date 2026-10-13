from __future__ import annotations

import subprocess
import sys

from engine.claims.domain import Claim, Evidence
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


def _fresh_school_derivation_digest(claim_id: str, version: str) -> str:
    code = (
        "from engine.application.governance_claim_adapters import "
        "adapt_decision_school_claim\n"
        "from engine.decision.models import SchoolClaim\n"
        "from engine.governance import (ClaimReferenceCategory, "
        "GovernanceReferenceCatalog, ReferenceRegistration)\n"
        "catalog = GovernanceReferenceCatalog(("
        "ReferenceRegistration(ClaimReferenceCategory.SCHOOL_REASON, "
        f"'family:signal', {version!r}), "
        "ReferenceRegistration(ClaimReferenceCategory.SOURCE_RULE, "
        f"'rule:yang.rule', {version!r})))\n"
        f"claim = SchoolClaim(claim_id={claim_id!r}, school='yang_qingjuan', "
        "role_granted_by_l1='lead', domain='marriage', claim_type='event_claim', "
        "statement='source-bound', evidence_refs=['family:signal', 'rule:yang.rule'], "
        "confidence=0.6, falsifier='contrary result', metadata={'task_id': "
        "'marriage.divorce_or_remarriage', 'stance': 'support', "
        f"'temporal_scope': 'natal', 'reference_version': {version!r}}})\n"
        "print(adapt_decision_school_claim(claim, catalog).claim.derivation_chain_digest.value)\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", code], check=False, capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


def _domain_claim(claim_id: str) -> Claim:
    return Claim(
        claim_id=claim_id,
        school_id="ziping",
        task_id="structure.assessment",
        claim_type="structure_claim",
        stance="support",
        statement="source-bound",
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


def test_school_adapter_derivation_is_fresh_process_stable_and_source_bound() -> None:
    # Given: independently started adapters with stable and changed source identity.
    baseline = _fresh_school_derivation_digest("legacy-school-a", "legacy-v1")
    replay = _fresh_school_derivation_digest("legacy-school-a", "legacy-v1")
    changed_source = _fresh_school_derivation_digest("legacy-school-b", "legacy-v1")
    changed_version = _fresh_school_derivation_digest("legacy-school-a", "legacy-v2")

    # When / Then: only equivalent approved source material has an equal digest.
    assert baseline == replay
    assert baseline != changed_source
    assert baseline != changed_version


def test_domain_adapter_derivation_is_source_claim_bound() -> None:
    from engine.application.governance_claim_adapters import adapt_domain_claim

    # Given: equivalent legacy claim content with distinct legacy source identities.
    first = adapt_domain_claim(
        _domain_claim("legacy-domain-a"),
        _catalog(),
        TemporalScope(layer=TemporalLayer.NATAL),
    )
    second = adapt_domain_claim(
        _domain_claim("legacy-domain-b"),
        _catalog(),
        TemporalScope(layer=TemporalLayer.NATAL),
    )

    # When / Then: the approved source claim reference changes the derivation digest.
    assert first.claim is not None
    assert second.claim is not None
    assert first.claim.derivation_chain_digest != second.claim.derivation_chain_digest

"""六源三领域编排器 P1 行为测试。"""

from __future__ import annotations

from datetime import date, datetime

from engine.v5.domain import V5Claim, V5Confidence, V5Evidence, V5_SCHOOLS
from engine.v5.domain_slices.contract import DOMAIN_IDS, DomainAnalysisRequest, SliceAudit, SliceResult
from engine.v5.domain_slices.orchestrator import run_domain_analysis
from engine.v5.domain_slices.registry import DomainSliceRegistry, SliceRegistration, build_abstain_registry


def _request(domains=DOMAIN_IDS) -> DomainAnalysisRequest:
    return DomainAnalysisRequest(
        gender="乾",
        birth_datetime=datetime(1990, 1, 1, 12, 0),
        as_of_date=date(2026, 7, 31),
        domains=domains,
        output_dir="reports/domain-analysis",
    )


def test_p1_abstain_registry_produces_auditable_snapshot_without_fabricated_predictions() -> None:
    snapshot = run_domain_analysis(_request(), registry=build_abstain_registry())

    coverage = snapshot.metadata["slice_coverage"]
    assert len(coverage) == 18
    assert {item["status"] for item in coverage} == {"abstain"}
    assert {claim.school for claim in snapshot.claims} == {
        "ziping",
        "ditiansui",
        "gao_dechen",
        "duan_jianye",
        "yang_qingjuan",
        "ren_fuhong",
    }
    assert all(claim.stance == "abstain" for claim in snapshot.claims)
    assert snapshot.prediction_ledger.predictions == []
    assert snapshot.metadata["domain_conclusions"] == {
        "career": "证据不足",
        "wealth": "证据不足",
        "marriage": "证据不足",
    }
    assert snapshot.output_hash_matches()


def test_selected_domain_limits_claims_but_preserves_full_registry_audit() -> None:
    snapshot = run_domain_analysis(_request(("career",)), registry=build_abstain_registry())

    assert {claim.domain for claim in snapshot.claims} == {"事业"}
    assert len(snapshot.claims) == 6
    assert len(snapshot.metadata["slice_coverage"]) == 18
    assert snapshot.metadata["requested_domains"] == ["career"]


def test_same_request_produces_same_run_id() -> None:
    left = run_domain_analysis(_request(), registry=build_abstain_registry())
    right = run_domain_analysis(_request(), registry=build_abstain_registry())

    assert left.run_id == right.run_id
    assert left.output_hash == right.output_hash



def _registry_with_career_registration(registration: SliceRegistration) -> DomainSliceRegistry:
    return DomainSliceRegistry(
        registration
        if (school, domain) == (registration.school, registration.domain)
        else SliceRegistration(school=school, domain=domain, status="abstain")
        for school in V5_SCHOOLS
        for domain in DOMAIN_IDS
    )



def test_implemented_slice_exception_degrades_to_abstain_without_prediction() -> None:
    def broken(context):
        raise RuntimeError("boom")

    registration = SliceRegistration(school="ziping", domain="career", status="implemented", generator=broken)
    snapshot = run_domain_analysis(_request(("career",)), registry=_registry_with_career_registration(registration))
    slot = next(item for item in snapshot.metadata["slice_coverage"] if item["school"] == "ziping" and item["domain"] == "career")
    claim = next(item for item in snapshot.claims if item.school == "ziping")

    assert slot["status"] == "abstain"
    assert slot["audit"]["error_type"] == "RuntimeError"
    assert claim.metadata["slice_status"] == "abstain"
    assert snapshot.prediction_ledger.predictions == []



def test_unsupported_slice_is_explicit_abstain_not_opposition() -> None:
    registration = SliceRegistration(school="ziping", domain="career", status="unsupported")
    snapshot = run_domain_analysis(_request(("career",)), registry=_registry_with_career_registration(registration))
    claim = next(item for item in snapshot.claims if item.school == "ziping")

    assert claim.stance == "abstain"
    assert claim.metadata["slice_status"] == "unsupported"
    assert snapshot.metadata["domain_conclusions"] == {"career": "证据不足"}



def test_registry_input_order_does_not_change_snapshot() -> None:
    registrations = [
        SliceRegistration(school=school, domain=domain, status="abstain")
        for school in V5_SCHOOLS
        for domain in DOMAIN_IDS
    ]
    forward = run_domain_analysis(_request(), registry=DomainSliceRegistry(registrations))
    reverse = run_domain_analysis(_request(), registry=DomainSliceRegistry(reversed(registrations)))

    assert forward.run_id == reverse.run_id
    assert forward.output_hash == reverse.output_hash
    assert forward.metadata == reverse.metadata



def test_high_risk_gate_runs_before_graph_and_arbitration_and_records_snapshot_audit() -> None:
    def high_risk_claim(school: str, claim_id: str) -> SliceResult:
        claim = V5Claim(
            claim_id=claim_id,
            school=school,  # type: ignore[arg-type]
            domain="财富",
            claim="存在债务风险。",
            claim_type="event_claim",
            stance="support",
            confidence=V5Confidence(tier="★★★★", score=0.72),
            evidence=[
                V5Evidence(
                    evidence_id=f"ev-{claim_id}",
                    source=school,
                    text="债务事件证据。",
                    node_refs=["chart:root"],
                    rule_ids=[f"RULE-{school}"],
                )
            ],
            falsifiable="若现实核验不存在债务，则本命题失验。",
            metadata={"task_id": "wealth.debt", "high_risk": True},
        )
        return SliceResult(school=school, domain="wealth", status="implemented", claims=(claim,))  # type: ignore[arg-type]

    registrations = [
        SliceRegistration(
            school=school,
            domain=domain,
            status="implemented" if domain == "wealth" and school in {"gao_dechen", "duan_jianye"} else "abstain",
            generator=(lambda context, school=school: high_risk_claim(school, f"cl-{school}"))
            if domain == "wealth" and school in {"gao_dechen", "duan_jianye"}
            else None,
        )
        for school in V5_SCHOOLS
        for domain in DOMAIN_IDS
    ]

    snapshot = run_domain_analysis(_request(("wealth",)), registry=DomainSliceRegistry(registrations))

    gated = [claim for claim in snapshot.claims if claim.metadata.get("task_id") == "wealth.debt"]
    assert {claim.metadata["high_risk_gate"]["status"] for claim in gated} == {"passed"}
    assert snapshot.metadata["high_risk_gate"]["status_counts"] == {"passed": 2}
    assert all(claim.confidence.score == 0.72 for claim in gated)
    assert all(
        node.get("label") != "高风险命题证据未通过独立安全门禁，暂不形成肯定判断。"
        for node in snapshot.structure_graph.nodes
    )
    event_result = next(
        item for item in snapshot.arbitration_results
        if item.domain == "财富" and item.stage == "event_realization"
    )
    assert event_result.support_score == 2.0


def test_failed_high_risk_claim_is_abstain_before_arbitration_not_opposition() -> None:
    def implemented(context):
        claim = V5Claim(
            claim_id="cl-single-debt",
            school="duan_jianye",
            domain="财富",
            claim="存在债务风险。",
            claim_type="event_claim",
            stance="support",
            confidence=V5Confidence(tier="★★★★", score=0.72),
            evidence=[V5Evidence("ev-debt", "duan_jianye", "单源债务证据。", ["chart:root"], ["RULE-DUAN"])],
            falsifiable="若现实核验不存在债务，则本命题失验。",
            metadata={"task_id": "wealth.debt", "high_risk": True},
        )
        return SliceResult(school="duan_jianye", domain="wealth", status="implemented", claims=(claim,))

    registration = SliceRegistration(school="duan_jianye", domain="wealth", status="implemented", generator=implemented)
    snapshot = run_domain_analysis(_request(("wealth",)), registry=_registry_with_career_registration(registration))
    claim = next(item for item in snapshot.claims if item.claim_id == "cl-single-debt")
    event_result = next(
        item for item in snapshot.arbitration_results
        if item.domain == "财富" and item.stage == "event_realization"
    )

    assert claim.stance == "abstain"
    assert claim.metadata["high_risk_gate"]["status"] == "failed"
    assert event_result.support_score == 0.0
    assert event_result.opposition_score == 0.0


def test_implemented_slice_claim_keeps_evidence_and_non_abstain_conclusion() -> None:
    def implemented(context):
        evidence = V5Evidence(
            evidence_id="ev-career",
            source="test-rule",
            text="事业规则命中。",
            node_refs=["chart:root"],
        )
        claim = V5Claim(
            claim_id="cl-career",
            school="ziping",
            domain="事业",
            claim="事业结构命中。",
            claim_type="structure_claim",
            stance="support",
            confidence=V5Confidence(tier="★★★", score=0.6),
            evidence=[evidence],
            falsifiable="反馈不符则证伪。",
        )
        return SliceResult(
            school="ziping",
            domain="career",
            status="implemented",
            claims=(claim,),
            audit=SliceAudit(reason="rule matched"),
        )

    registration = SliceRegistration(school="ziping", domain="career", status="implemented", generator=implemented)
    snapshot = run_domain_analysis(_request(("career",)), registry=_registry_with_career_registration(registration))

    assert any(claim.claim_id == "cl-career" and claim.evidence for claim in snapshot.claims)
    assert "career" not in snapshot.metadata["domain_conclusions"]

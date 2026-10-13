"""事业域六源切片的适配、能力边界与注册行为测试。"""

from __future__ import annotations

from datetime import date, datetime

from engine.claims import Claim, Evidence, TimeWindow
from engine.v5.domain import V5_SCHOOLS
from engine.v5.domain_slices.career import (
    adapt_legacy_claim,
    build_career_registry,
    context_to_chart_ledger,
    ren_fuhong_career_slice,
    run_legacy_career_slice,
)
from engine.v5.domain_slices.contract import (
    DomainAnalysisContext,
    DomainAnalysisRequest,
)
from engine.v5.domain_slices.orchestrator import run_domain_analysis
from engine.v5.domain_slices.registry import DomainSliceRegistry, SliceRegistration


def _context() -> DomainAnalysisContext:
    request = DomainAnalysisRequest(
        gender="乾",
        birth_datetime=datetime(1990, 1, 1, 12, 0),
        as_of_date=date(2024, 1, 1),
        domains=("career",),
        output_dir="reports/domain-analysis",
    )
    return DomainAnalysisContext(
        request=request,
        case_id="DA-CAREER-TEST",
        pillars=("癸未", "甲寅", "壬戌", "丙午"),
        dayun=(
            {"ganzhi": "丙辰", "start_year": 2018},
            {"ganzhi": "丁巳", "start_year": 2028},
        ),
        current_dayun={"ganzhi": "丙辰", "start_year": 2018, "end_year": 2027},
        future_years=((2024, "甲辰"), (2025, "乙巳"), (2026, "丙午")),
        calculator="test-calculator",
    )


def _legacy_claim(*, school_id: str = "ren") -> Claim:
    return Claim(
        claim_id="claim-private-short-school-id",
        school_id=school_id,
        task_id="career.change_window",
        claim_type="timing_claim",
        stance="support",
        statement="2024 年出现事业变化窗口。",
        evidence=(
            Evidence(
                evidence_id="evidence-private-short-school-id",
                fact_refs=("liunian_steps.0", "four_pillars.day"),
                feature_refs=("branch_conflict_intensity",),
                rule_id="REN-SUIYUN-RELATION-V1",
                text="甲辰流年引动日支。",
            ),
        ),
        falsifier="若 2024 年没有可核验事业变化则证伪。",
        time_window=TimeWindow(2024, 2024, "annual"),
        confidence_basis="按岁运关系确定时间窗。",
        applicability_snapshot={"year": 2024},
        domain="事业",
        confidence=0.7,
    )


def test_context_adapter_preserves_chart_current_dayun_and_three_future_years() -> None:
    ledger = context_to_chart_ledger(_context())

    assert ledger.sex_marker == "乾"
    assert ledger.solar_datetime == "1990-01-01 12:00:00"
    assert ledger.four_pillars == {
        "year": "癸未",
        "month": "甲寅",
        "day": "壬戌",
        "hour": "丙午",
    }
    assert ledger.dayun_steps[0] == {
        "ganzhi": "丙辰",
        "start_year": 2018,
        "end_year": 2027,
    }
    assert ledger.liunian_steps == [
        {"year": 2024, "ganzhi": "甲辰", "dayun": "丙辰"},
        {"year": 2025, "ganzhi": "乙巳", "dayun": "丙辰"},
        {"year": 2026, "ganzhi": "丙午", "dayun": "丙辰"},
    ]


def test_legacy_claim_adapter_uses_public_school_id_and_preserves_audit_evidence() -> None:
    claim = adapt_legacy_claim(_legacy_claim(), public_school="ren_fuhong")

    assert claim.school == "ren_fuhong"
    assert claim.domain == "事业"
    assert claim.claim_type == "timing_claim"
    assert claim.confidence.score == 0.7
    assert claim.confidence.tier == "★★★★"
    assert claim.timing_hints == [
        {"start_year": 2024, "end_year": 2024, "label": "annual"}
    ]
    assert claim.evidence[0].rule_ids == ["REN-SUIYUN-RELATION-V1"]
    assert claim.evidence[0].node_refs == [
        "liunian_steps.0",
        "four_pillars.day",
        "feature:branch_conflict_intensity",
    ]
    serialized = str(claim.to_dict())
    assert "claim-private-short-school-id" not in serialized
    assert "evidence-private-short-school-id" not in serialized
    assert "'school': 'ren'" not in serialized


def test_empty_legacy_output_becomes_explicit_abstain() -> None:
    result = run_legacy_career_slice(
        _context(),
        public_school="ziping",
        tasks=("career.role_change",),
        generator=lambda chart, features, task: [],
    )

    assert result.status == "abstain"
    assert result.claims == ()
    assert result.audit.reason == "career rules did not match"


def test_career_registry_implements_auditable_sources_and_does_not_fabricate_yang_claims() -> None:
    registry = build_career_registry()

    assert len(registry) == 18
    for school in ("ziping", "ditiansui", "gao_dechen", "duan_jianye", "ren_fuhong"):
        registration = registry.resolve(school, "career")
        assert registration.status == "implemented"
        assert registration.generator is not None
    assert registry.resolve("yang_qingjuan", "career").status == "unsupported"
    assert all(
        registry.resolve(school, domain).status == "abstain"
        for school in ("ziping", "ditiansui", "gao_dechen", "duan_jianye", "yang_qingjuan", "ren_fuhong")
        for domain in ("wealth", "marriage")
    )


def test_ren_fuhong_career_slice_outputs_timing_only_without_short_school_id() -> None:
    result = ren_fuhong_career_slice(_context())

    assert result.status == "implemented"
    assert result.claims
    assert {claim.claim_type for claim in result.claims} == {"timing_claim"}
    assert {claim.school for claim in result.claims} == {"ren_fuhong"}
    assert all(claim.timing_hints for claim in result.claims)
    assert "'school': 'ren'" not in str(result.to_dict())


def test_default_orchestrator_uses_career_registry_without_opt_in() -> None:
    snapshot = run_domain_analysis(_context().request)

    coverage = {
        (item["school"], item["domain"]): item["status"]
        for item in snapshot.metadata["slice_coverage"]
    }
    assert coverage[("ren_fuhong", "career")] == "implemented"
    assert coverage[("yang_qingjuan", "career")] == "unsupported"
    assert any(
        claim.school == "ren_fuhong"
        and claim.claim_type == "timing_claim"
        and claim.stance == "support"
        for claim in snapshot.claims
    )
    assert "career" not in snapshot.metadata["domain_conclusions"]
    serialized = str(snapshot.to_dict())
    assert "'school': 'gao'" not in serialized
    assert "'school': 'duan'" not in serialized
    assert "'school': 'ren'" not in serialized


def test_ren_timing_claim_does_not_change_structure_arbitration_confidence() -> None:
    full_registry = build_career_registry()
    without_ren = DomainSliceRegistry(
        SliceRegistration(school=school, domain=domain, status="abstain")
        if (school, domain) == ("ren_fuhong", "career")
        else full_registry.resolve(school, domain)
        for school in V5_SCHOOLS
        for domain in ("career", "wealth", "marriage")
    )

    with_timing = run_domain_analysis(_context().request, registry=full_registry)
    without_timing = run_domain_analysis(_context().request, registry=without_ren)
    with_structure = next(
        result
        for result in with_timing.arbitration_results
        if result.domain == "事业" and result.stage == "structure_legality"
    )
    without_structure = next(
        result
        for result in without_timing.arbitration_results
        if result.domain == "事业" and result.stage == "structure_legality"
    )

    assert with_structure.confidence == without_structure.confidence
    assert with_structure.conclusion == without_structure.conclusion

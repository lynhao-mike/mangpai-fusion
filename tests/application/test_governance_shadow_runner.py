from __future__ import annotations

import ast
from dataclasses import replace
from pathlib import Path

from engine.decision.models import ChartFactLedger, RawWenzhenPayload, SchoolClaim
from engine.governance import (
    ClaimEvidenceGrade,
    ClaimKind,
    ClaimReferenceCategory,
    DigestRef,
    FactConflictContext,
    GovernanceReferenceCatalog,
    ReferenceRegistration,
    TemporalLayer,
    TriggerEvaluationContext,
    TriggerRegistrationSpec,
    build_trigger_registry,
)
from engine.governance.registries import (
    CapabilityIdentity,
    CapabilityRegistration,
    CapabilityRole,
    FactCertificationRegistry,
    LegacyCompatibilitySource,
    PeerSchool,
    PublicationStatus,
    SchoolRegistry,
    TriggerEvaluatorId,
    TriggerPublicationStatus,
)

from engine.application.governance_shadow_runner import (
    GovernanceShadowDependencies,
    GovernanceShadowRequest,
    SchoolViewFailure,
    SchoolViewOutcome,
    TriggerRequest,
    run_governance_shadow,
)


def _raw() -> RawWenzhenPayload:
    return RawWenzhenPayload(raw_text="fixture", raw_hash="raw-shadow-001")


def _chart() -> ChartFactLedger:
    return ChartFactLedger(
        sex_marker="qian",
        four_pillars={"year": "jiazi", "month": "yichou", "day": "bingyin"},
        dayun_steps=[{"ganzhi": "wuchen", "start_year": 2018, "end_year": 2027}],
        liunian_steps=[{"year": 2026, "ganzhi": "bingwu"}],
        raw_source_hash="raw-shadow-001",
    )


def _catalog() -> GovernanceReferenceCatalog:
    return GovernanceReferenceCatalog(
        (
            ReferenceRegistration(
                ClaimReferenceCategory.SCHOOL_REASON, "reason:ziping", "legacy-v1"
            ),
            ReferenceRegistration(
                ClaimReferenceCategory.SCHOOL_REASON, "reason:gao", "legacy-v1"
            ),
            ReferenceRegistration(
                ClaimReferenceCategory.SOURCE_RULE, "rule:structure", "legacy-v1"
            ),
        )
    )


def _school_registry() -> SchoolRegistry:
    capabilities = tuple(
        CapabilityRegistration(
            CapabilityIdentity(
                school_id,
                "structure.assessment",
                ClaimKind.STRUCTURE,
                ClaimEvidenceGrade.INFERENTIAL,
                "governance/v1",
            ),
            CapabilityRole.LEAD,
            PublicationStatus.PUBLISHED,
        )
        for school_id in ("ziping", "gao_dechen")
    )
    return SchoolRegistry(
        tuple(
            PeerSchool(school_id)
            for school_id in (
                "ziping",
                "gao_dechen",
                "duan_jianye",
                "yang_qingjuan",
                "ren_fuhong",
            )
        ),
        (LegacyCompatibilitySource("ditiansui"),),
        capabilities,
    )


def _dependencies() -> GovernanceShadowDependencies:
    return GovernanceShadowDependencies(
        reference_catalog=_catalog(),
        school_registry=_school_registry(),
        certification_registry=FactCertificationRegistry(()),
        capability_version="governance/v1",
    )


def _legacy_claim(school: str, reason: str) -> SchoolClaim:
    return SchoolClaim(
        claim_id=f"legacy-{school}",
        school=school,
        role_granted_by_l1="lead",
        domain="structure",
        claim_type="structure_claim",
        statement=f"{school} structure view",
        evidence_refs=[reason, "rule:structure"],
        confidence=0.64,
        falsifier="",
        metadata={
            "task_id": "structure.assessment",
            "stance": "support",
            "temporal_scope": "natal",
            "reference_version": "legacy-v1",
        },
    )


def _request(
    *outcomes: SchoolViewOutcome | SchoolViewFailure,
    target_year: int | None = 2026,
) -> GovernanceShadowRequest:
    return GovernanceShadowRequest(
        case_id="C-SHADOW-001",
        raw_payload=_raw(),
        chart=_chart(),
        target_year=target_year,
        calculator_version="governance-fact-builder-v1",
        school_views=outcomes,
    )


def test_shadow_runner_preserves_available_schools_when_one_school_fails() -> None:
    # Given: one valid School View and one explicit unavailable School View.
    request = _request(
        SchoolViewOutcome("ziping", (_legacy_claim("ziping", "reason:ziping"),)),
        SchoolViewFailure("ren_fuhong", "SCHOOL_VIEW.RUNTIME", "ren view failed"),
    )

    # When: the shadow runner orchestrates fact build, adaptation, and arbitration.
    result = run_governance_shadow(request, _dependencies())

    # Then: the failed school is marked unavailable and the other claim survives.
    assert result.status == "ok"
    assert result.unavailable_schools[0].school_id == "ren_fuhong"
    assert result.arbitration is not None
    assert result.arbitration.decision == "consensus"
    assert result.arbitration.retained_claim_ids == (result.claims[0].claim_id,)
    assert tuple(record.gate for record in result.arbitration.gate_trace) == (
        "eligibility",
        "temporal",
        "evidence",
        "independence",
        "counterevidence",
        "applicability",
        "decision",
    )


def test_fact_conflict_stops_before_arena_with_typed_fail_closed_result() -> None:
    # Given: an explicit immutable fact conflict from an upstream snapshot check.
    conflict = FactConflictContext(
        "fact:shared",
        DigestRef.from_material(("first",)).value,
        DigestRef.from_material(("second",)).value,
    )
    request = replace(
        _request(
            SchoolViewOutcome("ziping", (_legacy_claim("ziping", "reason:ziping"),))
        ),
        fact_conflicts=(conflict,),
    )

    # When: the runner receives the conflict.
    result = run_governance_shadow(request, _dependencies())

    # Then: arbitration is not allowed to proceed.
    assert result.status == "fail_closed"
    assert result.arbitration is None
    assert result.issues[0].issue_code == "ARBITRATION.FACT_CONFLICT"


def test_same_inputs_and_versions_produce_the_same_shadow_digest() -> None:
    # Given: two equivalent requests with different School View ordering.
    first = _request(
        SchoolViewOutcome("ziping", (_legacy_claim("ziping", "reason:ziping"),)),
        SchoolViewOutcome("gao_dechen", (_legacy_claim("gao", "reason:gao"),)),
    )
    second = _request(*reversed(first.school_views))

    # When: both are evaluated through the same dependency snapshot.
    first_result = run_governance_shadow(first, _dependencies())
    second_result = run_governance_shadow(second, _dependencies())

    # Then: canonical ordering keeps the public digest deterministic.
    assert first_result.result_digest == second_result.result_digest
    assert first_result.to_canonical() == second_result.to_canonical()


def test_no_target_year_omits_liunian_and_keeps_liunian_trigger_inactive() -> None:
    # Given: an explicit liunian trigger request but no explicit target year.
    dependencies = replace(
        _dependencies(),
        trigger_registry=build_trigger_registry(
            (
                TriggerRegistrationSpec(
                    "timing.liunian",
                    TriggerEvaluatorId.LIUNIAN_TARGET_YEAR_PRESENT.value,
                    "1.0.0",
                    ("chart.liunian",),
                    (TemporalLayer.LIUNIAN.value,),
                    "inactive_with_issue",
                    TriggerPublicationStatus.PUBLISHED.value,
                ),
            )
        ),
        trigger_requests=(
            TriggerRequest("timing.liunian", TriggerEvaluationContext()),
        ),
    )

    # When: the runner executes without target_year.
    result = run_governance_shadow(
        _request(
            SchoolViewOutcome("ziping", (_legacy_claim("ziping", "reason:ziping"),)),
            target_year=None,
        ),
        dependencies,
    )

    # Then: no liunian fact appears and timing activation remains inactive.
    assert "chart.liunian" not in result.fact_kinds
    assert result.trigger_results[0].active is False
    assert result.trigger_results[0].issues == ("missing_required_fact",)


def test_ditiansui_legacy_claim_is_excluded_from_five_school_arena() -> None:
    # Given: one peer claim and one legacy Ditiansui compatibility claim.
    request = _request(
        SchoolViewOutcome("ziping", (_legacy_claim("ziping", "reason:ziping"),)),
        SchoolViewOutcome("ditiansui", (_legacy_claim("ditiansui", "reason:ziping"),)),
    )

    # When: the shadow arena is built.
    result = run_governance_shadow(request, _dependencies())

    # Then: Ditiansui is audited as excluded and never enters arbitration.
    assert result.status == "ok"
    assert result.excluded_claim_refs == ("legacy-ditiansui",)
    assert result.arbitration is not None
    assert result.arbitration.retained_claim_ids == (result.claims[0].claim_id,)


def test_shadow_runner_static_imports_stay_isolated_from_production_surfaces() -> None:
    # Given: the runner source.
    module_path = Path("engine/application/governance_shadow_runner.py")
    tree = ast.parse(module_path.read_text(encoding="utf-8"))

    # When: direct imports are inspected.
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            modules.add(node.module)

    # Then: shadow code does not bind production/report/feedback/learning surfaces.
    banned = (
        "engine.pipeline",
        "engine.v5.runner",
        "engine.application.pipeline_runner",
        "tools.render_report",
        "tools.feedback_ingest",
        "tools.feedback_loop",
        "tools.conditional_learning",
    )
    assert all(module not in modules for module in banned)

from __future__ import annotations

import ast
import dataclasses
import json
import subprocess
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any, Callable

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from engine.application.governance_shadow_runner import (
    CompositionRequest,
    GovernanceShadowDependencies,
    GovernanceShadowRequest,
    SchoolViewFailure,
    SchoolViewOutcome,
    TriggerRequest,
    run_governance_shadow,
)
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
from engine.governance.composition_templates import CompositionRegistry
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


def raw() -> RawWenzhenPayload:
    return RawWenzhenPayload(raw_text="qa fixture", raw_hash="raw-shadow-qa-001")


def chart() -> ChartFactLedger:
    return ChartFactLedger(
        sex_marker="qian",
        four_pillars={"year": "jiazi", "month": "yichou", "day": "bingyin", "hour": "dingmao"},
        dayun_steps=[{"ganzhi": "wuchen", "start_year": 2018, "end_year": 2027}],
        liunian_steps=[{"year": 2026, "ganzhi": "bingwu"}],
        raw_source_hash="raw-shadow-qa-001",
    )


def catalog() -> GovernanceReferenceCatalog:
    return GovernanceReferenceCatalog(
        (
            ReferenceRegistration(ClaimReferenceCategory.SCHOOL_REASON, "reason:ziping", "legacy-v1"),
            ReferenceRegistration(ClaimReferenceCategory.SCHOOL_REASON, "reason:gao", "legacy-v1"),
            ReferenceRegistration(ClaimReferenceCategory.SCHOOL_REASON, "reason:duan", "legacy-v1"),
            ReferenceRegistration(ClaimReferenceCategory.SOURCE_RULE, "rule:structure", "legacy-v1"),
        )
    )


def school_registry() -> SchoolRegistry:
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
        for school_id in ("ziping", "gao_dechen", "duan_jianye")
    )
    return SchoolRegistry(
        tuple(
            PeerSchool(school_id)
            for school_id in ("ziping", "gao_dechen", "duan_jianye", "yang_qingjuan", "ren_fuhong")
        ),
        (LegacyCompatibilitySource("ditiansui"),),
        capabilities,
    )


def dependencies(**overrides: Any) -> GovernanceShadowDependencies:
    base = GovernanceShadowDependencies(
        reference_catalog=catalog(),
        school_registry=school_registry(),
        certification_registry=FactCertificationRegistry(()),
        capability_version="governance/v1",
    )
    return replace(base, **overrides)


def legacy_claim(school: str, reason: str = "reason:ziping") -> SchoolClaim:
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


def request(*views: SchoolViewOutcome | SchoolViewFailure, target_year: int | None = 2026) -> GovernanceShadowRequest:
    return GovernanceShadowRequest(
        case_id="C-SHADOW-QA-001",
        raw_payload=raw(),
        chart=chart(),
        target_year=target_year,
        calculator_version="governance-fact-builder-v1",
        school_views=views,
    )


def canonical_json(value: Any) -> Any:
    if dataclasses.is_dataclass(value):
        return {field.name: canonical_json(getattr(value, field.name)) for field in dataclasses.fields(value)}
    if isinstance(value, tuple):
        return [canonical_json(item) for item in value]
    return value


def ok(name: str, actual: dict[str, Any]) -> None:
    print(json.dumps({"scenario": name, "verdict": "PASS", "actual": actual}, sort_keys=True))


def success_full_trace() -> None:
    result = run_governance_shadow(
        request(
            SchoolViewOutcome("ziping", (legacy_claim("ziping", "reason:ziping"),)),
            SchoolViewOutcome("gao_dechen", (legacy_claim("gao", "reason:gao"),)),
        ),
        dependencies(),
    )
    gates = tuple(record.gate for record in result.arbitration.gate_trace) if result.arbitration else ()
    expected = ("eligibility", "temporal", "evidence", "independence", "counterevidence", "applicability", "decision")
    assert result.status == "ok"
    assert result.arbitration is not None
    assert gates == expected
    assert result.arbitration.decision == "consensus"
    ok("success_full_trace", {"status": result.status, "decision": result.arbitration.decision, "gates": gates, "digest": result.result_digest})


def one_school_failure() -> None:
    result = run_governance_shadow(
        request(
            SchoolViewOutcome("ziping", (legacy_claim("ziping", "reason:ziping"),)),
            SchoolViewFailure("ren_fuhong", "SCHOOL_VIEW.RUNTIME", "ren view failed"),
        ),
        dependencies(),
    )
    assert result.status == "ok"
    assert result.unavailable_schools[0].school_id == "ren_fuhong"
    assert result.claims[0].school_id == "ziping"
    ok("one_school_failure", {"status": result.status, "unavailable": canonical_json(result.unavailable_schools), "claim_schools": [item.school_id for item in result.claims]})


def fact_conflict() -> None:
    conflict = FactConflictContext("fact:shared", DigestRef.from_material(("first",)).value, DigestRef.from_material(("second",)).value)
    result = run_governance_shadow(
        replace(request(SchoolViewOutcome("ziping", (legacy_claim("ziping", "reason:ziping"),))), fact_conflicts=(conflict,)),
        dependencies(),
    )
    assert result.status == "fail_closed"
    assert result.arbitration is None
    assert result.issues[0].issue_code == "ARBITRATION.FACT_CONFLICT"
    ok("fact_conflict", {"status": result.status, "arbitration": result.arbitration, "issues": canonical_json(result.issues)})


def deterministic_ordering() -> None:
    first = request(
        SchoolViewOutcome("ziping", (legacy_claim("ziping", "reason:ziping"),)),
        SchoolViewOutcome("gao_dechen", (legacy_claim("gao", "reason:gao"),)),
    )
    second = request(*reversed(first.school_views))
    left = run_governance_shadow(first, dependencies())
    right = run_governance_shadow(second, dependencies())
    assert left.result_digest == right.result_digest
    assert left.to_canonical() == right.to_canonical()
    ok("deterministic_ordering", {"left_digest": left.result_digest, "right_digest": right.result_digest, "canonical_equal": True})


def no_target_year() -> None:
    trigger_registry = build_trigger_registry(
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
    )
    deps = dependencies(
        trigger_registry=trigger_registry,
        trigger_requests=(TriggerRequest("timing.liunian", TriggerEvaluationContext(as_of_date="2026-08-04", parsed_present=True)),),
    )
    result = run_governance_shadow(request(SchoolViewOutcome("ziping", (legacy_claim("ziping", "reason:ziping"),)), target_year=None), deps)
    assert "chart.liunian" not in result.fact_kinds
    assert result.trigger_results[0].active is False
    assert result.trigger_results[0].issues == ("missing_required_fact",)
    ok("no_target_year", {"fact_kinds": result.fact_kinds, "trigger_results": canonical_json(result.trigger_results)})


def ditiansui_excluded() -> None:
    result = run_governance_shadow(
        request(
            SchoolViewOutcome("ziping", (legacy_claim("ziping", "reason:ziping"),)),
            SchoolViewOutcome("ditiansui", (legacy_claim("ditiansui", "reason:ziping"),)),
        ),
        dependencies(),
    )
    assert result.status == "ok"
    assert result.excluded_claim_refs == ("legacy-ditiansui",)
    assert all(claim.school_id != "ditiansui" for claim in result.claims)
    ok("ditiansui_excluded", {"excluded_claim_refs": result.excluded_claim_refs, "claim_schools": [item.school_id for item in result.claims]})


def no_mutation() -> None:
    req = request(SchoolViewOutcome("ziping", (legacy_claim("ziping", "reason:ziping"),)))
    deps = dependencies()
    before = (req, deps, req.school_views, deps.school_registry.capabilities)
    result = run_governance_shadow(req, deps)
    after = (req, deps, req.school_views, deps.school_registry.capabilities)
    assert before == after
    assert result.status == "ok"
    ok("no_mutation", {"request_equal": before[0] == after[0], "dependencies_equal": before[1] == after[1], "capability_count": len(deps.school_registry.capabilities)})


def serializable_canonical() -> None:
    result = run_governance_shadow(request(SchoolViewOutcome("ziping", (legacy_claim("ziping", "reason:ziping"),))), dependencies())
    payload = canonical_json(result)
    text = json.dumps(payload, ensure_ascii=True, sort_keys=True)
    restored = json.loads(text)
    assert restored["result_digest"] == result.result_digest
    assert result.to_canonical()
    ok("serializable_canonical", {"json_bytes": len(text), "digest": restored["result_digest"], "status": restored["status"]})


def banned_imports() -> None:
    tree = ast.parse(Path("engine/application/governance_shadow_runner.py").read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            modules.add(node.module)
    banned = (
        "engine.pipeline",
        "engine.v5.runner",
        "engine.application.pipeline_runner",
        "tools.render_report",
        "tools.feedback_ingest",
        "tools.feedback_loop",
        "tools.conditional_learning",
        "engine.application.production_rule_triggers",
    )
    present = sorted(module for module in banned if module in modules)
    assert present == []
    ok("banned_imports", {"checked_modules": len(modules), "banned_present": present})


def unknown_school() -> None:
    result = run_governance_shadow(request(SchoolViewOutcome("unknown_school", (legacy_claim("unknown_school", "reason:ziping"),))), dependencies())
    assert result.status == "ok"
    assert result.arbitration is not None
    assert result.arbitration.decision == "abstain"
    assert result.claims == ()
    assert result.arbitration.retained_claim_ids == ()
    assert any(issue.issue_code == "UNSUPPORTED_LEGACY_CLAIM" for issue in result.issues)
    ok("unknown_school", {"status": result.status, "decision": result.arbitration.decision, "issues": canonical_json(result.issues)})


def unknown_capability() -> None:
    result = run_governance_shadow(request(SchoolViewOutcome("yang_qingjuan", (legacy_claim("yang", "reason:ziping"),))), dependencies())
    assert result.status == "ok"
    assert result.arbitration is not None
    assert result.arbitration.decision == "abstain"
    applicability_gate = next(record for record in result.arbitration.gate_trace if record.gate == "applicability")
    assert applicability_gate.rejected_claim_ids == tuple(claim.claim_id for claim in result.claims)
    assert result.arbitration.retained_claim_ids == ()
    ok("unknown_capability", {"decision": result.arbitration.decision, "applicability_gate": canonical_json(applicability_gate), "claim_count": len(result.claims)})


def unknown_trigger() -> None:
    trigger_registry = build_trigger_registry(
        (
            TriggerRegistrationSpec(
                "known.structure",
                TriggerEvaluatorId.FACT_KIND_PRESENT.value,
                "1.0.0",
                ("chart.sex_marker",),
                (TemporalLayer.NATAL.value,),
                "inactive_with_issue",
                TriggerPublicationStatus.PUBLISHED.value,
            ),
        )
    )
    result = run_governance_shadow(
        request(SchoolViewOutcome("ziping", (legacy_claim("ziping", "reason:ziping"),))),
        dependencies(trigger_registry=trigger_registry, trigger_requests=(TriggerRequest("unknown.trigger", TriggerEvaluationContext()),)),
    )
    assert result.trigger_results[0].active is False
    assert result.trigger_results[0].issues == ("unknown_trigger",)
    ok("unknown_trigger", {"trigger_results": canonical_json(result.trigger_results)})


def unsupported_composition() -> None:
    result = run_governance_shadow(
        request(SchoolViewOutcome("ziping", (legacy_claim("ziping", "reason:ziping"),))),
        dependencies(
            composition_registry=CompositionRegistry(()),
            composition_requests=(CompositionRequest("unknown.template", "1.0.0", ("governance:legacy-ziping",)),),
        ),
    )
    assert result.composition_results[0].outcome == "unsupported"
    assert result.composition_results[0].issue_code == "COMPOSITION.UNSUPPORTED_TEMPLATE"
    ok("unsupported_composition", {"composition_results": canonical_json(result.composition_results)})


def malformed_input() -> None:
    bad_chart = ChartFactLedger(
        sex_marker="qian",
        four_pillars={"year": "jiazi"},
        raw_source_hash="different-raw-hash",
    )
    result = run_governance_shadow(
        GovernanceShadowRequest(
            case_id="C-SHADOW-QA-BAD",
            raw_payload=raw(),
            chart=bad_chart,
            target_year=2026,
            calculator_version="governance-fact-builder-v1",
            school_views=(),
        ),
        dependencies(),
    )
    assert result.status == "fail_closed"
    assert result.issues
    ok("malformed_input", {"status": result.status, "issues": canonical_json(result.issues)})


def legacy_surfaces() -> None:
    from engine.decision import decision_run_from_v5, run_decision_mvp
    from engine.v5 import run_v5

    raw_text = """
$BASE
Qian
$FOUR
Y:jiazi
M:yichou
D:bingyin
H:dingmao
$DY_LOOP
# 2018-2027 wuchen
""".strip()
    run = run_decision_mvp(raw_text)
    v5_output = run_v5({"case_id": "C-SHADOW-QA-V5", "pillars": ["jiazi", "yichou", "bingyin", "dingmao"]})
    adapted = decision_run_from_v5(v5_output)
    assert run.validate_trace() == []
    assert adapted.validate_trace() == []
    ok("legacy_surfaces", {"run_decision_mvp_case_id": run.case_id, "v5_adapter_case_id": adapted.case_id, "mvp_errors": run.validate_trace(), "v5_errors": adapted.validate_trace()})


def stale_state_two_processes() -> None:
    cmd = [sys.executable, str(Path(__file__).resolve()), "deterministic_ordering"]
    first = subprocess.run(cmd, check=False, capture_output=True, text=True, timeout=30)
    second = subprocess.run(cmd, check=False, capture_output=True, text=True, timeout=30)
    assert first.returncode == 0
    assert second.returncode == 0
    left = json.loads(first.stdout)["actual"]["left_digest"]
    right = json.loads(second.stdout)["actual"]["left_digest"]
    assert left == right
    ok("stale_state_two_processes", {"first_exit": first.returncode, "second_exit": second.returncode, "first_digest": left, "second_digest": right})


SCENARIOS: dict[str, Callable[[], None]] = {
    "success_full_trace": success_full_trace,
    "one_school_failure": one_school_failure,
    "fact_conflict": fact_conflict,
    "deterministic_ordering": deterministic_ordering,
    "no_target_year": no_target_year,
    "ditiansui_excluded": ditiansui_excluded,
    "no_mutation": no_mutation,
    "serializable_canonical": serializable_canonical,
    "banned_imports": banned_imports,
    "unknown_school": unknown_school,
    "unknown_capability": unknown_capability,
    "unknown_trigger": unknown_trigger,
    "unsupported_composition": unsupported_composition,
    "malformed_input": malformed_input,
    "legacy_surfaces": legacy_surfaces,
    "stale_state_two_processes": stale_state_two_processes,
}


def main() -> None:
    if len(sys.argv) != 2 or sys.argv[1] not in SCENARIOS:
        print(json.dumps({"available": sorted(SCENARIOS)}))
        raise SystemExit(2)
    SCENARIOS[sys.argv[1]]()


if __name__ == "__main__":
    main()

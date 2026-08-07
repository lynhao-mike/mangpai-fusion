from __future__ import annotations

import ast
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_product_version_sources_are_synchronized() -> None:
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    assert re.fullmatch(r"\d+\.\d+\.\d+(?:[-.][A-Za-z0-9]+)?", version), version

    init_source = (ROOT / "engine" / "__init__.py").read_text(encoding="utf-8")
    module = ast.parse(init_source)
    init_version = None
    for node in module.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "__version__":
                    assert isinstance(node.value, ast.Constant)
                    init_version = node.value.value
    assert init_version == version

    project_state = json.loads((ROOT / "META" / "project-state.json").read_text(encoding="utf-8"))
    assert project_state["product_version_source"] == "VERSION"
    assert project_state["product_version"] == version


def test_ai_entrypoints_exist_and_are_wired() -> None:
    required_paths = [
        "AGENTS.md",
        "README.md",
        "STATUS.md",
        "META/project-state.json",
        "tools/README.md",
        "tools/tool_registry.py",
        "tools/rule_status_scan.py",
    ]
    for rel in required_paths:
        assert (ROOT / rel).exists(), rel

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    state = json.loads((ROOT / "META" / "project-state.json").read_text(encoding="utf-8"))

    assert "AGENTS.md" in readme
    assert "META/project-state.json" in agents
    assert state["ai_entrypoint"] == "AGENTS.md"
    assert state["tool_index"] == "tools/README.md"


def test_deprecated_and_missing_tools_are_not_primary_entrypoints() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    status = (ROOT / "STATUS.md").read_text(encoding="utf-8")
    meta_index = (ROOT / "META" / "INDEX.md").read_text(encoding="utf-8")
    tools_readme = (ROOT / "tools" / "README.md").read_text(encoding="utf-8")

    combined_primary_docs = "\n".join([readme, status])
    assert "tools/calibrate.py" not in combined_primary_docs
    assert "seal_prediction.py" not in combined_primary_docs
    assert "verify_evidence.py" not in combined_primary_docs
    assert "已 deprecated，不应用于新反馈" in meta_index

    assert "deprecated" in tools_readme
    assert "calibrate.py" in tools_readme
    assert "missing" in tools_readme
    assert "seal_prediction.py" in tools_readme
    assert "verify_evidence.py" in tools_readme


def test_tool_registry_supports_internal_status() -> None:
    source = (ROOT / "tools" / "tool_registry.py").read_text(encoding="utf-8")
    assert '"internal"' in source

    tools_readme = (ROOT / "tools" / "README.md").read_text(encoding="utf-8")
    assert "## internal" in tools_readme
    assert "feedback_loop.py" in tools_readme
    assert "rule_lifecycle.py" in tools_readme


def test_tool_registry_only_uses_first_readme_table_cell_for_status() -> None:
    from tools.tool_registry import build_registry

    entries = {entry.name: entry for entry in build_registry()}

    assert entries["feedback_ingest.py"].status == "active"
    assert entries["feedback_loop.py"].status == "internal"
    assert entries["output_linter.py"].status == "active"
    assert entries["cross_school_scan.py"].status == "active"
    assert entries["extract_predictions.py"].status == "active"

    missing_entries = [entry for entry in entries.values() if entry.status == "missing"]
    assert missing_entries
    assert all(not entry.exists for entry in missing_entries)


@pytest.mark.parametrize(
    "rel, forbidden",
    [
        ("engine/contracts/04-gate-protocol.md", "≥ 0.90 → 5"),
        ("engine/contracts/07-pipeline-flow.md", "engine/pangzheng/support.py support_with_shensha"),
        ("engine/contracts/00-OVERVIEW.md", "└── seal_prediction.py"),
        ("META/conflict-trends.md", "engine/dimension-weights.yaml"),
        ("predictions/PRED-2026-001-C2026001-乾-庚申戊寅壬子辛丑-future.md", "seal_prediction.py"),
        ("predictions/PRED-2026-001-C2026001-乾-庚申戊寅壬子辛丑-future.md", "calibrate.py"),
    ],
)
def test_contract_drift_forbidden_fragments_do_not_return(rel: str, forbidden: str) -> None:
    text = (ROOT / rel).read_text(encoding="utf-8")
    assert forbidden not in text


def test_current_contract_entrypoints_match_implementation() -> None:
    overview = (ROOT / "engine" / "contracts" / "00-OVERVIEW.md").read_text(encoding="utf-8")
    pipeline_flow = (ROOT / "engine" / "contracts" / "07-pipeline-flow.md").read_text(encoding="utf-8")
    naming = (ROOT / "engine" / "contracts" / "09-naming-convention.md").read_text(encoding="utf-8")
    project_state = json.loads((ROOT / "META" / "project-state.json").read_text(encoding="utf-8"))

    assert "V1-V6 / V8" in overview
    assert "V7" in overview
    assert "domain-weights.yaml" in overview
    assert "dimension-weights.yaml` 事实源" in overview
    assert "tools/feedback_ingest.py" in overview
    assert "tools/feedback_loop.py" in overview
    assert "唯一标准报告" in overview

    assert "render_from_output" in pipeline_flow
    assert "variant=\"standard\"" in pipeline_flow
    assert "templates/report-v5.md" in pipeline_flow
    assert "master/client" not in pipeline_flow

    assert "适用分支：`main`" in naming
    assert "tools/preflight.py" in naming
    assert "tools/render_report.py" in naming
    assert "tools/extract_predictions.py" in naming
    assert "当前不存在，不作为可执行入口" in naming

    assert project_state["active_feedback_entrypoints"][:2] == ["tools/feedback_ingest.py", "tools/feedback_loop.py"]
    assert "tools/batch_review.py" in project_state["active_feedback_entrypoints"]
    assert "tools/domain_feedback.py" in project_state["active_feedback_entrypoints"]
    assert project_state["active_report_entrypoints"] == [
        "tools/render_report.py",
        "tools/output_linter.py",
        "tools/domain_analysis_cli.py",
    ]


def test_six_source_three_domain_governance_capabilities_are_wired_without_production_claim() -> None:
    state = json.loads((ROOT / "META" / "project-state.json").read_text(encoding="utf-8"))
    engine_readme = (ROOT / "engine" / "README.md").read_text(encoding="utf-8")
    tools_readme = (ROOT / "tools" / "README.md").read_text(encoding="utf-8")

    required_paths = (
        "engine/evaluation/domain_prospective.py",
        "engine/v5/domain_report_view.py",
        "engine/v5/domain_capability_metrics.py",
        "engine/v5/high_risk_gate.py",
        "engine/v5/domain_feedback.py",
        "engine/contracts/20-domain-prospective-evaluation-v1.md",
        "engine/contracts/21-high-risk-domain-claims-v1.md",
        "tools/domain_prospective_cohort.py",
        "tools/domain_capability_status.py",
        "tools/domain_feedback.py",
        "templates/domain-claim-feedback.json",
    )
    for rel in required_paths:
        assert (ROOT / rel).is_file(), rel

    statuses = state["intelligence_platform_status"]
    assert statuses["domain_prospective_evaluation"].startswith("landed_protocol_and_cli")
    assert statuses["domain_claim_report_workbench"].startswith("landed_")
    assert statuses["domain_capability_diagnostics"].startswith("landed_")
    assert statuses["high_risk_domain_claim_gate"].startswith("landed_")
    assert statuses["domain_claim_feedback"].startswith("landed_")
    assert state["domain_prospective_entrypoint"] == "tools/domain_prospective_cohort.py"
    assert state["domain_capability_status_entrypoint"] == "tools/domain_capability_status.py"
    assert state["domain_prospective_status"] == {
        "engineering_implementation": "landed",
        "real_cohort": "not_ready",
        "production_ready": False,
        "production_switch_permitted": False,
        "status_source": "engine/contracts/20-domain-prospective-evaluation-v1.md",
    }

    for name in ("domain_prospective_cohort.py", "domain_capability_status.py", "domain_feedback.py"):
        assert name in tools_readme
    for name in (
        "domain_prospective.py",
        "domain_report_view.py",
        "domain_capability_metrics.py",
        "high_risk_gate.py",
        "domain_feedback.py",
    ):
        assert name in engine_readme


def test_task12_document_files_and_offline_cohort_tool_are_wired() -> None:
    required_paths = (
        "META/prospective-intake-protocol-v1.md",
        "plans/upgrade-guides/post-gate-action-plan-2026-07-15.md",
        "tools/school_capability_cohort.py",
    )
    for rel in required_paths:
        assert (ROOT / rel).is_file(), rel

    tools_readme = (ROOT / "tools" / "README.md").read_text(encoding="utf-8")
    intake_protocol = (
        ROOT / "META" / "prospective-intake-protocol-v1.md"
    ).read_text(encoding="utf-8")
    assert "school_capability_cohort.py" in tools_readme
    assert "仅离线评估" in tools_readme
    assert "production_switch=false" in tools_readme
    assert "`prediction_capability_candidate_gate_v1` 只消费即时回顾" in intake_protocol
    assert "`future_empirical_gate_v1` 只消费未来观察" in intake_protocol
    assert (
        "`historical_platform_baseline_2026_07_15` 保持只读独立 HOLD"
        in intake_protocol
    )
    assert "`production_switch=false`" in intake_protocol


def test_historical_agent_handoff_is_not_current_branch_source() -> None:
    handoff = (ROOT / "engine" / "contracts" / "08-agent-handoff.md").read_text(encoding="utf-8")
    assert "历史说明" in handoff
    assert "不再作为当前分支策略事实源" in handoff
    assert "AGENTS.md" in handoff
    assert "META/project-state.json" in handoff


def test_ren_career_timing_slice_is_staged_not_production() -> None:
    state = json.loads((ROOT / "META" / "project-state.json").read_text(encoding="utf-8"))
    assert state["intelligence_platform_status"]["ren_career_role_change_timing_slice"] == (
        "staged_verified_production_unchanged"
    )


def test_ziping_career_structure_slice_is_staged_verified_without_production_change() -> None:
    state = json.loads((ROOT / "META" / "project-state.json").read_text(encoding="utf-8"))
    assert state["intelligence_platform_status"]["ziping_career_official_path_disruption_slice"] == (
        "staged_verified_production_unchanged"
    )


def test_yang_marriage_slice_is_staged_verified_without_production_change() -> None:
    state = json.loads((ROOT / "META" / "project-state.json").read_text(encoding="utf-8"))
    assert state["intelligence_platform_status"]["yang_marriage_discrimination_slice"] == (
        "staged_verified_production_unchanged"
    )

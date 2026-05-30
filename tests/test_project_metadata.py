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
    assert "render_both" in overview

    assert "engine.pangzheng.support_with_shensha" in pipeline_flow
    assert "render_from_output" in pipeline_flow
    assert "render_both" in pipeline_flow
    assert "templates/report-v1.3.md" in pipeline_flow

    assert "适用分支：`main`" in naming
    assert "tools/preflight.py" in naming
    assert "tools/render_report.py" in naming
    assert "tools/extract_predictions.py" in naming
    assert "当前不存在，不作为可执行入口" in naming

    assert project_state["active_feedback_entrypoints"][:2] == ["tools/feedback_ingest.py", "tools/feedback_loop.py"]
    assert "tools/batch_review.py" in project_state["active_feedback_entrypoints"]
    assert project_state["active_report_entrypoints"] == ["tools/render_report.py", "tools/output_linter.py"]


def test_historical_agent_handoff_is_not_current_branch_source() -> None:
    handoff = (ROOT / "engine" / "contracts" / "08-agent-handoff.md").read_text(encoding="utf-8")
    assert "历史说明" in handoff
    assert "不再作为当前分支策略事实源" in handoff
    assert "AGENTS.md" in handoff
    assert "META/project-state.json" in handoff

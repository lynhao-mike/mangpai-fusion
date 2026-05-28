from __future__ import annotations

import ast
import json
import re
from pathlib import Path

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

    combined_primary_docs = "\n".join([readme, status, meta_index])
    assert "tools/calibrate.py" not in combined_primary_docs
    assert "seal_prediction.py" not in combined_primary_docs
    assert "verify_evidence.py" not in combined_primary_docs

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

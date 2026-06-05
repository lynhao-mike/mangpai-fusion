from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from engine.application.production_rule_loader import (
    ProductionRuleValidationError,
    load_default_production_library,
    load_production_library,
    load_production_rule_set,
)
from engine.pipeline import run_pipeline
from tests.fixtures.cases import load_case


def test_load_default_production_library_loads_ziping_and_ditiansui() -> None:
    library = load_default_production_library()

    assert set(library.rule_sets) == {"ziping", "tiaohou_ditiansui"}
    assert [rule.id for rule in library.rules] == [
        "ZP-PROD-20260605-001",
        "ZP-PROD-20260605-002",
        "DTS-PROD-20260605-001",
        "DTS-PROD-20260605-002",
    ]
    assert all(rule.status == "active" for rule in library.rules)


def test_pipeline_injects_production_rule_conclusions() -> None:
    parsed = load_case("C-2026-001-乾-庚申戊寅壬子辛丑")

    output = run_pipeline(parsed, write_findings=False)

    production_ids = {
        evidence.rule_id
        for conclusion in output.final_conclusions
        for evidence in conclusion.evidence
        if evidence.rule_id.startswith(("ZP-PROD-", "DTS-PROD-"))
    }
    assert "ZP-PROD-20260605-001" in production_ids
    assert "DTS-PROD-20260605-001" in production_ids
    assert any("子平规则参与" in c.statement for c in output.final_conclusions)
    assert any("滴天髓规则参与" in c.statement for c in output.final_conclusions)


def test_production_loader_rejects_bypass_candidate_path() -> None:
    with pytest.raises(ProductionRuleValidationError, match="只能读取 theory/ziping"):
        load_production_rule_set("theory/raw/yaml/ziping_candidate_rules_2026-06-05.yaml")


def test_production_loader_rejects_non_active_status(tmp_path: Path) -> None:
    path = _write_production_yaml(tmp_path, "ziping", status="review_draft")

    with pytest.raises(ProductionRuleValidationError, match="active"):
        load_production_rule_set(path, workspace_root=tmp_path)


def test_production_loader_rejects_duplicate_expert_system(tmp_path: Path) -> None:
    path_a = _write_production_yaml(tmp_path, "ziping", filename="a.yaml")
    path_b = _write_production_yaml(tmp_path, "ziping", filename="b.yaml")

    with pytest.raises(ProductionRuleValidationError, match="重复加载"):
        load_production_library([path_a, path_b], workspace_root=tmp_path)


def _write_production_yaml(
    tmp_path: Path,
    expert_system: str,
    *,
    filename: str = "index.yaml",
    status: str = "active",
    rule_status: str = "active",
) -> Path:
    directory = tmp_path / "theory" / expert_system
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / filename
    payload = {
        "schema_version": "production-rules-test",
        "status": status,
        "source_scope": "production_rules",
        "expert_system": expert_system,
        "notes": "test production rules",
        "rules": [
            {
                "id": f"TEST-PROD-{expert_system}-001",
                "status": rule_status,
                "expert_system": expert_system,
                "title": "测试生产规则",
                "topic": "test_topic",
                "domains": ["事业"],
                "axis_refs": ["AXIS-TEST"],
                "claim": "测试 claim",
                "layer": "互补",
                "conditions": {
                    "trigger": "always",
                    "required": ["存在测试条件"],
                    "optional": [],
                    "exclusions": [],
                },
                "output": {
                    "statement": "测试 statement",
                    "falsifiable": "测试 falsifiable",
                },
                "confidence": {
                    "star": 4,
                    "percent": 0.75,
                    "posterior": 0.75,
                    "variance": 0.04,
                    "sample_n": 1,
                },
                "source": {"path": "sources/test.md", "excerpt": "测试 excerpt"},
                "review": {"notes": "测试 review"},
            }
        ],
    }
    path.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return path

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from engine.application.candidate_rule_loader import (
    CandidateRuleValidationError,
    load_candidate_library,
    load_candidate_rule_set,
    load_default_candidate_library,
)


def test_load_default_candidate_library_loads_ziping_and_ditiansui() -> None:
    library = load_default_candidate_library()

    assert set(library.rule_sets) == {"ziping", "tiaohou_ditiansui"}
    assert len(library.rule_sets["ziping"].rules) == 2
    assert len(library.rule_sets["tiaohou_ditiansui"].rules) == 2
    assert [rule.id for rule in library.rules] == [
        "ZP-CAND-20260605-001",
        "ZP-CAND-20260605-002",
        "DTS-CAND-20260605-001",
        "DTS-CAND-20260605-002",
    ]


def test_rules_can_be_filtered_by_domain_and_expert_system() -> None:
    library = load_default_candidate_library()

    career_rules = library.rules_for_domain("事业")
    ziping_wealth_rules = library.rules_for_domain("财富", expert_system="ziping")
    dts_health_rules = library.rules_for_domain("健康", expert_system="tiaohou_ditiansui")

    assert [rule.id for rule in career_rules] == [
        "ZP-CAND-20260605-001",
        "ZP-CAND-20260605-002",
        "DTS-CAND-20260605-001",
        "DTS-CAND-20260605-002",
    ]
    assert [rule.id for rule in ziping_wealth_rules] == [
        "ZP-CAND-20260605-001",
        "ZP-CAND-20260605-002",
    ]
    assert [rule.id for rule in dts_health_rules] == [
        "DTS-CAND-20260605-001",
        "DTS-CAND-20260605-002",
    ]


def test_candidate_rule_can_be_converted_to_evidence_item() -> None:
    rule = load_default_candidate_library().rule_sets["ziping"].rules[0]

    evidence = rule.to_evidence_item()

    assert evidence.evidence_type == "candidate_rule"
    assert evidence.ref == "ZP-CAND-20260605-001"
    assert evidence.summary == rule.claim
    assert evidence.strength == "medium"


def test_load_candidate_library_rejects_duplicate_expert_system(tmp_path: Path) -> None:
    path_a = _write_candidate_yaml(tmp_path, "ziping_a.yaml", expert_system="ziping")
    path_b = _write_candidate_yaml(tmp_path, "ziping_b.yaml", expert_system="ziping")

    with pytest.raises(CandidateRuleValidationError, match="重复加载"):
        load_candidate_library([path_a, path_b], workspace_root=tmp_path)


def test_loader_rejects_paths_outside_bypass_yaml_dir(tmp_path: Path) -> None:
    path = tmp_path / "outside.yaml"
    path.write_text(yaml.safe_dump(_candidate_payload("ziping"), allow_unicode=True), encoding="utf-8")

    with pytest.raises(CandidateRuleValidationError, match="只能读取"):
        load_candidate_rule_set(path, workspace_root=tmp_path)


def test_loader_rejects_non_review_draft_top_level_status(tmp_path: Path) -> None:
    path = _write_candidate_yaml(tmp_path, "ziping.yaml", expert_system="ziping", status="active")

    with pytest.raises(CandidateRuleValidationError, match="review_draft"):
        load_candidate_rule_set(path, workspace_root=tmp_path)


def test_loader_rejects_non_bypass_source_scope(tmp_path: Path) -> None:
    path = _write_candidate_yaml(
        tmp_path,
        "ziping.yaml",
        expert_system="ziping",
        source_scope="production_rules",
    )

    with pytest.raises(CandidateRuleValidationError, match="bypass_candidate_rules"):
        load_candidate_rule_set(path, workspace_root=tmp_path)


@pytest.mark.parametrize("rule_status", ["active", "confirmed", "promoted", "deprecated"])
def test_loader_rejects_prohibited_rule_statuses(tmp_path: Path, rule_status: str) -> None:
    path = _write_candidate_yaml(
        tmp_path,
        "ziping.yaml",
        expert_system="ziping",
        rule_status=rule_status,
    )

    with pytest.raises(CandidateRuleValidationError, match="candidate"):
        load_candidate_rule_set(path, workspace_root=tmp_path)


def test_loader_rejects_rule_expert_system_mismatch(tmp_path: Path) -> None:
    payload = _candidate_payload("ziping")
    payload["rules"][0]["expert_system"] = "tiaohou_ditiansui"
    path = _write_payload(tmp_path, "ziping.yaml", payload)

    with pytest.raises(CandidateRuleValidationError, match="expert_system"):
        load_candidate_rule_set(path, workspace_root=tmp_path)


def test_loader_rejects_expected_expert_system_mismatch(tmp_path: Path) -> None:
    path = _write_candidate_yaml(tmp_path, "ziping.yaml", expert_system="ziping")

    with pytest.raises(CandidateRuleValidationError, match="文件 expert_system"):
        load_candidate_rule_set(
            path,
            workspace_root=tmp_path,
            expected_expert_system="tiaohou_ditiansui",
        )


def _write_candidate_yaml(
    tmp_path: Path,
    filename: str,
    *,
    expert_system: str,
    status: str = "review_draft",
    source_scope: str = "bypass_candidate_rules",
    rule_status: str = "candidate",
) -> Path:
    payload = _candidate_payload(
        expert_system,
        status=status,
        source_scope=source_scope,
        rule_status=rule_status,
    )
    return _write_payload(tmp_path, filename, payload)


def _write_payload(tmp_path: Path, filename: str, payload: dict) -> Path:
    yaml_dir = tmp_path / "theory" / "raw" / "yaml"
    yaml_dir.mkdir(parents=True, exist_ok=True)
    path = yaml_dir / filename
    path.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return path


def _candidate_payload(
    expert_system: str,
    *,
    status: str = "review_draft",
    source_scope: str = "bypass_candidate_rules",
    rule_status: str = "candidate",
) -> dict:
    return {
        "schema_version": "review-draft-2026-06-05",
        "status": status,
        "source_scope": source_scope,
        "expert_system": expert_system,
        "notes": "test candidate rules",
        "rules": [
            {
                "id": f"TEST-{expert_system}-001",
                "status": rule_status,
                "expert_system": expert_system,
                "title": "测试候选规则",
                "topic": "test_topic",
                "domains": ["事业", "健康"],
                "axis_refs": ["AXIS-TEST"],
                "claim": "测试 claim",
                "conditions": {
                    "required": ["存在测试条件"],
                    "optional": ["存在可选条件"],
                    "exclusions": ["存在排除条件"],
                },
                "output": {
                    "statement": "测试 statement",
                    "falsifiable": "测试 falsifiable",
                },
                "source": {
                    "path": "sources/test.md",
                    "excerpt": "测试 excerpt",
                },
                "review": {"notes": "测试 review"},
            }
        ],
    }

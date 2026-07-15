from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest
import yaml

from engine.claims.rule_loader import (
    CLAIM_RULE_SCHEMA_VERSION,
    ClaimRuleRegistry,
    RuleCondition,
    RuleEvaluationError,
    RuleSchemaError,
    evaluate_rule,
    load_claim_rule_registry,
)


RULE_PATH = Path("theory/production/claim-rules-v1.yaml")
EXPECTED_RULE_IDS = (
    "DUAN-EVENT-CAREER-ROLE-CHANGE-V1",
    "DUAN-EVENT-CAREER-PATH-EMPLOYMENT-V1",
    "DUAN-EVENT-CAREER-PATH-ENTREPRENEURSHIP-V1",
    "DUAN-EVENT-CAREER-PATH-MIXED-V1",
    "DUAN-EVENT-WEALTH-DEBT-V1",
    "DUAN-EVENT-MARRIAGE-DIVORCE-REMARRIAGE-V1",
    "GAO-WEALTH-DEBT-STRUCTURAL-CORROBORATION-V1",
    "GAO-HEALTH-SYSTEM-RISK-MODERATE-V1",
    "GAO-HEALTH-SYSTEM-RISK-HIGH-V1",
    "YANG-MARRIAGE-DIVORCE-REMARRIAGE-RISK-V1",
)
REQUIRED_RULE_FIELDS = {
    "rule_id",
    "school_id",
    "task_scope",
    "claim_type",
    "required_facts",
    "conditions",
    "exclusions",
    "counter_conditions",
    "conclusion_template",
    "confidence_basis",
    "falsifier",
    "source_refs",
    "lifecycle_state",
}


def _document() -> dict[str, object]:
    return yaml.safe_load(RULE_PATH.read_text(encoding="utf-8"))


def _write_document(tmp_path: Path, document: dict[str, object]) -> Path:
    path = tmp_path / "claim-rules.yaml"
    path.write_text(yaml.safe_dump(document, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return path


def _minimal_rule() -> dict[str, object]:
    return {
        "rule_id": "TEST-RULE-V1",
        "school_id": "duan",
        "task_scope": ["wealth.debt"],
        "claim_type": "event_claim",
        "required_facts": ["score", "blocked", "warning"],
        "conditions": [{"fact": "score", "op": "gte", "value": 3}],
        "exclusions": [{"fact": "blocked", "op": "truthy", "value": True}],
        "counter_conditions": [{"fact": "warning", "op": "truthy", "value": True}],
        "conclusion_template": "测试结论。",
        "confidence_basis": "测试证据强度。",
        "falsifier": "若现实结果未发生则证伪。",
        "source_refs": [
            {
                "path": "theory/duan/index.yaml",
                "locator": "M1-D-009 / §17.3 做功",
                "supports": "支持测试结构。",
            }
        ],
        "lifecycle_state": "production-candidate",
        "base_confidence": 0.6,
        "high_risk_confidence_cap": 0.62,
        "polarity": "negative",
    }


def _minimal_document() -> dict[str, object]:
    return {"schema_version": CLAIM_RULE_SCHEMA_VERSION, "rules": [_minimal_rule()]}


def _load_temp(tmp_path: Path, document: dict[str, object]) -> ClaimRuleRegistry:
    return load_claim_rule_registry(_write_document(tmp_path, document))


def test_production_registry_loads_exact_versioned_rule_set_and_real_sources() -> None:
    registry = load_claim_rule_registry(RULE_PATH)

    assert registry.schema_version == "claim-executable-rules/v1"
    assert registry.rule_ids == EXPECTED_RULE_IDS
    assert len(registry) == 10
    assert registry.find(school_id="duan", task_id="career.path_type") == tuple(
        registry.get(rule_id) for rule_id in EXPECTED_RULE_IDS[1:4]
    )
    for rule in registry.rules:
        assert rule.claim_type == "event_claim"
        assert rule.lifecycle_state in {"staged", "production-candidate"}
        assert rule.conditions and rule.task_scope and rule.falsifier and rule.source_refs
        assert set(condition.fact for condition in (*rule.conditions, *rule.exclusions, *rule.counter_conditions)) <= set(
            rule.required_facts
        )
        for source_ref in rule.source_refs:
            assert Path(source_ref.path).is_file(), (rule.rule_id, source_ref.path)
            assert source_ref.locator and source_ref.supports


def test_repeated_load_is_equivalent_and_order_is_stable() -> None:
    first = load_claim_rule_registry(RULE_PATH)
    second = load_claim_rule_registry(RULE_PATH)
    assert first == second
    assert first.rule_ids == second.rule_ids == EXPECTED_RULE_IDS


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda doc: doc.update(schema_version="claim-executable-rules/v999"), "schema_version"),
        (lambda doc: doc.update(extra=True), "unknown top-level"),
    ],
)
def test_top_level_schema_is_strict(tmp_path: Path, mutation, message: str) -> None:
    document = _minimal_document()
    mutation(document)
    with pytest.raises(RuleSchemaError, match=message):
        _load_temp(tmp_path, document)


@pytest.mark.parametrize("missing", sorted(REQUIRED_RULE_FIELDS))
def test_each_required_rule_field_is_enforced(tmp_path: Path, missing: str) -> None:
    document = _minimal_document()
    document["rules"][0].pop(missing)  # type: ignore[index]
    with pytest.raises(RuleSchemaError, match=missing):
        _load_temp(tmp_path, document)


def test_unknown_rule_field_is_rejected(tmp_path: Path) -> None:
    document = _minimal_document()
    document["rules"][0]["speculative_magic"] = True  # type: ignore[index]
    with pytest.raises(RuleSchemaError, match="unknown.*speculative_magic"):
        _load_temp(tmp_path, document)


def test_duplicate_rule_id_is_rejected(tmp_path: Path) -> None:
    document = _minimal_document()
    document["rules"].append(dict(document["rules"][0]))  # type: ignore[union-attr,index]
    with pytest.raises(RuleSchemaError, match="duplicate rule_id"):
        _load_temp(tmp_path, document)


def test_unknown_operator_is_rejected(tmp_path: Path) -> None:
    document = _minimal_document()
    document["rules"][0]["conditions"][0]["op"] = "python_eval"  # type: ignore[index]
    with pytest.raises(RuleSchemaError, match="operator"):
        _load_temp(tmp_path, document)


@pytest.mark.parametrize(
    ("field", "value"),
    [("conditions", []), ("falsifier", ""), ("source_refs", []), ("task_scope", [])],
)
def test_required_non_empty_rule_values_are_enforced(tmp_path: Path, field: str, value: object) -> None:
    document = _minimal_document()
    document["rules"][0][field] = value  # type: ignore[index]
    with pytest.raises(RuleSchemaError, match=field):
        _load_temp(tmp_path, document)


def test_missing_source_path_is_rejected(tmp_path: Path) -> None:
    document = _minimal_document()
    document["rules"][0]["source_refs"][0]["path"] = "theory/no-such-source.yaml"  # type: ignore[index]
    with pytest.raises(RuleSchemaError, match="source.*does not exist"):
        _load_temp(tmp_path, document)


def test_registry_and_nested_rule_values_are_immutable_and_detached_from_yaml(tmp_path: Path) -> None:
    document = _minimal_document()
    registry = _load_temp(tmp_path, document)
    rule = registry.get("TEST-RULE-V1")

    document["rules"][0]["task_scope"].append("career.role_change")  # type: ignore[index]
    document["rules"][0]["conditions"][0]["value"] = 999  # type: ignore[index]
    assert rule.task_scope == ("wealth.debt",)
    assert rule.conditions[0].value == 3
    assert isinstance(rule.conditions, tuple)
    with pytest.raises(FrozenInstanceError):
        rule.rule_id = "changed"  # type: ignore[misc]
    with pytest.raises(TypeError):
        registry.by_id["OTHER"] = rule  # type: ignore[index]


def test_unknown_rule_id_fails_explicitly() -> None:
    registry = load_claim_rule_registry(RULE_PATH)
    with pytest.raises(KeyError, match="unknown claim rule"):
        registry.get("NO-SUCH-RULE")


@pytest.mark.parametrize(
    ("condition", "matching", "not_matching"),
    [
        (RuleCondition("value", "eq", 3), {"value": 3}, {"value": 4}),
        (RuleCondition("value", "ne", 3), {"value": 4}, {"value": 3}),
        (RuleCondition("value", "gte", 3), {"value": 3}, {"value": 2}),
        (RuleCondition("value", "lte", 3), {"value": 3}, {"value": 4}),
        (RuleCondition("value", "in", ("a", "b")), {"value": "a"}, {"value": "c"}),
        (RuleCondition("value", "not_in", ("a", "b")), {"value": "c"}, {"value": "a"}),
        (RuleCondition("value", "truthy", True), {"value": [1]}, {"value": []}),
        (RuleCondition("value", "falsy", True), {"value": []}, {"value": [1]}),
    ],
)
def test_operator_whitelist_has_positive_and_negative_behavior(
    condition: RuleCondition, matching: dict[str, object], not_matching: dict[str, object],
) -> None:
    rule = replace(
        load_claim_rule_registry(RULE_PATH).rules[0],
        required_facts=("value",),
        conditions=(condition,),
        exclusions=(),
        counter_conditions=(),
    )
    assert evaluate_rule(rule, matching).matched is True
    assert evaluate_rule(rule, not_matching).matched is False


def test_all_conditions_must_match_and_any_exclusion_vetoes() -> None:
    base = load_claim_rule_registry(RULE_PATH).rules[0]
    rule = replace(
        base,
        required_facts=("nested.score", "ready", "blocked"),
        conditions=(RuleCondition("nested.score", "gte", 3), RuleCondition("ready", "truthy", True)),
        exclusions=(RuleCondition("blocked", "truthy", True),),
        counter_conditions=(),
    )
    assert evaluate_rule(rule, {"nested": {"score": 3}, "ready": True, "blocked": False}).matched
    assert not evaluate_rule(rule, {"nested": {"score": 2}, "ready": True, "blocked": False}).matched
    vetoed = evaluate_rule(rule, {"nested": {"score": 3}, "ready": True, "blocked": True})
    assert not vetoed.matched and vetoed.matched_exclusions == rule.exclusions


def test_counter_conditions_are_auditable_but_do_not_veto() -> None:
    registry = load_claim_rule_registry(RULE_PATH)
    base = registry.rules[0]
    counter = RuleCondition("warning", "truthy", True)
    rule = replace(
        base,
        required_facts=("score", "warning"),
        conditions=(RuleCondition("score", "gte", 3),),
        exclusions=(),
        counter_conditions=(counter,),
    )
    result = evaluate_rule(rule, {"score": 4, "warning": True})
    assert result.matched is True
    assert result.matched_counter_conditions == (counter,)


def test_missing_context_fact_and_incompatible_types_fail_explicitly() -> None:
    rule = load_claim_rule_registry(RULE_PATH).rules[0]
    with pytest.raises(RuleEvaluationError, match="missing context fact"):
        evaluate_rule(rule, {})

    numeric_rule = replace(
        rule,
        required_facts=("score",),
        conditions=(RuleCondition("score", "gte", 3),),
        exclusions=(),
        counter_conditions=(),
    )
    with pytest.raises(RuleEvaluationError, match="incompatible"):
        evaluate_rule(numeric_rule, {"score": "3"})


def test_temporary_yaml_threshold_changes_result_without_evaluator_change(tmp_path: Path) -> None:
    document = _minimal_document()
    low = _load_temp(tmp_path, document).get("TEST-RULE-V1")
    assert evaluate_rule(low, {"score": 3, "blocked": False, "warning": False}).matched

    document["rules"][0]["conditions"][0]["value"] = 4  # type: ignore[index]
    high = _load_temp(tmp_path, document).get("TEST-RULE-V1")
    assert not evaluate_rule(high, {"score": 3, "blocked": False, "warning": False}).matched


def _contexts() -> dict[str, tuple[dict[str, object], dict[str, object], dict[str, object], dict[str, object]]]:
    full = {"evidence_completeness": "full"}
    return {
        "DUAN-EVENT-CAREER-ROLE-CHANGE-V1": (
            {**full, "has_official": True, "has_output": True, "output_count": 2, "official_count": 1, "movement_structure": True, "mixed_official_kill": True, "branch_conflict_intensity": 0.0, "active_path_count": 1},
            {**full, "has_official": True, "has_output": False, "output_count": 2, "official_count": 1, "movement_structure": True, "mixed_official_kill": True, "branch_conflict_intensity": 0.0, "active_path_count": 1},
            {"evidence_completeness": "partial", "has_official": True, "has_output": True, "output_count": 2, "official_count": 1, "movement_structure": True, "mixed_official_kill": True, "branch_conflict_intensity": 0.0, "active_path_count": 1},
            {**full, "has_official": True, "has_output": True, "output_count": 1, "official_count": 1, "movement_structure": True, "mixed_official_kill": True, "branch_conflict_intensity": 0.0, "active_path_count": 1},
        ),
        "DUAN-EVENT-CAREER-PATH-EMPLOYMENT-V1": (
            {**full, "predicted_label": "employment", "employment_score": 4, "entrepreneurship_score": 1, "employment_advantage": 3, "active_path_count": 0},
            {**full, "predicted_label": "mixed", "employment_score": 4, "entrepreneurship_score": 4, "employment_advantage": 0, "active_path_count": 1},
            {"evidence_completeness": "partial", "predicted_label": "employment", "employment_score": 4, "entrepreneurship_score": 1, "employment_advantage": 3, "active_path_count": 0},
            {**full, "predicted_label": "employment", "employment_score": 3, "entrepreneurship_score": 0, "employment_advantage": 3, "active_path_count": 0},
        ),
        "DUAN-EVENT-CAREER-PATH-ENTREPRENEURSHIP-V1": (
            {**full, "predicted_label": "entrepreneurship", "employment_score": 1, "entrepreneurship_score": 4, "entrepreneurship_advantage": 3, "active_path_count": 1},
            {**full, "predicted_label": "employment", "employment_score": 4, "entrepreneurship_score": 1, "entrepreneurship_advantage": -3, "active_path_count": 1},
            {"evidence_completeness": "partial", "predicted_label": "entrepreneurship", "employment_score": 1, "entrepreneurship_score": 4, "entrepreneurship_advantage": 3, "active_path_count": 1},
            {**full, "predicted_label": "entrepreneurship", "employment_score": 1, "entrepreneurship_score": 4, "entrepreneurship_advantage": 3, "active_path_count": 0},
        ),
        "DUAN-EVENT-CAREER-PATH-MIXED-V1": (
            {**full, "predicted_label": "mixed", "employment_score": 4, "entrepreneurship_score": 4, "branch_conflict_intensity": 0.35, "active_path_count": 1},
            {**full, "predicted_label": "mixed", "employment_score": 4, "entrepreneurship_score": 4, "branch_conflict_intensity": 0.2, "active_path_count": 1},
            {"evidence_completeness": "partial", "predicted_label": "mixed", "employment_score": 4, "entrepreneurship_score": 4, "branch_conflict_intensity": 0.35, "active_path_count": 1},
            {**full, "predicted_label": "mixed", "employment_score": 3, "entrepreneurship_score": 4, "branch_conflict_intensity": 0.35, "active_path_count": 1},
        ),
        "DUAN-EVENT-WEALTH-DEBT-V1": (
            {**full, "has_wealth": True, "wealth_count": 2, "peer_pressure": 3, "support_drain_imbalance": 3, "branch_conflict_intensity": 0.55, "active_path_count": 1},
            {**full, "has_wealth": False, "wealth_count": 2, "peer_pressure": 3, "support_drain_imbalance": 3, "branch_conflict_intensity": 0.55, "active_path_count": 1},
            {"evidence_completeness": "partial", "has_wealth": True, "wealth_count": 2, "peer_pressure": 3, "support_drain_imbalance": 3, "branch_conflict_intensity": 0.55, "active_path_count": 1},
            {**full, "has_wealth": True, "wealth_count": 2, "peer_pressure": 3, "support_drain_imbalance": 3, "branch_conflict_intensity": 0.54, "active_path_count": 1},
        ),
        "DUAN-EVENT-MARRIAGE-DIVORCE-REMARRIAGE-V1": (
            {**full, "independent_signal_count": 2, "active_path_count": 1},
            {**full, "independent_signal_count": 1, "active_path_count": 1},
            {"evidence_completeness": "partial", "independent_signal_count": 2, "active_path_count": 1},
            {**full, "independent_signal_count": 2, "active_path_count": 0},
        ),
        "GAO-WEALTH-DEBT-STRUCTURAL-CORROBORATION-V1": (
            {**full, "wealth_exposed": True, "pressure_signal_count": 2},
            {**full, "wealth_exposed": False, "pressure_signal_count": 2},
            {"evidence_completeness": "partial", "wealth_exposed": True, "pressure_signal_count": 2},
            {**full, "wealth_exposed": True, "pressure_signal_count": 1},
        ),
        "GAO-HEALTH-SYSTEM-RISK-MODERATE-V1": (
            {**full, "predicted_label": "moderate", "risk_signal_count": 2},
            {**full, "predicted_label": "high", "risk_signal_count": 3},
            {"evidence_completeness": "partial", "predicted_label": "moderate", "risk_signal_count": 2},
            {**full, "predicted_label": "moderate", "risk_signal_count": 1},
        ),
        "GAO-HEALTH-SYSTEM-RISK-HIGH-V1": (
            {**full, "predicted_label": "high", "risk_signal_count": 3},
            {**full, "predicted_label": "moderate", "risk_signal_count": 2},
            {"evidence_completeness": "partial", "predicted_label": "high", "risk_signal_count": 3},
            {**full, "predicted_label": "high", "risk_signal_count": 2},
        ),
        "YANG-MARRIAGE-DIVORCE-REMARRIAGE-RISK-V1": (
            {**full, "sex": "male", "spouse_star_basis": "wealth", "independent_signal_count": 2},
            {**full, "sex": "male", "spouse_star_basis": "wealth", "independent_signal_count": 1},
            {**full, "sex": None, "spouse_star_basis": "unknown", "independent_signal_count": 2},
            {**full, "sex": "female", "spouse_star_basis": "official", "independent_signal_count": 1},
        ),
    }


@pytest.mark.parametrize("rule_id", EXPECTED_RULE_IDS)
def test_each_production_rule_has_positive_negative_exclusion_boundary_and_two_context_stability(rule_id: str) -> None:
    rule = load_claim_rule_registry(RULE_PATH).get(rule_id)
    positive, negative, excluded, boundary = _contexts()[rule_id]

    assert evaluate_rule(rule, positive).matched is True
    assert evaluate_rule(rule, dict(positive)).matched is True
    assert evaluate_rule(rule, negative).matched is False
    excluded_result = evaluate_rule(rule, excluded)
    assert excluded_result.matched is False and excluded_result.matched_exclusions
    assert evaluate_rule(rule, boundary).matched is False
    assert rule.falsifier and any(token in rule.falsifier for token in ("若", "未", "没有", "不属于"))


def test_loader_and_migrated_runners_do_not_use_dynamic_execution_or_revealed_inputs() -> None:
    forbidden_import_tokens = ("feedback", "labels", "reports", "cases", "importlib")
    for relative in (
        "engine/claims/rule_loader.py",
        "engine/v5/duan_runner.py",
        "engine/v5/gao_runner.py",
        "engine/v5/yang_runner.py",
    ):
        source = Path(relative).read_text(encoding="utf-8")
        tree = ast.parse(source)
        assert not any(isinstance(node, (ast.Call,)) and isinstance(node.func, ast.Name) and node.func.id in {"eval", "exec"} for node in ast.walk(tree))
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.append(node.module or "")
        assert not any(token in item.lower() for token in forbidden_import_tokens for item in imports), relative

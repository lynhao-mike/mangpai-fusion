from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest
import yaml

from engine.decision.ziping_career_rules import (
    DEFAULT_RULE_PATH,
    MappingSchemaError,
    load_ziping_career_rule_mapping,
    mapping_digest,
)


def test_mapping_binds_exact_production_ids_to_one_task_rule() -> None:
    mapping = load_ziping_career_rule_mapping()
    assert mapping.schema_version == "ziping-career-structure-rules/v1"
    assert mapping.school_id == "ziping"
    assert mapping.task_id == "career.role_change"
    assert mapping.domain == "事业"
    assert mapping.target_layer == "L3"
    assert mapping.task_rule_id == "ZIPING-CAREER-OFFICIAL-PATH-DISRUPTION-V1"
    assert tuple(item.production_rule_id for item in mapping.source_anchors) == (
        "ZP-PROD-20260622-011",
        "ZP-PROD-20260622-012",
    )
    assert mapping.required_gates == (
        "complete_fact_closure",
        "official_path_anchor",
        "output_interference_present",
        "structure_qualification",
    )


def test_source_anchors_resolve_to_exact_production_entries() -> None:
    document = yaml.safe_load(Path("theory/ziping/index.yaml").read_text(encoding="utf-8"))
    indexed = {item["id"]: item for item in document["rules"]}
    mapping = load_ziping_career_rule_mapping()
    for anchor in mapping.source_anchors:
        source = indexed[anchor.production_rule_id]
        assert source["source"]["path"] == anchor.path
        assert int(source["source"]["line"]) == anchor.line
        assert anchor.excerpt in source["source"]["excerpt"]


def test_mapping_is_immutable_and_digest_is_order_stable(tmp_path: Path) -> None:
    original = load_ziping_career_rule_mapping()
    raw = yaml.safe_load(DEFAULT_RULE_PATH.read_text(encoding="utf-8"))
    raw["source_anchors"] = list(reversed(raw["source_anchors"]))
    path = tmp_path / "mapping.yaml"
    path.write_text(yaml.safe_dump(raw, allow_unicode=True, sort_keys=False), encoding="utf-8")
    reordered = load_ziping_career_rule_mapping(path)
    assert mapping_digest(original) == mapping_digest(reordered)
    with pytest.raises(FrozenInstanceError):
        original.task_rule_id = "changed"  # type: ignore[misc]


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda doc: doc.update(extra=True), "unknown top-level"),
        (lambda doc: doc.update(schema_version="wrong"), "schema_version"),
        (lambda doc: doc.update(task_id="career.change_window"), "task_id"),
        (lambda doc: doc["source_anchors"].clear(), "source_anchors"),
        (lambda doc: doc["conditions"][0].update(op="python_eval"), "operator"),
    ],
)
def test_invalid_mapping_fails_closed(tmp_path: Path, mutation, message: str) -> None:
    raw = yaml.safe_load(DEFAULT_RULE_PATH.read_text(encoding="utf-8"))
    mutation(raw)
    path = tmp_path / "invalid.yaml"
    path.write_text(yaml.safe_dump(raw, allow_unicode=True, sort_keys=False), encoding="utf-8")
    with pytest.raises(MappingSchemaError, match=message):
        load_ziping_career_rule_mapping(path)

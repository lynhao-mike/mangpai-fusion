from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import yaml

INPUT_FILES = [
    Path("theory/duan/index.yaml"),
    Path("theory/gao/index.yaml"),
    Path("theory/yang/index.yaml"),
    Path("theory/ren/index.yaml"),
    Path("theory/ziping/index.yaml"),
    Path("theory/tiaohou_ditiansui/index.yaml"),
]

DOMAIN_MAP = {
    "财": "财",
    "财运": "财",
    "财富": "财",
    "事业财富": "财",
    "官": "官",
    "官运": "官",
    "事业": "官",
    "职业": "官",
    "印": "印",
    "学业": "印",
    "学历": "印",
    "婚姻": "婚姻",
    "婚恋": "婚姻",
    "感情": "婚姻",
    "健康": "健康",
    "疾病": "健康",
    "寿命": "健康",
    "性格": "性格",
}

ELEMENT_TOKENS = {
    "wood": ["木", "甲", "乙", "寅", "卯"],
    "fire": ["火", "丙", "丁", "巳", "午"],
    "earth": ["土", "戊", "己", "辰", "戌", "丑", "未"],
    "metal": ["金", "庚", "辛", "申", "酉"],
    "water": ["水", "壬", "癸", "亥", "子"],
}


def load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def theory_id_for(path: Path, item: dict[str, Any]) -> str:
    return str(item.get("school") or item.get("expert_system") or path.parent.name)


def extract_records(path: Path, data: Any) -> tuple[list[dict[str, Any]], list[str], str]:
    if isinstance(data, dict) and isinstance(data.get("rules"), list):
        return [x for x in data["rules"] if isinstance(x, dict)], [], "mapping_with_rules_list"
    if isinstance(data, list):
        records: list[dict[str, Any]] = []
        wrappers: Counter[str] = Counter()
        mismatch: list[str] = []
        for idx, item in enumerate(data):
            if isinstance(item, dict) and len(item) == 1 and isinstance(item.get("Rule"), dict):
                wrappers["Rule"] += 1
                records.append(item["Rule"])
            elif isinstance(item, dict):
                records.append(item)
                mismatch.append(f"list_item_{idx}: dict_without_Rule_wrapper")
            else:
                mismatch.append(f"list_item_{idx}: unsupported_{type(item).__name__}")
        fmt = "list_of_Rule_wrappers" if wrappers else "list_of_mappings"
        return records, mismatch, fmt
    return [], [f"top_level_unsupported_{type(data).__name__}"], type(data).__name__


def flatten_strings(value: Any) -> list[str]:
    out: list[str] = []
    if value is None:
        return out
    if isinstance(value, str):
        s = value.strip()
        if s:
            out.append(s)
    elif isinstance(value, (int, float, bool)):
        out.append(str(value))
    elif isinstance(value, list):
        for x in value:
            out.extend(flatten_strings(x))
    elif isinstance(value, dict):
        for x in value.values():
            out.extend(flatten_strings(x))
    return out


def first_text(item: dict[str, Any], keys: list[str]) -> str:
    for key in keys:
        val = item.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
        if key == "output" and isinstance(val, dict):
            statement = val.get("statement")
            if isinstance(statement, str) and statement.strip():
                return statement.strip()
    return ""


def extract_statement(item: dict[str, Any]) -> str:
    return first_text(item, ["statement", "claim", "conclusion", "output", "title"])


def extract_domains(item: dict[str, Any]) -> list[str]:
    explicit: list[str] = []
    for key in ("domain", "domains", "prediction_target"):
        val = item.get(key)
        if isinstance(val, str):
            explicit.append(val)
        elif isinstance(val, list):
            explicit.extend([x for x in val if isinstance(x, str)])
    normalized: list[str] = []
    for raw in explicit:
        raw = raw.strip()
        if not raw:
            continue
        mapped = DOMAIN_MAP.get(raw)
        if mapped and mapped not in normalized:
            normalized.append(mapped)
    return normalized


def extract_tags(item: dict[str, Any]) -> list[str]:
    tags: list[str] = []
    for key in ("topic", "topic_label", "rule_type", "axis_refs", "layer", "canon", "raw_anchor"):
        val = item.get(key)
        vals = val if isinstance(val, list) else [val]
        for entry in vals:
            if entry is None:
                continue
            tag = f"{key}:{entry}".strip()
            if tag not in tags:
                tags.append(tag)
    return tags


def extract_element_vector(item: dict[str, Any]) -> dict[str, int]:
    text_keys = [
        "statement", "claim", "conclusion", "title", "topic", "topic_label",
        "trigger_conditions", "adjustment_mechanism", "conditions", "source", "output",
    ]
    text_parts: list[str] = []
    for key in text_keys:
        text_parts.extend(flatten_strings(item.get(key)))
    text = "\n".join(text_parts)
    return {name: 1 if any(token in text for token in tokens) else 0 for name, tokens in ELEMENT_TOKENS.items()}


def mismatch_for_item(item: dict[str, Any]) -> list[str]:
    out: list[str] = []
    if not item.get("id"):
        out.append("missing_id")
    if not extract_statement(item):
        out.append("missing_statement_claim_conclusion_output_statement_title")
    if not (item.get("school") or item.get("expert_system")):
        out.append("missing_theory_identifier_field")
    if not (item.get("domain") or item.get("domains") or item.get("prediction_target")):
        out.append("missing_explicit_domain_field")
    return out


def make_ir(path: Path, item: dict[str, Any], index: int) -> dict[str, Any]:
    rule_id = str(item.get("id") or f"{path.parent.name.upper()}-UNKEYED-{index:04d}")
    status = str(item.get("status") or "active")
    return {
        "rule_id": rule_id,
        "theory_id": theory_id_for(path, item),
        "source_path": path.as_posix(),
        "statement": extract_statement(item),
        "semantic_tags": extract_tags(item),
        "domain": extract_domains(item),
        "element_vector": extract_element_vector(item),
        "status": status,
        "original_format": item,
    }


def main() -> None:
    ir_rules: list[dict[str, Any]] = []
    report: dict[str, Any] = {
        "schema_version": "theory-alignment-report-2026-06-13",
        "normalization_scope": [p.as_posix() for p in INPUT_FILES],
        "constraints": {
            "no_inference": True,
            "no_conflict_analysis": True,
            "no_family_clustering": True,
            "no_rule_merge": True,
            "preserve_original_format": True,
        },
        "field_mapping": {
            "rule_id": "id or generated fallback when id missing",
            "theory_id": "school or expert_system or parent directory name",
            "statement": "statement > claim > conclusion > output.statement > title",
            "semantic_tags": "explicit structural fields only: topic/topic_label/rule_type/axis_refs/layer/canon/raw_anchor",
            "domain": "explicit domain/domains/prediction_target normalized to 财/官/印/婚姻/健康/性格 where literal mapping exists",
            "element_vector": "literal element/stem/branch token presence only, binary 0/1; no strength inference",
            "status": "source status or active fallback",
            "original_format": "complete original rule mapping preserved",
        },
        "theories": [],
        "totals": {},
    }
    totals = Counter()
    for path in INPUT_FILES:
        data = load_yaml(path)
        records, top_mismatch, fmt = extract_records(path, data)
        theory_key = path.parent.name
        converted = 0
        item_mismatches: Counter[str] = Counter(top_mismatch)
        ids = Counter()
        for idx, item in enumerate(records, start=1):
            ids[str(item.get("id") or f"__missing_{idx}")] += 1
            mismatches = mismatch_for_item(item)
            item_mismatches.update(mismatches)
            ir = make_ir(path, item, idx)
            ir_rules.append(ir)
            converted += 1
        duplicate_ids = sorted([rid for rid, count in ids.items() if count > 1])
        if duplicate_ids:
            item_mismatches["duplicate_rule_id"] += len(duplicate_ids)
        total = len(records)
        success_rate = round(converted / total, 6) if total else 0.0
        can_enter = converted == total and "missing_id" not in item_mismatches and "missing_statement_claim_conclusion_output_statement_title" not in item_mismatches
        schema_mismatch_points = []
        if fmt != "mapping_with_rules_list":
            schema_mismatch_points.append(f"top_level_format:{fmt}")
        if theory_key in {"duan", "gao", "yang", "ren"}:
            schema_mismatch_points.append("blind_school_index_lacks_explicit_domain_on_many_rules")
        if theory_key == "tiaohou_ditiansui":
            schema_mismatch_points.append("top_level_is_list_of_Rule_wrappers_not_production_rules_mapping")
        for name, count in sorted(item_mismatches.items()):
            schema_mismatch_points.append(f"{name}:{count}")
        report["theories"].append({
            "theory_id": theory_key,
            "source_path": path.as_posix(),
            "detected_rule_format": fmt,
            "source_rule_count": total,
            "converted_rule_count": converted,
            "conversion_success_rate": success_rate,
            "schema_mismatch_points": schema_mismatch_points,
            "can_enter_unified_inference_layer": bool(can_enter),
            "blocking_reasons": [] if can_enter else [
                reason for reason in schema_mismatch_points
                if reason.startswith("missing_id") or reason.startswith("missing_statement") or reason.startswith("top_level_unsupported")
            ] or ["structural_mismatch_requires_loader_adapter_but_ir_records_are_available"],
        })
        totals["source_rule_count"] += total
        totals["converted_rule_count"] += converted
    report["totals"] = {
        "source_rule_count": totals["source_rule_count"],
        "converted_rule_count": totals["converted_rule_count"],
        "conversion_success_rate": round(totals["converted_rule_count"] / totals["source_rule_count"], 6) if totals["source_rule_count"] else 0.0,
        "ir_rule_count": len(ir_rules),
    }
    out_dir = Path("theory/_ir")
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "unified_rule_ir.yaml").write_text(
        yaml.safe_dump({"schema_version": "RuleIR-2026-06-13", "rules": ir_rules}, allow_unicode=True, sort_keys=False, width=120),
        encoding="utf-8",
    )
    (out_dir / "theory_alignment_report.yaml").write_text(
        yaml.safe_dump(report, allow_unicode=True, sort_keys=False, width=120),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()

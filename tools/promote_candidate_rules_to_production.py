from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


SPECS = [
    (
        "ziping",
        Path("theory/raw/yaml/ziping_candidate_rules_2026-06-05.yaml"),
        Path("theory/ziping/index.yaml"),
        "ZP-CAND-",
        "ZP-PROD-",
        "子平",
    ),
    (
        "tiaohou_ditiansui",
        Path("theory/raw/yaml/tiaohou_ditiansui_candidate_rules_2026-06-05.yaml"),
        Path("theory/tiaohou_ditiansui/index.yaml"),
        "DTS-CAND-",
        "DTS-PROD-",
        "滴天髓",
    ),
]


def _trigger_for(rule: dict[str, Any], expert_system: str) -> str:
    title = str(rule.get("title", ""))
    topic = str(rule.get("topic", ""))
    claim = str(rule.get("claim", ""))
    domains = [str(x) for x in rule.get("domains", [])]

    trigger = "always"
    if "财富" in domains or "wealth" in topic or "财" in title:
        trigger = "has_wealth_picture"
    if "婚姻" in domains or "marriage" in topic or "夫妻" in title:
        trigger = "has_marriage_picture"
    if "官名" in domains or "official" in topic or "官" in title or "杀" in title:
        trigger = "has_official_picture"
    if expert_system == "tiaohou_ditiansui" and (
        "调候" in title or "寒" in claim or "燥" in claim or "湿" in claim
    ):
        trigger = "has_tiaohou_advice"
    if "冲" in title or "冲" in claim:
        trigger = "has_zhi_chong"
    return trigger


def _promote_rule(rule: dict[str, Any], *, expert_system: str, old_prefix: str, new_prefix: str, label: str) -> dict[str, Any]:
    promoted = dict(rule)
    promoted["id"] = str(promoted["id"]).replace(old_prefix, new_prefix, 1)
    promoted["status"] = "active"
    promoted["expert_system"] = expert_system
    promoted["layer"] = promoted.get("layer", "互补")

    raw_conditions = dict(promoted.get("conditions") or {})
    promoted["conditions"] = {
        "trigger": _trigger_for(promoted, expert_system),
        "required": raw_conditions.get("required", []),
        "optional": raw_conditions.get("optional", []),
        "exclusions": raw_conditions.get("exclusions", []),
    }

    output = dict(promoted.get("output") or {})
    statement = str(output.get("statement", "")).strip()
    prefix = f"{label}规则参与："
    if statement and not statement.startswith(prefix):
        output["statement"] = prefix + statement
    output["falsifiable"] = str(
        output.get("falsifiable", "若该候选理论在案例反馈中持续不应验，则本规则需降权或退回审查。")
    )
    promoted["output"] = output

    promoted["confidence"] = {
        "star": 4,
        "percent": 0.72,
        "posterior": 0.72,
        "variance": 0.06,
        "sample_n": 1,
    }

    review = dict(promoted.get("review") or {})
    original_notes = str(review.get("notes", ""))
    review["notes"] = f"由候选规则批量提升为生产生成规则；原审查备注：{original_notes}"
    promoted["review"] = review
    return promoted


def main() -> None:
    for expert_system, source_path, target_path, old_prefix, new_prefix, label in SPECS:
        candidate_payload = yaml.safe_load(source_path.read_text(encoding="utf-8"))
        rules = [
            _promote_rule(
                rule,
                expert_system=expert_system,
                old_prefix=old_prefix,
                new_prefix=new_prefix,
                label=label,
            )
            for rule in candidate_payload.get("rules", [])
        ]
        production_payload = {
            "schema_version": "production-rules-2026-06-07",
            "status": "active",
            "source_scope": "production_rules",
            "expert_system": expert_system,
            "notes": "由旁路候选规则批量提升为正式生产生成规则；所有 candidate 均转为 active，可被默认 pipeline 与双引擎理论层加载。",
            "rules": rules,
        }
        target_path.write_text(
            yaml.safe_dump(production_payload, allow_unicode=True, sort_keys=False, width=1000),
            encoding="utf-8",
        )
        print(f"{target_path.as_posix()}={len(rules)}")


if __name__ == "__main__":
    main()

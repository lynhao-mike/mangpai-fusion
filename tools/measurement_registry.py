"""校验 CHART_L2 → 现实测量注册表的准入边界。

该工具只读取机器可读注册表和候选 Measurement Spec，不创建映射、不修改
taxonomy、不读取案例现实结果。它的核心职责是失败关闭：未批准、未冻结或
缺少现实 falsifier 的候选不能被标记为 pilot eligible。

示例：
    py -3 -m tools.measurement_registry --format markdown
    py -3 -m tools.measurement_registry --check
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
REGISTRY_PATH = ROOT / "mapping" / "chart-l2-measurement-registry-v1.json"

ALLOWED_MAPPING_TYPES = {"DIRECT", "RANGE", "CONDITIONAL", "COMPOSITE", "NO_MAPPING"}
ALLOWED_MAPPING_STATUSES = {"UNRESOLVED", "PROPOSED", "FROZEN", "REJECTED"}


class MeasurementRegistryError(ValueError):
    """Raised when the measurement registry violates its fail-closed contract."""


def _read_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise MeasurementRegistryError(f"missing file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise MeasurementRegistryError(f"invalid JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise MeasurementRegistryError(f"JSON object required: {path}")
    return value


def load_registry(path: Path = REGISTRY_PATH) -> dict[str, Any]:
    registry = _read_object(path)
    if registry.get("schema_version") != "chart-l2-measurement-registry-v1":
        raise MeasurementRegistryError("unsupported registry schema_version")
    if registry.get("registry_status") not in {"PROPOSAL_ONLY", "ACTIVE"}:
        raise MeasurementRegistryError("invalid registry_status")
    if set(registry.get("mapping_types", [])) != ALLOWED_MAPPING_TYPES:
        raise MeasurementRegistryError("registry mapping_types must match the governance set")
    if set(registry.get("mapping_statuses", [])) != ALLOWED_MAPPING_STATUSES:
        raise MeasurementRegistryError("registry mapping_statuses must match the governance set")
    entries = registry.get("entries")
    if not isinstance(entries, list) or not entries:
        raise MeasurementRegistryError("registry entries must be a non-empty list")
    seen: set[str] = set()
    for entry in entries:
        _validate_entry(entry, seen)
    return registry


def _validate_entry(entry: Any, seen: set[str]) -> None:
    if not isinstance(entry, dict):
        raise MeasurementRegistryError("each registry entry must be an object")
    entry_id = entry.get("chart_l2_id")
    if not isinstance(entry_id, str) or not entry_id.strip() or entry_id in seen:
        raise MeasurementRegistryError(f"invalid or duplicate chart_l2_id: {entry_id!r}")
    seen.add(entry_id)
    mapping_type = entry.get("mapping_type")
    if mapping_type is not None and mapping_type not in ALLOWED_MAPPING_TYPES:
        raise MeasurementRegistryError(f"invalid mapping_type for {entry_id}: {mapping_type!r}")
    mapping_status = entry.get("mapping_status")
    if mapping_status not in ALLOWED_MAPPING_STATUSES:
        raise MeasurementRegistryError(f"invalid mapping_status for {entry_id}: {mapping_status!r}")
    spec_path = entry.get("measurement_spec")
    if not isinstance(spec_path, str) or not (ROOT / spec_path).is_file():
        raise MeasurementRegistryError(f"measurement_spec missing for {entry_id}: {spec_path!r}")
    spec = _read_object(ROOT / spec_path)
    if spec.get("spec_status") not in {"DRAFT", "APPROVED", "REJECTED"}:
        raise MeasurementRegistryError(f"invalid spec_status for {entry_id}")
    if spec.get("mapping_status") != mapping_status:
        raise MeasurementRegistryError(f"registry/spec mapping_status mismatch for {entry_id}")
    if spec.get("mapping_type") != mapping_type:
        raise MeasurementRegistryError(f"registry/spec mapping_type mismatch for {entry_id}")
    if bool(entry.get("frozen")) != bool(spec.get("frozen")):
        raise MeasurementRegistryError(f"registry/spec frozen mismatch for {entry_id}")
    pilot_eligible = bool(entry.get("pilot_eligible"))
    if pilot_eligible:
        required = (
            mapping_status == "FROZEN",
            mapping_type is not None,
            entry.get("approval_status") == "APPROVED",
            bool(entry.get("frozen")),
            spec.get("approval_status") == "APPROVED",
            spec.get("observation", {}).get("status") == "FROZEN",
            spec.get("scoring", {}).get("status") == "FROZEN",
            spec.get("falsifier", {}).get("status") == "FROZEN",
            bool(spec.get("falsifier", {}).get("reality_falsifier")),
        )
        if not all(required):
            raise MeasurementRegistryError(f"pilot eligible entry is not fully frozen: {entry_id}")
    if mapping_status == "UNRESOLVED" and (mapping_type is not None or pilot_eligible or entry.get("frozen")):
        raise MeasurementRegistryError(f"UNRESOLVED entry must remain unfrozen and non-pilot: {entry_id}")


def load_report(path: Path = REGISTRY_PATH) -> dict[str, Any]:
    registry = load_registry(path)
    entries = registry["entries"]
    return {
        "schema_version": registry["schema_version"],
        "registry_status": registry["registry_status"],
        "entries": [
            {
                "chart_l2_id": entry["chart_l2_id"],
                "wording": entry["wording"],
                "mapping_status": entry["mapping_status"],
                "mapping_type": entry["mapping_type"],
                "candidate_outcome_indicators": entry.get("candidate_outcome_indicators", []),
                "frozen": bool(entry.get("frozen")),
                "pilot_eligible": bool(entry.get("pilot_eligible")),
            }
            for entry in entries
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# CHART_L2 → 现实测量注册表状态",
        "",
        f"> 注册表状态：`{report['registry_status']}`；schema：`{report['schema_version']}`。",
        "> 本表只登记候选和准入状态，不产生理论结论、现实结果或 pilot 标签。",
        "",
        "| CHART_L2 | 现有候选指标 | Mapping Status | Mapping Type | 冻结 | Pilot |",
        "|---|---|---|---|---|---|",
    ]
    for entry in report["entries"]:
        indicators = "、".join(entry["candidate_outcome_indicators"]) or "—"
        lines.append(
            f"| `{entry['chart_l2_id']}` {entry['wording']} | {indicators} | "
            f"`{entry['mapping_status']}` | `{entry['mapping_type'] or 'NOT_ASSIGNED'}` | "
            f"{str(entry['frozen']).lower()} | {str(entry['pilot_eligible']).lower()} |"
        )
    lines.extend([
        "",
        "## 失败关闭规则",
        "",
        "- `UNRESOLVED` 不得带有 Mapping Type、冻结状态或 pilot 资格。",
        "- 只有批准、冻结且具备观察、评分和现实 falsifier 的 Measurement Spec 才能进入 pilot。",
        "- 本注册表不允许用学历、能力或任一单字段替代未完成的语义测量定义。",
        "",
    ])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="校验 CHART_L2 现实测量注册表。")
    parser.add_argument("--format", choices=("json", "markdown"), default="markdown")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    try:
        report = load_report()
    except MeasurementRegistryError as exc:
        print(f"measurement registry check failed: {exc}", file=sys.stderr)
        return 1
    if args.check:
        print("measurement registry check passed")
        return 0
    if args.format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(render_markdown(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

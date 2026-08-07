"""跨案例多专家功能域反馈与 promotion 前置证据只读扫描器。"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Mapping

import yaml

ROOT = Path(__file__).resolve().parent.parent
EXPERT_FEEDBACK_LOG = ROOT / "engine" / "logs" / "expert_domain_feedback.jsonl"
ADJUDICATION_ACCURACY_LOG = ROOT / "engine" / "logs" / "adjudication_accuracy.jsonl"
CANONICAL_PROFILE = ROOT / "engine" / "expert-weights.yaml"


def _wilson_lower(hits: int, total: int, z: float = 1.96) -> float:
    if total <= 0:
        return 0.0
    phat = hits / total
    denominator = 1 + z * z / total
    centre = phat + z * z / (2 * total)
    margin = z * math.sqrt((phat * (1 - phat) + z * z / (4 * total)) / total)
    return max(0.0, (centre - margin) / denominator)


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            rows.append(payload)
    return rows


def aggregate_expert_domain_feedback(path: str | Path) -> list[dict[str, Any]]:
    """Aggregate every valid historical expert/domain feedback row in one JSONL."""

    buckets: dict[tuple[str, str], dict[str, int]] = defaultdict(
        lambda: {"hits": 0, "misses": 0}
    )
    for row in _read_jsonl(Path(path)):
        domain = str(row.get("domain", "")).strip()
        expert_system = str(row.get("expert_system", "")).strip()
        verdict = row.get("verdict")
        if not domain or not expert_system or verdict not in {"hit", "miss"}:
            continue
        buckets[(domain, expert_system)]["hits" if verdict == "hit" else "misses"] += 1

    items: list[dict[str, Any]] = []
    for (domain, expert_system), counts in sorted(buckets.items()):
        hits = counts["hits"]
        misses = counts["misses"]
        n_eff = hits + misses
        items.append(
            {
                "domain": domain,
                "expert_system": expert_system,
                "hits": hits,
                "misses": misses,
                "n_eff": float(n_eff),
                "beta_mean": round((hits + 1) / (n_eff + 2), 6),
                "wilson_lower": round(_wilson_lower(hits, n_eff), 6),
            }
        )
    return items


def _load_profile(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expert weight profile 顶层必须是 mapping：{path}")
    if payload.get("schema_version") != "expert-weight-profile/v1":
        raise ValueError("只支持 expert-weight-profile/v1 profile。")
    if not isinstance(payload.get("feedback_overlay"), Mapping):
        raise ValueError("profile 缺少 feedback_overlay mapping。")
    return payload


def _minimum_effective_sample(profile: Mapping[str, Any]) -> float:
    overlay = profile.get("feedback_overlay", {})
    constraints = profile.get("constraints", {})
    raw_value = None
    if isinstance(overlay, Mapping):
        raw_value = overlay.get("min_effective_sample_for_adjustment")
    if raw_value is None and isinstance(constraints, Mapping):
        raw_value = constraints.get("min_effective_sample_for_adjustment")
    try:
        threshold = float(raw_value)
    except (TypeError, ValueError) as exc:
        raise ValueError("profile 缺少有效的 min_effective_sample_for_adjustment。") from exc
    if threshold <= 0:
        raise ValueError("min_effective_sample_for_adjustment 必须大于 0。")
    return threshold


def _overlay_entries(profile: Mapping[str, Any]) -> list[dict[str, Any]]:
    overlay = profile["feedback_overlay"]
    entries: list[dict[str, Any]] = []
    for raw in overlay.get("entries", []) or []:
        if not isinstance(raw, Mapping):
            continue
        domain = str(raw.get("domain", "")).strip()
        expert_system = str(raw.get("expert_system", "")).strip()
        if not domain or not expert_system:
            continue
        try:
            n_eff = float(raw.get("n_eff", 0))
        except (TypeError, ValueError):
            n_eff = 0.0
        entries.append(
            {"domain": domain, "expert_system": expert_system, "n_eff": n_eff}
        )
    return sorted(entries, key=lambda item: (item["domain"], item["expert_system"]))


def build_status_report(
    *,
    expert_log_path: str | Path,
    adjudication_log_path: str | Path,
    profile_path: str | Path,
) -> dict[str, Any]:
    """Build a read-only cross-case status report from logs and canonical profile."""

    profile = _load_profile(Path(profile_path))
    threshold = _minimum_effective_sample(profile)
    aggregated = aggregate_expert_domain_feedback(expert_log_path)
    entries = _overlay_entries(profile)
    overlay_by_key = {
        (item["domain"], item["expert_system"]): item["n_eff"] for item in entries
    }
    pending: list[dict[str, Any]] = []
    for item in aggregated:
        log_n_eff = float(item["n_eff"])
        if log_n_eff < threshold:
            continue
        key = (item["domain"], item["expert_system"])
        overlay_n_eff = overlay_by_key.get(key)
        if overlay_n_eff is None or log_n_eff > overlay_n_eff:
            pending.append(
                {
                    "domain": item["domain"],
                    "expert_system": item["expert_system"],
                    "log_n_eff": log_n_eff,
                    "overlay_n_eff": overlay_n_eff,
                    "reason": (
                        "missing_overlay_entry"
                        if overlay_n_eff is None
                        else "overlay_n_eff_behind_log"
                    ),
                }
            )

    adjudication_rows = _read_jsonl(Path(adjudication_log_path))
    valid_adjudication_rows = sum(
        1
        for row in adjudication_rows
        if row.get("verdict") in {"hit", "miss"}
        and str(row.get("domain", "")).strip()
    )
    overlay = profile["feedback_overlay"]
    return {
        "schema_version": "parallel-domain-weight-status/v1",
        "min_effective_sample_for_adjustment": threshold,
        "expert_domain_stats": aggregated,
        "expert_feedback_valid_rows": int(
            sum(item["hits"] + item["misses"] for item in aggregated)
        ),
        "adjudication_accuracy_rows": len(adjudication_rows),
        "adjudication_accuracy_valid_rows": valid_adjudication_rows,
        "feedback_overlay": {
            "version": str(overlay.get("version", "")),
            "entry_count": len(entries),
            "entries": entries,
        },
        "pending_promotion_review": pending,
        "pending_promotion_review_count": len(pending),
    }


def _stats_table(items: list[dict[str, Any]]) -> list[str]:
    lines = [
        "| domain | expert_system | hits | misses | N_eff | beta_mean | wilson_lower |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    if not items:
        lines.append("| — | — | — | — | — | — | — |")
    for item in items:
        lines.append(
            f"| {item['domain']} | {item['expert_system']} | {item['hits']} | "
            f"{item['misses']} | {item['n_eff']} | {item['beta_mean']} | "
            f"{item['wilson_lower']} |"
        )
    return lines


def _overlay_table(items: list[dict[str, Any]]) -> list[str]:
    lines = ["| domain | expert_system | overlay N_eff |", "|---|---|---:|"]
    if not items:
        lines.append("| — | — | — |")
    for item in items:
        lines.append(f"| {item['domain']} | {item['expert_system']} | {item['n_eff']} |")
    return lines


def _pending_table(items: list[dict[str, Any]]) -> list[str]:
    lines = [
        "| domain | expert_system | log N_eff | overlay N_eff | reason |",
        "|---|---|---:|---:|---|",
    ]
    if not items:
        lines.append("| — | — | — | — | — |")
    for item in items:
        overlay_n_eff = "—" if item["overlay_n_eff"] is None else item["overlay_n_eff"]
        lines.append(
            f"| {item['domain']} | {item['expert_system']} | {item['log_n_eff']} | "
            f"{overlay_n_eff} | {item['reason']} |"
        )
    return lines


def report_to_markdown(report: Mapping[str, Any]) -> str:
    overlay = report["feedback_overlay"]
    lines = [
        "# parallel domain weight status scan",
        "",
        f"- min_effective_sample_for_adjustment: {report['min_effective_sample_for_adjustment']}",
        f"- expert_feedback_valid_rows: {report['expert_feedback_valid_rows']}",
        f"- adjudication_accuracy_rows: {report['adjudication_accuracy_rows']}",
        f"- adjudication_accuracy_valid_rows: {report['adjudication_accuracy_valid_rows']}",
        f"- feedback_overlay.version: {overlay['version']}",
        f"- feedback_overlay.entry_count: {overlay['entry_count']}",
        f"- pending_promotion_review_count: {report['pending_promotion_review_count']}",
        "",
        "## expert × domain historical aggregation",
        "",
        *_stats_table(report["expert_domain_stats"]),
        "",
        "## feedback overlay entries",
        "",
        *_overlay_table(overlay["entries"]),
        "",
        "## pending_promotion_review",
        "",
        *_pending_table(report["pending_promotion_review"]),
        "",
        "> 只读前置证据；是否运行 promotion 由人工决定，本工具不会写入权重或切换路由。",
    ]
    return "\n".join(lines)


def report_to_json(report: Mapping[str, Any]) -> str:
    return json.dumps(dict(report), ensure_ascii=False, indent=2)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Scan cross-case expert/domain feedback and promotion review readiness."
    )
    parser.add_argument("--format", choices=("json", "markdown"), default="markdown")
    parser.add_argument(
        "--check",
        action="store_true",
        help="exit non-zero if pending_promotion_review items are found",
    )
    args = parser.parse_args(argv)

    report = build_status_report(
        expert_log_path=EXPERT_FEEDBACK_LOG,
        adjudication_log_path=ADJUDICATION_ACCURACY_LOG,
        profile_path=CANONICAL_PROFILE,
    )
    if args.check:
        pending = report["pending_promotion_review"]
        if pending:
            print("parallel domain weight status scan failed:", file=sys.stderr)
            for item in pending:
                overlay_n_eff = (
                    "missing" if item["overlay_n_eff"] is None else item["overlay_n_eff"]
                )
                print(
                    f"- {item['domain']} / {item['expert_system']}: "
                    f"log_n_eff={item['log_n_eff']}, overlay_n_eff={overlay_n_eff}, "
                    f"reason={item['reason']}",
                    file=sys.stderr,
                )
            return 1
        print("parallel domain weight status scan passed")
        return 0

    print(report_to_json(report) if args.format == "json" else report_to_markdown(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

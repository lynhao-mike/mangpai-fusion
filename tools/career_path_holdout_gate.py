"""职业路径未见 holdout 的准入门禁。

只校验数据隔离、标签复核和预注册状态；不运行模型、不生成评分、不修改生产入口。
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any
import re

from engine.infrastructure.file_digest import compare_digest, digest_diagnostics

DEFAULT_REGISTRY = Path("META/as-of-evaluation/career-path-dataset-registry-v1.json")
DEFAULT_PREREGISTRATION = Path(
    "META/as-of-evaluation/career-path-holdout-preregistration-v1.json"
)
_BINARY_LABELS = {"employment", "entrepreneurship"}
_RETAINED_LABELS = _BINARY_LABELS | {"mixed", "unknown"}
_ALLOWED_REVIEW_STATUSES = {"double_review_agreed", "adjudicated"}
_HUMAN_ID = re.compile(r"^human-[A-Za-z0-9][A-Za-z0-9._-]*$")


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"JSONL line {number} is not an object: {path}")
        rows.append(value)
    return rows


def _timestamp(value: Any, field: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be an ISO-8601 timestamp")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError(f"{field} must include a timezone")
    return parsed


def _development_ids(registry: dict[str, Any]) -> set[str]:
    datasets = registry.get("development_datasets")
    if not isinstance(datasets, list):
        raise ValueError("registry.development_datasets must be a list")
    result: set[str] = set()
    for dataset in datasets:
        if not isinstance(dataset, dict):
            raise ValueError("development dataset must be an object")
        if dataset.get("classification") != "development_replay_only":
            raise ValueError("development dataset must be development_replay_only")
        if dataset.get("promotion_eligible") is not False or dataset.get("holdout_eligible") is not False:
            raise ValueError("development dataset must be excluded from promotion and holdout")
        case_ids = dataset.get("case_ids")
        if not isinstance(case_ids, list) or any(not isinstance(case_id, str) for case_id in case_ids):
            raise ValueError("development dataset case_ids must be strings")
        result.update(case_ids)
    return result


def _review_is_valid(row: dict[str, Any]) -> bool:
    status = row.get("review_status")
    reviewers = row.get("reviewers")
    if status not in _ALLOWED_REVIEW_STATUSES:
        return False
    if not isinstance(reviewers, list) or len(reviewers) != 2:
        return False
    if any(not isinstance(reviewer, str) or not _HUMAN_ID.fullmatch(reviewer) for reviewer in reviewers):
        return False
    if len(set(reviewers)) != 2:
        return False
    if status == "double_review_agreed":
        reviewer_labels = row.get("reviewer_labels")
        return reviewer_labels is None or reviewer_labels == [row.get("label"), row.get("label")]
    reviewer_labels = row.get("reviewer_labels")
    adjudicator = row.get("adjudicator")
    return (
        isinstance(reviewer_labels, list)
        and len(reviewer_labels) == 2
        and all(label in _RETAINED_LABELS for label in reviewer_labels)
        and reviewer_labels[0] != reviewer_labels[1]
        and isinstance(adjudicator, str)
        and bool(_HUMAN_ID.fullmatch(adjudicator))
        and adjudicator not in reviewers
        and row.get("adjudicated_label") == row.get("label")
    )


def _result(
    status: str,
    checks: dict[str, bool],
    failures: list[str],
    *,
    metrics: dict[str, Any] | None = None,
    diagnostics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "status": status,
        "ready": status == "ready",
        "checks": checks,
        "metrics": metrics or {},
        "failures": failures,
        "diagnostics": diagnostics or {},
    }


def check_holdout_admission(
    manifest_path: Path | None,
    labels_path: Path | None,
    registry_path: Path = DEFAULT_REGISTRY,
    preregistration_path: Path = DEFAULT_PREREGISTRATION,
) -> dict[str, Any]:
    """校验候选 holdout；材料尚未登记时返回 ``not_ready``。"""
    check_names = (
        "registry_development_exclusion",
        "preregistration_frozen",
        "preregistration_state_allows_admission",
        "labels_not_revealed",
        "one_shot_freeze",
        "preregistration_precedes_manifest",
        "unique_case_ids",
        "development_set_disjoint",
        "manifest_ids_match_labels",
        "strict_binary_labels",
        "minimum_strict_binary_cases",
        "minimum_cases_per_class",
        "labels_double_reviewed_or_adjudicated",
        "labels_hash_matches_manifest",
    )
    checks = {name: False for name in check_names}
    diagnostics: dict[str, Any] = {}
    try:
        registry_path = Path(registry_path)
        preregistration_path = Path(preregistration_path)
        registry = _read_json(registry_path)
        preregistration = _read_json(preregistration_path)
        development_ids = _development_ids(registry)
        checks["registry_development_exclusion"] = True

        models = preregistration.get("models")
        metrics = preregistration.get("metrics")
        thresholds = preregistration.get("promotion_thresholds")
        freeze_policy = preregistration.get("freeze_policy")
        checks["preregistration_frozen"] = (
            isinstance(models, list)
            and len(models) == 3
            and isinstance(metrics, list)
            and bool(metrics)
            and isinstance(thresholds, dict)
            and bool(thresholds)
            and isinstance(freeze_policy, dict)
            and freeze_policy.get("one_shot_freeze") is True
            and freeze_policy.get("one_score_only") is True
            and freeze_policy.get("post_label_tuning_permitted") is False
        )
        checks["labels_not_revealed"] = preregistration.get("labels_revealed") is False
        if not checks["preregistration_frozen"]:
            return _result("rejected", checks, ["preregistration_frozen"])
        if not checks["labels_not_revealed"]:
            return _result("rejected", checks, ["labels_not_revealed"])

        if manifest_path is None or labels_path is None:
            checks["preregistration_state_allows_admission"] = (
                preregistration.get("status") == "awaiting_unseen_holdout"
                and preregistration.get("holdout_ready") is False
            )
            if not checks["preregistration_state_allows_admission"]:
                return _result("rejected", checks, ["preregistration_state_allows_admission"])
            return _result("not_ready", checks, ["unseen_holdout_not_registered"])
        checks["preregistration_state_allows_admission"] = (
            preregistration.get("status") == "holdout_frozen_awaiting_predictions"
            and preregistration.get("holdout_ready") is True
        )
        if not checks["preregistration_state_allows_admission"]:
            return _result("rejected", checks, ["preregistration_state_allows_admission"])
        manifest_path = Path(manifest_path)
        labels_path = Path(labels_path)
        if not manifest_path.exists() or not labels_path.exists():
            return _result("not_ready", checks, ["unseen_holdout_artifacts_missing"])

        manifest = _read_json(manifest_path)
        rows = _read_jsonl(labels_path)
        checks["labels_not_revealed"] = (
            checks["labels_not_revealed"] and manifest.get("labels_revealed") is False
        )
        checks["one_shot_freeze"] = manifest.get("one_shot_freeze") is True
        checks["preregistration_precedes_manifest"] = _timestamp(
            preregistration.get("registered_at"), "registered_at"
        ) <= _timestamp(manifest.get("frozen_at"), "frozen_at")

        case_ids = manifest.get("case_ids")
        if not isinstance(case_ids, list) or any(not isinstance(case_id, str) for case_id in case_ids):
            raise ValueError("manifest.case_ids must be a list of strings")
        checks["unique_case_ids"] = len(case_ids) == len(set(case_ids))
        checks["development_set_disjoint"] = not (set(case_ids) & development_ids)

        label_ids = [row.get("case_id") for row in rows]
        labels = [row.get("label") for row in rows]
        checks["manifest_ids_match_labels"] = (
            all(isinstance(case_id, str) for case_id in label_ids)
            and len(label_ids) == len(set(label_ids))
            and set(case_ids) == set(label_ids)
            and manifest.get("case_count") == len(case_ids)
        )
        checks["strict_binary_labels"] = all(label in _RETAINED_LABELS for label in labels)
        counts = Counter(label for label in labels if label in _BINARY_LABELS)
        strict_binary_count = sum(counts.values())
        minimum_cases = int(preregistration.get("minimum_strict_binary_cases", 30))
        minimum_per_class = int(preregistration.get("minimum_cases_per_class", 10))
        checks["minimum_strict_binary_cases"] = strict_binary_count >= minimum_cases
        checks["minimum_cases_per_class"] = all(
            counts[label] >= minimum_per_class for label in _BINARY_LABELS
        )
        checks["labels_double_reviewed_or_adjudicated"] = all(
            _review_is_valid(row) for row in rows
        )
        expected_hash = manifest.get("labels_sha256")
        label_digest = compare_digest(labels_path, expected_hash)
        checks["labels_hash_matches_manifest"] = label_digest != "mismatch"
        if label_digest != "match":
            # 记录判定详情：行尾假漂移与真漂移必须可区分，否则「Windows 上
            # 突然不 ready」无法诊断（KB-001）。
            diagnostics["labels_digest"] = digest_diagnostics(labels_path, expected_hash)

        metrics_result = {
            "retained_cases": len(rows),
            "strict_binary_cases": strict_binary_count,
            "employment_cases": counts["employment"],
            "entrepreneurship_cases": counts["entrepreneurship"],
            "nonbinary_retained_cases": len(rows) - strict_binary_count,
            "development_overlap_count": len(set(case_ids) & development_ids),
        }
        failures = [name for name, passed in checks.items() if not passed]
        if not failures:
            return _result("ready", checks, [], metrics=metrics_result, diagnostics=diagnostics)
        not_ready_checks = {"minimum_strict_binary_cases", "minimum_cases_per_class"}
        status = "not_ready" if set(failures).issubset(not_ready_checks) else "rejected"
        return _result(status, checks, failures, metrics=metrics_result, diagnostics=diagnostics)
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        return _result("rejected", checks, [f"invalid_gate_input:{exc}"], diagnostics=diagnostics)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--labels", type=Path)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--preregistration", type=Path, default=DEFAULT_PREREGISTRATION)
    args = parser.parse_args(argv)
    result = check_holdout_admission(
        args.manifest, args.labels, args.registry, args.preregistration
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

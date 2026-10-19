"""职业路径分类器的离线 promotion 门禁。

门禁从冻结预测和人工标签重新计算指标；不信任外部预计算分数，也不修改模型、
预测、标签、生产规则或路由。
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from engine.infrastructure.file_digest import (
    MISMATCH,
    compare_digest,
    digest_diagnostics,
)


PROMOTION_REQUIREMENTS = {
    "min_holdout_cases": 30,
    "min_balanced_accuracy": 0.60,
    "min_employment_recall": 0.55,
    "min_entrepreneurship_recall": 0.55,
    "min_coverage": 0.70,
    "beats_majority_baseline": True,
    "beats_frozen_baseline_balanced_acc": 0.425,
    "one_shot_freeze_required": True,
}

_BINARY = {"employment", "entrepreneurship"}
_NON_BINARY = {"mixed", "transitioning"}
_PREDICTIONS = _BINARY | _NON_BINARY | {"abstain"}
_LABEL_SCHEMAS = {"legacy_label_v1", "career_path_temporal_v1"}


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


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _hash_verdict(predictions_path: Path, recorded_sha: object) -> tuple[bool, str]:
    """比对预测文件与冻结记录的 hash，区分「真漂移」与「行尾假漂移」。

    返回 (passed, reason)。passed 为 False 时 reason 说明失败性质，便于门禁
    输出可诊断信息而不是笼统的 false。
    行尾语义见 KB-001 与 ``engine.infrastructure.file_digest``。
    """
    verdict = compare_digest(predictions_path, recorded_sha)
    if verdict == MISMATCH:
        return False, "content_mismatch"
    # match / match_eol_normalized / match_crlf_recorded 均视为通过
    return True, verdict


def _failed_result(
    checks: dict[str, bool], reason: str, diagnostics: dict[str, Any] | None = None
) -> dict[str, Any]:
    return {
        "eligible": False,
        "requirements": dict(PROMOTION_REQUIREMENTS),
        "metrics": {},
        "checks": checks,
        "failures": [reason],
        "diagnostics": diagnostics or {},
    }


def _labels_by_schema(
    rows: list[dict[str, Any]], label_schema: str
) -> tuple[dict[str, str], dict[str, dict[str, Any]]]:
    """按调用方显式声明的 schema 解析标签；绝不依据字段猜测。"""
    if label_schema not in _LABEL_SCHEMAS:
        raise ValueError(f"unknown label schema: {label_schema}")
    field = "label" if label_schema == "legacy_label_v1" else "reality_status_at_feedback"
    mapping = {
        "employment": "employment",
        "entrepreneurship": "entrepreneurship",
        "employed": "employment",
        "entrepreneurial": "entrepreneurship",
        "mixed": "mixed",
        "transitioning": "transitioning",
        "unknown": None,
    }
    labels: dict[str, str] = {}
    source: dict[str, dict[str, Any]] = {}
    seen_ids: set[str] = set()
    for row in rows:
        case_id = row.get("case_id")
        raw = row.get(field)
        if not isinstance(case_id, str) or raw not in mapping:
            raise ValueError(f"invalid {label_schema} label row")
        if case_id in seen_ids:
            raise ValueError("duplicate case_id")
        seen_ids.add(case_id)
        normalized = mapping[str(raw)]
        if normalized is None:
            continue
        labels[case_id] = normalized
        source[case_id] = row
    return labels, source


def check_promotion_eligibility(
    predictions_path: Path,
    labels_path: Path,
    freeze_path: Path,
    *,
    label_schema: str = "legacy_label_v1",
) -> dict[str, Any]:
    """重新计算冻结 holdout 指标并返回可审计的 promotion 决策。

    ``label_schema`` 必须由调用方显式选择；默认值只用于保持旧 ``label``
    调用兼容，正式时序标签必须传 ``career_path_temporal_v1``。
    """
    predictions_path = Path(predictions_path)
    labels_path = Path(labels_path)
    freeze_path = Path(freeze_path)
    check_names = (
        "predictions_hash_matches_freeze",
        "prediction_ids_match_labels",
        "min_holdout_cases",
        "min_balanced_accuracy",
        "min_employment_recall",
        "min_entrepreneurship_recall",
        "min_coverage",
        "beats_majority_baseline",
        "beats_frozen_baseline_balanced_acc",
        "one_shot_freeze_required",
    )
    checks = {name: False for name in check_names}
    diagnostics: dict[str, Any] = {}

    try:
        freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
        if not isinstance(freeze, dict):
            raise ValueError("freeze must be a JSON object")
        hash_ok, hash_reason = _hash_verdict(
            predictions_path, freeze.get("predictions_sha256")
        )
        checks["predictions_hash_matches_freeze"] = hash_ok
        diagnostics["predictions_hash_reason"] = hash_reason
        if not hash_ok:
            # 记录失败性质后继续计算真实指标：调用方需要可引用的 balanced_accuracy，
            # 而不是被提前 return 丢弃成空 metrics（历史 bug：测试断言
            # metrics["balanced_accuracy"] 时 KeyError）。可审计性优先于静默。
            diagnostics["predictions_digest"] = digest_diagnostics(
                predictions_path, freeze.get("predictions_sha256")
            )
        checks["one_shot_freeze_required"] = (
            freeze.get("one_shot_freeze") is True
            if PROMOTION_REQUIREMENTS["one_shot_freeze_required"]
            else True
        )
        if not checks["predictions_hash_matches_freeze"]:
            return _failed_result(checks, "predictions_hash_matches_freeze", diagnostics)

        prediction_rows = _read_jsonl(predictions_path)
        label_rows = _read_jsonl(labels_path)
        predictions = {str(row["case_id"]): str(row["prediction"]) for row in prediction_rows}
        labels, label_sources = _labels_by_schema(label_rows, label_schema)
        if len(predictions) != len(prediction_rows):
            raise ValueError("duplicate case_id")
        if any(value not in _PREDICTIONS for value in predictions.values()):
            raise ValueError("invalid prediction enum")
        checks["prediction_ids_match_labels"] = set(predictions) == set(labels)
        if not checks["prediction_ids_match_labels"]:
            return _failed_result(checks, "prediction_ids_match_labels")
        strict_ids = [case_id for case_id, truth in labels.items() if truth in _BINARY]
        truth_counts = Counter(labels[case_id] for case_id in strict_ids)
        correct = sum(predictions[case_id] == labels[case_id] for case_id in strict_ids)
        covered = sum(predictions[case_id] != "abstain" for case_id in strict_ids)
        recalls = {
            truth: (
                sum(predictions[case_id] == truth for case_id in strict_ids if labels[case_id] == truth)
                / truth_counts[truth]
                if truth_counts[truth]
                else 0.0
            )
            for truth in sorted(_BINARY)
        }
        count = len(strict_ids)
        accuracy = correct / count if count else 0.0
        balanced_accuracy = sum(recalls.values()) / 2
        coverage = covered / count if count else 0.0
        majority_baseline = max(truth_counts.values(), default=0) / count if count else 0.0
        metrics = {
            "label_schema": label_schema,
            "holdout_cases": count,
            "mixed_holdout_cases": sum(truth == "mixed" for truth in labels.values()),
            "transitioning_holdout_cases": sum(
                truth == "transitioning" for truth in labels.values()
            ),
            "accuracy": accuracy,
            "balanced_accuracy": balanced_accuracy,
            "employment_recall": recalls["employment"],
            "entrepreneurship_recall": recalls["entrepreneurship"],
            "coverage": coverage,
            "majority_class_baseline_accuracy": majority_baseline,
        }
        for state in sorted(_NON_BINARY):
            state_ids = [case_id for case_id, truth in labels.items() if truth == state]
            if state_ids:
                metrics[f"{state}_recognition"] = {
                    "value": sum(predictions[case_id] == state for case_id in state_ids)
                    / len(state_ids),
                    "denominator": len(state_ids),
                }
        pillar_ids = [
            case_id
            for case_id, row in label_sources.items()
            if isinstance(row.get("career_pillar"), str)
        ]
        if pillar_ids:
            metrics["career_pillar_location_consistency"] = {
                "value": sum(
                    next(
                        item.get("career_pillar")
                        for item in prediction_rows
                        if str(item.get("case_id")) == case_id
                    )
                    == label_sources[case_id]["career_pillar"]
                    for case_id in pillar_ids
                )
                / len(pillar_ids),
                "denominator": len(pillar_ids),
            }
        trace_ids = [
            str(row["case_id"])
            for row in prediction_rows
            if row.get("model_id") == "career-path-relation-model-v1"
        ]
        if trace_ids:
            by_id = {str(row["case_id"]): row for row in prediction_rows}
            metrics["trace_completeness"] = {
                "value": sum(bool(by_id[case_id].get("trace")) for case_id in trace_ids)
                / len(trace_ids),
                "denominator": len(trace_ids),
            }

        checks["min_holdout_cases"] = count >= PROMOTION_REQUIREMENTS["min_holdout_cases"]
        checks["min_balanced_accuracy"] = balanced_accuracy >= PROMOTION_REQUIREMENTS["min_balanced_accuracy"]
        checks["min_employment_recall"] = recalls["employment"] >= PROMOTION_REQUIREMENTS["min_employment_recall"]
        checks["min_entrepreneurship_recall"] = recalls["entrepreneurship"] >= PROMOTION_REQUIREMENTS["min_entrepreneurship_recall"]
        checks["min_coverage"] = coverage >= PROMOTION_REQUIREMENTS["min_coverage"]
        checks["beats_majority_baseline"] = (
            accuracy > majority_baseline
            if PROMOTION_REQUIREMENTS["beats_majority_baseline"]
            else True
        )
        checks["beats_frozen_baseline_balanced_acc"] = (
            balanced_accuracy > PROMOTION_REQUIREMENTS["beats_frozen_baseline_balanced_acc"]
        )
        failures = [name for name, passed in checks.items() if not passed]
        return {
            "eligible": not failures,
            "requirements": dict(PROMOTION_REQUIREMENTS),
            "metrics": metrics,
            "checks": checks,
            "failures": failures,
            "diagnostics": diagnostics,
        }
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        return _failed_result(checks, f"invalid_gate_input:{exc}", diagnostics)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--labels", type=Path, required=True)
    parser.add_argument("--freeze", type=Path, required=True)
    parser.add_argument(
        "--label-schema", choices=sorted(_LABEL_SCHEMAS), default="legacy_label_v1"
    )
    args = parser.parse_args(argv)
    result = check_promotion_eligibility(
        args.predictions, args.labels, args.freeze, label_schema=args.label_schema
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["eligible"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

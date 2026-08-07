"""冻结职业路径竞争实验的只读产品分流控制。

本工具只消费已经存在的一次评分、receipt 与其冻结证据，不运行模型、不评分、
不创建 receipt，也永远不授权生产默认切换。任何缺失证据均失败关闭。
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Sequence

from tools.career_path_competition_harness import DEFAULT_MODEL_DISPOSITION
from tools.career_path_holdout_gate import DEFAULT_PREREGISTRATION, DEFAULT_REGISTRY, check_holdout_admission

INVALIDATED_MODEL_ID = "career-path-relation-model-v1"
_PRODUCT_STATES = {
    "blocked_not_ready",
    "shadow_candidate",
    "structural_evidence_assistant",
    "rejected",
}
_REQUIRED_TERMINAL_CHECKS = {
    "min_balanced_accuracy",
    "min_employment_recall",
    "min_entrepreneurship_recall",
    "min_coverage",
    "beats_majority_baseline",
    "beats_frozen_counting_baseline",
}


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON object required: {path}")
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _canonical_sha256(value: object) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _result(
    state: str,
    failures: list[str],
    checks: dict[str, bool],
    *,
    structural_status: str = "not_evaluable",
    model_id: str | None = None,
) -> dict[str, Any]:
    if state not in _PRODUCT_STATES:
        raise ValueError(f"unknown product route: {state}")
    return {
        "schema_version": "career-path-product-route/v1",
        "state": state,
        "model_id": model_id,
        "checks": checks,
        "failures": failures,
        "structural_evidence_status": structural_status,
        "shadow_use_permitted": state == "shadow_candidate",
        "assistant_use_permitted": state == "structural_evidence_assistant",
        "production_switch_permitted": False,
        "production_authorization_required": True,
    }


def repository_product_status(
    *,
    registry_path: Path = DEFAULT_REGISTRY,
    preregistration_path: Path = DEFAULT_PREREGISTRATION,
    disposition_path: Path = DEFAULT_MODEL_DISPOSITION,
) -> dict[str, Any]:
    """报告仓库事实状态；不发现真实 holdout 或有效新模型时保持 blocked。"""
    checks = {
        "holdout_ready": False,
        "new_model_eligible": False,
        "preregistration_eligible": False,
        "labels_eligible": False,
    }
    failures: list[str] = []
    model_id: str | None = None
    try:
        gate = check_holdout_admission(
            None,
            None,
            registry_path=Path(registry_path),
            preregistration_path=Path(preregistration_path),
        )
        checks["holdout_ready"] = gate.get("ready") is True
        checks["labels_eligible"] = gate.get("ready") is True
        failures.extend(str(item) for item in gate.get("failures", []))

        preregistration = _read_json(Path(preregistration_path))
        disposition = _read_json(Path(disposition_path))
        model_id = disposition.get("model_id") if isinstance(disposition.get("model_id"), str) else None
        candidates = [
            item.get("model_id")
            for item in preregistration.get("models", [])
            if isinstance(item, dict) and item.get("role") == "candidate"
        ]
        checks["preregistration_eligible"] = (
            preregistration.get("holdout_ready") is True
            and preregistration.get("labels_revealed") is False
            and len(candidates) == 1
            and candidates[0] == model_id
            and model_id != INVALIDATED_MODEL_ID
        )
        checks["new_model_eligible"] = (
            model_id != INVALIDATED_MODEL_ID
            and disposition.get("formal_scoring_status") == "eligible"
            and disposition.get("holdout_scoring_permitted") is True
            and disposition.get("promotion_eligible") is True
        )
        if model_id == INVALIDATED_MODEL_ID or disposition.get("formal_scoring_status") == "invalidated":
            failures.append("invalidated_model_id")
        elif not checks["new_model_eligible"]:
            failures.append("new_model_not_eligible")
        if not checks["preregistration_eligible"]:
            failures.append("new_model_preregistration_not_eligible")
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        failures.append(f"invalid_status_input:{exc}")
    return _result("blocked_not_ready", list(dict.fromkeys(failures)), checks, model_id=model_id)


def _candidate_model(preregistration: dict[str, Any]) -> str:
    candidates = [
        item.get("model_id")
        for item in preregistration.get("models", [])
        if isinstance(item, dict) and item.get("role") == "candidate"
    ]
    if len(candidates) != 1 or not isinstance(candidates[0], str):
        raise ValueError("exactly one candidate model must be preregistered")
    return candidates[0]


def _structural_gate(
    preregistration: dict[str, Any], score: dict[str, Any], model_id: str
) -> tuple[str, list[str]]:
    gate = preregistration.get("structural_assistant_gate")
    if not isinstance(gate, dict):
        return "not_evaluable", ["structural_assistant_gate_not_preregistered"]
    metric_requirements = gate.get("metrics")
    required_evidence = gate.get("required_evidence")
    if not isinstance(metric_requirements, dict) or not metric_requirements:
        return "not_evaluable", ["structural_metric_thresholds_not_preregistered"]
    if not isinstance(required_evidence, list) or not required_evidence or any(
        not isinstance(item, str) for item in required_evidence
    ):
        return "not_evaluable", ["structural_evidence_requirements_not_preregistered"]
    metrics_by_model = score.get("metrics")
    candidate_metrics = metrics_by_model.get(model_id) if isinstance(metrics_by_model, dict) else None
    supplied_evidence = score.get("structural_evidence")
    if not isinstance(candidate_metrics, dict) or not isinstance(supplied_evidence, list):
        return "not_evaluable", ["structural_metrics_or_evidence_missing"]

    failures: list[str] = []
    for name, requirement in metric_requirements.items():
        observed = candidate_metrics.get(name)
        if not isinstance(requirement, dict) or not isinstance(observed, dict):
            return "not_evaluable", [f"structural_metric_missing:{name}"]
        minimum = requirement.get("minimum")
        minimum_denominator = requirement.get("minimum_denominator")
        value = observed.get("value")
        denominator = observed.get("denominator")
        if not isinstance(minimum, (int, float)) or not isinstance(minimum_denominator, int):
            return "not_evaluable", [f"structural_threshold_invalid:{name}"]
        if not isinstance(value, (int, float)) or not isinstance(denominator, int):
            return "not_evaluable", [f"structural_metric_invalid:{name}"]
        if value < minimum or denominator < minimum_denominator:
            failures.append(f"structural_threshold_failed:{name}")
    missing_evidence = sorted(set(required_evidence) - set(supplied_evidence))
    failures.extend(f"structural_evidence_missing:{item}" for item in missing_evidence)
    return ("failed", failures) if failures else ("passed", [])


def evaluate_product_route(
    *,
    preregistration_path: Path,
    disposition_path: Path,
    freeze_path: Path,
    reveal_path: Path,
    score_path: Path,
    receipt_path: Path,
) -> dict[str, Any]:
    """验证完整冻结证据链，并返回唯一的失败关闭产品分流状态。"""
    checks = {
        "new_model_eligible": False,
        "preregistration_bound": False,
        "cohort_bound": False,
        "prediction_bound": False,
        "labels_bound": False,
        "disposition_bound": False,
        "score_receipt_bound": False,
        "score_unique": False,
        "integrity_and_leakage": False,
    }
    failures: list[str] = []
    model_id: str | None = None
    try:
        preregistration = _read_json(Path(preregistration_path))
        disposition = _read_json(Path(disposition_path))
        freeze = _read_json(Path(freeze_path))
        reveal = _read_json(Path(reveal_path))
        score = _read_json(Path(score_path))
        receipt = _read_json(Path(receipt_path))
        model_id = _candidate_model(preregistration)

        if model_id == INVALIDATED_MODEL_ID or disposition.get("formal_scoring_status") == "invalidated":
            return _result(
                "blocked_not_ready",
                ["invalidated_model_id"],
                checks,
                model_id=model_id,
            )
        checks["new_model_eligible"] = (
            disposition.get("model_id") == model_id
            and disposition.get("formal_scoring_status") == "eligible"
            and disposition.get("holdout_scoring_permitted") is True
            and disposition.get("promotion_eligible") is True
        )
        if not checks["new_model_eligible"]:
            return _result("blocked_not_ready", ["new_model_not_eligible"], checks, model_id=model_id)

        preregistration_sha = _sha256(Path(preregistration_path))
        disposition_sha = _sha256(Path(disposition_path))
        freeze_sha = _sha256(Path(freeze_path))
        score_sha = _canonical_sha256(score)
        predictions_path = Path(str(freeze.get("predictions_path")))
        labels_path = Path(str(reveal.get("labels_path")))
        predictions_sha = _sha256(predictions_path)
        labels_sha = _sha256(labels_path)

        preregistration_id = preregistration.get("preregistration_id")
        cohort_sha = freeze.get("cohort_sha256")
        expected = {
            "preregistration_id": preregistration_id,
            "preregistration_sha256": preregistration_sha,
            "cohort_sha256": cohort_sha,
            "predictions_sha256": predictions_sha,
            "labels_sha256": labels_sha,
            "freeze_sha256": freeze_sha,
            "model_id": model_id,
            "disposition_sha256": disposition_sha,
        }
        checks["preregistration_bound"] = all(
            artifact.get("preregistration_id") == preregistration_id
            and artifact.get("preregistration_sha256") == preregistration_sha
            for artifact in (freeze, score, receipt)
        )
        checks["cohort_bound"] = (
            isinstance(cohort_sha, str)
            and len(cohort_sha) == 64
            and score.get("cohort_sha256") == cohort_sha
            and receipt.get("cohort_sha256") == cohort_sha
        )
        checks["prediction_bound"] = (
            freeze.get("predictions_sha256") == predictions_sha
            and score.get("predictions_sha256") == predictions_sha
            and receipt.get("predictions_sha256") == predictions_sha
        )
        checks["labels_bound"] = (
            reveal.get("labels_sha256") == labels_sha
            and score.get("labels_sha256") == labels_sha
            and receipt.get("labels_sha256") == labels_sha
        )
        checks["disposition_bound"] = (
            score.get("model_id") == model_id
            and receipt.get("model_id") == model_id
            and score.get("disposition_sha256") == disposition_sha
            and receipt.get("disposition_sha256") == disposition_sha
        )
        checks["score_receipt_bound"] = (
            receipt.get("score_sha256") == score_sha
            and all(receipt.get(name) == value for name, value in expected.items())
            and reveal.get("freeze_sha256") == freeze_sha
            and score.get("freeze_sha256") == freeze_sha
        )
        checks["score_unique"] = (
            freeze.get("one_score_only") is True
            and score.get("one_score_only") is True
            and receipt.get("one_score_only") is True
        )
        admission = score.get("admission_checks")
        checks["integrity_and_leakage"] = (
            isinstance(admission, dict)
            and admission.get("cohort_ready") is True
            and admission.get("labels_valid") is True
            and admission.get("no_leakage") is True
        )
        failure_names = {
            "preregistration_bound": "preregistration_hash_or_id_mismatch",
            "cohort_bound": "cohort_hash_mismatch",
            "prediction_bound": "predictions_hash_mismatch",
            "labels_bound": "labels_hash_mismatch",
            "disposition_bound": "model_or_disposition_mismatch",
            "score_receipt_bound": "score_receipt_binding_mismatch",
            "score_unique": "score_uniqueness_not_proven",
            "integrity_and_leakage": "completeness_or_leakage_gate_failed",
        }
        failures = [failure_names[name] for name, passed in checks.items() if name in failure_names and not passed]
        if failures:
            return _result("rejected", failures, checks, model_id=model_id)

        promotion_checks = score.get("promotion_checks")
        if not isinstance(promotion_checks, dict) or not _REQUIRED_TERMINAL_CHECKS.issubset(promotion_checks):
            return _result(
                "blocked_not_ready",
                ["terminal_metrics_missing"],
                checks,
                model_id=model_id,
            )
        terminal_passed = all(promotion_checks[name] is True for name in _REQUIRED_TERMINAL_CHECKS)
        if terminal_passed:
            return _result("shadow_candidate", [], checks, model_id=model_id)

        structural_status, structural_failures = _structural_gate(preregistration, score, model_id)
        if structural_status == "not_evaluable":
            return _result(
                "blocked_not_ready",
                structural_failures,
                checks,
                structural_status=structural_status,
                model_id=model_id,
            )
        if structural_status == "passed":
            return _result(
                "structural_evidence_assistant",
                [],
                checks,
                structural_status=structural_status,
                model_id=model_id,
            )
        return _result(
            "rejected",
            structural_failures,
            checks,
            structural_status=structural_status,
            model_id=model_id,
        )
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        failures.append(f"invalid_route_input:{exc}")
        return _result("rejected", failures, checks, model_id=model_id)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    status = commands.add_parser("status")
    status.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    status.add_argument("--preregistration", type=Path, default=DEFAULT_PREREGISTRATION)
    status.add_argument("--disposition", type=Path, default=DEFAULT_MODEL_DISPOSITION)
    report = commands.add_parser("report")
    report.add_argument("--preregistration", type=Path, required=True)
    report.add_argument("--disposition", type=Path, required=True)
    report.add_argument("--freeze", type=Path, required=True)
    report.add_argument("--reveal", type=Path, required=True)
    report.add_argument("--score", type=Path, required=True)
    report.add_argument("--receipt", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "status":
        result = repository_product_status(
            registry_path=args.registry,
            preregistration_path=args.preregistration,
            disposition_path=args.disposition,
        )
    else:
        result = evaluate_product_route(
            preregistration_path=args.preregistration,
            disposition_path=args.disposition,
            freeze_path=args.freeze,
            reveal_path=args.reveal,
            score_path=args.score,
            receipt_path=args.receipt,
        )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["state"] in {"shadow_candidate", "structural_evidence_assistant"} else 1


if __name__ == "__main__":
    raise SystemExit(main())

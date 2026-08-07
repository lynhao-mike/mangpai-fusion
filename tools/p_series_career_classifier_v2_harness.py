"""职业路径分类器 v2 的标签隔离 prepare/predict/score harness。

``prepare`` 复用既有 case-id-only cohort；``predict`` 只读取 cohort 与
``cases/shuru-input.md`` 的四柱/大运受限字段，随后原子创建预测与 freeze；
``score`` 在冻结后才读取时序标签并原子创建 score JSON。任何产物均拒绝覆盖。
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from engine.asof.career_path_classifier_v2 import SCORE_MARGIN, classify_career_path
from tools.p_series_career_blind_harness import (
    BINARY_LABELS,
    FORBIDDEN_BLIND_TEXT,
    VALID_LABELS,
    _atomic_create,
    _blocks,
    _parse_dayun,
    _read_json,
    _read_jsonl,
    _sha256_file,
    score_predictions,
)

FROZEN_BASELINE_BALANCED_ACCURACY = 0.425
THRESHOLDS = {
    "balanced_accuracy": 0.60,
    "employment_recall": 0.55,
    "entrepreneurship_recall": 0.55,
    "coverage": 0.70,
}


def prepare_existing_cohort(source_path: Path, out_path: Path) -> dict[str, Any]:
    """从既有无标签 cohort 原子复制 v2 prepare 产物。"""
    manifest = _read_json(source_path)
    case_ids = manifest.get("case_ids")
    if manifest.get("contract") != "case_ids_only_no_labels":
        raise ValueError("source manifest is not case-id-only")
    if not isinstance(case_ids, list) or len(case_ids) != 40 or len(set(case_ids)) != 40:
        raise ValueError("source manifest must contain 40 unique IDs")
    prepared = {
        "schema_version": "p-series-career-cohort/v1",
        "classification": "career_path_classifier_v2_one_shot_holdout",
        "case_ids": sorted(case_ids),
        "case_count": 40,
        "contract": "case_ids_only_no_labels",
        "source_manifest_path": source_path.as_posix(),
        "source_manifest_sha256": _sha256_file(source_path),
    }
    _atomic_create(out_path, json.dumps(prepared, ensure_ascii=False, indent=2).encode("utf-8") + b"\n")
    return {"manifest": out_path.as_posix(), "sha256": _sha256_file(out_path), "case_count": 40}


def _restricted_charts(input_path: Path, allowed_ids: set[str]) -> tuple[dict[str, dict[str, Any]], dict[str, list[str]]]:
    charts: dict[str, dict[str, Any]] = {}
    scan: dict[str, list[str]] = {}
    for base_id, _sex, block, header_pillars in _blocks(input_path.read_text(encoding="utf-8")):
        if base_id not in allowed_ids:
            continue
        dayun = _parse_dayun(block)
        selected_lines = [f"四柱：{' '.join(header_pillars)}", "大运：" + " ".join(dayun)]
        scan[base_id] = [line.split("：", 1)[0] for line in selected_lines if FORBIDDEN_BLIND_TEXT.search(line)]
        charts[base_id] = {"pillars": header_pillars, "dayun": dayun}
    missing = allowed_ids - charts.keys()
    if missing:
        raise ValueError(f"cohort IDs missing from blind input: {', '.join(sorted(missing))}")
    return charts, scan


def _predict_chart(case_id: str, chart: dict[str, Any]) -> dict[str, Any]:
    # 输入大运无可靠日期边界，分类器按契约不能猜当前运，故 as_of_date=None。
    state = classify_career_path(
        tuple(chart["pillars"]),
        [{"ganzhi": item} for item in chart["dayun"]],
        None,
    )
    natal = state.natal_inclination
    if state.abstain_reason is not None or natal.employment_inclined == natal.entrepreneurship_inclined:
        prediction = "abstain"
    elif natal.employment_inclined:
        prediction = "employment"
    else:
        prediction = "entrepreneurship"
    return {
        "case_id": case_id,
        "prediction": prediction,
        "signal": {
            "adapter": "career_path_classifier_v2",
            "reason": state.abstain_reason or "natal_score_advantage",
            "evidence_refs": list(natal.evidence_refs),
            "dayun_mechanism": state.dayun_context.mechanism if state.dayun_context else None,
        },
    }


def predict_and_freeze(
    manifest_path: Path,
    input_path: Path,
    predictions_path: Path,
    freeze_path: Path,
    classifier_path: Path,
) -> dict[str, Any]:
    manifest = _read_json(manifest_path)
    case_ids = manifest.get("case_ids")
    if manifest.get("contract") != "case_ids_only_no_labels":
        raise ValueError("manifest is not case-id-only")
    if not isinstance(case_ids, list) or len(case_ids) != 40 or len(set(case_ids)) != 40:
        raise ValueError("manifest must contain 40 unique IDs")
    charts, scan = _restricted_charts(input_path, set(case_ids))
    contaminated = {case_id: hits for case_id, hits in scan.items() if hits}
    rows = [
        _predict_chart(case_id, charts[case_id])
        if case_id not in contaminated
        else {
            "case_id": case_id,
            "prediction": "abstain",
            "signal": {"adapter": "leakage_guard", "reason": "restricted_field_leakage", "hits": contaminated[case_id]},
        }
        for case_id in sorted(case_ids)
    ]
    payload = "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows).encode("utf-8")
    _atomic_create(predictions_path, payload)
    prediction_hash = hashlib.sha256(payload).hexdigest()
    freeze = {
        "schema_version": "career-path-classifier-freeze/v2",
        "classification": "one_shot_historical_label_isolated_holdout",
        "one_shot_freeze": True,
        "post_score_tuning_permitted": False,
        "frozen_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "classifier_path": classifier_path.as_posix(),
        "classifier_sha256": _sha256_file(classifier_path),
        "manifest_path": manifest_path.as_posix(),
        "manifest_sha256": _sha256_file(manifest_path),
        "blind_input_path": input_path.as_posix(),
        "blind_input_sha256": _sha256_file(input_path),
        "predictions_path": predictions_path.as_posix(),
        "predictions_sha256": prediction_hash,
        "case_count": len(rows),
        "case_ids": sorted(case_ids),
        "leakage_scan": {
            "method": "restricted_fields_only",
            "contaminated_case_count": len(contaminated),
            "contaminated_cases": sorted(contaminated),
        },
        "rule_parameters": {
            "score_margin": SCORE_MARGIN,
            "detector_1": "rooted official/resource chain + visible official/resource chain - unrescued output break",
            "detector_2": "usable output/wealth chain requires peer or subject participation; wealth-only capped",
            "detector_3": "official dayun with resource receiver suppresses entrepreneurship",
            "symmetric_dayun": "output/wealth dayun with subject capacity opens entrepreneurship and suppresses employment",
            "dayun_selection": "only explicit date-bounded current segment",
        },
    }
    _atomic_create(freeze_path, json.dumps(freeze, ensure_ascii=False, indent=2).encode("utf-8") + b"\n")
    return {"predictions": predictions_path.as_posix(), "freeze": freeze_path.as_posix(), "sha256": prediction_hash, "case_count": len(rows)}


def score_frozen(freeze_path: Path, labels_path: Path, score_path: Path) -> dict[str, Any]:
    freeze = _read_json(freeze_path)
    predictions_path = Path(str(freeze["predictions_path"]))
    if _sha256_file(predictions_path) != freeze.get("predictions_sha256"):
        raise ValueError("frozen predictions SHA256 mismatch")
    predictions = _read_jsonl(predictions_path)
    label_rows = _read_jsonl(labels_path)
    temporal_to_binary = {
        "employed": "employment",
        "entrepreneurial": "entrepreneurship",
        "mixed": "mixed",
        "transitioning": "mixed",
    }
    labels = {
        str(row["case_id"]): temporal_to_binary[str(row["reality_status_at_feedback"])]
        for row in label_rows
        if str(row.get("reality_status_at_feedback")) in temporal_to_binary
    }
    result = score_predictions(predictions=predictions, labels=labels)
    if result["strict_binary_count"] != 37 or result["mixed_holdout_count"] != 3:
        raise ValueError("expected strict=37 and mixed holdout=3")
    employment_recall = result["recall"]["employment"]
    entrepreneurship_recall = result["recall"]["entrepreneurship"]
    passes = (
        result["balanced_accuracy"] >= THRESHOLDS["balanced_accuracy"]
        and employment_recall >= THRESHOLDS["employment_recall"]
        and entrepreneurship_recall >= THRESHOLDS["entrepreneurship_recall"]
        and result["coverage"] >= THRESHOLDS["coverage"]
        and result["balanced_accuracy"] > FROZEN_BASELINE_BALANCED_ACCURACY
    )
    score = {
        "schema_version": "career-path-classifier-score/v2",
        "freeze_path": freeze_path.as_posix(),
        "freeze_sha256": _sha256_file(freeze_path),
        "predictions_sha256": freeze["predictions_sha256"],
        "strict_binary_count": result["strict_binary_count"],
        "mixed_holdout_count": result["mixed_holdout_count"],
        "balanced_accuracy": result["balanced_accuracy"],
        "employment_recall": employment_recall,
        "entrepreneurship_recall": entrepreneurship_recall,
        "coverage": result["coverage"],
        "accuracy": result["accuracy"],
        "confusion_matrix": result["confusion_matrix"],
        "prediction_distribution": result["prediction_distribution"],
        "frozen_baseline_balanced_accuracy": FROZEN_BASELINE_BALANCED_ACCURACY,
        "thresholds": THRESHOLDS,
        "passes_all_thresholds": passes,
        "post_score_tuning_permitted": False,
        "audit_rows": result["audit_rows"],
    }
    _atomic_create(score_path, json.dumps(score, ensure_ascii=False, indent=2).encode("utf-8") + b"\n")
    return {key: score[key] for key in ("strict_binary_count", "mixed_holdout_count", "balanced_accuracy", "employment_recall", "entrepreneurship_recall", "coverage", "passes_all_thresholds")}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser("prepare")
    prepare.add_argument("--source-manifest", type=Path, required=True)
    prepare.add_argument("--out", type=Path, required=True)
    predict = commands.add_parser("predict")
    predict.add_argument("--manifest", type=Path, required=True)
    predict.add_argument("--input", type=Path, required=True)
    predict.add_argument("--predictions", type=Path, required=True)
    predict.add_argument("--freeze", type=Path, required=True)
    predict.add_argument("--classifier", type=Path, required=True)
    score = commands.add_parser("score")
    score.add_argument("--freeze", type=Path, required=True)
    score.add_argument("--labels", type=Path, required=True)
    score.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.command == "prepare":
        result = prepare_existing_cohort(args.source_manifest, args.out)
    elif args.command == "predict":
        result = predict_and_freeze(args.manifest, args.input, args.predictions, args.freeze, args.classifier)
    else:
        result = score_frozen(args.freeze, args.labels, args.out)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

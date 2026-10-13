"""P 系列任职/经营历史标签隔离回放基线。

``prepare`` 是唯一读取人工标签的阶段，但只公布 ``case_id`` cohort；``predict``
只消费该 cohort 和 ``shuru-input.md`` 中受限提取的排盘字段；``score`` 在冻结后才
读取标签。此工具不读取 ``cases/fankui-feedback.md``，也不修改任何生产规则或权重。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from engine.claims.orchestrator import chart_ledger_from_mapping
from engine.features import build_chart_feature_vector
from engine.v5.duan_runner import _duan_structure

PREDICTIONS = {"employment", "entrepreneurship", "abstain"}
BINARY_LABELS = {"employment", "entrepreneurship"}
VALID_LABELS = BINARY_LABELS | {"mixed"}
CASE_HEADER = re.compile(r"^##\s+(P-\d{4}-\d{3})\s+·\s+([乾坤])\s+·\s+((?:[甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]){4})", re.MULTILINE)
PILLAR = r"[甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]"
FORBIDDEN_BLIND_TEXT = re.compile(r"职业|履历|任职|经营|创业|经商|打工|上班|工作(?:经历|情况|反馈)?|反馈|occupation|known[_ -]?facts", re.IGNORECASE)


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _atomic_create(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as stream:
            stream.write(content)
    except FileExistsError as exc:
        raise FileExistsError(f"refusing to overwrite immutable artifact: {path}") from exc


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"JSONL line {number} is not an object")
        rows.append(value)
    return rows


def prepare_cohort(labels_path: Path, out_path: Path) -> dict[str, Any]:
    """Reveal-stage preparation: publish only valid cohort IDs, never labels."""
    case_ids: list[str] = []
    for row in _read_jsonl(labels_path):
        case_id, label = row.get("case_id"), row.get("label")
        if not isinstance(case_id, str) or not isinstance(label, str):
            raise ValueError("labels require string case_id and label")
        if label != "unknown":
            if label not in VALID_LABELS:
                raise ValueError(f"unsupported valid label: {label}")
            case_ids.append(case_id)
    if len(case_ids) != len(set(case_ids)):
        raise ValueError("valid cohort has duplicate case_id")
    if len(case_ids) != 40:
        raise ValueError(f"expected 40 valid cases, got {len(case_ids)}")
    manifest = {
        "schema_version": "p-series-career-cohort/v1",
        "classification": "historical_label_isolated_replay_baseline",
        "case_ids": sorted(case_ids),
        "case_count": len(case_ids),
        "contract": "case_ids_only_no_labels",
    }
    _atomic_create(out_path, json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8") + b"\n")
    return {"manifest": out_path.as_posix(), "sha256": _sha256_file(out_path), "case_count": len(case_ids)}


def _blocks(text: str) -> Iterable[tuple[str, str, str, tuple[str, str, str, str]]]:
    matches = list(CASE_HEADER.finditer(text))
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        base_id, sex, compact = match.groups()
        pillars = tuple(re.findall(PILLAR, compact))
        yield base_id, sex, text[match.start():end], pillars  # type: ignore[misc]


def _parse_dayun(block: str) -> tuple[str, ...]:
    match = re.search(r"^- 大运[：:]\s*(.+)$", block, re.MULTILINE)
    if not match:
        return ()
    return tuple(re.findall(PILLAR, match.group(1)))


def _restricted_charts(input_path: Path, allowed_ids: set[str]) -> tuple[dict[str, dict[str, Any]], dict[str, list[str]]]:
    charts: dict[str, dict[str, Any]] = {}
    scan: dict[str, list[str]] = {}
    for base_id, sex, block, header_pillars in _blocks(input_path.read_text(encoding="utf-8")):
        if base_id not in allowed_ids:
            continue
        pillar_match = re.search(r"^- 四柱[：:]\s*((?:" + PILLAR + r"\s*){4})", block, re.MULTILINE)
        if pillar_match is None:
            raise ValueError(f"missing four pillars: {base_id}")
        pillars = tuple(re.findall(PILLAR, pillar_match.group(1)))
        if pillars != header_pillars:
            raise ValueError(f"header/four-pillar mismatch: {base_id}")
        selected_lines = [f"性别：{sex}", f"四柱：{' '.join(pillars)}", "大运：" + " ".join(_parse_dayun(block))]
        hits = [line.split("：", 1)[0] for line in selected_lines if FORBIDDEN_BLIND_TEXT.search(line)]
        scan[base_id] = hits
        charts[base_id] = {"sex_marker": sex, "four_pillars": list(pillars), "dayun_steps": [{"ganzhi": item} for item in _parse_dayun(block)]}
    missing = allowed_ids - charts.keys()
    if missing:
        raise ValueError(f"cohort IDs missing from blind input: {', '.join(sorted(missing))}")
    return charts, scan


def decide_duan_career_path(*, employment_score: int, entrepreneurship_score: int, branch_conflict_intensity: float) -> dict[str, Any]:
    """Minimal semantic adapter for ``duan_runner._career_path_type``.

    The source rule can emit ``mixed``. This harness contract forbids it, so that
    source branch becomes ``abstain`` rather than an arbitrary binary tie-break.
    """
    if employment_score >= 4 and entrepreneurship_score >= 4 and branch_conflict_intensity >= 0.35:
        return {"prediction": "abstain", "reason": "duan_runner_mixed_not_allowed"}
    if employment_score >= 4 and employment_score - entrepreneurship_score >= 3:
        return {"prediction": "employment", "reason": "duan_runner_employment_trigger"}
    if entrepreneurship_score >= 4 and entrepreneurship_score - employment_score >= 3:
        return {"prediction": "entrepreneurship", "reason": "duan_runner_entrepreneurship_trigger"}
    return {"prediction": "abstain", "reason": "duan_runner_insufficient_advantage"}


def _predict_chart(case_id: str, chart: dict[str, Any]) -> dict[str, Any]:
    ledger = chart_ledger_from_mapping(chart)
    features = build_chart_feature_vector(ledger)
    structure = _duan_structure(ledger)
    employment = sum(features.ten_god_counts[name] for name in ("正官", "七杀", "正印", "偏印"))
    entrepreneurship = sum(features.ten_god_counts[name] for name in ("食神", "伤官", "正财", "偏财"))
    decision = decide_duan_career_path(
        employment_score=employment,
        entrepreneurship_score=entrepreneurship,
        branch_conflict_intensity=features.branch_conflict_intensity,
    )
    return {
        "case_id": case_id,
        "prediction": decision["prediction"],
        "signal": {
            "adapter": "duan_runner_semantic_adapter",
            "employment_score": employment,
            "entrepreneurship_score": entrepreneurship,
            "branch_conflict_intensity": features.branch_conflict_intensity,
            "active_path_count": structure.active_path_count,
            "reason": decision["reason"],
        },
    }


def predict_from_manifest(manifest_path: Path, input_path: Path, predictions_path: Path, freeze_path: Path) -> dict[str, Any]:
    """Prediction stage: accepts only case IDs plus restricted chart facts."""
    manifest = _read_json(manifest_path)
    if manifest.get("contract") != "case_ids_only_no_labels":
        raise ValueError("manifest is not a case-id-only cohort")
    case_ids = manifest.get("case_ids")
    if not isinstance(case_ids, list) or not all(isinstance(item, str) for item in case_ids):
        raise ValueError("manifest case_ids invalid")
    if len(case_ids) != 40 or len(set(case_ids)) != 40:
        raise ValueError("manifest must contain 40 unique IDs")
    charts, scan = _restricted_charts(input_path, set(case_ids))
    contaminated = {case_id: hits for case_id, hits in scan.items() if hits}
    rows = [_predict_chart(case_id, charts[case_id]) if case_id not in contaminated else {
        "case_id": case_id, "prediction": "abstain", "signal": {"adapter": "leakage_guard", "reason": "restricted_field_leakage", "hits": contaminated[case_id]},
    } for case_id in sorted(case_ids)]
    payload = "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows).encode("utf-8")
    _atomic_create(predictions_path, payload)
    prediction_sha256 = _sha256_bytes(payload)
    freeze = {
        "schema_version": "p-series-career-prediction-freeze/v1",
        "classification": "historical_label_isolated_replay_baseline",
        "frozen_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "manifest_path": manifest_path.as_posix(),
        "manifest_sha256": _sha256_file(manifest_path),
        "blind_input_path": input_path.as_posix(),
        "blind_input_sha256": _sha256_file(input_path),
        "predictions_path": predictions_path.as_posix(),
        "predictions_sha256": prediction_sha256,
        "case_count": len(rows),
        "case_ids": sorted(case_ids),
        "leakage_scan": {"method": "restricted_fields_only", "contaminated_case_count": len(contaminated), "contaminated_cases": sorted(contaminated)},
    }
    _atomic_create(freeze_path, json.dumps(freeze, ensure_ascii=False, indent=2).encode("utf-8") + b"\n")
    return {"predictions": predictions_path.as_posix(), "freeze": freeze_path.as_posix(), "sha256": prediction_sha256, "case_count": len(rows)}


def score_predictions(*, predictions: list[dict[str, Any]], labels: dict[str, str]) -> dict[str, Any]:
    if len(predictions) != len({str(row.get("case_id")) for row in predictions}):
        raise ValueError("duplicate prediction case_id")
    if set(row.get("case_id") for row in predictions) != set(labels):
        raise ValueError("prediction IDs and label IDs differ")
    matrix = {truth: {prediction: 0 for prediction in ("employment", "entrepreneurship", "abstain")} for truth in BINARY_LABELS}
    rows: list[dict[str, Any]] = []
    distribution: Counter[str] = Counter()
    mixed_rows: list[dict[str, Any]] = []
    for row in sorted(predictions, key=lambda value: str(value["case_id"])):
        case_id, prediction = str(row["case_id"]), row.get("prediction")
        truth = labels[case_id]
        if prediction not in PREDICTIONS:
            raise ValueError(f"invalid prediction: {prediction}")
        if truth not in VALID_LABELS:
            raise ValueError(f"invalid label: {truth}")
        distribution[prediction] += 1
        scored = truth in BINARY_LABELS
        hit = prediction == truth if scored else None
        audit = {"case_id": case_id, "prediction": prediction, "truth": truth, "strict_binary_scored": scored, "hit": hit, "signal": row.get("signal", {})}
        rows.append(audit)
        if scored:
            matrix[truth][prediction] += 1
        else:
            mixed_rows.append(audit)
    total = sum(sum(values.values()) for values in matrix.values())
    correct = sum(matrix[label][label] for label in BINARY_LABELS)
    recalls = {label: matrix[label][label] / sum(matrix[label].values()) if sum(matrix[label].values()) else 0.0 for label in BINARY_LABELS}
    abstain = sum(matrix[label]["abstain"] for label in BINARY_LABELS)
    return {
        "audit_rows": rows,
        "strict_binary_count": total,
        "mixed_holdout_count": len(mixed_rows),
        "mixed_holdout": mixed_rows,
        "prediction_distribution": dict(sorted(distribution.items())),
        "confusion_matrix": matrix,
        "accuracy": correct / total if total else 0.0,
        "balanced_accuracy": sum(recalls.values()) / len(BINARY_LABELS),
        "recall": recalls,
        "abstain_count": abstain,
        "coverage": (total - abstain) / total if total else 0.0,
        "majority_class_baseline": 32 / 37,
    }


def _render_report(score: dict[str, Any], freeze: dict[str, Any]) -> str:
    lines = [
        "# P 系列任职/经营盲断 Harness 审计报告",
        "",
        "> 分类：历史案例的标签隔离回放基线，不是前瞻盲测；不得据此宣称已获得真实新案例盲断能力。",
        "",
        "## 隔离与冻结",
        "",
        f"- 预测 cohort：40 个 case_id；预测阶段只读取 cohort manifest 与 `cases/shuru-input.md` 的性别、四柱和大运受限字段。",
        "- 人工标签在独立 score 阶段才由 `cases/p-series-career-path-labels.jsonl` 揭示；预测代码不读取 `cases/fankui-feedback.md`。",
        f"- 冻结预测 SHA256：`{freeze['predictions_sha256']}`。",
        f"- 输入 SHA256：`{freeze['blind_input_sha256']}`；受限字段泄漏扫描命中：{freeze['leakage_scan']['contaminated_case_count']}。",
        "- 模型：`engine/v5/duan_runner.py::_career_path_type` 的语义适配器；原逻辑的 mixed 分支在本契约中一律转为 abstain，未改写或调参生产规则。",
        "",
        "## 严格二分类指标",
        "",
        f"- 严格可评分样本：{score['strict_binary_count']}；mixed holdout：{score['mixed_holdout_count']}。",
        f"- 准确率：{score['accuracy']:.2%}；balanced accuracy：{score['balanced_accuracy']:.2%}。",
        f"- recall：employment {score['recall']['employment']:.2%}；entrepreneurship {score['recall']['entrepreneurship']:.2%}。",
        f"- abstain：{score['abstain_count']}；覆盖率：{score['coverage']:.2%}。",
        f"- 多数类基线：32/37 = {score['majority_class_baseline']:.2%}。只预测 employment 即使准确率较高也没有实际区分能力。",
        "",
        "| 真值 \\ 预测 | employment | entrepreneurship | abstain |",
        "|---|---:|---:|---:|",
        *[f"| {truth} | {values['employment']} | {values['entrepreneurship']} | {values['abstain']} |" for truth, values in score["confusion_matrix"].items()],
        "",
        "## 预测类别分布",
        "",
        "| 预测 | 数量 |",
        "|---|---:|",
        *[f"| {label} | {count} |" for label, count in score["prediction_distribution"].items()],
        "",
        "## 逐案审计表",
        "",
        "| Case | 预测 | 人工真值 | 严格评分 | 命中 | 证据/模型信号 |",
        "|---|---|---|---|---|---|",
    ]
    for row in score["audit_rows"]:
        signal = row["signal"]
        if isinstance(signal, dict):
            signal_text = "; ".join(f"{key}={value}" for key, value in signal.items() if key != "adapter")
        else:
            signal_text = str(signal)
        hit = "—" if row["hit"] is None else ("是" if row["hit"] else "否")
        lines.append(f"| {row['case_id']} | {row['prediction']} | {row['truth']} | {'是' if row['strict_binary_scored'] else '否（mixed holdout）'} | {hit} | {signal_text} |")
    return "\n".join(lines) + "\n"


def score_frozen(freeze_path: Path, labels_path: Path, report_path: Path) -> dict[str, Any]:
    freeze = _read_json(freeze_path)
    predictions_path = Path(str(freeze["predictions_path"]))
    if _sha256_file(predictions_path) != freeze.get("predictions_sha256"):
        raise ValueError("frozen predictions SHA256 mismatch")
    manifest_path = Path(str(freeze["manifest_path"]))
    if _sha256_file(manifest_path) != freeze.get("manifest_sha256"):
        raise ValueError("cohort manifest SHA256 mismatch")
    predictions = _read_jsonl(predictions_path)
    labels = {str(row["case_id"]): str(row["label"]) for row in _read_jsonl(labels_path) if row.get("label") != "unknown"}
    result = score_predictions(predictions=predictions, labels=labels)
    if result["strict_binary_count"] != 37 or result["mixed_holdout_count"] != 3:
        raise ValueError("expected strict=37 and mixed holdout=3")
    _atomic_create(report_path, _render_report(result, freeze).encode("utf-8"))
    return {"report": report_path.as_posix(), **{key: result[key] for key in ("strict_binary_count", "mixed_holdout_count", "accuracy", "balanced_accuracy", "abstain_count", "coverage")}}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser("prepare")
    prepare.add_argument("--labels", type=Path, required=True)
    prepare.add_argument("--out", type=Path, required=True)
    predict = commands.add_parser("predict")
    predict.add_argument("--manifest", type=Path, required=True)
    predict.add_argument("--input", type=Path, required=True)
    predict.add_argument("--predictions", type=Path, required=True)
    predict.add_argument("--freeze", type=Path, required=True)
    score = commands.add_parser("score")
    score.add_argument("--freeze", type=Path, required=True)
    score.add_argument("--labels", type=Path, required=True)
    score.add_argument("--report", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.command == "prepare":
        result = prepare_cohort(args.labels, args.out)
    elif args.command == "predict":
        result = predict_from_manifest(args.manifest, args.input, args.predictions, args.freeze)
    else:
        result = score_frozen(args.freeze, args.labels, args.report)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

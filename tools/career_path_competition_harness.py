"""预注册职业路径三模型竞争 harness。

严格阶段为 prepare -> predict -> freeze -> reveal -> score。预测阶段只接受
case-id-only 准备制品和受限命盘 JSONL；任何标签、反馈、occupation 或 known facts
字段都会失败关闭。本工具是实验旁路，不修改生产入口。
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from engine.asof.career_path_classifier_v3 import classify_career_path
from engine.asof.career_relation_graph import build_career_relation_graph
from engine.asof.career_relation_reasoner import reason_natal_career_inclination
from engine.infrastructure.file_digest import digest_matches
from engine.predicates.types import Bazi, GanZhi
from tools.career_path_holdout_gate import (
    DEFAULT_PREREGISTRATION,
    DEFAULT_REGISTRY,
    check_holdout_admission,
)

MODEL_IDS = (
    "majority_or_abstain_baseline-v1",
    "career-path-counting-baseline-v3-frozen",
    "career-path-relation-model-v1",
)
PREDICTIONS = {"employment", "entrepreneurship", "mixed", "transitioning", "abstain"}
FORBIDDEN_KEYS = {
    "label", "labels", "feedback", "occupation", "known_facts", "knownfacts",
    "reality_status_at_feedback", "evidence_quote", "rationale", "source",
}
RULE_PATHS = (
    Path("engine/asof/career_path_classifier_v3.py"),
    Path("engine/asof/career_relation_graph.py"),
    Path("engine/asof/career_relation_reasoner.py"),
)
HARNESS_PATH = Path("tools/career_path_competition_harness.py")
DEFAULT_MODEL_DISPOSITION = Path(
    "META/as-of-evaluation/career-relation-model-v1-disposition.json"
)


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON root must be object: {path}")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for number, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"JSONL line {number} must be object: {path}")
        rows.append(value)
    return rows


def _canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sha256(path: Path) -> str:
    """记录侧：原始字节 sha256（历史记录语义，勿改为归一化）。

    跨阶段比对请用 ``digest_matches``（行尾无关），见 KB-001。
    """
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _bound_hash_matches(path: Path, recorded: object, what: str) -> None:
    """行尾无关地校验绑定 hash；仅真漂移抛错。

    冻结记录的 hash 多在 LF 下计算，Windows 检出会把文件转成 CRLF，
    导致内容一致却误判为「制品被改动」。三种归一化皆不匹配才抛错。
    """
    if not digest_matches(path, recorded):
        raise ValueError(f"{what} hash mismatch")


def _hash_value(value: object) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _create(path: Path, payload: bytes) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as stream:
            stream.write(payload)
    except FileExistsError as exc:
        raise FileExistsError(f"refusing to overwrite immutable artifact: {path}") from exc


def _create_json(path: Path, value: object) -> None:
    _create(path, json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8") + b"\n")


def _write_jsonl_create(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    payload = b"".join(
        json.dumps(row, ensure_ascii=False, sort_keys=True).encode("utf-8") + b"\n"
        for row in rows
    )
    _create(path, payload)


def _assert_id(preregistration: dict[str, Any], preregistration_id: str) -> None:
    if preregistration.get("preregistration_id") != preregistration_id:
        raise ValueError("preregistration_id mismatch")


def assert_formal_model_eligibility(
    disposition_path: Path = DEFAULT_MODEL_DISPOSITION,
) -> None:
    """失败关闭：只有显式 ``eligible`` 的同一模型身份才可进入正式实验。"""
    disposition = _read_json(Path(disposition_path))
    if disposition.get("model_id") != MODEL_IDS[2]:
        raise ValueError("model disposition model_id mismatch")
    status = disposition.get("formal_scoring_status")
    if status == "invalidated":
        raise ValueError(
            "career-path-relation-model-v1 is invalidated; semantic revision requires "
            "a new model_id and preregistration"
        )
    if status != "eligible":
        raise ValueError("relation model is not explicitly eligible for formal scoring")


def _assert_no_forbidden(value: object, path: str = "root") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = str(key).lower().replace("-", "_").replace(" ", "_")
            if normalized in FORBIDDEN_KEYS:
                raise ValueError(f"forbidden blind field at {path}.{key}")
            _assert_no_forbidden(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _assert_no_forbidden(child, f"{path}[{index}]")


def current_status(
    *, registry_path: Path = DEFAULT_REGISTRY,
    preregistration_path: Path = DEFAULT_PREREGISTRATION,
) -> dict[str, Any]:
    """返回仓库当前准入证据；零 holdout 时保持 ``not_ready``。"""
    result = check_holdout_admission(
        None, None, registry_path=registry_path, preregistration_path=preregistration_path
    )
    return {**result, "production_switch_permitted": False}


def prepare_experiment(
    manifest_path: Path,
    labels_path: Path,
    out_path: Path,
    *,
    registry_path: Path = DEFAULT_REGISTRY,
    preregistration_path: Path = DEFAULT_PREREGISTRATION,
) -> dict[str, Any]:
    """先校验模型处置和 holdout gate，再发布不含标签的准备制品。"""
    assert_formal_model_eligibility()
    gate = check_holdout_admission(
        manifest_path, labels_path, registry_path=registry_path,
        preregistration_path=preregistration_path,
    )
    if not gate["ready"]:
        return {"status": gate["status"], "prepared": False, "holdout_gate": gate}
    prereg = _read_json(preregistration_path)
    manifest = _read_json(manifest_path)
    case_ids = manifest["case_ids"]
    artifact = {
        "schema_version": "career-path-competition-prepare/v1",
        "stage": "prepare",
        "preregistration_id": prereg["preregistration_id"],
        "preregistration_path": Path(preregistration_path).as_posix(),
        "preregistration_sha256": _sha256(preregistration_path),
        "cohort_id": manifest.get("cohort_id"),
        "cohort_sha256": _hash_value(sorted(case_ids)),
        "manifest_path": Path(manifest_path).as_posix(),
        "manifest_sha256": _sha256(manifest_path),
        "case_ids": sorted(case_ids),
        "case_count": len(case_ids),
        "contract": "case_ids_only_no_labels",
        "models": list(MODEL_IDS),
    }
    _create_json(out_path, artifact)
    return {"status": "prepared", "prepared": True, "artifact": Path(out_path).as_posix()}


def _chart(row: dict[str, Any]) -> tuple[str, tuple[str, str, str, str], tuple[str, ...]]:
    _assert_no_forbidden(row)
    case_id = row.get("case_id")
    pillars = row.get("four_pillars", row.get("pillars"))
    dayun = row.get("dayun", row.get("dayun_steps", ()))
    if not isinstance(case_id, str) or not isinstance(pillars, list) or len(pillars) != 4:
        raise ValueError("blind chart requires case_id and four_pillars[4]")
    if any(not isinstance(item, str) for item in pillars):
        raise ValueError("four_pillars must contain strings")
    dayun_values = tuple(
        str(item["ganzhi"]) if isinstance(item, dict) else str(item) for item in dayun
    ) if isinstance(dayun, list) else ()
    return case_id, tuple(pillars), dayun_values  # type: ignore[return-value]


def _legacy_prediction(case_id: str, pillars: tuple[str, ...], dayun: tuple[str, ...]) -> dict[str, Any]:
    state = classify_career_path(pillars, [{"ganzhi": item} for item in dayun], None)
    natal = state.natal_inclination
    if state.abstain_reason is not None or natal.employment_inclined == natal.entrepreneurship_inclined:
        prediction = "abstain"
    else:
        prediction = "employment" if natal.employment_inclined else "entrepreneurship"
    return {
        "case_id": case_id, "model_id": MODEL_IDS[1], "prediction": prediction,
        "career_pillar": None,
        "trace": {"adapter": "frozen_classifier_v3", "evidence_refs": list(natal.evidence_refs)},
    }


def _relation_prediction(case_id: str, pillars: tuple[str, ...]) -> dict[str, Any]:
    bazi = Bazi(
        年柱=GanZhi.parse(pillars[0]), 月柱=GanZhi.parse(pillars[1]),
        日柱=GanZhi.parse(pillars[2]), 时柱=GanZhi.parse(pillars[3]),
    )
    graph = build_career_relation_graph(bazi)
    decision = reason_natal_career_inclination(graph)
    employment = decision.inclination.employment_inclined
    entrepreneurship = decision.inclination.entrepreneurship_inclined
    if employment and entrepreneurship:
        prediction = "mixed"
    elif employment:
        prediction = "employment"
    elif entrepreneurship:
        prediction = "entrepreneurship"
    else:
        prediction = "abstain"
    selected = graph.inference.selected_pillar
    return {
        "case_id": case_id, "model_id": MODEL_IDS[2], "prediction": prediction,
        "career_pillar": selected.value if selected is not None else None,
        "trace": {
            "schema_version": graph.schema_version,
            "stage_trace": [
                {"stage": item.stage.value, "found_pillars": [p.value for p in item.found_pillars], "note": item.note}
                for item in graph.stage_trace
            ],
            "evidence_refs": list(decision.inclination.evidence_refs),
            "abstain_reason": decision.abstain_reason,
        },
    }


def predict_competition(prepare_path: Path, blind_input_path: Path, out_path: Path) -> dict[str, Any]:
    """无标签预测阶段；输入中出现泄漏字段即拒绝。"""
    prepared = _read_json(prepare_path)
    if prepared.get("stage") != "prepare" or prepared.get("contract") != "case_ids_only_no_labels":
        raise ValueError("invalid prepare artifact")
    _bound_hash_matches(
        Path(str(prepared["preregistration_path"])),
        prepared.get("preregistration_sha256"),
        "preregistration",
    )
    charts = {}
    for row in _read_jsonl(blind_input_path):
        case_id, pillars, dayun = _chart(row)
        if case_id in charts:
            raise ValueError("duplicate blind case_id")
        charts[case_id] = (pillars, dayun)
    if set(charts) != set(prepared["case_ids"]):
        raise ValueError("blind input IDs differ from prepared cohort")
    rows: list[dict[str, Any]] = []
    for case_id in prepared["case_ids"]:
        pillars, dayun = charts[case_id]
        rows.append({
            "case_id": case_id, "model_id": MODEL_IDS[0], "prediction": "abstain",
            "career_pillar": None, "trace": {"adapter": "no_label_majority_or_abstain", "reason": "majority_unknown_before_reveal"},
        })
        rows.append(_legacy_prediction(case_id, pillars, dayun))
        rows.append(_relation_prediction(case_id, pillars))
    _write_jsonl_create(out_path, rows)
    return {"status": "predicted", "case_count": len(charts), "prediction_rows": len(rows), "predictions_sha256": _sha256(out_path)}


def freeze_predictions(
    prepare_path: Path, predictions_path: Path, freeze_path: Path,
    *, preregistration_path: Path = DEFAULT_PREREGISTRATION,
) -> dict[str, Any]:
    """绑定 cohort、预注册、代码/规则版本和预测 SHA256。"""
    prepared = _read_json(prepare_path)
    prereg = _read_json(preregistration_path)
    _assert_id(prereg, str(prepared.get("preregistration_id")))
    _bound_hash_matches(
        preregistration_path, prepared.get("preregistration_sha256"), "preregistration"
    )
    rows = _read_jsonl(predictions_path)
    expected = {(case_id, model) for case_id in prepared["case_ids"] for model in MODEL_IDS}
    actual = {(row.get("case_id"), row.get("model_id")) for row in rows}
    if actual != expected or len(rows) != len(expected):
        raise ValueError("prediction case/model IDs mismatch")
    if any(row.get("prediction") not in PREDICTIONS for row in rows):
        raise ValueError("invalid prediction enum")
    rule_hashes = {path.as_posix(): _sha256(path) for path in RULE_PATHS}
    freeze = {
        "schema_version": "career-path-competition-freeze/v1", "stage": "freeze",
        "frozen_at": _now(), "one_shot_freeze": True, "one_score_only": True,
        "post_label_tuning_permitted": False,
        "preregistration_id": prereg["preregistration_id"],
        "preregistration_sha256": _sha256(preregistration_path),
        "cohort_sha256": prepared["cohort_sha256"],
        "prepare_path": Path(prepare_path).as_posix(), "prepare_sha256": _sha256(prepare_path),
        "predictions_path": Path(predictions_path).as_posix(), "predictions_sha256": _sha256(predictions_path),
        "code_version": {"path": HARNESS_PATH.as_posix(), "sha256": _sha256(HARNESS_PATH)},
        "rule_version": {"files": rule_hashes, "sha256": _hash_value(rule_hashes)},
        "models": list(MODEL_IDS), "case_ids": prepared["case_ids"], "case_count": prepared["case_count"],
    }
    _create_json(freeze_path, freeze)
    return {"status": "frozen", "freeze": Path(freeze_path).as_posix(), "predictions_sha256": freeze["predictions_sha256"]}


def reveal_labels(
    freeze_path: Path, labels_path: Path, reveal_path: Path,
    *, manifest_path: Path, registry_path: Path = DEFAULT_REGISTRY,
    preregistration_path: Path = DEFAULT_PREREGISTRATION,
    label_schema: str = "legacy_label_v1",
) -> dict[str, Any]:
    """冻结完成后才绑定标签制品；再次调用 holdout gate 防止绕过准入。"""
    freeze = _read_json(freeze_path)
    if freeze.get("stage") != "freeze" or not digest_matches(
        Path(str(freeze["predictions_path"])), freeze.get("predictions_sha256")
    ):
        raise ValueError("invalid or tampered freeze")
    gate = check_holdout_admission(manifest_path, labels_path, registry_path, preregistration_path)
    if not gate["ready"]:
        raise ValueError(f"holdout gate is not ready: {gate['failures']}")
    prereg = _read_json(preregistration_path)
    _assert_id(prereg, str(freeze.get("preregistration_id")))
    if label_schema not in {"legacy_label_v1", "career_path_temporal_v1"}:
        raise ValueError(f"unknown label schema: {label_schema}")
    reveal = {
        "schema_version": "career-path-competition-reveal/v1", "stage": "reveal", "revealed_at": _now(),
        "preregistration_id": freeze["preregistration_id"],
        "freeze_path": Path(freeze_path).as_posix(), "freeze_sha256": _sha256(freeze_path),
        "labels_path": Path(labels_path).as_posix(), "labels_sha256": _sha256(labels_path),
        "label_schema": label_schema,
    }
    _create_json(reveal_path, reveal)
    return {"status": "revealed", "reveal": Path(reveal_path).as_posix(), "labels_sha256": reveal["labels_sha256"]}


def _truth(row: dict[str, Any], schema: str) -> tuple[str, bool | None, str | None]:
    if schema == "legacy_label_v1":
        value = row.get("label")
    elif schema == "career_path_temporal_v1":
        value = row.get("reality_status_at_feedback")
    else:
        raise ValueError(f"unknown label schema: {schema}")
    mapping = {"employment": "employment", "entrepreneurship": "entrepreneurship", "employed": "employment", "entrepreneurial": "entrepreneurship", "mixed": "mixed", "transitioning": "transitioning"}
    if value not in mapping:
        raise ValueError(f"invalid label for {schema}")
    return mapping[str(value)], row.get("has_transition") if "has_transition" in row else None, row.get("career_pillar")


def _model_metrics(rows: list[dict[str, Any]], labels: dict[str, tuple[str, bool | None, str | None]]) -> dict[str, Any]:
    strict = [case_id for case_id, value in labels.items() if value[0] in {"employment", "entrepreneurship"}]
    recalls = {}
    for truth in ("employment", "entrepreneurship"):
        ids = [case_id for case_id in strict if labels[case_id][0] == truth]
        recalls[truth] = sum(next(row["prediction"] for row in rows if row["case_id"] == case_id) == truth for case_id in ids) / len(ids) if ids else 0.0
    predictions = {str(row["case_id"]): str(row["prediction"]) for row in rows}
    accuracy = sum(predictions[case_id] == labels[case_id][0] for case_id in strict) / len(strict) if strict else 0.0
    coverage = sum(predictions[case_id] != "abstain" for case_id in strict) / len(strict) if strict else 0.0
    truth_counts = {truth: sum(labels[case_id][0] == truth for case_id in strict) for truth in ("employment", "entrepreneurship")}
    result: dict[str, Any] = {
        "strict_binary_count": len(strict), "accuracy": accuracy,
        "balanced_accuracy": sum(recalls.values()) / 2,
        "employment_recall": recalls["employment"], "entrepreneurship_recall": recalls["entrepreneurship"],
        "coverage": coverage,
        "majority_class_baseline_accuracy": max(truth_counts.values(), default=0) / len(strict) if strict else 0.0,
    }
    for state in ("mixed", "transitioning"):
        ids = [case_id for case_id, value in labels.items() if value[0] == state]
        if ids:
            result[f"{state}_recognition"] = {"value": sum(predictions[i] == state for i in ids) / len(ids), "denominator": len(ids)}
    transition_ids = [case_id for case_id, value in labels.items() if value[1] is True]
    if transition_ids:
        result["has_transition_recognition"] = {"value": sum(predictions[i] in {"mixed", "transitioning"} for i in transition_ids) / len(transition_ids), "denominator": len(transition_ids)}
    pillar_ids = [case_id for case_id, value in labels.items() if isinstance(value[2], str)]
    if pillar_ids:
        by_id = {str(row["case_id"]): row for row in rows}
        result["career_pillar_location_consistency"] = {"value": sum(by_id[i].get("career_pillar") == labels[i][2] for i in pillar_ids) / len(pillar_ids), "denominator": len(pillar_ids)}
    result["trace_completeness"] = {"value": sum(bool(row.get("trace")) for row in rows) / len(rows) if rows else 0.0, "denominator": len(rows)}
    return result


def score_competition(
    reveal_path: Path,
    score_path: Path,
    receipt_path: Path,
    *,
    disposition_path: Path = DEFAULT_MODEL_DISPOSITION,
) -> dict[str, Any]:
    """一次评分；语义处置必须显式 eligible，且同一预注册只能评分一次。"""
    reveal = _read_json(reveal_path)
    freeze_path = Path(str(reveal["freeze_path"]))
    labels_path = Path(str(reveal["labels_path"]))
    if not digest_matches(freeze_path, reveal.get("freeze_sha256")) or not digest_matches(
        labels_path, reveal.get("labels_sha256")
    ):
        raise ValueError("reveal-bound artifact hash mismatch")
    freeze = _read_json(freeze_path)
    predictions_path = Path(str(freeze["predictions_path"]))
    if not digest_matches(predictions_path, freeze.get("predictions_sha256")):
        raise ValueError("prediction hash mismatch")
    if Path(receipt_path).exists():
        raise ValueError("preregistration_id has already been scored")
    assert_formal_model_eligibility(disposition_path)
    label_rows = _read_jsonl(labels_path)
    labels: dict[str, tuple[str, bool | None, str | None]] = {}
    for row in label_rows:
        case_id = row.get("case_id")
        if not isinstance(case_id, str) or case_id in labels:
            raise ValueError("invalid or duplicate label case_id")
        labels[case_id] = _truth(row, str(reveal["label_schema"]))
    predictions = _read_jsonl(predictions_path)
    if set(labels) != set(freeze["case_ids"]):
        raise ValueError("label IDs differ from frozen cohort")
    metrics = {}
    for model_id in MODEL_IDS:
        rows = [row for row in predictions if row.get("model_id") == model_id]
        if len(rows) != len(labels) or {row.get("case_id") for row in rows} != set(labels):
            raise ValueError("prediction IDs differ from labels")
        metrics[model_id] = _model_metrics(rows, labels)
    candidate = metrics[MODEL_IDS[2]]
    prereg = _read_json(DEFAULT_PREREGISTRATION)
    thresholds = prereg["promotion_thresholds"]
    checks = {
        "min_balanced_accuracy": candidate["balanced_accuracy"] >= thresholds["min_balanced_accuracy"],
        "min_employment_recall": candidate["employment_recall"] >= thresholds["min_employment_recall"],
        "min_entrepreneurship_recall": candidate["entrepreneurship_recall"] >= thresholds["min_entrepreneurship_recall"],
        "min_coverage": candidate["coverage"] >= thresholds["min_coverage"],
        "beats_majority_baseline": candidate["accuracy"] > candidate["majority_class_baseline_accuracy"],
        "beats_frozen_counting_baseline": candidate["balanced_accuracy"] > metrics[MODEL_IDS[1]]["balanced_accuracy"],
    }
    score = {
        "schema_version": "career-path-competition-score/v1", "stage": "score", "scored_at": _now(),
        "preregistration_id": freeze["preregistration_id"], "one_score_only": True,
        "freeze_sha256": _sha256(freeze_path), "predictions_sha256": freeze["predictions_sha256"],
        "labels_sha256": reveal["labels_sha256"], "metrics": metrics, "promotion_checks": checks,
        "eligible": all(checks.values()), "post_score_tuning_permitted": False,
    }
    receipt = {"preregistration_id": freeze["preregistration_id"], "score_sha256": _hash_value(score), "scored_at": score["scored_at"]}
    _create_json(receipt_path, receipt)
    try:
        _create_json(score_path, score)
    except Exception:
        Path(receipt_path).unlink(missing_ok=True)
        raise
    return {"status": "scored", "eligible": score["eligible"], "score": Path(score_path).as_posix()}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("status")
    prepare = commands.add_parser("prepare")
    prepare.add_argument("--manifest", type=Path, required=True); prepare.add_argument("--labels", type=Path, required=True); prepare.add_argument("--out", type=Path, required=True)
    predict = commands.add_parser("predict")
    predict.add_argument("--prepare", type=Path, required=True); predict.add_argument("--input", type=Path, required=True); predict.add_argument("--out", type=Path, required=True)
    freeze = commands.add_parser("freeze")
    freeze.add_argument("--prepare", type=Path, required=True); freeze.add_argument("--predictions", type=Path, required=True); freeze.add_argument("--out", type=Path, required=True)
    reveal = commands.add_parser("reveal")
    reveal.add_argument("--freeze", type=Path, required=True); reveal.add_argument("--labels", type=Path, required=True); reveal.add_argument("--manifest", type=Path, required=True); reveal.add_argument("--out", type=Path, required=True); reveal.add_argument("--label-schema", choices=("legacy_label_v1", "career_path_temporal_v1"), required=True)
    score = commands.add_parser("score")
    score.add_argument("--reveal", type=Path, required=True); score.add_argument("--out", type=Path, required=True); score.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.command == "status": result = current_status()
    elif args.command == "prepare": result = prepare_experiment(args.manifest, args.labels, args.out)
    elif args.command == "predict": result = predict_competition(args.prepare, args.input, args.out)
    elif args.command == "freeze": result = freeze_predictions(args.prepare, args.predictions, args.out)
    elif args.command == "reveal": result = reveal_labels(args.freeze, args.labels, args.out, manifest_path=args.manifest, label_schema=args.label_schema)
    else: result = score_competition(args.reveal, args.out, args.receipt)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result.get("status") not in {"not_ready", "rejected"} else 1


if __name__ == "__main__":
    raise SystemExit(main())

"""事业角色变化 development replay 的物理隔离双模型 harness。

流程被拆成三个独立命令和进程边界：

``predict-freeze`` 只读取 chart-only blind cohort；
``reveal-score`` 只在读取已冻结制品后才读取 labels artifact；
``compare`` 只读取已评分制品并计算模型差值。

所有结果固定标记为 ``development_replay_only``，不得用于 Calibration、正式
准确率声明或 production promotion。
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from engine.asof.career_event_prediction import (
    CareerPredictionWindow,
    predict_career_role_change,
)
from engine.claims.orchestrator import chart_ledger_from_mapping
from engine.evaluation.career_event_replay import (
    CAREER_EVENT_LABEL_SCHEMA,
    CareerEventReplayPrediction,
    FrozenCareerEventReplay,
    freeze_career_event_replay_predictions,
    project_career_event_prediction,
    project_legacy_ren_career_event_prediction,
    reveal_career_event_labels,
    score_career_event_replay,
    verify_frozen_career_event_replay,
)
from engine.predicates.cycles import liunian_ganzhi

_BLIND_COHORT_SCHEMA = "career-event-development-replay-blind-cohort/v1"
_LABEL_SOURCE_SCHEMA = "career-event-development-replay-labels/v1"
_FREEZE_BUNDLE_SCHEMA = "career-event-development-replay-freeze-bundle/v1"
_SCORE_BUNDLE_SCHEMA = "career-event-development-replay-score-bundle/v1"
_COMPARISON_SCHEMA = "career-event-development-replay-comparison/v1"
_DATASET_CLASSIFICATION = "development_replay_only"
_FORBIDDEN_BLIND_KEYS = frozenset(
    {
        "label",
        "labels",
        "no_event_cases",
        "source_ref",
        "confidence_grade",
        "known_facts",
        "known_fact_text",
        "feedback",
        "verification",
        "truth",
        "observed",
        "calibration",
        "event_type",
        "direction",
        "magnitude",
        "event_text",
        "evidence_quote",
    }
)


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("JSON root must be an object")
    return value


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _assert_exact_keys(
    document: Mapping[str, Any],
    required: set[str],
    message: str,
) -> None:
    if set(document) != required:
        raise ValueError(message)


def _assert_development_boundary(document: Mapping[str, Any], artifact: str) -> None:
    if document.get("dataset_classification") != _DATASET_CLASSIFICATION:
        raise ValueError(f"{artifact} classification must remain fixed")
    if document.get("promotion_eligible") is not False:
        raise ValueError(f"{artifact} cannot be promotion eligible")
    if document.get("unseen_holdout_evidence") != "none":
        raise ValueError(f"{artifact} cannot claim unseen holdout evidence")


def _assert_no_revealed_keys(value: object, path: str = "root") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            normalized = str(key).strip().lower()
            if normalized in _FORBIDDEN_BLIND_KEYS:
                raise ValueError(f"revealed field is forbidden in blind cohort: {path}.{key}")
            _assert_no_revealed_keys(child, f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            _assert_no_revealed_keys(child, f"{path}[{index}]")


def _validate_blind_cohort(document: Mapping[str, Any]) -> None:
    _assert_exact_keys(
        document,
        {
            "schema_version",
            "dataset_id",
            "dataset_classification",
            "promotion_eligible",
            "unseen_holdout_evidence",
            "normalization_policy",
            "charts",
            "replay_units",
        },
        "career event blind cohort schema is invalid",
    )
    if document.get("schema_version") != _BLIND_COHORT_SCHEMA:
        raise ValueError("unexpected career event blind cohort schema_version")
    _assert_development_boundary(document, "blind cohort")
    if not isinstance(document.get("dataset_id"), str) or not document["dataset_id"]:
        raise ValueError("blind cohort dataset_id must be non-empty")
    if not isinstance(document.get("normalization_policy"), Mapping):
        raise ValueError("blind cohort normalization_policy must be an object")
    if not isinstance(document.get("charts"), list) or not isinstance(
        document.get("replay_units"), list
    ):
        raise ValueError("blind cohort charts and replay_units must be lists")
    _assert_no_revealed_keys(document)


def _validate_label_source(document: Mapping[str, Any]) -> None:
    _assert_exact_keys(
        document,
        {
            "schema_version",
            "dataset_id",
            "dataset_classification",
            "promotion_eligible",
            "unseen_holdout_evidence",
            "normalization_policy",
            "labels",
            "no_event_cases",
        },
        "career event labels source schema is invalid",
    )
    if document.get("schema_version") != _LABEL_SOURCE_SCHEMA:
        raise ValueError("unexpected career event labels source schema_version")
    _assert_development_boundary(document, "labels source")
    if not isinstance(document.get("dataset_id"), str) or not document["dataset_id"]:
        raise ValueError("labels source dataset_id must be non-empty")
    if not isinstance(document.get("normalization_policy"), Mapping):
        raise ValueError("labels source normalization_policy must be an object")
    if not isinstance(document.get("labels"), list) or not isinstance(
        document.get("no_event_cases"), list
    ):
        raise ValueError("labels and no_event_cases must be lists")


def _chart_index(document: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    charts: dict[str, dict[str, Any]] = {}
    for raw in document["charts"]:
        if not isinstance(raw, dict) or set(raw) != {
            "source_case_id",
            "sex_marker",
            "four_pillars",
            "dayun_steps",
        }:
            raise ValueError("blind cohort chart record is invalid")
        case_id = raw["source_case_id"]
        pillars = raw["four_pillars"]
        dayun_steps = raw["dayun_steps"]
        if (
            not isinstance(case_id, str)
            or not case_id
            or case_id in charts
            or raw["sex_marker"] not in {"乾", "坤"}
            or not isinstance(pillars, list)
            or len(pillars) != 4
            or any(not isinstance(item, str) or len(item) != 2 for item in pillars)
            or not isinstance(dayun_steps, list)
        ):
            raise ValueError("blind cohort chart values are invalid")
        charts[case_id] = raw
    return charts


def _dayun_for_year(dayun_steps: Sequence[Mapping[str, Any]], year: int) -> str:
    matches = [
        str(step.get("ganzhi", ""))
        for step in dayun_steps
        if type(step.get("start_year")) is int
        and type(step.get("end_year")) is int
        and int(step["start_year"]) <= year <= int(step["end_year"])
    ]
    if len(matches) != 1 or len(matches[0]) != 2:
        raise ValueError(f"replay year {year} requires exactly one declared dayun")
    return matches[0]


def _prediction_inputs(document: Mapping[str, Any]) -> tuple[dict[str, Any], ...]:
    charts = _chart_index(document)
    units: list[dict[str, Any]] = []
    replay_ids: set[str] = set()
    for raw in document["replay_units"]:
        if not isinstance(raw, dict) or set(raw) != {"replay_id", "source_case_id", "year"}:
            raise ValueError("replay unit is invalid")
        replay_id = raw["replay_id"]
        source_case_id = raw["source_case_id"]
        year = raw["year"]
        if (
            not isinstance(replay_id, str)
            or replay_id in replay_ids
            or not isinstance(source_case_id, str)
            or source_case_id not in charts
            or type(year) is not int
            or replay_id != f"{source_case_id}@{year}"
        ):
            raise ValueError("replay unit identity is invalid")
        replay_ids.add(replay_id)
        raw_chart = charts[source_case_id]
        dayun = _dayun_for_year(raw_chart["dayun_steps"], year)
        units.append(
            {
                "replay_id": replay_id,
                "year": year,
                "chart": chart_ledger_from_mapping(
                    {
                        "sex_marker": raw_chart["sex_marker"],
                        "four_pillars": raw_chart["four_pillars"],
                        "dayun_steps": raw_chart["dayun_steps"],
                        "liunian_steps": [
                            {
                                "year": year,
                                "ganzhi": str(liunian_ganzhi(year)),
                                "dayun": dayun,
                            }
                        ],
                    }
                ),
            }
        )
    if not units:
        raise ValueError("blind cohort requires at least one replay unit")
    return tuple(sorted(units, key=lambda item: item["replay_id"]))


def _freeze_predictions(
    predictions: Sequence[CareerEventReplayPrediction],
    *,
    dataset_id: str,
) -> FrozenCareerEventReplay:
    return freeze_career_event_replay_predictions(
        predictions,
        dataset_id=dataset_id,
        dataset_classification=_DATASET_CLASSIFICATION,
    )


def predict_and_freeze_blind_cohort(
    blind_document: Mapping[str, Any],
) -> dict[str, Any]:
    """只消费 chart-only artifact，生成两模型冻结制品。"""

    _validate_blind_cohort(blind_document)
    units = _prediction_inputs(blind_document)
    legacy_predictions: list[CareerEventReplayPrediction] = []
    shared_predictions: list[CareerEventReplayPrediction] = []
    for unit in units:
        window = CareerPredictionWindow(unit["year"], unit["year"], "historical")
        legacy_predictions.append(
            project_legacy_ren_career_event_prediction(
                case_id=unit["replay_id"],
                chart=unit["chart"],
                window=window,
            )
        )
        shared_predictions.append(
            project_career_event_prediction(
                predict_career_role_change(
                    case_id=unit["replay_id"],
                    chart=unit["chart"],
                    window=window,
                )
            )
        )
    dataset_id = str(blind_document["dataset_id"])
    legacy = _freeze_predictions(
        legacy_predictions,
        dataset_id=f"{dataset_id}:legacy-ren",
    )
    shared = _freeze_predictions(
        shared_predictions,
        dataset_id=f"{dataset_id}:shared-structure-event-timing",
    )
    if {item.case_id for item in legacy.predictions} != {
        item.case_id for item in shared.predictions
    }:
        raise ValueError("legacy and shared freezes must cover identical replay units")
    payload: dict[str, Any] = {
        "schema_version": _FREEZE_BUNDLE_SCHEMA,
        "dataset_id": dataset_id,
        "dataset_classification": _DATASET_CLASSIFICATION,
        "promotion_eligible": False,
        "unseen_holdout_evidence": "none",
        "blind_cohort_digest": _digest(blind_document),
        "replay_unit_count": len(units),
        "legacy_freeze": legacy.to_dict(),
        "shared_freeze": shared.to_dict(),
    }
    payload["freeze_bundle_hash"] = _digest(payload)
    return payload


def _validate_freeze_bundle(document: Mapping[str, Any]) -> tuple[FrozenCareerEventReplay, FrozenCareerEventReplay]:
    _assert_exact_keys(
        document,
        {
            "schema_version",
            "dataset_id",
            "dataset_classification",
            "promotion_eligible",
            "unseen_holdout_evidence",
            "blind_cohort_digest",
            "replay_unit_count",
            "legacy_freeze",
            "shared_freeze",
            "freeze_bundle_hash",
        },
        "career event freeze bundle schema is invalid",
    )
    if document.get("schema_version") != _FREEZE_BUNDLE_SCHEMA:
        raise ValueError("unexpected career event freeze bundle schema_version")
    _assert_development_boundary(document, "freeze bundle")
    if type(document.get("replay_unit_count")) is not int or document["replay_unit_count"] < 1:
        raise ValueError("freeze bundle replay_unit_count must be positive")
    unsigned = {key: value for key, value in document.items() if key != "freeze_bundle_hash"}
    if document.get("freeze_bundle_hash") != _digest(unsigned):
        raise ValueError("career event freeze bundle hash mismatch")
    if not isinstance(document.get("legacy_freeze"), Mapping) or not isinstance(
        document.get("shared_freeze"), Mapping
    ):
        raise ValueError("freeze bundle model freezes must be objects")
    legacy = FrozenCareerEventReplay.from_dict(document["legacy_freeze"])
    shared = FrozenCareerEventReplay.from_dict(document["shared_freeze"])
    verify_frozen_career_event_replay(legacy)
    verify_frozen_career_event_replay(shared)
    base = str(document["dataset_id"])
    if legacy.dataset_id != f"{base}:legacy-ren" or shared.dataset_id != (
        f"{base}:shared-structure-event-timing"
    ):
        raise ValueError("freeze bundle model dataset identities are invalid")
    if legacy.model_id == shared.model_id:
        raise ValueError("freeze bundle requires distinct legacy and shared model IDs")
    legacy_cases = {item.case_id for item in legacy.predictions}
    shared_cases = {item.case_id for item in shared.predictions}
    if legacy_cases != shared_cases or len(legacy_cases) != document["replay_unit_count"]:
        raise ValueError("freeze bundle replay unit coverage mismatch")
    return legacy, shared


def _bound_labels(document: Mapping[str, Any], freeze_hash: str) -> dict[str, Any]:
    return {
        "schema_version": CAREER_EVENT_LABEL_SCHEMA,
        "freeze_hash": freeze_hash,
        "labels": document["labels"],
        "no_event_cases": document["no_event_cases"],
    }


def _score_frozen_model(
    frozen: FrozenCareerEventReplay,
    labels_document: Mapping[str, Any],
) -> dict[str, Any]:
    revealed = reveal_career_event_labels(
        frozen,
        _bound_labels(labels_document, frozen.freeze_hash),
    )
    return score_career_event_replay(frozen, revealed).to_dict()


def reveal_and_score_frozen_replay(
    freeze_bundle: Mapping[str, Any],
    labels_document: Mapping[str, Any],
) -> dict[str, Any]:
    """冻结完整性通过后才接纳独立 labels artifact 并评分。"""

    legacy, shared = _validate_freeze_bundle(freeze_bundle)
    _validate_label_source(labels_document)
    if labels_document["dataset_id"] != freeze_bundle["dataset_id"]:
        raise ValueError("labels source dataset_id does not match freeze bundle")
    payload: dict[str, Any] = {
        "schema_version": _SCORE_BUNDLE_SCHEMA,
        "dataset_id": freeze_bundle["dataset_id"],
        "dataset_classification": _DATASET_CLASSIFICATION,
        "promotion_eligible": False,
        "unseen_holdout_evidence": "none",
        "blind_cohort_digest": freeze_bundle["blind_cohort_digest"],
        "labels_digest": _digest(labels_document),
        "replay_unit_count": freeze_bundle["replay_unit_count"],
        "freeze_bundle_hash": freeze_bundle["freeze_bundle_hash"],
        "legacy": {
            "freeze": legacy.to_dict(),
            "score": _score_frozen_model(legacy, labels_document),
        },
        "shared": {
            "freeze": shared.to_dict(),
            "score": _score_frozen_model(shared, labels_document),
        },
    }
    payload["score_bundle_hash"] = _digest(payload)
    return payload


def _validate_score_bundle(document: Mapping[str, Any]) -> None:
    _assert_exact_keys(
        document,
        {
            "schema_version",
            "dataset_id",
            "dataset_classification",
            "promotion_eligible",
            "unseen_holdout_evidence",
            "blind_cohort_digest",
            "labels_digest",
            "replay_unit_count",
            "freeze_bundle_hash",
            "legacy",
            "shared",
            "score_bundle_hash",
        },
        "career event score bundle schema is invalid",
    )
    if document.get("schema_version") != _SCORE_BUNDLE_SCHEMA:
        raise ValueError("unexpected career event score bundle schema_version")
    _assert_development_boundary(document, "score bundle")
    unsigned = {key: value for key, value in document.items() if key != "score_bundle_hash"}
    if document.get("score_bundle_hash") != _digest(unsigned):
        raise ValueError("career event score bundle hash mismatch")
    for model_name in ("legacy", "shared"):
        model = document.get(model_name)
        if not isinstance(model, Mapping) or set(model) != {"freeze", "score"}:
            raise ValueError("score bundle model record is invalid")
        if not isinstance(model["freeze"], Mapping) or not isinstance(model["score"], Mapping):
            raise ValueError("score bundle freeze and score must be objects")
        frozen = FrozenCareerEventReplay.from_dict(model["freeze"])
        verify_frozen_career_event_replay(frozen)
        score = model["score"]
        required_score = {
            "schema_version",
            "dataset_id",
            "dataset_classification",
            "model_id",
            "freeze_hash",
            "case_scores",
            "metrics",
        }
        if set(score) != required_score:
            raise ValueError("score bundle model score schema is invalid")
        if (
            score["dataset_id"] != frozen.dataset_id
            or score["dataset_classification"] != frozen.dataset_classification
            or score["model_id"] != frozen.model_id
            or score["freeze_hash"] != frozen.freeze_hash
            or not isinstance(score["case_scores"], list)
            or not isinstance(score["metrics"], Mapping)
        ):
            raise ValueError("score bundle model score does not bind to its freeze")


def _metric_delta(
    shared: Mapping[str, Any],
    legacy: Mapping[str, Any],
) -> dict[str, float | int]:
    metric_names = (
        "predicted_case_count",
        "abstain_count",
        "coverage",
        "timing_hit_rate",
        "event_type_hit_rate",
        "domain_hit_rate",
        "direction_hit_rate",
        "magnitude_hit_rate",
        "false_positive_count",
        "false_positive_rate",
        "false_negative_count",
        "false_negative_rate",
    )
    return {
        name: round(float(shared[name]) - float(legacy[name]), 6)
        for name in metric_names
    }


def compare_scored_replay(score_bundle: Mapping[str, Any]) -> dict[str, Any]:
    """只消费已评分制品，计算 legacy/shared 指标差值。"""

    _validate_score_bundle(score_bundle)
    legacy = score_bundle["legacy"]
    shared = score_bundle["shared"]
    payload: dict[str, Any] = {
        "schema_version": _COMPARISON_SCHEMA,
        "dataset_id": score_bundle["dataset_id"],
        "dataset_classification": _DATASET_CLASSIFICATION,
        "promotion_eligible": False,
        "unseen_holdout_evidence": "none",
        "blind_cohort_digest": score_bundle["blind_cohort_digest"],
        "labels_digest": score_bundle["labels_digest"],
        "freeze_bundle_hash": score_bundle["freeze_bundle_hash"],
        "score_bundle_hash": score_bundle["score_bundle_hash"],
        "replay_unit_count": score_bundle["replay_unit_count"],
        "legacy": legacy,
        "shared": shared,
        "metric_delta_shared_minus_legacy": _metric_delta(
            shared["score"]["metrics"],
            legacy["score"]["metrics"],
        ),
        "physical_isolation": {
            "predict_freeze_input": "chart-only blind cohort",
            "reveal_score_input": "sealed freeze bundle plus separate labels artifact",
            "compare_input": "score bundle only",
        },
        "interpretation": (
            "development_replay_only: estimates describe this exposed historical cohort only; "
            "they are not formal accuracy, calibration, holdout, or production-promotion evidence."
        ),
    }
    payload["comparison_hash"] = _digest(payload)
    return payload


def _render_markdown(payload: Mapping[str, Any]) -> str:
    legacy = payload["legacy"]["score"]["metrics"]
    shared = payload["shared"]["score"]["metrics"]
    delta = payload["metric_delta_shared_minus_legacy"]
    rows = []
    for name in (
        "predicted_case_count",
        "abstain_count",
        "coverage",
        "timing_hit_rate",
        "event_type_hit_rate",
        "domain_hit_rate",
        "direction_hit_rate",
        "magnitude_hit_rate",
        "false_positive_count",
        "false_positive_rate",
        "false_negative_count",
        "false_negative_rate",
    ):
        rows.append(f"| `{name}` | {legacy[name]} | {shared[name]} | {delta[name]} |")
    return "\n".join(
        [
            "# Phase 2 事业角色变化 development replay 双模型比较",
            "",
            "## 证据边界",
            "- 数据分类：`development_replay_only`。",
            "- `promotion_eligible = false`。",
            "- `unseen_holdout_evidence = none`。",
            "- `predict-freeze` 进程只读取 chart-only blind cohort；标签保存在独立 artifact，并由后续 `reveal-score` 进程读取。",
            "- 本结果只比较已暴露历史 cohort 上的旧 Ren `Timing → Event` 与共享 `Structure → Event → Timing`；不得表述为正式准确率提升。",
            "",
            "## 指标",
            "| 指标 | legacy Ren | shared | shared - legacy |",
            "|---|---:|---:|---:|",
            *rows,
            "",
            "## 解释",
            "- 结构门降低覆盖并抑制 timing-only 事件声明，但在当前 cohort 上增加了假阴性。",
            "- 方向维度仍受共享结构规则 `neutral` 输出限制；当前对比用于暴露瓶颈，不用于 Calibration。",
            f"- blind cohort digest：`{payload['blind_cohort_digest']}`。",
            f"- labels digest：`{payload['labels_digest']}`。",
            f"- freeze bundle hash：`{payload['freeze_bundle_hash']}`。",
            f"- score bundle hash：`{payload['score_bundle_hash']}`。",
            f"- comparison hash：`{payload['comparison_hash']}`。",
            "",
        ]
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run physically isolated legacy/shared career event development replay."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    predict = subparsers.add_parser(
        "predict-freeze",
        help="Read only a chart-only blind cohort and write sealed model freezes.",
    )
    predict.add_argument("--blind-cohort", type=Path, required=True)
    predict.add_argument("--out-freeze", type=Path, required=True)

    reveal = subparsers.add_parser(
        "reveal-score",
        help="Read sealed freezes, then reveal a separate labels artifact and score.",
    )
    reveal.add_argument("--freeze", type=Path, required=True)
    reveal.add_argument("--labels", type=Path, required=True)
    reveal.add_argument("--out-score", type=Path, required=True)

    compare = subparsers.add_parser(
        "compare",
        help="Read only the score bundle and emit comparison artifacts.",
    )
    compare.add_argument("--score", type=Path, required=True)
    compare.add_argument("--out-json", type=Path)
    compare.add_argument("--out-md", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    if args.command == "predict-freeze":
        payload = predict_and_freeze_blind_cohort(_read_json(args.blind_cohort))
        _write_json(args.out_freeze, payload)
        return 0
    if args.command == "reveal-score":
        freeze_bundle = _read_json(args.freeze)
        _validate_freeze_bundle(freeze_bundle)
        labels_document = _read_json(args.labels)
        payload = reveal_and_score_frozen_replay(freeze_bundle, labels_document)
        _write_json(args.out_score, payload)
        return 0
    if args.command == "compare":
        payload = compare_scored_replay(_read_json(args.score))
        if args.out_json is not None:
            _write_json(args.out_json, payload)
        if args.out_md is not None:
            args.out_md.parent.mkdir(parents=True, exist_ok=True)
            args.out_md.write_text(_render_markdown(payload), encoding="utf-8")
        if args.out_json is None and args.out_md is None:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    raise AssertionError("unreachable command")


if __name__ == "__main__":
    raise SystemExit(main())

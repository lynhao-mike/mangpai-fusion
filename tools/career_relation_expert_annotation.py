"""职业关系模型专家中间结构盲标、双审裁决与一致率门禁。

本工具仅用于结构机制审计与新 model_id 设计；不执行模型评分，不解禁
career-path-relation-model-v1，也不切换生产入口。所有写操作默认 dry-run，
正式写入为 create-only，并拒绝符号链接。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any, Iterable, Sequence


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DISPOSITION = ROOT / "META/as-of-evaluation/career-relation-model-v1-disposition.json"
MODEL_ID = "career-path-relation-model-v1"
EXPECTED_DECISION = "invalidated_requires_new_model_id"
PERMITTED_USES = ["structural_mechanism_audit", "new_model_id_design"]

STAGES = {
    "step_1_self_officer_killing",
    "step_2_self_officer_killing_tomb",
    "step_3_other_officer_killing_linked_to_hour",
    "step_4_wealth_or_wealth_tomb",
    "step_5_formation_star_linked_to_self",
}
PILLARS = {"year", "month", "day", "hour"}
NATURES = {"正财", "偏财", "印", "食伤", "官杀", "比劫"}
STRENGTH_STATES = {"无", "弱", "中", "强", "极强", "unresolved"}
SEMANTIC_LAYERS = {
    "career_type",
    "career_nature",
    "income_mode",
    "organization_form",
    "reality_state",
}
LAYER_STATUSES = {"annotated", "unresolved", "abstained", "out_of_scope"}
FORBIDDEN_BLIND_KEYS = {
    "occupation",
    "feedback",
    "known_fact",
    "known_facts",
    "knownfacts",
    "career_label",
    "career_labels",
    "label",
    "labels",
    "model_prediction",
    "model_predictions",
    "prediction",
    "predictions",
    "reality_state",
    "reality_status",
}
UNSUPPORTED_ANNOTATION_FIELDS = {
    "employment_inclined",
    "entrepreneurship_inclined",
    "employment",
    "entrepreneurship",
    "terminal_label",
}
METRIC_FIELDS = {
    "career_pillar": "career_pillar",
    "selected_stage": "selected_stage",
    "left_pillar": "left_pillar",
    "key_relation_set": "key_relations",
    "nature_label_set": "nature_labels",
    "abstention": "abstention_reason",
}
HUMAN_ID = re.compile(r"^human-[A-Za-z0-9][A-Za-z0-9._-]*$")


def _canonical(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def canonical_sha256(value: object) -> str:
    """Return the SHA-256 of canonical JSON bytes."""
    return hashlib.sha256(_canonical(value)).hexdigest()


def _normal_key(value: object) -> str:
    return re.sub(r"[\s-]+", "_", str(value).strip().lower())


def _assert_no_blind_leakage(value: object, path: str = "root") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = _normal_key(key)
            if normalized in FORBIDDEN_BLIND_KEYS:
                raise ValueError(f"blind packet leakage at {path}.{key}")
            _assert_no_blind_leakage(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _assert_no_blind_leakage(child, f"{path}[{index}]")


def _reject_symlink_chain(path: Path, description: str) -> None:
    current = path
    while True:
        if current.is_symlink():
            raise ValueError(f"{description} must not contain a symlink: {current}")
        if current.parent == current:
            return
        current = current.parent


def _write_new_json(path: Path, payload: object, *, dry_run: bool) -> None:
    path = Path(path)
    _reject_symlink_chain(path, "output path")
    if path.exists() or path.is_symlink():
        raise ValueError(f"output target must not exist: {path}")
    if dry_run:
        return
    _reject_symlink_chain(path.parent, "output parent")
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as stream:
            json.dump(payload, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.rename(temporary, path)
    except BaseException:
        try:
            temporary.unlink(missing_ok=True)
        finally:
            raise


def _read_json(path: Path) -> dict[str, Any]:
    if path.is_symlink():
        raise ValueError(f"input must not be a symlink: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON object required: {path}")
    return value


def _require_human(identity: object, role: str) -> str:
    if not isinstance(identity, str) or not HUMAN_ID.fullmatch(identity):
        raise ValueError(f"{role} must identify a human reviewer using human-*")
    return identity


def prepare_blind_packet(
    chart: dict[str, Any],
    theory_refs: list[dict[str, str]],
    *,
    output: Path | None = None,
    dry_run: bool = True,
) -> dict[str, Any]:
    """Build a whitelist-only deterministic packet; write only when explicitly requested."""
    if not isinstance(chart, dict) or not isinstance(chart.get("case_id"), str):
        raise ValueError("chart must be an object with case_id")
    if not isinstance(theory_refs, list) or not theory_refs:
        raise ValueError("at least one frozen theory reference is required")
    _assert_no_blind_leakage(chart)
    _assert_no_blind_leakage(theory_refs)
    safe_refs: list[dict[str, str]] = []
    for reference in theory_refs:
        if not isinstance(reference, dict) or set(reference) != {"path", "sha256", "scope"}:
            raise ValueError("theory reference fields must be path, sha256, and scope")
        if not re.fullmatch(r"[0-9a-f]{64}", reference["sha256"]):
            raise ValueError("theory reference sha256 must be lowercase SHA-256")
        safe_refs.append(dict(reference))
    safe_refs.sort(key=lambda row: (row["path"], row["sha256"], row["scope"]))
    packet = {
        "schema_version": "career-relation-blind-packet/v1",
        "case_id": chart["case_id"],
        "safe_chart_facts": chart,
        "frozen_theory_references": safe_refs,
        "annotation_scope": "intermediate_structure_only",
    }
    result = {
        "packet": packet,
        "manifest": {
            "schema_version": "career-relation-blind-manifest/v1",
            "case_id": chart["case_id"],
            "content_sha256": canonical_sha256(packet),
            "permitted_uses": PERMITTED_USES,
            "formal_scoring_permitted": False,
            "promotion_eligible": False,
            "production_switch_permitted": False,
        },
    }
    if output is not None:
        _write_new_json(Path(output), result, dry_run=dry_run)
    return result


def validate_annotation(annotation: dict[str, Any]) -> None:
    """Validate one human intermediate-structure annotation without inferring values."""
    if not isinstance(annotation, dict):
        raise ValueError("annotation must be an object")
    unsupported = set(annotation) & UNSUPPORTED_ANNOTATION_FIELDS
    if unsupported:
        raise ValueError(f"unsupported terminal field(s): {sorted(unsupported)}")
    required = {
        "schema_version",
        "case_id",
        "blind_packet_sha256",
        "reviewer_id",
        "career_pillar",
        "selected_stage",
        "left_pillar",
        "key_relations",
        "nature_labels",
        "strength_state",
        "semantic_layers",
        "unresolved_items",
        "conflicts",
        "abstention_reason",
        "signed_at",
    }
    if set(annotation) != required:
        raise ValueError(f"annotation fields mismatch: expected {sorted(required)}")
    if annotation["schema_version"] != "career-relation-expert-annotation/v1":
        raise ValueError("annotation schema_version mismatch")
    _require_human(annotation["reviewer_id"], "reviewer_id")
    if not isinstance(annotation["case_id"], str) or not annotation["case_id"]:
        raise ValueError("case_id is required")
    if not re.fullmatch(r"[0-9a-f]{64}", str(annotation["blind_packet_sha256"])):
        raise ValueError("blind_packet_sha256 must be SHA-256")
    abstaining = annotation["abstention_reason"] is not None
    if annotation["career_pillar"] is not None and annotation["career_pillar"] not in PILLARS:
        raise ValueError("career_pillar is invalid")
    if annotation["selected_stage"] is not None and annotation["selected_stage"] not in STAGES:
        raise ValueError("selected_stage is invalid")
    if annotation["left_pillar"] is not None and annotation["left_pillar"] not in PILLARS:
        raise ValueError("left_pillar is invalid")
    if not isinstance(annotation["key_relations"], list) or not all(
        isinstance(value, str) and value for value in annotation["key_relations"]
    ):
        raise ValueError("key_relations must be a string list")
    if len(annotation["key_relations"]) != len(set(annotation["key_relations"])):
        raise ValueError("key_relations must not contain duplicates")
    if not isinstance(annotation["nature_labels"], list) or not set(annotation["nature_labels"]) <= NATURES:
        raise ValueError("nature_labels must use the six frozen nature categories")
    if len(annotation["nature_labels"]) != len(set(annotation["nature_labels"])):
        raise ValueError("nature_labels must not contain duplicates")
    if annotation["strength_state"] not in STRENGTH_STATES:
        raise ValueError("strength_state is invalid")
    layers = annotation["semantic_layers"]
    if not isinstance(layers, dict) or set(layers) != SEMANTIC_LAYERS:
        raise ValueError("semantic_layers must keep all five layers separate")
    for name, layer in layers.items():
        if not isinstance(layer, dict) or set(layer) != {"status", "value"}:
            raise ValueError(f"semantic layer {name} must contain status and value")
        if layer["status"] not in LAYER_STATUSES:
            raise ValueError(f"semantic layer {name} status is invalid")
        if name == "reality_state" and layer != {"status": "out_of_scope", "value": None}:
            raise ValueError("reality_state must remain out_of_scope in blind annotation")
    for field in ("unresolved_items", "conflicts"):
        if not isinstance(annotation[field], list) or not all(isinstance(value, str) for value in annotation[field]):
            raise ValueError(f"{field} must be a string list")
    if abstaining:
        if not isinstance(annotation["abstention_reason"], str) or not annotation["abstention_reason"]:
            raise ValueError("abstention_reason must be a non-empty string or null")
    elif any(annotation[name] is None for name in ("career_pillar", "selected_stage", "left_pillar")):
        raise ValueError("missing structural values require abstention_reason")


def submit_annotation(annotation: dict[str, Any], output: Path, *, dry_run: bool = True) -> dict[str, Any]:
    """Validate and create one immutable raw human submission."""
    validate_annotation(annotation)
    _write_new_json(Path(output), annotation, dry_run=dry_run)
    return annotation


def _same_binding(left: dict[str, Any], right: dict[str, Any]) -> None:
    for field in ("case_id", "blind_packet_sha256"):
        if left[field] != right[field]:
            raise ValueError(f"annotations must share {field}")


def _has_disagreement(left: dict[str, Any], right: dict[str, Any]) -> bool:
    for field in METRIC_FIELDS.values():
        left_value = set(left[field]) if field in {"key_relations", "nature_labels"} else left[field]
        right_value = set(right[field]) if field in {"key_relations", "nature_labels"} else right[field]
        if left_value != right_value:
            return True
    return False


def _validate_adjudication(
    adjudication: dict[str, Any], left: dict[str, Any], right: dict[str, Any]
) -> None:
    required = {
        "schema_version",
        "case_id",
        "blind_packet_sha256",
        "adjudicator_id",
        "resolution",
        "rationale",
        "signed_at",
    }
    if not isinstance(adjudication, dict) or set(adjudication) != required:
        raise ValueError("adjudication fields mismatch")
    if adjudication["schema_version"] != "career-relation-expert-adjudication/v1":
        raise ValueError("adjudication schema_version mismatch")
    adjudicator = _require_human(adjudication["adjudicator_id"], "adjudicator_id")
    if adjudicator in {left["reviewer_id"], right["reviewer_id"]}:
        raise ValueError("adjudicator must be a third independent human")
    if adjudication["case_id"] != left["case_id"] or adjudication["blind_packet_sha256"] != left["blind_packet_sha256"]:
        raise ValueError("adjudication must share case and blind packet binding")
    if not isinstance(adjudication["rationale"], str) or not adjudication["rationale"].strip():
        raise ValueError("adjudication rationale is required")
    validate_annotation(adjudication["resolution"])
    if adjudication["resolution"]["reviewer_id"] != adjudicator:
        raise ValueError("adjudication resolution must be signed by adjudicator")
    _same_binding(left, adjudication["resolution"])


def finalize_annotations(
    review_a: dict[str, Any],
    review_b: dict[str, Any],
    adjudication: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Preserve two raw reviews and require independent adjudication for conflicts."""
    validate_annotation(review_a)
    validate_annotation(review_b)
    if review_a["reviewer_id"] == review_b["reviewer_id"]:
        raise ValueError("different independent reviewers are required")
    _same_binding(review_a, review_b)
    conflict = _has_disagreement(review_a, review_b)
    if conflict and adjudication is None:
        return {
            "status": "not_ready",
            "reason": "adjudication_required",
            "raw_annotations": [review_a, review_b],
            "conflict_state": "unresolved",
            "production_switch_permitted": False,
        }
    if adjudication is not None:
        _validate_adjudication(adjudication, review_a, review_b)
    return {
        "status": "ready",
        "raw_annotations": [review_a, review_b],
        "conflict_state": "resolved_by_adjudication" if conflict else "none",
        "adjudication": adjudication,
        "resolved_annotation": adjudication["resolution"] if conflict else review_a,
        "production_switch_permitted": False,
    }


def _empty_metrics() -> dict[str, dict[str, int | float | None]]:
    return {
        name: {"numerator": 0, "denominator": 0, "value": None}
        for name in METRIC_FIELDS
    }


def _jaccard(left: Iterable[str], right: Iterable[str]) -> float | None:
    left_set, right_set = set(left), set(right)
    union = left_set | right_set
    if not union:
        return None
    return len(left_set & right_set) / len(union)


def agreement_gate(
    review_pairs: list[tuple[dict[str, Any], dict[str, Any] | None]],
    *,
    adjudications: list[dict[str, Any] | None] | None = None,
) -> dict[str, Any]:
    """Compute deterministic pairwise agreement with explicit scoreable denominators."""
    metrics = _empty_metrics()
    failures: list[str] = []
    adjudications = adjudications or [None] * len(review_pairs)
    if len(adjudications) != len(review_pairs):
        raise ValueError("adjudications must align with review_pairs")
    for index, (review_a, review_b) in enumerate(review_pairs):
        if review_b is None:
            if "missing_dual_review" not in failures:
                failures.append("missing_dual_review")
            continue
        final = finalize_annotations(review_a, review_b, adjudications[index])
        if final["status"] != "ready" and "unresolved_disagreement" not in failures:
            failures.append("unresolved_disagreement")
        for metric_name, field in METRIC_FIELDS.items():
            left, right = review_a[field], review_b[field]
            if metric_name in {"key_relation_set", "nature_label_set"}:
                score = _jaccard(left, right)
            elif metric_name == "abstention":
                score = 1.0 if (left is None) == (right is None) else 0.0
            elif left is None or right is None:
                score = None
            else:
                score = 1.0 if left == right else 0.0
            if score is None:
                continue
            metrics[metric_name]["numerator"] = float(metrics[metric_name]["numerator"]) + score
            metrics[metric_name]["denominator"] = int(metrics[metric_name]["denominator"]) + 1
    for metric in metrics.values():
        denominator = int(metric["denominator"])
        if denominator:
            numerator = float(metric["numerator"])
            metric["numerator"] = int(numerator) if numerator.is_integer() else numerator
            metric["value"] = numerator / denominator
    if any(metric["denominator"] == 0 for metric in metrics.values()) and "insufficient_metric_data" not in failures:
        failures.append("insufficient_metric_data")
    if failures == ["missing_dual_review", "insufficient_metric_data"]:
        failures = ["missing_dual_review"]
    return {
        "status": "not_ready" if failures else "ready",
        "failures": failures,
        "metrics": metrics,
        "permitted_uses": PERMITTED_USES,
        "formal_scoring_permitted": False,
        "production_switch_permitted": False,
    }


def status(
    *,
    disposition_path: Path = DEFAULT_DISPOSITION,
    annotation_pairs: list[tuple[dict[str, Any], dict[str, Any] | None]] | None = None,
) -> dict[str, Any]:
    """Report repository readiness without treating invalidated model-v1 as promotable."""
    disposition = _read_json(Path(disposition_path))
    if (
        disposition.get("model_id") != MODEL_ID
        or disposition.get("decision") != EXPECTED_DECISION
        or disposition.get("formal_scoring_status") != "invalidated"
        or disposition.get("promotion_eligible") is not False
        or disposition.get("production_switch_permitted") is not False
    ):
        raise ValueError("invalidated model-v1 frozen disposition is inconsistent")
    if not annotation_pairs:
        gate = {"status": "not_ready", "failures": ["no_human_annotations"]}
    else:
        gate = agreement_gate(annotation_pairs)
    return {
        **gate,
        "model_id": MODEL_ID,
        "model_decision": EXPECTED_DECISION,
        "promotion_eligible": False,
        "formal_scoring_permitted": False,
        "production_switch_permitted": False,
        "permitted_uses": PERMITTED_USES,
    }


def _load_refs(path: Path) -> list[dict[str, str]]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, list):
        raise ValueError("theory references must be a JSON list")
    return value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    status_parser = subparsers.add_parser("status", help="report current annotation readiness")
    status_parser.add_argument("--disposition", type=Path, default=DEFAULT_DISPOSITION)

    prepare = subparsers.add_parser("prepare-blind", help="prepare a safe deterministic blind packet")
    prepare.add_argument("--chart", type=Path, required=True)
    prepare.add_argument("--theory-refs", type=Path, required=True)
    prepare.add_argument("--out", type=Path, required=True)
    prepare.add_argument("--write", action="store_true", help="perform create-only write; default is dry-run")

    submit = subparsers.add_parser("submit", help="validate and create one raw human annotation")
    submit.add_argument("--annotation", type=Path, required=True)
    submit.add_argument("--out", type=Path, required=True)
    submit.add_argument("--write", action="store_true", help="perform create-only write; default is dry-run")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "status":
            result = status(disposition_path=args.disposition)
        elif args.command == "prepare-blind":
            result = prepare_blind_packet(
                _read_json(args.chart),
                _load_refs(args.theory_refs),
                output=args.out,
                dry_run=not args.write,
            )
        else:
            result = submit_annotation(
                _read_json(args.annotation), args.out, dry_run=not args.write
            )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("status") != "error" else 2


if __name__ == "__main__":
    raise SystemExit(main())

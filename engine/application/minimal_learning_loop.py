from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from engine.application.feedback_parser import StatementFeedback

ALPHA_RULE = 0.05
ALPHA_FAMILY = 0.02
BETA_RULE = 0.10
BETA_FAMILY = 0.05
DEFAULT_CONFIDENCE = 0.5
LEARNING_LOG_FILENAME = "learning_log.json"
CONFIDENCE_STATE_FILENAME = "updated_confidence_state.json"
_VALID_PHASE_A_VERDICTS = {"y", "n", "partial", "skip"}
_EMOJI_RE = re.compile(r"[\U0001F300-\U0001FAFF\u2600-\u27BF]")


class FeedbackNormalizationError(ValueError):
    """Raised when feedback is not strict Phase-A structured feedback."""


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def normalize_feedback_entry(
    feedback: StatementFeedback | Mapping[str, Any],
    *,
    case_id: str,
    timestamp: str | None = None,
) -> dict[str, str]:
    """Convert one feedback object into Phase-A normalized feedback format."""

    ts = timestamp or utc_now()
    if isinstance(feedback, StatementFeedback):
        statement_id = feedback.statement_id
        verdict = _phase_a_verdict(feedback.annotation, feedback.verdict)
    else:
        statement_id = str(feedback.get("statement_id") or "").strip()
        verdict = str(feedback.get("verdict") or feedback.get("annotation") or "").strip().lower()
        if verdict in {"hit", "true"}:
            verdict = "y"
        elif verdict in {"miss", "false"}:
            verdict = "n"
        elif verdict in {"abstain", "?", "no_data"}:
            verdict = "skip"
    if not statement_id:
        raise FeedbackNormalizationError("feedback missing statement_id")
    if verdict not in _VALID_PHASE_A_VERDICTS:
        raise FeedbackNormalizationError(f"unsupported feedback verdict: {verdict}")
    return {
        "statement_id": statement_id,
        "case_id": case_id,
        "verdict": verdict,
        "timestamp": ts,
    }


def normalize_feedback_entries(
    feedbacks: list[StatementFeedback | Mapping[str, Any]],
    *,
    case_id: str,
    source_text: str = "",
    timestamp: str | None = None,
) -> list[dict[str, str]]:
    """Normalize structured feedback and reject free text / emoji-only feedback."""

    if source_text.strip() and not feedbacks:
        raise FeedbackNormalizationError("free text or unstructured feedback is rejected")
    if source_text and _EMOJI_RE.search(source_text) and not _has_structured_feedback(feedbacks):
        raise FeedbackNormalizationError("emoji feedback is rejected")
    return [normalize_feedback_entry(item, case_id=case_id, timestamp=timestamp) for item in feedbacks]


def update_confidence(
    statement_record: Mapping[str, Any],
    feedback: Mapping[str, Any],
    state: Mapping[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    """Apply the Phase-A minimal confidence update for one statement feedback."""

    verdict = str(feedback.get("verdict") or "").strip().lower()
    if verdict == "skip":
        return dict(state or _empty_state()), None
    if verdict not in _VALID_PHASE_A_VERDICTS:
        raise FeedbackNormalizationError(f"unsupported feedback verdict: {verdict}")

    current = dict(state or _empty_state())
    rule_id = _required_record_value(statement_record, "rule_id")
    family_id = _required_record_value(statement_record, "family_id")
    before_rule = _confidence_for(current, "rule_confidence", rule_id, statement_record)
    before_family = _confidence_for(current, "family_confidence", family_id, statement_record)
    after_rule = before_rule
    after_family = before_family

    if verdict == "y":
        after_rule = _clamp(before_rule + ALPHA_RULE)
        after_family = _clamp(before_family + ALPHA_FAMILY)
    elif verdict == "n":
        after_rule = _clamp(before_rule - BETA_RULE)
        after_family = _clamp(before_family - BETA_FAMILY)

    current.setdefault("rule_confidence", {})[rule_id] = after_rule
    current.setdefault("family_confidence", {})[family_id] = after_family
    current["updated_at"] = str(feedback.get("timestamp") or utc_now())

    log_entry = {
        "timestamp": str(feedback.get("timestamp") or current["updated_at"]),
        "case_id": str(feedback.get("case_id") or statement_record.get("case_id") or "UNMAPPED"),
        "statement_id": _required_record_value(statement_record, "statement_id"),
        "rule_id": rule_id,
        "family_id": family_id,
        "verdict": verdict,
        "rule_confidence_before": before_rule,
        "rule_confidence_after": after_rule,
        "family_confidence_before": before_family,
        "family_confidence_after": after_family,
        "changed": after_rule != before_rule or after_family != before_family,
    }
    return current, log_entry


def run_learning_update(
    statement_records: Mapping[str, Any],
    normalized_feedback: list[Mapping[str, Any]],
    *,
    case_dir: str | Path,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Run Phase-A updates and write learning_log.json / updated_confidence_state.json."""

    case_path = Path(case_dir)
    records = _record_map(statement_records)
    state_path = case_path / CONFIDENCE_STATE_FILENAME
    log_path = case_path / LEARNING_LOG_FILENAME
    state = _load_json(state_path, default=_empty_state())
    logs = _load_json(log_path, default=[])
    if not isinstance(logs, list):
        logs = []

    updates: list[dict[str, Any]] = []
    skipped: list[dict[str, str]] = []
    for feedback in normalized_feedback:
        statement_id = str(feedback.get("statement_id") or "")
        record = records.get(statement_id)
        if not record:
            skipped.append({"statement_id": statement_id, "reason": "statement_record_not_found"})
            continue
        state, entry = update_confidence(record, feedback, state)
        if entry is not None:
            updates.append(entry)
            logs.append(entry)

    summary = {
        "schema_version": "phase_a_learning.v1",
        "case_id": str(statement_records.get("case_id") or case_path.name),
        "statement_record_count": len(records),
        "feedback_count": len(normalized_feedback),
        "updated_count": len(updates),
        "skipped_count": len(skipped),
        "observable_confidence_changes": [item for item in updates if item.get("changed")],
        "skipped": skipped,
    }
    state["summary"] = summary
    if not dry_run:
        case_path.mkdir(parents=True, exist_ok=True)
        log_path.write_text(json.dumps(logs, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return summary


def analysis_pipeline(
    statement_records: Mapping[str, Any],
    feedbacks: list[StatementFeedback | Mapping[str, Any]],
    *,
    case_dir: str | Path,
    source_text: str = "",
    dry_run: bool = False,
) -> dict[str, Any]:
    """Minimal Phase-A closed-loop pipeline over already generated statements."""

    case_id = str(statement_records.get("case_id") or Path(case_dir).name)
    normalized = normalize_feedback_entries(feedbacks, case_id=case_id, source_text=source_text)
    summary = run_learning_update(statement_records, normalized, case_dir=case_dir, dry_run=dry_run)
    return {"normalized_feedback": normalized, "learning_summary": summary}


def _phase_a_verdict(annotation: str, verdict: str) -> str:
    ann = str(annotation or "").strip().lower()
    old = str(verdict or "").strip().lower()
    if ann in _VALID_PHASE_A_VERDICTS:
        return ann
    if old == "hit":
        return "y"
    if old == "miss":
        return "n"
    if old == "abstain":
        return "partial"
    return "skip"


def _record_map(statement_records: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    raw = statement_records.get("records", []) if isinstance(statement_records, Mapping) else []
    if isinstance(raw, Mapping):
        raw = list(raw.values())
    if not isinstance(raw, list):
        return {}
    out: dict[str, dict[str, Any]] = {}
    for item in raw:
        if not isinstance(item, Mapping):
            continue
        sid = str(item.get("statement_id") or "").strip()
        if sid:
            out[sid] = dict(item)
    return out


def _required_record_value(record: Mapping[str, Any], field: str) -> str:
    value = str(record.get(field) or "").strip()
    return value or "UNMAPPED"


def _confidence_for(state: Mapping[str, Any], bucket: str, key: str, record: Mapping[str, Any]) -> float:
    values = state.get(bucket, {}) if isinstance(state, Mapping) else {}
    if isinstance(values, Mapping) and key in values:
        return _clamp(values[key])
    snapshot = record.get("confidence_snapshot", {})
    if isinstance(snapshot, Mapping):
        posterior = snapshot.get("posterior_mean")
        if posterior is not None:
            return _clamp(posterior)
        percent = snapshot.get("percent")
        if percent is not None:
            value = _clamp(float(percent) / 100 if float(percent) > 1 else float(percent))
            return value
    return DEFAULT_CONFIDENCE


def _empty_state() -> dict[str, Any]:
    return {
        "schema_version": "phase_a_confidence_state.v1",
        "rule_confidence": {},
        "family_confidence": {},
        "updated_at": utc_now(),
    }


def _load_json(path: Path, *, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, ValueError):
        return default


def _clamp(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = DEFAULT_CONFIDENCE
    return max(0.0, min(1.0, round(number, 6)))


def _has_structured_feedback(feedbacks: list[Any]) -> bool:
    return bool(feedbacks)

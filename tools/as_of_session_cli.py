"""历史/手动 as-of 事业会话旁路；手动 opt-in，不切换任何生产默认入口。"""

from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import hashlib
import json
import re
import sys
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, TypeVar

from engine import archive as archive_api
from engine.asof.archive_integration import archive_asof_state
from engine.asof.career_state_builder import (
    CAREER_IMPACT_SUGGESTION_SCHEMA_VERSION,
    CareerFundamentalAdjudication,
    CareerImpactAdjudication,
    CareerImpactSuggestion,
)
from engine.asof.consultation_freeze import (
    FREEZE_PACKAGE_SCHEMA_VERSION,
    CareerBlindDraft,
    CareerFreezePackage,
    FrozenCareerEvent,
    FrozenCareerFundamental,
    VerificationInput,
    compute_freeze_package_sha256,
    verification_input_from_mapping,
)
from engine.asof.event_candidate import (
    AnnualInteractionTrace,
    CompletionMode,
    EvidenceRef,
    RootLevel,
    SourceCitation,
    evaluate_event_candidate,
)
from engine.asof.future_projection import CareerFutureCandidate, WealthEventBinding
from engine.asof.reality_translation import FrozenLandingSet, LandingPoint
from engine.asof.session_contract import (
    SessionContractError,
    SessionIdentity,
    blind_chart_input_from_mapping,
    compute_blind_input_sha256,
)
from engine.asof.session_runner import SessionRunResult, run_career_session
from engine.asof.state_ledger import ImpactLevel, ImpactScope, Persistence
from engine.asof.wealth_propagation import WealthPropagationEdge

__all__ = ("SessionArchiveResult", "run_and_archive_session", "main")

_COMPUTED_DIGEST = "$computed"
_DIGEST = re.compile(r"[0-9a-f]{64}\Z")
_DATE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}\Z")
_TOP_REQUIRED = (
    "session_schema_version",
    "case_id",
    "as_of_date",
    "session_id",
    "blind_input",
    "draft",
    "verifications",
    "suggestions",
    "impact_adjudications",
    "fundamental_adjudication",
    "daiyun_end",
    "archive",
)
_TOP_OPTIONAL = ("career_candidates", "wealth_bindings")
_TEnum = TypeVar("_TEnum", bound=Enum)


@dataclasses.dataclass(frozen=True, slots=True)
class SessionArchiveResult:
    session_result: SessionRunResult
    archive_result: archive_api.ArchiveResult
    artifact: dict[str, object]


def _error(code: str, message: str) -> SessionContractError:
    return SessionContractError(code, message)


def _mapping(value: object, field: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise _error("INVALID_TYPE", f"{field} must be an object")
    if any(type(key) is not str for key in value):
        raise _error("UNKNOWN_FIELD", f"{field} contains a non-string field")
    return value


def _closed(
    value: object,
    required: tuple[str, ...],
    field: str,
    optional: tuple[str, ...] = (),
) -> Mapping[str, object]:
    mapping = _mapping(value, field)
    allowed = set(required) | set(optional)
    if any(key not in allowed for key in mapping):
        raise _error("UNKNOWN_FIELD", f"{field} contains an unknown field")
    missing = tuple(key for key in required if key not in mapping)
    if missing:
        raise _error("INVALID_VALUE", f"{field}.{missing[0]} is required")
    return mapping


def _text(value: object, field: str, *, empty: bool = False) -> str:
    if type(value) is not str:
        raise _error("INVALID_TYPE", f"{field} must be str")
    if not empty and not value.strip():
        raise _error("INVALID_VALUE", f"{field} must not be empty")
    return value


def _integer(value: object, field: str) -> int:
    if type(value) is not int:
        raise _error("INVALID_TYPE", f"{field} must be int")
    return value


def _boolean(value: object, field: str) -> bool:
    if type(value) is not bool:
        raise _error("INVALID_TYPE", f"{field} must be bool")
    return value


def _array(value: object, field: str) -> list[object]:
    if type(value) is not list:
        raise _error("INVALID_TYPE", f"{field} must be an array")
    return value


def _strings(value: object, field: str) -> tuple[str, ...]:
    items = _array(value, field)
    return tuple(_text(item, f"{field} item") for item in items)


def _date(value: object, field: str) -> dt.date:
    text = _text(value, field)
    if _DATE.fullmatch(text) is None:
        raise _error("INVALID_VALUE", f"{field} must use YYYY-MM-DD")
    try:
        return dt.date.fromisoformat(text)
    except ValueError as exc:
        raise _error("INVALID_VALUE", f"{field} is not a valid date") from exc


def _enum(enum_type: type[_TEnum], value: object, field: str) -> _TEnum:
    text = _text(value, field)
    try:
        return enum_type(text)
    except ValueError as exc:
        raise _error("INVALID_VALUE", f"{field} is outside its closed value domain") from exc


def _digest_value(value: object, digest: str, field: str) -> str:
    text = _text(value, field)
    if text == _COMPUTED_DIGEST:
        return digest
    if _DIGEST.fullmatch(text) is None:
        raise _error("INVALID_VALUE", f"{field} must be $computed or a lowercase SHA-256 digest")
    return text


def _evidence(value: object, field: str) -> EvidenceRef:
    item = _closed(value, ("source", "locator", "excerpt"), field)
    return EvidenceRef(
        _text(item["source"], f"{field}.source"),
        _text(item["locator"], f"{field}.locator"),
        _text(item["excerpt"], f"{field}.excerpt"),
    )


def _evidences(value: object, field: str) -> tuple[EvidenceRef, ...]:
    return tuple(_evidence(item, f"{field}[{index}]") for index, item in enumerate(_array(value, field)))


def _citation(value: object, field: str) -> SourceCitation:
    item = _closed(value, ("source_path", "line", "excerpt"), field)
    return SourceCitation(
        _text(item["source_path"], f"{field}.source_path"),
        _integer(item["line"], f"{field}.line"),
        _text(item["excerpt"], f"{field}.excerpt"),
    )


def _citations(value: object, field: str) -> tuple[SourceCitation, ...]:
    return tuple(_citation(item, f"{field}[{index}]") for index, item in enumerate(_array(value, field)))


def _point(value: object, field: str) -> LandingPoint:
    item = _closed(value, ("name", "domain", "direction"), field)
    return LandingPoint(
        _text(item["name"], f"{field}.name"),
        _text(item["domain"], f"{field}.domain"),
        _text(item["direction"], f"{field}.direction"),
    )


def _fundamental(value: object, field: str) -> FrozenCareerFundamental:
    item = _closed(
        value,
        (
            "fundamental_id",
            "window_start",
            "window_end",
            "window_center",
            "center",
            "reasonable_range",
            "strongest_alternative",
            "falsifiers",
        ),
        field,
    )
    return FrozenCareerFundamental(
        _text(item["fundamental_id"], f"{field}.fundamental_id"),
        _date(item["window_start"], f"{field}.window_start"),
        _date(item["window_end"], f"{field}.window_end"),
        _date(item["window_center"], f"{field}.window_center"),
        _text(item["center"], f"{field}.center"),
        _strings(item["reasonable_range"], f"{field}.reasonable_range"),
        _text(item["strongest_alternative"], f"{field}.strongest_alternative"),
        _strings(item["falsifiers"], f"{field}.falsifiers"),
    )


def _event(value: object, field: str) -> FrozenCareerEvent:
    item = _closed(value, ("candidate", "landing_set"), field)
    raw = _closed(
        item["candidate"],
        (
            "candidate_id",
            "event_type",
            "window_start",
            "window_end",
            "annual_trace",
            "root_level",
            "completion_mode",
            "natal_evidence",
            "daiyun_evidence",
            "root_evidence",
            "source_citations",
            "supporting_evidence",
            "counter_evidence",
            "alternative_hypotheses",
            "frozen_version",
        ),
        f"{field}.candidate",
    )
    trace_raw = _closed(
        raw["annual_trace"],
        (
            "year",
            "liunian",
            "dayun_ganzhi",
            "relations",
            "activated_node_ids",
            "domains",
            "supporting_evidence",
            "counter_evidence",
            "trigger_strength",
            "crossed_candidate_gate",
        ),
        f"{field}.candidate.annual_trace",
    )
    trace = AnnualInteractionTrace(
        _integer(trace_raw["year"], f"{field}.candidate.annual_trace.year"),
        _text(trace_raw["liunian"], f"{field}.candidate.annual_trace.liunian"),
        _text(trace_raw["dayun_ganzhi"], f"{field}.candidate.annual_trace.dayun_ganzhi"),
        _evidences(trace_raw["relations"], f"{field}.candidate.annual_trace.relations"),
        _strings(trace_raw["activated_node_ids"], f"{field}.candidate.annual_trace.activated_node_ids"),
        _strings(trace_raw["domains"], f"{field}.candidate.annual_trace.domains"),
        _evidences(trace_raw["supporting_evidence"], f"{field}.candidate.annual_trace.supporting_evidence"),
        _evidences(trace_raw["counter_evidence"], f"{field}.candidate.annual_trace.counter_evidence"),
        _text(trace_raw["trigger_strength"], f"{field}.candidate.annual_trace.trigger_strength"),
        _boolean(trace_raw["crossed_candidate_gate"], f"{field}.candidate.annual_trace.crossed_candidate_gate"),
    )
    decision = evaluate_event_candidate(
        candidate_id=_text(raw["candidate_id"], f"{field}.candidate.candidate_id"),
        event_type=_text(raw["event_type"], f"{field}.candidate.event_type"),
        window_start=_date(raw["window_start"], f"{field}.candidate.window_start"),
        window_end=_date(raw["window_end"], f"{field}.candidate.window_end"),
        annual_trace=trace,
        root_level=_enum(RootLevel, raw["root_level"], f"{field}.candidate.root_level"),
        completion_mode=_enum(CompletionMode, raw["completion_mode"], f"{field}.candidate.completion_mode"),
        natal_evidence=_evidences(raw["natal_evidence"], f"{field}.candidate.natal_evidence"),
        daiyun_evidence=_evidences(raw["daiyun_evidence"], f"{field}.candidate.daiyun_evidence"),
        root_evidence=_evidences(raw["root_evidence"], f"{field}.candidate.root_evidence"),
        source_citations=_citations(raw["source_citations"], f"{field}.candidate.source_citations"),
        supporting_evidence=_evidences(raw["supporting_evidence"], f"{field}.candidate.supporting_evidence"),
        counter_evidence=_evidences(raw["counter_evidence"], f"{field}.candidate.counter_evidence"),
        alternative_hypotheses=_strings(raw["alternative_hypotheses"], f"{field}.candidate.alternative_hypotheses"),
        frozen_version=_text(raw["frozen_version"], f"{field}.candidate.frozen_version"),
    )
    if not decision.accepted or decision.candidate is None:
        raise _error("CANDIDATE_REJECTED", decision.reason_code)
    landing = _closed(
        item["landing_set"],
        ("function_candidate", "center", "alternatives", "weak_hit_boundary", "falsifiers", "exclusions", "frozen_version"),
        f"{field}.landing_set",
    )
    landing_set = FrozenLandingSet(
        _text(landing["function_candidate"], f"{field}.landing_set.function_candidate"),
        _point(landing["center"], f"{field}.landing_set.center"),
        tuple(
            _point(point, f"{field}.landing_set.alternatives[{index}]")
            for index, point in enumerate(_array(landing["alternatives"], f"{field}.landing_set.alternatives"))
        ),
        _text(landing["weak_hit_boundary"], f"{field}.landing_set.weak_hit_boundary"),
        _strings(landing["falsifiers"], f"{field}.landing_set.falsifiers"),
        _strings(landing["exclusions"], f"{field}.landing_set.exclusions"),
        _text(landing["frozen_version"], f"{field}.landing_set.frozen_version"),
    )
    return FrozenCareerEvent(decision.candidate, landing_set)


def _draft(value: object) -> CareerBlindDraft:
    item = _closed(value, ("fundamentals", "events"), "draft")
    return CareerBlindDraft(
        tuple(_fundamental(raw, f"draft.fundamentals[{index}]") for index, raw in enumerate(_array(item["fundamentals"], "draft.fundamentals"))),
        tuple(_event(raw, f"draft.events[{index}]") for index, raw in enumerate(_array(item["events"], "draft.events"))),
    )


def _suggestion(value: object, digest: str, field: str) -> CareerImpactSuggestion:
    item = _closed(
        value,
        (
            "schema_version", "freeze_package_sha256", "item_id", "event_date", "suggested_impact",
            "suggested_persistence", "suggested_scope", "suggested_short_term_until", "state_value",
            "opened_path_ids", "closed_path_ids",
        ),
        field,
    )
    schema = _text(item["schema_version"], f"{field}.schema_version")
    if schema != CAREER_IMPACT_SUGGESTION_SCHEMA_VERSION:
        raise _error("SCHEMA_MISMATCH", "career impact suggestion schema mismatch")
    until = item["suggested_short_term_until"]
    return CareerImpactSuggestion(
        schema_version=schema,
        freeze_package_sha256=_digest_value(item["freeze_package_sha256"], digest, f"{field}.freeze_package_sha256"),
        item_id=_text(item["item_id"], f"{field}.item_id"),
        event_date=_date(item["event_date"], f"{field}.event_date"),
        suggested_impact=_enum(ImpactLevel, item["suggested_impact"], f"{field}.suggested_impact"),
        suggested_persistence=_enum(Persistence, item["suggested_persistence"], f"{field}.suggested_persistence"),
        suggested_scope=_enum(ImpactScope, item["suggested_scope"], f"{field}.suggested_scope"),
        suggested_short_term_until=None if until is None else _date(until, f"{field}.suggested_short_term_until"),
        state_value=_text(item["state_value"], f"{field}.state_value"),
        opened_path_ids=_strings(item["opened_path_ids"], f"{field}.opened_path_ids"),
        closed_path_ids=_strings(item["closed_path_ids"], f"{field}.closed_path_ids"),
    )


def _adjudication(value: object, digest: str, field: str) -> CareerImpactAdjudication:
    names = tuple(item.name for item in dataclasses.fields(CareerImpactAdjudication))
    raw = _closed(value, names, field)
    until = raw["final_short_term_until"]
    return CareerImpactAdjudication(
        _digest_value(raw["freeze_package_sha256"], digest, f"{field}.freeze_package_sha256"),
        _text(raw["item_id"], f"{field}.item_id"),
        _enum(ImpactLevel, raw["final_impact"], f"{field}.final_impact"),
        _enum(Persistence, raw["final_persistence"], f"{field}.final_persistence"),
        _enum(ImpactScope, raw["final_scope"], f"{field}.final_scope"),
        None if until is None else _date(until, f"{field}.final_short_term_until"),
        _text(raw["adjustment_reason"], f"{field}.adjustment_reason"),
        _text(raw["condition"], f"{field}.condition", empty=True),
        _text(raw["difference_from_verified"], f"{field}.difference_from_verified", empty=True),
        _strings(raw["changed_fundamental_ids"], f"{field}.changed_fundamental_ids"),
        _strings(raw["changed_future_conclusions"], f"{field}.changed_future_conclusions"),
        _text(raw["minimum_question"], f"{field}.minimum_question", empty=True),
        _text(raw["falsifier"], f"{field}.falsifier", empty=True),
    )


def _fundamental_adjudication(value: object, digest: str) -> CareerFundamentalAdjudication:
    raw = _closed(value, ("freeze_package_sha256", "selected_fundamental_id", "reason"), "fundamental_adjudication")
    return CareerFundamentalAdjudication(
        _digest_value(raw["freeze_package_sha256"], digest, "fundamental_adjudication.freeze_package_sha256"),
        _text(raw["selected_fundamental_id"], "fundamental_adjudication.selected_fundamental_id"),
        _text(raw["reason"], "fundamental_adjudication.reason"),
    )


def _future_candidate(value: object, field: str) -> CareerFutureCandidate:
    raw = _closed(value, ("case_id", "as_of_date", "candidate_id", "conclusion", "required_active_state_ids", "required_open_path_ids"), field)
    return CareerFutureCandidate(
        case_id=_text(raw["case_id"], f"{field}.case_id"),
        as_of_date=_date(raw["as_of_date"], f"{field}.as_of_date"),
        candidate_id=_text(raw["candidate_id"], f"{field}.candidate_id"),
        conclusion=_text(raw["conclusion"], f"{field}.conclusion"),
        required_active_state_ids=_strings(raw["required_active_state_ids"], f"{field}.required_active_state_ids"),
        required_open_path_ids=_strings(raw["required_open_path_ids"], f"{field}.required_open_path_ids"),
    )


def _edge(value: object, field: str) -> WealthPropagationEdge:
    raw = _closed(value, ("edge_id", "source_event_type", "target_state", "required_conditions", "delay_days", "persistence", "falsifiers", "verified", "short_term_days"), field)
    days = raw["short_term_days"]
    return WealthPropagationEdge(
        _text(raw["edge_id"], f"{field}.edge_id"),
        _text(raw["source_event_type"], f"{field}.source_event_type"),
        _text(raw["target_state"], f"{field}.target_state"),
        _strings(raw["required_conditions"], f"{field}.required_conditions"),
        _integer(raw["delay_days"], f"{field}.delay_days"),
        _enum(Persistence, raw["persistence"], f"{field}.persistence"),
        _strings(raw["falsifiers"], f"{field}.falsifiers"),
        _boolean(raw["verified"], f"{field}.verified"),
        None if days is None else _integer(days, f"{field}.short_term_days"),
    )


def _binding(value: object, field: str) -> WealthEventBinding:
    raw = _closed(value, ("event_id", "observed_conditions", "active_falsifiers", "edges"), field)
    return WealthEventBinding(
        event_id=_text(raw["event_id"], f"{field}.event_id"),
        observed_conditions=_strings(raw["observed_conditions"], f"{field}.observed_conditions"),
        active_falsifiers=_strings(raw["active_falsifiers"], f"{field}.active_falsifiers"),
        edges=tuple(_edge(item, f"{field}.edges[{index}]") for index, item in enumerate(_array(raw["edges"], f"{field}.edges"))),
    )


def _load(path: Path) -> Mapping[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise
    except OSError:
        raise
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise _error("INVALID_JSON", "input must be readable UTF-8 JSON") from exc
    return _closed(value, _TOP_REQUIRED, "session", _TOP_OPTIONAL)


def _verification(value: object, digest: str, field: str) -> VerificationInput:
    raw = dict(_mapping(value, field))
    if "freeze_package_sha256" in raw:
        raw["freeze_package_sha256"] = _digest_value(raw["freeze_package_sha256"], digest, f"{field}.freeze_package_sha256")
    return verification_input_from_mapping(raw)


def _verify_artifact(path: Path, expected_id: str, expected_digest: str) -> dict[str, object]:
    try:
        raw = path.read_bytes()
        value = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise archive_api.ArchiveIOError("cannot read back archived as-of artifact") from exc
    fields = {"schema_version", "artifact_id", "source_digest", "payload_digest", "verified_at", "verifier", "verification_basis", "payload"}
    if type(value) is not dict or set(value) != fields:
        raise archive_api.ArchiveInputError("archived artifact fields differ from verified artifact contract")
    payload = value["payload"]
    payload_bytes = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    digest = hashlib.sha256(payload_bytes).hexdigest()
    if value["artifact_id"] != expected_id or digest != expected_digest or value["payload_digest"] != digest or value["source_digest"] != digest:
        raise archive_api.ArchiveInputError("archived artifact identity or digest readback mismatch")
    return value


def run_and_archive_session(
    input_path: str | Path,
    *,
    archive_root: str | Path | None = None,
) -> SessionArchiveResult:
    """运行并归档一条显式 JSON 会话；异常保持原类型向调用者传播。"""

    payload = _load(Path(input_path))
    session_schema_version = _text(payload["session_schema_version"], "session_schema_version")
    case_id = _text(payload["case_id"], "case_id")
    as_of_date = _date(payload["as_of_date"], "as_of_date")
    session_id = _text(payload["session_id"], "session_id")
    blind_input = blind_chart_input_from_mapping(payload["blind_input"])
    draft = _draft(payload["draft"])
    identity = SessionIdentity(session_schema_version, case_id, as_of_date, session_id)
    expected_package = CareerFreezePackage(
        FREEZE_PACKAGE_SCHEMA_VERSION,
        identity,
        compute_blind_input_sha256(blind_input),
        draft.fundamentals,
        draft.events,
    )
    digest = compute_freeze_package_sha256(expected_package)
    verifications = tuple(
        _verification(item, digest, f"verifications[{index}]")
        for index, item in enumerate(_array(payload["verifications"], "verifications"))
    )
    suggestions = tuple(
        _suggestion(item, digest, f"suggestions[{index}]")
        for index, item in enumerate(_array(payload["suggestions"], "suggestions"))
    )
    adjudications = tuple(
        _adjudication(item, digest, f"impact_adjudications[{index}]")
        for index, item in enumerate(_array(payload["impact_adjudications"], "impact_adjudications"))
    )
    fundamental = _fundamental_adjudication(payload["fundamental_adjudication"], digest)
    candidates = None
    if "career_candidates" in payload:
        candidates = tuple(
            _future_candidate(item, f"career_candidates[{index}]")
            for index, item in enumerate(_array(payload["career_candidates"], "career_candidates"))
        )
    bindings = None
    if "wealth_bindings" in payload:
        bindings = tuple(
            _binding(item, f"wealth_bindings[{index}]")
            for index, item in enumerate(_array(payload["wealth_bindings"], "wealth_bindings"))
        )
    session_result = run_career_session(
        session_schema_version=session_schema_version,
        case_id=case_id,
        as_of_date=as_of_date,
        session_id=session_id,
        blind_input=blind_input,
        draft=draft,
        verifications=verifications,
        suggestions=suggestions,
        impact_adjudications=adjudications,
        fundamental_adjudication=fundamental,
        daiyun_end=_date(payload["daiyun_end"], "daiyun_end"),
        career_candidates=candidates,
        wealth_bindings=bindings,
    )
    archive = _closed(payload["archive"], ("archive_root", "artifact_id", "verified_at", "verifier", "verification_basis"), "archive")
    root = Path(_text(archive["archive_root"], "archive.archive_root")) if archive_root is None else Path(archive_root)
    artifact_id = _text(archive["artifact_id"], "archive.artifact_id")
    archive_result = archive_asof_state(
        session_result.final_envelope,
        session_result.freeze_package,
        session_result.adjudication_bundle,
        session_result.state_result,
        session_result.projection,
        archive_root=root,
        artifact_id=artifact_id,
        verified_at=_text(archive["verified_at"], "archive.verified_at"),
        verifier=_text(archive["verifier"], "archive.verifier"),
        verification_basis=_strings(archive["verification_basis"], "archive.verification_basis"),
    )
    artifact = _verify_artifact(archive_result.target, artifact_id, archive_result.payload_digest)
    return SessionArchiveResult(session_result, archive_result, artifact)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the historical/manual opt-in as-of career session side path")
    parser.add_argument("input_json", help="explicit structured session JSON")
    parser.add_argument("--archive-root", help="local archive directory override")
    return parser


def _error_code(exc: BaseException) -> str:
    code = getattr(exc, "code", None)
    if type(code) is str and code:
        return code
    if isinstance(exc, FileNotFoundError):
        return "INPUT_NOT_FOUND"
    if isinstance(exc, PermissionError):
        return "PERMISSION_DENIED"
    if isinstance(exc, archive_api.ArchiveConflictError):
        return "ARCHIVE_CONFLICT"
    if isinstance(exc, archive_api.ArchiveInputError):
        return "ARCHIVE_INPUT_ERROR"
    if isinstance(exc, archive_api.ArchiveIOError):
        return "ARCHIVE_IO_ERROR"
    if isinstance(exc, OSError):
        return "IO_ERROR"
    return "UNEXPECTED_ERROR"


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        result = run_and_archive_session(args.input_json, archive_root=args.archive_root)
    except Exception as exc:
        print(
            json.dumps(
                {"status": "error", "error_code": _error_code(exc), "error_type": type(exc).__name__, "message": str(exc)},
                ensure_ascii=False,
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 1
    identity = result.session_result.final_envelope.identity
    print(
        json.dumps(
            {
                "status": result.archive_result.status,
                "archive_path": str(result.archive_result.target),
                "artifact_id": result.archive_result.artifact_id,
                "payload_digest": result.archive_result.payload_digest,
                "case_id": identity.case_id,
                "as_of_date": identity.as_of_date.isoformat(),
                "session_state": result.session_result.final_envelope.state.value,
                "projection_created": result.session_result.projection is not None,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

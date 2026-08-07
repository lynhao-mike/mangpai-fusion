from __future__ import annotations

import ctypes
import dataclasses
import datetime
import errno
import hashlib
import hmac
import json
import os
import re
import shutil
import sys
import tempfile
import types
from collections.abc import Callable, Mapping
from pathlib import Path, PurePosixPath, PureWindowsPath

from engine.asof.consultation_freeze import (
    FREEZE_PACKAGE_SCHEMA_VERSION,
    CareerBlindDraft,
    CareerFreezePackage,
    CareerVerificationRecord,
    FrozenCareerEvent,
    FrozenCareerFundamental,
    compute_freeze_package_sha256,
    freeze_career_draft,
    freeze_package_to_canonical_bytes,
    open_verification,
    record_career_verification,
    verification_input_from_mapping,
)
from engine.asof.event_candidate import (
    AnnualInteractionTrace,
    CompletionMode,
    ExtensionBoundary,
    LifeEventCandidate,
    RootLevel,
    VerificationStatus,
)
from engine.asof.natal_capacity import EvidenceRef, SourceCitation
from engine.asof.reality_translation import FrozenLandingSet, LandingPoint, LandingVerdict, RealityConstraint
from engine.asof.session_contract import (
    BLIND_INPUT_SCHEMA_VERSION,
    SESSION_SCHEMA_VERSION,
    BlindChartInput,
    ConsultationState,
    SessionEnvelope,
    SessionIdentity,
    blind_chart_input_from_mapping,
    create_initial_envelope,
    transition_session,
)
from engine.evaluation.prospective_single_case import verify_single_case_bundle


_TRUSTED_WORKSPACE_ROOT = Path.cwd().resolve(strict=True)
_REQUEST_SCHEMA = "prospective-asof-request/v1"
_BUNDLE_SCHEMA = "prospective-asof-blind-bundle/v1"
_FROZEN_SCHEMA = "prospective-asof-frozen-run/v1"
_RELEASE_SCHEMA = "prospective-asof-feedback-release/v1"
_CUSTODY_SCHEMA = "prospective-asof-custody/v1"
_RESULT_SCHEMA = "prospective-asof-verified-result/v1"
_DIGEST = re.compile(r"[0-9a-f]{64}")
_CASE_ID = re.compile(r"P-GO-[0-9]{4}-[0-9]{3}-(?:乾|坤)-(?:[甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]){4}")
_SESSION_ID = re.compile(r"S-[0-9]{8}T[0-9]{6}Z-[0-9a-f]{8}")
_PILLARS = ("year", "month", "day", "hour")
_STEMS = frozenset("甲乙丙丁戊己庚辛壬癸")
_BRANCHES = frozenset("子丑寅卯辰巳午未申酉戌亥")
_GROWTH = frozenset(("长生", "沐浴", "冠带", "临官", "帝旺", "衰", "病", "死", "墓", "绝", "胎", "养"))
_REQUEST_INPUT_FIELDS = frozenset((
    "schema_version", "case_id", "session_case_id", "subject_id_hash", "as_of_date",
    "session_id", "chart_source", "hidden_stems_by_pillar", "changsheng_by_pillar",
    "daiyun", "created_at",
))
_REQUEST_FIELDS = _REQUEST_INPUT_FIELDS | frozenset(("artifact_path", "parents", "artifact_sha256"))
_BUNDLE_FIELDS = frozenset((
    "schema_version", "case_id", "session_case_id", "subject_id_hash", "as_of_date",
    "session_id", "created_at", "artifact_path", "parents", "files", "bundle_status",
    "artifact_sha256",
))
_FROZEN_FIELDS = frozenset((
    "schema_version", "case_id", "session_case_id", "subject_id_hash", "as_of_date",
    "session_id", "frozen_at", "artifact_path", "parents", "freeze_status",
    "blind_input_sha256", "freeze_package_sha256", "freeze_package", "artifact_sha256",
))
_RELEASE_FIELDS = frozenset((
    "schema_version", "case_id", "session_case_id", "subject_id_hash", "as_of_date",
    "session_id", "created_at", "artifact_path", "parents", "release_status",
    "blind_input_sha256", "freeze_package_sha256", "artifact_sha256",
))
_CUSTODY_FIELDS = frozenset((
    "schema_version", "case_id", "session_case_id", "subject_id_hash", "session_id",
    "freeze_package_sha256", "verifications",
))
_RESULT_FIELDS = frozenset((
    "schema_version", "case_id", "session_case_id", "subject_id_hash", "as_of_date",
    "session_id", "collected_at", "artifact_path", "parents", "verification_status",
    "blind_input_sha256", "freeze_package_sha256", "records", "artifact_sha256",
))
_FORBIDDEN_CUSTODY_KEYS = frozenset((
    "prediction", "report", "analysis", "lesson", "score", "runner", "reviewer",
    "known_fact", "feedback_path",
))


class _ProtectedAsOfModule(types.ModuleType):
    def __setattr__(self, name: str, value: object) -> None:
        if name == "_TRUSTED_WORKSPACE_ROOT":
            raise AttributeError("trusted workspace root is immutable")
        super().__setattr__(name, value)

    def __delattr__(self, name: str) -> None:
        if name == "_TRUSTED_WORKSPACE_ROOT":
            raise AttributeError("trusted workspace root is immutable")
        super().__delattr__(name)


sys.modules[__name__].__class__ = _ProtectedAsOfModule


class _AsOfError(ValueError):
    __slots__ = ("category", "reason")

    def __init__(self, category: str, reason: str = "") -> None:
        super().__init__(category)
        self.category = category
        self.reason = reason


def _fail(category: str, reason: str = "") -> None:
    raise _AsOfError(category, reason)


def _closed(value: object, fields: frozenset[str], category: str = "ASOF_SCHEMA_ERROR") -> Mapping[str, object]:
    if not isinstance(value, Mapping) or set(value) != fields or any(type(key) is not str for key in value):
        _fail(category)
    return value


def _canonical_bytes(value: Mapping[str, object]) -> bytes:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError):
        _fail("ASOF_SCHEMA_ERROR")


def _artifact_sha(value: Mapping[str, object]) -> str:
    return hashlib.sha256(_canonical_bytes({key: item for key, item in value.items() if key != "artifact_sha256"})).hexdigest()


def _document_bytes(value: Mapping[str, object]) -> bytes:
    try:
        return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")
    except (TypeError, ValueError):
        _fail("ASOF_SCHEMA_ERROR")


def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _is_link(path: Path) -> bool:
    junction = getattr(path, "is_junction", None)
    try:
        attributes = path.lstat().st_file_attributes
    except (AttributeError, OSError):
        attributes = 0
    return (
        path.is_symlink()
        or bool(junction is not None and junction())
        or bool(attributes & 0x400)
    )


def _workspace_path(path: Path) -> Path:
    supplied = Path(path)
    if "." in supplied.parts or ".." in supplied.parts:
        _fail("ASOF_PATH_ERROR")
    candidate = supplied if supplied.is_absolute() else _TRUSTED_WORKSPACE_ROOT / supplied
    try:
        relative = candidate.relative_to(_TRUSTED_WORKSPACE_ROOT)
    except ValueError:
        _fail("ASOF_PATH_ERROR")
    if not relative.parts:
        _fail("ASOF_PATH_ERROR")
    current = _TRUSTED_WORKSPACE_ROOT
    if _is_link(current):
        _fail("ASOF_LINK_ERROR")
    for part in relative.parts:
        current = current / part
        if _is_link(current):
            _fail("ASOF_LINK_ERROR")
    try:
        resolved = candidate.resolve(strict=candidate.exists())
        resolved.relative_to(_TRUSTED_WORKSPACE_ROOT)
    except (OSError, ValueError):
        _fail("ASOF_PATH_ERROR")
    return candidate


def _stored_path(value: object) -> Path:
    if type(value) is not str:
        _fail("ASOF_PATH_ERROR")
    posix = PurePosixPath(value)
    windows = PureWindowsPath(value)
    if (
        not value
        or value in {".", ".."}
        or posix.is_absolute()
        or windows.is_absolute()
        or bool(windows.drive)
        or posix.as_posix() != value
        or "." in posix.parts
        or ".." in posix.parts
    ):
        _fail("ASOF_PATH_ERROR")
    return _workspace_path(Path(*posix.parts))


def _check_chain(path: Path) -> None:
    _workspace_path(path)


def _check_new(path: Path) -> None:
    candidate = _workspace_path(path)
    if candidate.exists() or _is_link(candidate):
        _fail("ASOF_CONFLICT_ERROR")


def _canonical_path(path: Path) -> str:
    candidate = _workspace_path(path)
    return candidate.relative_to(_TRUSTED_WORKSPACE_ROOT).as_posix()


def _timestamp(value: object) -> datetime.datetime:
    if type(value) is not str or re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]+)?Z", value) is None:
        _fail("ASOF_TIME_ERROR")
    try:
        result = datetime.datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        _fail("ASOF_TIME_ERROR")
    if result.tzinfo != datetime.timezone.utc:
        _fail("ASOF_TIME_ERROR")
    return result


def _date(value: object) -> datetime.date:
    if type(value) is not str or re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value) is None:
        _fail("ASOF_SCHEMA_ERROR")
    try:
        return datetime.date.fromisoformat(value)
    except ValueError:
        _fail("ASOF_SCHEMA_ERROR")


def _digest(value: object, category: str = "ASOF_HASH_ERROR") -> str:
    if type(value) is not str or _DIGEST.fullmatch(value) is None:
        _fail(category)
    return value


def _ref(value: object) -> dict[str, object]:
    mapping = _closed(value, frozenset(("artifact_path", "artifact_sha256")), "ASOF_PARENT_ERROR")
    _stored_path(mapping["artifact_path"])
    return {
        "artifact_path": mapping["artifact_path"],
        "artifact_sha256": _digest(mapping["artifact_sha256"], "ASOF_PARENT_ERROR"),
    }


def _read_json(path: Path, *, expected_bytes: bool = True) -> dict[str, object]:
    _check_chain(path)
    if not path.is_file():
        _fail("ASOF_IO_ERROR")
    try:
        raw = path.read_bytes()
        value = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        _fail("ASOF_IO_ERROR")
    if type(value) is not dict:
        _fail("ASOF_SCHEMA_ERROR")
    if expected_bytes and raw != _document_bytes(value):
        _fail("ASOF_HASH_ERROR")
    return value


def _verify_artifact(document: Mapping[str, object], fields: frozenset[str], schema: str) -> dict[str, object]:
    value = dict(_closed(document, fields))
    if value["schema_version"] != schema:
        _fail("ASOF_SCHEMA_ERROR")
    stored = _digest(value["artifact_sha256"])
    if not hmac.compare_digest(stored, _artifact_sha(value)):
        _fail("ASOF_HASH_ERROR")
    return value


def _sealed(path: Path, fields: frozenset[str], schema: str) -> dict[str, object]:
    candidate = _workspace_path(path)
    document = _read_json(candidate)
    value = _verify_artifact(document, fields, schema)
    if value["artifact_path"] != _canonical_path(candidate):
        _fail("ASOF_PATH_ERROR")
    if _stored_path(value["artifact_path"]) != candidate:
        _fail("ASOF_PATH_ERROR")
    return value


def _session_case(case_id: str) -> str:
    if _CASE_ID.fullmatch(case_id) is None:
        _fail("ASOF_IDENTITY_ERROR")
    return "C-" + case_id.removeprefix("P-GO-")


def _case_paths(case_root: Path, case_id: str) -> dict[str, Path]:
    case_root = _workspace_path(case_root)
    if case_root.name != case_id or _CASE_ID.fullmatch(case_id) is None:
        _fail("ASOF_PATH_ERROR")
    return {
        "case_root": case_root,
        "request": case_root / f"{case_id}--asof-request--v001.json",
        "bundle": case_root / f"{case_id}--asof-blind-bundle--v001",
        "frozen": case_root / f"{case_id}--asof-frozen-run--v001.json",
        "release": case_root / f"{case_id}--asof-feedback-release--v001.json",
        "verified": case_root / f"{case_id}--asof-verified-result--v001.json",
    }


def _paths(parent_root: Path, case_id: str) -> dict[str, Path]:
    parent_root = _workspace_path(parent_root)
    expected = re.fullmatch(re.escape(case_id) + r"--blind-bundle--v[0-9]{3}", parent_root.name)
    if parent_root.parent.name != case_id or expected is None:
        _fail("ASOF_PATH_ERROR")
    return _case_paths(parent_root.parent, case_id)


def _validate_request_input(value: Mapping[str, object], parent: Mapping[str, object]) -> dict[str, object]:
    request = dict(_closed(value, _REQUEST_INPUT_FIELDS))
    if request["schema_version"] != _REQUEST_SCHEMA:
        _fail("ASOF_SCHEMA_ERROR")
    case_id = request["case_id"]
    if type(case_id) is not str or case_id != parent.get("case_id"):
        _fail("ASOF_IDENTITY_ERROR")
    session_case = _session_case(case_id)
    if request["session_case_id"] != session_case or request["subject_id_hash"] != parent.get("subject_id_hash"):
        _fail("ASOF_IDENTITY_ERROR")
    _digest(request["subject_id_hash"], "ASOF_IDENTITY_ERROR")
    as_of = _date(request["as_of_date"])
    session_id = request["session_id"]
    if type(session_id) is not str or _SESSION_ID.fullmatch(session_id) is None or session_id[2:10] != as_of.strftime("%Y%m%d"):
        _fail("ASOF_IDENTITY_ERROR")
    if request["chart_source"] != "wenzhen_structured_v1":
        _fail("ASOF_SCHEMA_ERROR")
    hidden = _closed(request["hidden_stems_by_pillar"], frozenset(_PILLARS))
    growth = _closed(request["changsheng_by_pillar"], frozenset(_PILLARS))
    for key in _PILLARS:
        stems = hidden[key]
        if (
            type(stems) is not list
            or not 1 <= len(stems) <= 3
            or any(type(item) is not str or item not in _STEMS for item in stems)
            or len(set(stems)) != len(stems)
        ):
            _fail("ASOF_SCHEMA_ERROR")
        if type(growth[key]) is not str or growth[key] not in _GROWTH:
            _fail("ASOF_SCHEMA_ERROR")
    daiyun = request["daiyun"]
    if type(daiyun) is not list or not 1 <= len(daiyun) <= 20:
        _fail("ASOF_SCHEMA_ERROR")
    previous: datetime.date | None = None
    for sequence, raw in enumerate(daiyun, 1):
        item = _closed(raw, frozenset(("sequence", "stem", "branch", "start_date", "end_date")))
        start, end = _date(item["start_date"]), _date(item["end_date"])
        if (
            type(item["sequence"]) is not int
            or item["sequence"] != sequence
            or type(item["stem"]) is not str
            or item["stem"] not in _STEMS
            or type(item["branch"]) is not str
            or item["branch"] not in _BRANCHES
            or start >= end
            or previous is not None and previous != start
        ):
            _fail("ASOF_SCHEMA_ERROR")
        previous = end
    _timestamp(request["created_at"])
    return request


def _validate_chart(chart: object) -> Mapping[str, object]:
    if not isinstance(chart, Mapping):
        _fail("ASOF_SCHEMA_ERROR")
    four = chart.get("four_pillars")
    if not isinstance(four, Mapping) or set(four) != set(_PILLARS):
        _fail("ASOF_SCHEMA_ERROR")
    for name in _PILLARS:
        raw = four[name]
        if (
            not isinstance(raw, Mapping)
            or set(raw) != {"stem", "branch"}
            or type(raw["stem"]) is not str
            or raw["stem"] not in _STEMS
            or type(raw["branch"]) is not str
            or raw["branch"] not in _BRANCHES
        ):
            _fail("ASOF_SCHEMA_ERROR")
    return chart


def _parent_chart_bytes(parent_root: Path, parent: Mapping[str, object], chart: object) -> bytes:
    chart_name = f"cases/{parent.get('case_id')}/chart.json"
    files = parent.get("files")
    if not isinstance(files, Mapping) or chart_name not in files:
        _fail("ASOF_PARENT_ERROR")
    chart_path = parent_root / Path(chart_name)
    _check_chain(chart_path)
    try:
        raw = chart_path.read_bytes()
        decoded = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        _fail("ASOF_PARENT_ERROR")
    if not hmac.compare_digest(_sha(raw), _digest(files[chart_name], "ASOF_PARENT_ERROR")):
        _fail("ASOF_PARENT_ERROR")
    if decoded != chart or _validate_chart(decoded) != decoded:
        _fail("ASOF_PARENT_ERROR")
    return raw


def _blind_mapping(request: Mapping[str, object], chart: Mapping[str, object]) -> dict[str, object]:
    four = chart["four_pillars"]
    pillars = {
        name: {
            "stem": four[name]["stem"], "branch": four[name]["branch"],
            "hidden_stems": request["hidden_stems_by_pillar"][name],
            "changsheng": request["changsheng_by_pillar"][name],
        }
        for name in _PILLARS
    }
    return {
        "schema_version": BLIND_INPUT_SCHEMA_VERSION,
        "chart_source": request["chart_source"],
        "gender": chart["sex_marker"],
        "pillars": pillars,
        "daiyun": request["daiyun"],
    }


def _publish_directory_no_replace(source: Path, target: Path) -> None:
    if os.name == "nt":
        try:
            os.rename(source, target)
        except FileExistsError:
            _fail("ASOF_CONFLICT_ERROR")
        except OSError:
            _fail("ASOF_IO_ERROR")
        return
    try:
        library = ctypes.CDLL(None, use_errno=True)
        renameat2 = library.renameat2
        renameat2.argtypes = (
            ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint,
        )
        renameat2.restype = ctypes.c_int
    except (AttributeError, OSError):
        _fail("ASOF_IO_ERROR")
    if renameat2(-100, os.fsencode(source), -100, os.fsencode(target), 1) == 0:
        return
    error_number = ctypes.get_errno()
    if error_number in (errno.EEXIST, errno.ENOTEMPTY):
        _fail("ASOF_CONFLICT_ERROR")
    _fail("ASOF_IO_ERROR")


def _create_json(path: Path, document: Mapping[str, object]) -> None:
    _check_new(path)
    if not path.parent.is_dir():
        _fail("ASOF_PATH_ERROR")
    descriptor = -1
    temporary: Path | None = None
    try:
        descriptor, name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".part", dir=path.parent)
        temporary = Path(name)
        with os.fdopen(descriptor, "wb") as stream:
            descriptor = -1
            stream.write(_document_bytes(document))
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError:
            _fail("ASOF_CONFLICT_ERROR")
    except _AsOfError:
        raise
    except OSError:
        _fail("ASOF_IO_ERROR")
    finally:
        if descriptor >= 0:
            try:
                os.close(descriptor)
            except OSError:
                pass
        if temporary is not None:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass


def _evidence(value: Mapping[str, object]) -> EvidenceRef:
    mapping = _closed(value, frozenset(("source", "locator", "excerpt")))
    return EvidenceRef(mapping["source"], mapping["locator"], mapping["excerpt"])


def _citation(value: Mapping[str, object]) -> SourceCitation:
    mapping = _closed(value, frozenset(("source_path", "line", "excerpt")))
    return SourceCitation(mapping["source_path"], mapping["line"], mapping["excerpt"])


def _point(value: Mapping[str, object]) -> LandingPoint:
    mapping = _closed(value, frozenset(("name", "domain", "direction")))
    return LandingPoint(mapping["name"], mapping["domain"], mapping["direction"])


def _package_from_mapping(value: object) -> CareerFreezePackage:
    try:
        return _package_from_mapping_unchecked(value)
    except _AsOfError:
        raise
    except (AttributeError, KeyError, TypeError, ValueError):
        _fail("ASOF_SCHEMA_ERROR")


def _package_from_mapping_unchecked(value: object) -> CareerFreezePackage:
    top = _closed(value, frozenset(("schema_version", "identity", "blind_input_sha256", "fundamentals", "events")))
    if top["schema_version"] != FREEZE_PACKAGE_SCHEMA_VERSION:
        _fail("ASOF_SCHEMA_ERROR")
    identity_raw = _closed(top["identity"], frozenset(("schema_version", "case_id", "as_of_date", "session_id")))
    try:
        identity = SessionIdentity(identity_raw["schema_version"], identity_raw["case_id"], _date(identity_raw["as_of_date"]), identity_raw["session_id"])
    except _AsOfError:
        raise
    except (TypeError, ValueError):
        _fail("ASOF_SCHEMA_ERROR")
    fundamentals_raw, events_raw = top["fundamentals"], top["events"]
    if (
        type(fundamentals_raw) is not list
        or type(events_raw) is not list
        or len(fundamentals_raw) != 1
        or len(events_raw) != 1
    ):
        _fail("ASOF_SCHEMA_ERROR")
    fundamentals = []
    for raw in fundamentals_raw:
        item = _closed(raw, frozenset(("fundamental_id", "window_start", "window_end", "window_center", "center", "reasonable_range", "strongest_alternative", "falsifiers")))
        if type(item["reasonable_range"]) is not list or type(item["falsifiers"]) is not list:
            _fail("ASOF_SCHEMA_ERROR")
        fundamentals.append(FrozenCareerFundamental(item["fundamental_id"], _date(item["window_start"]), _date(item["window_end"]), _date(item["window_center"]), item["center"], tuple(item["reasonable_range"]), item["strongest_alternative"], tuple(item["falsifiers"])))
    events = []
    for raw in events_raw:
        item = _closed(raw, frozenset(("candidate", "landing_set")))
        candidate_raw = _closed(item["candidate"], frozenset(("candidate_id", "domain", "event_type", "window_start", "window_end", "natal_evidence", "daiyun_evidence", "annual_trace", "root_level", "root_evidence", "source_citations", "completion_mode", "supporting_evidence", "counter_evidence", "alternative_hypotheses", "frozen_version", "verification_status", "extension_boundary", "is_primary_event")))
        trace_raw = _closed(candidate_raw["annual_trace"], frozenset(("year", "liunian", "dayun_ganzhi", "relations", "activated_node_ids", "domains", "supporting_evidence", "counter_evidence", "trigger_strength", "crossed_candidate_gate")))
        trace = AnnualInteractionTrace(trace_raw["year"], trace_raw["liunian"], trace_raw["dayun_ganzhi"], tuple(_evidence(row) for row in trace_raw["relations"]), tuple(trace_raw["activated_node_ids"]), tuple(trace_raw["domains"]), tuple(_evidence(row) for row in trace_raw["supporting_evidence"]), tuple(_evidence(row) for row in trace_raw["counter_evidence"]), trace_raw["trigger_strength"], trace_raw["crossed_candidate_gate"])
        candidate = LifeEventCandidate(candidate_raw["candidate_id"], candidate_raw["domain"], candidate_raw["event_type"], _date(candidate_raw["window_start"]), _date(candidate_raw["window_end"]), tuple(_evidence(row) for row in candidate_raw["natal_evidence"]), tuple(_evidence(row) for row in candidate_raw["daiyun_evidence"]), trace, RootLevel(candidate_raw["root_level"]), tuple(_evidence(row) for row in candidate_raw["root_evidence"]), tuple(_citation(row) for row in candidate_raw["source_citations"]), CompletionMode(candidate_raw["completion_mode"]), tuple(_evidence(row) for row in candidate_raw["supporting_evidence"]), tuple(_evidence(row) for row in candidate_raw["counter_evidence"]), tuple(candidate_raw["alternative_hypotheses"]), candidate_raw["frozen_version"], VerificationStatus(candidate_raw["verification_status"]), ExtensionBoundary(candidate_raw["extension_boundary"]), candidate_raw["is_primary_event"])
        landing_raw = _closed(item["landing_set"], frozenset(("function_candidate", "center", "alternatives", "weak_hit_boundary", "falsifiers", "exclusions", "frozen_version")))
        landing = FrozenLandingSet(landing_raw["function_candidate"], _point(landing_raw["center"]), tuple(_point(row) for row in landing_raw["alternatives"]), landing_raw["weak_hit_boundary"], tuple(landing_raw["falsifiers"]), tuple(landing_raw["exclusions"]), landing_raw["frozen_version"])
        events.append(FrozenCareerEvent(candidate, landing))
    try:
        return CareerFreezePackage(top["schema_version"], identity, top["blind_input_sha256"], tuple(fundamentals), tuple(events))
    except (TypeError, ValueError):
        _fail("ASOF_SCHEMA_ERROR")


def _record_projection(
    record: CareerVerificationRecord,
    *,
    state: ConsultationState,
) -> dict[str, object]:
    point = None if record.actual_landing is None else dataclasses.asdict(record.actual_landing)
    constraint = None if record.reality_constraint is None else {
        "state_id": record.reality_constraint.state_id,
        "description": record.reality_constraint.description,
        "closed_landing_names": list(record.reality_constraint.closed_landing_names),
        "reachable_landing_names": list(record.reality_constraint.reachable_landing_names),
        "verified": record.reality_constraint.verified,
    }
    return {
        "envelope": {
            "identity": {
                "schema_version": record.envelope.identity.schema_version,
                "case_id": record.envelope.identity.case_id,
                "as_of_date": record.envelope.identity.as_of_date.isoformat(),
                "session_id": record.envelope.identity.session_id,
            },
            "blind_input_sha256": record.envelope.blind_input_sha256,
            "state": state.value,
        },
        "freeze_package_sha256": record.freeze_package_sha256,
        "item_id": record.item_id,
        "verdict": record.verdict.value,
        "actual_landing": point,
        "reality_constraint": constraint,
        "taxonomy_evidence": list(record.taxonomy_evidence),
        "landing_verdict": None if record.landing_verdict is None else record.landing_verdict.value,
        "frozen_landing_name": record.frozen_landing_name,
        "reason_code": record.reason_code,
    }


def prepare_asof_blind_bundle(
    *,
    parent_bundle_root: Path,
    asof_request: Mapping[str, object],
    target_dir: Path,
    dry_run: bool,
) -> dict[str, object]:
    parent_root = _workspace_path(parent_bundle_root)
    _check_chain(parent_root)
    try:
        parent_verified = verify_single_case_bundle(parent_root)
    except _AsOfError:
        raise
    except (OSError, TypeError, ValueError):
        _fail("ASOF_PARENT_ERROR")
    parent = parent_verified.get("manifest")
    chart = parent_verified.get("chart")
    if not isinstance(parent, Mapping) or not isinstance(chart, Mapping):
        _fail("ASOF_PARENT_ERROR")
    case_id = parent.get("case_id")
    if type(case_id) is not str:
        _fail("ASOF_IDENTITY_ERROR")
    paths = _paths(parent_root, case_id)
    target = _workspace_path(target_dir)
    if target != paths["bundle"]:
        _fail("ASOF_PATH_ERROR")
    request_input = _validate_request_input(asof_request, parent)
    canonical_chart = _validate_chart(chart)
    if canonical_chart.get("case_id") != case_id or canonical_chart.get("sex_marker") != case_id.split("-")[4]:
        _fail("ASOF_IDENTITY_ERROR")
    chart_bytes = _parent_chart_bytes(parent_root, parent, canonical_chart)
    parent_ref = {
        "artifact_path": _canonical_path(parent_root / "bundle-manifest.json"),
        "artifact_sha256": _digest(parent.get("artifact_sha256"), "ASOF_PARENT_ERROR"),
    }
    request_payload = {**request_input, "artifact_path": _canonical_path(paths["request"]), "parents": [parent_ref]}
    request = {**request_payload, "artifact_sha256": _artifact_sha(request_payload)}
    request_ref = {"artifact_path": request["artifact_path"], "artifact_sha256": request["artifact_sha256"]}
    file_bytes = {
        "parent-bundle-ref.json": _document_bytes(parent_ref),
        "asof-request.json": _document_bytes(request),
        "chart.json": chart_bytes,
    }
    manifest_payload = {
        "schema_version": _BUNDLE_SCHEMA,
        "case_id": case_id,
        "session_case_id": request["session_case_id"],
        "subject_id_hash": request["subject_id_hash"],
        "as_of_date": request["as_of_date"],
        "session_id": request["session_id"],
        "created_at": request["created_at"],
        "artifact_path": _canonical_path(target / "bundle-manifest.json"),
        "parents": [parent_ref, request_ref],
        "files": {name: _sha(content) for name, content in file_bytes.items()},
        "bundle_status": "BUNDLE_VERIFIED",
    }
    manifest = {**manifest_payload, "artifact_sha256": _artifact_sha(manifest_payload)}
    _check_new(paths["request"])
    _check_new(target)
    plan = {"request": request, "manifest": manifest}
    if dry_run:
        return plan
    _create_json(paths["request"], request)
    temporary: Path | None = None
    try:
        sealed_request = _sealed(paths["request"], _REQUEST_FIELDS, _REQUEST_SCHEMA)
        sealed_request_bytes = paths["request"].read_bytes()
        request_ref = {
            "artifact_path": sealed_request["artifact_path"],
            "artifact_sha256": sealed_request["artifact_sha256"],
        }
        file_bytes = {
            "parent-bundle-ref.json": _document_bytes(parent_ref),
            "asof-request.json": sealed_request_bytes,
            "chart.json": chart_bytes,
        }
        manifest_payload = {
            "schema_version": _BUNDLE_SCHEMA,
            "case_id": sealed_request["case_id"],
            "session_case_id": sealed_request["session_case_id"],
            "subject_id_hash": sealed_request["subject_id_hash"],
            "as_of_date": sealed_request["as_of_date"],
            "session_id": sealed_request["session_id"],
            "created_at": sealed_request["created_at"],
            "artifact_path": _canonical_path(target / "bundle-manifest.json"),
            "parents": [parent_ref, request_ref],
            "files": {name: _sha(content) for name, content in file_bytes.items()},
            "bundle_status": "BUNDLE_VERIFIED",
        }
        manifest = {**manifest_payload, "artifact_sha256": _artifact_sha(manifest_payload)}
        plan = {"request": sealed_request, "manifest": manifest}
        temporary = Path(tempfile.mkdtemp(prefix=".asof-stage-", dir=paths["case_root"]))
        staged_bytes = {**file_bytes, "bundle-manifest.json": _document_bytes(manifest)}
        for name in ("parent-bundle-ref.json", "asof-request.json", "chart.json", "bundle-manifest.json"):
            (temporary / name).write_bytes(staged_bytes[name])
            if (temporary / name).read_bytes() != staged_bytes[name]:
                _fail("ASOF_IO_ERROR")
        _publish_directory_no_replace(temporary, target)
        temporary = None
        verify_asof_blind_bundle(bundle_root=target)
    except Exception as error:
        if isinstance(error, _AsOfError):
            error.category = "ASOF_IO_ERROR"
            error.reason = "ORPHANED_SEALED_PREREQUISITE"
            raise
        raise _AsOfError("ASOF_IO_ERROR", "ORPHANED_SEALED_PREREQUISITE") from None
    finally:
        if temporary is not None:
            shutil.rmtree(temporary, ignore_errors=True)
    return plan


def verify_asof_blind_bundle(
    *,
    bundle_root: Path,
) -> dict[str, object]:
    root = _workspace_path(bundle_root)
    _check_chain(root)
    if not root.is_dir():
        _fail("ASOF_PATH_ERROR")
    try:
        actual = {item.name for item in root.iterdir()}
    except OSError:
        _fail("ASOF_IO_ERROR")
    expected = {"parent-bundle-ref.json", "asof-request.json", "chart.json", "bundle-manifest.json"}
    if actual != expected or any(_is_link(root / name) or not (root / name).is_file() for name in expected):
        _fail("ASOF_SCHEMA_ERROR")
    manifest = _sealed(root / "bundle-manifest.json", _BUNDLE_FIELDS, _BUNDLE_SCHEMA)
    manifest_case_id = manifest["case_id"]
    if type(manifest_case_id) is not str:
        _fail("ASOF_IDENTITY_ERROR")
    paths = _case_paths(root.parent, manifest_case_id)
    if root != paths["bundle"]:
        _fail("ASOF_PATH_ERROR")
    if manifest["bundle_status"] != "BUNDLE_VERIFIED":
        _fail("ASOF_STATE_ERROR")
    files = _closed(manifest["files"], frozenset(("parent-bundle-ref.json", "asof-request.json", "chart.json")))
    for name, digest in files.items():
        try:
            raw = (root / name).read_bytes()
        except OSError:
            _fail("ASOF_IO_ERROR")
        if not hmac.compare_digest(_sha(raw), _digest(digest)):
            _fail("ASOF_HASH_ERROR")
    parent_ref = _ref(_read_json(root / "parent-bundle-ref.json"))
    manifest_parents = manifest["parents"]
    if type(manifest_parents) is not list or len(manifest_parents) != 2:
        _fail("ASOF_PARENT_ERROR")
    request_path = _stored_path(_ref(manifest_parents[1])["artifact_path"])
    if request_path != paths["request"]:
        _fail("ASOF_PATH_ERROR")
    request = _sealed(request_path, _REQUEST_FIELDS, _REQUEST_SCHEMA)
    bundled_request = _read_json(root / "asof-request.json")
    try:
        bundled_request_bytes = (root / "asof-request.json").read_bytes()
    except OSError:
        _fail("ASOF_IO_ERROR")
    if request != bundled_request or _document_bytes(request) != bundled_request_bytes:
        _fail("ASOF_PARENT_ERROR")
    if manifest["parents"] != [parent_ref, {"artifact_path": request["artifact_path"], "artifact_sha256": request["artifact_sha256"]}] or request["parents"] != [parent_ref]:
        _fail("ASOF_PARENT_ERROR")
    parent_root = _stored_path(parent_ref["artifact_path"]).parent
    try:
        parent_verified = verify_single_case_bundle(parent_root)
    except _AsOfError:
        raise
    except (OSError, TypeError, ValueError):
        _fail("ASOF_PARENT_ERROR")
    parent = parent_verified.get("manifest")
    if not isinstance(parent, Mapping) or parent.get("artifact_sha256") != parent_ref["artifact_sha256"]:
        _fail("ASOF_PARENT_ERROR")
    parent_chart_bytes = _parent_chart_bytes(parent_root, parent, parent_verified.get("chart"))
    try:
        bundled_chart_bytes = (root / "chart.json").read_bytes()
        chart = json.loads(bundled_chart_bytes.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        _fail("ASOF_IO_ERROR")
    if bundled_chart_bytes != parent_chart_bytes or chart != parent_verified.get("chart"):
        _fail("ASOF_PARENT_ERROR")
    _validate_chart(chart)
    request_input = {key: request[key] for key in _REQUEST_INPUT_FIELDS}
    _validate_request_input(request_input, parent)
    if manifest["case_id"] != request["case_id"] or manifest["session_case_id"] != request["session_case_id"] or manifest["subject_id_hash"] != request["subject_id_hash"] or manifest["as_of_date"] != request["as_of_date"] or manifest["session_id"] != request["session_id"] or manifest["created_at"] != request["created_at"]:
        _fail("ASOF_IDENTITY_ERROR")
    try:
        blind_input = blind_chart_input_from_mapping(_blind_mapping(request, chart))
        identity = SessionIdentity(SESSION_SCHEMA_VERSION, request["session_case_id"], _date(request["as_of_date"]), request["session_id"])
        initial_envelope = create_initial_envelope(identity, blind_input)
    except _AsOfError:
        raise
    except (AttributeError, KeyError, TypeError, ValueError):
        _fail("ASOF_SCHEMA_ERROR")
    if identity.session_id[2:10] != identity.as_of_date.strftime("%Y%m%d"):
        _fail("ASOF_IDENTITY_ERROR")
    return {"manifest": manifest, "request": request, "chart": chart, "blind_input": blind_input, "identity": identity, "initial_envelope": initial_envelope}


def build_career_blind_draft(
    *,
    blind_input: BlindChartInput,
    identity: SessionIdentity,
) -> CareerBlindDraft:
    eligible = [item for item in blind_input.daiyun if item.end_date <= identity.as_of_date]
    if not eligible:
        _fail("ASOF_DOMAIN_ERROR")
    probe = max(eligible, key=lambda item: item.sequence)
    pillar_token = "".join(getattr(blind_input.pillars, name).stem + getattr(blind_input.pillars, name).branch for name in _PILLARS)
    token = f"{identity.case_id}|{identity.as_of_date.isoformat()}|{pillar_token}|{probe.sequence}|{probe.stem}{probe.branch}|{probe.start_date.isoformat()}|{probe.end_date.isoformat()}"
    digest = _sha(token.encode("utf-8"))
    center = datetime.date.fromordinal((probe.start_date.toordinal() + probe.end_date.toordinal()) // 2)
    fundamental = FrozenCareerFundamental(
        "career-fundamental-" + digest[:16], probe.start_date, probe.end_date, center,
        "STRUCTURAL_PROBE_ONLY", ("STRUCTURAL_PROBE_ONLY",), "NO_CAREER_INFERENCE",
        ("PROOF_SEAM_IS_NOT_A_CAREER_PREDICTION",),
    )
    natal = EvidenceRef("blind-input", "pillars", pillar_token)
    daiyun = EvidenceRef("blind-input", f"daiyun[{probe.sequence}]", f"{probe.stem}{probe.branch}|{probe.start_date.isoformat()}|{probe.end_date.isoformat()}")
    trace = AnnualInteractionTrace(probe.end_date.year, "STRUCTURAL_PROBE_ONLY", probe.stem + probe.branch, (daiyun,), (f"daiyun-{probe.sequence}",), ("career",), (natal, daiyun), (), "low", True)
    candidate = LifeEventCandidate(
        "career-event-" + digest[:16], "career", "STRUCTURAL_PROBE_ONLY", probe.start_date,
        probe.end_date, (natal,), (daiyun,), trace, RootLevel.WEAK_ROOT, (natal,),
        (SourceCitation("plans/as-of-blind-bundle-first-proof-point-contract-2026-08-07.md", 1, "# as-of blind-bundle First Proof Point 合同（2026-08-07）"),),
        CompletionMode.COMPLETE_LATENT, (natal,), (), ("NO_CAREER_INFERENCE",),
        "prospective-asof-structural-probe/v1", VerificationStatus.FROZEN,
        ExtensionBoundary.REMAINDER_ONLY_RECHECK_CROSS_DAIYUN, True,
    )
    landing = FrozenLandingSet(
        "STRUCTURAL_PROBE_ONLY", LandingPoint("STRUCTURAL_PROBE_ONLY", "career", "structural-probe"),
        (), "EXACT_PROBE_LABEL_ONLY", ("ANY_REAL_CAREER_CLAIM",), ("ACCURACY_INFERENCE",),
        "prospective-asof-structural-probe/v1",
    )
    return CareerBlindDraft((fundamental,), (FrozenCareerEvent(candidate, landing),))


def build_asof_frozen_artifact(
    *,
    bundle_root: Path,
) -> dict[str, object]:
    verified = verify_asof_blind_bundle(bundle_root=bundle_root)
    try:
        drafted = transition_session(verified["initial_envelope"], ConsultationState.BLIND_DRAFTED)
        draft = build_career_blind_draft(blind_input=verified["blind_input"], identity=verified["identity"])
        frozen_envelope, package = freeze_career_draft(drafted, draft)
        package_bytes = freeze_package_to_canonical_bytes(package)
        package_sha = compute_freeze_package_sha256(package)
    except _AsOfError:
        raise
    except (AttributeError, KeyError, TypeError, ValueError):
        _fail("ASOF_DOMAIN_ERROR")
    if not hmac.compare_digest(_sha(package_bytes), package_sha):
        _fail("ASOF_HASH_ERROR")
    manifest = verified["manifest"]
    case_id = manifest["case_id"]
    actual_bundle_root = _workspace_path(bundle_root)
    paths = _case_paths(actual_bundle_root.parent, case_id)
    if actual_bundle_root != paths["bundle"]:
        _fail("ASOF_PATH_ERROR")
    bundle_ref = {"artifact_path": manifest["artifact_path"], "artifact_sha256": manifest["artifact_sha256"]}
    try:
        package_projection = json.loads(package_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        _fail("ASOF_DOMAIN_ERROR")
    payload = {
        "schema_version": _FROZEN_SCHEMA, "case_id": case_id,
        "session_case_id": manifest["session_case_id"], "subject_id_hash": manifest["subject_id_hash"],
        "as_of_date": manifest["as_of_date"], "session_id": manifest["session_id"],
        "frozen_at": verified["request"]["created_at"], "artifact_path": _canonical_path(paths["frozen"]),
        "parents": [bundle_ref], "freeze_status": "FROZEN_SEALED",
        "blind_input_sha256": frozen_envelope.blind_input_sha256,
        "freeze_package_sha256": package_sha,
        "freeze_package": package_projection,
    }
    return {**payload, "artifact_sha256": _artifact_sha(payload)}


def build_asof_feedback_release(
    *,
    frozen_artifact: Mapping[str, object],
    created_at: str,
) -> dict[str, object]:
    supplied = dict(_closed(frozen_artifact, _FROZEN_FIELDS))
    path = _stored_path(supplied["artifact_path"])
    case_id_value = supplied["case_id"]
    if type(case_id_value) is not str:
        _fail("ASOF_IDENTITY_ERROR")
    if path != _case_paths(path.parent, case_id_value)["frozen"]:
        _fail("ASOF_PATH_ERROR")
    frozen = _sealed(path, _FROZEN_FIELDS, _FROZEN_SCHEMA)
    if frozen != supplied or frozen["freeze_status"] != "FROZEN_SEALED":
        _fail("ASOF_STATE_ERROR")
    parents = frozen["parents"]
    if type(parents) is not list or len(parents) != 1:
        _fail("ASOF_PARENT_ERROR")
    bundle_ref = _ref(parents[0])
    bundle = verify_asof_blind_bundle(bundle_root=_stored_path(bundle_ref["artifact_path"]).parent)
    if bundle["manifest"]["artifact_sha256"] != bundle_ref["artifact_sha256"]:
        _fail("ASOF_PARENT_ERROR")
    for key in ("case_id", "session_case_id", "subject_id_hash", "as_of_date", "session_id"):
        if frozen[key] != bundle["manifest"][key]:
            _fail("ASOF_IDENTITY_ERROR")
    package = _package_from_mapping(frozen["freeze_package"])
    if (
        package.identity.case_id != frozen["session_case_id"]
        or package.identity.as_of_date.isoformat() != frozen["as_of_date"]
        or package.identity.session_id != frozen["session_id"]
        or package.blind_input_sha256 != frozen["blind_input_sha256"]
        or frozen["blind_input_sha256"] != bundle["initial_envelope"].blind_input_sha256
        or frozen["frozen_at"] != bundle["request"]["created_at"]
    ):
        _fail("ASOF_IDENTITY_ERROR")
    try:
        package_sha = compute_freeze_package_sha256(package)
        package_projection = json.loads(freeze_package_to_canonical_bytes(package).decode("utf-8"))
    except (TypeError, ValueError, UnicodeDecodeError, json.JSONDecodeError):
        _fail("ASOF_SCHEMA_ERROR")
    if not hmac.compare_digest(package_sha, _digest(frozen["freeze_package_sha256"])) or package_projection != frozen["freeze_package"]:
        _fail("ASOF_HASH_ERROR")
    frozen_time, release_time = _timestamp(frozen["frozen_at"]), _timestamp(created_at)
    if release_time < frozen_time:
        _fail("ASOF_TIME_ERROR")
    case_id = frozen["case_id"]
    paths = _case_paths(path.parent, case_id)
    payload = {
        "schema_version": _RELEASE_SCHEMA, "case_id": case_id,
        "session_case_id": frozen["session_case_id"], "subject_id_hash": frozen["subject_id_hash"],
        "as_of_date": frozen["as_of_date"], "session_id": frozen["session_id"],
        "created_at": created_at, "artifact_path": _canonical_path(paths["release"]),
        "parents": [{"artifact_path": frozen["artifact_path"], "artifact_sha256": frozen["artifact_sha256"]}],
        "release_status": "RELEASED", "blind_input_sha256": frozen["blind_input_sha256"],
        "freeze_package_sha256": frozen["freeze_package_sha256"],
    }
    return {**payload, "artifact_sha256": _artifact_sha(payload)}


def verify_asof_feedback_release(
    *,
    release: Mapping[str, object],
) -> tuple[dict[str, object], dict[str, object]]:
    supplied = dict(_closed(release, _RELEASE_FIELDS))
    release_path = _stored_path(supplied["artifact_path"])
    supplied_case_id = supplied["case_id"]
    if type(supplied_case_id) is not str:
        _fail("ASOF_IDENTITY_ERROR")
    if release_path != _case_paths(release_path.parent, supplied_case_id)["release"]:
        _fail("ASOF_PATH_ERROR")
    actual = _sealed(release_path, _RELEASE_FIELDS, _RELEASE_SCHEMA)
    if actual != supplied or actual["release_status"] != "RELEASED":
        _fail("ASOF_STATE_ERROR")
    parents = actual["parents"]
    if type(parents) is not list or len(parents) != 1:
        _fail("ASOF_PARENT_ERROR")
    frozen_ref = _ref(parents[0])
    frozen_path = _stored_path(frozen_ref["artifact_path"])
    canonical_frozen_path = _case_paths(release_path.parent, actual["case_id"])["frozen"]
    if frozen_path != canonical_frozen_path:
        _fail("ASOF_PATH_ERROR")
    frozen = _sealed(frozen_path, _FROZEN_FIELDS, _FROZEN_SCHEMA)
    if frozen["artifact_sha256"] != frozen_ref["artifact_sha256"] or frozen["freeze_status"] != "FROZEN_SEALED":
        _fail("ASOF_PARENT_ERROR")
    frozen_parents = frozen["parents"]
    if type(frozen_parents) is not list or len(frozen_parents) != 1:
        _fail("ASOF_PARENT_ERROR")
    bundle_ref = _ref(frozen_parents[0])
    bundle = verify_asof_blind_bundle(bundle_root=_stored_path(bundle_ref["artifact_path"]).parent)
    if bundle["manifest"]["artifact_sha256"] != bundle_ref["artifact_sha256"]:
        _fail("ASOF_PARENT_ERROR")
    for key in ("case_id", "session_case_id", "subject_id_hash", "as_of_date", "session_id"):
        if frozen[key] != bundle["manifest"][key]:
            _fail("ASOF_IDENTITY_ERROR")
    package = _package_from_mapping(frozen["freeze_package"])
    if (
        package.identity.case_id != frozen["session_case_id"]
        or package.identity.as_of_date.isoformat() != frozen["as_of_date"]
        or package.identity.session_id != frozen["session_id"]
        or package.blind_input_sha256 != frozen["blind_input_sha256"]
        or frozen["blind_input_sha256"] != bundle["initial_envelope"].blind_input_sha256
        or frozen["frozen_at"] != bundle["request"]["created_at"]
    ):
        _fail("ASOF_IDENTITY_ERROR")
    try:
        package_sha = compute_freeze_package_sha256(package)
        package_projection = json.loads(freeze_package_to_canonical_bytes(package).decode("utf-8"))
    except (TypeError, ValueError, UnicodeDecodeError, json.JSONDecodeError):
        _fail("ASOF_SCHEMA_ERROR")
    if package_sha != frozen["freeze_package_sha256"] or package_projection != frozen["freeze_package"]:
        _fail("ASOF_HASH_ERROR")
    for key in ("case_id", "session_case_id", "subject_id_hash", "as_of_date", "session_id", "blind_input_sha256", "freeze_package_sha256"):
        if actual[key] != frozen[key]:
            _fail("ASOF_IDENTITY_ERROR")
    if _timestamp(actual["created_at"]) < _timestamp(frozen["frozen_at"]):
        _fail("ASOF_TIME_ERROR")
    return actual, frozen


def collect_asof_verification(
    *,
    release: Mapping[str, object],
    custody_reader: Callable[[], Mapping[str, object]],
    collected_at: str,
) -> dict[str, object]:
    actual_release, frozen = verify_asof_feedback_release(release=release)
    collected = _timestamp(collected_at)
    if collected < _timestamp(actual_release["created_at"]):
        _fail("ASOF_TIME_ERROR")
    try:
        custody_raw = custody_reader()
    except Exception:
        _fail("ASOF_CUSTODY_ERROR")
    custody = _closed(custody_raw, _CUSTODY_FIELDS, "ASOF_CUSTODY_ERROR")
    if custody["schema_version"] != _CUSTODY_SCHEMA:
        _fail("ASOF_CUSTODY_ERROR")
    def forbidden(value: object) -> bool:
        if isinstance(value, Mapping):
            return any(type(key) is not str or key in _FORBIDDEN_CUSTODY_KEYS or forbidden(item) for key, item in value.items())
        return isinstance(value, list) and any(forbidden(item) for item in value)
    if forbidden(custody):
        _fail("ASOF_CUSTODY_ERROR")
    for key in ("case_id", "session_case_id", "subject_id_hash", "session_id", "freeze_package_sha256"):
        if custody[key] != frozen[key]:
            _fail("ASOF_CUSTODY_ERROR")
    package = _package_from_mapping(frozen["freeze_package"])
    rows = custody["verifications"]
    if type(rows) is not list or len(rows) != 1 or len(package.events) != 1:
        _fail("ASOF_CUSTODY_ERROR")
    event = package.events[0]
    row = rows[0]
    if not isinstance(row, Mapping) or row.get("item_id") != event.candidate.candidate_id:
        _fail("ASOF_CUSTODY_ERROR")
    try:
        frozen_envelope = SessionEnvelope(
            package.identity, frozen["blind_input_sha256"], ConsultationState.FROZEN,
        )
        opened = open_verification(frozen_envelope, package, frozen["freeze_package_sha256"])
        verification = verification_input_from_mapping(row)
        record = record_career_verification(opened, package, verification)
        records = [_record_projection(record, state=opened.state)]
    except _AsOfError:
        raise
    except (AttributeError, KeyError, TypeError, ValueError):
        _fail("ASOF_CUSTODY_ERROR")
    projected = records[0]
    if (
        projected["envelope"]["state"] != "VERIFICATION_OPEN"
        or projected["envelope"]["identity"] != {
            "schema_version": package.identity.schema_version,
            "case_id": package.identity.case_id,
            "as_of_date": package.identity.as_of_date.isoformat(),
            "session_id": package.identity.session_id,
        }
        or projected["envelope"]["blind_input_sha256"] != frozen["blind_input_sha256"]
        or projected["freeze_package_sha256"] != frozen["freeze_package_sha256"]
        or projected["item_id"] != event.candidate.candidate_id
    ):
        _fail("ASOF_STATE_ERROR")
    case_id = frozen["case_id"]
    actual_release_path = _stored_path(actual_release["artifact_path"])
    paths = _case_paths(actual_release_path.parent, case_id)
    if actual_release_path != paths["release"]:
        _fail("ASOF_PATH_ERROR")
    payload = {
        "schema_version": _RESULT_SCHEMA, "case_id": case_id,
        "session_case_id": frozen["session_case_id"], "subject_id_hash": frozen["subject_id_hash"],
        "as_of_date": frozen["as_of_date"], "session_id": frozen["session_id"],
        "collected_at": collected_at, "artifact_path": _canonical_path(paths["verified"]),
        "parents": [
            {"artifact_path": actual_release["artifact_path"], "artifact_sha256": actual_release["artifact_sha256"]},
            {"artifact_path": frozen["artifact_path"], "artifact_sha256": frozen["artifact_sha256"]},
        ],
        "verification_status": "VERIFIED_RESULT_SEALED",
        "blind_input_sha256": frozen["blind_input_sha256"],
        "freeze_package_sha256": frozen["freeze_package_sha256"], "records": records,
    }
    return {**payload, "artifact_sha256": _artifact_sha(payload)}



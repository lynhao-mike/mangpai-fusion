"""三领域 prospective 盲测的不可变领域契约与确定性评分。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Iterable, Literal, Mapping

from engine.evaluation.prospective_artifacts import canonical_artifact_sha256
from engine.v5.domain import V5RunSnapshot
from engine.v5.domain_metadata_integrity import (
    validate_capability_metadata,
    validate_domain_evaluation_metadata,
)
from engine.v5.domain_slices.contract import DOMAIN_IDS, DomainAnalysisRequest, DomainId

Track = Literal["prospective", "historical"]
ClaimState = Literal["claim", "abstain"]
Outcome = Literal["hit", "miss", "pending", "unknown"]

INTAKE_SCHEMA = "domain-prospective-intake/v1"
FREEZE_SCHEMA = "domain-prospective-freeze/v1"
LABEL_SCHEMA = "domain-prospective-labels/v1"
REVEAL_SCHEMA = "domain-prospective-reveal/v1"
SCORE_SCHEMA = "domain-prospective-score/v1"
STATUS_SCHEMA = "domain-prospective-status/v1"
MIN_PROSPECTIVE_CASES = 30
_ALLOWED_INTAKE = frozenset(
    {"schema_version", "case_id", "track", "gender", "birth_datetime", "as_of_date", "domains"}
)
_FORBIDDEN_KEYS = frozenset(
    {
        "feedback",
        "labels",
        "label",
        "report",
        "knownfacts",
        "known_facts",
        "modelprediction",
        "model_prediction",
        "prediction",
        "predictions",
        "occupation",
        "realitystatus",
        "reality_status",
    }
)


def _normal_key(value: object) -> str:
    return "".join(character for character in str(value).lower() if character.isalnum() or character == "_")


def _assert_no_leakage(value: object, path: str = "root") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if _normal_key(key) in _FORBIDDEN_KEYS:
                raise ValueError(f"intake leakage field at {path}.{key}")
            _assert_no_leakage(child, f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            _assert_no_leakage(child, f"{path}[{index}]")


def _require_text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} is required")
    return value.strip()


def _parse_datetime(value: object) -> datetime:
    text = _require_text(value, "birth_datetime")
    try:
        return datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError("birth_datetime must be ISO-8601") from exc


def _parse_date(value: object) -> date:
    text = _require_text(value, "as_of_date")
    try:
        return date.fromisoformat(text)
    except ValueError as exc:
        raise ValueError("as_of_date must be YYYY-MM-DD") from exc


def _hash_payload(payload: Mapping[str, Any], hash_field: str) -> str:
    return canonical_artifact_sha256({key: value for key, value in payload.items() if key != hash_field})


@dataclass(frozen=True, slots=True)
class DomainProspectiveIntake:
    case_id: str
    track: Track
    request: DomainAnalysisRequest
    identity_hash: str
    schema_version: str = INTAKE_SCHEMA

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "case_id": self.case_id,
            "track": self.track,
            "request": self.request.to_dict(),
            "identity_hash": self.identity_hash,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "DomainProspectiveIntake":
        if data.get("schema_version") != INTAKE_SCHEMA:
            raise ValueError("intake schema_version is invalid")
        return cls(
            case_id=_require_text(data.get("case_id"), "case_id"),
            track=_validate_track(data.get("track")),
            request=DomainAnalysisRequest.from_dict(dict(data.get("request", {}))),
            identity_hash=_require_text(data.get("identity_hash"), "identity_hash"),
        )


@dataclass(frozen=True, slots=True)
class FrozenDomainClaim:
    claim_id: str
    domain: DomainId
    task_id: str
    state: ClaimState
    school: str = ""
    claim_type: str = ""
    source_claim_id: str = ""
    source_claim_hash: str = ""

    def to_dict(self) -> dict[str, str]:
        result = {
            "claim_id": self.claim_id,
            "domain": self.domain,
            "task_id": self.task_id,
            "state": self.state,
        }
        for key in ("school", "claim_type", "source_claim_id", "source_claim_hash"):
            value = getattr(self, key)
            if value:
                result[key] = value
        return result

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "FrozenDomainClaim":
        domain = data.get("domain")
        state = data.get("state")
        if domain not in DOMAIN_IDS:
            raise ValueError("claim domain is invalid")
        if state not in {"claim", "abstain"}:
            raise ValueError("claim state must be claim or abstain")
        return cls(
            claim_id=_require_text(data.get("claim_id"), "claim_id"),
            domain=domain,
            task_id=_require_text(data.get("task_id"), "task_id"),
            state=state,
            school=str(data.get("school", "")).strip(),
            claim_type=str(data.get("claim_type", "")).strip(),
            source_claim_id=str(data.get("source_claim_id", "")).strip(),
            source_claim_hash=str(data.get("source_claim_hash", "")).strip(),
        )


@dataclass(frozen=True, slots=True)
class DomainFreeze:
    case_id: str
    track: Track
    intake_hash: str
    snapshot_hash: str
    snapshot: V5RunSnapshot
    claims: tuple[FrozenDomainClaim, ...]
    freeze_hash: str
    schema_version: str = FREEZE_SCHEMA

    def unsigned_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "case_id": self.case_id,
            "track": self.track,
            "intake_hash": self.intake_hash,
            "snapshot_hash": self.snapshot_hash,
            "snapshot": self.snapshot.to_dict(),
            "claims": [claim.to_dict() for claim in self.claims],
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self.unsigned_dict(), "freeze_hash": self.freeze_hash}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "DomainFreeze":
        if data.get("schema_version") != FREEZE_SCHEMA:
            raise ValueError("freeze schema_version is invalid")
        result = cls(
            case_id=_require_text(data.get("case_id"), "case_id"),
            track=_validate_track(data.get("track")),
            intake_hash=_require_text(data.get("intake_hash"), "intake_hash"),
            snapshot_hash=_require_text(data.get("snapshot_hash"), "snapshot_hash"),
            snapshot=V5RunSnapshot.from_dict(dict(data.get("snapshot", {}))),
            claims=tuple(FrozenDomainClaim.from_dict(item) for item in data.get("claims", [])),
            freeze_hash=_require_text(data.get("freeze_hash"), "freeze_hash"),
        )
        verify_freeze(result)
        return result


@dataclass(frozen=True, slots=True)
class RevealedDomainLabels:
    case_id: str
    track: Track
    freeze_hash: str
    labels: tuple[dict[str, str], ...]
    reveal_hash: str
    schema_version: str = REVEAL_SCHEMA

    def unsigned_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "case_id": self.case_id,
            "track": self.track,
            "freeze_hash": self.freeze_hash,
            "labels": [dict(label) for label in self.labels],
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self.unsigned_dict(), "reveal_hash": self.reveal_hash}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "RevealedDomainLabels":
        if data.get("schema_version") != REVEAL_SCHEMA:
            raise ValueError("reveal schema_version is invalid")
        result = cls(
            case_id=_require_text(data.get("case_id"), "case_id"),
            track=_validate_track(data.get("track")),
            freeze_hash=_require_text(data.get("freeze_hash"), "freeze_hash"),
            labels=tuple(dict(item) for item in data.get("labels", [])),
            reveal_hash=_require_text(data.get("reveal_hash"), "reveal_hash"),
        )
        if _hash_payload(result.to_dict(), "reveal_hash") != result.reveal_hash:
            raise ValueError("reveal hash mismatch")
        return result


@dataclass(frozen=True, slots=True)
class DomainScore:
    case_id: str
    track: Track
    freeze_hash: str
    reveal_hash: str
    metrics: dict[str, Any]
    score_hash: str
    schema_version: str = SCORE_SCHEMA

    def unsigned_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "case_id": self.case_id,
            "track": self.track,
            "freeze_hash": self.freeze_hash,
            "reveal_hash": self.reveal_hash,
            "metrics": self.metrics,
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self.unsigned_dict(), "score_hash": self.score_hash}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "DomainScore":
        if data.get("schema_version") != SCORE_SCHEMA:
            raise ValueError("score schema_version is invalid")
        result = cls(
            case_id=_require_text(data.get("case_id"), "case_id"),
            track=_validate_track(data.get("track")),
            freeze_hash=_require_text(data.get("freeze_hash"), "freeze_hash"),
            reveal_hash=_require_text(data.get("reveal_hash"), "reveal_hash"),
            metrics=dict(data.get("metrics", {})),
            score_hash=_require_text(data.get("score_hash"), "score_hash"),
        )
        if _hash_payload(result.to_dict(), "score_hash") != result.score_hash:
            raise ValueError("score hash mismatch")
        return result


def _validate_track(value: object) -> Track:
    if value not in {"prospective", "historical"}:
        raise ValueError("track must be prospective or historical")
    return value


def build_intake(
    payload: Mapping[str, Any], *, existing: Iterable[DomainProspectiveIntake] = ()
) -> DomainProspectiveIntake:
    _assert_no_leakage(payload)
    unknown = set(payload).difference(_ALLOWED_INTAKE)
    missing = _ALLOWED_INTAKE.difference(payload)
    if unknown or missing:
        raise ValueError("intake must use the strict blind whitelist")
    if payload.get("schema_version") != INTAKE_SCHEMA:
        raise ValueError("intake schema_version is invalid")
    case_id = _require_text(payload.get("case_id"), "case_id")
    track = _validate_track(payload.get("track"))
    domains = payload.get("domains")
    if not isinstance(domains, (list, tuple)):
        raise ValueError("domains must be a list")
    request = DomainAnalysisRequest(
        gender=_require_text(payload.get("gender"), "gender"),
        birth_datetime=_parse_datetime(payload.get("birth_datetime")),
        as_of_date=_parse_date(payload.get("as_of_date")),
        domains=tuple(domains),
    )
    identity_hash = canonical_artifact_sha256(
        {"gender": request.gender, "birth_datetime": request.birth_datetime.isoformat()}
    )
    for prior in existing:
        if prior.case_id == case_id:
            raise ValueError("duplicate case_id")
        if prior.identity_hash == identity_hash:
            raise ValueError("duplicate identity")
    return DomainProspectiveIntake(case_id, track, request, identity_hash)


def _claims_from_snapshot(snapshot: V5RunSnapshot) -> tuple[FrozenDomainClaim, ...]:
    if "slice_coverage" in snapshot.metadata or "domain_evaluation_integrity" in snapshot.metadata:
        validate_capability_metadata(snapshot.metadata)
        validate_domain_evaluation_metadata(snapshot.claims, snapshot.metadata)
    raw_claims = snapshot.metadata.get("domain_evaluation_claims")
    if not isinstance(raw_claims, list) or not raw_claims:
        raise ValueError("snapshot must contain domain_evaluation_claims")
    claims = tuple(FrozenDomainClaim.from_dict(item) for item in raw_claims)
    identities = [(claim.claim_id, claim.domain, claim.task_id) for claim in claims]
    if len(identities) != len(set(identities)):
        raise ValueError("duplicate claim identity")
    return claims


def freeze_snapshot(intake: DomainProspectiveIntake, snapshot: V5RunSnapshot) -> DomainFreeze:
    if snapshot.case_id != intake.case_id:
        raise ValueError("intake and snapshot case_id must match")
    if not snapshot.output_hash_matches():
        raise ValueError("V5RunSnapshot output hash mismatch")
    expected_request = {
        "gender": intake.request.gender,
        "birth_datetime": intake.request.birth_datetime.isoformat(),
        "as_of_date": intake.request.as_of_date.isoformat(),
        "domains": list(intake.request.domains),
    }
    actual_request = {
        "gender": snapshot.canonical_input.get("gender_marker"),
        "birth_datetime": snapshot.canonical_input.get("birth_datetime"),
        "as_of_date": snapshot.canonical_input.get("as_of_date"),
        "domains": snapshot.metadata.get("requested_domains"),
    }
    try:
        actual_birth = datetime.fromisoformat(str(actual_request["birth_datetime"])).isoformat()
    except (TypeError, ValueError):
        actual_birth = None
    actual_request["birth_datetime"] = actual_birth
    if actual_request != expected_request:
        raise ValueError("snapshot normalized request does not match intake request")
    claims = _claims_from_snapshot(snapshot)
    if any(claim.domain not in set(intake.request.domains) for claim in claims):
        raise ValueError("snapshot claim domain is outside intake scope")
    unsigned = DomainFreeze(
        case_id=intake.case_id,
        track=intake.track,
        intake_hash=canonical_artifact_sha256(intake.to_dict()),
        snapshot_hash=snapshot.hash(),
        snapshot=snapshot,
        claims=claims,
        freeze_hash="",
    )
    return DomainFreeze(
        case_id=unsigned.case_id,
        track=unsigned.track,
        intake_hash=unsigned.intake_hash,
        snapshot_hash=unsigned.snapshot_hash,
        snapshot=unsigned.snapshot,
        claims=unsigned.claims,
        freeze_hash=canonical_artifact_sha256(unsigned.unsigned_dict()),
    )


def verify_freeze(frozen: DomainFreeze) -> None:
    if frozen.snapshot.case_id != frozen.case_id:
        raise ValueError("freeze snapshot case_id mismatch")
    if not frozen.snapshot.output_hash_matches():
        raise ValueError("freeze snapshot output hash mismatch")
    if frozen.snapshot.hash() != frozen.snapshot_hash:
        raise ValueError("snapshot hash mismatch")
    if canonical_artifact_sha256(frozen.unsigned_dict()) != frozen.freeze_hash:
        raise ValueError("freeze hash mismatch")
    if _claims_from_snapshot(frozen.snapshot) != frozen.claims:
        raise ValueError("frozen claims differ from snapshot")


def reveal_labels(
    frozen: DomainFreeze | Mapping[str, Any] | None, labels_document: Mapping[str, Any]
) -> RevealedDomainLabels:
    if frozen is None:
        raise ValueError("freeze is required before reveal")
    actual = frozen if isinstance(frozen, DomainFreeze) else DomainFreeze.from_dict(frozen)
    verify_freeze(actual)
    if set(labels_document) != {"schema_version", "freeze_hash", "labels"}:
        raise ValueError("labels document has invalid schema")
    if labels_document.get("schema_version") != LABEL_SCHEMA:
        raise ValueError("labels schema_version is invalid")
    if labels_document.get("freeze_hash") != actual.freeze_hash:
        raise ValueError("labels freeze_hash does not match freeze")
    raw_labels = labels_document.get("labels")
    if not isinstance(raw_labels, list):
        raise ValueError("labels must be a list")
    frozen_by_id = {claim.claim_id: claim for claim in actual.claims}
    labels: list[dict[str, str]] = []
    seen: set[str] = set()
    for raw in raw_labels:
        if not isinstance(raw, Mapping) or set(raw) != {"claim_id", "domain", "task_id", "outcome"}:
            raise ValueError("label record has invalid schema")
        claim_id = _require_text(raw.get("claim_id"), "claim_id")
        if claim_id in seen:
            raise ValueError("duplicate label claim_id")
        seen.add(claim_id)
        claim = frozen_by_id.get(claim_id)
        if claim is None or raw.get("domain") != claim.domain or raw.get("task_id") != claim.task_id:
            raise ValueError("label identity does not match frozen claim")
        if raw.get("outcome") not in {"hit", "miss", "pending", "unknown"}:
            raise ValueError("label outcome must be hit, miss, pending, or unknown")
        labels.append({key: str(raw[key]) for key in ("claim_id", "domain", "task_id", "outcome")})
    labels.sort(key=lambda item: (item["domain"], item["task_id"], item["claim_id"]))
    unsigned = RevealedDomainLabels(actual.case_id, actual.track, actual.freeze_hash, tuple(labels), "")
    return RevealedDomainLabels(
        actual.case_id,
        actual.track,
        actual.freeze_hash,
        tuple(labels),
        canonical_artifact_sha256(unsigned.unsigned_dict()),
    )


def _empty_bucket() -> dict[str, Any]:
    return {
        "claim_count": 0,
        "labeled_count": 0,
        "scored_count": 0,
        "hit_count": 0,
        "miss_count": 0,
        "pending_count": 0,
        "abstain_count": 0,
        "label_coverage": None,
        "scored_coverage": None,
        "accuracy": None,
    }


def _add(bucket: dict[str, Any], *, state: ClaimState, outcome: Outcome | None) -> None:
    if state == "abstain":
        bucket["abstain_count"] += 1
        return
    bucket["claim_count"] += 1
    if outcome is None:
        return
    bucket["labeled_count"] += 1
    if outcome in {"pending", "unknown"}:
        bucket["pending_count"] += 1
        return
    bucket["scored_count"] += 1
    bucket[f"{outcome}_count"] += 1


def _finish(bucket: dict[str, Any]) -> None:
    bucket["label_coverage"] = (
        round(bucket["labeled_count"] / bucket["claim_count"], 12)
        if bucket["claim_count"]
        else None
    )
    bucket["scored_coverage"] = (
        round(bucket["scored_count"] / bucket["claim_count"], 12)
        if bucket["claim_count"]
        else None
    )
    bucket["accuracy"] = (
        round(bucket["hit_count"] / bucket["scored_count"], 12)
        if bucket["scored_count"]
        else None
    )


def score_revealed(frozen: DomainFreeze, revealed: RevealedDomainLabels) -> DomainScore:
    verify_freeze(frozen)
    if revealed.freeze_hash != frozen.freeze_hash or revealed.case_id != frozen.case_id or revealed.track != frozen.track:
        raise ValueError("reveal does not bind to freeze")
    if _hash_payload(revealed.to_dict(), "reveal_hash") != revealed.reveal_hash:
        raise ValueError("reveal hash mismatch")
    label_by_id = {item["claim_id"]: item for item in revealed.labels}
    overall = _empty_bucket()
    by_domain: dict[str, dict[str, Any]] = {}
    by_task: dict[str, dict[str, Any]] = {}
    by_claim: dict[str, dict[str, Any]] = {}
    for claim in frozen.claims:
        label = label_by_id.get(claim.claim_id)
        outcome: Outcome | None = label["outcome"] if label is not None else None
        for bucket in (overall, by_domain.setdefault(claim.domain, _empty_bucket()), by_task.setdefault(claim.task_id, _empty_bucket())):
            _add(bucket, state=claim.state, outcome=outcome)
        by_claim[claim.claim_id] = {
            "domain": claim.domain,
            "task_id": claim.task_id,
            "status": "abstain" if claim.state == "abstain" else outcome or "unlabeled",
        }
    for bucket in [overall, *by_domain.values(), *by_task.values()]:
        _finish(bucket)
    metrics = {
        "overall": overall,
        "by_domain": dict(sorted(by_domain.items())),
        "by_task": dict(sorted(by_task.items())),
        "by_claim": dict(sorted(by_claim.items())),
    }
    unsigned = DomainScore(frozen.case_id, frozen.track, frozen.freeze_hash, revealed.reveal_hash, metrics, "")
    return DomainScore(
        frozen.case_id,
        frozen.track,
        frozen.freeze_hash,
        revealed.reveal_hash,
        metrics,
        canonical_artifact_sha256(unsigned.unsigned_dict()),
    )


def summarize_status(scores: Iterable[DomainScore]) -> dict[str, Any]:
    """兼容旧 score 参数，但孤立 score 永远不能证明完整链或真人资格。"""

    tracks = {
        "prospective": {"qualified_case_count": 0, "score_count": 0},
        "historical": {"qualified_case_count": 0, "score_count": 0},
    }
    for score in scores:
        DomainScore.from_dict(score.to_dict())
        tracks[score.track]["score_count"] += 1
    return {
        "schema_version": STATUS_SCHEMA,
        "status": "not_ready",
        "minimum_prospective_cases": MIN_PROSPECTIVE_CASES,
        "tracks": tracks,
        "production_ready": False,
        "production_switch_permitted": False,
        "failures": ["unverified_artifact_chain", "insufficient_genuine_prospective_cases"],
    }

"""六源三领域 run snapshot 的只读能力覆盖与弃权诊断。

本模块只消费内存中的 :class:`V5RunSnapshot`，不写规则、权重、路由或快照。
registration capability 来自当前十八槽位注册表；runtime coverage 只来自快照审计，
两者始终分账。
"""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Iterable

from engine.v5.domain import V5Claim, V5RunSnapshot, V5_SCHOOLS, V5_RUN_SNAPSHOT_SCHEMA_VERSION
from engine.v5.domain_metadata_integrity import validate_capability_metadata
from engine.v5.domain_slices import build_domain_registry
from engine.v5.domain_slices.contract import DOMAIN_IDS

METRICS_SCHEMA_VERSION = "domain-capability-metrics-v1"
DOMAIN_NAMES = {"career": "事业", "wealth": "财富", "marriage": "婚姻"}
DOMAIN_IDS_BY_NAME = {value: key for key, value in DOMAIN_NAMES.items()}
_STATUSES = {"implemented", "abstain", "unsupported"}


def _rate(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 6) if denominator else 0.0


def _registration_statuses() -> dict[tuple[str, str], str]:
    registry = build_domain_registry()
    return {key: registry.resolve(*key).status for key in registry.keys()}


def _coverage(snapshot: V5RunSnapshot) -> dict[tuple[str, str], dict[str, Any]]:
    raw = snapshot.metadata.get("slice_coverage")
    if not isinstance(raw, list):
        raise ValueError(f"run {snapshot.run_id}: eighteen-slot identity is missing")
    expected = {(school, domain) for school in V5_SCHOOLS for domain in DOMAIN_IDS}
    rows: dict[tuple[str, str], dict[str, Any]] = {}
    for item in raw:
        if not isinstance(item, dict):
            raise ValueError(f"run {snapshot.run_id}: eighteen-slot identity contains a non-object")
        key = (str(item.get("school", "")), str(item.get("domain", "")))
        status = item.get("status")
        audit = item.get("audit")
        if key in rows or status not in _STATUSES or not isinstance(audit, dict):
            raise ValueError(f"run {snapshot.run_id}: eighteen-slot identity or status is invalid")
        rows[key] = item
    if len(raw) != 18 or set(rows) != expected:
        raise ValueError(f"run {snapshot.run_id}: eighteen-slot identity is incomplete")
    return rows


def validate_snapshot(snapshot: V5RunSnapshot) -> None:
    """失败关闭校验统计所需的快照 hash、schema 与十八槽位身份。"""

    if snapshot.snapshot_schema_version != V5_RUN_SNAPSHOT_SCHEMA_VERSION:
        raise ValueError(
            f"run {snapshot.run_id}: unsupported snapshot schema {snapshot.snapshot_schema_version!r}"
        )
    if not snapshot.run_id or not snapshot.case_id:
        raise ValueError("run snapshot identity is incomplete")
    if not snapshot.output_hash_matches():
        raise ValueError(f"run {snapshot.run_id}: output hash mismatch")
    _coverage(snapshot)
    validate_capability_metadata(snapshot.metadata)


def _deduplicate(snapshots: Iterable[V5RunSnapshot]) -> tuple[list[V5RunSnapshot], int]:
    unique: dict[str, V5RunSnapshot] = {}
    hashes: dict[str, str] = {}
    duplicate_count = 0
    for snapshot in snapshots:
        validate_snapshot(snapshot)
        digest = snapshot.hash()
        if snapshot.run_id in unique:
            if hashes[snapshot.run_id] != digest:
                raise ValueError(f"duplicate run_id has conflicting snapshots: {snapshot.run_id}")
            duplicate_count += 1
            continue
        unique[snapshot.run_id] = snapshot
        hashes[snapshot.run_id] = digest
    if not unique:
        raise ValueError("at least one run snapshot is required")
    return [unique[key] for key in sorted(unique)], duplicate_count


def _runtime_status(item: dict[str, Any]) -> str:
    audit = item["audit"]
    if str(audit.get("reason", "")) == "not requested":
        return "not_requested"
    return str(item["status"])


def _claim_task(claim: V5Claim) -> str:
    task = str(claim.metadata.get("task_id", "")).strip()
    return task or "__slot__"


def _evidence_complete(claim: V5Claim) -> bool:
    return bool(claim.evidence) and all(item.source.strip() and item.text.strip() for item in claim.evidence)


def _has_conflict(claims: list[V5Claim]) -> bool:
    stances = {claim.stance for claim in claims if claim.stance != "abstain"}
    return "mixed" in stances or ({"support", "oppose"} <= stances)


def _reason_taxon(reason: str, error_type: str = "") -> str:
    normalized = reason.strip().lower()
    if normalized == "not requested":
        return "not_requested"
    if normalized == "slice unsupported":
        return "unsupported_capability"
    if normalized == "slice execution failed" or error_type.strip():
        return "execution_failure"
    if "rules did not match" in normalized:
        return "rules_not_matched"
    if "explicit abstain placeholder" in normalized:
        return "registered_abstain"
    if not normalized:
        return "unspecified"
    return "other"


def _gate_value(claim: V5Claim) -> tuple[bool, str]:
    """只读任务 4 可能写入的字段；未出现正式字段时明确 unavailable。"""

    if not bool(claim.metadata.get("high_risk", False)):
        return False, "not_applicable"
    gate = claim.metadata.get("high_risk_gate")
    if isinstance(gate, dict):
        status = str(gate.get("status", "")).strip().lower()
        if status:
            return True, status
    status = str(claim.metadata.get("high_risk_gate_status", "")).strip().lower()
    return True, status or "unavailable"


def build_capability_metrics(snapshots: Iterable[V5RunSnapshot]) -> dict[str, Any]:
    """按 school/domain/task 聚合同源、确定性的只读诊断。"""

    runs, duplicate_count = _deduplicate(snapshots)
    registration = _registration_statuses()
    slot_runtime: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    task_claims: dict[tuple[str, str, str], list[V5Claim]] = defaultdict(list)
    task_run_claims: dict[tuple[str, str, str], dict[str, list[V5Claim]]] = defaultdict(lambda: defaultdict(list))
    task_runtime: dict[tuple[str, str, str], Counter[str]] = defaultdict(Counter)
    abstain_reasons: Counter[str] = Counter()

    for snapshot in runs:
        coverage = _coverage(snapshot)
        claims_by_slot: dict[tuple[str, str], list[V5Claim]] = defaultdict(list)
        for claim in snapshot.claims:
            domain_id = DOMAIN_IDS_BY_NAME.get(claim.domain)
            key = (claim.school, domain_id or "")
            if key not in coverage:
                raise ValueError(f"run {snapshot.run_id}: claim does not belong to an eighteen-slot identity")
            claims_by_slot[key].append(claim)
        for key, item in coverage.items():
            runtime = _runtime_status(item)
            slot_runtime[key][runtime] += 1
            slot_claims = claims_by_slot.get(key, [])
            grouped: dict[str, list[V5Claim]] = defaultdict(list)
            for claim in slot_claims:
                grouped[_claim_task(claim)].append(claim)
            if not grouped:
                grouped["__slot__"] = []
            for task, claims in grouped.items():
                task_key = (key[0], key[1], task)
                task_runtime[task_key][runtime] += 1
                task_claims[task_key].extend(claims)
                task_run_claims[task_key][snapshot.run_id].extend(claims)
            audit = item["audit"]
            if runtime in {"abstain", "unsupported", "not_requested"}:
                abstain_reasons[_reason_taxon(str(audit.get("reason", "")), str(audit.get("error_type", "")))] += 1

    slots = []
    for school in V5_SCHOOLS:
        for domain in DOMAIN_IDS:
            key = (school, domain)
            slots.append(
                {
                    "school": school,
                    "domain": domain,
                    "registration_status": registration[key],
                    "runtime_status_counts": dict(sorted(slot_runtime[key].items())),
                }
            )

    tasks = []
    observed_gate_statuses: Counter[str] = Counter()
    for key in sorted(task_runtime):
        school, domain, task = key
        claims = task_claims[key]
        substantive = [claim for claim in claims if claim.stance != "abstain" and task != "__slot__"]
        conflict_run_count = sum(_has_conflict(group) for group in task_run_claims[key].values())
        high_risk = False
        gate_statuses: Counter[str] = Counter()
        for claim in claims:
            is_high_risk, gate_status = _gate_value(claim)
            if is_high_risk:
                high_risk = True
                gate_statuses[gate_status] += 1
                observed_gate_statuses[gate_status] += 1
        if high_risk:
            gate_status = next(iter(gate_statuses)) if len(gate_statuses) == 1 else "mixed"
        else:
            gate_status = "not_applicable"
        tasks.append(
            {
                "school": school,
                "domain": domain,
                "task": task,
                "registration_status": registration[(school, domain)],
                "runtime_status_counts": dict(sorted(task_runtime[key].items())),
                "implemented_count": task_runtime[key]["implemented"],
                "abstain_count": task_runtime[key]["abstain"],
                "unsupported_count": task_runtime[key]["unsupported"],
                "claim_count": len(claims),
                "substantive_claim_count": len(substantive),
                "evidence_completeness_rate": _rate(sum(_evidence_complete(claim) for claim in substantive), len(substantive)),
                "conflict_rate": _rate(conflict_run_count, len(task_run_claims[key])),
                "timing_coverage_rate": _rate(sum(bool(claim.timing_hints) for claim in substantive), len(substantive)),
                "high_risk": {
                    "metadata_present": high_risk,
                    "gate_status": gate_status,
                    "gate_status_counts": dict(sorted(gate_statuses.items())),
                },
            }
        )

    formal_gate_available = bool(observed_gate_statuses) and set(observed_gate_statuses) != {"unavailable"}
    return {
        "schema_version": METRICS_SCHEMA_VERSION,
        "run_count": len(runs),
        "input_count": len(runs) + duplicate_count,
        "deduplicated_run_count": duplicate_count,
        "run_ids": [snapshot.run_id for snapshot in runs],
        "slot_count": len(slots),
        "status_ledger_semantics": {
            "registration_status": "current immutable domain registry capability",
            "runtime_status": "observed slice_coverage status per validated run",
            "strictly_separate": True,
        },
        "slots": slots,
        "tasks": tasks,
        "abstain_reason_taxonomy": [
            {"reason": reason, "count": count} for reason, count in sorted(abstain_reasons.items())
        ],
        "high_risk_gate": {
            "availability": "available" if formal_gate_available else "unavailable",
            "note": (
                "Only existing snapshot metadata is reported."
                if formal_gate_available
                else "Task 4 formal gate metadata is unavailable; high-risk markers are read without inferring a gate result."
            ),
            "status_counts": dict(sorted(observed_gate_statuses.items())),
        },
        "read_only": True,
    }

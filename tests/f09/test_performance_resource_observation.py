from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
from time import perf_counter_ns
import tracemalloc
from typing import Any, Callable

import pytest

import engine.f09.application as application
import engine.f09.artifacts as artifacts
from engine.f09.contracts import ArtifactSetState
from tests.f09.conftest import (
    _bind_canonical_artifact_authority,
    baseline_scenario_bundle,
    materialize_f09_decision_inputs,
)


PHASES = (
    "SOURCE_PREFLIGHT",
    "EVIDENCE",
    "DECISION",
    "TRACE",
    "ARTIFACT",
)
SNAPSHOT_PREFIX = "F09_PERF_RESOURCE_SNAPSHOT="


def _prepared_bundle(root: Path):
    bundle = baseline_scenario_bundle(root.parent)
    bundle = replace(
        bundle,
        request=replace(bundle.request, artifact_root=root),
    )
    decision_inputs = materialize_f09_decision_inputs(bundle)
    return _bind_canonical_artifact_authority(bundle, decision_inputs), decision_inputs


def _run(bundle, decision_inputs):
    return application.run_f09_slice(
        bundle.request,
        gate_inputs=decision_inputs.gate_inputs,
        competition_input=decision_inputs.competition_input,
        root_input=decision_inputs.root_input,
        timing_input=decision_inputs.timing_input,
    )


def _measure_call(
    monkeypatch: pytest.MonkeyPatch,
    *,
    scenario: str,
    bundle,
    decision_inputs,
) -> dict[str, Any]:
    phase_wall_ns: dict[str, int] = {}
    counters = {
        "artifact_atomic_write_calls": 0,
        "observation_persist_calls": 0,
    }
    boundaries: dict[str, int] = {}

    original_evidence = application.build_f09_evidence_package
    original_decision = application.evaluate_f09
    original_trace = application.build_trace
    original_statement_set = application.build_statement_set
    original_projection_validation = application.validate_statement_projection
    original_artifact = application.coordinate_artifact_operation
    original_atomic_write = artifacts._atomic_write_verified
    original_observation_persist = application.persist_phase_observation_log

    def timed_call(phase: str, function: Callable[..., Any], *args, **kwargs):
        started = perf_counter_ns()
        try:
            return function(*args, **kwargs)
        finally:
            phase_wall_ns[phase] = perf_counter_ns() - started

    def evidence_wrapper(*args, **kwargs):
        boundaries["evidence_started"] = perf_counter_ns()
        try:
            return original_evidence(*args, **kwargs)
        finally:
            phase_wall_ns["EVIDENCE"] = perf_counter_ns() - boundaries["evidence_started"]

    def decision_wrapper(*args, **kwargs):
        return timed_call("DECISION", original_decision, *args, **kwargs)

    def trace_wrapper(*args, **kwargs):
        boundaries["trace_started"] = perf_counter_ns()
        return original_trace(*args, **kwargs)

    def statement_set_wrapper(*args, **kwargs):
        return original_statement_set(*args, **kwargs)

    def projection_validation_wrapper(*args, **kwargs):
        try:
            return original_projection_validation(*args, **kwargs)
        finally:
            phase_wall_ns["TRACE"] = perf_counter_ns() - boundaries["trace_started"]

    def artifact_wrapper(*args, **kwargs):
        return timed_call("ARTIFACT", original_artifact, *args, **kwargs)

    def atomic_write_wrapper(*args, **kwargs):
        counters["artifact_atomic_write_calls"] += 1
        return original_atomic_write(*args, **kwargs)

    def observation_persist_wrapper(*args, **kwargs):
        counters["observation_persist_calls"] += 1
        return original_observation_persist(*args, **kwargs)

    with monkeypatch.context() as patcher:
        patcher.setattr(application, "build_f09_evidence_package", evidence_wrapper)
        patcher.setattr(application, "evaluate_f09", decision_wrapper)
        patcher.setattr(application, "build_trace", trace_wrapper)
        patcher.setattr(application, "build_statement_set", statement_set_wrapper)
        patcher.setattr(application, "validate_statement_projection", projection_validation_wrapper)
        patcher.setattr(application, "coordinate_artifact_operation", artifact_wrapper)
        patcher.setattr(artifacts, "_atomic_write_verified", atomic_write_wrapper)
        patcher.setattr(application, "persist_phase_observation_log", observation_persist_wrapper)

        tracemalloc.start()
        total_started = perf_counter_ns()
        try:
            result = _run(bundle, decision_inputs)
            total_wall_ns = perf_counter_ns() - total_started
            _, peak_traced_bytes = tracemalloc.get_traced_memory()
        finally:
            tracemalloc.stop()

    phase_wall_ns["SOURCE_PREFLIGHT"] = boundaries["evidence_started"] - total_started
    phase_wall_ns = {phase: phase_wall_ns[phase] for phase in PHASES}
    unattributed_ns = total_wall_ns - sum(phase_wall_ns.values())
    phase_statuses = {item.phase: item.status for item in result.observations}

    return {
        "scenario": scenario,
        "run_status": "SUCCEEDED" if result.stopped_at is None else "STOPPED",
        "stopped_at": result.stopped_at,
        "artifact_set_state": result.manifest.state.value if result.manifest is not None else None,
        "phase_statuses": phase_statuses,
        "phase_wall_ns": phase_wall_ns,
        "total_wall_ns": total_wall_ns,
        "unattributed_ns": unattributed_ns,
        "peak_traced_bytes": peak_traced_bytes,
        **counters,
    }


def _assert_snapshot_record(record: dict[str, Any]) -> None:
    assert record["run_status"] == "SUCCEEDED"
    assert record["stopped_at"] is None
    assert record["artifact_set_state"] == ArtifactSetState.COMPLETE_VERIFIED.value
    assert tuple(record["phase_statuses"]) == PHASES
    assert all(status == "SUCCEEDED" for status in record["phase_statuses"].values())
    assert tuple(record["phase_wall_ns"]) == PHASES
    numeric_fields = (
        "total_wall_ns",
        "unattributed_ns",
        "peak_traced_bytes",
        "artifact_atomic_write_calls",
        "observation_persist_calls",
    )
    assert all(type(record[field]) is int and record[field] >= 0 for field in numeric_fields)
    assert all(type(value) is int and value >= 0 for value in record["phase_wall_ns"].values())


def test_f09_performance_resource_snapshot(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    cold_bundle, cold_inputs = _prepared_bundle(tmp_path / "cold" / "f09-artifacts")
    cold = _measure_call(
        monkeypatch,
        scenario="cold",
        bundle=cold_bundle,
        decision_inputs=cold_inputs,
    )

    repeat_bundle, repeat_inputs = _prepared_bundle(tmp_path / "repeat" / "f09-artifacts")
    prepared_result = _run(repeat_bundle, repeat_inputs)
    assert prepared_result.stopped_at is None
    assert prepared_result.manifest is not None
    repeated_bundle = replace(
        repeat_bundle,
        request=replace(
            repeat_bundle.request,
            existing_manifest=prepared_result.manifest,
            attempt_id="ATTEMPT-F09-VERTICAL-REPEAT",
        ),
    )
    repeated = _measure_call(
        monkeypatch,
        scenario="repeat",
        bundle=repeated_bundle,
        decision_inputs=repeat_inputs,
    )

    snapshot = {"schema_version": "g10-r3-f09-performance-resource-v1", "scenarios": [cold, repeated]}
    assert [record["scenario"] for record in snapshot["scenarios"]] == ["cold", "repeat"]
    for record in snapshot["scenarios"]:
        _assert_snapshot_record(record)

    print(SNAPSHOT_PREFIX + json.dumps(snapshot, sort_keys=True, separators=(",", ":")))

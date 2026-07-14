from __future__ import annotations

from engine.decision.routing_holdout_artifacts import compare_static_learned_routes


def _row(case: str, school: str, utility: float, *, calibration: float = 0.1) -> dict[str, object]:
    return {
        "case_id": case,
        "task_id": "career.role_change",
        "school_id": school,
        "utility": utility,
        "probability_score": 1.0 - calibration,
        "observed_positive": True,
    }


def test_learned_route_uses_training_school_mean_and_beats_static_when_supported() -> None:
    scores = [
        _row("T-1", "ziping", 0.2), _row("T-1", "ren", 0.8),
        _row("T-2", "ziping", 0.3), _row("T-2", "ren", 0.7),
        _row("H-1", "ziping", 0.1), _row("H-1", "ren", 0.9),
        _row("H-2", "ziping", 0.2), _row("H-2", "ren", 0.8),
    ]

    result = compare_static_learned_routes(
        scores,
        training_case_ids={"T-1", "T-2"},
        holdout_case_ids={"H-1", "H-2"},
        static_school_by_task={"career.role_change": "ziping"},
        minimum_holdout_cases=2,
    )

    assert result.status == "GO"
    assert result.learned_mean_utility > result.static_mean_utility
    assert result.records[0].learned_school == "ren"


def test_learned_route_stops_when_holdout_utility_is_worse() -> None:
    scores = [
        _row("T-1", "ziping", 0.2), _row("T-1", "ren", 0.8),
        _row("H-1", "ziping", 0.9), _row("H-1", "ren", 0.1),
        _row("H-2", "ziping", 0.8), _row("H-2", "ren", 0.2),
    ]

    result = compare_static_learned_routes(
        scores,
        training_case_ids={"T-1"},
        holdout_case_ids={"H-1", "H-2"},
        static_school_by_task={"career.role_change": "ziping"},
        minimum_holdout_cases=2,
    )

    assert result.status == "STOP"
    assert result.learned_mean_utility < result.static_mean_utility

from __future__ import annotations

import json
from pathlib import Path

from engine.decision.real_routing_evaluator import build_training_capability_snapshot


def test_training_snapshot_rewrites_prototypes_and_excludes_holdout(tmp_path: Path) -> None:
    batch = {
        "cases": [
            {"case_id": "T-1", "sex_marker": "乾", "four_pillars": ["甲子", "乙丑", "丙寅", "丁卯"], "solar_datetime": "", "dayun_sequence": ["戊辰"]},
            {"case_id": "H-1", "sex_marker": "坤", "four_pillars": ["戊辰", "己巳", "庚午", "辛未"], "solar_datetime": "", "dayun_sequence": ["壬申"]},
        ]
    }
    scores = [
        {"case_id": "T-1", "school_id": "ziping", "task_id": "career.role_change", "claim_type": "binary_event", "state": "claim", "abstained": False, "knowledge_coverage": True, "chart_prototype_id": "prototype-provisional", "time_horizon": "ten_year", "evidence_completeness_band": "partial", "probability_score": 0.8, "timing_score": None, "ordinal_score": None, "portrait_agreement": None, "utility": 0.65, "observed_positive": True},
        {"case_id": "H-1", "school_id": "ziping", "task_id": "career.role_change", "claim_type": "binary_event", "state": "claim", "abstained": False, "knowledge_coverage": True, "chart_prototype_id": "prototype-provisional", "time_horizon": "ten_year", "evidence_completeness_band": "partial", "probability_score": 0.8, "timing_score": None, "ordinal_score": None, "portrait_agreement": None, "utility": 0.65, "observed_positive": True},
    ]

    snapshot = build_training_capability_snapshot(
        batch=batch,
        score_rows=scores,
        training_case_ids={"T-1"},
        evaluated_at="2026-07-14T00:00:00Z",
    )

    assert snapshot["training_case_ids"] == ["T-1"]
    assert snapshot["posteriors"]
    assert all(row["chart_prototype_id"] != "prototype-provisional" for row in snapshot["posteriors"])
    assert "H-1" not in json.dumps(snapshot)

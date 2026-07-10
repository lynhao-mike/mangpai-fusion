from __future__ import annotations

import json
from pathlib import Path

BASELINE_PATH = Path("tests/r10/fixtures/r6_ziping_career_baseline.json")


def load_r6_baseline() -> dict[str, object]:
    return json.loads(BASELINE_PATH.read_text(encoding="utf-8"))


def test_r6_baseline_is_frozen_and_nonempty() -> None:
    baseline = load_r6_baseline()
    assert baseline["case_id"] == "C-2026-035-乾-戊辰癸亥甲戌庚午"
    assert int(baseline["career_claim_count"]) > 0
    assert int(baseline["career_school_count"]) > 0
    assert int(baseline["career_evidence_count"]) > 0
    assert int(baseline["career_fifteen_layer_count"]) == 15
    assert baseline["required_text_sentinels"]

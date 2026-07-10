from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

BASELINE_PATH = Path("tests/r10/fixtures/r6_ziping_career_baseline.json")


def load_r6_baseline() -> dict[str, object]:
    return json.loads(BASELINE_PATH.read_text(encoding="utf-8"))


def test_r6_baseline_is_frozen_and_nonempty() -> None:
    baseline = load_r6_baseline()
    assert baseline["case_id"] == "C-2026-035-乾-戊辰癸亥甲戌庚午"
    assert int(baseline["career_claim_count"]) == 270
    assert int(baseline["career_school_count"]) == 5
    assert int(baseline["career_evidence_count"]) == 270
    assert int(baseline["career_fifteen_layer_count"]) == 15
    assert baseline["required_text_sentinels"] == ["事业", "依据", "置信度", "应期"]


def test_r6_frozen_gate_rejects_degraded_fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    degraded_path = tmp_path / "r6_ziping_career_baseline.json"
    degraded_path.write_text(
        json.dumps(
            {
                "case_id": "C-2026-035-乾-戊辰癸亥甲戌庚午",
                "career_claim_count": 1,
                "career_school_count": 1,
                "career_evidence_count": 1,
                "career_fifteen_layer_count": 15,
                "required_text_sentinels": ["x"],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(sys.modules[__name__], "BASELINE_PATH", degraded_path)

    with pytest.raises(AssertionError):
        test_r6_baseline_is_frozen_and_nonempty()

from __future__ import annotations

from pathlib import Path

import pytest


CASE_ID = "C-2026-022-坤-癸亥庚申戊寅己未"
INPUT_PATH = Path(f"cases/{CASE_ID}/input.md")
INSUFFICIENT_EVIDENCE_REASON = (
    "G6 evidence gate: case input has four pillars, hidden stems and luck-cycle start, "
    "but no explicit ten-god or hidden-stem ten-god fields; deriving them is forbidden"
)


def _input_text() -> str:
    return INPUT_PATH.read_text(encoding="utf-8")


def test_case_2022_source_lacks_explicit_ten_god_fields_required_by_g6_gate() -> None:
    source = _input_text()

    assert "四柱:" in source
    assert "藏干:" in source
    assert "起运岁:" in source
    assert "起运年:" in source
    assert "十神:" not in source
    assert "藏干十神:" not in source


def test_case_2022_out_of_sample_replay_is_skipped_without_deriving_ten_gods() -> None:
    pytest.skip(INSUFFICIENT_EVIDENCE_REASON)

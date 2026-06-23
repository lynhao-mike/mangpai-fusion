"""tools.v5_prediction_feedback smoke 测试。"""

from __future__ import annotations

import json
from pathlib import Path

from tools.render_report_v6 import render_case
from tools.v5_prediction_feedback import (
    apply_prediction_feedback,
    list_predictions,
)

ROOT = Path(__file__).resolve().parents[2]
CASE_INPUT = ROOT / "cases" / "C-2026-001-乾-庚申戊寅壬子辛丑" / "input.md"


def test_list_predictions_returns_prediction_entries(tmp_path: Path) -> None:
    report_path = tmp_path / "v6-report.md"
    _, json_path = render_case(CASE_INPUT, output_path=report_path)

    predictions = list_predictions("C-2026-001-乾-庚申戊寅壬子辛丑", v5_json_path=json_path)
    assert len(predictions) >= 5

    domains = {p.domain for p in predictions}
    assert {"事业", "财富", "婚姻", "健康", "学业"}.issubset(domains)

    for p in predictions:
        assert p.feedback_state == "pending"
        assert p.prediction_id.startswith("v5pred-")
        assert p.falsifier


def test_apply_prediction_feedback_updates_json(tmp_path: Path) -> None:
    report_path = tmp_path / "v6-report.md"
    _, json_path = render_case(CASE_INPUT, output_path=report_path)

    raw = json.loads(json_path.read_text(encoding="utf-8"))
    first_prediction = raw["prediction_ledger"]["predictions"][0]
    pid = first_prediction["prediction_id"]

    ok = apply_prediction_feedback(
        "C-2026-001-乾-庚申戊寅壬子辛丑",
        pid,
        "hit",
        note="事业命中测试",
        v5_json_path=json_path,
    )
    assert ok is True

    raw_after = json.loads(json_path.read_text(encoding="utf-8"))
    updated = next(
        item for item in raw_after["prediction_ledger"]["predictions"]
        if item["prediction_id"] == pid
    )
    assert updated["feedback_state"] == "hit"
    assert "事业命中测试" in updated.get("calibration_note", "")


def test_apply_prediction_feedback_invalid_prediction_id_returns_false(tmp_path: Path) -> None:
    report_path = tmp_path / "v6-report.md"
    _, json_path = render_case(CASE_INPUT, output_path=report_path)

    ok = apply_prediction_feedback(
        "C-2026-001-乾-庚申戊寅壬子辛丑",
        "v5pred-NONEXISTENT",
        "miss",
        v5_json_path=json_path,
    )
    assert ok is False


def test_apply_prediction_feedback_dry_run_does_not_write(tmp_path: Path) -> None:
    report_path = tmp_path / "v6-report.md"
    _, json_path = render_case(CASE_INPUT, output_path=report_path)

    raw_before = json_path.read_text(encoding="utf-8")
    raw = json.loads(raw_before)
    pid = raw["prediction_ledger"]["predictions"][0]["prediction_id"]

    ok = apply_prediction_feedback(
        "C-2026-001-乾-庚申戊寅壬子辛丑",
        pid,
        "miss",
        dry_run=True,
        v5_json_path=json_path,
    )
    assert ok is True
    assert json_path.read_text(encoding="utf-8") == raw_before

"""render_report_v6 预生产渲染 smoke 测试。"""

from __future__ import annotations

from pathlib import Path

import json

from engine.v5 import V5RunSnapshot
from tools.render_report_v6 import main, render_case, render_cases

ROOT = Path(__file__).resolve().parents[2]
CASE_INPUT = ROOT / "cases" / "C-2026-001-乾-庚申戊寅壬子辛丑" / "input.md"


def test_render_report_v6_generates_report_and_v5_json(tmp_path: Path) -> None:
    report_path = tmp_path / "v6-report.md"

    rendered_report, rendered_json = render_case(CASE_INPUT, output_path=report_path)

    assert rendered_report == report_path
    assert rendered_report.exists()
    assert rendered_json.exists()
    rendered_run_json = rendered_report.with_suffix(".run.json")
    rendered_decision_json = rendered_report.with_suffix(".decision-run.json")
    assert rendered_run_json.exists()
    assert rendered_decision_json.exists()

    report_text = rendered_report.read_text(encoding="utf-8")
    json_text = rendered_json.read_text(encoding="utf-8")

    assert "## 五派裁决与共识融合总论" in report_text
    assert "## 十五层判断摘要" in report_text
    assert "## 主要事件预测账本（prediction-first）" in report_text
    assert "滴天髓规则参与" in report_text
    assert "段建业" in report_text
    assert "杨清娟" in report_text
    assert "{{" not in report_text
    assert "{%" not in report_text

    assert '"schema_version": "5.0.0-five-school-mvp"' in json_text
    assert '"expert_system": "tiaohou_ditiansui"' in json_text
    assert '"selection": "v6_preprod_limited"' in json_text
    assert '"prediction_ledger"' in json_text

    run_snapshot = V5RunSnapshot.from_json(rendered_run_json.read_text(encoding="utf-8"))
    assert run_snapshot.case_id == "C-2026-001-乾-庚申戊寅壬子辛丑"
    assert run_snapshot.output_hash_matches()
    assert run_snapshot.artifact_bindings["v5_json"].endswith(rendered_json.as_posix())
    assert run_snapshot.artifact_bindings["decision_run_json"].endswith(rendered_decision_json.as_posix())
    decision_payload = json.loads(rendered_decision_json.read_text(encoding="utf-8"))
    assert decision_payload["schema_version"] == "decision-run-v1"
    assert decision_payload["case_id"] == "C-2026-001-乾-庚申戊寅壬子辛丑"
    assert decision_payload["feedback_signals"]


def test_render_report_v6_batch_generates_multiple_reports(tmp_path: Path) -> None:
    output_dir = tmp_path / "batch"

    rendered = render_cases([CASE_INPUT, CASE_INPUT], output_dir=output_dir)

    assert len(rendered) == 2
    for report_path, json_path in rendered:
        assert report_path.parent == output_dir
        assert report_path.exists()
        assert json_path.exists()
        run_json_path = report_path.with_suffix(".run.json")
        decision_json_path = report_path.with_suffix(".decision-run.json")
        assert run_json_path.exists()
        assert decision_json_path.exists()
        run_snapshot = V5RunSnapshot.from_json(run_json_path.read_text(encoding="utf-8"))
        assert run_snapshot.output_hash_matches()
        report_text = report_path.read_text(encoding="utf-8")
        assert "## 五派裁决与共识融合总论" in report_text
        assert "## 主要事件预测账本（prediction-first）" in report_text


def test_render_report_v6_cli_prints_run_json_path(tmp_path: Path, capsys) -> None:
    report_path = tmp_path / "cli-report.md"

    code = main([str(CASE_INPUT), "--output", str(report_path)])
    captured = capsys.readouterr().out

    assert code == 0
    assert "[OK] report:" in captured
    assert "[OK] v5 json:" in captured
    assert "[OK] run json:" in captured
    assert "[OK] decision run json:" in captured
    assert report_path.with_suffix(".run.json").exists()
    assert report_path.with_suffix(".decision-run.json").exists()

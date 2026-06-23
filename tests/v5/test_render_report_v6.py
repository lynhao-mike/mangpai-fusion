"""render_report_v6 预生产渲染 smoke 测试。"""

from __future__ import annotations

from pathlib import Path

from tools.render_report_v6 import render_case, render_cases

ROOT = Path(__file__).resolve().parents[2]
CASE_INPUT = ROOT / "cases" / "C-2026-001-乾-庚申戊寅壬子辛丑" / "input.md"


def test_render_report_v6_generates_report_and_v5_json(tmp_path: Path) -> None:
    report_path = tmp_path / "v6-report.md"

    rendered_report, rendered_json = render_case(CASE_INPUT, output_path=report_path)

    assert rendered_report == report_path
    assert rendered_report.exists()
    assert rendered_json.exists()

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


def test_render_report_v6_batch_generates_multiple_reports(tmp_path: Path) -> None:
    output_dir = tmp_path / "batch"

    rendered = render_cases([CASE_INPUT, CASE_INPUT], output_dir=output_dir)

    assert len(rendered) == 2
    for report_path, json_path in rendered:
        assert report_path.parent == output_dir
        assert report_path.exists()
        assert json_path.exists()
        report_text = report_path.read_text(encoding="utf-8")
        assert "## 五派裁决与共识融合总论" in report_text
        assert "## 主要事件预测账本（prediction-first）" in report_text

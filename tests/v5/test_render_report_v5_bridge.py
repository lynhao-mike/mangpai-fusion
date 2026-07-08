from __future__ import annotations

from engine.v5 import run_v5
from tools.output_linter import lint
from tools.render_report import render_from_output


def test_render_from_output_accepts_v5_output(tmp_path) -> None:
    output = run_v5(
        {
            "case_id": "C-TEST-V5-REPORT",
            "pillars": ["甲子", "乙丑", "丙寅", "丁卯"],
            "gender_marker": "乾",
            "year_stem": "甲",
            "year_branch": "子",
            "month_stem": "乙",
            "month_branch": "丑",
            "day_stem": "丙",
            "day_branch": "寅",
            "hour_stem": "丁",
            "hour_branch": "卯",
            "current_dayun": "庚午",
            "start_luck": "2008-03-12",
            "dayun_summary": "庚午运：2024–2033年（18–27岁）",
        }
    )

    report = render_from_output(output, lint_before=False, cases_dir=tmp_path)

    assert "## 五派裁决与共识融合总论" in report
    assert "## 主要事件预测账本（prediction-first）" in report
    assert "C-TEST-V5-REPORT" in report
    assert "{{" not in report

    result = lint(output)
    assert result.passed, result.format()

    md_result = lint(report)
    assert md_result.passed, md_result.format()

    statement_index = tmp_path / output.case_id / "statement_index.json"
    assert statement_index.exists()

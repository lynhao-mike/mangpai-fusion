"""render_report_v6 预生产渲染 smoke 测试。"""

from __future__ import annotations

from pathlib import Path

import json
import shutil

from engine.decision.r10_ziping_career import build_ziping_career_decision_run
from engine.v5 import V5CaseManifest, V5FeedbackAttachment, V5Output, V5RunSnapshot
from engine.v5.preprod import build_chart_from_input
from tools.render_report_v6 import main, render_case, render_cases

ROOT = Path(__file__).resolve().parents[2]
CASE_INPUT = ROOT / "cases" / "C-2026-001-乾-庚申戊寅壬子辛丑" / "input.md"


def _copy_case_input(tmp_path: Path) -> Path:
    case_dir = tmp_path / CASE_INPUT.parent.name
    shutil.copytree(CASE_INPUT.parent, case_dir, ignore=shutil.ignore_patterns("manifest.json"))
    return case_dir / "input.md"

def test_build_chart_from_input_merges_multiple_yaml_blocks() -> None:
    chart = build_chart_from_input(ROOT / "cases" / "C-2026-036-乾-辛巳壬辰甲寅乙丑" / "input.md")

    assert chart["year_stem"] == "辛"
    assert chart["year_branch"] == "巳"
    assert chart["month_stem"] == "壬"
    assert chart["month_branch"] == "辰"
    assert chart["day_stem"] == "甲"
    assert chart["day_branch"] == "寅"
    assert chart["hour_stem"] == "乙"
    assert chart["hour_branch"] == "丑"
    assert chart["pillars"] == {
        "year": "辛巳",
        "month": "壬辰",
        "day": "甲寅",
        "hour": "乙丑",
    }


def test_render_report_v6_includes_marriage_timing_for_c2026036(tmp_path: Path) -> None:
    case_input = ROOT / "cases" / "C-2026-036-乾-辛巳壬辰甲寅乙丑" / "input.md"
    report_path = tmp_path / "c2026036-v6.md"

    rendered_report, _ = render_case(case_input, output_path=report_path)
    report_text = rendered_report.read_text(encoding="utf-8")

    assert "2031 辛亥" in report_text
    assert "首选婚期" in report_text
    assert "车像" not in report_text



def test_render_report_v6_generates_report_and_v5_json(tmp_path: Path) -> None:
    case_input = _copy_case_input(tmp_path)
    report_path = tmp_path / "v6-report.md"

    rendered_report, rendered_json = render_case(case_input, output_path=report_path)

    assert rendered_report == report_path
    assert rendered_report.exists()
    assert rendered_json.exists()
    rendered_run_json = rendered_report.with_suffix(".run.json")
    rendered_decision_json = rendered_report.with_suffix(".decision-run.json")
    rendered_feedback_attachment_json = rendered_report.with_suffix(".feedback-attachment.json")
    assert rendered_run_json.exists()
    assert rendered_decision_json.exists()
    assert rendered_feedback_attachment_json.exists()

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

    assert '"schema_version": "5.1.0-six-source"' in json_text
    assert '"expert_system": "tiaohou_ditiansui"' in json_text
    assert '"selection": "v6_preprod_limited"' in json_text
    assert '"prediction_ledger"' in json_text

    run_snapshot = V5RunSnapshot.from_json(rendered_run_json.read_text(encoding="utf-8"))
    assert run_snapshot.case_id == "C-2026-001-乾-庚申戊寅壬子辛丑"
    assert run_snapshot.output_hash_matches()
    expected_artifacts = {
        "report": rendered_report.as_posix(),
        "v5_json": rendered_json.as_posix(),
        "run_json": rendered_run_json.as_posix(),
        "decision_run_json": rendered_decision_json.as_posix(),
        "feedback_attachment": rendered_feedback_attachment_json.as_posix(),
        "input": case_input.as_posix(),
        "feedback": (case_input.parent / "feedback.md").as_posix(),
    }
    assert run_snapshot.artifact_bindings == expected_artifacts
    manifest_path = case_input.parent / "manifest.json"
    manifest = V5CaseManifest.from_json(manifest_path.read_text(encoding="utf-8"))
    assert manifest.case_id == run_snapshot.case_id
    assert manifest.active_run_id == run_snapshot.run_id
    assert run_snapshot.run_id in manifest.run_ids
    assert manifest.artifact_paths == expected_artifacts
    attachment = V5FeedbackAttachment.from_json(rendered_feedback_attachment_json.read_text(encoding="utf-8"))
    assert attachment.case_id == run_snapshot.case_id
    assert attachment.run_id == run_snapshot.run_id
    assert attachment.feedback_path == (case_input.parent / "feedback.md").as_posix()
    assert attachment.validate_targets(run_snapshot) == []
    decision_payload = json.loads(rendered_decision_json.read_text(encoding="utf-8"))
    assert decision_payload["run_id"] == run_snapshot.run_id
    assert decision_payload["schema_version"] == "decision-run-v1"
    assert decision_payload["case_id"] == "C-2026-001-乾-庚申戊寅壬子辛丑"
    assert decision_payload["feedback_signals"]
    v5_output = V5Output.from_json(rendered_json.read_text(encoding="utf-8"))
    assert run_snapshot.to_output().to_dict() == v5_output.to_dict()
    expected = build_ziping_career_decision_run(
        run_snapshot.to_output(),
        raw_text=case_input.read_text(encoding="utf-8"),
        run_id=run_snapshot.run_id,
    )
    assert expected.to_dict() == decision_payload
    assert expected.validate_trace() == []


def test_render_report_v6_batch_generates_multiple_reports(tmp_path: Path) -> None:
    case_input = _copy_case_input(tmp_path)
    output_dir = tmp_path / "batch"

    rendered = render_cases([case_input, case_input], output_dir=output_dir)

    assert len(rendered) == 2
    for report_path, json_path in rendered:
        assert report_path.parent == output_dir
        assert report_path.exists()
        assert json_path.exists()
        run_json_path = report_path.with_suffix(".run.json")
        decision_json_path = report_path.with_suffix(".decision-run.json")
        feedback_attachment_path = report_path.with_suffix(".feedback-attachment.json")
        assert run_json_path.exists()
        assert decision_json_path.exists()
        assert feedback_attachment_path.exists()
        run_snapshot = V5RunSnapshot.from_json(run_json_path.read_text(encoding="utf-8"))
        assert run_snapshot.output_hash_matches()
        report_text = report_path.read_text(encoding="utf-8")
        assert "## 五派裁决与共识融合总论" in report_text
        assert "## 主要事件预测账本（prediction-first）" in report_text


def test_render_report_v6_cli_prints_run_json_path(tmp_path: Path, capsys) -> None:
    case_input = _copy_case_input(tmp_path)
    report_path = tmp_path / "cli-report.md"

    code = main([str(case_input), "--output", str(report_path)])
    captured = capsys.readouterr().out

    assert code == 0
    assert "[OK] report:" in captured
    assert "[OK] v5 json:" in captured
    assert "[OK] run json:" in captured
    assert "[OK] decision run json:" in captured
    assert "[OK] feedback attachment json:" in captured
    assert report_path.with_suffix(".run.json").exists()
    assert report_path.with_suffix(".decision-run.json").exists()
    assert report_path.with_suffix(".feedback-attachment.json").exists()

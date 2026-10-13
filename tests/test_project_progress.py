from __future__ import annotations

from pathlib import Path

from tools.project_progress import (
    DEFAULT_DASHBOARD,
    DEFAULT_MILESTONES,
    DEFAULT_STATE,
    build_report,
    load_state,
    render_dashboard,
)


ROOT = Path(__file__).resolve().parents[1]


def test_progress_state_is_valid_and_has_explicit_task_completion() -> None:
    state = load_state()
    assert state["project"] == "mangpai-fusion"
    assert state["policy"]["production_readiness_is_separate"] is True
    assert state["stages"]
    for stage in state["stages"]:
        for task in stage["tasks"]:
            assert "completion" in task
            assert 0 <= task["completion"] <= 1


def test_progress_report_keeps_engineering_and_production_separate() -> None:
    report = build_report()
    assert report["overall"]["completion_percent"] > 0
    assert report["runtime"]["production_ready"] is False
    assert report["runtime"]["production_switch_permitted"] is False
    p03 = next(stage for stage in report["stages"] if stage["id"] == "P03")
    p06 = next(stage for stage in report["stages"] if stage["id"] == "P06")
    assert p03["status"] == "COMPLETE"
    assert p03["readiness"].startswith("ENGINEERING_COMPLETE")
    assert p06["readiness"].endswith("COHORT_NOT_READY")


def test_dashboard_and_milestones_are_generated_artifacts() -> None:
    report = build_report()
    assert DEFAULT_STATE.is_file()
    assert DEFAULT_DASHBOARD.is_file()
    assert DEFAULT_MILESTONES.is_file()
    dashboard = DEFAULT_DASHBOARD.read_text(encoding="utf-8")
    assert dashboard == render_dashboard(report)
    assert "production_ready | **false**" in dashboard
    assert "P04" in dashboard
    assert "P06" in dashboard

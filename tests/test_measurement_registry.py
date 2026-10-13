from __future__ import annotations

from tools.measurement_registry import load_registry, load_report, render_markdown


def test_measurement_registry_is_fail_closed_for_unresolved_candidates() -> None:
    registry = load_registry()
    entry = registry["entries"][0]
    assert registry["registry_status"] == "PROPOSAL_ONLY"
    assert entry["mapping_status"] == "UNRESOLVED"
    assert entry["mapping_type"] is None
    assert entry["frozen"] is False
    assert entry["pilot_eligible"] is False


def test_measurement_registry_report_keeps_candidate_indicator_separate() -> None:
    report = load_report()
    entry = report["entries"][0]
    assert entry["candidate_outcome_indicators"] == ["education.academic_achievement"]
    text = render_markdown(report)
    assert "NOT_ASSIGNED" in text
    assert "pilot" in text.lower()

from __future__ import annotations

from engine.decision import decision_run_from_v5
from engine.v5 import V5RunSnapshot, run_v5
from tools.output_linter import lint


def test_v5_output_linter_requires_structure_and_event_stages() -> None:
    payload = {
        "case_id": "C-TEST-V5-LINT",
        "arbitration_results": [
            {"domain": "事业", "stage": "event_realization", "conclusion": "事业事件成立"},
            {"domain": "财富", "stage": "structure_legality", "conclusion": "财富结构成立"},
            {"domain": "财富", "stage": "event_realization", "conclusion": "财富事件成立"},
            {"domain": "婚姻", "stage": "structure_legality", "conclusion": "婚姻结构成立"},
            {"domain": "婚姻", "stage": "event_realization", "conclusion": "婚姻事件成立"},
            {"domain": "健康", "stage": "structure_legality", "conclusion": "健康结构成立"},
            {"domain": "健康", "stage": "event_realization", "conclusion": "健康事件成立"},
            {"domain": "学业", "stage": "structure_legality", "conclusion": "学业结构成立"},
            {"domain": "学业", "stage": "event_realization", "conclusion": "学业事件成立"},
        ],
    }

    result = lint(payload)

    codes = {issue.code for issue in result.issues}
    assert "E-V5-STRUCTURE-STAGE" in codes
    assert "W-V5-STRUCTURE-MISSING" in codes
    assert "E-V5-EVENT-STAGE" not in codes


def test_v5_output_linter_accepts_run_snapshot() -> None:
    output = run_v5({"case_id": "C-TEST-V5-SNAPSHOT-LINT", "pillars": ["甲子", "乙丑", "丙寅", "丁卯"]})
    snapshot = V5RunSnapshot.from_output(output)

    result = lint(snapshot)

    assert result.passed, result.format()


def test_output_linter_accepts_decision_run_payload() -> None:
    output = run_v5({"case_id": "C-TEST-DECISION-LINT", "pillars": ["甲子", "乙丑", "丙寅", "丁卯"]})
    decision_run = decision_run_from_v5(output)

    result = lint(decision_run.to_dict())

    assert result.passed, result.format()


def test_output_linter_rejects_broken_decision_run_trace() -> None:
    output = run_v5({"case_id": "C-TEST-DECISION-LINT-BROKEN", "pillars": ["甲子", "乙丑", "丙寅", "丁卯"]})
    payload = decision_run_from_v5(output).to_dict()
    payload["timing_probabilities"][0]["event_id"] = "missing-event"

    result = lint(payload)

    codes = {issue.code for issue in result.errors}
    assert "E-DR-L5-L4" in codes

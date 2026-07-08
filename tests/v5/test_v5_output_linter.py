from __future__ import annotations

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

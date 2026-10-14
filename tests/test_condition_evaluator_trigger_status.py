from engine.predicates.condition_evaluator import (
    evaluate_trigger,
    trigger_evidence_status,
)


def test_unknown_trigger_is_not_treated_as_satisfied() -> None:
    chart = {"pillars": {"year": "甲子", "month": "乙丑", "day": "丙寅", "hour": "丁卯"}}

    assert trigger_evidence_status("literal_overlap_only") == "insufficient_evidence"
    assert evaluate_trigger("literal_overlap_only", chart) is False


def test_character_overlap_is_not_support() -> None:
    from engine.predicates.condition_evaluator import score_blind_rule

    chart = {"pillars": {"year": "甲子", "month": "乙丑", "day": "丙寅", "hour": "丁卯"}}
    rule = {"conclusion": "甲子年见寅则动", "candidate_score": 0.9}

    assert score_blind_rule(rule, chart) == 0.0


def test_known_trigger_remains_evaluable() -> None:
    chart = {"pillars": {"year": "甲子", "month": "乙丑", "day": "丙寅", "hour": "丁卯"}}

    assert trigger_evidence_status("wuxing_imbalanced") == "evaluable"
    assert isinstance(evaluate_trigger("wuxing_imbalanced", chart), bool)

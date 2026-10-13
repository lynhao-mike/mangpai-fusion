from __future__ import annotations

import inspect
from datetime import datetime

from engine.asof.career_path_classifier import classify_career_path


def test_official_resource_structure_prefers_employment() -> None:
    state = classify_career_path(("庚申", "壬子", "甲子", "癸亥"), [])

    assert state.natal_inclination.employment_inclined is True
    assert state.natal_inclination.entrepreneurship_inclined is False
    assert state.abstain_reason is None
    assert state.reality_status.current == "unknown"


def test_output_wealth_with_peer_prefers_entrepreneurship() -> None:
    state = classify_career_path(("甲寅", "丙午", "甲辰", "戊辰"), [])

    assert state.natal_inclination.employment_inclined is False
    assert state.natal_inclination.entrepreneurship_inclined is True
    assert state.abstain_reason is None


def test_close_scores_force_abstention() -> None:
    state = classify_career_path(("庚申", "壬子", "甲午", "戊辰"), [])

    assert state.abstain_reason == "score_margin_below_threshold"
    assert state.natal_inclination.employment_inclined is True
    assert state.natal_inclination.entrepreneurship_inclined is True


def test_current_official_dayun_suppresses_entrepreneurship_and_abstains_on_conflict() -> None:
    state = classify_career_path(
        ("甲寅", "丙午", "甲辰", "戊辰"),
        [{"ganzhi": "庚申", "start": "2020-01-01", "end": "2029-12-31"}],
        datetime(2025, 6, 1),
    )

    assert state.dayun_context is not None
    assert state.dayun_context.opens_employment is True
    assert state.dayun_context.suppresses_entrepreneurship is True
    assert state.abstain_reason == "mixed_signal"


def test_insufficient_pillars_force_abstention() -> None:
    state = classify_career_path(("甲寅", "", "甲辰", "戊辰"), [])

    assert state.abstain_reason == "insufficient_information"
    assert state.natal_inclination.employment_inclined is False
    assert state.natal_inclination.entrepreneurship_inclined is False


def test_missing_dayun_does_not_force_abstention_when_natal_signal_is_clear() -> None:
    state = classify_career_path(("庚申", "壬子", "甲子", "癸亥"), [])

    assert state.dayun_context is None
    assert state.abstain_reason is None


def test_classifier_has_no_reality_or_feedback_dependency() -> None:
    referenced_names = {name.lower() for name in classify_career_path.__code__.co_names}

    assert "known_facts" not in referenced_names
    assert "occupation" not in referenced_names
    assert "feedback" not in referenced_names
    assert "fankui" not in referenced_names
    assert "known_facts" in (inspect.getdoc(classify_career_path) or "")

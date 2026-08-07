from __future__ import annotations

import inspect
from datetime import datetime

from engine.asof.career_path_classifier_v2 import classify_career_path


def test_rooted_visible_official_resource_chain_prefers_employment() -> None:
    """官杀有根、官印同透并由印承接时，不再被财星数量覆盖。"""
    state = classify_career_path(("庚申", "壬子", "甲子", "癸亥"), [])

    assert state.natal_inclination.employment_inclined is True
    assert state.natal_inclination.entrepreneurship_inclined is False
    assert state.abstain_reason is None
    assert "detector_1:rooted_official_resource_chain" in state.natal_inclination.evidence_refs
    assert "detector_1:visible_official_resource_chain" in state.natal_inclination.evidence_refs
    assert state.reality_status.current == "unknown"


def test_output_wealth_peer_subject_work_chain_prefers_entrepreneurship() -> None:
    """食伤生财连续、有根且比劫/日支主体参与时形成经营闭环。"""
    state = classify_career_path(("甲寅", "丙午", "甲辰", "戊辰"), [])

    assert state.natal_inclination.employment_inclined is False
    assert state.natal_inclination.entrepreneurship_inclined is True
    assert state.abstain_reason is None
    assert "detector_2:usable_output_directly_generates_wealth" in state.natal_inclination.evidence_refs
    assert "detector_2:rooted_continuous_output_wealth_chain" in state.natal_inclination.evidence_refs
    assert "detector_2:peer_or_subject_participation" in state.natal_inclination.evidence_refs


def test_wealth_without_output_chain_cannot_trigger_entrepreneurship() -> None:
    state = classify_career_path(("戊辰", "己丑", "甲子", "戊辰"), [])

    assert state.natal_inclination.entrepreneurship_inclined is False
    assert "detector_2:wealth_only_cap" in state.natal_inclination.evidence_refs


def test_natal_close_score_boundary_abstains() -> None:
    state = classify_career_path(("庚申", "壬子", "甲午", "戊辰"), [])

    assert state.natal_inclination.employment_inclined is True
    assert state.natal_inclination.entrepreneurship_inclined is True
    assert state.abstain_reason == "score_margin_below_threshold"


def test_official_dayun_agrees_with_employment_natal_path() -> None:
    state = classify_career_path(
        ("庚申", "壬子", "甲子", "癸亥"),
        [{"ganzhi": "辛酉", "start": "2020-01-01", "end": "2029-12-31"}],
        datetime(2025, 6, 1),
    )

    assert state.dayun_context is not None
    assert state.dayun_context.opens_employment is True
    assert state.dayun_context.suppresses_entrepreneurship is True
    assert state.abstain_reason is None


def test_output_wealth_dayun_agrees_with_entrepreneurship_natal_path() -> None:
    state = classify_career_path(
        ("甲寅", "丙午", "甲辰", "戊辰"),
        [{"ganzhi": "丙午", "start": "2020-01-01", "end": "2029-12-31"}],
        datetime(2025, 6, 1),
    )

    assert state.dayun_context is not None
    assert state.dayun_context.opens_entrepreneurship is True
    assert state.dayun_context.suppresses_employment is True
    assert state.abstain_reason is None


def test_dayun_direction_opposed_to_natal_advantage_returns_mixed_signal() -> None:
    entrepreneurial_natal = classify_career_path(
        ("甲寅", "丙午", "甲辰", "戊辰"),
        [{"ganzhi": "庚申", "start": "2020-01-01", "end": "2029-12-31"}],
        datetime(2025, 6, 1),
    )
    employment_natal = classify_career_path(
        ("庚申", "壬子", "甲子", "癸亥"),
        [{"ganzhi": "丙午", "start": "2020-01-01", "end": "2029-12-31"}],
        datetime(2025, 6, 1),
    )

    assert entrepreneurial_natal.abstain_reason == "mixed_signal"
    assert employment_natal.abstain_reason == "mixed_signal"


def test_invalid_or_incomplete_input_returns_unknown_state() -> None:
    state = classify_career_path(("甲寅", "", "甲辰", "戊辰"), [])

    assert state.abstain_reason == "insufficient_information"
    assert state.natal_inclination.employment_inclined is False
    assert state.natal_inclination.entrepreneurship_inclined is False
    assert state.reality_status.current == "unknown"


def test_classifier_signature_and_code_have_no_reality_dependency() -> None:
    assert tuple(inspect.signature(classify_career_path).parameters) == (
        "pillars",
        "dayun_sequence",
        "as_of_date",
    )
    referenced_names = {name.lower() for name in classify_career_path.__code__.co_names}
    assert not {"known_facts", "occupation", "feedback", "fankui"} & referenced_names
    assert "known_facts" in (inspect.getdoc(classify_career_path) or "")

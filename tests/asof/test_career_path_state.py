from dataclasses import FrozenInstanceError, fields

import pytest

from engine.asof.career_path_state import (
    CareerPathState,
    DayunCareerContext,
    NatalCareerInclination,
    RealityCareerStatus,
)


def _natal() -> NatalCareerInclination:
    return NatalCareerInclination(
        employment_inclined=True,
        entrepreneurship_inclined=False,
        evidence_refs=("natal:official-seal-chain",),
    )


def _reality(current: str = "employed") -> RealityCareerStatus:
    return RealityCareerStatus(
        current=current,
        verified_events=("event:entered-public-service",),
        transition_history=(),
    )


def test_contracts_are_frozen_and_use_slots() -> None:
    inclination = _natal()

    with pytest.raises(FrozenInstanceError):
        inclination.employment_inclined = False  # type: ignore[misc]

    assert not hasattr(inclination, "__dict__")


def test_mixed_is_a_valid_reality_state() -> None:
    status = RealityCareerStatus(
        current="mixed",
        verified_events=("event:employment", "event:side-business"),
        transition_history=({"from": "employed", "to": "mixed", "year": 2012},),
    )

    assert status.current == "mixed"
    assert status.transition_history[0]["to"] == "mixed"


def test_dayun_context_can_be_absent_when_information_is_unavailable() -> None:
    state = CareerPathState(
        natal_inclination=_natal(),
        dayun_context=None,
        reality_status=_reality(),
        abstain_reason="insufficient_dayun_information",
    )

    assert state.dayun_context is None
    assert state.abstain_reason == "insufficient_dayun_information"


def test_dayun_context_keeps_open_and_suppress_axes_separate() -> None:
    context = DayunCareerContext(
        opens_employment=True,
        opens_entrepreneurship=False,
        suppresses_employment=False,
        suppresses_entrepreneurship=True,
        mechanism="官杀当令且印绶承接，开放组织路径并抑制经营。",
    )

    assert context.opens_employment is True
    assert context.suppresses_entrepreneurship is True
    assert context.opens_entrepreneurship is False


def test_transition_history_is_preserved_without_normalizing_mixed_away() -> None:
    history = (
        {"from": "employed", "to": "entrepreneurial", "window": "2012"},
        {"from": "entrepreneurial", "to": "mixed", "window": "2013"},
    )
    status = RealityCareerStatus(
        current="mixed",
        verified_events=("event:resigned", "event:started-business"),
        transition_history=history,
    )

    assert status.transition_history == history
    assert status.current != "unknown"


def test_career_path_state_has_exactly_four_top_level_layers() -> None:
    expected = {
        "natal_inclination",
        "dayun_context",
        "reality_status",
        "abstain_reason",
    }

    assert {field.name for field in fields(CareerPathState)} == expected


def test_unknown_reality_does_not_erase_natal_inclination() -> None:
    state = CareerPathState(
        natal_inclination=NatalCareerInclination(True, True, ("natal:dual-chain",)),
        dayun_context=None,
        reality_status=RealityCareerStatus("unknown", (), ()),
        abstain_reason="reality_not_verified",
    )

    assert state.reality_status.current == "unknown"
    assert state.natal_inclination.employment_inclined is True
    assert state.natal_inclination.entrepreneurship_inclined is True

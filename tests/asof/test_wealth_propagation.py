from __future__ import annotations

from datetime import date

import pytest

from engine.asof.state_ledger import Persistence
from engine.asof.wealth_propagation import (
    WealthPropagationEdge,
    propagate_career_event_to_wealth,
)


PROMOTION_EDGE = WealthPropagationEdge(
    edge_id="synthetic-promotion-to-income-capacity",
    source_event_type="promotion",
    target_state="稳定收入能力提高",
    required_conditions=("薪酬制度随职级调整",),
    delay_days=30,
    persistence=Persistence.CROSS_DAIYUN,
    falsifiers=("晋升不伴随收入变化",),
    verified=True,
)

ENTREPRENEURSHIP_EDGE = WealthPropagationEdge(
    edge_id="synthetic-entrepreneurship-to-risk-exposure",
    source_event_type="entrepreneurship",
    target_state="收入结构变化与资产风险暴露",
    required_conditions=("经营主体已实际运行",),
    delay_days=0,
    persistence=Persistence.SHORT_TERM,
    falsifiers=("未发生资金投入",),
    verified=True,
    short_term_days=365,
)


def test_at_least_two_explicit_synthetic_edges_are_registered_for_boundary_tests() -> None:
    """合成传播边，非案例 C-2026-028 的真实财富历史。"""
    assert {PROMOTION_EDGE.source_event_type, ENTREPRENEURSHIP_EDGE.source_event_type} == {
        "promotion",
        "entrepreneurship",
    }
    assert PROMOTION_EDGE.target_state == "稳定收入能力提高"
    assert ENTREPRENEURSHIP_EDGE.target_state == "收入结构变化与资产风险暴露"


def test_no_explicit_edge_never_changes_wealth() -> None:
    decision = propagate_career_event_to_wealth(
        event_id="career-1",
        event_type="promotion",
        event_date=date(2022, 1, 1),
        verified_event=True,
        observed_conditions=("薪酬制度随职级调整",),
        edges=(),
    )
    assert decision.changed is False
    assert decision.reason_code == "NO_EXPLICIT_EDGE"
    assert decision.state is None


def test_unmet_condition_never_changes_target_domain() -> None:
    decision = propagate_career_event_to_wealth(
        event_id="career-2",
        event_type="promotion",
        event_date=date(2022, 1, 1),
        verified_event=True,
        observed_conditions=(),
        edges=(PROMOTION_EDGE,),
    )
    assert decision.changed is False
    assert decision.reason_code == "PROPAGATION_CONDITIONS_NOT_MET"
    assert decision.state is None


@pytest.mark.parametrize(
    ("verified_event", "edge_verified", "reason"),
    (
        (False, True, "SOURCE_EVENT_UNVERIFIED"),
        (True, False, "EDGE_UNVERIFIED"),
    ),
)
def test_source_event_and_edge_must_both_be_verified_before_fact_write(
    verified_event: bool,
    edge_verified: bool,
    reason: str,
) -> None:
    edge = WealthPropagationEdge(
        edge_id="synthetic-verification-gate",
        source_event_type="promotion",
        target_state="稳定收入能力提高",
        required_conditions=("薪酬制度随职级调整",),
        delay_days=0,
        persistence=Persistence.PERMANENT,
        falsifiers=(),
        verified=edge_verified,
    )
    decision = propagate_career_event_to_wealth(
        event_id="career-3",
        event_type="promotion",
        event_date=date(2022, 1, 1),
        verified_event=verified_event,
        observed_conditions=("薪酬制度随职级调整",),
        edges=(edge,),
    )
    assert decision.changed is False
    assert decision.reason_code == reason
    assert decision.state is None


def test_active_falsifier_blocks_otherwise_matching_edge() -> None:
    decision = propagate_career_event_to_wealth(
        event_id="career-4",
        event_type="promotion",
        event_date=date(2022, 1, 1),
        verified_event=True,
        observed_conditions=("薪酬制度随职级调整",),
        active_falsifiers=("晋升不伴随收入变化",),
        edges=(PROMOTION_EDGE,),
    )
    assert decision.changed is False
    assert decision.reason_code == "PROPAGATION_FALSIFIED"


def test_verified_explicit_edge_writes_delayed_wealth_fact_state() -> None:
    """合成传播结果，非案例 C-2026-028 的真实财富历史。"""
    decision = propagate_career_event_to_wealth(
        event_id="career-5",
        event_type="promotion",
        event_date=date(2022, 1, 1),
        verified_event=True,
        observed_conditions=("薪酬制度随职级调整",),
        edges=(PROMOTION_EDGE,),
    )
    assert decision.changed is True
    assert decision.reason_code == "WEALTH_STATE_PROPAGATED"
    assert decision.state is not None
    assert decision.state.domain == "wealth"
    assert decision.state.value == "稳定收入能力提高"
    assert decision.state.effective_from == date(2022, 1, 31)
    assert decision.state.verified is True


def test_second_explicit_edge_preserves_short_term_duration() -> None:
    """合成传播结果，非案例 C-2026-028 的真实财富历史。"""
    decision = propagate_career_event_to_wealth(
        event_id="career-6",
        event_type="entrepreneurship",
        event_date=date(2022, 1, 1),
        verified_event=True,
        observed_conditions=("经营主体已实际运行",),
        edges=(ENTREPRENEURSHIP_EDGE,),
    )
    assert decision.state is not None
    assert decision.state.effective_until == date(2023, 1, 1)

"""事业事件到财富状态的显式传播边；无边不传播。"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from engine.asof.reality_track import RealityStateEntry
from engine.asof.state_ledger import Persistence


@dataclass(frozen=True, slots=True)
class WealthPropagationEdge:
    """设计 §11.2 的显式传播边；不是默认领域联动。"""

    edge_id: str
    source_event_type: str
    target_state: str
    required_conditions: tuple[str, ...]
    delay_days: int
    persistence: Persistence
    falsifiers: tuple[str, ...]
    verified: bool
    short_term_days: int | None = None

    def __post_init__(self) -> None:
        if not all((self.edge_id.strip(), self.source_event_type.strip(), self.target_state.strip())):
            raise ValueError("propagation edge requires identity, source event and target state")
        if self.delay_days < 0:
            raise ValueError("propagation delay cannot be negative")
        if self.persistence is Persistence.SHORT_TERM:
            if self.short_term_days is None or self.short_term_days < 1:
                raise ValueError("short-term propagation requires positive duration")
        elif self.short_term_days is not None:
            raise ValueError("short_term_days is only valid for short-term propagation")


@dataclass(frozen=True, slots=True)
class WealthPropagationDecision:
    changed: bool
    reason_code: str
    state: RealityStateEntry | None
    edge_id: str | None


def _effective_until(edge: WealthPropagationEdge, effective_from: date) -> date | None:
    if edge.persistence is Persistence.INSTANT:
        return effective_from
    if edge.persistence is Persistence.SHORT_TERM:
        assert edge.short_term_days is not None
        return effective_from + timedelta(days=edge.short_term_days)
    return None


def propagate_career_event_to_wealth(
    *,
    event_id: str,
    event_type: str,
    event_date: date,
    verified_event: bool,
    observed_conditions: tuple[str, ...],
    active_falsifiers: tuple[str, ...] = (),
    edges: tuple[WealthPropagationEdge, ...] = (),
) -> WealthPropagationDecision:
    """仅让一条匹配且已核验的显式边写入财富事实状态。"""

    matching = tuple(edge for edge in edges if edge.source_event_type == event_type)
    if not matching:
        return WealthPropagationDecision(False, "NO_EXPLICIT_EDGE", None, None)
    if len(matching) > 1:
        return WealthPropagationDecision(False, "AMBIGUOUS_EXPLICIT_EDGES", None, None)

    edge = matching[0]
    observed = set(observed_conditions)
    if not set(edge.required_conditions).issubset(observed):
        return WealthPropagationDecision(False, "PROPAGATION_CONDITIONS_NOT_MET", None, edge.edge_id)
    if set(edge.falsifiers) & set(active_falsifiers):
        return WealthPropagationDecision(False, "PROPAGATION_FALSIFIED", None, edge.edge_id)
    if not verified_event:
        return WealthPropagationDecision(False, "SOURCE_EVENT_UNVERIFIED", None, edge.edge_id)
    if not edge.verified:
        return WealthPropagationDecision(False, "EDGE_UNVERIFIED", None, edge.edge_id)

    effective_from = event_date + timedelta(days=edge.delay_days)
    state = RealityStateEntry(
        state_id=f"wealth:{edge.edge_id}:{event_id}",
        domain="wealth",
        value=edge.target_state,
        source_event_id=event_id,
        effective_from=effective_from,
        effective_until=_effective_until(edge, effective_from),
        verified=True,
    )
    return WealthPropagationDecision(True, "WEALTH_STATE_PROPAGATED", state, edge.edge_id)

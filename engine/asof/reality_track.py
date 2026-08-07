"""独立现实状态轨：上一现实位置 + 已核验事件的有效后果。"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class RealityStateEntry:
    """一个已核验事件留下的现实状态；不包含命理触发强度。"""

    state_id: str
    domain: str
    value: str
    source_event_id: str
    effective_from: date
    effective_until: date | None
    verified: bool

    def __post_init__(self) -> None:
        if not all((self.state_id.strip(), self.domain.strip(), self.value.strip(), self.source_event_id.strip())):
            raise ValueError("reality state requires identity, domain, value and event source")
        if not self.verified:
            raise ValueError("reality track only accepts verified states")
        if self.effective_until is not None and self.effective_until < self.effective_from:
            raise ValueError("reality state validity range is reversed")

    def is_effective_on(self, as_of_date: date) -> bool:
        return self.effective_from <= as_of_date and (
            self.effective_until is None or as_of_date <= self.effective_until
        )


@dataclass(frozen=True, slots=True)
class PathState:
    path_id: str
    status: str
    source_event_id: str

    def __post_init__(self) -> None:
        if self.status not in {"open", "closed", "reduced"}:
            raise ValueError("unsupported reality path status")


@dataclass(frozen=True, slots=True)
class RealityTrack:
    """截止日现实轨；与命理结构轨物理分离。"""

    case_id: str
    as_of_date: date
    active_states: tuple[RealityStateEntry, ...]
    path_states: tuple[PathState, ...]
    verified_event_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if any(not state.verified or not state.is_effective_on(self.as_of_date) for state in self.active_states):
            raise ValueError("reality track contains unverified or ineffective state")
        event_ids = set(self.verified_event_ids)
        if any(state.source_event_id not in event_ids for state in self.active_states):
            raise ValueError("every reality state must reference a verified event")
        if any(path.source_event_id not in event_ids for path in self.path_states):
            raise ValueError("every path change must reference a verified event")


def build_reality_track(
    *,
    case_id: str,
    as_of_date: date,
    states: tuple[RealityStateEntry, ...],
    path_states: tuple[PathState, ...] = (),
) -> RealityTrack:
    """过滤截止日有效的已核验状态，不读取任何命理结构对象。"""

    eligible = tuple(state for state in states if state.verified and state.is_effective_on(as_of_date))
    eligible_event_ids = tuple(dict.fromkeys(state.source_event_id for state in eligible))
    eligible_paths = tuple(path for path in path_states if path.source_event_id in set(eligible_event_ids))
    return RealityTrack(case_id, as_of_date, eligible, eligible_paths, eligible_event_ids)

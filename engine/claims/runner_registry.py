"""任务级 Claim runner 只读注册表。"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from types import MappingProxyType

from engine.claims.domain import Claim
from engine.decision.models import ChartFactLedger
from engine.evaluation.models import BlindTask
from engine.features import ChartFeatureVector
from engine.v5.duan_runner import generate_claims as generate_duan_claims
from engine.v5.ren_runner import generate_claims as generate_ren_claims
from engine.v5.ziping_runner import generate_claims as generate_ziping_claims

ClaimGenerator = Callable[[ChartFactLedger, ChartFeatureVector, BlindTask], list[Claim]]
RunnerKey = tuple[str, str]
Registration = tuple[str, str, ClaimGenerator]


class RunnerRegistry:
    """构造后不可变的 ``(school_id, task_id)`` runner 解析表。"""

    __slots__ = ("_runners",)

    def __init__(
        self,
        registrations: Mapping[RunnerKey, ClaimGenerator] | Iterable[Registration],
    ) -> None:
        runners: dict[RunnerKey, ClaimGenerator] = {}
        items = (
            ((school_id, task_id, generator) for (school_id, task_id), generator in registrations.items())
            if isinstance(registrations, Mapping)
            else registrations
        )
        for school_id, task_id, generator in items:
            key = (school_id, task_id)
            if key in runners:
                raise ValueError(f"duplicate runner registration: {school_id}/{task_id}")
            runners[key] = generator
        self._runners = MappingProxyType(runners)

    def resolve(self, school_id: str, task_id: str) -> ClaimGenerator | None:
        """精确解析任务 runner；未知或未覆盖任务返回 ``None``。"""
        return self._runners.get((school_id, task_id))


DEFAULT_RUNNER_REGISTRY = RunnerRegistry(
    [
        ("ziping", "structure.overview", generate_ziping_claims),
        ("ziping", "marriage.late_marriage", generate_ziping_claims),
        ("ziping", "career.role_change", generate_ziping_claims),
        ("ren", "career.change_window", generate_ren_claims),
        ("ren", "career.role_change", generate_ren_claims),
        ("ren", "marriage.event_window", generate_ren_claims),
        ("ren", "wealth.major_loss_window", generate_ren_claims),
        ("ren", "health.event_window", generate_ren_claims),
        ("duan", "career.role_change", generate_duan_claims),
        ("duan", "career.path_type", generate_duan_claims),
        ("duan", "wealth.debt", generate_duan_claims),
        ("duan", "marriage.divorce_or_remarriage", generate_duan_claims),
    ]
)

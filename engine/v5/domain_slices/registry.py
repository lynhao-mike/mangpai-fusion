"""不可变的六源三领域切片注册表。"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from types import MappingProxyType

from engine.v5.domain import V5_SCHOOLS, V5School
from engine.v5.domain_slices.contract import DOMAIN_IDS, DomainAnalysisContext, DomainId, SliceResult, SliceStatus

SliceGenerator = Callable[[DomainAnalysisContext], SliceResult]


@dataclass(frozen=True, slots=True)
class SliceRegistration:
    school: V5School
    domain: DomainId
    status: SliceStatus
    generator: SliceGenerator | None = None

    def __post_init__(self) -> None:
        if self.school not in V5_SCHOOLS:
            raise ValueError(f"unknown school: {self.school}")
        if self.domain not in DOMAIN_IDS:
            raise ValueError(f"unknown domain: {self.domain}")
        if self.status == "implemented" and self.generator is None:
            raise ValueError("implemented slice requires a generator")


class DomainSliceRegistry:
    """构造后不可变，并强制六源乘三领域完整覆盖。"""

    __slots__ = ("_registrations",)

    def __init__(self, registrations: Iterable[SliceRegistration]) -> None:
        values: dict[tuple[str, str], SliceRegistration] = {}
        for registration in registrations:
            key = (registration.school, registration.domain)
            if key in values:
                raise ValueError(f"duplicate slice registration: {registration.school}/{registration.domain}")
            values[key] = registration
        expected = {(school, domain) for school in V5_SCHOOLS for domain in DOMAIN_IDS}
        missing = expected - set(values)
        extra = set(values) - expected
        if missing or extra:
            raise ValueError(f"missing or extra slice registrations: missing={sorted(missing)}, extra={sorted(extra)}")
        ordered = {(school, domain): values[(school, domain)] for school in V5_SCHOOLS for domain in DOMAIN_IDS}
        self._registrations = MappingProxyType(ordered)

    def __len__(self) -> int:
        return len(self._registrations)

    def keys(self) -> tuple[tuple[str, str], ...]:
        return tuple(self._registrations)

    def resolve(self, school: str, domain: str) -> SliceRegistration:
        try:
            return self._registrations[(school, domain)]
        except KeyError as exc:
            raise KeyError(f"unknown slice: {school}/{domain}") from exc


def build_abstain_registry() -> DomainSliceRegistry:
    """P1 骨架：创建十八个显式 abstain 槽位。"""

    return DomainSliceRegistry(
        SliceRegistration(school=school, domain=domain, status="abstain")
        for school in V5_SCHOOLS
        for domain in DOMAIN_IDS
    )

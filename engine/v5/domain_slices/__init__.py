"""六源三领域分析切片公共入口。"""

from engine.v5.domain import V5_SCHOOLS
from engine.v5.domain_slices.career import CAREER_GENERATORS
from engine.v5.domain_slices.contract import (
    DOMAIN_IDS,
    DomainAnalysisContext,
    DomainAnalysisRequest,
    SliceAudit,
    SliceResult,
)
from engine.v5.domain_slices.marriage import MARRIAGE_GENERATORS
from engine.v5.domain_slices.registry import (
    DomainSliceRegistry,
    SliceRegistration,
    build_abstain_registry,
)
from engine.v5.domain_slices.wealth import WEALTH_GENERATORS


def build_domain_registry() -> DomainSliceRegistry:
    """构建六源三领域完整能力矩阵；无可靠能力的槽位显式 unsupported。"""

    registrations: list[SliceRegistration] = []
    generators = {
        "career": CAREER_GENERATORS,
        "wealth": WEALTH_GENERATORS,
        "marriage": MARRIAGE_GENERATORS,
    }
    for school in V5_SCHOOLS:
        for domain in DOMAIN_IDS:
            generator = generators[domain].get(school)
            registrations.append(
                SliceRegistration(
                    school=school,
                    domain=domain,
                    status="implemented" if generator is not None else "unsupported",
                    generator=generator,
                )
            )
    return DomainSliceRegistry(registrations)


__all__ = [
    "DOMAIN_IDS",
    "DomainAnalysisContext",
    "DomainAnalysisRequest",
    "DomainSliceRegistry",
    "SliceAudit",
    "SliceResult",
    "build_abstain_registry",
    "build_domain_registry",
]

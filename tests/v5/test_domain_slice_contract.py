"""六源三领域切片基础契约测试。"""

from __future__ import annotations

from datetime import date, datetime

import pytest

from engine.v5.domain_slices.contract import (
    DOMAIN_IDS,
    DomainAnalysisContext,
    DomainAnalysisRequest,
    SliceAudit,
    SliceResult,
)
from engine.v5.domain_slices.registry import DomainSliceRegistry, build_abstain_registry
from engine.v5.domain import V5_SCHOOLS


def _request(**overrides: object) -> DomainAnalysisRequest:
    values: dict[str, object] = {
        "gender": "乾",
        "birth_datetime": datetime(1990, 1, 1, 12, 30),
        "as_of_date": date(2026, 7, 31),
        "domains": DOMAIN_IDS,
        "output_dir": "reports/domain-analysis",
    }
    values.update(overrides)
    return DomainAnalysisRequest(**values)  # type: ignore[arg-type]


def test_request_normalizes_domains_without_losing_caller_order() -> None:
    request = _request(domains=("wealth", "career", "wealth"))

    assert request.domains == ("wealth", "career")


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("gender", "男"),
        ("domains", ()),
        ("domains", ("health",)),
        ("birth_datetime", datetime(1990, 1, 1, tzinfo=__import__("datetime").timezone.utc)),
        ("output_dir", ""),
    ],
)
def test_request_rejects_invalid_input(field: str, value: object) -> None:
    with pytest.raises(ValueError):
        _request(**{field: value})


def test_context_round_trip_preserves_paipan_and_time_scope() -> None:
    context = DomainAnalysisContext(
        request=_request(),
        case_id="DA-TEST",
        pillars=("庚午", "戊子", "丙寅", "甲午"),
        dayun=({"ganzhi": "甲申", "start_year": 2020}, {"ganzhi": "乙酉", "start_year": 2030}),
        current_dayun={"ganzhi": "甲申", "start_year": 2020, "end_year": 2029},
        future_years=((2026, "丙午"), (2027, "丁未"), (2028, "戊申")),
        calculator="lunar-python",
    )

    assert DomainAnalysisContext.from_dict(context.to_dict()) == context


def test_abstain_registry_has_exactly_eighteen_immutable_slots() -> None:
    registry = build_abstain_registry()

    assert len(registry) == len(V5_SCHOOLS) * len(DOMAIN_IDS) == 18
    assert registry.keys() == tuple((school, domain) for school in V5_SCHOOLS for domain in DOMAIN_IDS)
    assert all(registry.resolve(*key).status == "abstain" for key in registry.keys())


def test_registry_rejects_duplicate_or_incomplete_slots() -> None:
    abstain = build_abstain_registry()
    first = abstain.resolve("ziping", "career")

    with pytest.raises(ValueError, match="duplicate"):
        DomainSliceRegistry([first, first])
    with pytest.raises(ValueError, match="missing"):
        DomainSliceRegistry([first])


def test_slice_result_round_trip_keeps_audit_and_explicit_abstain() -> None:
    result = SliceResult(
        school="ren_fuhong",
        domain="career",
        status="abstain",
        claims=(),
        audit=SliceAudit(reason="timing evidence insufficient"),
    )

    assert SliceResult.from_dict(result.to_dict()) == result

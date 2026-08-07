"""从已校正出生时间构建六源三领域分析上下文。"""

from __future__ import annotations

from engine.asof.birth_to_bazi import calc_bazi
from engine.predicates.cycles import liunian_ganzhi
from engine.v5.domain_slices.contract import DomainAnalysisContext, DomainAnalysisRequest


def _current_dayun(dayun: tuple[dict[str, int | str], ...], year: int) -> dict[str, int | str]:
    ordered = sorted(dayun, key=lambda item: int(item["start_year"]))
    for index, item in enumerate(ordered):
        start_year = int(item["start_year"])
        next_start = int(ordered[index + 1]["start_year"]) if index + 1 < len(ordered) else start_year + 10
        if start_year <= year < next_start:
            return {"ganzhi": str(item["ganzhi"]), "start_year": start_year, "end_year": next_start - 1}
    raise ValueError(f"current dayun cannot be determined for {year}")


def build_analysis_context(request: DomainAnalysisRequest) -> DomainAnalysisContext:
    """调用现有排盘器并冻结当前大运与未来三个公历流年。"""

    result = calc_bazi(request.birth_datetime, "M" if request.gender == "乾" else "F")
    current_dayun = _current_dayun(result.dayun, request.as_of_date.year)
    future_years = tuple(
        (year, str(liunian_ganzhi(year)))
        for year in range(request.as_of_date.year, request.as_of_date.year + 3)
    )
    pillars_text = "".join(result.pillars)
    case_id = request.case_id or f"DA-{request.gender}-{pillars_text}-{request.birth_datetime:%Y%m%d%H%M}"
    return DomainAnalysisContext(
        request=request,
        case_id=case_id,
        pillars=result.pillars,
        dayun=result.dayun,
        current_dayun=current_dayun,
        future_years=future_years,
        calculator=result.calculator,
    )

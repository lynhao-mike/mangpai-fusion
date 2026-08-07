"""tools/as_of_freeze_preflight.py 的真实案例测试。

使用 tests/fixtures/cases.py 注册的真实历史案例 C-2026-001，验证年度轨迹被转换
为独立预览对象并完整分层；测试不读取该案 feedback.md，也不把结构强度当成应期铁断。
"""
from __future__ import annotations

from engine.asof.event_candidate import AnnualInteractionTrace
from tests.fixtures.cases import load_case
from tools.as_of_freeze_preflight import YearTriggerSignal, run_freeze_preflight


def test_real_case_preflight_partitions_all_scanned_years() -> None:
    parsed = load_case("C-2026-001-乾-庚申戊寅壬子辛丑")

    result = run_freeze_preflight(parsed, as_of_year=2026)

    assert result.total_years_scanned > 0
    all_signals = (
        result.high_trigger_years
        + result.medium_trigger_years
        + result.low_trigger_years
    )
    assert len(all_signals) == result.total_years_scanned
    assert result.note.strip()
    assert "结构" in result.note or "信号" in result.note


def test_preflight_uses_independent_view_objects_sorted_within_tiers() -> None:
    parsed = load_case("C-2026-001-乾-庚申戊寅壬子辛丑")

    result = run_freeze_preflight(parsed, as_of_year=2026)

    tiers = (
        result.high_trigger_years,
        result.medium_trigger_years,
        result.low_trigger_years,
    )
    for tier in tiers:
        assert [signal.year for signal in tier] == sorted(signal.year for signal in tier)
        assert all(isinstance(signal, YearTriggerSignal) for signal in tier)
        assert all(not isinstance(signal, AnnualInteractionTrace) for signal in tier)

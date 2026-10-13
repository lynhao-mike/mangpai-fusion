"""as-of 方法论差异评分工具的真实冻结案例测试。"""
from __future__ import annotations

from pathlib import Path

from tools.as_of_methodology_diff import (
    build_methodology_diff_report,
    compute_freeze_metrics,
)

OLD_FREEZE_PATHS = (
    Path("cases/C-2026-RF000894-乾-壬戌己酉庚子戊子/asof-blind-freeze.json"),
    Path("cases/C-2026-RF000900-乾-戊寅乙卯丙寅戊子/asof-blind-freeze.json"),
    Path("cases/C-2026-RF000868-乾-壬申戊申庚辰丁亥/asof-blind-freeze.json"),
)
NEW_RF000861_FREEZE_PATH = Path(
    "cases/C-2026-RF000861-乾-癸酉甲寅庚午乙酉/asof-blind-freeze.json"
)


def test_rf000861_satisfies_new_methodology_constraints() -> None:
    metrics = compute_freeze_metrics(NEW_RF000861_FREEZE_PATH, methodology="new")

    assert metrics.case_id == "C-2026-RF000861"
    assert metrics.methodology == "new"
    assert metrics.freeze_path == str(NEW_RF000861_FREEZE_PATH)
    assert metrics.center_or_count == 0
    assert metrics.max_event_window_months <= 14.0
    assert metrics.has_incomplete_realization_guard is True


def test_new_methodology_is_not_worse_than_old_real_cases() -> None:
    report = build_methodology_diff_report(
        OLD_FREEZE_PATHS,
        (NEW_RF000861_FREEZE_PATH,),
    )

    assert len(report.old_cases) == 3
    assert len(report.new_cases) == 1
    assert report.new_avg_or_count <= report.old_avg_or_count
    assert report.new_avg_window_months <= report.old_avg_window_months
    assert report.new_guard_rate >= report.old_guard_rate
    assert report.summary

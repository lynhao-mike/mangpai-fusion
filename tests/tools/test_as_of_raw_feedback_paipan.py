from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from tools.as_of_current_state_scanner import analyze_feedback_current_state
from tools.as_of_raw_feedback_paipan import (
    choose_birth_datetime,
    is_late_zi_hour_boundary,
    normalize_birth_datetime,
    render_feedback,
    select_records,
)


def _record(**overrides: object) -> dict[str, object]:
    record: dict[str, object] = {
        "raw_id": "RF-2026-000001",
        "quality_grade": "A",
        "calendar_type": "solar",
        "birth_datetime_raw": "1990-11-29 06:20 分",
        "true_solar_time_raw": "",
        "gender": "男",
        "qian_kun": "乾",
        "events": [{"year": 2024, "text": "目前在职，收入稳定", "domains": ["occupation"]}],
        "quality_flags": [],
        "duplicate_key": "unique-1",
        "bazi_raw": "",
    }
    record.update(overrides)
    return record


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("1993 年 6 月 1 日 16:50", datetime(1993, 6, 1, 16, 50)),
        ("1991-02-08 16 点 20 分", datetime(1991, 2, 8, 16, 20)),
        ("1986 年 1 月 23 日 22：30", datetime(1986, 1, 23, 22, 30)),
        ("1981.4.11，凌晨 1:00", datetime(1981, 4, 11, 1, 0)),
        ("2000.11.04 早上 6 点 35", datetime(2000, 11, 4, 6, 35)),
        ("2000-01-01 24:00", datetime(2000, 1, 2, 0, 0)),
    ],
)
def test_normalize_birth_datetime_accepts_observed_formats(raw: str, expected: datetime) -> None:
    assert normalize_birth_datetime(raw) == expected


def test_normalize_birth_datetime_rejects_date_without_time() -> None:
    with pytest.raises(ValueError, match="时辰"):
        normalize_birth_datetime("1996.3.6")


def test_choose_birth_datetime_prefers_true_solar_time() -> None:
    chosen, source = choose_birth_datetime(
        _record(
            birth_datetime_raw="1990-01-01 12:00",
            true_solar_time_raw="1990-01-01 11:42:00",
        )
    )

    assert chosen == datetime(1990, 1, 1, 11, 42)
    assert source == "true_solar_time_raw"


def test_select_records_applies_filters_deduplicates_and_prioritizes_bazi() -> None:
    records = [
        _record(raw_id="ordinary", duplicate_key="one"),
        _record(raw_id="with-bazi", duplicate_key="two", bazi_raw="庚午丁亥戊戌乙卯"),
        _record(raw_id="duplicate", duplicate_key="one"),
        _record(raw_id="lunar", duplicate_key="three", calendar_type="lunar"),
        _record(raw_id="unsafe", duplicate_key="four", quality_flags=["abnormal_birth_date"]),
    ]

    selected = select_records(records, limit=20)

    assert [record["raw_id"] for record in selected] == ["with-bazi", "ordinary"]


def test_select_records_excludes_raw_ids_already_present_in_cases_root() -> None:
    records = [
        _record(raw_id="RF-2026-000001", duplicate_key="one"),
        _record(raw_id="RF-2026-000002", duplicate_key="two"),
    ]

    selected = select_records(records, limit=20, excluded_raw_ids={"RF-2026-000001"})

    assert [record["raw_id"] for record in selected] == ["RF-2026-000002"]


def test_render_feedback_produces_scannable_current_state_table(tmp_path: Path) -> None:
    text = render_feedback(_record(), "C-2026-RF000001-乾-庚午丁亥戊戌乙卯")
    path = tmp_path / "feedback.md"
    path.write_text(text, encoding="utf-8")

    signal = analyze_feedback_current_state(
        text,
        case_id="C-2026-RF000001-乾-庚午丁亥戊戌乙卯",
        feedback_path=str(path),
    )

    assert "| 2024 |" in text
    assert signal.likely_has_current_state is True


# ---------------------------------------------------------------------------
# 晚子时（23:00-23:59）边界过滤逻辑
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("hour", "expected"),
    [
        (22, False),
        (23, True),   # 23:00 是边界
        (0, False),
        (1, False),
    ],
)
def test_is_late_zi_hour_boundary_by_hour(hour: int, expected: bool) -> None:
    dt = datetime(2000, 1, 1, hour, 0, 0)
    assert is_late_zi_hour_boundary(dt) is expected


def test_is_late_zi_hour_boundary_23_59() -> None:
    """23:59 仍属于晚子时边界区间。"""
    dt = datetime(2000, 1, 1, 23, 59, 59)
    assert is_late_zi_hour_boundary(dt) is True


def test_select_records_excludes_late_zi_hour_by_default() -> None:
    """默认启用排除时，23:00-23:59出生的记录应被跳过，不进入选集。"""
    records = [
        _record(raw_id="normal", duplicate_key="a", birth_datetime_raw="2000-01-01 12:00"),
        _record(raw_id="boundary", duplicate_key="b", birth_datetime_raw="2000-01-01 23:10"),
    ]
    selected = select_records(records, limit=20)
    assert [r["raw_id"] for r in selected] == ["normal"]


def test_select_records_exclude_late_zi_hour_captures_skipped_ids() -> None:
    """skipped_late_zi_hour 列表应收集被排除的 raw_id。"""
    records = [
        _record(raw_id="normal", duplicate_key="a", birth_datetime_raw="2000-01-01 12:00"),
        _record(raw_id="boundary", duplicate_key="b", birth_datetime_raw="2002-11-24 23:10"),
    ]
    skipped: list[str] = []
    selected = select_records(records, limit=20, skipped_late_zi_hour=skipped)
    assert [r["raw_id"] for r in selected] == ["normal"]
    assert skipped == ["boundary"]


def test_select_records_allow_late_zi_hour_when_flag_off() -> None:
    """传入 exclude_late_zi_hour=False 时，23:00-23:59出生记录应被纳入。"""
    records = [
        _record(raw_id="boundary", duplicate_key="a", birth_datetime_raw="2000-01-01 23:10"),
    ]
    selected = select_records(records, limit=20, exclude_late_zi_hour=False)
    assert [r["raw_id"] for r in selected] == ["boundary"]


def test_select_records_late_zi_hour_does_not_affect_skipped_when_disabled() -> None:
    """exclude_late_zi_hour=False 时，skipped_late_zi_hour 列表不应被写入。"""
    records = [
        _record(raw_id="boundary", duplicate_key="a", birth_datetime_raw="2000-01-01 23:10"),
    ]
    skipped: list[str] = []
    select_records(records, limit=20, exclude_late_zi_hour=False, skipped_late_zi_hour=skipped)
    assert skipped == []

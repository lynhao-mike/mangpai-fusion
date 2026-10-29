"""T-168 · 应期事件年份审计的确定性单测。

只测 ``tools/timing_event_year_audit.py`` 的纯函数与聚合口径：
年份变体识别（``2008 年`` / ``08 年`` / ``二〇〇八 年`` / 区间）、四桶可加、
剔除名单可复现、只读不改输入。不重写审计产物，不需要 engine。
"""
from __future__ import annotations

import json
from hashlib import sha256

import pytest

from tools import timing_event_year_audit as audit


@pytest.fixture(scope="module")
def payload() -> dict:
    return audit.run_audit()


def _years(text: str, birth_year: int = 1980) -> list[int]:
    refs = audit.extract_year_refs(text, birth_year)
    return sorted({year for ref in refs for year in ref["years"]})


# ── 年份变体 ────────────────────────────────────────────────────────────────


def test_three_year_variants_are_equivalent() -> None:
    """卡上点名的三种写法必须识别成同一年。"""
    assert _years("2008 年结婚") == [2008]
    assert _years("08 年结婚") == [2008]
    assert _years("二〇〇八 年结婚") == [2008]
    assert _years("二零零八年结婚") == [2008]


def test_variant_kind_is_reported() -> None:
    kinds = {
        text: [ref["kind"] for ref in audit.extract_year_refs(text, 1980)]
        for text in ("2008 年", "08 年", "二〇〇八 年")
    }
    assert kinds["2008 年"] == ["y4"]
    assert kinds["08 年"] == ["y2"]
    assert kinds["二〇〇八 年"] == ["cn4"]


def test_ranges_expand_to_full_year_sets() -> None:
    assert _years("2008-2012 年") == [2008, 2009, 2010, 2011, 2012]
    assert _years("08-12 年极顺利") == [2008, 2009, 2010, 2011, 2012]
    assert _years("14.15 年成绩很好") == [2014, 2015]
    assert _years("20～23 年，诸事不顺") == [2020, 2021, 2022, 2023]
    assert _years("2013-15 年左右有抑郁症") == [2013, 2014, 2015]


def test_two_digit_year_uses_lifetime_century() -> None:
    assert _years("93 年毕业", birth_year=1974) == [1993]
    assert _years("24 年结的婚", birth_year=1997) == [2024]


def test_glued_year_after_number() -> None:
    """原文有「9852020 年」「2112014 年」这种粘连写法。"""
    assert _years("考研上岸 9852020 年: 吉", birth_year=1997) == [2020]
    assert _years("高考顺利 2112014 年: 凶", birth_year=1997) == [2014]


# ── 不该当年份的数字 ────────────────────────────────────────────────────────


def test_duration_and_money_are_not_years() -> None:
    assert _years("和拍拖 12 年的女友结婚") == []
    assert _years("未来10 年 下一部大运") == []
    assert _years("加上老宅目前 2000 多万") == []


def test_plain_two_digit_year_still_detected() -> None:
    assert _years("10 年工资有提升") == [2010]
    assert _years("从 19 年开始欠债") == [2019]


# ── 四桶 ────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("year", "text", "bucket"),
    [
        (2008, "2008 年结婚", "match"),
        (2008, "2008 年结婚，2016 年离婚", "multi_year"),
        (2000, "2017 年结婚", "contradiction"),
        (2000, "这年结婚了", "no_year_in_text"),
        ("2000", "2017 年结婚", "other"),
    ],
)
def test_bucket_classification(year: object, text: str, bucket: str) -> None:
    assert audit.classify_event(year, text, 1980)["bucket"] == bucket


def test_four_buckets_add_up(payload: dict) -> None:
    counts = payload["counts"]
    assert counts["cases"] == 382
    assert counts["events"] == 547
    assert sum(counts["events_by_bucket"].values()) == counts["events"]
    assert sum(counts["cases_by_bucket"].values()) == counts["cases"]
    assert counts["events_by_bucket"]["other"] == 0
    assert counts["cases_by_bucket"]["other"] == 0
    for bucket in audit.BUCKETS:
        assert bucket in counts["events_by_bucket"]


def test_every_case_bucket_is_known(payload: dict) -> None:
    assert len(payload["cases"]) == 382
    for row in payload["cases"]:
        assert row["bucket"] in audit.BUCKETS
        for bucket in row["event_buckets"]:
            assert bucket in audit.BUCKETS


# ── 婚姻年份冲突 ────────────────────────────────────────────────────────────


def test_marriage_years_need_a_marriage_word() -> None:
    refs = audit.extract_year_refs("2015 年结婚，2016 年生子", 1980)
    assert audit.marriage_years_in("2015 年结婚，2016 年生子", 1980, refs) == [2015]


def test_marriage_conflict_flags_wrong_label_year() -> None:
    case = {"case_id": "T", "birth_year": 1980}
    text = "工作不顺利，2015 年结婚，2016 年生子"

    wrong = audit._event_row(case, 0, {"year": 2018, "text": text}, None)
    assert wrong["marriage_conflict"] is True
    assert wrong["marriage_years"] == [2015]

    right = audit._event_row(case, 0, {"year": 2015, "text": text}, None)
    assert right["marriage_conflict"] is False


# ── 原文依据（provenance）──────────────────────────────────────────────────


def test_provenance_header_and_bare_year() -> None:
    record = {
        "raw_text": "年表经历：2016 年: 吉,这年结婚了2020 年: 凶,买房",
        "events": [{"year": 2016, "text": "这年结婚了"}],
    }
    info = audit.provenance(record, "这年结婚了", 2016, 1980)
    assert info["text_found_in_raw"] is True
    assert info["source_kind"] == "header"
    assert info["source_agrees"] is True
    assert info["year_table_header"] is True
    assert info["record_event_present"] is True

    # 解析器把裸年份一起剥掉（「2014 正常工作」→ 正文以「正常工作」开头）
    record2 = {"raw_text": "年表经历：2014 年: 凶,2014 正常工作", "events": []}
    info2 = audit.provenance(record2, "正常工作", 2014, 1980)
    assert info2["source_kind"] == "header"
    assert info2["source_agrees"] is True


def test_provenance_reports_missing_text() -> None:
    info = audit.provenance({"raw_text": "别的内容", "events": []}, "不存在", 2016, 1980)
    assert info["text_found_in_raw"] is False
    assert info["source_kind"] == "none"


# ── 剔除名单可复现 ──────────────────────────────────────────────────────────


def test_sensitivity_exclude_is_reproducible(payload: dict) -> None:
    exclude = payload["sensitivity"]["sensitivity_exclude"]
    recomputed = sorted(
        {
            item["case_id"]
            for item in payload["marriage_conflicts"]
            if item["in_window"]
        }
    )
    assert exclude == recomputed
    assert exclude == sorted(set(exclude))
    assert payload["sensitivity"]["count"] == len(exclude)
    assert set(exclude) <= {row["case_id"] for row in payload["cases"]}
    for case_id in exclude:
        assert case_id.startswith("RF-2026-")


def test_sensitivity_variants_are_ordered(payload: dict) -> None:
    variants = payload["sensitivity"]["variants"]
    assert variants["in_window_marriage_conflict"] == payload["sensitivity"]["count"]
    assert variants["any_window_marriage_conflict"] >= variants["in_window_marriage_conflict"]
    assert variants["in_window_literal_contradiction"] >= 0


# ── 只读与产物一致 ──────────────────────────────────────────────────────────


def test_inputs_are_not_modified(payload: dict) -> None:
    expected = {
        audit.EVAL_PATH: payload["inputs"]["eval_set"]["sha256"],
        audit.RAW_PATH: payload["inputs"]["raw_cases"]["sha256"],
        audit.FEAS_PATH: payload["inputs"]["feasibility_audit"]["sha256"],
    }
    for path, digest in expected.items():
        assert sha256(path.read_bytes()).hexdigest() == digest
    audit.run_audit()
    for path, digest in expected.items():
        assert sha256(path.read_bytes()).hexdigest() == digest


def test_committed_artifact_matches_fresh_run(payload: dict) -> None:
    if not audit.OUT_JSON.exists():
        pytest.skip("审计产物尚未生成：先跑 python -m tools.timing_event_year_audit")
    artifact = json.loads(audit.OUT_JSON.read_text(encoding="utf-8"))
    assert artifact["schema"] == audit.SCHEMA
    assert artifact["counts"] == payload["counts"]
    assert artifact["sensitivity"]["sensitivity_exclude"] == payload["sensitivity"]["sensitivity_exclude"]
    assert artifact["sample_20"] == payload["sample_20"]

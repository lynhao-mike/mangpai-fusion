"""T-153 婚姻质量标签工具测试。

覆盖：
1. 提问文本不作关键词证据（含「么」子串按卡片字面规则判提问、跨事件独立判定）
2. negative 优先于 positive（极性 / 关键词 / 混合）
3. unknown 不被折叠成 positive/negative（中性 / 无证据 / 提问各自保留）
4. 泄漏防线：标签不读 marriage_events 之外的字段
5. 冻结数字：411 / 382 / 342 / 54.39%
6. 确定性与幂等：两次构建、两次落盘逐字节一致，不含运行时间戳
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import marriage_quality_labels as mql  # noqa: E402


def _event(text: str, polarity: str = "unknown", year: int = 2000, age: int = 20) -> dict:
    return {"year": year, "age": age, "age_plausible": True, "polarity": polarity, "text": text}


def _case(events: list[dict], **extra) -> dict:
    case = {"case_id": "RF-TEST-000001", "usable_for_timing": True, "marriage_events": events}
    case.update(extra)
    return case


@pytest.fixture(scope="module")
def eval_set() -> dict:
    return mql.load_eval_set(mql.EVAL_PATH)


@pytest.fixture(scope="module")
def built(eval_set: dict) -> tuple[dict, list[dict], dict]:
    return mql.build_payload(eval_set)


# ---------------------------------------------------------------------------
# 提问判定
# ---------------------------------------------------------------------------


def test_question_text_with_marriage_keyword_is_not_evidence() -> None:
    row = mql.analyse_case(_case([_event("以后会结婚吗？")]))
    assert row["label"] == "unknown"
    assert row["basis"] == "none"
    assert row["unknown_reason"] == "question"
    assert row["positive_evidence"]["total"] == 0


def test_question_marker_mo_matches_inside_shenme_by_frozen_rule() -> None:
    # 卡片按字面规则：「么」出现在「什么」里也先判提问（只会让 unknown 变多）。
    row = mql.analyse_case(_case([_event("一直没什么起色，2019 年结婚")]))
    assert row["label"] == "unknown"
    assert row["unknown_reason"] == "question"


def test_one_question_event_does_not_block_other_events() -> None:
    row = mql.analyse_case(
        _case(
            [
                _event("以后会结婚吗？", year=2010, age=20),
                _event("2020 年结婚，婚姻稳定", year=2020, age=30),
            ]
        )
    )
    assert row["label"] == "positive"
    assert row["basis"] == "keyword"
    assert row["events_question"] == 1
    assert row["positive_evidence"]["keywords"] == ["结婚", "婚姻稳定"]


# ---------------------------------------------------------------------------
# negative 优先 / 关键词
# ---------------------------------------------------------------------------


def test_negative_polarity_beats_positive_polarity() -> None:
    row = mql.analyse_case(
        _case([_event("登记结婚", polarity="positive"), _event("离婚", polarity="negative")])
    )
    assert row["label"] == "negative"
    assert row["negative"] is True
    assert row["conflict"] is True
    assert row["basis"] == "polarity"


def test_negative_keyword_beats_positive_keyword() -> None:
    row = mql.analyse_case(_case([_event("13 年结婚，16 年离婚")]))
    assert row["label"] == "negative"
    assert row["conflict"] is True
    assert row["basis"] == "keyword"
    assert row["negative_evidence"]["keywords"] == ["离婚"]
    assert row["positive_evidence"]["keywords"] == ["结婚"]


def test_positive_keyword_without_negative() -> None:
    row = mql.analyse_case(_case([_event("领证结婚，婚后一子")]))
    assert row["label"] == "positive"
    assert row["basis"] == "keyword"
    assert row["conflict"] is False


def test_negative_keyword_without_positive() -> None:
    row = mql.analyse_case(_case([_event("2023 年离异")]))
    assert row["label"] == "negative"
    assert row["negative_evidence"]["keywords"] == ["离异"]


# ---------------------------------------------------------------------------
# unknown 不折叠
# ---------------------------------------------------------------------------


def test_neutral_text_stays_unknown() -> None:
    row = mql.analyse_case(_case([_event("父母感情一般，工作稳定")]))
    assert row["label"] == "unknown"
    assert row["negative"] is False
    assert row["unknown_reason"] == "neutral"


def test_question_only_stays_unknown() -> None:
    row = mql.analyse_case(_case([_event("婚姻怎么样？")]))
    assert row["label"] == "unknown"
    assert row["unknown_reason"] == "question"


def test_no_events_is_no_evidence() -> None:
    row = mql.analyse_case(_case([]))
    assert row["label"] == "unknown"
    assert row["unknown_reason"] == "no_evidence"


def test_empty_text_is_no_evidence() -> None:
    row = mql.analyse_case(_case([_event("   ")]))
    assert row["label"] == "unknown"
    assert row["unknown_reason"] == "no_evidence"


def test_unknown_polarity_value_is_treated_as_unknown() -> None:
    # 三值之外的取值按 unknown 处理：文本仍走关键词判定。
    row = mql.analyse_case(_case([_event("2019 年结婚", polarity="neutral")]))
    assert row["label"] == "positive"
    assert row["basis"] == "keyword"


# ---------------------------------------------------------------------------
# 泄漏防线
# ---------------------------------------------------------------------------


def test_label_ignores_non_event_fields() -> None:
    base = _case([_event("2019 年结婚")])
    decorated = dict(base)
    decorated.update(
        {
            "gender": "男",
            "birth_dt": "1990-01-01 00:00:00",
            "birth_year": 1990,
            "bazi_raw": "庚申 戊寅 壬子 辛丑",
            "quality_grade": "A",
        }
    )
    assert mql.analyse_case(base) == mql.analyse_case(decorated)


def test_case_record_has_no_birth_or_bazi_fields(built) -> None:
    payload, _rows, _audit = built
    allowed = {
        "case_id",
        "usable_for_timing",
        "label",
        "negative",
        "basis",
        "conflict",
        "unknown_reason",
        "events_total",
        "events_question",
        "events_empty_text",
        "negative_evidence",
        "positive_evidence",
        "evidence_events",
    }
    for row in payload["cases"]:
        assert set(row) == allowed


# ---------------------------------------------------------------------------
# 冻结数字
# ---------------------------------------------------------------------------


def test_frozen_counts(built) -> None:
    payload, _rows, _audit = built
    counts = payload["counts"]
    assert counts["cases_total"] == 411
    assert counts["usable_for_timing"] == 382
    assert counts["all"] == {
        "negative": 151,
        "positive": 164,
        "unknown": 48,
        "conflict": 48,
        "sum": 411,
    }
    assert counts["usable"] == {
        "negative": 138,
        "positive": 156,
        "unknown": 40,
        "conflict": 48,
        "sum": 382,
    }
    assert counts["final"]["usable"] == {"negative": 186, "positive": 156, "unknown": 40}
    assert payload["baseline"]["sample_size"] == 342
    assert payload["baseline"]["majority_class"] == "negative"
    assert payload["baseline"]["hits"] == 186
    assert payload["baseline"]["rate_pct"] == 54.39


def test_four_buckets_sum_to_population(built) -> None:
    payload, _rows, _audit = built
    counts = payload["counts"]
    for key, expected in (("all", 411), ("usable", 382)):
        bucket = counts[key]
        total = bucket["negative"] + bucket["positive"] + bucket["unknown"] + bucket["conflict"]
        assert total == bucket["sum"] == expected


def test_unknown_reasons_reported(built) -> None:
    payload, _rows, _audit = built
    reasons = payload["counts"]["unknown_reasons"]
    assert reasons["usable"] == {"question": 16, "neutral": 24, "no_evidence": 0}
    assert sum(reasons["usable"].values()) == payload["counts"]["final"]["usable"]["unknown"]
    assert reasons["all"] == {"question": 22, "neutral": 26, "no_evidence": 0}


def test_golden_case_labels(built) -> None:
    """冻结规则下的样例。RF-2026-000495 是已知误判，锁的是规则可复现性（见报告 §7）。"""
    _payload, rows, _audit = built
    by_id = {row["case_id"]: row for row in rows}
    assert by_id["RF-2026-000354"]["label"] == "negative"
    assert by_id["RF-2026-000354"]["conflict"] is True
    assert by_id["RF-2026-000495"]["label"] == "positive"
    assert by_id["RF-2026-000495"]["basis"] == "keyword"
    assert by_id["RF-2026-000544"]["label"] == "negative"
    assert by_id["RF-2026-000728"]["label"] == "negative"
    assert by_id["RF-2026-000259"]["label"] == "unknown"
    assert by_id["RF-2026-000259"]["unknown_reason"] == "question"
    assert by_id["RF-2026-000947"]["label"] == "unknown"


def test_audit_samples_match_frozen_report(built) -> None:
    payload, _rows, _audit = built
    mql.check_audit_samples(payload)  # 不等即抛 AuditError


# ---------------------------------------------------------------------------
# 确定性与幂等
# ---------------------------------------------------------------------------


def test_payload_and_report_deterministic(eval_set: dict, built) -> None:
    payload, rows, _audit = built
    payload_again, rows_again, _audit_again = mql.build_payload(eval_set)
    assert json.dumps(payload, ensure_ascii=False, indent=2) == json.dumps(
        payload_again, ensure_ascii=False, indent=2
    )
    assert payload["payload_sha256"] == payload_again["payload_sha256"]
    cases_by_id = {case["case_id"]: case for case in eval_set["cases"]}
    assert mql.render_report(payload, rows, cases_by_id) == mql.render_report(
        payload_again, rows_again, cases_by_id
    )


def test_no_run_timestamp_in_payload(built) -> None:
    payload, _rows, _audit = built
    assert "generated_at" not in payload
    assert payload["frozen_at"] == "2026-10-28"
    header = json.dumps(
        {key: payload[key] for key in ("schema", "task", "frozen_at", "source", "definition", "baseline")},
        ensure_ascii=False,
    )
    assert re.search(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}", header) is None


def test_main_writes_identical_bytes_twice(tmp_path, monkeypatch) -> None:
    json_path = tmp_path / "marriage-quality-labels-v1.json"
    md_path = tmp_path / "marriage-quality-labels-v1.md"
    monkeypatch.setattr(mql, "JSON_PATH", json_path)
    monkeypatch.setattr(mql, "REPORT_PATH", md_path)

    assert mql.main() == 0
    first = (json_path.read_bytes(), md_path.read_bytes())
    assert mql.main() == 0
    second = (json_path.read_bytes(), md_path.read_bytes())
    assert first == second
    assert b"generated_at" not in first[0]


def test_bad_schema_exits_2(tmp_path, monkeypatch) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text('{"schema": "something-else", "cases": []}', encoding="utf-8")
    monkeypatch.setattr(mql, "EVAL_PATH", bad)
    assert mql.main() == 2

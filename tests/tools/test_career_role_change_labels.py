"""T-161 · ``role_change`` 标签（1/null，文本先去重）回归测试。"""

from __future__ import annotations

import json
from typing import Any

import pytest

from tools import career_role_change_labels as labels


# ---------------------------------------------------------------------------
# 数据构造
# ---------------------------------------------------------------------------


def _record(
    case_id: str,
    texts: list[str],
    *,
    gender: str = "男",
    birth: str = "1990-01-01 10:00",
    duplicate_key: str | None = None,
) -> dict[str, Any]:
    return {
        "raw_id": case_id,
        "duplicate_key": duplicate_key or f"key-{case_id}",
        "gender": gender,
        "birth_datetime_raw": birth,
        "events": [
            {
                "domains": ["occupation"],
                "text": text,
                "year": 2020,
                "polarity": "unknown",
            }
            for text in texts
        ],
    }


def _label(records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    unique, _ = labels.dedupe_records(records)
    events = labels.collect_events(unique)
    labels.dedupe_event_texts(events)
    return {case["case_id"]: case for case in labels.build_cases(unique, events)}


@pytest.fixture(scope="module")
def payload() -> dict[str, Any]:
    records = labels.load_records()
    return labels.build_payload(records, labels._sha256_file(labels.SOURCE_PATH))


# ---------------------------------------------------------------------------
# 冻结口径
# ---------------------------------------------------------------------------


def test_keyword_table_is_frozen() -> None:
    assert labels.ROLE_KEYWORDS == (
        "升职", "晋升", "提拔", "跳槽", "换工作", "换岗", "调动", "转行",
        "辞职", "裸辞", "下岗", "失业", "岗位变化", "职责变化", "任职", "入职",
    )


def test_exclusion_tables_are_frozen() -> None:
    assert labels.QUESTION_MARKERS == ("？", "?", "是否", "能否", "请问", "怎么样", "吗", "么", "呢")
    assert labels.OTHER_SUBJECTS == (
        "父母", "父亲", "母亲", "爸", "妈", "老公", "老婆", "妻子", "丈夫",
        "儿子", "女儿", "孩子", "家人", "家属", "兄弟", "姐妹", "亲戚", "朋友",
        "爷爷", "奶奶", "姥姥", "姥爷", "公公", "婆婆", "岳父", "岳母",
        "兄长", "姐姐", "妹妹",
    )
    assert labels.SELF_SUBJECTS == ("我", "本人", "自己")
    assert labels.ASPIRATION_MARKERS == ("希望", "打算", "准备", "想", "能否", "是否", "计划", "有望")
    assert labels.NEGATION_MARKERS == ("无", "没", "没有", "未", "差点", "并非")
    assert labels.NEGATION_WINDOW == 6


# ---------------------------------------------------------------------------
# 标签语义：1 / null，不造 0
# ---------------------------------------------------------------------------


def test_clean_hit_is_one() -> None:
    cases = _label([_record("RF-2026-100001", ["工作晋升，收入可以"])])
    assert cases["RF-2026-100001"]["role_change"] == 1
    assert cases["RF-2026-100001"]["work_no_change"] == 0


def test_work_without_change_is_null_and_flagged() -> None:
    cases = _label([_record("RF-2026-100002", ["我一直在公司上班，收入稳定"])])
    case = cases["RF-2026-100002"]
    assert case["role_change"] is None
    assert case["work_no_change"] == 1


def test_question_only_is_null_and_not_work_no_change() -> None:
    cases = _label([_record("RF-2026-100003", ["今年事业怎么样？"])])
    case = cases["RF-2026-100003"]
    assert case["role_change"] is None
    assert case["work_no_change"] == 0
    assert case["text_events"]["usable"] == 0


def test_question_event_does_not_poison_other_event() -> None:
    cases = _label([_record("RF-2026-100004", ["今年事业怎么样？", "同一年辞职了"])])
    assert cases["RF-2026-100004"]["role_change"] == 1


def test_never_produces_zero() -> None:
    cases = _label(
        [
            _record("RF-2026-100005", ["工作晋升"]),
            _record("RF-2026-100006", ["我在公司上班"]),
            _record("RF-2026-100007", ["今年事业怎么样？"]),
        ]
    )
    assert {case["role_change"] for case in cases.values()} == {1, None}
    assert all(case["role_change"] != 0 for case in cases.values())


# ---------------------------------------------------------------------------
# 四类排除
# ---------------------------------------------------------------------------


def test_other_subject_excluded() -> None:
    cases = _label([_record("RF-2026-100010", ["因父亲工作调动，从山区来到杭州读书"])])
    assert cases["RF-2026-100010"]["role_change"] is None
    assert "other_subject" in {
        tag for item in cases["RF-2026-100010"]["excluded_occurrences"] for tag in item["tags"]
    }


def test_self_subject_in_window_keeps_hit() -> None:
    cases = _label([_record("RF-2026-100011", ["我被迫升岗级，换岗位"])])
    assert cases["RF-2026-100011"]["role_change"] == 1


def test_aspiration_excluded() -> None:
    cases = _label([_record("RF-2026-100012", ["工作顺利有晋升希望"])])
    assert cases["RF-2026-100012"]["role_change"] is None
    assert cases["RF-2026-100012"]["excluded_occurrences"][0]["tags"] == ["aspiration"]


def test_negation_window_is_six_chars() -> None:
    near = _label([_record("RF-2026-100013", ["没有升职加薪"])])
    assert near["RF-2026-100013"]["role_change"] is None
    far = _label([_record("RF-2026-100014", ["没有 123456789 升职"])])
    assert far["RF-2026-100014"]["role_change"] == 1


def test_question_markers_are_whole_event() -> None:
    cases = _label([_record("RF-2026-100015", ["公司不错，工作晋升吗"])])
    assert cases["RF-2026-100015"]["role_change"] is None


# ---------------------------------------------------------------------------
# 文本去重
# ---------------------------------------------------------------------------


def test_text_digest_ignores_whitespace() -> None:
    assert labels.text_digest("换 工作") == labels.text_digest("换工作")
    assert labels.text_digest("  换工作  ") == labels.text_digest("换工作")
    assert labels.text_digest("换工作") != labels.text_digest("换岗")


def test_cross_case_duplicate_keeps_smallest_raw_id() -> None:
    cases = _label(
        [
            _record("RF-2026-100021", ["2020 年换工作"]),
            _record("RF-2026-100020", ["2020 年换工作"]),
        ]
    )
    assert cases["RF-2026-100020"]["role_change"] == 1
    assert cases["RF-2026-100020"]["text_events"]["kept"] == 1
    assert cases["RF-2026-100021"]["role_change"] is None
    assert cases["RF-2026-100021"]["text_events"]["kept"] == 0
    assert cases["RF-2026-100021"]["text_events"]["dropped_duplicate"] == 1


def test_same_case_duplicate_is_collapsed() -> None:
    cases = _label([_record("RF-2026-100022", ["换工作", "换  工作"])])
    case = cases["RF-2026-100022"]
    assert case["text_events"]["kept"] == 1
    assert case["text_events"]["dropped_duplicate"] == 1
    assert case["role_change"] == 1


# ---------------------------------------------------------------------------
# 全量不变量
# ---------------------------------------------------------------------------


def test_full_funnel(payload: dict[str, Any]) -> None:
    counts = payload["counts"]
    assert counts["records"] == 992
    assert counts["unique_cases"] == 959
    assert counts["occupation_cases"] == 620
    assert counts["occupation_events"] == 957
    assert counts["question_events"] == 79
    assert counts["usable_events"] == 878
    assert counts["cases_all_events_questions"] == 56
    assert counts["chart_ready_cases"] == 614
    assert counts["role_change_1"] == 85
    assert counts["role_change_null"] == 535
    assert counts["work_no_change"] == 473
    assert counts["dropped_duplicate_text"] == 21


def test_text_dedup_reproduces_t159(payload: dict[str, Any]) -> None:
    dedup = payload["text_dedup"]
    assert dedup["groups_with_duplicates"] == 19
    assert sum(item["events"] for item in dedup["details"]) == 40
    assert dedup["cross_case_groups"] == 16
    assert dedup["cross_case_events"] == 32
    assert dedup["dropped_events"] == 21
    assert dedup["cases_affected"] == 13


def test_label_additivity(payload: dict[str, Any]) -> None:
    assert payload["invariants"]["role_change_1_plus_null"] == 620
    assert payload["invariants"]["zero_labels"] == 0
    assert payload["counts"]["role_change_1"] + payload["counts"]["role_change_null"] == 620
    labels.check_invariants(payload)


def test_baseline_formula(payload: dict[str, Any]) -> None:
    baseline = payload["baseline"]["all_cases"]
    assert baseline["rate"] == round(baseline["role_change_1"] / (1 + baseline["null"]), 4)
    assert baseline["percent"] == 15.86
    chart = payload["baseline"]["chart_ready"]
    assert chart["n"] == 614
    assert chart["rate"] == round(chart["role_change_1"] / (1 + chart["null"]), 4)


# ---------------------------------------------------------------------------
# 防泄漏与确定性
# ---------------------------------------------------------------------------


def test_no_board_fields_in_payload(payload: dict[str, Any]) -> None:
    def walk(node: Any, path: str = "$") -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                lowered = str(key).lower()
                for token in ("bazi", "qian_kun", "ganzhi", "dayun", "liunian", "score"):
                    assert token not in lowered, f"{path}.{key} 含盘面字段 {token}"
                walk(value, f"{path}.{key}")
        elif isinstance(node, list):
            for index, value in enumerate(node):
                walk(value, f"{path}[{index}]")

    walk(payload)


def test_payload_is_deterministic(payload: dict[str, Any]) -> None:
    records = labels.load_records()
    again = labels.build_payload(records, labels._sha256_file(labels.SOURCE_PATH))
    assert again["payload_sha256"] == payload["payload_sha256"]
    assert json.dumps(again, ensure_ascii=False, indent=2) == json.dumps(
        payload, ensure_ascii=False, indent=2
    )


def test_main_writes_identical_bytes_twice() -> None:
    assert labels.main() == 0
    first = labels.JSON_PATH.read_bytes()
    report_first = labels.REPORT_PATH.read_bytes()
    assert labels.main() == 0
    assert labels.JSON_PATH.read_bytes() == first
    assert labels.REPORT_PATH.read_bytes() == report_first


def test_no_zero_in_written_json() -> None:
    data = json.loads(labels.JSON_PATH.read_text(encoding="utf-8"))
    assert all(case["role_change"] in (1, None) for case in data["cases"])
    assert all(case["role_change"] != 0 for case in data["cases"])
    assert data["invariants"]["zero_labels"] == 0


# ---------------------------------------------------------------------------
# 审计与报告
# ---------------------------------------------------------------------------


def test_audit_rows_are_frozen(payload: dict[str, Any]) -> None:
    rows = payload["audit"]["rows"]
    assert len(rows) == 20
    assert all(row["verdict"] for row in rows)
    passed = sum(1 for row in rows if row["verdict"].startswith("成立"))
    assert passed == 18
    assert {row["case_id"] for row in rows} == set(labels.AUDIT_VERDICTS)


def test_exclusion_audit_covers_four_types(payload: dict[str, Any]) -> None:
    rows = payload["audit"]["exclusion_examples"]
    assert {row["type"] for row in rows} == {"他人主体", "意向语", "否定", "提问"}
    assert any(row["verdict"].startswith("正确") for row in rows)
    assert any(row["verdict"].startswith("误伤") for row in rows)


def test_report_matches_payload(payload: dict[str, Any]) -> None:
    report = labels.render_report(payload)
    assert "# 事业角色变化标签 v1（T-161）" in report
    assert "620" in report and "614" in report
    assert str(payload["counts"]["role_change_1"]) in report
    assert str(payload["counts"]["role_change_null"]) in report
    assert "没有 0" in report
    assert "18/20" in report
    assert "重复组 **19**" in report


def test_audit_stale_detection() -> None:
    cases = _label([_record("RF-2026-100099", ["工作晋升"])])
    with pytest.raises(labels.AuditStaleError):
        labels.build_audit_rows(
            [{**case, "role_change": 1} for case in cases.values() if case["role_change"] == 1]
        )


def test_invariants_reject_tampered_counts(payload: dict[str, Any]) -> None:
    tampered = json.loads(json.dumps(payload, ensure_ascii=False))
    tampered["counts"]["occupation_cases"] = 619
    with pytest.raises(labels.FunnelInvariantError):
        labels.check_invariants(tampered)


def test_labels_reject_bool_or_zero(payload: dict[str, Any]) -> None:
    zero_payload = json.loads(json.dumps(payload, ensure_ascii=False))
    zero_payload["cases"][0]["role_change"] = 0
    zero_payload["invariants"]["zero_labels"] = 1
    with pytest.raises(labels.FunnelInvariantError):
        labels._assert_labels(zero_payload)

    bool_payload = json.loads(json.dumps(payload, ensure_ascii=False))
    bool_payload["cases"][0]["role_change"] = True
    with pytest.raises(labels.FunnelInvariantError):
        labels._assert_labels(bool_payload)

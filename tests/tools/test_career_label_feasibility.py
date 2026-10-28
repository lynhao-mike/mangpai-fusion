"""T-159 事业标签可行性审计工具测试。

覆盖：
1. 提问判定：9 个标记逐个压制（含「么」子串按卡片字面规则），整段不作证据
2. 关键词命中 / 多位置 / 噪声旗标（他人主体、意向语、子串）
3. 四桶互斥与可加性（四桶之和 = occupation 案例数）
4. 冻结计数：992 / 959 / 620 / 957 / 79 / 878 / 56 / 614，角色 107，四桶 162/38/24/396
5. 只读：不建标签、不评分、不建盘、不含任何八字/盘面字段名
6. 确定性：两次构建 JSON 逐字节一致
7. 审计表可回原文：20 + 20 例、带 raw_id 与 JSONL 行号、角色证据含命中词
8. 结论必须是三分类之一，且路径三分类不得写成「可判」
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import career_label_feasibility as clf  # noqa: E402

FORBIDDEN_KEY_TOKENS = ("bazi", "qian_kun", "pillar", "ganzhi", "dayun", "四柱", "八字")
# ``chart_ready`` 是「出生时刻可解析」的就绪标记（T-158 §2.1），不是盘面事实；
# ``charts_built`` 是只读声明位。其余带 chart 的键名一律视为泄漏。
ALLOWED_CHART_KEYS = {"chart_ready", "chart_ready_cases", "chart_ready_basis", "charts_built"}


@pytest.fixture(scope="module")
def payload() -> dict:
    records = clf.load_records()
    built, _cases = clf.build_payload(records, clf._sha256_file(clf.SOURCE_PATH))
    return built


def _event(text: str, polarity: str = "unknown", year: int = 2000) -> dict:
    return {"text": text, "polarity": polarity, "year": year, "domains": ["occupation"]}


def _record(*texts: str, case_id: str = "RF-TEST-000001") -> dict:
    return {
        "raw_id": case_id,
        "line_start": 1,
        "line_end": 1,
        "gender": "男",
        "birth_datetime_raw": "1990-01-01 10:00",
        "profile": {},
        "events": [_event(text) for text in texts],
    }


# ---------------------------------------------------------------------------
# 提问判定
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("marker", clf.QUESTION_MARKERS)
def test_each_question_marker_suppresses_whole_segment(marker: str) -> None:
    text = f"2018 年升职 {marker} 后面还有陈述"
    assert clf.is_question(text)
    assert clf.scan_keywords([_event(text)], clf.ROLE_KEYWORDS) == []


def test_statement_not_question_and_keywords_hit() -> None:
    text = "2018 年被提拔，跳槽到另一家单位"
    assert not clf.is_question(text)
    keys = {item["keyword"] for item in clf.scan_keywords([_event(text)], clf.ROLE_KEYWORDS)}
    assert keys == {"提拔", "跳槽"}
    emp = {item["keyword"] for item in clf.scan_keywords([_event(text)], clf.EMPLOYMENT_KEYWORDS)}
    assert emp == {"单位"}


def test_question_event_does_not_block_sibling_event() -> None:
    record = _record("2018 年升职加薪", "以后会怎么样？")
    case = clf.analyse_case(record)
    assert case["role"]["raw"] == ["升职"]
    assert case["usable_events"] == 1


# ---------------------------------------------------------------------------
# 关键词与旗标
# ---------------------------------------------------------------------------


def test_keyword_positions_returns_all_starts() -> None:
    assert clf.keyword_positions("跳槽又跳槽", "跳槽") == [0, 3]


@pytest.mark.parametrize(
    ("text", "keyword", "tag"),
    [
        ("媳妇换工作花了 6 万", "换工作", "other_subject"),
        ("工作顺利有晋升希望", "晋升", "aspiration"),
        ("应聘国企本来要成功", "国企", "aspiration"),
        ("阴差阳错全票通过，当上班长", "上班", "substring"),
        ("学历大专，工作室内设计师", "工作室", "substring"),
        ("创业公司倒闭了", "创业", "substring"),
    ],
)
def test_occurrence_tags(text: str, keyword: str, tag: str) -> None:
    position = text.find(keyword)
    assert position >= 0
    assert tag in clf.occurrence_tags(text, position, keyword)


def test_clean_hit_without_flag() -> None:
    text = "我被迫升岗级，换岗位"
    position = text.find("换岗")
    assert clf.occurrence_tags(text, position, "换岗") == ()


# ---------------------------------------------------------------------------
# 四桶
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("employment", "entrepreneurship", "bucket"),
    [
        (True, False, "employment"),
        (False, True, "entrepreneurship"),
        (True, True, "mixed"),
        (False, False, "neither"),
    ],
)
def test_bucket_of(employment: bool, entrepreneurship: bool, bucket: str) -> None:
    assert clf.bucket_of(employment, entrepreneurship) == bucket


def test_bucket_additive(payload: dict) -> None:
    raw = payload["path_types"]["raw"]
    assert raw["sum"] == payload["funnel"]["occupation_cases"]
    assert raw["employment"] + raw["entrepreneurship"] + raw["mixed"] + raw["neither"] == raw["sum"]
    guarded = payload["path_types"]["guarded"]
    assert guarded["sum"] == payload["funnel"]["occupation_cases"]
    ready = payload["path_types"]["raw_chart_ready"]
    assert ready["sum"] == payload["funnel"]["chart_ready_cases"]


# ---------------------------------------------------------------------------
# 冻结计数
# ---------------------------------------------------------------------------


def test_frozen_funnel(payload: dict) -> None:
    funnel = payload["funnel"]
    assert funnel["records"] == 992
    assert funnel["unique"] == 959
    assert funnel["occupation_cases"] == 620
    assert funnel["occupation_events"] == 957
    assert funnel["question_events"] == 79
    assert funnel["usable_events"] == 878
    assert funnel["cases_without_usable_event"] == 56
    assert funnel["chart_ready_cases"] == 614


def test_frozen_role_and_path_counts(payload: dict) -> None:
    role = payload["role_change"]["raw"]
    assert role["cases"] == 107
    assert role["chart_ready_cases"] == 107
    raw = payload["path_types"]["raw"]
    assert (raw["employment"], raw["entrepreneurship"], raw["mixed"], raw["neither"]) == (
        162,
        38,
        24,
        396,
    )


def test_question_split_reconciles(payload: dict) -> None:
    funnel = payload["funnel"]
    assert funnel["usable_events"] + funnel["question_events"] == funnel["occupation_events"]
    neither = payload["path_types"]["neither_breakdown"]
    assert (
        neither["all_events_are_questions"] + neither["text_but_no_path_keyword"]
        == neither["cases"]
    )
    assert neither["all_events_are_questions"] == funnel["cases_without_usable_event"]


# ---------------------------------------------------------------------------
# 只读与泄漏
# ---------------------------------------------------------------------------


def test_payload_declares_read_only(payload: dict) -> None:
    audit = payload["audit"]
    assert audit["read_only"] is True
    assert audit["labels_written"] is False
    assert audit["scores_written"] is False
    assert audit["charts_built"] is False
    assert audit["bazi_fields_used"] is False
    assert "cases" not in payload  # 不写逐例标签


def _walk_keys(node: object, path: str = "$") -> list[str]:
    found: list[str] = []
    if isinstance(node, dict):
        for key, value in node.items():
            if any(token in str(key).lower() for token in FORBIDDEN_KEY_TOKENS):
                found.append(f"{path}.{key}")
            found.extend(_walk_keys(value, f"{path}.{key}"))
    elif isinstance(node, list):
        for index, value in enumerate(node):
            found.extend(_walk_keys(value, f"{path}[{index}]"))
    return found


def test_no_bazi_or_chart_fields_in_payload(payload: dict) -> None:
    # bazi_fields_used 是显式声明位，不是数据字段。
    offenders = [item for item in _walk_keys(payload) if not item.endswith("bazi_fields_used")]
    assert offenders == []
    chart_keys = {
        key
        for key in _walk_keys(payload)
        if "chart" in key.rsplit(".", 1)[-1].lower()
    }
    assert {key for key in chart_keys if key.rsplit(".", 1)[-1] not in ALLOWED_CHART_KEYS} == set()


# ---------------------------------------------------------------------------
# 确定性
# ---------------------------------------------------------------------------


def test_two_builds_are_byte_identical(payload: dict) -> None:
    records = clf.load_records()
    rebuilt, _cases = clf.build_payload(records, clf._sha256_file(clf.SOURCE_PATH))
    first = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
    second = json.dumps(rebuilt, ensure_ascii=False, indent=2, sort_keys=True)
    assert first == second


def test_payload_sha256_recomputes(payload: dict) -> None:
    assert payload["payload_sha256"] == clf._payload_sha256(payload)


# ---------------------------------------------------------------------------
# 审计表
# ---------------------------------------------------------------------------


def test_audit_samples_traceable(payload: dict) -> None:
    role_rows = payload["audit"]["role_change"]
    path_rows = payload["audit"]["path_type"]
    assert len(role_rows) == 20
    assert len(path_rows) == 20
    for row in role_rows + path_rows:
        assert row["case_id"].startswith("RF-2026-")
        assert isinstance(row["line_start"], int) and row["line_start"] >= 1
    for row in role_rows:
        assert row["evidence"], f"{row['case_id']} 无证据事件"
        for item in row["evidence"]:
            assert item["keyword"] in item["text"]


def test_audit_covers_all_four_buckets(payload: dict) -> None:
    buckets = {row["bucket_raw"] for row in payload["audit"]["path_type"]}
    assert buckets == set(clf.BUCKET_ORDER)
    assert len({row["case_id"] for row in payload["audit"]["path_type"]}) == 20


def test_frozen_findings_align_with_audit_rows(payload: dict) -> None:
    rows = {row["case_id"]: row for row in payload["audit"]["role_change"]}
    for case_id, keywords, verdict in clf.AUDIT_ROLE_CHANGE:
        assert tuple(rows[case_id]["matched_keywords"]) == tuple(sorted(keywords))
        assert verdict
    rows = {row["case_id"]: row for row in payload["audit"]["path_type"]}
    for case_id, bucket, verdict in clf.AUDIT_PATH_TYPE:
        assert rows[case_id]["bucket_raw"] == bucket
        assert verdict


# ---------------------------------------------------------------------------
# 结论
# ---------------------------------------------------------------------------


def test_conclusion_is_explicit(payload: dict) -> None:
    allowed = {"可判", "勉强可判", "不可判"}
    conclusion = payload["conclusion"]
    assert conclusion["role_change"]["verdict"] in allowed
    assert conclusion["path_type_3class"]["verdict"] in allowed
    assert conclusion["path_type_3class"]["reasons"]
    # 三分类结论不许写成「可判」：去噪后 71% 案例无路径证据。
    assert conclusion["path_type_3class"]["verdict"] != "可判"
    assert conclusion["role_change"]["verdict"] == "勉强可判"


def test_known_issues_nonempty(payload: dict) -> None:
    assert len(payload["known_issues"]) >= 5
    assert all(item["evidence"] for item in payload["known_issues"])

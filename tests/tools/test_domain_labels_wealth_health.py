"""T-158 财富 / 健康结局标签测试。

覆盖：
1. 冻结关键词表与提问标记与任务卡 §2 完全一致（不许为了阳性率调词）
2. 提问文本不作证据（每个标记逐一验证，整段抑制、跨事件独立）
3. `null` 不折叠成 0 / 1（无该域事件 / 全是提问 / 无文本）
4. `1` 优先（混合证据），polarity 不参与判定
5. 漏斗与四桶可加：992 / 959 / 950 / 952 / 947、基础集 944、chart_ready 940
6. 无盘面 / 八字字段泄漏（JSON 键与工具源码双向检查）
7. 确定性与幂等：两次构建逐字节一致，落盘产物与当前实现一致
8. 已知误判清单与 20 例抽查仍可在当前数据复核
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import domain_labels_wealth_health as m  # noqa: E402

SOURCE_CODE = Path(m.__file__).read_text(encoding="utf-8")

# 盘面 / 八字字段名（防泄漏）。`chart_ready` 是任务卡要求的标记字段，单独允许。
FORBIDDEN_KEYS = (
    "bazi",
    "qian_kun",
    "pillars",
    "ganzhi",
    "shishen",
    "dayun",
    "liunian",
    "nayin",
    "shensha",
    "canggan",
    "day_master",
    "engine",
    "profile",
    "raw_text",
    "birth_place",
)
# 源码里连这些 token 都不该出现（`raw_text` 等是数据源字段名，允许出现在读取校验里）。
FORBIDDEN_SOURCE_TOKENS = (
    "bazi",
    "qian_kun",
    "pillars",
    "ganzhi",
    "shishen",
    "dayun",
    "liunian",
    "nayin",
    "shensha",
    "canggan",
    "day_master",
    "engine",
    "chart",
)


# ---------------------------------------------------------------------------
# 构造器
# ---------------------------------------------------------------------------


def _event(
    domains: list[str],
    text: str,
    polarity: str = "unknown",
    year: int = 2020,
) -> dict:
    return {"domains": domains, "polarity": polarity, "text": text, "year": year}


def _record(
    events: list[dict],
    *,
    raw_id: str = "RF-TEST-000001",
    gender: str = "女",
    birth: str = "1990-01-01 08:00",
    calendar: str = "solar",
    true_solar: str = "",
    raw_text: str = "",
) -> dict:
    return {
        "raw_id": raw_id,
        "duplicate_key": raw_id,
        "gender": gender,
        "birth_datetime_raw": birth,
        "calendar_type": calendar,
        "true_solar_time_raw": true_solar,
        "raw_text": raw_text,
        "events": events,
    }


def _labels_of(record: dict) -> dict:
    return {spec.key: m.classify_domain(record, spec)["label"] for spec in m.LABEL_SPECS}


@pytest.fixture(scope="module")
def built() -> tuple[dict, list[dict], list[dict]]:
    records = m.load_source()
    return m.build_payload(
        records, source_path=m.SOURCE_PATH, source_sha256=m._sha256_file(m.SOURCE_PATH)
    )


# ---------------------------------------------------------------------------
# 1. 冻结定义
# ---------------------------------------------------------------------------


def test_debt_keywords_frozen_to_task_card() -> None:
    assert m.DEBT_KEYWORDS == (
        "负债", "欠债", "债务", "欠款", "借款", "贷款", "信贷", "破产", "被骗", "还债",
        "负债累累", "亏损", "资金链", "被执行人",
    )


def test_serious_health_keywords_frozen_to_task_card() -> None:
    assert m.SERIOUS_HEALTH_KEYWORDS == (
        "手术", "住院", "ICU", "抢救", "病危", "癌", "肿瘤", "重病", "大病", "慢性病",
        "中风", "心脏病", "糖尿病", "肾衰竭", "化疗", "放疗", "瘫痪", "失明", "精神病",
    )


def test_question_markers_frozen_to_task_card() -> None:
    assert m.QUESTION_MARKERS == ("？", "?", "是否", "能否", "请问", "怎么样", "吗", "么", "呢")


# ---------------------------------------------------------------------------
# 2. 提问不算证据
# ---------------------------------------------------------------------------


def test_question_event_is_not_debt_evidence() -> None:
    record = _record([_event(["income"], "我现在负债累累，什么时候能还清？")])
    result = m.classify_domain(record, m.LABEL_SPECS[0])
    assert result["label"] is None
    assert result["null_reason"] == "all_question"
    assert result["events_evidence"] == 0
    assert result["events"][0]["matched"] == []
    assert result["events"][0]["verdict"] == "question"


@pytest.mark.parametrize("marker", m.QUESTION_MARKERS)
def test_each_question_marker_suppresses_whole_event(marker: str) -> None:
    text = f"2019 年手术住院，负债 20 万{marker}"
    record = _record([_event(["income", "health"], text)])
    debt = m.classify_domain(record, m.LABEL_SPECS[0])
    health = m.classify_domain(record, m.LABEL_SPECS[1])
    assert debt["label"] is None and debt["null_reason"] == "all_question"
    assert health["label"] is None and health["null_reason"] == "all_question"


def test_question_event_does_not_block_other_events() -> None:
    record = _record(
        [
            _event(["income"], "以后会不会负债？", year=2010),
            _event(["income"], "信用卡负债 10 万", year=2020),
        ]
    )
    result = m.classify_domain(record, m.LABEL_SPECS[0])
    assert result["label"] == 1
    assert result["events_question"] == 1
    assert result["events_evidence"] == 1
    assert result["matched_keywords"] == ["负债"]


def test_question_marker_mo_inside_shenme_also_suppresses() -> None:
    # 卡片按字面规则：「么」出现在「什么」里也先判提问（只会让证据变少）。
    record = _record([_event(["health"], "也不知道什么原因，住院了")])
    result = m.classify_domain(record, m.LABEL_SPECS[1])
    assert result["label"] is None
    assert result["null_reason"] == "all_question"


# ---------------------------------------------------------------------------
# 3. null 不折叠
# ---------------------------------------------------------------------------


def test_no_domain_event_is_null_not_zero() -> None:
    record = _record([_event(["occupation"], "升职加薪")])
    assert _labels_of(record) == {"debt": None, "serious_health": None}
    assert m.classify_domain(record, m.LABEL_SPECS[0])["null_reason"] == "no_domain_event"


def test_zero_requires_an_evidence_event() -> None:
    record = _record([_event(["income"], "今年收入一般，工作还算稳定")])
    result = m.classify_domain(record, m.LABEL_SPECS[0])
    assert result["label"] == 0
    assert result["null_reason"] is None
    assert result["events_evidence"] == 1


def test_empty_text_event_is_null_no_text() -> None:
    record = _record([_event(["income"], "   ")])
    result = m.classify_domain(record, m.LABEL_SPECS[0])
    assert result["label"] is None
    assert result["null_reason"] == "no_text"


def test_null_not_folded_in_built_counts(built: tuple[dict, list[dict], list[dict]]) -> None:
    payload, _cases, _excluded = built
    counts = payload["counts"]
    for spec in m.LABEL_SPECS:
        block = counts[spec.key]
        assert block["null"] > 0, f"{spec.key} 应存在 null，不能被折成 0"
        assert block["1"] + block["0"] + block["null"] == block["sum"] == counts["base_sample"]
        ready = block["chart_ready"]
        assert ready["1"] + ready["0"] + ready["null"] == ready["sum"] == counts["base_chart_ready"]
    assert sum(
        1 for case in payload["cases"] if case["labels"]["debt"] is None
    ) == counts["debt"]["null"]


# ---------------------------------------------------------------------------
# 4. 1 优先 / polarity 不参与
# ---------------------------------------------------------------------------


def test_mixed_evidence_one_wins() -> None:
    record = _record(
        [
            _event(["income"], "信用卡负债 10 万"),
            _event(["income"], "收入稳定"),
        ]
    )
    result = m.classify_domain(record, m.LABEL_SPECS[0])
    assert result["label"] == 1
    assert result["conflict"] is True


@pytest.mark.parametrize("polarity", ["negative", "positive", "unknown"])
def test_polarity_does_not_change_label(polarity: str) -> None:
    record = _record([_event(["income"], "买了房，背上了贷款", polarity=polarity)])
    assert m.classify_domain(record, m.LABEL_SPECS[0])["label"] == 1


def test_no_hit_even_if_polarity_negative() -> None:
    record = _record([_event(["income"], "今年感情不顺，破财", polarity="negative")])
    assert m.classify_domain(record, m.LABEL_SPECS[0])["label"] == 0


# ---------------------------------------------------------------------------
# 5. 漏斗与四桶
# ---------------------------------------------------------------------------


def test_funnel_counts_frozen(built: tuple[dict, list[dict], list[dict]]) -> None:
    counts = built[0]["counts"]
    assert counts["records_total"] == 992
    assert counts["after_dedupe"] == 959
    assert counts["with_gender"] == 950
    assert counts["birth_date_parsable"] == 952
    assert counts["birth_time_parsable"] == 947
    assert counts["base_sample"] == 944
    assert counts["base_chart_ready"] == 940


def test_domain_event_counts_frozen(built: tuple[dict, list[dict], list[dict]]) -> None:
    audit = built[0]["audit"]["domain"]
    assert audit["debt"]["cases_with_domain_events"] == 377
    assert audit["debt"]["events_total"] == 606
    assert audit["serious_health"]["cases_with_domain_events"] == 453
    assert audit["serious_health"]["events_total"] == 659


def test_dedupe_and_exclusions(built: tuple[dict, list[dict], list[dict]]) -> None:
    payload, cases, excluded = built
    assert payload["counts"]["duplicate_records_removed"] == 33
    assert len(cases) == 944
    assert len(excluded) == 15
    assert payload["audit"]["base_excluded"]["total"] == 15
    assert all(item["reasons"] for item in excluded)


# ---------------------------------------------------------------------------
# 6. 无盘面字段泄漏
# ---------------------------------------------------------------------------


def _walk_keys(node, path: str = "$") -> list[str]:
    found: list[str] = []
    if isinstance(node, dict):
        for key, value in node.items():
            found.append(f"{path}.{key}")
            found.extend(_walk_keys(value, f"{path}.{key}"))
    elif isinstance(node, list):
        for index, value in enumerate(node):
            found.extend(_walk_keys(value, f"{path}[{index}]"))
    return found


def test_payload_has_no_chart_fields(built: tuple[dict, list[dict], list[dict]]) -> None:
    payload = built[0]
    leaked = []
    for path in _walk_keys(payload):
        key = path.rsplit(".", 1)[-1].split("[", 1)[0].lower()
        if key == "chart_ready":
            continue
        if any(token in key for token in FORBIDDEN_KEYS):
            leaked.append(path)
    assert leaked == []


def test_case_fields_are_exactly_the_card_contract(built: tuple[dict, list[dict], list[dict]]) -> None:
    payload = built[0]
    for case in payload["cases"]:
        assert set(case) == {
            "case_id",
            "gender",
            "birth_datetime_raw",
            "birth_dt",
            "time_basis",
            "chart_ready",
            "labels",
            "evidence_events",
        }
        assert set(case["labels"]) == {"debt", "serious_health"}
        assert case["labels"]["debt"] in (0, 1, None)
        assert case["labels"]["serious_health"] in (0, 1, None)


def test_source_has_no_chart_or_engine_tokens() -> None:
    stripped = SOURCE_CODE.replace("chart_ready", "").lower()
    leaked = [token for token in FORBIDDEN_SOURCE_TOKENS if token in stripped]
    assert leaked == [], f"工具源码出现盘面/引擎 token：{leaked}"


def test_no_engine_import() -> None:
    assert "from engine" not in SOURCE_CODE
    assert "import engine" not in SOURCE_CODE


# ---------------------------------------------------------------------------
# 7. 确定性 / 幂等
# ---------------------------------------------------------------------------


def test_two_builds_are_identical(built: tuple[dict, list[dict], list[dict]]) -> None:
    payload_first = built[0]
    payload_second, _cases, _excluded = m.build_payload(
        m.load_source(), source_path=m.SOURCE_PATH, source_sha256=m._sha256_file(m.SOURCE_PATH)
    )
    first = json.dumps(payload_first, ensure_ascii=False, sort_keys=True)
    second = json.dumps(payload_second, ensure_ascii=False, sort_keys=True)
    assert first == second
    assert payload_first["payload_sha256"] == payload_second["payload_sha256"]


def test_artifacts_match_current_build(built: tuple[dict, list[dict], list[dict]]) -> None:
    payload, cases, _excluded = built
    on_disk_json = m.JSON_PATH.read_text(encoding="utf-8")
    expected_json = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    assert on_disk_json == expected_json
    assert m.REPORT_PATH.read_text(encoding="utf-8") == m.render_report(payload, cases)
    assert not {"generated_at", "run_at", "timestamp"} & set(payload)


def test_payload_sha256_is_stable(built: tuple[dict, list[dict], list[dict]]) -> None:
    payload = built[0]
    material = {
        key: value for key, value in payload.items() if key != "payload_sha256"
    }
    digest = hashlib.sha256(
        json.dumps(material, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    assert digest == payload["payload_sha256"]


# ---------------------------------------------------------------------------
# 8. 人工核查与证据可回溯
# ---------------------------------------------------------------------------


def test_known_issues_still_reproduce(built: tuple[dict, list[dict], list[dict]]) -> None:
    _payload, cases, _excluded = built
    m.check_known_issues(cases)  # 任何一条失效都会抛 AuditError
    by_id = {case["case_id"]: case for case in cases}
    for key, _kind, case_id, keyword, _phenomenon, _verdict in m.KNOWN_ISSUES:
        assert by_id[case_id]["labels"][key] == 1
        matched = {
            hit
            for entry in by_id[case_id]["evidence_events"]
            if entry["label_key"] == key
            for hit in entry["matched"]
        }
        assert keyword in matched


def test_audit_samples_frozen(built: tuple[dict, list[dict], list[dict]]) -> None:
    _payload, cases, _excluded = built
    assert len(m.AUDIT_SAMPLES) == 20
    m.check_audit_samples(cases)


def test_matched_keywords_come_from_event_text(built: tuple[dict, list[dict], list[dict]]) -> None:
    _payload, cases, _excluded = built
    source = {record["raw_id"]: record for record in m.load_source()}
    for case in cases:
        record = source[case["case_id"]]
        for entry in case["evidence_events"]:
            if entry["verdict"] != "evidence":
                assert entry["matched"] == []
                continue
            # 摘要会截断，命中必须能回落到该案例该域的完整事件原文。
            domain_text = " ".join(
                event.get("text") or ""
                for event in record["events"]
                if entry["domain"] in (event.get("domains") or [])
            )
            for keyword in entry["matched"]:
                assert keyword in domain_text
    assert any(
        entry["verdict"] == "question" and entry["matched"] == []
        for case in cases
        for entry in case["evidence_events"]
    )


def test_excluded_records_carry_reasons() -> None:
    records = [
        _record([], raw_id="RF-TEST-000001", gender="", birth="1990-01-01 08:00"),
        _record([], raw_id="RF-TEST-000002", gender="男", birth=""),
        _record([], raw_id="RF-TEST-000003", gender="女", birth="1990-01-01 08:00"),
    ]
    unique, _groups, _removed = m.dedupe_records(records)
    _payload, cases, excluded = m.build_payload(
        unique, source_path=m.SOURCE_PATH, source_sha256="test"
    )
    assert [case["case_id"] for case in cases] == ["RF-TEST-000003"]
    reasons = {item["case_id"]: item["reasons"] for item in excluded}
    assert reasons["RF-TEST-000001"] == ["missing_gender"]
    assert reasons["RF-TEST-000002"] == ["birth_empty"]

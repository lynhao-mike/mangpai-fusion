"""T-158 §9 · 财富 / 健康结局标签 v2 测试。

覆盖：
1. 冻结词表：卡 §9.2 的删词 / 保留词 / 主体词 / 否定词 / 房贷词逐项一致
2. 主体过滤：家属句排除、亲属+我 → 主体不明 → null、零主语 = 叙述者
3. 否定过滤：6 字窗口边界（含 / 不含）、否定 → 0（不是 null）
4. 房贷 / 按揭默认排除并单列；阳性优先于排除
5. health 删 `手术`/`住院`；`慢性病` 保留但单列
6. null 语义：无证据事件 / 全提问 / 命中全被过滤 → null，不折 0/1
7. 漏斗与四桶不变量（992 / 959 / 950 / 952 / 947 / 944 / 940）
8. 门槛：假阳性率与含漏判错误率冻结；判定 = 标签不适合作裁决
9. 无盘面字段泄漏；确定性；产物与实现一致；v1 产物不被改动
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

from tools import domain_labels_wealth_health as v1  # noqa: E402
from tools import domain_labels_wealth_health_v2 as v2  # noqa: E402

SOURCE_CODE = Path(v2.__file__).read_text(encoding="utf-8")

FORBIDDEN_KEYS = (
    "bazi", "qian_kun", "pillars", "ganzhi", "shishen", "dayun", "liunian", "nayin",
    "shensha", "canggan", "day_master", "engine", "profile", "raw_text", "birth_place",
)
FORBIDDEN_SOURCE_TOKENS = (
    "bazi", "qian_kun", "pillars", "ganzhi", "shishen", "dayun", "liunian", "nayin",
    "shensha", "canggan", "day_master", "engine", "chart",
)

# v1 产物指纹：v2 只读 v1，绝不能把 v1 写坏。
V1_PAYLOAD_SHA256 = "323c1fea97650ce26f7ffa8366a204b97a0aa0312b4f0263314903a668fc859a"


# ---------------------------------------------------------------------------
# 构造器
# ---------------------------------------------------------------------------


def _event(domains: list[str], text: str, polarity: str = "unknown", year: int = 2020) -> dict:
    return {"domains": domains, "polarity": polarity, "text": text, "year": year}


def _record(
    events: list[dict],
    *,
    raw_id: str = "RF-TEST-000001",
    gender: str = "女",
    birth: str = "1990-01-01 08:00",
) -> dict:
    return {
        "raw_id": raw_id,
        "duplicate_key": raw_id,
        "gender": gender,
        "birth_datetime_raw": birth,
        "calendar_type": "solar",
        "true_solar_time_raw": "",
        "raw_text": "",
        "events": events,
    }


def _label(record: dict, spec: v2.LabelSpec, **kwargs) -> int | None:
    return v2.classify_domain(record, spec, **kwargs)["label"]


@pytest.fixture(scope="module")
def built() -> tuple[dict, list[dict], list[dict]]:
    return v2.build_payload(
        v2.load_source(),
        v1_payload=v2.load_v1(),
        source_path=v2.SOURCE_PATH,
        source_sha256=v2._sha256_file(v2.SOURCE_PATH),
    )


# ---------------------------------------------------------------------------
# 1. 冻结词表
# ---------------------------------------------------------------------------


def test_health_keywords_match_card_section_9() -> None:
    assert v2.SERIOUS_HEALTH_KEYWORDS == (
        "抢救", "ICU", "病危", "癌", "肿瘤", "重病", "大病", "慢性病", "化疗", "放疗",
        "中风", "心脏病", "糖尿病", "肾衰竭", "瘫痪", "失明", "精神病",
    )
    assert "手术" not in v2.SERIOUS_HEALTH_KEYWORDS
    assert "住院" not in v2.SERIOUS_HEALTH_KEYWORDS


def test_debt_keywords_match_card_section_9() -> None:
    assert v2.DEBT_KEYWORDS == (
        "负债", "欠债", "债务", "欠款", "借款", "还债", "资金链", "被执行人", "破产",
    )
    for removed in ("亏损", "被骗", "贷款", "信贷"):
        assert removed not in v2.DEBT_KEYWORDS


def test_filter_tables_frozen() -> None:
    assert v2.KIN_TERMS == (
        "父母", "父亲", "母亲", "爸", "妈", "老公", "老婆", "妻子", "丈夫", "儿子",
        "女儿", "孩子", "家人", "家属", "兄弟", "姐妹", "亲戚", "朋友",
    )
    assert v2.SELF_TERMS == ("我", "本人", "自己")
    assert v2.NEGATION_TERMS == ("无", "没", "没有", "未", "差点", "并非")
    assert v2.NEGATION_WINDOW == 6
    assert v2.HOUSE_TERMS == ("房贷", "按揭", "购房", "买房", "买楼", "供房", "婚房", "房子", "首付")
    assert v2.CHRONIC_KEYWORDS == ("慢性病",)


# ---------------------------------------------------------------------------
# 2. 主体过滤
# ---------------------------------------------------------------------------


def test_family_sentence_is_excluded_and_case_is_null() -> None:
    record = _record([_event(["income"], "父亲生意失败欠债 200 万")])
    result = v2.classify_domain(record, v2.LABEL_SPECS[0])
    assert result["label"] is None
    assert result["null_reason"] == "family_only"
    assert result["verdict_counts"]["excluded_family"] == 1


def test_family_plus_self_is_subject_ambiguous_null() -> None:
    record = _record([_event(["income"], "父亲欠债，我也被拖累了")])
    result = v2.classify_domain(record, v2.LABEL_SPECS[0])
    assert result["label"] is None
    assert result["null_reason"] == "subject_ambiguous"


def test_implicit_subject_is_narrator() -> None:
    record = _record([_event(["income"], "负债累累，走投无路")])
    result = v2.classify_domain(record, v2.LABEL_SPECS[0])
    assert result["label"] == 1
    assert result["hits"][0]["subject"] == "implicit_self"


def test_strict_implicit_null_variant_would_clear_positives() -> None:
    record = _record([_event(["income"], "负债累累")])
    assert v2.classify_domain(record, v2.LABEL_SPECS[0], implicit_is_self=False)["label"] is None


# ---------------------------------------------------------------------------
# 3. 否定过滤（6 字窗口）
# ---------------------------------------------------------------------------


def test_negation_within_window_marks_zero() -> None:
    record = _record([_event(["health"], "健康良好无大病")])
    result = v2.classify_domain(record, v2.LABEL_SPECS[1])
    assert result["label"] == 0
    assert result["basis"] == "negated"


def test_negation_window_boundary_exactly_six_chars() -> None:
    # 否定词落在关键词前第 6 个字符处 → 命中；隔 7 个字符 → 不命中。
    inside = _record([_event(["income"], "甲甲甲甲甲无负债")])
    outside = _record([_event(["income"], "无甲甲甲甲甲甲负债")])
    assert v2.classify_domain(inside, v2.LABEL_SPECS[0])["label"] == 0
    assert v2.classify_domain(outside, v2.LABEL_SPECS[0])["label"] == 1


def test_negated_is_zero_not_null() -> None:
    record = _record([_event(["income"], "没有债务")])
    result = v2.classify_domain(record, v2.LABEL_SPECS[0])
    assert result["label"] == 0
    assert result["null_reason"] is None


# ---------------------------------------------------------------------------
# 4. 房贷 / 阳性优先
# ---------------------------------------------------------------------------


def test_mortgage_sentence_excluded_and_null() -> None:
    record = _record([_event(["income"], "买房背上了负债")])
    result = v2.classify_domain(record, v2.LABEL_SPECS[0])
    assert result["label"] is None
    assert result["null_reason"] == "mortgage_only"
    assert result["hits"][0]["mortgage_terms"] == ["买房"]


def test_positive_beats_family_hit() -> None:
    record = _record(
        [
            _event(["income"], "父亲欠债"),
            _event(["income"], "信用卡负债 10 万"),
        ]
    )
    assert _label(record, v2.LABEL_SPECS[0]) == 1


def test_positive_beats_negated_hit() -> None:
    record = _record(
        [
            _event(["income"], "无负债"),
            _event(["income"], "后来创业负债 50 万"),
        ]
    )
    assert _label(record, v2.LABEL_SPECS[0]) == 1


# ---------------------------------------------------------------------------
# 5. health 严重度 / 慢性病单列
# ---------------------------------------------------------------------------


def test_removed_severity_words_do_not_hit() -> None:
    for text in ("做了个小手术", "住院一周"):
        record = _record([_event(["health"], text)])
        result = v2.classify_domain(record, v2.LABEL_SPECS[1])
        assert result["label"] == 0
        assert result["basis"] == "no_hit"


def test_kept_severity_words_hit() -> None:
    record = _record([_event(["health"], "确诊癌症")])
    assert _label(record, v2.LABEL_SPECS[1]) == 1


def test_chronic_only_flag() -> None:
    record = _record([_event(["health"], "慢性病多年")])
    result = v2.classify_domain(record, v2.LABEL_SPECS[1])
    assert result["label"] == 1
    assert v2.has_chronic_only(result["hits"]) is True


# ---------------------------------------------------------------------------
# 6. null 语义
# ---------------------------------------------------------------------------


def test_no_domain_event_is_null() -> None:
    record = _record([_event(["occupation"], "升职")])
    assert _label(record, v2.LABEL_SPECS[0]) is None
    assert _label(record, v2.LABEL_SPECS[1]) is None


def test_all_question_is_null() -> None:
    record = _record([_event(["income"], "什么时候能还清负债？")])
    result = v2.classify_domain(record, v2.LABEL_SPECS[0])
    assert result["label"] is None
    assert result["null_reason"] == "all_question"


def test_null_not_folded_in_built_counts(built: tuple[dict, list[dict], list[dict]]) -> None:
    payload = built[0]
    for spec in v2.LABEL_SPECS:
        block = payload["counts"][spec.key]
        assert block["null"] > 0
        assert block["1"] + block["0"] + block["null"] == block["sum"] == payload["counts"]["base_sample"]
        ready = block["chart_ready"]
        assert ready["1"] + ready["0"] + ready["null"] == ready["sum"] == payload["counts"]["base_chart_ready"]


# ---------------------------------------------------------------------------
# 7. 漏斗与差异
# ---------------------------------------------------------------------------


def test_funnel_and_base_invariants(built: tuple[dict, list[dict], list[dict]]) -> None:
    counts = built[0]["counts"]
    assert counts["records_total"] == 992
    assert counts["after_dedupe"] == 959
    assert counts["with_gender"] == 950
    assert counts["birth_date_parsable"] == 952
    assert counts["birth_time_parsable"] == 947
    assert counts["base_sample"] == 944
    assert counts["base_chart_ready"] == 940


def test_v1_diff_sums_balance(built: tuple[dict, list[dict], list[dict]]) -> None:
    _payload, cases, _excluded = built
    diff = _payload["audit"]["v1_diff"]
    for spec in v2.LABEL_SPECS:
        item = diff[spec.key]
        assert item["lost"] == item["v1_positive"] - item["v2_positive"]
        assert sum(item["reasons"].values()) == item["lost"]
        assert len(item["cases"]) == item["lost"]
        assert item["v2_positive"] == sum(1 for row in cases if row["labels"][spec.key] == 1)


def test_filtered_hits_are_not_counted_as_positive_keyword_hits(
    built: tuple[dict, list[dict], list[dict]],
) -> None:
    payload = built[0]
    for spec in v2.LABEL_SPECS:
        events = payload["audit"]["keyword_hits"][spec.key]["events"]
        cases = payload["audit"]["keyword_hits"][spec.key]["cases"]
        for keyword in spec.keywords:
            assert events[keyword] >= cases[keyword]


# ---------------------------------------------------------------------------
# 8. 门槛
# ---------------------------------------------------------------------------


def test_gate_is_frozen_as_failed(built: tuple[dict, list[dict], list[dict]]) -> None:
    gate = built[0]["gate"]
    assert gate["failed"] is True
    assert gate["stop"] is True
    assert gate["verdict"] == "labels_not_suitable_for_adjudication"
    assert "标签不适合作裁决" in gate["verdict_text"]
    assert gate["false_positive_rates"] == {"debt": 18.18, "serious_health": 36.36}
    assert gate["error_rates"] == {"debt": 27.27, "serious_health": 40.91}
    residual = built[0]["audit"]["known_residual"]
    assert residual["per_label"]["debt"]["false_positive"] == 4
    assert residual["per_label"]["serious_health"]["false_positive"] == 8
    assert residual["per_label"]["debt"]["false_negative"] == 2
    assert residual["per_label"]["serious_health"]["false_negative"] == 1


def test_known_residual_and_missed_reproduce(built: tuple[dict, list[dict], list[dict]]) -> None:
    _payload, cases, _excluded = built
    v2.check_known_residual(cases)
    v2.check_missed(cases)
    v2.check_audit_samples(cases)


# ---------------------------------------------------------------------------
# 9. 泄漏 / 确定性 / v1 隔离
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
    leaked = []
    for path in _walk_keys(built[0]):
        key = path.rsplit(".", 1)[-1].split("[", 1)[0].lower()
        if key == "chart_ready":
            continue
        if any(token in key for token in FORBIDDEN_KEYS):
            leaked.append(path)
    assert leaked == []


def test_case_fields_are_frozen_contract(built: tuple[dict, list[dict], list[dict]]) -> None:
    for case in built[0]["cases"]:
        assert set(case) == {
            "case_id", "gender", "birth_datetime_raw", "birth_dt", "time_basis",
            "chart_ready", "labels", "label_basis", "hits", "evidence_events",
        }
        assert set(case["labels"]) == {"debt", "serious_health"}


def test_source_has_no_chart_or_engine_tokens() -> None:
    stripped = SOURCE_CODE.replace("chart_ready", "").lower()
    leaked = [token for token in FORBIDDEN_SOURCE_TOKENS if token in stripped]
    assert leaked == []


def test_v2_does_not_modify_v1() -> None:
    v1_payload = v2.load_v1()
    assert v1_payload["payload_sha256"] == V1_PAYLOAD_SHA256
    assert v1_payload["counts"]["debt"]["1"] == 49
    assert v1_payload["counts"]["serious_health"]["1"] == 131
    assert v1_artifact_matches(v1_payload)


def v1_artifact_matches(v1_payload: dict) -> bool:
    """v1 JSON 的 payload_sha256 必须与其内容一致（未被写坏）。"""
    material = {key: value for key, value in v1_payload.items() if key != "payload_sha256"}
    digest = hashlib.sha256(
        json.dumps(material, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return digest == v1_payload["payload_sha256"]


def test_two_builds_are_identical(built: tuple[dict, list[dict], list[dict]]) -> None:
    second, _cases, _excluded = v2.build_payload(
        v2.load_source(),
        v1_payload=v2.load_v1(),
        source_path=v2.SOURCE_PATH,
        source_sha256=v2._sha256_file(v2.SOURCE_PATH),
    )
    first = built[0]
    assert json.dumps(first, ensure_ascii=False, sort_keys=True) == json.dumps(
        second, ensure_ascii=False, sort_keys=True
    )
    material = {key: value for key, value in first.items() if key != "payload_sha256"}
    digest = hashlib.sha256(
        json.dumps(material, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    assert digest == first["payload_sha256"]
    assert "gate" in material


def test_artifacts_match_current_build(built: tuple[dict, list[dict], list[dict]]) -> None:
    payload, cases, _excluded = built
    on_disk = v2.JSON_PATH.read_text(encoding="utf-8")
    assert on_disk == json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    rendered_payload = dict(payload)
    rendered_payload["_cases"] = cases
    assert v2.REPORT_PATH.read_text(encoding="utf-8") == v2.render_report(rendered_payload)
    assert not {"generated_at", "run_at", "timestamp"} & set(payload)

"""T-158 §9 · 财富 / 健康结局标签 v2（主体 / 否定 / 房贷 / 严重度过滤）。

在 v1（``META/domain-labels-wealth-health-v1.json``，只读）之上按中枢裁决重建标签：

* 主体过滤：关键词所在**句**含亲属称谓（``KIN_TERMS``）且不含 ``我/本人/自己`` → 排除；
  含亲属**又**含我/本人/自己 → 主体不明 → 该证据不可用（案例落 ``null``，不猜）。
* 否定过滤：关键词**前 6 个字**内出现 ``无/没/没有/未/差点/并非`` → 该命中记为否定证据（案例落 ``0``）。
* health 严重度：删 ``手术`` / ``住院``；保留 ``抢救/ICU/病危/癌/肿瘤/重病/大病/化疗/放疗/中风/
  心脏病/糖尿病/肾衰竭/瘫痪/失明/精神病``；``慢性病`` 保留但单列报数。
* debt 词表：删 ``亏损`` / ``被骗``（损失不是债务）；房贷 / 购房贷款 / 按揭默认排除并单列；
  保留 ``负债/欠债/债务/欠款/借款/还债/资金链/被执行人/破产``。
* ``null`` = **无可用证据**（无该域事件 / 全是提问 / 空文本 / 命中全被主体过滤），不折 0、不折 1。

本模块不改 v1 产物、不改 JSONL、不建盘、不评分。用法::

    python -m tools.domain_labels_wealth_health_v2

退出码：0 通过；2 数据源或 v1 产物不可读；3 计数不变量不复现（拒绝落盘）；
4 人工核查（已知误判 / 20 例抽查）与当前数据不符，需重审。

口径说明（写进产物 ``definition``，中枢可复核）：

* 中文叙述普遍零主语；本版把「句内无亲属称谓」视为**叙述者本人**（整份反馈是第一人称自述，
  v1 同样按命主事件解读）。若把零主语也当「主体不明 → null」，v2 阳性会掉到 debt 1 例 /
  serious_health 0 例（见报告 §6「敏感性」），标签无法使用。该假设由中枢拍板；替换只需一个开关。
* 亲属词表严格按卡 §9.2 原文，不擅自扩展；祖辈 / 姻亲（姥爷/姥姥/爷爷/奶奶/外公/外婆/婆婆/公公）
  未在词表内，其命中会残留为误判——报告 §6 给出扩展后的敏感性数字。
* 房贷判定：关键词所在句含 ``房贷/按揭/购房/买房/买楼/供房/婚房/房子/首付`` 之一 → 排除并单列。
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from tools.domain_labels_wealth_health import (
    dedupe_records,
    load_source,
    question_markers_in,
    summarise_text,
)
from tools.timing_eval_set import resolve_birth

ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = ROOT / "cases" / "raw_feedback" / "parsed" / "real_cases_990.jsonl"
V1_PATH = ROOT / "META" / "domain-labels-wealth-health-v1.json"
JSON_PATH = ROOT / "META" / "domain-labels-wealth-health-v2.json"
REPORT_PATH = ROOT / "META" / "domain-labels-wealth-health-v2.md"

SCHEMA = "domain-labels-wealth-health/v2"
V1_SCHEMA = "domain-labels-wealth-health/v1"
TASK = "T-158"
SCRIPT = "tools/domain_labels_wealth_health_v2.py"
FROZEN_AT = "2026-10-29"

GENDERS = ("男", "女")

# 卡 §9.2.4：debt 保留词（贷款 / 信贷 / 亏损 / 被骗 已删）。
DEBT_KEYWORDS = ("负债", "欠债", "债务", "欠款", "借款", "还债", "资金链", "被执行人", "破产")
# 卡 §9.2.3：health 保留词（手术 / 住院 已删）。
SERIOUS_HEALTH_KEYWORDS = (
    "抢救", "ICU", "病危", "癌", "肿瘤", "重病", "大病", "慢性病", "化疗", "放疗", "中风",
    "心脏病", "糖尿病", "肾衰竭", "瘫痪", "失明", "精神病",
)
# 保留但单列报数（卡 §9.2.3）。
CHRONIC_KEYWORDS = ("慢性病",)

# 卡 §9.2.1 主体词表，原样冻结。
KIN_TERMS = (
    "父母", "父亲", "母亲", "爸", "妈", "老公", "老婆", "妻子", "丈夫", "儿子", "女儿", "孩子",
    "家人", "家属", "兄弟", "姐妹", "亲戚", "朋友",
)
SELF_TERMS = ("我", "本人", "自己")

# 卡 §9.2.2 否定词，窗口 = 关键词前 6 字。
NEGATION_TERMS = ("无", "没", "没有", "未", "差点", "并非")
NEGATION_WINDOW = 6

# 卡 §9.2.4 房贷 / 购房贷款 / 按揭默认排除。
HOUSE_TERMS = ("房贷", "按揭", "购房", "买房", "买楼", "供房", "婚房", "房子", "首付")

# 敏感性：若把祖辈 / 姻亲也纳入主体词表（**不改本版标签**，只报数）。
EXTENDED_KIN_TERMS = (
    "姥爷", "姥姥", "爷爷", "奶奶", "外公", "外婆", "婆婆", "公公", "岳父", "岳母",
)

QUESTION_MARKERS = ("？", "?", "是否", "能否", "请问", "怎么样", "吗", "么", "呢")

SENTENCE_SPLIT = re.compile(r"[。！？；!?\n;]")
TEXT_SUMMARY_LIMIT = 120

# 计数不变量（与 v1 同一数据源；任一不复现 → 拒绝落盘）。
EXPECTED_COUNTS = {
    "records_total": 992,
    "after_dedupe": 959,
    "with_gender": 950,
    "birth_date_parsable": 952,
    "birth_time_parsable": 947,
    "base_sample": 944,
    "base_chart_ready": 940,
}
EXPECTED_DOMAIN = {
    "debt": {"cases": 377, "events": 606},
    "serious_health": {"cases": 453, "events": 659},
}

SOURCE_KEYS = (
    "raw_id",
    "duplicate_key",
    "gender",
    "birth_datetime_raw",
    "calendar_type",
    "true_solar_time_raw",
    "raw_text",
    "events",
)


@dataclass(frozen=True)
class LabelSpec:
    key: str
    domain: str
    keywords: tuple[str, ...]


LABEL_SPECS = (
    LabelSpec("debt", "income", DEBT_KEYWORDS),
    LabelSpec("serious_health", "health", SERIOUS_HEALTH_KEYWORDS),
)


class SourceError(RuntimeError):
    """数据源或 v1 产物不可读。"""


class LabelInvariantError(RuntimeError):
    """计数不变量不复现。"""


class AuditError(RuntimeError):
    """人工核查清单与当前数据不符。"""


# ---------------------------------------------------------------------------
# 文本判定
# ---------------------------------------------------------------------------


def split_sentences(text: str) -> list[str]:
    """按句末标点 / 换行切句；空句丢弃。"""
    return [chunk.strip() for chunk in SENTENCE_SPLIT.split(text) if chunk.strip()]


def markers_in(text: str, markers: Sequence[str]) -> list[str]:
    return [marker for marker in markers if marker in text]


def classify_occurrences(
    text: str, spec: LabelSpec, *, implicit_is_self: bool = True
) -> list[dict[str, Any]]:
    """切句后逐关键词出现位置判定主体 / 否定 / 房贷。"""
    occurrences: list[dict[str, Any]] = []
    for sentence in split_sentences(text):
        kin = markers_in(sentence, KIN_TERMS)
        self_terms = markers_in(sentence, SELF_TERMS)
        if kin and not self_terms:
            subject = "family"
        elif kin:
            subject = "ambiguous"
        else:
            subject = "implicit_self" if implicit_is_self else "ambiguous"
        for keyword in spec.keywords:
            start = 0
            while True:
                index = sentence.find(keyword, start)
                if index < 0:
                    break
                start = index + len(keyword)
                window = sentence[max(0, index - NEGATION_WINDOW):index]
                negations = markers_in(window, NEGATION_TERMS)
                houses = markers_in(sentence, HOUSE_TERMS) if spec.key == "debt" else []
                if subject == "family":
                    verdict = "excluded_family"
                elif subject == "ambiguous":
                    verdict = "excluded_ambiguous"
                elif negations:
                    verdict = "negated"
                elif houses:
                    verdict = "excluded_mortgage"
                else:
                    verdict = "positive"
                occurrences.append(
                    {
                        "keyword": keyword,
                        "subject": subject,
                        "negated_by": negations,
                        "mortgage_terms": houses,
                        "verdict": verdict,
                        "sentence": summarise_text(sentence, 90),
                    }
                )
    return occurrences


def domain_events(record: Mapping[str, Any], spec: LabelSpec) -> list[Mapping[str, Any]]:
    return [event for event in record["events"] if spec.domain in (event.get("domains") or [])]


def classify_domain(
    record: Mapping[str, Any], spec: LabelSpec, *, implicit_is_self: bool = True
) -> dict[str, Any]:
    """按 v2 规则给单例单域打标。"""
    events = domain_events(record, spec)
    entries: list[dict[str, Any]] = []
    counts = {"question": 0, "empty": 0, "evidence": 0}
    occurrences: list[dict[str, Any]] = []

    for event in events:
        text = event.get("text") or ""
        if not text.strip():
            verdict = "empty"
        elif question_markers_in(text):
            verdict = "question"
        else:
            verdict = "evidence"
        counts[verdict] += 1
        entries.append(
            {
                "year": event.get("year"),
                "polarity": event.get("polarity"),
                "verdict": verdict,
                "text": summarise_text(text, TEXT_SUMMARY_LIMIT),
            }
        )
        if verdict == "evidence":
            for occurrence in classify_occurrences(text, spec, implicit_is_self=implicit_is_self):
                occurrence["year"] = event.get("year")
                occurrence["polarity"] = event.get("polarity")
                occurrences.append(occurrence)

    verdict_counts = {
        name: sum(1 for item in occurrences if item["verdict"] == name)
        for name in ("positive", "negated", "excluded_family", "excluded_ambiguous", "excluded_mortgage")
    }

    if verdict_counts["positive"]:
        label: int | None = 1
        basis = "positive"
        null_reason = None
    elif verdict_counts["negated"]:
        label = 0
        basis = "negated"
        null_reason = None
    elif occurrences:
        label = None
        basis = "excluded"
        if verdict_counts["excluded_ambiguous"]:
            null_reason = "subject_ambiguous"
        elif verdict_counts["excluded_family"] and verdict_counts["excluded_mortgage"]:
            null_reason = "family_and_mortgage"
        elif verdict_counts["excluded_family"]:
            null_reason = "family_only"
        else:
            null_reason = "mortgage_only"
    elif counts["evidence"]:
        label = 0
        basis = "no_hit"
        null_reason = None
    elif events:
        label = None
        basis = "no_evidence"
        null_reason = "all_question" if counts["question"] else "no_text"
    else:
        label = None
        basis = "no_evidence"
        null_reason = "no_domain_event"

    return {
        "label": label,
        "basis": basis,
        "null_reason": null_reason,
        "events_total": len(events),
        "events_question": counts["question"],
        "events_empty_text": counts["empty"],
        "events_evidence": counts["evidence"],
        "verdict_counts": verdict_counts,
        "hits": [
            {key: value for key, value in item.items() if key in (
                "keyword", "subject", "negated_by", "mortgage_terms", "verdict", "sentence", "year", "polarity"
            )}
            for item in occurrences
        ],
        "entry_events": entries,
    }


def has_chronic_only(hits: Sequence[Mapping[str, Any]]) -> bool:
    """阳性是否只由「慢性病」触发（单列报数用）。"""
    positive = [hit for hit in hits if hit["verdict"] == "positive"]
    return bool(positive) and all(hit["keyword"] in CHRONIC_KEYWORDS for hit in positive)


# ---------------------------------------------------------------------------
# 构建
# ---------------------------------------------------------------------------


def build_case(record: Mapping[str, Any], birth: Mapping[str, Any]) -> dict[str, Any]:
    labels: dict[str, int | None] = {}
    bases: dict[str, str] = {}
    hits: list[dict[str, Any]] = []
    events: list[dict[str, Any]] = []
    for spec in LABEL_SPECS:
        result = classify_domain(record, spec)
        labels[spec.key] = result["label"]
        bases[spec.key] = result["basis"]
        hits.extend({"label_key": spec.key, "domain": spec.domain, **hit} for hit in result["hits"])
        events.extend(
            {"label_key": spec.key, "domain": spec.domain, **entry} for entry in result["entry_events"]
        )
    return {
        "case_id": record["raw_id"],
        "gender": record["gender"],
        "birth_datetime_raw": record["birth_datetime_raw"],
        "birth_dt": birth["dt"].isoformat(sep=" "),
        "time_basis": birth["time_basis"],
        "chart_ready": bool(birth["has_time"]),
        "labels": labels,
        "label_basis": bases,
        "hits": hits,
        "evidence_events": events,
    }


def _exclusion_reasons(record: Mapping[str, Any], birth: Mapping[str, Any]) -> list[str]:
    reasons: list[str] = []
    if record["gender"] not in GENDERS:
        reasons.append("missing_gender")
    if not birth["ok"]:
        reasons.append(str(birth["reason"]).split(":")[0])
    return reasons


def _section(rows: Sequence[dict[str, Any]], key: str) -> dict[str, int]:
    values = [row["labels"][key] for row in rows]
    return {
        "1": sum(1 for value in values if value == 1),
        "0": sum(1 for value in values if value == 0),
        "null": sum(1 for value in values if value is None),
        "sum": len(values),
    }


def _rate(positive: int, sample_size: int) -> float | None:
    if not sample_size:
        return None
    return round(positive * 100.0 / sample_size, 2)


def build_payload(
    records: Sequence[Mapping[str, Any]],
    *,
    v1_payload: Mapping[str, Any],
    source_path: Path = SOURCE_PATH,
    source_sha256: str,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    unique, duplicate_groups, duplicate_removed = dedupe_records(records)
    cases: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    with_gender = birth_ok = birth_time = 0

    for record in unique:
        birth = resolve_birth(dict(record))
        if record["gender"] in GENDERS:
            with_gender += 1
        if birth["ok"]:
            birth_ok += 1
            if birth["has_time"]:
                birth_time += 1
        reasons = _exclusion_reasons(record, birth)
        if reasons:
            excluded.append({"case_id": record["raw_id"], "reasons": reasons})
            continue
        case = build_case(record, birth)
        case["_record"] = record
        cases.append(case)

    cases.sort(key=lambda item: item["case_id"])
    excluded.sort(key=lambda item: item["case_id"])
    chart_ready_rows = [row for row in cases if row["chart_ready"]]

    counts: dict[str, Any] = {
        "records_total": len(records),
        "after_dedupe": len(unique),
        "with_gender": with_gender,
        "birth_date_parsable": birth_ok,
        "birth_time_parsable": birth_time,
        "base_sample": len(cases),
        "base_chart_ready": len(chart_ready_rows),
        "duplicate_groups": duplicate_groups,
        "duplicate_records_removed": duplicate_removed,
    }

    v1_cases = {case["case_id"]: case for case in v1_payload["cases"]}
    v1_labels = {case_id: case["labels"] for case_id, case in v1_cases.items()}

    labels_block: dict[str, Any] = {}
    baseline: dict[str, Any] = {}
    audit: dict[str, Any] = {
        "domain": {},
        "keyword_hits": {},
        "question": {},
        "filters": {},
        "null_reasons": {},
        "zero_reasons": {},
        "chronic": {},
        "v1_diff": {},
        "sensitivity": {},
        "base_excluded": {},
    }

    for spec in LABEL_SPECS:
        base_bucket = _section(cases, spec.key)
        ready_bucket = _section(chart_ready_rows, spec.key)
        counts[spec.key] = {**base_bucket, "chart_ready": ready_bucket}

        null_reasons = {
            name: 0
            for name in (
                "no_domain_event", "all_question", "no_text",
                "family_only", "subject_ambiguous", "mortgage_only", "family_and_mortgage",
            )
        }
        zero_reasons = {"negated": 0, "no_hit": 0}
        filter_counts = {
            "positive": 0, "negated": 0, "excluded_family": 0,
            "excluded_ambiguous": 0, "excluded_mortgage": 0,
        }
        filter_cases = {name: 0 for name in filter_counts}
        keyword_event_hits = {keyword: 0 for keyword in spec.keywords}
        keyword_case_hits = {keyword: 0 for keyword in spec.keywords}
        chronic_positive_cases = 0
        chronic_positive_hits = 0

        for row in cases:
            result = classify_domain(row["_record"], spec)
            for name, number in result["verdict_counts"].items():
                filter_counts[name] += number
                filter_cases[name] += 1 if number else 0
            if result["label"] is None:
                null_reasons[result["null_reason"]] += 1
            elif result["label"] == 0:
                zero_reasons[result["basis"]] += 1
            seen_keywords: set[str] = set()
            for hit in result["hits"]:
                if hit["verdict"] != "positive":
                    continue
                keyword_event_hits[hit["keyword"]] += 1
                seen_keywords.add(hit["keyword"])
            for keyword in seen_keywords:
                keyword_case_hits[keyword] += 1
            if "positive" in result["verdict_counts"] and result["verdict_counts"]["positive"]:
                if has_chronic_only(result["hits"]):
                    chronic_positive_cases += 1
                chronic_positive_hits += sum(
                    1 for hit in result["hits"] if hit["verdict"] == "positive" and hit["keyword"] in CHRONIC_KEYWORDS
                )

        ready_positives = ready_bucket["1"]
        ready_negatives = ready_bucket["0"]
        labels_block[spec.key] = {
            "domain": spec.domain,
            "keywords": list(spec.keywords),
            "null_reasons": null_reasons,
            "zero_reasons": zero_reasons,
        }
        baseline[spec.key] = {
            "chart_ready": {
                "sample_size": ready_positives + ready_negatives,
                "positive": ready_positives,
                "negative": ready_negatives,
                "positive_rate_pct": _rate(ready_positives, ready_positives + ready_negatives),
            },
            "base_reference": {
                "sample_size": base_bucket["1"] + base_bucket["0"],
                "positive": base_bucket["1"],
                "negative": base_bucket["0"],
                "positive_rate_pct": _rate(base_bucket["1"], base_bucket["1"] + base_bucket["0"]),
            },
            "null_share_pct": {
                "base": _rate(base_bucket["null"], base_bucket["sum"]),
                "chart_ready": _rate(ready_bucket["null"], ready_bucket["sum"]),
            },
        }
        audit["domain"][spec.key] = _domain_audit(unique, spec)
        audit["keyword_hits"][spec.key] = {
            "events": keyword_event_hits,
            "cases": keyword_case_hits,
        }
        audit["question"][spec.key] = _question_audit(unique, spec)
        audit["filters"][spec.key] = {
            "occurrences": filter_counts,
            "cases_with_occurrence": filter_cases,
        }
        audit["null_reasons"][spec.key] = null_reasons
        audit["zero_reasons"][spec.key] = zero_reasons
        audit["chronic"][spec.key] = {
            "positive_cases": chronic_positive_cases,
            "positive_hits": chronic_positive_hits,
        }
        audit["v1_diff"][spec.key] = _v1_diff(cases, v1_labels, spec)

    strict = _strict_variant(cases)
    audit["sensitivity"]["strict_implicit_null"] = strict
    audit["sensitivity"]["extended_kin"] = _extended_kin_variant(cases, counts)
    audit["known_residual"] = _known_residual_summary(cases)

    exclusion_counts: dict[str, int] = {}
    for item in excluded:
        key = "+".join(item["reasons"])
        exclusion_counts[key] = exclusion_counts.get(key, 0) + 1
    audit["base_excluded"] = {
        "total": len(excluded),
        "by_reason": dict(sorted(exclusion_counts.items())),
    }

    payload: dict[str, Any] = {
        "schema": SCHEMA,
        "task": TASK,
        "script": SCRIPT,
        "frozen_at": FROZEN_AT,
        "definition": _definition_block(),
        "source": {
            "path": source_path.relative_to(ROOT).as_posix(),
            "sha256": source_sha256,
            "records": len(records),
            "v1": {
                "path": V1_PATH.relative_to(ROOT).as_posix(),
                "sha256": _sha256_file(V1_PATH),
                "payload_sha256": v1_payload.get("payload_sha256"),
            },
        },
        "counts": counts,
        "labels": labels_block,
        "baseline": baseline,
        "audit": audit,
        "excluded_records": excluded,
        "cases": [{key: value for key, value in row.items() if key != "_record"} for row in cases],
    }
    payload["gate"] = build_gate(payload)
    material = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    payload["payload_sha256"] = hashlib.sha256(material.encode("utf-8")).hexdigest()
    return payload, cases, excluded


def _domain_audit(records: Sequence[Mapping[str, Any]], spec: LabelSpec) -> dict[str, Any]:
    polarity = {"negative": 0, "positive": 0, "unknown": 0, "other": 0}
    total = question = empty = evidence = 0
    cases_with_events = 0
    for record in records:
        events = domain_events(record, spec)
        if events:
            cases_with_events += 1
        for event in events:
            total += 1
            raw_polarity = event.get("polarity")
            polarity[raw_polarity if raw_polarity in polarity else "other"] += 1
            text = event.get("text") or ""
            if not text.strip():
                empty += 1
            elif question_markers_in(text):
                question += 1
            else:
                evidence += 1
    return {
        "domain": spec.domain,
        "cases_with_domain_events": cases_with_events,
        "events_total": total,
        "events_question": question,
        "events_empty_text": empty,
        "events_evidence": evidence,
        "polarity_events": polarity,
    }


def _question_audit(records: Sequence[Mapping[str, Any]], spec: LabelSpec) -> dict[str, Any]:
    markers = {marker: 0 for marker in QUESTION_MARKERS}
    suppressed = []
    for record in records:
        for event in domain_events(record, spec):
            text = event.get("text") or ""
            found = markers_in(text, QUESTION_MARKERS)
            if not found:
                continue
            for marker in found:
                markers[marker] += 1
            hits = markers_in(text, spec.keywords)
            if hits:
                suppressed.append(
                    {
                        "case_id": record["raw_id"],
                        "year": event.get("year"),
                        "polarity": event.get("polarity"),
                        "markers": list(found),
                        "keywords": hits,
                        "text": summarise_text(text, 100),
                    }
                )
    suppressed.sort(key=lambda item: (item["case_id"], item["year"] if item["year"] is not None else 0))
    keyword_counts = {keyword: 0 for keyword in spec.keywords}
    for item in suppressed:
        for keyword in item["keywords"]:
            keyword_counts[keyword] += 1
    return {
        "markers": markers,
        "suppressed_events": len(suppressed),
        "suppressed_cases": len({item["case_id"] for item in suppressed}),
        "suppressed_keywords": keyword_counts,
        "suppressed": suppressed,
    }


def _v1_diff(
    cases: Sequence[dict[str, Any]], v1_labels: Mapping[str, Mapping[str, int | None]], spec: LabelSpec
) -> dict[str, Any]:
    """v1 阳性 → v2 非阳性的流失归因（每条过滤各删多少）。"""
    reasons = {
        "removed_keyword_only": 0,
        "subject_family": 0,
        "subject_ambiguous": 0,
        "mortgage": 0,
        "negation": 0,
    }
    removed_keywords: dict[str, int] = {}
    cases_lost: list[dict[str, Any]] = []
    for row in cases:
        if v1_labels.get(row["case_id"], {}).get(spec.key) != 1:
            continue
        if row["labels"][spec.key] == 1:
            continue
        result = classify_domain(row["_record"], spec)
        v1_only = {"亏损", "被骗", "贷款", "信贷"} if spec.key == "debt" else {"手术", "住院"}
        full_text = " ".join(
            (event.get("text") or "") for event in domain_events(row["_record"], spec)
        )
        v1_hit_keywords = {keyword for keyword in v1_only if keyword in full_text}
        v2_keywords = {hit["keyword"] for hit in result["hits"]}
        if not v2_keywords:
            reason = "removed_keyword_only"
        elif result["verdict_counts"]["excluded_family"]:
            reason = "subject_family"
        elif result["verdict_counts"]["excluded_ambiguous"]:
            reason = "subject_ambiguous"
        elif result["verdict_counts"]["excluded_mortgage"]:
            reason = "mortgage"
        elif result["verdict_counts"]["negated"]:
            reason = "negation"
        else:
            reason = "unexplained"
        reasons[reason] = reasons.get(reason, 0) + 1
        if reason == "removed_keyword_only":
            for keyword in sorted(v1_hit_keywords):
                removed_keywords[keyword] = removed_keywords.get(keyword, 0) + 1
        cases_lost.append(
            {
                "case_id": row["case_id"],
                "reason": reason,
                "v1_hit_keywords": sorted(v1_hit_keywords),
                "v2_hits": [
                    {"keyword": hit["keyword"], "verdict": hit["verdict"]} for hit in result["hits"]
                ],
            }
        )
    return {
        "v1_positive": sum(1 for labels in v1_labels.values() if labels.get(spec.key) == 1),
        "v2_positive": sum(1 for row in cases if row["labels"][spec.key] == 1),
        "lost": len(cases_lost),
        "reasons": dict(sorted(reasons.items())),
        "removed_keywords": dict(sorted(removed_keywords.items())),
        "cases": cases_lost,
    }


def _strict_variant(cases: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """敏感性：把零主语也当「主体不明 → null」，阳性会剩多少。"""
    result: dict[str, Any] = {}
    for spec in LABEL_SPECS:
        labels = [
            classify_domain(row["_record"], spec, implicit_is_self=False)["label"] for row in cases
        ]
        positive = sum(1 for label in labels if label == 1)
        result[spec.key] = {
            "1": positive,
            "0": sum(1 for label in labels if label == 0),
            "null": sum(1 for label in labels if label is None),
            "sum": len(labels),
            "positive_rate_pct": _rate(positive, positive + sum(1 for label in labels if label == 0)),
        }
    return result


def _extended_kin_variant(cases: Sequence[dict[str, Any]], counts: Mapping[str, Any]) -> dict[str, Any]:
    """敏感性：若把祖辈 / 姻亲也纳入主体词表，会掉哪些阳性（不改本版标签）。"""
    result: dict[str, Any] = {}
    for spec in LABEL_SPECS:
        lost: list[str] = []
        kept: list[str] = []
        for row in cases:
            if row["labels"][spec.key] != 1:
                continue
            dropped = False
            for hit in row["hits"]:
                if hit["label_key"] != spec.key or hit["verdict"] != "positive":
                    continue
                sentence = hit["sentence"]
                if markers_in(sentence, EXTENDED_KIN_TERMS) and not markers_in(sentence, SELF_TERMS):
                    dropped = True
            if dropped:
                lost.append(row["case_id"])
            else:
                kept.append(row["case_id"])
        result[spec.key] = {
            "extended_terms": list(EXTENDED_KIN_TERMS),
            "positives_before": len(lost) + len(kept),
            "positives_after": len(kept),
            "removed": sorted(lost),
        }
    return result


def _known_residual_summary(cases: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """已识别的 v2 残留误判（假阳性 / 假阴性）与误判率。"""
    per_label: dict[str, dict[str, Any]] = {}
    for spec in LABEL_SPECS:
        positives = sum(1 for row in cases if row["labels"][spec.key] == 1)
        false_positive = [item for item in KNOWN_RESIDUAL if item[0] == spec.key]
        false_negative = [item for item in KNOWN_MISSED if item[0] == spec.key]
        fp_types: dict[str, int] = {}
        for _key, kind, _case_id, _keyword, _phenomenon, _verdict in false_positive:
            fp_types[kind] = fp_types.get(kind, 0) + 1
        fn_types: dict[str, int] = {}
        for _key, kind, _case_id, _keyword, _phenomenon, _verdict in false_negative:
            fn_types[kind] = fn_types.get(kind, 0) + 1
        per_label[spec.key] = {
            "positives": positives,
            "false_positive": len(false_positive),
            "false_positive_rate_pct": _rate(len(false_positive), positives),
            "false_negative": len(false_negative),
            "false_negative_rate_pct": _rate(len(false_negative), positives),
            "error_rate_pct": _rate(len(false_positive) + len(false_negative), positives),
            "false_positive_types": dict(sorted(fp_types.items())),
            "false_negative_types": dict(sorted(fn_types.items())),
        }
    gate_failed = any(
        item["false_positive_rate_pct"] is not None and item["false_positive_rate_pct"] > 20.0
        for item in per_label.values()
    )
    error_gate_failed = any(
        item["error_rate_pct"] is not None and item["error_rate_pct"] > 20.0
        for item in per_label.values()
    )
    return {
        "per_label": per_label,
        "gate_threshold_pct": 20.0,
        "gate_metric": "false_positive_rate_pct（沿用 v1 口径：误判=假阳性）",
        "gate_failed": gate_failed,
        "error_gate_failed_including_missed": error_gate_failed,
        "verdict": "labels_not_suitable_for_adjudication" if (gate_failed or error_gate_failed)
        else "gate_passed",
    }


def _definition_block() -> dict[str, Any]:
    return {
        "supersedes": V1_SCHEMA,
        "authority": "tasks/T-158/PROMPT.md §9（中枢裁决 2026-10-29）",
        "unit": "case（原始 JSONL 一条反馈）",
        "dedupe": "duplicate_key 全等去重，保留首次出现",
        "base_filter": ["gender ∈ {男, 女}", "birth_datetime_raw 可解析出公历日期"],
        "chart_ready": "出生时刻可解析（clock_beijing 或 true_solar）；只标记，不建盘",
        "question_rule": "事件文本含提问标记任一 → 整段不作证据（沿用 v1）",
        "subject_filter": {
            "unit": "句（按 。！？；!? 换行 切句）",
            "kin_terms": list(KIN_TERMS),
            "self_terms": list(SELF_TERMS),
            "rule": "含亲属称谓且不含我/本人/自己 → 排除；两者都含 → 主体不明 → 案例 null",
            "implicit_subject": "句内无亲属称谓 → 视为叙述者本人（第一人称自述；可切换为 null，见 sensitivity）",
        },
        "negation_filter": {
            "window_chars": NEGATION_WINDOW,
            "terms": list(NEGATION_TERMS),
            "rule": "关键词前 6 字内出现否定词 → 该命中记为否定证据（案例 0）",
        },
        "mortgage_filter": {
            "terms": list(HOUSE_TERMS),
            "rule": "debt 关键词所在句含房贷类词 → 排除并单列",
        },
        "labels": {
            "debt": {
                "domain": "income",
                "keywords": list(DEBT_KEYWORDS),
                "removed_from_v1": ["亏损", "被骗", "贷款", "信贷"],
                "positive": "任一通过主体 / 否定 / 房贷过滤的 income 命中",
                "zero": "无阳性，但有否定证据（否定句）或证据事件零命中",
                "null": "无可用证据（无该域事件 / 全是提问 / 空文本 / 命中全被主体或房贷过滤）",
            },
            "serious_health": {
                "domain": "health",
                "keywords": list(SERIOUS_HEALTH_KEYWORDS),
                "removed_from_v1": ["手术", "住院"],
                "chronic_reported_separately": list(CHRONIC_KEYWORDS),
                "positive": "任一通过主体 / 否定的 health 命中",
                "zero": "无阳性，但有否定证据（否定句）或证据事件零命中",
                "null": "无可用证据（无该域事件 / 全是提问 / 空文本 / 命中全被主体过滤）",
            },
        },
        "conflict_rule": "同一案例既有阳性又有否定/排除命中 → 1 优先（存在性标签）",
        "no_prediction": "不输出评分 / 概率 / 应期；标签是结果变量",
        "leak_guard": "只读事件 domains / polarity / text 与出生年月日时；不读任何盘面字段",
    }


# ---------------------------------------------------------------------------
# 人工核查（静态）
# ---------------------------------------------------------------------------


# v2 残留误判（假阳性）：逐例回原文人工核查后冻结。案例标签变化 → AuditError（exit 4）。
# 每条：(标签 key, 类型, case_id, 关键词, 原文摘要, 按语义应为)
KNOWN_RESIDUAL: tuple[tuple[str, str, str, str, str, str], ...] = (
    # --- debt：标签为 1 但语义不是命主负债 ---
    ("debt", "家属 / 家庭债务（词表无「家庭」）", "RF-2026-000248", "负债",
     "「为凑钱做植皮手术，家庭破产，负债累累」",
     "家庭为治病破产，非命主本人负债（当时 1 岁半）"),
    ("debt", "房贷语境跨句泄漏", "RF-2026-000331", "负债",
     "「房贷车贷搞到负债过日子」被排除，但同案例「还是负债过日子」「上半年还是负债中」仍判 1",
     "债务由房贷车贷驱动，按卡 §9.2.4 应排除"),
    ("debt", "公司破产（非个人）", "RF-2026-000877", "破产",
     "「但公司内斗问题依旧，1 年后公司破产」",
     "雇主公司破产，非命主破产"),
    ("debt", "应收款误判（欠款）", "RF-2026-000918", "欠款",
     "「因为欠款要不上来转行做建材」",
     "别人欠命主（应收款），不是命主欠债"),
    # --- serious_health：标签为 1 但语义不是命主本人 ---
    ("serious_health", "跨句主语继承（父亲疾病）", "RF-2026-000067", "糖尿病",
     "上一句「我爸查出癌症」被主体过滤，下一句「但也确诊了糖尿病和胰腺炎」仍按叙述者采纳",
     "是父亲的糖尿病 / 胰腺炎，非命主"),
    ("serious_health", "主体词表缺祖辈（姥姥）", "RF-2026-000137", "癌",
     "「姥爷查出脑梗，姥姥查出癌症」",
     "姥姥患病，非命主（词表不含祖辈）"),
    ("serious_health", "主体词表缺姻亲（婆婆）", "RF-2026-000284", "癌",
     "「没有考上教师入编考试，婆婆**癌」",
     "婆婆患病，非命主（词表不含姻亲）"),
    ("serious_health", "繁体亲属称谓（兄長）", "RF-2026-000291", "癌",
     "繁体「兄長癌病去世」",
     "兄长患病；「兄長」不在词表（词表是简体「兄弟」）"),
    ("serious_health", "非亲属第三人称（初恋）", "RF-2026-000435", "癌",
     "「网恋，5 月份初恋胃癌去世」",
     "伴侣患病，非命主（词表不含伴侣）"),
    ("serious_health", "主体词表缺祖辈（爷爷）", "RF-2026-000461", "癌",
     "「也是那个年份左右爷爷肺癌去世（后爷爷）」",
     "爷爷患病，非命主（词表不含祖辈）"),
    ("serious_health", "主体词表缺祖辈（爷爷）", "RF-2026-000462", "癌",
     "同上（与 000461 内容重复）",
     "爷爷患病，非命主（词表不含祖辈）"),
    ("serious_health", "主体词表缺祖辈（爷爷）", "RF-2026-000683", "癌",
     "「爷爷因癌症病逝」",
     "爷爷患病，非命主（词表不含祖辈）"),
)

# v2 漏判（假阴性，案例为 0 但语义应为 1）：逐例回原文核查后冻结。
KNOWN_MISSED: tuple[tuple[str, str, str, str, str, str], ...] = (
    ("debt", "否定窗口误伤（「无」来自收入栏）", "RF-2026-000492", "负债",
     "「身价年收入: 无，求学多年负债较多」；关键词前 6 字窗口「无，求学多年」命中「无」",
     "命主求学负债，应为 1"),
    ("debt", "否定窗口误伤（「没」指钱没要回来）", "RF-2026-000515", "负债",
     "「还有很多钱没要回来，且负债 500w」；窗口含「没」",
     "命主负债 500w，应为 1"),
    ("serious_health", "否定窗口误伤（「差点挂了」+ 重病）", "RF-2026-000639", "重病",
     "「凶,差点挂了 重病」；「差点」在窗口内被当作否定",
     "命主确有大病，应为 1"),
)


# 20 例人工抽查：(case_id, debt, serious_health, 人工结论)。
AUDIT_SAMPLES: tuple[tuple[str, int | None, int | None, str], ...] = (
    ("RF-2026-000001", 0, 1, "合理：ICU/抢救/病危为本人事实；income 无命中 → 0"),
    ("RF-2026-000002", None, None, "提问排除：income 整段是提问、health 无事件 → 双 null"),
    ("RF-2026-000003", None, None, "合理：两域无事件 → 双 null（chart_ready=false，仅日期）"),
    ("RF-2026-000016", None, 0, "合理：health 有证据事件零命中 → 0；debt 无事件 → null"),
    ("RF-2026-000017", 0, 0, "合理：只有日期，两域均无命中 → 0（chart_ready=false）"),
    ("RF-2026-000034", 0, 0, "词表删除：v1 因「贷款」判 1，v2 删「贷款」→ 0"),
    ("RF-2026-000048", 0, None, "词表删除 + 无 health 事件：v1 房贷 1 → v2 0"),
    ("RF-2026-000084", 1, 0, "合理：负债为本人；v1 的「小手术」随「手术」删词消失 → 0"),
    ("RF-2026-000137", 0, 1, "存疑：姥姥癌症被当叙述者 → §7 残留误判"),
    ("RF-2026-000235", None, 0, "合理：「健康良好无大病」否定句 → 0；debt 无事件 → null"),
    ("RF-2026-000243", 0, 0, "词表删除：v1 因「贷款」判 1，v2 删「贷款」→ 无 v2 命中 → 0"),
    ("RF-2026-000284", 0, 1, "存疑：婆婆患癌被当叙述者 → §7 残留误判"),
    ("RF-2026-000308", 0, 0, "词表删除：「差点住院」随「住院」删词消失 → 0"),
    ("RF-2026-000331", 1, 0, "房贷句被排除，但「还是负债过日子」等句仍判 1 → §7 边界"),
    ("RF-2026-000461", None, 1, "存疑：爷爷肺癌 → §7 残留误判；debt 无事件 → null"),
    ("RF-2026-000531", 0, None, "词表删除：v1 因「被骗」判 1，v2 删「被骗」→ 0"),
    ("RF-2026-000592", 1, None, "主体过滤生效：家庭购房债务被排除，本人信用卡负债保留 → 1"),
    ("RF-2026-000681", None, 1, "家属排除：儿子欠债 → debt null；本人摔伤抢救 → health 1"),
    ("RF-2026-000796", 0, 1, "合理：本人「重病，住院命危」→ 1（「住院」已删，靠「重病」命中）"),
    ("RF-2026-000918", 1, 0, "存疑：「欠款要不回来」是应收款 → §7 残留误判"),
)


def check_known_residual(cases: Sequence[dict[str, Any]]) -> None:
    by_id = {row["case_id"]: row for row in cases}
    problems: list[str] = []
    for key, _kind, case_id, keyword, _phenomenon, _verdict in KNOWN_RESIDUAL:
        row = by_id.get(case_id)
        if row is None:
            problems.append(f"{case_id} 不在基础集")
            continue
        if row["labels"][key] != 1:
            problems.append(f"{case_id} 的 {key} 标签不是 1")
            continue
        matched = {hit["keyword"] for hit in row["hits"] if hit["label_key"] == key and hit["verdict"] == "positive"}
        if keyword not in matched:
            problems.append(f"{case_id} 未再命中「{keyword}」")
    if problems:
        raise AuditError("；".join(problems))


def check_missed(cases: Sequence[dict[str, Any]]) -> None:
    """假阴性清单：案例必须仍是 0，且该关键词仍被否定窗口拦下。"""
    by_id = {row["case_id"]: row for row in cases}
    problems: list[str] = []
    for key, _kind, case_id, keyword, _phenomenon, _verdict in KNOWN_MISSED:
        row = by_id.get(case_id)
        if row is None:
            problems.append(f"{case_id} 不在基础集")
            continue
        if row["labels"][key] != 0:
            problems.append(f"{case_id} 的 {key} 标签不是 0")
            continue
        negated = {
            hit["keyword"]
            for hit in row["hits"]
            if hit["label_key"] == key and hit["verdict"] == "negated"
        }
        if keyword not in negated:
            problems.append(f"{case_id} 的「{keyword}」不再被否定过滤")
    if problems:
        raise AuditError("；".join(problems))


def check_audit_samples(cases: Sequence[dict[str, Any]]) -> None:
    if len(AUDIT_SAMPLES) != 20:
        raise AuditError(f"抽查样本应为 20 例，实际 {len(AUDIT_SAMPLES)} 例")
    by_id = {row["case_id"]: row for row in cases}
    for case_id, debt, health, _verdict in AUDIT_SAMPLES:
        row = by_id.get(case_id)
        if row is None:
            raise AuditError(f"抽查案例不在基础集：{case_id}")
        if row["labels"]["debt"] != debt or row["labels"]["serious_health"] != health:
            raise AuditError(
                f"{case_id} 标签 debt={row['labels']['debt']!r}/serious_health="
                f"{row['labels']['serious_health']!r}，冻结期望 debt={debt!r}/serious_health={health!r}"
            )


def check_invariants(payload: Mapping[str, Any]) -> None:
    counts = payload["counts"]
    problems: list[str] = []
    for key, expected in EXPECTED_COUNTS.items():
        if counts.get(key) != expected:
            problems.append(f"{key}={counts.get(key)}（期望 {expected}）")
    for spec in LABEL_SPECS:
        block = counts[spec.key]
        if block["1"] + block["0"] + block["null"] != block["sum"] or block["sum"] != counts["base_sample"]:
            problems.append(f"{spec.key} 四桶不可加或合计不等于基础集")
        ready = block["chart_ready"]
        if ready["1"] + ready["0"] + ready["null"] != ready["sum"] or ready["sum"] != counts["base_chart_ready"]:
            problems.append(f"{spec.key} chart_ready 四桶不可加")
        domain = payload["audit"]["domain"][spec.key]
        expected_domain = EXPECTED_DOMAIN[spec.key]
        if domain["cases_with_domain_events"] != expected_domain["cases"]:
            problems.append(f"{spec.key} 域案例数 {domain['cases_with_domain_events']}")
        if domain["events_total"] != expected_domain["events"]:
            problems.append(f"{spec.key} 域事件数 {domain['events_total']}")
    if problems:
        raise LabelInvariantError("；".join(problems))
    residual = payload["audit"]["known_residual"]
    if residual["verdict"] == "labels_not_suitable_for_adjudication" and not payload["gate"]["stop"]:
        raise LabelInvariantError("门槛判定与 gate 字段不一致")


# ---------------------------------------------------------------------------
# 渲染
# ---------------------------------------------------------------------------


def _table(headers: Sequence[str], rows: Iterable[Sequence[Any]]) -> list[str]:
    lines = ["| " + " | ".join(str(cell) for cell in headers) + " |"]
    lines.append("|" + "|".join("---" for _ in headers) + "|")
    for row in rows:
        lines.append("| " + " | ".join(str(cell) for cell in row) + " |")
    return lines


def _pct(value: float | None) -> str:
    return "—" if value is None else f"{value:.2f}%"


def _label_text(value: int | None) -> str:
    return "null" if value is None else str(value)


def render_report(payload: Mapping[str, Any]) -> str:
    counts = payload["counts"]
    source = payload["source"]
    audit = payload["audit"]
    lines: list[str] = []
    add = lines.append

    add("# T-158 · 财富 / 健康结局标签 v2（`debt` / `serious_health`）")
    add("")
    add(f"- 数据源：`{source['path']}`（{source['records']} 条，sha256 `{source['sha256']}`）")
    add(f"- 上游 v1（只读）：`{source['v1']['path']}`（payload_sha256 `{source['v1']['payload_sha256']}`）")
    add(f"- 生成脚本：`{SCRIPT}`；定义冻结日 `{payload['frozen_at']}`（不是运行时间戳）")
    add(
        "- 依据：`tasks/T-158/PROMPT.md` §9（中枢裁决）。性质：**结果变量，不是预测**；"
        "只读事件文本 / polarity 与出生年月日时，**不使用任何盘面字段**；本文件无运行时间戳。"
    )
    add("")

    gate = payload["gate"]
    add("## 0. 门槛结论（卡 §9.2.6）")
    add("")
    residual = audit["known_residual"]
    debt_item = residual["per_label"]["debt"]
    health_item = residual["per_label"]["serious_health"]
    add(
        f"- v2 残留误判（假阳性）：`debt` **{debt_item['false_positive_rate_pct']}%**"
        f"（{debt_item['false_positive']}/{debt_item['positives']}）、"
        f"`serious_health` **{health_item['false_positive_rate_pct']}%**"
        f"（{health_item['false_positive']}/{health_item['positives']}）；门槛 = {residual['gate_threshold_pct']}%。"
    )
    add(
        f"- 另有漏判（假阴性）：`debt` {debt_item['false_negative']} 例、"
        f"`serious_health` {health_item['false_negative']} 例；"
        f"含漏判的错误率 `debt` {debt_item['error_rate_pct']}%、"
        f"`serious_health` {health_item['error_rate_pct']}%。"
    )
    add(f"- 判定：**{gate['verdict_text']}**")
    for item in gate["notes"]:
        add(f"- {item}")
    add("")

    add("## 1. 冻结定义（卡 §9）")
    add("")
    add(
        "1. **主体过滤**：关键词所在句含 "
        + "、".join(f"`{term}`" for term in KIN_TERMS)
        + " 且不含 `我/本人/自己` → 排除；两者都含 → 主体不明 → 案例 `null`（不猜）。"
    )
    add(
        "2. **否定过滤**：关键词前 6 字内出现 "
        + "、".join(f"`{term}`" for term in NEGATION_TERMS)
        + " → 该命中记为否定证据（案例 `0`）。"
    )
    add("3. **health 严重度**：删 `手术`、`住院`；保留词：" + "、".join(f"`{kw}`" for kw in SERIOUS_HEALTH_KEYWORDS) + "。")
    add("4. **debt 词表**：删 `亏损`、`被骗`、`贷款`、`信贷`；保留词：" + "、".join(f"`{kw}`" for kw in DEBT_KEYWORDS) + "。")
    add("5. **房贷 / 按揭**：关键词句含 " + "、".join(f"`{term}`" for term in HOUSE_TERMS) + " → 排除并单列。")
    add(
        "6. **null** = 无可用证据（无该域事件 / 全是提问 / 空文本 / 命中全被主体或房贷过滤），不折 0、不折 1。"
    )
    add(
        "7. **零主语假设**：句内无亲属称谓视为叙述者本人（第一人称自述；v1 同口径）。"
        "若把零主语也当主体不明，见 §6 敏感性。"
    )
    add("")

    add("## 2. 漏斗与标签计数")
    add("")
    lines.extend(
        _table(
            ["阶段", "条数"],
            [
                ["原始记录", counts["records_total"]],
                ["去重", counts["after_dedupe"]],
                ["有性别", counts["with_gender"]],
                ["出生日期可解析", counts["birth_date_parsable"]],
                ["出生时刻可解析", counts["birth_time_parsable"]],
                ["**基础集**", f"**{counts['base_sample']}**"],
                ["**chart_ready**", f"**{counts['base_chart_ready']}**"],
            ],
        )
    )
    add("")
    count_rows = []
    for spec in LABEL_SPECS:
        block = counts[spec.key]
        ready = block["chart_ready"]
        count_rows.append(
            [spec.key, block["1"], block["0"], block["null"], block["sum"],
             ready["1"], ready["0"], ready["null"], ready["sum"]]
        )
    lines.extend(
        _table(
            ["标签", "1（全集）", "0（全集）", "null（全集）", "合计", "1（chart_ready）",
             "0（chart_ready）", "null（chart_ready）", "合计"],
            count_rows,
        )
    )
    add("")
    for spec in LABEL_SPECS:
        block = counts[spec.key]
        add(
            f"- `{spec.key}` 可加：{block['sum']} = {block['1']}+{block['0']}+{block['null']}；"
            f"chart_ready {block['chart_ready']['sum']} = {block['chart_ready']['1']}+"
            f"{block['chart_ready']['0']}+{block['chart_ready']['null']}。"
        )
    add("")
    reason_rows = []
    for spec in LABEL_SPECS:
        reasons = audit["null_reasons"][spec.key]
        zeros = audit["zero_reasons"][spec.key]
        reason_rows.append(
            [
                spec.key,
                reasons["no_domain_event"], reasons["all_question"], reasons["no_text"],
                reasons["family_only"], reasons["subject_ambiguous"],
                reasons["mortgage_only"], reasons["family_and_mortgage"],
                zeros["negated"], zeros["no_hit"],
            ]
        )
    lines.extend(
        _table(
            ["标签", "null:无事件", "null:全提问", "null:无文本", "null:仅家属",
             "null:主体不明", "null:仅房贷", "null:家属+房贷", "0:否定句", "0:零命中"],
            reason_rows,
        )
    )
    add("")
    add(
        "> 与 v1 的关键差别：v2 的 `0` 只来自「否定句」或「证据事件零命中」；"
        "命中被主体 / 房贷过滤掉时落 `null`（无可用证据），不再折成 0。"
    )
    add("")

    add("## 3. 阳性率与基线（卡 §4 同口径）")
    add("")
    baseline_rows = []
    for spec in LABEL_SPECS:
        item = payload["baseline"][spec.key]
        ready = item["chart_ready"]
        base = item["base_reference"]
        baseline_rows.append(
            [spec.key, ready["sample_size"], ready["positive"], ready["negative"],
             _pct(ready["positive_rate_pct"]), base["sample_size"], base["positive"],
             base["negative"], _pct(base["positive_rate_pct"])]
        )
    lines.extend(
        _table(
            ["标签", "n（chart_ready）", "1", "0", "阳性率（验收口径）", "n（全集）", "1", "0", "阳性率（仅参考）"],
            baseline_rows,
        )
    )
    add("")
    add(
        "口径：分母 = 非 `null` 案例（`1+0`）。v2 阳性样本量很小（见上表），"
        "统计功效有限；流失来自词表删除与主体 / 否定 / 房贷过滤，逐项见 §4 / §6。"
    )
    add("")

    add("## 4. v1 → v2 差异（每条过滤删了多少阳性）")
    add("")
    diff_rows = []
    for spec in LABEL_SPECS:
        diff = audit["v1_diff"][spec.key]
        reasons = diff["reasons"]
        diff_rows.append(
            [
                spec.key, diff["v1_positive"], diff["v2_positive"], diff["lost"],
                reasons.get("removed_keyword_only", 0),
                reasons.get("subject_family", 0),
                reasons.get("subject_ambiguous", 0),
                reasons.get("mortgage", 0),
                reasons.get("negation", 0),
                reasons.get("unexplained", 0),
            ]
        )
    lines.extend(
        _table(
            ["标签", "v1 阳性", "v2 阳性", "流失", "词表删除", "家属排除",
             "主体不明", "房贷排除", "否定排除", "未解释"],
            diff_rows,
        )
    )
    add("")
    add(
        "> 流失归因按优先级：词表删除（v1 命中的词全部不在 v2 词表）→ 家属排除 → 主体不明 → 房贷 → 否定。"
        "同一案例只计一次。逐例清单见 `audit.v1_diff.<label>.cases`。"
    )
    add("")
    for spec in LABEL_SPECS:
        diff = audit["v1_diff"][spec.key]
        if diff["removed_keywords"]:
            add(
                f"- `{spec.key}` 词表删除明细："
                + "、".join(f"`{kw}` {number} 例" for kw, number in diff["removed_keywords"].items())
            )
    add("")

    add("## 5. 过滤审计")
    add("")
    filter_rows = []
    for spec in LABEL_SPECS:
        item = audit["filters"][spec.key]
        occ = item["occurrences"]
        filter_rows.append(
            [spec.key, occ["positive"], occ["negated"], occ["excluded_family"],
             occ["excluded_ambiguous"], occ["excluded_mortgage"]]
        )
    lines.extend(
        _table(
            ["标签", "采纳（阳性）次数", "否定次数", "家属排除", "主体不明", "房贷排除"],
            filter_rows,
        )
    )
    add("")
    chronic_rows = []
    for spec in LABEL_SPECS:
        chronic = audit["chronic"][spec.key]
        chronic_rows.append([spec.key, chronic["positive_cases"], chronic["positive_hits"]])
    add("`慢性病` 单列（卡 §9.2.3）：")
    add("")
    lines.extend(_table(["标签", "仅由慢性病触发的阳性案例", "慢性病阳性命中次数"], chronic_rows))
    add("")
    add("### 5.1 关键词命中（被采纳的阳性命中）")
    add("")
    keyword_rows = []
    for spec in LABEL_SPECS:
        hits = audit["keyword_hits"][spec.key]
        for keyword in spec.keywords:
            keyword_rows.append([f"`{spec.key}`", f"`{keyword}`", hits["events"][keyword], hits["cases"][keyword]])
    lines.extend(_table(["标签", "关键词", "阳性命中次数", "涉及案例"], keyword_rows))
    add("")
    add("### 5.2 提问排除（沿用 v1 规则）")
    add("")
    suppressed_rows = []
    for spec in LABEL_SPECS:
        block = audit["question"][spec.key]
        suppressed_rows.append([f"`{spec.key}`", block["suppressed_events"], block["suppressed_cases"]])
    lines.extend(_table(["标签", "含 v2 关键词的提问事件", "涉及案例"], suppressed_rows))
    add("")

    add("## 6. 敏感性（不改本版标签，只报数）")
    add("")
    strict = audit["sensitivity"]["strict_implicit_null"]
    extended = audit["sensitivity"]["extended_kin"]
    add("### 6.1 零主语按「主体不明 → null」")
    add("")
    lines.extend(
        _table(
            ["标签", "1", "0", "null", "阳性率"],
            [
                [spec.key, strict[spec.key]["1"], strict[spec.key]["0"], strict[spec.key]["null"],
                 _pct(strict[spec.key]["positive_rate_pct"])]
                for spec in LABEL_SPECS
            ],
        )
    )
    add("")
    add(
        "> 语料是中文零主语叙述，绝大多数命中句没有「我/自己」。若把零主语也判为主体不明，"
        "阳性几乎清零，标签失去统计意义——因此本版采用「无亲属称谓 = 叙述者」的默认。"
    )
    add("")
    add("### 6.2 主体词表加入祖辈 / 姻亲（姥爷/姥姥/爷爷/奶奶/外公/外婆/婆婆/公公/岳父/岳母）")
    add("")
    lines.extend(
        _table(
            ["标签", "扩展前阳性", "扩展后阳性", "会改为 `null` 的案例"],
            [
                [
                    spec.key,
                    extended[spec.key]["positives_before"],
                    extended[spec.key]["positives_after"],
                    "、".join(extended[spec.key]["removed"]) if extended[spec.key]["removed"] else "—",
                ]
                for spec in LABEL_SPECS
            ],
        )
    )
    add("")
    add(
        "> 卡 §9.2.1 的亲属词表不含祖辈 / 姻亲；这些称谓在本版按「零主语 → 叙述者」处理，"
        "因此残留为误判（见 §7）。是否扩展词表由中枢决定。"
    )
    add("")

    add("## 7. v2 残留误判与漏判（人工逐例核查）")
    add("")
    types_rows = []
    for spec in LABEL_SPECS:
        item = residual["per_label"][spec.key]
        for kind, number in item["false_positive_types"].items():
            types_rows.append([f"`{spec.key}`", "假阳性", kind, number])
        for kind, number in item["false_negative_types"].items():
            types_rows.append([f"`{spec.key}`", "假阴性", kind, number])
    if types_rows:
        lines.extend(_table(["标签", "方向", "类型", "案例数"], types_rows))
        add("")
    add(
        f"合计：假阳性 `debt` {debt_item['false_positive']} 例 / 阳性 {debt_item['positives']}"
        f"（{_pct(debt_item['false_positive_rate_pct'])}），"
        f"`serious_health` {health_item['false_positive']} 例 / 阳性 {health_item['positives']}"
        f"（{_pct(health_item['false_positive_rate_pct'])}）；"
        f"假阴性 `debt` {debt_item['false_negative']} 例、`serious_health` {health_item['false_negative']} 例。"
    )
    add("")
    if KNOWN_RESIDUAL:
        add("### 7.1 假阳性（标签 1 但语义不是命主本人）")
        add("")
        lines.extend(
            _table(
                ["标签", "类型", "case_id", "命中词", "原文摘要", "按语义应为"],
                [list(item) for item in KNOWN_RESIDUAL],
            )
        )
        add("")
    if KNOWN_MISSED:
        add("### 7.2 假阴性（标签 0 但语义应为 1）")
        add("")
        lines.extend(
            _table(
                ["标签", "类型", "case_id", "命中词", "原文摘要", "按语义应为"],
                [list(item) for item in KNOWN_MISSED],
            )
        )
        add("")
    add(
        "> 这些是规则边界，不是实现 bug；按卡 §9.2.6，门槛未过即**停**，不再调词。"
        "如需 v3，建议按类型重新预注册（扩展亲属词表 / 处理跨句主语 / 否定窗口避开干支与「差点挂了」），"
        "而不是在本版上就地改词。"
    )
    add("")

    add("## 8. 20 例人工抽查")
    add("")
    add("抽查方式：回 JSONL 逐例核对事件原文与过滤规则，并复算标签。20/20 与冻结结论一致。")
    add("")
    by_id = {row["case_id"]: row for row in payload["_cases"]}
    rows = []
    for index, (case_id, _debt, _health, verdict) in enumerate(AUDIT_SAMPLES, start=1):
        row = by_id[case_id]
        rows.append(
            [
                index,
                case_id,
                "是" if row["chart_ready"] else "否",
                _label_text(row["labels"]["debt"]),
                _label_text(row["labels"]["serious_health"]),
                row["label_basis"]["debt"] + " / " + row["label_basis"]["serious_health"],
                verdict,
            ]
        )
    lines.extend(
        _table(["#", "case_id", "chart_ready", "debt", "serious_health", "判定依据", "结论"], rows)
    )
    add("")

    add("## 9. 复现与不变量")
    add("")
    add("```bash")
    add(".venv\\Scripts\\python.exe -m tools.domain_labels_wealth_health_v2")
    add(".venv\\Scripts\\python.exe -m pytest tests/tools/test_domain_labels_wealth_health_v2.py -q -o addopts=\"-ra --tb=short\"")
    add("```")
    add("")
    add(
        f"- 漏斗不变量：{counts['records_total']} / {counts['after_dedupe']} / {counts['with_gender']} / "
        f"{counts['birth_date_parsable']} / {counts['birth_time_parsable']}；基础集 {counts['base_sample']}，"
        f"chart_ready {counts['base_chart_ready']}。"
    )
    add(f"- JSON `payload_sha256`：`{payload['payload_sha256']}`")
    add("- 无运行时间戳、不读盘面事实、不建盘、不写 v1 产物；两次运行输出逐字节一致。")
    add("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 入口
# ---------------------------------------------------------------------------


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_if_changed(path: Path, content: str) -> bool:
    if path.exists() and path.read_text(encoding="utf-8") == content:
        return False
    path.write_text(content, encoding="utf-8")
    return True


def load_v1(path: Path = V1_PATH) -> dict[str, Any]:
    if not path.exists():
        raise SourceError(f"v1 产物不存在：{path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SourceError(f"{path.name} 不是合法 JSON：{exc}") from exc
    if payload.get("schema") != V1_SCHEMA:
        raise SourceError(f"{path.name} schema={payload.get('schema')!r}，期望 {V1_SCHEMA}")
    return payload


def build_gate(payload: Mapping[str, Any]) -> dict[str, Any]:
    """门槛：v2 已知误判率 > 20% → 停，写「标签不适合作裁决」（卡 §9.2.6）。"""
    residual = payload["audit"]["known_residual"]
    threshold = residual["gate_threshold_pct"]
    per_label = residual["per_label"]
    failed = residual["gate_failed"] or residual["error_gate_failed_including_missed"]
    problems = [
        f"{key} 假阳性 {item['false_positive_rate_pct']}%（{item['false_positive']}/{item['positives']}）、"
        f"含漏判的错误率 {item['error_rate_pct']}%"
        for key, item in per_label.items()
        if (item["false_positive_rate_pct"] or 0) > threshold
        or (item["error_rate_pct"] or 0) > threshold
    ]
    small = [key for key, item in per_label.items() if item["positives"] < 30]
    notes: list[str] = []
    if failed:
        notes.append("门槛未过：残留误判率 > 20%，按卡 §9.2.6 **不再调词**，标签停用，T-160 不启动。")
    else:
        notes.append("门槛通过（两标签残留误判率均 ≤ 20%）。")
    if small:
        notes.append(
            "阳性样本量偏小（"
            + "、".join(f"{key} n={per_label[key]['positives']}" for key in small)
            + "），统计功效有限。"
        )
    notes.append(
        "口径：门槛按「假阳性 / 阳性」计（沿用 v1 的误判口径）；"
        "若把漏判（假阴性）也算错误率，"
        + "、".join(f"{key} {per_label[key]['error_rate_pct']}%" for key in per_label)
        + "，结论不变。"
    )
    return {
        "threshold_pct": threshold,
        "false_positive_rates": {key: per_label[key]["false_positive_rate_pct"] for key in per_label},
        "error_rates": {key: per_label[key]["error_rate_pct"] for key in per_label},
        "failed": failed,
        "stop": bool(failed),
        "verdict": residual["verdict"],
        "verdict_text": "标签不适合作裁决（停，不再调词）" if failed else "门槛通过（标签仍受样本量限制）",
        "problems": problems,
        "notes": notes,
    }


def main() -> int:
    try:
        records = load_source()
        v1_payload = load_v1()
        payload, cases, excluded = build_payload(
            records,
            v1_payload=v1_payload,
            source_path=SOURCE_PATH,
            source_sha256=_sha256_file(SOURCE_PATH),
        )
        check_invariants(payload)
        check_known_residual(cases)
        check_missed(cases)
        check_audit_samples(cases)
        payload["_cases"] = cases
        report = render_report(payload)
        payload.pop("_cases")
    except SourceError as exc:
        print(f"[FAIL] 数据源不可用：{exc}", file=sys.stderr)
        return 2
    except LabelInvariantError as exc:
        print(f"[FAIL] 不变量不复现：{exc}", file=sys.stderr)
        return 3
    except AuditError as exc:
        print(f"[FAIL] 人工核查与当前数据不符，需重审：{exc}", file=sys.stderr)
        return 4

    json_text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    _write_if_changed(JSON_PATH, json_text)
    _write_if_changed(REPORT_PATH, report)

    counts = payload["counts"]
    print("T-158 domain-labels-wealth-health v2")
    print(
        f"  source   : {payload['source']['path']} sha256={payload['source']['sha256'][:12]}… "
        f"records={counts['records_total']} | v1={payload['source']['v1']['payload_sha256'][:12]}…"
    )
    print(
        f"  funnel   : {counts['records_total']} → {counts['after_dedupe']} → "
        f"base={counts['base_sample']} chart_ready={counts['base_chart_ready']}"
    )
    for spec in LABEL_SPECS:
        block = counts[spec.key]
        ready = block["chart_ready"]
        baseline = payload["baseline"][spec.key]
        print(
            f"  {spec.key:<14} : 1={block['1']} 0={block['0']} null={block['null']} (sum={block['sum']}) "
            f"| chart_ready 1={ready['1']} 0={ready['0']} null={ready['null']} "
            f"| rate={_pct(baseline['chart_ready']['positive_rate_pct'])} n={baseline['chart_ready']['sample_size']}"
        )
    print(
        f"  gate     : FP rate debt={payload['gate']['false_positive_rates']['debt']}% "
        f"serious_health={payload['gate']['false_positive_rates']['serious_health']}% "
        f"| error debt={payload['gate']['error_rates']['debt']}% "
        f"serious_health={payload['gate']['error_rates']['serious_health']}% "
        f"→ {payload['gate']['verdict_text']}"
    )
    print(f"  wrote    : META/domain-labels-wealth-health-v2.json sha256={_sha256_file(JSON_PATH)[:12]}…")
    print("           : META/domain-labels-wealth-health-v2.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

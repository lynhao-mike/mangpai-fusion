"""T-158 · 财富 / 健康结局标签 v1（``debt`` / ``serious_health`` 二值标签）。

从 ``cases/raw_feedback/parsed/real_cases_990.jsonl`` 的 ``income`` / ``health`` 事件造两个
**存在性**结果变量，冻结定义、样本量、阳性率与基线。标签**只**来自事件文本关键词与
``polarity`` 记录，**不读取任何八字 / 盘面 / 排盘字段**（防泄漏，任务卡 §2.1 / §5 / §8）。

产物（确定性，无运行时间戳，重复运行逐字节一致）：

* ``META/domain-labels-wealth-health-v1.json``  逐例标签 + 漏斗计数 + 基线 + 审计
* ``META/domain-labels-wealth-health-v1.md``    人读报告（漏斗 / 计数 / 阳性率 / 关键词 / 提问排除 / 20 例抽查 / 已知误差）

定义由任务卡 §2 预注册，本模块不改关键词、不改判定顺序。用法::

    python -m tools.domain_labels_wealth_health

退出码：0 通过；2 数据源不可读或结构不符；3 漏斗 / 计数不变量不复现（数据源变更，拒绝落盘）；
4 人工抽查或已知误判清单与当前数据不符（需重审）。

口径（与任务卡 §2 逐条对应）：

* 基础集：``duplicate_key`` 全等去重（保留首次出现）+ ``gender ∈ {男, 女}`` + 出生日期可解析。
* ``chart_ready``：出生时刻可解析（``clock_beijing`` 或 ``true_solar`` 均可；只标记，不建盘）。
* ``debt`` 看 ``income`` 域事件，``serious_health`` 看 ``health`` 域事件；两个标签互不依赖。
* 提问判定：事件文本含 ``？``、``?``、``是否``、``能否``、``请问``、``怎么样``、``吗``、``么``、``呢``
  任一 → **整段不作证据**（不还原问句语义）。
* ``1``：任一非提问事件命中冻结关键词；``0``：有证据事件但零命中；``null``：该域**无证据事件**
  （无该域事件 / 全是提问 / 无文本）→ 该域排除，**不折入 0 或 1**。
* 同一案例既有命中又有未命中事件 → ``1`` 优先（存在性标签），并在计数里单列 ``conflict``。
* ``polarity`` 只随事件记录并在报告里审计，**不参与**判定：卡片 §2.2 / §2.3 的规则是纯关键词规则。
* 出生字段复用 ``tools.timing_eval_set.resolve_birth``（其内部调用 ``parse_clock_datetime``，
  并把农历记录换算为公历），该文件只读 import，不改动。
"""

from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from tools.timing_eval_set import resolve_birth

ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = ROOT / "cases" / "raw_feedback" / "parsed" / "real_cases_990.jsonl"
JSON_PATH = ROOT / "META" / "domain-labels-wealth-health-v1.json"
REPORT_PATH = ROOT / "META" / "domain-labels-wealth-health-v1.md"

SCHEMA = "domain-labels-wealth-health/v1"
TASK = "T-158"
SCRIPT = "tools/domain_labels_wealth_health.py"

# 定义冻结日 = 任务卡 §2 建卡日（预注册）。不是运行时间戳：本产物必须可逐字节复现。
FROZEN_AT = "2026-10-29"

GENDERS = ("男", "女")

# 任务卡 §2.2 关键词表，原样冻结，禁止增删。
DEBT_KEYWORDS = (
    "负债", "欠债", "债务", "欠款", "借款", "贷款", "信贷", "破产", "被骗", "还债", "负债累累",
    "亏损", "资金链", "被执行人",
)

# 任务卡 §2.3 关键词表，原样冻结，禁止增删。
SERIOUS_HEALTH_KEYWORDS = (
    "手术", "住院", "ICU", "抢救", "病危", "癌", "肿瘤", "重病", "大病", "慢性病", "中风",
    "心脏病", "糖尿病", "肾衰竭", "化疗", "放疗", "瘫痪", "失明", "精神病",
)

# 任务卡 §2.2 提问标记，原样冻结。字面匹配（子串），不还原问句语义。
QUESTION_MARKERS = ("？", "?", "是否", "能否", "请问", "怎么样", "吗", "么", "呢")

TEXT_SUMMARY_LIMIT = 160

# 计数不变量（任务卡 §1 / §6）。不满足即视为数据源变更，拒绝落盘。
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
    """一个结局标签的冻结配置：看哪个域、命中哪些词。"""

    key: str
    domain: str
    keywords: tuple[str, ...]


LABEL_SPECS = (
    LabelSpec("debt", "income", DEBT_KEYWORDS),
    LabelSpec("serious_health", "health", SERIOUS_HEALTH_KEYWORDS),
)


class SourceError(RuntimeError):
    """数据源不可读或结构不符。"""


class LabelInvariantError(RuntimeError):
    """漏斗 / 计数不变量不复现。"""


class AuditError(RuntimeError):
    """人工抽查或已知误判清单与当前数据不符。"""


# ---------------------------------------------------------------------------
# 文本判定
# ---------------------------------------------------------------------------


def question_markers_in(text: str) -> tuple[str, ...]:
    """返回命中的提问标记（按冻结顺序，可多选）。"""
    return tuple(marker for marker in QUESTION_MARKERS if marker in text)


def keyword_hits(text: str, keywords: Sequence[str]) -> list[str]:
    """返回命中的关键词（按冻结顺序，可多选；长词与短词可同时命中）。"""
    return [keyword for keyword in keywords if keyword in text]


def event_verdict(text: str) -> str:
    """事件文本的证据状态：``empty`` / ``question`` / ``evidence``。"""
    if not text.strip():
        return "empty"
    if question_markers_in(text):
        return "question"
    return "evidence"


def summarise_text(text: str, limit: int = TEXT_SUMMARY_LIMIT) -> str:
    """压缩空白并截断到固定长度，供审计展示（确定性）。"""
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    return compact[:limit] + "…"


# ---------------------------------------------------------------------------
# 数据读取与打标
# ---------------------------------------------------------------------------


def load_source(path: Path = SOURCE_PATH) -> list[dict[str, Any]]:
    """逐行读 JSONL。缺字段 / 非对象 / JSON 损坏 → SourceError。"""
    if not path.exists():
        raise SourceError(f"数据源不存在：{path}")
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise SourceError(f"{path.name}:{line_number} 不是合法 JSON：{exc}") from exc
            if not isinstance(record, dict):
                raise SourceError(f"{path.name}:{line_number} 不是 JSON 对象")
            missing = [key for key in SOURCE_KEYS if key not in record]
            if missing:
                raise SourceError(f"{path.name}:{line_number} 缺字段：{', '.join(missing)}")
            if not isinstance(record["events"], list):
                raise SourceError(f"{path.name}:{line_number} events 不是数组")
            records.append(record)
    if not records:
        raise SourceError(f"数据源为空：{path}")
    return records


def dedupe_records(
    records: Sequence[Mapping[str, Any]],
) -> tuple[list[Mapping[str, Any]], int, int]:
    """按 ``duplicate_key`` 去重（保留首次出现）。返回去重结果、重复组数、移除条数。"""
    seen: dict[str, str] = {}
    unique: list[Mapping[str, Any]] = []
    duplicate_keys: set[str] = set()
    for record in records:
        key = record["duplicate_key"]
        if key in seen:
            duplicate_keys.add(key)
            continue
        seen[key] = str(record["raw_id"])
        unique.append(record)
    return unique, len(duplicate_keys), len(records) - len(unique)


def classify_domain(record: Mapping[str, Any], spec: LabelSpec) -> dict[str, Any]:
    """按任务卡 §2 给单例的单个域打标。只读该域事件的 domains / polarity / text。"""
    domain_events = [event for event in record["events"] if spec.domain in (event.get("domains") or [])]
    entries: list[dict[str, Any]] = []
    counts = {"question": 0, "empty": 0, "evidence": 0}

    for event in domain_events:
        text = event.get("text") or ""
        verdict = event_verdict(text)
        counts[verdict] += 1
        entries.append(
            {
                "year": event.get("year"),
                "polarity": event.get("polarity"),
                "verdict": verdict,
                "matched": keyword_hits(text, spec.keywords) if verdict == "evidence" else [],
                "text": summarise_text(text),
            }
        )

    evidence = [entry for entry in entries if entry["verdict"] == "evidence"]
    if not domain_events:
        label: int | None = None
        null_reason: str | None = "no_domain_event"
    elif not evidence:
        label = None
        null_reason = "all_question" if counts["question"] else "no_text"
    elif any(entry["matched"] for entry in evidence):
        label = 1
        null_reason = None
    else:
        label = 0
        null_reason = None

    conflict = any(entry["matched"] for entry in evidence) and any(
        not entry["matched"] for entry in evidence
    )

    return {
        "label": label,
        "null_reason": null_reason,
        "conflict": conflict,
        "events_total": len(domain_events),
        "events_question": counts["question"],
        "events_empty_text": counts["empty"],
        "events_evidence": counts["evidence"],
        "hit_events": sum(1 for entry in evidence if entry["matched"]),
        "matched_keywords": [
            keyword for entry in evidence for keyword in entry["matched"]
        ],
        "events": entries,
    }


def _birth_of(record: Mapping[str, Any]) -> dict[str, Any]:
    return resolve_birth(dict(record))


def build_case(record: Mapping[str, Any], birth: Mapping[str, Any]) -> dict[str, Any]:
    """产出标签案例（不含任何盘面字段）。"""
    labels: dict[str, int | None] = {}
    evidence_events: list[dict[str, Any]] = []
    for spec in LABEL_SPECS:
        result = classify_domain(record, spec)
        labels[spec.key] = result["label"]
        for entry in result["events"]:
            evidence_events.append({"label_key": spec.key, "domain": spec.domain, **entry})
    return {
        "case_id": record["raw_id"],
        "gender": record["gender"],
        "birth_datetime_raw": record["birth_datetime_raw"],
        "birth_dt": birth["dt"].isoformat(sep=" "),
        "time_basis": birth["time_basis"],
        "chart_ready": bool(birth["has_time"]),
        "labels": labels,
        "evidence_events": evidence_events,
    }


def _exclusion_reasons(record: Mapping[str, Any], birth: Mapping[str, Any]) -> list[str]:
    reasons: list[str] = []
    if record["gender"] not in GENDERS:
        reasons.append("missing_gender")
    if not birth["ok"]:
        reasons.append(str(birth["reason"]).split(":")[0])
    return reasons


# ---------------------------------------------------------------------------
# 聚合：计数 / 基线 / 审计
# ---------------------------------------------------------------------------


def _section(rows: Sequence[dict[str, Any]], key: str) -> dict[str, Any]:
    """一个标签在给定案例集上的四桶：1 / 0 / null 可加。"""
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


def _domain_audit(records: Sequence[Mapping[str, Any]], spec: LabelSpec) -> dict[str, Any]:
    polarity = {"negative": 0, "positive": 0, "unknown": 0, "other": 0}
    total = question = empty = evidence = 0
    cases_with_events = 0
    for record in records:
        domain_events = [
            event for event in record["events"] if spec.domain in (event.get("domains") or [])
        ]
        if domain_events:
            cases_with_events += 1
        for event in domain_events:
            total += 1
            raw_polarity = event.get("polarity")
            polarity[raw_polarity if raw_polarity in polarity else "other"] += 1
            verdict = event_verdict(event.get("text") or "")
            if verdict == "question":
                question += 1
            elif verdict == "empty":
                empty += 1
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


def _keyword_audit(rows: Sequence[dict[str, Any]], spec: LabelSpec) -> dict[str, Any]:
    event_hits = {keyword: 0 for keyword in spec.keywords}
    case_hits = {keyword: 0 for keyword in spec.keywords}
    for row in rows:
        seen: set[str] = set()
        for entry in row["evidence_events"]:
            if entry["label_key"] != spec.key:
                continue
            for keyword in entry["matched"]:
                event_hits[keyword] += 1
                seen.add(keyword)
        for keyword in seen:
            case_hits[keyword] += 1
    return {
        "events": event_hits,
        "events_total": sum(event_hits.values()),
        "cases": case_hits,
        "cases_any": sum(1 for row in rows if any(
            entry["matched"] for entry in row["evidence_events"] if entry["label_key"] == spec.key
        )),
    }


def _question_audit(
    records: Sequence[Mapping[str, Any]], spec: LabelSpec
) -> dict[str, Any]:
    markers = {marker: 0 for marker in QUESTION_MARKERS}
    suppressed: list[dict[str, Any]] = []
    for record in records:
        for event in record["events"]:
            if spec.domain not in (event.get("domains") or []):
                continue
            text = event.get("text") or ""
            found = question_markers_in(text)
            if not found:
                continue
            for marker in found:
                markers[marker] += 1
            hits = keyword_hits(text, spec.keywords)
            if hits:
                suppressed.append(
                    {
                        "case_id": record["raw_id"],
                        "year": event.get("year"),
                        "polarity": event.get("polarity"),
                        "markers": list(found),
                        "keywords": hits,
                        "text": summarise_text(text, 120),
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


def _null_reasons(rows: Sequence[dict[str, Any]], key: str) -> dict[str, int]:
    counts = {"no_domain_event": 0, "all_question": 0, "no_text": 0}
    for row in rows:
        if row["labels"][key] is not None:
            continue
        record = row["_record"]
        spec = next(spec for spec in LABEL_SPECS if spec.key == key)
        counts[classify_domain(record, spec)["null_reason"]] += 1
    return counts


def build_payload(
    records: Sequence[Mapping[str, Any]],
    *,
    source_path: Path = SOURCE_PATH,
    source_sha256: str,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    """构建完整载荷。返回 (payload, 案例列表, 剔除清单)。"""
    unique, duplicate_groups, duplicate_removed = dedupe_records(records)
    cases: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    with_gender = birth_ok = birth_time = 0

    for record in unique:
        birth = _birth_of(record)
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

    labels_block: dict[str, Any] = {}
    baseline: dict[str, Any] = {}
    audit: dict[str, Any] = {
        "domain": {},
        "keyword_hits": {},
        "question": {},
        "null_reasons": {},
        "null_share_pct": {},
        "base_excluded": {},
    }
    for spec in LABEL_SPECS:
        base_bucket = _section(cases, spec.key)
        ready_bucket = _section(chart_ready_rows, spec.key)
        counts[spec.key] = {**base_bucket, "chart_ready": ready_bucket}
        labels_block[spec.key] = {
            "domain": spec.domain,
            "keywords": list(spec.keywords),
            "null_reasons": _null_reasons(cases, spec.key),
            "conflict_cases": sum(
                1 for row in cases if classify_domain(row["_record"], spec)["conflict"]
            ),
            "positive_events": sum(
                1 for row in cases for entry in row["evidence_events"]
                if entry["label_key"] == spec.key and entry["matched"]
            ),
        }
        ready_positives = sum(1 for row in chart_ready_rows if row["labels"][spec.key] == 1)
        ready_negatives = sum(1 for row in chart_ready_rows if row["labels"][spec.key] == 0)
        base_positives = base_bucket["1"]
        base_negatives = base_bucket["0"]
        baseline[spec.key] = {
            "chart_ready": {
                "sample_size": ready_positives + ready_negatives,
                "positive": ready_positives,
                "negative": ready_negatives,
                "positive_rate_pct": _rate(ready_positives, ready_positives + ready_negatives),
            },
            "base_reference": {
                "sample_size": base_positives + base_negatives,
                "positive": base_positives,
                "negative": base_negatives,
                "positive_rate_pct": _rate(base_positives, base_positives + base_negatives),
            },
            "null_share_pct": {
                "base": _rate(base_bucket["null"], base_bucket["sum"]),
                "chart_ready": _rate(ready_bucket["null"], ready_bucket["sum"]),
            },
        }
        audit["domain"][spec.key] = _domain_audit(unique, spec)
        audit["keyword_hits"][spec.key] = _keyword_audit(cases, spec)
        question_block = _question_audit(unique, spec)
        audit["question"][spec.key] = question_block
        audit["null_reasons"][spec.key] = labels_block[spec.key]["null_reasons"]
        audit["null_share_pct"][spec.key] = baseline[spec.key]["null_share_pct"]

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
        },
        "counts": counts,
        "labels": labels_block,
        "baseline": baseline,
        "audit": audit,
        "excluded_records": excluded,
        "cases": [{key: value for key, value in row.items() if key != "_record"} for row in cases],
    }
    material = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    payload["payload_sha256"] = hashlib.sha256(material.encode("utf-8")).hexdigest()
    return payload, cases, excluded


def _definition_block() -> dict[str, Any]:
    return {
        "unit": "case（原始 JSONL 一条反馈）",
        "dedupe": "duplicate_key 全等去重，保留文件中首次出现者",
        "base_filter": ["gender ∈ {男, 女}", "birth_datetime_raw 可解析出公历日期"],
        "chart_ready": "出生时刻可解析（clock_beijing 或 true_solar）；本卡只标记，不建盘",
        "labels": {
            "debt": {
                "domain": "income",
                "positive": "任一非提问 income 事件文本命中债务关键词",
                "zero": "有 income 证据事件（非提问、非空文本）但零关键词命中",
                "null": "无 income 证据事件（无该域事件 / 全是提问 / 无文本）→ 该域排除",
                "keywords": list(DEBT_KEYWORDS),
            },
            "serious_health": {
                "domain": "health",
                "positive": "任一非提问 health 事件文本命中严重关键词",
                "zero": "有 health 证据事件（非提问、非空文本）但零关键词命中",
                "null": "无 health 证据事件（无该域事件 / 全是提问 / 无文本）→ 该域排除",
                "keywords": list(SERIOUS_HEALTH_KEYWORDS),
            },
        },
        "question_rule": "事件文本含提问标记任一 → 整段不作证据（字面子串匹配，不还原问句语义）",
        "question_markers": list(QUESTION_MARKERS),
        "conflict_rule": "同一案例既有命中事件又有未命中事件 → 1 优先（存在性标签），单列 conflict",
        "polarity_usage": "只随事件记录并在报告审计；不参与判定（卡片 §2.2 / §2.3 为纯关键词规则）",
        "no_prediction": "不输出任何评分 / 概率 / 应期；标签是结果变量",
        "leak_guard": "只读事件 domains / polarity / text 与出生年月日时；不读任何盘面字段",
    }


# ---------------------------------------------------------------------------
# 不变量与人工核查
# ---------------------------------------------------------------------------


def _flatten_section(section: Mapping[str, Any]) -> tuple[int, int, int, int]:
    return int(section["1"]), int(section["0"]), int(section["null"]), int(section["sum"])


def check_invariants(payload: Mapping[str, Any]) -> None:
    """漏斗、域计数、四桶可加。任一不复现 → LabelInvariantError。"""
    counts = payload["counts"]
    problems: list[str] = []
    for key, expected in EXPECTED_COUNTS.items():
        actual = counts.get(key)
        if actual != expected:
            problems.append(f"{key}={actual}（期望 {expected}）")

    for spec in LABEL_SPECS:
        one, zero, null, total = _flatten_section(counts[spec.key])
        if one + zero + null != total:
            problems.append(f"{spec.key} 四桶不可加：{one}+{zero}+{null}≠{total}")
        if total != counts["base_sample"]:
            problems.append(f"{spec.key} 合计 {total} ≠ 基础集 {counts['base_sample']}")
        ready_one, ready_zero, ready_null, ready_total = _flatten_section(
            counts[spec.key]["chart_ready"]
        )
        if ready_one + ready_zero + ready_null != ready_total:
            problems.append(
                f"{spec.key} chart_ready 四桶不可加：{ready_one}+{ready_zero}+{ready_null}≠{ready_total}"
            )
        if ready_total != counts["base_chart_ready"]:
            problems.append(
                f"{spec.key} chart_ready 合计 {ready_total} ≠ {counts['base_chart_ready']}"
            )
        domain = payload["audit"]["domain"][spec.key]
        expected_domain = EXPECTED_DOMAIN[spec.key]
        if domain["cases_with_domain_events"] != expected_domain["cases"]:
            problems.append(
                f"{spec.key} 域案例数 {domain['cases_with_domain_events']}（期望 {expected_domain['cases']}）"
            )
        if domain["events_total"] != expected_domain["events"]:
            problems.append(
                f"{spec.key} 域事件数 {domain['events_total']}（期望 {expected_domain['events']}）"
            )
        if (
            domain["events_question"] + domain["events_empty_text"] + domain["events_evidence"]
            != domain["events_total"]
        ):
            problems.append(f"{spec.key} 事件拆分不可加")

    if problems:
        raise LabelInvariantError("；".join(problems))


# 已知误判 / 漏判：人工逐条回原文核查后冻结。按预注册规则保留原判，不就地改词。
# 每条：(标签 key, 类型, case_id, 命中关键词, 原文摘要, 按语义应为 / 说明)
KNOWN_ISSUES: tuple[tuple[str, str, str, str, str, str], ...] = (
    # --- debt：标签会从 1 变成 0 的误判 ---
    ("debt", "第三人称（家属债务）", "RF-2026-000243", "贷款",
     "「家里贷款买房」+「父亲…欠下百万贷款，想为家里分担」", "家属债务，不是命主本人负债"),
    ("debt", "第三人称（家属债务）", "RF-2026-000531", "被骗",
     "「工作顺利…但妈妈被骗，工资全都补贴家里了」", "母亲被骗，命主只是补贴家里"),
    ("debt", "第三人称（家属债务）", "RF-2026-000681", "欠债",
     "「骑车摔倒，膝盖粉碎性骨折，儿子欠债」", "儿子欠债，非命主负债（该事件另有自身受伤）"),
    ("debt", "房贷 / 购房贷款", "RF-2026-000048", "贷款",
     "「我们一家人就住在贷款买的地下室里」", "购房贷款（且为家庭），非债务危机"),
    ("debt", "房贷 / 购房贷款", "RF-2026-000220", "贷款", "「吉，算是比较平稳，买了房，背上了贷款」", "按揭购房，非负面债务事件"),
    ("debt", "房贷 / 购房贷款", "RF-2026-000221", "贷款", "「吉，买了房，背上贷款」", "按揭购房，非负面债务事件"),
    ("debt", "房贷 / 购房贷款", "RF-2026-000331", "负债",
     "「因为口罩问题收入减少了。再加上房贷车贷搞到负债过日子」", "房贷车贷，非经营/消费债务危机"),
    ("debt", "房贷 / 购房贷款", "RF-2026-000513", "贷款", "「吉，2007 年底家里贷款买房了」", "家属按揭购房"),
    ("debt", "房贷 / 购房贷款", "RF-2026-000868", "贷款", "「吉，贷款买房了，家里支持的不多」", "按揭购房，非负面债务事件"),
    ("debt", "投资 / 经营亏损", "RF-2026-000537", "亏损", "「实习…剧组亏损，没有拿到工资」", "雇主项目亏损，非命主债务"),
    ("debt", "投资 / 经营亏损", "RF-2026-000736", "亏损", "「2017-2024 转行继续做别的投资亏损 100 万」", "投资亏损，非借贷债务"),
    ("debt", "投资 / 经营亏损", "RF-2026-000900", "亏损", "「炒股亏损」/「持续亏损…回了点本」", "证券/经营亏损，非借贷债务"),
    ("debt", "应收款误判（欠款）", "RF-2026-000918", "欠款", "「因为欠款要不上来转行做建材」", "别人欠命主（应收款），不是命主欠债"),
    ("debt", "公司破产（非个人）", "RF-2026-000877", "破产", "「但公司内斗问题依旧，1 年后公司破产」", "雇主公司破产，非命主破产"),
    ("debt", "被骗（损失非负债）", "RF-2026-000345", "被骗", "「被网上的**，和掷骰子骗了…第一次被骗」", "被骗损失，不等同负债"),
    ("debt", "被骗（损失非负债）", "RF-2026-000986", "被骗", "「结婚，但是同年被骗了 10 几万」", "被骗损失，不等同负债"),
    # --- debt：事件级误判，不改变案例标签 ---
    ("debt", "否定语境（事件级）", "RF-2026-000970", "负债",
     "「幸而父母无负债」（同案例另有「2019 至今持续负债」）", "该事件为否定句；案例仍因自身负债判 1"),
    # --- health：标签会从 1 变成 0 的误判 ---
    ("serious_health", "第三人称（家属疾病）", "RF-2026-000026", "重病", "「父亲突发重病」+「我爸旧病复发又住院，做了手术」", "父亲患病，非命主"),
    ("serious_health", "第三人称（家属疾病）", "RF-2026-000031", "手术", "「母亲 2023 年做过手术」", "母亲手术，非命主"),
    ("serious_health", "第三人称（家属疾病）", "RF-2026-000056", "住院", "「父亲胃出血住院」", "父亲住院，非命主"),
    ("serious_health", "第三人称（家属疾病）", "RF-2026-000067", "癌", "「我爸…误诊癌症。但也确诊了糖尿病和胰腺炎」（爸爸）", "父亲患病，非命主"),
    ("serious_health", "第三人称（家属疾病）", "RF-2026-000137", "癌", "「姥爷查出脑梗，姥姥查出癌症」", "祖辈患病，非命主"),
    ("serious_health", "第三人称（家属疾病）", "RF-2026-000139", "住院", "「父亲摔着，住院」", "父亲住院，非命主"),
    ("serious_health", "第三人称（家属疾病）", "RF-2026-000192", "癌", "「2020 年母亲患癌」", "母亲患病，非命主（同事件「4 次流产」未命中）"),
    ("serious_health", "第三人称（家属疾病）", "RF-2026-000251", "重病", "「父亲生患重病」", "父亲患病，非命主"),
    ("serious_health", "第三人称（家属疾病）", "RF-2026-000267", "手术", "「父亲在该年动手术，后因病情恶化离世」", "父亲手术，非命主"),
    ("serious_health", "第三人称（家属疾病）", "RF-2026-000284", "癌", "「婆婆**癌」+「小的生病住院」", "亲属患病，非命主"),
    ("serious_health", "第三人称（家属疾病）", "RF-2026-000286", "住院", "「妈妈生病住院差点离世」", "母亲住院，非命主"),
    ("serious_health", "第三人称（家属疾病）", "RF-2026-000287", "住院", "「妈妈生病住院差点离世」", "母亲住院，非命主"),
    ("serious_health", "第三人称（家属疾病）", "RF-2026-000291", "癌", "繁体「兄長癌病去世」", "兄长患病，非命主（且为繁体）"),
    ("serious_health", "第三人称（家属疾病）", "RF-2026-000306", "癌", "「父亲癌症去世」", "父亲患病，非命主"),
    ("serious_health", "第三人称（家属疾病）", "RF-2026-000339", "中风", "「父亲得的一场中风…半边偏瘫」", "父亲中风，非命主"),
    ("serious_health", "第三人称（家属疾病）", "RF-2026-000353", "重病", "「妈妈重病」", "母亲重病，非命主"),
    ("serious_health", "第三人称（家属疾病）", "RF-2026-000354", "癌", "「婆婆身体出现大问题（晚期癌症）」", "婆婆患病，非命主"),
    ("serious_health", "第三人称（家属疾病）", "RF-2026-000356", "住院", "「母亲生病住院」+「父亲生病住院」", "父母住院，非命主"),
    ("serious_health", "第三人称（家属疾病）", "RF-2026-000359", "手术", "「母亲生病住院」+「父亲生病住院，和母亲一样的手术」", "父母手术，非命主"),
    ("serious_health", "第三人称（家属疾病）", "RF-2026-000361", "手术", "「父亲住院手术」", "父亲手术，非命主"),
    ("serious_health", "第三人称（家属疾病）", "RF-2026-000362", "手术", "「父亲住院做手术，到处筹钱」", "父亲手术，非命主"),
    ("serious_health", "第三人称（家属疾病）", "RF-2026-000435", "癌", "「初恋胃癌去世」", "伴侣患病，非命主"),
    ("serious_health", "第三人称（家属疾病）", "RF-2026-000461", "癌", "「爷爷肺癌去世（后爷爷）」", "祖父患病，非命主（同事件自身骨折未命中）"),
    ("serious_health", "第三人称（家属疾病）", "RF-2026-000462", "癌", "「爷爷肺癌去世（后爷爷）」", "祖父患病，非命主（与 000461 内容重复）"),
    ("serious_health", "第三人称（家属疾病）", "RF-2026-000475", "手术", "「父亲胃癌，动手术」", "父亲手术，非命主"),
    ("serious_health", "第三人称（家属疾病）", "RF-2026-000498", "住院", "「家里人除了父亲都住院几天」", "家人住院，非命主"),
    ("serious_health", "第三人称（家属疾病）", "RF-2026-000537", "瘫痪", "「父亲脑基底动脉瘤…无法手术，全身瘫痪」", "父亲瘫痪，非命主"),
    ("serious_health", "第三人称（家属疾病）", "RF-2026-000538", "瘫痪", "「父亲基底脑脑动脉瘤…全身瘫痪」", "父亲瘫痪，非命主"),
    ("serious_health", "第三人称（家属疾病）", "RF-2026-000551", "手术", "「妈妈生病了…也动了个小手术」", "母亲手术，非命主"),
    ("serious_health", "第三人称（家属疾病）", "RF-2026-000577", "手术", "「妈妈肌瘤做手术，年中又做了一次」", "母亲手术，非命主"),
    ("serious_health", "第三人称（家属疾病）", "RF-2026-000584", "癌", "「父亲肺癌去世」", "父亲患病，非命主"),
    ("serious_health", "第三人称（家属疾病）", "RF-2026-000601", "癌", "「母亲**癌」", "母亲患病，非命主"),
    ("serious_health", "第三人称（家属疾病）", "RF-2026-000607", "癌", "「父亲癌症手术」", "父亲手术，非命主"),
    ("serious_health", "第三人称（家属疾病）", "RF-2026-000610", "癌", "「父亲肝癌早逝」", "父亲患病，非命主"),
    ("serious_health", "第三人称（家属疾病）", "RF-2026-000611", "癌", "「父亲肝癌离世」", "父亲患病，非命主"),
    ("serious_health", "第三人称（家属疾病）", "RF-2026-000633", "手术", "「老爹给我办休学的时候晕倒了…最后开刀手术」", "父亲手术，非命主"),
    ("serious_health", "第三人称（家属疾病）", "RF-2026-000660", "重病", "「母亲重病…母亲病逝」", "母亲重病，非命主"),
    ("serious_health", "第三人称（家属疾病）", "RF-2026-000804", "住院", "「不是老婆生病住院，就是幺儿生病住院」", "妻儿住院，非命主"),
    ("serious_health", "第三人称（家属疾病）", "RF-2026-000864", "癌", "「父亲癌症复发去世」", "父亲患病，非命主（「女儿出生」未命中）"),
    ("serious_health", "第三人称（家属疾病）", "RF-2026-000878", "重病", "「出生那年我妈重病差点没生下我」", "母亲孕期患病；语义可议，按字面非命主自身"),
    ("serious_health", "第三人称（家属疾病）", "RF-2026-000893", "重病", "「母亲重病，家里积蓄几乎没了」", "母亲重病，非命主"),
    ("serious_health", "第三人称（家属疾病）", "RF-2026-000900", "大病", "「父亲生大病」", "父亲患病，非命主"),
    ("serious_health", "第三人称（家属疾病）", "RF-2026-000916", "癌", "「母亲**癌」", "母亲患病，非命主"),
    ("serious_health", "第三人称（家属疾病）", "RF-2026-000917", "癌", "「该年父亲检查出结肠癌」", "父亲患病，非命主"),
    ("serious_health", "第三人称（家属疾病）", "RF-2026-000952", "癌", "「五月母亲癌症去世」", "母亲患病，非命主"),
    ("serious_health", "第三人称（家属疾病）", "RF-2026-000953", "癌", "「母亲癌症去世」", "母亲患病，非命主"),
    ("serious_health", "第三人称（家属疾病）", "RF-2026-000963", "心脏病", "「妈妈被查出心脏病，好在手术后康复」", "母亲手术，非命主"),
    ("serious_health", "第三人称（家属疾病）", "RF-2026-000972", "心脏病", "「妈妈心脏病去世」", "母亲患病，非命主"),
    ("serious_health", "第三人称（家属疾病）", "RF-2026-000979", "手术", "「外婆生病动手术」", "外婆手术，非命主"),
    ("serious_health", "第三人称（家属疾病）", "RF-2026-000980", "手术", "「爸爸在工地手术，动了手术」", "父亲手术，非命主"),
    # --- health：非危重手术 ---
    ("serious_health", "非危重手术（小手术/微创等）", "RF-2026-000084", "手术", "「上半年做了一个小手术」", "小手术，不宜等同严重健康事件"),
    ("serious_health", "非危重手术（小手术/微创等）", "RF-2026-000118", "手术", "「双膝髌骨粉碎性骨折，动手术打了钢板和钢钉」", "意外骨折内固定；严重性可议"),
    ("serious_health", "非危重手术（小手术/微创等）", "RF-2026-000121", "手术", "「做疝气手术」+「疝气复发…动手术」", "疝气手术，常规非危重"),
    ("serious_health", "非危重手术（小手术/微创等）", "RF-2026-000193", "手术", "「疝气微创手术」", "微创疝气手术"),
    ("serious_health", "非危重手术（小手术/微创等）", "RF-2026-000329", "手术", "「动小手术」", "小手术"),
    ("serious_health", "非危重手术（小手术/微创等）", "RF-2026-000363", "手术", "「做的阑尾炎手术」", "阑尾炎手术，常规非危重"),
    ("serious_health", "非危重手术（小手术/微创等）", "RF-2026-000438", "手术", "「09 年还做了一个小手术」", "小手术"),
    ("serious_health", "非危重手术（小手术/微创等）", "RF-2026-000474", "手术", "「体检查出**结节，动了手术」", "结节切除，非危重"),
    ("serious_health", "非危重手术（小手术/微创等）", "RF-2026-000493", "手术", "「急性阑尾炎做了微创手术」", "微创阑尾手术"),
    ("serious_health", "非危重手术（小手术/微创等）", "RF-2026-000590", "手术", "「期间还做了一个小手术」", "小手术"),
    ("serious_health", "非危重手术（小手术/微创等）", "RF-2026-000593", "手术", "「急性阑尾炎做了个手术」", "阑尾炎手术"),
    ("serious_health", "非危重手术（小手术/微创等）", "RF-2026-000617", "手术", "「做了一个小手术」", "小手术"),
    ("serious_health", "非危重手术（小手术/微创等）", "RF-2026-000667", "手术", "「中耳炎手术（需开刀，留下疤痕）」", "中耳炎手术，非危重"),
    ("serious_health", "非危重手术（小手术/微创等）", "RF-2026-000668", "手术", "「中耳炎手术」", "中耳炎手术，非危重（与 000667 内容重复）"),
    ("serious_health", "非危重手术（小手术/微创等）", "RF-2026-000677", "手术", "「15 年底 16 年初做了扁桃体切除手术」", "扁桃体切除，且事件 polarity=positive"),
    ("serious_health", "非危重手术（小手术/微创等）", "RF-2026-000837", "手术", "「做过暖巢囊肿手术，术后恢复健康」", "囊肿手术，非危重"),
    ("serious_health", "非危重手术（小手术/微创等）", "RF-2026-000838", "手术", "「甲状腺结节微创手术」", "微创结节手术"),
    ("serious_health", "非危重手术（小手术/微创等）", "RF-2026-000934", "手术", "「脚踝韧带断裂动手术」", "运动损伤手术"),
    ("serious_health", "非危重手术（小手术/微创等）", "RF-2026-000984", "手术", "「右手臂骨折脱臼…两个月后动手术」", "骨折手术，严重性可议"),
    # --- health：否定 / 未实际发生 ---
    ("serious_health", "否定 / 未发生", "RF-2026-000235", "大病", "「健康良好无大病」", "否定句，按语义应为 0"),
    ("serious_health", "否定 / 未发生", "RF-2026-000308", "住院", "「严重药物过敏反应，差点住院」", "「差点」未实际住院，按语义应为 0"),
)

# 20 例人工抽查：(case_id, debt, serious_health, 人工结论)。
# 结论来自逐例阅读事件原文并回 JSONL 核对；标签不一致说明数据或规则变了，本模块拒绝覆盖产物。
AUDIT_SAMPLES: tuple[tuple[str, int | None, int | None, str], ...] = (
    ("RF-2026-000001", 0, 1, "合理：同一事件跨 income/health 域；ICU/抢救/病危是本人事实"),
    ("RF-2026-000002", None, None, "提问排除：income 事件整段是提问（「什么时候能发财？」）→ null；health 无事件 → null"),
    ("RF-2026-000003", None, None, "合理：两域都没有事件 → 双 null，未折成 0；仅出生日期，chart_ready=false"),
    ("RF-2026-000013", None, None, "提问排除：health 文本含「肿瘤」但整段是提问 → null（偏保守）"),
    ("RF-2026-000016", None, 0, "合理：health 有证据事件但零命中 → 0；debt 无事件 → null（0 与 null 不混）"),
    ("RF-2026-000017", 0, 0, "合理：出生只有日期（农历换算后），chart_ready=false，标签照算"),
    ("RF-2026-000034", 1, 0, "合理：贷款过多 + 信用卡还款为本人债务"),
    ("RF-2026-000048", 1, None, "存疑：家庭购房贷款被记为债务 → §7"),
    ("RF-2026-000067", None, 1, "存疑：父亲癌症（且误诊），非命主本人 → §7"),
    ("RF-2026-000079", None, None, "提问排除：income 文本含「负债」但带问号 → null（偏保守）"),
    ("RF-2026-000118", 0, 1, "合理（偏宽）：骨折内固定手术，严重性可议 → §7"),
    ("RF-2026-000137", 0, 1, "存疑：姥姥癌症/姥爷脑梗，非命主本人 → §7"),
    ("RF-2026-000235", None, 1, "存疑：「健康良好无大病」是否定句 → §7"),
    ("RF-2026-000243", 1, 0, "存疑：家里贷款买房 + 父亲百万贷款，非命主本人 → §7"),
    ("RF-2026-000308", 0, 1, "存疑：「差点住院」未实际发生 → §7"),
    ("RF-2026-000531", 1, None, "存疑：妈妈被骗，非命主负债 → §7"),
    ("RF-2026-000572", 0, 1, "合理：重度抑郁精神科住院为本人事实；「近视手术」非严重"),
    ("RF-2026-000633", 0, 1, "存疑：父亲晕倒后开刀手术，非命主本人 → §7"),
    ("RF-2026-000681", 1, 1, "混合：health 为本人摔伤抢救（合理）；debt 为儿子欠债（存疑 → §7）"),
    ("RF-2026-000918", 1, 0, "存疑：「欠款要不上来」是应收款，不是命主欠债 → §7"),
)


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


def _audit_rows(cases: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id = {row["case_id"]: row for row in cases}
    missing = [case_id for case_id, _, _, _ in AUDIT_SAMPLES if case_id not in by_id]
    if missing:
        raise AuditError(f"抽查案例不在基础集：{', '.join(missing)}")
    rows = []
    for case_id, debt, health, verdict in AUDIT_SAMPLES:
        row = by_id[case_id]
        if row["labels"]["debt"] != debt or row["labels"]["serious_health"] != health:
            raise AuditError(
                f"{case_id} 标签为 debt={row['labels']['debt']!r} / "
                f"serious_health={row['labels']['serious_health']!r}，"
                f"冻结期望 debt={debt!r} / serious_health={health!r}"
            )
        rows.append(
            {
                "case_id": case_id,
                "chart_ready": row["chart_ready"],
                "debt": row["labels"]["debt"],
                "serious_health": row["labels"]["serious_health"],
                "events": row["evidence_events"],
                "verdict": verdict,
            }
        )
    return rows


def check_known_issues(cases: Sequence[dict[str, Any]]) -> None:
    """已知误判清单必须仍可在当前数据里复核（案例存在、标签为 1、命中词仍命中）。"""
    by_id = {row["case_id"]: row for row in cases}
    problems: list[str] = []
    for key, _kind, case_id, keyword, _phenomenon, _verdict in KNOWN_ISSUES:
        row = by_id.get(case_id)
        if row is None:
            problems.append(f"{case_id} 不在基础集")
            continue
        if row["labels"][key] != 1:
            problems.append(f"{case_id} 的 {key} 标签不是 1")
            continue
        matched = {
            hit
            for entry in row["evidence_events"]
            if entry["label_key"] == key
            for hit in entry["matched"]
        }
        if keyword not in matched:
            problems.append(f"{case_id} 未再命中「{keyword}」")
    if problems:
        raise AuditError("；".join(problems))


def check_audit_samples(cases: Sequence[dict[str, Any]]) -> None:
    """20 例抽查的冻结标签必须复现（数量固定 20）。"""
    if len(AUDIT_SAMPLES) != 20:
        raise AuditError(f"抽查样本应为 20 例，实际 {len(AUDIT_SAMPLES)} 例")
    _audit_rows(cases)


def render_report(payload: Mapping[str, Any], cases: Sequence[dict[str, Any]]) -> str:
    counts = payload["counts"]
    source = payload["source"]
    lines: list[str] = []
    add = lines.append

    add("# T-158 · 财富 / 健康结局标签 v1（`debt` / `serious_health`）")
    add("")
    add(f"- 数据源：`{source['path']}`（{source['records']} 条，sha256 `{source['sha256']}`）")
    add(f"- 生成脚本：`{SCRIPT}`")
    add(f"- 定义冻结日：`{payload['frozen_at']}`（预注册日；**不是**运行时间戳）")
    add(
        "- 性质：**结果变量，不是预测**。标签只来自 `income` / `health` 事件的文本关键词与 polarity 记录，"
        "**不使用任何八字 / 盘面 / 排盘字段**（防泄漏，任务卡 §2.1 / §5）。"
        "本文件无运行时间戳，重复运行逐字节一致。"
    )
    add("")

    add("## 1. 冻结定义（任务卡 §2，预注册，不得中途改）")
    add("")
    add("基础集：`duplicate_key` 全等去重（保留首次出现）+ `gender ∈ {男, 女}` + 出生日期可解析。"
        "`chart_ready` = 出生时刻可解析（只标记，不建盘）。")
    add("")
    add("- **debt = 1**：任一**非提问** `income` 事件文本命中债务关键词。")
    add("- **debt = 0**：有 `income` 证据事件（非提问、非空文本），但零关键词命中。")
    add("- **debt = null**：无 `income` 证据事件（无该域事件 / 全是提问 / 无文本）→ 该域排除，**不折入 0 或 1**。")
    add("- **serious_health** 同构，域换成 `health`，关键词换成严重健康关键词。")
    add("- **1 优先**：同一案例既有命中事件又有未命中事件 → `1`（存在性标签），计数单列 `conflict`。")
    add("- **提问不算证据**：事件文本含 "
        + "、".join(f"`{marker}`" for marker in QUESTION_MARKERS)
        + " 任一 → **整段**不作证据（字面子串匹配，不还原问句语义）。")
    add("")
    add("债务关键词（原样冻结）：" + "、".join(f"`{kw}`" for kw in DEBT_KEYWORDS))
    add("")
    add("严重健康关键词（原样冻结）：" + "、".join(f"`{kw}`" for kw in SERIOUS_HEALTH_KEYWORDS))
    add("")
    add(
        "> `polarity` 只随事件记录并参与审计，**不参与判定**：卡片 §2.2 / §2.3 是纯关键词规则。"
        "语料里「么」大量出现在「什么 / 怎么 / 这么」中，按字面规则一律先判提问；"
        "这个方向的误差只会把证据变成排除（null），不会把提问当证据。"
    )
    add("")

    add("## 2. 漏斗（992 → 959 → 950 / 952 → 947）")
    add("")
    lines.extend(
        _table(
            ["阶段", "条数", "口径"],
            [
                ["原始记录", counts["records_total"], "JSONL 行数"],
                ["按 duplicate_key 去重", counts["after_dedupe"], "保留首次出现"],
                ["有性别", counts["with_gender"], "在去重后的 959 上过滤"],
                ["出生日期可解析", counts["birth_date_parsable"], "在去重后的 959 上独立过滤"],
                ["出生时刻可解析", counts["birth_time_parsable"], "日期可解析且有时刻"],
                ["**基础集（三条件交集）**", f"**{counts['base_sample']}**", "去重 + 性别 + 日期"],
                ["**chart_ready**", f"**{counts['base_chart_ready']}**", "基础集内出生时刻可解析"],
            ],
        )
    )
    add("")
    add(
        "读法：`有性别 950` / `日期 952` / `时刻 947` 都是在 **959** 上的独立过滤，**不是嵌套漏斗**；"
        f"三者交集才是可打标的基础集 **{counts['base_sample']}** 例（其中 {counts['base_chart_ready']} 例可建盘）。"
        f"基础集之外 {payload['audit']['base_excluded']['total']} 例（理由："
        + "、".join(
            f"{reason} {number} 例" for reason, number in payload["audit"]["base_excluded"]["by_reason"].items()
        )
        + "）。"
    )
    add("")
    domain_rows = []
    for spec in LABEL_SPECS:
        domain = payload["audit"]["domain"][spec.key]
        domain_rows.append(
            [
                spec.key,
                f"`{spec.domain}`",
                domain["cases_with_domain_events"],
                domain["events_total"],
                domain["events_question"],
                domain["events_empty_text"],
                domain["events_evidence"],
            ]
        )
    lines.extend(
        _table(
            ["标签", "域", "有该域事件的案例", "事件数", "提问事件", "空文本事件", "证据事件"],
            domain_rows,
        )
    )
    add("")
    add(
        "事件口径与任务卡 §1 一致：`income` 606 事件 / 377 案例，`health` 659 事件 / 453 案例（均为去重后）。"
    )
    add("")

    add("## 3. 标签计数（1 / 0 / null；四桶可加）")
    add("")
    count_rows = []
    for spec in LABEL_SPECS:
        block = counts[spec.key]
        ready = block["chart_ready"]
        count_rows.append(
            [
                spec.key,
                block["1"],
                block["0"],
                block["null"],
                block["sum"],
                ready["1"],
                ready["0"],
                ready["null"],
                ready["sum"],
            ]
        )
    lines.extend(
        _table(
            ["标签", "1（全集）", "0（全集）", "null（全集）", "合计（全集）",
             "1（chart_ready）", "0（chart_ready）", "null（chart_ready）", "合计（chart_ready）"],
            count_rows,
        )
    )
    add("")
    for spec in LABEL_SPECS:
        block = counts[spec.key]
        ready = block["chart_ready"]
        assert block["1"] + block["0"] + block["null"] == block["sum"]
        assert ready["1"] + ready["0"] + ready["null"] == ready["sum"]
        add(
            f"- `{spec.key}` 可加校验：{block['sum']} = {block['1']}+{block['0']}+{block['null']}；"
            f"chart_ready {ready['sum']} = {ready['1']}+{ready['0']}+{ready['null']}。"
        )
    add("")
    reason_rows = []
    for spec in LABEL_SPECS:
        reasons = payload["labels"][spec.key]["null_reasons"]
        conflict = payload["labels"][spec.key]["conflict_cases"]
        reason_rows.append(
            [
                spec.key,
                reasons["no_domain_event"],
                reasons["all_question"],
                reasons["no_text"],
                counts[spec.key]["null"],
                conflict,
            ]
        )
    lines.extend(
        _table(
            ["标签", "null：无该域事件", "null：全是提问", "null：无文本", "null 合计", "混合证据（1 优先）案例"],
            reason_rows,
        )
    )
    add("")
    add(
        "> `null` 的两大来源都是「没有证据」：该案例根本没有这个域的事件，或该域事件全带提问标记。"
        "任务卡 §2.4 要求 `null` 超 30% 时按原因分类；本版两个标签的 null 占比为 "
        + "、".join(
            f"`{spec.key}` {_pct(payload['baseline'][spec.key]['null_share_pct']['base'])}（全集）/ "
            f"{_pct(payload['baseline'][spec.key]['null_share_pct']['chart_ready'])}（chart_ready）"
            for spec in LABEL_SPECS
        )
        + "，因此一并给出上述分类。"
    )
    add("")

    add("## 4. 阳性率与基线")
    add("")
    baseline_rows = []
    for spec in LABEL_SPECS:
        item = payload["baseline"][spec.key]
        ready = item["chart_ready"]
        base = item["base_reference"]
        baseline_rows.append(
            [
                spec.key,
                ready["sample_size"],
                ready["positive"],
                ready["negative"],
                _pct(ready["positive_rate_pct"]),
                base["sample_size"],
                base["positive"],
                base["negative"],
                _pct(base["positive_rate_pct"]),
            ]
        )
    lines.extend(
        _table(
            ["标签", "n（chart_ready）", "1", "0", "阳性率（验收口径）", "n（全集）", "1", "0", "阳性率（仅参考）"],
            baseline_rows,
        )
    )
    add("")
    add(
        "口径：分母 = 该标签非 `null` 的案例（`1+0`），`null` 不进分母；"
        "主口径为 `chart_ready=true`，全集数字只作参考。后续 T-160 评分必须用同一口径基线。"
    )
    add("")

    add("## 5. 关键词命中与提问排除")
    add("")
    add("### 5.1 关键词命中（只统计被采纳的证据事件）")
    add("")
    keyword_rows = []
    for spec in LABEL_SPECS:
        hits = payload["audit"]["keyword_hits"][spec.key]
        for keyword in spec.keywords:
            keyword_rows.append(
                [f"`{spec.key}`", f"`{keyword}`", hits["events"][keyword], hits["cases"][keyword]]
            )
    lines.extend(_table(["标签", "关键词", "命中事件数", "命中案例数"], keyword_rows))
    add("")
    add(
        "合计："
        + "；".join(
            f"`{spec.key}` 命中事件 {payload['audit']['keyword_hits'][spec.key]['events_total']} 次、"
            f"命中案例 {payload['audit']['keyword_hits'][spec.key]['cases_any']} 例"
            for spec in LABEL_SPECS
        )
        + "（同一事件可命中多个关键词；`负债` 是 `负债累累` 的子串，二者会同时计数）。"
    )
    add("")
    add("### 5.2 提问标记命中（该域事件，可多选）")
    add("")
    marker_rows = []
    for spec in LABEL_SPECS:
        markers = payload["audit"]["question"][spec.key]["markers"]
        marker_rows.append([f"`{spec.key}`"] + [markers[marker] for marker in QUESTION_MARKERS])
    lines.extend(_table(["标签 / 标记"] + [f"`{m}`" for m in QUESTION_MARKERS], marker_rows))
    add("")
    add(
        "> 「么」命中最多是语料特性（「什么 / 怎么 / 这么」），按冻结规则一律整段降级为提问；"
        "方向偏保守，不会把提问当证据。"
    )
    add("")
    add("### 5.3 被提问规则抑制的关键词证据")
    add("")
    suppressed_rows = []
    for spec in LABEL_SPECS:
        block = payload["audit"]["question"][spec.key]
        suppressed_rows.append(
            [f"`{spec.key}`", block["suppressed_events"], block["suppressed_cases"]]
        )
    lines.extend(_table(["标签", "含关键词的提问事件", "涉及案例"], suppressed_rows))
    add("")
    for spec in LABEL_SPECS:
        block = payload["audit"]["question"][spec.key]
        if not block["suppressed"]:
            continue
        add(f"`{spec.key}` 被抑制明细（{block['suppressed_events']} 条事件）：")
        add("")
        lines.extend(
            _table(
                ["case_id", "年份", "polarity", "标记", "被抑制关键词", "文本摘要"],
                [
                    [
                        item["case_id"],
                        item["year"],
                        item["polarity"],
                        "".join(f"`{marker}`" for marker in item["markers"]),
                        "、".join(item["keywords"]),
                        item["text"],
                    ]
                    for item in block["suppressed"]
                ],
            )
        )
        add("")
    add(
        "> 这些案例的该条事件里有陈述式的债务 / 健康事实（如「2011 年结节做手术」），"
        "但整段含提问标记，按冻结规则不采证；相关案例因此落到 `0` 或 `null`（取决于是否还有别的证据事件）。"
    )
    add("")
    add("### 5.4 事件 polarity 分布（只记录，不参与判定）")
    add("")
    polarity_rows = []
    for spec in LABEL_SPECS:
        polarity = payload["audit"]["domain"][spec.key]["polarity_events"]
        polarity_rows.append(
            [f"`{spec.key}`", polarity["negative"], polarity["positive"], polarity["unknown"],
             polarity["other"], sum(polarity.values())]
        )
    lines.extend(_table(["标签", "negative", "positive", "unknown", "三值之外", "合计"], polarity_rows))
    add("")
    add(
        "`negative` 事件的文本也可能零关键词（抑郁、破财、感情不顺等），这类案例记 `0`；"
        "反之 `positive` 事件里也常有负债（如「吉，买房背贷款」），这类案例记 `1`。"
        "标签只看有没有命中，不看吉凶。"
    )
    add("")

    add("## 6. 20 例人工抽查")
    add("")
    add(
        "抽查方式：按 `case_id` 回 `cases/raw_feedback/parsed/real_cases_990.jsonl` 逐例核对 "
        "`income` / `health` 事件的 `year / polarity / text`，并复算标签。20/20 与冻结结论一致。"
    )
    add("")
    audit_rows = _audit_rows(cases)
    audit_table = []
    for index, row in enumerate(audit_rows, start=1):
        audit_table.append(
            [
                index,
                row["case_id"],
                "是" if row["chart_ready"] else "否",
                _label_text(row["debt"]),
                _label_text(row["serious_health"]),
                row["verdict"],
            ]
        )
    lines.extend(_table(["#", "case_id", "chart_ready", "debt", "serious_health", "结论"], audit_table))
    add("")
    add(
        "结论列：**合理** = 规则与原文一致；**存疑** = 规则产出与语义不一致（见 §7），本版**不**就地改判；"
        "**提问排除** = 该域事件全带提问标记或关键事件被抑制，标签落到 null/0，方向偏保守。"
    )
    add("")

    add("## 7. 已知误判（人工核查；按预注册规则保留原判，未就地改词）")
    add("")
    kind_totals: dict[tuple[str, str], int] = {}
    for key, kind, _case_id, _keyword, _phenomenon, _verdict in KNOWN_ISSUES:
        kind_totals[(key, kind)] = kind_totals.get((key, kind), 0) + 1
    lines.extend(
        _table(
            ["标签", "类型", "案例数", "标签影响"],
            [
                [
                    f"`{key}`",
                    kind,
                    number,
                    "事件级，不改变案例标签" if "事件级" in kind else "该案例标签会从 1 变成 0",
                ]
                for (key, kind), number in kind_totals.items()
            ],
        )
    )
    add("")
    debt_total = sum(number for (key, kind), number in kind_totals.items()
                     if key == "debt" and "事件级" not in kind)
    health_total = sum(number for (key, kind), number in kind_totals.items()
                       if key == "serious_health" and "事件级" not in kind)
    add(
        f"合计：`debt` 可翻转型误判 **{debt_total}** 例，`serious_health` **{health_total}** 例"
        f"（另有 `debt` 事件级误判 1 例，不改变标签）。"
        "这些是**规则本身的边界**（第三人称 / 房贷 / 亏损 / 应收款 / 公司破产 / 小手术 / 否定句），"
        "不是实现 bug：卡片冻结的关键词表与判定顺序不允许现场加否定、主体识别或严重度分级。"
    )
    add("")
    lines.extend(
        _table(
            ["标签", "类型", "case_id", "命中词", "原文摘要", "按语义应为"],
            [
                [
                    f"`{key}`",
                    kind,
                    case_id,
                    f"`{keyword}`",
                    phenomenon,
                    verdict,
                ]
                for key, kind, case_id, keyword, phenomenon, verdict in KNOWN_ISSUES
            ],
        )
    )
    add("")
    add(
        "> 若中枢决定出 v2，建议按上表类型分别处理（第三人称主体识别、房贷/应收款/公司破产降级、"
        "手术严重度分级、否定句抑制），并**重新预注册**关键词与规则，而不是在本版上就地调词。"
    )
    add("")

    add("## 8. 复现与不变量")
    add("")
    add("```bash")
    add(".venv\\Scripts\\python.exe -m tools.domain_labels_wealth_health")
    add(".venv\\Scripts\\python.exe -m pytest tests/tools/test_domain_labels_wealth_health.py -q -o addopts=\"-ra --tb=short\"")
    add("```")
    add("")
    add(
        f"- 漏斗不变量：{counts['records_total']} / {counts['after_dedupe']} / {counts['with_gender']} / "
        f"{counts['birth_date_parsable']} / {counts['birth_time_parsable']}；"
        f"基础集 {counts['base_sample']}，chart_ready {counts['base_chart_ready']}。"
    )
    add(
        f"- 四桶不变量："
        + "；".join(
            f"`{spec.key}` {counts[spec.key]['sum']} = {counts[spec.key]['1']}+{counts[spec.key]['0']}"
            f"+{counts[spec.key]['null']}"
            for spec in LABEL_SPECS
        )
        + "。"
    )
    add(f"- JSON `payload_sha256`：`{payload['payload_sha256']}`")
    add("- 无运行时间戳、不读盘面事实、不建盘、不写评测集；两次运行输出逐字节一致。")
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


def main() -> int:
    try:
        records = load_source()
        source_sha = _sha256_file(SOURCE_PATH)
        payload, cases, _excluded = build_payload(records, source_path=SOURCE_PATH, source_sha256=source_sha)
        check_invariants(payload)
        check_known_issues(cases)
        check_audit_samples(cases)
        report = render_report(payload, cases)
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
    print("T-158 domain-labels-wealth-health v1")
    print(
        f"  source   : {payload['source']['path']} sha256={payload['source']['sha256'][:12]}… "
        f"records={counts['records_total']}"
    )
    print(
        f"  funnel   : {counts['records_total']} → {counts['after_dedupe']} → "
        f"gender={counts['with_gender']} date={counts['birth_date_parsable']} "
        f"time={counts['birth_time_parsable']} | base={counts['base_sample']} "
        f"chart_ready={counts['base_chart_ready']}"
    )
    for spec in LABEL_SPECS:
        block = counts[spec.key]
        ready = block["chart_ready"]
        baseline = payload["baseline"][spec.key]
        print(
            f"  {spec.key:<14} : 1={block['1']} 0={block['0']} null={block['null']} "
            f"(sum={block['sum']}) | chart_ready 1={ready['1']} 0={ready['0']} null={ready['null']} "
            f"| rate={_pct(baseline['chart_ready']['positive_rate_pct'])} "
            f"n={baseline['chart_ready']['sample_size']}"
        )
    print(f"  wrote    : META/domain-labels-wealth-health-v1.json sha256={_sha256_file(JSON_PATH)[:12]}…")
    print("           : META/domain-labels-wealth-health-v1.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

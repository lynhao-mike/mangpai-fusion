"""T-153 · 婚姻质量标签 v1（负面婚姻事件二值标签）。

把「婚姻形态 A–E」换成「有没有负面婚姻事件」的二值结果变量。标签**只**来自
``marriage_events[].polarity`` 与事件文本关键词；**不读取任何盘面/八字特征**（防泄漏）。

产物（确定性，无运行时间戳，重复运行逐字节一致）：

* ``META/marriage-quality-labels-v1.json``  机器可读标签（411 例逐例 + 计数 + 基线）
* ``META/marriage-quality-labels-v1.md``    人读审计报告（计数 / 关键词 / 提问 / 冲突 / 20 例抽查）

定义由任务卡 §2 预注册，本模块不改关键词、不改判定顺序。用法::

    python -m tools.marriage_quality_labels

退出码：0 通过；2 评测集不可读或 schema 不符；3 计数不变量不复现（411 / 382）；
4 人工抽查样本的标签与冻结结论不符（需重审）。

口径（与任务卡 §2 逐条对应）：

* 负证据：``polarity == "negative"``；或 ``polarity == "unknown"`` 且非提问文本命中负面关键词。
* 正证据：``polarity == "positive"``；或 ``polarity == "unknown"`` 且非提问文本命中正面关键词。
* negative 优先：两类证据并存时标签为 negative，并在计数里单列 ``conflict`` 桶。
* unknown：无任何证据（全是提问 / 中性 / 无证据）→ 排除，不进分母。
* 提问判定只作用于 unknown 文本：含 ``？``、``?``、``是否``、``能否``、``请问``、``怎么样``、
  ``吗``、``么``、``呢`` 任一即**整段**不作关键词证据。同一案例的其余事件独立判定。
* ``polarity`` 出现三值之外的取值时按 unknown 处理，并单独计数（本版为 0）。
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
EVAL_PATH = ROOT / "META" / "timing-eval-set-v1.json"
JSON_PATH = ROOT / "META" / "marriage-quality-labels-v1.json"
REPORT_PATH = ROOT / "META" / "marriage-quality-labels-v1.md"

SCHEMA = "marriage-quality-labels/v1"
EVAL_SCHEMA = "timing-eval-set/v1"
TASK = "T-153"
SCRIPT = "tools/marriage_quality_labels.py"

# 定义冻结日 = 任务卡 §2 建卡日（预注册）。不是运行时间戳：本产物必须可逐字节复现。
FROZEN_AT = "2026-10-28"

# 计数不变量（任务卡 §1 / §6）。不满足即视为数据源变更，拒绝落盘。
EXPECTED_CASES = 411
EXPECTED_USABLE = 382

# 任务卡 §2 关键词表，原样冻结，禁止增删。
NEGATIVE_KEYWORDS = ("离婚", "离异", "丧偶", "亡夫", "亡妻", "再婚", "二婚", "三婚", "多婚", "婚变")
POSITIVE_KEYWORDS = ("结婚", "成婚", "登记结婚", "婚礼", "一婚", "婚姻稳定", "白头")

# 任务卡 §2 提问标记，原样冻结。字面匹配（子串），不还原问句语义。
QUESTION_MARKERS = ("？", "?", "是否", "能否", "请问", "怎么样", "吗", "么", "呢")

TEXT_SUMMARY_LIMIT = 80

# 20 例人工抽查：(case_id, 冻结标签, 人工结论)。结论来自逐例阅读事件原文并回 JSONL 核对；
# 标签不一致说明数据或规则变了，本模块拒绝覆盖产物，等人工重审。
AUDIT_SAMPLES: tuple[tuple[str, str, str], ...] = (
    ("RF-2026-000010", "unknown", "提问（？/是否）整段不采证；段内「2017 年结婚」被抑制 → 合理（偏保守）"),
    ("RF-2026-000038", "unknown", "提问（？/请问/吗）；「也没结婚」不是结婚证据 → 合理"),
    ("RF-2026-000050", "unknown", "提问（么）；「什么时候结婚生小孩合适」→ 合理"),
    ("RF-2026-000902", "unknown", "提问（？/能否）；「哪一年能结婚？」→ 合理"),
    ("RF-2026-000259", "unknown", "「老公起诉离婚」被后文「能否」整段抑制 → 存疑：偏保守"),
    ("RF-2026-000207", "unknown", "陈述「结婚其他信息…婚后一子」被「怎么样/么」抑制 → 存疑：偏保守"),
    ("RF-2026-000495", "positive", "「一直没结婚…婚礼不顺」命中「结婚」「婚礼」→ 存疑：否定语境误判"),
    ("RF-2026-000560", "positive", "「且未结婚」命中「结婚」→ 存疑：否定语境误判"),
    ("RF-2026-000509", "positive", "「未结婚」命中「结婚」→ 存疑：否定语境（不可评测，不进分母）"),
    ("RF-2026-000354", "negative", "极性 positive×1 + negative×2 → 冲突，negative 优先 → 合理"),
    ("RF-2026-000372", "negative", "极性 negative + 文本「结婚…2023 年离异」→ 冲突 → 合理"),
    ("RF-2026-000063", "negative", "单段「13 年结婚…16 年离婚」→ 冲突，negative 优先 → 合理"),
    ("RF-2026-000845", "negative", "正「11 月份结婚/刚结婚」+ 负「父母离异」→ 冲突判负 → 存疑：第三人称误判"),
    ("RF-2026-000528", "negative", "「再婚对象」（父）、「孙子结婚」→ 冲突判负 → 存疑：第三人称，均非命主"),
    ("RF-2026-000544", "negative", "「父母离婚」→ 存疑：第三人称，不是命主婚姻"),
    ("RF-2026-000728", "negative", "无极性，「2004 年离婚…2006 年二婚…2020 年二离」→ 关键词 → 合理"),
    ("RF-2026-000947", "unknown", "繁体「2020 離婚」未命中简体关键词 → 存疑：漏判"),
    ("RF-2026-000355", "positive", "繁体「離過婚(2021)」未命中，另有极性 positive → 存疑：漏判"),
    ("RF-2026-000081", "negative", "单一事件 polarity=negative（「婚姻很累」），无关键词 → 合理"),
    ("RF-2026-000066", "positive", "单一事件 polarity=positive（「找到对象」）→ 合理（上游事件域偏宽，见风险）"),
)

# 已知的规则误判 / 漏判（人工核查，按预注册规则保留原判，不就地改）。纯静态审计记录。
KNOWN_ISSUES: tuple[tuple[str, str, str, str], ...] = (
    ("否定语境", "RF-2026-000495", "「一直没结婚…婚礼不顺」命中「结婚」「婚礼」", "positive：否定语境不应算正面证据"),
    ("否定语境", "RF-2026-000560", "「且未结婚」命中「结婚」", "positive：同上"),
    ("否定语境", "RF-2026-000509", "「未结婚」命中「结婚」", "positive：同上（不可评测，不进分母）"),
    ("第三人称", "RF-2026-000544", "「父母离婚」命中「离婚」", "negative：非命主婚姻"),
    ("第三人称", "RF-2026-000528", "「再婚对象」（父）、「孙子结婚」", "conflict→negative：两处均非命主"),
    ("第三人称", "RF-2026-000845", "「父母离异」+「11 月份结婚」", "conflict→negative：按语义应为 positive"),
    ("繁体漏判", "RF-2026-000947", "繁体「2020 離婚」未命中简体「离婚」", "unknown：按语义应为 negative"),
    ("繁体漏判", "RF-2026-000355", "繁体「離過婚(2021)」未命中，另有极性 positive", "positive：按语义应为 negative"),
)


class EvalSetError(RuntimeError):
    """评测集不可读 / schema 不符。"""


class LabelInvariantError(RuntimeError):
    """计数不变量不复现。"""


class AuditError(RuntimeError):
    """人工抽查结论与当前数据不一致。"""


# ---------------------------------------------------------------------------
# 文本判定
# ---------------------------------------------------------------------------


def question_markers_in(text: str) -> tuple[str, ...]:
    """返回命中的提问标记（按冻结顺序，可多选）。"""
    return tuple(marker for marker in QUESTION_MARKERS if marker in text)


def keyword_hits(text: str, keywords: tuple[str, ...]) -> list[str]:
    """返回命中的关键词（按冻结顺序，可多选）。"""
    return [keyword for keyword in keywords if keyword in text]


def summarise_text(text: str) -> str:
    """压缩空白并截断到固定长度，供审计展示（确定性）。"""
    compact = " ".join(text.split())
    if len(compact) <= TEXT_SUMMARY_LIMIT:
        return compact
    return compact[:TEXT_SUMMARY_LIMIT] + "…"


def _extend_unique(target: list[str], items: list[str]) -> None:
    for item in items:
        if item not in target:
            target.append(item)


def _evidence_event(event: dict[str, Any], source: str, matched: list[str]) -> dict[str, Any]:
    return {
        "year": event.get("year"),
        "age": event.get("age"),
        "polarity": event.get("polarity"),
        "text": summarise_text(event.get("text") or ""),
        "source": source,
        "matched": list(matched),
    }


def _evidence_block(block: dict[str, Any], total: int) -> dict[str, Any]:
    return {
        "polarity": block["polarity"],
        "keyword": block["keyword"],
        "total": total,
        "keywords": list(block["keywords"]),
    }


# ---------------------------------------------------------------------------
# 逐例打标
# ---------------------------------------------------------------------------


def analyse_case(case: dict[str, Any]) -> dict[str, Any]:
    """按任务卡 §2 的顺序给单例打标。只读 marriage_events。"""
    events = case.get("marriage_events") or []
    evidence: list[dict[str, Any]] = []
    negative = {"polarity": 0, "keyword": 0, "keywords": []}
    positive = {"polarity": 0, "keyword": 0, "keywords": []}
    question_events = 0
    non_question_unknown = 0
    empty_text = 0

    for event in events:
        polarity = event.get("polarity")
        text = event.get("text") or ""

        if polarity == "negative":
            negative["polarity"] += 1
            evidence.append(_evidence_event(event, "polarity", []))
            continue
        if polarity == "positive":
            positive["polarity"] += 1
            evidence.append(_evidence_event(event, "polarity", []))
            continue

        # unknown（以及三值之外的取值）：先判提问，再判关键词。
        if not text.strip():
            empty_text += 1
            continue
        markers = question_markers_in(text)
        if markers:
            question_events += 1
            continue

        non_question_unknown += 1
        negative_hits = keyword_hits(text, NEGATIVE_KEYWORDS)
        positive_hits = keyword_hits(text, POSITIVE_KEYWORDS)
        if negative_hits:
            negative["keyword"] += 1
            _extend_unique(negative["keywords"], negative_hits)
        if positive_hits:
            positive["keyword"] += 1
            _extend_unique(positive["keywords"], positive_hits)
        if negative_hits or positive_hits:
            evidence.append(_evidence_event(event, "keyword", negative_hits + positive_hits))

    negative_total = negative["polarity"] + negative["keyword"]
    positive_total = positive["polarity"] + positive["keyword"]
    conflict = bool(negative_total and positive_total)

    if negative_total:
        label = "negative"
        basis = "polarity" if negative["polarity"] else "keyword"
    elif positive_total:
        label = "positive"
        basis = "polarity" if positive["polarity"] else "keyword"
    else:
        label = "unknown"
        basis = "none"

    if label == "unknown":
        if non_question_unknown:
            unknown_reason: str | None = "neutral"
        elif question_events:
            unknown_reason = "question"
        else:
            unknown_reason = "no_evidence"
    else:
        unknown_reason = None

    return {
        "case_id": case.get("case_id"),
        "usable_for_timing": bool(case.get("usable_for_timing")),
        "label": label,
        "negative": label == "negative",
        "basis": basis,
        "conflict": conflict,
        "unknown_reason": unknown_reason,
        "events_total": len(events),
        "events_question": question_events,
        "events_empty_text": empty_text,
        "negative_evidence": _evidence_block(negative, negative_total),
        "positive_evidence": _evidence_block(positive, positive_total),
        "evidence_events": evidence,
    }


# ---------------------------------------------------------------------------
# 计数
# ---------------------------------------------------------------------------


def _bucket_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    """互斥四桶：conflict 不计入 negative，保证四桶相加 = 样本量。"""
    negative = sum(1 for row in rows if row["label"] == "negative" and not row["conflict"])
    positive = sum(1 for row in rows if row["label"] == "positive")
    unknown = sum(1 for row in rows if row["label"] == "unknown")
    conflict = sum(1 for row in rows if row["conflict"])
    return {
        "negative": negative,
        "positive": positive,
        "unknown": unknown,
        "conflict": conflict,
        "sum": negative + positive + unknown + conflict,
    }


def _final_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    """最终标签：conflict 已按 negative 优先归入 negative。"""
    return {
        "negative": sum(1 for row in rows if row["label"] == "negative"),
        "positive": sum(1 for row in rows if row["label"] == "positive"),
        "unknown": sum(1 for row in rows if row["label"] == "unknown"),
    }


def _unknown_reason_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts = {"question": 0, "neutral": 0, "no_evidence": 0}
    for row in rows:
        if row["label"] == "unknown":
            counts[row["unknown_reason"]] += 1
    return counts


def _basis_counts(rows: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    result = {"negative": {"polarity": 0, "keyword": 0}, "positive": {"polarity": 0, "keyword": 0}}
    for row in rows:
        if row["label"] in ("negative", "positive"):
            result[row["label"]][row["basis"]] += 1
    return result


def _event_audit(cases: list[dict[str, Any]]) -> dict[str, Any]:
    """事件层审计：polarity 分布、unknown 拆分、关键词命中、提问标记、被抑制案例。"""
    subsets = ("all", "usable")
    polarity = {key: {"negative": 0, "positive": 0, "unknown": 0, "other": 0, "total": 0} for key in subsets}
    split = {
        key: {"question": 0, "non_question": 0, "empty_text": 0}
        for key in subsets
    }
    hits = {
        key: {"negative": {kw: 0 for kw in NEGATIVE_KEYWORDS}, "positive": {kw: 0 for kw in POSITIVE_KEYWORDS}}
        for key in subsets
    }
    markers = {marker: 0 for marker in QUESTION_MARKERS}
    suppressed: dict[str, dict[str, Any]] = {}

    for case in cases:
        case_id = case.get("case_id")
        usable = bool(case.get("usable_for_timing"))
        keys = ["all", "usable"] if usable else ["all"]
        for event in case.get("marriage_events") or []:
            raw_polarity = event.get("polarity")
            text = event.get("text") or ""
            polarity_key = raw_polarity if raw_polarity in ("negative", "positive", "unknown") else "other"
            for key in keys:
                polarity[key]["total"] += 1
                polarity[key][polarity_key] += 1
            if polarity_key != "unknown":
                continue

            event_markers = question_markers_in(text)
            if not text.strip():
                split_key = "empty_text"
            elif event_markers:
                split_key = "question"
            else:
                split_key = "non_question"
            for key in keys:
                split[key][split_key] += 1

            if event_markers:
                for marker in event_markers:
                    markers[marker] += 1
                suppressed_hits = keyword_hits(text, NEGATIVE_KEYWORDS) + keyword_hits(text, POSITIVE_KEYWORDS)
                if suppressed_hits:
                    entry = suppressed.setdefault(
                        case_id,
                        {"case_id": case_id, "usable": usable, "markers": [], "keywords": []},
                    )
                    _extend_unique(entry["markers"], list(event_markers))
                    _extend_unique(entry["keywords"], suppressed_hits)
            else:
                for key in keys:
                    for keyword in keyword_hits(text, NEGATIVE_KEYWORDS):
                        hits[key]["negative"][keyword] += 1
                    for keyword in keyword_hits(text, POSITIVE_KEYWORDS):
                        hits[key]["positive"][keyword] += 1

    return {
        "polarity": polarity,
        "unknown_split": split,
        "keyword_hits": hits,
        "question_markers": markers,
        "suppressed": sorted(suppressed.values(), key=lambda item: item["case_id"]),
    }


def _share_pct(part: int, total: int) -> float:
    return round(part / total * 100.0, 2) if total else 0.0


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def _payload_sha256(payload: dict[str, Any]) -> str:
    material = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# 组装
# ---------------------------------------------------------------------------


def load_eval_set(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:  # pragma: no cover - 环境问题
        raise EvalSetError(f"无法读取评测集 {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise EvalSetError(f"评测集 JSON 解析失败 {path}: {exc}") from exc
    if payload.get("schema") != EVAL_SCHEMA:
        raise EvalSetError(f"评测集 schema 不符：期望 {EVAL_SCHEMA}，实得 {payload.get('schema')!r}")
    cases = payload.get("cases")
    if not isinstance(cases, list) or not cases:
        raise EvalSetError("评测集缺少 cases")
    return payload


def build_payload(eval_set: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    cases = eval_set["cases"]
    rows = sorted((analyse_case(case) for case in cases), key=lambda row: row["case_id"])
    usable_rows = [row for row in rows if row["usable_for_timing"]]

    bucket_all = _bucket_counts(rows)
    bucket_usable = _bucket_counts(usable_rows)
    final_all = _final_counts(rows)
    final_usable = _final_counts(usable_rows)

    event_audit = _event_audit(cases)
    source_meta = eval_set.get("source") or {}

    denominator = final_usable["negative"] + final_usable["positive"]
    majority = "negative" if final_usable["negative"] >= final_usable["positive"] else "positive"
    baseline = {
        "sample_size": denominator,
        "negative": final_usable["negative"],
        "positive": final_usable["positive"],
        "unknown_excluded": final_usable["unknown"],
        "majority_class": majority,
        "hits": max(final_usable["negative"], final_usable["positive"]),
        "rate_pct": _share_pct(max(final_usable["negative"], final_usable["positive"]), denominator),
        "formula": "max(negative, positive) / (negative + positive)",
        "note": (
            f"382 例可评测集上按最终标签计算：unknown {final_usable['unknown']} 例排除，"
            f"分母 {denominator}。"
        ),
    }

    denominator_all = final_all["negative"] + final_all["positive"]
    majority_all = "negative" if final_all["negative"] >= final_all["positive"] else "positive"
    reference_411 = {
        "sample_size": denominator_all,
        "negative": final_all["negative"],
        "positive": final_all["positive"],
        "unknown_excluded": final_all["unknown"],
        "majority_class": majority_all,
        "hits": max(final_all["negative"], final_all["positive"]),
        "rate_pct": _share_pct(max(final_all["negative"], final_all["positive"]), denominator_all),
        "note": "仅参考：411 全集（含 29 例不可评测）标签分布，不是验收基线。",
    }

    payload: dict[str, Any] = {
        "schema": SCHEMA,
        "task": TASK,
        "status": "frozen",
        "immutable": True,
        "notice": (
            "标签定义与数字冻结于 T-153（任务卡 §2 预注册）。标签只来自婚姻事件"
            "（polarity + 事件文本关键词），不含任何盘面/八字特征。本文件为确定性产物："
            "无运行时间戳，重复运行逐字节一致；如需变更，另建 v2，不得就地改数。"
        ),
        "frozen_at": FROZEN_AT,
        "frozen_at_note": "= 任务卡建卡日（定义预注册日），不是运行时间戳。",
        "script": SCRIPT,
        "source": {
            "eval_set": {
                "path": "META/timing-eval-set-v1.json",
                "schema": eval_set.get("schema"),
                "task": eval_set.get("task"),
                "sha256": _sha256_file(EVAL_PATH),
                "cases": len(cases),
            },
            "upstream": {
                "path": source_meta.get("path"),
                "records": source_meta.get("records"),
                "sha256": source_meta.get("sha256"),
            },
        },
        "definition": {
            "population": (
                "META/timing-eval-set-v1.json 的 411 例候选；验收分母为 382 例 "
                "usable_for_timing=true"
            ),
            "order": [
                "negative：任一婚姻事件 polarity == 'negative'；或 polarity == 'unknown' 且非提问文本"
                "命中负面关键词",
                "positive：无 negative 证据，且任一事件 polarity == 'positive'；或 polarity == 'unknown' "
                "且非提问文本命中正面关键词",
                "unknown：以上都不成立（全是提问 / 中性 / 无证据）→ 排除，不进分母",
                "冲突：negative 与 positive 证据并存时 negative 优先",
            ],
            "negative_keywords": list(NEGATIVE_KEYWORDS),
            "positive_keywords": list(POSITIVE_KEYWORDS),
            "question_markers": list(QUESTION_MARKERS),
            "question_rule": (
                "只对 polarity == 'unknown' 的事件文本判定：文本含任一标记即视为提问，整段不作"
                "关键词证据（提问里的结婚/离婚不是结果）；同一案例的其余事件独立判定。"
            ),
            "unknown_reason_precedence": [
                "no_evidence：无婚姻事件，或全部事件文本为空",
                "neutral：存在非提问但无关键词命中（且非空）的文本",
                "question：其余 unknown（全部有文本的事件均为提问）",
            ],
            "polarity_other": "negative/positive/unknown 之外的取值按 unknown 参与打标并单独计数（本版 0 条）。",
            "conflict_bucket": (
                "counts.all / counts.usable 的 negative 是「纯负证据」桶，与 conflict 互斥；"
                "final.negative = negative + conflict。"
            ),
            "leakage": "标签只读 marriage_events[].polarity 与 text；未读取任何盘面/八字特征。",
            "case_order": "cases 按 case_id 升序。",
            "determinism": "不含运行时间戳；frozen_at 为定义冻结日。",
        },
        "counts": {
            "cases_total": len(cases),
            "usable_for_timing": len(usable_rows),
            "all": bucket_all,
            "usable": bucket_usable,
            "final": {"all": final_all, "usable": final_usable},
            "unknown_share_pct": {
                "all": _share_pct(final_all["unknown"], len(cases)),
                "usable": _share_pct(final_usable["unknown"], len(usable_rows)),
            },
            "unknown_reasons": {
                "all": _unknown_reason_counts(rows),
                "usable": _unknown_reason_counts(usable_rows),
            },
            "deciding_basis": {
                "all": _basis_counts(rows),
                "usable": _basis_counts(usable_rows),
            },
            "events": {
                "polarity": event_audit["polarity"],
                "unknown_split": event_audit["unknown_split"],
                "keyword_hits": event_audit["keyword_hits"],
                "question_markers": event_audit["question_markers"],
                "question_suppressed_cases": {
                    "count": len(event_audit["suppressed"]),
                    "usable_count": sum(1 for item in event_audit["suppressed"] if item["usable"]),
                    "cases": event_audit["suppressed"],
                },
                "other_polarity_note": "三值之外的 polarity 事件数见 polarity.*.other（本版 0）。",
            },
        },
        "baseline": baseline,
        "reference_411": reference_411,
        "cases": rows,
    }
    payload["payload_sha256"] = _payload_sha256(payload)
    return payload, rows, event_audit


def check_invariants(payload: dict[str, Any], cases: list[dict[str, Any]]) -> None:
    problems: list[str] = []
    counts = payload["counts"]
    if len(cases) != EXPECTED_CASES:
        problems.append(f"评测集案例数 {len(cases)} != {EXPECTED_CASES}")
    if counts["usable_for_timing"] != EXPECTED_USABLE:
        problems.append(f"usable_for_timing {counts['usable_for_timing']} != {EXPECTED_USABLE}")
    for key in ("all", "usable"):
        bucket = counts[key]
        total = bucket["negative"] + bucket["positive"] + bucket["unknown"] + bucket["conflict"]
        if total != bucket["sum"]:
            problems.append(f"counts.{key} 四桶 {total} != sum {bucket['sum']}")
    if counts["all"]["sum"] != EXPECTED_CASES:
        problems.append(f"counts.all.sum {counts['all']['sum']} != {EXPECTED_CASES}")
    if counts["usable"]["sum"] != EXPECTED_USABLE:
        problems.append(f"counts.usable.sum {counts['usable']['sum']} != {EXPECTED_USABLE}")
    ids = [row["case_id"] for row in payload["cases"]]
    if len(set(ids)) != len(ids):
        problems.append("cases 存在重复 case_id")
    final_usable = counts["final"]["usable"]
    baseline = payload["baseline"]
    if baseline["sample_size"] != final_usable["negative"] + final_usable["positive"]:
        problems.append("baseline.sample_size 与 final.usable 不符")
    if problems:
        raise LabelInvariantError("；".join(problems))


def check_audit_samples(payload: dict[str, Any]) -> None:
    rows = {row["case_id"]: row for row in payload["cases"]}
    problems: list[str] = []
    for case_id, expected, _verdict in AUDIT_SAMPLES:
        row = rows.get(case_id)
        if row is None:
            problems.append(f"{case_id}: 案例不存在")
        elif row["label"] != expected:
            problems.append(f"{case_id}: 期望 {expected}，实得 {row['label']}")
    if problems:
        raise AuditError("；".join(problems))


# ---------------------------------------------------------------------------
# 人读报告
# ---------------------------------------------------------------------------


def _cell(value: Any) -> str:
    text = "" if value is None else str(value)
    return text.replace("|", "\\|").replace("\n", " ")


def _table(header: list[str], body: list[list[Any]]) -> list[str]:
    lines = ["| " + " | ".join(header) + " |"]
    lines.append("|" + "|".join(["---"] * len(header)) + "|")
    for row in body:
        lines.append("| " + " | ".join(_cell(value) for value in row) + " |")
    return lines


def _evidence_cell(block: dict[str, Any]) -> str:
    parts: list[str] = []
    if block["polarity"]:
        parts.append(f"极性×{block['polarity']}")
    if block["keyword"]:
        keywords = "、".join(block["keywords"]) if block["keywords"] else "—"
        parts.append(f"关键词×{block['keyword']}（{keywords}）")
    return " + ".join(parts) if parts else "—"


def _sample_event_text(case: dict[str, Any], row: dict[str, Any]) -> str:
    events = case.get("marriage_events") or []
    if row["evidence_events"]:
        first = row["evidence_events"][0]
        return f"{first['year']} · {first['text']}"
    for event in events:
        if question_markers_in(event.get("text") or ""):
            return f"{event.get('year')} · {summarise_text(event.get('text') or '')}"
    if events:
        return f"{events[0].get('year')} · {summarise_text(events[0].get('text') or '')}"
    return "—"


def render_report(
    payload: dict[str, Any],
    rows: list[dict[str, Any]],
    cases_by_id: dict[str, dict[str, Any]],
) -> str:
    counts = payload["counts"]
    events = counts["events"]
    baseline = payload["baseline"]
    reference = payload["reference_411"]
    source = payload["source"]
    usable_rows = [row for row in rows if row["usable_for_timing"]]
    final_all = counts["final"]["all"]
    final_usable = counts["final"]["usable"]

    lines: list[str] = []
    add = lines.append

    add("# T-153 · 婚姻质量标签 v1（人读报告）")
    add("")
    add("- 生成脚本：`tools/marriage_quality_labels.py`")
    add("- 标签定义冻结日：`2026-10-28`（预注册日；**不是**运行时间戳）")
    add(
        f"- 评测集：`{source['eval_set']['path']}`（sha256 `{source['eval_set']['sha256']}`，"
        f"{counts['cases_total']} 例 / {counts['usable_for_timing']} 可评测）"
    )
    add(
        f"- 上游语料：`{source['upstream']['path']}`（{source['upstream']['records']} 条，"
        f"sha256 `{source['upstream']['sha256']}`）"
    )
    add(
        "- 性质：**结果变量，不是预测**。标签只来自 `marriage_events` 的 polarity 与事件文本关键词，"
        "**不使用任何盘面/八字特征**（防泄漏，任务卡 §5）。本文件无运行时间戳，重复运行逐字节一致。"
    )
    add("")

    add("## 1. 冻结定义（任务卡 §2，预注册，不得中途改）")
    add("")
    add("按顺序判定（negative 优先）：")
    add("")
    add("1. **negative**：任一婚姻事件 `polarity == \"negative\"`；或 `polarity == \"unknown\"` 且**非提问**文本命中负面关键词。")
    add("2. **positive**：无 negative 证据，且任一事件 `polarity == \"positive\"`；或 `polarity == \"unknown\"` 且非提问文本命中正面关键词。")
    add("3. **unknown**：以上都不成立（全是提问 / 中性 / 无证据）→ 排除，不进分母。")
    add("4. **冲突**：negative 与 positive 证据并存时 negative 优先。")
    add("")
    add("负面关键词（原样冻结）：" + "、".join(f"`{kw}`" for kw in NEGATIVE_KEYWORDS))
    add("")
    add("正面关键词（原样冻结）：" + "、".join(f"`{kw}`" for kw in POSITIVE_KEYWORDS))
    add("")
    add(
        "提问判定（只用于 `polarity == \"unknown\"` 的文本）：含 "
        + "、".join(f"`{marker}`" for marker in QUESTION_MARKERS)
        + " 任一 → **整段不作关键词证据**。同一案例的其余事件独立判定。"
    )
    add("")
    add(
        "> 语料里「么」大量出现在「什么/怎么/这么」中，按卡片字面规则一律先判提问。"
        "这个方向的误差只会让 unknown 变多，不会把提问当证据。"
    )
    add("")

    add("## 2. 计数（互斥四桶；negative 不含冲突）")
    add("")
    lines.extend(
        _table(
            ["桶", f"{counts['cases_total']} 全集", f"{counts['usable_for_timing']} 可评测"],
            [
                ["negative（纯负证据）", counts["all"]["negative"], counts["usable"]["negative"]],
                ["positive", counts["all"]["positive"], counts["usable"]["positive"]],
                ["unknown（排除，不进分母）", counts["all"]["unknown"], counts["usable"]["unknown"]],
                ["conflict（负正并存，最终记 negative）", counts["all"]["conflict"], counts["usable"]["conflict"]],
                ["**合计**", f"**{counts['all']['sum']}**", f"**{counts['usable']['sum']}**"],
            ],
        )
    )
    add("")
    add(
        f"最终标签（冲突计入 negative）：{counts['cases_total']} 全集 negative **{final_all['negative']}** / "
        f"positive **{final_all['positive']}** / unknown **{final_all['unknown']}**；"
        f"{counts['usable_for_timing']} 可评测 negative **{final_usable['negative']}** / "
        f"positive **{final_usable['positive']}** / unknown **{final_usable['unknown']}**"
        f"（unknown 占 {counts['unknown_share_pct']['usable']:.2f}%）。"
    )
    add("")
    add(
        f"四桶相加校验：{counts['all']['sum']} = {counts['all']['negative']}+{counts['all']['positive']}"
        f"+{counts['all']['unknown']}+{counts['all']['conflict']}；"
        f"{counts['usable']['sum']} = {counts['usable']['negative']}+{counts['usable']['positive']}"
        f"+{counts['usable']['unknown']}+{counts['usable']['conflict']}。"
    )
    add("")

    polarity = events["polarity"]
    split = events["unknown_split"]
    add("## 3. 事件 polarity 审计")
    add("")
    lines.extend(
        _table(
            ["polarity", "事件数（全集）", "事件数（可评测）"],
            [
                ["negative", polarity["all"]["negative"], polarity["usable"]["negative"]],
                ["positive", polarity["all"]["positive"], polarity["usable"]["positive"]],
                ["unknown", polarity["all"]["unknown"], polarity["usable"]["unknown"]],
                ["三值之外", polarity["all"]["other"], polarity["usable"]["other"]],
                ["**合计**", f"**{polarity['all']['total']}**", f"**{polarity['usable']['total']}**"],
            ],
        )
    )
    add("")
    add(
        f"unknown 事件拆分：全集 {polarity['all']['unknown']} = 提问 {split['all']['question']} + "
        f"非提问 {split['all']['non_question']} + 空文本 {split['all']['empty_text']}；"
        f"可评测 {polarity['usable']['unknown']} = 提问 {split['usable']['question']} + "
        f"非提问 {split['usable']['non_question']} + 空文本 {split['usable']['empty_text']}。"
    )
    add("")

    add("## 4. 关键词与提问审计")
    add("")
    add("### 4.1 非提问 unknown 文本的关键词命中（事件数）")
    add("")
    keyword_rows: list[list[Any]] = []
    for keyword in NEGATIVE_KEYWORDS:
        keyword_rows.append(
            [f"负面 `{keyword}`", events["keyword_hits"]["all"]["negative"][keyword],
             events["keyword_hits"]["usable"]["negative"][keyword]]
        )
    for keyword in POSITIVE_KEYWORDS:
        keyword_rows.append(
            [f"正面 `{keyword}`", events["keyword_hits"]["all"]["positive"][keyword],
             events["keyword_hits"]["usable"]["positive"][keyword]]
        )
    lines.extend(_table(["关键词", "全集", "可评测"], keyword_rows))
    add("")
    add(
        f"合计命中事件：负面 {sum(events['keyword_hits']['all']['negative'].values())} / "
        f"正面 {sum(events['keyword_hits']['all']['positive'].values())}（同一事件可命中多个关键词）。"
    )
    add("")

    add("### 4.2 提问标记命中（unknown 事件，可多选）")
    add("")
    lines.extend(
        _table(
            ["标记", "命中事件数"],
            [[f"`{marker}`", events["question_markers"][marker]] for marker in QUESTION_MARKERS],
        )
    )
    add("")

    suppressed = events["question_suppressed_cases"]
    add(
        f"### 4.3 提问规则抑制了关键词证据的案例：{suppressed['count']} 例"
        f"（其中可评测 {suppressed['usable_count']} 例）"
    )
    add("")
    labels_by_id = {row["case_id"]: row["label"] for row in rows}
    lines.extend(
        _table(
            ["case_id", "可评测", "标记", "被抑制关键词", "最终标签"],
            [
                [
                    item["case_id"],
                    "是" if item["usable"] else "否",
                    "、".join(f"`{marker}`" for marker in item["markers"]),
                    "、".join(item["keywords"]),
                    labels_by_id.get(item["case_id"], "?"),
                ]
                for item in suppressed["cases"]
            ],
        )
    )
    add("")
    add(
        "> 这些案例的该条事件文本里有陈述式的「结婚/离婚」，但整段含提问标记，按冻结规则不采证。"
        "多数案例仍可被其它事件定标；定不了标的进入 unknown（偏保守）。"
    )
    add("")

    reasons = counts["unknown_reasons"]
    add("### 4.4 unknown 主因分类（案例级）")
    add("")
    lines.extend(
        _table(
            ["原因", "全集", "可评测", "定义"],
            [
                ["question", reasons["all"]["question"], reasons["usable"]["question"], "全部有文本事件均为提问"],
                ["neutral", reasons["all"]["neutral"], reasons["usable"]["neutral"], "存在非提问、无关键词命中的文本"],
                ["no_evidence", reasons["all"]["no_evidence"], reasons["usable"]["no_evidence"], "无婚姻事件或事件文本为空"],
            ],
        )
    )
    add("")
    add(
        "判定顺序：先看是否有非提问中性文本（neutral），否则看是否有提问（question），"
        "否则 no_evidence。unknown 占比：全集 "
        f"{counts['unknown_share_pct']['all']:.2f}%，可评测 {counts['unknown_share_pct']['usable']:.2f}%。"
    )
    add("")

    basis = counts["deciding_basis"]
    add("### 4.5 最终标签的判定依据（basis）")
    add("")
    lines.extend(
        _table(
            ["最终标签", "依据", "全集", "可评测"],
            [
                ["negative", "polarity", basis["all"]["negative"]["polarity"], basis["usable"]["negative"]["polarity"]],
                ["negative", "keyword", basis["all"]["negative"]["keyword"], basis["usable"]["negative"]["keyword"]],
                ["positive", "polarity", basis["all"]["positive"]["polarity"], basis["usable"]["positive"]["polarity"]],
                ["positive", "keyword", basis["all"]["positive"]["keyword"], basis["usable"]["positive"]["keyword"]],
            ],
        )
    )
    add("")

    conflicts = [row for row in rows if row["conflict"]]
    add(f"## 5. 冲突审计（{len(conflicts)} 例，全部按 negative 优先）")
    add("")
    lines.extend(
        _table(
            ["case_id", "可评测", "负证据", "正证据"],
            [
                [
                    row["case_id"],
                    "是" if row["usable_for_timing"] else "否",
                    _evidence_cell(row["negative_evidence"]),
                    _evidence_cell(row["positive_evidence"]),
                ]
                for row in conflicts
            ],
        )
    )
    add("")

    add("## 6. 最终标签与多数类基线")
    add("")
    lines.extend(
        _table(
            ["项", f"{counts['usable_for_timing']} 可评测（验收口径）", f"{counts['cases_total']} 全集（仅参考）"],
            [
                ["negative", final_usable["negative"], final_all["negative"]],
                ["positive", final_usable["positive"], final_all["positive"]],
                ["unknown（排除）", final_usable["unknown"], final_all["unknown"]],
                ["分母（negative+positive）", baseline["sample_size"], reference["sample_size"]],
                ["多数类", baseline["majority_class"], reference["majority_class"]],
                ["多数类命中", baseline["hits"], reference["hits"]],
                ["**多数类命中率**", f"**{baseline['rate_pct']:.2f}%**", f"{reference['rate_pct']:.2f}%"],
            ],
        )
    )
    add("")
    add("口径：`max(negative, positive) / (negative + positive)`；unknown 不折入任何一类。")
    add("")

    add("## 7. 已知误判与漏判（人工核查；按预注册规则保留原判，未就地改）")
    add("")
    lines.extend(
        _table(
            ["类型", "案例", "现象", "按语义应为"],
            [[kind, case_id, phenomenon, verdict] for kind, case_id, phenomenon, verdict in KNOWN_ISSUES],
        )
    )
    add("")
    add(
        "> 这些是**规则本身的边界**（否定语境 / 第三人称 / 繁体），不是实现 bug：卡片冻结的关键词表"
        "与判定顺序不允许现场加否定或主体识别。修正须由中枢另建 v2 并写明规则变更；"
        "本版标签保持机械可复现。"
    )
    add("")

    add("## 8. 20 例人工抽查")
    add("")
    add(
        "抽查方式：按 `raw_id` 回 `cases/raw_feedback/parsed/real_cases_990.jsonl`，逐例比对事件条的 "
        "`year / polarity / text`；20/20 与评测集一致（事件条数与文本逐字相同）。"
    )
    add("")
    audit_rows: list[list[Any]] = []
    for index, (case_id, _expected, verdict) in enumerate(AUDIT_SAMPLES, start=1):
        row = next(item for item in rows if item["case_id"] == case_id)
        audit_rows.append(
            [
                index,
                case_id,
                "是" if row["usable_for_timing"] else "否",
                row["label"],
                row["basis"],
                _sample_event_text(cases_by_id[case_id], row),
                verdict,
            ]
        )
    lines.extend(_table(["#", "case_id", "可评测", "标签", "依据", "事件摘要", "结论"], audit_rows))
    add("")
    add(
        "结论列「合理」= 规则与原文一致；「存疑」= 规则产出与语义不一致（见 §7），"
        "本版**不**就地改判。"
    )
    add("")

    add("## 9. 复现与不变量")
    add("")
    add("```bash")
    add(".venv\\Scripts\\python.exe -m tools.marriage_quality_labels")
    add("```")
    add("")
    add(
        f"- 不变量：{counts['cases_total']} = {counts['all']['negative']}+{counts['all']['positive']}"
        f"+{counts['all']['unknown']}+{counts['all']['conflict']}；"
        f"{counts['usable_for_timing']} = {counts['usable']['negative']}+{counts['usable']['positive']}"
        f"+{counts['usable']['unknown']}+{counts['usable']['conflict']}。"
    )
    add(f"- JSON `payload_sha256`：`{payload['payload_sha256']}`")
    add("- 无运行时间戳、不读盘面事实、不写评测集；两次运行输出逐字节一致。")
    add("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 入口
# ---------------------------------------------------------------------------


def main() -> int:
    try:
        eval_set = load_eval_set(EVAL_PATH)
        payload, rows, _event_audit_data = build_payload(eval_set)
        check_invariants(payload, eval_set["cases"])
        check_audit_samples(payload)
    except EvalSetError as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        return 2
    except LabelInvariantError as exc:
        print(f"[FAIL] 计数不变量不复现：{exc}", file=sys.stderr)
        return 3
    except AuditError as exc:
        print(f"[FAIL] 人工抽查结论与数据不符，需重审：{exc}", file=sys.stderr)
        return 4

    cases_by_id = {case["case_id"]: case for case in eval_set["cases"]}
    JSON_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    REPORT_PATH.write_text(render_report(payload, rows, cases_by_id), encoding="utf-8")

    counts = payload["counts"]
    final = counts["final"]
    baseline = payload["baseline"]
    print("T-153 marriage-quality-labels v1")
    print(
        f"  eval_set : {payload['source']['eval_set']['path']} "
        f"sha256={payload['source']['eval_set']['sha256'][:12]}… "
        f"cases={counts['cases_total']} usable={counts['usable_for_timing']}"
    )
    print(
        f"  all      : negative={counts['all']['negative']} positive={counts['all']['positive']} "
        f"unknown={counts['all']['unknown']} conflict={counts['all']['conflict']} "
        f"sum={counts['all']['sum']} | final negative={final['all']['negative']}"
    )
    print(
        f"  usable   : negative={counts['usable']['negative']} positive={counts['usable']['positive']} "
        f"unknown={counts['usable']['unknown']} conflict={counts['usable']['conflict']} "
        f"sum={counts['usable']['sum']} | final negative={final['usable']['negative']} "
        f"positive={final['usable']['positive']} unknown={final['usable']['unknown']}"
        f" ({counts['unknown_share_pct']['usable']:.2f}%)"
    )
    print(
        f"  baseline : n={baseline['sample_size']} majority={baseline['majority_class']} "
        f"hits={baseline['hits']} rate={baseline['rate_pct']:.2f}%"
    )
    print(f"  wrote    : META/marriage-quality-labels-v1.json sha256={_sha256_file(JSON_PATH)[:12]}…")
    print("           : META/marriage-quality-labels-v1.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

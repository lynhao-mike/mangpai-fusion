"""T-161 · 事业角色变化标签 v1（``1`` / ``null``，文本先去重，不造 ``0``）。

从 ``occupation`` 事件文本造 ``role_change`` 标签：

* ``1``    = 有既成的角色变化证据（干净命中任一冻结关键词）
* ``null`` = 没有可用证据（**不产生 0**）
* 另记 ``work_no_change = 1``：案例有非提问 occupation 文本、但无干净命中（诊断用，不是标签）

铁律（任务卡 §2 / §8）：

* 只用事件文本与 polarity；不读 ``bazi_raw`` / ``qian_kun`` / 任何盘面字段，不评分、不建盘。
* 文本先去重：规范化（去首尾空白、连续空白合一）后再移除全部空白，取 sha256；跨案例
  同文只保留 ``raw_id`` 最小的一条，其余记 ``dropped_duplicate_text``；同案例内同文折叠。
* 先剔除提问文本，再判关键词；关键词表原样冻结，禁止为阳性率调词。
* 四类排除：他人主体 / 意向语 / 否定窗口 6 字 / 提问。

产物（确定性，无运行时间戳，重复运行逐字节一致）：

* ``META/career-role-change-labels-v1.json``
* ``META/career-role-change-labels-v1.md``

用法::

    python -m tools.career_role_change_labels

退出码：0 通过；3 计数不变量不复现（数据源变更）；4 数据源不可读；
5 冻结的人工审计结论与当前标签不符（需重审）。
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

from tools.timing_eval_set import parse_clock_datetime

ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = ROOT / "cases" / "raw_feedback" / "parsed" / "real_cases_990.jsonl"
JSON_PATH = ROOT / "META" / "career-role-change-labels-v1.json"
REPORT_PATH = ROOT / "META" / "career-role-change-labels-v1.md"

SCHEMA = "career-role-change-labels/v1"
TASK = "T-161"
SCRIPT = "tools/career_role_change_labels.py"

# 定义冻结日 = 任务卡建卡日（预注册）。不是运行时间戳：本产物必须可逐字节复现。
FROZEN_AT = "2026-10-29"

# 任务卡 §1 冻结计数（T-159 已复现）。不满足即视为数据源变更，拒绝落盘。
EXPECTED_RECORDS = 992
EXPECTED_UNIQUE = 959
EXPECTED_OCCUPATION_CASES = 620
EXPECTED_OCCUPATION_EVENTS = 957
EXPECTED_CHART_READY = 614

# 任务卡 §2.2 关键词表，原样冻结，禁止增删改。
ROLE_KEYWORDS = (
    "升职", "晋升", "提拔", "跳槽", "换工作", "换岗", "调动", "转行",
    "辞职", "裸辞", "下岗", "失业", "岗位变化", "职责变化", "任职", "入职",
)

# 任务卡 §2.3 提问标记，原样冻结。整段事件命中任一即不作证据。
QUESTION_MARKERS = ("？", "?", "是否", "能否", "请问", "怎么样", "吗", "么", "呢")

# 任务卡 §2.3 他人主体词表，原样冻结。
OTHER_SUBJECTS = (
    "父母", "父亲", "母亲", "爸", "妈", "老公", "老婆", "妻子", "丈夫",
    "儿子", "女儿", "孩子", "家人", "家属", "兄弟", "姐妹", "亲戚", "朋友",
    "爷爷", "奶奶", "姥姥", "姥爷", "公公", "婆婆", "岳父", "岳母",
    "兄长", "姐姐", "妹妹",
)
SELF_SUBJECTS = ("我", "本人", "自己")

# 任务卡 §2.3 意向语，原样冻结。整段事件命中任一即不作证据。
ASPIRATION_MARKERS = ("希望", "打算", "准备", "想", "能否", "是否", "计划", "有望")

# 任务卡 §2.3 否定词，原样冻结。关键词前 6 字内命中即该次命中不作证据。
NEGATION_MARKERS = ("无", "没", "没有", "未", "差点", "并非")

# 任务卡只写「关键词附近」，未给窗口；本版冻结为关键词两侧各 10 字。
OTHER_SUBJECT_WINDOW = 10
NEGATION_WINDOW = 6

TEXT_SUMMARY_LIMIT = 60

# 禁止出现的盘面字段（防泄漏）。payload 的键名不得含这些 token。
DISALLOWED_FIELD_TOKENS = (
    "bazi", "qian_kun", "ganzhi", "dayun", "liunian", "sizhu",
    "pillar", "chart_facts", "yongshen", "score",
)


class SourceError(RuntimeError):
    """数据源不可读。"""


class FunnelInvariantError(RuntimeError):
    """计数不变量不复现（数据源变更）。"""


class AuditStaleError(RuntimeError):
    """冻结的人工审计结论与当前标签不符。"""


# ---------------------------------------------------------------------------
# 文本与事件
# ---------------------------------------------------------------------------


def normalize_text(text: str | None) -> str:
    """去首尾空白、连续空白合一（任务卡 §2.1 文本规范化）。"""
    return re.sub(r"\s+", " ", (text or "").strip())


def text_digest(text: str | None) -> str:
    """文本去重键的 sha256。

    先按任务卡 §2.1 规范化（去首尾空白、连续空白合一），再把**全部空白**移除后取哈希。
    空白不承载语义；只折叠连续空白会漏掉「仅空白位置不同」的同文，无法复现 T-159 的
    19 组 / 40 条泄漏面，故本版把去重键收紧到空白不敏感。
    """
    normalized = normalize_text(text)
    compact = "".join(normalized.split())
    return hashlib.sha256(compact.encode("utf-8")).hexdigest()


def question_markers_in(text: str) -> list[str]:
    return [marker for marker in QUESTION_MARKERS if marker in text]


def is_question(text: str) -> bool:
    """整段是否按卡片口径判为提问（提问段一律不作证据）。"""
    return bool(question_markers_in(text))


def keyword_positions(text: str, keyword: str) -> list[int]:
    """关键词在文本中的全部出现位置（子串，起点递增）。"""
    positions: list[int] = []
    start = 0
    while True:
        index = text.find(keyword, start)
        if index < 0:
            return positions
        positions.append(index)
        start = index + 1


def other_subject_near(text: str, position: int, keyword: str) -> bool:
    """关键词附近是否指向他人（且附近没有命主自称）。

    任务卡 §2.3：「关键词附近含 [他人词表]，且不含 我/本人/自己」。
    两个条件都按关键词两侧各 ``OTHER_SUBJECT_WINDOW`` 字的同一窗口判：他人词与自称
    同窗出现时视为命主（如「我被迫升岗级，换岗位」），避免把「老公辞职」这类句子
    因事件别处出现「我」而漏放行。
    """
    start = max(0, position - OTHER_SUBJECT_WINDOW)
    end = min(len(text), position + len(keyword) + OTHER_SUBJECT_WINDOW)
    vicinity = text[start:end]
    if not any(token in vicinity for token in OTHER_SUBJECTS):
        return False
    return not any(token in vicinity for token in SELF_SUBJECTS)


def negation_near(text: str, position: int) -> bool:
    """关键词前 6 字内是否出现否定词（任务卡 §2.3）。"""
    return any(marker in text[max(0, position - NEGATION_WINDOW):position] for marker in NEGATION_MARKERS)


def aspiration_in(text: str) -> bool:
    """整段是否含意向语（任务卡 §2.3）。"""
    return any(marker in text for marker in ASPIRATION_MARKERS)


def occurrence_tags(text: str, position: int, keyword: str) -> tuple[str, ...]:
    """返回一次关键词命中的排除标签：other_subject / aspiration / negation。"""
    tags: list[str] = []
    if other_subject_near(text, position, keyword):
        tags.append("other_subject")
    if aspiration_in(text):
        tags.append("aspiration")
    if negation_near(text, position):
        tags.append("negation")
    return tuple(tags)


def event_polarity(event: dict[str, Any]) -> str:
    value = event.get("polarity")
    return value if value in ("positive", "negative", "unknown") else "unknown"


def occupation_events(record: dict[str, Any]) -> list[dict[str, Any]]:
    """返回 ``domains`` 含 ``occupation`` 的事件条（保持 JSON 顺序）。"""
    return [event for event in record.get("events") or [] if "occupation" in (event.get("domains") or [])]


# ---------------------------------------------------------------------------
# 读源与两轮去重
# ---------------------------------------------------------------------------


def load_records(path: Path = SOURCE_PATH) -> list[dict[str, Any]]:
    """按文件行序读取 JSONL。"""
    if not path.exists():
        raise SourceError(f"数据源不存在：{path}")
    records: list[dict[str, Any]] = []
    try:
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                stripped = line.strip()
                if not stripped:
                    continue
                records.append(json.loads(stripped))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SourceError(f"数据源不可读：{path}（{exc}）") from exc
    return records


def dedupe_records(records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """``duplicate_key`` 全等去重，保留首次出现。"""
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    duplicates = 0
    groups: dict[str, int] = {}
    for record in records:
        key = str(record.get("duplicate_key") or "")
        groups[key] = groups.get(key, 0) + 1
        if key in seen:
            duplicates += 1
            continue
        seen.add(key)
        unique.append(record)
    repeated = sum(1 for count in groups.values() if count > 1)
    return unique, {"groups": repeated, "extra_records": duplicates}


def collect_events(unique: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """收集全部 occupation 事件（含文本规范化与哈希）。"""
    events: list[dict[str, Any]] = []
    for record in unique:
        for event_index, event in enumerate(occupation_events(record)):
            text = event.get("text") or ""
            events.append(
                {
                    "case_id": str(record.get("raw_id")),
                    "event_index": event_index,
                    "year": event.get("year"),
                    "polarity": event_polarity(event),
                    "text": text,
                    "digest": text_digest(text),
                    "question": is_question(text),
                }
            )
    return events


def dedupe_event_texts(events: list[dict[str, Any]]) -> dict[str, Any]:
    """按规范化文本 sha256 去重：跨案例保留 ``raw_id`` 最小的一条，同案例折叠。

    原地写入 ``kept`` / ``dropped`` 字段，返回去重明细（确定性排序）。
    """
    groups: dict[str, list[dict[str, Any]]] = {}
    for event in events:
        groups.setdefault(event["digest"], []).append(event)

    details: list[dict[str, Any]] = []
    dropped_total = 0
    dropped_cross_case = 0
    dropped_within_case = 0
    dropped_usable = 0
    dropped_question = 0
    cases_affected: set[str] = set()
    for digest, members in groups.items():
        keeper = min(members, key=lambda event: (event["case_id"], event["event_index"]))
        for event in members:
            event["kept"] = event is keeper
            event["dropped"] = event is not keeper
        if len(members) == 1:
            continue
        case_ids = sorted({event["case_id"] for event in members})
        dropped = [event for event in members if event is not keeper]
        cross_case = len(case_ids) > 1
        dropped_total += len(dropped)
        if cross_case:
            dropped_cross_case += len(dropped)
        else:
            dropped_within_case += len(dropped)
        for event in dropped:
            cases_affected.add(event["case_id"])
            if event["question"]:
                dropped_question += 1
            else:
                dropped_usable += 1
        details.append(
            {
                "digest": digest,
                "events": len(members),
                "dropped": len(dropped),
                "cross_case": cross_case,
                "kept_case_id": keeper["case_id"],
                "kept_event_index": keeper["event_index"],
                "case_ids": case_ids,
                "dropped_case_ids": sorted({event["case_id"] for event in dropped}),
                "text": normalize_text(keeper["text"]),
            }
        )
    details.sort(key=lambda item: (item["kept_case_id"], item["kept_event_index"]))
    return {
        "groups_with_duplicates": len(details),
        "cross_case_groups": sum(1 for item in details if item["cross_case"]),
        "cross_case_events": sum(item["events"] for item in details if item["cross_case"]),
        "within_case_groups": sum(1 for item in details if not item["cross_case"]),
        "within_case_events": sum(item["events"] for item in details if not item["cross_case"]),
        "dropped_events": dropped_total,
        "dropped_cross_case": dropped_cross_case,
        "dropped_within_case": dropped_within_case,
        "dropped_usable_events": dropped_usable,
        "dropped_question_events": dropped_question,
        "cases_affected": len(cases_affected),
        "details": details,
    }


# ---------------------------------------------------------------------------
# 逐例打标
# ---------------------------------------------------------------------------


def scan_case(case_id: str, events: list[dict[str, Any]]) -> dict[str, Any]:
    """扫描单案例（events 已按文本去重）的干净命中与排除账。"""
    occurrences: list[dict[str, Any]] = []
    kept_events = [event for event in events if event["kept"]]
    usable_events = [event for event in kept_events if not event["question"]]
    for event in usable_events:
        text = event["text"]
        for keyword in ROLE_KEYWORDS:
            for position in keyword_positions(text, keyword):
                occurrences.append(
                    {
                        "case_id": case_id,
                        "event_index": event["event_index"],
                        "keyword": keyword,
                        "position": position,
                        "tags": occurrence_tags(text, position, keyword),
                        "year": event["year"],
                        "polarity": event["polarity"],
                        "text": text,
                    }
                )
    clean = [item for item in occurrences if not item["tags"]]
    evidence: list[dict[str, Any]] = []
    for event in usable_events:
        keywords = sorted({item["keyword"] for item in clean if item["event_index"] == event["event_index"]})
        if not keywords:
            continue
        evidence.append(
            {
                "event_index": event["event_index"],
                "year": event["year"],
                "polarity": event["polarity"],
                "keywords": keywords,
                "text": event["text"],
            }
        )
    return {
        "case_id": case_id,
        "kept_events": kept_events,
        "usable_events": usable_events,
        "occurrences": occurrences,
        "clean": clean,
        "evidence_events": evidence,
        "role_change": 1 if clean else None,
        "work_no_change": 0 if clean else (1 if usable_events else 0),
    }


def build_cases(unique: list[dict[str, Any]], events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """按案例聚合，产出冻结字段（不派生任何盘面事实）。"""
    events_by_case: dict[str, list[dict[str, Any]]] = {}
    for event in events:
        events_by_case.setdefault(event["case_id"], []).append(event)

    cases: list[dict[str, Any]] = []
    for record in unique:
        case_id = str(record.get("raw_id"))
        if case_id not in events_by_case:
            continue
        birth = parse_clock_datetime(record.get("birth_datetime_raw"))
        scan = scan_case(case_id, events_by_case[case_id])
        cases.append(
            {
                "case_id": case_id,
                "gender": (record.get("gender") or "").strip(),
                "birth_datetime_raw": record.get("birth_datetime_raw"),
                "birth_dt": birth["dt"].isoformat(sep=" ") if birth["ok"] else None,
                "time_basis": "clock_beijing" if birth["ok"] else None,
                "chart_ready": bool(birth["ok"] and birth["has_time"]),
                "role_change": scan["role_change"],
                "work_no_change": scan["work_no_change"],
                "evidence_events": scan["evidence_events"],
                "text_events": {
                    "occupation": len(events_by_case[case_id]),
                    "kept": len(scan["kept_events"]),
                    "usable": len(scan["usable_events"]),
                    "question": sum(1 for event in events_by_case[case_id] if event["question"]),
                    "dropped_duplicate": sum(
                        1 for event in events_by_case[case_id] if event["dropped"]
                    ),
                },
                "excluded_occurrences": [
                    {
                        "event_index": item["event_index"],
                        "keyword": item["keyword"],
                        "tags": list(item["tags"]),
                        "year": item["year"],
                        "polarity": item["polarity"],
                        "text": item["text"],
                    }
                    for item in scan["occurrences"]
                    if item["tags"]
                ],
            }
        )
    cases.sort(key=lambda case: case["case_id"])
    return cases


# ---------------------------------------------------------------------------
# 抽样与人工审计
# ---------------------------------------------------------------------------


def select_audit_sample(cases: list[dict[str, Any]], size: int = 20) -> list[dict[str, Any]]:
    """20 例审计：标签为 1 的案例按关键词表轮转，每个有干净命中的词至少覆盖一次。"""
    hits = [case for case in cases if case["role_change"] == 1]
    selected: list[dict[str, Any]] = []
    used: set[str] = set()
    while len(selected) < size:
        progressed = False
        for keyword in ROLE_KEYWORDS:
            if len(selected) >= size:
                break
            for case in hits:
                if case["case_id"] in used:
                    continue
                keywords = {word for item in case["evidence_events"] for word in item["keywords"]}
                if keyword in keywords:
                    selected.append(case)
                    used.add(case["case_id"])
                    progressed = True
                    break
        if not progressed:
            break
    if len(selected) < size:
        for case in hits:
            if len(selected) >= size:
                break
            if case["case_id"] not in used:
                selected.append(case)
                used.add(case["case_id"])
    return selected


# 20 例人工结论（回 JSONL 原文逐例核对后冻结）。键 = case_id，值 = (命中词集合, 结论)。
# 命中词集合与当前标签不符、或案例不是 1 → AuditStaleError。
AUDIT_VERDICTS: dict[str, tuple[tuple[str, ...], str]] = {
    "RF-2026-000126": (
        ("升职", "转行"),
        "成立：本人「08-12 年极顺利升职加薪，14 年转行业房地产」；事件 year=2022 而正文跨 2007–2022，年份字段不可信",
    ),
    "RF-2026-000139": (("晋升",), "成立：「工作晋升，收入可以」"),
    "RF-2026-000053": (("提拔",), "成立：「进入世界 500 百强,被提拔」"),
    "RF-2026-000093": (("失业", "跳槽"), "成立：「2012 年跳槽后工作不顺利失业 1 年」"),
    "RF-2026-000066": (
        ("换工作",),
        "不成立：主体是配偶（「媳妇换工作花了 6 万」）；任务卡 §2.3 他人主体词表没有「媳妇」→ 词表缺口",
    ),
    "RF-2026-000475": (
        ("换岗",),
        "成立：「我被迫升岗级，换岗位」明确本人（原文是「升岗级」，不含「升职」）",
    ),
    "RF-2026-000178": (("升职", "调动"), "成立：「工作升职」「工作调动，升职」"),
    "RF-2026-000537": (("转行",), "成立：「转行至 IT 软件行业」"),
    "RF-2026-000108": (("辞职",), "成立：「同一年辞职了」，另有「有钱了辞职回家写书」"),
    "RF-2026-000001": (("裸辞",), "成立：「裸辞了…自由职业方面开始写网文」"),
    "RF-2026-000041": (
        ("失业",),
        "成立：「彻底不工作了…在家里失业躺平」（本人；「家里」不在他人词表，未误伤）",
    ),
    "RF-2026-000729": (
        ("任职",),
        "成立：「这个月再小公司任职小经理」（本人；含原文错字「再」）",
    ),
    "RF-2026-000173": (
        ("入职",),
        "成立：「2022 年八月离职，2023 年 3 月新入职一家公司到 6 月离职」",
    ),
    "RF-2026-000258": (("升职",), "成立：「破财，升职，做手术」（升职为本人事实）"),
    "RF-2026-000236": (
        ("晋升",),
        "不成立：「再坚持就有机会晋升」是意向；任务卡 §2.3 意向语表没有「机会」→ 词表缺口",
    ),
    "RF-2026-000302": (("提拔",), "成立：「被提拔升職加薪」（繁体「職」；公务员）"),
    "RF-2026-000118": (("跳槽",), "成立：「跳槽到央企华润集团」"),
    "RF-2026-000154": (("换工作",), "成立：「经常换工作」（概括性陈述，非单次事件）"),
    "RF-2026-000333": (
        ("换工作", "调动"),
        "成立：「换工作，到管理层」「频繁调动工作」",
    ),
    "RF-2026-000538": (
        ("转行",),
        "成立：2021「有机会转行做 IT…从事大型央企运维岗位」+ profile「IT 技术工程师」；但与 000537 是同一人两次提交（近重复，文本不同未被哈希剔除）",
    ),
}


def _clean_keywords(case: dict[str, Any]) -> tuple[str, ...]:
    return tuple(sorted({word for item in case["evidence_events"] for word in item["keywords"]}))


def build_audit_rows(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    sample = select_audit_sample(cases)
    rows: list[dict[str, Any]] = []
    for index, case in enumerate(sample, start=1):
        keywords = _clean_keywords(case)
        frozen = AUDIT_VERDICTS.get(case["case_id"])
        if frozen is None:
            raise AuditStaleError(f"{case['case_id']} 缺少冻结的人工审计结论")
        frozen_keywords, verdict = frozen
        if tuple(sorted(frozen_keywords)) != keywords:
            raise AuditStaleError(
                f"{case['case_id']} 冻结命中词 {frozen_keywords} != 当前 {keywords}"
            )
        if case["role_change"] != 1:
            raise AuditStaleError(f"{case['case_id']} 应审计 1 侧，当前 role_change={case['role_change']}")
        rows.append(
            {
                "index": index,
                "case_id": case["case_id"],
                "gender": case["gender"],
                "chart_ready": case["chart_ready"],
                "matched_keywords": list(keywords),
                "evidence_events": case["evidence_events"],
                "verdict": verdict,
            }
        )
    return rows


# 四类排除的人工样例（回原文核对后冻结）。build 时校验该案例确有该关键词命中且带该标签；
# 提问样例校验该案例的全部事件都是提问。
EXCLUSION_AUDIT: tuple[dict[str, str], ...] = (
    {
        "type": "他人主体",
        "tag": "other_subject",
        "case_id": "RF-2026-000243",
        "keyword": "调动",
        "verdict": "正确：主体是父亲（「因父亲工作调动…来杭州读书」）",
    },
    {
        "type": "他人主体",
        "tag": "other_subject",
        "case_id": "RF-2026-000651",
        "keyword": "下岗",
        "verdict": "正确：主体是父母（「父母下岗」）",
    },
    {
        "type": "他人主体",
        "tag": "other_subject",
        "case_id": "RF-2026-000329",
        "keyword": "升职",
        "verdict": "误伤：「儿子出生，同年工作升职」升职是本人，儿子出生只是并列事件",
    },
    {
        "type": "意向语",
        "tag": "aspiration",
        "case_id": "RF-2026-000233",
        "keyword": "换工作",
        "verdict": "正确：「打算换工作」未发生",
    },
    {
        "type": "意向语",
        "tag": "aspiration",
        "case_id": "RF-2026-000728",
        "keyword": "提拔",
        "verdict": "误伤：「2011 年提拔副科…想知道未来的事」提拔已发生，「想」在句尾",
    },
    {
        "type": "否定",
        "tag": "negation",
        "case_id": "RF-2026-000834",
        "keyword": "升职",
        "verdict": "正确：「没有升职加薪」明确否定",
    },
    {
        "type": "否定",
        "tag": "negation",
        "case_id": "RF-2026-000073",
        "keyword": "调动",
        "verdict": "误伤：「丁未 调岗 调动工作」的「未」是年柱用字，不是否定词",
    },
    {
        "type": "否定",
        "tag": "negation",
        "case_id": "RF-2026-000632",
        "keyword": "辞职",
        "verdict": "误伤：「没有一个月辞职」意为「不到一个月就辞职」，事实已发生",
    },
    {
        "type": "提问",
        "tag": "question",
        "case_id": "RF-2026-000002",
        "keyword": "",
        "verdict": "按卡片正确排除整段提问；但同段「2018 年事业顺利，找到了一份好工作」是本人真证据 → 已知代价",
    },
)


def build_exclusion_audit(cases: list[dict[str, Any]], events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id = {case["case_id"]: case for case in cases}
    events_by_case: dict[str, list[dict[str, Any]]] = {}
    for event in events:
        events_by_case.setdefault(event["case_id"], []).append(event)
    rows: list[dict[str, Any]] = []
    for entry in EXCLUSION_AUDIT:
        case = by_id.get(entry["case_id"])
        if case is None:
            raise AuditStaleError(f"排除样例 {entry['case_id']} 不在基础集")
        if entry["tag"] == "question":
            question_events = [event for event in events_by_case[entry["case_id"]] if event["question"]]
            if not question_events or case["text_events"]["usable"] != 0:
                raise AuditStaleError(f"{entry['case_id']} 不是「全部事件都是提问」")
            primary = question_events[0]
            rows.append(
                {
                    **entry,
                    "text": primary["text"],
                    "year": primary["year"],
                    "polarity": primary["polarity"],
                }
            )
            continue
        matches = [
            item
            for item in case["excluded_occurrences"]
            if item["keyword"] == entry["keyword"] and entry["tag"] in item["tags"]
        ]
        if not matches:
            raise AuditStaleError(
                f"{entry['case_id']} 未找到 {entry['keyword']} 的 {entry['tag']} 排除"
            )
        rows.append(
            {
                **entry,
                "text": matches[0]["text"],
                "year": matches[0]["year"],
                "polarity": matches[0]["polarity"],
            }
        )
    return rows


# 已知误判 / 边界（人工归纳；本版只记录，不就地改判）。
KNOWN_ISSUES: tuple[tuple[str, str, str], ...] = (
    (
        "他人主体词表缺口",
        "「媳妇/太太/爱人」等配偶称谓不在任务卡 §2.3 词表",
        "000066「媳妇换工作」判 1（审计不成立）；000903「老公辞职」因窗口内无自称被正确排除",
    ),
    (
        "他人主体窗口误伤",
        "家人只作并列事件时，关键词附近仍被当成主体，整条命中被排除",
        "000329「儿子出生，同年工作升职」、000130「现失业家成员:父母…」、"
        "000543「换工作，养父母…」、000493「(对象是现在的老公)…换工作」→ 真阳性丢失",
    ),
    (
        "意向语「机会」缺口",
        "「有机会晋升 / 有机会转行」不在任务卡 §2.3 意向语表",
        "000236「再坚持就有机会晋升」判 1（审计不成立）；000537 的「偶然机会，转行至」是既成事实，"
        "说明「机会」本身不能一刀切",
    ),
    (
        "意向语「想」误伤",
        "「想知道 / 想种植 / 一度想离职」等句尾「想」触发整段排除",
        "000728（2011 提拔副科、2021 提拔正科）、000045（离职失业至今）、000097（20 年 9 月失业）、"
        "000567（转行了）、000595（跳槽去了药厂）被排除",
    ),
    (
        "否定窗口 6 字误伤",
        "「未 / 没」与干支用字或短语边界冲突",
        "000073「丁未」的「未」；000632「没有一个月辞职」＝不到一个月就辞职；"
        "000635「无业，毕业即失业」；000903「没上一年辞职」",
    ),
    (
        "学业 / 语义越界",
        "「提拔 / 晋升」可用于班干部或职场外身份",
        "000421「有贵人老师提拔，晋升了变成了小委员」、000448「初三提拔为班长」判 1",
    ),
    (
        "未发生",
        "「面临失业」「愿意帮助我调动」是未来或他人意愿，词表未覆盖",
        "000318「面临失业」、000924「愿意帮助我调动」判 1",
    ),
    (
        "提问整段代价",
        "一段里夹着真证据也会被一票否决（任务卡口径：不做段内切分）",
        "56 例全部事件都是提问；000002 同段「2018 年事业顺利，找到了一份好工作」被一起排除",
    ),
    (
        "文本去重代价",
        "全同文案例失去全部文本 → 按 null 计（宁缺勿泄漏）",
        "000029、000156、000287、000462、000504、000961 共 6 例；000287 的 4 条事件全为 000286 的重复",
    ),
    (
        "近重复未剔除",
        "同一人两次提交、文本措辞不同，规范化哈希无法识别",
        "000537 / 000538（同一人，出生日期 9-30 vs 8-30，正文几乎同义）、"
        "000667 / 000668（仅差「获得」二字）；两对都判 1 → 仍可能泄漏",
    ),
    (
        "时间不可信",
        "事件 year 与正文年份不一致",
        "000126 year=2022，正文跨 2007–2022 → 只做「是否」，不做「何时」",
    ),
    (
        "概括性陈述",
        "「经常换工作」不是单次事件，不能支撑「何时」",
        "000154 判 1（成立，但粒度粗）",
    ),
)


# ---------------------------------------------------------------------------
# 统计与 payload
# ---------------------------------------------------------------------------


def _share_pct(part: int, total: int) -> float:
    return round(100.0 * part / total, 2) if total else 0.0


def _rate(positive: int, null: int) -> dict[str, Any]:
    denominator = 1 + null
    return {
        "role_change_1": positive,
        "null": null,
        "n": positive + null,
        "formula": "1 / (1 + null)",
        "rate": round(positive / denominator, 4) if denominator else 0.0,
        "percent": round(100.0 * positive / denominator, 2) if denominator else 0.0,
    }


def build_payload(records: list[dict[str, Any]], source_sha: str) -> dict[str, Any]:
    unique, dedupe_stats = dedupe_records(records)
    events = collect_events(unique)
    text_dedup = dedupe_event_texts(events)
    cases = build_cases(unique, events)

    question_events = sum(1 for event in events if event["question"])
    usable_events = len(events) - question_events
    cases_all_events_questions = sum(
        1 for case in cases if case["text_events"]["occupation"] == case["text_events"]["question"]
    )
    cases_without_usable_event = sum(
        1 for case in cases if case["text_events"]["usable"] == 0
    )
    chart_ready_cases = [case for case in cases if case["chart_ready"]]
    positive_cases = [case for case in cases if case["role_change"] == 1]
    null_cases = [case for case in cases if case["role_change"] is None]
    work_no_change_cases = [case for case in cases if case["work_no_change"] == 1]

    all_rate = _rate(len(positive_cases), len(null_cases))
    chart_rate = _rate(
        sum(1 for case in chart_ready_cases if case["role_change"] == 1),
        sum(1 for case in chart_ready_cases if case["role_change"] is None),
    )

    exclusion_occurrences: dict[str, int] = {"other_subject": 0, "aspiration": 0, "negation": 0}
    exclusion_cases: dict[str, set[str]] = {"other_subject": set(), "aspiration": set(), "negation": set()}
    for case in cases:
        for item in case["excluded_occurrences"]:
            for tag in item["tags"]:
                exclusion_occurrences[tag] += 1
                exclusion_cases[tag].add(case["case_id"])
    raw_hit_cases = [case for case in cases if case["evidence_events"] or case["excluded_occurrences"]]

    payload: dict[str, Any] = {
        "schema": SCHEMA,
        "task": TASK,
        "script": SCRIPT,
        "frozen_at": FROZEN_AT,
        "definition": {
            "label": "role_change",
            "values": {
                "1": "任一 occupation 事件通过四类排除且命中冻结关键词（既成角色变化证据）",
                "null": "其余情况（没有可用证据）",
            },
            "forbid_zero": True,
            "zero_rationale": "0 侧是沉默不是证据（T-159 裁决）：513/620 非命中里 411 例只提工作不提变化、102 例无事业话语",
            "work_no_change": "有非提问 occupation 文本、但无干净命中 → 1（诊断标记，不是标签）",
            "keywords": list(ROLE_KEYWORDS),
            "question": {
                "markers": list(QUESTION_MARKERS),
                "scope": "整段事件命中任一即不作证据（同案其余事件独立判定）",
            },
            "exclusions": {
                "other_subject": {
                    "terms": list(OTHER_SUBJECTS),
                    "self_terms": list(SELF_SUBJECTS),
                    "window_chars": OTHER_SUBJECT_WINDOW,
                    "rule": "关键词两侧各 window_chars 字内出现他人词，且同一窗口内无 我/本人/自己 → 该次命中不作证据",
                },
                "aspiration": {
                    "markers": list(ASPIRATION_MARKERS),
                    "scope": "整段事件",
                },
                "negation": {
                    "markers": list(NEGATION_MARKERS),
                    "window_chars": NEGATION_WINDOW,
                    "rule": "关键词前 window_chars 字内出现否定词 → 该次命中不作证据",
                },
            },
            "text_dedup": {
                "normalization": "去首尾空白、连续空白合一；去重键再移除全部空白（空白不承载语义，用于复现 T-159 的 19 组 / 40 条泄漏面）",
                "hash": "sha256",
                "policy": "跨案例同文只保留 raw_id 最小的一条；同案例内同文折叠；其余记 dropped_duplicate_text",
            },
            "label_side_effect": "文本被剔重后，该案例失去这条证据 → 按 null 计（防跨案例泄漏）",
            "birth_fields": (
                "chart_ready 只用 birth_datetime_raw（可解析且含时刻）；birth_dt / time_basis "
                "是该解析口径（clock_beijing），未使用 true_solar_time_raw，也不派生盘面事实"
            ),
        },
        "source": {
            "path": SOURCE_PATH.relative_to(ROOT).as_posix(),
            "sha256": source_sha,
            "records": len(records),
        },
        "counts": {
            "records": len(records),
            "unique_cases": len(unique),
            "duplicate_groups": dedupe_stats["groups"],
            "duplicate_extra_records": dedupe_stats["extra_records"],
            "occupation_cases": len(cases),
            "occupation_events": len(events),
            "question_events": question_events,
            "usable_events": usable_events,
            "cases_all_events_questions": cases_all_events_questions,
            "cases_without_usable_event": cases_without_usable_event,
            "gender_ok_cases": sum(1 for case in cases if case["gender"] in ("男", "女")),
            "birth_date_ok_cases": sum(1 for case in cases if case["birth_dt"]),
            "chart_ready_cases": len(chart_ready_cases),
            "dropped_duplicate_text": text_dedup["dropped_events"],
            "dropped_duplicate_text_usable_events": text_dedup["dropped_usable_events"],
            "dropped_duplicate_text_question_events": text_dedup["dropped_question_events"],
            "text_dedup_cases_affected": text_dedup["cases_affected"],
            "role_change_1": len(positive_cases),
            "role_change_null": len(null_cases),
            "role_change_1_chart_ready": chart_rate["role_change_1"],
            "work_no_change": len(work_no_change_cases),
            "work_no_change_chart_ready": sum(
                1 for case in chart_ready_cases if case["work_no_change"] == 1
            ),
        },
        "baseline": {
            "all_cases": all_rate,
            "chart_ready": chart_rate,
            "work_no_change_share_pct": {
                "all_cases": _share_pct(len(work_no_change_cases), len(cases)),
                "chart_ready": _share_pct(
                    sum(1 for case in chart_ready_cases if case["work_no_change"] == 1),
                    len(chart_ready_cases),
                ),
            },
        },
        "text_dedup": text_dedup,
        "exclusions": {
            "occurrences": exclusion_occurrences,
            "cases": {tag: len(ids) for tag, ids in sorted(exclusion_cases.items())},
            "raw_hit_cases": len(raw_hit_cases),
            "lost_cases": len(raw_hit_cases) - len(positive_cases),
            "cases_all_occurrences_tagged": {
                tag: sum(
                    1
                    for case in cases
                    if case["excluded_occurrences"]
                    and all(tag in item["tags"] for item in case["excluded_occurrences"])
                )
                for tag in ("other_subject", "aspiration", "negation")
            },
        },
        "cases": cases,
        "audit": {
            "sample_policy": "标签为 1 的案例按关键词表轮转取样，每个有干净命中的词至少覆盖一次，至多 20 例",
            "sample_size": 20,
            "rows": build_audit_rows(cases),
            "exclusion_examples": build_exclusion_audit(cases, events),
            "known_issues": [
                {"type": kind, "phenomenon": what, "evidence": where}
                for kind, what, where in KNOWN_ISSUES
            ],
        },
        "invariants": {
            "role_change_1_plus_null": len(positive_cases) + len(null_cases),
            "occupation_cases": len(cases),
            "chart_ready_cases": len(chart_ready_cases),
            "zero_labels": sum(1 for case in cases if case["role_change"] == 0),
        },
    }

    _assert_labels(payload)
    _assert_no_board_fields(payload)
    payload["payload_sha256"] = _payload_sha256(payload)
    return payload


def _assert_labels(payload: dict[str, Any]) -> None:
    """标签只能是 1/null，且不允许 bool 冒充 int。"""
    for case in payload["cases"]:
        value = case["role_change"]
        if value is not None and not (type(value) is int and value == 1):
            raise FunnelInvariantError(f"{case['case_id']} role_change 非 1/null：{value!r}")
    if payload["invariants"]["zero_labels"] != 0:
        raise FunnelInvariantError("role_change 出现 0")
    if payload["invariants"]["role_change_1_plus_null"] != payload["counts"]["occupation_cases"]:
        raise FunnelInvariantError("role_change 1 + null != occupation 案例数")


def check_invariants(payload: dict[str, Any]) -> None:
    """任务卡 §1 冻结计数与 §2.4 标签可加性（仅对全量数据成立）。"""
    counts = payload["counts"]
    expected = {
        "records": EXPECTED_RECORDS,
        "unique_cases": EXPECTED_UNIQUE,
        "occupation_cases": EXPECTED_OCCUPATION_CASES,
        "occupation_events": EXPECTED_OCCUPATION_EVENTS,
        "chart_ready_cases": EXPECTED_CHART_READY,
    }
    for key, value in expected.items():
        if counts[key] != value:
            raise FunnelInvariantError(f"{key} {counts[key]} != {value}")
    invariants = payload["invariants"]
    if counts["role_change_1"] + counts["role_change_null"] != counts["occupation_cases"]:
        raise FunnelInvariantError("role_change 1 + null != occupation 案例数")
    if counts["usable_events"] + counts["question_events"] != counts["occupation_events"]:
        raise FunnelInvariantError("usable_events + question_events != occupation_events")
    if invariants["zero_labels"] != 0:
        raise FunnelInvariantError("role_change 出现 0")


def _assert_no_board_fields(payload: Any, path: str = "$") -> None:
    """防泄漏：payload 及其键名不得出现盘面字段。"""
    if isinstance(payload, dict):
        for key, value in payload.items():
            lowered = str(key).lower()
            for token in DISALLOWED_FIELD_TOKENS:
                if token in lowered:
                    raise FunnelInvariantError(f"标签文件出现盘面字段：{path}.{key}")
            _assert_no_board_fields(value, f"{path}.{key}")
    elif isinstance(payload, list):
        for index, value in enumerate(payload):
            _assert_no_board_fields(value, f"{path}[{index}]")


# ---------------------------------------------------------------------------
# 落盘
# ---------------------------------------------------------------------------


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _payload_sha256(payload: dict[str, Any]) -> str:
    core = {key: value for key, value in payload.items() if key != "payload_sha256"}
    material = json.dumps(core, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def _write_if_changed(path: Path, text: str) -> bool:
    if path.exists() and path.read_text(encoding="utf-8") == text:
        return False
    path.write_text(text, encoding="utf-8")
    return True


def _cell(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def _table(header: list[str], body: list[list[Any]]) -> list[str]:
    lines = ["| " + " | ".join(_cell(item) for item in header) + " |"]
    lines.append("|" + "|".join("---" for _ in header) + "|")
    for row in body:
        lines.append("| " + " | ".join(_cell(item) for item in row) + " |")
    return lines


def summarise_text(text: str, limit: int = TEXT_SUMMARY_LIMIT) -> str:
    compact = " ".join((text or "").split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 1] + "…"


def snippet_around(text: str, token: str, limit: int = TEXT_SUMMARY_LIMIT) -> str:
    compact = " ".join((text or "").split())
    if len(compact) <= limit:
        return compact
    index = compact.find(token) if token else -1
    if index < 0:
        return summarise_text(compact, limit)
    start = max(0, min(index - (limit - len(token)) // 2, len(compact) - limit))
    head = "…" if start > 0 else ""
    tail = "…" if start + limit < len(compact) else ""
    return head + compact[start : start + limit] + tail


def render_report(payload: dict[str, Any]) -> str:
    """渲染人读报告（纯函数，只依赖 payload，确定性）。"""
    counts = payload["counts"]
    baseline = payload["baseline"]
    dedup = payload["text_dedup"]
    exclusions = payload["exclusions"]
    audit = payload["audit"]
    cases = payload["cases"]

    lines: list[str] = []
    add = lines.append
    add("# 事业角色变化标签 v1（T-161）")
    add("")
    add("> 从 `occupation` 事件文本造 `role_change` 标签：**1 = 有角色变化证据；null = 无可用证据；不造 0**。")
    add("> 只用事件文本与 polarity，不读任何八字/盘面字段，不评分、不建盘。")
    add(
        f"> 数据源 `{payload['source']['path']}`（sha256 `{payload['source']['sha256']}`，"
        f"{counts['records']} 条）。"
    )
    add("")

    add("## 0. 标签与结果")
    add("")
    lines.extend(
        _table(
            ["项", "数值", "说明"],
            [
                ["基础集（occupation 案例）", counts["occupation_cases"], "`duplicate_key` 去重后 620"],
                ["其中 chart_ready", counts["chart_ready_cases"], "出生日期可解析且含时刻（只用出生字段）"],
                ["role_change = 1", counts["role_change_1"], "干净命中的案例"],
                ["role_change = null", counts["role_change_null"], "没有可用证据；**没有 0**"],
                ["work_no_change = 1", counts["work_no_change"], "有非提问文本但无干净命中（诊断，不是标签）"],
                ["dropped_duplicate_text", counts["dropped_duplicate_text"], "文本去重删掉的事件条，涉及案例数 "
                 + str(counts["text_dedup_cases_affected"])],
            ],
        )
    )
    add("")
    add(
        f"**基线 `1/(1+null)`**：全样本 {baseline['all_cases']['role_change_1']}/"
        f"{baseline['all_cases']['n']} → **{baseline['all_cases']['percent']:.2f}%**；"
        f"chart_ready {baseline['chart_ready']['role_change_1']}/{baseline['chart_ready']['n']} → "
        f"**{baseline['chart_ready']['percent']:.2f}%**。"
    )
    add("")
    add(
        f"`work_no_change` 占比（仅参考，不进基线）：全样本 "
        f"{baseline['work_no_change_share_pct']['all_cases']:.2f}%，chart_ready "
        f"{baseline['work_no_change_share_pct']['chart_ready']:.2f}%。"
    )
    add("")

    add("## 1. 漏斗（620 / 614）")
    add("")
    lines.extend(
        _table(
            ["层级", "数量", "说明"],
            [
                ["原始记录", counts["records"], "JSONL 有效行"],
                ["按 duplicate_key 去重", counts["unique_cases"], f"重复组 {counts['duplicate_groups']}，多余 {counts['duplicate_extra_records']} 条"],
                ["有 occupation 事件的案例", counts["occupation_cases"], "任务卡 §1 的 620"],
                ["occupation 事件条", counts["occupation_events"], "任务卡 §1 的 957"],
                ["其中整段判为提问", counts["question_events"], "不作证据；同案其余事件独立判定"],
                ["可用证据事件（未去重文本）", counts["usable_events"], "非提问事件"],
                ["文本去重删掉", counts["dropped_duplicate_text"], f"跨案例 {dedup['dropped_cross_case']} / 同案例 {dedup['dropped_within_case']}；非提问 {counts['dropped_duplicate_text_usable_events']} / 提问 {counts['dropped_duplicate_text_question_events']}；涉及 {dedup['cases_affected']} 例"],
                ["全部事件都是提问的案例", counts["cases_all_events_questions"], "无文本可判 → null"],
                [
                    "文本去重后无可用事件的案例",
                    counts["cases_without_usable_event"],
                    "含仅因去重失去全部文本的 "
                    + str(counts["cases_without_usable_event"] - counts["cases_all_events_questions"])
                    + " 例",
                ],
                ["性别可判（男/女）", counts["gender_ok_cases"], "独立口径，不叠加"],
                ["出生日期可解析", counts["birth_date_ok_cases"], "独立口径，不叠加"],
                ["chart_ready（日期+时刻）", counts["chart_ready_cases"], "本标签只用出生字段，不派生盘面事实"],
            ],
        )
    )
    add("")
    add(
        "口径：基础集 620 不叠加性别/出生过滤（与 T-159 同口径）；性别 617、出生日期 616 是独立口径；"
        "chart_ready 614 用于第二条基线。"
    )
    add("")
    add(
        f"不变量：`role_change` 1 + null = {payload['invariants']['role_change_1_plus_null']} = "
        f"occupation 案例 {payload['invariants']['occupation_cases']}；chart_ready = "
        f"{payload['invariants']['chart_ready_cases']}；0 标签 = {payload['invariants']['zero_labels']}。"
    )
    add("")

    add("## 2. 关键词与四类排除")
    add("")
    add("关键词（任务卡 §2.2，原样冻结，未为阳性率调词）：")
    add("")
    add("、".join(f"`{keyword}`" for keyword in payload["definition"]["keywords"]))
    add("")
    add("排除规则（任一命中即该事件/该次命中不作证据）：")
    add("")
    lines.extend(
        _table(
            ["类型", "口径", "规模"],
            [
                [
                    "提问",
                    "整段事件含 " + "、".join(f"`{m}`" for m in payload["definition"]["question"]["markers"]),
                    f"{counts['question_events']} 条事件",
                ],
                [
                    "他人主体",
                    f"关键词两侧各 {payload['definition']['exclusions']['other_subject']['window_chars']} 字内含他人词，且同一窗口内无 我/本人/自己",
                    f"{exclusions['occurrences']['other_subject']} 次 / {exclusions['cases']['other_subject']} 例有命中",
                ],
                [
                    "意向语",
                    "整段事件含 " + "、".join(f"`{m}`" for m in payload["definition"]["exclusions"]["aspiration"]["markers"]),
                    f"{exclusions['occurrences']['aspiration']} 次 / {exclusions['cases']['aspiration']} 例有命中",
                ],
                [
                    "否定",
                    f"关键词前 {payload['definition']['exclusions']['negation']['window_chars']} 字内含 "
                    + "、".join(f"`{m}`" for m in payload["definition"]["exclusions"]["negation"]["markers"]),
                    f"{exclusions['occurrences']['negation']} 次 / {exclusions['cases']['negation']} 例有命中",
                ],
            ],
        )
    )
    add("")
    add(
        "「有命中」是排除账的规模，不等于这些案例最终都被排除（一个案例可能另有干净命中）。"
        f"合计 {exclusions['raw_hit_cases']} 例有命中，{counts['role_change_1']} 例留 1，"
        f"{exclusions['lost_cases']} 例因排除变 null（全命中被标记者：他人主体 "
        f"{exclusions['cases_all_occurrences_tagged']['other_subject']} 例 / 意向语 "
        f"{exclusions['cases_all_occurrences_tagged']['aspiration']} 例 / 否定 "
        f"{exclusions['cases_all_occurrences_tagged']['negation']} 例，可重叠）。"
    )
    add("")

    add("## 3. 20 例审计（标签 = 1 侧）")
    add("")
    add(audit["sample_policy"] + "。")
    add("")
    audit_rows: list[list[Any]] = []
    for row in audit["rows"]:
        primary = row["evidence_events"][0] if row["evidence_events"] else {}
        keyword = row["matched_keywords"][0] if row["matched_keywords"] else ""
        audit_rows.append(
            [
                row["index"],
                f"`{row['case_id']}`",
                "、".join(row["matched_keywords"]) if row["matched_keywords"] else "（无）",
                f"{primary.get('year')} / {primary.get('polarity')}",
                snippet_around(primary.get("text", ""), keyword),
                row["verdict"] or "（待填）",
            ]
        )
    lines.extend(
        _table(
            ["#", "case_id", "命中词", "年份/极性", "证据摘要（全文见 JSON）", "人工结论"],
            audit_rows,
        )
    )
    add("")
    passed = sum(1 for row in audit["rows"] if row["verdict"].startswith("成立"))
    add(
        f"统计：**{passed}/{len(audit['rows'])} 成立**；不成立 "
        f"{len(audit['rows']) - passed} 例（均为任务卡词表缺口：他人主体「媳妇」、意向语「机会」）。"
    )
    add("")
    if audit["exclusion_examples"]:
        add("四类排除的回原文样例：")
        add("")
        lines.extend(
            _table(
                ["类型", "case_id", "命中词", "原文（节选）", "人工结论"],
                [
                    [
                        row["type"],
                        f"`{row['case_id']}`",
                        row["keyword"],
                        snippet_around(row["text"], row["keyword"]),
                        row["verdict"],
                    ]
                    for row in audit["exclusion_examples"]
                ],
            )
        )
        add("")

    add("## 4. 已知误判与代价")
    add("")
    if audit["known_issues"]:
        lines.extend(
            _table(
                ["类型", "现象", "证据"],
                [[item["type"], item["phenomenon"], item["evidence"]] for item in audit["known_issues"]],
            )
        )
    else:
        add("（待填）")
    add("")

    add("## 5. 文本去重明细")
    add("")
    add(
        "规范化（去首尾空白、连续空白合一）后再移除全部空白，取 sha256"
        "（空白不承载语义；只折叠连续空白会漏掉仅空白位置不同的同文，无法复现 T-159 的泄漏面）："
        f"重复组 **{dedup['groups_with_duplicates']}**，"
        f"涉及事件 **{sum(item['events'] for item in dedup['details'])}** 条，删掉 **{dedup['dropped_events']}** 条"
        f"（跨案例 {dedup['dropped_cross_case']} / 同案例 {dedup['dropped_within_case']}），"
        f"涉及案例 **{dedup['cases_affected']}** 例。"
    )
    add("")
    add(
        f"其中跨案例组 **{dedup['cross_case_groups']}** 组 / **{dedup['cross_case_events']}** 条"
        "（T-159 预警的泄漏面）；同案例折叠 "
        f"**{dedup['within_case_groups']}** 组 / **{dedup['within_case_events']}** 条。"
    )
    add("")
    if dedup["details"]:
        lines.extend(
            _table(
                ["kept case_id", "保留事件", "组内事件", "删掉", "跨案例", "被删 case_id", "文本摘要"],
                [
                    [
                        f"`{item['kept_case_id']}`",
                        item["kept_event_index"],
                        item["events"],
                        item["dropped"],
                        "是" if item["cross_case"] else "否",
                        "、".join(f"`{case_id}`" for case_id in item["dropped_case_ids"]) or "—",
                        summarise_text(item["text"]),
                    ]
                    for item in dedup["details"]
                ],
            )
        )
        add("")

    add("## 6. 复现与边界")
    add("")
    add("```bash")
    add(".venv\\Scripts\\python.exe -m tools.career_role_change_labels")
    add("```")
    add("")
    add("- 无运行时间戳；两次运行 JSON 与本文逐字节一致。")
    add("- 不使用任何八字/盘面字段；`birth_dt` 只记录出生解析结果，不参与打标。")
    add("- 事件 `year` 不可信（T-159：000126 year=2022，正文跨 2007–2022）→ 本标签只做「是否」，不做「何时」。")
    add("- 事件文本被剔重后案例失去该证据 → 按 null 计（宁缺勿泄漏）。")
    add("")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# 入口
# ---------------------------------------------------------------------------


def main() -> int:
    try:
        records = load_records()
    except SourceError as exc:
        print(f"[T-161] {exc}", file=sys.stderr)
        return 4
    source_sha = _sha256_file(SOURCE_PATH)
    try:
        payload = build_payload(records, source_sha)
        check_invariants(payload)
    except FunnelInvariantError as exc:
        print(f"[T-161] 计数不变量不通过：{exc}", file=sys.stderr)
        return 3
    except AuditStaleError as exc:
        print(f"[T-161] 冻结审计结论失效：{exc}", file=sys.stderr)
        return 5

    _write_if_changed(JSON_PATH, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    _write_if_changed(REPORT_PATH, render_report(payload))
    print(
        "[T-161] "
        f"cases={payload['counts']['occupation_cases']} "
        f"chart_ready={payload['counts']['chart_ready_cases']} "
        f"role_change=1:{payload['counts']['role_change_1']} "
        f"null:{payload['counts']['role_change_null']} "
        f"work_no_change:{payload['counts']['work_no_change']} "
        f"dropped_duplicate_text:{payload['counts']['dropped_duplicate_text']} "
        f"payload_sha256={payload['payload_sha256'][:12]}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

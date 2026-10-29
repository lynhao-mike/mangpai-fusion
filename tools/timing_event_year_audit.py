"""T-168 · 应期事件年份审计（只读）。

逐例核对 ``META/timing-eval-set-v1.json`` 里 382 例婚姻事件的 ``year`` 与
``text`` / 原文是否一致，回答 ``tasks/T-168/PROMPT.md`` §2 的 5 个问题，
并按**预注册**分类产出可复现的敏感性剔除名单。

本脚本**不评分、不建模、不建盘、不改任何 year 或评测集**；只读三份输入，
产出 ``META/timing-event-year-audit-v1.json`` / ``.md``，两次运行逐字节一致。

口径（预注册，先于结果固定）：

- 事件集合 = ``usable_for_timing`` 的案例（382）× ``marriage_events``（547）。
- 年份识别（``extract_year_refs``）覆盖卡上要求的文本变体：
  ``2008 年``（4 位）、``08 年``（2 位，按最近世纪还原）、``二〇〇八 年``（中文数字）、
  区间 ``2008-2012 年`` / ``08-12 年`` / ``14.15 年`` / ``20～23 年``。
  2 位数只在「非时长语境」下算年份（``未来10 年``、``拍拖 12 年的女友`` 不算），
  且必须落在当事人生命周期 ``[birth_year-10, birth_year+80]`` 内。
- 四桶（互斥，``other`` 为残余，本数据应为 0）：

  | 桶 | 定义 |
  |---|---|
  | ``match`` | 文本恰好只提到 ``year`` 这一年 |
  | ``multi_year`` | 文本提到 ``year``，但同时提到别的年份（可能错抽/漏抽） |
  | ``contradiction`` | 文本提到了年份，但都不是 ``year``（差 ≥1 年） |
  | ``no_year_in_text`` | 文本没有任何年份表述 |
  | ``other`` | ``year`` 非整数 / 文本缺失等无法分类 |

- 正交口径（不改四桶）：

  * ``provenance``：原文在事件正文**紧前方**的年份记号（年表表头 / 区间端点 /
    裸年份），回答「这个 year 是不是解析器从原文年表里取的」。
  * ``marriage_years``：正文里贴着婚姻词（结婚/离婚/相亲/恋爱/分手/对象…）的年份。
    ``marriage_conflict`` = 正文点了别的婚姻年份，而 ``event.year`` 不在其中
    —— 这是「标签年不是这段婚姻事实的年」的硬信号。

- 剔除规则（``sensitivity_exclude``）：窗口内（20–35 岁）存在
  ``marriage_conflict`` 事件 → 剔除。规则写死在 ``EXCLUDE_RULE``。

运行：
    .venv\\Scripts\\python.exe -m tools.timing_event_year_audit
"""
from __future__ import annotations

import json
import re
from collections import Counter
from hashlib import sha256
from pathlib import Path
from typing import Any, Optional

ROOT = Path(__file__).resolve().parents[1]
EVAL_PATH = ROOT / "META" / "timing-eval-set-v1.json"
RAW_PATH = ROOT / "cases" / "raw_feedback" / "parsed" / "real_cases_990.jsonl"
FEAS_PATH = ROOT / "META" / "timing-feasibility-audit-v1.json"
OUT_JSON = ROOT / "META" / "timing-event-year-audit-v1.json"
OUT_MD = ROOT / "META" / "timing-event-year-audit-v1.md"

SCHEMA = "timing-event-year-audit/v1"
TASK = "T-168"
WINDOW = (20, 35)

BUCKETS = ("match", "no_year_in_text", "contradiction", "multi_year", "other")
MAIN_BUCKETS = ("match", "no_year_in_text", "contradiction", "multi_year")
SEVERITY = {"match": 0, "other": 1, "no_year_in_text": 2, "multi_year": 3, "contradiction": 4}

EXCLUDE_RULE = (
    "case_id ∈ sensitivity_exclude ⇔ 该案例存在 age∈[20,35]、bucket∈四桶 且 "
    "marriage_conflict==true 的婚姻事件；marriage_conflict ⇔ 正文有贴婚姻词的年份集合 "
    "marriage_years 非空且 event.year ∉ marriage_years（年龄 = event.year - case.birth_year）"
)

# 2 位数年份的时长语境前缀 / 后缀（命中即不当作年份）。
_DURATION_PREFIX = (
    "未来",
    "这",
    "近",
    "连续",
    "过去",
    "最近",
    "将近",
    "已经",
    "前后",
    "大约",
    "大概",
    "约",
    "几",
    "多",
    "整",
    "半",
    "个",
)
_DURATION_SUFFIX = ("的",)

# 婚姻域里程碑词（刻意不收「婚姻/感情」这类状态词，避免把「婚姻情况：」小节名当成年份锚点）。
MARRIAGE_WORDS = (
    "结婚",
    "结婚证",
    "离婚",
    "再婚",
    "复婚",
    "订婚",
    "定亲",
    "领证",
    "结了婚",
    "结的婚",
    "婚礼",
    "婚宴",
    "成亲",
    "相亲",
    "恋爱",
    "谈恋爱",
    "对象",
    "女友",
    "男友",
    "女朋友",
    "男朋友",
    "妻子",
    "丈夫",
    "老婆",
    "老公",
    "前夫",
    "前妻",
    "分手",
    "拍拖",
    "同居",
    "怀孕",
    "結婚",
    "離婚",
    "訂婚",
    "領證",
    "戀愛",
    "對象",
    "婚禮",
    "相親",
    "懷孕",
)

_CN_DIGIT = {
    "〇": "0",
    "零": "0",
    "○": "0",
    "O": "0",
    "o": "0",
    "一": "1",
    "二": "2",
    "三": "3",
    "四": "4",
    "五": "5",
    "六": "6",
    "七": "7",
    "八": "8",
    "九": "9",
}

_YEAR_MIN, _YEAR_MAX = 1900, 2100
_RANGE_SEP = "-–—~～至到"
_CLAUSE_RE = re.compile(r"[，。；！？,;!?\n、]")

_Y4_RANGE = re.compile(r"(?<!\d)((?:19|20)\d{2})\s*[-–—~～至到]\s*(\d{2,4})(?!\d)")
_Y2_RANGE = re.compile(r"(?<!\d)(\d{2})\s*([-–—~～、.,至到])\s*(\d{2})(?!\d)\s*年")
_CN4 = re.compile(r"([〇零○Oo0一二三四五六七八九]{4})\s*年")
# 原文常有「9852020 年」「2112014 年」这种粘连：年份直接贴在上一条内容的数字后面，
# 所以再补一条「后面跟 年」就允许前面是数字的规则。
_Y4 = re.compile(r"(?<!\d)((?:19|20)\d{2})(?!\d)")
_Y4_GLUED = re.compile(r"((?:19|20)\d{2})(?=\s*年)")
_Y2 = re.compile(r"(?<!\d)(\d{2})(\s*年)")

_SOURCE_GAP = re.compile(r"[\s:：,，、吉凶年()（）的于在]*")
_HEADER_OF = re.compile(r"((?:19|20)\d{2})\s*年\s*[:：]?\s*[吉凶]?\s*[,，、]?\s*$")
_T165_YEAR = re.compile(r"(?:19|20)\d{2}")


# ── 年份识别 ────────────────────────────────────────────────────────────────


def _normalize(text: str) -> str:
    """全角数字 → ASCII，避免 ``２００８ 年`` 之类的输入漏检。"""
    return "".join(chr(ord(ch) - 0xFEE0) if "０" <= ch <= "９" else ch for ch in text or "")


def _century(yy: int, ref: int) -> int:
    """把 2 位数年份按「离 ref 最近的世纪」还原为 4 位年份。"""
    value = (ref // 100) * 100 + yy
    if value - ref > 50:
        value -= 100
    elif ref - value > 50:
        value += 100
    return value


def _cn_year(token: str) -> Optional[int]:
    if not any(ch in "一二三四五六七八九" for ch in token):
        return None  # 「0000 年」这类不是年份
    return int("".join(_CN_DIGIT[ch] for ch in token))


def _lifetime_ok(year: int, birth_year: int) -> bool:
    return birth_year - 10 <= year <= birth_year + 80


def extract_year_refs(text: str, birth_year: int) -> list[dict[str, Any]]:
    """返回文本里的年份表述列表（按出现位置升序）。

    每个 ref：``kind`` / ``raw`` / ``years`` / ``start`` / ``end``。
    ``years`` 对区间是展开后的完整集合。
    """
    body = _normalize(text)
    taken = [False] * len(body)
    refs: list[dict[str, Any]] = []

    def free(start: int, end: int) -> bool:
        return not any(taken[start:end])

    def add(kind: str, match: re.Match[str], years: list[int]) -> None:
        for i in range(match.start(), match.end()):
            taken[i] = True
        refs.append(
            {
                "kind": kind,
                "raw": match.group(0).strip(),
                "years": years,
                "start": match.start(),
                "end": match.end(),
            }
        )

    for match in _Y4_RANGE.finditer(body):
        if not free(match.start(), match.end()):
            continue
        start_year = int(match.group(1))
        end_year = int(match.group(2))
        if len(match.group(2)) == 2:
            end_year = _century(end_year, start_year)
        if end_year < start_year or end_year - start_year > 30:
            continue
        if not (_YEAR_MIN <= start_year <= _YEAR_MAX and _YEAR_MIN <= end_year <= _YEAR_MAX):
            continue
        if not _lifetime_ok(start_year, birth_year):
            continue
        add("y4_range", match, list(range(start_year, end_year + 1)))

    for match in _Y2_RANGE.finditer(body):
        if not free(match.start(), match.end()):
            continue
        reference = birth_year + 30
        start_year = _century(int(match.group(1)), reference)
        end_year = _century(int(match.group(3)), reference)
        if end_year < start_year or end_year - start_year > 30:
            continue
        if not (_lifetime_ok(start_year, birth_year) and _lifetime_ok(end_year, birth_year)):
            continue
        add("y2_range", match, list(range(start_year, end_year + 1)))

    for match in _CN4.finditer(body):
        if not free(match.start(), match.end()):
            continue
        year = _cn_year(match.group(1))
        if year is None or not (_YEAR_MIN <= year <= _YEAR_MAX):
            continue
        add("cn4", match, [year])

    for match in _Y4.finditer(body):
        if not free(match.start(), match.end()):
            continue
        year = int(match.group(1))
        if not _lifetime_ok(year, birth_year):
            continue
        if re.match(r"\s*[万萬元块块个多余]", body[match.end() : match.end() + 2]):
            continue  # 「2000 多万」这类金额，不是年份
        add("y4", match, [year])

    for match in _Y4_GLUED.finditer(body):
        if not free(match.start(), match.end()):
            continue
        year = int(match.group(1))
        if not _lifetime_ok(year, birth_year):
            continue
        if re.match(r"\s*[万萬元块块个多余]", body[match.end() : match.end() + 2]):
            continue
        add("y4", match, [year])

    for match in _Y2.finditer(body):
        if not free(match.start(), match.end()):
            continue
        prefix = body[max(0, match.start() - 3) : match.start()]
        if any(prefix.endswith(word) for word in _DURATION_PREFIX):
            continue
        if body[match.end() : match.end() + 1] in _DURATION_SUFFIX:
            continue
        year = _century(int(match.group(1)), birth_year + 30)
        if not _lifetime_ok(year, birth_year):
            continue
        add("y2", match, [year])

    refs.sort(key=lambda item: item["start"])
    return refs


# ── 分类 ────────────────────────────────────────────────────────────────────


def classify_event(year: Any, text: Any, birth_year: int) -> dict[str, Any]:
    """把单条事件分到四桶之一（``other`` 为残余），并带出检出年份。"""
    if not isinstance(year, int):
        return {"bucket": "other", "refs": [], "years": [], "reason": "year_not_int"}
    body = "" if text is None else str(text)
    refs = extract_year_refs(body, birth_year)
    years = sorted({value for ref in refs for value in ref["years"]})
    if not years:
        bucket = "no_year_in_text"
    elif year not in years:
        bucket = "contradiction"
    elif len(years) >= 2:
        bucket = "multi_year"
    else:
        bucket = "match"
    return {"bucket": bucket, "refs": refs, "years": years, "reason": None}


# ── 婚姻年份锚定 ────────────────────────────────────────────────────────────

def _clause_after(text: str, ref: dict[str, Any]) -> str:
    return _CLAUSE_RE.split(text[ref["end"] : ref["end"] + 14], maxsplit=1)[0]


def _clause_before(text: str, ref: dict[str, Any]) -> str:
    return _CLAUSE_RE.split(text[max(0, ref["start"] - 10) : ref["start"]])[-1]


def is_marriage_ref(text: str, ref: dict[str, Any]) -> bool:
    """年份记号是否贴着婚姻词（``2015 年结婚`` / ``恋爱 2019 年``）。"""
    after = _clause_after(text, ref)
    before = _clause_before(text, ref)
    return any(word in after or word in before for word in MARRIAGE_WORDS)


def marriage_years_in(text: str, birth_year: int, refs: list[dict[str, Any]]) -> list[int]:
    return sorted({value for ref in refs if is_marriage_ref(text, ref) for value in ref["years"]})


# ── 原文依据（正交口径，不改四桶）────────────────────────────────────────────


def _locate(raw: str, text: str) -> int:
    if not text:
        return -1
    return raw.find(text)


def provenance(
    record: Optional[dict[str, Any]],
    text: str,
    year: Any,
    birth_year: int,
) -> dict[str, Any]:
    """事件 year 在原文里有没有结构依据。

    解析器把年表按年份记号切开，并把切点上的年份从正文里剥掉，所以「紧贴正文前的
    那个年份记号」就是 year 的来源。这里只做取证，不判对错：

    - ``source_kind == 'header'``：``2023 年:`` / ``2023 年`` 年表表头（区间端点已排除）；
    - ``source_kind == 'range_endpoint'``：紧贴的是一个区间的端点（``2008-2011 年``）；
    - ``source_kind == 'bare_year'``：``2013`` 这种没写「年」的切点（常在叙事/其他信息块里）；
    - ``source_kind == 'none'``：正文前 30 字内没有年份记号。
    """
    info: dict[str, Any] = {
        "text_found_in_raw": False,
        "text_offset": None,
        "text_scope": "unknown",
        "source_year": None,
        "source_kind": "none",
        "source_agrees": None,
        "year_table_header": False,
        "record_event_present": False,
        "record_event_year_differs": False,
    }
    if record is None:
        return info
    raw = record.get("raw_text") or ""
    pos = _locate(raw, text)
    if pos < 0:
        info["text_scope"] = "not_in_raw"
        return info

    info["text_found_in_raw"] = True
    info["text_offset"] = pos
    other = raw.rfind("其他信息", 0, pos)
    info["text_scope"] = "other_info_block" if (other >= 0 and pos - other < 400) else "record_year_table"

    window = raw[max(0, pos - 60) : pos]
    refs = extract_year_refs(window, birth_year)
    if refs and refs[0]["start"] == 0:
        refs = refs[1:]  # 窗口左边界可能把年份记号切成半截
    if refs:
        last = refs[-1]
        gap = window[last["end"] :]
        if _SOURCE_GAP.fullmatch(gap):
            has_nian = "年" in gap or last["raw"].endswith("年")
            before_char = window[last["start"] - 1 : last["start"]] if last["start"] else ""
            if last["kind"] in ("y4_range", "y2_range"):
                kind = "range_endpoint"
            elif has_nian and before_char in _RANGE_SEP:
                kind = "range_endpoint"
            elif has_nian:
                kind = "header"
            else:
                head = _HEADER_OF.search(window[: last["start"]])
                kind = "header" if head and int(head.group(1)) in last["years"] else "bare_year"
            info["source_year"] = last["years"][-1] if len(last["years"]) > 1 else last["years"][0]
            info["source_kind"] = kind
            info["source_agrees"] = isinstance(year, int) and year in last["years"]
            info["year_table_header"] = bool(kind == "header" and info["source_agrees"])

    for event in record.get("events") or []:
        if event.get("text") != text:
            continue
        if event.get("year") == year:
            info["record_event_present"] = True
        else:
            info["record_event_year_differs"] = True
    return info


# ── 输入 / 输出 ─────────────────────────────────────────────────────────────


def _sha256(path: Path) -> str:
    digest = sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_records(path: Path) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        records.setdefault(record["raw_id"], record)
    return records


# ── 审计主体 ────────────────────────────────────────────────────────────────


def _t165_label(text: Any, year: int) -> str:
    """复现 T-165 ``_years_in_text`` 的粗查口径（只认 4 位 19xx/20xx）。"""
    years = {int(x) for x in _T165_YEAR.findall("" if text is None else str(text))}
    if not years:
        return "no_year_in_text"
    return "match" if year in years else "mismatch"


def _event_row(case: dict[str, Any], index: int, event: dict[str, Any], record) -> dict[str, Any]:
    year = event.get("year")
    text = event.get("text")
    birth_year = case["birth_year"]
    body = "" if text is None else str(text)

    result = classify_event(year, text, birth_year)
    bucket = result["bucket"]
    refs = result["refs"]
    years = result["years"]

    prov = provenance(record, body, year, birth_year)
    marriage_years = marriage_years_in(body, birth_year, refs)
    if prov["source_agrees"]:
        cut = refs[0]["start"] if refs else len(body)
        if any(word in body[:cut] for word in MARRIAGE_WORDS):
            marriage_years = sorted(set(marriage_years) | {year})
    marriage_conflict = bool(marriage_years) and isinstance(year, int) and year not in marriage_years

    age = year - birth_year if isinstance(year, int) else None
    return {
        "case_id": case["case_id"],
        "index": index,
        "year": year,
        "age": age,
        "in_window": bool(isinstance(age, int) and WINDOW[0] <= age <= WINDOW[1]),
        "bucket": bucket,
        "years_in_text": years,
        "ref_kinds": sorted({ref["kind"] for ref in refs}),
        "marriage_years": marriage_years,
        "marriage_conflict": marriage_conflict,
        "t165_label": _t165_label(text, year) if isinstance(year, int) else "other",
        "provenance": prov,
        "text": body,
    }


def run_audit() -> dict[str, Any]:
    timing = _load_json(EVAL_PATH)
    feasibility = _load_json(FEAS_PATH)
    records = load_records(RAW_PATH)

    all_cases = timing["cases"]
    cases = [case for case in all_cases if case.get("usable_for_timing")]

    missing_records = [case["case_id"] for case in cases if case["case_id"] not in records]
    case_rows: list[dict[str, Any]] = []
    event_rows: list[dict[str, Any]] = []
    for case in cases:
        record = records.get(case["case_id"])
        events = [
            _event_row(case, index, event, record)
            for index, event in enumerate(case.get("marriage_events") or [])
        ]
        event_rows.extend(events)
        case_bucket = "match"
        for event in events:
            if SEVERITY[event["bucket"]] > SEVERITY[case_bucket]:
                case_bucket = event["bucket"]
        in_window = [event for event in events if event["in_window"]]
        case_rows.append(
            {
                "case_id": case["case_id"],
                "birth_year": case["birth_year"],
                "bucket": case_bucket,
                "n_events": len(events),
                "n_in_window": len(in_window),
                "structural_zero": not in_window,
                "event_buckets": [event["bucket"] for event in events],
                "event_years": [event["year"] for event in events],
                "window_event_years": [event["year"] for event in in_window],
                "window_buckets": [event["bucket"] for event in in_window],
                "marriage_conflicts": sum(1 for event in events if event["marriage_conflict"]),
                "year_table_header_events": sum(
                    1 for event in events if event["provenance"]["year_table_header"]
                ),
            }
        )

    event_counts = Counter(event["bucket"] for event in event_rows)
    case_counts = Counter(row["bucket"] for row in case_rows)
    in_window_events = [event for event in event_rows if event["in_window"]]
    in_window_cases = {event["case_id"] for event in in_window_events}
    structural_zero = [row["case_id"] for row in case_rows if row["structural_zero"]]
    contradictions = [event for event in event_rows if event["bucket"] == "contradiction"]
    multi_years = [event for event in event_rows if event["bucket"] == "multi_year"]
    conflicts = [event for event in event_rows if event["marriage_conflict"]]

    # ── 剔除名单（规则写死，脚本算出）────────────────────────────────────
    exclude = sorted({event["case_id"] for event in in_window_events if event["marriage_conflict"]})
    exclude_any_conflict = sorted({event["case_id"] for event in conflicts})
    exclude_literal = sorted(
        {event["case_id"] for event in in_window_events if event["bucket"] == "contradiction"}
    )
    exclude_multi = sorted(
        {event["case_id"] for event in in_window_events if event["bucket"] == "multi_year"}
    )
    exclude_no_source = sorted(
        {
            event["case_id"]
            for event in in_window_events
            if event["provenance"]["source_agrees"] is False
        }
    )

    # ── 与 T-165 粗查口径对账 ────────────────────────────────────────────
    t165 = Counter(event["t165_label"] for event in event_rows)
    label_fidelity = feasibility.get("label_fidelity") or {}
    t165_expected = {
        "match": label_fidelity.get("match"),
        "mismatch": label_fidelity.get("mismatch"),
        "no_year_in_text": label_fidelity.get("no_year_in_text"),
    }
    t165_reproduced = all(t165_expected.get(key) == t165.get(key) for key in t165_expected)

    # ── 变体覆盖 ────────────────────────────────────────────────────────
    kind_events: Counter[str] = Counter()
    kind_refs: Counter[str] = Counter()
    for event in event_rows:
        for kind in event["ref_kinds"]:
            kind_events[kind] += 1
    for case in cases:
        for event in case.get("marriage_events") or []:
            body = "" if event.get("text") is None else str(event.get("text"))
            for ref in extract_year_refs(body, case["birth_year"]):
                kind_refs[ref["kind"]] += 1
    variant_coverage = {
        kind: {"events": kind_events.get(kind, 0), "refs": kind_refs.get(kind, 0)}
        for kind in ("y4", "y2", "y4_range", "y2_range", "cn4")
    }

    source_kind = Counter(event["provenance"]["source_kind"] for event in event_rows)
    scope_by_bucket = {
        bucket: dict(
            sorted(
                Counter(
                    event["provenance"]["text_scope"]
                    for event in event_rows
                    if event["bucket"] == bucket
                ).items()
            )
        )
        for bucket in BUCKETS
    }

    payload: dict[str, Any] = {
        "schema": SCHEMA,
        "task": TASK,
        "mode": "read_only_audit",
        "deterministic": True,
        "inputs": {
            "eval_set": {"path": "META/timing-eval-set-v1.json", "sha256": _sha256(EVAL_PATH)},
            "raw_cases": {
                "path": "cases/raw_feedback/parsed/real_cases_990.jsonl",
                "sha256": _sha256(RAW_PATH),
                "records": len(records),
                "eval_source_sha256": timing.get("source", {}).get("sha256"),
            },
            "feasibility_audit": {
                "path": "META/timing-feasibility-audit-v1.json",
                "sha256": _sha256(FEAS_PATH),
                "label_fidelity": label_fidelity,
            },
        },
        "preregistration": {
            "window": list(WINDOW),
            "age_definition": "event.year - case.birth_year（整年差，T-148/评测集口径）",
            "buckets": {
                "match": "文本只提到 event.year 这一年",
                "no_year_in_text": "文本没有任何年份表述（4 位 / 2 位 / 中文数字 / 区间）",
                "contradiction": "文本提到了年份，但都不是 event.year（差 ≥1 年）",
                "multi_year": "文本提到 event.year，但同时提到别的年份（可能错抽/漏抽）",
                "other": "year 非整数 / 文本缺失等无法分类（残余桶）",
            },
            "bucket_precedence": [
                "other（无法分类）",
                "no_year_in_text（无任何年份）",
                "contradiction（年份不含 event.year）",
                "multi_year（含 event.year 但多于一年）",
                "match",
            ],
            "year_variants": {
                "y4": "19xx / 20xx 四位年份",
                "y2": "两位 + 年（08 年），按最近世纪还原，排除时长语境",
                "cn4": "中文数字四位 + 年（二〇〇八 年）",
                "y4_range": "四位起点区间（2008-2012 年 / 2013-15 年）",
                "y2_range": "两位区间（08-12 年 / 14.15 年 / 20～23 年）",
            },
            "marriage_years_rule": "年份记号的同句后面或前一短句里出现 MARRIAGE_WORDS（结婚/离婚/相亲/"
            "恋爱/分手/对象/女友/妻子…）；正文开头贴婚姻词且原文紧前年份记号与 event.year 一致时，"
            "event.year 也算婚姻年。",
            "marriage_conflict_rule": "marriage_years 非空且 event.year 不在其中",
            "sensitivity_exclude_rule": EXCLUDE_RULE,
            "sensitivity_exclude_is_primary": True,
        },
        "counts": {
            "cases_total_in_eval": len(all_cases),
            "cases": len(cases),
            "events": len(event_rows),
            "events_age_15_50": sum(
                1 for event in event_rows if isinstance(event["age"], int) and 15 <= event["age"] <= 50
            ),
            "events_in_window": len(in_window_events),
            "unique_window_years": len({(event["case_id"], event["year"]) for event in in_window_events}),
            "cases_with_window_event": len(in_window_cases),
            "cases_structurally_zero": len(structural_zero),
            "events_by_bucket": {bucket: event_counts.get(bucket, 0) for bucket in BUCKETS},
            "cases_by_bucket": {bucket: case_counts.get(bucket, 0) for bucket in BUCKETS},
            "events_bucket_sum": sum(event_counts.get(bucket, 0) for bucket in BUCKETS),
            "cases_bucket_sum": sum(case_counts.get(bucket, 0) for bucket in BUCKETS),
            "events_bucket_sum_main4": sum(event_counts.get(bucket, 0) for bucket in MAIN_BUCKETS),
            "cases_bucket_sum_main4": sum(case_counts.get(bucket, 0) for bucket in MAIN_BUCKETS),
            "source_kind": {kind: source_kind.get(kind, 0) for kind in ("header", "range_endpoint", "bare_year", "none")},
            "events_year_from_source": sum(
                1 for event in event_rows if event["provenance"]["source_agrees"]
            ),
            "events_year_table_header": sum(
                1 for event in event_rows if event["provenance"]["year_table_header"]
            ),
            "events_source_disagrees": sum(
                1 for event in event_rows if event["provenance"]["source_agrees"] is False
            ),
            "events_with_record_event": sum(
                1 for event in event_rows if event["provenance"]["record_event_present"]
            ),
            "events_record_event_year_differs": sum(
                1 for event in event_rows if event["provenance"]["record_event_year_differs"]
            ),
            "cases_missing_record": missing_records,
            "events_marriage_conflict": len(conflicts),
            "cases_marriage_conflict": len(exclude_any_conflict),
            "events_marriage_conflict_in_window": sum(
                1 for event in in_window_events if event["marriage_conflict"]
            ),
            "cases_marriage_conflict_in_window": len(exclude),
            "events_contradiction_in_window": sum(
                1 for event in in_window_events if event["bucket"] == "contradiction"
            ),
            "cases_contradiction_in_window": len(exclude_literal),
            "header_backed_by_bucket": {
                bucket: sum(
                    1
                    for event in event_rows
                    if event["bucket"] == bucket and event["provenance"]["year_table_header"]
                )
                for bucket in BUCKETS
            },
            "source_kind_by_bucket": {
                bucket: dict(
                    sorted(
                        Counter(
                            event["provenance"]["source_kind"]
                            for event in event_rows
                            if event["bucket"] == bucket
                        ).items()
                    )
                )
                for bucket in BUCKETS
            },
            "text_scope_by_bucket": scope_by_bucket,
        },
        "variant_coverage": variant_coverage,
        "crosscheck_t165": {
            "expected": t165_expected,
            "reproduced": {
                "match": t165.get("match", 0),
                "mismatch": t165.get("mismatch", 0),
                "no_year_in_text": t165.get("no_year_in_text", 0),
            },
            "reproduced_exactly": t165_reproduced,
            "note": "T-165 只认 4 位 19xx/20xx 且只看事件正文；本审计扩展变体、并区分四桶，"
            "两套口径不可直接相减。",
            "mine_vs_t165": {
                "no_year_in_text": event_counts.get("no_year_in_text", 0),
                "contradiction": event_counts.get("contradiction", 0),
                "multi_year": event_counts.get("multi_year", 0),
                "match": event_counts.get("match", 0),
            },
        },
        "sensitivity": {
            "primary_rule": EXCLUDE_RULE,
            "count": len(exclude),
            "sensitivity_exclude": exclude,
            "variants": {
                "in_window_marriage_conflict": len(exclude),
                "any_window_marriage_conflict": len(exclude_any_conflict),
                "in_window_literal_contradiction": len(exclude_literal),
                "in_window_multi_year": len(exclude_multi),
                "in_window_source_year_disagrees": len(exclude_no_source),
            },
            "variant_lists": {
                "any_window_marriage_conflict": exclude_any_conflict,
                "in_window_literal_contradiction": exclude_literal,
                "in_window_multi_year": exclude_multi,
            },
            "not_used": "literal contradiction / multi_year / no_year_in_text 不进主剔除名单："
            "前两类只说明「正文还写了别的年份」，第三类只是正文没写年份（多数原文有年表依据），"
            "按它们剔除会把上下文年份当标签错误。",
        },
        "contradictions": [
            {
                "case_id": event["case_id"],
                "index": event["index"],
                "year": event["year"],
                "age": event["age"],
                "in_window": event["in_window"],
                "years_in_text": event["years_in_text"],
                "ref_kinds": event["ref_kinds"],
                "nearest_delta": _nearest_delta(event["year"], event["years_in_text"]),
                "marriage_years": event["marriage_years"],
                "marriage_conflict": event["marriage_conflict"],
                "source_kind": event["provenance"]["source_kind"],
                "source_year": event["provenance"]["source_year"],
                "text_scope": event["provenance"]["text_scope"],
                "text": _clip(event["text"], 400),
            }
            for event in sorted(contradictions, key=lambda item: (item["case_id"], item["index"]))
        ],
        "marriage_conflicts": [
            {
                "case_id": event["case_id"],
                "index": event["index"],
                "year": event["year"],
                "age": event["age"],
                "in_window": event["in_window"],
                "bucket": event["bucket"],
                "years_in_text": event["years_in_text"],
                "marriage_years": event["marriage_years"],
                "source_kind": event["provenance"]["source_kind"],
                "source_year": event["provenance"]["source_year"],
                "text": _clip(event["text"], 360),
            }
            for event in sorted(conflicts, key=lambda item: (item["case_id"], item["index"]))
        ],
        "multi_year_events": [
            {
                "case_id": event["case_id"],
                "index": event["index"],
                "year": event["year"],
                "age": event["age"],
                "in_window": event["in_window"],
                "years_in_text": event["years_in_text"],
                "ref_kinds": event["ref_kinds"],
                "year_table_header": event["provenance"]["year_table_header"],
                "text": _clip(event["text"], 240),
            }
            for event in sorted(multi_years, key=lambda item: (item["case_id"], item["index"]))
        ],
        "sample_20": _select_sample(case_rows, event_rows, variant_coverage),
        "cases": case_rows,
    }
    return payload


def _nearest_delta(year: int, years: list[int]) -> Optional[int]:
    if not years:
        return None
    return min(abs(year - value) for value in years)


def _clip(text: str, limit: int) -> str:
    body = (text or "").replace("\n", " ")
    return body if len(body) <= limit else body[: limit - 1] + "…"


def _select_sample(
    case_rows: list[dict[str, Any]],
    event_rows: list[dict[str, Any]],
    variant_coverage: dict[str, dict[str, int]],
) -> list[dict[str, Any]]:
    """确定性抽 20 例：先保证变体覆盖，再按桶轮转补足，案例不重复。"""
    by_case = {row["case_id"]: row for row in case_rows}
    events = sorted(event_rows, key=lambda item: (item["case_id"], item["index"]))
    chosen: list[dict[str, Any]] = []
    used: set[str] = set()

    def push(case_id: str, index: int, reason: str) -> None:
        if case_id in used:
            return
        used.add(case_id)
        chosen.append({"case_id": case_id, "index": index, "reason": reason})

    for kind in ("y4", "y2", "y4_range", "y2_range", "cn4"):
        if variant_coverage.get(kind, {}).get("events", 0) <= 0:
            continue
        for event in events:
            if kind in event["ref_kinds"]:
                push(event["case_id"], event["index"], f"variant:{kind}")
                break

    order = ("contradiction", "marriage_conflict", "no_year_in_text", "multi_year", "match")
    pools = {
        bucket: [
            event
            for event in events
            if (event["marriage_conflict"] if bucket == "marriage_conflict" else event["bucket"] == bucket)
            and not (bucket != "marriage_conflict" and event["marriage_conflict"])
        ]
        for bucket in order
    }
    while len(chosen) < 20:
        progressed = False
        for bucket in order:
            if len(chosen) >= 20:
                break
            while pools[bucket]:
                event = pools[bucket].pop(0)
                if event["case_id"] in used:
                    continue
                push(event["case_id"], event["index"], f"bucket:{bucket}")
                progressed = True
                break
        if not progressed:
            break
    if len(chosen) < 20:
        for event in events:
            if len(chosen) >= 20:
                break
            push(event["case_id"], event["index"], "fill")

    rank = {"contradiction": 0, "multi_year": 1, "no_year_in_text": 2, "match": 3, "other": 4}
    chosen.sort(
        key=lambda item: (
            0 if by_case[item["case_id"]]["marriage_conflicts"] else 1,
            rank[by_case[item["case_id"]]["bucket"]],
            item["case_id"],
        )
    )
    by_key = {(event["case_id"], event["index"]): event for event in events}
    enriched: list[dict[str, Any]] = []
    for item in chosen:
        event = by_key[(item["case_id"], item["index"])]
        enriched.append(
            {
                "case_id": item["case_id"],
                "index": item["index"],
                "reason": item["reason"],
                "year": event["year"],
                "age": event["age"],
                "bucket": event["bucket"],
                "years_in_text": event["years_in_text"],
                "marriage_years": event["marriage_years"],
                "marriage_conflict": event["marriage_conflict"],
                "source_kind": event["provenance"]["source_kind"],
                "source_year": event["provenance"]["source_year"],
                "text": _clip(event["text"], 240),
            }
        )
    return enriched


# ── Markdown ────────────────────────────────────────────────────────────────


def _fmt_years(years: list[int]) -> str:
    return "、".join(str(year) for year in years) if years else "—"


def _excerpt(record: Optional[dict[str, Any]], text: str, pad_before: int = 45, pad_after: int = 30) -> str:
    if record is None:
        return "（原始记录缺失）"
    raw = record.get("raw_text") or ""
    pos = _locate(raw, text)
    if pos < 0:
        return "（原文未定位到该段文本）"
    start = max(0, pos - pad_before)
    end = min(len(raw), pos + len(text) + pad_after)
    head = "…" if start > 0 else ""
    tail = "…" if end < len(raw) else ""
    return f"{head}{raw[start:end]}{tail}".replace("\n", " ")


def _bucket_table(title: str, counts: dict[str, int], total: int) -> list[str]:
    lines = [f"### {title}", "", "| 桶 | 计数 | 占比 |", "|---|---:|---:|"]
    for bucket in BUCKETS:
        value = counts.get(bucket, 0)
        lines.append(f"| `{bucket}` | {value} | {value / total:.1%} |")
    lines.append(f"| **合计** | **{sum(counts.values())}** | 100.0% |")
    lines.append("")
    return lines


def _verdict_text(event: dict[str, Any]) -> str:
    bucket = event["bucket"]
    year = event["year"]
    years = event["years_in_text"]
    marriage_years = event["marriage_years"]
    if bucket == "match":
        base = f"正文只出现 {year} 年，与结构化 year 一致。"
    elif bucket == "multi_year":
        base = f"正文含 {year} 年，同时含 {_fmt_years([value for value in years if value != year])}，存在错抽/漏抽风险。"
    elif bucket == "contradiction":
        base = (
            f"正文年份 {_fmt_years(years)} 与结构化 year={year} 相差最小 {_nearest_delta(year, years)} 年。"
        )
    elif bucket == "no_year_in_text":
        base = "正文没有年份表述。"
    else:
        base = "无法分类（year 非整数或文本缺失）。"
    if event["marriage_conflict"]:
        base += f" 正文点名的婚姻年份是 {_fmt_years(marriage_years)}，不含 {year} → 标签年与这段婚姻事实不符。"
    elif marriage_years:
        base += f" 正文点名的婚姻年份 {_fmt_years(marriage_years)}。"
    elif event["provenance"]["year_table_header"]:
        base += f" 原文「年表」表头为 {year} 年，year 有结构依据。"
    return base


def _event_rows_for_md() -> list[dict[str, Any]]:
    """重建事件行（含 provenance / text），供 Markdown 抽样段使用。"""
    timing = _load_json(EVAL_PATH)
    records = load_records(RAW_PATH)
    rows: list[dict[str, Any]] = []
    for case in timing["cases"]:
        if not case.get("usable_for_timing"):
            continue
        record = records.get(case["case_id"])
        for index, event in enumerate(case.get("marriage_events") or []):
            rows.append(_event_row(case, index, event, record))
    return rows


def render_markdown(payload: dict[str, Any], records: dict[str, dict[str, Any]]) -> str:
    counts = payload["counts"]
    events_total = counts["events"]
    event_bucket = counts["events_by_bucket"]
    case_bucket = counts["cases_by_bucket"]
    sensitivity = payload["sensitivity"]
    events_by_key = {(event["case_id"], event["index"]): event for event in _event_rows_for_md()}

    lines: list[str] = []
    add = lines.append
    add("# T-168 · 应期事件年份审计（382 例 / 547 事件，只读）")
    add("")
    add("- 任务卡：`tasks/T-168/PROMPT.md`；模式：只读审计，不评分、不建模、不建盘、不改任何 `year` 或评测集。")
    add("- 输入：`META/timing-eval-set-v1.json`（382 例 `usable_for_timing`）、")
    add("  `cases/raw_feedback/parsed/real_cases_990.jsonl`（回原文）、`META/timing-feasibility-audit-v1.json`（T-165 对账）。")
    add("- 复现：`.venv\\Scripts\\python.exe -m tools.timing_event_year_audit`（退出码 0；两次运行逐字节一致，不写墙钟时间戳）。")
    add("")
    add("## 0. 结论")
    add("")
    add(
        f"1. **四桶可加**：`match` {event_bucket['match']} + `no_year_in_text` {event_bucket['no_year_in_text']} + "
        f"`contradiction` {event_bucket['contradiction']} + `multi_year` {event_bucket['multi_year']} "
        f"+ `other` {event_bucket['other']} = **{counts['events_bucket_sum']} 事件**；"
        f"案例口径 **{counts['cases_bucket_sum']} 例**（`other` {case_bucket['other']}）。"
    )
    add(
        f"2. **year 几乎都从原文年份记号来**：{counts['events_year_from_source']}/{events_total} 条事件的 year "
        f"等于紧贴正文前的年份记号；其中 {counts['events_year_table_header']} 条是「年表」表头，"
        f"{counts['source_kind']['bare_year']} 条是没写「年」的裸年份切点，"
        f"{counts['source_kind']['range_endpoint']} 条是区间端点。"
        "所以「547 条里 425 条文本无年份」是**正文口径**，不等于这些 year 凭空捏造。"
    )
    add(
        f"3. **真问题不是「无年份」而是「正文点了别的婚姻年份」**：{counts['events_marriage_conflict']} 条事件"
        f"（{counts['cases_marriage_conflict']} 例）正文贴着婚姻词的年份不含 `event.year`；"
        f"窗口内有 {counts['events_marriage_conflict_in_window']} 条（**{sensitivity['count']} 例**）。"
        f"按预注册规则剔除这 {sensitivity['count']} 例。"
    )
    add(
        f"4. **可评分案例只有 {counts['cases_with_window_event']} 例**：{counts['cases_structurally_zero']} 例在 20–35 岁窗口内没有任何婚姻事件（结构性零），"
        f"窗口内事件 {counts['events_in_window']} 条。任何应期评测的分母都不是 382。"
    )
    add("")

    add("## 1. 计数与四桶")
    add("")
    add("| 指标 | 数值 |")
    add("|---|---|")
    add(f"| 评测集案例 / 可用案例 | {counts['cases_total_in_eval']} / {counts['cases']} |")
    add(f"| 婚姻事件 / 其中 age 15–50 | {events_total} / {counts['events_age_15_50']} |")
    add(f"| 窗口内（20–35）事件 / 去重 case-year | {counts['events_in_window']} / {counts['unique_window_years']} |")
    add(f"| 窗口内有事件的案例 / 结构性零 | {counts['cases_with_window_event']} / {counts['cases_structurally_zero']} |")
    add(f"| year == 紧前原文年份记号 | {counts['events_year_from_source']}/{events_total} |")
    add(f"| year 来自「年表」表头 | {counts['events_year_table_header']}/{events_total} |")
    add(f"| 紧前年份记号与 year 不一致 | {counts['events_source_disagrees']} |")
    add(f"| 与原始记录 events[] 完全一致 | {counts['events_with_record_event']}/{events_total} |")
    add(f"| 原始记录内同文本但 year 不同 | {counts['events_record_event_year_differs']} |")
    add(f"| 案例在原文里找不到原始记录 | {len(counts['cases_missing_record'])} |")
    add("")
    lines.extend(_bucket_table("事件口径（547）", event_bucket, events_total))
    lines.extend(_bucket_table("案例口径（382，取该例最严重事件）", case_bucket, counts["cases"]))

    add("### 1.1 桶 × 原文依据（正交口径）")
    add("")
    add("| 桶 | 事件数 | 其中「年表」表头 | 正文来源（年表 / 其他信息 / 未定位） |")
    add("|---|---:|---:|---|")
    for bucket in BUCKETS:
        scope = counts["text_scope_by_bucket"][bucket]
        scope_text = " / ".join(f"{key} {value}" for key, value in scope.items()) or "—"
        add(f"| `{bucket}` | {event_bucket[bucket]} | {counts['header_backed_by_bucket'][bucket]} | {scope_text} |")
    add("")
    add("「其他信息」块 = 原文 `其他信息：…` 段落。解析器把年表按年份记号切开，其他信息块里的裸年份")
    add("（如 `2014 生和前期生第一个女儿`）也会被当成事件年，这是 `bare_year` 的来源。")
    add("")

    add("## 2. 文本变体覆盖")
    add("")
    add("| 变体 | 定义 | 命中事件数 | 出现次数 |")
    add("|---|---|---:|---:|")
    variant_desc = {
        "y4": "`2008 年` / `2008`（4 位）",
        "y2": "`08 年`（2 位，排除时长语境）",
        "cn4": "`二〇〇八 年`（中文数字）",
        "y4_range": "`2008-2012 年` / `2013-15 年`",
        "y2_range": "`08-12 年` / `14.15 年` / `20～23 年`",
    }
    for kind in ("y4", "y2", "cn4", "y4_range", "y2_range"):
        coverage = payload["variant_coverage"][kind]
        add(f"| `{kind}` | {variant_desc[kind]} | {coverage['events']} | {coverage['refs']} |")
    add("")
    if payload["variant_coverage"]["cn4"]["events"] == 0:
        add(
            "本语料没有任何中文数字年份（全库唯一 4 字候选是 `0000 年`，已按「必须含一–九」排除），"
            "所以 `cn4` 的覆盖由 `tests/tools/test_timing_event_year_audit.py` 的合成用例证明（`二〇〇八 年 → 2008`）。"
        )
        add("")

    add("## 3. 20 例逐条（可回原文）")
    add("")
    add("每条给出：结构化 `year`、检出年份与变体、原文里的紧前年份记号、原文摘录（同一 `raw_id`）、判定。")
    add("")
    for number, item in enumerate(payload["sample_20"], start=1):
        event = events_by_key[(item["case_id"], item["index"])]
        record = records.get(item["case_id"])
        prov = event["provenance"]
        add(f"### {number}. `{item['case_id']}` · {event['year']} 年（{event['age']} 岁）· `{event['bucket']}`")
        add("")
        add(f"- 抽样理由：`{item['reason']}`")
        add(f"- 检出年份：{_fmt_years(event['years_in_text'])}（变体：{('、'.join(event['ref_kinds']) or '—')}）")
        add(
            f"- 原文依据：紧前年份记号 `{prov['source_year']}`（`{prov['source_kind']}`，与 year 一致={prov['source_agrees']}）"
            f"/ 正文来源 `{prov['text_scope']}`"
        )
        add(f"- 原文摘录：`{_excerpt(record, event['text'])}`")
        add(f"- 判定：{_verdict_text(event)}")
        add("")

    add("## 4. 敏感性剔除名单（脚本算出，非手写）")
    add("")
    add(f"- 预注册规则：{EXCLUDE_RULE}")
    add(f"- 主名单大小：**{sensitivity['count']} 例**")
    add("")
    if sensitivity["sensitivity_exclude"]:
        add("`sensitivity_exclude` =")
        add("")
        add("```text")
        for case_id in sensitivity["sensitivity_exclude"]:
            add(case_id)
        add("```")
        add("")
    add("变体口径（只作敏感性参考，不替代主名单）：")
    add("")
    add("| 口径 | 案例数 |")
    add("|---|---:|")
    for key, value in sensitivity["variants"].items():
        add(f"| `{key}` | {value} |")
    add("")
    add("为什么主名单不直接用 `contradiction` 桶：该桶在正文口径上很宽 —— 正文写 `2015 年生子`、")
    add("`2021 年是不是也破财`、`一直做到 2015 年` 都算，但它并不否定 `event.year`。主名单只在")
    add("「正文点名的**婚姻年份**不含 event.year」时剔除，避免把上下文年份当成标签错误；")
    add("放宽口径的名单在 `variant_lists` 里同时给出。")
    add("")

    add("## 5. 矛盾清单（正文年份 ≠ event.year）")
    add("")
    add(f"共 {len(payload['contradictions'])} 条事件，其中窗口内 "
        f"{counts['events_contradiction_in_window']} 条、"
        f"命中婚姻年份冲突 {sum(1 for item in payload['contradictions'] if item['marriage_conflict'])} 条。")
    add("")
    add("| # | case_id | year | age | 窗口 | 正文年份 | 婚姻年份 | 最近差 | 来源 | 原文（截断） |")
    add("|---:|---|---:|---:|:--:|---|---|---:|---|---|")
    for number, item in enumerate(payload["contradictions"], start=1):
        add(
            f"| {number} | `{item['case_id']}` | {item['year']} | {item['age']} | "
            f"{'✓' if item['in_window'] else ''} | {_fmt_years(item['years_in_text'])} | "
            f"{_fmt_years(item['marriage_years'])} | {item['nearest_delta']} | "
            f"`{item['source_kind']}` | {_clip(item['text'], 80)} |"
        )
    add("")

    add("## 6. 婚姻年份冲突清单（剔除依据）")
    add("")
    add(f"共 {len(payload['marriage_conflicts'])} 条事件，其中窗口内 "
        f"{sum(1 for item in payload['marriage_conflicts'] if item['in_window'])} 条。")
    add("")
    add("| # | case_id | year | age | 窗口 | 四桶 | 正文婚姻年份 | 来源 | 原文（截断） |")
    add("|---:|---|---:|---:|:--:|---|---|---|---|")
    for number, item in enumerate(payload["marriage_conflicts"], start=1):
        add(
            f"| {number} | `{item['case_id']}` | {item['year']} | {item['age']} | "
            f"{'✓' if item['in_window'] else ''} | `{item['bucket']}` | {_fmt_years(item['marriage_years'])} | "
            f"`{item['source_kind']}` | {_clip(item['text'], 80)} |"
        )
    add("")

    add("## 7. 与 T-165 粗查对账")
    add("")
    add("| 口径 | T-165 `label_fidelity` | 本审计复现 |")
    add("|---|---:|---:|")
    for key in ("match", "mismatch", "no_year_in_text"):
        add(f"| `{key}` | {payload['crosscheck_t165']['expected'][key]} | {payload['crosscheck_t165']['reproduced'][key]} |")
    add("")
    add(
        f"逐字节复现 T-165 粗查口径：**{'是' if payload['crosscheck_t165']['reproduced_exactly'] else '否'}**。"
        "T-165 只认 4 位 `19xx/20xx`、只看事件正文，所以 `08 年学的气焊`、`13 年结婚` 会被判成「无年份」，"
        "「正文年份与 year 不同」会被粗算成 74 条；本审计把后者拆成 `contradiction` / `multi_year`，"
        "识别出 `08 年` 这类变体后，`no_year_in_text` 从 425 降到 "
        f"{event_bucket['no_year_in_text']}。"
    )
    add("")

    add("## 8. 风险与不可判")
    add("")
    unsupported = (
        event_bucket["no_year_in_text"] - counts["header_backed_by_bucket"]["no_year_in_text"]
    )
    no_year_kinds = counts["source_kind_by_bucket"]["no_year_in_text"]
    no_year_other = "、".join(
        f"`{kind}` {no_year_kinds.get(kind, 0)}"
        for kind in ("bare_year", "range_endpoint", "none")
        if no_year_kinds.get(kind, 0)
    ) or "无"
    add(
        f"1. **正文无年份仍占多数**：{event_bucket['no_year_in_text']}/{events_total} 条事件正文不写年份；"
        f"其中 {counts['header_backed_by_bucket']['no_year_in_text']} 条原文有「年表」表头，"
        f"其余 {unsupported} 条不是表头（{no_year_other}），需人工看。"
    )
    add(
        f"2. **「其他信息」并入**：{sum(value for bucket in BUCKETS for key, value in counts['text_scope_by_bucket'][bucket].items() if key == 'other_info_block')} "
        "条事件正文来自原文「其他信息」块；这类正文里的裸年份会被解析器切成事件年，是矛盾与多事件年的主要来源。"
    )
    add(
        f"3. **2 位数年份有歧义**：`08 年` / `13 年` 按最接近 `birth_year+30` 还原，"
        "并对 `未来10 年` / `拍拖 12 年的女友` 做了时长语境排除；`18 年后` 这类两可写法仍可能误判，"
        "只带 2 位证据（无 4 位/区间证据）的矛盾有 "
        f"{sum(1 for item in payload['contradictions'] if 'y2' in item['ref_kinds'] and not ({'y4', 'y4_range', 'cn4'} & set(item['ref_kinds'])))} 条。"
    )
    add(
        f"4. **不可判案例**：{counts['cases_structurally_zero']} 例窗口内零事件（应期标签为空，不参与时序评分）；"
        f"{len(counts['cases_missing_record'])} 例在原文里找不到记录（本数据为 0，若不为 0 需先修数据源）。"
    )
    add(
        f"5. **剔除只剔除「正文点名别的婚姻年份」的 {sensitivity['count']} 例**：`multi_year` "
        f"（窗口内 {sensitivity['variants']['in_window_multi_year']} 例）与 "
        "`no_year_in_text` 不进主名单 —— 前者不否定标签年，后者多数有表头依据。"
    )
    add("")
    return "\n".join(lines) + "\n"


# ── 入口 ────────────────────────────────────────────────────────────────────


def main() -> int:
    payload = run_audit()
    records = load_records(RAW_PATH)
    OUT_JSON.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    OUT_MD.write_text(render_markdown(payload, records), encoding="utf-8", newline="\n")

    counts = payload["counts"]
    print(f"[T-168] cases={counts['cases']} events={counts['events']}")
    print(f"[T-168] events_by_bucket={counts['events_by_bucket']} sum={counts['events_bucket_sum']}")
    print(f"[T-168] cases_by_bucket={counts['cases_by_bucket']} sum={counts['cases_bucket_sum']}")
    print(
        f"[T-168] in_window={counts['events_in_window']} structural_zero={counts['cases_structurally_zero']} "
        f"year_from_source={counts['events_year_from_source']}"
    )
    print(
        f"[T-168] marriage_conflict={counts['events_marriage_conflict']} "
        f"cases={counts['cases_marriage_conflict']} in_window_cases={counts['cases_marriage_conflict_in_window']}"
    )
    print(
        f"[T-168] t165_reproduced={payload['crosscheck_t165']['reproduced_exactly']} "
        f"sensitivity_exclude={payload['sensitivity']['count']}"
    )
    print(f"[T-168] wrote {OUT_JSON.relative_to(ROOT)} / {OUT_MD.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

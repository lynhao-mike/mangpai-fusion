"""T-159 · 事业标签可行性审计（只读，不建标签、不评分、不建盘）。

判断 ``occupation`` 事件能否支撑两个标签：

* **角色变化（二值）** → ``DUAN-EVENT-CAREER-ROLE-CHANGE-V1``
* **职业路径三分类（受雇 / 创业 / 混合）** → ``DUAN-EVENT-CAREER-PATH-{EMPLOYMENT,ENTREPRENEURSHIP,MIXED}-V1``

本模块**只做审计与提案**：不写标签文件、不生成逐例标签、不评分、不建盘，也不读取任何
八字/盘面字段（``bazi_raw`` / ``qian_kun`` / ``profile`` 一律不参与判定）。证据只来自
``events[].text``、``events[].domains``、``events[].polarity``、``events[].year``。

产物（确定性，无运行时间戳，重复运行逐字节一致）：

* ``META/career-label-feasibility-v1.json``  计数 / 关键词命中 / 20+20 例编号与原文 / 结论
* ``META/career-label-feasibility-v1.md``    漏斗、四类分布、20 例审计表、建议定义、可判性结论

用法::

    python -m tools.career_label_feasibility

退出码：0 通过；4 数据源不可读；3 计数不变量不复现（数据源变更）；5 冻结人工结论与数据不符（需重审）。

口径（与任务卡 §2 逐条对应）：

* 去重：``duplicate_key`` 全等去重，保留首次出现；案例数 620、事件数 957（任务卡 §1 复现）。
* ``occupation`` 事件 = ``domains`` 含 ``occupation`` 的事件条。
* 提问判定：文本含 ``？``、``?``、``是否``、``能否``、``请问``、``怎么样``、``吗``、``么``、``呢``
  任一 → **整段**不作关键词证据（不还原问句语义，与 T-153 同口径）。
* ``chart_ready`` = ``birth_datetime_raw`` 可解析出日期且含时刻（T-158 §2.1 定义；
  仅用出生字段，不派生任何盘面事实）。
* 关键词表由任务卡 §2.1 / §2.2 原样冻结，禁止增删改；命中与否按字面子串，不做同义扩展。
* 四类互斥：明确受雇 / 明确创业 / 两类都出现 / 两类都没有；四桶之和恒等于 occupation 案例数。
* 「去噪（guarded）」不是标签，只是诊断：三类机械噪声旗标（他人主体 / 意向语 / 子串）
  用来量化误判率；旗标本身也会误伤（见报告 §8），故不据以产出标签。
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from tools.timing_eval_set import parse_clock_datetime

ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = ROOT / "cases" / "raw_feedback" / "parsed" / "real_cases_990.jsonl"
JSON_PATH = ROOT / "META" / "career-label-feasibility-v1.json"
REPORT_PATH = ROOT / "META" / "career-label-feasibility-v1.md"

SCHEMA = "career-label-feasibility/v1"
TASK = "T-159"
SCRIPT = "tools/career_label_feasibility.py"

# 定义冻结日 = 任务卡建卡日（预注册）。不是运行时间戳：本产物必须可逐字节复现。
FROZEN_AT = "2026-10-29"

# 计数不变量（任务卡 §1 中枢探针）。不满足即视为数据源变更，拒绝落盘。
EXPECTED_RECORDS = 992
EXPECTED_UNIQUE = 959
EXPECTED_OCCUPATION_CASES = 620
EXPECTED_OCCUPATION_EVENTS = 957

# 任务卡 §2.1 / §2.2 关键词表，原样冻结，禁止增删。
ROLE_KEYWORDS = (
    "升职", "晋升", "提拔", "跳槽", "换工作", "换岗", "调动", "转行",
    "辞职", "裸辞", "下岗", "失业", "岗位变化", "职责变化", "任职", "入职",
)
EMPLOYMENT_KEYWORDS = (
    "单位", "公司", "上班", "职员", "公务员", "编制", "国企", "外企", "私企", "打工", "任职",
)
ENTREPRENEURSHIP_KEYWORDS = (
    "创业", "生意", "开店", "公司法人", "自由职业", "个体", "经商", "工作室",
)

# 任务卡口径的提问标记，原样冻结（与 T-158 / T-153 一致）。字面子串匹配。
QUESTION_MARKERS = ("？", "?", "是否", "能否", "请问", "怎么样", "吗", "么", "呢")

# 去噪诊断用的人称词表：命主自称 vs 他人。只做「最近前置主体」的启发式判断。
SELF_SUBJECTS = ("我", "自己", "本人")
OTHER_SUBJECTS = (
    "父亲", "母亲", "爸爸", "妈妈", "父母", "老公", "丈夫", "媳妇", "妻子", "老婆",
    "祖辈", "爷爷", "奶奶", "外公", "外婆", "哥哥", "姐姐", "弟弟", "妹妹",
    "儿子", "女儿", "朋友", "亲戚", "同事", "领导", "室友", "员工", "合伙人",
    "家里", "家中",
)
# 未发生 / 意向语：关键词前 8 字内出现即视为「不是既成事实」。
ASPIRATION_MARKERS = ("应聘", "考公", "国考", "省考", "选调", "面试", "希望", "打算", "准备", "想", "有机会")
# 关键词之后的「希望/机会」（「晋升希望」「提拔机会」）同样是意向，不是既成事实。
POST_ASPIRATION_MARKERS = ("希望", "机会")
# 子串误判：(更长的词, 被误命中的关键词)。只列人工确认过的形态。
SUBSTRING_GUARDS = (
    ("当上班长", "上班"),
    ("工作室内", "工作室"),
    ("创业公司", "创业"),
)

SUBJECT_WINDOW = 20
ASPIRATION_WINDOW = 8
POST_ASPIRATION_WINDOW = 4
TEXT_SUMMARY_LIMIT = 60

BUCKET_ORDER = ("employment", "entrepreneurship", "mixed", "neither")
BUCKET_LABELS = {
    "employment": "明确受雇",
    "entrepreneurship": "明确创业",
    "mixed": "两类都出现",
    "neither": "两类都没有",
}

# 事业话语词（仅用于衡量「0 侧」的沉默强度，不参与标签判定）。
CAREER_DISCOURSE = ("工作", "事业", "职业", "就业", "岗位", "职位", "老板", "同事")

# 20 例角色变化人工抽查：(case_id, 冻结命中词集合, 人工结论)。
# 结论来自逐例回 JSONL 读原文（raw_id + line_start 可复查）。命中词与当前数据不符即拒绝重写。
AUDIT_ROLE_CHANGE: tuple[tuple[str, tuple[str, ...], str], ...] = (
    ("RF-2026-000126", ("升职", "转行"), "成立：本人「08-12 年极顺利升职加薪，14 年转行业房地产」；事件 year=2022 而正文跨 2007–2022，年份字段不可信"),
    ("RF-2026-000139", ("晋升",), "成立：「工作晋升，收入可以」；同案 2023「被动掉工作」也是角色变化"),
    ("RF-2026-000053", ("提拔",), "成立：「进入世界 500 百强,被提拔」"),
    ("RF-2026-000093", ("失业", "跳槽"), "成立：「2012 年跳槽后工作不顺利失业 1 年」"),
    ("RF-2026-000066", ("换工作",), "不成立：主体是配偶（「媳妇换工作花了 6 万」）→ 他人主体误判"),
    ("RF-2026-000475", ("换岗",), "成立：「我被迫升岗级，换岗位」明确本人（原文是「升岗级」，不含「升职」）"),
    ("RF-2026-000073", ("调动",), "成立：「调岗 调动工作 做公司的教育培训管理工作」"),
    ("RF-2026-000537", ("转行",), "成立：「转行至 IT 软件行业」"),
    ("RF-2026-000108", ("辞职",), "成立：「同一年辞职了」，另有「有钱了辞职回家写书」；多次进出职场"),
    ("RF-2026-000001", ("裸辞",), "成立：「裸辞了…自由职业方面开始写网文」"),
    ("RF-2026-000162", ("下岗",), "案例成立但命中位置错：关键词落在「父母下岗工人」；本人另有「原公司倒闭…重新就业」→ 词对语境错"),
    ("RF-2026-000041", ("失业",), "成立：「彻底不工作了…在家里失业躺平」（本人）"),
    ("RF-2026-000729", ("任职",), "成立：「这个月再小公司任职小经理」（本人；含原文错字「再」）"),
    ("RF-2026-000173", ("入职",), "成立：「2022 年八月离职，2023 年 3 月新入职一家公司到 6 月离职」"),
    ("RF-2026-000178", ("升职", "调动"), "成立：「工作调动，升职」"),
    ("RF-2026-000236", ("晋升",), "不成立：两处为「有晋升希望」「有机会晋升」，意向非事实 → 意向语误判"),
    ("RF-2026-000302", ("提拔",), "成立：「被提拔升職加薪」（繁体「職」；公务员）"),
    ("RF-2026-000118", ("跳槽",), "成立：「跳槽到央企华润集团」"),
    ("RF-2026-000154", ("换工作",), "成立：「经常换工作」（概括性陈述，非单次事件）"),
    ("RF-2026-000243", ("调动",), "不成立：「因父亲工作调动…来杭州读书」是父亲 → 他人主体误判"),
)

# 20 例路径三分类人工抽查：(case_id, 冻结桶, 人工结论)。
AUDIT_PATH_TYPE: tuple[tuple[str, str, str], ...] = (
    ("RF-2026-000028", "employment", "成立：「进入了一间美资保险公司的财务部门」"),
    ("RF-2026-000029", "employment", "成立：与 000028 正文几乎相同（近重复样本，去重未剔除）"),
    ("RF-2026-000034", "employment", "成立：「在计算机行业一直工作到现在」+ 公司降薪"),
    ("RF-2026-000045", "employment", "成立：公司欠薪、全员工打官司、离职失业"),
    ("RF-2026-000056", "employment", "不成立：「应聘国企本来要成功被关系户顶上」「考公落榜」→ 求职未成，受雇未发生"),
    ("RF-2026-000097", "entrepreneurship", "勉强成立：「之后 3 年自由职业」是自雇，但无经营实体，不属受雇亦非典型创业"),
    ("RF-2026-000212", "entrepreneurship", "不成立：「祖辈经商」是祖辈 → 他人主体误判"),
    ("RF-2026-000220", "entrepreneurship", "不成立：「工作室内设计师」子串误判（工作室 ≠ 室内设计）"),
    ("RF-2026-000319", "entrepreneurship", "不成立：「家里做点小生意」是家里；同案「找到合适工作」是受雇（漏检）→ 双向误判"),
    ("RF-2026-000327", "entrepreneurship", "不成立：「父母个体户」是父母 → 他人主体误判"),
    ("RF-2026-000001", "mixed", "成立（先后型）：「外企底层工作」+ 2023 裸辞后「自由职业写网文」→ 先受雇后自雇，非同时"),
    ("RF-2026-000026", "mixed", "不成立：「帮一位领导创业」非本人创业；「小单位」「评估公司工作」是受雇"),
    ("RF-2026-000101", "mixed", "成立（同时型）：「在工作之余做了一个小生意失败」明确同时"),
    ("RF-2026-000162", "mixed", "部分成立：「创业公司倒闭…奋斗五年」创始人身份存疑；家人「父母下岗工人，老婆公务员」；本人「地方私企小主管」"),
    ("RF-2026-000255", "mixed", "不成立：「当上班长」子串 + 「专业工作室」是学校工作室 → 两处误判"),
    ("RF-2026-000002", "neither", "不可判：该案 occupation 事件全部为提问，无可用文本"),
    ("RF-2026-000004", "neither", "不可判：该案 occupation 事件全部为提问，无可用文本"),
    ("RF-2026-000005", "neither", "不可判：唯一事件是考试/「帮我看一下事业运和姻缘运」，无路径信息"),
    ("RF-2026-000008", "neither", "不可判：该案 occupation 事件全部为提问，无可用文本"),
    ("RF-2026-000010", "neither", "不可判：该案 occupation 事件全部为提问，无可用文本"),
)

# 已知误判类型（人工从 20+20 例归纳；本版不就地改判，只记录）。
KNOWN_ISSUES: tuple[tuple[str, str, str], ...] = (
    ("他人主体", "关键词指向父母/配偶/子女/祖辈/同事，非命主",
     "角色变化 3/20（000066、000243，及 000162 的命中位置）；路径 4/20（000212、000319、000327、000162）"),
    ("意向语", "「有晋升希望」「应聘国企」「考公」被当作既成事实",
     "角色变化 1/20（000236）；路径 1/20（000056）"),
    ("子串", "「当上班长」含「上班」、「工作室内设计师」含「工作室」",
     "路径 2/20（000255、000220）"),
    ("语义越界", "「创业公司」可能是受雇于此；「自由职业」不属受雇也不属典型经营",
     "路径 3/20（000162、000097、000212）"),
    ("时间不可信", "事件 year 与正文年份不一致（000126 year=2022，正文 2007–2022）",
     "角色变化 1/20（000126）；影响「何时变化」，不影响「是否变化」"),
    ("近重复", "去重键不同但正文几乎相同（000028 / 000029）",
     "20 例里 1 对；按空白归一化文本哈希可再识别 19 组 40 条"),
)


class SourceError(RuntimeError):
    """数据源不可读。"""


class FunnelInvariantError(RuntimeError):
    """计数不变量不复现（数据源变更）。"""


class AuditStaleError(RuntimeError):
    """冻结的人工抽查结论与当前数据不符。"""


# ---------------------------------------------------------------------------
# 文本判定
# ---------------------------------------------------------------------------


def question_markers_in(text: str) -> tuple[str, ...]:
    """返回命中的提问标记（按冻结顺序，可多选）。"""
    return tuple(marker for marker in QUESTION_MARKERS if marker in text)


def is_question(text: str) -> bool:
    """整段是否按卡片口径判为提问（提问段一律不作证据）。"""
    return bool(question_markers_in(text))


def keyword_hits(text: str, keywords: tuple[str, ...]) -> list[str]:
    """返回命中的关键词（按冻结顺序，可多选）。"""
    return [keyword for keyword in keywords if keyword in text]


def keyword_positions(text: str, keyword: str) -> list[int]:
    """返回关键词在文本中的全部出现位置（子串，起点递增）。"""
    positions: list[int] = []
    start = 0
    while True:
        index = text.find(keyword, start)
        if index < 0:
            return positions
        positions.append(index)
        start = index + 1


def nearest_subject(text: str, position: int, window: int = SUBJECT_WINDOW) -> str | None:
    """返回关键词前 ``window`` 字内最近出现的人称词（无则 None）。"""
    head = text[max(0, position - window):position]
    best: str | None = None
    best_index = -1
    for token in SELF_SUBJECTS + OTHER_SUBJECTS:
        index = head.rfind(token)
        if index > best_index:
            best_index = index
            best = token
    return best


def occurrence_tags(text: str, position: int, keyword: str) -> tuple[str, ...]:
    """返回一次关键词命中的机械噪声旗标（他人主体 / 意向语 / 子串）。"""
    tags: list[str] = []
    subject = nearest_subject(text, position)
    if subject in OTHER_SUBJECTS:
        tags.append("other_subject")
    head = text[max(0, position - ASPIRATION_WINDOW):position]
    tail = text[position + len(keyword): position + len(keyword) + POST_ASPIRATION_WINDOW]
    if any(marker in head for marker in ASPIRATION_MARKERS) or any(
        marker in tail for marker in POST_ASPIRATION_MARKERS
    ):
        tags.append("aspiration")
    for longer, inner in SUBSTRING_GUARDS:
        if inner != keyword:
            continue
        index = text.find(longer)
        if 0 <= index <= position < index + len(longer):
            tags.append("substring")
            break
    return tuple(tags)


def summarise_text(text: str, limit: int = TEXT_SUMMARY_LIMIT) -> str:
    """压缩空白并截断到固定长度，供审计表展示（确定性）。"""
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 1] + "…"


def snippet_around(text: str, token: str, limit: int = TEXT_SUMMARY_LIMIT) -> str:
    """以命中词为中心截取固定长度片段，保证审计表能看到被命中的上下文。"""
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    index = compact.find(token) if token else -1
    if index < 0:
        return summarise_text(compact, limit)
    start = max(0, min(index - (limit - len(token)) // 2, len(compact) - limit))
    head = "…" if start > 0 else ""
    tail = "…" if start + limit < len(compact) else ""
    return head + compact[start : start + limit] + tail


def _cell(value: Any) -> str:
    """Markdown 表格单元转义：管道符与换行。"""
    return str(value).replace("|", "\\|").replace("\n", " ")


def _table(header: list[str], body: list[list[Any]]) -> list[str]:
    lines = ["| " + " | ".join(_cell(item) for item in header) + " |"]
    lines.append("|" + "|".join("---" for _ in header) + "|")
    for row in body:
        lines.append("| " + " | ".join(_cell(item) for item in row) + " |")
    return lines


def _share_pct(part: int, total: int) -> float:
    return round(100.0 * part / total, 2) if total else 0.0


def bucket_of(employment: bool, entrepreneurship: bool) -> str:
    """四类互斥分桶。"""
    if employment and entrepreneurship:
        return "mixed"
    if employment:
        return "employment"
    if entrepreneurship:
        return "entrepreneurship"
    return "neither"


# ---------------------------------------------------------------------------
# 读源与去重
# ---------------------------------------------------------------------------


def load_records(path: Path = SOURCE_PATH) -> list[dict[str, Any]]:
    """按文件行序读取 JSONL（保留原始顺序，去重依赖首次出现）。"""
    if not path.exists():
        raise SourceError(f"数据源不存在：{path}")
    records: list[dict[str, Any]] = []
    try:
        with path.open(encoding="utf-8") as handle:
            for line_no, line in enumerate(handle, start=1):
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
    group_counts: dict[str, int] = {}
    for record in records:
        key = str(record.get("duplicate_key") or "")
        group_counts[key] = group_counts.get(key, 0) + 1
        if key in seen:
            duplicates += 1
            continue
        seen.add(key)
        unique.append(record)
    repeated = sum(1 for count in group_counts.values() if count > 1)
    return unique, {"groups": repeated, "extra_records": duplicates}


def occupation_events(record: dict[str, Any]) -> list[dict[str, Any]]:
    """返回 ``domains`` 含 ``occupation`` 的事件条（保持 JSON 顺序）。"""
    events = record.get("events") or []
    return [event for event in events if "occupation" in (event.get("domains") or [])]


def event_polarity(event: dict[str, Any]) -> str:
    value = event.get("polarity")
    return value if value in ("positive", "negative", "unknown") else "unknown"


# ---------------------------------------------------------------------------
# 逐例分析
# ---------------------------------------------------------------------------


def scan_keywords(events: list[dict[str, Any]], keywords: tuple[str, ...]) -> list[dict[str, Any]]:
    """扫描非提问事件的冻结关键词，返回每次命中（含噪声旗标）。"""
    occurrences: list[dict[str, Any]] = []
    for event_index, event in enumerate(events):
        text = event.get("text") or ""
        if is_question(text):
            continue
        for keyword in keywords:
            for position in keyword_positions(text, keyword):
                occurrences.append(
                    {
                        "keyword": keyword,
                        "event_index": event_index,
                        "year": event.get("year"),
                        "polarity": event_polarity(event),
                        "tags": list(occurrence_tags(text, position, keyword)),
                        "text": text,
                    }
                )
    return occurrences


def _keywords(occurrences: list[dict[str, Any]], clean: bool) -> list[str]:
    selected = {item["keyword"] for item in occurrences if not clean or not item["tags"]}
    return sorted(selected)


def analyse_case(record: dict[str, Any]) -> dict[str, Any]:
    """单例审计中间结果（不写盘，不含任何盘面字段）。"""
    events = occupation_events(record)
    usable = [event for event in events if not is_question(event.get("text") or "")]
    role_occ = scan_keywords(events, ROLE_KEYWORDS)
    emp_occ = scan_keywords(events, EMPLOYMENT_KEYWORDS)
    ent_occ = scan_keywords(events, ENTREPRENEURSHIP_KEYWORDS)

    role_raw = _keywords(role_occ, clean=False)
    role_clean = _keywords(role_occ, clean=True)
    emp_raw = _keywords(emp_occ, clean=False)
    emp_clean = _keywords(emp_occ, clean=True)
    ent_raw = _keywords(ent_occ, clean=False)
    ent_clean = _keywords(ent_occ, clean=True)

    birth = parse_clock_datetime(record.get("birth_datetime_raw"))
    gender = (record.get("gender") or "").strip()

    evidence_events = [
        {
            "event_index": index,
            "year": event.get("year"),
            "polarity": event_polarity(event),
            "text": event.get("text") or "",
        }
        for index, event in enumerate(events)
        if not is_question(event.get("text") or "")
    ]
    role_evidence = [
        {
            "event_index": item["event_index"],
            "year": item["year"],
            "polarity": item["polarity"],
            "keyword": item["keyword"],
            "tags": item["tags"],
            "text": item["text"],
        }
        for item in role_occ
    ]
    role_evidence.sort(key=lambda item: (item["event_index"], item["keyword"]))

    return {
        "case_id": record.get("raw_id"),
        "line_start": record.get("line_start"),
        "line_end": record.get("line_end"),
        "gender": gender,
        "birth_datetime_raw": record.get("birth_datetime_raw"),
        "birth_date_ok": bool(birth["ok"]),
        "chart_ready": bool(birth["ok"] and birth["has_time"]),
        "occupation_events": len(events),
        "usable_events": len(usable),
        "role": {
            "occurrences": role_occ,
            "raw": role_raw,
            "clean": role_clean,
            "hit": bool(role_raw),
            "clean_hit": bool(role_clean),
            "evidence": role_evidence,
        },
        "path": {
            "occurrences": {"employment": emp_occ, "entrepreneurship": ent_occ},
            "employment_raw": emp_raw,
            "employment_clean": emp_clean,
            "entrepreneurship_raw": ent_raw,
            "entrepreneurship_clean": ent_clean,
            "bucket_raw": bucket_of(bool(emp_raw), bool(ent_raw)),
            "bucket_clean": bucket_of(bool(emp_clean), bool(ent_clean)),
        },
        "evidence_events": evidence_events,
        "profile_occupation_present": bool((record.get("profile") or {}).get("occupation")),
    }


# ---------------------------------------------------------------------------
# 抽样
# ---------------------------------------------------------------------------


def select_role_sample(cases: list[dict[str, Any]], size: int = 20) -> list[dict[str, Any]]:
    """角色变化 20 例：按关键词表轮转取样，保证每个有命中的关键词至少覆盖一次。"""
    hits = [case for case in cases if case["role"]["hit"]]
    hits.sort(key=lambda case: str(case["case_id"]))
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
                if keyword in case["role"]["raw"]:
                    selected.append(case)
                    used.add(case["case_id"])
                    progressed = True
                    break
        if not progressed:
            break
    return selected


def select_path_sample(cases: list[dict[str, Any]], per_bucket: int = 5) -> list[dict[str, Any]]:
    """路径 20 例：四桶各 5 例，桶内按 case_id 升序取前 N（确定性）。"""
    selected: list[dict[str, Any]] = []
    for bucket in BUCKET_ORDER:
        members = [case for case in cases if case["path"]["bucket_raw"] == bucket]
        members.sort(key=lambda case: str(case["case_id"]))
        selected.extend(members[:per_bucket])
    return selected


def _role_row(case: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "index": index,
        "case_id": case["case_id"],
        "line_start": case["line_start"],
        "line_end": case["line_end"],
        "chart_ready": case["chart_ready"],
        "matched_keywords": case["role"]["raw"],
        "clean_keywords": case["role"]["clean"],
        "occupation_events": case["occupation_events"],
        "evidence": case["role"]["evidence"],
    }


def _path_row(case: dict[str, Any], index: int) -> dict[str, Any]:
    matched: dict[int, dict[str, Any]] = {}
    for dimension in ("employment", "entrepreneurship"):
        for item in case["path"]["occurrences"][dimension]:
            entry = matched.setdefault(
                item["event_index"],
                {
                    "event_index": item["event_index"],
                    "year": item["year"],
                    "polarity": item["polarity"],
                    "text": item["text"],
                    "keywords": [],
                },
            )
            if item["keyword"] not in entry["keywords"]:
                entry["keywords"].append(item["keyword"])
    matched_evidence = [matched[key] for key in sorted(matched)]
    for entry in matched_evidence:
        entry["keywords"] = sorted(entry["keywords"])
    return {
        "index": index,
        "case_id": case["case_id"],
        "line_start": case["line_start"],
        "line_end": case["line_end"],
        "chart_ready": case["chart_ready"],
        "bucket_raw": case["path"]["bucket_raw"],
        "bucket_clean": case["path"]["bucket_clean"],
        "employment_keywords": case["path"]["employment_raw"],
        "entrepreneurship_keywords": case["path"]["entrepreneurship_raw"],
        "occupation_events": case["occupation_events"],
        "usable_events": case["usable_events"],
        "matched_evidence": matched_evidence,
        "evidence": case["evidence_events"],
    }


# ---------------------------------------------------------------------------
# 统计
# ---------------------------------------------------------------------------


def _bucket_counts(cases: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts = {bucket: 0 for bucket in BUCKET_ORDER}
    for case in cases:
        counts[case["path"][key]] += 1
    counts["sum"] = sum(counts[bucket] for bucket in BUCKET_ORDER)
    return counts


def _chart_ready_buckets(cases: list[dict[str, Any]], key: str) -> dict[str, int]:
    ready = [case for case in cases if case["chart_ready"]]
    return _bucket_counts(ready, key)


def _polarity_breakdown(events: list[dict[str, Any]]) -> dict[str, int]:
    counts = {"positive": 0, "negative": 0, "unknown": 0}
    for event in events:
        counts[event_polarity(event)] += 1
    return counts


def _event_count_distribution(cases: list[dict[str, Any]], field: str) -> dict[str, int]:
    distribution: dict[str, int] = {}
    for case in cases:
        key = str(case[field])
        distribution[key] = distribution.get(key, 0) + 1
    return dict(sorted(distribution.items(), key=lambda item: int(item[0])))


def near_duplicate_texts(unique: list[dict[str, Any]]) -> dict[str, Any]:
    """去重后仍存在的同文事件（按空白归一化后的文本哈希），用于泄漏预警。"""
    seen: dict[str, dict[str, Any]] = {}
    for record in unique:
        for event in occupation_events(record):
            text = "".join((event.get("text") or "").split())
            if not text:
                continue
            digest = hashlib.sha1(text.encode("utf-8")).hexdigest()
            entry = seen.setdefault(digest, {"events": 0, "cases": []})
            entry["events"] += 1
            case_id = record.get("raw_id")
            if case_id not in entry["cases"]:
                entry["cases"].append(case_id)
    duplicated = [entry for entry in seen.values() if entry["events"] > 1]
    cross_case = [entry for entry in duplicated if len(entry["cases"]) > 1]
    examples = sorted(cross_case, key=lambda item: (-item["events"], sorted(item["cases"])))[:3]
    return {
        "groups": len(duplicated),
        "events": sum(entry["events"] for entry in duplicated),
        "cross_case_groups": len(cross_case),
        "cross_case_events": sum(entry["events"] for entry in cross_case),
        "examples": [
            {"events": entry["events"], "cases": sorted(entry["cases"])} for entry in examples
        ],
    }


def build_payload(
    records: list[dict[str, Any]], source_sha: str
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    unique, dedupe_stats = dedupe_records(records)
    cases = [analyse_case(record) for record in unique if occupation_events(record)]
    cases.sort(key=lambda case: str(case["case_id"]))

    all_events = [event for record in unique for event in occupation_events(record)]
    usable_events = [event for event in all_events if not is_question(event.get("text") or "")]

    role_cases = [case for case in cases if case["role"]["hit"]]
    role_clean_cases = [case for case in cases if case["role"]["clean_hit"]]

    role_keyword_cases: dict[str, int] = {keyword: 0 for keyword in ROLE_KEYWORDS}
    role_keyword_events: dict[str, int] = {keyword: 0 for keyword in ROLE_KEYWORDS}
    role_flag_occurrences: dict[str, int] = {}
    role_flag_cases: dict[str, set[str]] = {}
    role_hit_events: dict[tuple[str, int], dict[str, Any]] = {}
    for case in cases:
        for keyword in case["role"]["raw"]:
            role_keyword_cases[keyword] += 1
        seen_pairs: set[tuple[int, str]] = set()
        for item in case["role"]["evidence"]:
            pair = (item["event_index"], item["keyword"])
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)
            role_keyword_events[item["keyword"]] += 1
            role_hit_events[(str(case["case_id"]), item["event_index"])] = {
                "year": item["year"],
                "polarity": item["polarity"],
                "text": item["text"],
            }
            for tag in item["tags"]:
                role_flag_occurrences[tag] = role_flag_occurrences.get(tag, 0) + 1
                role_flag_cases.setdefault(tag, set()).add(str(case["case_id"]))

    path_flag_occurrences: dict[str, int] = {}
    path_flag_cases: dict[str, set[str]] = {}
    for dimension in ("employment", "entrepreneurship"):
        for case in cases:
            for item in case["path"]["occurrences"][dimension]:
                for tag in item["tags"]:
                    bucket_key = f"{dimension}:{tag}"
                    path_flag_occurrences[bucket_key] = path_flag_occurrences.get(bucket_key, 0) + 1
                    path_flag_cases.setdefault(bucket_key, set()).add(str(case["case_id"]))

    path_raw = _bucket_counts(cases, "bucket_raw")
    path_clean = _bucket_counts(cases, "bucket_clean")
    neither_members = [case for case in cases if case["path"]["bucket_raw"] == "neither"]
    neither_no_text = sum(1 for case in neither_members if case["usable_events"] == 0)

    role_non_hit = [case for case in cases if not case["role"]["hit"]]
    discourse = 0
    for case in role_non_hit:
        if any(
            keyword_hits(event["text"], EMPLOYMENT_KEYWORDS + ENTREPRENEURSHIP_KEYWORDS + CAREER_DISCOURSE)
            for event in case["evidence_events"]
        ):
            discourse += 1

    events_per_case = _event_count_distribution(cases, "occupation_events")
    single_event_share = _share_pct(events_per_case.get("1", 0), len(cases))

    role_sample = select_role_sample(cases)
    path_sample = select_path_sample(cases)

    payload: dict[str, Any] = {
        "schema": SCHEMA,
        "task": TASK,
        "script": SCRIPT,
        "frozen_at": FROZEN_AT,
        "audit": {
            "read_only": True,
            "labels_written": False,
            "scores_written": False,
            "charts_built": False,
            "bazi_fields_used": False,
            "role_change_selection": "角色变化命中案例按关键词表轮转取样，每个有命中的词至少覆盖一次，至多 20 例",
            "path_type_selection": "四桶各 5 例，桶内按 case_id 升序取前 5",
            "role_change": [_role_row(case, index) for index, case in enumerate(role_sample, start=1)],
            "path_type": [_path_row(case, index) for index, case in enumerate(path_sample, start=1)],
            "role_change_findings": [
                {"case_id": case_id, "keywords": list(keywords), "verdict": verdict}
                for case_id, keywords, verdict in AUDIT_ROLE_CHANGE
            ],
            "path_type_findings": [
                {"case_id": case_id, "bucket": bucket, "verdict": verdict}
                for case_id, bucket, verdict in AUDIT_PATH_TYPE
            ],
        },
        "source": {
            "path": SOURCE_PATH.relative_to(ROOT).as_posix(),
            "sha256": source_sha,
            "records": len(records),
        },
        "dedupe": {
            "key": "duplicate_key",
            "unique": len(unique),
            "duplicate_groups": dedupe_stats["groups"],
            "extra_records": dedupe_stats["extra_records"],
        },
        "funnel": {
            "records": len(records),
            "unique": len(unique),
            "occupation_cases": len(cases),
            "occupation_events": len(all_events),
            "question_events": len(all_events) - len(usable_events),
            "usable_events": len(usable_events),
            "cases_without_usable_event": sum(1 for case in cases if case["usable_events"] == 0),
            "gender_ok_cases": sum(1 for case in cases if case["gender"] in ("男", "女")),
            "birth_date_ok_cases": sum(1 for case in cases if case["birth_date_ok"]),
            "chart_ready_cases": sum(1 for case in cases if case["chart_ready"]),
            "chart_ready_basis": "birth_datetime_raw 可解析且含时刻（T-158 §2.1，不派生盘面事实）",
        },
        "question_policy": {
            "markers": list(QUESTION_MARKERS),
            "scope": "同案其余事件独立判定",
        },
        "keywords": {
            "role_change": list(ROLE_KEYWORDS),
            "employment": list(EMPLOYMENT_KEYWORDS),
            "entrepreneurship": list(ENTREPRENEURSHIP_KEYWORDS),
        },
        "role_change": {
            "raw": {
                "cases": len(role_cases),
                "share_pct": _share_pct(len(role_cases), len(cases)),
                "chart_ready_cases": sum(1 for case in role_cases if case["chart_ready"]),
                "events": len(role_hit_events),
                "by_polarity": _polarity_breakdown(list(role_hit_events.values())),
                "keyword_cases": role_keyword_cases,
                "keyword_events": role_keyword_events,
            },
            "guarded": {
                "cases": len(role_clean_cases),
                "share_pct": _share_pct(len(role_clean_cases), len(cases)),
                "chart_ready_cases": sum(1 for case in role_clean_cases if case["chart_ready"]),
                "dropped_cases": len(role_cases) - len(role_clean_cases),
                "flag_occurrences": dict(sorted(role_flag_occurrences.items())),
                "flag_cases": {tag: len(ids) for tag, ids in sorted(role_flag_cases.items())},
            },
            "negative_side": {
                "non_hit_cases": len(role_non_hit),
                "non_hit_with_career_discourse": discourse,
                "non_hit_without_discourse": len(role_non_hit) - discourse,
            },
            "coverage": {
                "cases": len(cases),
                "events_per_case": events_per_case,
                "usable_events_per_case": _event_count_distribution(cases, "usable_events"),
            },
        },
        "path_types": {
            "buckets": {bucket: BUCKET_LABELS[bucket] for bucket in BUCKET_ORDER},
            "raw": {
                **path_raw,
                "share_pct": {
                    bucket: _share_pct(path_raw[bucket], len(cases)) for bucket in BUCKET_ORDER
                },
            },
            "raw_chart_ready": _chart_ready_buckets(cases, "bucket_raw"),
            "guarded": {
                **path_clean,
                "share_pct": {
                    bucket: _share_pct(path_clean[bucket], len(cases)) for bucket in BUCKET_ORDER
                },
            },
            "guarded_chart_ready": _chart_ready_buckets(cases, "bucket_clean"),
            "neither_breakdown": {
                "cases": len(neither_members),
                "all_events_are_questions": neither_no_text,
                "text_but_no_path_keyword": len(neither_members) - neither_no_text,
            },
            "flag_occurrences": dict(sorted(path_flag_occurrences.items())),
            "flag_cases": {tag: len(ids) for tag, ids in sorted(path_flag_cases.items())},
        },
        "noise_model": {
            "description": "机械去噪诊断，不是标签：命中带任一旗标即不计入 guarded 计数",
            "other_subject_window": SUBJECT_WINDOW,
            "aspiration_window": ASPIRATION_WINDOW,
            "other_subjects": list(OTHER_SUBJECTS),
            "self_subjects": list(SELF_SUBJECTS),
            "aspiration_markers": list(ASPIRATION_MARKERS),
            "post_aspiration_markers": list(POST_ASPIRATION_MARKERS),
            "post_aspiration_window": POST_ASPIRATION_WINDOW,
            "substring_guards": [list(pair) for pair in SUBSTRING_GUARDS],
            "over_flag_examples": [
                "RF-2026-000041「在家里失业躺平」→「家里」触发 other_subject，属误伤",
                "RF-2026-000154「经常换工作」无前置主语 → 不触发，结论正确",
            ],
        },
        "near_duplicate_texts": near_duplicate_texts(unique),
        "side_resources": {
            "profile_occupation_cases": sum(1 for case in cases if case["profile_occupation_present"]),
            "cases_without_usable_event_but_profile": sum(
                1 for case in cases if case["profile_occupation_present"] and case["usable_events"] == 0
            ),
            "used": False,
        },
        "known_issues": [
            {"type": kind, "phenomenon": what, "evidence": where} for kind, what, where in KNOWN_ISSUES
        ],
        "conclusion": {
            "role_change": {
                "verdict": "勉强可判",
                "usable_part": (
                    f"存在性（1 侧）：{len(role_cases)} 例命中，20 例抽查 17 例成立（85%）"
                ),
                "unusable_part": (
                    f"0 侧：{len(role_non_hit)} 例非命中里 {discourse} 例只提工作不提变化、"
                    f"{len(role_non_hit) - discourse} 例无事业话语；"
                    f"{single_event_share:.1f}% 案例仅 1 条 occupation 事件"
                ),
                "recommendation": "只建 1 vs null 的存在性标签；不建 0/1 全样本二值",
            },
            "path_type_3class": {
                "verdict": "不可判",
                "reasons": [
                    f"去噪后 {path_clean['neither']}/{len(cases)}"
                    f"（{_share_pct(path_clean['neither'], len(cases)):.1f}%）无任何路径关键词，只能给 null",
                    "20 例抽查：受雇 4/5、创业 1/5、混合 2/5、两类都没有 0/5",
                    f"「创业」去噪后仅 {path_clean['entrepreneurship']} 例且含「自由职业」10 例，"
                    "不属受雇亦非典型经营",
                    f"「混合」去噪后仅 {path_clean['mixed']} 例；「同时副业」与「先后转行」在文本上无法区分",
                    f"规则 falsifier 要求「主要职业路径」，但 {single_event_share:.1f}% 案例只有 1 条事件，"
                    "无法支撑「主要」",
                ],
                "fallback": (
                    f"降级为「是否受雇」二分类（{path_clean['employment']}–{path_raw['employment']} 例，"
                    "需人工消歧）可勉强使用；创业/混合不建"
                ),
            },
            "scope": "本报告不给逐例标签；审计表只覆盖 40 例，供中枢复核抽样质量",
        },
    }
    payload["payload_sha256"] = _payload_sha256(payload)
    return payload, cases


# ---------------------------------------------------------------------------
# 校验与落盘
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


def check_invariants(payload: dict[str, Any]) -> None:
    """任务卡 §5 的计数可加性 + §1 的冻结数字。"""
    funnel = payload["funnel"]
    if funnel["records"] != EXPECTED_RECORDS:
        raise FunnelInvariantError(f"records {funnel['records']} != {EXPECTED_RECORDS}")
    if funnel["unique"] != EXPECTED_UNIQUE:
        raise FunnelInvariantError(f"unique {funnel['unique']} != {EXPECTED_UNIQUE}")
    if funnel["occupation_cases"] != EXPECTED_OCCUPATION_CASES:
        raise FunnelInvariantError(
            f"occupation_cases {funnel['occupation_cases']} != {EXPECTED_OCCUPATION_CASES}"
        )
    if funnel["occupation_events"] != EXPECTED_OCCUPATION_EVENTS:
        raise FunnelInvariantError(
            f"occupation_events {funnel['occupation_events']} != {EXPECTED_OCCUPATION_EVENTS}"
        )
    raw = payload["path_types"]["raw"]
    if raw["sum"] != funnel["occupation_cases"]:
        raise FunnelInvariantError(f"四桶之和 {raw['sum']} != occupation 案例数 {funnel['occupation_cases']}")
    guarded = payload["path_types"]["guarded"]
    if guarded["sum"] != funnel["occupation_cases"]:
        raise FunnelInvariantError(
            f"guarded 四桶之和 {guarded['sum']} != occupation 案例数 {funnel['occupation_cases']}"
        )
    ready = payload["path_types"]["raw_chart_ready"]
    if ready["sum"] != funnel["chart_ready_cases"]:
        raise FunnelInvariantError(
            f"chart_ready 四桶之和 {ready['sum']} != chart_ready_cases {funnel['chart_ready_cases']}"
        )
    usable = funnel["usable_events"]
    if usable + funnel["question_events"] != funnel["occupation_events"]:
        raise FunnelInvariantError("usable_events + question_events != occupation_events")


def render_report(payload: dict[str, Any]) -> str:
    """渲染人读报告（纯函数，只依赖 payload，确定性）。"""
    funnel = payload["funnel"]
    role_raw = payload["role_change"]["raw"]
    role_guarded = payload["role_change"]["guarded"]
    negative = payload["role_change"]["negative_side"]
    coverage = payload["role_change"]["coverage"]
    path = payload["path_types"]
    raw = path["raw"]
    ready = path["raw_chart_ready"]
    guarded = path["guarded"]
    neither = path["neither_breakdown"]
    conclusion = payload["conclusion"]
    cases_total = funnel["occupation_cases"]

    lines: list[str] = []
    add = lines.append
    add("# 事业标签可行性审计 v1（T-159）")
    add("")
    add("> **只读审计**：不建标签、不评分、不建盘、不读取任何八字/盘面字段。")
    add(
        f"> 数据源 `{payload['source']['path']}`（sha256 `{payload['source']['sha256']}`，"
        f"{funnel['records']} 条）。"
    )
    add("")
    add("## 0. 结论（先给裁决）")
    add("")
    lines.extend(
        _table(
            ["标签", "结论", "依据"],
            [
                [
                    "角色变化（二值）",
                    f"**{conclusion['role_change']['verdict']}**",
                    conclusion["role_change"]["usable_part"],
                ],
                [
                    "职业路径三分类",
                    f"**{conclusion['path_type_3class']['verdict']}**",
                    conclusion["path_type_3class"]["reasons"][0],
                ],
            ],
        )
    )
    add("")
    add("**角色变化（风险）**：" + conclusion["role_change"]["unusable_part"])
    add("")
    add("**职业路径三分类**：" + "；".join(conclusion["path_type_3class"]["reasons"]) + "。")
    add("")
    add("**降级方案**：" + conclusion["path_type_3class"]["fallback"] + "。")
    add("")

    add("## 1. 数据与漏斗")
    add("")
    lines.extend(
        _table(
            ["层级", "数量", "说明"],
            [
                ["原始记录", funnel["records"], "JSONL 有效行"],
                ["按 duplicate_key 去重", funnel["unique"], f"重复组 {payload['dedupe']['duplicate_groups']}，多余 {payload['dedupe']['extra_records']} 条"],
                ["有 occupation 事件的案例", funnel["occupation_cases"], "任务卡 §1 的 620 例，与本轮复现一致"],
                ["occupation 事件条", funnel["occupation_events"], "任务卡 §1 的 957 条，与本轮复现一致"],
                ["其中整段判为提问", funnel["question_events"], f"{_share_pct(funnel['question_events'], funnel['occupation_events']):.2f}% 事件不作证据"],
                ["可用证据事件", funnel["usable_events"], "非提问事件"],
                ["无任何可用事件的案例", funnel["cases_without_usable_event"], "全部事件都是提问 → 该案无文本证据"],
                ["性别可判（男/女）", funnel["gender_ok_cases"], "独立口径，不叠加"],
                ["出生日期可解析", funnel["birth_date_ok_cases"], "独立口径，不叠加"],
                ["chart_ready（日期+时刻）", funnel["chart_ready_cases"], funnel["chart_ready_basis"]],
            ],
        )
    )
    add("")

    add("## 2. 提问排除规则与代价")
    add("")
    add(
        "标记："
        + "、".join(f"`{marker}`" for marker in payload["question_policy"]["markers"])
        + f" 任一出现 → 整段不作证据（{payload['question_policy']['scope']}）。"
    )
    add("")
    add(
        f"代价：{funnel['question_events']} 条事件被整段排除，其中一部分同段夹着真证据"
        "（如 `RF-2026-000002`：「2018 年事业顺利，找到了一份好工作」与「问题：什么时候能发财？」同段，"
        "整段一票否决后该案没有任何可用事件）。按卡片口径保留此保守规则，不做段内切分。"
    )
    add("")

    add("## 3. 角色变化（二值）计数")
    add("")
    lines.extend(
        _table(
            ["口径", "命中案例", "占比", "chart_ready 内", "命中事件"],
            [
                ["原始关键词（卡片词表）", role_raw["cases"], f"{role_raw['share_pct']:.2f}%", role_raw["chart_ready_cases"], role_raw["events"]],
                ["去噪诊断（机械旗标）", role_guarded["cases"], f"{role_guarded['share_pct']:.2f}%", role_guarded["chart_ready_cases"], "—"],
            ],
        )
    )
    add("")
    add(
        "命中事件 polarity："
        f"negative {role_raw['by_polarity']['negative']} / "
        f"positive {role_raw['by_polarity']['positive']} / "
        f"unknown {role_raw['by_polarity']['unknown']}。"
        "极性是事件整体色彩，不代表角色变化本身的好坏。"
    )
    add("")
    add("按关键词（案例数 / 命中事件数）：")
    add("")
    lines.extend(
        _table(
            ["关键词", "案例", "事件"],
            [
                [keyword, role_raw["keyword_cases"][keyword], role_raw["keyword_events"][keyword]]
                for keyword in payload["keywords"]["role_change"]
            ],
        )
    )
    add("")
    add(
        f"去噪旗标：他人主体 {role_guarded['flag_occurrences'].get('other_subject', 0)} 次 / "
        f"{role_guarded['flag_cases'].get('other_subject', 0)} 例，"
        f"意向语 {role_guarded['flag_occurrences'].get('aspiration', 0)} 次 / "
        f"{role_guarded['flag_cases'].get('aspiration', 0)} 例；"
        f"两旗标合计去掉 {role_guarded['dropped_cases']} 例。"
    )
    add("")
    add("**0 侧强度**（决定能否给 0）：")
    add("")
    lines.extend(
        _table(
            ["分层", "案例数", "含义"],
            [
                ["非命中合计", negative["non_hit_cases"], "没有命中任何角色变化词"],
                ["其中：提了工作但没提变化", negative["non_hit_with_career_discourse"], "有事业话语（工作/事业/单位/公司…）却无变化词"],
                ["其中：完全没有事业话语", negative["non_hit_without_discourse"], "文本与该案职业无关"],
            ],
        )
    )
    add("")
    add(
        "覆盖度："
        f"{coverage['events_per_case'].get('1', 0)}/{coverage['cases']} 例只有 1 条 occupation 事件"
        f"（可用事件为 1 条的 {coverage['usable_events_per_case'].get('1', 0)} 例）。"
        "单条片段无法证明「一生没有角色变化」→ **0 侧不可当作阴性证据**。"
    )
    add("")

    add("## 4. 角色变化 20 例审计")
    add("")
    add("抽样：命中案例按关键词表轮转，每个有命中的词至少覆盖一次（`岗位变化`/`职责变化` 全库 0 命中）。")
    add("")
    audit_rows: list[list[Any]] = []
    findings = {item["case_id"]: item["verdict"] for item in payload["audit"]["role_change_findings"]}
    for row in payload["audit"]["role_change"]:
        evidence = row["evidence"][0] if row["evidence"] else {}
        keyword = row["evidence"][0]["keyword"] if row["evidence"] else ""
        audit_rows.append(
            [
                row["index"],
                f"`{row['case_id']}`",
                f"{row['line_start']}",
                "、".join(row["matched_keywords"]),
                f"{evidence.get('year')} / {evidence.get('polarity')}",
                snippet_around(evidence.get("text", ""), keyword),
                findings.get(row["case_id"], ""),
            ]
        )
    lines.extend(
        _table(
            ["#", "case_id", "JSONL 行", "命中词", "年份/极性", "证据摘要（全文见 JSON）", "人工结论"],
            audit_rows,
        )
    )
    add("")
    add(
        "统计：**17/20 成立**，3/20 不成立（他人主体 2、意向语 1）；另有 1 例关键词落在家人身上但同案确有本人变化"
        "（`RF-2026-000162`）。机械旗标能抓住这 3 例，但也会误伤真阳性（`RF-2026-000041`「在家里失业躺平」）。"
    )
    add("")

    add("## 5. 职业路径三分类：四类分布")
    add("")
    bucket_rows: list[list[Any]] = []
    for bucket in BUCKET_ORDER:
        bucket_rows.append(
            [
                BUCKET_LABELS[bucket],
                f"`{bucket}`",
                raw[bucket],
                f"{raw['share_pct'][bucket]:.2f}%",
                ready[bucket],
                guarded[bucket],
                f"{guarded['share_pct'][bucket]:.2f}%",
            ]
        )
    bucket_rows.append(["**合计**", "—", f"**{raw['sum']}**", "100.00%", ready["sum"], guarded["sum"], "100.00%"])
    lines.extend(
        _table(
            ["类别", "代码", "原始计数", "占比", "chart_ready 内", "去噪后", "去噪占比"],
            bucket_rows,
        )
    )
    add("")
    add(
        f"`两类都没有` 拆解：**{neither['all_events_are_questions']} 例**全部事件都是提问（无文本可判），"
        f"**{neither['text_but_no_path_keyword']} 例**有可用文本但没有任何路径关键词。"
        "也就是说「两类都没有」绝大多数是**没有信息**，不是「确认既非受雇也非创业」。"
    )
    add("")
    add(
        "去噪旗标（次 / 案例）："
        + "；".join(
            f"{tag} {count} 次 / {path['flag_cases'].get(tag, 0)} 例"
            for tag, count in path["flag_occurrences"].items()
        )
        + "。"
    )
    add("")

    add("## 6. 职业路径 20 例审计")
    add("")
    add("抽样：四桶各 5 例，桶内按 `case_id` 升序取前 5。")
    add("")
    path_findings = {item["case_id"]: item["verdict"] for item in payload["audit"]["path_type_findings"]}
    path_rows: list[list[Any]] = []
    for row in payload["audit"]["path_type"]:
        matched = row.get("matched_evidence") or []
        primary = matched[0] if matched else (row["evidence"][0] if row["evidence"] else {})
        keyword = matched[0]["keywords"][0] if matched and matched[0]["keywords"] else ""
        keywords = row["employment_keywords"] + row["entrepreneurship_keywords"]
        path_rows.append(
            [
                row["index"],
                f"`{row['case_id']}`",
                f"{row['line_start']}",
                BUCKET_LABELS[row["bucket_raw"]],
                "、".join(keywords) if keywords else "（无）",
                f"{primary.get('year')} / {primary.get('polarity')}",
                snippet_around(primary.get("text", ""), keyword) if primary else "（无可用事件）",
                path_findings.get(row["case_id"], ""),
            ]
        )
    lines.extend(
        _table(
            ["#", "case_id", "JSONL 行", "自动桶", "命中词", "年份/极性", "证据摘要（全文见 JSON）", "人工结论"],
            path_rows,
        )
    )
    add("")
    add(
        "统计：受雇 **4/5** 成立、创业 **1/5** 成立、两类都出现 **2/5** 成立（1 例为「先后」而非「同时」）、"
        "两类都没有 **0/5** 可判。"
    )
    add("")

    add("## 7. 已知误判类型")
    add("")
    lines.extend(
        _table(
            ["类型", "现象", "证据"],
            [[item["type"], item["phenomenon"], item["evidence"]] for item in payload["known_issues"]],
        )
    )
    add("")
    add(
        f"另有近重复泄漏：按空白归一化文本哈希，去重后仍有 **{payload['near_duplicate_texts']['groups']} 组 "
        f"{payload['near_duplicate_texts']['events']} 条** occupation 事件正文完全相同，"
        f"其中**跨案例 {payload['near_duplicate_texts']['cross_case_groups']} 组 "
        f"{payload['near_duplicate_texts']['cross_case_events']} 条**会直接造成评测泄漏"
        "（例：" + "、".join(
            " / ".join(item["cases"]) for item in payload["near_duplicate_texts"]["examples"][:2]
        ) + "）。建任何标签前必须先按文本哈希再剔重。"
    )
    add("")

    add("## 8. 建议定义（提案，不落标签）")
    add("")
    add("### 8.1 角色变化：只建 1 侧存在性")
    add("")
    add("- 取值：`1` = 有既成的角色变化证据；`null` = 文本不作证。**不建 0**。")
    add(
        "- 判定：任一 occupation 事件非提问 + 命中角色词 + 主体为命主（最近前置主体不是父母/配偶/子女/同事）"
        "+ 非意向语（「希望/打算/应聘/考公/有机会」不算）。"
    )
    add(f"- 抽样 {role_raw['cases']} 例人工过一遍再冻结；机械旗标只做初筛，勿直接当标签。")
    add("")
    add("### 8.2 职业路径：不建互斥三分类")
    add("")
    single_share = _share_pct(coverage["events_per_case"].get("1", 0), coverage["cases"])
    add(f"- 「主要职业路径」在单条片段上不可判（{single_share:.1f}% 案例只有 1 条事件，事件年份还与正文不符）。")
    add(
        f"- 只可试建「是否受雇」二分类（{raw['employment']} 例原始 / {guarded['employment']} 例去噪），"
        "且需人工消歧。"
    )
    add("- 「混合」必须要求**同时**表述（如「在工作之余做了一个小生意」）；「先后转行」不算 mixed。")
    add("- 「自由职业」是第三态，不塞进受雇或创业；若要保留，需另立类别并由中枢决定。")
    add("")
    add("### 8.3 通用前置条件")
    add("")
    add(
        f"- 先按文本哈希剔重（{payload['near_duplicate_texts']['groups']} 组 "
        f"{payload['near_duplicate_texts']['events']} 条），再谈样本量。"
    )
    add("- 事件 `year` 不可信（000126：year=2022，正文 2007–2022）→ 只做「是否」，不做「何时」。")
    add(
        f"- `profile.occupation` 是自由文本自述（620 例中 {payload['side_resources']['profile_occupation_cases']} 例有），"
        f"本版**未使用**；其中 {payload['side_resources']['cases_without_usable_event_but_profile']} 例"
        "可补「无可用事件」的语境，但不能当事件证据。"
    )
    add("")

    add("## 9. 边界、不变量与复现")
    add("")
    add("```bash")
    add(".venv\\Scripts\\python.exe -m tools.career_label_feasibility")
    add("```")
    add("")
    add(
        f"- 不变量：{raw['sum']} = {raw['employment']}+{raw['entrepreneurship']}+{raw['mixed']}+{raw['neither']}"
        f"（occupation 案例数 {cases_total}）；去噪后四桶之和 {guarded['sum']} 亦为 {cases_total}；"
        f"chart_ready 内 {ready['sum']} = {funnel['chart_ready_cases']}。"
    )
    add(f"- JSON `payload_sha256`：`{payload['payload_sha256']}`")
    add("- 不写标签文件、不评分、不建盘、不读 `bazi_raw` / `qian_kun` / 盘面事实。")
    add("- 无运行时间戳；两次运行 JSON 与本文逐字节一致。")
    add("")
    add("> 本报告只给可行性与建议定义，**不给逐例标签**。审计表覆盖 40 例，全量判定需中枢另行决定。")
    add("")
    return "\n".join(lines)


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

    try:
        records = load_records()
        payload, _cases = build_payload(records, _sha256_file(SOURCE_PATH))
        check_invariants(payload)
        check_audit_samples(payload)
    except SourceError as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        return 4
    except FunnelInvariantError as exc:
        print(f"[FAIL] 计数不变量不复现（数据源变更？）：{exc}", file=sys.stderr)
        return 3
    except AuditStaleError as exc:
        print(f"[FAIL] 冻结人工结论与数据不符，需重审：{exc}", file=sys.stderr)
        return 5

    JSON_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    REPORT_PATH.write_text(render_report(payload), encoding="utf-8")

    funnel = payload["funnel"]
    role_raw = payload["role_change"]["raw"]
    raw = payload["path_types"]["raw"]
    guarded = payload["path_types"]["guarded"]
    print("T-159 career-label-feasibility v1（只读审计）")
    print(
        f"  source   : {payload['source']['path']} sha256={payload['source']['sha256'][:12]}… "
        f"records={funnel['records']} unique={funnel['unique']}"
    )
    print(
        f"  occupation: cases={funnel['occupation_cases']} events={funnel['occupation_events']} "
        f"question={funnel['question_events']} usable={funnel['usable_events']} "
        f"no_event_cases={funnel['cases_without_usable_event']} chart_ready={funnel['chart_ready_cases']}"
    )
    print(
        f"  role     : cases={role_raw['cases']} ({role_raw['share_pct']:.2f}%) events={role_raw['events']} "
        f"chart_ready={role_raw['chart_ready_cases']} guarded={payload['role_change']['guarded']['cases']}"
    )
    print(
        f"  path     : employment={raw['employment']} entrepreneurship={raw['entrepreneurship']} "
        f"mixed={raw['mixed']} neither={raw['neither']} sum={raw['sum']}"
    )
    print(
        f"  path(guarded): employment={guarded['employment']} entrepreneurship={guarded['entrepreneurship']} "
        f"mixed={guarded['mixed']} neither={guarded['neither']} sum={guarded['sum']}"
    )
    print(
        f"  verdict  : role_change={payload['conclusion']['role_change']['verdict']} "
        f"path_type_3class={payload['conclusion']['path_type_3class']['verdict']}"
    )
    print(f"  wrote    : META/career-label-feasibility-v1.json sha256={_sha256_file(JSON_PATH)[:12]}…")
    print("           : META/career-label-feasibility-v1.md")
    return 0


def check_audit_samples(payload: dict[str, Any]) -> None:
    """冻结的 20+20 例人工结论必须与当前抽样和自动命中一致，否则拒绝重写。"""
    role_rows = {row["case_id"]: row for row in payload["audit"]["role_change"]}
    path_rows = {row["case_id"]: row for row in payload["audit"]["path_type"]}
    if len(role_rows) != 20:
        raise AuditStaleError(f"角色变化抽样 {len(role_rows)} 例，应为 20")
    if len(path_rows) != 20:
        raise AuditStaleError(f"路径抽样 {len(path_rows)} 例，应为 20")
    for case_id, keywords, _verdict in AUDIT_ROLE_CHANGE:
        row = role_rows.get(case_id)
        if row is None:
            raise AuditStaleError(f"{case_id} 不在当前角色变化抽样内")
        if tuple(row["matched_keywords"]) != tuple(sorted(keywords)):
            raise AuditStaleError(
                f"{case_id} 命中词变为 {row['matched_keywords']}，冻结值 {sorted(keywords)}"
            )
    for case_id, bucket, _verdict in AUDIT_PATH_TYPE:
        row = path_rows.get(case_id)
        if row is None:
            raise AuditStaleError(f"{case_id} 不在当前路径抽样内")
        if row["bucket_raw"] != bucket:
            raise AuditStaleError(f"{case_id} 桶变为 {row['bucket_raw']}，冻结值 {bucket}")
    for dimension, findings in (("role", AUDIT_ROLE_CHANGE), ("path", AUDIT_PATH_TYPE)):
        verdicts = [item[2] for item in findings]
        if any(not verdict for verdict in verdicts):
            raise AuditStaleError(f"{dimension} 抽查存在空结论")


if __name__ == "__main__":
    raise SystemExit(main())


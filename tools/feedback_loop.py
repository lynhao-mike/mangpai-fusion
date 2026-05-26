"""tools/feedback_loop.py · v1.2 Track-G 自迭代主循环

落地契约：
    engine/contracts/05-rule-lifecycle.md § 七（feedback_loop 主循环伪代码）
    engine/contracts/05-rule-lifecycle.md § 八（iteration-log 格式）
    engine/contracts/00-OVERVIEW.md § 三（自迭代闭环）

职责：
    `ingest_feedback(case_id) -> IterationDiff`
        ① 解析 cases/C-XXX/{feedback.md, analysis.md}
        ② 抽出每条 conclusion 的 verdict（hit / miss / abstain / no_data）
        ③ 顺 trace_id（evidence_chain）找规律 → 更新 hits/misses + recent_5
        ④ Beta 重算 confidence_cache
        ⑤ 跑升降级 + 漂移检测
        ⑥ save_rule()
        ⑦ 写 META/iteration-log.md
        ⑧ 落 META/calibration/{date}-after-{case_id}.snapshot.yaml
        ⑨ case_count % 10 == 0 → 触发 cross_school_scan

注意现有案例的现实状况：
    - cases/C-XXX/analysis.md 是 v1.0 自由 Markdown，没有结构化的 conclusion_id
      / evidence_chain trace_id（v1.2 之后才规范化）。
    - 但 feedback.md 中明确写了"应验/失验"标签 + 派别引用（M2-Y-068 等）。
    - 所以本期 ingest_feedback 采用"启发式抽取"：
        · 从 analysis.md 找 "M[1-3]-[DYRG]-\d+" / "G-[A-Z]+-\d+"  形式的规律 ID
        · 从 feedback.md 表格行抽出对应断语 + 应验状态
        · "完全失验" / "失验" / "❌" → miss
        · "应验" / "✅" / "铁应验" → hit
        · "部分" / "🟡" → abstain（不计入 hits/misses，但记 abstained++）
        · "存疑" / "❓" / "未提供" → no_data（跳过）
    - 当 v1.2 下游 Track-F 把 analysis_output.json 落盘后（含 trace_id 链），
      ingest_feedback 会优先消费结构化 JSON，启发式逻辑作为 fallback。

作者：Track-G
"""
from __future__ import annotations

import datetime as _dt
import json
import pathlib
import re
from dataclasses import dataclass, field
from typing import Any, Literal, Optional

import yaml

from tools.drift_detect import detect_drift
from tools.rule_lifecycle import (
    AppliedCase,
    LifecycleConfig,
    Rule,
    RuleStatus,
    RuleNotFoundError,
    apply_status_change,
    load_rule,
    maybe_downgrade,
    maybe_upgrade,
    save_rule,
)

# ============================================================
# 一、路径常量
# ============================================================

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
CASES_DIR = REPO_ROOT / "cases"
META_DIR = REPO_ROOT / "META"
ITERATION_LOG = META_DIR / "iteration-log.md"
CALIBRATION_DIR = META_DIR / "calibration"


# ============================================================
# 二、解析器：feedback.md / analysis.md
# ============================================================

Verdict = Literal["hit", "miss", "abstain", "no_data"]

# 规律 ID 正则：
#   - 段派 M1-D-001
#   - 杨派 M2-Y-068
#   - 任派 M3-R-031
#   - 高派 G-XX-005 / G-BD-词馆 / G-* 等
RULE_ID_RE = re.compile(
    r"\b(?:M[123]-[DYRY]-\d+|G(?:-[A-Z\u4e00-\u9fff]+){1,3}-?\d*)\b"
)

# 更宽松的二级正则：含中文章节的高派形式 G-BD-词馆
RULE_ID_RE_RELAX = re.compile(
    r"\b(?:M[123]-[A-Z]-\d+|G-[A-Z]+(?:-[\u4e00-\u9fff\w]+)?)"
)


@dataclass
class FeedbackRow:
    """从 feedback.md 表格里解析出的一条断语反馈。"""
    statement: str          # "学历：本科以上 / 211/985"
    schools: list[str]      # ["杨", "高", "段"]
    confidence_str: str     # "★★★★ (84%)"
    verdict: Verdict
    detail: str             # "本科 ✅，但非 211/985 ❌"
    raw_line: str           # 原始行
    domain: Optional[str] = None      # "婚姻" / "学历" / "财运" 等
    yingqi_year: Optional[int] = None # 应期年份（若可推断）


@dataclass
class AnalysisConclusion:
    """从 analysis.md 启发式抽出的一条结论。"""
    section: str             # 所在章节，如 "COMP-2 婚姻波折"
    statement: str           # "婚姻波折显著, 大概率离异或长期不婚 / 晚婚"
    schools: list[str]       # 派别签名
    rule_ids: list[str]      # 抽到的规律 ID（trace_id 替身）
    domain: Optional[str] = None
    yingqi_year: Optional[int] = None


# ----------------------------------------------------------------
# 启发式：根据语义标记判定 verdict
# ----------------------------------------------------------------

# v1.3 D5+ 历史回补扩展（2026-05-25）：
#   - HIT 增加 "铁断"（C-012 用 ✅✅✅ 铁断）、"铁证"（C-008 用"罕见史诗级铁证"）
#   - MISS 增加 "完全证伪"（C-008 用"完全证伪"代替"完全失验"）
#   - ABSTAIN 增加 "◐"（C-007 用半圆表示部分命中）、"⚠️"（C-007/C-011 用作"需修正/偏保守"中性标记）
#   - NODATA 增加 "未知"（C-013"⏳ 未知"）、"待补"（C-009"待补具体应期"）
# 仅在能稳定提升 fanout 命中且不引入误判时纳入。
_HIT_MARKERS = ("✅", "应验", "铁应验", "命中", "铁断", "铁证")
_MISS_MARKERS = ("❌", "失验", "完全失验", "完全证伪", "miss")
_ABSTAIN_MARKERS = ("🟡", "部分应验", "部分", "🟠", "◐", "⚠️")
_NODATA_MARKERS = (
    "❓", "存疑", "未提供", "未明确", "未知", "待补", "待回测", "待验",
    "⏳", "进行中", "待时间触发",
)


def _classify_verdict(text: str) -> Verdict:
    """根据反馈文字判定应验情况。优先级：miss > hit > abstain > no_data。

    注意：含"完全失验"必为 miss，即使同时含"✅"片段（部分细节对了但总体失验）。
    """
    if any(m in text for m in ("完全失验", "❌ 完全失验", "彻底失验")):
        return "miss"
    has_hit = any(m in text for m in _HIT_MARKERS)
    has_miss = any(m in text for m in _MISS_MARKERS)
    has_abstain = any(m in text for m in _ABSTAIN_MARKERS)
    has_nodata = any(m in text for m in _NODATA_MARKERS)
    # 优先级
    if has_miss and not has_hit:
        return "miss"
    if has_hit and not has_miss:
        return "hit"
    if has_miss and has_hit:
        # 既有应验又有失验 = 部分
        return "abstain"
    if has_abstain:
        return "abstain"
    if has_nodata:
        return "no_data"
    return "no_data"


# ----------------------------------------------------------------
# 派别名抽取
# ----------------------------------------------------------------

_SCHOOL_TOKENS = ("段", "杨", "高", "任")


def _extract_schools(text: str) -> list[str]:
    """从 "杨+高+任" / "[杨派独门]" / "段派" 等表达里抽出派别。"""
    # 1) 显式 "X+Y+Z"
    out: list[str] = []
    for ch in _SCHOOL_TOKENS:
        if ch in text:
            out.append(ch)
    # 去重保序
    seen: set[str] = set()
    res: list[str] = []
    for s in out:
        if s not in seen:
            seen.add(s)
            res.append(s)
    return res


# ----------------------------------------------------------------
# domain 抽取
# ----------------------------------------------------------------

_DOMAIN_KEYWORDS: list[tuple[str, str]] = [
    ("婚姻", "婚姻"), ("婚期", "婚姻"), ("妻", "婚姻"), ("配偶", "婚姻"),
    ("夫宫", "婚姻"), ("克妻", "婚姻"), ("妻宫", "婚姻"),
    ("学历", "学业"), ("高考", "学业"), ("学业", "学业"),
    ("财运", "财运"), ("财富", "财运"), ("收入", "财运"),
    ("健康", "健康"), ("疾病", "健康"), ("外伤", "健康"),
    ("职业", "事业"), ("升迁", "事业"), ("事业", "事业"), ("公门", "事业"),
    ("六亲", "六亲"), ("母亲", "六亲"), ("父亲", "六亲"),
]


def _extract_domain(text: str) -> Optional[str]:
    for kw, domain in _DOMAIN_KEYWORDS:
        if kw in text:
            return domain
    return None


# ----------------------------------------------------------------
# 表格行解析（feedback.md "二、已过应期回测" + "三、定性结论回测"）
# ----------------------------------------------------------------

def parse_feedback_md(path: pathlib.Path) -> list[FeedbackRow]:
    """解析 feedback.md 中所有"应验/失验"标记的表格行。

    本函数只扫表格行（| ... |），其它段落不处理。
    """
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    out: list[FeedbackRow] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line.startswith("|") or not line.endswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        # v1.3 D5+ 历史回补扩展（2026-05-25）：放宽到 >=3 列，覆盖 C-008/C-009/C-010 极简
        # `| # | 事实 | 派别命中 |` 三列表格。verdict 标记仍是必要条件（见下面 any() 判断），
        # 故无 verdict 标记的普通"事实表"不会被误纳入。
        if len(cells) < 3:
            continue
        # 跳过表头 + 分隔行
        if all(re.fullmatch(r"-+:?|:?-+", c.replace(" ", "")) for c in cells):
            continue
        if "应验/失验" in line or "应验状态" in line or cells[0].startswith("---"):
            continue
        joined = " ".join(cells)
        # 仅当行内含 verdict 标记才纳入
        if not any(
            m in joined
            for m in (
                *_HIT_MARKERS,
                *_MISS_MARKERS,
                *_ABSTAIN_MARKERS,
                *_NODATA_MARKERS,
            )
        ):
            continue
        verdict = _classify_verdict(joined)
        # 选择"断语"列：通常是第 2 或第 4 列（应期回测 vs 定性回测两种格式）
        statement = ""
        for c in cells:
            if any(kw in c for kw in (
                "婚", "财", "学", "健", "事", "职", "公门", "母", "父", "印动",
                "高考", "拐点", "大运", "应期", "晚景"
            )):
                statement = c
                break
        if not statement:
            statement = cells[0]
        confidence_str = ""
        for c in cells:
            if "★" in c or "%)" in c:
                confidence_str = c
                break
        schools = _extract_schools(joined)
        domain = _extract_domain(joined) or _extract_domain(statement)
        # 应期年份（表格首列若为 4 位数字）
        yingqi_year: Optional[int] = None
        m_year = re.search(r"\b(19|20)\d{2}\b", cells[0])
        if m_year:
            try:
                yingqi_year = int(m_year.group())
            except ValueError:
                pass
        # detail = 倒数 1-2 列（"实际情况"或"详情"）
        detail = " | ".join(cells[-2:])
        out.append(FeedbackRow(
            statement=statement,
            schools=schools,
            confidence_str=confidence_str,
            verdict=verdict,
            detail=detail,
            raw_line=line,
            domain=domain,
            yingqi_year=yingqi_year,
        ))
    return out


def parse_analysis_md(path: pathlib.Path) -> list[AnalysisConclusion]:
    """启发式：扫 analysis.md 把每条带规律 ID 的"结论行"作为一条 conclusion。

    具体策略：以 markdown heading（### / ####）划段，每段中找：
      - 含 "★N (X%)" 的行（断语）
      - 该段内出现的所有规律 ID
      - 段标题作为 statement 提示
      - 派别 token + domain
    """
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    sections: list[tuple[str, list[str]]] = []  # (title, lines)
    cur_title = "(prelude)"
    cur_lines: list[str] = []
    for raw in text.splitlines():
        if raw.startswith("### ") or raw.startswith("#### "):
            if cur_lines:
                sections.append((cur_title, cur_lines))
            cur_title = raw.lstrip("# ").strip()
            cur_lines = []
        else:
            cur_lines.append(raw)
    if cur_lines:
        sections.append((cur_title, cur_lines))

    conclusions: list[AnalysisConclusion] = []
    for title, lines in sections:
        body = "\n".join(lines)
        rule_ids = list(set(RULE_ID_RE.findall(body)))
        if not rule_ids:
            # 二级宽松正则
            rule_ids = list(set(RULE_ID_RE_RELAX.findall(body)))
        if not rule_ids:
            continue
        # 取首个含 ★ 的行作为 statement（fallback 用 title）
        statement = title
        for ln in lines:
            if "★" in ln:
                # 去 markdown 加粗
                stmt = re.sub(r"\*+", "", ln).strip()
                if stmt and stmt != title:
                    statement = stmt
                    break
        schools = _extract_schools(title) or _extract_schools(body)
        domain = _extract_domain(title) or _extract_domain(body)
        conclusions.append(AnalysisConclusion(
            section=title,
            statement=statement,
            schools=schools,
            rule_ids=rule_ids,
            domain=domain,
        ))
    return conclusions


# ============================================================
# 三、verdict 匹配（conclusion ↔ feedback）
# ============================================================

def match_verdict_for_rule(
    rule_id: str,
    conclusion: AnalysisConclusion,
    feedback_rows: list[FeedbackRow],
) -> tuple[Verdict, str]:
    """v1.3 D5+ 历史回补：单 rule_id 精确匹配优先。

    对单条 (conclusion, rule_id) 做匹配，避免 conclusion 级一次性合并多个 rule_id
    导致的 verdict 串扰（C-2026-014 学业段 = 3 个 rule_id 各自命中不同 verdict）。

    优先级：
      0. raw_line 显式含 ``rule_id`` → 直接取该行 verdict（多行时 miss>hit>abstain>no_data）
      1. 回退到 conclusion 级 :func:`match_verdict`

    Returns
    -------
    tuple[Verdict, str]
        (verdict, source) — source ∈ {"rule_id_exact", "domain_fallback"}
    """
    # Step 0: rule_id 在 raw_line 中精确出现
    exact = [r for r in feedback_rows if rule_id in r.raw_line]
    if exact:
        priority = {"miss": 0, "hit": 1, "abstain": 2, "no_data": 3}
        exact.sort(key=lambda r: priority[r.verdict])
        return exact[0].verdict, "rule_id_exact"
    return match_verdict(conclusion, feedback_rows), "domain_fallback"


def match_verdict(conclusion: AnalysisConclusion, feedback_rows: list[FeedbackRow]) -> Verdict:
    """05 § 十 的简化实现：把 analysis 结论与 feedback 行做语义匹配。

    优先匹配规则：
      1. domain 匹配 + 派别交集 → 取该子集中最具决断力的 verdict（miss > hit > abstain > no_data）
      2. domain 匹配 → 同上
      3. 全部 → no_data

    注意：rule_id 级的精确匹配请用 :func:`match_verdict_for_rule`，本函数仅做 conclusion 级回退。
    """
    if not feedback_rows:
        return "no_data"

    # ----- Step 1-2：domain + 派别交集 / domain 匹配 -----
    candidates: list[FeedbackRow] = []
    if conclusion.domain:
        candidates = [
            r for r in feedback_rows
            if r.domain == conclusion.domain
        ]
        if conclusion.schools:
            sch_set = set(conclusion.schools)
            tighter = [r for r in candidates if sch_set & set(r.schools)]
            if tighter:
                candidates = tighter
    if not candidates:
        # 退回到全集
        candidates = feedback_rows

    # 决断力：miss > hit > abstain > no_data
    priority = {"miss": 0, "hit": 1, "abstain": 2, "no_data": 3}
    candidates.sort(key=lambda r: priority[r.verdict])
    return candidates[0].verdict


# ============================================================
# 四、IterationDiff（输出 + 落盘审计）
# ============================================================

@dataclass
class RuleUpdate:
    rule_id: str
    school: str
    hits_before: int
    misses_before: int
    hits_after: int
    misses_after: int
    star_before: int
    star_after: int
    posterior_before: float
    posterior_after: float
    status_before: RuleStatus
    status_after: RuleStatus
    verdict: Verdict
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "school": self.school,
            "hits": {"before": self.hits_before, "after": self.hits_after},
            "misses": {"before": self.misses_before, "after": self.misses_after},
            "star": {"before": self.star_before, "after": self.star_after},
            "posterior": {
                "before": round(self.posterior_before, 4),
                "after": round(self.posterior_after, 4),
            },
            "status": {"before": self.status_before, "after": self.status_after},
            "verdict": self.verdict,
            "note": self.note,
        }


@dataclass
class VerdictContext:
    """v1.3 D5：规律级 verdict 的上下文，用于 IterationDiff 记录。

    两条路径都用这个数据类喂给 ``_apply_rule_verdicts``：
      - 启发式路径（v1.0）：从 ``AnalysisConclusion`` 转换而来
      - 结构化路径（v1.3，``feedback_ingest.py``）：直接从 statement_index.json 反查
    """
    section: str = ""
    year: Optional[int] = None
    domain: str = ""
    statement_ids: list[str] = field(default_factory=list)


@dataclass
class IterationDiff:
    case_id: str
    ts: str                                     # ISO datetime
    case_count: int
    rule_updates: list[RuleUpdate] = field(default_factory=list)
    status_changes: list[tuple[str, RuleStatus, RuleStatus, str]] = field(default_factory=list)
    cross_school_triggered: bool = False
    frozen: bool = False
    skipped_rule_ids: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "ts": self.ts,
            "case_count": self.case_count,
            "rule_updates": [u.to_dict() for u in self.rule_updates],
            "status_changes": [
                {"rule_id": r, "from": a, "to": b, "reason": z}
                for (r, a, b, z) in self.status_changes
            ],
            "cross_school_triggered": self.cross_school_triggered,
            "frozen": self.frozen,
            "skipped_rule_ids": self.skipped_rule_ids,
            "notes": self.notes,
        }


# ============================================================
# 五、case 工具
# ============================================================

def find_case_dir(case_id: str) -> pathlib.Path:
    """允许传入完整 case_id 或简化前缀。"""
    p = CASES_DIR / case_id
    if p.exists():
        return p
    # 模糊匹配前缀
    for child in CASES_DIR.iterdir():
        if child.is_dir() and child.name.startswith(case_id):
            return child
    raise FileNotFoundError(f"case 目录不存在: {case_id}")


def total_case_count() -> int:
    """统计 cases/ 下符合 C-YYYY-NNN-* 格式的目录数。"""
    if not CASES_DIR.exists():
        return 0
    pattern = re.compile(r"^C-\d{4}-\d{3}-")
    return sum(
        1 for p in CASES_DIR.iterdir()
        if p.is_dir() and pattern.match(p.name)
    )


# ============================================================
# 六、iteration-log.md 写入
# ============================================================

def append_iteration_log(diff: IterationDiff) -> None:
    """05 § 八 格式追加。

    在 ITERATION_LOG 末尾"## Annotations"段之前插入新段。
    """
    if not ITERATION_LOG.exists():
        # 兜底：若文件被误删则建一个最小骨架
        ITERATION_LOG.parent.mkdir(parents=True, exist_ok=True)
        ITERATION_LOG.write_text(
            "# iteration-log · 自迭代审计日志\n\n## Annotations\n",
            encoding="utf-8",
        )

    block = _format_iteration_block(diff)
    text = ITERATION_LOG.read_text(encoding="utf-8")

    if "## Annotations" in text:
        before, sep, after = text.partition("## Annotations")
        new_text = before.rstrip() + "\n\n" + block.rstrip() + "\n\n---\n\n" + sep + after
    else:
        new_text = text.rstrip() + "\n\n" + block.rstrip() + "\n"
    ITERATION_LOG.write_text(new_text, encoding="utf-8")


def _format_iteration_block(diff: IterationDiff) -> str:
    """格式化一个 ingest 段（中文 markdown）。"""
    lines: list[str] = []
    short_ts = diff.ts.replace("T", " ")[:16]
    lines.append(f"## {short_ts} · ingest {diff.case_id}")
    lines.append("")
    lines.append(f"case_count: {diff.case_count}")
    if diff.frozen:
        lines.append("trigger: ingest_feedback (FROZEN — calibration.yaml.freeze_iteration=true)")
    else:
        lines.append("trigger: ingest_feedback")
    lines.append("")

    # Rule Updates
    if diff.rule_updates:
        lines.append(f"### Rule Updates ({len(diff.rule_updates)} 条)")
        lines.append("")
        lines.append("| rule_id | 派 | hits 旧→新 | misses 旧→新 | conf ★ 旧→新 | status 旧→新 | verdict |")
        lines.append("|---|---|---|---|---|---|---|")
        for u in diff.rule_updates:
            lines.append(
                f"| {u.rule_id} | {u.school} | {u.hits_before}→{u.hits_after} | "
                f"{u.misses_before}→{u.misses_after} | "
                f"★{u.star_before}→★{u.star_after} | "
                f"{u.status_before}→{u.status_after} | {u.verdict} |"
            )
        lines.append("")

    # Status Changes
    if diff.status_changes:
        lines.append("### Status Changes")
        lines.append("")
        for rid, frm, to, why in diff.status_changes:
            lines.append(f"- {rid}: {frm} → {to}  ({why})")
        lines.append("")

    if diff.skipped_rule_ids:
        lines.append("### Skipped Rule IDs (in analysis but not in theory yaml)")
        lines.append("")
        for rid in diff.skipped_rule_ids:
            lines.append(f"- {rid}")
        lines.append("")

    if diff.notes:
        lines.append("### Notes")
        lines.append("")
        for n in diff.notes:
            lines.append(f"- {n}")
        lines.append("")

    # Cross-school
    lines.append("### Cross-School Scan")
    if diff.cross_school_triggered:
        lines.append(
            f"- 已触发（case_count={diff.case_count}，每 10 案）"
            f" → META/conflict-trends.md 已更新"
        )
    else:
        lines.append(
            f"- 未触发（case_count={diff.case_count}，下一次在 case_count "
            f"% 10 == 0 时）"
        )
    lines.append("")

    # Rollback
    snap_name = f"{_dt.date.today().isoformat()}-after-{diff.case_id}.snapshot.yaml"
    lines.append("### Rollback Hint")
    lines.append("")
    lines.append("```")
    lines.append(f"# 回滚到本次 ingest 前：")
    lines.append(f"git revert <commit-hash>")
    lines.append(f"# 或恢复快照：")
    lines.append(f"META/calibration/{snap_name}")
    lines.append("```")
    return "\n".join(lines)


# ============================================================
# 七、snapshot 落盘
# ============================================================

def write_snapshot(diff: IterationDiff) -> pathlib.Path:
    """落 META/calibration/{date}-after-{case_id}.snapshot.yaml。"""
    CALIBRATION_DIR.mkdir(parents=True, exist_ok=True)
    fname = f"{_dt.date.today().isoformat()}-after-{diff.case_id}.snapshot.yaml"
    path = CALIBRATION_DIR / fname
    payload = diff.to_dict()
    path.write_text(
        yaml.safe_dump(payload, allow_unicode=True, sort_keys=False, width=4096),
        encoding="utf-8",
    )
    return path


# ============================================================
# 八、ingest_feedback 主函数
# ============================================================

def _apply_rule_verdicts(
    case_id: str,
    rule_verdicts: dict[str, tuple[Verdict, VerdictContext]],
    *,
    cfg: LifecycleConfig,
    today: str,
    dry_run: bool = False,
) -> IterationDiff:
    """v1.3 D5 内部接口：把 rule-level verdicts 应用到规律 yaml 上。

    职责（05 § 七 主循环的核心步骤）：
        ③ 顺 rule_id 找规律 → 更新 hits/misses + recent_5
        ④ Beta 重算 confidence_cache
        ⑤ 跑升降级 + 漂移检测
        ⑥ save_rule()
        ⑨ case_count % 10 == 0 → 触发 cross_school_scan

    **不**做日志/快照落盘——caller（``ingest_feedback`` 或 ``feedback_ingest``）
    决定是否写 ``iteration-log.md`` 和 ``calibration/.snapshot.yaml``。

    Args:
        case_id:        完整 case_id（如 ``C-2026-001-庚申戊寅壬子辛丑``）
        rule_verdicts:  ``{"M2-Y-068": ("hit", VerdictContext(...)), ...}``
                        每条 verdict 已经在调用方做过决断力优先级合并
                        （miss > hit > abstain > no_data）
        cfg:            LifecycleConfig
        today:          ISO 日期串（用于规律状态变更登记）
        dry_run:        True 则不调 save_rule

    Returns:
        IterationDiff（含 case_count、rule_updates、status_changes、cross_school_triggered）
    """
    ts = _dt.datetime.now().isoformat(timespec="seconds")
    diff = IterationDiff(case_id=case_id, ts=ts, case_count=total_case_count())

    if cfg.freeze_iteration:
        diff.frozen = True
        diff.notes.append("freeze_iteration=true，全部更新被静默跳过")
        return diff

    for rid, (verdict, vctx) in rule_verdicts.items():
        try:
            rule = load_rule(rid)
        except RuleNotFoundError:
            diff.skipped_rule_ids.append(rid)
            continue

        # v1.4 V1：quantifiable=False → 框架性心法不参与 hit/miss 计分
        # 触发场景：M3-R-003 等"原局定层次..."级别的方法论总纲
        if not rule.quantifiable:
            diff.notes.append(
                f"[v1.4-V1] 跳过 {rid}: quantifiable=False"
                f"（框架性心法不参与 hit/miss 计分）"
            )
            continue

        # v1.4 V2：domain_restriction 非空且当前 domain 不在列表中 → 跳过该规律的本次计分
        # 触发场景：M3-R-031 仅适用于"应期"域，被错误引用到"婚姻"域时不计 miss
        # 注意：vctx.domain 为空时不强制（无法判定域）→ 仍计分，由上层决断力合并兜底
        if (
            rule.domain_restriction
            and vctx.domain
            and vctx.domain not in rule.domain_restriction
        ):
            diff.notes.append(
                f"[v1.4-V2] 跳过 {rid}: domain={vctx.domain!r} ∉ "
                f"domain_restriction={rule.domain_restriction}"
            )
            continue

        hits_before = rule.hits
        misses_before = rule.misses
        old_conf = rule.confidence_cache or rule.recompute_confidence(
            variance_threshold=cfg.variance_threshold
        )
        old_status = rule.status

        # 备注：v1.3 路径会把 statement_ids 也写入 note，便于反查
        sid_str = (
            f" | sids={','.join(vctx.statement_ids[:3])}"
            if vctx.statement_ids else ""
        )
        note = f"{vctx.section} | {vctx.domain}{sid_str}".strip(" |")

        if verdict == "hit":
            rule.hits += 1
            rule.update_recent_window(True, window_size=cfg.drift_window_size)
            rule.applied_cases.append(AppliedCase(
                case_id=case_id,
                year=vctx.year,
                hit=True,
                evidence_chain=[rid],
                note=note,
            ))
        elif verdict == "miss":
            rule.misses += 1
            rule.update_recent_window(False, window_size=cfg.drift_window_size)
            rule.applied_cases.append(AppliedCase(
                case_id=case_id,
                year=vctx.year,
                hit=False,
                evidence_chain=[rid],
                note=note,
            ))
        elif verdict == "abstain":
            rule.abstained += 1
        else:
            # no_data → 跳过完全
            continue

        new_conf = rule.recompute_confidence(variance_threshold=cfg.variance_threshold)

        # 升降级 + 漂移
        new_status: Optional[RuleStatus] = None
        reason = ""
        up = maybe_upgrade(rule, cfg=cfg)
        if up is not None:
            new_status = up
            reason = f"auto-upgrade (n={rule.n} rate={rule.hit_rate:.2f})"
        if new_status is None:
            down = maybe_downgrade(rule, cfg=cfg)
            if down is not None:
                new_status = down
                reason = f"auto-downgrade (累计 misses 触发缓冲阈值)"
        if new_status is None:
            drift = detect_drift(rule, cfg=cfg)
            if drift is not None:
                new_status = drift
                window = rule.recent_5[-cfg.drift_window_size:]
                rate = sum(1 for x in window if x) / cfg.drift_window_size
                reason = f"drift detected (recent_{cfg.drift_window_size} hit_rate={rate:.0%})"

        if new_status is not None and new_status != rule.status:
            apply_status_change(rule, new_status, case_id=case_id, reason=reason, today=today)
            diff.status_changes.append((rule.id, old_status, new_status, reason))

        diff.rule_updates.append(RuleUpdate(
            rule_id=rid,
            school=rule.school,
            hits_before=hits_before,
            misses_before=misses_before,
            hits_after=rule.hits,
            misses_after=rule.misses,
            star_before=old_conf.star,
            star_after=new_conf.star,
            posterior_before=old_conf.posterior,
            posterior_after=new_conf.posterior,
            status_before=old_status,
            status_after=rule.status,
            verdict=verdict,
            note=vctx.section,
        ))

        if not dry_run:
            save_rule(rule)

    # cross_school_scan trigger（每 N 案）
    if (
        diff.case_count > 0
        and cfg.cross_school_every_n_cases > 0
        and diff.case_count % cfg.cross_school_every_n_cases == 0
    ):
        diff.cross_school_triggered = True
        if not dry_run:
            try:
                from tools.cross_school_scan import cross_school_scan
                cross_school_scan(triggered_by=case_id)
            except Exception as exc:  # pragma: no cover
                diff.notes.append(f"cross_school_scan 失败: {exc!r}")

    return diff


# ============================================================
# 八、ingest_feedback 主函数
# ============================================================

def ingest_feedback(
    case_id: str,
    *,
    cfg: Optional[LifecycleConfig] = None,
    today: Optional[str] = None,
    dry_run: bool = False,
) -> IterationDiff:
    """05 § 七 主循环（v1.0 启发式入口，向下兼容）。

    v1.3 D5 重构：把核心 rule-level 应用逻辑抽到 ``_apply_rule_verdicts``，
    本函数仅负责 v1.0 启发式解析（``parse_feedback_md`` + ``parse_analysis_md``）
    + 日志/快照落盘。新格式的结构化反馈走 ``tools/feedback_ingest.py``。

    Parameters
    ----------
    case_id : str
        案例 ID，如 "C-2026-001-庚申戊寅壬子辛丑"。也接受前缀 "C-2026-001"。
    cfg : LifecycleConfig
        可选，默认从 engine/calibration.yaml 加载。
    today : str
        ISO 日期；测试用。
    dry_run : bool
        若 True，不落盘 yaml / iteration-log / snapshot。
    """
    cfg = cfg or LifecycleConfig.from_yaml()
    today = today or _dt.date.today().isoformat()

    case_dir = find_case_dir(case_id)
    full_case_id = case_dir.name

    if cfg.freeze_iteration:
        # 走快速通道，与原行为一致：写一条空 diff + 落 snapshot
        ts = _dt.datetime.now().isoformat(timespec="seconds")
        diff = IterationDiff(case_id=full_case_id, ts=ts, case_count=total_case_count())
        diff.frozen = True
        diff.notes.append("freeze_iteration=true，全部更新被静默跳过")
        if not dry_run:
            append_iteration_log(diff)
            write_snapshot(diff)
        return diff

    feedback_rows = parse_feedback_md(case_dir / "feedback.md")
    conclusions = parse_analysis_md(case_dir / "analysis.md")

    # 启发式：build rule_verdicts
    # v1.3 D5+ 历史回补（2026-05-25）：rule_id 级精确匹配优先（match_verdict_for_rule），
    # 避免 conclusion 一次性合并多个 rule_id 导致 verdict 串扰（C-2026-014 学业段三规律
    # 各自有不同 verdict 是典型场景）。
    rule_verdicts: dict[str, tuple[Verdict, VerdictContext]] = {}
    priority = {"miss": 0, "hit": 1, "abstain": 2, "no_data": 3}
    for c in conclusions:
        for rid in c.rule_ids:
            v, _src = match_verdict_for_rule(rid, c, feedback_rows)
            existing = rule_verdicts.get(rid)
            vctx = VerdictContext(
                section=c.section,
                year=c.yingqi_year,
                domain=c.domain or "",
                statement_ids=[],  # v1.0 启发式路径无 statement_id
            )
            if existing is None or priority[v] < priority[existing[0]]:
                rule_verdicts[rid] = (v, vctx)

    diff = _apply_rule_verdicts(
        full_case_id, rule_verdicts, cfg=cfg, today=today, dry_run=dry_run
    )

    # notes
    if not feedback_rows:
        diff.notes.append("feedback.md 中未检出含应验标记的表格行")
    if not conclusions:
        diff.notes.append("analysis.md 中未检出任何含规律 ID 的结论段")

    if not dry_run:
        append_iteration_log(diff)
        write_snapshot(diff)

    return diff


# ============================================================
# 九、smoke / CLI
# ============================================================

def _smoke() -> None:
    """轻量回放 C-2026-001（dry_run=True，不写盘）。"""
    diff = ingest_feedback("C-2026-001", dry_run=True)
    print(f"[ingest] case_id={diff.case_id}")
    print(f"  case_count={diff.case_count}")
    print(f"  rule_updates={len(diff.rule_updates)}")
    print(f"  status_changes={len(diff.status_changes)}")
    print(f"  skipped={len(diff.skipped_rule_ids)}")
    for u in diff.rule_updates[:8]:
        print(
            f"    {u.rule_id} ({u.school}) {u.verdict}: "
            f"hits {u.hits_before}→{u.hits_after}, miss {u.misses_before}→{u.misses_after}, "
            f"★{u.star_before}→★{u.star_after}, status {u.status_before}→{u.status_after}"
        )
    if diff.skipped_rule_ids:
        print(f"  跳过的（theory yaml 中找不到的）规律 ID:")
        for rid in diff.skipped_rule_ids[:8]:
            print(f"    - {rid}")


if __name__ == "__main__":  # pragma: no cover
    import sys
    if len(sys.argv) > 1:
        case_id = sys.argv[1]
        diff = ingest_feedback(case_id, dry_run="--dry-run" in sys.argv)
        print(json.dumps(diff.to_dict(), ensure_ascii=False, indent=2))
    else:
        _smoke()

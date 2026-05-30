"""tools/late_feedback.py · v1.3 D7 应期延迟反馈通道

落地契约：
    plans/architecture-v1.3.md § 四 D7（应期延迟反馈）
    plans/architecture-v1.3.md § 七 (问题 5)：应期统计独立隔离

工作流（命主 1+ 年后回流事件）：
    1. 事件签名通过 extract_predictions 在分析阶段已经写到
       predictions/PRED-YYYY-NNN-CXXXXXXX-{乾/坤}-{干支}-{event}.md 的 frontmatter。
    2. 命理师收到延迟反馈：「命主 2027 年 3 月领证结婚」
    3. 运行：python3 -m tools.late_feedback C-2026-007 --year 2027 --event marriage --hit yes
    4. 系统：
       a. 扫 predictions/ 找该 case_id 的所有 pending 预测
       b. 按 (year ±1, event_signature) 匹配候选预测
       c. 命中（in window） → status=verified，hit_score=1.0
          边缘（off-by-1）→ status=verified_partial，hit_score=0.5
          无匹配（窗内未发生）→ 命理师可显式 --hit no 标记 status=falsified
       d. 写 META/late-feedback-log.md 审计日志
       e. **不**调 _apply_rule_verdicts，应期统计与画像统计完全隔离

为什么不调 _apply_rule_verdicts：
    应期类规律（任派 MR-LAYER3、M3-R-*）的命中率必须独立维护，
    避免应期晚验把画像类规律统计带歪（D7 锁定决策）。
    本工具仅更新 PRED 文件状态 + 累积审计日志。
    后续 W3 实现 boundary_miner 时再决定是否合并到独立的 yingqi_stats.json。

公开 API
--------
record(case_id, year, event, hit) -> LateFeedbackResult
    主入口

find_matching_predictions(case_id, year, event) -> list[Match]
    纯函数：扫 predictions 找候选

EVENT_ALIASES
    用户输入的中文/英文别名 → 标准签名
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import pathlib
import re
import sys
from dataclasses import dataclass, field
from typing import Any, Literal, Optional

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
PREDICTIONS_DIR = REPO_ROOT / "predictions"
META_DIR = REPO_ROOT / "META"
LATE_FEEDBACK_LOG = META_DIR / "late-feedback-log.md"

# ============================================================
# 一、事件别名（命理师输入 → 标准签名）
# ============================================================

# 同时接受英文标准签名 + 中文别名 + 命理师习惯口径
EVENT_ALIASES: dict[str, str] = {
    # marriage
    "marriage": "marriage", "结婚": "marriage", "成婚": "marriage",
    "领证": "marriage", "嫁娶": "marriage", "婚": "marriage",
    # divorce
    "divorce": "divorce", "离婚": "divorce", "分居": "divorce",
    # childbirth
    "childbirth": "childbirth", "生子": "childbirth", "生女": "childbirth",
    "添丁": "childbirth", "怀孕": "childbirth", "得子": "childbirth",
    # death
    "death": "death", "去世": "death", "亡故": "death", "病逝": "death",
    "身亡": "death",
    # accident
    "accident": "accident", "车祸": "accident", "外伤": "accident",
    "意外": "accident", "受伤": "accident",
    # illness
    "illness": "illness", "重病": "illness", "大病": "illness",
    "手术": "illness", "住院": "illness", "癌症": "illness",
    # promotion
    "promotion": "promotion", "升职": "promotion", "升迁": "promotion",
    "晋升": "promotion", "高升": "promotion", "提拔": "promotion",
    # demotion
    "demotion": "demotion", "降职": "demotion", "撤职": "demotion",
    # career_change
    "career_change": "career_change", "跳槽": "career_change",
    "转行": "career_change", "创业": "career_change", "辞职": "career_change",
    # exam_pass
    "exam_pass": "exam_pass", "高考": "exam_pass", "考上": "exam_pass",
    "录取": "exam_pass", "考研": "exam_pass", "中举": "exam_pass",
    # wealth_gain / loss
    "wealth_gain": "wealth_gain", "发财": "wealth_gain", "中奖": "wealth_gain",
    "wealth_loss": "wealth_loss", "破财": "wealth_loss", "亏损": "wealth_loss",
    "破产": "wealth_loss",
    # legal_trouble
    "legal_trouble": "legal_trouble", "官司": "legal_trouble",
    "牢狱": "legal_trouble", "诉讼": "legal_trouble",
    # emigration
    "emigration": "emigration", "出国": "emigration", "移民": "emigration",
}


def normalize_event(event: str) -> str:
    """把命理师输入的事件名归一化到标准签名。"""
    if not event:
        return "unknown"
    e = event.strip().lower()
    if e in EVENT_ALIASES:
        return EVENT_ALIASES[e]
    # 中文不区分大小写
    if event.strip() in EVENT_ALIASES:
        return EVENT_ALIASES[event.strip()]
    # 部分匹配（命理师可能写"领证结婚"）
    for alias, sig in EVENT_ALIASES.items():
        if alias in event:
            return sig
    return event.strip().lower()  # 兜底：原样返回


# ============================================================
# 二、PRED 文件解析
# ============================================================

# YAML frontmatter 简易解析（不依赖 yaml 包）
# PRED-*.md 的 frontmatter 由 extract_predictions 用 yaml.safe_dump 生成，
# 但本工具读时只需抽取几个标量字段，用 regex 即可。
_FM_RE = re.compile(r"^---\s*\n(?P<body>.*?)\n---", re.DOTALL)


def _parse_frontmatter(text: str) -> dict[str, Any]:
    """极简 frontmatter 抽取：仅支持本工具关心的几个标量字段。

    支持的 pattern:
        case_id: C-2026-007-...
        yingqi_year: 2027
        event_signature: marriage
        domain: 婚姻
        status: pending
        fingerprint: abc12345
        yingqi_window: [2026, 2028]
    """
    m = _FM_RE.search(text)
    if not m:
        return {}
    body = m.group("body")
    out: dict[str, Any] = {}
    for line in body.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        # key: value
        mm = re.match(r"^([\w_]+):\s*(.*)$", s)
        if not mm:
            continue
        k, v = mm.group(1), mm.group(2).strip()
        # 去引号
        if (v.startswith("'") and v.endswith("'")) or (v.startswith('"') and v.endswith('"')):
            v = v[1:-1]
        # int
        if re.fullmatch(r"-?\d+", v):
            out[k] = int(v)
            continue
        # list[int]
        m_list = re.fullmatch(r"\[\s*(-?\d+)\s*,\s*(-?\d+)\s*\]", v)
        if m_list:
            out[k] = [int(m_list.group(1)), int(m_list.group(2))]
            continue
        out[k] = v
    return out


# ============================================================
# 三、匹配
# ============================================================

@dataclass
class PredictionMatch:
    path: pathlib.Path
    case_id: str
    yingqi_year: int
    event_signature: str
    domain: str
    status: str
    in_window: bool         # 是否落在 ±1 应期窗口内
    year_offset: int        # |reported_year - yingqi_year|
    score: float            # 1.0 (in window) / 0.5 (off-by-1) / 0.0 (mismatch)


def find_matching_predictions(
    case_id: str,
    year: int,
    event: str,
    *,
    predictions_dir: Optional[pathlib.Path] = None,
) -> list[PredictionMatch]:
    """扫 predictions/ 找候选预测。

    匹配条件（D7 决策）：
      1. case_id 完全相同
      2. event_signature 完全相同（已归一化）
      3. |yingqi_year - reported_year| ≤ 1（窗内 hit_score=1.0，边缘 0.5）

    若一个事件签名在该 case 下有多条预测（罕见），全部返回让命理师选。
    """
    sig = normalize_event(event)
    out: list[PredictionMatch] = []
    pdir = predictions_dir if predictions_dir is not None else PREDICTIONS_DIR
    if not pdir.exists():
        return out
    for p in sorted(pdir.glob("PRED-*.md")):
        try:
            text = p.read_text(encoding="utf-8")
        except OSError:
            continue
        fm = _parse_frontmatter(text)
        if fm.get("case_id") != case_id:
            continue
        pred_year = fm.get("yingqi_year")
        if not isinstance(pred_year, int):
            continue
        offset = abs(int(pred_year) - int(year))
        if offset > 1:
            continue
        pred_sig = fm.get("event_signature", "unknown")
        if pred_sig != sig:
            continue
        in_window = offset == 0
        score = 1.0 if in_window else 0.5
        out.append(PredictionMatch(
            path=p,
            case_id=case_id,
            yingqi_year=int(pred_year),
            event_signature=str(pred_sig),
            domain=str(fm.get("domain", "")),
            status=str(fm.get("status", "pending")),
            in_window=in_window,
            year_offset=offset,
            score=score,
        ))
    return out


# ============================================================
# 四、状态更新（直接改 PRED frontmatter status 行）
# ============================================================

_STATUS_RE = re.compile(r"^status:\s*\S+\s*$", re.MULTILINE)
_VERIFIED_AT_RE = re.compile(r"^verified_at:\s*.*$", re.MULTILINE)


def _update_pred_status(
    path: pathlib.Path,
    new_status: str,
    *,
    reported_year: int,
    reported_event: str,
    hit_score: float,
    today: str,
) -> None:
    """把 PRED 文件 frontmatter 中 status 改为 new_status，并追加审计行。"""
    text = path.read_text(encoding="utf-8")
    text = _STATUS_RE.sub(f"status: {new_status}", text, count=1)
    # frontmatter 末尾 (--- 前) 插入 verified 字段
    audit_block = (
        f"verified_at: {today}\n"
        f"reported_year: {reported_year}\n"
        f"reported_event: {reported_event}\n"
        f"hit_score: {hit_score:.1f}\n"
    )
    # 如果之前已经写过 verified 块，先删
    text = _VERIFIED_AT_RE.sub("", text)
    text = re.sub(r"^reported_year:\s*.*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^reported_event:\s*.*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^hit_score:\s*.*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"\n{3,}", "\n\n", text)
    # 找到第二个 ---（frontmatter 闭合）并在其前插入
    parts = text.split("---", 2)
    if len(parts) >= 3:
        # parts[1] 是 frontmatter 内容
        fm = parts[1].rstrip() + "\n" + audit_block
        text = "---" + fm + "---" + parts[2]
    path.write_text(text, encoding="utf-8")


# ============================================================
# 五、审计日志（独立于规律 yaml）
# ============================================================

@dataclass
class LateFeedbackResult:
    case_id: str
    reported_year: int
    reported_event: str          # 归一化后
    raw_event_input: str         # 命理师原始输入
    hit: bool
    matches: list[PredictionMatch] = field(default_factory=list)
    updated_files: list[pathlib.Path] = field(default_factory=list)
    skipped_no_match: bool = False
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "reported_year": self.reported_year,
            "reported_event": self.reported_event,
            "raw_event_input": self.raw_event_input,
            "hit": self.hit,
            "matches": [
                {
                    "path": str(m.path.relative_to(REPO_ROOT)),
                    "yingqi_year": m.yingqi_year,
                    "year_offset": m.year_offset,
                    "score": m.score,
                    "in_window": m.in_window,
                    "status_before": m.status,
                }
                for m in self.matches
            ],
            "updated_files": [str(p.relative_to(REPO_ROOT)) for p in self.updated_files],
            "skipped_no_match": self.skipped_no_match,
            "notes": self.notes,
        }


def _append_audit_log(result: LateFeedbackResult, today: str) -> None:
    META_DIR.mkdir(parents=True, exist_ok=True)
    if not LATE_FEEDBACK_LOG.exists():
        LATE_FEEDBACK_LOG.write_text(
            "# late-feedback-log · 应期延迟反馈审计日志\n\n"
            "> 由 `tools/late_feedback.py` 维护。\n"
            "> 应期类规律命中率独立统计（D7 决策），不污染画像类规律 yaml。\n\n"
            "## Annotations\n",
            encoding="utf-8",
        )
    block = _format_log_block(result, today)
    text = LATE_FEEDBACK_LOG.read_text(encoding="utf-8")
    if "## Annotations" in text:
        before, sep, after = text.partition("## Annotations")
        new_text = before.rstrip() + "\n\n" + block.rstrip() + "\n\n---\n\n" + sep + after
    else:
        new_text = text.rstrip() + "\n\n" + block.rstrip() + "\n"
    LATE_FEEDBACK_LOG.write_text(new_text, encoding="utf-8")


def _format_log_block(result: LateFeedbackResult, today: str) -> str:
    lines: list[str] = []
    lines.append(f"## {today} · late-feedback {result.case_id}")
    lines.append("")
    lines.append(f"- reported_year: {result.reported_year}")
    lines.append(f"- reported_event: `{result.reported_event}` (raw: {result.raw_event_input!r})")
    lines.append(f"- hit: {result.hit}")
    if result.matches:
        lines.append(f"- matches: {len(result.matches)} 条")
        lines.append("")
        lines.append("| PRED | yingqi_year | offset | score | in_window | status_before |")
        lines.append("|---|---|---|---|---|---|")
        for m in result.matches:
            lines.append(
                f"| `{m.path.name}` | {m.yingqi_year} | {m.year_offset} | "
                f"{m.score:.1f} | {m.in_window} | {m.status} |"
            )
    else:
        lines.append("- matches: 无（窗外或事件签名不匹配）")
    if result.notes:
        lines.append("")
        lines.append("**Notes:**")
        for n in result.notes:
            lines.append(f"- {n}")
    return "\n".join(lines)


# ============================================================
# 六、主入口 record()
# ============================================================

def record(
    case_id: str,
    year: int,
    event: str,
    hit: bool,
    *,
    today: Optional[str] = None,
    dry_run: bool = False,
) -> LateFeedbackResult:
    """v1.3 D7 主入口：登记一条应期延迟反馈。

    Args:
        case_id:  完整 case_id（如 ``C-2026-007-乾-乙丑庚辰己丑庚午``）
        year:     命主回流的事件年份
        event:    事件名（中文/英文/标准签名均可，会自动归一化）
        hit:      True=应验、False=失验（窗内未发生指定事件）
        today:    ISO 日期串
        dry_run:  True 则不更新 PRED 文件 / 不写日志

    Returns:
        LateFeedbackResult
    """
    today = today or _dt.date.today().isoformat()
    sig = normalize_event(event)

    matches = find_matching_predictions(case_id, year, sig)

    result = LateFeedbackResult(
        case_id=case_id,
        reported_year=year,
        reported_event=sig,
        raw_event_input=event,
        hit=hit,
        matches=matches,
    )

    if not matches:
        result.skipped_no_match = True
        result.notes.append(
            f"未在 predictions/ 找到 (case_id={case_id}, year={year}±1, "
            f"event={sig}) 的 pending 预测。可能原因：①该断语未到 ★4+ 没被封存；"
            f"②命理师事件名拼写不规范；③该应期实际无预测（命中即 hit=False，"
            f"表示画像类规律预测的事件未发生）。"
        )
    else:
        # 决策树：
        #   hit=True  且 in_window      → status=verified, score=1.0
        #   hit=True  且 off-by-1       → status=verified_partial, score=0.5
        #   hit=False                   → status=falsified, score=0.0（命主在窗内未发生指定事件）
        for m in matches:
            if hit:
                new_status = "verified" if m.in_window else "verified_partial"
                hit_score = 1.0 if m.in_window else 0.5
            else:
                new_status = "falsified"
                hit_score = 0.0
                m.score = 0.0  # 反映 result
            if not dry_run:
                _update_pred_status(
                    m.path, new_status,
                    reported_year=year,
                    reported_event=sig,
                    hit_score=hit_score,
                    today=today,
                )
                result.updated_files.append(m.path)

    if not dry_run:
        _append_audit_log(result, today)

    return result


# ============================================================
# 七、CLI
# ============================================================

def _print_human(result: LateFeedbackResult) -> None:
    print(f"\n[late-feedback] case_id={result.case_id}")
    print(f"  reported: year={result.reported_year}, event={result.reported_event}"
          f" (raw='{result.raw_event_input}'), hit={result.hit}")
    if result.skipped_no_match:
        print("  ⚠️  未找到匹配的 pending 预测")
        for n in result.notes:
            print(f"    {n}")
        return
    print(f"  匹配到 {len(result.matches)} 条预测：")
    for m in result.matches:
        marker = "🎯" if m.in_window else "🟡"
        print(f"    {marker} {m.path.name}")
        print(f"        yingqi_year={m.yingqi_year} offset={m.year_offset} "
              f"score={m.score:.1f} in_window={m.in_window}")
    if result.updated_files:
        print(f"  已更新 {len(result.updated_files)} 个 PRED 文件状态")
    print(f"  审计日志: META/late-feedback-log.md")


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="v1.3 D7 应期延迟反馈：把命主 1+ 年后回流的事件匹配到封存预测",
        epilog=(
            "示例:\n"
            "  late_feedback C-2026-007-乾-乙丑庚辰己丑庚午 --year 2027 --event marriage --hit yes\n"
            "  late_feedback C-2026-007 --year 2028 --event 升职 --hit no\n"
            "事件名支持中英文 + 别名（见 tools/late_feedback.EVENT_ALIASES）"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("case_id", help="完整 case_id（C-YYYY-NNN-八字）")
    parser.add_argument("--year", type=int, required=True, help="命主回流的事件年份")
    parser.add_argument("--event", required=True,
                        help="事件名（中/英/别名都行，会自动归一化）")
    parser.add_argument("--hit", choices=["yes", "no", "y", "n"], required=True,
                        help="yes=应验 / no=失验")
    parser.add_argument("--dry-run", action="store_true",
                        help="不更新 PRED 文件，不写审计日志")
    parser.add_argument("--json", action="store_true", help="JSON 输出")
    args = parser.parse_args(argv)

    hit = args.hit in ("yes", "y")
    try:
        result = record(args.case_id, args.year, args.event, hit, dry_run=args.dry_run)
    except FileNotFoundError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    else:
        _print_human(result)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())

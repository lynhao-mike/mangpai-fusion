"""tools/feedback_ingest.py · v1.3 D5 结构化反馈摄入

落地契约：
    plans/architecture-v1.3.md § 四 D5（过后反馈工作流）
    plans/architecture-v1.3.md § 四 D8（每 10 反馈案触发自迭代）

工作流（命理师视角）：
    1. 命理师把 master 报告（含 `[S-...] [ ]` 反馈位）另存为
       cases/C-XXXX/feedback.md
    2. 把每条 `[ ]` 填为：
         [y]    应验
         [n]    失验
         [?]    命主当场不知道（入库不计数，等待延迟反馈兑现）
         [skip] 解释时未讲到 / 不适用
    3. 运行：python3 -m tools.feedback_ingest C-XXXX
    4. 系统反查 cases/C-XXXX/statement_index.json 找规律 ID，
       把 statement-level verdict fanout 到 rule-level，
       调 feedback_loop._apply_rule_verdicts 重算置信度
    5. 完成反馈案数 +1；若达到 10 的整数倍 → 输出迭代提示

公开 API
--------
ingest(case_id, *, cfg=None, dry_run=False) -> IngestResult
    主入口；解析 → fanout → 应用 → 计数 → 落盘审计

parse_statement_feedback(text) -> list[StatementFeedback]
    纯函数：从填好的 feedback.md 文本里抽出 [(sid, verdict), ...]

fanout_to_rules(statement_feedbacks, statement_index)
    → dict[rule_id, (Verdict, VerdictContext)]
    按决断力优先级（miss > hit > abstain > skip/no_data）合并

注意：本工具优先消费 v1.3 结构化路径（statement_index.json + 标注式 feedback.md）。
若 statement_index.json 不存在或 feedback.md 中无 `[S-...]` 标注，
回退给 feedback_loop.ingest_feedback 走 v1.0 启发式路径。

作者：Track-G v1.3
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

from tools.feedback_loop import (
    IterationDiff,
    Verdict,
    VerdictContext,
    _apply_rule_verdicts,
    append_iteration_log,
    find_case_dir,
    total_case_count,
    write_snapshot,
)
from tools.rule_lifecycle import LifecycleConfig

# ============================================================
# 一、路径常量
# ============================================================

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
META_DIR = REPO_ROOT / "META"
ITERATION_STATE_FILE = META_DIR / "iteration-state.json"


# ============================================================
# 二、解析器
# ============================================================

# 反馈标注正则：``[S-001-a3f1c2] [y]`` 或同行的 ``反馈：[S-...] [n]``
# 分组 1: statement_id；分组 2: 标注（y/n/?/skip）
FEEDBACK_RE = re.compile(
    r"\[(S-[A-Za-z0-9_]+-[a-f0-9]{6})\]\s*\[(y|n|\?|skip)\]",
    re.IGNORECASE,
)

# verdict 映射：标注 → 内部 Verdict
ANNOTATION_TO_VERDICT: dict[str, Verdict] = {
    "y": "hit",
    "n": "miss",
    "?": "no_data",   # D5 决策：? 入库不计数
    "skip": "no_data",
}


@dataclass
class StatementFeedback:
    """一条断语级反馈。"""
    statement_id: str
    annotation: str            # 原始标注："y"/"n"/"?"/"skip"
    verdict: Verdict           # 转换后的内部 Verdict
    raw_line: str = ""


@dataclass
class IngestResult:
    """ingest() 的返回值。"""
    case_id: str
    feedback_count: int                       # 解析到的 statement 反馈条数
    rule_count: int                           # fanout 后涉及的不重复规律数
    skipped_unknown_sid: list[str] = field(default_factory=list)
    skipped_no_index: bool = False             # 走了启发式 fallback
    iteration_diff: Optional[IterationDiff] = None
    feedback_completed_count: int = 0          # 本次写入后的总完成反馈案数
    iteration_seq: int = 0                     # 当前迭代序号（每 10 完成案 +1）
    iteration_triggered: bool = False          # 本次是否达到 10 案整数倍
    iteration_report_path: Optional[str] = None  # v1.3 D8：自动触发的迭代报告路径

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "feedback_count": self.feedback_count,
            "rule_count": self.rule_count,
            "skipped_unknown_sid": self.skipped_unknown_sid,
            "skipped_no_index": self.skipped_no_index,
            "feedback_completed_count": self.feedback_completed_count,
            "iteration_seq": self.iteration_seq,
            "iteration_triggered": self.iteration_triggered,
            "iteration_report_path": self.iteration_report_path,
            "iteration_diff": self.iteration_diff.to_dict() if self.iteration_diff else None,
        }


def parse_statement_feedback(text: str) -> list[StatementFeedback]:
    """从填好的 feedback.md 文本里抽出所有 `[S-...] [y/n/?/skip]` 标注。

    去重策略：同一 statement_id 出现多次 → 取**最后一次**有效标注（命理师可能改主意）。
    """
    matches: dict[str, StatementFeedback] = {}
    for line in text.splitlines():
        for m in FEEDBACK_RE.finditer(line):
            sid = m.group(1)
            ann = m.group(2).lower()
            verdict = ANNOTATION_TO_VERDICT.get(ann, "no_data")
            matches[sid] = StatementFeedback(
                statement_id=sid,
                annotation=ann,
                verdict=verdict,
                raw_line=line.strip(),
            )
    return list(matches.values())


# ============================================================
# 三、Statement → Rule fanout
# ============================================================

# 决断力优先级：miss 最强 → no_data 最弱
_PRIORITY: dict[Verdict, int] = {
    "miss": 0,
    "hit": 1,
    "abstain": 2,
    "no_data": 3,
}


def fanout_to_rules(
    feedbacks: list[StatementFeedback],
    statement_index: dict[str, Any],
) -> tuple[dict[str, tuple[Verdict, VerdictContext]], list[str]]:
    """v1.3 D5：把 statement-level verdict fanout 到 rule-level。

    一条规律可能被多条断语共用 → 取**最具决断力**的 verdict
    （miss > hit > abstain > no_data）。

    Returns:
        rule_verdicts: ``{rule_id: (Verdict, VerdictContext)}``
        unknown_sids: 在 feedback.md 中出现但 statement_index 里查不到的 sid
                      （通常意味着报告与索引版本不匹配，需重跑 render）
    """
    statements = statement_index.get("statements", {})
    rule_verdicts: dict[str, tuple[Verdict, VerdictContext]] = {}
    unknown_sids: list[str] = []

    for fb in feedbacks:
        info = statements.get(fb.statement_id)
        if info is None:
            unknown_sids.append(fb.statement_id)
            continue
        rule_ids = info.get("rule_ids", []) or []
        if not rule_ids:
            continue
        section = info.get("section", "")
        year = info.get("year")
        domain = info.get("domain", "")

        for rid in rule_ids:
            existing = rule_verdicts.get(rid)
            if existing is None or _PRIORITY[fb.verdict] < _PRIORITY[existing[0]]:
                # 合并 statement_ids（多条断语指向同一规律时累积）
                prev_sids = existing[1].statement_ids if existing else []
                vctx = VerdictContext(
                    section=section,
                    year=year,
                    domain=domain,
                    statement_ids=sorted(set(prev_sids + [fb.statement_id])),
                )
                rule_verdicts[rid] = (fb.verdict, vctx)
            else:
                # 优先级相同或更低 → 仅累积 statement_ids
                ev, vctx = existing
                vctx.statement_ids = sorted(set(vctx.statement_ids + [fb.statement_id]))

    return rule_verdicts, unknown_sids


# ============================================================
# 四、迭代计数器（D8 每 10 反馈案触发）
# ============================================================

@dataclass
class IterationState:
    feedback_completed_count: int = 0
    last_iteration_at_count: int = 0
    iteration_seq: int = 0
    completed_case_ids: list[str] = field(default_factory=list)

    @classmethod
    def load(cls) -> "IterationState":
        if ITERATION_STATE_FILE.exists():
            try:
                payload = json.loads(ITERATION_STATE_FILE.read_text(encoding="utf-8"))
                return cls(
                    feedback_completed_count=payload.get("feedback_completed_count", 0),
                    last_iteration_at_count=payload.get("last_iteration_at_count", 0),
                    iteration_seq=payload.get("iteration_seq", 0),
                    completed_case_ids=payload.get("completed_case_ids", []),
                )
            except (json.JSONDecodeError, ValueError):
                pass
        return cls()

    def save(self) -> None:
        META_DIR.mkdir(parents=True, exist_ok=True)
        ITERATION_STATE_FILE.write_text(
            json.dumps(
                {
                    "feedback_completed_count": self.feedback_completed_count,
                    "last_iteration_at_count": self.last_iteration_at_count,
                    "iteration_seq": self.iteration_seq,
                    "completed_case_ids": self.completed_case_ids,
                    "_updated_at": _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )


# ============================================================
# 五、主入口 ingest()
# ============================================================

def ingest(
    case_id: str,
    *,
    cfg: Optional[LifecycleConfig] = None,
    today: Optional[str] = None,
    dry_run: bool = False,
) -> IngestResult:
    """v1.3 D5 主入口：解析新格式 feedback.md → fanout → 应用 → 计数。

    Steps:
        1. 找 case 目录
        2. 读 statement_index.json（D1 落盘的索引）
        3. 解析 feedback.md 中的 `[S-...] [y/n/?/skip]` 标注
        4. fanout 到 rule_verdicts
        5. 调 feedback_loop._apply_rule_verdicts 应用更新
        6. 写 iteration-log + snapshot
        7. 更新 META/iteration-state.json 计数器
        8. 检查 % 10 == 0 → iteration_triggered=True

    Args:
        case_id:  完整 case_id 或前缀（如 ``C-2026-001``）
        cfg:      LifecycleConfig；默认从 engine/calibration.yaml 加载
        today:    ISO 日期串（测试用）
        dry_run:  True 则不写规律 yaml / 不写 iteration-log / 不写 state

    Raises:
        FileNotFoundError: case 目录或 feedback.md 不存在
        RuntimeError:      没有可解析的反馈（既无标注又无启发式可走）
    """
    cfg = cfg or LifecycleConfig.from_yaml()
    today = today or _dt.date.today().isoformat()

    case_dir = find_case_dir(case_id)
    full_case_id = case_dir.name

    feedback_path = case_dir / "feedback.md"
    if not feedback_path.exists():
        raise FileNotFoundError(f"feedback.md 不存在: {feedback_path}")

    # 1. 解析 statement-level 标注
    feedback_text = feedback_path.read_text(encoding="utf-8")
    feedbacks = parse_statement_feedback(feedback_text)

    # 2. 读 statement_index
    index_path = case_dir / "statement_index.json"
    statement_index: dict = {}
    skipped_no_index = False
    if index_path.exists():
        try:
            statement_index = json.loads(index_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, ValueError):
            statement_index = {}

    # 3. 决策路径选择
    if not feedbacks or not statement_index.get("statements"):
        # 退回 v1.0 启发式路径（feedback_loop.ingest_feedback）
        from tools.feedback_loop import ingest_feedback as _legacy_ingest
        diff = _legacy_ingest(full_case_id, cfg=cfg, today=today, dry_run=dry_run)
        skipped_no_index = True
        # 仍然把这个案纳入完成反馈计数（哪怕走了启发式）
        result = IngestResult(
            case_id=full_case_id,
            feedback_count=len(feedbacks),
            rule_count=len(diff.rule_updates),
            skipped_unknown_sid=[],
            skipped_no_index=True,
            iteration_diff=diff,
        )
        if not dry_run:
            _bump_state(result, full_case_id)
        return result

    # 4. fanout
    rule_verdicts, unknown_sids = fanout_to_rules(feedbacks, statement_index)

    # 5. 应用规律级更新（不写 log，本函数末尾统一写）
    diff = _apply_rule_verdicts(
        full_case_id, rule_verdicts, cfg=cfg, today=today, dry_run=dry_run
    )

    # 6. 落 log + snapshot
    if unknown_sids:
        diff.notes.append(
            f"忽略 {len(unknown_sids)} 个 statement_id（report 与 index 不匹配，"
            f"可能需重跑 render）：{','.join(unknown_sids[:3])}"
        )
    if not dry_run:
        append_iteration_log(diff)
        write_snapshot(diff)

    # 7. 计数器
    result = IngestResult(
        case_id=full_case_id,
        feedback_count=len(feedbacks),
        rule_count=len(rule_verdicts),
        skipped_unknown_sid=unknown_sids,
        iteration_diff=diff,
    )
    if not dry_run:
        _bump_state(result, full_case_id)

    return result


def _bump_state(result: IngestResult, case_id: str) -> None:
    """把当前案件计入完成反馈，并检测是否到 10 案触发点。"""
    state = IterationState.load()
    if case_id in state.completed_case_ids:
        # 同一案重复 ingest 不重复计数
        result.feedback_completed_count = state.feedback_completed_count
        result.iteration_seq = state.iteration_seq
        return
    state.feedback_completed_count += 1
    state.completed_case_ids.append(case_id)

    # 每 10 案触发一次（D8 锁定）
    if state.feedback_completed_count - state.last_iteration_at_count >= 10:
        state.iteration_seq += 1
        state.last_iteration_at_count = state.feedback_completed_count
        result.iteration_triggered = True
        result.iteration_seq = state.iteration_seq
    else:
        result.iteration_seq = state.iteration_seq

    result.feedback_completed_count = state.feedback_completed_count
    state.save()

    # v1.3 D8：完成反馈案达 10 整数倍 → 自动触发迭代调度
    # 失败不阻塞 ingest 主流程（warn-only），命理师仍能继续摄入下一案
    if result.iteration_triggered:
        try:
            from tools.iteration_report import run_iteration
            ir = run_iteration(seq=result.iteration_seq, dry_run=False)
            if ir.report_path:
                result.iteration_report_path = str(ir.report_path)
        except Exception as exc:  # noqa: BLE001
            # 把异常打到 iteration_diff.notes（如果存在），不抛
            if result.iteration_diff is not None:
                result.iteration_diff.notes.append(
                    f"[D8 warn-only] iteration_report 触发失败：{exc!r}"
                )


# ============================================================
# 六、CLI
# ============================================================

def _safe_print(text: str = "") -> None:
    """跨平台安全打印，避免 Windows cmd 的 GBK 编码被 emoji 阻断。"""
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode(sys.stdout.encoding or "utf-8", errors="replace").decode(
            sys.stdout.encoding or "utf-8", errors="replace"
        ))


def _print_human(result: IngestResult) -> None:
    _safe_print(f"\n[feedback_ingest] case_id={result.case_id}")
    _safe_print(f"  解析到 statement 反馈: {result.feedback_count} 条")
    _safe_print(f"  fanout 后涉及规律: {result.rule_count} 条")
    if result.skipped_no_index:
        _safe_print("  [WARN] statement_index.json 缺失或为空 → 已退回 v1.0 启发式路径")
    if result.skipped_unknown_sid:
        _safe_print(f"  [WARN] 忽略未知 sid: {len(result.skipped_unknown_sid)} 条 (前 3: "
                    f"{','.join(result.skipped_unknown_sid[:3])})")
    if result.iteration_diff:
        d = result.iteration_diff
        _safe_print(f"  规律更新: {len(d.rule_updates)} 条 / "
                    f"状态变更: {len(d.status_changes)} 条 / "
                    f"跨派扫描: {'是' if d.cross_school_triggered else '否'}")
    _safe_print(f"  累计完成反馈案: {result.feedback_completed_count}")
    _safe_print(f"  当前迭代序号 (iteration_seq): {result.iteration_seq:03d}")
    if result.iteration_triggered:
        _safe_print("\n  ** 已达 10 案整数倍 → iteration_report 已自动触发 **")
        if result.iteration_report_path:
            _safe_print(f"     报告: {result.iteration_report_path}")
        else:
            _safe_print("     [WARN] 报告写入失败，详见 iteration_diff.notes")
            _safe_print(f"     预期路径: META/iteration-report-{result.iteration_seq:03d}.md")


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="v1.3 D5 结构化反馈摄入：解析填好的 feedback.md → 应用规律级更新"
    )
    parser.add_argument("case_id", help="案例 ID 或前缀（如 C-2026-001）")
    parser.add_argument("--dry-run", action="store_true", help="不落盘 yaml / log / state")
    parser.add_argument("--json", action="store_true", help="以 JSON 格式输出结果")
    args = parser.parse_args(argv)

    try:
        result = ingest(args.case_id, dry_run=args.dry_run)
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

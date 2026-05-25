"""tools/batch_review.py · v1.3 D6 批量复盘工具

落地契约：
    plans/architecture-v1.3.md § 四 D6（批量工作流 — 复盘侧）
    plans/architecture-v1.3.md § 五 W2

工作流：
    1. 命理师对若干案例完成了过后反馈（feedback.md 已填好 [y]/[n]/[?]/[skip]）
    2. 运行 batch_review：
         python3 -m tools.batch_review            # 处理所有"待 ingest"案例
         python3 -m tools.batch_review --cases C-2026-001 C-2026-002
    3. 工具识别"待 ingest"标准：
         a. 案例目录存在 cases/{case_id}/feedback.md
         b. 该 case_id 不在 META/iteration-state.json::completed_case_ids 里
         c. （可选）feedback.md 中含 [S-...] [y/n/?] 至少 1 条标注（v1.3 路径）
    4. 对每案调 tools.feedback_ingest.ingest()
       feedback_ingest 内部已经处理：
         - statement_index.json 缺失 → 退回 v1.0 启发式
         - 完成案数 +1，每 10 案触发 iteration_seq
    5. 汇总：rule_updates 总数 / status_changes 总数 / 跨派扫描触发次数 /
            是否达到 10 案触发点

公开 API
--------
review(cases=None, *, dry_run=False) -> BatchReviewResult
    主入口

discover_pending() -> list[str]
    返回所有"有 feedback.md 但未 ingest"的 case_id
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import pathlib
import re
import sys
import traceback
from dataclasses import dataclass, field
from typing import Any, Optional

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
CASES_DIR = REPO_ROOT / "cases"
META_DIR = REPO_ROOT / "META"
ITERATION_STATE_FILE = META_DIR / "iteration-state.json"
BATCH_REVIEW_LOG = META_DIR / "batch-reviews.md"

CASE_DIR_RE = re.compile(r"^C-\d{4}-\d{3}-")


# ============================================================
# 一、扫描"待 ingest"案例
# ============================================================

def _load_completed_set() -> set[str]:
    """从 META/iteration-state.json 读 completed_case_ids。"""
    if not ITERATION_STATE_FILE.exists():
        return set()
    try:
        payload = json.loads(ITERATION_STATE_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, ValueError):
        return set()
    return set(payload.get("completed_case_ids", []))


def discover_pending(*, only_with_v13_annotations: bool = False) -> list[str]:
    """扫 cases/ 找所有"待 ingest"的 case_id。

    判定规则：
        a. 目录名匹配 ``C-YYYY-NNN-*``
        b. 目录下存在 ``feedback.md``
        c. case_id 不在 iteration-state.json 的 completed_case_ids 里
        d. （只在 only_with_v13_annotations=True 时）feedback.md 含 ``[S-...]`` 标注

    Returns:
        case_id 列表（按目录名排序）
    """
    if not CASES_DIR.exists():
        return []
    completed = _load_completed_set()
    out: list[str] = []
    sid_re = re.compile(r"\[S-[A-Za-z0-9_]+-[a-f0-9]{6}\]\s*\[(y|n|\?|skip)\]")

    for child in sorted(CASES_DIR.iterdir()):
        if not child.is_dir() or not CASE_DIR_RE.match(child.name):
            continue
        fb = child / "feedback.md"
        if not fb.exists():
            continue
        if child.name in completed:
            continue
        if only_with_v13_annotations:
            try:
                text = fb.read_text(encoding="utf-8")
            except OSError:
                continue
            if not sid_re.search(text):
                continue
        out.append(child.name)
    return out


# ============================================================
# 二、单案处理
# ============================================================

@dataclass
class ReviewedCase:
    case_id: str
    success: bool = False
    error_step: str = ""
    error_message: str = ""
    error_traceback: str = ""

    # 统计（来自 IngestResult / IterationDiff）
    feedback_count: int = 0           # statement-level 反馈条数（v1.3 路径）
    rule_count: int = 0               # 规律级别更新条数
    status_change_count: int = 0      # 升降级 / 漂移触发次数
    cross_school_triggered: bool = False
    iteration_triggered: bool = False  # 是否在该案触发了 iteration_seq +1
    iteration_seq: int = 0
    feedback_completed_count: int = 0
    used_legacy_path: bool = False    # True 则走的 v1.0 启发式路径

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "success": self.success,
            "error_step": self.error_step,
            "error_message": self.error_message,
            "feedback_count": self.feedback_count,
            "rule_count": self.rule_count,
            "status_change_count": self.status_change_count,
            "cross_school_triggered": self.cross_school_triggered,
            "iteration_triggered": self.iteration_triggered,
            "iteration_seq": self.iteration_seq,
            "feedback_completed_count": self.feedback_completed_count,
            "used_legacy_path": self.used_legacy_path,
        }


def _process_single(case_id: str, *, dry_run: bool) -> ReviewedCase:
    """对单案调 feedback_ingest.ingest()。"""
    rc = ReviewedCase(case_id=case_id)
    try:
        from tools.feedback_ingest import ingest
        result = ingest(case_id, dry_run=dry_run)
        rc.feedback_count = result.feedback_count
        rc.rule_count = result.rule_count
        rc.iteration_triggered = result.iteration_triggered
        rc.iteration_seq = result.iteration_seq
        rc.feedback_completed_count = result.feedback_completed_count
        rc.used_legacy_path = result.skipped_no_index
        if result.iteration_diff:
            d = result.iteration_diff
            rc.status_change_count = len(d.status_changes)
            rc.cross_school_triggered = d.cross_school_triggered
        rc.success = True
    except Exception as exc:  # noqa: BLE001
        rc.error_step = "feedback_ingest"
        rc.error_message = str(exc)
        rc.error_traceback = traceback.format_exc()
    return rc


# ============================================================
# 三、批次入口
# ============================================================

@dataclass
class BatchReviewResult:
    started_at: str = ""
    finished_at: str = ""
    cases: list[ReviewedCase] = field(default_factory=list)
    dry_run: bool = False

    @property
    def success_count(self) -> int:
        return sum(1 for c in self.cases if c.success)

    @property
    def failure_count(self) -> int:
        return sum(1 for c in self.cases if not c.success)

    @property
    def total_rule_updates(self) -> int:
        return sum(c.rule_count for c in self.cases if c.success)

    @property
    def total_status_changes(self) -> int:
        return sum(c.status_change_count for c in self.cases if c.success)

    @property
    def cross_school_count(self) -> int:
        return sum(1 for c in self.cases if c.cross_school_triggered)

    @property
    def iteration_triggered_count(self) -> int:
        return sum(1 for c in self.cases if c.iteration_triggered)

    @property
    def latest_iteration_seq(self) -> int:
        seqs = [c.iteration_seq for c in self.cases if c.success]
        return max(seqs) if seqs else 0

    @property
    def latest_feedback_completed(self) -> int:
        counts = [c.feedback_completed_count for c in self.cases if c.success]
        return max(counts) if counts else 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "dry_run": self.dry_run,
            "totals": {
                "input": len(self.cases),
                "success": self.success_count,
                "failure": self.failure_count,
                "rule_updates": self.total_rule_updates,
                "status_changes": self.total_status_changes,
                "cross_school_triggers": self.cross_school_count,
                "iteration_triggers": self.iteration_triggered_count,
            },
            "latest_iteration_seq": self.latest_iteration_seq,
            "latest_feedback_completed": self.latest_feedback_completed,
            "cases": [c.to_dict() for c in self.cases],
        }


def review(
    cases: Optional[list[str]] = None,
    *,
    only_with_v13_annotations: bool = False,
    dry_run: bool = False,
) -> BatchReviewResult:
    """批量复盘所有"待 ingest"案例。

    Args:
        cases: 显式指定 case_id 列表；None → 扫所有 pending
        only_with_v13_annotations: True 则仅处理含 [S-...] 标注的（D5 严格路径）
        dry_run: 不写规律 yaml / 不写 iteration_state

    Returns:
        BatchReviewResult
    """
    started = _dt.datetime.now().isoformat(timespec="seconds")
    target = (
        cases if cases is not None
        else discover_pending(only_with_v13_annotations=only_with_v13_annotations)
    )
    result = BatchReviewResult(started_at=started, dry_run=dry_run)

    for cid in target:
        rc = _process_single(cid, dry_run=dry_run)
        result.cases.append(rc)

    result.finished_at = _dt.datetime.now().isoformat(timespec="seconds")
    if not dry_run and result.cases:
        _append_review_log(result)
    return result


# ============================================================
# 四、复盘日志
# ============================================================

def _append_review_log(result: BatchReviewResult) -> None:
    META_DIR.mkdir(parents=True, exist_ok=True)
    if not BATCH_REVIEW_LOG.exists():
        BATCH_REVIEW_LOG.write_text(
            "# batch-reviews · 批量复盘历史\n\n"
            "> 由 `tools/batch_review.py` 维护。\n\n",
            encoding="utf-8",
        )

    lines: list[str] = []
    lines.append(f"\n## {result.started_at} → {result.finished_at}")
    lines.append("")
    lines.append(
        f"- 输入: {len(result.cases)} 案"
        f" / 成功: {result.success_count}"
        f" / 失败: {result.failure_count}"
        f" / dry_run: {result.dry_run}"
    )
    lines.append(f"- 累计 rule_updates: {result.total_rule_updates}")
    lines.append(f"- 累计 status_changes: {result.total_status_changes}")
    lines.append(f"- cross_school_scan 触发: {result.cross_school_count} 次")
    lines.append(
        f"- iteration_seq 触发: {result.iteration_triggered_count} 次 "
        f"(最新 seq={result.latest_iteration_seq:03d}, "
        f"完成反馈案累计={result.latest_feedback_completed})"
    )

    if result.cases:
        lines.append("")
        lines.append("| case_id | 路径 | sids | rules | status变 | cross-school | iteration触发 | 结果 |")
        lines.append("|---|---|---|---|---|---|---|---|")
        for c in result.cases:
            path = "v1.0 启发式" if c.used_legacy_path else "v1.3 标注"
            cs = "✓" if c.cross_school_triggered else "—"
            it = f"✓ seq={c.iteration_seq:03d}" if c.iteration_triggered else "—"
            res = "✅" if c.success else f"❌ {c.error_message[:40]}"
            lines.append(
                f"| {c.case_id} | {path} | {c.feedback_count} | {c.rule_count} | "
                f"{c.status_change_count} | {cs} | {it} | {res} |"
            )

    if result.iteration_triggered_count > 0:
        lines.append("")
        lines.append(
            f"> ⚠️ 本批次触发了 {result.iteration_triggered_count} 次 iteration_seq +1，"
            f"对应 META/iteration-report-{result.latest_iteration_seq:03d}.md "
            f"(W3 实现后自动产出)。"
        )

    with BATCH_REVIEW_LOG.open("a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


# ============================================================
# 五、CLI
# ============================================================

def _print_human(result: BatchReviewResult) -> None:
    print(f"\n[batch_review] {result.started_at} → {result.finished_at}"
          f" (dry_run={result.dry_run})")
    print(f"  输入: {len(result.cases)} 案")
    print(f"  ✅ 成功: {result.success_count}")
    print(f"  ❌ 失败: {result.failure_count}")
    print()
    print(f"  累计规律更新: {result.total_rule_updates}")
    print(f"  累计状态变更: {result.total_status_changes}")
    print(f"  跨派扫描触发: {result.cross_school_count} 次")
    print(f"  iteration_seq 触发: {result.iteration_triggered_count} 次"
          f" (最新 seq={result.latest_iteration_seq:03d},"
          f" 完成反馈案累计={result.latest_feedback_completed})")
    print()
    for c in result.cases:
        if not c.success:
            print(f"  ❌ {c.case_id}: [{c.error_step}] {c.error_message[:80]}")
            continue
        path = "v1.0" if c.used_legacy_path else "v1.3"
        trigger = " 🔥 触发迭代" if c.iteration_triggered else ""
        print(
            f"  ✅ {c.case_id} [{path}]: "
            f"{c.feedback_count} sid → {c.rule_count} 规律 "
            f"(status变 {c.status_change_count}){trigger}"
        )

    if result.iteration_triggered_count > 0:
        print(
            f"\n  🔥 本批触发 {result.iteration_triggered_count} 次迭代点；"
            f"W3 上线后将自动产出 META/iteration-report-"
            f"{result.latest_iteration_seq:03d}.md"
        )


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="v1.3 D6 批量复盘：扫所有有反馈未 ingest 的案 → "
                    "调 feedback_ingest 一条龙",
    )
    parser.add_argument(
        "--cases", nargs="*", default=None,
        help="显式指定 case_id 列表；不指定则扫所有 pending"
    )
    parser.add_argument(
        "--strict-v13", action="store_true",
        help="只处理含 [S-...] v1.3 标注的反馈（跳过纯 v1.0 旧格式）"
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="不写规律 yaml / 不更新 iteration-state")
    parser.add_argument("--json", action="store_true", help="JSON 输出")
    args = parser.parse_args(argv)

    result = review(
        cases=args.cases,
        only_with_v13_annotations=args.strict_v13,
        dry_run=args.dry_run,
    )

    if args.json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    else:
        _print_human(result)
    return 0 if result.failure_count == 0 else 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())

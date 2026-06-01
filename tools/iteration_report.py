"""tools/iteration_report.py · v1.3 D8 自迭代调度器 + 报告产出

落地契约：
    plans/architecture-v1.3.md § 四 D8'（每 10 完成反馈案触发）

调度顺序：
    1. 读 META/iteration-state.json 取本周期 case_ids
    2. mine_all（boundary_miner）— 扫所有规律找候选边界
    3. veto_all（veto_miner，传入 boundary 结果，避免重复挖掘）— 兜底停用
    4. 全量扫规律：drift_detect / 升降级状态变化已经在 _apply_rule_verdicts
       中按案触发，这里**只读取**最近变更（不重复触发，避免抖动）
    5. 收集 cross_school_scan 摘要（已由 feedback_ingest 调用，读 META 文件）
    6. 输出 META/iteration-report-{NNN}.md

为什么不重新跑 cross_school / drift / lifecycle：
    这些在 _apply_rule_verdicts 中**每案**已经触发，
    iteration_report 只做"周期性汇总"——读最近 10 案的累积变化，
    避免重复触发引起规律状态跳变。

公开 API：
    run_iteration(seq=None, *, dry_run=False) -> IterationReportResult

CLI：
    python3 -m tools.iteration_report          # 自动从 state 读 seq 跑
    python3 -m tools.iteration_report --seq 2  # 指定 seq
    python3 -m tools.iteration_report --dry-run

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
from typing import Any, Optional

from engine.application.timing import PipelineTiming
from tools.boundary_miner import BoundaryMineResult, mine_all
from tools.rule_lifecycle import LifecycleConfig, list_rule_ids, load_rule
from tools.veto_miner import VetoResult, veto_all

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
META_DIR = REPO_ROOT / "META"
ITERATION_STATE_FILE = META_DIR / "iteration-state.json"
CONFLICT_TRENDS = META_DIR / "conflict-trends.md"
ITERATION_LOG = META_DIR / "iteration-log.md"
RULE_CHANGELOG = META_DIR / "rule-changelog.md"


# ============================================================
# 一、结果数据结构
# ============================================================

@dataclass
class IterationReportResult:
    seq: int = 0
    started_at: str = ""
    finished_at: str = ""
    feedback_completed_count: int = 0
    cycle_case_ids: list[str] = field(default_factory=list)

    # 各调度步统计
    boundary_results: dict[str, BoundaryMineResult] = field(default_factory=dict)
    veto_results: dict[str, VetoResult] = field(default_factory=dict)
    rules_with_accepted_boundaries: list[str] = field(default_factory=list)
    rules_vetoed: list[str] = field(default_factory=list)

    # 摘要（来自其他 META 文件，非本工具直接驱动）
    upgrades_in_cycle: list[str] = field(default_factory=list)    # 升级
    downgrades_in_cycle: list[str] = field(default_factory=list)  # 降级（含漂移）
    cross_school_conflicts: int = 0

    # 输出
    report_path: Optional[pathlib.Path] = None
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "seq": self.seq,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "feedback_completed_count": self.feedback_completed_count,
            "cycle_case_ids": self.cycle_case_ids,
            "totals": {
                "rules_scanned_for_boundary": len(self.boundary_results),
                "rules_with_accepted_boundaries": len(self.rules_with_accepted_boundaries),
                "rules_vetoed": len(self.rules_vetoed),
                "upgrades_in_cycle": len(self.upgrades_in_cycle),
                "downgrades_in_cycle": len(self.downgrades_in_cycle),
                "cross_school_conflicts": self.cross_school_conflicts,
            },
            "rules_with_accepted_boundaries": self.rules_with_accepted_boundaries,
            "rules_vetoed": self.rules_vetoed,
            "upgrades_in_cycle": self.upgrades_in_cycle,
            "downgrades_in_cycle": self.downgrades_in_cycle,
            "report_path": str(self.report_path) if self.report_path else None,
            "notes": self.notes,
        }


# ============================================================
# 二、辅助：读 iteration-state.json
# ============================================================

def _load_state() -> dict[str, Any]:
    if not ITERATION_STATE_FILE.exists():
        return {
            "feedback_completed_count": 0,
            "last_iteration_at_count": 0,
            "iteration_seq": 0,
            "completed_case_ids": [],
        }
    try:
        return json.loads(ITERATION_STATE_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, ValueError):
        return {
            "feedback_completed_count": 0,
            "last_iteration_at_count": 0,
            "iteration_seq": 0,
            "completed_case_ids": [],
        }


# ============================================================
# 三、辅助：从已有日志提取本周期变更
# ============================================================

# iteration-log.md 中查"## YYYY-MM-DD HH:MM · ingest C-XXX"块；
# Status Changes 段格式："- {rule_id}: {from} → {to}  ({reason})"
_INGEST_HEADER_RE = re.compile(r"^## (\d{4}-\d{2}-\d{2} \d{2}:\d{2}) · ingest (\S+)\s*$")
_STATUS_CHANGE_RE = re.compile(
    r"^- ([\w-]+): (\S+) → (\S+)\s+\((.+)\)\s*$"
)


def _scan_recent_status_changes(
    cycle_case_ids: list[str],
) -> tuple[list[str], list[str]]:
    """从 META/iteration-log.md 抽出本周期 case 触发的升降级。

    Returns: (upgrades, downgrades) — 每条形如 "M2-Y-068: candidate → confirmed (auto-upgrade ...)"
    """
    upgrades: list[str] = []
    downgrades: list[str] = []
    if not ITERATION_LOG.exists():
        return upgrades, downgrades

    text = ITERATION_LOG.read_text(encoding="utf-8")
    cycle_set = set(cycle_case_ids)

    # 切块：每个 "## ... ingest CASE_ID" 至下一个 "## " 之间
    blocks = re.split(r"^## ", text, flags=re.MULTILINE)
    for blk in blocks:
        first_line = blk.split("\n", 1)[0] if blk else ""
        m = re.match(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}) · ingest (\S+)", first_line)
        if not m:
            continue
        case_id = m.group(2)
        if case_id not in cycle_set:
            continue
        # 在块里找 "### Status Changes" 段
        if "### Status Changes" not in blk:
            continue
        sc_block = blk.split("### Status Changes", 1)[1]
        for line in sc_block.splitlines():
            sc = _STATUS_CHANGE_RE.match(line.strip())
            if not sc:
                if line.startswith("###"):
                    break  # 进入下一个三级标题，停止
                continue
            rid, frm, to_, reason = sc.groups()
            entry = f"{rid}: {frm} → {to_} ({reason})"
            if "upgrade" in reason.lower() or to_ in ("candidate", "confirmed"):
                upgrades.append(entry)
            elif to_ in ("flagged_for_review", "deprecated"):
                downgrades.append(entry)
    return upgrades, downgrades


def _count_recent_conflicts(cycle_case_ids: list[str]) -> int:
    """从 META/conflict-trends.md 数本周期触发的跨派冲突。

    简化策略：扫文件最近修改时间附近的 conflict 条数。
    更准确的实现需要 conflict_scan 在写日志时打 trigger_case 标记。
    本期返回 0 当占位，等 conflict-trends 格式稳定后再加。
    """
    # MVP：只检查 conflict-trends 是否存在且非空
    if not CONFLICT_TRENDS.exists():
        return 0
    text = CONFLICT_TRENDS.read_text(encoding="utf-8")
    # 数文件中含 cycle case_id 的行
    return sum(
        1 for cid in cycle_case_ids if cid in text
    )


# ============================================================
# 四、主入口 run_iteration
# ============================================================

def run_iteration(
    *,
    seq: Optional[int] = None,
    cfg: Optional[LifecycleConfig] = None,
    dry_run: bool = False,
) -> IterationReportResult:
    """跑一次自迭代调度 + 输出 META/iteration-report-NNN.md。

    Args:
        seq:     迭代序号；None 则从 state 读
        cfg:     LifecycleConfig
        dry_run: True 不写规律 yaml / 不写报告

    Returns:
        IterationReportResult
    """
    started_at = _dt.datetime.now().isoformat(timespec="seconds")
    state = _load_state()

    if seq is None:
        seq = int(state.get("iteration_seq", 0)) or 1

    completed = list(state.get("completed_case_ids", []))
    last_at = int(state.get("last_iteration_at_count", 0))
    # 本周期 = 最近 10 案（last_at - 10 到 last_at）
    start_idx = max(0, last_at - 10)
    cycle_case_ids = completed[start_idx:last_at]

    result = IterationReportResult(
        seq=seq,
        started_at=started_at,
        feedback_completed_count=int(state.get("feedback_completed_count", 0)),
        cycle_case_ids=cycle_case_ids,
    )

    timing = PipelineTiming()
    timing_run_id = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    # Step 1: boundary_miner 全量扫描
    try:
        with timing.step("boundary_miner"):
            boundary_results = mine_all(cfg=cfg, dry_run=dry_run)
        result.boundary_results = boundary_results
        for rid, br in boundary_results.items():
            if br.accepted:
                result.rules_with_accepted_boundaries.append(rid)
    except Exception as exc:  # noqa: BLE001
        result.notes.append(f"boundary_miner 异常: {exc!r}")

    # Step 2: veto_miner（传入 boundary 结果避免重复挖掘）
    try:
        with timing.step("veto_miner"):
            veto_results = veto_all(
                boundary_results=result.boundary_results,
                cfg=cfg, dry_run=dry_run,
            )
        result.veto_results = veto_results
        for rid, vr in veto_results.items():
            if vr.vetoed:
                result.rules_vetoed.append(rid)
    except Exception as exc:  # noqa: BLE001
        result.notes.append(f"veto_miner 异常: {exc!r}")

    # Step 3: 读取本周期状态变更（不重复触发，仅汇总）
    try:
        with timing.step("scan_status_changes"):
            ups, downs = _scan_recent_status_changes(cycle_case_ids)
        result.upgrades_in_cycle = ups
        result.downgrades_in_cycle = downs
    except Exception as exc:  # noqa: BLE001
        result.notes.append(f"扫 iteration-log.md 异常: {exc!r}")

    # Step 4: cross-school 冲突计数
    try:
        with timing.step("cross_school_summary"):
            result.cross_school_conflicts = _count_recent_conflicts(cycle_case_ids)
    except Exception as exc:  # noqa: BLE001
        result.notes.append(f"扫 conflict-trends.md 异常: {exc!r}")

    result.finished_at = _dt.datetime.now().isoformat(timespec="seconds")

    # Step 5: 写报告
    if not dry_run:
        with timing.step("write_report"):
            result.report_path = _write_report(result)
        timing.write_meta_timing(
            META_DIR,
            timing_type="iteration_report",
            run_id=f"{timing_run_id}-{seq:03d}",
            extra={
                "seq": seq,
                "feedback_completed_count": result.feedback_completed_count,
                "cycle_case_count": len(result.cycle_case_ids),
                "boundary_result_count": len(result.boundary_results),
                "veto_result_count": len(result.veto_results),
                "rules_with_accepted_boundaries": len(result.rules_with_accepted_boundaries),
                "rules_vetoed": len(result.rules_vetoed),
                "dry_run": dry_run,
            },
        )

    return result


# ============================================================
# 五、Markdown 报告写入
# ============================================================

def _write_report(result: IterationReportResult) -> pathlib.Path:
    META_DIR.mkdir(parents=True, exist_ok=True)
    fname = f"iteration-report-{result.seq:03d}.md"
    path = META_DIR / fname

    lines: list[str] = []
    lines.append(f"# Iteration Report #{result.seq:03d}")
    lines.append("")
    lines.append(f"> 由 `tools/iteration_report.py` 自动生成。")
    lines.append(
        f"> 触发：每 10 完成反馈案 (D8 锁定)；当前累计 "
        f"{result.feedback_completed_count} 案。"
    )
    lines.append("")
    lines.append(f"- **started_at**：{result.started_at}")
    lines.append(f"- **finished_at**：{result.finished_at}")
    lines.append(f"- **本周期 case_ids ({len(result.cycle_case_ids)} 案)**：")
    lines.append("")
    for cid in result.cycle_case_ids:
        lines.append(f"  - `{cid}`")
    lines.append("")

    # 一、规律状态变化（来自 _apply_rule_verdicts 已触发的）
    lines.append("---")
    lines.append("")
    lines.append("## 一、本周期规律状态变化")
    lines.append("")
    lines.append(
        f"- ⬆️ 升级：{len(result.upgrades_in_cycle)} 条"
        f" / ⬇️ 降级：{len(result.downgrades_in_cycle)} 条"
    )
    if result.upgrades_in_cycle:
        lines.append("")
        lines.append("### 升级")
        lines.append("")
        for u in result.upgrades_in_cycle:
            lines.append(f"- {u}")
    if result.downgrades_in_cycle:
        lines.append("")
        lines.append("### 降级 / 漂移")
        lines.append("")
        for d in result.downgrades_in_cycle:
            lines.append(f"- {d}")
    lines.append("")

    # 二、自动挖出的边界（D3）
    lines.append("---")
    lines.append("")
    lines.append("## 二、自动挖掘的边界（D3 boundary_miner）")
    lines.append("")
    if result.rules_with_accepted_boundaries:
        lines.append(
            f"- 找到 {len(result.rules_with_accepted_boundaries)} 条规律有显著边界候选"
        )
        lines.append("")
        lines.append("| rule_id | 接受边界 | 拒绝候选 | 备注 |")
        lines.append("|---|---|---|---|")
        for rid in result.rules_with_accepted_boundaries:
            br = result.boundary_results[rid]
            top_acc = br.accepted[0] if br.accepted else None
            if top_acc:
                top = (
                    f"`NOT({top_acc.feature})` p={top_acc.p_value:.3f} "
                    f"lift={top_acc.lift:.2f} hit_rate "
                    f"{top_acc.old_hit_rate:.2f}→{top_acc.new_hit_rate_after_boundary:.2f}"
                )
            else:
                top = "—"
            lines.append(
                f"| {rid} | {top} | {len(br.rejected)} | "
                f"详见 META/auto-mined-boundaries.md |"
            )
    else:
        lines.append("- 本周期无显著边界候选（所有规律 miss<5 或 p/lift 不达标）")

    skipped_for_low_miss = sum(
        1 for br in result.boundary_results.values()
        if br.skipped and "min_miss" in br.skip_reason
    )
    if skipped_for_low_miss:
        lines.append("")
        lines.append(
            f"> {skipped_for_low_miss} 条规律因 misses<5 跳过挖掘（数据不足，等更多反馈）"
        )
    lines.append("")

    # 三、自动停用规律（D4）
    lines.append("---")
    lines.append("")
    lines.append("## 三、自动停用的规律（D4 veto_miner）")
    lines.append("")
    if result.rules_vetoed:
        lines.append(f"- 本周期停用 {len(result.rules_vetoed)} 条")
        lines.append("")
        lines.append("| rule_id | 派 | n | hits/miss | posterior 旧→新 | 复活方式 |")
        lines.append("|---|---|---|---|---|---|")
        for rid in result.rules_vetoed:
            vr = result.veto_results[rid]
            lines.append(
                f"| {rid} | {vr.school} | {vr.n} | {vr.hits}/{vr.misses} | "
                f"{vr.posterior_before:.3f} → 0.0 | "
                f"详见 META/auto-vetoed-rules.md |"
            )
        lines.append("")
        lines.append(
            "> 命理师可手动复活：编辑 `theory/{school}/index.yaml` 把 `status` 改回 "
            "`candidate`/`confirmed`，删除 `confidence_cache`。"
        )
    else:
        lines.append("- 本周期无规律被自动停用（满足 D4 全部触发条件的规律为 0）")
    lines.append("")

    # 四、跨派冲突
    lines.append("---")
    lines.append("")
    lines.append("## 四、跨派一致性")
    lines.append("")
    lines.append(
        f"- 本周期相关冲突计数：{result.cross_school_conflicts}"
        f"（来源 META/conflict-trends.md）"
    )
    lines.append("")

    # 五、漂移告警 — 命理师唯一需要关注的
    drift_alerts = [
        d for d in result.downgrades_in_cycle
        if "drift" in d.lower()
    ]
    lines.append("---")
    lines.append("")
    lines.append("## 五、⚠️ 漂移告警（命理师重点关注）")
    lines.append("")
    if drift_alerts:
        lines.append(
            f"- 本周期触发漂移 **{len(drift_alerts)}** 条 — 这些规律最近 5 案命中率偏低，"
            f"建议人工瞄一眼是否需要补反馈或调整规律："
        )
        lines.append("")
        for d in drift_alerts:
            lines.append(f"- ⚠️ {d}")
    else:
        lines.append("- ✅ 本周期无漂移告警")
    lines.append("")

    # Notes
    if result.notes:
        lines.append("---")
        lines.append("")
        lines.append("## 调度执行备注")
        lines.append("")
        for n in result.notes:
            lines.append(f"- {n}")
        lines.append("")

    # 全文落盘
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


# ============================================================
# 六、CLI
# ============================================================

def _print_human(result: IterationReportResult) -> None:
    print(f"\n[iteration_report] seq={result.seq:03d}"
          f" ({result.started_at} → {result.finished_at})")
    print(f"  本周期 case_ids: {len(result.cycle_case_ids)} 案")
    print(f"  累计完成反馈: {result.feedback_completed_count}")
    print()
    print(f"  ⬆️ 升级: {len(result.upgrades_in_cycle)}"
          f" / ⬇️ 降级: {len(result.downgrades_in_cycle)}")
    print(f"  🆕 新挖边界: {len(result.rules_with_accepted_boundaries)} 条规律")
    print(f"  🚫 自动停用: {len(result.rules_vetoed)} 条规律")
    print(f"  ⚔️ 跨派冲突相关: {result.cross_school_conflicts}")

    drift = [d for d in result.downgrades_in_cycle if "drift" in d.lower()]
    if drift:
        print(f"\n  ⚠️ 漂移告警 {len(drift)} 条（命理师关注）：")
        for d in drift[:5]:
            print(f"     · {d}")

    if result.report_path:
        print(f"\n  📄 报告: {result.report_path}")


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="v1.3 D8 自迭代调度器：每 10 完成反馈案触发，"
                    "调 boundary_miner + veto_miner + 汇总报告"
    )
    parser.add_argument("--seq", type=int, default=None,
                        help="迭代序号；不指定从 META/iteration-state.json 读")
    parser.add_argument("--dry-run", action="store_true",
                        help="不修改规律 yaml / 不写报告")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    result = run_iteration(seq=args.seq, dry_run=args.dry_run)

    if args.json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    else:
        _print_human(result)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())

"""tools/batch_intake.py · 批量入库工具

落地契约：
    plans/architecture-v1.3.md § 四 D6（批量工作流）
    plans/architecture-v1.3.md § 五 W2（密集注入开跑）

工作流：
    1. 命理师把待分析的 input.md 文件丢进 cases/inbox/
       支持两种布局：
         a. cases/inbox/{name}.md            → 单文件
         b. cases/inbox/{name}/input.md      → 子目录
    2. 运行 batch_intake：
         python3 -m tools.batch_intake               # 处理 inbox 全部
         python3 -m tools.batch_intake --files a.md b.md  # 仅处理指定
    3. 每个 input.md 走以下流水线：
         a. preflight.parse() 校验 + 拿 case_id（含干支后缀）
         b. 自动建 cases/{case_id}/ 目录
         c. 把 input.md 移入（命理师可对照）
         d. 跑 engine.pipeline 完整四派分析
         e. render_from_output 产出唯一标准报告
         f. extract_predictions 抽 ★4+ 应期 + 事件签名（D7）
         g. 索引落 cases/{case_id}/statement_index.json（D1）
    4. 单案失败不阻塞批次（落 META/batch-errors.log）
    5. 汇总输出统计：成功 N / 失败 M / 跳过 K（已存在的 case）

公开 API
--------
batch(files=None, *, dry_run=False) -> BatchIntakeResult
    主入口

discover_inbox() -> list[Path]
    扫描 cases/inbox/ 找所有候选 input.md

注：本工具的 pipeline 调用部分依赖 engine.pipeline + PyYAML。
    沙箱 INTEGRATIONS_ONLY 模式下无法跑完整链路；
    但 discover_inbox / move_to_case / 错误聚合 等结构性能力可独立验证。
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import pathlib
import shutil
import sys
import traceback
from dataclasses import dataclass, field
from typing import Any, Optional

from engine.application.timing import PipelineTiming

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
CASES_DIR = REPO_ROOT / "cases"
INBOX_DIR = CASES_DIR / "inbox"
META_DIR = REPO_ROOT / "META"
BATCH_ERROR_LOG = META_DIR / "batch-errors.log"
BATCH_RUN_LOG = META_DIR / "batch-runs.md"


# ============================================================
# 一、扫描 inbox
# ============================================================

def discover_inbox(inbox_dir: pathlib.Path = INBOX_DIR) -> list[pathlib.Path]:
    """扫 cases/inbox/ 找所有候选 input.md。

    支持两种布局：
      cases/inbox/foo.md            → 直接是 input.md
      cases/inbox/foo/input.md      → 子目录里的 input.md
    """
    out: list[pathlib.Path] = []
    if not inbox_dir.exists():
        return out
    for child in sorted(inbox_dir.iterdir()):
        if child.is_file() and child.suffix == ".md":
            out.append(child)
        elif child.is_dir():
            sub_input = child / "input.md"
            if sub_input.exists():
                out.append(sub_input)
    return out


# ============================================================
# 二、case 目录创建 + 文件移动
# ============================================================

def _move_to_case_dir(input_path: pathlib.Path, case_id: str) -> pathlib.Path:
    """把 inbox 的 input.md 移到 cases/{case_id}/input.md。

    若目标目录已存在 input.md → 不覆盖，抛 FileExistsError 让 caller 决策。
    """
    case_dir = CASES_DIR / case_id
    case_dir.mkdir(parents=True, exist_ok=True)
    target = case_dir / "input.md"
    if target.exists():
        raise FileExistsError(
            f"目标 input.md 已存在: {target}（说明该 case 已立案）"
        )
    shutil.move(str(input_path), str(target))
    # 如果原文件位于子目录里（cases/inbox/foo/input.md），把整个子目录清干净
    parent = input_path.parent
    if parent != INBOX_DIR and parent.exists() and not any(parent.iterdir()):
        parent.rmdir()
    return target


# ============================================================
# 三、单案处理（pipeline 调度）
# ============================================================

@dataclass
class CaseResult:
    source_path: pathlib.Path
    case_id: Optional[str] = None
    case_dir: Optional[pathlib.Path] = None
    success: bool = False
    skipped: bool = False
    skip_reason: str = ""
    error_step: str = ""           # preflight / move / pipeline / render / extract / index
    error_message: str = ""
    error_traceback: str = ""
    report_path: Optional[pathlib.Path] = None
    predictions_written: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": str(self.source_path),
            "case_id": self.case_id,
            "case_dir": str(self.case_dir) if self.case_dir else None,
            "success": self.success,
            "skipped": self.skipped,
            "skip_reason": self.skip_reason,
            "error_step": self.error_step,
            "error_message": self.error_message,
            "report_path": str(self.report_path) if self.report_path else None,
            "predictions_written": self.predictions_written,
        }


def _process_single(input_path: pathlib.Path, *, dry_run: bool) -> CaseResult:
    """处理一份 inbox 中的 input.md。"""
    result = CaseResult(source_path=input_path)

    # ── Step 1: preflight ────────────────────────────────────
    try:
        from tools.preflight import parse as preflight_parse
        cases_index = CASES_DIR / "cases-index.md"
        parsed = preflight_parse(
            input_path,
            cases_index_path=cases_index if cases_index.exists() else None,
        )
        result.case_id = parsed.case_id
    except Exception as exc:  # noqa: BLE001
        result.error_step = "preflight"
        result.error_message = str(exc)
        result.error_traceback = traceback.format_exc()
        return result

    # ── Step 2: 检查 case 是否已存在 ─────────────────────────
    target_dir = CASES_DIR / parsed.case_id
    if target_dir.exists() and (target_dir / "input.md").exists():
        result.case_dir = target_dir
        result.skipped = True
        result.skip_reason = "case 已存在（cases/{case_id}/input.md 已就位）"
        return result

    # ── Step 3: 移动 input.md → cases/{case_id}/input.md ─────
    if not dry_run:
        try:
            new_input = _move_to_case_dir(input_path, parsed.case_id)
        except Exception as exc:  # noqa: BLE001
            result.error_step = "move"
            result.error_message = str(exc)
            result.error_traceback = traceback.format_exc()
            return result
        result.case_dir = target_dir
    else:
        new_input = input_path
        result.case_dir = target_dir

    # ── Step 4: 跑 pipeline ─────────────────────────────────
    try:
        from engine.pipeline import run_pipeline  # type: ignore[attr-defined]
        analysis_output = run_pipeline(parsed)
    except Exception as exc:  # noqa: BLE001
        result.error_step = "pipeline"
        result.error_message = str(exc)
        result.error_traceback = traceback.format_exc()
        return result

    # ── Step 5: render 唯一标准报告 ─────────────────────────
    try:
        from tools.render_report import render_from_output  # noqa: F401
    except ImportError as exc:
        result.error_step = "render_import"
        result.error_message = str(exc)
        result.error_traceback = traceback.format_exc()
        return result

    reports_dir = REPO_ROOT / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    try:
        from tools.render_report import render_from_output as _render
        report_md = _render(analysis_output, variant="standard", lint_before=True)
        if not dry_run:
            report_path = reports_dir / f"{parsed.case_id}-analyst-report.md"
            report_path.write_text(report_md, encoding="utf-8")
            result.report_path = report_path
    except Exception as exc:  # noqa: BLE001
        result.error_step = "render"
        result.error_message = str(exc)
        result.error_traceback = traceback.format_exc()
        return result

    # ── Step 6: 抽 ★4+ 应期 + 事件签名 ─────────────────────
    try:
        from tools.extract_predictions import extract_for_case
        if not dry_run:
            written = extract_for_case(parsed.case_id)
            result.predictions_written = len(written)
    except Exception as exc:  # noqa: BLE001
        # 应期抽取失败不应阻塞 ingest，登记 warn 但不算 fail
        result.error_step = "extract_predictions (warn-only)"
        result.error_message = str(exc)
        result.error_traceback = traceback.format_exc()
        # success 仍设 True
        result.success = True
        return result

    result.success = True
    return result


# ============================================================
# 四、批次入口
# ============================================================

@dataclass
class BatchIntakeResult:
    started_at: str = ""
    finished_at: str = ""
    cases: list[CaseResult] = field(default_factory=list)
    dry_run: bool = False

    @property
    def success_count(self) -> int:
        return sum(1 for c in self.cases if c.success and not c.skipped)

    @property
    def failure_count(self) -> int:
        return sum(1 for c in self.cases if not c.success and not c.skipped)

    @property
    def skip_count(self) -> int:
        return sum(1 for c in self.cases if c.skipped)

    def to_dict(self) -> dict[str, Any]:
        return {
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "dry_run": self.dry_run,
            "totals": {
                "input": len(self.cases),
                "success": self.success_count,
                "failure": self.failure_count,
                "skipped": self.skip_count,
            },
            "cases": [c.to_dict() for c in self.cases],
        }


def batch(
    files: Optional[list[pathlib.Path]] = None,
    *,
    dry_run: bool = False,
) -> BatchIntakeResult:
    """批量处理 inbox 中所有 input.md。

    Args:
        files:    显式指定文件列表；None → 扫 cases/inbox/
        dry_run:  True 则不移文件 / 不写报告 / 不抽预测

    Returns:
        BatchIntakeResult（含每案结果 + 汇总）
    """
    started = _dt.datetime.now().isoformat(timespec="seconds")
    run_id = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    timing = PipelineTiming()
    with timing.step("discover"):
        inputs = files if files is not None else discover_inbox()
    result = BatchIntakeResult(started_at=started, dry_run=dry_run)

    for inp in inputs:
        with timing.step("process_single"):
            cr = _process_single(inp, dry_run=dry_run)
        result.cases.append(cr)
        # 失败立即写错误日志（每案独立写避免批次崩溃丢日志）
        if not cr.success and not cr.skipped and not dry_run:
            _append_error_log(cr)

    result.finished_at = _dt.datetime.now().isoformat(timespec="seconds")
    if not dry_run and result.cases:
        _append_run_log(result)
        timing.write_meta_timing(
            META_DIR,
            timing_type="batch_intake",
            run_id=run_id,
            extra={
                "input_count": len(result.cases),
                "success_count": result.success_count,
                "failure_count": result.failure_count,
                "skip_count": result.skip_count,
                "dry_run": result.dry_run,
            },
        )
    return result


# ============================================================
# 五、错误聚合 + 运行日志
# ============================================================

def _append_error_log(case: CaseResult) -> None:
    """单案失败时追加到 META/batch-errors.log（plain text，便于 grep）。"""
    META_DIR.mkdir(parents=True, exist_ok=True)
    ts = _dt.datetime.now().isoformat(timespec="seconds")
    block = (
        f"\n---\n"
        f"[{ts}] STEP={case.error_step} CASE={case.case_id or '?'}\n"
        f"SOURCE: {case.source_path}\n"
        f"ERROR: {case.error_message}\n"
        f"\nTRACEBACK:\n{case.error_traceback}\n"
    )
    with BATCH_ERROR_LOG.open("a", encoding="utf-8") as f:
        f.write(block)


def _append_run_log(result: BatchIntakeResult) -> None:
    """每次 batch 跑完后写一段 markdown 摘要到 META/batch-runs.md。"""
    META_DIR.mkdir(parents=True, exist_ok=True)
    if not BATCH_RUN_LOG.exists():
        BATCH_RUN_LOG.write_text(
            "# batch-runs · 批量入库历史\n\n"
            "> 由 `tools/batch_intake.py` 维护。\n\n",
            encoding="utf-8",
        )

    lines: list[str] = []
    lines.append(f"\n## {result.started_at} → {result.finished_at}")
    lines.append("")
    lines.append(
        f"- 输入: {len(result.cases)} 案"
        f" / 成功: {result.success_count}"
        f" / 失败: {result.failure_count}"
        f" / 跳过: {result.skip_count}"
        f" / dry_run: {result.dry_run}"
    )
    if result.cases:
        lines.append("")
        lines.append("| source | case_id | 结果 | 报告 | 应期 | 备注 |")
        lines.append("|---|---|---|---|---|---|")
        for c in result.cases:
            if c.skipped:
                state = f"⏭️ skip ({c.skip_reason})"
            elif c.success:
                state = "✅"
            else:
                state = f"❌ {c.error_step}: {c.error_message[:60]}"
            reports = f"`{c.report_path.name}`" if c.report_path else "—"
            lines.append(
                f"| `{c.source_path.name}` | {c.case_id or '—'} | {state} | "
                f"{reports} | {c.predictions_written} | {c.error_message[:50] or '—'} |"
            )

    with BATCH_RUN_LOG.open("a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


# ============================================================
# 六、CLI
# ============================================================

def _print_human(result: BatchIntakeResult) -> None:
    print(f"\n[batch_intake] {result.started_at} → {result.finished_at}"
          f" (dry_run={result.dry_run})")
    print(f"  输入: {len(result.cases)} 案")
    print(f"  ✅ 成功: {result.success_count}")
    print(f"  ❌ 失败: {result.failure_count}")
    print(f"  ⏭️  跳过: {result.skip_count}")
    print()
    for c in result.cases:
        if c.skipped:
            print(f"  ⏭️  {c.source_path.name} → {c.case_id or '?'}: {c.skip_reason}")
        elif c.success:
            preds = f" + {c.predictions_written} preds" if c.predictions_written else ""
            print(f"  ✅ {c.source_path.name} → {c.case_id}{preds}")
        else:
            print(f"  ❌ {c.source_path.name}: [{c.error_step}] {c.error_message[:80]}")
    if result.failure_count > 0 and not result.dry_run:
        print(f"\n  ⚠️  失败详情见 {BATCH_ERROR_LOG}")


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="批量入库：扫 cases/inbox/*.md → 流水线 → 唯一标准报告 + 应期",
    )
    parser.add_argument(
        "--files", nargs="*", default=None,
        help="显式指定 input.md 文件列表；不指定则扫 cases/inbox/"
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="不移文件 / 不写报告 / 不抽预测")
    parser.add_argument("--json", action="store_true", help="JSON 输出")
    args = parser.parse_args(argv)

    files = (
        [pathlib.Path(f) for f in args.files] if args.files else None
    )
    result = batch(files=files, dry_run=args.dry_run)

    if args.json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    else:
        _print_human(result)
    return 0 if result.failure_count == 0 else 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())

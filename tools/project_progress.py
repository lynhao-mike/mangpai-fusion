"""项目进度状态源的校验、计算与文本仪表盘生成器。

机器状态源为 ``progress/PROJECT_PROGRESS.json``。本工具按显式任务权重计算
阶段和总体进度，区分工程完成、现实验证和生产准入，不读取或写入案例现实结果。

示例：
    python -m tools.project_progress --format markdown
    python -m tools.project_progress --write --record
    python -m tools.project_progress --check
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_STATE = ROOT / "progress" / "PROJECT_PROGRESS.json"
DEFAULT_DASHBOARD = ROOT / "progress" / "PROJECT_PROGRESS.md"
DEFAULT_MILESTONES = ROOT / "progress" / "MILESTONES.md"
DEFAULT_HISTORY = ROOT / "progress" / "PROGRESS_HISTORY.md"
PROJECT_STATE = ROOT / "META" / "project-state.json"
VERSION = ROOT / "VERSION"

ALLOWED_STATUSES = {
    "NOT_STARTED",
    "READY",
    "IN_PROGRESS",
    "VALIDATING",
    "COMPLETE",
    "LOCKED",
    "BLOCKED",
    "WAITING_FOR_DECISION",
}
DONE_STATUSES = {"COMPLETE", "LOCKED"}


class ProgressStateError(ValueError):
    """Raised when the progress state is incomplete or internally inconsistent."""


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ProgressStateError(f"missing JSON state: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ProgressStateError(f"invalid JSON state {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ProgressStateError(f"JSON state must be an object: {path}")
    return value


def load_state(path: Path = DEFAULT_STATE) -> dict[str, Any]:
    state = _read_json(path)
    if state.get("schema_version") != "1.0":
        raise ProgressStateError("unsupported progress schema_version")
    if not state.get("project") or not state.get("last_updated"):
        raise ProgressStateError("project and last_updated are required")
    stages = state.get("stages")
    if not isinstance(stages, list) or not stages:
        raise ProgressStateError("stages must be a non-empty list")

    stage_ids: set[str] = set()
    for stage in stages:
        if not isinstance(stage, dict):
            raise ProgressStateError("each stage must be an object")
        stage_id = stage.get("id")
        if not isinstance(stage_id, str) or stage_id in stage_ids:
            raise ProgressStateError(f"duplicate or invalid stage id: {stage_id!r}")
        stage_ids.add(stage_id)
        _validate_status(stage.get("status"), f"stage {stage_id}")
        _validate_weight(stage.get("weight"), f"stage {stage_id}")
        tasks = stage.get("tasks")
        if not isinstance(tasks, list) or not tasks:
            raise ProgressStateError(f"stage {stage_id} needs tasks")
        task_ids: set[str] = set()
        for task in tasks:
            if not isinstance(task, dict):
                raise ProgressStateError(f"stage {stage_id} task must be an object")
            task_id = task.get("id")
            if not isinstance(task_id, str) or task_id in task_ids:
                raise ProgressStateError(f"duplicate or invalid task id: {task_id!r}")
            task_ids.add(task_id)
            _validate_status(task.get("status"), f"task {task_id}")
            _validate_weight(task.get("weight"), f"task {task_id}")
            completion = task.get("completion")
            if not isinstance(completion, (int, float)) or not 0 <= completion <= 1:
                raise ProgressStateError(f"task {task_id} completion must be in [0, 1]")
            if task["status"] in DONE_STATUSES and completion != 1:
                raise ProgressStateError(f"done task {task_id} must have completion=1")
            if task["status"] not in DONE_STATUSES and completion == 1:
                raise ProgressStateError(f"unfinished task {task_id} cannot have completion=1")
    return state


def _validate_status(status: object, label: str) -> None:
    if status not in ALLOWED_STATUSES:
        raise ProgressStateError(f"{label} has invalid status: {status!r}")


def _validate_weight(weight: object, label: str) -> None:
    if not isinstance(weight, (int, float)) or weight <= 0:
        raise ProgressStateError(f"{label} weight must be positive")


def _percent(value: float) -> float:
    return round(value * 100, 1)


def _stage_metrics(stage: dict[str, Any]) -> dict[str, Any]:
    tasks = stage["tasks"]
    total_weight = sum(float(task["weight"]) for task in tasks)
    completed_weight = sum(float(task["weight"]) * float(task["completion"]) for task in tasks)
    return {
        "total_weight": total_weight,
        "completed_weight": completed_weight,
        "completion": completed_weight / total_weight,
        "completion_percent": _percent(completed_weight / total_weight),
        "task_count": len(tasks),
        "completed_task_count": sum(task["status"] in DONE_STATUSES for task in tasks),
    }


def _runtime_snapshot() -> dict[str, Any]:
    project_state = _read_json(PROJECT_STATE)
    version = VERSION.read_text(encoding="utf-8").strip()
    prospective = project_state.get("domain_prospective_status", {})
    single_case = project_state.get("single_case_prospective_status", {})
    return {
        "product_version": version,
        "declared_product_version": project_state.get("product_version"),
        "current_phase": project_state.get("current_phase"),
        "domain_engineering": prospective.get("engineering_implementation"),
        "real_cohort": prospective.get("real_cohort"),
        "production_ready": prospective.get("production_ready"),
        "production_switch_permitted": prospective.get("production_switch_permitted"),
        "single_case_future_observation": single_case.get("future_observation"),
    }


def build_report(state: dict[str, Any] | None = None) -> dict[str, Any]:
    state = state or load_state()
    stages: list[dict[str, Any]] = []
    total_stage_weight = 0.0
    total_completed_weight = 0.0
    for stage in state["stages"]:
        metrics = _stage_metrics(stage)
        stage_weight = float(stage["weight"])
        total_stage_weight += stage_weight
        total_completed_weight += stage_weight * metrics["completion"]
        stages.append({**stage, "metrics": metrics})
    return {
        "schema_version": state["schema_version"],
        "project": state["project"],
        "last_updated": state["last_updated"],
        "runtime": _runtime_snapshot(),
        "overall": {
            "stage_weight": total_stage_weight,
            "completed_stage_weight": total_completed_weight,
            "completion": total_completed_weight / total_stage_weight,
            "completion_percent": _percent(total_completed_weight / total_stage_weight),
        },
        "next_stage": state.get("next_stage"),
        "next_actions": state.get("next_actions", []),
        "global_blockers": state.get("global_blockers", []),
        "stages": stages,
    }


def _cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def render_dashboard(report: dict[str, Any]) -> str:
    runtime = report["runtime"]
    overall = report["overall"]
    lines = [
        "# mangpai-fusion 项目进度仪表盘",
        "",
        f"> 状态快照：{report['last_updated']}；机器状态源：`progress/PROJECT_PROGRESS.json`。",
        "> 本仪表盘展示工程任务完成度，不把工程完成度等同于现实验证或生产准入。",
        "",
        "## 当前总览",
        "",
        "| 项目 | 当前值 |",
        "|---|---|",
        f"| 产品版本 | `{_cell(runtime['product_version'])}` |",
        f"| 当前工作阶段 | `{_cell(runtime['current_phase'])}` |",
        f"| 加权任务进度 | **{overall['completion_percent']:.1f}%** |",
        f"| 下一阶段 | `{_cell(report['next_stage'])}` |",
        f"| 真实 prospective cohort | `{_cell(runtime['real_cohort'])}` |",
        f"| 单案例未来观察 | `{_cell(runtime['single_case_future_observation'])}` |",
        f"| production_ready | **{str(runtime['production_ready']).lower()}** |",
        f"| production_switch_permitted | **{str(runtime['production_switch_permitted']).lower()}** |",
        "",
        "### 结论",
        "",
        "当前系统的工程能力已覆盖多个阶段，但现实 cohort 尚未就绪，生产准入仍关闭。",
        "",
        "## 阶段进度",
        "",
        "| 阶段 | 名称 | 状态 | 就绪条件 | 进度 | 已完成任务 |",
        "|---|---|---|---|---:|---:|",
    ]
    for stage in report["stages"]:
        metrics = stage["metrics"]
        lines.append(
            f"| `{stage['id']}` | {_cell(stage['name'])} | `{stage['status']}` | "
            f"`{_cell(stage['readiness'])}` | {metrics['completion_percent']:.1f}% | "
            f"{metrics['completed_task_count']}/{metrics['task_count']} |"
        )

    for stage in report["stages"]:
        metrics = stage["metrics"]
        lines.extend([
            "",
            f"## {stage['id']} · {stage['name']}",
            "",
            f"状态：`{stage['status']}`；就绪状态：`{stage['readiness']}`；阶段权重：{stage['weight']}。",
            f"阶段进度：**{metrics['completion_percent']:.1f}%**（任务权重 {metrics['completed_weight']:.1f}/{metrics['total_weight']:.1f}）。",
            "",
            "进入条件：",
            "",
        ])
        lines.extend(f"- {condition}" for condition in stage["entry_conditions"])
        lines.extend(["", "退出条件：", ""])
        lines.extend(f"- {condition}" for condition in stage["exit_conditions"])
        lines.extend([
            "",
            "任务：",
            "",
            "| 任务 | 状态 | 完成度 | 权重 | 证据 / 说明 |",
            "|---|---|---:|---:|---|",
        ])
        for task in stage["tasks"]:
            evidence = "；".join(task.get("evidence", [])) or "—"
            lines.append(
                f"| `{task['id']}` {_cell(task['label'])} | `{task['status']}` | "
                f"{float(task['completion']) * 100:.1f}% | {task['weight']} | {_cell(evidence)} |"
            )
        lines.extend(["", "阻塞项：", ""])
        if stage["blockers"]:
            lines.extend(f"- {blocker}" for blocker in stage["blockers"])
        else:
            lines.append("- 无")
        lines.extend(["", "下一步：", ""])
        if stage["next_actions"]:
            lines.extend(f"- {action}" for action in stage["next_actions"])
        else:
            lines.append("- 无")

    lines.extend(["", "## 全局阻塞项", ""])
    lines.extend(f"- {item}" for item in report["global_blockers"])
    lines.extend(["", "## 下一步", ""])
    lines.extend(f"1. {action}" for action in report["next_actions"])
    lines.append("")
    return "\n".join(lines)


def render_milestones(report: dict[str, Any]) -> str:
    lines = [
        "# 项目阶段与里程碑",
        "",
        f"> 当前状态快照：{report['last_updated']}。详细任务状态见 [`PROJECT_PROGRESS.md`](PROJECT_PROGRESS.md)。",
        "",
        "## 阶段与里程碑",
        "",
        "| 阶段 | 里程碑 | 状态 | 进度 | 退出条件是否满足 |",
        "|---|---|---|---:|---|",
    ]
    for stage in report["stages"]:
        milestones = "、".join(stage["milestones"]) or "—"
        exit_ready = "是" if stage["status"] in DONE_STATUSES else "否"
        lines.append(
            f"| `{stage['id']}` {_cell(stage['name'])} | {milestones} | `{stage['status']}` | "
            f"{stage['metrics']['completion_percent']:.1f}% | {exit_ready} |"
        )
    lines.extend(["", "## 使用规则", "", "- 任务完成度必须由状态源中的明确任务和权重计算。", "- 阶段任务全部完成不代表现实验证完成；现实验证和生产准入单独受项目状态源控制。", "- 阻塞、等待决策和验证失败必须保留在状态源中，不得用模糊百分比掩盖。", "- 现实结果只允许进入验证层，不得污染盲态裁决或冻结分析制品。", ""])
    return "\n".join(lines)


def _history_entry(report: dict[str, Any]) -> str:
    stage_summary = "；".join(
        f"{stage['id']} {stage['metrics']['completion_percent']:.1f}%/{stage['status']}"
        for stage in report["stages"]
    )
    return "\n".join([
        f"## {report['last_updated']}",
        "",
        f"- 加权任务进度：{report['overall']['completion_percent']:.1f}%",
        f"- 当前工作阶段：`{report['runtime']['current_phase']}`",
        f"- production_ready：`{str(report['runtime']['production_ready']).lower()}`",
        f"- 阶段快照：{stage_summary}",
        "",
    ])


def write_outputs(report: dict[str, Any], *, record: bool = False) -> None:
    DEFAULT_DASHBOARD.write_text(render_dashboard(report), encoding="utf-8", newline="\n")
    DEFAULT_MILESTONES.write_text(render_milestones(report), encoding="utf-8", newline="\n")
    if record:
        if DEFAULT_HISTORY.exists():
            history = DEFAULT_HISTORY.read_text(encoding="utf-8")
        else:
            history = "# 项目进度历史\n\n"
        heading = f"## {report['last_updated']}"
        if heading not in history:
            if not history.endswith("\n"):
                history += "\n"
            history += "\n" + _history_entry(report)
            DEFAULT_HISTORY.write_text(history, encoding="utf-8", newline="\n")


def check_outputs(report: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    expected = {
        DEFAULT_DASHBOARD: render_dashboard(report),
        DEFAULT_MILESTONES: render_milestones(report),
    }
    for path, content in expected.items():
        if not path.exists():
            problems.append(f"missing generated file: {path.relative_to(ROOT)}")
        elif path.read_text(encoding="utf-8") != content:
            problems.append(f"generated file is stale: {path.relative_to(ROOT)}")
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="计算并渲染项目进度仪表盘。")
    parser.add_argument("--format", choices=("json", "markdown"), default="markdown")
    parser.add_argument("--write", action="store_true", help="写入 PROJECT_PROGRESS.md 与 MILESTONES.md")
    parser.add_argument("--record", action="store_true", help="写入一次去重后的 PROGRESS_HISTORY.md 快照")
    parser.add_argument("--check", action="store_true", help="校验状态源和生成文件是否一致")
    args = parser.parse_args(argv)

    try:
        report = build_report()
        if args.check:
            problems = check_outputs(report)
            if problems:
                for problem in problems:
                    print(problem, file=sys.stderr)
                return 1
            print("project progress check passed")
            return 0
        if args.write or args.record:
            write_outputs(report, record=args.record)
        if args.format == "json":
            print(json.dumps(report, ensure_ascii=False, indent=2))
        else:
            print(render_dashboard(report))
        return 0
    except ProgressStateError as exc:
        print(f"project progress check failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

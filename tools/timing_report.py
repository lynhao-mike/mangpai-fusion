"""tools/timing_report.py · 轻量 metrics 聚合报告

扫描 cases/*/findings/timing.json，输出全局耗时概览到 META/timing-summary.json。

用法：
    python3 -m tools.timing_report          # 输出 JSON 到 stdout + 落盘
    python3 -m tools.timing_report --human   # 输出人类可读摘要

输出格式（META/timing-summary.json）：
    {
      "generated_at": "...",
      "case_count": 11,
      "total_avg_seconds": 0.002,
      "threshold_seconds": 60.0,
      "exceeded_count": 0,
      "per_step_avg": {"energy": 0.0004, ...},
      "slowest_case": {"case_id": "...", "total_seconds": ...},
      "cases": [...]
    }

设计原则（v1.2.1 DevOps 对齐）：
    - 仅依赖 stdlib (json / pathlib / statistics)
    - 不导入 engine.*（避免 yaml 依赖，沙箱可直接跑）
    - 60s 阈值沿用 pipeline.py PIPELINE_THRESHOLD_SECONDS
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
CASES_DIR = REPO_ROOT / "cases"
META_DIR = REPO_ROOT / "META"
THRESHOLD_SECONDS = 60.0


def collect_timings() -> list[dict[str, Any]]:
    """扫描所有 cases/*/findings/timing.json，返回按 total_seconds 降序排列。"""
    results = []
    for timing_file in sorted(CASES_DIR.rglob("findings/timing.json")):
        try:
            data = json.loads(timing_file.read_text(encoding="utf-8"))
            results.append(data)
        except (json.JSONDecodeError, OSError):
            continue
    results.sort(key=lambda d: d.get("total_seconds", 0), reverse=True)
    return results


def build_summary(timings: list[dict[str, Any]]) -> dict[str, Any]:
    """构建聚合摘要。"""
    if not timings:
        return {
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "case_count": 0,
            "total_avg_seconds": 0.0,
            "threshold_seconds": THRESHOLD_SECONDS,
            "exceeded_count": 0,
            "per_step_avg": {},
            "slowest_case": None,
            "cases": [],
        }

    totals = [t.get("total_seconds", 0.0) for t in timings]
    exceeded = [t for t in timings if t.get("exceeded_threshold", False)]

    # 按步骤聚合平均耗时
    step_totals: dict[str, list[float]] = {}
    for t in timings:
        steps = t.get("steps", {})
        for name, sec in steps.items():
            step_totals.setdefault(name, []).append(sec)
    per_step_avg = {
        name: round(mean(values), 6) for name, values in step_totals.items()
    }

    slowest = timings[0] if timings else None

    return {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "case_count": len(timings),
        "total_avg_seconds": round(mean(totals), 6),
        "threshold_seconds": THRESHOLD_SECONDS,
        "exceeded_count": len(exceeded),
        "per_step_avg": per_step_avg,
        "slowest_case": {
            "case_id": slowest.get("case_id", "?"),
            "total_seconds": slowest.get("total_seconds", 0),
        } if slowest else None,
        "cases": [
            {
                "case_id": t.get("case_id", "?"),
                "total_seconds": t.get("total_seconds", 0),
                "exceeded": t.get("exceeded_threshold", False),
            }
            for t in timings
        ],
    }


def write_summary(summary: dict[str, Any]) -> Path:
    """落盘到 META/timing-summary.json。"""
    META_DIR.mkdir(parents=True, exist_ok=True)
    path = META_DIR / "timing-summary.json"
    path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return path


def print_human(summary: dict[str, Any]) -> None:
    """人类可读摘要输出。"""
    print("=" * 60)
    print("Pipeline Timing Summary")
    print("=" * 60)
    print(f"  案例数: {summary['case_count']}")
    print(f"  平均总耗时: {summary['total_avg_seconds']:.4f}s")
    print(f"  阈值: {summary['threshold_seconds']:.1f}s")
    print(f"  超阈值案例: {summary['exceeded_count']}")
    print()
    if summary['per_step_avg']:
        print("  各步骤平均耗时:")
        for name, avg in summary['per_step_avg'].items():
            bar = "█" * max(1, int(avg * 1000))  # 1ms = 1 block
            print(f"    {name:12s}  {avg:.4f}s  {bar}")
    print()
    if summary['slowest_case']:
        sc = summary['slowest_case']
        print(f"  最慢案例: {sc['case_id']}  ({sc['total_seconds']:.4f}s)")
    if summary['exceeded_count']:
        print("\n  ⚠️  有超阈值案例！请 review pipeline 性能。")
    else:
        print("\n  ✅  所有案例均在 60s 阈值内。")
    print("=" * 60)


def main() -> int:
    timings = collect_timings()
    summary = build_summary(timings)
    path = write_summary(summary)

    if "--human" in sys.argv:
        print_human(summary)
    else:
        print(json.dumps(summary, ensure_ascii=False, indent=2))

    print(f"\n[timing_report] 写入: {path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

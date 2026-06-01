"""tools/timing_report.py · 轻量 metrics 聚合报告

扫描 cases/*/findings/timing.json 与 META/timings/*.json，输出全局耗时概览到 META/timing-summary.json。

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
    """扫描 pipeline 与 META/timings/ timing.json，返回按 total_seconds 降序排列。"""
    results: list[dict[str, Any]] = []
    for timing_file in sorted(CASES_DIR.rglob("findings/timing.json")):
        try:
            data = json.loads(timing_file.read_text(encoding="utf-8"))
            data.setdefault("timing_type", "pipeline")
            data.setdefault("source_path", str(timing_file.relative_to(REPO_ROOT)))
            results.append(data)
        except (json.JSONDecodeError, OSError, ValueError):
            continue
    meta_timings_dir = META_DIR / "timings"
    for timing_file in sorted(meta_timings_dir.glob("*.json")) if meta_timings_dir.exists() else []:
        try:
            data = json.loads(timing_file.read_text(encoding="utf-8"))
            data.setdefault("timing_type", "meta")
            data.setdefault("source_path", str(timing_file.relative_to(REPO_ROOT)))
            results.append(data)
        except (json.JSONDecodeError, OSError, ValueError):
            continue
    results.sort(key=lambda d: d.get("total_seconds", 0), reverse=True)
    return results


def build_summary(timings: list[dict[str, Any]]) -> dict[str, Any]:
    """构建聚合摘要。"""
    if not timings:
        return {
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "case_count": 0,
            "timing_count": 0,
            "total_avg_seconds": 0.0,
            "threshold_seconds": THRESHOLD_SECONDS,
            "exceeded_count": 0,
            "per_step_avg": {},
            "per_type": {},
            "slowest_case": None,
            "cases": [],
        }

    totals = [t.get("total_seconds", 0.0) for t in timings]
    exceeded = [t for t in timings if t.get("exceeded_threshold", False)]

    # 按步骤聚合平均耗时
    step_totals: dict[str, list[float]] = {}
    type_totals: dict[str, list[float]] = {}
    for t in timings:
        timing_type = str(t.get("timing_type") or "pipeline")
        type_totals.setdefault(timing_type, []).append(float(t.get("total_seconds", 0.0)))
        steps = t.get("steps", {})
        for name, sec in steps.items():
            step_totals.setdefault(name, []).append(sec)
    per_step_avg = {
        name: round(mean(values), 6) for name, values in step_totals.items()
    }
    per_type = {
        name: {
            "count": len(values),
            "avg_seconds": round(mean(values), 6),
            "max_seconds": round(max(values), 6),
        }
        for name, values in sorted(type_totals.items())
    }

    slowest = timings[0] if timings else None
    pipeline_timings = [t for t in timings if str(t.get("timing_type") or "pipeline") == "pipeline"]

    return {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "case_count": len(pipeline_timings),
        "timing_count": len(timings),
        "total_avg_seconds": round(mean(totals), 6),
        "threshold_seconds": THRESHOLD_SECONDS,
        "exceeded_count": len(exceeded),
        "per_step_avg": per_step_avg,
        "per_type": per_type,
        "slowest_case": {
            "case_id": slowest.get("case_id", "?"),
            "run_id": slowest.get("run_id", ""),
            "timing_type": slowest.get("timing_type", "pipeline"),
            "total_seconds": slowest.get("total_seconds", 0),
        } if slowest else None,
        "cases": [
            {
                "case_id": t.get("case_id", "?"),
                "run_id": t.get("run_id", ""),
                "timing_type": t.get("timing_type", "pipeline"),
                "total_seconds": t.get("total_seconds", 0),
                "exceeded": t.get("exceeded_threshold", False),
                "source_path": t.get("source_path", ""),
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
    _safe_print("=" * 60)
    _safe_print("Pipeline Timing Summary")
    _safe_print("=" * 60)
    _safe_print(f"  Pipeline 案例数: {summary['case_count']}")
    _safe_print(f"  Timing 样本数: {summary.get('timing_count', summary['case_count'])}")
    _safe_print(f"  平均总耗时: {summary['total_avg_seconds']:.4f}s")
    _safe_print(f"  阈值: {summary['threshold_seconds']:.1f}s")
    _safe_print(f"  超阈值案例: {summary['exceeded_count']}")
    _safe_print()
    if summary['per_step_avg']:
        _safe_print("  各步骤平均耗时:")
        for name, avg in summary['per_step_avg'].items():
            bar = "#" * max(1, int(avg * 1000))  # 1ms = 1 block，使用 ASCII 兼容 Windows cmd
            _safe_print(f"    {name:12s}  {avg:.4f}s  {bar}")
    if summary.get('per_type'):
        _safe_print()
        _safe_print("  按类型聚合:")
        for name, item in summary['per_type'].items():
            _safe_print(
                f"    {name:18s} count={item['count']} "
                f"avg={item['avg_seconds']:.4f}s max={item['max_seconds']:.4f}s"
            )
    _safe_print()
    if summary['slowest_case']:
        sc = summary['slowest_case']
        label = sc.get('case_id') or sc.get('run_id') or '?'
        _safe_print(f"  最慢样本: {sc.get('timing_type', 'pipeline')} {label}  ({sc['total_seconds']:.4f}s)")
    if summary['exceeded_count']:
        _safe_print("\n  [WARN] 有超阈值案例！请 review pipeline 性能。")
    else:
        _safe_print("\n  [OK] 所有案例均在 60s 阈值内。")
    _safe_print("=" * 60)


def _safe_print(text: str = "") -> None:
    """跨平台安全打印，避免 Windows cmd 的 GBK 编码被 Unicode 阻断。"""
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode(sys.stdout.encoding or "utf-8", errors="replace").decode(
            sys.stdout.encoding or "utf-8", errors="replace"
        ))


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

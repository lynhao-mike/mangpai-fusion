"""应用层计时器：记录 pipeline 各步骤耗时并提供软护栏。"""

from __future__ import annotations

import json
import logging
import sys
import time
import warnings
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator, Optional, Union

logger = logging.getLogger(__name__)

PIPELINE_THRESHOLD_SECONDS: float = 60.0

PIPELINE_STEP_NAMES: tuple[str, ...] = (
    "preflight",   # 兜底护栏 #1：input.md → ParsedInput
    "energy",      # W1 D1 段派
    "picture",     # W2 D2 杨派
    "yingqi",      # W3 D3 任派
    "pangzheng",   # W4 D4 高派
    "integrate",   # D1-D4 → AnalysisOutput
    "render",      # tools/render_report.render_from_output
    "self_iter",   # tools/feedback_loop.ingest_feedback（自迭代）
)

META_TIMING_STEP_NAMES: tuple[str, ...] = (
    "discover",
    "process_single",
    "parse_feedback",
    "fanout",
    "apply_rules",
    "write_audit",
    "bump_state",
    "iteration_report",
    "boundary_miner",
    "veto_miner",
    "scan_status_changes",
    "cross_school_summary",
    "write_report",
)


@dataclass
class StepTiming:
    """单步耗时记录。"""
    name: str
    seconds: float
    started_at: str  # ISO 8601 UTC，含微秒

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "seconds": self.seconds,
            "started_at": self.started_at,
        }

class PipelineTiming:
    """轻量级流水线耗时记录器（仅依赖 stdlib time）。

    用法 1（被 run_pipeline 内部使用）::

        timing = PipelineTiming()
        with timing.step("energy"):
            energy = evaluate_energy(parsed)
        ...
        timing.write_to(findings_dir, case_id=case_id)
        timing.check_threshold()  # 超 60s 时打印 [PERF WARN]

    用法 2（外层 e2e 注入复用，避免双重计时器）::

        timing = PipelineTiming()
        with timing.step("preflight"):
            parsed = preflight.parse(path)
        run_pipeline(parsed, timing=timing, write_findings=False)
        # 所有 8 步累加在同一个 timing 上
    """

    def __init__(self, threshold_seconds: float = PIPELINE_THRESHOLD_SECONDS) -> None:
        self.threshold_seconds: float = float(threshold_seconds)
        self.records: list[StepTiming] = []
        self._created_at: float = time.perf_counter()

    @contextmanager
    def step(self, name: str) -> Iterator["PipelineTiming"]:
        """精准计时一个步骤；异常也会落账（finally 块）。"""
        started_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        t0 = time.perf_counter()
        try:
            yield self
        finally:
            dt = time.perf_counter() - t0
            self.records.append(StepTiming(
                name=name,
                seconds=round(dt, 4),
                started_at=started_at,
            ))

    @property
    def total_seconds(self) -> float:
        """所有已记录步骤的耗时之和（秒）。"""
        return round(sum(r.seconds for r in self.records), 4)

    @property
    def exceeded_threshold(self) -> bool:
        return self.total_seconds > self.threshold_seconds

    def steps_map(self) -> dict[str, float]:
        """按步骤名汇总（同名重复出现时累加，例如 yingqi 多次循环计时）。"""
        out: dict[str, float] = {}
        for r in self.records:
            out[r.name] = round(out.get(r.name, 0.0) + r.seconds, 4)
        return out

    def to_dict(
        self,
        *,
        case_id: str = "",
        timing_type: str = "pipeline",
        run_id: str = "",
        step_names: Optional[tuple[str, ...]] = None,
        extra: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "case_id": case_id,
            "run_id": run_id,
            "timing_type": timing_type,
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "pipeline_version": "1.2.1",
            "threshold_seconds": self.threshold_seconds,
            "total_seconds": self.total_seconds,
            "exceeded_threshold": self.exceeded_threshold,
            "step_names": list(step_names or PIPELINE_STEP_NAMES),
            "steps": self.steps_map(),
            "step_details": [r.to_dict() for r in self.records],
        }
        if extra:
            payload["extra"] = extra
        return payload

    def write_to(
        self,
        findings_dir: Union[str, Path],
        *,
        case_id: str = "",
    ) -> Path:
        """落盘 timing.json 到 findings/ 目录。"""
        findings_dir = Path(findings_dir)
        findings_dir.mkdir(parents=True, exist_ok=True)
        path = findings_dir / "timing.json"
        path.write_text(
            json.dumps(self.to_dict(case_id=case_id), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return path

    def write_meta_timing(
        self,
        meta_dir: Union[str, Path],
        *,
        timing_type: str,
        run_id: str,
        case_id: str = "",
        extra: Optional[dict[str, Any]] = None,
    ) -> Path:
        """落盘非 pipeline 链路 timing 到 META/timings/。"""
        timings_dir = Path(meta_dir) / "timings"
        timings_dir.mkdir(parents=True, exist_ok=True)
        safe_type = _safe_timing_part(timing_type)
        safe_run_id = _safe_timing_part(run_id or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
        path = timings_dir / f"{safe_type}-{safe_run_id}.json"
        path.write_text(
            json.dumps(
                self.to_dict(
                    case_id=case_id,
                    run_id=run_id,
                    timing_type=timing_type,
                    step_names=META_TIMING_STEP_NAMES,
                    extra=extra,
                ),
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        return path

    def check_threshold(self) -> Optional[str]:
        """护栏断言：若总耗时超过阈值，发出醒目警告。

        - 终端：在 stderr 上用 "!!!" 边框打印（命令行肉眼可见）
        - 日志：``logger.warning(...)``
        - Python warning：``warnings.warn(..., RuntimeWarning)``
          （便于 pytest / capsys / -W error 捕获）

        **不抛异常、不阻断主业务**——这是软护栏，仅作可见性提醒。

        Returns:
            超阈值时返回警告文本；未超返回 None。
        """
        if not self.exceeded_threshold:
            return None
        per_step = ", ".join(
            f"{r.name}={r.seconds:.2f}s" for r in self.records
        ) or "<no steps recorded>"
        msg = (
            f"Pipeline total {self.total_seconds:.2f}s exceeded threshold "
            f"{self.threshold_seconds:.2f}s. Per-step: {per_step}"
        )
        bar = "!" * 70
        print(f"\n{bar}", file=sys.stderr)
        print(f"[PERF WARN] {msg}", file=sys.stderr)
        print(f"{bar}\n", file=sys.stderr)
        logger.warning("[PERF WARN] %s", msg)
        warnings.warn(msg, RuntimeWarning, stacklevel=2)
        return msg


def _safe_timing_part(value: str) -> str:
    """把 timing_type/run_id 清理成可跨平台使用的文件名片段。"""
    return "".join(ch if ch.isalnum() or ch in ("-", "_") else "-" for ch in value).strip("-") or "timing"

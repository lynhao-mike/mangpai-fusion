"""应用层：用例编排、整合服务与运行时协作。"""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Final, Protocol

if TYPE_CHECKING:
    from engine.application.integration import integrate, verify_hash_chain
    from engine.application.pipeline_runner import run_pipeline, run_pipeline_e2e
    from engine.application.recompute import (
        RecomputeHardGateError,
        RecomputeRequest,
        RecomputeResult,
        recompute_wenzhen_case,
    )
    from engine.application.timing import PipelineTiming, StepTiming


class _ApplicationExport(Protocol):
    __module__: str
    __name__: str


_LAZY_EXPORTS: Final[dict[str, tuple[str, str]]] = {
    "PipelineTiming": ("engine.application.timing", "PipelineTiming"),
    "RecomputeHardGateError": (
        "engine.application.recompute",
        "RecomputeHardGateError",
    ),
    "RecomputeRequest": ("engine.application.recompute", "RecomputeRequest"),
    "RecomputeResult": ("engine.application.recompute", "RecomputeResult"),
    "StepTiming": ("engine.application.timing", "StepTiming"),
    "integrate": ("engine.application.integration", "integrate"),
    "recompute_wenzhen_case": (
        "engine.application.recompute",
        "recompute_wenzhen_case",
    ),
    "run_pipeline": ("engine.application.pipeline_runner", "run_pipeline"),
    "run_pipeline_e2e": (
        "engine.application.pipeline_runner",
        "run_pipeline_e2e",
    ),
    "verify_hash_chain": ("engine.application.integration", "verify_hash_chain"),
}


__all__ = [
    "PipelineTiming",
    "RecomputeHardGateError",
    "RecomputeRequest",
    "RecomputeResult",
    "StepTiming",
    "integrate",
    "recompute_wenzhen_case",
    "run_pipeline",
    "run_pipeline_e2e",
    "verify_hash_chain",
]


def __getattr__(name: str) -> _ApplicationExport:
    target = _LAZY_EXPORTS.get(name)
    if target is None:
        message = f"module {__name__!r} has no attribute {name!r}"
        raise AttributeError(message)
    module_name, attribute_name = target
    export = getattr(import_module(module_name), attribute_name)
    globals()[name] = export
    return export


def __dir__() -> list[str]:
    return sorted((*globals(), *__all__))

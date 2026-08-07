from __future__ import annotations

from types import FunctionType
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from engine.f09.application import (
        F09Observation as F09Observation,
        F09RunExecutionResultV1 as F09RunExecutionResultV1,
        F09RunRequest as F09RunRequest,
        F09RunResult as F09RunResult,
        run_f09_slice as run_f09_slice,
        run_f09_slice_with_execution_authority_v1 as run_f09_slice_with_execution_authority_v1,
    )

__all__: Final[tuple[str, ...]] = (
    "F09Observation",
    "F09RunExecutionResultV1",
    "F09RunRequest",
    "F09RunResult",
    "run_f09_slice",
    "run_f09_slice_with_execution_authority_v1",
)


def __getattr__(name: str) -> type | FunctionType:
    if name not in __all__:
        message = f"module {__name__!r} has no attribute {name!r}"
        raise AttributeError(message)

    from engine.f09.application import (
        F09Observation,
        F09RunExecutionResultV1,
        F09RunRequest,
        F09RunResult,
        run_f09_slice,
        run_f09_slice_with_execution_authority_v1,
    )

    exports: dict[str, type | FunctionType] = {
        "F09Observation": F09Observation,
        "F09RunExecutionResultV1": F09RunExecutionResultV1,
        "F09RunRequest": F09RunRequest,
        "F09RunResult": F09RunResult,
        "run_f09_slice": run_f09_slice,
        "run_f09_slice_with_execution_authority_v1": run_f09_slice_with_execution_authority_v1,
    }
    value = exports[name]
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))

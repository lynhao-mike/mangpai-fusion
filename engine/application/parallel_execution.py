"""并行功能域 analyzer 执行策略。

本模块只负责调度 callable，不承载任何命理业务规则。
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, TimeoutError
from dataclasses import dataclass
from typing import Callable, Literal, TypeVar

T = TypeVar("T")
ExecutionMode = Literal["sequential", "threaded"]


@dataclass(frozen=True)
class ParallelExecutionConfig:
    """功能域 analyzer 执行配置。

    enable_concurrency=False 时强制顺序执行；enable_concurrency=True 时使用
    bounded ThreadPoolExecutor。mode 字段保留用于既有调用兼容。
    """

    mode: ExecutionMode = "sequential"
    max_workers: int = 4
    timeout_seconds: float | None = None
    enable_concurrency: bool = False


def execute_callables(
    callables: list[Callable[[], T]],
    *,
    config: ParallelExecutionConfig | None = None,
) -> list[T | TimeoutError | BaseException]:
    """按配置执行一组 callable，并保持输入顺序返回结果。"""

    active_config = config or ParallelExecutionConfig()
    if not active_config.enable_concurrency and active_config.mode != "threaded":
        return [_execute_one(callable_) for callable_ in callables]

    max_workers = max(1, min(active_config.max_workers, len(callables) or 1))
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(callable_) for callable_ in callables]
        results: list[T | TimeoutError | BaseException] = []
        for future in futures:
            try:
                results.append(future.result(timeout=active_config.timeout_seconds))
            except TimeoutError as exc:
                future.cancel()
                results.append(exc)
            except BaseException as exc:  # noqa: BLE001
                results.append(exc)
        return results


def _execute_one(callable_: Callable[[], T]) -> T | BaseException:
    try:
        return callable_()
    except BaseException as exc:  # noqa: BLE001
        return exc

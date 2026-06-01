"""生产分析任务队列雏形。

当前实现保持 stdlib-only：使用内存队列 + 后台线程执行
ProductionAnalysisService.submit()。它为 production_api 提供异步提交能力，
同时不改变既有同步 service 边界，后续可替换为 SQLite / Redis / Celery 等实现。
"""

from __future__ import annotations

import queue
import threading
from dataclasses import dataclass
from typing import Any, Optional

from engine.application.production_service import ProductionAnalysisService, SubmitAnalysisRequest


@dataclass(frozen=True)
class QueueSubmitResult:
    """异步提交后的稳定响应。"""

    analysis_id: str
    status: str
    queued: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "analysis_id": self.analysis_id,
            "status": self.status,
            "queued": self.queued,
        }


@dataclass(frozen=True)
class _QueuedAnalysis:
    analysis_id: str
    request: SubmitAnalysisRequest


class InMemoryAnalysisQueue:
    """单进程后台分析队列。"""

    def __init__(self, service: ProductionAnalysisService, *, worker_count: int = 1) -> None:
        self.service = service
        self.worker_count = max(1, int(worker_count))
        self._queue: queue.Queue[_QueuedAnalysis | None] = queue.Queue()
        self._threads: list[threading.Thread] = []
        self._started = False
        self._lock = threading.Lock()

    def start(self) -> None:
        """启动后台 worker；重复调用安全。"""
        with self._lock:
            if self._started:
                return
            self._started = True
            for idx in range(self.worker_count):
                thread = threading.Thread(
                    target=self._worker,
                    name=f"analysis-queue-worker-{idx + 1}",
                    daemon=True,
                )
                thread.start()
                self._threads.append(thread)

    def stop(self, *, timeout: Optional[float] = 5.0) -> None:
        """请求 worker 停止。"""
        with self._lock:
            if not self._started:
                return
            for _ in self._threads:
                self._queue.put(None)
            for thread in self._threads:
                thread.join(timeout=timeout)
            self._threads.clear()
            self._started = False

    def submit(self, request: SubmitAnalysisRequest) -> QueueSubmitResult:
        """建立 queued job 并放入后台队列。"""
        queued = self.service.enqueue(request)
        self._queue.put(_QueuedAnalysis(analysis_id=queued.analysis_id, request=request))
        return QueueSubmitResult(analysis_id=queued.analysis_id, status=queued.status)

    def _worker(self) -> None:
        while True:
            item = self._queue.get()
            try:
                if item is None:
                    return
                self.service.run_queued(item.analysis_id, item.request)
            finally:
                self._queue.task_done()

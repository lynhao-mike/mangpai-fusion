"""并行功能域 analyzer 执行审计模型。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from engine.domain.parallel import DomainName, ExpertSystem

ExecutionStatus = Literal["success", "abstain", "exception", "timeout"]


@dataclass(frozen=True)
class AnalyzerExecutionAudit:
    """单个 expert × domain analyzer 的执行状态。"""

    case_id: str
    domain: DomainName
    expert_system: ExpertSystem
    status: ExecutionStatus
    duration_ms: float
    source_engine: str
    error_type: str = ""
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "domain": self.domain,
            "expert_system": self.expert_system,
            "status": self.status,
            "duration_ms": round(self.duration_ms, 3),
            "source_engine": self.source_engine,
            "error_type": self.error_type,
            "message": self.message,
        }

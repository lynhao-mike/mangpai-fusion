"""多专家功能域 analyzer 协议与注册表。

该模块只定义旁路 runner 所需的统一调用边界。各派内部可以有完全不同的
实现，但暴露给裁判层的结果必须是 ExpertReading。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from engine.domain.parallel import (
    DomainName,
    ExpertReading,
    ExpertSystem,
    ParallelConfidence,
)


@dataclass(frozen=True)
class DomainAnalysisContext:
    """功能域分析器的最小上下文。"""

    case_id: str
    base_context: dict[str, Any] = field(default_factory=dict)


class DomainAnalyzer(Protocol):
    """专家体系 × 功能域分析器协议。"""

    expert_system: ExpertSystem
    expert_name: str

    def analyze(self, parsed: Any, domain: DomainName, context: DomainAnalysisContext) -> ExpertReading:
        """返回该专家体系对指定功能域的独立 ExpertReading。"""


class AbstainDomainAnalyzer:
    """未接线专家体系的显式弃权 analyzer。"""

    def __init__(
        self,
        *,
        expert_system: ExpertSystem,
        expert_name: str,
        reason: str = "理论库或执行器尚未接入，按旁路原则显式弃权。",
    ) -> None:
        self.expert_system = expert_system
        self.expert_name = expert_name
        self.reason = reason

    def analyze(self, parsed: Any, domain: DomainName, context: DomainAnalysisContext) -> ExpertReading:
        return ExpertReading(
            reading_id=f"RD-{context.case_id}-{domain}-{self.expert_system}-ABSTAIN",
            case_id=context.case_id,
            domain=domain,
            expert_system=self.expert_system,
            expert_name=self.expert_name,
            stance="abstain",
            claim=self.reason,
            polarity="neutral",
            confidence=ParallelConfidence(
                raw=0.0,
                merged=None,
                feedback_adjusted=None,
                star=1,
                percent=0,
                reason="显式弃权不参与加权胜出。",
            ),
            evidence_items=[],
            axis_refs=[],
            scope_limit="未接入执行器，不能输出正式结论。",
            falsifiable="后续接线并回测后再建立可证伪断语。",
            source_engine="abstain_adapter",
            isolation_boundary="external_protocol_only",
            notes=self.reason,
        )


class StaticReadingAnalyzer:
    """测试与旁路演练用的静态 reading analyzer。"""

    def __init__(self, reading: ExpertReading) -> None:
        self.reading = reading
        self.expert_system = reading.expert_system
        self.expert_name = reading.expert_name

    def analyze(self, parsed: Any, domain: DomainName, context: DomainAnalysisContext) -> ExpertReading:
        if self.reading.domain != domain:
            raise ValueError(f"静态 reading domain 不匹配：{self.reading.domain} != {domain}")
        if self.reading.case_id != context.case_id:
            data = self.reading.to_dict()
            data["case_id"] = context.case_id
            data["reading_id"] = f"RD-{context.case_id}-{domain}-{self.reading.expert_system}"
            return ExpertReading.from_dict(data)
        return self.reading


class DomainAnalyzerRegistry:
    """专家体系 × 功能域注册表，避免 runner 使用大量 if/else。"""

    def __init__(self) -> None:
        self._items: dict[tuple[DomainName, ExpertSystem], DomainAnalyzer] = {}

    def register(self, domain: DomainName, expert_system: ExpertSystem, analyzer: DomainAnalyzer) -> None:
        self._items[(domain, expert_system)] = analyzer

    def get(self, domain: DomainName, expert_system: ExpertSystem) -> DomainAnalyzer:
        analyzer = self._items.get((domain, expert_system))
        if analyzer is not None:
            return analyzer
        return AbstainDomainAnalyzer(
            expert_system=expert_system,
            expert_name=EXPERT_LABELS[expert_system],
        )

    def registered_experts(self, domain: DomainName) -> list[ExpertSystem]:
        return [expert for (registered_domain, expert), _ in self._items.items() if registered_domain == domain]


EXPERT_LABELS: dict[ExpertSystem, str] = {
    "blind": "盲派综合组",
    "ziping": "子平格局派",
    "tiaohou_ditiansui": "滴天髓调候派",
}

DEFAULT_EXPERT_ORDER: tuple[ExpertSystem, ...] = ("blind", "ziping", "tiaohou_ditiansui")
DEFAULT_DOMAINS: tuple[DomainName, ...] = ("婚姻", "财运", "事业", "健康", "性格", "学业")


def build_empty_parallel_registry() -> DomainAnalyzerRegistry:
    """构造全部专家默认弃权的旁路注册表。"""

    return DomainAnalyzerRegistry()

"""engine/domain/prediction_model.py · v4.2 预测模型领域实体

声明式概率模型：把信号提取公式、融合规则、权重配置显式化为可检视、可测试、可版本化的数据结构。
这是 P0 阶段的类型定义原型，暂不加载 YAML，为后续 P1/P2 阶段的迁移奠定基础。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


class MissingSignalInputError(ValueError):
    """信号提取时缺少必需输入字段。"""
    pass


class SignalExtractionError(RuntimeError):
    """信号提取过程执行失败。"""
    pass


@dataclass(frozen=True)
class SignalExtractor:
    """信号提取规则：从输入上下文计算 0-1 标量信号。
    
    Attributes:
        signal_id: 信号唯一标识，如 "ziping_career_pressure"
        formula: Python 表达式字符串，支持 eval（P1 阶段实现）
        inputs: 依赖的字段路径列表，如 ["day_master_strength", "energy.score"]
        output_range: 输出值区间，用于验证
        rationale: 公式设计理由，用于文档与审查
        version: 公式版本号，用于追溯演进历史
    """
    signal_id: str
    formula: str
    inputs: list[str]
    output_range: tuple[float, float]
    rationale: str
    version: str = "v4.2.0"
    
    def validate_output(self, value: float) -> float:
        """验证输出值是否在合法区间内。"""
        min_val, max_val = self.output_range
        if not (min_val <= value <= max_val):
            raise SignalExtractionError(
                f"Signal {self.signal_id} output {value} out of range [{min_val}, {max_val}]"
            )
        return value


@dataclass(frozen=True)
class FusionRule:
    """信号融合规则：如何合并多个信号为事件概率。
    
    Attributes:
        event_id: 事件唯一标识，如 "career_change"
        method: 融合方法，如 "bayesian_log_odds" / "weighted_average"
        signal_sources: 信号来源列表，每项为 (signal_path, weight_key)
        conflict_threshold: 冲突检测阈值
        conflict_fallback: 冲突时的降级策略表达式
        rationale: 融合逻辑设计理由
    """
    event_id: str
    method: str  # "bayesian_log_odds" | "weighted_average"
    signal_sources: list[tuple[str, str]]  # [(signal_path, weight_key), ...]
    conflict_threshold: float = 0.35
    conflict_fallback: str | None = None
    rationale: str = ""


@dataclass(frozen=True)
class DomainMapping:
    """领域语义映射：事件 → 领域 → 候选含义。
    
    Attributes:
        domain: 领域名称，如 "婚姻" / "事业" / "财运"
        meaning_candidates: 候选事件含义列表，如 ["婚变/离合", "情感纠葛"]
        priority: 展示优先级
    """
    domain: str
    meaning_candidates: list[str]
    priority: int = 50


@dataclass
class ModelSnapshot:
    """概率模型快照：完整的可执行预测模型版本。
    
    Attributes:
        version: 模型版本号，如 "v4.2.0"
        extractors: 信号提取器字典 {signal_id: SignalExtractor}
        fusion_rules: 融合规则字典 {event_id: FusionRule}
        domain_mappings: 领域映射字典 {domain: DomainMapping}
        school_weights: 流派权重字典 {school_name: weight}
        metadata: 模型元数据（创建时间、来源、备注等）
    """
    version: str
    extractors: dict[str, SignalExtractor] = field(default_factory=dict)
    fusion_rules: dict[str, FusionRule] = field(default_factory=dict)
    domain_mappings: dict[str, DomainMapping] = field(default_factory=dict)
    school_weights: dict[str, float] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def extract_signal(self, signal_id: str, context: dict[str, Any]) -> float:
        """执行信号提取（P1 阶段实现，当前为占位）。
        
        Args:
            signal_id: 信号 ID
            context: 输入上下文字典，包含所有依赖字段
            
        Returns:
            提取的信号值（0-1 区间）
            
        Raises:
            MissingSignalInputError: 缺少必需输入字段
            SignalExtractionError: 公式执行失败
        """
        if signal_id not in self.extractors:
            raise SignalExtractionError(f"Unknown signal: {signal_id}")
        
        extractor = self.extractors[signal_id]
        
        # 验证所有输入字段存在
        for input_path in extractor.inputs:
            if not self._get_nested(context, input_path):
                raise MissingSignalInputError(
                    f"Signal {signal_id} requires input: {input_path}"
                )
        
        # P1 阶段实现：eval(extractor.formula, context)
        # P0 阶段占位：返回默认值
        raise NotImplementedError(
            "Signal extraction via formula eval will be implemented in P1 phase"
        )
    
    def fuse_signals(
        self,
        event_id: str,
        signal_values: dict[str, float],
        weights: dict[str, float],
    ) -> float:
        """执行信号融合（P2 阶段实现，当前为占位）。
        
        Args:
            event_id: 事件 ID
            signal_values: 信号值字典 {signal_id: value}
            weights: 权重字典 {weight_key: weight}
            
        Returns:
            融合后的事件概率（0-1 区间）
        """
        if event_id not in self.fusion_rules:
            raise SignalExtractionError(f"Unknown event: {event_id}")
        
        # P2 阶段实现：根据 fusion_rules[event_id].method 执行融合
        raise NotImplementedError(
            "Signal fusion will be implemented in P2 phase"
        )
    
    @staticmethod
    def _get_nested(data: dict[str, Any], path: str) -> Any:
        """获取嵌套字段值，如 "energy.score" → data["energy"]["score"]。"""
        keys = path.split(".")
        value: Any = data
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                value = getattr(value, key, None)
            if value is None:
                return None
        return value
    
    def to_dict(self) -> dict[str, Any]:
        """序列化为字典（用于 YAML 导出）。"""
        return {
            "version": self.version,
            "extractors": {
                sid: {
                    "formula": e.formula,
                    "inputs": e.inputs,
                    "output_range": list(e.output_range),
                    "rationale": e.rationale,
                    "version": e.version,
                }
                for sid, e in self.extractors.items()
            },
            "fusion_rules": {
                eid: {
                    "method": r.method,
                    "signal_sources": [list(src) for src in r.signal_sources],  # tuple → list
                    "conflict_threshold": r.conflict_threshold,
                    "conflict_fallback": r.conflict_fallback,
                    "rationale": r.rationale,
                }
                for eid, r in self.fusion_rules.items()
            },
            "domain_mappings": {
                domain: {
                    "meaning_candidates": m.meaning_candidates,
                    "priority": m.priority,
                }
                for domain, m in self.domain_mappings.items()
            },
            "school_weights": dict(self.school_weights),
            "metadata": dict(self.metadata),
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ModelSnapshot:
        """从字典反序列化（用于 YAML 加载）。"""
        return cls(
            version=data["version"],
            extractors={
                sid: SignalExtractor(
                    signal_id=sid,
                    formula=e["formula"],
                    inputs=e["inputs"],
                    output_range=tuple(e["output_range"]),
                    rationale=e["rationale"],
                    version=e.get("version", data["version"]),
                )
                for sid, e in data.get("extractors", {}).items()
            },
            fusion_rules={
                eid: FusionRule(
                    event_id=eid,
                    method=r["method"],
                    signal_sources=[tuple(src) for src in r["signal_sources"]],  # list → tuple
                    conflict_threshold=r.get("conflict_threshold", 0.35),
                    conflict_fallback=r.get("conflict_fallback"),
                    rationale=r.get("rationale", ""),
                )
                for eid, r in data.get("fusion_rules", {}).items()
            },
            domain_mappings={
                domain: DomainMapping(
                    domain=domain,
                    meaning_candidates=m["meaning_candidates"],
                    priority=m.get("priority", 50),
                )
                for domain, m in data.get("domain_mappings", {}).items()
            },
            school_weights=data.get("school_weights", {}),
            metadata=data.get("metadata", {}),
        )

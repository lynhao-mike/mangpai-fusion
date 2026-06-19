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
        """验证并 clamp 输出值到合法区间。"""
        min_val, max_val = self.output_range
        return max(min_val, min(value, max_val))


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
        """执行信号提取。
        
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
        
        # 验证所有输入字段存在并构建 eval 命名空间
        eval_namespace: dict[str, Any] = {}
        for input_path in extractor.inputs:
            value = self._get_nested(context, input_path)
            if value is None:
                raise MissingSignalInputError(
                    f"Signal {signal_id} requires input: {input_path}"
                )
            # 将嵌套路径映射为扁平变量名，如 "energy.score" → "energy_score"
            var_name = input_path.replace(".", "_")
            eval_namespace[var_name] = value
        
        # 执行公式求值
        try:
            # 预处理公式：将嵌套路径替换为扁平变量名
            processed_formula = extractor.formula
            for input_path in extractor.inputs:
                var_name = input_path.replace(".", "_")
                processed_formula = processed_formula.replace(input_path, var_name)
            
            # 构建安全的全局命名空间：只暴露必要的内置函数
            safe_builtins = {
                "abs": abs,
                "min": min,
                "max": max,
                "len": len,
                "int": int,
                "float": float,
                "bool": bool,
                "str": str,
            }
            
            # 在受限命名空间中执行 eval
            result = eval(processed_formula, {"__builtins__": safe_builtins}, eval_namespace)
            
            if not isinstance(result, (int, float)):
                raise SignalExtractionError(
                    f"Signal {signal_id} formula returned non-numeric type: {type(result)}"
                )
            
            # 验证输出范围（自动 clamp）
            return extractor.validate_output(float(result))
            
        except Exception as exc:
            if isinstance(exc, (MissingSignalInputError, SignalExtractionError)):
                raise
            raise SignalExtractionError(
                f"Signal {signal_id} formula evaluation failed: {exc}"
            ) from exc
    
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
    def from_dict(cls, data: dict[str, Any]) -> "ModelSnapshot":
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
    
    @classmethod
    def load(cls, yaml_path: str) -> "ModelSnapshot":
        """从 YAML 文件加载模型快照。
        
        Args:
            yaml_path: YAML 文件路径（相对于项目根目录）
            
        Returns:
            ModelSnapshot 实例
            
        Raises:
            FileNotFoundError: 文件不存在
            yaml.YAMLError: YAML 解析失败
        """
        import yaml
        from pathlib import Path
        
        path = Path(yaml_path)
        if not path.exists():
            raise FileNotFoundError(f"Model snapshot file not found: {yaml_path}")
        
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        
        return cls.from_dict(data)
    
    def save(self, yaml_path: str) -> None:
        """保存模型快照到 YAML 文件。
        
        Args:
            yaml_path: YAML 文件路径（相对于项目根目录）
        """
        import yaml
        from pathlib import Path
        
        path = Path(yaml_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(
                self.to_dict(),
                f,
                allow_unicode=True,
                default_flow_style=False,
                sort_keys=False,
            )

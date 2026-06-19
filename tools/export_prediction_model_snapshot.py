#!/usr/bin/env python3
"""export_prediction_model_snapshot.py · 导出当前预测模型为 YAML 快照

从现有代码中提取魔法数字、公式、映射，生成声明式模型快照。
这是 P0 阶段工具，为后续 P1/P2 迁移提供 baseline。

Usage:
    python -m tools.export_prediction_model_snapshot --version v4.2.0
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

import yaml

from engine.domain.prediction_model import (
    DomainMapping,
    FusionRule,
    ModelSnapshot,
    SignalExtractor,
)


def extract_current_model() -> ModelSnapshot:
    """从当前代码中提取模型参数，构建 ModelSnapshot。
    
    硬编码当前 v4.2 实现的所有魔法数字、公式、映射。
    """
    # ── 信号提取器 ──────────────────────────────────────────────
    extractors = {
        "ziping_career_pressure": SignalExtractor(
            signal_id="ziping_career_pressure",
            formula="dms if dms >= 0.5 else (1.0 - dms) * 0.6",
            inputs=["day_master_strength"],
            output_range=(0.0, 1.0),
            rationale="身强需外泄能量，事业压力大；身弱则事业压力小",
            version="v4.2.0",
        ),
        "ziping_wealth_activity": SignalExtractor(
            signal_id="ziping_wealth_activity",
            formula="energy_score * (1.0 - abs(dms - 0.5))",
            inputs=["energy_level.score", "day_master_strength"],
            output_range=(0.0, 1.0),
            rationale="能量水平 × 身强弱平衡度，越接近中和财运越活跃",
            version="v4.2.0",
        ),
        "ziping_relationship_tension": SignalExtractor(
            signal_id="ziping_relationship_tension",
            formula="min(ziping_count / total_count, 1.0) * 0.8",
            inputs=["rule_count_by_system.ziping", "rule_count_by_system.total"],
            output_range=(0.0, 0.8),
            rationale="子平规则占比 × 0.8 系数，反映婚姻张力",
            version="v4.2.0",
        ),
        "dtt_imbalance_index": SignalExtractor(
            signal_id="dtt_imbalance_index",
            formula="1.0 - balance_score",
            inputs=["tiaohou.balance_score"],
            output_range=(0.0, 1.0),
            rationale="调候平衡度反转，越不平衡越高",
            version="v4.2.0",
        ),
        "dtt_seasonal_pressure": SignalExtractor(
            signal_id="dtt_seasonal_pressure",
            formula="min(len(missing_elements) * 0.2, 1.0)",
            inputs=["tiaohou.missing_elements"],
            output_range=(0.0, 1.0),
            rationale="缺失五行数量 × 0.2，反映季节压力",
            version="v4.2.0",
        ),
        "dtt_transformation_likelihood": SignalExtractor(
            signal_id="dtt_transformation_likelihood",
            formula="min(wuhe_count * 0.25, 1.0)",
            inputs=["wuhe_relations"],
            output_range=(0.0, 1.0),
            rationale="五合成化数量 × 0.25，反映转化概率",
            version="v4.2.0",
        ),
        "mp_symbolic_event_weight": SignalExtractor(
            signal_id="mp_symbolic_event_weight",
            formula="(passed_layers / 3.0 + confidence_percent) / 2.0",
            inputs=["gate.passed_layers", "gate.confidence.percent"],
            output_range=(0.0, 1.0),
            rationale="通过层数占比与置信度的平均值",
            version="v4.2.0",
        ),
    }
    
    # ── 融合规则 ──────────────────────────────────────────────
    fusion_rules = {
        "career_change": FusionRule(
            event_id="career_change",
            method="bayesian_log_odds",
            signal_sources=[
                ("ziping.career_pressure", "ziping"),
                ("dtt.seasonal_pressure", "tiaohou_ditiansui"),
            ],
            conflict_threshold=0.35,
            conflict_fallback="ziping * 1.5",
            rationale="事业变动：子平身强压力 + 滴天髓季节压力，冲突时子平优先（×1.5）",
        ),
        "wealth_shift": FusionRule(
            event_id="wealth_shift",
            method="bayesian_log_odds",
            signal_sources=[
                ("ziping.wealth_activity", "ziping"),
                ("dtt.transformation_likelihood", "tiaohou_ditiansui"),
            ],
            conflict_threshold=0.35,
            conflict_fallback=None,
            rationale="财运变化：子平财运活跃度 + 滴天髓转化概率",
        ),
        "relationship_shift": FusionRule(
            event_id="relationship_shift",
            method="bayesian_log_odds",
            signal_sources=[
                ("ziping.relationship_tension", "ziping"),
                ("dtt.imbalance_index * 0.6", "tiaohou_ditiansui"),
            ],
            conflict_threshold=0.35,
            conflict_fallback=None,
            rationale="婚姻变化：子平婚姻张力 + 滴天髓失衡度（×0.6 系数）",
        ),
    }
    
    # ── 领域映射 ──────────────────────────────────────────────
    domain_mappings = {
        "婚姻": DomainMapping(
            domain="婚姻",
            meaning_candidates=["婚变/离合", "情感纠葛", "配偶健康"],
            priority=90,
        ),
        "财运": DomainMapping(
            domain="财运",
            meaning_candidates=["财源增减", "投资置业", "破财风险"],
            priority=85,
        ),
        "事业": DomainMapping(
            domain="事业",
            meaning_candidates=["职位变动", "创业机遇", "事业受挫"],
            priority=88,
        ),
        "健康": DomainMapping(
            domain="健康",
            meaning_candidates=["伤病风险", "手术外伤", "慢性耗损"],
            priority=80,
        ),
        "学业": DomainMapping(
            domain="学业",
            meaning_candidates=["考学升迁", "学业受阻"],
            priority=70,
        ),
        "六亲": DomainMapping(
            domain="六亲",
            meaning_candidates=["六亲变故", "人际争端"],
            priority=60,
        ),
        "其他": DomainMapping(
            domain="其他",
            meaning_candidates=["意外变化"],
            priority=10,
        ),
    }
    
    # ── 流派权重（默认值）────────────────────────────────────────
    school_weights = {
        "ziping": 0.42,
        "tiaohou_ditiansui": 0.32,
        "blind": 0.26,
    }
    
    # ── 元数据 ────────────────────────────────────────────────
    metadata = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source": "export_prediction_model_snapshot.py",
        "description": "v4.2.0 baseline model extracted from production code",
        "magic_numbers_extracted": {
            "career_pressure_weak_factor": 0.6,
            "relationship_tension_factor": 0.8,
            "seasonal_pressure_per_missing": 0.2,
            "transformation_per_wuhe": 0.25,
            "conflict_threshold": 0.35,
            "conflict_ziping_boost": 1.5,
            "imbalance_relationship_factor": 0.6,
        },
    }
    
    return ModelSnapshot(
        version="v4.2.0",
        extractors=extractors,
        fusion_rules=fusion_rules,
        domain_mappings=domain_mappings,
        school_weights=school_weights,
        metadata=metadata,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="导出预测模型快照为 YAML")
    parser.add_argument(
        "--version",
        default="v4.2.0",
        help="模型版本号（默认：v4.2.0）",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="输出文件路径（默认：theory/prediction_models/model_versions/{version}_baseline.yaml）",
    )
    args = parser.parse_args()
    
    # 提取模型
    snapshot = extract_current_model()
    snapshot.version = args.version
    snapshot.metadata["version"] = args.version
    
    # 确定输出路径
    if args.output:
        output_path = args.output
    else:
        output_dir = Path("theory/prediction_models/model_versions")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{args.version}_baseline.yaml"
    
    # 序列化为 YAML
    yaml_data = snapshot.to_dict()
    
    # 写入文件
    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump(
            yaml_data,
            f,
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=False,
            indent=2,
        )
    
    print(f"[OK] Model snapshot exported: {output_path}")
    print(f"  Version: {snapshot.version}")
    print(f"  Extractors: {len(snapshot.extractors)}")
    print(f"  Fusion rules: {len(snapshot.fusion_rules)}")
    print(f"  Domain mappings: {len(snapshot.domain_mappings)}")
    print(f"  School weights: {len(snapshot.school_weights)}")


if __name__ == "__main__":
    main()

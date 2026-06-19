"""tests/test_prediction_model_snapshot.py · 预测模型快照验证测试

验证 v4.2.0 baseline 模型快照的完整性、格式正确性与可加载性。
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from engine.domain.prediction_model import (
    DomainMapping,
    FusionRule,
    ModelSnapshot,
    SignalExtractor,
)


@pytest.fixture
def baseline_yaml_path() -> Path:
    """v4.2.0 baseline YAML 文件路径。"""
    return Path("theory/prediction_models/model_versions/v4.2.0_baseline.yaml")


def test_baseline_yaml_exists(baseline_yaml_path: Path) -> None:
    """验证 v4.2.0 baseline YAML 文件存在。"""
    assert baseline_yaml_path.exists(), f"Baseline YAML not found: {baseline_yaml_path}"


def test_baseline_yaml_valid_syntax(baseline_yaml_path: Path) -> None:
    """验证 YAML 语法正确。"""
    with open(baseline_yaml_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    assert isinstance(data, dict), "YAML root must be a dictionary"
    assert "version" in data, "Missing 'version' field"
    assert data["version"] == "v4.2.0", f"Expected version v4.2.0, got {data['version']}"


def test_baseline_model_can_be_loaded(baseline_yaml_path: Path) -> None:
    """验证可以从 YAML 加载 ModelSnapshot。"""
    with open(baseline_yaml_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    
    snapshot = ModelSnapshot.from_dict(data)
    assert snapshot.version == "v4.2.0"
    assert len(snapshot.extractors) > 0, "Should have signal extractors"
    assert len(snapshot.fusion_rules) > 0, "Should have fusion rules"
    assert len(snapshot.domain_mappings) > 0, "Should have domain mappings"
    assert len(snapshot.school_weights) > 0, "Should have school weights"


def test_baseline_model_extractors_schema(baseline_yaml_path: Path) -> None:
    """验证所有 signal extractors 符合 schema。"""
    with open(baseline_yaml_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    
    snapshot = ModelSnapshot.from_dict(data)
    
    required_extractors = [
        "ziping_career_pressure",
        "ziping_wealth_activity",
        "ziping_relationship_tension",
        "dtt_imbalance_index",
        "dtt_seasonal_pressure",
        "dtt_transformation_likelihood",
        "mp_symbolic_event_weight",
    ]
    
    for extractor_id in required_extractors:
        assert extractor_id in snapshot.extractors, f"Missing extractor: {extractor_id}"
        extractor = snapshot.extractors[extractor_id]
        assert extractor.formula, f"Extractor {extractor_id} has empty formula"
        assert extractor.inputs, f"Extractor {extractor_id} has no inputs"
        assert extractor.output_range[0] <= extractor.output_range[1], \
            f"Invalid output_range for {extractor_id}"
        assert extractor.rationale, f"Extractor {extractor_id} missing rationale"


def test_baseline_model_fusion_rules_schema(baseline_yaml_path: Path) -> None:
    """验证所有 fusion rules 符合 schema。"""
    with open(baseline_yaml_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    
    snapshot = ModelSnapshot.from_dict(data)
    
    required_rules = ["career_change", "wealth_shift", "relationship_shift"]
    
    for rule_id in required_rules:
        assert rule_id in snapshot.fusion_rules, f"Missing fusion rule: {rule_id}"
        rule = snapshot.fusion_rules[rule_id]
        assert rule.method in ["bayesian_log_odds", "weighted_average"], \
            f"Invalid fusion method for {rule_id}: {rule.method}"
        assert len(rule.signal_sources) >= 1, \
            f"Fusion rule {rule_id} must have at least 1 signal source"
        assert 0.0 <= rule.conflict_threshold <= 1.0, \
            f"Invalid conflict_threshold for {rule_id}"


def test_baseline_model_domain_mappings_schema(baseline_yaml_path: Path) -> None:
    """验证所有 domain mappings 符合 schema。"""
    with open(baseline_yaml_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    
    snapshot = ModelSnapshot.from_dict(data)
    
    required_domains = ["婚姻", "财运", "事业", "健康", "学业", "六亲", "其他"]
    
    for domain in required_domains:
        assert domain in snapshot.domain_mappings, f"Missing domain mapping: {domain}"
        mapping = snapshot.domain_mappings[domain]
        assert len(mapping.meaning_candidates) > 0, \
            f"Domain {domain} has no meaning candidates"
        assert mapping.priority > 0, f"Domain {domain} has invalid priority"


def test_baseline_model_school_weights_valid(baseline_yaml_path: Path) -> None:
    """验证流派权重总和接近 1.0。"""
    with open(baseline_yaml_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    
    snapshot = ModelSnapshot.from_dict(data)
    
    assert "ziping" in snapshot.school_weights
    assert "tiaohou_ditiansui" in snapshot.school_weights
    assert "blind" in snapshot.school_weights
    
    total_weight = sum(snapshot.school_weights.values())
    assert 0.99 <= total_weight <= 1.01, \
        f"School weights should sum to ~1.0, got {total_weight}"
    
    for school, weight in snapshot.school_weights.items():
        assert 0.0 <= weight <= 1.0, \
            f"School weight for {school} out of range: {weight}"


def test_baseline_model_round_trip_serialization(baseline_yaml_path: Path) -> None:
    """验证 YAML 加载 → to_dict → from_dict 往返一致性。"""
    with open(baseline_yaml_path, encoding="utf-8") as f:
        original_data = yaml.safe_load(f)
    
    # Load → serialize → reload
    snapshot1 = ModelSnapshot.from_dict(original_data)
    serialized = snapshot1.to_dict()
    snapshot2 = ModelSnapshot.from_dict(serialized)
    
    # 验证版本一致
    assert snapshot1.version == snapshot2.version
    
    # 验证 extractors 数量一致
    assert len(snapshot1.extractors) == len(snapshot2.extractors)
    
    # 验证 fusion_rules 数量一致
    assert len(snapshot1.fusion_rules) == len(snapshot2.fusion_rules)
    
    # 验证 domain_mappings 数量一致
    assert len(snapshot1.domain_mappings) == len(snapshot2.domain_mappings)
    
    # 验证 school_weights 数值一致
    for school in snapshot1.school_weights:
        assert snapshot1.school_weights[school] == pytest.approx(
            snapshot2.school_weights[school],
            abs=1e-6,
        )


def test_baseline_model_metadata_present(baseline_yaml_path: Path) -> None:
    """验证元数据字段存在。"""
    with open(baseline_yaml_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    
    assert "metadata" in data, "Missing metadata field"
    metadata = data["metadata"]
    
    assert "created_at" in metadata, "Missing metadata.created_at"
    assert "source" in metadata, "Missing metadata.source"
    assert "description" in metadata, "Missing metadata.description"
    assert "magic_numbers_extracted" in metadata, "Missing metadata.magic_numbers_extracted"


def test_signal_extractor_output_range_validation() -> None:
    """测试 SignalExtractor.validate_output() 边界检查（自动 clamp）。"""
    extractor = SignalExtractor(
        signal_id="test_signal",
        formula="x * 2",
        inputs=["x"],
        output_range=(0.0, 1.0),
        rationale="Test extractor",
    )
    
    # 合法值
    assert extractor.validate_output(0.0) == 0.0
    assert extractor.validate_output(0.5) == 0.5
    assert extractor.validate_output(1.0) == 1.0
    
    # 越界值自动 clamp 到有效范围
    assert extractor.validate_output(-0.1) == 0.0  # clamp 到下界
    assert extractor.validate_output(1.1) == 1.0   # clamp 到上界
    assert extractor.validate_output(2.0) == 1.0   # 极端越界也 clamp
    assert extractor.validate_output(-5.0) == 0.0


def test_model_snapshot_missing_signal_raises_error() -> None:
    """测试访问不存在的 signal 时抛出错误。"""
    snapshot = ModelSnapshot(version="test")
    
    from engine.domain.prediction_model import SignalExtractionError
    
    with pytest.raises(SignalExtractionError, match="Unknown signal"):
        snapshot.extract_signal("nonexistent_signal", {})


def test_model_snapshot_missing_input_raises_error() -> None:
    """测试信号提取时缺少必需输入字段抛出错误。"""
    extractor = SignalExtractor(
        signal_id="test_signal",
        formula="x + y",
        inputs=["x", "y"],
        output_range=(0.0, 1.0),
        rationale="Test",
    )
    snapshot = ModelSnapshot(
        version="test",
        extractors={"test_signal": extractor},
    )
    
    from engine.domain.prediction_model import MissingSignalInputError
    
    # 缺少输入字段
    with pytest.raises(MissingSignalInputError, match="requires input"):
        snapshot.extract_signal("test_signal", {})
    
    # 只提供部分输入
    with pytest.raises(MissingSignalInputError, match="requires input"):
        snapshot.extract_signal("test_signal", {"x": 1.0})

"""tests/test_prediction_yaml_migration.py · P1 阶段：YAML 信号提取器迁移验证

P1-2 proof point: 验证 YAML-based ModelSnapshot 提取与 Python 实现输出一致性。
"""

from __future__ import annotations

import time
from typing import Any

import pytest

from engine.application.prediction_signals import extract_ziping_signal
from engine.energy.types import Magnitude, EnergyFindings
from engine.domain.prediction_model import ModelSnapshot
from engine.domain.dual_engine import TheoryFindings


# ────────────────────────────────────────────────────────────────────────────
# P1-2: Proof Point — ziping_career_pressure
# ────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def model_snapshot() -> ModelSnapshot:
    """加载 v4.2.0 baseline 模型快照。"""
    return ModelSnapshot.load("theory/prediction_models/model_versions/v4.2.0_baseline.yaml")


@pytest.fixture
def test_context_strong_dms() -> dict[str, Any]:
    """测试上下文：身强 (dms=0.75)。
    
    注意：rule_count_by_system 包含 ziping/ditiansui 两个流派的规则数。
    Python 实现会 sum(values()) 来计算 total，所以这里不包含显式 total 键，
    避免被错误地加入求和。YAML 需要单独计算 ziping + ditiansui。
    """
    return {
        "day_master_strength": 0.75,
        "energy_level": {"score": 0.8},
        "rule_count_by_system": {"ziping": 5, "ditiansui": 3},
    }


@pytest.fixture
def test_context_weak_dms() -> dict[str, Any]:
    """测试上下文：身弱 (dms=0.3)。"""
    return {
        "day_master_strength": 0.3,
        "energy_level": {"score": 0.6},
        "rule_count_by_system": {"ziping": 2, "ditiansui": 6},
    }


@pytest.fixture
def test_context_boundary_dms() -> dict[str, Any]:
    """测试上下文：边界 (dms=0.5)。"""
    return {
        "day_master_strength": 0.5,
        "energy_level": {"score": 0.5},
        "rule_count_by_system": {"ziping": 4, "ditiansui": 4},
    }


def test_ziping_career_pressure_strong_dms_matches_python(
    model_snapshot: ModelSnapshot,
    test_context_strong_dms: dict[str, Any],
) -> None:
    """P1-2-1: 身强情况下，YAML 提取与 Python 实现一致。"""
    # Python 实现
    energy = EnergyFindings(
        energy_level=Magnitude(ordinal=4, score=test_context_strong_dms["energy_level"]["score"]),
        layer_count=3,
        zuogong_paths=[],
        tiyong=None,  # type: ignore
        shidang=None,  # type: ignore
        zeishen=None,  # type: ignore
        wealth_ceiling=None,  # type: ignore
        has_guoheqiaoqiao=False,
        muxing_qufa=None,  # type: ignore
        confidence=None,  # type: ignore
        evidence=[],
    )
    theory = TheoryFindings(
        case_id="test",
        day_master_strength=test_context_strong_dms["day_master_strength"],
        rule_count_by_system=test_context_strong_dms["rule_count_by_system"],
    )
    python_result = extract_ziping_signal(energy, theory)
    
    # YAML 实现
    yaml_career_pressure = model_snapshot.extract_signal(
        "ziping_career_pressure",
        test_context_strong_dms,
    )
    
    # 验证一致性（浮点数容差 1e-9）
    assert abs(yaml_career_pressure - python_result.career_pressure) < 1e-9, (
        f"YAML 输出 {yaml_career_pressure} 与 Python 输出 {python_result.career_pressure} 不一致"
    )
    
    # 验证逻辑：身强 (0.75) → career_pressure = 0.75
    assert abs(yaml_career_pressure - 0.75) < 1e-9


def test_ziping_career_pressure_weak_dms_matches_python(
    model_snapshot: ModelSnapshot,
    test_context_weak_dms: dict[str, Any],
) -> None:
    """P1-2-2: 身弱情况下，YAML 提取与 Python 实现一致。"""
    # Python 实现
    energy = EnergyFindings(
        energy_level=Magnitude(ordinal=3, score=test_context_weak_dms["energy_level"]["score"]),
        layer_count=2,
        zuogong_paths=[],
        tiyong=None,  # type: ignore
        shidang=None,  # type: ignore
        zeishen=None,  # type: ignore
        wealth_ceiling=None,  # type: ignore
        has_guoheqiaoqiao=False,
        muxing_qufa=None,  # type: ignore
        confidence=None,  # type: ignore
        evidence=[],
    )
    theory = TheoryFindings(
        case_id="test",
        day_master_strength=test_context_weak_dms["day_master_strength"],
        rule_count_by_system=test_context_weak_dms["rule_count_by_system"],
    )
    python_result = extract_ziping_signal(energy, theory)
    
    # YAML 实现
    yaml_career_pressure = model_snapshot.extract_signal(
        "ziping_career_pressure",
        test_context_weak_dms,
    )
    
    # 验证一致性
    assert abs(yaml_career_pressure - python_result.career_pressure) < 1e-9
    
    # 验证逻辑：身弱 (0.3) → career_pressure = (1.0 - 0.3) * 0.6 = 0.42
    expected = (1.0 - 0.3) * 0.6
    assert abs(yaml_career_pressure - expected) < 1e-9


def test_ziping_career_pressure_boundary_dms_matches_python(
    model_snapshot: ModelSnapshot,
    test_context_boundary_dms: dict[str, Any],
) -> None:
    """P1-2-3: 边界情况 (dms=0.5) 下，YAML 提取与 Python 实现一致。"""
    # Python 实现
    energy = EnergyFindings(
        energy_level=Magnitude(ordinal=3, score=test_context_boundary_dms["energy_level"]["score"]),
        layer_count=2,
        zuogong_paths=[],
        tiyong=None,  # type: ignore
        shidang=None,  # type: ignore
        zeishen=None,  # type: ignore
        wealth_ceiling=None,  # type: ignore
        has_guoheqiaoqiao=False,
        muxing_qufa=None,  # type: ignore
        confidence=None,  # type: ignore
        evidence=[],
    )
    theory = TheoryFindings(
        case_id="test",
        day_master_strength=test_context_boundary_dms["day_master_strength"],
        rule_count_by_system=test_context_boundary_dms["rule_count_by_system"],
    )
    python_result = extract_ziping_signal(energy, theory)
    
    # YAML 实现
    yaml_career_pressure = model_snapshot.extract_signal(
        "ziping_career_pressure",
        test_context_boundary_dms,
    )
    
    # 验证一致性
    assert abs(yaml_career_pressure - python_result.career_pressure) < 1e-9
    
    # 验证逻辑：dms=0.5 刚好在边界，公式 `dms if dms >= 0.5 else ...` 应返回 0.5
    assert abs(yaml_career_pressure - 0.5) < 1e-9


# ────────────────────────────────────────────────────────────────────────────
# P1-3: 回归测试 — 验证完整 ZipingPredictionSignal
# ────────────────────────────────────────────────────────────────────────────


def test_full_ziping_signal_regression(
    model_snapshot: ModelSnapshot,
    test_context_strong_dms: dict[str, Any],
) -> None:
    """P1-3: 完整 ZipingPredictionSignal 三个字段回归测试。"""
    # Python 实现
    energy = EnergyFindings(
        energy_level=Magnitude(ordinal=4, score=test_context_strong_dms["energy_level"]["score"]),
        layer_count=3,
        zuogong_paths=[],
        tiyong=None,  # type: ignore
        shidang=None,  # type: ignore
        zeishen=None,  # type: ignore
        wealth_ceiling=None,  # type: ignore
        has_guoheqiaoqiao=False,
        muxing_qufa=None,  # type: ignore
        confidence=None,  # type: ignore
        evidence=[],
    )
    theory = TheoryFindings(
        case_id="test",
        day_master_strength=test_context_strong_dms["day_master_strength"],
        rule_count_by_system=test_context_strong_dms["rule_count_by_system"],
    )
    python_result = extract_ziping_signal(energy, theory)
    
    # YAML 实现（三个信号）
    yaml_career = model_snapshot.extract_signal("ziping_career_pressure", test_context_strong_dms)
    yaml_wealth = model_snapshot.extract_signal("ziping_wealth_activity", test_context_strong_dms)
    yaml_relationship = model_snapshot.extract_signal("ziping_relationship_tension", test_context_strong_dms)
    
    # 验证三个字段一致性
    assert abs(yaml_career - python_result.career_pressure) < 1e-9
    assert abs(yaml_wealth - python_result.wealth_activity) < 1e-9
    assert abs(yaml_relationship - python_result.relationship_tension) < 1e-9


# ────────────────────────────────────────────────────────────────────────────
# P1-4: 性能测试 — 验证延迟 <10ms
# ────────────────────────────────────────────────────────────────────────────


def test_yaml_extraction_performance(
    model_snapshot: ModelSnapshot,
    test_context_strong_dms: dict[str, Any],
) -> None:
    """P1-4: 性能测试 — 单次 YAML 信号提取延迟 <10ms。"""
    # 预热（避免首次加载影响）
    model_snapshot.extract_signal("ziping_career_pressure", test_context_strong_dms)
    
    # 计时 100 次提取
    iterations = 100
    start = time.perf_counter()
    for _ in range(iterations):
        model_snapshot.extract_signal("ziping_career_pressure", test_context_strong_dms)
    end = time.perf_counter()
    
    avg_latency_ms = ((end - start) / iterations) * 1000
    
    # 验证平均延迟 <10ms
    assert avg_latency_ms < 10.0, f"平均延迟 {avg_latency_ms:.2f}ms 超过 10ms 阈值"


def test_yaml_model_load_performance() -> None:
    """P1-4-2: YAML 模型加载性能 <50ms。"""
    # 首次加载计时
    start = time.perf_counter()
    ModelSnapshot.load("theory/prediction_models/model_versions/v4.2.0_baseline.yaml")
    end = time.perf_counter()
    
    load_latency_ms = (end - start) * 1000
    
    # 验证加载延迟 <50ms
    assert load_latency_ms < 50.0, f"模型加载延迟 {load_latency_ms:.2f}ms 超过 50ms 阈值"


# ────────────────────────────────────────────────────────────────────────────
# P1-5: 边界条件与异常处理
# ────────────────────────────────────────────────────────────────────────────


def test_yaml_extraction_missing_input_raises_error(model_snapshot: ModelSnapshot) -> None:
    """P1-5-1: 缺失必需输入时抛出 MissingSignalInputError。"""
    from engine.domain.prediction_model import MissingSignalInputError
    
    incomplete_context = {"energy_level": {"score": 0.8}}  # 缺失 day_master_strength
    
    with pytest.raises(MissingSignalInputError, match="day_master_strength"):
        model_snapshot.extract_signal("ziping_career_pressure", incomplete_context)


def test_yaml_extraction_out_of_range_clamped(model_snapshot: ModelSnapshot) -> None:
    """P1-5-2: 输出越界时自动 clamp 到有效范围。"""
    # 构造极端输入（dms=1.5 超出 [0,1]）
    extreme_context = {
        "day_master_strength": 1.5,  # 超出范围
    }
    
    # 应该 clamp 到 [0.0, 1.0]
    result = model_snapshot.extract_signal("ziping_career_pressure", extreme_context)
    assert 0.0 <= result <= 1.0


def test_yaml_extraction_zero_division_safe(model_snapshot: ModelSnapshot) -> None:
    """P1-5-3: 除零安全（ziping_relationship_tension，ziping=0 且 ditiansui=0）。"""
    zero_context = {
        "rule_count_by_system": {"ziping": 0, "ditiansui": 0},
    }
    # max(..., 1) 保护：ziping/(max(0+0,1)) = 0/1 = 0.0
    result = model_snapshot.extract_signal("ziping_relationship_tension", zero_context)
    assert result == 0.0

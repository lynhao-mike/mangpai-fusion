"""tests/regression/test_a_energy.py · 整合 Track-A 的 A-001~A-005

把 ``tests/track_a_smoke/test_a_layer_count.py`` 中的核心测试以 pytest
参数化方式重新组织，便于 v1.2 整合 agent 一键回归。

策略：
    - **不重写** Track-A 已实现的核心断言逻辑
    - 仅做 pytest 适配（class → 函数 + parametrize）
    - 期望表与 Track-A 完全一致
    - A-003 严格版已通过杀印链吸收修复，不再标记 ``xfail``

运行：
    pytest tests/regression/test_a_energy.py -v

依赖：
    - engine.energy.evaluator.evaluate_energy（Track-A 已实现）
    - tests.fixtures.cases.load_case（Track-H 提供）

作者：Track-H · v1.2.0
"""
from __future__ import annotations

import pytest

from engine import FINDINGS_SCHEMA_VERSION
from engine.energy.evaluator import evaluate_energy
from tests.fixtures.cases import load_case

pytestmark = pytest.mark.regression

# ============================================================
# 期望表（与 tests/track_a_smoke/test_a_layer_count.py 保持一致）
# ============================================================
WEALTH_ZHONG_FU: set[str] = {"中富级·上", "中富级·中", "中富级·下"}
WEALTH_DA_FU: set[str] = {"大富级·上", "大富级·中", "大富级·下"}
WEALTH_ZHONG_OR_DA: set[str] = WEALTH_ZHONG_FU | WEALTH_DA_FU


# ============================================================
# A-001 ~ A-005
# ============================================================

def test_A001_C2026_001_layer_2_zhongfu_or_dafu() -> None:
    """A-001: C-2026-001 (庚申戊寅壬子辛丑) layer=2, 中富/大富。"""
    parsed = load_case("C-2026-001-乾-庚申戊寅壬子辛丑")
    ef = evaluate_energy(parsed)
    assert ef.layer_count == 2, (
        f"A-001 layer_count 应为 2，实为 {ef.layer_count}"
    )
    assert ef.wealth_ceiling in WEALTH_ZHONG_OR_DA, (
        f"A-001 wealth_ceiling 应在 中富/大富 范围，实为 {ef.wealth_ceiling}"
    )


def test_A002_C2026_002_layer_1_zhongfu() -> None:
    """A-002: C-2026-002 (壬戌庚戌戊辰丙辰) layer=1, 中富。"""
    parsed = load_case("C-2026-002-坤-壬戌庚戌戊辰丙辰")
    ef = evaluate_energy(parsed)
    assert ef.layer_count == 1, (
        f"A-002 layer_count 应为 1，实为 {ef.layer_count}"
    )
    assert ef.wealth_ceiling in WEALTH_ZHONG_FU, (
        f"A-002 wealth_ceiling 应在 中富 范围，实为 {ef.wealth_ceiling}"
    )


def test_A003_C2026_014_strict_layer_1() -> None:
    """A-003 严格版：C-2026-014 (丙戌庚子乙亥辛巳) layer=1。

    杀印相生主结构中的 庚/辛/戌 已由同一印化杀链吸收，避免字符级
    over-count；与 ``tests/track_a_smoke/test_a_layer_count.py::test_A003_C2026014_strict``
    保持一致。
    """
    parsed = load_case("C-2026-014-乾-丙戌庚子乙亥辛巳")
    ef = evaluate_energy(parsed)
    assert ef.layer_count == 1, (
        f"A-003 期望 layer=1，实为 {ef.layer_count}"
    )


def test_A003_C2026_014_relaxed_layer_in_range() -> None:
    """A-003 宽松版：C-2026-014 layer ∈ [1, 4] 且 wealth ∉ 巨富/贫困。"""
    parsed = load_case("C-2026-014-乾-丙戌庚子乙亥辛巳")
    ef = evaluate_energy(parsed)
    assert 1 <= ef.layer_count <= 4
    assert "贫困" not in ef.wealth_ceiling
    assert "巨富" not in ef.wealth_ceiling


def test_A004_C2026_011_layer_ge_2() -> None:
    """A-004: C-2026-011 (乙丑乙酉丁丑癸卯) layer ≥ 2。"""
    parsed = load_case("C-2026-011-乾-乙丑乙酉丁丑癸卯")
    ef = evaluate_energy(parsed)
    assert ef.layer_count >= 2, (
        f"A-004 layer_count 应 ≥ 2，实为 {ef.layer_count}"
    )


def test_A005_C2026_012_layer_ge_2() -> None:
    """A-005: C-2026-012 (壬戌癸丑丙申壬辰) layer ≥ 2。"""
    parsed = load_case("C-2026-012-坤-壬戌癸丑丙申壬辰")
    ef = evaluate_energy(parsed)
    assert ef.layer_count >= 2, (
        f"A-005 layer_count 应 ≥ 2，实为 {ef.layer_count}"
    )


# ============================================================
# 通用契约测试（EnergyFindings 输出格式）
# ============================================================

@pytest.mark.parametrize(
    "case_id",
    [
        "C-2026-001-乾-庚申戊寅壬子辛丑",
        "C-2026-002-坤-壬戌庚戌戊辰丙辰",
        "C-2026-014-乾-丙戌庚子乙亥辛巳",
    ],
)
def test_energy_findings_required_fields(case_id: str) -> None:
    """每个 EnergyFindings 必含全部必填字段。"""
    parsed = load_case(case_id)
    ef = evaluate_energy(parsed)
    assert ef.energy_level is not None
    assert ef.energy_level.ordinal in ("无", "弱", "中", "强", "极强")
    assert 0 <= ef.layer_count <= 4
    assert ef.zuogong_paths is not None
    assert ef.tiyong is not None
    assert ef.shidang is not None
    assert ef.zeishen is not None
    assert "级·" in ef.wealth_ceiling
    assert ef.muxing_qufa in ("禄", "食伤", "比劫", "印")
    assert ef.school == "段"
    assert ef.schema_version == FINDINGS_SCHEMA_VERSION
    assert ef.confidence.star in (1, 2, 3, 4, 5)
    assert 0.0 <= ef.confidence.percent <= 1.0
    assert len(ef.evidence) >= 1
    for e in ef.evidence:
        assert e.school in ("段", "杨", "高", "任")
        assert e.rule_id.startswith(("M1-", "M2-", "M3-", "G-", "MR-", "XF-"))


def test_energy_findings_round_trip_json() -> None:
    """to_json → from_json 一致 + hash 稳定。"""
    parsed = load_case("C-2026-002-坤-壬戌庚戌戊辰丙辰")
    ef = evaluate_energy(parsed)
    s = ef.to_json()

    from engine.energy.types import EnergyFindings
    ef2 = EnergyFindings.from_json(s)
    assert ef.to_dict() == ef2.to_dict()
    assert ef.hash() == ef2.hash()
    assert len(ef.hash()) == 16


@pytest.mark.parametrize(
    "case_id",
    [
        "C-2026-001-乾-庚申戊寅壬子辛丑",
        "C-2026-002-坤-壬戌庚戌戊辰丙辰",
        "C-2026-014-乾-丙戌庚子乙亥辛巳",
        "C-2026-011-乾-乙丑乙酉丁丑癸卯",
        "C-2026-012-坤-壬戌癸丑丙申壬辰",
    ],
)
def test_segpai_muxing_qufa_not_yin(case_id: str) -> None:
    """段派"母星取法"决策 J：必须落在 禄/食伤/比劫，不能取印。"""
    parsed = load_case(case_id)
    ef = evaluate_energy(parsed)
    assert ef.muxing_qufa != "印", (
        f"{case_id} 段派母星不应取印（决策 J），实为 {ef.muxing_qufa}"
    )

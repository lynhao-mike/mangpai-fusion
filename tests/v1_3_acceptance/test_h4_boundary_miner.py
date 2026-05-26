"""H4 · boundary 自挖（D3 决策）

落地：plans/architecture-v1.3.md § 六 H4 + decisions-locked.md D3
代码：tools/boundary_miner.mine_boundaries

D3 阈值：≥5 miss + p<0.1 + lift≥2 + 回放 hit_rate 升 → 候选边界

本文件目标：把 boundary_miner 公共 API 的契约性行为锚定到 pytest（最低门槛），
深度的统计正确性测试（卡方 / lift / 回放）由 boundary_miner 自带的单元逻辑 +
smoke/run_iteration_001 流程覆盖。

历史背景：v1.3 W4 验收时 STATUS.md 写"H4 / H5 由 CI 单独验证"但当时 CI 中
并无对应文件。本 PR 补上 H4 的 pytest 锚点（不依赖完整流水线 + 案例目录）。
"""
from __future__ import annotations

import pathlib

import pytest


pytestmark = [pytest.mark.v1_3_acceptance]


def test_h4_mine_boundaries_unknown_rule_returns_skipped(monkeypatch):
    """未知 rule_id → BoundaryMineResult(skipped=True, skip_reason 含 RuleNotFoundError)，
    不应崩溃。这是 mine_boundaries 必须遵守的最低契约。"""
    from tools.rule_lifecycle import RuleNotFoundError
    monkeypatch.setattr(
        "tools.boundary_miner.load_rule",
        lambda rid: (_ for _ in ()).throw(RuleNotFoundError(rid)),
    )
    from tools.boundary_miner import mine_boundaries
    result = mine_boundaries("DOES-NOT-EXIST-RULE", dry_run=True)
    assert result.skipped is True
    assert "RuleNotFoundError" in result.skip_reason


def test_h4_d3_thresholds_locked():
    """D3 锁定阈值：≥5 miss + p<0.1 + lift≥2。
    如果有人改了默认值，这个测试会立刻发现。"""
    import inspect
    from tools.boundary_miner import mine_boundaries
    sig = inspect.signature(mine_boundaries)
    assert sig.parameters["min_miss"].default == 5, "D3 锁定 min_miss=5"
    assert sig.parameters["p_threshold"].default == 0.1, "D3 锁定 p<0.1"
    assert sig.parameters["lift_threshold"].default == 2.0, "D3 锁定 lift≥2"


def test_h4_chi_square_p_value_basic():
    """卡方公式：完全独立的 2x2 表 → p 接近 1；强相关 → p 接近 0。"""
    from tools.boundary_miner import chi_square_p_value
    # 完全独立（每格 25）
    p_indep = chi_square_p_value([[25, 25], [25, 25]])
    assert p_indep > 0.5, f"独立表 p 应接近 1，得到 {p_indep:.4f}"
    # 强相关（对角主导）
    p_strong = chi_square_p_value([[40, 1], [1, 40]])
    assert p_strong < 0.001, f"强相关表 p 应接近 0，得到 {p_strong:.6f}"


def test_h4_mine_boundaries_low_miss_skips(monkeypatch):
    """miss 数不足 D3 阈值（min_miss=5）→ skipped 而不是误挖。"""
    from tools.rule_lifecycle import Rule
    from tools.boundary_miner import mine_boundaries

    fake = Rule(id="LOW-MISS", school="任", topic="lifa",
                hits=10, misses=3)
    monkeypatch.setattr("tools.boundary_miner.load_rule",
                         lambda rid: fake if rid == "LOW-MISS" else None)
    result = mine_boundaries("LOW-MISS", dry_run=True)
    assert result.skipped is True
    assert "miss" in result.skip_reason.lower()

"""H7 · quantifiable=False 不计分

落地：plans/architecture-v1.4.md § 六 H7（v1.4 W1 决策 V1）
契约：engine/contracts/05-rule-lifecycle.md § 6.1 V1 跳过策略

要求：
    1. quantifiable=False 的规律 ingest 时整体跳过（不计 hit/miss/abstain）
    2. 跳过原因写入 IterationDiff.notes，前缀 "[v1.4-V1]"
    3. 默认值（无字段）按 quantifiable=True 处理（向后兼容）

测试策略：
    用 monkeypatch 注入 fake Rule（不依赖真实 yaml），
    直接驱动 _apply_rule_verdicts dry_run，断言 rule_updates / notes / 计数器。
    端到端的 yaml round-trip 行为由 smoke/smoke_h7_h8_h9.py 覆盖（CI 单独跑）。
"""
from __future__ import annotations

import pytest


pytestmark = [pytest.mark.v1_3_acceptance, pytest.mark.v1_4_acceptance]


def _make_fake_rule(rid: str, *, quantifiable: bool = True,
                    domain_restriction: list[str] | None = None,
                    status: str = "confirmed",
                    hits: int = 0, misses: int = 0):
    """构造一个 Rule，避开 yaml I/O。"""
    from tools.rule_lifecycle import Rule
    return Rule(
        id=rid, school="任", topic="lifa",
        status=status,
        hits=hits, misses=misses,
        quantifiable=quantifiable,
        domain_restriction=list(domain_restriction or []),
    )


@pytest.fixture
def patched_loader(monkeypatch):
    """注入一个内存 rule store，patch load_rule + save_rule。"""
    from tools.rule_lifecycle import RuleNotFoundError
    store: dict = {}

    def fake_load(rid):
        if rid not in store:
            raise RuleNotFoundError(rid)
        return store[rid]

    def fake_save(rule):
        store[rule.id] = rule

    monkeypatch.setattr("tools.feedback_loop.load_rule", fake_load)
    monkeypatch.setattr("tools.feedback_loop.save_rule", fake_save)
    # 也 patch掉 cross_school_scan import 路径（10案触发时不真跑）
    return store


def test_h7_quantifiable_false_skips_miss(patched_loader):
    """V1 主断言：quantifiable=False + verdict=miss → rule_updates 为空，
    hits/misses 完全不变，notes 含 [v1.4-V1] 标记。"""
    from tools.feedback_loop import _apply_rule_verdicts, VerdictContext
    from tools.rule_lifecycle import LifecycleConfig

    fake = _make_fake_rule("M3-R-003-FAKE", quantifiable=False,
                            hits=0, misses=3)
    patched_loader["M3-R-003-FAKE"] = fake

    cfg = LifecycleConfig()
    diff = _apply_rule_verdicts(
        "C-H7-A",
        {"M3-R-003-FAKE": ("miss", VerdictContext(section="任派心法", domain="婚姻"))},
        cfg=cfg, today="2026-05-26", dry_run=True,
    )

    # 1) 跳过：rule_updates 为空
    assert diff.rule_updates == [], f"应跳过，但有更新：{[u.rule_id for u in diff.rule_updates]}"
    # 2) note 标记
    assert any("[v1.4-V1]" in n for n in diff.notes), \
        f"notes 未含 [v1.4-V1] 标记：{diff.notes}"
    assert any("M3-R-003-FAKE" in n for n in diff.notes)
    # 3) 计数器不变
    assert fake.hits == 0
    assert fake.misses == 3  # 没增长


def test_h7_quantifiable_false_skips_hit(patched_loader):
    """quantifiable=False 对 hit 也跳过（不只是 miss 跳过，而是整体跳过）。"""
    from tools.feedback_loop import _apply_rule_verdicts, VerdictContext
    from tools.rule_lifecycle import LifecycleConfig

    fake = _make_fake_rule("M3-R-003-FAKE2", quantifiable=False,
                            hits=2, misses=1)
    patched_loader["M3-R-003-FAKE2"] = fake

    diff = _apply_rule_verdicts(
        "C-H7-B",
        {"M3-R-003-FAKE2": ("hit", VerdictContext(domain="婚姻"))},
        cfg=LifecycleConfig(), today="2026-05-26", dry_run=True,
    )
    assert diff.rule_updates == []
    assert fake.hits == 2  # 没增长
    assert fake.misses == 1


def test_h7_quantifiable_true_normal_path(patched_loader):
    """默认 quantifiable=True 走正常计分路径（向后兼容）。"""
    from tools.feedback_loop import _apply_rule_verdicts, VerdictContext
    from tools.rule_lifecycle import LifecycleConfig

    fake = _make_fake_rule("NORMAL-RULE", quantifiable=True,
                            hits=1, misses=0)
    patched_loader["NORMAL-RULE"] = fake

    diff = _apply_rule_verdicts(
        "C-H7-C",
        {"NORMAL-RULE": ("hit", VerdictContext(domain="财运"))},
        cfg=LifecycleConfig(), today="2026-05-26", dry_run=True,
    )
    assert len(diff.rule_updates) == 1
    u = diff.rule_updates[0]
    assert u.verdict == "hit"
    assert u.hits_after == u.hits_before + 1
    # 没有 V1 标记
    assert not any("[v1.4-V1]" in n for n in diff.notes), \
        f"非 quantifiable=False 不应出现 V1 标记：{diff.notes}"


def test_h7_quantifiable_false_does_not_appear_in_skipped_rule_ids(patched_loader):
    """quantifiable=False 跳过 ≠ 规律不存在。
    skipped_rule_ids 仅记录 RuleNotFoundError，V1 跳过走 notes 通道。"""
    from tools.feedback_loop import _apply_rule_verdicts, VerdictContext
    from tools.rule_lifecycle import LifecycleConfig

    fake = _make_fake_rule("V1-SKIP", quantifiable=False)
    patched_loader["V1-SKIP"] = fake

    diff = _apply_rule_verdicts(
        "C-H7-D",
        {"V1-SKIP": ("miss", VerdictContext(domain="婚姻"))},
        cfg=LifecycleConfig(), today="2026-05-26", dry_run=True,
    )
    assert diff.skipped_rule_ids == [], \
        "V1 跳过不应误入 skipped_rule_ids（这通道留给 RuleNotFound）"

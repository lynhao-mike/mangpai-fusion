"""tests/regression/test_g_iteration.py · 整合 Track-G G-001 回放测试

把 ``tests/track_g_smoke/test_g_replay.py`` 的核心断言重新组织为 pytest
风格。Track-G 已经用 ``unittest.TestCase`` 写好，pytest 可直接收集。

本文件的作用：
    - 显式标记为 ``pytest.mark.regression``，便于 -m 过滤
    - 在 pytest 默认收集（``tests/track_g_smoke/`` 全量）之外，确保
      ``pytest tests/regression/`` 一键就能跑到 G 系测试

策略：
    - 不重写 Track-G 已实现的核心逻辑
    - 通过参数化 + 委托调用 ``ingest_feedback()`` 进行 dry_run 验证
    - 落盘+回滚部分（test_g001_replay_full）保留在 ``tests/track_g_smoke/`` 里
      pytest 自然会收集那份；本文件仅做 dry_run 幂等 + 接口校验

验收（08 § 六）：G-001 回放后 M2-Y-068 misses += 1（在 dry_run 计算中可见）。

作者：Track-H · v1.2.0
"""
from __future__ import annotations

from pathlib import Path

import pytest

from tools.feedback_loop import ingest_feedback
from tools.rule_lifecycle import LifecycleConfig

pytestmark = pytest.mark.regression


CASE_001 = "C-2026-001-庚申戊寅壬子辛丑"
TARGET_MARRIAGE_RULE = "M2-Y-068"   # 杨派"男命劫财见财妻宫破=必离"


# ============================================================
# G-001 回放（dry_run，幂等）
# ============================================================

def test_g001_dry_run_idempotent() -> None:
    """G-001-a：dry_run 回放幂等 + rule_updates 集合稳定。"""
    diff1 = ingest_feedback(CASE_001, dry_run=True)
    diff2 = ingest_feedback(CASE_001, dry_run=True)

    ids1 = sorted(u.rule_id for u in diff1.rule_updates)
    ids2 = sorted(u.rule_id for u in diff2.rule_updates)
    assert ids1 == ids2, "dry_run 必须幂等（同一 case 两次调用返回同样的 rule_updates）"


def test_g001_marriage_rule_miss() -> None:
    """G-001-b：M2-Y-068（婚凶必离）被识别为 miss。"""
    diff = ingest_feedback(CASE_001, dry_run=True)
    target = [u for u in diff.rule_updates if u.rule_id == TARGET_MARRIAGE_RULE]
    assert len(target) == 1, (
        f"{TARGET_MARRIAGE_RULE} 必须出现在 ingest 结果中，"
        f"got: {[u.rule_id for u in diff.rule_updates]}"
    )
    u = target[0]
    assert u.verdict == "miss", (
        f"{TARGET_MARRIAGE_RULE} 应判为 miss（命主 23 岁稳定婚姻，'必离' 失验）"
    )


def test_g001_marriage_rule_misses_incremented() -> None:
    """G-001-c：dry_run 计算的 misses_after 确实 +1。"""
    diff = ingest_feedback(CASE_001, dry_run=True)
    target = [u for u in diff.rule_updates if u.rule_id == TARGET_MARRIAGE_RULE][0]
    assert target.misses_after == target.misses_before + 1, (
        f"{TARGET_MARRIAGE_RULE} misses 应 +1: "
        f"{target.misses_before} → {target.misses_after}"
    )


def test_g001_calibration_freeze_default_off() -> None:
    """G-001-d：calibration.yaml.freeze_iteration 默认 false。"""
    cfg = LifecycleConfig.from_yaml()
    assert cfg.freeze_iteration is False, (
        "默认不冻结（freeze_iteration=False），紧急回滚开关只在显式开启时生效"
    )

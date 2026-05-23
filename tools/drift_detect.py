"""tools/drift_detect.py · v1.2 Track-G 漂移检测

落地契约：
    engine/contracts/05-rule-lifecycle.md § 五·3（detect_drift）

职责：
    检测 confirmed 规律的"近期失准"——
    最近 N 案滑动窗 hit_rate < drift_min_rate 且总样本 ≥ drift_min_n
    → 推荐 confirmed → flagged_for_review

注意：
    - drift_detect 不直接修改 rule，只返回建议状态；feedback_loop 决定是否执行。
    - 仅对 status == "confirmed" 的规律启用（其它状态由 maybe_upgrade/maybe_downgrade 管）。
    - 若 recent_5 长度 < drift_window_size，跳过（数据不足）。

作者：Track-G
"""
from __future__ import annotations

from typing import Optional

from tools.rule_lifecycle import LifecycleConfig, Rule, RuleStatus


def detect_drift(
    rule: Rule, *, cfg: Optional[LifecycleConfig] = None
) -> Optional[RuleStatus]:
    """05 § 五·3 漂移检测。

    返回 "flagged_for_review" 则推荐立即降级；返回 None 则未触发。

    判定条件（4 个全部满足）：
        1. rule.status == "confirmed"
        2. len(rule.recent_5) >= drift_window_size
        3. rule.n >= drift_min_n
        4. mean(rule.recent_5) < drift_min_rate
    """
    cfg = cfg or LifecycleConfig.from_yaml()

    if rule.status != "confirmed":
        return None
    if len(rule.recent_5) < cfg.drift_window_size:
        return None
    if rule.n < cfg.drift_min_n:
        return None

    window = rule.recent_5[-cfg.drift_window_size:]
    recent_hit_rate = sum(1 for x in window if x) / cfg.drift_window_size
    if recent_hit_rate < cfg.drift_min_rate:
        return "flagged_for_review"
    return None


# ============================================================
# smoke / 单测
# ============================================================

def _smoke() -> None:
    """覆盖契约提示的两个用例 + 状态保护边界。"""
    cfg = LifecycleConfig.from_yaml()
    print(f"drift cfg: window={cfg.drift_window_size} min_n={cfg.drift_min_n} min_rate={cfg.drift_min_rate}")

    # 用例 1：last_5=[T,T,T,F,F] hit_rate=60% → 不漂移
    r1 = Rule(id="DRIFT-001", school="段", topic="test", status="confirmed",
              hits=5, misses=3, recent_5=[True, True, True, False, False],
              misses_at_confirmed=0)
    assert detect_drift(r1, cfg=cfg) is None, "60% 不应漂移"
    print(f"[OK] 用例 1: recent_5=[T,T,T,F,F] hit_rate=60% → 不漂移")

    # 用例 2：last_5=[F,F,F,F,T] hit_rate=20% n=8 → 漂移
    r2 = Rule(id="DRIFT-002", school="段", topic="test", status="confirmed",
              hits=4, misses=4, recent_5=[False, False, False, False, True],
              misses_at_confirmed=0)
    assert detect_drift(r2, cfg=cfg) == "flagged_for_review", "20% 应该漂移"
    print(f"[OK] 用例 2: recent_5=[F,F,F,F,T] hit_rate=20% n=8 → flagged_for_review")

    # 用例 3：n=7 < 8 → 不启用漂移检测
    r3 = Rule(id="DRIFT-003", school="段", topic="test", status="confirmed",
              hits=3, misses=4, recent_5=[False] * 5,
              misses_at_confirmed=0)
    assert detect_drift(r3, cfg=cfg) is None, "n<8 应跳过"
    print(f"[OK] 用例 3: n=7 < drift_min_n → 跳过")

    # 用例 4：candidate 状态 → 不检测
    r4 = Rule(id="DRIFT-004", school="段", topic="test", status="candidate",
              hits=4, misses=4, recent_5=[False] * 5)
    assert detect_drift(r4, cfg=cfg) is None
    print(f"[OK] 用例 4: candidate 状态 → 跳过（仅检测 confirmed）")

    # 用例 5：recent_5 不足 5 → 跳过
    r5 = Rule(id="DRIFT-005", school="段", topic="test", status="confirmed",
              hits=8, misses=2, recent_5=[True, True, True],
              misses_at_confirmed=0)
    assert detect_drift(r5, cfg=cfg) is None
    print(f"[OK] 用例 5: recent_5 长度<{cfg.drift_window_size} → 跳过")

    # 用例 6：边界 hit_rate=50%（恰好 drift_min_rate）→ 不漂移
    r6 = Rule(id="DRIFT-006", school="段", topic="test", status="confirmed",
              hits=5, misses=5, recent_5=[True, True, False, False, True],
              misses_at_confirmed=0)
    # 60% > 50% → 不漂移
    assert detect_drift(r6, cfg=cfg) is None
    print(f"[OK] 用例 6: 边界 hit_rate=60% > 50% 阈值 → 不漂移")

    print("\n=== drift_detect.smoke 全部通过 ===")


if __name__ == "__main__":  # pragma: no cover
    _smoke()

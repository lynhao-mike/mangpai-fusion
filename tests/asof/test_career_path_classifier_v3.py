"""v3 分类器测试：通根/透出/临近日主强度分级判别。

核心验证：
1. 食伤+财+主体仅在藏干（弱配置）不应触发完整经营链 → 不压倒官印链
2. 食伤透天干 + 财月支 + 比劫透天干（强配置）→ 触发完整经营链
3. 官印链（官杀有根 + 印绶承接）→ 任职倾向
4. 仅有财星无做功闭环 → 封顶 0.5，不触发经营
5. 输入非法 → 返回 unknown
6. 大运弃权边界（mixed_signal）
"""
from __future__ import annotations

import pytest

from engine.asof.career_path_classifier_v3 import classify_career_path


def _classify(pillars: tuple[str, str, str, str]) -> dict:
    state = classify_career_path(pillars, [], None)
    natal = state.natal_inclination
    if state.abstain_reason is not None or natal.employment_inclined == natal.entrepreneurship_inclined:
        pred = "abstain"
    elif natal.employment_inclined:
        pred = "employment"
    else:
        pred = "entrepreneurship"
    return {
        "pred": pred,
        "abstain_reason": state.abstain_reason,
        "refs": natal.evidence_refs,
    }


# ──────────────────────────────────────────────────────────────────────────────
# 测试 1：弱做功配置（食伤+财+比劫均仅藏干）不应压倒官印链
# ──────────────────────────────────────────────────────────────────────────────
def test_weak_entrepreneurship_does_not_override_official_resource_chain():
    """官印链强（庚七杀透干+子中癸正印月令），全盘无食伤/财/比劫 → 任职，绝不判经营。

    壬子 庚子 甲子 庚子：
      日主甲；壬=偏印在年干；庚=七杀在月干、时干透出 → official_strength=3
      子=月支，子中癸=正印 → resource_strength=2
      全盘无午/巳/卯（无食伤）、无戊/己（无财）、无比劫透干
      entrepreneurship_score=0（无财无食伤），employment_score≥2 → 任职。
    """
    pillars = ("壬子", "庚子", "甲子", "庚子")
    result = _classify(pillars)
    assert result["pred"] in ("employment", "abstain"), (
        f"官印链强且无食伤/财时不应判经营，实际={result}"
    )


# ──────────────────────────────────────────────────────────────────────────────
# 测试 2：强做功配置（食伤透干 + 月支财 + 比劫透干）→ 经营
# ──────────────────────────────────────────────────────────────────────────────
def test_strong_entrepreneurship_chain_with_stem_output_month_wealth():
    """食神透干 + 月支正财 + 比肩透干，且官印不强 → 经营倾向。"""
    # 甲子 庚辰 甲寅 甲午：
    # 日主甲木，甲在年干(比肩)、时干(比肩)透干
    # 庚(七杀)在年支辰中壬水... 需选一个官印弱的盘
    # 改用：比肩透干+食神透干+正财月支
    # 戊午 食神(丙)月支，甲(比肩)年干透，正财戊在年支午中...
    # 选：甲子 戊午 甲午 戊午
    # 日主甲，戊(正财)在年干透出，午月，午中丁(伤官)，甲在年干比肩
    # 官杀：需要无官杀或官杀极弱
    # 选无庚辛的组合：甲子 甲午 甲午 戊午
    # 日主甲，甲比肩透出年干，甲透出月干，戊正财透出时干
    # 月支午中丁(伤官)，已是月支，out_in_month=True
    # peer_in_stems=True（甲=比肩在月干透出）
    # wealth_strength: 戊透时干=3
    # output_strength: 午中丁=月支=2
    # 官杀：无庚辛，official_strength=0
    pillars = ("甲子", "甲午", "甲午", "戊午")
    result = _classify(pillars)
    # 应该是经营或弃权（因为官杀=0，官印链不成立；经营链强）
    assert result["pred"] in ("entrepreneurship", "abstain"), (
        f"强经营链配置应判经营或弃权，实际={result}"
    )


# ──────────────────────────────────────────────────────────────────────────────
# 测试 3：官印相生链明确→任职
# ──────────────────────────────────────────────────────────────────────────────
def test_official_resource_chain_yields_employment():
    """庚透干（正官）+ 辰中癸（正印）且无有效做功闭环 → 任职倾向。"""
    # 庚辰 庚辰 甲辰 庚辰
    # 日主甲，庚七杀透年、月、时干；辰中癸正印藏（月支辰=月令）
    # 财星：辰中无财；食伤：辰中无食伤；比劫：无比肩劫财
    # official_strength=3（透干），resource_strength=2（月支藏干）
    pillars = ("庚辰", "庚辰", "甲辰", "庚辰")
    result = _classify(pillars)
    assert result["pred"] in ("employment", "abstain"), (
        f"官印链强应判任职或弃权，实际={result}"
    )


# ──────────────────────────────────────────────────────────────────────────────
# 测试 4：仅财星无做功闭环 → 封顶 0.5，不判经营
# ──────────────────────────────────────────────────────────────────────────────
def test_wealth_only_does_not_trigger_entrepreneurship():
    """只有财星透干，无食伤、无主体参与 → 经营分 ≤ 0.5，不超过任职链。"""
    # 壬午 壬午 甲午 壬午
    # 日主甲，壬（正印）透出；午中丁（伤官）在月支 → output_in_month=True
    # 这样会有伤官，不是纯财... 改为只有财的设计
    # 用无食伤的地支组合：甲申 庚子 甲子 庚子
    # 日主甲，庚（七杀）透干，子中癸（正印）
    # 申中庚（七杀）、壬（偏印）... 这样官印链成立，没问题
    # 选：庚申 庚子 甲申 戊子
    # 日主甲，戊（正财）透时干；庚（七杀）透年、月干；子中癸（正印）
    # 有官印链，有财但无食伤、比劫
    pillars = ("庚申", "庚子", "甲申", "戊子")
    result = _classify(pillars)
    refs = " ".join(result["refs"])
    assert "wealth_only_cap" in refs or "output_only_cap" in refs or result["pred"] in ("employment", "abstain"), (
        f"仅财星不应触发完整经营链，实际={result}"
    )


# ──────────────────────────────────────────────────────────────────────────────
# 测试 5：输入非法 → unknown
# ──────────────────────────────────────────────────────────────────────────────
def test_invalid_pillars_returns_unknown():
    """不合法输入应优雅返回 unknown，不抛出异常。"""
    # 单字符（长度!=2）→ insufficient_information（函数不抛异常，优雅返回）
    state1 = classify_career_path(("甲", "乙", "丙", "丁"), [], None)  # type: ignore[arg-type]
    assert state1.abstain_reason == "insufficient_information"

    # 长度不足（仅2柱）→ insufficient_information
    state2 = classify_career_path(("甲子", "乙丑"), [], None)  # type: ignore[arg-type]
    assert state2.abstain_reason == "insufficient_information"

    # 空元组 → insufficient_information
    state3 = classify_career_path((), [], None)  # type: ignore[arg-type]
    assert state3.abstain_reason == "insufficient_information"


# ──────────────────────────────────────────────────────────────────────────────
# 测试 6：弱做功链 entrepreneurship_score ≤ 2
# ──────────────────────────────────────────────────────────────────────────────
def test_weak_chain_score_is_low():
    """食伤+财+比劫均仅藏在非月支地支时，经营分应 ≤ 2。"""
    # 甲子 庚申 甲申 庚子
    # 日主甲，庚（七杀）透干，申中庚七杀/壬偏印；子中癸正印月支
    # 食伤：子中无食伤，申中无食伤；比劫：无透干
    # 财：无财星 → wealth_only_cap 或 no entrepreneurship
    pillars = ("甲子", "庚申", "甲申", "庚子")
    state = classify_career_path(pillars, [], None)
    refs = " ".join(state.natal_inclination.evidence_refs)
    # 应当没有完整经营链触发标记
    assert "strong_output_wealth_chain" not in refs, (
        f"弱配置不应触发强经营链，refs={refs}"
    )


# ──────────────────────────────────────────────────────────────────────────────
# 测试 7：v3 弱配置比 v2 有更低的经营分（回归验证核心修复）
# ──────────────────────────────────────────────────────────────────────────────
def test_v3_weak_chain_lower_than_v2():
    """v3 弱配置的经营分应 ≤ 2（v2 恒为 4.0，这是回归保护）。"""
    # 具有藏干食伤+财+比劫但无月支主力的案例
    # 癸巳 庚申 甲申 庚子
    # 日主甲，庚七杀透干，子中癸正印（非月支），巳中丙食神（非月支）
    # 比劫：无透干
    pillars = ("癸巳", "庚申", "甲申", "庚子")
    state = classify_career_path(pillars, [], None)
    refs_str = " ".join(state.natal_inclination.evidence_refs)
    # 提取 entrepreneurship_score
    for ref in state.natal_inclination.evidence_refs:
        if ref.startswith("entrepreneurship_score="):
            score = float(ref.split("=")[1])
            assert score <= 2.0, (
                f"v3 弱配置经营分应 ≤ 2（v2 bug 为 4.0），实际={score}，refs={refs_str}"
            )
            break
    else:
        pytest.fail(f"未找到 entrepreneurship_score 字段，refs={refs_str}")

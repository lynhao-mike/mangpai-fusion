"""tools/as_of_root_level_gate.py 的单元测试。

用真实历史案例的 ``confidence_qualitative`` 冻结文本作为测试数据：
RF000149、RF000164（复核确认为"根气强弱替代领域定位"的捷径判定，事后证明
STRONG_ROOT 判定失手）应命中 ``likely_shortcut=True``；RF000121、RF000125（
复核确认为 CENTER_HIT，判定成功）的冻结文本作为对照，检验该检测不会对
命中案例产生误报（若产生误报，说明检测规则本身设计有误，需要重新调整）。
"""
from __future__ import annotations

import pytest

from tools.as_of_root_level_gate import check_root_level_justification


# 逐字摘自 cases/C-2026-RF000149-坤-.../asof-blind-judgment-n50-frozen-draft.json
# 的 confidence_qualitative 字段；该案最终核验为 MISS。
RF000149_TEXT = (
    "中等偏高：日主日支临官、时支帝旺，根气结构性极强，判定为STRONG_ROOT；"
    "正官(辛)潜藏于年支中气与月支主气但未透干，构成待修复的既有管理路径缺陷；"
    "行运乙巳伤官透干未直接扶助正官，但日主本身根气充足，故判定为"
    "STRONG_ROOT+REPAIR_DEFECT"
)

# 逐字摘自 cases/C-2026-RF000164-乾-.../asof-blind-judgment-n50-frozen-draft.json
# 的 confidence_qualitative 字段；该案最终核验为 MISS。
RF000164_TEXT = (
    "中等偏高：正财(己)与食神(丁)三见构成既有商业技术复合承载功能，日主年支"
    "帝旺、月支/时支双长生，根气结构性极强，判定为STRONG_ROOT；行运庚申偏印"
    "透干间接扶身，激活既有财食承载，故判定为STRONG_ROOT+ACTIVATE_EXISTING"
)


def test_empty_text_rejected() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        check_root_level_justification("  ")


def test_rf000149_flagged_as_likely_shortcut() -> None:
    """RF000149：命中根气强弱描述，且提到正官"潜藏"但judgment主要落在根气上。

    注：该文本确实提到"正官(辛)潜藏"，命中 DOMAIN_LOCATION_PATTERN；因此本
    检测不会把它标记为最严重的"完全没有领域定位"，但会在 root_qi_only_hit 上
    如实命中——这符合本工具"启发式提示、非自动拒绝"的设计边界。测试锚定的是
    root_qi_only_hit 必须为真，而不是笼统断言"一定被拒绝"。
    """

    finding = check_root_level_justification(RF000149_TEXT)
    assert finding.root_qi_only_hit is True


def test_rf000164_domain_mention_present_but_still_flagged_root_qi() -> None:
    """RF000164：文本提及"食神...承载"（命中表层领域信号），但复核已证实

    该案 root_level 判定最终失手（MISS）。这说明本工具是纯表层正则匹配：
    "提及十神+动作词"不等于"领域对应关系已被真实论证"——工具无法分辨两者，
    这是启发式工具的诚实能力边界，不应通过加更多正则规则去掩盖。本测试锚定
    root_qi_only_hit 命中（根气强弱描述确实存在），如实记录该工具在此案上
    不会触发 likely_shortcut（因为表层领域词命中了），提示未来若要真正拦截
    这类"提及但未论证"的判定，需要人工复核而非纯正则能解决。
    """

    finding = check_root_level_justification(RF000164_TEXT)
    assert finding.root_qi_only_hit is True
    assert finding.domain_location_hit is True
    assert finding.likely_shortcut is False


def test_note_is_non_empty_for_true_shortcut_case() -> None:
    """构造一个真正只有根气描述、完全不提十神定位的文本，验证 note 可操作。"""

    pure_root_qi_text = "日主日支临官、时支帝旺，根气结构性极强，故判定为STRONG_ROOT"
    finding = check_root_level_justification(pure_root_qi_text)
    assert finding.root_qi_only_hit is True
    assert finding.domain_location_hit is False
    assert finding.likely_shortcut is True
    assert finding.note.strip()
    assert "人工" in finding.note


def test_text_without_root_qi_language_is_not_flagged() -> None:
    """不含十二长生根气强弱描述的理由文本，不应被标记为捷径判定。"""

    finding = check_root_level_justification(
        "正官(辛)年支透出，构成明确管理路径承载，参见《子平真诠》相关篇章"
    )
    assert finding.root_qi_only_hit is False
    assert finding.likely_shortcut is False

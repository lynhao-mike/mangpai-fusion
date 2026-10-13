"""tools/as_of_theory_lookup.py 的单元测试。

用 First Proof Point 复核实际使用的关键词组合，验证检索工具能真实命中支撑
或推翻 RF000149、RF000164 判定的 theory/ 条目（见根因诊断报告与本工具模块
docstring）。这些断言基于对仓库当前 theory/yang/index.yaml、theory/ziping/
index.yaml 实际内容的真实检索结果，不是构造的模拟数据。
"""
from __future__ import annotations

import pytest

from tools.as_of_theory_lookup import load_school_rules, search_theory


def test_search_theory_rejects_empty_keywords() -> None:
    with pytest.raises(ValueError, match="at least one keyword"):
        search_theory(())


def test_search_theory_rejects_blank_keyword() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        search_theory(("正官", "  "))


def test_load_school_rules_returns_tuple_of_dicts_for_known_school() -> None:
    rules = load_school_rules("yang")
    assert len(rules) > 0
    assert all(isinstance(rule, dict) for rule in rules)


def test_load_school_rules_returns_empty_for_unknown_school() -> None:
    rules = load_school_rules("nonexistent_school_xyz")
    assert rules == ()


def test_rf000149_keywords_hit_yang_official_star_transformation_rule() -> None:
    """RF000149 判定"正官潜藏+REPAIR_DEFECT"时未查此条：正官须用印化才成贵。

    theory/yang/index.yaml 中"正者要化偏者要制"铁律（M2-Y-003 及其复现
    M2-Y-057）明确说"正官用印化=贵……颠倒则半途而废"——该案判定理由完全
    没有提及原局是否有印星去化正官，而这条规律本可以在冻结前被检索到。
    """

    hits = search_theory(("正官", "印化"), schools=("yang",))
    assert len(hits) >= 1
    assert any("正官" in hit.searchable_text and "印化" in hit.searchable_text for hit in hits)
    assert all(hit.school == "yang" for hit in hits)


def test_rf000164_keywords_hit_ziping_shishen_caution_rule() -> None:
    """RF000164 判定"正财+食神三见+ACTIVATE_EXISTING"时未查此条：

    食神生财须"身旺有根"且"忌枭神夺食"——判定理由只提及食神构成承载功能，
    未检查原局是否有偏印夺食的破坏结构。theory/ziping/index.yaml 命中
    《子平真诠》"我生者为食神……食神生财、制杀，喜身旺有根，忌枭神夺食"。
    """

    hits = search_theory(("食神", "忌枭"), schools=("ziping",))
    assert len(hits) >= 1
    assert any("食神" in hit.searchable_text and "忌枭" in hit.searchable_text for hit in hits)


def test_as_citation_line_includes_school_rule_id_and_source() -> None:
    hits = search_theory(("正官", "印化"), schools=("yang",))
    assert len(hits) >= 1
    line = hits[0].as_citation_line()
    assert hits[0].school in line
    assert hits[0].rule_id in line
    assert "来源" in line


def test_search_theory_and_semantics_requires_all_keywords_present() -> None:
    """AND 语义：只有全部关键词都出现的条目才命中，不是任意一个关键词命中即可。"""

    hits_both = search_theory(("正官", "印化"), schools=("yang",))
    hits_single = search_theory(("印化",), schools=("yang",))
    # 单关键词命中数应 >= 双关键词命中数（AND 语义收窄结果，不会扩大）。
    assert len(hits_single) >= len(hits_both)


def test_search_theory_with_no_matching_keyword_returns_empty() -> None:
    hits = search_theory(("这是一个绝不可能出现在任何命理规律文本中的超长唯一字符串标记XYZ123",))
    assert hits == ()


def test_search_theory_default_schools_covers_all_four_schools_plus_ziping_and_tiaohou() -> None:
    """默认检索范围应覆盖四派 + 子平 + 调候滴天髓，不遗漏任何一个既有规律库。"""

    from tools.as_of_theory_lookup import SEARCHABLE_SCHOOLS

    assert set(SEARCHABLE_SCHOOLS) == {"gao", "duan", "yang", "ren", "ziping", "tiaohou_ditiansui"}

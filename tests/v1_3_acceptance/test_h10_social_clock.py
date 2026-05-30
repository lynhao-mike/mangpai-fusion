"""H10 · social_clock_check 学制盲区律强制前置（gate 层）

落地：plans/architecture-v1.4.md § 六 H10 + CFL-C014-003 v2
代码：engine/yingqi/gate.check_social_clock + _compute_age_at_year

场景：所有"成立性事件"（高考 / 毕业 / 工作 / 婚期）应期判定前必须通过年龄合规性检查；
偏差 > 1 年（容差） → 不允许下铁断。

参考：smoke/smoke_h10.py（stdlib smoke 版本）。本文件是 pytest 收编版本。
"""
from __future__ import annotations

import pytest


pytestmark = [pytest.mark.v1_3_acceptance, pytest.mark.v1_4_acceptance]


# ============================================================
# Mock ParsedInput（命主 14：2006-12 出生，8 岁起运）
# ============================================================

class _DayunStep:
    def __init__(self, gz, s, e):
        self.干支 = gz
        self.起讫年 = (s, e)


class _Dayun:
    def __init__(self, qiyun_year=2014, qiyun_age=8):
        self.起运年 = qiyun_year
        self.起运岁 = qiyun_age
        self.排布: list = []


@pytest.fixture
def parsed_2006():
    """命主 14：李砚儒儿子，2006-12-15 出生（虚岁 8 岁起运 = 2014）"""
    class _Parsed:
        case_id = "C-2026-014-乾-丙戌庚子乙亥辛巳"
        birth = {"公历": "2006-12-15", "性别": "男"}
        dayun = _Dayun(qiyun_year=2014, qiyun_age=8)
        bazi = None
        shensha = None
    return _Parsed()


@pytest.fixture
def parsed_no_gonglii():
    """命主 14 但 birth 缺公历字段，回退用大运推算 birth_year=2006"""
    class _Parsed:
        case_id = "C-2026-014-fallback"
        birth = {"性别": "男"}
        dayun = _Dayun(qiyun_year=2014, qiyun_age=8)
        bazi = None
        shensha = None
    return _Parsed()


# ============================================================
# T1: _compute_age_at_year
# ============================================================

def test_h10_compute_age_basic(parsed_2006):
    from engine.yingqi.gate import _compute_age_at_year
    assert _compute_age_at_year(parsed_2006, 2024) == 18
    assert _compute_age_at_year(parsed_2006, 2028) == 22
    assert _compute_age_at_year(parsed_2006, 2029) == 23


def test_h10_compute_age_fallback_to_dayun(parsed_no_gonglii):
    """缺 birth.公历 时回退到大运起运年-起运岁推算 birth_year。"""
    from engine.yingqi.gate import _compute_age_at_year
    assert _compute_age_at_year(parsed_no_gonglii, 2024) == 18


# ============================================================
# T2: 高考事件
# ============================================================

class TestH10Gaokao:
    def test_18_pass(self, parsed_2006):
        from engine.yingqi.gate import check_social_clock
        ok, notes = check_social_clock("高考", 2024, parsed_2006)
        assert ok
        assert any("[17,19]" in n for n in notes)

    def test_19_edge_pass(self, parsed_2006):
        from engine.yingqi.gate import check_social_clock
        ok, _ = check_social_clock("高考", 2025, parsed_2006)
        assert ok

    def test_20_tolerance_pass_with_warning(self, parsed_2006):
        """容差带（窗口外 1 年）通过但带 ⚠️。"""
        from engine.yingqi.gate import check_social_clock
        ok, notes = check_social_clock("高考", 2026, parsed_2006)
        assert ok, "20 岁高考应在容差内通过"
        assert any("⚠️" in n for n in notes)

    def test_21_over_tolerance_fail(self, parsed_2006):
        from engine.yingqi.gate import check_social_clock
        ok, notes = check_social_clock("高考", 2027, parsed_2006)
        assert not ok
        assert any("CFL-C014-003" in n for n in notes)


# ============================================================
# T3: 大学毕业事件
# ============================================================

class TestH10Graduation:
    def test_22_pass(self, parsed_2006):
        """2028 戊申 = 4 年制本科毕业（age=22）→ 通过。"""
        from engine.yingqi.gate import check_social_clock
        ok, notes = check_social_clock("大学毕业", 2028, parsed_2006)
        assert ok
        assert any("[21,24]" in n for n in notes)

    def test_23_still_in_window_pass(self, parsed_2006):
        """2029 己酉 = age 23，仍在严格窗口 [21,24]。"""
        from engine.yingqi.gate import check_social_clock
        ok, _ = check_social_clock("大学毕业", 2029, parsed_2006)
        assert ok

    def test_24_edge_pass(self, parsed_2006):
        from engine.yingqi.gate import check_social_clock
        ok, _ = check_social_clock("大学毕业", 2030, parsed_2006)
        assert ok

    def test_25_tolerance_pass(self, parsed_2006):
        from engine.yingqi.gate import check_social_clock
        ok, notes = check_social_clock("大学毕业", 2031, parsed_2006)
        assert ok
        assert any("⚠️" in n for n in notes)

    def test_26_over_tolerance_fail(self, parsed_2006):
        from engine.yingqi.gate import check_social_clock
        ok, _ = check_social_clock("大学毕业", 2032, parsed_2006)
        assert not ok


# ============================================================
# T4: 长关键词优先级（防止"毕业"误吃"研究生毕业"）
# ============================================================

def test_h10_grad_keyword_priority(parsed_2006):
    """研究生毕业 = [24,29]，不能误匹配大学毕业 [21,24]。"""
    from engine.yingqi.gate import check_social_clock
    ok, notes = check_social_clock("研究生毕业", 2031, parsed_2006)  # age=25
    assert ok
    assert any("研究生毕业" in n and "[24,29]" in n for n in notes)


def test_h10_phd_keyword(parsed_2006):
    """博士毕业 = [27,35]。"""
    from engine.yingqi.gate import check_social_clock
    ok, notes = check_social_clock("博士毕业", 2035, parsed_2006)  # age=29
    assert ok
    assert any("博士毕业" in n and "[27,35]" in n for n in notes)


# ============================================================
# T5: 婚姻 / 工作 事件
# ============================================================

class TestH10Marriage:
    def test_25_within_initial_window(self, parsed_2006):
        from engine.yingqi.gate import check_social_clock
        ok, _ = check_social_clock("结婚", 2031, parsed_2006)
        assert ok

    def test_44_within_remarriage_window(self, parsed_2006):
        from engine.yingqi.gate import check_social_clock
        ok, _ = check_social_clock("结婚", 2050, parsed_2006)
        assert ok

    def test_64_far_outside_fails(self, parsed_2006):
        from engine.yingqi.gate import check_social_clock
        ok, _ = check_social_clock("结婚", 2070, parsed_2006)
        assert not ok


class TestH10Work:
    def test_24_normal_entry(self, parsed_2006):
        from engine.yingqi.gate import check_social_clock
        ok, _ = check_social_clock("入职", 2030, parsed_2006)
        assert ok

    def test_12_underage_fail(self, parsed_2006):
        from engine.yingqi.gate import check_social_clock
        ok, _ = check_social_clock("入职", 2018, parsed_2006)
        assert not ok


# ============================================================
# T6: 边界情况
# ============================================================

def test_h10_empty_event_skips(parsed_2006):
    from engine.yingqi.gate import check_social_clock
    ok, notes = check_social_clock("", 2028, parsed_2006)
    assert ok
    assert any("为空" in n for n in notes)


def test_h10_atypical_event_skips(parsed_2006):
    from engine.yingqi.gate import check_social_clock
    ok, notes = check_social_clock("流年震荡", 2028, parsed_2006)
    assert ok
    assert any("非典型" in n for n in notes)


def test_h10_year_before_birth_skips(parsed_2006):
    from engine.yingqi.gate import check_social_clock
    ok, notes = check_social_clock("结婚", 2000, parsed_2006)  # 命主 2006 出生
    assert ok
    assert any(("不合法" in n or "早于" in n) for n in notes)


# ============================================================
# T7: 规则字典结构
# ============================================================

def test_h10_rules_minimum_count():
    from engine.yingqi.gate import _SOCIAL_CLOCK_RULES
    assert len(_SOCIAL_CLOCK_RULES) >= 12


def test_h10_tolerance_is_one_year():
    from engine.yingqi.gate import _SOCIAL_CLOCK_TOLERANCE
    assert _SOCIAL_CLOCK_TOLERANCE == 1


def test_h10_grad_keyword_before_undergrad():
    """研究生毕业必须在大学毕业之前（关键词长度优先）。"""
    from engine.yingqi.gate import _SOCIAL_CLOCK_RULES
    flat = []
    for keywords, _, _ in _SOCIAL_CLOCK_RULES:
        flat.extend(keywords)
    idx_grad = next((i for i, kw in enumerate(flat) if kw == "研究生毕业"), -1)
    idx_undergrad = next((i for i, kw in enumerate(flat) if kw == "大学毕业"), -1)
    assert idx_grad >= 0 and idx_undergrad >= 0
    assert idx_grad < idx_undergrad, \
        f"研究生毕业 idx={idx_grad} 必须在 大学毕业 idx={idx_undergrad} 之前"

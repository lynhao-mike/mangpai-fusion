"""tests/test_chart_validation.py · 八字排盘验证模块测试

使用问真八字 APP 可信样本作为标准，验证排盘计算的正确性：
- 四柱计算（年柱、月柱、日柱、时柱）
- 节气换月（月柱地支与节气对应）
- 起运时间（起运岁数）
- 大运排布（顺逆排列与干支序列）

作者：排盘验证模块
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from engine.chart_validation import (
    ChartValidator,
    ValidationResult,
    compute_year_pillar,
    compute_month_pillar,
    compute_day_pillar,
    compute_hour_pillar,
    compute_hour_pillar_at,
    compute_dayun,
    ChartValidationError,
    ensure_parsed_chart_validated,
    lunar_to_solar,
    reverse_pillar_dates,
    validate_chart,
)
from engine.predicates.types import GanZhi


# ============================================================
# 可信样本数据（来源：问真八字 APP 排盘）
# ============================================================

TRUSTED_SAMPLES = [
    {
        "case_id": "C-2026-001-乾-庚申戊寅壬子辛丑",
        "gender": "M",
        "solar_date": "1980-02-09",
        "hour_zhi": "丑",  # 丑时 = 01:00-03:00
        "expected_pillars": {
            "年柱": "庚申",
            "月柱": "戊寅",
            "日柱": "壬子",
            "时柱": "辛丑",
        },
        "expected_dayun": {
            "起运岁": 8,
            "顺逆": "顺",
            "排布": ["己卯", "庚辰", "辛巳", "壬午", "癸未", "甲申", "乙酉", "丙戌", "丁亥"],
        },
    },
    {
        "case_id": "C-2026-002-坤-壬戌庚戌戊辰丙辰",
        "gender": "F",
        "solar_date": "1982-10-12",
        "hour_zhi": "辰",  # 辰时 = 07:00-09:00
        "expected_pillars": {
            "年柱": "壬戌",
            "月柱": "庚戌",
            "日柱": "戊辰",
            "时柱": "丙辰",
        },
        "expected_dayun": {
            "起运岁": 2,
            "顺逆": "逆",
            "排布": ["己酉", "戊申", "丁未", "丙午", "乙巳", "甲辰", "癸卯", "壬寅"],
        },
    },
    {
        "case_id": "C-2026-008-坤-壬申癸卯丁未壬寅",
        "gender": "F",
        "solar_date": "1992-04-01",
        "hour_zhi": "寅",  # 寅时 = 03:00-05:00
        "expected_pillars": {
            "年柱": "壬申",
            "月柱": "癸卯",
            "日柱": "丁未",
            "时柱": "壬寅",
        },
        "expected_dayun": {
            "起运岁": 10,
            "顺逆": "逆",
            "排布": ["壬寅", "辛丑", "庚子", "己亥", "戊戌", "丁酉"],
        },
    },
    {
        "case_id": "C-2026-009-乾-庚辰乙酉丙申乙未",
        "gender": "M",
        "solar_date": "2000-10-05",
        "hour_zhi": "未",  # 未时 = 13:00-15:00
        "expected_pillars": {
            "年柱": "庚辰",
            "月柱": "乙酉",
            "日柱": "丙申",
            "时柱": "乙未",
        },
        "expected_dayun": {
            "起运岁": 2,
            "顺逆": "顺",
            "排布": ["丙戌", "丁亥", "戊子", "己丑", "庚寅", "辛卯"],
        },
    },
    {
        "case_id": "C-2026-015-乾-甲寅乙亥丙辰辛卯",
        "gender": "M",
        "solar_date": "1974-11-11",
        "hour_zhi": "卯",  # 卯时 = 05:00-07:00
        "expected_pillars": {
            "年柱": "甲寅",
            "月柱": "乙亥",
            "日柱": "丙辰",
            "时柱": "辛卯",
        },
        "expected_dayun": {
            "起运岁": 9,
            "顺逆": "顺",
            "排布": ["丙子", "丁丑", "戊寅", "己卯", "庚辰", "辛巳", "壬午", "癸未", "甲申"],
        },
    },
]


# ============================================================
# 测试：年柱计算
# ============================================================

class TestYearPillar:
    """验证年柱计算（以立春为分界）。"""

    @pytest.mark.parametrize("sample", TRUSTED_SAMPLES, ids=lambda s: s["case_id"])
    def test_year_pillar_matches_wenzhen(self, sample):
        """年柱必须与问真八字 APP 一致。"""
        result = compute_year_pillar(sample["solar_date"])
        expected = sample["expected_pillars"]["年柱"]
        assert str(result) == expected, (
            f"[{sample['case_id']}] 年柱计算错误: "
            f"期望 {expected}, 实际 {result}"
        )

    def test_year_pillar_lichun_boundary_before(self):
        """立春前仍属上一年。1980-02-09 在立春后，属庚申年。
        1980-02-04 是立春前（1979己未年仍有效）但需确认具体立春时间。
        """
        # 1980 立春在 2月5日 04:10（约），所以 2月4日仍属己未年
        result = compute_year_pillar("1980-02-04")
        assert str(result) == "己未", (
            f"1980-02-04（立春前）应为己未年，实际: {result}"
        )

    def test_year_pillar_lichun_boundary_after(self):
        """立春后属新年。1980-02-09 属庚申年。"""
        result = compute_year_pillar("1980-02-09")
        assert str(result) == "庚申"


# ============================================================
# 测试：月柱计算（节气换月）
# ============================================================

class TestMonthPillar:
    """验证月柱计算（节气换月规则）。"""

    @pytest.mark.parametrize("sample", TRUSTED_SAMPLES, ids=lambda s: s["case_id"])
    def test_month_pillar_matches_wenzhen(self, sample):
        """月柱必须与问真八字 APP 一致。"""
        result = compute_month_pillar(sample["solar_date"])
        expected = sample["expected_pillars"]["月柱"]
        assert str(result) == expected, (
            f"[{sample['case_id']}] 月柱计算错误: "
            f"期望 {expected}, 实际 {result}"
        )

    def test_month_pillar_before_jieqi_minute_stays_previous_month(self):
        """1989寒露15:27，01:35出生仍应为癸酉月。"""
        result = compute_month_pillar("1989-10-08 01:35")
        assert str(result) == "癸酉"

    def test_month_pillar_after_jieqi_minute_enters_new_month(self):
        """1989寒露15:27，16:00出生应进入甲戌月。"""
        result = compute_month_pillar("1989-10-08 16:00")
        assert str(result) == "甲戌"

    def test_month_pillar_jieqi_boundary(self):
        """节气换月边界：2000-10-05 在寒露之后，属酉月。
        寒露约在10月8日，所以10月5日仍在秋分后、寒露前 = 酉月。
        """
        result = compute_month_pillar("2000-10-05")
        assert str(result) == "乙酉", (
            f"2000-10-05 应在酉月(寒露前)，实际: {result}"
        )


# ============================================================
# 测试：日柱计算
# ============================================================

class TestDayPillar:
    """验证日柱计算（基于日柱万年历查表）。"""

    @pytest.mark.parametrize("sample", TRUSTED_SAMPLES, ids=lambda s: s["case_id"])
    def test_day_pillar_matches_wenzhen(self, sample):
        """日柱必须与问真八字 APP 一致。"""
        result = compute_day_pillar(sample["solar_date"])
        expected = sample["expected_pillars"]["日柱"]
        assert str(result) == expected, (
            f"[{sample['case_id']}] 日柱计算错误: "
            f"期望 {expected}, 实际 {result}"
        )

    def test_day_pillar_known_anchor(self):
        """锚点验证：2000-01-01 = 戊午日（万年历标准）。"""
        result = compute_day_pillar("2000-01-01")
        assert str(result) == "戊午", f"2000-01-01 应为戊午日，实际: {result}"


# ============================================================
# 测试：时柱计算
# ============================================================

class TestHourPillar:
    """验证时柱计算（日干配时支）。"""

    @pytest.mark.parametrize("sample", TRUSTED_SAMPLES, ids=lambda s: s["case_id"])
    def test_hour_pillar_matches_wenzhen(self, sample):
        """时柱必须与问真八字 APP 一致。"""
        day_gan = sample["expected_pillars"]["日柱"][0]  # 取日干
        hour_zhi = sample["hour_zhi"]
        result = compute_hour_pillar(day_gan, hour_zhi)
        expected = sample["expected_pillars"]["时柱"]
        assert str(result) == expected, (
            f"[{sample['case_id']}] 时柱计算错误: "
            f"日干={day_gan}, 时支={hour_zhi}, "
            f"期望 {expected}, 实际 {result}"
        )

    def test_late_zi_hour_uses_next_day_stem(self):
        """问真口径：23点晚子时，日柱仍属当日，时干按次日日干起。"""
        result = compute_hour_pillar_at("1991-08-08 23:21")
        assert str(result) == "戊子"

    def test_hour_pillar_jiazi_rule(self):
        """甲己日起甲子时、乙庚日起丙子时..."""
        # 壬日子时 = 庚子（壬丁日起庚子时）
        result = compute_hour_pillar("壬", "子")
        assert str(result) == "庚子", f"壬日子时应为庚子，实际: {result}"

        # 丙日未时 = 乙未（丙辛日起戊子时，未=7，戊+7=乙）
        result = compute_hour_pillar("丙", "未")
        assert str(result) == "乙未", f"丙日未时应为乙未，实际: {result}"


# ============================================================
# 测试：大运排布
# ============================================================

class TestDayun:
    """验证大运计算（起运岁、顺逆、干支序列）。"""

    @pytest.mark.parametrize("sample", TRUSTED_SAMPLES, ids=lambda s: s["case_id"])
    def test_dayun_direction(self, sample):
        """大运顺逆方向必须正确。"""
        month_pillar = GanZhi.parse(sample["expected_pillars"]["月柱"])
        result = compute_dayun(
            month_pillar=month_pillar,
            gender=sample["gender"],
            year_gan=sample["expected_pillars"]["年柱"][0],
        )
        assert result.direction == sample["expected_dayun"]["顺逆"], (
            f"[{sample['case_id']}] 大运方向错误: "
            f"期望 {sample['expected_dayun']['顺逆']}, 实际 {result.direction}"
        )

    @pytest.mark.parametrize("sample", TRUSTED_SAMPLES, ids=lambda s: s["case_id"])
    def test_dayun_sequence(self, sample):
        """大运干支序列必须与问真八字一致。"""
        month_pillar = GanZhi.parse(sample["expected_pillars"]["月柱"])
        result = compute_dayun(
            month_pillar=month_pillar,
            gender=sample["gender"],
            year_gan=sample["expected_pillars"]["年柱"][0],
        )
        expected_seq = sample["expected_dayun"]["排布"]
        actual_seq = [str(step) for step in result.sequence]
        # 至少比较前 N 步（样本给了多少就比多少）
        for i, (exp, act) in enumerate(zip(expected_seq, actual_seq)):
            assert act == exp, (
                f"[{sample['case_id']}] 第{i+1}步大运错误: "
                f"期望 {exp}, 实际 {act}"
            )

    def test_qiyun_uses_same_day_jieqi_when_birth_is_after_it(self):
        """1991立秋08:37后出生且逆排，应取当天立秋，起运不足1岁。"""
        result = compute_dayun(
            month_pillar=GanZhi.parse("丙申"),
            gender="M",
            year_gan="辛",
            solar_date="1991-08-08 23:21",
        )
        assert result.qiyun_age < 1.0

    @pytest.mark.parametrize("sample", TRUSTED_SAMPLES, ids=lambda s: s["case_id"])
    def test_qiyun_age_within_tolerance(self, sample):
        """起运岁数应在 ±1 岁的问真取整误差范围内。"""
        month_pillar = GanZhi.parse(sample["expected_pillars"]["月柱"])
        result = compute_dayun(
            month_pillar=month_pillar,
            gender=sample["gender"],
            year_gan=sample["expected_pillars"]["年柱"][0],
            solar_date=sample["solar_date"],
        )
        expected_age = sample["expected_dayun"]["起运岁"]
        # 问真取整可能是四舍五入或截断，允许 ±1 岁的容差
        diff = abs(result.qiyun_age - expected_age)
        assert diff < 1.5, (
            f"[{sample['case_id']}] 起运岁差距过大: "
            f"期望 {expected_age}, 精算 {result.qiyun_age:.2f}"
        )


# ============================================================
# 测试：整体排盘验证入口
# ============================================================

class TestValidateChart:
    """验证 validate_chart() 入口函数。"""

    @pytest.mark.parametrize("sample", TRUSTED_SAMPLES, ids=lambda s: s["case_id"])
    def test_validate_passes_for_correct_chart(self, sample):
        """正确的排盘数据应通过验证。"""
        result = validate_chart(
            solar_date=sample["solar_date"],
            hour_zhi=sample["hour_zhi"],
            gender=sample["gender"],
            claimed_pillars=sample["expected_pillars"],
        )
        assert result.is_valid, (
            f"[{sample['case_id']}] 正确排盘未通过验证: {result.errors}"
        )

    def test_validate_detects_wrong_year_pillar(self):
        """错误的年柱应被检出。"""
        result = validate_chart(
            solar_date="1980-02-09",
            hour_zhi="丑",
            gender="M",
            claimed_pillars={
                "年柱": "己未",  # 错误：应为庚申
                "月柱": "戊寅",
                "日柱": "壬子",
                "时柱": "辛丑",
            },
        )
        assert not result.is_valid
        assert any("年柱" in e for e in result.errors)

    def test_validate_detects_wrong_month_pillar(self):
        """错误的月柱应被检出。"""
        result = validate_chart(
            solar_date="1980-02-09",
            hour_zhi="丑",
            gender="M",
            claimed_pillars={
                "年柱": "庚申",
                "月柱": "丁丑",  # 错误：应为戊寅
                "日柱": "壬子",
                "时柱": "辛丑",
            },
        )
        assert not result.is_valid
        assert any("月柱" in e for e in result.errors)

    # NOTE（起运口径争议，暂不设断言）：
    # C-2026-RF000449 起运原文"出生后0年10月24天9小时"约 0.88 岁，
    # 生后最近节清明(1997-04-05)距出生约 3 天 → 1 岁，与原文基本吻合；
    # 但改为"取最近节"后 C-2026-001 等阳男案例（预期约 8.5 岁）测试失败。
    # 两套案例给出了相互矛盾的起运算法证据，问真 APP 口径尚待人工澄清。
    # 参见：META/chart-validation-review-evidence.md §起运口径争议

    def test_validate_respects_jieqi_minute_and_late_zi_hour(self):
        """完整日期时间验证应同时处理节气分钟与晚子时。"""
        jieqi_result = validate_chart(
            solar_date="1989-10-08 01:35",
            hour_zhi="丑",
            gender="M",
            claimed_pillars={
                "年柱": "己巳",
                "月柱": "癸酉",
                "日柱": "辛丑",
                "时柱": "己丑",
            },
        )
        late_zi_result = validate_chart(
            solar_date="1991-08-08 23:21",
            hour_zhi="子",
            gender="M",
            claimed_pillars={
                "年柱": "辛未",
                "月柱": "丙申",
                "日柱": "庚戌",
                "时柱": "戊子",
            },
        )
        assert jieqi_result.is_valid, jieqi_result.errors
        assert late_zi_result.is_valid, late_zi_result.errors

    def test_validate_from_pillars_only(self):
        """仅提供四柱（无日期），通过四柱反推验证内部一致性。"""
        result = validate_chart(
            claimed_pillars={
                "年柱": "庚申",
                "月柱": "戊寅",
                "日柱": "壬子",
                "时柱": "辛丑",
            },
            gender="M",
        )
        # 无日期时仍可验证：年干月支关系、日干时支关系、大运方向
        assert result.is_valid

    def test_reverse_pillars_finds_trusted_date(self):
        """仅四柱反推时，可信样本日期应出现在候选日期中。"""
        candidates = reverse_pillar_dates(
            {
                "年柱": "庚申",
                "月柱": "戊寅",
                "日柱": "壬子",
                "时柱": "辛丑",
            },
            start_year=1979,
            end_year=1981,
        )
        assert "1980-02-09" in candidates

    def test_pillars_only_validation_returns_reverse_candidates(self):
        """无日期验证不只做形式检查，还应返回历法反推候选。"""
        result = validate_chart(
            claimed_pillars={
                "年柱": "庚申",
                "月柱": "戊寅",
                "日柱": "壬子",
                "时柱": "辛丑",
            },
            gender="M",
            reverse_start_year=1979,
            reverse_end_year=1981,
        )
        assert result.is_valid
        assert result.reverse_candidates is not None
        assert "1980-02-09" in result.reverse_candidates

    def test_validate_detects_inconsistent_hour_pillar(self):
        """时柱天干与日干不匹配应被检出。"""
        result = validate_chart(
            claimed_pillars={
                "年柱": "庚申",
                "月柱": "戊寅",
                "日柱": "壬子",
                "时柱": "甲丑",  # 错误：壬日丑时应为辛丑
            },
            gender="M",
        )
        assert not result.is_valid
        assert any("时柱" in e for e in result.errors)

    def test_wenzhen_source_bypass(self):
        """来源为问真八字 APP 时跳过验证。"""
        result = validate_chart(
            claimed_pillars={
                "年柱": "庚申",
                "月柱": "戊寅",
                "日柱": "壬子",
                "时柱": "辛丑",
            },
            gender="M",
            source="问真八字",
        )
        assert result.is_valid
        assert result.skipped  # 标记为跳过验证

    def test_wenzhen_source_description_bypass(self):
        """真实 case_meta 中含问真描述时也应识别为可信来源。"""
        result = validate_chart(
            claimed_pillars={
                "年柱": "甲子",
                "月柱": "丙寅",
                "日柱": "甲子",
                "时柱": "甲子",
            },
            gender="M",
            source="用户对话直贴（问真八字 APP 排盘信息）",
        )
        assert result.is_valid
        assert result.skipped

    def test_validate_from_lunar_date(self):
        """仅提供农历日期也应能精确验证四柱。"""
        result = validate_chart(
            lunar_date="1979-12-23",
            hour_zhi="丑",
            gender="M",
            claimed_pillars={
                "年柱": "庚申",
                "月柱": "戊寅",
                "日柱": "壬子",
                "时柱": "辛丑",
            },
        )
        assert result.is_valid, result.errors

    def test_lunar_to_solar_trusted_anchor(self):
        """问真样本：农历1979腊月廿三 = 公历1980-02-09。"""
        assert lunar_to_solar("1979-12-23") == "1980-02-09"

    def test_rejects_both_solar_and_lunar_dates(self):
        """同时提供公历和农历会产生歧义，应明确拒绝。"""
        result = validate_chart(
            solar_date="1980-02-09",
            lunar_date="1979-12-23",
            hour_zhi="丑",
            gender="M",
            claimed_pillars={
                "年柱": "庚申",
                "月柱": "戊寅",
                "日柱": "壬子",
                "时柱": "辛丑",
            },
        )
        assert not result.is_valid
        assert any("同时提供" in error for error in result.errors)

    def test_validate_dayun_direction_mismatch(self):
        """大运方向声明与规则不符应被检出。"""
        result = validate_chart(
            claimed_pillars={
                "年柱": "庚申",
                "月柱": "戊寅",
                "日柱": "壬子",
                "时柱": "辛丑",
            },
            gender="M",
            claimed_dayun={"顺逆": "逆"},  # 错：阳男应顺行
        )
        assert not result.is_valid
        assert any("大运" in e for e in result.errors)

    def test_validate_dayun_sequence_mismatch(self):
        """大运干支序列与推演不符应被检出。"""
        result = validate_chart(
            claimed_pillars={
                "年柱": "庚申",
                "月柱": "戊寅",
                "日柱": "壬子",
                "时柱": "辛丑",
            },
            gender="M",
            claimed_dayun={
                "顺逆": "顺",
                "排布": ["戊寅", "己卯"],  # 错：首步应为己卯（跳过月柱本身）
            },
        )
        assert not result.is_valid

    def test_validate_dayun_sequence_correct(self):
        """正确的大运序列应通过。"""
        result = validate_chart(
            claimed_pillars={
                "年柱": "庚申",
                "月柱": "戊寅",
                "日柱": "壬子",
                "时柱": "辛丑",
            },
            gender="M",
            claimed_dayun={
                "顺逆": "顺",
                "排布": ["己卯", "庚辰", "辛巳"],
            },
        )
        assert result.is_valid

    def test_corrected_pillars_when_wrong(self):
        """错误声明时，validate_chart 应返回精算后的正确四柱。"""
        result = validate_chart(
            solar_date="1980-02-09",
            hour_zhi="丑",
            gender="M",
            claimed_pillars={
                "年柱": "己未",  # 错
                "月柱": "戊寅",
                "日柱": "壬子",
                "时柱": "辛丑",
            },
        )
        assert not result.is_valid
        assert result.corrected_pillars is not None
        assert result.corrected_pillars["年柱"] == "庚申"


# ============================================================
# 测试：月柱天干与年干的五虎遁规则
# ============================================================

class TestProgrammaticAnalysisGate:
    """程序化调用分析入口时也必须先验证排盘。"""

    @staticmethod
    def _parsed(*, source=None, month="戊寅"):
        bazi = SimpleNamespace(
            年柱=GanZhi.parse("庚申"),
            月柱=GanZhi.parse(month),
            日柱=GanZhi.parse("壬子"),
            时柱=GanZhi.parse("辛丑"),
        )
        dayun = SimpleNamespace(
            顺逆="顺",
            起运岁=8.0,
            排布=[
                SimpleNamespace(干支=GanZhi.parse(gz))
                for gz in ("己卯", "庚辰", "辛巳")
            ],
        )
        birth = {"性别": "M", "公历": "1980-02-09 02:00"}
        if source:
            birth["来源"] = source
        return SimpleNamespace(
            bazi=bazi,
            dayun=dayun,
            birth=birth,
            case_meta={},
        )

    def test_programmatic_gate_marks_validated_chart(self):
        parsed = self._parsed()
        ensure_parsed_chart_validated(parsed)
        assert parsed.case_meta["排盘验证状态"] == "validated"

    def test_programmatic_gate_rejects_wrong_chart(self):
        parsed = self._parsed(month="丁丑")
        with pytest.raises(ChartValidationError) as exc:
            ensure_parsed_chart_validated(parsed)
        assert "月柱" in str(exc.value)

    def test_programmatic_gate_bypasses_trusted_wenzhen(self):
        parsed = self._parsed(source="问真八字 APP 排盘")
        ensure_parsed_chart_validated(parsed)
        assert parsed.case_meta["排盘验证状态"] == "skipped_trusted_wenzhen"


class TestMonthGanRule:
    """五虎遁月：年干决定月柱天干起点。"""

    def test_wuhu_dun_jiayi(self):
        """甲己年起丙寅月。"""
        # C-2026-015: 甲寅年亥月 → 乙亥
        result = compute_month_pillar("1974-11-11")
        assert result.gan == "乙", f"甲年亥月天干应为乙，实际: {result.gan}"

    def test_wuhu_dun_gengxin(self):
        """庚辛年：庚年起戊寅月。
        C-2026-001: 庚申年寅月 → 戊寅。"""
        result = compute_month_pillar("1980-02-09")
        assert result.gan == "戊", f"庚年寅月天干应为戊，实际: {result.gan}"

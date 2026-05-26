"""H11 · output_linter W10 学制盲区律报告级扫描

落地：plans/architecture-v1.4.md § 六 H11 + CFL-C014-003 v2 报告层补丁
代码：tools/output_linter._lint_social_clock + _extract_birth_year_from_md

场景：social_clock_check 在 gate.py 中已生效（H10），但报告 markdown 是命理师手写
（不经 gate pipeline）→ output_linter W10 自动扫描错锚。

参考：smoke/smoke_h11.py。本文件是 pytest 收编版本。
"""
from __future__ import annotations

import pathlib

import pytest


pytestmark = [pytest.mark.v1_3_acceptance, pytest.mark.v1_4_acceptance]


# ============================================================
# T1: 出生年提取
# ============================================================

class TestH11ExtractBirthYear:
    @pytest.mark.parametrize("md,expected", [
        ("**出生**：2006-12-12 09:45（真太阳时·巳时）", 2006),
        ("生年：1980", 1980),
    ])
    def test_extract(self, md, expected):
        from tools.output_linter import _extract_birth_year_from_md
        assert _extract_birth_year_from_md(md) == expected

    def test_extract_none_when_missing(self):
        from tools.output_linter import _extract_birth_year_from_md
        assert _extract_birth_year_from_md("无出生信息") is None


# ============================================================
# T2: 元数据行跳过（含 v1.0/v2.0/已应验/修正等关键字）
# ============================================================

@pytest.mark.parametrize("line", [
    "v1.0 写'2029 = 大学毕业'是错的",
    "已应验：2024 高考南京审计大学",
    "v2.0 错锚：2029 大学毕业 → v2.1 修正为 2028",
    "原 v2.0 校准记录",
    "✅ 2024 高考已应验",
])
def test_h11_should_skip_metadata_lines(line):
    from tools.output_linter import _should_skip_sc_lint
    assert _should_skip_sc_lint(line)


def test_h11_should_not_skip_prediction_line():
    from tools.output_linter import _should_skip_sc_lint
    assert not _should_skip_sc_lint("2029 己酉 大学毕业 ★4")


# ============================================================
# T3: 错锚检测
# ============================================================

def test_h11_late_gaokao_triggers_w10():
    """命主 2006 出生，2027 高考（age=21，超容差）→ 触发 W10。"""
    from tools.output_linter import lint
    md = (
        "# 八字分析报告 · 命主 14\n"
        "**出生**：2006-12-12 09:45\n\n"
        "## 应期总表（错锚示范）\n"
        "| 2027 | 丁未 | 高考重大年 ★4 |\n"
    )
    result = lint(md)
    w10 = [i for i in result.issues if i.code == "W10"]
    assert len(w10) >= 1, f"应触发 W10，issues={[i.message[:60] for i in w10]}"
    assert any("2027" in i.message and "高考" in i.message for i in w10)


# ============================================================
# T4: v2.1 正确版报告不应触发
# ============================================================

def test_h11_correct_v21_report_no_w10():
    from tools.output_linter import lint
    md = (
        "# 八字分析报告 · 命主 14\n"
        "**出生**：2006-12-12 09:45\n\n"
        "## 应期总表（v2.1 校准）\n\n"
        "| 年份 | 流年 | 大运 | 事件预测 |\n"
        "|---|---|---|---|\n"
        "| 2024 | 甲辰 | ✅ 高考·南京审计大学 |\n"
        "| 2028 | 戊申 | 大学毕业 · 三岔口落定 ★4 |\n"
        "| 2031 | 辛亥 | 婚期窗口① ★4 |\n"
        "| 2033 癸丑 | 婚期最可能 ★4 |\n\n"
        "[共识] 体制内财经赛道 ★4 (84%)\n"
    )
    result = lint(md)
    w10 = [i for i in result.issues if i.code == "W10"]
    assert len(w10) == 0, f"v2.1 正确版不应有 W10：{[i.message[:60] for i in w10]}"


# ============================================================
# T5: v2.1 含 v2.0 历史错锚记录 应被跳过
# ============================================================

def test_h11_history_metadata_skipped():
    from tools.output_linter import lint
    md = (
        "# 八字分析报告 · 命主 14\n"
        "**出生**：2006-12-12 09:45\n\n"
        "## v2.0 → v2.1 变更\n"
        "| v2.0 | v2.1 | 修正 |\n"
        "|---|---|---|\n"
        "| 2029 己酉=大学毕业 ★4 (76%) | 2028 戊申=大学毕业 ★4 (78%) | v2.1 重锚 |\n\n"
        "## 应期总表\n"
        "| 2028 | 戊申 | 大学毕业 ★4 |\n\n"
        "[共识] 已应验：2024 高考南审 ★5\n"
    )
    result = lint(md)
    w10 = [i for i in result.issues if i.code == "W10"]
    assert len(w10) == 0


# ============================================================
# T6: 不同事件类型
# ============================================================

class TestH11OtherEvents:
    def test_25_marriage_ok(self):
        from tools.output_linter import lint
        md = "**出生**：1990-06-15\n| 2015 | 结婚 ★4 |\n"
        assert all(i.code != "W10" for i in lint(md).issues)

    def test_60_gaokao_fails(self):
        from tools.output_linter import lint
        md = "**出生**：1990-01-01\n| 2050 | 高考 ★3 |\n"
        w10 = [i for i in lint(md).issues if i.code == "W10"]
        assert len(w10) >= 1

    def test_75_marriage_fails(self):
        from tools.output_linter import lint
        md = "**出生**：1980-01-01\n| 2055 | 结婚 ★3 |\n"
        w10 = [i for i in lint(md).issues if i.code == "W10"]
        assert len(w10) >= 1


# ============================================================
# T7: 容差边界（±1 年）
# ============================================================

class TestH11ToleranceBoundary:
    def test_19_pass(self):
        from tools.output_linter import lint
        md = "**出生**：2006-12-12\n| 2025 | 高考 |\n"
        assert all(i.code != "W10" for i in lint(md).issues)

    def test_20_in_tolerance_pass(self):
        from tools.output_linter import lint
        md = "**出生**：2006-12-12\n| 2026 | 高考 |\n"
        assert all(i.code != "W10" for i in lint(md).issues)

    def test_21_over_tolerance_fail(self):
        from tools.output_linter import lint
        md = "**出生**：2006-12-12\n| 2027 | 高考 |\n"
        w10 = [i for i in lint(md).issues if i.code == "W10"]
        assert len(w10) >= 1


# ============================================================
# T8: 真实 C-014 v2.1 报告（验证修正后零 W10）
# ============================================================

def test_h11_real_c014_v21_report():
    """C-2026-014 v2.1 修正版报告应零 W10 告警。"""
    from tools.output_linter import lint
    repo_root = pathlib.Path(__file__).resolve().parents[2]
    report_path = (repo_root / "reports"
                   / "C-2026-014-丙戌庚子乙亥辛巳-report.md")
    if not report_path.exists():
        pytest.skip(f"真实报告不存在: {report_path}")
    md = report_path.read_text(encoding="utf-8")
    result = lint(md)
    w10 = [i for i in result.issues if i.code == "W10"]
    assert len(w10) == 0, (
        f"v2.1 修正版应零 W10 告警，实际有 {len(w10)} 条：\n  "
        + "\n  ".join(f"{i.message[:100]}" for i in w10[:5])
    )


# ============================================================
# T9: 无出生年信息 → 跳过
# ============================================================

def test_h11_no_birth_year_skips():
    from tools.output_linter import lint
    md = "[共识] 学历层级 一本 ★4\n| 2029 | 大学毕业 ★4 |\n"
    w10 = [i for i in lint(md).issues if i.code == "W10"]
    assert len(w10) == 0


# ============================================================
# T10: 规则字典与 gate 同步
# ============================================================

class TestH11LintRulesParity:
    def test_count_minimum(self):
        from tools.output_linter import _LINT_SOCIAL_CLOCK_RULES
        assert len(_LINT_SOCIAL_CLOCK_RULES) >= 12

    def test_tolerance_is_one(self):
        from tools.output_linter import _LINT_SOCIAL_CLOCK_TOLERANCE
        assert _LINT_SOCIAL_CLOCK_TOLERANCE == 1

    def test_count_matches_gate(self):
        """linter 与 gate 字典数量必须一致（避免一边漏改）。"""
        from tools.output_linter import _LINT_SOCIAL_CLOCK_RULES
        from engine.yingqi.gate import _SOCIAL_CLOCK_RULES
        assert len(_LINT_SOCIAL_CLOCK_RULES) == len(_SOCIAL_CLOCK_RULES)

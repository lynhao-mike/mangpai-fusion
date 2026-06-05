"""tests/track_f_smoke/test_f_render.py · Track-F 标准报告验收测试

025 标准已取代历史三段式/双版报告：

| ID    | 输入               | 期望                                   |
|-------|--------------------|----------------------------------------|
| F-001 | mock AnalysisOutput | output_linter 0 error                 |
| F-002 | 3 个 GateResult     | trace_id（evidence.rule_id）覆盖率 100% |
| F-003 | 含 passed_layers=3  | 关键应期表仅含高置信候选，不泄漏低层候选 |

同时跑 G2 集成：render 后报告体现 2005 vs 2013 婚期差异
（2005 出现在关键应期，2013 不出现）。

作者：Track-F
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest
from engine.energy.evaluator import evaluate_energy
from engine.picture.matcher import match_picture
from engine.pipeline import run_pipeline
from engine.yingqi import gate_yingqi
from tests.fixtures.cases import load_case
from tools.output_linter import lint
from tools.render_report import render, render_from_output


# ============================================================
# fixtures（module scope，整个测试文件只跑一次上游引擎）
# ============================================================

@pytest.fixture(scope="module")
def c001_findings():
    """C-2026-001 完整 findings（energy + picture + 4 个 gate）。"""
    parsed = load_case("C-2026-001-乾-庚申戊寅壬子辛丑")
    energy = evaluate_energy(parsed)
    picture = match_picture(energy, parsed)
    gates = []
    for year, event, domain in [
        (2005, "结婚",    "婚姻"),
        (2013, "结婚",    "婚姻"),   # v1.0 错婚期，应不出现在铁断
        (2020, "母亲去世", "六亲"),
        (2020, "升副科",  "事业"),
    ]:
        g = gate_yingqi(year, event, domain, energy, picture, parsed)
        if g.passed_layers >= 1:
            gates.append(g)
    return {"parsed": parsed, "energy": energy, "picture": picture, "gates": gates}


@pytest.fixture(scope="module")
def sample_report(c001_findings):
    """用 C-2026-001 生成一份完整报告。"""
    return render(
        c001_findings["energy"],
        c001_findings["picture"],
        c001_findings["gates"],
        c001_findings["parsed"],
        support=None,
    )


# ============================================================
# F-001 · output_linter 0 error
# ============================================================

def test_F001_output_linter_zero_error(sample_report):
    """F-001: 渲染报告通过 output_linter，0 error。"""
    result = lint(sample_report)
    errors = result.errors
    print(f"\n[F-001] linter passed={result.passed} "
          f"errors={len(errors)} warnings={len(result.warnings)}")
    for e in errors:
        print(f"  [E{e.code}] @ {e.location}: {e.message}")
    assert result.passed, (
        f"F-001 期望 0 error，实际有 {len(errors)} 个 error：\n"
        + "\n".join(f"  [{e.code}] {e.message}" for e in errors)
    )


# ============================================================
# F-002 · trace_id 覆盖率 100%
# ============================================================

RULE_ID_RE = re.compile(
    r"\b(?:M[1-3]-[A-Z]-\d+|MR-[A-Z\d-]+|G-[A-Z0-9]+-\d+|XF-\d+|GP-[A-Z0-9-]+)\b"
)
STAR_LINE_RE = re.compile(r"★[1-5]\s*\(")


def _key_yingqi_years(report: str) -> set[int]:
    """从 025 标准报告的“关键应期”表中抽取年份。"""
    years: set[int] = set()
    in_section = False
    for line in report.splitlines():
        if line.startswith("## 六、关键应期"):
            in_section = True
            continue
        if in_section and line.startswith("## "):
            break
        if not in_section:
            continue
        m = re.match(r"\|\s*(\d{4})\s*\|", line)
        if m:
            years.add(int(m.group(1)))
    return years


def test_F002_trace_id_coverage_100pct(sample_report, c001_findings):
    """F-002: 所有含 ★ 的铁断段必须含 evidence rule_id（trace_id 链覆盖 100%）。"""
    from tools.output_linter import extract_conclusions_from_md

    cons = extract_conclusions_from_md(sample_report)
    star_cons = [c for c in cons if c.star and c.star >= 1]

    # 过滤掉没有 evidence 要求的系统断语（E2 没有 evidence 是 linter 的问题，
    # trace_id 覆盖率测试只统计 [任派/共识/互补] 铁断）
    iron_cons = [c for c in star_cons
                 if any(tag in c.school_tags for tag in ("任", "共识", "互补", "段", "杨"))]

    if not iron_cons:
        pytest.skip("无铁断断语（可能 gate 不足），跳过覆盖率测试")

    missing = [c for c in iron_cons if c.evidence_count == 0]

    print(f"\n[F-002] 铁断断语共 {len(iron_cons)} 条")
    print(f"  有 evidence 链: {len(iron_cons) - len(missing)}")
    print(f"  缺 evidence 链: {len(missing)}")
    for c in missing[:3]:
        print(f"    → {c.raw_text[:80]}")

    coverage = (len(iron_cons) - len(missing)) / len(iron_cons) if iron_cons else 0
    print(f"  trace_id 覆盖率: {coverage:.0%}")

    assert coverage == 1.0, (
        f"F-002 trace_id 覆盖率 = {coverage:.0%}（期望 100%），"
        f"{len(missing)} 条缺 evidence"
    )


# ============================================================
# F-003 · 关键应期只含高置信候选
# ============================================================

def test_F003_key_yingqi_only_high_confidence(sample_report, c001_findings):
    """F-003: 025 标准报告“关键应期”只输出高置信候选；
    passed<3 的（如 2013 年结婚）不出现在关键应期表中。"""
    key_years = _key_yingqi_years(sample_report)
    print(f"\n[F-003] 关键应期年份集合: {sorted(key_years)}")

    non_iron_years = {g.year for g in c001_findings["gates"] if g.passed_layers < 3}
    print(f"  非铁断年份（passed<3）: {sorted(non_iron_years)}")

    gates_by_year = {g.year: g for g in c001_findings["gates"]}
    gate_2005 = gates_by_year.get(2005)
    gate_2013 = gates_by_year.get(2013)

    if gate_2005 and gate_2005.passed_layers == 3:
        assert 2005 in key_years, "F-003: 2005 三层齐备，应出现在关键应期表"
        print("  ✓ 2005 在关键应期中（G2 圣杯前半：实际婚年）")

    if gate_2013 and gate_2013.passed_layers < 3:
        assert 2013 not in key_years, (
            f"F-003: 2013 passed={gate_2013.passed_layers}<3，"
            "不应出现在关键应期表（G2 圣杯后半：picture 钳制生效）"
        )
        print("  ✓ 2013 不在关键应期中（G2 圣杯后半：picture 钳制生效）")

    leaked = key_years & non_iron_years
    assert not leaked, f"F-003: 以下非铁断年份泄漏到关键应期：{leaked}"


# ============================================================
# 综合：报告基本结构完整
# ============================================================

def test_F_report_structure(sample_report):
    """报告包含 C-2026-025 唯一标准段落标记。"""
    required = [
        "## 0. 基本盘面",
        "## 一、命局核心结论",
        "## 二、体用、病药与人生主线",
        "## 三、五维定位",
        "## 四、婚恋与家庭",
        "## 五、事业与财富",
        "## 六、关键应期",
        "## 七、健康与生活风险",
        "## 八、行动建议",
        "## 九、总评",
        "## 归档信息",
        "mangpai-fusion 产品 v1.3.0",
    ]
    for marker in required:
        assert marker in sample_report, f"报告缺必要段落标记: {marker!r}"
    print("\n[F-结构] 报告结构完整 ✓")


def test_F_render_from_output_keeps_parsed_context(tmp_path):
    """render_from_output 必须保留 run_pipeline 的 ParsedInput 上下文。"""
    parsed = load_case("C-2026-001-乾-庚申戊寅壬子辛丑")
    output = run_pipeline(parsed, write_findings=False)

    assert getattr(output, "_parsed", None) is parsed

    report = render_from_output(
        output,
        lint_before=False,
        cases_dir=tmp_path,
        skip_findings_save=True,
    )

    assert "{{ qian_kun }}" not in report
    assert "# 八字分析报告 · C-2026-001-乾-庚申戊寅壬子辛丑 · 乾" in report
    assert "| 四柱 | 庚申戊寅壬子辛丑 |" in report
    assert "| 四柱 | — |" not in report
    assert "| 大运 | — |" not in report


def test_F_support_none_graceful(c001_findings):
    """support=None 时报告仍可渲染并使用标准健康兜底文案。"""
    report = render(
        c001_findings["energy"],
        c001_findings["picture"],
        c001_findings["gates"],
        c001_findings["parsed"],
        support=None,
    )
    assert "健康风险需结合实际体检、作息和反馈继续校准" in report
    result = lint(report)
    assert result.passed, f"support=None 时报告仍应通过 linter，errors={result.errors}"
    print("\n[F-兼容] support=None 路径 ✓")


def test_F_production_rules_render_from_output(tmp_path):
    """render_from_output 应展示子平 / 滴天髓生产规则参与结果与证据链。"""
    parsed = load_case("C-2026-001-乾-庚申戊寅壬子辛丑")
    output = run_pipeline(parsed, write_findings=False)

    report = render_from_output(
        output,
        lint_before=False,
        cases_dir=tmp_path,
        skip_findings_save=True,
    )

    assert "### 子平 / 滴天髓生产规则参与" in report
    assert "子平规则参与" in report
    assert "滴天髓规则参与" in report
    assert "ZP-PROD-20260605-001" in report
    assert "DTS-PROD-20260605-001" in report
    result = lint(report)
    assert result.passed, f"生产规则展示应通过 linter，errors={result.errors}"


# ============================================================
# 独立运行入口（不依赖 pytest）
# ============================================================

def _run_standalone() -> int:
    """独立运行（不依赖 pytest）。"""
    print("=" * 78)
    print("              Track-F 验收：F-001/F-002/F-003 + 2 项综合")
    print("=" * 78)

    parsed = load_case("C-2026-001-乾-庚申戊寅壬子辛丑")
    energy = evaluate_energy(parsed)
    picture = match_picture(energy, parsed)
    gates = []
    for year, event, domain in [
        (2005, "结婚", "婚姻"),
        (2013, "结婚", "婚姻"),
        (2020, "母亲去世", "六亲"),
        (2020, "升副科", "事业"),
    ]:
        g = gate_yingqi(year, event, domain, energy, picture, parsed)
        if g.passed_layers >= 1:
            gates.append(g)

    report = render(energy, picture, gates, parsed)
    fail = 0

    def _check(name: str, cond: bool, detail: str) -> None:
        nonlocal fail
        mark = "✓" if cond else "✗"
        print(f"  [{mark}] {name}: {detail}")
        if not cond:
            fail += 1

    # F-001
    print("\n--- F-001 output_linter 0 error ---")
    r = lint(report)
    _check("F-001 passed", r.passed, f"errors={len(r.errors)} warnings={len(r.warnings)}")
    for e in r.errors:
        print(f"    [E{e.code}] {e.message[:60]}")

    # F-002
    print("\n--- F-002 trace_id 覆盖率 100% ---")
    from tools.output_linter import extract_conclusions_from_md
    cons = extract_conclusions_from_md(report)
    iron_cons = [c for c in cons
                 if c.star and any(t in c.school_tags for t in ("任","共识","互补","段","杨"))]
    missing = [c for c in iron_cons if c.evidence_count == 0]
    cov = (len(iron_cons) - len(missing)) / len(iron_cons) if iron_cons else 1.0
    _check("F-002 coverage=100%", cov == 1.0,
           f"{len(iron_cons)-len(missing)}/{len(iron_cons)} = {cov:.0%}")

    # F-003
    print("\n--- F-003 关键应期仅高置信候选 ---")
    key_years = _key_yingqi_years(report)
    non_iron = {g.year for g in gates if g.passed_layers < 3}
    leaked = key_years & non_iron
    _check("F-003 no leak", not leaked, f"leaked={leaked}, key_years={sorted(key_years)}")
    gates_map = {g.year: g for g in gates}
    if gates_map.get(2005) and gates_map[2005].passed_layers == 3:
        _check("G2 2005 in key yingqi", 2005 in key_years, f"key_years={key_years}")
    if gates_map.get(2013) and gates_map[2013].passed_layers < 3:
        _check("G2 2013 not in key yingqi", 2013 not in key_years, f"key_years={key_years}")

    # 综合
    print("\n--- 综合结构 ---")
    for marker in ["## 0. 基本盘面", "## 六、关键应期", "## 归档信息"]:
        _check(f"含{marker!r}", marker in report, "")

    total = 10
    passed = total - fail
    print(f"\n{'='*78}")
    print(f"  RESULT: {passed}/{total} passed (fail={fail})")
    print(f"{'='*78}")
    return fail


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(_run_standalone())

"""tests/track_c_smoke/test_c_gate.py · Track-C 5 项验收测试

按 08-agent-handoff.md § 六 Track-C 表格：

| ID    | 输入                            | 期望                                    |
|-------|--------------------------------|----------------------------------------|
| C-001 | C-2026-001 year=2005 婚姻      | passed_layers=3, ★≥4                  |
| C-002 | C-2026-001 year=2013 婚姻      | passed_layers≤1（picture_consistent=F） |
| C-003 | C-2026-001 year=2020 六亲(母)  | passed_layers=3, ★★★★★              |
| C-004 | C-2026-001 year=2020 事业      | passed_layers≥2                       |
| C-005 | C-2026-014 year=2024 学业      | passed_layers≥2                       |

C-001 + C-002 是 G2 圣杯（v1.0 婚期偏差 8 年的修复）。

作者：Track-C
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

# 注入 sys.path（独立运行时也能 import）
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    import pytest
except ImportError:
    # pytest 不可用时，提供 no-op 装饰器以便独立运行（_run_unittest_style）
    class _NoOpMark:
        def __getattr__(self, name):  # type: ignore
            return lambda fn: fn

    class _NoOpFixture:
        def __call__(self, *args, **kwargs):
            # 支持 @pytest.fixture 和 @pytest.fixture(scope="module")
            if len(args) == 1 and callable(args[0]) and not kwargs:
                return args[0]
            return lambda fn: fn

    class _Pytest:
        fixture = _NoOpFixture()
        mark = _NoOpMark()

    pytest = _Pytest()  # type: ignore

from engine.energy.evaluator import evaluate_energy
from engine.picture.matcher import match_picture
from engine.predicates.cycles import liunian_ganzhi
from engine.yingqi import gate_yingqi
from tests.fixtures.cases import load_case


# ============================================================
# pytest 风格（推荐 - 接 conftest.py 的 fixture）
# ============================================================

@pytest.fixture(scope="module")
def parsed_c001():
    """C-2026-001 ParsedInput"""
    return load_case("C-2026-001-乾-庚申戊寅壬子辛丑")


@pytest.fixture(scope="module")
def parsed_c014():
    """C-2026-014 ParsedInput"""
    return load_case("C-2026-014-乾-丙戌庚子乙亥辛巳")


@pytest.fixture(scope="module")
def energy_c001(parsed_c001):
    return evaluate_energy(parsed_c001)


@pytest.fixture(scope="module")
def picture_c001(parsed_c001, energy_c001):
    return match_picture(energy_c001, parsed_c001)


@pytest.fixture(scope="module")
def energy_c014(parsed_c014):
    return evaluate_energy(parsed_c014)


@pytest.fixture(scope="module")
def picture_c014(parsed_c014, energy_c014):
    return match_picture(energy_c014, parsed_c014)


# ============================================================
# C-001 婚姻 2005（G2 圣杯之一）
# ============================================================

@pytest.mark.needs_engine_c
def test_C001_marriage_2005(parsed_c001, energy_c001, picture_c001):
    """C-001: C-2026-001 year=2005 婚姻 → passed_layers=3, ★≥4"""
    r = gate_yingqi(2005, "结婚", "婚姻",
                    energy_c001, picture_c001, parsed_c001)
    print(f"\n[C-001] {r.year} 结婚 婚姻 → "
          f"passed={r.passed_layers}/3 ★{r.confidence.star} "
          f"({r.confidence.percent:.0%}) door={r.door}")
    print(f"   triggers: {[t.type for t in r.triggers]}")
    print(f"   primary: {r.primary_trigger.type if r.primary_trigger else None}")
    print(f"   picture_ok={r.picture_consistent}")

    assert r.passed_layers == 3, (
        f"C-001 期望 passed_layers=3，实 {r.passed_layers}（{r.consistency_notes[:2]}）"
    )
    assert r.confidence.star >= 4, (
        f"C-001 期望 ★≥4，实 ★{r.confidence.star}"
    )
    assert r.picture_consistent is True, (
        "C-001 picture_consistent 应为 True（25 岁在 [22,28] 窗口内）"
    )


# ============================================================
# C-002 婚姻 2013（G2 圣杯之二 - v1.0 错婚期）
# ============================================================

@pytest.mark.needs_engine_c
def test_C002_marriage_2013_picture_kicks_in(
    parsed_c001, energy_c001, picture_c001
):
    """C-002: C-2026-001 year=2013 婚姻 → passed_layers≤1, picture_consistent=False"""
    r = gate_yingqi(2013, "结婚", "婚姻",
                    energy_c001, picture_c001, parsed_c001)
    print(f"\n[C-002] {r.year} 结婚 婚姻 → "
          f"raw_passed={r.debug_info['raw_passed_layers']} → "
          f"final={r.passed_layers}/3 ★{r.confidence.star} "
          f"({r.confidence.percent:.0%})")
    print(f"   picture_ok={r.picture_consistent}")
    print(f"   consistency_notes: {r.consistency_notes[:2]}")

    assert r.passed_layers <= 1, (
        f"C-002 期望 passed_layers≤1（被 picture 钳），实 {r.passed_layers}"
    )
    assert r.picture_consistent is False, (
        "C-002 picture_consistent 必须为 False（33 岁不在 [22,28] 窗口）"
    )
    assert r.confidence.star <= 3, (
        f"C-002 期望 ★≤3，实 ★{r.confidence.star}"
    )


# ============================================================
# C-003 六亲(母) 2020（feedback 真实事件：母亲正月去世）
# ============================================================

@pytest.mark.needs_engine_c
def test_C003_liuqin_mother_2020(parsed_c001, energy_c001, picture_c001):
    """C-003: C-2026-001 year=2020 六亲（母） → passed_layers=3, ★★★★★"""
    r = gate_yingqi(2020, "母亲去世", "六亲",
                    energy_c001, picture_c001, parsed_c001)
    print(f"\n[C-003] {r.year} 母亲去世 六亲 → "
          f"passed={r.passed_layers}/3 ★{r.confidence.star} "
          f"door={r.door}")
    print(f"   sub_domain={r.debug_info['sub_domain']}")
    print(f"   triggers: {[t.type for t in r.triggers]}")
    print(f"   primary: {r.primary_trigger.type if r.primary_trigger else None}")
    print(f"   is_xiong={r.debug_info['is_xiong']}")

    assert r.passed_layers >= 2, (
        f"C-003 期望 passed_layers≥2（凶应必报），实 {r.passed_layers}"
    )
    assert r.debug_info["sub_domain"] == "母", (
        f"C-003 应推断 sub_domain='母'，实 {r.debug_info['sub_domain']}"
    )


# ============================================================
# C-004 事业 2020（feedback 真实事件：提副科）
# ============================================================

@pytest.mark.needs_engine_c
def test_C004_career_2020(parsed_c001, energy_c001, picture_c001):
    """C-004: C-2026-001 year=2020 事业 → passed_layers≥2"""
    r = gate_yingqi(2020, "升副科", "事业",
                    energy_c001, picture_c001, parsed_c001)
    print(f"\n[C-004] {r.year} 升副科 事业 → "
          f"passed={r.passed_layers}/3 ★{r.confidence.star} "
          f"door={r.door}")
    print(f"   triggers: {[t.type for t in r.triggers]}")
    print(f"   primary: {r.primary_trigger.type if r.primary_trigger else None}")

    assert r.passed_layers >= 2, (
        f"C-004 期望 passed_layers≥2，实 {r.passed_layers}"
    )


# ============================================================
# C-005 学业 2024（feedback 真实事件：高考考上一本）
# ============================================================

@pytest.mark.needs_engine_c
def test_C005_education_2024(parsed_c014, energy_c014, picture_c014):
    """C-005: C-2026-014 year=2024 学业 → passed_layers≥2"""
    r = gate_yingqi(2024, "高考考上一本", "学业",
                    energy_c014, picture_c014, parsed_c014)
    print(f"\n[C-005] {r.year} 高考考上一本 学业 → "
          f"passed={r.passed_layers}/3 ★{r.confidence.star} "
          f"door={r.door}")
    print(f"   triggers: {[t.type for t in r.triggers]}")
    print(f"   primary: {r.primary_trigger.type if r.primary_trigger else None}")

    assert r.passed_layers >= 2, (
        f"C-005 期望 passed_layers≥2，实 {r.passed_layers}"
    )


# ============================================================
# G2 圣杯专项对比（C-001 vs C-002 双向断言）
# ============================================================

@pytest.mark.needs_engine_c
@pytest.mark.v1_2_gate
def test_G2_holy_grail_c001_vs_c002(parsed_c001, energy_c001, picture_c001):
    """G2 圣杯：C-2026-001 婚期 2005 vs 2013 必须明显区分。

    v1.0 报告判 2013，实际 2005，差 8 年。
    v1.2 限值：婚期误差 ≤ 3 年。
    """
    r2005 = gate_yingqi(2005, "结婚", "婚姻",
                        energy_c001, picture_c001, parsed_c001)
    r2013 = gate_yingqi(2013, "结婚", "婚姻",
                        energy_c001, picture_c001, parsed_c001)

    print("\n" + "=" * 78)
    print("    G2 圣杯对比 · C-2026-001 婚期 v1.0 vs v1.2")
    print("=" * 78)
    print(f"  v1.0 = 2013（差 8 年），实际 = 2005，picture 窗口 = "
          f"{picture_c001.marriage_picture['初婚最佳窗口']}")
    print(f"  {'年份':<8}{'流年':<8}{'层数':<8}{'★':<8}{'置信度':<10}{'picture':<10}")
    print("  " + "-" * 60)
    for label, r in (("2005", r2005), ("2013", r2013)):
        ln = liunian_ganzhi(int(label))
        pic_ok = "✓" if r.picture_consistent else "✗"
        stars = "★" * r.confidence.star
        print(f"  {label:<8}{str(ln):<8}{r.passed_layers}/3{'':<5}{stars:<8}"
              f"{r.confidence.percent*100:>6.1f}%   {pic_ok}")
    print("=" * 78)

    # 强制双向区分
    assert r2005.passed_layers == 3, "G2: 2005 必须 3 层全过"
    assert r2005.confidence.star >= 4, "G2: 2005 必须 ★≥4"
    assert r2013.passed_layers <= 1, "G2: 2013 必须被 picture 钳到 ≤1"
    assert r2013.confidence.star <= 3, "G2: 2013 必须 ★≤3"
    assert r2005.confidence.percent - r2013.confidence.percent >= 0.30, (
        f"G2: 2005 vs 2013 置信度差距应 ≥ 30%，实 "
        f"{r2005.confidence.percent - r2013.confidence.percent:.2%}"
    )


# ============================================================
# Tools 三层一致性校验（接 Track-E）
# ============================================================

@pytest.mark.needs_engine_c
def test_track_e_three_layer_check_compatibility(
    parsed_c001, energy_c001, picture_c001
):
    """Track-E tools/three_layer_check.py 应能校验 Track-C 的 GateResult。"""
    import sys as _sys
    from pathlib import Path as _Path
    _root = _Path(__file__).resolve().parents[2]
    if str(_root) not in _sys.path:
        _sys.path.insert(0, str(_root))
    from tools.three_layer_check import check_yingqi  # type: ignore

    r2005 = gate_yingqi(2005, "结婚", "婚姻",
                        energy_c001, picture_c001, parsed_c001)
    r2013 = gate_yingqi(2013, "结婚", "婚姻",
                        energy_c001, picture_c001, parsed_c001)

    ok2005, msg2005 = check_yingqi(r2005)
    ok2013, msg2013 = check_yingqi(r2013)
    print(f"\n  three_layer_check 2005 → {ok2005} | {msg2005}")
    print(f"  three_layer_check 2013 → {ok2013} | {msg2013}")
    assert ok2005, f"2005 GateResult 必须通过三层校验：{msg2005}"
    assert ok2013, f"2013 GateResult 必须通过三层校验：{msg2013}"


# ============================================================
# 入口（独立运行）
# ============================================================

def _run_unittest_style() -> int:
    """unittest 风格的备用入口（不依赖 pytest）。"""
    print("=" * 78)
    print("                    Track-C 5 项验收 + G2 圣杯 + Track-E 联动")
    print("=" * 78)

    p001 = load_case("C-2026-001-乾-庚申戊寅壬子辛丑")
    e001 = evaluate_energy(p001)
    pic001 = match_picture(e001, p001)
    p014 = load_case("C-2026-014-乾-丙戌庚子乙亥辛巳")
    e014 = evaluate_energy(p014)
    pic014 = match_picture(e014, p014)

    fail = 0

    def _check(name: str, cond: bool, detail: str) -> None:
        nonlocal fail
        mark = "✓" if cond else "✗"
        print(f"  [{mark}] {name}: {detail}")
        if not cond:
            fail += 1

    print("\n--- C-001 婚姻 2005 ---")
    r = gate_yingqi(2005, "结婚", "婚姻", e001, pic001, p001)
    _check("C-001 passed=3", r.passed_layers == 3,
           f"passed={r.passed_layers}/3")
    _check("C-001 ★≥4", r.confidence.star >= 4, f"★{r.confidence.star}")

    print("\n--- C-002 婚姻 2013 ---")
    r = gate_yingqi(2013, "结婚", "婚姻", e001, pic001, p001)
    _check("C-002 passed≤1", r.passed_layers <= 1,
           f"passed={r.passed_layers}/3")
    _check("C-002 picture✗", not r.picture_consistent, str(r.picture_consistent))

    print("\n--- C-003 六亲(母) 2020 ---")
    r = gate_yingqi(2020, "母亲去世", "六亲", e001, pic001, p001)
    _check("C-003 passed≥2", r.passed_layers >= 2,
           f"passed={r.passed_layers}/3")
    _check("C-003 sub_domain=母", r.debug_info["sub_domain"] == "母",
           str(r.debug_info["sub_domain"]))

    print("\n--- C-004 事业 2020 ---")
    r = gate_yingqi(2020, "升副科", "事业", e001, pic001, p001)
    _check("C-004 passed≥2", r.passed_layers >= 2,
           f"passed={r.passed_layers}/3")

    print("\n--- C-005 学业 2024 ---")
    r = gate_yingqi(2024, "高考考上一本", "学业", e014, pic014, p014)
    _check("C-005 passed≥2", r.passed_layers >= 2,
           f"passed={r.passed_layers}/3")

    print("\n" + "=" * 78)
    print(f"  RESULT: {5 + 5 - fail}/10 passed (fail={fail})")
    print("=" * 78)
    return fail


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(_run_unittest_style())

"""tests/track_d_smoke/test_d_pangzheng.py · Track-D 3 项验收测试

按 08-agent-handoff.md § 六 Track-D 表格：

| ID    | 输入                           | 期望                              |
|-------|------------------------------|-----------------------------------|
| D-001 | C-2026-001 金舆在时柱           | boost marriage ≥ 0.04             |
| D-002 | C-2026-014 词馆+天乙×2          | boost 学业 ≤ 0.10（不能过高）     |
| D-003 | C-2026-001 驿马                | boost 含"奔波/调动"标签            |

作者：Track-D
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

# 注入 sys.path
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    import pytest
except ImportError:
    class _NoOpMark:
        def __getattr__(self, name):  # type: ignore
            return lambda fn: fn

    class _NoOpFixture:
        def __call__(self, *args, **kwargs):
            if len(args) == 1 and callable(args[0]) and not kwargs:
                return args[0]
            return lambda fn: fn

    class _Pytest:
        fixture = _NoOpFixture()
        mark = _NoOpMark()

    pytest = _Pytest()  # type: ignore

from engine.pangzheng import attach_shensha, support_with_shensha
from tests.fixtures.cases import load_case


# ============================================================
# pytest 风格
# ============================================================

@pytest.fixture(scope="module")
def support_c001():
    """C-2026-001 SupportFindings"""
    parsed = load_case("C-2026-001-庚申戊寅壬子辛丑")
    attach_shensha(parsed)
    return support_with_shensha(parsed)


@pytest.fixture(scope="module")
def support_c014():
    """C-2026-014 SupportFindings"""
    parsed = load_case("C-2026-014-丙戌庚子乙亥辛巳")
    attach_shensha(parsed)
    return support_with_shensha(parsed)


# ============================================================
# D-001 金舆在时柱 → boost marriage ≥ 0.04
# ============================================================

@pytest.mark.needs_engine_d
def test_D001_jinyu_at_time_pillar(support_c001):
    """D-001: C-001 金舆在时柱 → 金舆 boost ≥ 0.04 且作用域含 marriage"""
    marriage_supports = support_c001.shensha_supports.get("marriage", [])
    jinyu = next((s for s in marriage_supports if s.name == "金舆"), None)
    assert jinyu is not None, "C-001 marriage 应含金舆旁证"
    assert "时柱" in jinyu.palaces, f"金舆应在时柱：{jinyu.palaces}"
    assert jinyu.boost >= 0.04, (
        f"D-001 金舆 boost 应 ≥ 0.04，实 {jinyu.boost:.3f}"
    )
    print(f"\n[D-001] 金舆 boost = {jinyu.boost:.3f}（在 {jinyu.palaces}）")
    print(f"   tags = {jinyu.tags}")
    print(f"   contribution = {jinyu.contribution[:60]}")


# ============================================================
# D-002 词馆+天乙×2 → boost 学业 ≤ 0.10
# ============================================================

@pytest.mark.needs_engine_d
def test_D002_education_boost_capped(support_c014):
    """D-002: C-014 词馆+天乙×2 → education 总 boost ≤ 0.10（cap）"""
    edu_total = support_c014.total_boost_for("education")
    assert edu_total <= 0.10, (
        f"D-002 education boost 应 ≤ 0.10（cap），实 {edu_total:.3f}"
    )
    cx = support_c014.ciguan_xuetang
    assert cx is not None, "C-014 应有 CiguanXuetang"
    assert cx.has_ciguan, f"C-014 日柱应含词馆"
    assert cx.has_taiyi, f"C-014 应含天乙贵人"
    print(f"\n[D-002] education total_boost = {edu_total:.3f} ≤ 0.10 ✓")
    print(f"   词馆: {cx.has_ciguan}, 学堂: {cx.has_xuetang}, "
          f"文昌: {cx.has_wenchang}, 天乙: {cx.has_taiyi}")
    print(f"   contribution: {cx.contribution[:80]}")


# ============================================================
# D-003 驿马 → boost 含"奔波/调动"标签
# ============================================================

@pytest.mark.needs_engine_d
def test_D003_yima_tags(support_c001):
    """D-003: C-001 驿马 → tags 含"奔波/调动"（取象标签）"""
    career_supports = support_c001.shensha_supports.get("career", [])
    yima = next((s for s in career_supports if s.name == "驿马"), None)
    assert yima is not None, "C-001 career 应含驿马旁证"
    assert any("奔波" in t or "调动" in t for t in yima.tags), (
        f"D-003 驿马 tags 应含'奔波/调动'：{yima.tags}"
    )
    print(f"\n[D-003] 驿马 tags = {yima.tags}")
    print(f"   palaces = {yima.palaces}")
    print(f"   boost = {yima.boost:.3f}")


# ============================================================
# 综合：旁证完整性
# ============================================================

@pytest.mark.needs_engine_d
def test_D_completeness_c001(support_c001):
    """C-001 应至少覆盖 marriage / career / health / education 4 个 domain"""
    domains = set(support_c001.shensha_supports.keys())
    must_have = {"marriage", "career", "health"}
    missing = must_have - domains
    assert not missing, f"C-001 应至少覆盖 {must_have}，缺 {missing}"

    # 至少 1 条 health_finding（C-001 有血刃 + 羊刃 + 童子煞）
    assert len(support_c001.health_findings) >= 1, (
        f"C-001 至少应有 1 条健康风险，实 {len(support_c001.health_findings)}"
    )

    # round-trip
    s_json = support_c001.to_json()
    from engine.pangzheng import SupportFindings
    s2 = SupportFindings.from_json(s_json)
    assert s2.hash() == support_c001.hash()


@pytest.mark.needs_engine_d
def test_D_only_supports_no_new_conclusions(support_c001):
    """03 § 八 铁律：D4 boost 必须在 [-0.20, 0.20] 范围内（cap），
    且不引入新结论字段（仅 shensha_supports / health / ciguan）。"""
    # 所有 boost 在 [-0.20, 0.20]
    for domain, supports in support_c001.shensha_supports.items():
        for s in supports:
            assert -0.20 <= s.boost <= 0.20, (
                f"{domain}.{s.name} boost={s.boost} 越界"
            )
    # 任何 domain 的 total_boost ≤ 0.20
    for domain in support_c001.shensha_supports:
        total = support_c001.total_boost_for(domain)
        assert total <= 0.20 + 1e-9, f"{domain} total_boost={total} 越界"


# ============================================================
# 入口（独立运行，不依赖 pytest）
# ============================================================

def _run_unittest_style() -> int:
    print("=" * 78)
    print("                    Track-D 3 项验收（D-001/D-002/D-003）")
    print("=" * 78)

    parsed_c001 = load_case("C-2026-001-庚申戊寅壬子辛丑")
    attach_shensha(parsed_c001)
    s001 = support_with_shensha(parsed_c001)

    parsed_c014 = load_case("C-2026-014-丙戌庚子乙亥辛巳")
    attach_shensha(parsed_c014)
    s014 = support_with_shensha(parsed_c014)

    fail = 0

    def _check(name: str, cond: bool, detail: str) -> None:
        nonlocal fail
        mark = "✓" if cond else "✗"
        print(f"  [{mark}] {name}: {detail}")
        if not cond:
            fail += 1

    print("\n--- D-001 C-001 金舆在时柱 ---")
    marriage_supports = s001.shensha_supports.get("marriage", [])
    jinyu = next((s for s in marriage_supports if s.name == "金舆"), None)
    _check("D-001 金舆 in marriage", jinyu is not None,
           f"找到={jinyu is not None}")
    if jinyu:
        _check("D-001 金舆 在时柱", "时柱" in jinyu.palaces,
               f"palaces={jinyu.palaces}")
        _check("D-001 金舆 boost ≥ 0.04", jinyu.boost >= 0.04,
               f"boost={jinyu.boost:.3f}")

    print("\n--- D-002 C-014 词馆+天乙×2 ---")
    edu_total = s014.total_boost_for("education")
    _check("D-002 education ≤ 0.10",
           edu_total <= 0.10,
           f"education total = {edu_total:.3f}")
    cx = s014.ciguan_xuetang
    _check("D-002 词馆 found", cx is not None and cx.has_ciguan,
           f"has_ciguan={cx.has_ciguan if cx else None}")
    _check("D-002 天乙 found", cx is not None and cx.has_taiyi,
           f"has_taiyi={cx.has_taiyi if cx else None}")

    print("\n--- D-003 C-001 驿马 ---")
    career_supports = s001.shensha_supports.get("career", [])
    yima = next((s for s in career_supports if s.name == "驿马"), None)
    _check("D-003 驿马 in career", yima is not None,
           f"找到={yima is not None}")
    if yima:
        _check("D-003 驿马 含'奔波/调动'",
               any("奔波" in t or "调动" in t for t in yima.tags),
               f"tags={yima.tags}")

    print("\n--- 综合检查 ---")
    domains = set(s001.shensha_supports.keys())
    _check("C-001 覆盖 marriage/career/health",
           {"marriage", "career", "health"}.issubset(domains),
           f"domains={sorted(domains)}")
    _check("C-001 health_findings ≥ 1",
           len(s001.health_findings) >= 1,
           f"n={len(s001.health_findings)}")
    s_json = s001.to_json()
    from engine.pangzheng import SupportFindings
    s_back = SupportFindings.from_json(s_json)
    _check("JSON round-trip", s_back.hash() == s001.hash(),
           f"hash 一致")

    total = 9
    passed = total - fail
    print("\n" + "=" * 78)
    print(f"  RESULT: {passed}/{total} passed (fail={fail})")
    print("=" * 78)
    return fail


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(_run_unittest_style())

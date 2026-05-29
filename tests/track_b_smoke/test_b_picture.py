"""tests/track_b_smoke/test_b_picture.py · Track-B 验收测试

08-agent-handoff § 二 Agent B + § 六 列出的 4 项验收：

| 测试 | 输入                  | 期望 |
|------|-----------------------|------|
| B-001 | C-2026-001 energy+bazi | 职业=公门/国企; caifu.rank ≤ 4 |
| B-002 | C-2026-001 energy+bazi | marriage_picture.初婚最佳窗口 含 [22, 28]（修复 G2 圣杯）|
| B-003 | C-2026-002 energy+bazi | 职业=服务/公共; energy_consistent=True |
| B-004 | C-2026-014 energy+bazi | 学业=一本+; energy_consistent=True; 不应给 985 画面（修复 G4）|

支持两种运行方式：
1. ``pytest tests/track_b_smoke/test_b_picture.py``
2. ``python tests/track_b_smoke/test_b_picture.py``（自跑模式，输出详细诊断）

作者：Track-B
"""
from __future__ import annotations

import sys
from pathlib import Path

# 自跑模式：注入 sys.path
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest

from engine import FINDINGS_SCHEMA_VERSION
from engine.energy.evaluator import evaluate_energy
from engine.picture.matcher import match_picture
from tests.fixtures.cases import load_case


pytestmark = pytest.mark.smoke


# ============================================================
# 共用：跑 D1 + D2
# ============================================================

def _run_pipeline(case_id: str):
    parsed = load_case(case_id)
    energy = evaluate_energy(parsed)
    picture = match_picture(energy, parsed)
    return parsed, energy, picture


# ============================================================
# B-001 · C-2026-001：职业=公门/国企 + caifu.rank ≤ 4
# ============================================================

def test_B001_C2026_001_career_gongmen_caifu_le_4() -> None:
    parsed, energy, picture = _run_pipeline("C-2026-001-庚申戊寅壬子辛丑")

    # 1) caifu.rank ≤ 4
    assert picture.caifu is not None, "caifu 不应为 None"
    assert picture.caifu.rank <= 4, (
        f"B-001: caifu.rank 应 ≤ 4, 实为 {picture.caifu.rank} "
        f"({picture.caifu.type}). rationale={picture.caifu.rationale}"
    )

    # 2) 职业 = 公门/国企（在 industry_pointers 中能找到此关键词）
    pointers = picture.industry_pointers
    has_gongmen = any(
        any(kw in p for kw in ("公门", "国企", "皇粮", "体制"))
        for p in pointers
    )
    assert has_gongmen, (
        f"B-001: industry_pointers 应含'公门/国企'类，"
        f"实为 {pointers}"
    )

    # 3) energy_consistent
    assert picture.energy_consistent, (
        f"B-001: energy_consistent 应为 True, "
        f"violations={picture.energy_violations}"
    )

    # 4) upstream_hash 一致
    assert picture.upstream_hash == energy.hash(), (
        f"B-001: upstream_hash 不一致"
    )


# ============================================================
# B-002 · 关键测试：C-2026-001 marriage_picture.初婚最佳窗口 含 [22, 28]
#         （修复 G2 婚期 8 年误差的圣杯证据）
# ============================================================

def test_B002_C2026_001_marriage_window_contains_22_28() -> None:
    """修复 G2：C-2026-001 实际 25 岁（2005 年）结婚，
    v1.0 错判为 33 岁（2013 年），误差 8 年。
    
    v1.2 D2 必须给出 [22, 28] 窗口包含 25 岁，
    让 D3 在该窗口内搜索应期。
    """
    parsed, energy, picture = _run_pipeline("C-2026-001-庚申戊寅壬子辛丑")

    assert picture.marriage_picture is not None, (
        "B-002: marriage_picture 不应为 None"
    )
    mp = picture.marriage_picture

    # 必含字段
    assert "初婚最佳窗口" in mp, (
        f"B-002: marriage_picture 缺少'初婚最佳窗口'字段。keys={list(mp.keys())}"
    )

    window = mp["初婚最佳窗口"]
    assert isinstance(window, tuple) and len(window) == 2, (
        f"B-002: 初婚最佳窗口 应为 (lo, hi) tuple, 实为 {window!r}"
    )

    lo, hi = window
    assert isinstance(lo, int) and isinstance(hi, int), (
        f"B-002: 窗口边界应为 int, 实为 ({type(lo).__name__}, {type(hi).__name__})"
    )

    # 关键：[22, 28] ⊆ [lo, hi]
    assert lo <= 22 and hi >= 28, (
        f"B-002 G2 修复关键：marriage_picture.初婚最佳窗口 ({lo}, {hi}) "
        f"必须含 [22, 28]（即覆盖 25 岁=2005 年的真实婚期）"
    )

    # 实际婚龄 25 岁必须在窗口内
    actual_marriage_age = 25  # 2005 - 1980
    assert lo <= actual_marriage_age <= hi, (
        f"B-002: 窗口 ({lo}, {hi}) 必须含真实婚龄 {actual_marriage_age}"
    )

    # 早婚信号必须 ≥ 中（强或中）
    early_signal = mp.get("早婚信号", "弱")
    assert early_signal in ("强", "中"), (
        f"B-002: 早婚信号应为 '强' 或 '中'，实为 {early_signal!r}"
    )

    # 配偶画像非空
    assert mp.get("配偶画像"), "B-002: 配偶画像 不应为空"


# ============================================================
# B-003 · C-2026-002：职业=服务/公共 + energy_consistent=True
# ============================================================

def test_B003_C2026_002_career_service_consistent() -> None:
    parsed, energy, picture = _run_pipeline("C-2026-002-壬戌庚戌戊辰丙辰")

    # 1) energy_consistent
    assert picture.energy_consistent, (
        f"B-003: energy_consistent 应为 True, "
        f"violations={picture.energy_violations}"
    )

    # 2) 职业 = 服务/公共（C-2026-002 实际职业 = 县级卫健局事业单位）
    pointers = picture.industry_pointers
    # 预期关键词："服务"、"公共"、"公门"、"国企"、"体制"、"医"、"教育"
    # 都属于公共服务领域
    has_service_or_public = any(
        any(kw in p for kw in (
            "服务", "公共", "公门", "国企",
            "体制", "医", "教育", "文教",
        ))
        for p in pointers
    )
    assert has_service_or_public, (
        f"B-003: industry_pointers 应含服务/公共类关键词，"
        f"实为 {pointers}"
    )

    # 3) marriage_picture 非空（女命婚姻必判）
    assert picture.marriage_picture is not None
    assert "初婚最佳窗口" in picture.marriage_picture


# ============================================================
# B-004 · C-2026-014：学业=一本+ + 不应给 985 画面（修复 G4）
# ============================================================

def test_B004_C2026_014_education_yiben_no_985() -> None:
    """修复 G4：C-2026-014 学历应判为"一本+"水平，
    不应过判到 985/211 顶配（v1.0 失误）。
    """
    parsed, energy, picture = _run_pipeline("C-2026-014-丙戌庚子乙亥辛巳")

    # 1) energy_consistent
    assert picture.energy_consistent, (
        f"B-004: energy_consistent 应为 True, "
        f"violations={picture.energy_violations}"
    )

    # 2) 不应给 985 / 211 / 顶级 / 北清复交 / 巨富 等过判画面
    blacklist_kws = ("985", "211", "北清复交", "藤校", "Ivy", "海外名校")
    
    # 扫描全部文本字段
    all_texts: list[str] = []
    all_texts.extend(picture.industry_pointers)
    for s in picture.wubu_steps:
        all_texts.append(s.finding)
    for a in picture.anyin_results:
        all_texts.append(a.real_meaning)
    if picture.caifu:
        all_texts.append(picture.caifu.rationale)
    if picture.guanming:
        all_texts.append(picture.guanming.rationale)
    if picture.marriage_picture:
        all_texts.append(picture.marriage_picture.get("配偶画像", ""))

    for txt in all_texts:
        for kw in blacklist_kws:
            assert kw not in txt, (
                f"B-004 G4 修复：picture 不应含'{kw}'画面，"
                f"但在文本中发现：{txt!r}"
            )

    # 3) 学业相关：印生比劫 / 印护身 / 印星相关结构应被识别
    # 支持"一本+"的结构：印星出现 + 比劫暗引（M2-Y-030）
    has_yin_signal = (
        any("印" in a.real_meaning or "印" in a.triggered_shishen
            for a in picture.anyin_results)
        or any("印" in s.finding for s in picture.wubu_steps)
    )
    assert has_yin_signal, (
        "B-004: 应有'印星/印生比劫'等学历相关 anyin 触发"
    )

    # 4) marriage_picture 非空（即使是 19 岁未婚命主也应给画像）
    assert picture.marriage_picture is not None
    assert "初婚最佳窗口" in picture.marriage_picture


# ============================================================
# 通用契约测试
# ============================================================

@pytest.mark.parametrize("case_id", [
    "C-2026-001-庚申戊寅壬子辛丑",
    "C-2026-002-壬戌庚戌戊辰丙辰",
    "C-2026-014-丙戌庚子乙亥辛巳",
])
def test_picture_findings_required_fields(case_id: str) -> None:
    """每个 PictureFindings 必含全部必填字段。"""
    parsed, energy, picture = _run_pipeline(case_id)

    # 五步法必跑 5 步
    assert len(picture.wubu_steps) == 5, (
        f"{case_id}: wubu_steps 应有 5 步，实有 {len(picture.wubu_steps)}"
    )
    for i, s in enumerate(picture.wubu_steps, start=1):
        assert s.step == i
        assert s.finding, f"step {i} finding 不应为空"

    # 财富 / 官命 至少财富一定有
    assert picture.caifu is not None
    assert 1 <= picture.caifu.rank <= 7

    # 婚姻画像
    assert picture.marriage_picture is not None
    assert "初婚最佳窗口" in picture.marriage_picture
    win = picture.marriage_picture["初婚最佳窗口"]
    assert isinstance(win, tuple) and len(win) == 2
    assert win[0] >= 16 and win[1] <= 50, (
        f"窗口范围异常: {win}"
    )

    # 调候建议
    assert picture.tiaohou_advice is not None
    assert "免责" in picture.tiaohou_advice

    # 上游一致性
    assert isinstance(picture.energy_consistent, bool)
    assert isinstance(picture.energy_violations, list)

    # 元信息
    assert picture.school == "杨"
    assert picture.schema_version == FINDINGS_SCHEMA_VERSION
    assert picture.upstream_hash == energy.hash()
    assert picture.confidence is not None
    assert 1 <= picture.confidence.star <= 5
    assert 0.0 <= picture.confidence.percent <= 1.0
    assert len(picture.evidence) >= 1

    for e in picture.evidence:
        assert e.school in ("段", "杨", "高", "任")
        assert e.rule_id


def test_picture_findings_round_trip_json() -> None:
    """to_json → from_json 一致 + hash 稳定。"""
    parsed, energy, picture = _run_pipeline(
        "C-2026-001-庚申戊寅壬子辛丑"
    )
    s = picture.to_json()

    from engine.picture.types import PictureFindings
    pf2 = PictureFindings.from_json(s)
    assert picture.to_dict() == pf2.to_dict()
    assert picture.hash() == pf2.hash()
    assert len(picture.hash()) == 16

    # 重要字段保持
    assert pf2.marriage_picture is not None
    win = pf2.marriage_picture["初婚最佳窗口"]
    assert isinstance(win, tuple) and win == (22, 28)


# ============================================================
# 自跑模式（python tests/track_b_smoke/test_b_picture.py）
# ============================================================

def _main() -> int:
    """自跑 4 项验收 + 通用契约。"""
    print("=" * 70)
    print("Track-B 验收测试 4 项")
    print("=" * 70)

    tests = [
        ("B-001", test_B001_C2026_001_career_gongmen_caifu_le_4),
        ("B-002", test_B002_C2026_001_marriage_window_contains_22_28),
        ("B-003", test_B003_C2026_002_career_service_consistent),
        ("B-004", test_B004_C2026_014_education_yiben_no_985),
    ]
    passed = 0
    for name, fn in tests:
        print(f"\n--- {name} ---")
        try:
            fn()
            print(f"  [PASS] {name}")
            passed += 1
        except AssertionError as e:
            print(f"  [FAIL] {name}: {e}")

    print("\n--- 通用契约测试 ---")
    for cid in [
        "C-2026-001-庚申戊寅壬子辛丑",
        "C-2026-002-壬戌庚戌戊辰丙辰",
        "C-2026-014-丙戌庚子乙亥辛巳",
    ]:
        try:
            test_picture_findings_required_fields(cid)
            print(f"  [PASS] required_fields {cid}")
        except AssertionError as e:
            print(f"  [FAIL] required_fields {cid}: {e}")

    try:
        test_picture_findings_round_trip_json()
        print("  [PASS] round_trip_json")
    except AssertionError as e:
        print(f"  [FAIL] round_trip_json: {e}")

    print(f"\n=== Track-B 4 项验收：{passed}/4 通过 ===")
    return 0 if passed == 4 else 1


if __name__ == "__main__":
    sys.exit(_main())

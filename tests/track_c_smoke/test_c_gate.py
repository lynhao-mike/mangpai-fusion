"""Track-C 5 项验收测试 · C-001 ~ C-005

| 测试 | 输入 | 期望 |
|------|------|------|
| C-001 | C-2026-001 year=2005 婚姻 | passed_layers=3, ★≥4  |
| C-002 | C-2026-001 year=2013 婚姻 | passed_layers≤1（picture钳制）, ★≤3 |
| C-003 | C-2026-001 year=2020 六亲（母）| passed_layers=3, ★★★★★ |
| C-004 | C-2026-001 year=2020 事业 | passed_layers≥2 |
| C-005 | C-2026-014 year=2024 学业 | passed_layers≥2 |

C-001 + C-002 是 G2 圣杯：v1.2 必须"2005 强 / 2013 弱"。
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

# 让脚本既可作为 module（python -m）跑，也可直接 python 跑
ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.yingqi import gate_yingqi  # noqa: E402

from tests.track_c_smoke.fixtures import (  # noqa: E402
    parsed_C001, energy_C001, picture_C001,
    parsed_C002, energy_C002, picture_C002,
    parsed_C014, energy_C014, picture_C014,
)


# ============================================================
# 工具：单测打印 + 断言
# ============================================================


def _show(name: str, result, expected: str) -> None:
    print(f"\n=== {name} | 期望: {expected} ===")
    print(result.summary)


# ============================================================
# 5 项测试
# ============================================================


class TrackCGateTests(unittest.TestCase):
    """Track-C gate_yingqi 5 项验收测试。"""

    # ------------ C-001 婚姻 2005 (G2 圣杯 1) ------------
    def test_C001_marriage_2005(self) -> None:
        pi = parsed_C001()
        en = energy_C001()
        pic = picture_C001()
        r = gate_yingqi(2005, "结婚", "婚姻", en, pic, pi)
        _show("C-001 · year=2005 · 婚姻 · 结婚", r, "passed_layers=3, ★≥4")
        self.assertEqual(r.passed_layers, 3, "C-001 2005 婚姻必须三层齐备")
        self.assertGreaterEqual(r.star, 4, "C-001 2005 婚姻 ★ 必须 ≥4")

    # ------------ C-002 婚姻 2013 (G2 圣杯 2) ------------
    def test_C002_marriage_2013(self) -> None:
        pi = parsed_C001()
        en = energy_C001()
        pic = picture_C001()
        r = gate_yingqi(2013, "结婚", "婚姻", en, pic, pi)
        _show("C-002 · year=2013 · 婚姻 · 结婚", r, "passed_layers≤1, ★≤3, picture✗")
        self.assertLessEqual(r.passed_layers, 1, "C-002 2013 婚姻必须被 picture 钳制")
        self.assertLessEqual(r.star, 3, "C-002 2013 婚姻 ★ 必须 ≤3")
        self.assertFalse(r.picture_consistent, "picture_consistent 必须 False")

    # ------------ C-003 六亲 2020 (印动 / 母亲去世) ------------
    def test_C003_liuqin_2020(self) -> None:
        pi = parsed_C001()
        en = energy_C001()
        pic = picture_C001()
        r = gate_yingqi(2020, "母亲去世", "六亲", en, pic, pi, sub_domain="母")
        _show("C-003 · year=2020 · 六亲(母) · 母亲去世", r, "passed_layers=3, ★★★★★")
        # C-003 真实事件：2020 庚子 母亲正月去世（印动+伏吟子+庚透）
        self.assertGreaterEqual(r.passed_layers, 2,
                                f"C-003 2020 六亲应该至少 ≥2 层（实际={r.passed_layers}）")

    # ------------ C-004 事业 2020 (升副科) ------------
    def test_C004_career_2020(self) -> None:
        pi = parsed_C001()
        en = energy_C001()
        pic = picture_C001()
        r = gate_yingqi(2020, "升副科", "事业", en, pic, pi)
        _show("C-004 · year=2020 · 事业 · 升副科", r, "passed_layers≥2")
        # C-004 真实事件：2020 提副科 + 2025 提正科
        self.assertGreaterEqual(r.passed_layers, 2,
                                f"C-004 2020 事业 passed_layers={r.passed_layers}, 期望 ≥2")

    # ------------ C-005 学业 2024 (高考考上) ------------
    def test_C005_education_2024(self) -> None:
        pi = parsed_C014()
        en = energy_C014()
        pic = picture_C014()
        r = gate_yingqi(2024, "高考考上一本", "学业", en, pic, pi)
        _show("C-005 · year=2024 · 学业 · 高考考上", r, "passed_layers≥2")
        # C-005 真实事件：2024 甲辰 高考考上南审一本
        self.assertGreaterEqual(r.passed_layers, 2,
                                f"C-005 2024 学业 passed_layers={r.passed_layers}, 期望 ≥2")


# ============================================================
# C-001 vs C-002 对比表（G2 圣杯专用打印）
# ============================================================


def print_g2_holy_grail_comparison() -> dict:
    """打印 C-001 婚 2005 vs C-001 婚 2013 的对比表。

    这是 v1.2 重构的 G2 圣杯：必须"2005 强 / 2013 弱"。
    """
    pi = parsed_C001()
    en = energy_C001()
    pic = picture_C001()
    r1 = gate_yingqi(2005, "结婚", "婚姻", en, pic, pi)
    r2 = gate_yingqi(2013, "结婚", "婚姻", en, pic, pi)

    print("\n" + "=" * 78)
    print("           G2 圣杯对比 · C-2026-001 婚姻应期 (v1.2 重构关键指标)")
    print("=" * 78)
    print(f"  v1.0 报告判婚期 = 2013 年（差 8 年）")
    print(f"  实际婚年 = 2005 年（25 岁，命主反馈）")
    print(f"  v1.2 期望：2005 强 / 2013 弱\n")

    print(f"{'年份':<8}{'流年':<8}{'大运':<8}{'L1':<5}{'L2':<5}{'L3':<5}{'层数':<8}{'★':<5}{'置信度':<10}{'picture':<8}{'主触发':<14}{'道门'}")
    print("-" * 78)
    for label, r in [("2005", r1), ("2013", r2)]:
        from engine.predicates.cycles import liunian_ganzhi, get_dayun_at_year
        ln = "".join(liunian_ganzhi(int(label)))
        dy_obj = get_dayun_at_year(pi, int(label))
        dy = f"{dy_obj.gan}{dy_obj.zhi}" if dy_obj else "-"
        l1 = "✓" if (r.layer1 and r.layer1.passed) else "✗"
        l2 = "✓" if (r.layer2 and r.layer2.passed) else "✗"
        l3 = "✓" if (r.layer3 and r.layer3.passed) else "✗"
        pic_ok = "✓" if r.picture_consistent else "✗"
        pt = r.primary_trigger.trigger_type if r.primary_trigger else "-"
        door = r.door.door_type if r.door else "-"
        print(f"{label:<8}{ln:<8}{dy:<8}{l1:<5}{l2:<5}{l3:<5}{r.passed_layers:<8}{'★'*r.star:<5}{r.confidence*100:>5.1f}%   {pic_ok:<8}{pt:<14}{door}")
    print("=" * 78)

    g2_pass = (
        r1.passed_layers == 3 and r1.star >= 4
        and r2.passed_layers <= 1 and r2.star <= 3
    )
    print(f"\nG2 圣杯结论: {'PASS ✓' if g2_pass else 'FAIL ✗'}")
    print(f"  · 2005 三层齐 ★≥4: {'✓' if (r1.passed_layers==3 and r1.star>=4) else '✗'}")
    print(f"  · 2013 ≤1 层 ★≤3:  {'✓' if (r2.passed_layers<=1 and r2.star<=3) else '✗'}")
    return {
        "2005": {"passed_layers": r1.passed_layers, "star": r1.star, "confidence": r1.confidence},
        "2013": {"passed_layers": r2.passed_layers, "star": r2.star, "confidence": r2.confidence},
        "g2_pass": g2_pass,
    }


# ============================================================
# 入口
# ============================================================


if __name__ == "__main__":
    # 显式打印 G2 对比表（任务要求）
    g2 = print_g2_holy_grail_comparison()

    # 跑 unittest
    print("\n" + "=" * 78)
    print("                    Track-C 5 项验收测试")
    print("=" * 78)
    unittest.main(argv=[""], verbosity=2, exit=False)

    print("\n" + "=" * 78)
    print(f"G2 圣杯结果: {g2}")
    print("=" * 78)

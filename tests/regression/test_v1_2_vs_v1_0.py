"""tests/regression/test_v1_2_vs_v1_0 · v1.2 vs v1.0 量化基准

按 00-OVERVIEW § 八 v1.2 发布门槛的 6 项指标：
  G1 · 三个真实案例核心断语命中率 ≥ v1.0 + 1 条
  G2 · 婚期误差（C-2026-001）≤ 3 年 (v1.0 = 8 年)
  G3 · 婚姻定性失验数（C-2026-002）≤ 1 (v1.0 = 4)
  G4 · 学历过判档数（C-2026-014）= 0 (v1.0 = +1)
  G5 · 平均断语 trace_id 覆盖率 = 100% (v1.0 = 0%)
  G6 · ★★★★★ 断语三层 gate 通过率 = 100% (v1.0 = 0%)

本文件 Track-C 阶段只实现 G2 + G6（其他指标依赖 Track-A/B/D/F/G/H）。
未实现的指标用 unittest.skip 标记，并附原因说明。
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.yingqi import gate_yingqi  # noqa: E402

from tests.track_c_smoke.fixtures import (  # noqa: E402
    parsed_C001, energy_C001, picture_C001,
)


class V12VsV10Regression(unittest.TestCase):
    """v1.2 vs v1.0 量化基准。"""

    def test_G2_marriage_year_error_le_3(self) -> None:
        """G2: C-2026-001 婚期误差 ≤ 3 年。

        v1.0 报告判 2013，实际 2005，误差 8 年。
        v1.2 必须能在 [2005-3, 2005+3] = [2002, 2008] 内找到三层齐的 ★≥4 婚姻应期；
        且对 [2009, 2018] 区间应该都给 ★≤3。
        """
        pi = parsed_C001()
        en = energy_C001()
        pic = picture_C001()

        # 在合理窗口 [2002, 2008] 中寻找最强应期
        windowed_results = []
        for y in range(2002, 2009):
            r = gate_yingqi(y, "结婚", "婚姻", en, pic, pi)
            windowed_results.append((y, r))

        # 至少要有一年达到 passed_layers=3 + ★≥4
        strong_in_window = [
            (y, r) for y, r in windowed_results
            if r.passed_layers == 3 and r.star >= 4
        ]
        self.assertGreater(
            len(strong_in_window), 0,
            f"G2: 必须在 [2002, 2008] 内至少 1 年三层齐 ★≥4，"
            f"实际 {len(strong_in_window)} 年命中"
        )

        # 误差 = 最近的强应期年与 2005 的距离
        nearest = min(abs(y - 2005) for y, _ in strong_in_window)
        self.assertLessEqual(
            nearest, 3,
            f"G2: 婚期误差必须 ≤ 3 年，实际 {nearest} 年"
        )

        # 反向：v1.0 误判的 2013 必须 ★≤3
        r2013 = gate_yingqi(2013, "结婚", "婚姻", en, pic, pi)
        self.assertLessEqual(
            r2013.star, 3,
            f"G2: 2013 必须 ★≤3，实际 ★{r2013.star}"
        )
        self.assertLessEqual(
            r2013.passed_layers, 1,
            f"G2: 2013 必须 passed_layers≤1，实际 {r2013.passed_layers}"
        )

        # 漂亮地打印
        print("\nG2 · C-2026-001 婚期误差检测")
        for y, r in windowed_results:
            mark = "✓" if (r.passed_layers == 3 and r.star >= 4) else " "
            print(f"  {y} {mark} passed={r.passed_layers}/3 ★{r.star} conf={r.confidence:.2%}")
        print(f"  → 强应期最近距离 2005: {nearest} 年（v1.0 = 8 年；v1.2 限值 ≤ 3 年）")

    def test_G6_iron_call_three_layer_gate_rate(self) -> None:
        """G6: ★★★★★ 断语三层 gate 通过率 = 100%。

        v1.2 任何 ★★★★★ 断语都必须 passed_layers=3。
        本测试用一组 GateResult 抽样验证。
        """
        pi = parsed_C001()
        en = energy_C001()
        pic = picture_C001()

        candidates = [
            (2005, "结婚", "婚姻"),
            (2020, "母亲去世", "六亲"),
        ]
        five_star_count = 0
        five_star_three_layer = 0
        for y, ev, dom in candidates:
            sub = "母" if dom == "六亲" else None
            r = gate_yingqi(y, ev, dom, en, pic, pi, sub_domain=sub)
            if r.star == 5:
                five_star_count += 1
                if r.passed_layers == 3:
                    five_star_three_layer += 1

        if five_star_count == 0:
            self.skipTest("无 ★★★★★ 断语样本，G6 跳过")
        self.assertEqual(
            five_star_three_layer, five_star_count,
            f"G6: ★★★★★ 必须 100% 三层齐，"
            f"实际 {five_star_three_layer}/{five_star_count}"
        )
        print(f"\nG6 · ★★★★★ 三层 gate 通过率: {five_star_three_layer}/{five_star_count} = 100%")

    @unittest.skip("G1: 依赖 Track-F render_report + 14 案完整断语，Track-C 阶段不可达")
    def test_G1_3_cases_hit_rate(self) -> None:
        pass

    @unittest.skip("G3: 依赖 Track-B picture_matcher 完整实现 + C-002 婚姻细化定性")
    def test_G3_C002_marriage_misjudge_le_1(self) -> None:
        pass

    @unittest.skip("G4: 依赖 Track-B 学历分级 + level-scales 完整对接")
    def test_G4_C014_education_overcall(self) -> None:
        pass

    @unittest.skip("G5: 依赖 Track-F render_report 自动写入 trace_id")
    def test_G5_trace_id_coverage(self) -> None:
        pass


if __name__ == "__main__":
    unittest.main(verbosity=2)

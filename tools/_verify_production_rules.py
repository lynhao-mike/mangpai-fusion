"""临时核验脚本：核验子平/滴天髓生产规则能否真正用于八字分析。

核验链路：加载 → 触发评估 → 证据产出
- 统计每个案例实际触发的规则数（按派别）
- 定位永远无法触发的 trigger（_rule_triggered 未实现 → 静默 False）
- 验证触发规则能否转为 Evidence
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

from engine.application.production_rule_loader import (
    _rule_triggered,
    load_default_production_library,
)

# _rule_triggered 中已实现（会返回非 False）的 trigger 白名单
IMPLEMENTED_TRIGGERS = {
    "always",
    "has_wealth_picture",
    "has_official_picture",
    "has_marriage_picture",
    "has_tiaohou_advice",
    "wuxing_imbalanced",
    "has_zhi_chong",
    "has_energy_structure",
    # B: 大运/流年
    "has_dayun",
    "has_xiaoyun",
    "has_liunian",
    "has_suiyun_interaction",
    # A: 神煞
    "has_sanhe_partial",
    "has_sanxing",
    "has_kongwang",
    "has_zaisha",
    "has_goujiao",
    "has_guchen_guasu",
    "has_tianluodiwang",
    "has_shie_dabai",
    "has_qisha_with_control",
    "has_hour_qisha",
    "has_guansha_mixed",
    # C: 日时组合
    "has_yi_day_bingzi_hour",
    "has_xin_day_wuzi_hour",
    # D: 六亲评估
    "child_chart_health_assessment",
    "child_chart_guansha",
    "liuqin_star_location_assessment",
    "spouse_star_location_assessment",
    "children_star_location_assessment",
    "female_chart_spouse_children_assessment",
}


def _load_case(case_id: str):
    """尝试用 fixtures.load_case 加载真实案例的 ParsedInput。"""
    from tests.fixtures.cases import load_case  # type: ignore

    return load_case(case_id)


def main() -> None:
    lib = load_default_production_library()
    all_rules = lib.rules

    print("=" * 70)
    print("一、规则库加载核验")
    print("=" * 70)
    by_school = Counter(r.expert_system for r in all_rules)
    print(f"总规则数: {len(all_rules)}")
    for school, n in by_school.items():
        print(f"  {school}: {n}")

    # 二、静态分析：哪些 trigger 永远无法触发
    print()
    print("=" * 70)
    print("二、Trigger 实现覆盖分析（静默失效检测）")
    print("=" * 70)
    trigger_counter = Counter(r.conditions.trigger for r in all_rules)
    dead_rules = []
    for trig, cnt in sorted(trigger_counter.items(), key=lambda x: -x[1]):
        implemented = trig in IMPLEMENTED_TRIGGERS
        flag = "OK " if implemented else "DEAD"
        print(f"  [{flag}] {trig}: {cnt} 条")
        if not implemented:
            dead_rules.extend(
                r.id for r in all_rules if r.conditions.trigger == trig
            )
    print()
    print(f"永远无法触发的规则数（静默失效）: {len(dead_rules)} / {len(all_rules)}")
    if dead_rules:
        print("失效规则 ID（前 20）:")
        for rid in dead_rules[:20]:
            print(f"    - {rid}")

    # 三、端到端：用真实案例跑触发
    print()
    print("=" * 70)
    print("三、端到端触发核验（真实案例）")
    print("=" * 70)

    case_ids = [
        "C-2026-001-乾-庚申戊寅壬子辛丑",
        "C-2026-002-坤-壬戌庚戌戊辰丙辰",
        "C-2026-007-乾-乙丑庚辰己丑庚午",
    ]

    from engine.energy.types import EnergyFindings
    from engine.picture.types import PictureFindings

    for case_id in case_ids:
        try:
            parsed = _load_case(case_id)
        except Exception as exc:  # noqa: BLE001
            print(f"  [{case_id}] 案例加载失败: {exc}")
            continue

        # 用最小 findings：仅靠 parsed 可触发的规则（always/wuxing_imbalanced/has_zhi_chong）
        empty_energy = EnergyFindings(
            energy_level=None,  # type: ignore
            layer_count=0,
            zuogong_paths=[],
            tiyong=None,  # type: ignore
            shidang=None,  # type: ignore
            zeishen=None,  # type: ignore
            wealth_ceiling=None,  # type: ignore
            has_guoheqiaoqiao=False,
            muxing_qufa=None,  # type: ignore
            confidence=None,  # type: ignore
            evidence=[],
        )
        try:
            empty_picture = PictureFindings()  # type: ignore
        except Exception:
            empty_picture = object()  # type: ignore

        triggered = [
            r
            for r in all_rules
            if _rule_triggered(
                r, parsed=parsed, energy=empty_energy, picture=empty_picture
            )
        ]
        tri_by_school = Counter(r.expert_system for r in triggered)
        print(f"  [{case_id}] 触发 {len(triggered)} 条: {dict(tri_by_school)}")

        # 证据链转换验证
        if triggered:
            ev = triggered[0].to_evidence()
            print(
                f"      样例 Evidence: rule_id={ev.rule_id} school={ev.school} weight={ev.weight}"
            )


if __name__ == "__main__":
    sys.exit(main())

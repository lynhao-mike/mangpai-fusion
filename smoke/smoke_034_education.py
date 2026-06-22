"""034 案例学业分析——用新模块跑一遍。

ponytail: 读已有 findings，不重新调 pipeline，不写文件，只打印。
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from engine.education import EducationSignal, analyze_education


_signals = [
    # ── 子平 · 学习能力 ──
    EducationSignal("ziping", "ability", "印星辛金藏月时戌库，可用但不透出，学习需要外部环境或后天培养激活", 0.40),
    EducationSignal("ziping", "ability", "伤官甲木双透于年月，日坐卯木食神，理解转化与表达能力突出", 0.75),
    EducationSignal("ziping", "ability", "戌中戊生辛为官印相生，原局有读书结构因果但不显于天干", 0.50),
    EducationSignal("ziping", "ability", "癸水得子禄壬劫帮身，日主不弱，有能量支撑学习投入", 0.55),
    EducationSignal("ziping", "exam_pressure", "官杀戊土藏双戌库不透，考试制度压力隐性，大运戊寅官星透出时压力会增强", 0.50),
    EducationSignal("ziping", "interference", "丁火偏财藏戌库，早运丙子、丁丑运财星透干，易因消费、兴趣或人际圈分心", 0.55),
    EducationSignal("ziping", "interference", "伤官见官结构潜在（甲木伤官→戌中戊官），学业路径可能倾向应用型或非传统方向", 0.40),

    # ── 滴天髓 · 学习环境 ──
    EducationSignal("tiaohou_ditiansui", "environment", "水木双党占77%——木得水生，有灵秀之气，理解悟性不弱", 0.65),
    EducationSignal("tiaohou_ditiansui", "environment", "戌月燥土占19%，火仅1%，调候偏寒——学习持续性与冲刺力受环境制约", 0.45),
    EducationSignal("tiaohou_ditiansui", "environment", "水木主力、金火土均弱：气偏清不浊，但格局层次受限，不宜判定高级学历", 0.40),

    # ── 盲派 · 象法直断候选 ──
    EducationSignal("blind", "degree_direct", "文昌贵人+天乙贵人同在日柱，福星+德秀辅佐，学历候选明显", 0.70),
    EducationSignal("blind", "degree_direct", "日柱文昌坐食神卯，聪明好学之象，但需锚点验证是发挥还是浪费", 0.60),
    EducationSignal("blind", "ability", "天乙贵人×4柱皆见 + 太极贵人年柱 + 国印贵人月时，贵人文化象重", 0.55),
    EducationSignal("blind", "interference", "月时两柱空亡各叠寡宿吊客——某些学业阶段可能出现信息断层或社交边缘化", 0.30),
]


def main() -> None:
    profile = analyze_education(
        birth_year=1984,
        signals=_signals,
        anchors={},
    )

    print("=" * 68)
    print("  C-2026-034-乾-甲子甲戌癸卯壬戌  学业分析（新模块）")
    print("=" * 68)

    print("\n📅 教育阶段时间轴")
    print("-" * 40)
    for item in profile.timeline:
        yr = item["year_range"]
        age = item["age_range"]
        print(f"  {item['stage']:　<10s}  {yr[0]}–{yr[1]}年   {age[0]}–{age[1]}岁   {item['required_checks']}")

    print("\n📊 学业分数")
    print("-" * 40)
    print(f"  学习能力分：     {profile.ability_score:.3f}")
    print(f"  学习环境分：     {profile.environment_score:.3f}")
    print(f"  考试压力分：     {profile.exam_pressure_score:.3f}")
    print(f"  干扰/分心分：    {profile.interference_score:.3f}")

    print("\n🎓 学历结论")
    print("-" * 40)
    print(f"  可输出确定学历：  {'是' if profile.usable_for_final_degree else '否——现实锚点不足'}")
    print(f"  学历层级：        {profile.degree_verdict}")
    print(f"  学校层级：        {profile.institution_verdict}")

    if profile.risks:
        print("\n⚠️  风险提示")
        print("-" * 40)
        for r in profile.risks:
            print(f"  • {r}")

    ability_signals = [s for s in _signals if s.kind == "ability"]
    direct_signals = [s for s in _signals if s.kind == "degree_direct"]
    print(f"\n📋 信号统计: 能力信号 {len(ability_signals)} 条, 直断信号 {len(direct_signals)} 条, 环境信号 {len([s for s in _signals if s.kind == 'environment'])} 条")
    print(f"   能力最高: {max(s.strength for s in ability_signals):.2f} (子平·伤官双透)")
    print(f"   直断最高: {max(s.strength for s in direct_signals):.2f} (盲派·文昌+天乙在日柱)")
    print(f"   现实锚点: 0 条（known_facts=[]，gate_results=[]，feedback=待补）")

    print("\n📌 命理师行动建议")
    print("-" * 40)
    print("  1. 先用本报告学业结构回访命主，收集高考年份、录取批次、学校名称、专业、毕业年份、最高学历。")
    print("  2. 锚点到位后重新运行 analyze_education(anchors={...})，模块会自动放开学历结论。")
    print("  3. 当前不要给确定学历——元信息不足时给结论反而降低命理师可信度。")


if __name__ == "__main__":
    main()

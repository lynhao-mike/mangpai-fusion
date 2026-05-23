"""engine/picture/tiaohou.py · v1.2 D2 杨派 · 调候改运 6 维

杨派调候改运（M2-Y-073, 074, §17.1-3）：

> 调候 = 调时候；提前引好驱走坏。
> 化敌为友（合制）+ 制伏（克制）。

6 维（颜色 / 方位 / 数字 / 文化 / 食物 / 贵人）：

| 命中喜 | 颜色 | 方位 | 数字 | 食物 |
|---|---|---|---|---|
| 木 | 绿 | 东 | 1, 2 | 酸味 |
| 火 | 红/紫 | 南 | 3, 4 | 苦味/辣 |
| 土 | 黄/咖啡 | 中 | 5, 6 | 甜/土豆 |
| 金 | 白 | 西 | 7, 8 | 辛辣/白色 |
| 水 | 黑/蓝 | 北 | 9, 0 | 咸/海鲜 |

输入：EnergyFindings + Bazi
输出：dict[str, str | list]

简化逻辑：
- 取 5 行最弱者作为"喜补五行"
- 给出该五行对应的颜色/方位/数字/食物
- 文化倾向：木火→文 / 金水→理
- 贵人：印 → 师长；财 → 朋友；官 → 上司
- 必带免责声明（M2-Y-010 / §18.1）

作者：Track-B
"""
from __future__ import annotations

from typing import Optional

from engine.energy.types import EnergyFindings
from engine.predicates.ganzhi import gan_to_wuxing
from engine.predicates.strength import calc_wuxing_strength
from engine.predicates.types import Bazi, Wuxing


_TIAOHOU_TABLE: dict[Wuxing, dict] = {
    "木": {
        "颜色": ["绿色", "深绿"],
        "方位": "东方",
        "数字": [1, 2],
        "食物": ["酸味", "豆类", "绿叶蔬菜"],
        "文化": "文化/教育/书籍/木工艺品",
        "贵人方向": "东",
    },
    "火": {
        "颜色": ["红色", "紫色"],
        "方位": "南方",
        "数字": [3, 4],
        "食物": ["苦味", "辣味", "咖啡", "红色食物"],
        "文化": "电子/影视/明星元素",
        "贵人方向": "南",
    },
    "土": {
        "颜色": ["黄色", "咖啡色", "土黄"],
        "方位": "中宫",
        "数字": [5, 6],
        "食物": ["甜味", "土豆", "南瓜"],
        "文化": "瓷器/玉器/讲台/书法",
        "贵人方向": "中",
    },
    "金": {
        "颜色": ["白色", "金色"],
        "方位": "西方",
        "数字": [7, 8],
        "食物": ["辛辣", "白色食物", "肉类"],
        "文化": "金属/珠宝/法律/金融",
        "贵人方向": "西",
    },
    "水": {
        "颜色": ["黑色", "蓝色"],
        "方位": "北方",
        "数字": [9, 0],
        "食物": ["咸味", "海鲜", "汤水"],
        "文化": "数字/化工/运输/玄学",
        "贵人方向": "北",
    },
}


def build_tiaohou_advice(
    energy: EnergyFindings,
    bazi: Bazi,
) -> dict:
    """构造调候改运建议（6 维 dict）。

    简化：取 5 行最弱者作为"喜补五行"。
    """
    # 优先级：从 EnergyFindings.shidang.shi 拿；fallback 重新算
    if energy.shidang and energy.shidang.shi:
        shi = dict(energy.shidang.shi)
    else:
        shi = calc_wuxing_strength(bazi)

    if not shi:
        return {"提示": "数据不足", "免责": _DISCLAIMER}

    # 找最弱（势力最低）的五行
    sorted_shi = sorted(shi.items(), key=lambda x: x[1])
    weak_wx = sorted_shi[0][0]
    # 兜底：若最弱是日干本五行（自伤无补）→ 取次弱
    day_wx = gan_to_wuxing(bazi.day_master)
    if weak_wx == day_wx and len(sorted_shi) > 1:
        weak_wx = sorted_shi[1][0]

    info = _TIAOHOU_TABLE.get(weak_wx, {})  # type: ignore[arg-type]
    return {
        "喜补五行": weak_wx,
        "颜色": info.get("颜色", []),
        "方位": info.get("方位", ""),
        "数字": info.get("数字", []),
        "文化": info.get("文化", ""),
        "食物": info.get("食物", []),
        "贵人方向": info.get("贵人方向", ""),
        "免责": _DISCLAIMER,
        "_debug_shi": {k: round(v, 3) for k, v in shi.items()},
    }


_DISCLAIMER = (
    "本调候建议为概率性指引，"
    "非医疗/非法律/非金融建议；"
    "不进行风水营销（M2-Y-010 / §18.1）"
)


# ============================================================
# smoke
# ============================================================

def _smoke() -> None:
    from tests.fixtures.cases import load_case
    from engine.energy.evaluator import evaluate_energy

    for cid in [
        "C-2026-001-庚申戊寅壬子辛丑",
        "C-2026-014-丙戌庚子乙亥辛巳",
    ]:
        parsed = load_case(cid)
        energy = evaluate_energy(parsed)
        adv = build_tiaohou_advice(energy, parsed.bazi)
        print(f"\n=== {cid} 调候 ===")
        for k, v in adv.items():
            print(f"  {k}: {v}")
    print("\n[OK] tiaohou smoke 通过")


if __name__ == "__main__":  # pragma: no cover
    _smoke()

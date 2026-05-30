"""engine/yingqi/retrospective.py · F6 · 流年回溯模块

按 portrait-v2 § 四的"力量场图谱"实现：
扫描 [起运年, 当前年] 的每个流年，输出与原局/大运的作用关系。

特点：
- **不下应期铁断**（D3 的职责，含 known_facts 校验）
- 仅展示**结构性力量场**：哪一年发生**什么类型**的能量碰撞
- 当 known_facts 不足以激活 D3 应期门时，本模块依然能展示画面

输出按大运分段，每段含若干流年。

作者：Kiro Agent · v1.3.1 (PR #33)
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Literal, Optional

from engine.predicates.cycles import get_dayun_at_year, liunian_ganzhi
from engine.predicates.relations import (
    gan_he,
    zhi_chong,
    zhi_chuan,
    zhi_liuhe,
    zhi_xing,
)
from engine.predicates.types import Bazi, Dayun, GanZhi, ParsedInput
from engine.predicates.palace import get_shishen


Strength = Literal["▲", "●", "▽"]
Domain = Literal["学业", "婚姻", "事业", "财富", "健康", "家庭", "六亲"]


# ============================================================
# 数据结构
# ============================================================

@dataclass
class FlowYearEnergy:
    """单流年能量场。"""
    year: int
    age: int
    liunian: str                 # 干支字符串如 "癸亥"
    dayun: str                   # 当年所在大运干支
    relations: list[str] = field(default_factory=list)   # ["寅亥六合", "申冲年支寅"]
    main_energy: str = ""        # 主能量类型，如 "印重 / 财动"
    strength: Strength = "●"
    domains: list[str] = field(default_factory=list)     # ["学业","事业",...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "year": self.year, "age": self.age,
            "liunian": self.liunian, "dayun": self.dayun,
            "relations": list(self.relations),
            "main_energy": self.main_energy,
            "strength": self.strength,
            "domains": list(self.domains),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "FlowYearEnergy":
        return cls(
            year=int(d["year"]), age=int(d["age"]),
            liunian=str(d["liunian"]), dayun=str(d["dayun"]),
            relations=list(d.get("relations", [])),
            main_energy=str(d.get("main_energy", "")),
            strength=str(d.get("strength", "●")),  # type: ignore
            domains=list(d.get("domains", [])),
        )


@dataclass
class DaiyunSegment:
    """一段大运 + 包含的流年。"""
    seq: int                     # 大运序号（1=丙子...）
    ganzhi: str                  # 干支
    age_range: tuple[int, int]   # (起岁, 止岁)
    year_range: tuple[int, int]  # (起年, 止年[非含])
    feature: str = ""            # 一句话描述大运能量主旋律
    typical_domains: list[str] = field(default_factory=list)
    flow_years: list[FlowYearEnergy] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "seq": self.seq, "ganzhi": self.ganzhi,
            "age_range": list(self.age_range),
            "year_range": list(self.year_range),
            "feature": self.feature,
            "typical_domains": list(self.typical_domains),
            "flow_years": [f.to_dict() for f in self.flow_years],
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "DaiyunSegment":
        return cls(
            seq=int(d["seq"]),
            ganzhi=str(d["ganzhi"]),
            age_range=(int(d["age_range"][0]), int(d["age_range"][1])),
            year_range=(int(d["year_range"][0]), int(d["year_range"][1])),
            feature=str(d.get("feature", "")),
            typical_domains=list(d.get("typical_domains", [])),
            flow_years=[FlowYearEnergy.from_dict(x) for x in d.get("flow_years", [])],
        )


@dataclass
class RetrospectiveReport:
    """完整流年回溯报告。"""
    case_id: str
    birth_year: int
    current_year: int
    current_age: int
    current_dayun: str
    segments: list[DaiyunSegment] = field(default_factory=list)
    note: str = (
        "本模块输出为结构性力量场，不构成应期铁断。"
        "应期铁断需 D3 三层 gate 激活（依赖 known_facts）。"
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "birth_year": self.birth_year,
            "current_year": self.current_year,
            "current_age": self.current_age,
            "current_dayun": self.current_dayun,
            "segments": [s.to_dict() for s in self.segments],
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "RetrospectiveReport":
        return cls(
            case_id=str(d.get("case_id", "")),
            birth_year=int(d.get("birth_year", 0)),
            current_year=int(d.get("current_year", 0)),
            current_age=int(d.get("current_age", 0)),
            current_dayun=str(d.get("current_dayun", "")),
            segments=[DaiyunSegment.from_dict(x) for x in d.get("segments", [])],
            note=str(d.get("note", "")),
        )


# ============================================================
# 二、能量类型推断辅助
# ============================================================

def _shishen_class(s: Optional[str]) -> str:
    """十神 → 大类（比劫/食伤/财/官杀/印）。"""
    if not s:
        return ""
    if s in ("比肩", "劫财"):
        return "比劫"
    if s in ("食神", "伤官"):
        return "食伤"
    if s in ("正财", "偏财"):
        return "财"
    if s in ("正官", "七杀"):
        return "官杀"
    if s in ("正印", "偏印"):
        return "印"
    return s


def _scan_year_relations(bazi: Bazi, dayun_gz: GanZhi, ln: GanZhi) -> list[str]:
    """扫描流年与原局 + 大运的关键作用。返回中文描述列表。"""
    out: list[str] = []
    # 干合（流年干 vs 4 柱干 + 大运干）
    targets = [
        ("年干", bazi.年柱.gan), ("月干", bazi.月柱.gan),
        ("日干", bazi.日柱.gan), ("时干", bazi.时柱.gan),
        ("大运干", dayun_gz.gan),
    ]
    for label, g in targets:
        wx = gan_he(ln.gan, g)
        if wx:
            out.append(f"流年干合{label}{g}化{wx}")
    # 支冲
    zhi_targets = [
        ("年支", bazi.年柱.zhi), ("月支", bazi.月柱.zhi),
        ("日支", bazi.日柱.zhi), ("时支", bazi.时柱.zhi),
        ("大运支", dayun_gz.zhi),
    ]
    for label, z in zhi_targets:
        if zhi_chong(ln.zhi, z):
            out.append(f"流年支冲{label}{z}")
    # 六合
    for label, z in zhi_targets:
        wx = zhi_liuhe(ln.zhi, z)
        if wx:
            out.append(f"流年支六合{label}{z}化{wx}")
    # 穿
    for label, z in zhi_targets:
        if zhi_chuan(ln.zhi, z):
            out.append(f"流年支穿{label}{z}")
    # 刑
    for label, z in zhi_targets:
        x = zhi_xing(ln.zhi, z)
        if x:
            out.append(f"流年支{x}{label}{z}")
    # 伏吟（同支）
    for label, z in zhi_targets:
        if ln.zhi == z and label != "年支":  # 与年支同则简单提
            out.append(f"流年伏吟{label}({z})")
    return out


def _infer_main_energy(
    bazi: Bazi,
    ln: GanZhi,
    dayun_gz: GanZhi,
    relations: Optional[list[str]] = None,
) -> tuple[str, Strength, list[str]]:
    """根据流年干十神（对日主）+ 流年支主气十神 推主能量类型。"""
    day_master = bazi.日柱.gan
    g_shishen = get_shishen(ln.gan, day_master)
    z_shishen = None  # 简化：不用支主气
    cls = _shishen_class(g_shishen)
    energy_label_map = {
        "比劫": "同业竞争 / 同辈互动",
        "食伤": "技术产出 / 子女 / 表达",
        "财": "财动 / 婚动",
        "官杀": "工作变动 / 压力",
        "印": "学问 / 文书 / 长辈",
    }
    main = energy_label_map.get(cls, f"{cls}年")

    # 强弱：默认 ●，关键支冲冲发 → ▲，伏吟+穿+刑 多 → ▽
    if relations is None:
        relations = _scan_year_relations(bazi, dayun_gz, ln)
    has_chong = any("冲" in r for r in relations)
    has_he = any("六合" in r for r in relations) or any("流年干合" in r for r in relations)
    has_neg = any("穿" in r or "伏吟" in r or "刑" in r for r in relations)
    if has_chong and has_he:
        s = "▲"   # 冲发后合 = 大转折
    elif has_chong:
        s = "●" if cls in ("印", "比劫") else "▲"
    elif has_he and not has_neg:
        s = "▲"
    elif has_neg and not has_he:
        s = "▽"
    else:
        s = "●"

    # 推测域（基于流年干十神类）
    domains = []
    if cls == "印":
        domains = ["学业", "家庭", "六亲"]
    elif cls == "财":
        domains = ["财富", "婚姻"]
    elif cls == "官杀":
        domains = ["事业", "健康"]
    elif cls == "食伤":
        domains = ["事业", "财富"]
    elif cls == "比劫":
        domains = ["事业", "家庭"]
    return main, s, domains  # type: ignore


def _dayun_feature(bazi: Bazi, dy: GanZhi) -> tuple[str, list[str]]:
    """大运特征 + 典型域。"""
    day_master = bazi.日柱.gan
    g_shishen = _shishen_class(get_shishen(dy.gan, day_master))
    feature = f"{dy.gan}{g_shishen} + {dy.zhi}支气"
    domain_map = {
        "印": ["学业", "家庭"],
        "比劫": ["事业", "家庭"],
        "食伤": ["事业", "子女"],
        "财": ["财富", "婚姻"],
        "官杀": ["事业", "健康"],
    }
    return feature, domain_map.get(g_shishen, ["综合"])


# ============================================================
# 三、主入口
# ============================================================

def scan_retrospective(
    parsed: ParsedInput,
    *,
    current_year: int = 2026,
    until_present_only: bool = True,
) -> RetrospectiveReport:
    """从起运年至 current_year 扫描流年回溯。

    Args:
        parsed: ParsedInput（含 bazi + dayun + birth）
        current_year: 截止流年（默认 2026 当前）
        until_present_only: True=只扫描到当前年；False=扫到所有大运结束

    Returns:
        RetrospectiveReport
    """
    bazi = parsed.bazi
    dayun = parsed.dayun
    birth_year = int((parsed.birth or {}).get("公历", "1980-01-01").split("-")[0])
    case_id = getattr(parsed, "case_id", "") or ""

    if not bazi or not dayun or not dayun.排布:
        return RetrospectiveReport(
            case_id=case_id,
            birth_year=birth_year,
            current_year=current_year,
            current_age=current_year - birth_year,
            current_dayun="—",
            segments=[],
            note="缺 bazi/dayun，无法回溯。",
        )

    current_age = current_year - birth_year
    current_step = None
    try:
        current_step = get_dayun_at_year(dayun, birth_year, current_year)
    except Exception:
        pass
    current_dayun = str(current_step.干支) if current_step else "—"

    end_year = current_year if until_present_only else dayun.排布[-1].起讫年[1] - 1

    segments: list[DaiyunSegment] = []
    for step in dayun.排布:
        y_start, y_end = step.起讫年
        # 大运覆盖到 [y_start, y_end-1]
        if y_start > end_year:
            break
        actual_end = min(y_end - 1, end_year)
        if actual_end < y_start:
            continue
        feat, doms = _dayun_feature(bazi, step.干支)
        seg = DaiyunSegment(
            seq=step.序号,
            ganzhi=str(step.干支),
            age_range=(step.起岁, step.止岁),
            year_range=(y_start, y_end),
            feature=feat,
            typical_domains=doms,
            flow_years=[],
        )
        for y in range(y_start, actual_end + 1):
            ln = liunian_ganzhi(y)
            relations = _scan_year_relations(bazi, step.干支, ln)
            main, strength, domains = _infer_main_energy(
                bazi, ln, step.干支, relations=relations
            )
            age = y - birth_year
            seg.flow_years.append(FlowYearEnergy(
                year=y, age=age,
                liunian=f"{ln.gan}{ln.zhi}",
                dayun=str(step.干支),
                relations=relations,
                main_energy=main,
                strength=strength,
                domains=domains,
            ))
        segments.append(seg)

    return RetrospectiveReport(
        case_id=case_id,
        birth_year=birth_year,
        current_year=current_year,
        current_age=current_age,
        current_dayun=current_dayun,
        segments=segments,
        note=(
            "本模块输出为结构性力量场（哪一年发生什么类型的能量碰撞），"
            "不构成应期铁断。应期铁断需 D3 三层 gate 激活（依赖 known_facts）。"
        ),
    )


# ============================================================
# 四、smoke
# ============================================================

def _smoke() -> None:
    """需 fixture cases，用 C-2026-015（已知案例）跑一遍。"""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
    from tools.preflight import parse
    p = parse(
        Path("cases/C-2026-015-乾-甲寅乙亥丙辰辛卯/input.md"),
        Path("cases/cases-index.md"),
    )
    from engine.predicates.types import adapt_parsed
    parsed = adapt_parsed(p)
    rr = scan_retrospective(parsed, current_year=2026)
    print(f"case_id: {rr.case_id}")
    print(f"birth_year: {rr.birth_year}, current_age: {rr.current_age}")
    print(f"current_dayun: {rr.current_dayun}")
    print(f"segments: {len(rr.segments)}")
    for seg in rr.segments:
        n_years = len(seg.flow_years)
        print(f"  Dayun #{seg.seq} {seg.ganzhi} ({seg.year_range[0]}-{seg.year_range[1]-1}, "
              f"岁 {seg.age_range[0]}-{seg.age_range[1]}): {n_years} 流年, feature={seg.feature}")
        if seg.flow_years:
            f = seg.flow_years[0]
            print(f"    e.g. {f.year} {f.liunian} 岁{f.age} {f.strength} "
                  f"{f.main_energy} | rel={'; '.join(f.relations[:2])}")
    # round-trip
    rr2 = RetrospectiveReport.from_dict(rr.to_dict())
    assert rr2.to_dict() == rr.to_dict()
    print("[OK] retrospective smoke 通过")


if __name__ == "__main__":  # pragma: no cover
    _smoke()

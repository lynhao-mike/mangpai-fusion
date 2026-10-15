"""engine/facts/chart_facts.py · 统一盘面事实 ChartFacts 的构造入口。

两个入口：
- ``chart_from_solar(dt, gender)``：公历时刻（调用方已完成真太阳时校正）→ lunar-python 排盘。
- ``chart_from_pillars(pillars, gender)``：直接给四柱，严格校验六十甲子、五虎遁、五鼠遁。

只输出客观事实与带出处的标签；争议口径由 ``profiles.yaml`` 注册，
与默认口径不同的字段写进 ``variants``，无差异则不写。
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from datetime import datetime, timedelta
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal, Optional, Sequence

import yaml

from engine.facts.types import (
    PALACE_PREFIX,
    PALACES,
    Addr,
    BoundaryWarning,
    BranchSlot,
    ChartFacts,
    Cycles,
    DayunStep,
    HiddenStem,
    InputEcho,
    KongWang,
    Pillar,
    ProfileSet,
    QiyunVariant,
    SelfSit,
    SourceTag,
    StemSlot,
    Variant,
)
from engine.predicates.palace import get_shishen
from engine.predicates.types import (
    CHANGSHENG_TABLE,
    GAN_LIST,
    GAN_TO_WUXING,
    GAN_YINYANG,
    SHENG_ORDER,
    ZHI_CANGGAN_TABLE,
    ZHI_LIST,
    ZHI_TO_WUXING,
    ZHI_YINYANG,
)

SCHEMA_VERSION = "chart-facts/v1"
PROFILES_PATH = Path(__file__).with_name("profiles.yaml")

# ── 出处常量（相对仓库根目录:行号）───────────────────────────────────────────
REF_KAISHAN = "sources/duan/MinerU_markdown_35.盲派命理开山之作_2056045397672648704.md"
REF_GAO_SHENSHA = "sources/gao/盲派神煞应用宝典.md"
REF_D01 = "theory/raw/duan/d01-deep-read.md"
REF_D02 = "theory/raw/duan/d02-theory.md"
REF_BINZHU = "theory/duan/index.yaml"   # M1-D-001..004 宾主四层

JIAZI: tuple[str, ...] = tuple(GAN_LIST[i % 10] + ZHI_LIST[i % 12] for i in range(60))
_QI_LABEL = {"主气": "本气", "中气": "中气", "余气": "余气"}
_LU = {"甲": "寅", "乙": "卯", "丙": "巳", "丁": "午", "戊": "巳",
       "己": "午", "庚": "申", "辛": "酉", "壬": "亥", "癸": "子"}
_YANG_REN = {"甲": "卯", "丙": "午", "戊": "午", "庚": "酉", "壬": "子"}
_YIN_REN = {"乙": "辰", "丁": "未", "己": "未", "辛": "戌", "癸": "丑"}     # 高派阴刃
_YIN_TO_YANG = {"乙": "甲", "丁": "丙", "己": "戊", "辛": "庚", "癸": "壬"}

# 段派《开山之作》:1338 干支自合
_ZIHE_BRANCH_CONTROLS = frozenset({"丁亥", "己亥", "辛巳", "癸巳"})
_ZIHE_STEM_COMBINES = frozenset({"壬午", "甲午", "戊子"})
_ZIHE_NEEDS_XING = frozenset({"丙戌", "壬戌"})
# 段派连体字：D-02 列举（d02-theory.md:237）与 D-01 列举（d02-theory.md:920 转述）
_LIANTI_D02 = frozenset({"戊申", "辛酉", "丁巳", "甲午", "己酉", "庚子"})
_LIANTI_D01 = frozenset({"丁巳", "丙戌", "丙午", "乙亥", "乙卯", "甲寅", "甲辰", "乙未", "庚申", "辛酉"})
# 段派带象 12 柱（d01-deep-read.md:377，干生支）
_DAIXIANG = frozenset({"甲午", "乙巳", "丙辰", "丙戌", "丁丑", "丁未",
                       "戊申", "己酉", "庚子", "辛亥", "壬寅", "癸卯"})

_GENDER = {"乾": "乾", "M": "乾", "MALE": "乾", "男": "乾",
           "坤": "坤", "F": "坤", "FEMALE": "坤", "女": "坤"}
_NEAR_JIE_HOURS = 2.0


class ChartInputError(ValueError):
    """输入四柱/大运/性别不合法；引擎不静默修正。"""


# ── 口径注册表 ───────────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def load_profiles() -> dict[str, Any]:
    data = yaml.safe_load(PROFILES_PATH.read_text(encoding="utf-8"))
    for axis, spec in data["axes"].items():
        for value, body in spec["values"].items():
            if not body.get("source_refs"):
                raise ValueError(f"口径 {axis}={value} 缺少 source_refs")
        if spec["default"] not in spec["values"]:
            raise ValueError(f"口径 {axis} 的 default 未注册")
    return data


def validate_profile(profile: ProfileSet) -> ProfileSet:
    axes = load_profiles()["axes"]
    for axis, value in profile.to_dict().items():
        if axis not in axes or value not in axes[axis]["values"]:
            raise ChartInputError(f"未注册的口径 {axis}={value}")
    return profile


def alternatives(axis: str, current: str) -> list[str]:
    return [v for v in load_profiles()["axes"][axis]["values"] if v != current]


# ── 地址与宾主 ───────────────────────────────────────────────────────────────

def natal_addr(palace_index: int, layer: Literal["s", "b"]) -> Addr:
    return f"{PALACE_PREFIX[PALACES[palace_index]]}.{layer}"


def binzhu_side(addr: Addr, layer: Literal[1, 2, 3, 4]) -> Literal["主", "宾"]:
    """段派宾主四层（M1-D-001..004）。宾主由位置决定，不进每份 JSON。

    1：日干为主，其余 7 字为宾；2：日柱为主；3：日柱+时柱为主；4：原局为主，岁运为宾。
    """
    head = addr.split(".", 1)[0]
    natal = head in ("Y", "M", "D", "H")
    if layer == 4:
        return "主" if natal else "宾"
    if not natal:
        raise ValueError(f"宾主第 {layer} 层只定义原局 8 字：{addr}")
    if layer == 1:
        return "主" if addr == "D.s" else "宾"
    if layer == 2:
        return "主" if head == "D" else "宾"
    if layer == 3:
        return "主" if head in ("D", "H") else "宾"
    raise ValueError(f"宾主层只有 1-4：{layer}")


# ── 基础查表 ─────────────────────────────────────────────────────────────────

def wuxing_relation(a: str, b: str) -> Literal["同", "生", "被生", "克", "被克"]:
    """a 对 b：同 / a 生 b / b 生 a / a 克 b / b 克 a。"""
    if a == b:
        return "同"
    ia, ib = SHENG_ORDER.index(a), SHENG_ORDER.index(b)
    if (ia + 1) % 5 == ib:
        return "生"
    if (ib + 1) % 5 == ia:
        return "被生"
    if (ia + 2) % 5 == ib:
        return "克"
    return "被克"


def changsheng(gan: str, zhi: str, profile: ProfileSet) -> str:
    if profile.yin_changsheng == "yin_same_as_yang" and gan in _YIN_TO_YANG:
        gan = _YIN_TO_YANG[gan]
    return CHANGSHENG_TABLE[gan][zhi]


def hidden_stems(zhi: str, day_master: str) -> tuple[HiddenStem, ...]:
    return tuple(
        HiddenStem(char=g, qi=_QI_LABEL[t], ten_god=get_shishen(g, day_master))  # type: ignore[arg-type]
        for g, t, _ in ZHI_CANGGAN_TABLE[zhi]
    )


def jiazi_index(gz: str) -> int:
    try:
        return JIAZI.index(gz)
    except ValueError as exc:
        raise ChartInputError(f"非六十甲子：{gz!r}") from exc


def xun_of(gz: str) -> tuple[str, tuple[str, str]]:
    """所在旬名与旬空两支。"""
    start = jiazi_index(gz) // 10 * 10
    zi = start % 12
    return JIAZI[start] + "旬", (ZHI_LIST[(zi + 10) % 12], ZHI_LIST[(zi + 11) % 12])


def nayin(gz: str) -> str:
    from lunar_python.util import LunarUtil
    return LunarUtil.NAYIN[gz]


def month_stem_for(year_stem: str, month_branch: str) -> str:
    """五虎遁：年干 → 该月支对应月干。"""
    start = (GAN_LIST.index(year_stem) % 5 * 2 + 2) % 10
    offset = (ZHI_LIST.index(month_branch) - 2) % 12
    return GAN_LIST[(start + offset) % 10]


def hour_stem_for(day_stem: str, hour_branch: str) -> str:
    """五鼠遁：日干 → 该时支对应时干。"""
    start = GAN_LIST.index(day_stem) % 5 * 2 % 10
    return GAN_LIST[(start + ZHI_LIST.index(hour_branch)) % 10]


def dayun_sequence(month_gz: str, forward: bool, n: int = 10) -> tuple[str, ...]:
    i = jiazi_index(month_gz)
    step = 1 if forward else -1
    return tuple(JIAZI[(i + step * (k + 1)) % 60] for k in range(n))


def is_forward(gender: str, year_stem: str) -> bool:
    return (GAN_YINYANG[year_stem] == "阳") == (gender == "乾")


# ── 柱构造 ───────────────────────────────────────────────────────────────────

def _self_sit(gan: str, zhi: str, profile: ProfileSet) -> SelfSit:
    status = changsheng(gan, zhi, profile)
    marks: list[str] = []
    if _LU[gan] == zhi:
        marks.append("坐禄")
    if _YANG_REN.get(gan) == zhi:
        marks.append("坐羊刃")
    if status == "长生":
        marks.append("坐长生")
    if status == "墓":
        marks.append("坐墓")
    rel = wuxing_relation(GAN_TO_WUXING[gan], ZHI_TO_WUXING[zhi])
    relation = {"同": "同气", "生": "干生支", "被生": "支生干", "克": "干克支", "被克": "支克干"}[rel]
    gan_wx = GAN_TO_WUXING[gan]
    rooted = tuple(_QI_LABEL[t] for g, t, _ in ZHI_CANGGAN_TABLE[zhi] if GAN_TO_WUXING[g] == gan_wx)
    return SelfSit(stem_changsheng=status, marks=tuple(marks),
                   stem_branch_relation=relation, rooted_in_own_branch=rooted)  # type: ignore[arg-type]


def _pillar_tags(gz: str) -> tuple[SourceTag, ...]:
    tags: list[SourceTag] = []
    if gz in _ZIHE_BRANCH_CONTROLS:
        tags.append(SourceTag("干支自合·支合克干", "duan", f"{REF_KAISHAN}:1338"))
    if gz in _ZIHE_STEM_COMBINES:
        tags.append(SourceTag("干支自合·干合支", "duan", f"{REF_KAISHAN}:1338"))
    if gz in _ZIHE_NEEDS_XING:
        tags.append(SourceTag("干支自合·需戌逢未刑", "duan", f"{REF_KAISHAN}:1338"))
    if gz in _LIANTI_D02:
        tags.append(SourceTag("连体字(D-02列举)", "duan", f"{REF_D02}:237"))
    if gz in _LIANTI_D01:
        tags.append(SourceTag("连体字(D-01列举)", "duan", f"{REF_D02}:920"))
    if gz in _DAIXIANG:
        tags.append(SourceTag("带象(干生支)", "duan", f"{REF_D01}:377"))
    if _YIN_REN.get(gz[0]) == gz[1]:
        tags.append(SourceTag("坐阴刃", "gao", f"{REF_GAO_SHENSHA}:1095"))
    return tuple(tags)


def _pillar(index: int, gz: str, day_master: str, profile: ProfileSet) -> Pillar:
    gan, zhi = gz[0], gz[1]
    hidden = hidden_stems(zhi, day_master)
    xun, _ = xun_of(gz)
    return Pillar(
        index=index,
        palace=PALACES[index],
        ganzhi=gz,
        stem=StemSlot(
            addr=natal_addr(index, "s"), char=gan, wuxing=GAN_TO_WUXING[gan],
            yinyang=GAN_YINYANG[gan],
            ten_god="日主" if index == 2 else get_shishen(gan, day_master),  # type: ignore[arg-type]
        ),
        branch=BranchSlot(
            addr=natal_addr(index, "b"), char=zhi, wuxing=ZHI_TO_WUXING[zhi],
            yinyang=ZHI_YINYANG[zhi], hidden=hidden, main_ten_god=hidden[0].ten_god,
        ),
        nayin=nayin(gz),
        xun=xun,
        self_sit=_self_sit(gan, zhi, profile),
        source_tags=_pillar_tags(gz),
    )


def _kongwang(pillars: Sequence[str]) -> KongWang:
    _, by_day = xun_of(pillars[2])
    _, by_year = xun_of(pillars[0])
    hits: list[tuple[Addr, Literal["day", "year"]]] = []
    for i, gz in enumerate(pillars):
        if gz[1] in by_day:
            hits.append((natal_addr(i, "b"), "day"))
        if gz[1] in by_year:
            hits.append((natal_addr(i, "b"), "year"))
    return KongWang(by_day_xun=by_day, by_year_xun=by_year, hits=tuple(hits))


# ── 校验 ────────────────────────────────────────────────────────────────────

def normalize_gender(gender: str) -> Literal["乾", "坤"]:
    key = str(gender).strip().upper() if str(gender).strip().isascii() else str(gender).strip()
    if key not in _GENDER:
        raise ChartInputError(f"无法识别的性别：{gender!r}（用 乾/坤/M/F）")
    return _GENDER[key]  # type: ignore[return-value]


def validate_pillars(pillars: Sequence[str]) -> list[BoundaryWarning]:
    """六十甲子 + 五虎遁 + 五鼠遁。晚子时（时干按次日五鼠遁）放行并给提示。"""
    if len(pillars) != 4:
        raise ChartInputError(f"四柱必须 4 个：{list(pillars)!r}")
    for gz in pillars:
        jiazi_index(gz)
    year, month, day, hour = pillars
    expected_month = month_stem_for(year[0], month[1])
    if month[0] != expected_month:
        raise ChartInputError(f"月柱 {month} 不合五虎遁：{year[0]}年{month[1]}月应为 {expected_month}{month[1]}")
    warnings: list[BoundaryWarning] = []
    expected_hour = hour_stem_for(day[0], hour[1])
    if hour[0] != expected_hour:
        next_day_stem = GAN_LIST[(GAN_LIST.index(day[0]) + 1) % 10]
        if hour[1] == "子" and hour[0] == hour_stem_for(next_day_stem, "子"):
            warnings.append(BoundaryWarning(
                "hour_stem_next_day",
                f"时柱 {hour} 按次日 {next_day_stem} 日五鼠遁，符合晚子时 late_zi_split 口径",
            ))
        else:
            raise ChartInputError(f"时柱 {hour} 不合五鼠遁：{day[0]}日{hour[1]}时应为 {expected_hour}{hour[1]}")
    return warnings


# ── 差异工具（variants 共用）──────────────────────────────────────────────────

def json_diff(a: Any, b: Any, path: str = "") -> list[tuple[str, Any]]:
    """返回 (JSON Pointer, b 中的值)；列表长度不同时整体替换。"""
    if isinstance(a, dict) and isinstance(b, dict):
        out: list[tuple[str, Any]] = []
        for k in sorted(set(a) | set(b), key=str):
            out.extend(json_diff(a.get(k), b.get(k), f"{path}/{k}"))
        return out
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)) and len(a) == len(b):
        out = []
        for i, (x, y) in enumerate(zip(a, b)):
            out.extend(json_diff(x, y, f"{path}/{i}"))
        return out
    return [] if a == b else [(path or "/", b)]


def _canonical_id(prefix: str, payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return prefix + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:20]


# ── 核心构造 ────────────────────────────────────────────────────────────────

def _build(
    pillars: tuple[str, str, str, str],
    gender: Literal["乾", "坤"],
    profile: ProfileSet,
    echo: InputEcho,
    cycles: Optional[Cycles],
    warnings: Sequence[BoundaryWarning],
) -> ChartFacts:
    day_master = pillars[2][0]
    chart_id = _canonical_id("cf-", {
        "schema": SCHEMA_VERSION, "pillars": list(pillars), "gender": gender,
        "profile": profile.to_dict(), "solar": echo.solar_datetime,
    })
    return ChartFacts(
        schema_version=SCHEMA_VERSION,
        chart_id=chart_id,
        input=echo,
        profile=profile,
        gender=gender,
        day_master=day_master,
        pillars=tuple(_pillar(i, gz, day_master, profile) for i, gz in enumerate(pillars)),  # type: ignore[arg-type]
        kongwang=_kongwang(pillars),
        cycles=cycles,
        boundary_warnings=tuple(warnings),
    )


def _profile_variants(base: ChartFacts, rebuild) -> tuple[Variant, ...]:
    """对不改变四柱的争议轴（yin_changsheng）逐个重算，只保留差异。"""
    variants: list[Variant] = []
    base_dict = base.to_dict()
    for alt in alternatives("yin_changsheng", base.profile.yin_changsheng):
        other = rebuild(replace(base.profile, yin_changsheng=alt))
        diffs = json_diff(base_dict["pillars"], other.to_dict()["pillars"], "/pillars")
        if diffs:
            variants.append(Variant("yin_changsheng", alt, tuple(diffs)))
    return tuple(variants)


def chart_from_pillars(
    pillars: Sequence[str],
    gender: str,
    *,
    dayun: Optional[Sequence[str]] = None,
    dayun_start_year: Optional[int] = None,
    profile: Optional[ProfileSet] = None,
) -> ChartFacts:
    """直接用四柱构造。``dayun`` 若提供必须与月柱推出的顺逆序列一致。"""
    profile = validate_profile(profile or ProfileSet())
    gz4 = tuple(str(p).strip() for p in pillars)
    warnings = validate_pillars(gz4)
    sex = normalize_gender(gender)
    forward = is_forward(sex, gz4[0][0])
    n = len(dayun) if dayun else 10
    expected = dayun_sequence(gz4[1], forward, n)
    if dayun is not None and tuple(dayun) != expected:
        raise ChartInputError(f"大运 {list(dayun)} 与月柱 {gz4[1]} {'顺' if forward else '逆'}排 {list(expected)} 不一致")
    steps = tuple(
        DayunStep(
            index=k + 1, ganzhi=gz,
            start_year=None if dayun_start_year is None else dayun_start_year + 10 * k,
            end_year=None if dayun_start_year is None else dayun_start_year + 10 * k + 9,
        )
        for k, gz in enumerate(expected)
    )
    cycles = Cycles(direction="顺" if forward else "逆", qiyun=(), dayun=steps)
    echo = InputEcho(mode="pillars", solar_datetime=None, true_solar_corrected=None,
                     supplied_dayun=tuple(dayun) if dayun is not None else None)

    def rebuild(p: ProfileSet) -> ChartFacts:
        return _build(gz4, sex, p, echo, cycles, warnings)  # type: ignore[arg-type]

    base = rebuild(profile)
    return replace(base, variants=_profile_variants(base, rebuild))


def _lunar_eight_char(dt: datetime, zi_shi: str):
    from lunar_python import Solar

    lunar = Solar.fromYmdHms(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second).getLunar()
    ec = lunar.getEightChar()
    ec.setSect(2 if zi_shi == "late_zi_split" else 1)
    return lunar, ec


def _solar_dt(solar) -> datetime:
    return datetime(solar.getYear(), solar.getMonth(), solar.getDay(),
                    solar.getHour(), solar.getMinute(), solar.getSecond())


def _boundary_warnings(dt: datetime, lunar) -> list[BoundaryWarning]:
    out: list[BoundaryWarning] = []
    if dt.hour == 23:
        out.append(BoundaryWarning("late_zi", "23:00-23:59 晚子时：日柱随 zi_shi 口径变化，见 variants"))
    elif dt.hour == 0:
        out.append(BoundaryWarning("early_zi", "00:00-00:59 早子时：出生时刻若跨过 0 点，日柱会变"))
    for jie in (lunar.getPrevJie(), lunar.getNextJie()):
        jie_dt = _solar_dt(jie.getSolar())
        gap = abs((jie_dt - dt).total_seconds()) / 3600
        if gap <= _NEAR_JIE_HOURS:
            out.append(BoundaryWarning(
                "near_jie", f"距{jie.getName()}交节 {jie_dt:%Y-%m-%d %H:%M:%S} 仅 {gap:.2f} 小时，月柱/年柱可能不同",
            ))
    return out


def chart_from_solar(
    dt: datetime,
    gender: str,
    *,
    profile: Optional[ProfileSet] = None,
    true_solar_corrected: Optional[bool] = None,
) -> ChartFacts:
    """公历时刻排盘。``dt`` 必须为无时区本地时间；引擎不做经度/真太阳时换算。"""
    from engine.asof.qiyun_calculator import calc_qiyun

    if dt.tzinfo is not None:
        raise ChartInputError("dt 必须是已校正的无时区 datetime")
    profile = validate_profile(profile or ProfileSet())
    sex = normalize_gender(gender)

    def pillars_for(p: ProfileSet) -> tuple[str, str, str, str]:
        _, ec = _lunar_eight_char(dt, p.zi_shi)
        return (ec.getYear(), ec.getMonth(), ec.getDay(), ec.getTime())

    lunar, ec = _lunar_eight_char(dt, profile.zi_shi)
    gz4 = pillars_for(profile)
    yun = ec.getYun(1 if sex == "乾" else 0, 1)
    steps = tuple(
        DayunStep(index=k, ganzhi=item.getGanZhi(), start_year=item.getStartYear(), end_year=item.getEndYear())
        for k, item in enumerate(yun.getDaYun(11))
        if item.getGanZhi()
    )
    q = calc_qiyun(dt, "M" if sex == "乾" else "F", gz4[0][0])
    qiyun = (
        QiyunVariant("mangpai_rough", float(q.mang_pai_start_age), None, "engine/asof/qiyun_calculator.py"),
        QiyunVariant("precise", float(q.hk_tw_start_years), q.hk_tw_start_datetime or None,
                     "engine/asof/qiyun_calculator.py"),
    )
    cycles = Cycles(direction="顺" if yun.isForward() else "逆", qiyun=qiyun, dayun=steps)
    echo = InputEcho(mode="solar", solar_datetime=dt.isoformat(sep=" ", timespec="seconds"),
                     true_solar_corrected=true_solar_corrected, supplied_dayun=None)
    warnings = _boundary_warnings(dt, lunar)

    def rebuild(p: ProfileSet) -> ChartFacts:
        return _build(pillars_for(p), sex, p, echo, cycles, warnings)

    base = rebuild(profile)
    variants = list(_profile_variants(base, rebuild))
    for alt in alternatives("zi_shi", profile.zi_shi):
        alt_chart = rebuild(replace(profile, zi_shi=alt))
        diffs = [(f"/pillars/{i}/ganzhi", a.ganzhi)
                 for i, (b, a) in enumerate(zip(base.pillars, alt_chart.pillars)) if a.ganzhi != b.ganzhi]
        if diffs:
            variants.append(Variant("zi_shi", alt, tuple(diffs), alt_chart_id=alt_chart.chart_id))
    return replace(base, variants=tuple(variants))


__all__ = [
    "ChartInputError",
    "alternatives",
    "binzhu_side",
    "changsheng",
    "chart_from_pillars",
    "chart_from_solar",
    "dayun_sequence",
    "hour_stem_for",
    "json_diff",
    "load_profiles",
    "month_stem_for",
    "validate_pillars",
    "wuxing_relation",
]

"""engine/predicates/types.py · v1.2 共用类型

定义所有谓词函数和 4 个 Findings 共用的基础类型。
严格遵守 02-predicate-library.md § 三的契约。

兼容性：
- GanZhi 使用 frozen dataclass（契约要求）
- 字段名沿用契约的中文标识符（年柱/月柱/日柱/时柱/藏干）
- Bazi 提供 attribute access；与 tools/preflight.py 的 dict[str, GanZhi]
  形态不完全一致，需用 ``adapt_bazi`` 适配。

Python 3.10+ 必需。
作者：Track-A
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Literal, Optional, Union

# ============================================================
# 一、字面量类型
# ============================================================

Gan = Literal["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
Zhi = Literal["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
Wuxing = Literal["金", "木", "水", "火", "土"]
YinYang = Literal["阴", "阳"]
Polarity = Literal["阳干", "阴干", "阳支", "阴支"]

CangganType = Literal["主气", "中气", "余气"]

PalaceName = Literal["年柱", "月柱", "日柱", "时柱", "年支", "月支", "日支", "时支"]

Shishen = Literal[
    "比肩", "劫财", "食神", "伤官",
    "正财", "偏财", "正官", "七杀",
    "正印", "偏印",
]

ChangshengStatus = Literal[
    "长生", "沐浴", "冠带", "临官", "帝旺",
    "衰", "病", "死", "墓", "绝", "胎", "养",
]

# ============================================================
# 二、常量表（不可变 tuple，便于 index）
# ============================================================

GAN_LIST: tuple[Gan, ...] = (
    "甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸",
)
ZHI_LIST: tuple[Zhi, ...] = (
    "子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥",
)
WUXING_LIST: tuple[Wuxing, ...] = ("木", "火", "土", "金", "水")

# 五行相生顺序（前→后）
SHENG_ORDER: tuple[Wuxing, ...] = ("木", "火", "土", "金", "水")
# 五行相克：木→土 / 土→水 / 水→火 / 火→金 / 金→木
KE_MAP: dict[Wuxing, Wuxing] = {
    "木": "土", "土": "水", "水": "火", "火": "金", "金": "木",
}

# 天干 → 五行
GAN_TO_WUXING: dict[Gan, Wuxing] = {
    "甲": "木", "乙": "木",
    "丙": "火", "丁": "火",
    "戊": "土", "己": "土",
    "庚": "金", "辛": "金",
    "壬": "水", "癸": "水",
}
# 地支 → 五行
ZHI_TO_WUXING: dict[Zhi, Wuxing] = {
    "寅": "木", "卯": "木",
    "巳": "火", "午": "火",
    "申": "金", "酉": "金",
    "亥": "水", "子": "水",
    "辰": "土", "戌": "土", "丑": "土", "未": "土",
}

# 阴阳
GAN_YINYANG: dict[Gan, YinYang] = {
    "甲": "阳", "丙": "阳", "戊": "阳", "庚": "阳", "壬": "阳",
    "乙": "阴", "丁": "阴", "己": "阴", "辛": "阴", "癸": "阴",
}
ZHI_YINYANG: dict[Zhi, YinYang] = {
    "子": "阳", "寅": "阳", "辰": "阳", "午": "阳", "申": "阳", "戌": "阳",
    "丑": "阴", "卯": "阴", "巳": "阴", "未": "阴", "酉": "阴", "亥": "阴",
}

# 地支藏干（标准表，主气1.0 / 中气0.3 / 余气0.2）
# 数据来源：段建业讲义 + 业内通用表（详见 m1-foundation §2 附图）
ZHI_CANGGAN_TABLE: dict[Zhi, list[tuple[Gan, CangganType, float]]] = {
    "子": [("癸", "主气", 1.0)],
    "丑": [("己", "主气", 1.0), ("癸", "中气", 0.3), ("辛", "余气", 0.2)],
    "寅": [("甲", "主气", 1.0), ("丙", "中气", 0.3), ("戊", "余气", 0.2)],
    "卯": [("乙", "主气", 1.0)],
    "辰": [("戊", "主气", 1.0), ("乙", "中气", 0.3), ("癸", "余气", 0.2)],
    "巳": [("丙", "主气", 1.0), ("庚", "中气", 0.3), ("戊", "余气", 0.2)],
    "午": [("丁", "主气", 1.0), ("己", "中气", 0.3)],
    "未": [("己", "主气", 1.0), ("丁", "中气", 0.3), ("乙", "余气", 0.2)],
    "申": [("庚", "主气", 1.0), ("壬", "中气", 0.3), ("戊", "余气", 0.2)],
    "酉": [("辛", "主气", 1.0)],
    "戌": [("戊", "主气", 1.0), ("辛", "中气", 0.3), ("丁", "余气", 0.2)],
    "亥": [("壬", "主气", 1.0), ("甲", "中气", 0.3)],
}

# 12 长生表：天干 → (寄宫，按 12 支顺序排长生 12 状态)
# 行：阳干顺行 / 阴干逆行
# 段派沿用业界表（与杨派一致，差异不在长生表上）
_CHANGSHENG_ORDER: tuple[ChangshengStatus, ...] = (
    "长生", "沐浴", "冠带", "临官", "帝旺",
    "衰", "病", "死", "墓", "绝", "胎", "养",
)
# 各天干长生位（地支）
_GAN_CHANGSHENG_START: dict[Gan, Zhi] = {
    "甲": "亥", "丙": "寅", "戊": "寅", "庚": "巳", "壬": "申",
    "乙": "午", "丁": "酉", "己": "酉", "辛": "子", "癸": "卯",
}


def _build_changsheng_full() -> dict[Gan, dict[Zhi, ChangshengStatus]]:
    """构造完整 10 干 × 12 支 长生状态表。"""
    table: dict[Gan, dict[Zhi, ChangshengStatus]] = {}
    for gan in GAN_LIST:
        start_zhi = _GAN_CHANGSHENG_START[gan]
        start_idx = ZHI_LIST.index(start_zhi)
        is_yang = GAN_YINYANG[gan] == "阳"
        per_gan: dict[Zhi, ChangshengStatus] = {}
        for step, status in enumerate(_CHANGSHENG_ORDER):
            if is_yang:
                zhi_idx = (start_idx + step) % 12
            else:
                zhi_idx = (start_idx - step) % 12
            per_gan[ZHI_LIST[zhi_idx]] = status
        table[gan] = per_gan
    return table


CHANGSHENG_TABLE: dict[Gan, dict[Zhi, ChangshengStatus]] = _build_changsheng_full()


# ============================================================
# 三、核心 dataclass
# ============================================================

@dataclass(frozen=True)
class GanZhi:
    """干支柱组合（frozen，可哈希）。"""
    gan: Gan
    zhi: Zhi

    def __str__(self) -> str:
        return f"{self.gan}{self.zhi}"

    @classmethod
    def parse(cls, s: str) -> "GanZhi":
        """从字符串解析（兼容 tools.preflight.GanZhi）。"""
        if not isinstance(s, str) or len(s) != 2:
            raise ValueError(f"干支必须 2 字: {s!r}")
        gan, zhi = s[0], s[1]
        if gan not in GAN_LIST:
            raise ValueError(f"非法天干: {gan!r}")
        if zhi not in ZHI_LIST:
            raise ValueError(f"非法地支: {zhi!r}")
        if GAN_YINYANG[gan] != ZHI_YINYANG[zhi]:
            raise ValueError(f"非 60 甲子（阴阳不配）: {s!r}")
        return cls(gan=gan, zhi=zhi)


@dataclass
class Canggan:
    """地支藏干。"""
    gan: Gan
    type: CangganType  # 主气 / 中气 / 余气
    li_liang: float    # 0.0-1.0


@dataclass
class Bazi:
    """八字四柱 + 藏干。

    字段名沿用契约的中文标识符。藏干字典 key 为 年支/月支/日支/时支。
    """
    年柱: GanZhi
    月柱: GanZhi
    日柱: GanZhi
    时柱: GanZhi
    藏干: dict[str, list[Canggan]] = field(default_factory=dict)

    @property
    def day_master(self) -> Gan:
        return self.日柱.gan

    @property
    def 月令(self) -> Zhi:
        return self.月柱.zhi

    def all_pillars(self) -> list[tuple[str, GanZhi]]:
        return [
            ("年柱", self.年柱),
            ("月柱", self.月柱),
            ("日柱", self.日柱),
            ("时柱", self.时柱),
        ]

    def all_gans(self) -> list[tuple[str, Gan]]:
        return [(name, gz.gan) for name, gz in self.all_pillars()]

    def all_zhis(self) -> list[tuple[str, Zhi]]:
        # 注意 key 形式："年支" 等
        return [
            ("年支", self.年柱.zhi),
            ("月支", self.月柱.zhi),
            ("日支", self.日柱.zhi),
            ("时支", self.时柱.zhi),
        ]


@dataclass
class DayunStep:
    """单步大运。"""
    序号: int
    干支: GanZhi
    起岁: int
    止岁: int
    起讫年: tuple[int, int]


@dataclass
class Dayun:
    """完整大运。"""
    起运岁: float
    起运年: int
    顺逆: Literal["顺", "逆"]
    排布: list[DayunStep] = field(default_factory=list)

    def at_age(self, age: int) -> Optional[DayunStep]:
        for step in self.排布:
            if step.起岁 <= age <= step.止岁:
                return step
        return None

    def at_year(self, year: int) -> Optional[DayunStep]:
        for step in self.排布:
            if step.起讫年[0] <= year < step.起讫年[1]:
                return step
        return None


# ============================================================
# 四、KnownFact / ParsedInput（契约式简化版）
# ============================================================

@dataclass
class KnownFact:
    type: str
    year: Optional[int] = None
    event: Optional[str] = None
    content: Optional[str] = None


@dataclass
class ParsedInput:
    """简化版 ParsedInput。

    Track-A 的引擎统一从此结构读取；preflight.parse() 输出可通过
    ``adapt_parsed`` 转换。
    """
    case_id: str
    bazi: Bazi
    dayun: Dayun
    birth: dict = field(default_factory=dict)
    shensha: dict[str, list[str]] = field(default_factory=dict)
    twelve_changsheng: dict[str, str] = field(default_factory=dict)
    known_facts: list[KnownFact] = field(default_factory=list)
    questions: list[str] = field(default_factory=list)
    case_meta: dict = field(default_factory=dict)
    fingerprint: str = ""
    schema_version: str = "1.2.0"


# ============================================================
# 五、Adapter：preflight.ParsedInput / dict → Track-A 形态
# ============================================================

def adapt_bazi(obj: object) -> Bazi:
    """把任意 bazi 形态（preflight dict、契约 Bazi、本地 Bazi）统一为 Bazi。

    支持：
    - ``Bazi`` 实例 → 直接返回
    - ``dict[str, GanZhi-like]`` → 构造 Bazi（藏干自动从标准表填充）
    """
    if isinstance(obj, Bazi):
        return obj

    # preflight.ParsedInput 的 bazi: dict[str, GanZhi-like]
    if isinstance(obj, dict):
        pillars = obj
        get = lambda k: _to_local_ganzhi(pillars[k])
        bazi = Bazi(
            年柱=get("年柱"),
            月柱=get("月柱"),
            日柱=get("日柱"),
            时柱=get("时柱"),
            藏干={},
        )
        bazi.藏干 = _default_canggan_for(bazi)
        return bazi

    raise TypeError(f"adapt_bazi: 不识别的输入类型 {type(obj).__name__}")


def _to_local_ganzhi(gz: object) -> GanZhi:
    if isinstance(gz, GanZhi):
        return gz
    # duck-type: gan, zhi attr
    gan = getattr(gz, "gan", None)
    zhi = getattr(gz, "zhi", None)
    if gan is not None and zhi is not None:
        return GanZhi(gan=gan, zhi=zhi)
    if isinstance(gz, str) and len(gz) == 2:
        return GanZhi.parse(gz)
    raise TypeError(f"无法转为 GanZhi: {gz!r}")


def _default_canggan_for(bazi: Bazi) -> dict[str, list[Canggan]]:
    """根据 4 个地支的标准藏干表，填充 Bazi.藏干。"""
    out: dict[str, list[Canggan]] = {}
    for key, zhi in (
        ("年支", bazi.年柱.zhi),
        ("月支", bazi.月柱.zhi),
        ("日支", bazi.日柱.zhi),
        ("时支", bazi.时柱.zhi),
    ):
        items = ZHI_CANGGAN_TABLE.get(zhi, [])
        out[key] = [Canggan(gan=g, type=t, li_liang=l) for (g, t, l) in items]
    return out


def adapt_dayun(obj: object) -> Dayun:
    """把 preflight.Dayun / 任意形态 → 本地 Dayun。"""
    if isinstance(obj, Dayun):
        return obj
    # duck-type
    qiyun_sui = getattr(obj, "起运岁", None)
    qiyun_year = getattr(obj, "起运年", None)
    shun_ni = getattr(obj, "顺逆", None)
    paibu = getattr(obj, "排布", None)
    if paibu is None:
        raise TypeError("adapt_dayun: 输入缺 排布 字段")

    steps: list[DayunStep] = []
    for s in paibu:
        # preflight.DayunStep 含 起讫: "YYYY-YYYY" 字符串
        gz = _to_local_ganzhi(getattr(s, "干支"))
        qiqi = getattr(s, "起讫", None)
        if isinstance(qiqi, str) and "-" in qiqi:
            y1s, y2s = qiqi.split("-", 1)
            year_pair = (int(y1s), int(y2s))
        elif isinstance(qiqi, tuple):
            year_pair = (int(qiqi[0]), int(qiqi[1]))
        else:
            # 自己构造
            year_pair = (
                int(qiyun_year or 0) + int(getattr(s, "起岁", 0)),
                int(qiyun_year or 0) + int(getattr(s, "止岁", 0)) + 1,
            )
        steps.append(DayunStep(
            序号=int(getattr(s, "序号")),
            干支=gz,
            起岁=int(getattr(s, "起岁")),
            止岁=int(getattr(s, "止岁")),
            起讫年=year_pair,
        ))

    return Dayun(
        起运岁=float(qiyun_sui or 0),
        起运年=int(qiyun_year or 0),
        顺逆=str(shun_ni or "顺"),
        排布=steps,
    )


def adapt_parsed(obj: object) -> ParsedInput:
    """把 preflight.ParsedInput / dict → 本地 ParsedInput。"""
    if isinstance(obj, ParsedInput):
        return obj

    bazi = adapt_bazi(getattr(obj, "bazi"))
    # 把 preflight.canggan 合并进 bazi.藏干（如果有）
    pf_canggan = getattr(obj, "canggan", None)
    if pf_canggan and isinstance(pf_canggan, dict):
        merged: dict[str, list[Canggan]] = {}
        for key, items in pf_canggan.items():
            cangs: list[Canggan] = []
            for it in items:
                gan = getattr(it, "gan", None) or (it.get("gan") if isinstance(it, dict) else None)
                typ = getattr(it, "type", None) or (it.get("type") if isinstance(it, dict) else None)
                li = getattr(it, "li_liang", None)
                if li is None and isinstance(it, dict):
                    li = it.get("li_liang") or it.get("力量")
                cangs.append(Canggan(gan=gan, type=typ, li_liang=float(li or 0.0)))
            merged[key] = cangs
        if merged:
            bazi.藏干 = merged

    dayun = adapt_dayun(getattr(obj, "dayun"))

    kfs_in = getattr(obj, "known_facts", []) or []
    kfs: list[KnownFact] = []
    for kf in kfs_in:
        if isinstance(kf, KnownFact):
            kfs.append(kf)
        else:
            kfs.append(KnownFact(
                type=getattr(kf, "type", "其他"),
                year=getattr(kf, "year", None),
                event=getattr(kf, "event", None),
                content=getattr(kf, "content", None),
            ))

    return ParsedInput(
        case_id=str(getattr(obj, "case_id", "")),
        bazi=bazi,
        dayun=dayun,
        birth=getattr(obj, "birth", {}) or {},
        shensha=getattr(obj, "shensha", {}) or {},
        twelve_changsheng=getattr(obj, "twelve_changsheng", {}) or {},
        known_facts=kfs,
        questions=list(getattr(obj, "questions", []) or []),
        case_meta=getattr(obj, "case_meta", {}) or {},
        fingerprint=str(getattr(obj, "fingerprint", "")),
        schema_version=str(getattr(obj, "schema_version", "1.2.0")),
    )


# ============================================================
# 六、smoke test
# ============================================================

def _smoke() -> None:
    """跑通几个边界用例。"""
    gz = GanZhi.parse("壬子")
    assert gz.gan == "壬" and gz.zhi == "子"
    # frozen 检查
    try:
        gz.gan = "甲"  # type: ignore[misc]
        raise AssertionError("frozen 失败：本应 raise")
    except Exception:
        pass

    bazi = Bazi(
        年柱=GanZhi("庚", "申"),
        月柱=GanZhi("戊", "寅"),
        日柱=GanZhi("壬", "子"),
        时柱=GanZhi("辛", "丑"),
    )
    bazi.藏干 = _default_canggan_for(bazi)
    assert bazi.day_master == "壬"
    assert bazi.月令 == "寅"
    print(f"[OK] Bazi 构造: {bazi.年柱}{bazi.月柱}{bazi.日柱}{bazi.时柱}")
    print(f"     寅藏干 = {[(c.gan, c.type, c.li_liang) for c in bazi.藏干['月支']]}")

    # 长生表抽查：壬在子=帝旺
    assert CHANGSHENG_TABLE["壬"]["子"] == "帝旺"
    # 壬在申=长生
    assert CHANGSHENG_TABLE["壬"]["申"] == "长生"
    # 乙木在午=长生（阴干逆数）
    assert CHANGSHENG_TABLE["乙"]["午"] == "长生"
    print("[OK] 长生表抽查 3 条全过")


if __name__ == "__main__":  # pragma: no cover
    _smoke()

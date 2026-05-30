"""tools/preflight.py · 兜底护栏 #1 · v1.2 输入 schema 校验

负责把 cases/C-XXX/input.md 解析成 ParsedInput 对象。
任何一步校验不通过 = raise PreflightError，流水线不启动。

实现 01-input-schema.md § 四 的 11 步校验清单。
不实现排盘算法（决策 A：靠问真 APP）。

依赖：标准库 + PyYAML
版本：v1.2.0
作者：Track-E
"""
from __future__ import annotations

import dataclasses
import hashlib
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable, Literal, Optional, Union

try:
    import yaml  # type: ignore
except ImportError as e:  # pragma: no cover
    raise SystemExit(
        "preflight.py 需要 PyYAML，请运行: pip install pyyaml"
    ) from e


# ============================================================
# 一、常量表（干支 / 60 甲子 / 长生 / known_facts 类型）
# ============================================================

GAN_LIST: tuple[str, ...] = ("甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸")
ZHI_LIST: tuple[str, ...] = (
    "子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥",
)

GAN_YANGYIN: dict[str, str] = {
    "甲": "阳", "丙": "阳", "戊": "阳", "庚": "阳", "壬": "阳",
    "乙": "阴", "丁": "阴", "己": "阴", "辛": "阴", "癸": "阴",
}
ZHI_YANGYIN: dict[str, str] = {
    "子": "阳", "寅": "阳", "辰": "阳", "午": "阳", "申": "阳", "戌": "阳",
    "丑": "阴", "卯": "阴", "巳": "阴", "未": "阴", "酉": "阴", "亥": "阴",
}

CANGGAN_TYPE_LIST: tuple[str, ...] = ("主气", "中气", "余气")

CHANGSHENG_LIST: tuple[str, ...] = (
    "长生", "沐浴", "冠带", "临官", "帝旺",
    "衰", "病", "死", "墓", "绝", "胎", "养",
)

KNOWN_FACT_TYPES: tuple[str, ...] = (
    "婚姻", "学历", "职业", "财运", "六亲", "健康",
    "子女", "灾厄", "牢狱", "出国", "其他",
)

STRATEGY_LIST: tuple[str, ...] = ("A", "B", "C")
GENDER_LIST: tuple[str, ...] = ("M", "F")
MINGSHI_BY_GENDER: dict[str, str] = {"M": "乾", "F": "坤"}

CASE_ID_PATTERN: re.Pattern[str] = re.compile(
    r"^C-\d{4}-\d{3}-[乾坤]-([甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]){4}$"
)


# ============================================================
# 二、错误类型
# ============================================================

@dataclass
class PreflightError(Exception):
    """preflight 校验失败异常。

    step      : 失败步骤（1-11 之一，对应 § 四清单序号）
    field_path: 失败字段（点分路径，例 "四柱.年柱"）
    detail    : 人类可读详情
    """
    step: int
    field_path: str
    detail: str

    def __str__(self) -> str:  # pragma: no cover
        return f"[FAIL #{self.step}] {self.field_path}: {self.detail}"


# ============================================================
# 三、ParsedInput 数据结构（精简自 03-findings-schema § 四）
# ============================================================

@dataclass
class GanZhi:
    """干支柱组合"""
    gan: str
    zhi: str

    def __str__(self) -> str:
        return f"{self.gan}{self.zhi}"

    @classmethod
    def parse(cls, s: str) -> "GanZhi":
        if not isinstance(s, str) or len(s) != 2:
            raise ValueError(f"干支必须 2 字: {s!r}")
        gan, zhi = s[0], s[1]
        if gan not in GAN_LIST:
            raise ValueError(f"非法天干: {gan!r}")
        if zhi not in ZHI_LIST:
            raise ValueError(f"非法地支: {zhi!r}")
        if GAN_YANGYIN[gan] != ZHI_YANGYIN[zhi]:
            # 60 甲子要求阴阳相同：阳干+阳支 / 阴干+阴支
            raise ValueError(f"非 60 甲子（阴阳不配）: {s!r}")
        return cls(gan=gan, zhi=zhi)


@dataclass
class Canggan:
    gan: str
    type: str          # 主气 / 中气 / 余气
    li_liang: float    # 力量 0.0-1.0


@dataclass
class DayunStep:
    序号: int
    干支: GanZhi
    起讫: str           # "YYYY-YYYY"
    起岁: int
    止岁: int


@dataclass
class Dayun:
    起运岁: float
    起运年: int
    顺逆: str            # 顺 / 逆
    排布: list[DayunStep]


@dataclass
class KnownFact:
    type: str           # KNOWN_FACT_TYPES 之一
    year: Optional[int] = None
    event: Optional[str] = None       # 时间型用
    content: Optional[str] = None     # 状态型用


@dataclass
class ParsedInput:
    """preflight 解析后的内部结构（已通过 11 步校验）。"""
    schema_version: str
    case_id: str
    case_meta: dict[str, Any]
    birth: dict[str, Any]
    bazi: dict[str, GanZhi]                    # {年柱, 月柱, 日柱, 时柱}
    canggan: dict[str, list[Canggan]]          # {年支, 月支, 日支, 时支}
    dayun: Dayun
    shensha: dict[str, list[str]]
    twelve_changsheng: dict[str, str]
    known_facts: list[KnownFact]
    questions: list[str]
    fingerprint: str                           # MD5(性别|公历)[:12]
    preflight_warnings: list[str] = field(default_factory=list)


# ============================================================
# 四、YAML 块抽取
# ============================================================

_YAML_BLOCK_RE = re.compile(
    r"```ya?ml\s*\n(?P<body>.*?)\n```",
    re.DOTALL | re.IGNORECASE,
)


def extract_yaml_blocks(text: str) -> list[dict[str, Any]]:
    """从 input.md 中抽取所有 ```yaml``` 代码块并合并解析。

    不合并成单 dict（顶层键可能跨块），返回每块各自解析的结果列表。
    """
    blocks: list[dict[str, Any]] = []
    for m in _YAML_BLOCK_RE.finditer(text):
        body = m.group("body")
        try:
            data = yaml.safe_load(body)
        except yaml.YAMLError as e:
            raise PreflightError(
                step=2,
                field_path="<yaml-block>",
                detail=f"YAML 解析失败: {e}",
            ) from e
        if data is None:
            continue
        if not isinstance(data, dict):
            raise PreflightError(
                step=2,
                field_path="<yaml-block>",
                detail=f"YAML 顶层必须是 mapping，实为 {type(data).__name__}",
            )
        blocks.append(data)
    return blocks


def merge_blocks(blocks: list[dict[str, Any]]) -> dict[str, Any]:
    """将多个 yaml block 合并为单一 dict。

    同名顶层键 → 后者覆盖前者，并写 warning。
    """
    merged: dict[str, Any] = {}
    duplicates: list[str] = []
    for blk in blocks:
        for k, v in blk.items():
            if k in merged:
                duplicates.append(k)
            merged[k] = v
    merged["__duplicate_keys__"] = duplicates
    return merged


# ============================================================
# 五、11 步校验（按 01-input-schema § 四 顺序）
# ============================================================

def _require(cond: bool, step: int, field_path: str, detail: str) -> None:
    if not cond:
        raise PreflightError(step=step, field_path=field_path, detail=detail)


# ---- step 1：schema_version ---------------------------------

def _check_schema_version(merged: dict[str, Any]) -> str:
    v = merged.get("schema_version")
    _require(
        v is not None,
        1, "schema_version", "缺失，必须为 '1.2.0'"
    )
    _require(
        v == "1.2.0",
        1, "schema_version", f"必须为 '1.2.0'，实为 {v!r}"
    )
    assert isinstance(v, str)
    return v


# ---- step 3：必填字段全在 -----------------------------------

REQUIRED_TOP_KEYS: tuple[str, ...] = (
    "schema_version", "case_meta", "birth",
    "四柱", "藏干", "大运",
    "神煞", "十二长生", "known_facts",
)


def _check_required_keys(merged: dict[str, Any]) -> None:
    for k in REQUIRED_TOP_KEYS:
        _require(k in merged, 3, k, "顶层必填字段缺失")
    case_meta = merged["case_meta"]
    _require(
        isinstance(case_meta, dict),
        3, "case_meta", "必须为 mapping"
    )
    for sub in ("case_id", "立案日期", "命主代号", "策略"):
        _require(
            sub in case_meta,
            3, f"case_meta.{sub}", "必填子字段缺失"
        )

    birth = merged["birth"]
    _require(isinstance(birth, dict), 3, "birth", "必须为 mapping")
    for sub in ("性别", "公历", "出生地", "真太阳时校正"):
        _require(
            sub in birth,
            3, f"birth.{sub}", "必填子字段缺失"
        )


# ---- step 4：case_id 格式 + 干支合法性 -----------------------

def _check_case_id(case_meta: dict[str, Any]) -> str:
    cid = case_meta["case_id"]
    _require(
        isinstance(cid, str) and CASE_ID_PATTERN.match(cid) is not None,
        4, "case_meta.case_id",
        f"格式必须为 C-YYYY-NNN-{{乾/坤}}-{{8 字干支}}，实为 {cid!r}"
    )
    # 干支八字段拆四柱再 60 甲子校验
    suffix = cid.split("-")[-1]
    pillars = [suffix[i:i + 2] for i in range(0, 8, 2)]
    for idx, pil in enumerate(pillars, start=1):
        try:
            GanZhi.parse(pil)
        except ValueError as e:
            raise PreflightError(
                step=4, field_path=f"case_meta.case_id 第{idx}柱",
                detail=f"{pil}: {e}"
            )
    # 策略合法
    strategy = case_meta["策略"]
    _require(
        strategy in STRATEGY_LIST,
        4, "case_meta.策略",
        f"必须为 {STRATEGY_LIST}，实为 {strategy!r}"
    )
    return cid


# ---- step 5：指纹防重 ---------------------------------------

def compute_fingerprint(birth: dict[str, Any]) -> str:
    """fingerprint = MD5(性别 | 公历精确到分钟)[:12]"""
    gender = str(birth["性别"]).strip().upper()
    gongli = birth["公历"]
    if isinstance(gongli, datetime):
        gongli_str = gongli.strftime("%Y-%m-%d %H:%M")
    elif isinstance(gongli, date):
        gongli_str = gongli.strftime("%Y-%m-%d 00:00")
    else:
        gongli_str = str(gongli)
    raw = f"{gender}|{gongli_str}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()[:12]


def _check_fingerprint(
    birth: dict[str, Any],
    cases_index_path: Optional[Path],
    self_case_id: str,
) -> str:
    fp = compute_fingerprint(birth)
    if cases_index_path is None or not cases_index_path.exists():
        # 索引不存在 → 跳过（首案 / 测试场景）
        return fp
    text = cases_index_path.read_text(encoding="utf-8")
    # 兼容 cases-index.md 第二节的 "<fp> · C-YYYY-... " 格式
    pat = re.compile(rf"^{re.escape(fp)}\s*·\s*(C-\d{{4}}-\d{{3}}\S*)", re.M)
    found = pat.findall(text)
    other = [c for c in found if c != self_case_id]
    _require(
        not other,
        5, "fingerprint",
        f"指纹 {fp} 已存在于 {other}，疑似重复立案"
    )
    return fp


# ---- step 6：四柱 ↔ 公历 (软校验：仅基础合法) -----------------

def _check_sizhu(merged: dict[str, Any]) -> dict[str, GanZhi]:
    sizhu_raw = merged["四柱"]
    _require(isinstance(sizhu_raw, dict), 6, "四柱", "必须为 mapping")
    pillars: dict[str, GanZhi] = {}
    for key in ("年柱", "月柱", "日柱", "时柱"):
        _require(key in sizhu_raw, 6, f"四柱.{key}", "必填字段缺失")
        try:
            pillars[key] = GanZhi.parse(str(sizhu_raw[key]))
        except ValueError as e:
            raise PreflightError(
                step=6, field_path=f"四柱.{key}",
                detail=str(e),
            )
    # case_id 中的 8 字干支必须与四柱完全一致
    case_id = merged["case_meta"]["case_id"]
    suffix = case_id.split("-")[-1]
    expected = (
        f"{pillars['年柱']}{pillars['月柱']}"
        f"{pillars['日柱']}{pillars['时柱']}"
    )
    _require(
        suffix == expected,
        6, "case_meta.case_id ↔ 四柱",
        f"case_id 后缀 {suffix} 与四柱 {expected} 不一致"
    )
    return pillars


# ---- step 7：大运一致性 -------------------------------------

def _check_dayun(
    merged: dict[str, Any], birth_year: int
) -> Dayun:
    dy_raw = merged["大运"]
    _require(isinstance(dy_raw, dict), 7, "大运", "必须为 mapping")
    qiyun_sui = dy_raw.get("起运岁")
    qiyun_year = dy_raw.get("起运年")
    shun_ni = dy_raw.get("顺逆")
    paibu = dy_raw.get("排布")
    _require(
        isinstance(qiyun_sui, (int, float)) and 0 < qiyun_sui < 12,
        7, "大运.起运岁",
        f"必须 0<x<12，实为 {qiyun_sui!r}"
    )
    _require(
        isinstance(qiyun_year, int),
        7, "大运.起运年",
        f"必须 int，实为 {qiyun_year!r}"
    )
    _require(
        qiyun_year == birth_year + int(qiyun_sui),
        7, "大运.起运年",
        f"必须 = birth.年({birth_year}) + floor(起运岁) "
        f"= {birth_year + int(qiyun_sui)}，实为 {qiyun_year}"
    )
    _require(
        shun_ni in ("顺", "逆"),
        7, "大运.顺逆", f"必须为 顺/逆，实为 {shun_ni!r}"
    )
    _require(
        isinstance(paibu, list) and len(paibu) >= 8,
        7, "大运.排布", f"必须 list 且长度 ≥ 8，实为 {paibu!r}"
    )

    steps: list[DayunStep] = []
    prev_zhi_qisui: Optional[int] = None
    for idx, item in enumerate(paibu):
        if not isinstance(item, dict):
            raise PreflightError(
                step=7, field_path=f"大运.排布[{idx}]",
                detail=f"每步必须 mapping，实为 {item!r}"
            )
        for k in ("序号", "干支", "起讫", "起岁", "止岁"):
            _require(
                k in item,
                7, f"大运.排布[{idx}].{k}", "字段缺失"
            )
        # 序号连续
        _require(
            item["序号"] == idx + 1,
            7, f"大运.排布[{idx}].序号",
            f"必须 = {idx + 1}，实为 {item['序号']}"
        )
        try:
            gz = GanZhi.parse(str(item["干支"]))
        except ValueError as e:
            raise PreflightError(
                step=7, field_path=f"大运.排布[{idx}].干支",
                detail=str(e)
            )
        # 起讫年差 = 10
        m = re.match(r"^(\d{4})-(\d{4})$", str(item["起讫"]))
        _require(
            m is not None,
            7, f"大运.排布[{idx}].起讫",
            f"必须 'YYYY-YYYY'，实为 {item['起讫']!r}"
        )
        assert m is not None
        y1, y2 = int(m.group(1)), int(m.group(2))
        _require(
            y2 - y1 == 10,
            7, f"大运.排布[{idx}].起讫",
            f"起讫年差必须 = 10，实为 {y2 - y1}"
        )
        qisui = int(item["起岁"])
        zhisui = int(item["止岁"])
        _require(
            zhisui - qisui == 9,
            7, f"大运.排布[{idx}].起岁/止岁",
            f"止岁-起岁 必须 = 9（覆盖 10 年），实为 {zhisui - qisui}"
        )
        if prev_zhi_qisui is not None:
            _require(
                qisui == prev_zhi_qisui + 1,
                7, f"大运.排布[{idx}].起岁",
                f"必须 = 上一步止岁+1 = {prev_zhi_qisui + 1}，实为 {qisui}"
            )
        prev_zhi_qisui = zhisui
        steps.append(DayunStep(
            序号=item["序号"],
            干支=gz,
            起讫=item["起讫"],
            起岁=qisui,
            止岁=zhisui,
        ))

    # 干支顺/逆推（基于第 1 步与第 2 步的 60 甲子序号差）
    if len(steps) >= 2:
        idx1 = _jiazi_index(steps[0].干支)
        idx2 = _jiazi_index(steps[1].干支)
        diff = (idx2 - idx1) % 60
        if shun_ni == "顺":
            expected = 1
        else:
            expected = 59  # -1 mod 60
        _require(
            diff == expected,
            7, "大运.排布[0..1].干支",
            f"顺/逆推方向不符（diff={diff}, 期望 {expected}）"
        )

    return Dayun(
        起运岁=float(qiyun_sui),
        起运年=int(qiyun_year),
        顺逆=str(shun_ni),
        排布=steps,
    )


def _jiazi_index(gz: GanZhi) -> int:
    """60 甲子序号 0-59，'甲子'=0, '癸亥'=59"""
    g_idx = GAN_LIST.index(gz.gan)
    z_idx = ZHI_LIST.index(gz.zhi)
    # 60 甲子的位置：序号 n 满足 n % 10 == g_idx 且 n % 12 == z_idx
    for n in range(60):
        if n % 10 == g_idx and n % 12 == z_idx:
            return n
    raise ValueError(f"非 60 甲子: {gz}")


# ---- step 8：藏干合法性 -------------------------------------

def _check_canggan(merged: dict[str, Any]) -> dict[str, list[Canggan]]:
    cg_raw = merged["藏干"]
    _require(isinstance(cg_raw, dict), 8, "藏干", "必须为 mapping")
    out: dict[str, list[Canggan]] = {}
    for key in ("年支", "月支", "日支", "时支"):
        _require(key in cg_raw, 8, f"藏干.{key}", "必填字段缺失")
        items = cg_raw[key]
        _require(
            isinstance(items, list) and len(items) >= 1,
            8, f"藏干.{key}", "必须 list 且至少含主气"
        )
        cangs: list[Canggan] = []
        types_seen: set[str] = set()
        for jdx, it in enumerate(items):
            _require(
                isinstance(it, dict),
                8, f"藏干.{key}[{jdx}]", f"每项必须 mapping"
            )
            gan = it.get("干")
            typ = it.get("类型")
            li = it.get("力量")
            _require(
                gan in GAN_LIST,
                8, f"藏干.{key}[{jdx}].干",
                f"非法天干 {gan!r}"
            )
            _require(
                typ in CANGGAN_TYPE_LIST,
                8, f"藏干.{key}[{jdx}].类型",
                f"必须 {CANGGAN_TYPE_LIST}，实为 {typ!r}"
            )
            _require(
                isinstance(li, (int, float)) and 0 <= float(li) <= 1.0,
                8, f"藏干.{key}[{jdx}].力量",
                f"必须 0-1，实为 {li!r}"
            )
            types_seen.add(str(typ))
            cangs.append(Canggan(gan=str(gan), type=str(typ), li_liang=float(li)))
        _require(
            "主气" in types_seen,
            8, f"藏干.{key}", "必须含主气"
        )
        out[key] = cangs
    return out


# ---- step 9：十二长生 ---------------------------------------

def _check_changsheng(
    merged: dict[str, Any], pillars: dict[str, GanZhi]
) -> dict[str, str]:
    cs = merged["十二长生"]
    _require(isinstance(cs, dict), 9, "十二长生", "必须为 mapping")
    rigan = cs.get("日干")
    _require(
        rigan == pillars["日柱"].gan,
        9, "十二长生.日干",
        f"必须 = 四柱.日柱[0]={pillars['日柱'].gan}，实为 {rigan!r}"
    )
    out: dict[str, str] = {"日干": str(rigan)}
    for key in ("年支", "月支", "日支", "时支"):
        _require(key in cs, 9, f"十二长生.{key}", "必填字段缺失")
        st = cs[key]
        _require(
            st in CHANGSHENG_LIST,
            9, f"十二长生.{key}",
            f"必须为 {CHANGSHENG_LIST}，实为 {st!r}"
        )
        out[key] = str(st)
    return out


# ---- step 10：known_facts 类型 ------------------------------

def _check_known_facts(merged: dict[str, Any]) -> list[KnownFact]:
    kfs = merged["known_facts"]
    _require(
        isinstance(kfs, list),
        10, "known_facts", "必须为 list（可空）"
    )
    out: list[KnownFact] = []
    for i, kf in enumerate(kfs):
        _require(
            isinstance(kf, dict),
            10, f"known_facts[{i}]", "每项必须 mapping"
        )
        typ = kf.get("类型")
        _require(
            typ in KNOWN_FACT_TYPES,
            10, f"known_facts[{i}].类型",
            f"必须 {KNOWN_FACT_TYPES}，实为 {typ!r}"
        )
        year = kf.get("年份")
        if year is not None:
            _require(
                isinstance(year, int) and 1900 <= year <= 2100,
                10, f"known_facts[{i}].年份",
                f"必须 1900-2100 整数，实为 {year!r}"
            )
        out.append(KnownFact(
            type=str(typ),
            year=year,
            event=kf.get("事件"),
            content=kf.get("内容"),
        ))
    return out


# ---- step 11：目录名 = case_id ------------------------------

def _check_dir_matches(
    input_md_path: Path, case_id: str
) -> None:
    parent_name = input_md_path.parent.name
    _require(
        parent_name == case_id,
        11, "目录名 ↔ case_id",
        f"目录 {parent_name!r} 与 case_id {case_id!r} 不一致"
    )


# ---- birth.公历 解析 ----------------------------------------

def _parse_birth_year(birth: dict[str, Any]) -> int:
    gongli = birth["公历"]
    if isinstance(gongli, datetime):
        return gongli.year
    if isinstance(gongli, date):
        return gongli.year
    s = str(gongli)
    m = re.match(r"^(\d{4})-\d{2}-\d{2}", s)
    if not m:
        raise PreflightError(
            step=3, field_path="birth.公历",
            detail=f"必须 'YYYY-MM-DD HH:MM' 格式，实为 {s!r}"
        )
    return int(m.group(1))


def _check_gender_strategy(birth: dict[str, Any]) -> None:
    g = birth.get("性别")
    _require(
        g in GENDER_LIST,
        3, "birth.性别", f"必须 M/F，实为 {g!r}"
    )


def _check_case_id_gender(case_id: str, birth: dict[str, Any]) -> None:
    gender = birth.get("性别")
    expected = MINGSHI_BY_GENDER[str(gender)]
    actual = case_id.split("-")[-2]
    _require(
        actual == expected,
        4, "case_meta.case_id ↔ birth.性别",
        f"case_id 命式段 {actual!r} 与 birth.性别 {gender!r}（应为 {expected!r}）不一致"
    )


# ============================================================
# 六、主接口 parse()
# ============================================================

def parse(
    input_md_path: Path,
    cases_index_path: Optional[Path] = None,
) -> ParsedInput:
    """主入口：解析 + 11 步校验 input.md → ParsedInput。

    :param input_md_path: cases/C-XXX/input.md 的路径
    :param cases_index_path: cases/cases-index.md（用于指纹防重）
        若为 None，跳过 step 5 的索引比对。
    :raises PreflightError: 任何一步校验失败
    """
    input_md_path = Path(input_md_path)
    if not input_md_path.exists():
        raise PreflightError(
            step=0, field_path="input.md", detail=f"文件不存在: {input_md_path}"
        )

    text = input_md_path.read_text(encoding="utf-8")
    blocks = extract_yaml_blocks(text)
    if not blocks:
        raise PreflightError(
            step=2, field_path="<yaml-block>",
            detail="input.md 中未发现任何 ```yaml``` 代码块"
        )
    merged = merge_blocks(blocks)
    warnings: list[str] = []
    if merged.get("__duplicate_keys__"):
        warnings.append(
            f"yaml block 中重复顶层键: {merged['__duplicate_keys__']}（后者覆盖）"
        )

    # step 1
    schema_v = _check_schema_version(merged)
    # step 3 (放前面，确保后续访问安全)
    _check_required_keys(merged)
    _check_gender_strategy(merged["birth"])
    # step 4
    case_id = _check_case_id(merged["case_meta"])
    _check_case_id_gender(case_id, merged["birth"])
    # step 11（先做目录校验，避免后面解析浪费时间）
    _check_dir_matches(input_md_path, case_id)
    # step 5
    fp = _check_fingerprint(
        merged["birth"], cases_index_path, case_id,
    )
    # step 6
    pillars = _check_sizhu(merged)
    # step 7
    birth_year = _parse_birth_year(merged["birth"])
    # 真太阳时校正 warning
    tts = merged["birth"].get("真太阳时校正")
    if tts is False:
        warnings.append(
            "birth.真太阳时校正=false，请确认四柱已基于真太阳时手工调整"
        )
    dayun = _check_dayun(merged, birth_year)
    # step 8
    canggan = _check_canggan(merged)
    # step 9
    cs = _check_changsheng(merged, pillars)
    # step 10
    kfs = _check_known_facts(merged)

    questions = merged.get("提问") or []
    if not isinstance(questions, list):
        raise PreflightError(
            step=3, field_path="提问",
            detail=f"必须 list，实为 {type(questions).__name__}"
        )

    return ParsedInput(
        schema_version=schema_v,
        case_id=case_id,
        case_meta=merged["case_meta"],
        birth=merged["birth"],
        bazi=pillars,
        canggan=canggan,
        dayun=dayun,
        shensha=merged["神煞"] or {},
        twelve_changsheng=cs,
        known_facts=kfs,
        questions=[str(q) for q in questions],
        fingerprint=fp,
        preflight_warnings=warnings,
    )


# ============================================================
# 七、CLI / smoke test
# ============================================================

_SMOKE_INPUT_MIN = """\
# C-2099-001-乾-甲子甲戌癸卯壬戌 · smoke

```yaml
schema_version: 1.2.0
case_meta:
  case_id: C-2099-001-乾-甲子甲戌癸卯壬戌
  立案日期: 2099-01-01
  命主代号: 测试命主
  策略: B
birth:
  性别: M
  公历: "2024-01-01 00:00"
  出生地: 北京市
  真太阳时校正: true

四柱:
  年柱: 甲子
  月柱: 甲戌
  日柱: 癸卯
  时柱: 壬戌
```

```yaml
藏干:
  年支:
    - {干: 癸, 类型: 主气, 力量: 1.0}
  月支:
    - {干: 戊, 类型: 主气, 力量: 1.0}
    - {干: 辛, 类型: 中气, 力量: 0.3}
    - {干: 丁, 类型: 余气, 力量: 0.2}
  日支:
    - {干: 乙, 类型: 主气, 力量: 1.0}
  时支:
    - {干: 戊, 类型: 主气, 力量: 1.0}
    - {干: 辛, 类型: 中气, 力量: 0.3}
    - {干: 丁, 类型: 余气, 力量: 0.2}

大运:
  起运岁: 5
  起运年: 2029
  顺逆: 顺
  排布:
    - {序号: 1, 干支: 乙亥, 起讫: "2029-2039", 起岁: 5,  止岁: 14}
    - {序号: 2, 干支: 丙子, 起讫: "2039-2049", 起岁: 15, 止岁: 24}
    - {序号: 3, 干支: 丁丑, 起讫: "2049-2059", 起岁: 25, 止岁: 34}
    - {序号: 4, 干支: 戊寅, 起讫: "2059-2069", 起岁: 35, 止岁: 44}
    - {序号: 5, 干支: 己卯, 起讫: "2069-2079", 起岁: 45, 止岁: 54}
    - {序号: 6, 干支: 庚辰, 起讫: "2079-2089", 起岁: 55, 止岁: 64}
    - {序号: 7, 干支: 辛巳, 起讫: "2089-2099", 起岁: 65, 止岁: 74}
    - {序号: 8, 干支: 壬午, 起讫: "2099-2109", 起岁: 75, 止岁: 84}

神煞:
  年柱: []
  月柱: []
  日柱: []
  时柱: []

十二长生:
  日干: 癸
  年支: 临官
  月支: 衰
  日支: 长生
  时支: 衰

known_facts: []

提问: []
```
"""


def _smoke() -> None:
    """模拟最小 input.md，跑通 parse()。"""
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        case_dir = Path(td) / "C-2099-001-乾-甲子甲戌癸卯壬戌"
        case_dir.mkdir()
        (case_dir / "input.md").write_text(
            _SMOKE_INPUT_MIN, encoding="utf-8"
        )
        parsed = parse(case_dir / "input.md")
        print(f"[OK] smoke: case_id={parsed.case_id} fp={parsed.fingerprint}")
        print(f"     dayun={[str(s.干支) for s in parsed.dayun.排布]}")
        print(f"     warnings={parsed.preflight_warnings}")


if __name__ == "__main__":  # pragma: no cover
    if len(sys.argv) >= 2:
        try:
            p = parse(Path(sys.argv[1]))
            print(f"[OK] preflight passed: {p.case_id}")
            for w in p.preflight_warnings:
                print(f"[WARN] {w}")
        except PreflightError as e:
            print(str(e))
            sys.exit(1)
    else:
        _smoke()

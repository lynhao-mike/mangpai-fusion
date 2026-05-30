"""tests/track_a_smoke/_fixtures.py · 5 个验收 case 的 fixture 构造器

由于现存 14 个旧案的 input.md 仍是 v1.0 Markdown 表格格式（非 v1.2 strict
YAML），preflight.parse() 暂时无法解析它们。Track-A 决定：
  - 直接从 case_id 的 8 字干支后缀构造 Bazi
  - Dayun 从 input.md 抽取的关键字段硬编码
  - 等 Track-E 把 14 个旧案 v1.2 yaml 化后，可换接 preflight.parse()

每个 fixture 含：case_id、bazi、dayun(8 步占位)。
"""
from __future__ import annotations

import re
from typing import Optional

from engine.predicates.types import (
    Bazi,
    Dayun,
    DayunStep,
    GanZhi,
    ParsedInput,
    _default_canggan_for,
)


def _parse_bazi_from_case_id(case_id: str) -> Bazi:
    """从 case_id 中提取 8 字干支后缀，构造 Bazi。

    case_id 形如 ``C-2026-001-乾-庚申戊寅壬子辛丑``。
    """
    m = re.match(
        r"^C-\d{4}-\d{3}-[乾坤]-([甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]){4}$",
        case_id,
    )
    if not m:
        raise ValueError(f"非法 case_id: {case_id!r}")
    suffix = case_id.split("-")[-1]
    pillars = [suffix[i: i + 2] for i in range(0, 8, 2)]
    bazi = Bazi(
        年柱=GanZhi.parse(pillars[0]),
        月柱=GanZhi.parse(pillars[1]),
        日柱=GanZhi.parse(pillars[2]),
        时柱=GanZhi.parse(pillars[3]),
    )
    bazi.藏干 = _default_canggan_for(bazi)
    return bazi


def _build_dayun(
    qiyun_sui: float,
    birth_year: int,
    shun_ni: str,
    raw_steps: list[tuple[int, str]],
) -> Dayun:
    """构造 Dayun。raw_steps = [(起岁, 干支字符串), ...]"""
    paibu: list[DayunStep] = []
    qiyun_year = birth_year + int(qiyun_sui)
    for idx, (qisui, gz_str) in enumerate(raw_steps, start=1):
        zhisui = qisui + 9
        起讫年 = (birth_year + qisui, birth_year + qisui + 10)
        paibu.append(DayunStep(
            序号=idx,
            干支=GanZhi.parse(gz_str),
            起岁=qisui,
            止岁=zhisui,
            起讫年=起讫年,
        ))
    return Dayun(
        起运岁=qiyun_sui,
        起运年=qiyun_year,
        顺逆=shun_ni,  # type: ignore[arg-type]
        排布=paibu,
    )


# ============================================================
# 5 个 case fixture
# ============================================================

# fixture 来源：cases/C-XXX/input.md 中的"大运"段落
# 因为这些 input.md 仍是 v1.0 markdown 表格，需手抄；以后切到 v1.2 yaml 后
# 改用 preflight.parse() 自动加载。

_CASE_DATA = {
    "C-2026-001-乾-庚申戊寅壬子辛丑": dict(
        birth_year=1980,
        gender="M",
        qiyun_sui=8.5,
        shun_ni="顺",
        steps=[
            (8,  "己卯"),
            (18, "庚辰"),
            (28, "辛巳"),
            (38, "壬午"),
            (48, "癸未"),
            (58, "甲申"),
            (68, "乙酉"),
            (78, "丙戌"),
        ],
    ),
    "C-2026-002-坤-壬戌庚戌戊辰丙辰": dict(
        birth_year=1982,
        gender="F",
        qiyun_sui=1.1,
        shun_ni="逆",
        steps=[
            (2,  "己酉"),
            (12, "戊申"),
            (22, "丁未"),
            (32, "丙午"),
            (42, "乙巳"),
            (52, "甲辰"),
            (62, "癸卯"),
            (72, "壬寅"),
        ],
    ),
    "C-2026-014-乾-丙戌庚子乙亥辛巳": dict(
        birth_year=2006,
        gender="M",
        qiyun_sui=8.2,
        shun_ni="顺",
        steps=[
            (15, "辛丑"),
            (20, "壬寅"),
            (30, "癸卯"),
            (40, "甲辰"),
            (50, "乙巳"),
            (60, "丙午"),
            (70, "丁未"),
            (80, "戊申"),
        ],
    ),
    "C-2026-011-乾-乙丑乙酉丁丑癸卯": dict(
        birth_year=1985,
        gender="M",
        # 起运 9 岁阴男逆排（实际 input.md 写"9 岁起，阴男逆排"）
        qiyun_sui=9.0,
        shun_ni="逆",
        steps=[
            (10, "甲申"),
            (20, "癸未"),
            (30, "壬午"),
            (40, "辛巳"),
            (50, "庚辰"),
            (60, "己卯"),
            (70, "戊寅"),
            (80, "丁丑"),
        ],
    ),
    "C-2026-012-坤-壬戌癸丑丙申壬辰": dict(
        birth_year=1983,
        gender="F",
        qiyun_sui=1.0,
        shun_ni="顺",
        steps=[
            (1,  "壬子"),
            (11, "辛亥"),
            (21, "庚戌"),
            (31, "己酉"),
            (41, "戊申"),
            (51, "丁未"),
            (61, "丙午"),
            (71, "乙巳"),
        ],
    ),
}


def make_parsed_input(case_id: str) -> ParsedInput:
    """构造 ParsedInput（含 bazi + dayun）。"""
    if case_id not in _CASE_DATA:
        raise KeyError(f"case fixture 未注册: {case_id}")
    data = _CASE_DATA[case_id]
    bazi = _parse_bazi_from_case_id(case_id)
    dayun = _build_dayun(
        qiyun_sui=float(data["qiyun_sui"]),
        birth_year=int(data["birth_year"]),
        shun_ni=str(data["shun_ni"]),
        raw_steps=list(data["steps"]),
    )
    return ParsedInput(
        case_id=case_id,
        bazi=bazi,
        dayun=dayun,
        birth={"性别": data["gender"], "公历": f"{data['birth_year']}-01-01"},
        case_meta={"case_id": case_id, "策略": "B"},
    )

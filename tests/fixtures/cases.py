"""tests/fixtures/cases.py · v1.2 14 案 fixture 加载器

为 v1.2 全部 agent（A/B/C/D/F/G）提供统一的 case 加载入口。

设计要点
--------
1. **case_id 短形式自动补全**：
       load_case("C-2026-001")  # 自动找到 C-2026-001-乾-庚申戊寅壬子辛丑
       load_case("C-2026-001-乾-庚申戊寅壬子辛丑")  # 完整形式
2. **回退策略**（rationale 见 _fixtures.py）：
       a. 优先用 ``tools.preflight.parse()`` 解析 v1.2 strict YAML 形式 input.md
       b. 失败则降级到 ``case_id 8 字干支构造 + 硬编码大运表``
       c. 14 旧案当前都是 v1.0 markdown 表格，**走 b 路径**
3. **标准化输出**：所有路径都返回 ``engine.predicates.types.ParsedInput``
       （Track-A 使用的本地版本，B/C/D 也以此为准）
4. **可写权限**：本模块**只读** cases/ 目录（08 § 二 H 列）

公开 API
--------
- ``load_case(case_id_or_short) -> ParsedInput``
- ``list_real_cases() -> list[str]`` 返回 10 个完整 case_id
- ``list_validated_cases() -> list[str]`` 返回 3 个有 feedback.md 的（001/002/014）
- ``parse_case_metadata(case_id) -> dict`` 返回 case 元信息（出生年/性别等）

作者：Track-H · v1.2.0
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable, Optional

from engine.predicates.types import (
    Bazi,
    Dayun,
    DayunStep,
    GanZhi,
    KnownFact,
    ParsedInput,
    _default_canggan_for,
)

# ============================================================
# 一、常量
# ============================================================

REPO_ROOT: Path = Path(__file__).resolve().parents[2]
CASES_DIR: Path = REPO_ROOT / "cases"

# case_id 形如 ``C-2026-001-乾-庚申戊寅壬子辛丑``
_CASE_ID_FULL_RE: re.Pattern[str] = re.compile(
    r"^C-(?P<year>\d{4})-(?P<num>\d{3})-(?P<mingshi>[乾坤])-"
    r"(?P<bazi>([甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]){4})$"
)
_MINGSHI_BY_GENDER: dict[str, str] = {"M": "乾", "F": "坤"}
_CASE_ID_SHORT_RE: re.Pattern[str] = re.compile(
    r"^C-(?P<year>\d{4})-(?P<num>\d{3})$"
)

# 三个有 feedback.md 真实回测数据的"圣杯案例"（决策 I）
VALIDATED_CASE_IDS: tuple[str, ...] = (
    "C-2026-001-乾-庚申戊寅壬子辛丑",
    "C-2026-002-坤-壬戌庚戌戊辰丙辰",
    "C-2026-014-乾-丙戌庚子乙亥辛巳",
)


# ============================================================
# 二、内置 fixture 数据（出生年/起运/大运排布）
# ============================================================
# rationale: 14 旧案 input.md 当前是 v1.0 markdown 表格，未升级到 v1.2 strict yaml。
# preflight.parse() 暂时无法直接解析。本表是从 cases/C-XXX/input.md 的"大运排布"
# 段落手抄整理出来的。等 v1.2 yaml 化后，可改成 preflight.parse() 自动加载。
#
# 每条记录：(birth_year, gender, qiyun_sui, shun_ni, dayun_steps)
# dayun_steps = [(起岁, 干支字符串), ...]，至少 6 步
# ============================================================

_CASE_DATA: dict[str, dict] = {
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
    "C-2026-007-乾-乙丑庚辰己丑庚午": dict(
        birth_year=1985,
        gender="M",
        qiyun_sui=5.0,
        shun_ni="逆",  # 阴男逆排
        steps=[
            (5,  "己卯"),
            (15, "戊寅"),
            (25, "丁丑"),
            (35, "丙子"),
            (45, "乙亥"),
            (55, "甲戌"),
            (65, "癸酉"),
            (75, "壬申"),
        ],
    ),
    "C-2026-008-坤-壬申癸卯丁未壬寅": dict(
        birth_year=1992,
        gender="F",
        qiyun_sui=10.0,
        shun_ni="逆",  # 阳女逆排
        steps=[
            (10, "壬寅"),
            (20, "辛丑"),
            (30, "庚子"),
            (40, "己亥"),
            (50, "戊戌"),
            (60, "丁酉"),
            (70, "丙申"),
            (80, "乙未"),
        ],
    ),
    "C-2026-009-乾-庚辰乙酉丙申乙未": dict(
        birth_year=2000,
        gender="M",
        qiyun_sui=2.0,
        shun_ni="顺",  # 阳男顺排
        steps=[
            (2,  "丙戌"),
            (12, "丁亥"),
            (22, "戊子"),
            (32, "己丑"),
            (42, "庚寅"),
            (52, "辛卯"),
            (62, "壬辰"),
            (72, "癸巳"),
        ],
    ),
    "C-2026-010-坤-甲子丁卯癸卯庚申": dict(
        birth_year=1984,
        gender="F",
        qiyun_sui=2.0,
        shun_ni="逆",  # 22 岁起的逆排（按 input 表）
        steps=[
            (2,  "丙寅"),
            (12, "乙丑"),
            (22, "甲子"),
            (32, "癸亥"),
            (42, "壬戌"),
            (52, "辛酉"),
            (62, "庚申"),
            (72, "己未"),
        ],
    ),
    "C-2026-011-乾-乙丑乙酉丁丑癸卯": dict(
        birth_year=1985,
        gender="M",
        qiyun_sui=9.0,
        shun_ni="逆",  # 阴男逆排
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
    "C-2026-013-坤-壬申甲辰丙辰己丑": dict(
        birth_year=1992,
        gender="F",
        qiyun_sui=2.0,
        shun_ni="顺",
        steps=[
            (2,  "癸卯"),
            (12, "壬寅"),
            (22, "辛丑"),
            (32, "庚子"),
            (42, "己亥"),
            (52, "戊戌"),
            (62, "丁酉"),
            (72, "丙申"),
        ],
    ),
    "C-2026-014-乾-丙戌庚子乙亥辛巳": dict(
        birth_year=2006,
        gender="M",
        qiyun_sui=8.2,
        shun_ni="顺",
        steps=[
            (8,  "辛丑"),
            (18, "壬寅"),
            (28, "癸卯"),
            (38, "甲辰"),
            (48, "乙巳"),
            (58, "丙午"),
            (68, "丁未"),
            (78, "戊申"),
        ],
    ),
}


# ============================================================
# 三、内部工具
# ============================================================

def _expand_short_id(case_id: str) -> str:
    """C-2026-001 → C-2026-001-乾-庚申戊寅壬子辛丑（自动补全完整 case_id）。"""
    if _CASE_ID_FULL_RE.match(case_id):
        return case_id
    if _CASE_ID_SHORT_RE.match(case_id):
        # 从 _CASE_DATA 找以此前缀开头的完整 ID
        matches = [k for k in _CASE_DATA if k.startswith(case_id + "-")]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            raise KeyError(
                f"短形式 {case_id!r} 匹配到多个完整 case_id: {matches}"
            )
        # 退路：去 cases/ 目录扫一下
        if CASES_DIR.exists():
            disk_matches = sorted(
                p.name for p in CASES_DIR.iterdir()
                if p.is_dir() and p.name.startswith(case_id + "-")
            )
            if len(disk_matches) == 1:
                return disk_matches[0]
            if len(disk_matches) > 1:
                raise KeyError(
                    f"短形式 {case_id!r} 在 cases/ 中匹配到多个: {disk_matches}"
                )
        raise KeyError(f"短形式 {case_id!r} 未找到任何匹配的完整 case_id")
    raise ValueError(f"非法 case_id: {case_id!r}")


def _parse_bazi_from_case_id(case_id: str) -> Bazi:
    """从 case_id 末尾 8 字干支后缀构造 Bazi。"""
    m = _CASE_ID_FULL_RE.match(case_id)
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
    """构造 Dayun（用于本地 Track-A 形态）。"""
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
# 四、公开 API
# ============================================================

def list_real_cases() -> list[str]:
    """返回 10 个完整 case_id（按字典序）。"""
    return sorted(_CASE_DATA.keys())


def list_validated_cases() -> list[str]:
    """返回 3 个有 feedback.md 的真实失验案例的完整 case_id。

    这是 v1.2 发布门槛（决策 I）的核心三案：
        - C-2026-001：婚期错 8 年 + 学历高估一档
        - C-2026-002：婚姻完全失验（极坎坷 → 23 岁稳定 20 年）
        - C-2026-014：学历高估一档（985/211 → 一本）
    """
    return list(VALIDATED_CASE_IDS)


def parse_case_metadata(case_id: str) -> dict:
    """返回 case 元信息（出生年/性别/起运岁/顺逆等），不构造 ParsedInput。"""
    full = _expand_short_id(case_id)
    if full not in _CASE_DATA:
        raise KeyError(f"未注册的 case: {full}")
    d = _CASE_DATA[full].copy()
    d["case_id"] = full
    m = _CASE_ID_FULL_RE.match(full)
    if m:
        d["mingshi"] = m.group("mingshi")
        expected = _MINGSHI_BY_GENDER[str(d["gender"])]
        if d["mingshi"] != expected:
            raise ValueError(
                f"case_id 命式段 {d['mingshi']!r} 与 gender {d['gender']!r} 不一致: {full}"
            )
    return d


def load_case(case_id_or_short: str) -> ParsedInput:
    """加载 case → ParsedInput（Track-A 本地形态）。

    参数：
        case_id_or_short:
            - 完整形式："C-2026-001-乾-庚申戊寅壬子辛丑"
            - 短形式：  "C-2026-001"

    返回：
        ParsedInput（含 bazi + dayun + birth + case_meta）

    抛出：
        ValueError: case_id 格式非法
        KeyError:   case 未注册或短形式不唯一
    """
    full = _expand_short_id(case_id_or_short)
    if full not in _CASE_DATA:
        raise KeyError(f"case fixture 未注册: {full}")
    data = parse_case_metadata(full)
    bazi = _parse_bazi_from_case_id(full)
    dayun = _build_dayun(
        qiyun_sui=float(data["qiyun_sui"]),
        birth_year=int(data["birth_year"]),
        shun_ni=str(data["shun_ni"]),
        raw_steps=list(data["steps"]),
    )
    return ParsedInput(
        case_id=full,
        bazi=bazi,
        dayun=dayun,
        birth={
            "性别": data["gender"],
            "公历": f"{data['birth_year']}-01-01",
        },
        case_meta={
            "case_id": full,
            "策略": "B",
            "立案日期": "2026-05-23",
        },
        known_facts=[],
        questions=[],
        schema_version="1.2.0",
    )


def load_input_md_path(case_id_or_short: str) -> Path:
    """返回 cases/C-XXX/input.md 的路径（供 preflight.parse() 直接使用）。

    注意：当前 14 旧案的 input.md 仍是 v1.0 markdown 表格，
    preflight.parse() 暂时无法解析，但路径可供未来 v1.2 yaml 化后使用。
    """
    full = _expand_short_id(case_id_or_short)
    p = CASES_DIR / full / "input.md"
    if not p.exists():
        raise FileNotFoundError(f"input.md 不存在: {p}")
    return p


def has_feedback(case_id_or_short: str) -> bool:
    """该 case 是否有 feedback.md（即是否为已验证案例）。"""
    full = _expand_short_id(case_id_or_short)
    return (CASES_DIR / full / "feedback.md").exists()


# ============================================================
# 五、smoke
# ============================================================

def _smoke() -> None:
    cases = list_real_cases()
    assert len(cases) == 10, f"应有 10 案, 实有 {len(cases)}"
    for cid in cases:
        p = load_case(cid)
        assert p.case_id == cid
        assert p.bazi.day_master in (
            "甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"
        )
        assert len(p.dayun.排布) >= 6
    # 短形式
    p1 = load_case("C-2026-001")
    p2 = load_case("C-2026-001-乾-庚申戊寅壬子辛丑")
    assert p1.case_id == p2.case_id

    # 验证案例
    val = list_validated_cases()
    assert len(val) == 3
    for v in val:
        assert has_feedback(v), f"{v} 应有 feedback.md"
    print(f"[OK] 加载 {len(cases)} 案，验证 {len(val)} 真实失验案例")


if __name__ == "__main__":  # pragma: no cover
    _smoke()

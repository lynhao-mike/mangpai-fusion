"""tools/p1_assertion_eval_v2.py · T-189a 核心 + T-189b 增量 · A+ 裁决评分器 v2。

T-189a 核心（未重写）：

1. **三层分录**：`fixed`（克/生/化/墓）/ `dynamic`（冲/合/穿/刑）/ `ambiguous`，
   三层各自记账，fixed 不混进 dynamic，ambiguous 单列；
2. **地址/字双向归一**：端点可写 `char_a/char_b`（单个地支字）或 `addr_a/addr_b`
   （地址；经 `address_book` 或同 case 的 addr↔char 对归一），系统输出同样两种写法混用可比；
3. **dynamic 上 nj=miss**：系统对可判条给 `needs_judgment` 记 `nj`，与 `missing` 一起算 miss，
   不再当作中性弃权；
4. **ambiguous 的双引文**：期望 `needs_judgment`，且 `conflict_quotes` 恰好 2 条、
   互不相同、**逐字**出现在所引原文行内（`source_texts` 的某一行）；缺引文/非逐字记 `quote_fail`；
5. 指标：`correct/total`、`precision`、`delivered`、Wilson 95% CI、分类型小表。

T-189b 增量（只加）：

6. **B1 = T-184 整数 delta 符号**（delta>0：火党端→金水党端；delta<0 反向；
   delta==0 按柱序左端）。delta 由 case 的 `party_delta` 显式给出，或由 `four_pillars`
   按 T-184 §2.2–2.7 现算（两者都给时必须相等）。同类端无法用符号定向时 B1 弃权，
   不发明方向；B1 弃权只在四库的「未戌」同类端出现，B2 会兜住。
7. **B2 = 本气笨基线**：本气克→克方；本气生→生方；本气同五行（辰戌/丑未/丑戌/未戌四库）
   → 主位端（D/H 优先于 Y/M；同为 D/H 或同为 Y/M 取柱序靠后者）。四库题**不弃权**。
8. **margin = dynamic.correct − max(B1 correct, B2 correct)**；两条基线都按 dynamic 40 全分母计，
   弃权记不中（对系统保守）。`margin_comparable=false` 表示有 case 缺 delta/柱位，不得引用 margin。
9. **chart_id 聚类**：按盘聚合，报 macro 准确率、全对盘率、chart bootstrap 95% CI
   （固定 seed，结果可复现）。
10. **3 次方向一致率**：`--system-output` 可重复；逐 case 比较方向（定向比较端点取向，
    mutual/nj 比较类型），报 dynamic 与全层的 `consistent/cases`。
11. **T-187 回归**：`t187_regression(run, answers)` 纯函数，读两份已解析 JSON，按四柱把
    `Y.s/M.b/...` 地址归一到字，复算 edge / direction / mismatch；不宣称新结果。
12. **ambiguous 只读 loader**：`--source-loader --source-root <sources/>` 时，若答案缺
    `source_texts`，按 `source_ref` / `source_refs` 从 `sources/` 读行文本；引文口径不变
    （仍须逐字落在某一行），loader 只读、不许越出 source root。

不做：真实 anchor-60 跑分、pass/kill 判定、阈值/分母改动、engine 改动。
本模块不 import engine、不写任何文件；只有显式 `--source-loader` 才读 `sources/`。

输入（两份 JSON，UTF-8）：

answers::

    {"schema_version": "p1-adjudication-answers/v2",
     "address_book": {"D1": "巳", "H3": "亥"},          # 可选；地址→地支字
     "cases": [
       {"case_id": "FX-01", "chart_id": "CH-01", "layer": "fixed", "kind": "克",
        "mechanism": "克", "addr_a": "D1", "char_a": "巳", "addr_b": "H3",
        "char_b": "亥", "expected_direction": "actor→target", "source_ref": "..."},
       {"case_id": "AM-01", "layer": "ambiguous", "kind": "刑", "mechanism": "刑",
        "char_a": "未", "char_b": "戌", "expected_direction": "needs_judgment",
        "source_ref": "sources/duan/x.md:L12",
        "source_texts": {"sources/duan/x.md:L12": "<该行原文>"},
        "conflict_quotes": ["<正引文>", "<反引文>"]}]}

T-189b 新增可选字段（只加，不改上面任何口径）：

- `chart_id`：聚类单位；缺省等于 `case_id`（逐条当独立盘）。
- `four_pillars`：`"己卯 己巳 辛亥 甲午"`，用于按 T-184 §2 现算 B1 的 `delta`。
- `party_delta`：显式整数 delta；与 `four_pillars` 同时给时必须一致，否则退出 2。
- `pillar_a` / `pillar_b`：`Y/M/D/H`；当地址不是柱位编码（`Y.b/M.b/...`）时给 B1 平局、
  B2 四库主位端用。地址本身是 `Y.b/M.b/D.b/H.b` 时自动解析。
- `source_refs`：ambiguous 的原文行定位符数组（`source_ref` 仍可给单条）；配合
  `--source-loader` 从 `sources/` 读行文本。

system output::

    {"schema_version": "p1-adjudication-system-output/v2",
     "cases": [{"case_id": "FX-01", "a": "巳", "b": "H3",
                "direction": "actor→target", "source_ref": "..."}]}

ambiguous 的 nj 声明必须带 `conflict_quotes: [...2 条...]`；每条可以是纯字符串，
也可以是 ``{"quote": "<逐字>", "source_ref": "<行定位符>"}``（给了定位符就只认那一行）。
引文必须逐字出现在答案 `source_texts` 的某一行内，缺一条/非逐字/重复均记 `quote_fail`。

CLI：``python -m tools.p1_assertion_eval_v2 --answers A.json --system-output S.json
[--system-output S2.json ...] [--json] [--source-loader --source-root sources/]
[--t187-run META/p1-system-run-v1.json --t187-answers META/p1-fresh-40-answers-v1.json]``
退出码 0 = 评完（分数高低不影响退出码）；2 = 输入不合口径（缺文件 / schema 错 / case 对不上 / 记账不平）。
产物不含时间戳，同一输入两次运行逐字节一致（bootstrap 用固定 seed）。
"""
from __future__ import annotations

import argparse
import json
import math
import random
import re
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

SCHEMA_ANSWERS = "p1-adjudication-answers/v2"
SCHEMA_OUTPUT = "p1-adjudication-system-output/v2"
SCHEMA_SCORE = "p1-adjudication-score/v2"

DIRECTED = "actor→target"
MUTUAL = "mutual"
NEEDS_JUDGMENT = "needs_judgment"
DIRECTIONS = (DIRECTED, MUTUAL, NEEDS_JUDGMENT)

LAYERS = ("fixed", "dynamic", "ambiguous")
FIXED_KINDS = ("克", "生", "化", "墓")
DYNAMIC_KINDS = ("冲", "合", "穿", "刑")
ZHI = "子丑寅卯辰巳午未申酉戌亥"
GAN = "甲乙丙丁戊己庚辛壬癸"

PREREG_DENOMINATORS = {"fixed": 10, "dynamic": 40, "ambiguous": 10}
Z95 = 1.959963984540054

# ── T-189b 基线 / 聚类 / T-187 常量 ─────────────────────────────────────────

PILLARS = ("Y", "M", "D", "H")
PILLAR_INDEX = {name: index for index, name in enumerate(PILLARS)}
PILLAR_ADDR_RE = re.compile(r"^([YMDH])[._]([SB])$", re.IGNORECASE)

STEM_ELEMENT = {
    "甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土",
    "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水",
}
BRANCH_ELEMENT = {
    "子": "水", "丑": "土", "寅": "木", "卯": "木", "辰": "土", "巳": "火",
    "午": "火", "未": "土", "申": "金", "酉": "金", "戌": "土", "亥": "水",
}
# T-184 §2.4：木火 = F；金水 = W；燥土（戌未）= F；湿土（辰丑）= W；天干戊己 = 中立。
STEM_PARTY = {
    "甲": "F", "乙": "F", "丙": "F", "丁": "F", "戊": None,
    "己": None, "庚": "W", "辛": "W", "壬": "W", "癸": "W",
}
BRANCH_PARTY = {
    "子": "W", "丑": "W", "寅": "F", "卯": "F", "辰": "W", "巳": "F",
    "午": "F", "未": "F", "申": "W", "酉": "W", "戌": "F", "亥": "W",
}
# T-184 §2.3：只列非本气藏干；藏干土（戊己）中立。
HIDDEN_STEMS = {
    "子": (), "丑": ("癸", "辛"), "寅": ("丙", "戊"), "卯": (), "辰": ("乙", "癸"),
    "巳": ("庚", "戊"), "午": ("己",), "未": ("丁", "乙"), "申": ("壬", "戊"),
    "酉": (), "戌": ("辛", "丁"), "亥": ("甲",),
}
CONTROLS = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}
GENERATES = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}

DATA_MISSING_BASIS = ("no_delta", "delta_zero_no_pillar", "same_element_no_pillar")

MAIN_PILLARS = (2, 3)  # D、H 为主位；Y、M 为宾位。
CLUSTER_BOOTSTRAP_ITERATIONS = 2000
CLUSTER_BOOTSTRAP_SEED = 20261029

SOURCE_REF_RE = re.compile(r"^(?P<path>.+?):L(?P<line>\d+)$", re.IGNORECASE)
DEFAULT_SOURCE_ROOT = Path(__file__).resolve().parent.parent / "sources"


class InputError(ValueError):
    """输入不合口径：CLI 退出码 2，不静默兜底。"""


# ── 通用小工具 ───────────────────────────────────────────────────────────────

def _norm_addr(addr: str) -> str:
    """地址归一：去空白 + 大写（`d1` / ` D1 ` 视同 `D1`）。"""
    return addr.strip().upper()


def _is_zhi(token: str) -> bool:
    return len(token) == 1 and token in ZHI


def _is_gan(token: str) -> bool:
    return len(token) == 1 and token in GAN


def _wilson95(k: int, n: int, z: float = Z95) -> dict[str, float | None]:
    """Wilson 95% 区间；n=0 时上下界为 None（不编造区间）。"""
    if n <= 0:
        return {"lower": None, "upper": None}
    p = k / n
    denom = 1.0 + z * z / n
    centre = p + z * z / (2 * n)
    margin = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return {
        "lower": round(max(0.0, (centre - margin) / denom), 4),
        "upper": round(min(1.0, (centre + margin) / denom), 4),
    }


def _metric(num: int, den: int) -> dict[str, Any]:
    value = None if den == 0 else num / den
    return {
        "numerator": num,
        "denominator": den,
        "value": value,
        "percent": None if value is None else round(value * 100, 1),
        "wilson95": _wilson95(num, den),
    }


def _require_str(raw: dict, key: str, where: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value.strip():
        raise InputError(f"{where}：{key} 必须是非空字符串")
    return value.strip()


def _read_json(path: Path, schema: str, label: str) -> dict:
    if not path.exists():
        raise InputError(f"{label} 文件不存在：{path}")
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InputError(f"{label} 读取/解析失败：{path}：{exc}") from exc
    if not isinstance(doc, dict):
        raise InputError(f"{label} 顶层必须是对象：{path}")
    version = doc.get("schema_version")
    if version is not None and version != schema:
        raise InputError(f"{label} schema_version={version!r}，期望 {schema!r}")
    cases = doc.get("cases")
    if not isinstance(cases, list):
        raise InputError(f"{label} 缺 cases 数组")
    if "case_count" in doc and doc["case_count"] != len(cases):
        raise InputError(f"{label} case_count={doc['case_count']} 与 cases 条数 {len(cases)} 不符")
    return doc


# ── T-184 §2 整数党势（B1 的 delta） ────────────────────────────────────────

def _split_four_pillars(four_pillars: str, where: str = "four_pillars") -> list[str]:
    if not isinstance(four_pillars, str) or not four_pillars.strip():
        raise InputError(f"{where}：four_pillars 必须是非空字符串")
    columns = four_pillars.split()
    if len(columns) != 4:
        raise InputError(f"{where}：four_pillars 必须是四柱（得到 {len(columns)} 柱）：{four_pillars!r}")
    for index, column in enumerate(columns):
        if len(column) != 2 or not _is_gan(column[0]) or not _is_zhi(column[1]):
            raise InputError(f"{where}：第 {index + 1} 柱 {column!r} 不是「天干+地支」两字")
    return columns


def compute_party_delta(four_pillars: str, where: str = "four_pillars") -> int:
    """按 T-184 §2.2–2.7 现算整数 delta = n_F − n_W（只作 B1 基线，不作方向判据）。

    八位同权；A=四天干（戊己中立）、B=四地支本气（土按燥湿）、C=非本气藏干同字透干
    （每个「地支×藏干」对最多 1，藏干土中立）、D=月支本气党 +1。无小数、无权重。
    """
    columns = _split_four_pillars(four_pillars, where)
    stems = [column[0] for column in columns]
    branches = [column[1] for column in columns]
    fire = water = 0

    for stem in stems:
        party = STEM_PARTY[stem]
        if party == "F":
            fire += 1
        elif party == "W":
            water += 1

    for branch in branches:
        party = BRANCH_PARTY[branch]
        if party == "F":
            fire += 1
        elif party == "W":
            water += 1

    for branch in branches:
        for hidden in HIDDEN_STEMS[branch]:
            if hidden not in stems:
                continue
            party = STEM_PARTY[hidden]
            if party == "F":
                fire += 1
            elif party == "W":
                water += 1

    month_party = BRANCH_PARTY[branches[1]]
    if month_party == "F":
        fire += 1
    elif month_party == "W":
        water += 1

    return fire - water


def _pillar_from_addr(addr: str) -> int | None:
    key = _norm_addr(addr)
    match = PILLAR_ADDR_RE.match(key)
    if not match:
        return None
    return PILLAR_INDEX[match.group(1).upper()]


# ── ambiguous 只读原文 loader（T-189b §6；不改引文口径） ─────────────────────

class SourceLoader:
    """按 `sources/<path>:L<line>` 只读取一行文本；绝不越出 source root，绝不写文件。"""

    def __init__(self, root: Path | str = DEFAULT_SOURCE_ROOT) -> None:
        self.root = Path(root).resolve()
        self._cache: dict[str, str] = {}

    def __call__(self, locator: str) -> str:
        key = locator.strip()
        if key in self._cache:
            return self._cache[key]
        match = SOURCE_REF_RE.match(key)
        if not match:
            raise InputError(f"source loader：定位符 {locator!r} 不是 `<path>.md:L<行号>` 形式")
        relative = match.group("path").strip().replace("\\", "/")
        if relative.startswith("sources/"):
            relative = relative[len("sources/"):]
        candidate = Path(relative)
        if candidate.is_absolute():
            raise InputError(f"source loader：定位符不得是绝对路径：{locator!r}")
        target = (self.root / candidate).resolve()
        try:
            target.relative_to(self.root)
        except ValueError as exc:
            raise InputError(f"source loader：定位符越出 source root：{locator!r}") from exc
        if not target.is_file():
            raise InputError(f"source loader：原文文件不存在：{target}")
        line_number = int(match.group("line"))
        try:
            lines = target.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeDecodeError) as exc:
            raise InputError(f"source loader：读取失败：{target}：{exc}") from exc
        if line_number < 1 or line_number > len(lines):
            raise InputError(f"source loader：行号 {line_number} 越界（{target} 共 {len(lines)} 行）")
        text = lines[line_number - 1]
        self._cache[key] = text
        return text


def _collect_source_locators(raw: dict) -> list[str]:
    locators: list[str] = []

    def add(value: Any) -> None:
        if isinstance(value, str) and value.strip():
            locators.append(value.strip())

    add(raw.get("source_ref"))
    extra = raw.get("source_refs")
    if isinstance(extra, list):
        for value in extra:
            add(value)
    quotes = raw.get("conflict_quotes")
    if isinstance(quotes, list):
        for quote in quotes:
            if isinstance(quote, dict):
                add(quote.get("source_ref"))
    return list(dict.fromkeys(locators))


# ── 解析答案（含地址/字归一） ───────────────────────────────────────────────

@dataclass(frozen=True)
class Case:
    case_id: str
    layer: str
    kind: str
    char_a: str
    char_b: str
    expected: str
    source_texts: dict[str, str] = field(default_factory=dict)
    gold_quotes: tuple[str, ...] = ()
    chart_id: str = ""
    pillar_a: int | None = None
    pillar_b: int | None = None
    party_delta: int | None = None
    book: dict[str, str] = field(default_factory=dict)


def _build_book(doc: dict) -> dict[str, str]:
    """全局 address_book；只放跨 case 稳定地址（如 D1/H3）。

    T-189b 起，柱位地址（`Y.b/M.b/...`）在不同盘上指向不同的字，**不能**进全局表；
    它们按 case 存在 `Case.book` 里，评分时只在本 case 内归一。
    """
    book: dict[str, str] = {}
    raw_book = doc.get("address_book")
    if raw_book is None:
        return book
    if not isinstance(raw_book, dict):
        raise InputError("address_book 必须是对象 {地址: 地支字}")
    for addr, char in raw_book.items():
        key = _norm_addr(str(addr))
        value = str(char).strip()
        if not key:
            raise InputError("address_book：地址不能为空")
        if not _is_zhi(value):
            raise InputError(f"address_book：地址 {addr!r} 对应的字 {value!r} 不是单个地支字")
        if key in book and book[key] != value:
            raise InputError(f"address_book：地址 {addr!r} 归一冲突（{book[key]} vs {value}）")
        book[key] = value
    return book


def _endpoint_char(raw: dict, side: str, book: dict[str, str], where: str,
                   case_book: dict[str, str]) -> str:
    char = raw.get(f"char_{side}")
    addr = raw.get(f"addr_{side}")
    has_char = isinstance(char, str) and char.strip()
    has_addr = isinstance(addr, str) and addr.strip()
    if has_char:
        value = char.strip()
        if not _is_zhi(value):
            raise InputError(f"{where}：char_{side}={value!r} 不是单个地支字")
        if has_addr:
            key = _norm_addr(addr)
            if key in book and book[key] != value:
                raise InputError(
                    f"{where}：addr_{side}={addr!r} 在 address_book 记 {book[key]}，"
                    f"与本 case char_{side}={value} 冲突"
                )
            if key in case_book and case_book[key] != value:
                raise InputError(
                    f"{where}：本 case 地址 {addr!r} 归一冲突（{case_book[key]} vs {value}）"
                )
            case_book[key] = value
        return value
    if has_addr:
        key = _norm_addr(addr)
        if key in case_book:
            return case_book[key]
        if key in book:
            return book[key]
        raise InputError(f"{where}：addr_{side}={addr!r} 无法归一到地支字")
    raise InputError(f"{where}：缺 {side} 端（char_{side} 或 addr_{side}）")


def _case_pillar(raw: dict, side: str, where: str) -> int | None:
    """柱位：显式 `pillar_a/b∈{Y,M,D,H}` 与柱位编码地址（`Y.b` 等）二选一或一致。"""
    declared = raw.get(f"pillar_{side}")
    index: int | None = None
    if declared is not None:
        if not isinstance(declared, str) or declared.strip().upper() not in PILLAR_INDEX:
            raise InputError(f"{where}：pillar_{side} 必须是 Y/M/D/H，得到 {declared!r}")
        index = PILLAR_INDEX[declared.strip().upper()]
    addr = raw.get(f"addr_{side}")
    if isinstance(addr, str) and addr.strip():
        from_addr = _pillar_from_addr(addr)
        if from_addr is not None:
            if index is not None and index != from_addr:
                raise InputError(f"{where}：pillar_{side}={declared!r} 与地址 {addr!r} 的柱位冲突")
            index = from_addr
    return index


def _case_party_delta(raw: dict, where: str) -> int | None:
    """B1 的 delta：显式整数，或由 four_pillars 按 T-184 §2 现算；两者都给必须一致。"""
    delta = raw.get("party_delta")
    if delta is not None:
        if isinstance(delta, bool) or not isinstance(delta, int):
            raise InputError(f"{where}：party_delta 必须是整数，得到 {delta!r}")
    computed = None
    four = raw.get("four_pillars")
    if four is not None:
        computed = compute_party_delta(four, f"{where}.four_pillars")
        if delta is not None and delta != computed:
            raise InputError(
                f"{where}：party_delta={delta} 与 four_pillars 现算 delta={computed} 不一致"
            )
    return computed if computed is not None else delta


def _parse_case(raw: dict, book: dict[str, str],
                source_loader: Callable[[str], str] | None = None) -> Case:
    if not isinstance(raw, dict):
        raise InputError("answers.cases 的元素必须是对象")
    case_id = _require_str(raw, "case_id", "answers.case")
    where = f"case {case_id}"
    layer = raw.get("layer")
    if layer not in LAYERS:
        raise InputError(f"{where}：layer={layer!r} 不在 {LAYERS}")
    kind = _require_str(raw, "kind", where)
    if layer == "fixed" and kind not in FIXED_KINDS:
        raise InputError(f"{where}：fixed 层 kind 必须是 {FIXED_KINDS}，得到 {kind!r}")
    if layer == "dynamic" and kind not in DYNAMIC_KINDS:
        raise InputError(f"{where}：dynamic 层 kind 必须是 {DYNAMIC_KINDS}，得到 {kind!r}")
    expected = raw.get("expected_direction")
    if expected not in DIRECTIONS:
        raise InputError(f"{where}：expected_direction={expected!r} 不在 {DIRECTIONS}")
    if layer in ("fixed", "dynamic") and expected == NEEDS_JUDGMENT:
        raise InputError(f"{where}：{layer} 是可判层，答案不得是 needs_judgment")
    if layer == "ambiguous" and expected != NEEDS_JUDGMENT:
        raise InputError(f"{where}：ambiguous 层答案必须是 needs_judgment")

    case_book: dict[str, str] = {}
    char_a = _endpoint_char(raw, "a", book, where, case_book)
    char_b = _endpoint_char(raw, "b", book, where, case_book)

    chart_id = case_id
    raw_chart = raw.get("chart_id")
    if raw_chart is not None:
        if not isinstance(raw_chart, str) or not raw_chart.strip():
            raise InputError(f"{where}：chart_id 必须是非空字符串")
        chart_id = raw_chart.strip()

    pillar_a = _case_pillar(raw, "a", where)
    pillar_b = _case_pillar(raw, "b", where)
    party_delta = _case_party_delta(raw, where)

    source_texts: dict[str, str] = {}
    gold_quotes: tuple[str, ...] = ()
    if layer == "ambiguous":
        raw_texts = raw.get("source_texts")
        if raw_texts is not None and not isinstance(raw_texts, dict):
            raise InputError(f"{where}：source_texts 必须是对象 {{定位符: 行原文}}")
        if isinstance(raw_texts, dict) and raw_texts:
            for locator, text in raw_texts.items():
                if not isinstance(locator, str) or not locator.strip():
                    raise InputError(f"{where}：source_texts 的定位符必须是非空字符串")
                if not isinstance(text, str) or not text.strip():
                    raise InputError(f"{where}：source_texts[{locator}] 必须是非空行原文")
                source_texts[locator.strip()] = text
        elif source_loader is not None:
            locators = _collect_source_locators(raw)
            if not locators:
                raise InputError(
                    f"{where}：ambiguous 缺 source_texts，且没有 source_ref/source_refs 可供 loader 取行"
                )
            for locator in locators:
                try:
                    text = source_loader(locator)
                except InputError:
                    raise
                except Exception as exc:  # 自定义 loader 的 I/O 错误统一归为输入错误
                    raise InputError(f"{where}：source loader 读取失败：{locator}：{exc}") from exc
                if not isinstance(text, str) or not text.strip():
                    raise InputError(f"{where}：source loader 对 {locator} 返回空行")
                source_texts[locator] = text
        else:
            raise InputError(f"{where}：ambiguous 必须给非空 source_texts {{定位符: 行原文}}")
        raw_quotes = raw.get("conflict_quotes")
        if not isinstance(raw_quotes, list) or len(raw_quotes) != 2:
            raise InputError(f"{where}：ambiguous 答案必须给 conflict_quotes[2]")
        quotes = []
        for quote in raw_quotes:
            if not isinstance(quote, str) or not quote.strip():
                raise InputError(f"{where}：conflict_quotes 的每一条都必须是非空字符串")
            quotes.append(quote)
        if quotes[0].strip() == quotes[1].strip():
            raise InputError(f"{where}：conflict_quotes 两条不得相同")
        gold_quotes = tuple(quotes)

    return Case(case_id, layer, kind, char_a, char_b, expected, source_texts, gold_quotes,
                chart_id, pillar_a, pillar_b, party_delta, {**book, **case_book})


# ── 解析系统输出 ────────────────────────────────────────────────────────────

def _parse_observation(raw: dict, known_ids: set[str]) -> dict:
    if not isinstance(raw, dict):
        raise InputError("system-output.cases 的元素必须是对象")
    case_id = _require_str(raw, "case_id", "system-output.case")
    if case_id not in known_ids:
        raise InputError(f"system-output 含未登记 case_id：{case_id}")
    a = _require_str(raw, "a", f"system-output {case_id}")
    b = _require_str(raw, "b", f"system-output {case_id}")
    direction = raw.get("direction")
    if direction not in DIRECTIONS:
        raise InputError(f"system-output {case_id}：direction={direction!r} 不在 {DIRECTIONS}")
    quotes = raw.get("conflict_quotes")
    if quotes is not None and not isinstance(quotes, list):
        raise InputError(f"system-output {case_id}：conflict_quotes 必须是数组")
    locator = raw.get("source_ref")
    if locator is not None and (not isinstance(locator, str) or not locator.strip()):
        raise InputError(f"system-output {case_id}：source_ref 必须是非空字符串")
    return {
        "case_id": case_id,
        "a": a,
        "b": b,
        "direction": direction,
        "conflict_quotes": quotes,
        "source_ref": locator.strip() if isinstance(locator, str) else None,
    }


def _resolve(token: str, book: dict[str, str], where: str) -> str:
    value = token.strip()
    if _is_zhi(value):
        return value
    key = _norm_addr(value)
    if key in book:
        return book[key]
    raise InputError(f"{where}：端点 {token!r} 既不是单个地支字，也不是登记地址")


# ── 单条判分 ────────────────────────────────────────────────────────────────

def _quote_items(quotes: list) -> list[tuple[str, str | None]] | None:
    """归一每条引文：纯字符串或 {quote, source_ref?}；非法返回 None。"""
    items: list[tuple[str, str | None]] = []
    for quote in quotes:
        if isinstance(quote, str):
            if not quote.strip():
                return None
            items.append((quote, None))
            continue
        if isinstance(quote, dict):
            text = quote.get("quote")
            locator = quote.get("source_ref")
            if not isinstance(text, str) or not text.strip():
                return None
            if locator is not None and (not isinstance(locator, str) or not locator.strip()):
                return None
            items.append((text, locator.strip() if isinstance(locator, str) else None))
            continue
        return None
    return items


def _quote_check(case: Case, observed: dict) -> tuple[str, str, list[dict]]:
    """返回 (status, reason, 每条引文明细)。status ∈ correct / quote_fail。"""
    quotes = observed.get("conflict_quotes")
    if not isinstance(quotes, list) or len(quotes) != 2:
        return "quote_fail", "conflict_quotes_not_2", []
    items = _quote_items(quotes)
    if items is None:
        return "quote_fail", "conflict_quotes_not_2", []
    if items[0][0].strip() == items[1][0].strip():
        return "quote_fail", "conflict_quotes_duplicate", []

    details = []
    for quote, locator in items:
        # 引文须逐字落在某一行原文内；若引文自带定位符且答案收录该行，则只认那一行。
        if locator is not None and locator in case.source_texts:
            pool = [case.source_texts[locator]]
        else:
            pool = list(case.source_texts.values())
        details.append({"quote": quote, "locator": locator,
                        "found": any(quote in text for text in pool)})
    if all(item["found"] for item in details):
        return "correct", "needs_judgment_with_quotes", details
    return "quote_fail", "quote_not_verbatim", details


def _element_of(char: str) -> str:
    if _is_zhi(char):
        return BRANCH_ELEMENT[char]
    if _is_gan(char):
        return STEM_ELEMENT[char]
    raise InputError(f"端点 {char!r} 既不是天干也不是地支，无法取本气五行")


def _party_of(char: str) -> str | None:
    if _is_zhi(char):
        return BRANCH_PARTY[char]
    if _is_gan(char):
        return STEM_PARTY[char]
    raise InputError(f"端点 {char!r} 既不是天干也不是地支，无法归党")


def _predicted_direction(actor: str | None) -> str | None:
    if actor == "a":
        return "a→b"
    if actor == "b":
        return "b→a"
    return None


def _b1_actor(case: Case) -> tuple[str | None, str]:
    """B1 = T-184 delta 符号；平局按柱序左端；符号无法定向同类端时弃权。"""
    delta = case.party_delta
    if delta is None:
        return None, "no_delta"
    if delta == 0:
        if case.pillar_a is None or case.pillar_b is None:
            return None, "delta_zero_no_pillar"
        return ("a" if case.pillar_a < case.pillar_b else "b"), "delta_zero_pillar_left"
    strong, weak = ("F", "W") if delta > 0 else ("W", "F")
    party_a = _party_of(case.char_a)
    party_b = _party_of(case.char_b)
    if party_a == strong and party_b == weak:
        return "a", "party_delta"
    if party_b == strong and party_a == weak:
        return "b", "party_delta"
    return None, "delta_party_ambiguous"


def _b2_actor(case: Case) -> tuple[str | None, str]:
    """B2 = 本气克→克方；本气生→生方；同五行→主位端（D/H 优先，否则柱序靠后）。"""
    element_a = _element_of(case.char_a)
    element_b = _element_of(case.char_b)
    if CONTROLS[element_a] == element_b:
        return "a", "ke"
    if CONTROLS[element_b] == element_a:
        return "b", "ke"
    if GENERATES[element_a] == element_b:
        return "a", "sheng"
    if GENERATES[element_b] == element_a:
        return "b", "sheng"
    if element_a == element_b:
        if case.pillar_a is None or case.pillar_b is None:
            return None, "same_element_no_pillar"
        main_a = case.pillar_a in MAIN_PILLARS
        main_b = case.pillar_b in MAIN_PILLARS
        if main_a != main_b:
            return ("a" if main_a else "b"), "same_element_main_position"
        return ("a" if case.pillar_a > case.pillar_b else "b"), "same_element_later_pillar"
    return None, "no_element_relation"


def _baseline_row(case: Case, which: str) -> dict[str, Any]:
    if which == "b1":
        actor, basis = _b1_actor(case)
        row: dict[str, Any] = {"delta": case.party_delta, "basis": basis}
    else:
        actor, basis = _b2_actor(case)
        row = {"basis": basis}
    row["actor"] = actor
    row["predicted"] = _predicted_direction(actor)
    if case.expected != DIRECTED:
        row["correct"] = False
        row["reason"] = "expected_mutual" if case.expected == MUTUAL else "not_decidable"
    elif actor == "a":
        row["correct"] = True
        row["reason"] = "actor_a"
    elif actor == "b":
        row["correct"] = False
        row["reason"] = "actor_b"
    else:
        row["correct"] = False
        row["reason"] = "abstain"
    return row


def _score_case(case: Case, observed: dict | None) -> dict:
    row: dict[str, Any] = {
        "case_id": case.case_id,
        "chart_id": case.chart_id,
        "layer": case.layer,
        "kind": case.kind,
        "expected_direction": case.expected,
        "observed_direction": None,
        "status": "missing",
        "reason": "not_in_system_output",
        "quotes": [],
    }
    if case.layer in ("fixed", "dynamic"):
        row["b1"] = _baseline_row(case, "b1")
        row["b2"] = _baseline_row(case, "b2")
    if observed is None:
        return row

    where = f"system-output {case.case_id}"
    obs_a = _resolve(observed["a"], case.book, where)
    obs_b = _resolve(observed["b"], case.book, where)
    direction = observed["direction"]
    row["observed_direction"] = direction
    row["observed_a"], row["observed_b"] = obs_a, obs_b

    pair_match = obs_a == case.char_a and obs_b == case.char_b
    pair_swapped = obs_a == case.char_b and obs_b == case.char_a

    if case.layer == "ambiguous":
        if not (pair_match or pair_swapped):
            row["status"], row["reason"] = "wrong", "endpoint_mismatch"
            return row
        if direction != NEEDS_JUDGMENT:
            row["status"] = "wrong"
            row["reason"] = "directed_claim_on_ambiguous" if direction == DIRECTED \
                else "mutual_claim_on_ambiguous"
            return row
        status, reason, details = _quote_check(case, observed)
        row["status"], row["reason"], row["quotes"] = status, reason, details
        return row

    # fixed / dynamic：可判层
    if direction == NEEDS_JUDGMENT:
        row["status"], row["reason"] = "nj", "needs_judgment"
        return row
    if case.expected == DIRECTED:
        if direction == MUTUAL:
            row["status"], row["reason"] = "wrong", "expected_directed_observed_mutual"
        elif pair_match:
            row["status"], row["reason"] = "correct", "directed_match"
        elif pair_swapped:
            row["status"], row["reason"] = "wrong", "reversed"
        else:
            row["status"], row["reason"] = "wrong", "endpoint_mismatch"
        return row
    # expected == MUTUAL
    if direction == DIRECTED:
        row["status"], row["reason"] = "wrong", "expected_mutual_observed_directed"
    elif pair_match or pair_swapped:
        row["status"], row["reason"] = "correct", "mutual_match"
    else:
        row["status"], row["reason"] = "wrong", "endpoint_mismatch"
    return row


# ── 汇总 ────────────────────────────────────────────────────────────────────

def _layer_summary(layer: str, rows: list[dict]) -> dict[str, Any]:
    counts = Counter(row["status"] for row in rows)
    total = len(rows)
    correct = counts.get("correct", 0)
    wrong = counts.get("wrong", 0)
    missing = counts.get("missing", 0)
    if layer == "ambiguous":
        # ambiguous 的 nj 本身就是交付：只要给了方向+双引文就计入 delivered。
        delivered = total - missing
    else:
        # fixed/dynamic 的 delivered 只算硬方向声明；nj 与 missing 同属 miss。
        delivered = correct + wrong
    summary: dict[str, Any] = {
        "total": total,
        "correct": correct,
        "wrong": wrong,
        "missing": missing,
        "delivered": delivered,
        "delivered_rate": _metric(delivered, total),
        "correct_over_total": _metric(correct, total),
        "precision": _metric(correct, delivered),
    }
    if layer == "ambiguous":
        quote_fail = counts.get("quote_fail", 0)
        quotes = [quote for row in rows for quote in row["quotes"]]
        verbatim = sum(1 for quote in quotes if quote["found"])
        summary.update({
            "quote_fail": quote_fail,
            "both_quotes": _metric(correct, total),
            "quotes_checked": len(quotes),
            "quotes_verbatim": verbatim,
            "quote_violations": len(quotes) - verbatim,
            "quote_violation_rate": _metric(len(quotes) - verbatim, len(quotes)),
        })
    else:
        nj = counts.get("nj", 0)
        summary.update({
            "nj": nj,
            "miss": nj + missing,
            "miss_rate": _metric(nj + missing, total),
            "all_correct": correct == total,
        })
    return summary


def _by_kind(rows: list[dict]) -> list[dict]:
    grouped: dict[tuple[str, str], list[dict]] = {}
    for row in rows:
        grouped.setdefault((row["layer"], row["kind"]), []).append(row)
    table = []
    for (layer, kind), items in grouped.items():
        counts = Counter(item["status"] for item in items)
        total = len(items)
        table.append({
            "layer": layer,
            "kind": kind,
            "total": total,
            "correct": counts.get("correct", 0),
            "wrong": counts.get("wrong", 0),
            "nj": counts.get("nj", 0),
            "quote_fail": counts.get("quote_fail", 0),
            "missing": counts.get("missing", 0),
            "hit_rate": _metric(counts.get("correct", 0), total),
        })
    table.sort(key=lambda row: (LAYERS.index(row["layer"]), row["kind"]))
    return table


def _baseline_summary(rows: list[dict]) -> dict[str, Any]:
    """dynamic 40 的两条笨基线与 margin；弃权按不中计（对系统保守）。"""
    dynamic = [row for row in rows if row["layer"] == "dynamic"]
    total = len(dynamic)
    correct = sum(1 for row in dynamic if row["status"] == "correct")
    summary: dict[str, Any] = {"total": total, "correct": correct}
    for key in ("b1", "b2"):
        hits = sum(1 for row in dynamic if row.get(key) and row[key]["correct"])
        available = sum(1 for row in dynamic if row.get(key) and row[key]["predicted"])
        data_missing = sum(
            1 for row in dynamic
            if row.get(key) and row[key]["basis"] in DATA_MISSING_BASIS
        )
        summary[key] = {
            "correct": hits,
            "available": available,
            "abstain": total - available,
            "data_missing": data_missing,
            "correct_over_total": _metric(hits, total),
        }
    best_key = "b1" if summary["b1"]["correct"] >= summary["b2"]["correct"] else "b2"
    best_correct = summary[best_key]["correct"]
    summary["best"] = best_key
    summary["best_correct"] = best_correct
    summary["margin"] = correct - best_correct
    summary["margin_comparable"] = (
        summary["b1"]["data_missing"] == 0 and summary["b2"]["data_missing"] == 0
    )
    return summary


def _chart_bootstrap(groups: dict[str, list[dict]], iterations: int,
                     seed: int) -> dict[str, float | None]:
    """chart 聚类 bootstrap：按盘有放回重抽，算 case 加权准确率的 95% 百分位区间。"""
    chart_ids = sorted(groups)
    if not chart_ids:
        return {"lower": None, "upper": None}
    rng = random.Random(seed)
    values: list[float] = []
    for _ in range(iterations):
        numerator = denominator = 0
        for _ in chart_ids:
            chosen = chart_ids[rng.randrange(len(chart_ids))]
            items = groups[chosen]
            numerator += sum(1 for row in items if row["status"] == "correct")
            denominator += len(items)
        values.append(numerator / denominator)
    values.sort()
    lower = values[int(0.025 * iterations)]
    upper = values[min(iterations - 1, int(0.975 * iterations) - 1)]
    return {"lower": round(lower, 4), "upper": round(upper, 4)}


def _chart_cluster(rows: list[dict], *, iterations: int = CLUSTER_BOOTSTRAP_ITERATIONS,
                   seed: int = CLUSTER_BOOTSTRAP_SEED) -> dict[str, Any]:
    """dynamic 按 chart_id 聚合：macro 准确率、全对盘率、chart bootstrap CI。"""
    dynamic = [row for row in rows if row["layer"] == "dynamic"]
    groups: dict[str, list[dict]] = {}
    for row in dynamic:
        groups.setdefault(row["chart_id"], []).append(row)
    charts = len(groups)
    total = len(dynamic)
    correct = sum(1 for row in dynamic if row["status"] == "correct")
    if charts:
        macro = sum(
            sum(1 for row in items if row["status"] == "correct") / len(items)
            for items in groups.values()
        ) / charts
        all_correct = sum(
            1 for items in groups.values() if all(row["status"] == "correct" for row in items)
        )
    else:
        macro = None
        all_correct = 0
    per_chart = [
        {
            "chart_id": chart_id,
            "cases": len(items),
            "correct": sum(1 for row in items if row["status"] == "correct"),
        }
        for chart_id, items in sorted(groups.items())
    ]
    sizes = Counter(len(items) for items in groups.values())
    return {
        "charts": charts,
        "cases": total,
        "correct": correct,
        "case_weighted_accuracy": _metric(correct, total),
        "chart_macro_accuracy": None if macro is None else round(macro, 4),
        "all_correct_charts": all_correct,
        "all_correct_chart_rate": _metric(all_correct, charts),
        "bootstrap95": _chart_bootstrap(groups, iterations, seed),
        "bootstrap": {"iterations": iterations, "seed": seed,
                      "method": "chart_cluster_percentile_case_weighted"},
        "chart_sizes": {str(size): count for size, count in sorted(sizes.items())},
        "per_chart": per_chart,
    }


def _direction_signature(row: dict | None) -> tuple:
    if row is None or row.get("observed_direction") is None:
        return ("missing",)
    direction = row["observed_direction"]
    if direction == DIRECTED:
        return ("directed", row.get("observed_a"), row.get("observed_b"))
    return (direction,)


def _consistency(rows_per_run: list[list[dict]]) -> dict[str, Any]:
    """3 次（或 n 次）运行的方向一致率：定向比端点取向，mutual/nj 比类型。"""
    if not rows_per_run:
        raise InputError("consistency 至少需要 1 次运行")
    runs = len(rows_per_run)
    case_ids = [row["case_id"] for row in rows_per_run[0]]
    lookups = [{row["case_id"]: row for row in rows} for rows in rows_per_run]
    result: dict[str, Any] = {"runs": runs, "three_runs": runs == 3}
    for scope in ("dynamic", "fixed", "ambiguous", "all"):
        subset = [
            case_id for case_id in case_ids
            if scope == "all" or lookups[0][case_id]["layer"] == scope
        ]
        consistent = 0
        for case_id in subset:
            signatures = tuple(_direction_signature(lookup.get(case_id)) for lookup in lookups)
            if len(set(signatures)) == 1:
                consistent += 1
        result[scope] = {
            "cases": len(subset),
            "consistent": consistent,
            "rate": _metric(consistent, len(subset)) if runs >= 2 else None,
        }
    return result


def _t187_endpoint(token: str, chart: list[str], where: str) -> str:
    value = token.strip()
    if _is_zhi(value) or _is_gan(value):
        return value
    match = PILLAR_ADDR_RE.match(_norm_addr(value))
    if not match:
        raise InputError(f"{where}：端点 {token!r} 不是字，也不是柱位地址（Y.s/M.b/...）")
    column = chart[PILLAR_INDEX[match.group(1).upper()]]
    return column[0] if match.group(2).upper() == "S" else column[1]


def t187_regression(run_doc: dict, answers_doc: dict) -> dict[str, Any]:
    """T-187 回归：读 system-run + fresh-40 答案，按四柱地址归一后复算三数。

    edge = 系统端点字集合 == 答案端点字集合（无序）；direction 只在系统交付了
    `actor→target` / `mutual` 时计分母，且要求边对得上、定向取向/ mutual 与答案一致。
    """
    run_cases = {case["case_id"]: case for case in run_doc["cases"]}
    answer_cases = answers_doc["cases"]
    edge_match = 0
    delivered = 0
    direction_correct = 0
    edge_match_case_ids: list[str] = []
    for case in answer_cases:
        case_id = case["case_id"]
        if case_id not in run_cases:
            continue
        run_case = run_cases[case_id]
        chart = _split_four_pillars(case["four_pillars"], f"T-187 {case_id}")
        system_a = _t187_endpoint(run_case["a"], chart, f"T-187 {case_id}")
        system_b = _t187_endpoint(run_case["b"], chart, f"T-187 {case_id}")
        answer_a = case["relation"]["a"]
        answer_b = case["relation"]["b"]
        edge_ok = {system_a, system_b} == {answer_a, answer_b}
        if edge_ok:
            edge_match += 1
            edge_match_case_ids.append(case_id)
        direction = run_case.get("direction")
        if direction not in (DIRECTED, MUTUAL):
            continue
        delivered += 1
        if not edge_ok:
            continue
        if direction == DIRECTED:
            if system_a == answer_a and system_b == answer_b:
                direction_correct += 1
        elif case["relation"].get("mutual") is True:
            direction_correct += 1
    total = len(answer_cases)
    return {
        "cases": total,
        "edge_match": edge_match,
        "edge_mismatch": total - edge_match,
        "edge_match_rate": _metric(edge_match, total),
        "edge_match_case_ids": edge_match_case_ids,
        "direction_delivered": delivered,
        "direction_correct": direction_correct,
        "direction_rate": _metric(direction_correct, delivered),
    }


def _parse_answers(answers: dict,
                   source_loader: Callable[[str], str] | None) -> list[Case]:
    raw_cases = answers["cases"]
    book = _build_book(answers)
    cases: list[Case] = []
    seen: set[str] = set()
    for raw in raw_cases:
        case = _parse_case(raw, book, source_loader)
        if case.case_id in seen:
            raise InputError(f"answers 含重复 case_id：{case.case_id}")
        seen.add(case.case_id)
        cases.append(case)
    return cases


def evaluate(answers: dict, output: dict,
             *, source_loader: Callable[[str], str] | None = None) -> dict:
    return evaluate_runs(answers, [output], source_loader=source_loader)


def evaluate_runs(answers: dict, outputs: list[dict],
                  *, source_loader: Callable[[str], str] | None = None) -> dict:
    if not outputs:
        raise InputError("至少需要一份 system-output")
    cases = _parse_answers(answers, source_loader)
    seen = {case.case_id for case in cases}
    results: list[dict[str, Any]] = []
    for output in outputs:
        observations = {}
        for raw in output["cases"]:
            observed = _parse_observation(raw, seen)
            if observed["case_id"] in observations:
                raise InputError(f"system-output 含重复 case_id：{observed['case_id']}")
            observations[observed["case_id"]] = observed

        rows = [_score_case(case, observations.get(case.case_id)) for case in cases]
        layers = {layer: _layer_summary(layer, [r for r in rows if r["layer"] == layer])
                  for layer in LAYERS}

        for layer, summary in layers.items():
            parts = summary["correct"] + summary["wrong"] + summary["missing"] + \
                summary.get("nj", 0) + summary.get("quote_fail", 0)
            if parts != summary["total"]:
                raise InputError(f"记账不平：{layer} {parts} != {summary['total']}")

        counts = {layer: layers[layer]["total"] for layer in LAYERS}
        counts["total"] = len(cases)
        counts["prereg"] = dict(PREREG_DENOMINATORS)
        counts["denominators_met"] = all(
            counts[layer] == PREREG_DENOMINATORS[layer] for layer in LAYERS
        )
        counts["total_met"] = (
            counts["total"] == sum(PREREG_DENOMINATORS.values()) and counts["denominators_met"]
        )

        results.append({
            "schema_version": SCHEMA_SCORE,
            "counts": counts,
            "layers": layers,
            "by_kind": _by_kind(rows),
            "cases": rows,
        })

    primary = results[0]
    primary["baselines"] = _baseline_summary(primary["cases"])
    primary["chart_cluster"] = _chart_cluster(primary["cases"])
    primary["consistency"] = _consistency([result["cases"] for result in results])
    return primary


def _read_any_json(path: Path, label: str) -> dict:
    if not path.exists():
        raise InputError(f"{label} 文件不存在：{path}")
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InputError(f"{label} 读取/解析失败：{path}：{exc}") from exc
    if not isinstance(doc, dict) or not isinstance(doc.get("cases"), list):
        raise InputError(f"{label} 顶层必须是含 cases 数组的对象：{path}")
    return doc


def run(answers_path: Path, output_path: Path,
        *, source_loader: Callable[[str], str] | None = None) -> dict:
    answers = _read_json(Path(answers_path), SCHEMA_ANSWERS, "answers")
    output = _read_json(Path(output_path), SCHEMA_OUTPUT, "system-output")
    return evaluate(answers, output, source_loader=source_loader)


def run_many(answers_path: Path, output_paths: list[Path],
             *, source_loader: Callable[[str], str] | None = None,
             t187_run_path: Path | None = None,
             t187_answers_path: Path | None = None) -> dict:
    answers = _read_json(Path(answers_path), SCHEMA_ANSWERS, "answers")
    outputs = [_read_json(Path(path), SCHEMA_OUTPUT, "system-output") for path in output_paths]
    result = evaluate_runs(answers, outputs, source_loader=source_loader)
    if t187_run_path is not None and t187_answers_path is not None:
        result["t187_regression"] = t187_regression(
            _read_any_json(Path(t187_run_path), "T-187 system-run"),
            _read_any_json(Path(t187_answers_path), "T-187 answers"),
        )
    return result


# ── CLI ─────────────────────────────────────────────────────────────────────

def _format_console(result: dict) -> str:
    layers = result["layers"]
    counts = result["counts"]
    lines = [
        "[P1 断言评分 v2] 三层分录："
        f"fixed {layers['fixed']['total']} / dynamic {layers['dynamic']['total']} / "
        f"ambiguous {layers['ambiguous']['total']}"
        f"（预注册 {PREREG_DENOMINATORS['fixed']}/{PREREG_DENOMINATORS['dynamic']}"
        f"/{PREREG_DENOMINATORS['ambiguous']}；分母"
        f"{'齐' if counts['total_met'] else '不齐（不得引用 pass/kill）'}）",
    ]
    for layer in LAYERS:
        summary = layers[layer]
        precision = summary["precision"]
        wilson = precision["wilson95"]
        if precision["value"] is None:
            precision_text = "n/a（无交付）"
        else:
            precision_text = (f"{precision['numerator']}/{precision['denominator']} = "
                              f"{precision['percent']}% Wilson95 "
                              f"[{wilson['lower']}, {wilson['upper']}]")
        if layer == "ambiguous":
            lines.append(
                f"  ambiguous：correct={summary['correct']} wrong={summary['wrong']} "
                f"quote_fail={summary['quote_fail']} missing={summary['missing']} | "
                f"双引文 {summary['both_quotes']['numerator']}/{summary['both_quotes']['denominator']}"
                f" | 引文违规 {summary['quote_violations']}/{summary['quotes_checked']}"
                f" | precision {precision_text}"
            )
        else:
            nj_note = "（nj=miss）" if layer == "dynamic" else ""
            lines.append(
                f"  {layer}：correct={summary['correct']} wrong={summary['wrong']} "
                f"nj={summary['nj']}{nj_note} missing={summary['missing']} | "
                f"precision {precision_text} | "
                f"correct/total {summary['correct']}/{summary['total']}"
            )
    kinds = " | ".join(
        f"{row['layer']}:{row['kind']} {row['correct']}/{row['total']}"
        for row in result["by_kind"]
    )
    lines.append(f"  分类型：{kinds}")

    baselines = result.get("baselines")
    if baselines and baselines["total"]:
        b1, b2 = baselines["b1"], baselines["b2"]
        comparable_note = "" if baselines["margin_comparable"] else "（缺 delta/柱位，不可比）"
        lines.append(
            f"  基线：B1 {b1['correct']}/{baselines['total']} | "
            f"B2 {b2['correct']}/{baselines['total']} | "
            f"best {baselines['best']} {baselines['best_correct']} | "
            f"margin {baselines['correct']}−{baselines['best_correct']}="
            f"{baselines['margin']:+d}{comparable_note}"
        )

    cluster = result.get("chart_cluster")
    if cluster and cluster["charts"]:
        boot = cluster["bootstrap95"]
        all_rate = cluster["all_correct_chart_rate"]
        macro = cluster["chart_macro_accuracy"]
        lines.append(
            f"  chart 聚类：{cluster['charts']} 盘 | 全对盘 "
            f"{all_rate['numerator']}/{all_rate['denominator']} = {all_rate['percent']}% | "
            f"macro {macro:.1%} | bootstrap95 [{boot['lower']}, {boot['upper']}]"
        )

    consistency = result.get("consistency")
    if consistency:
        dynamic = consistency["dynamic"]
        if consistency["three_runs"] and dynamic["rate"] is not None:
            lines.append(
                f"  3 次方向一致：dynamic {dynamic['consistent']}/{dynamic['cases']} = "
                f"{dynamic['rate']['percent']}%"
            )
        else:
            lines.append(
                f"  3 次方向一致：n/a（{consistency['runs']} 次运行；需 3 次）"
            )

    t187 = result.get("t187_regression")
    if t187:
        lines.append(
            f"  T-187 回归：edge {t187['edge_match']}/{t187['cases']}、"
            f"direction {t187['direction_correct']}/{t187['direction_delivered']}、"
            f"edge mismatch {t187['edge_mismatch']}/{t187['cases']}"
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="A+ 裁决评分器 v2（T-189a 核心 + T-189b 增量）")
    parser.add_argument("--answers", required=True, type=Path)
    parser.add_argument("--system-output", required=True, action="append", type=Path,
                        help="可重复 1–3 次；多次用于方向一致率")
    parser.add_argument("--json", action="store_true", help="输出机器可读 JSON")
    parser.add_argument("--source-loader", action="store_true",
                        help="ambiguous 缺 source_texts 时，按 source_ref(s) 从 sources/ 只读取行")
    parser.add_argument("--source-root", type=Path, default=DEFAULT_SOURCE_ROOT,
                        help="source loader 的只读根（默认仓库 sources/）")
    parser.add_argument("--t187-run", type=Path, help="可选：META/p1-system-run-v1.json")
    parser.add_argument("--t187-answers", type=Path, help="可选：META/p1-fresh-40-answers-v1.json")
    args = parser.parse_args(argv)
    if (args.t187_run is None) != (args.t187_answers is None):
        parser.error("--t187-run 与 --t187-answers 必须同时给")
    loader = SourceLoader(args.source_root) if args.source_loader else None
    try:
        result = run_many(
            args.answers, args.system_output, source_loader=loader,
            t187_run_path=args.t187_run, t187_answers_path=args.t187_answers,
        )
    except InputError as exc:
        print(f"[p1_assertion_eval_v2] 输入不合口径：{exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(_format_console(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

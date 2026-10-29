"""tools/p1_assertion_eval_v2.py · T-189a · A+ 裁决评分器 v2（核心层）。

只做核心尺子（T-189a 卡）：

1. **三层分录**：`fixed`（克/生/化/墓）/ `dynamic`（冲/合/穿/刑）/ `ambiguous`，
   三层各自记账，fixed 不混进 dynamic，ambiguous 单列；
2. **地址/字双向归一**：端点可写 `char_a/char_b`（单个地支字）或 `addr_a/addr_b`
   （地址；经 `address_book` 或同 case 的 addr↔char 对归一），系统输出同样两种写法混用可比；
3. **dynamic 上 nj=miss**：系统对可判条给 `needs_judgment` 记 `nj`，与 `missing` 一起算 miss，
   不再当作中性弃权；
4. **ambiguous 的双引文**：期望 `needs_judgment`，且 `conflict_quotes` 恰好 2 条、
   互不相同、**逐字**出现在所引原文行内（`source_texts` 的某一行）；缺引文/非逐字记 `quote_fail`；
5. 指标：`correct/total`、`precision`、`delivered`、Wilson 95% CI、分类型小表。
   `delivered`：fixed/dynamic 只算硬方向声明（`correct+wrong`；nj 不算交付），
   ambiguous 算全部有输出的行（nj + 双引文本身就是交付）；`precision = correct/delivered`。

不做（T-189b / 后续卡）：B1/B2 基线、chart 聚类、3 次一致、T-187 回归、真实 anchor-60 跑分、
pass/kill 判定、阈值改动。本模块不 import engine、不读 sources/、不写任何文件。

输入（两份 JSON，UTF-8）：

answers::

    {"schema_version": "p1-adjudication-answers/v2",
     "address_book": {"D1": "巳", "H3": "亥"},          # 可选；地址→地支字
     "cases": [
       {"case_id": "FX-01", "layer": "fixed", "kind": "克", "mechanism": "克",
        "addr_a": "D1", "char_a": "巳", "addr_b": "H3", "char_b": "亥",
        "expected_direction": "actor→target", "source_ref": "..."},
       {"case_id": "AM-01", "layer": "ambiguous", "kind": "刑", "mechanism": "刑",
        "char_a": "未", "char_b": "戌", "expected_direction": "needs_judgment",
        "source_ref": "sources/duan/x.md:L12",
        "source_texts": {"sources/duan/x.md:L12": "<该行原文>"},
        "conflict_quotes": ["<正引文>", "<反引文>"]}]}

system output::

    {"schema_version": "p1-adjudication-system-output/v2",
     "cases": [{"case_id": "FX-01", "a": "巳", "b": "H3",
                "direction": "actor→target", "source_ref": "..."}]}

ambiguous 的 nj 声明必须带 `conflict_quotes: [...2 条...]`；每条可以是纯字符串，
也可以是 ``{"quote": "<逐字>", "source_ref": "<行定位符>"}``（给了定位符就只认那一行）。
引文必须逐字出现在答案 `source_texts` 的某一行内，缺一条/非逐字/重复均记 `quote_fail`。

CLI：``python -m tools.p1_assertion_eval_v2 --answers A.json --system-output S.json [--json]``
退出码 0 = 评完（分数高低不影响退出码）；2 = 输入不合口径（缺文件 / schema 错 / case 对不上 / 记账不平）。
产物不含时间戳，同一输入两次运行逐字节一致。
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

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

PREREG_DENOMINATORS = {"fixed": 10, "dynamic": 40, "ambiguous": 10}
Z95 = 1.959963984540054


class InputError(ValueError):
    """输入不合口径：CLI 退出码 2，不静默兜底。"""


# ── 通用小工具 ───────────────────────────────────────────────────────────────

def _norm_addr(addr: str) -> str:
    """地址归一：去空白 + 大写（`d1` / ` D1 ` 视同 `D1`）。"""
    return addr.strip().upper()


def _is_zhi(token: str) -> bool:
    return len(token) == 1 and token in ZHI


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


def _build_book(doc: dict, raw_cases: list[dict]) -> dict[str, str]:
    """合并 doc.address_book 与各 case 的 addr↔char 对；冲突即报错。"""
    book: dict[str, str] = {}

    def add(addr: str, char: str, where: str) -> None:
        key = _norm_addr(addr)
        if not key:
            raise InputError(f"{where}：地址不能为空")
        if not _is_zhi(char):
            raise InputError(f"{where}：地址 {addr!r} 对应的字 {char!r} 不是单个地支字")
        if key in book and book[key] != char:
            raise InputError(f"{where}：地址 {addr!r} 归一冲突（{book[key]} vs {char}）")
        book[key] = char

    raw_book = doc.get("address_book")
    if raw_book is not None:
        if not isinstance(raw_book, dict):
            raise InputError("address_book 必须是对象 {地址: 地支字}")
        for addr, char in raw_book.items():
            add(str(addr), str(char).strip(), "address_book")

    for index, raw in enumerate(raw_cases):
        where = f"answers.cases[{index}]"
        case_id = raw.get("case_id") if isinstance(raw, dict) else None
        if isinstance(case_id, str) and case_id.strip():
            where = f"case {case_id.strip()}"
        addr = raw.get("addr_a")
        char = raw.get("char_a")
        if isinstance(addr, str) and addr.strip():
            if isinstance(char, str) and char.strip():
                add(addr, char.strip(), where)
            elif _norm_addr(addr) not in book:
                raise InputError(f"{where}：addr_a={addr!r} 不在 address_book，且未给 char_a，无法归一")
        addr = raw.get("addr_b")
        char = raw.get("char_b")
        if isinstance(addr, str) and addr.strip():
            if isinstance(char, str) and char.strip():
                add(addr, char.strip(), where)
            elif _norm_addr(addr) not in book:
                raise InputError(f"{where}：addr_b={addr!r} 不在 address_book，且未给 char_b，无法归一")
    return book


def _endpoint_char(raw: dict, side: str, book: dict[str, str], where: str) -> str:
    char = raw.get(f"char_{side}")
    addr = raw.get(f"addr_{side}")
    if isinstance(char, str) and char.strip():
        value = char.strip()
        if not _is_zhi(value):
            raise InputError(f"{where}：char_{side}={value!r} 不是单个地支字")
        return value
    if isinstance(addr, str) and addr.strip():
        key = _norm_addr(addr)
        if key in book:
            return book[key]
        raise InputError(f"{where}：addr_{side}={addr!r} 无法归一到地支字")
    raise InputError(f"{where}：缺 {side} 端（char_{side} 或 addr_{side}）")


def _parse_case(raw: dict, book: dict[str, str]) -> Case:
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

    char_a = _endpoint_char(raw, "a", book, where)
    char_b = _endpoint_char(raw, "b", book, where)

    source_texts: dict[str, str] = {}
    gold_quotes: tuple[str, ...] = ()
    if layer == "ambiguous":
        raw_texts = raw.get("source_texts")
        if not isinstance(raw_texts, dict) or not raw_texts:
            raise InputError(f"{where}：ambiguous 必须给非空 source_texts {{定位符: 行原文}}")
        for locator, text in raw_texts.items():
            if not isinstance(locator, str) or not locator.strip():
                raise InputError(f"{where}：source_texts 的定位符必须是非空字符串")
            if not isinstance(text, str) or not text.strip():
                raise InputError(f"{where}：source_texts[{locator}] 必须是非空行原文")
            source_texts[locator.strip()] = text
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

    return Case(case_id, layer, kind, char_a, char_b, expected, source_texts, gold_quotes)


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


def _score_case(case: Case, observed: dict | None, book: dict[str, str]) -> dict:
    row: dict[str, Any] = {
        "case_id": case.case_id,
        "layer": case.layer,
        "kind": case.kind,
        "expected_direction": case.expected,
        "observed_direction": None,
        "status": "missing",
        "reason": "not_in_system_output",
        "quotes": [],
    }
    if observed is None:
        return row

    where = f"system-output {case.case_id}"
    obs_a = _resolve(observed["a"], book, where)
    obs_b = _resolve(observed["b"], book, where)
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


def evaluate(answers: dict, output: dict) -> dict:
    raw_cases = answers["cases"]
    book = _build_book(answers, raw_cases)
    cases: list[Case] = []
    seen: set[str] = set()
    for raw in raw_cases:
        case = _parse_case(raw, book)
        if case.case_id in seen:
            raise InputError(f"answers 含重复 case_id：{case.case_id}")
        seen.add(case.case_id)
        cases.append(case)

    observations = {}
    for raw in output["cases"]:
        observed = _parse_observation(raw, seen)
        if observed["case_id"] in observations:
            raise InputError(f"system-output 含重复 case_id：{observed['case_id']}")
        observations[observed["case_id"]] = observed

    rows = [_score_case(case, observations.get(case.case_id), book) for case in cases]
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
    if counts["total"] != sum(PREREG_DENOMINATORS.values()):
        counts["total_met"] = False
    else:
        counts["total_met"] = counts["denominators_met"]

    return {
        "schema_version": SCHEMA_SCORE,
        "counts": counts,
        "layers": layers,
        "by_kind": _by_kind(rows),
        "cases": rows,
    }


def run(answers_path: Path, output_path: Path) -> dict:
    answers = _read_json(Path(answers_path), SCHEMA_ANSWERS, "answers")
    output = _read_json(Path(output_path), SCHEMA_OUTPUT, "system-output")
    return evaluate(answers, output)


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
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="A+ 裁决评分器 v2（T-189a 核心层）")
    parser.add_argument("--answers", required=True, type=Path)
    parser.add_argument("--system-output", required=True, type=Path)
    parser.add_argument("--json", action="store_true", help="输出机器可读 JSON")
    args = parser.parse_args(argv)
    try:
        result = run(args.answers, args.system_output)
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

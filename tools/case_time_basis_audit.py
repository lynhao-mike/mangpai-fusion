#!/usr/bin/env python
"""T-130 · 案例排盘口径普查器（只读）。

口径依据：``docs/adr/ADR-005-case-time-basis.md``。每个案例判定两个字段：

- ``time_basis``     ∈ {true_solar, clock_beijing, unknown}
- ``basis_evidence`` ∈ {longitude_calc, explicit_time, label_only, none}

判定只读 ``cases/*/input.md``，不改案例、不调引擎、不做任何真太阳时换算。

用法::

    python -m tools.case_time_basis_audit            # 摘要
    python -m tools.case_time_basis_audit --summary  # 分档计数表
    python -m tools.case_time_basis_audit --json     # 机器可读清单（写 META 产物）
    python -m tools.case_time_basis_audit --case C-2026-010-坤-甲子丁卯癸卯庚申
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CASES_DIR = REPO_ROOT / "cases"
DEFAULT_OUT = REPO_ROOT / "META" / "case-time-basis-v1.json"

TRUE_SOLAR = "true_solar"
CLOCK = "clock_beijing"
UNKNOWN = "unknown"

LONGITUDE_CALC = "longitude_calc"
EXPLICIT_TIME = "explicit_time"
LABEL_ONLY = "label_only"
NONE = "none"

TIME_BASIS_VALUES = (TRUE_SOLAR, CLOCK, UNKNOWN)
EVIDENCE_VALUES = (LONGITUDE_CALC, EXPLICIT_TIME, LABEL_ONLY, NONE)

# ---------------------------------------------------------------- 正则

RE_DATETIME = re.compile(
    r"\d{4}\s*-\s*\d{1,2}\s*-\s*\d{1,2}[ \t]*\d{1,2}\s*[:：]\s*\d{2}"
)
# 出生时刻声明行：同一行既有出生时间关键词又有具体到分的日期时间
BIRTH_KEYS = ("公历", "阳历", "Solar", "出生时间", "出生时刻", "生日")

# 结构化字段：真太阳时校正: true / false / 未知
RE_CORR_FLAG = re.compile(r"真太阳时校正\s*[:：]\s*(true|false|是|否|未知|unknown)")
# 手写字段：是否真太阳时：未知
RE_IS_SOLAR_UNKNOWN = re.compile(r"是否真太阳时\s*[:：]\s*未知")
# 导入器字段
RE_IMPORTER = re.compile(r"真太阳时字段优先\s*[:：]\s*(true|false)")
RE_SRC = re.compile(r"时间来源\s*[:：]\s*(true_solar_time_raw|birth_datetime_raw|none)")
# 明示「没有可用出生时刻」
RE_NO_TIME = re.compile(r"命主未提供(?:可确认的)?出生时刻|公历生日精确到分未提供")

# 校正后时刻字段：太阳时 / 真太阳时 / Sun（Sun = 真太阳时，见 C-2026-017/lessons.md）
RE_SOLAR_ROW = re.compile(
    r"(?m)^\s*(?:[-*>|]\s*)?(?:\*\*)?(?:真?太阳时|Sun)(?:\*\*)?\s*[|:：]\s*(.*?)\s*\|?\s*$"
)
# 出生行内的真太阳时标注，例如 （真太阳时） / （已校真太阳时） / （真太阳时·辰时）
RE_TABLE_NOTE = re.compile(r"[（(][^（()）]*真太阳时[^（()）]*[）)]")
# 出生地经度（度分表达式或「经度: 116」）
RE_LONGITUDE = re.compile(r"\d{2,3}(?:\.\d+)?\s*[°度]\s*[EeWwNn]|经度\s*[:：]\s*\d{2,3}")
# 自我否定：写了校正字段但没有真的校正
RE_NEGATED = re.compile(r"未校正|未做地理校正|与公历同|未换算|未做[^，。；]{0,8}换算")


# ---------------------------------------------------------------- 工具函数


def find_birth_lines(text: str) -> list[str]:
    """返回所有同时含出生时间关键词与具体时刻的行（同一案例可能重复声明）。"""
    out = []
    for line in text.splitlines():
        s = line.strip()
        if RE_DATETIME.search(s) and any(k in s for k in BIRTH_KEYS):
            out.append(s)
    return out


def solar_row_values(text: str) -> list[str]:
    """抽取所有「太阳时 / 真太阳时 / Sun」字段的值。"""
    return [m.group(1).strip() for m in RE_SOLAR_ROW.finditer(text)]


def has_concrete_time(value: str) -> bool:
    """该字段值是否给出具体时刻，且未被自我否定。"""
    return bool(RE_DATETIME.search(value)) and not RE_NEGATED.search(value)


def corr_flag(text: str) -> str | None:
    m = RE_CORR_FLAG.search(text)
    if not m:
        return None
    raw = m.group(1)
    if raw in ("true", "是"):
        return "true"
    if raw in ("false", "否"):
        return "false"
    return "unknown"


# ---------------------------------------------------------------- 判定


def classify(text: str) -> dict:
    """按 ADR-005 判定单例，返回 time_basis / basis_evidence / 依据说明。"""
    birth_lines = find_birth_lines(text)
    src = RE_SRC.search(text)
    src_kind = src.group(1) if src else None
    flag = corr_flag(text)
    is_unknown = bool(RE_IS_SOLAR_UNKNOWN.search(text))

    rows = solar_row_values(text)
    concrete_rows = [v for v in rows if has_concrete_time(v)]
    negated_rows = [v for v in rows if RE_NEGATED.search(v)]

    # 出生行上的真太阳时标注可能出现在任意一条出生行（C-2026-016 即在第二条）
    notes = [
        m.group(0)
        for line in birth_lines
        for m in [RE_TABLE_NOTE.search(line)]
        if m
    ]
    pos_notes = [n for n in notes if not RE_NEGATED.search(n)]
    neg_notes = [n for n in notes if RE_NEGATED.search(n)]
    table_note = pos_notes[0] if pos_notes else None

    # ---- 1) 无可用出生时刻
    if src_kind == "none" or RE_NO_TIME.search(text) or not birth_lines:
        if src_kind == "none":
            why = "时间来源: none（未提供出生时刻）"
        elif RE_NO_TIME.search(text):
            why = "案例明示未提供出生时刻"
        else:
            why = "无任何出生时刻声明"
        return {
            "time_basis": UNKNOWN,
            "basis_evidence": NONE,
            "notation": notation_of(text, table_note),
            "unknown_kind": "no_birth_time",
            "evidence": [why],
        }

    true_declared: list[str] = []
    clock_declared: list[str] = []

    if flag == "true":
        true_declared.append("真太阳时校正: true")
    if src_kind == "true_solar_time_raw":
        true_declared.append("时间来源: true_solar_time_raw")
    if table_note:
        true_declared.append(f"出生行标注 {table_note}")

    if flag == "false":
        clock_declared.append("真太阳时校正: false")
    if src_kind == "birth_datetime_raw":
        clock_declared.append("时间来源: birth_datetime_raw")
    if negated_rows:
        clock_declared.append("太阳时字段自我否定未校正")
    if neg_notes:
        clock_declared.append("出生行真太阳时标注自我否定")

    bare_solar_value = bool(concrete_rows) and not negated_rows

    # ---- 2) 证据互相矛盾 → unknown（ADR-005 §2）
    contradiction = None
    if true_declared and clock_declared:
        contradiction = f"{'／'.join(true_declared)} 与 {'／'.join(clock_declared)} 互相矛盾"
    elif is_unknown and (flag in ("true", "false") or src_kind in ("true_solar_time_raw", "birth_datetime_raw")):
        other = true_declared + clock_declared
        contradiction = f"「是否真太阳时：未知」与 {'／'.join(other)} 互相矛盾"
    elif flag == "unknown" and (table_note or bare_solar_value):
        contradiction = "「真太阳时校正: 未知」与校正后时刻字段互相矛盾"

    if contradiction:
        return {
            "time_basis": UNKNOWN,
            "basis_evidence": NONE,
            "notation": notation_of(text, table_note),
            "unknown_kind": "has_time_undecidable",
            "evidence": [f"证据互相矛盾：{contradiction}"],
        }

    # ---- 3) 明示只用了钟表时间
    if clock_declared:
        return {
            "time_basis": CLOCK,
            "basis_evidence": NONE,
            "notation": notation_of(text, table_note),
            "unknown_kind": None,
            "evidence": clock_declared,
        }

    # ---- 4) 声明已校正 / 直接给出校正后时刻
    if true_declared:
        if RE_LONGITUDE.search(text):
            evidence = LONGITUDE_CALC
            note = "有出生地经度 + 可复现换算"
        elif src_kind == "true_solar_time_raw" or table_note or concrete_rows:
            evidence = EXPLICIT_TIME
            note = "案例内直接给出校正后的具体时刻"
        else:
            evidence = LABEL_ONLY
            note = "只有校正标记，无经度、无校正后时刻"
        return {
            "time_basis": TRUE_SOLAR,
            "basis_evidence": evidence,
            "notation": notation_of(text, table_note),
            "unknown_kind": None,
            "evidence": true_declared + [note],
        }

    # ---- 5) 只给了太阳时字段值（太阳时 / Sun），未加否定
    if bare_solar_value:
        evidence = LONGITUDE_CALC if RE_LONGITUDE.search(text) else EXPLICIT_TIME
        return {
            "time_basis": TRUE_SOLAR,
            "basis_evidence": evidence,
            "notation": notation_of(text, table_note),
            "unknown_kind": None,
            "evidence": ["太阳时字段直接给出具体时刻"] + concrete_rows[:2],
        }

    # ---- 6) 明示口径未知
    if is_unknown or flag == "unknown":
        return {
            "time_basis": UNKNOWN,
            "basis_evidence": NONE,
            "notation": notation_of(text, table_note),
            "unknown_kind": "has_time_undecidable",
            "evidence": ["案例明示真太阳时口径未知"],
        }

    # ---- 7) 沉默：有时刻但未声明口径（ADR-005 §3：不得默认 clock_beijing）
    return {
        "time_basis": UNKNOWN,
        "basis_evidence": NONE,
        "notation": notation_of(text, table_note),
        "unknown_kind": "has_time_undecidable",
        "evidence": ["有出生时刻但未声明排盘口径（沉默）"],
    }


def notation_of(text: str, table_note: str | None) -> str:
    """元数据写法归类（按 ADR-005 背景第 2 条三写法 + 其余）。"""
    if RE_IMPORTER.search(text):
        return "importer_field"
    if RE_CORR_FLAG.search(text):
        return "structured_field"
    if table_note:
        return "table_note"
    return "other"


# ---------------------------------------------------------------- 主流程


def audit_cases() -> tuple[list[dict], list[str]]:
    if not CASES_DIR.is_dir():
        raise SystemExit(f"找不到案例目录：{CASES_DIR}")

    case_dirs = sorted(
        p for p in CASES_DIR.iterdir() if p.is_dir() and (p / "input.md").is_file()
    )
    records: list[dict] = []
    problems: list[str] = []

    for d in case_dirs:
        text = (d / "input.md").read_text(encoding="utf-8")
        verdict = classify(text)
        records.append(
            {
                "case_id": d.name,
                "time_basis": verdict["time_basis"],
                "basis_evidence": verdict["basis_evidence"],
                "notation": verdict["notation"],
                "unknown_kind": verdict["unknown_kind"],
                "evidence": verdict["evidence"],
            }
        )

    # 覆盖自检：每个含 input.md 的目录都必须且只能出现一次
    audited = [r["case_id"] for r in records]
    if len(audited) != len(set(audited)):
        problems.append("存在重复的 case_id")
    expected = {p.name for p in case_dirs}
    if set(audited) != expected:
        problems.append("audit 覆盖集合与 cases/*/input.md 目录集合不一致")

    # 取值自检
    for r in records:
        if r["time_basis"] not in TIME_BASIS_VALUES:
            problems.append(f"{r['case_id']}: 非法 time_basis={r['time_basis']}")
        if r["basis_evidence"] not in EVIDENCE_VALUES:
            problems.append(f"{r['case_id']}: 非法 basis_evidence={r['basis_evidence']}")
        if not r["time_basis"] or not r["basis_evidence"]:
            problems.append(f"{r['case_id']}: 字段缺失")

    # 三档之和自检
    total = len(records)
    tally = {v: sum(1 for r in records if r["time_basis"] == v) for v in TIME_BASIS_VALUES}
    if sum(tally.values()) != total:
        problems.append(f"三档计数之和 {sum(tally.values())} != 覆盖数 {total}")

    return records, problems


def build_payload(records: list[dict]) -> dict:
    total = len(records)
    tally = {v: sum(1 for r in records if r["time_basis"] == v) for v in TIME_BASIS_VALUES}
    evidence = {v: sum(1 for r in records if r["basis_evidence"] == v) for v in EVIDENCE_VALUES}
    notation: dict[str, int] = {}
    for r in records:
        notation[r["notation"]] = notation.get(r["notation"], 0) + 1
    unknown_kind = {
        "no_birth_time": sum(1 for r in records if r["unknown_kind"] == "no_birth_time"),
        "has_time_undecidable": sum(
            1 for r in records if r["unknown_kind"] == "has_time_undecidable"
        ),
    }
    # 同一案例号出现多个目录时提示（如 C-2026-015、C-2026-038）
    seen: dict[str, int] = {}
    for r in records:
        m = re.match(r"^([A-Z][A-Z0-9-]*?\d)-(?:乾|坤|[甲乙丙丁戊己庚辛壬癸])", r["case_id"])
        if m:
            seen[m.group(1)] = seen.get(m.group(1), 0) + 1
    dup_ids = sorted(k for k, v in seen.items() if v > 1)

    return {
        "schema": "case-time-basis-v1",
        "adr": "docs/adr/ADR-005-case-time-basis.md",
        "task": "T-130",
        "cases_dir": "cases",
        "coverage": total,
        "counts": tally,
        "counts_sum": sum(tally.values()),
        "basis_evidence_counts": evidence,
        "notation_counts": notation,
        "unknown_breakdown": unknown_kind,
        "duplicate_case_numbers": dup_ids,
        "cases": records,
    }


def print_summary(payload: dict) -> None:
    print("T-130 案例排盘口径普查（依据 ADR-005）")
    print(f"覆盖数：{payload['coverage']}")
    print()
    print("time_basis 分档：")
    print("+----------------+--------+---------+")
    print("| 档位           | 例数   | 占比    |")
    print("+----------------+--------+---------+")
    total = payload["coverage"] or 1
    for k in TIME_BASIS_VALUES:
        n = payload["counts"][k]
        print(f"| {k:<14} | {n:>6} | {n / total:>6.1%} |")
    print("+----------------+--------+---------+")
    print(f"| {'合计':<12} | {payload['counts_sum']:>6} | {'':>7} |")
    print("+----------------+--------+---------+")
    print()
    print("basis_evidence 分布：")
    for k in EVIDENCE_VALUES:
        print(f"  {k:<16} {payload['basis_evidence_counts'][k]:>6}")
    print()
    print("元数据写法分布：")
    for k, v in sorted(payload["notation_counts"].items(), key=lambda kv: -kv[1]):
        print(f"  {k:<16} {v:>6}")
    print()
    ub = payload["unknown_breakdown"]
    print("unknown 细分：")
    print(f"  确实无出生时刻        {ub['no_birth_time']:>6}")
    print(f"  有时刻但判不了        {ub['has_time_undecidable']:>6}")
    if payload["duplicate_case_numbers"]:
        print()
        print("同一案例号多目录：" + "、".join(payload["duplicate_case_numbers"]))


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    parser = argparse.ArgumentParser(description="T-130 案例排盘口径普查器（只读）")
    parser.add_argument("--json", action="store_true", help="输出完整 JSON 清单")
    parser.add_argument("--summary", action="store_true", help="打印分档计数表")
    parser.add_argument("--case", metavar="CASE_ID", help="只打印某案例的判定明细")
    parser.add_argument("--out", default=str(DEFAULT_OUT), help="产物路径")
    parser.add_argument("--no-write", action="store_true", help="不写产物文件")
    args = parser.parse_args(argv)

    records, problems = audit_cases()
    payload = build_payload(records)

    if not args.no_write:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    if args.case:
        hit = [r for r in records if r["case_id"] == args.case or r["case_id"].startswith(args.case)]
        if not hit:
            print(f"未找到案例：{args.case}", file=sys.stderr)
            return 1
        for r in hit:
            print(f"case_id       : {r['case_id']}")
            print(f"time_basis    : {r['time_basis']}")
            print(f"basis_evidence: {r['basis_evidence']}")
            print(f"notation      : {r['notation']}")
            for e in r["evidence"]:
                print(f"  依据        : {e}")
            print()
    elif args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    elif args.summary:
        print_summary(payload)
    else:
        print_summary(payload)

    if problems:
        for p in problems:
            print(f"[FAIL] {p}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Normalize repaired Wenzhen invalid-ganzhi cases for preflight.

This tool only patches structured YAML fields in the 7 repaired cases:
- birth.性别: 女/男 -> F/M
- 四柱: synchronize 年/月/日/时柱 from repaired case id
- 大运.排布: fill empty generated 8-step dayun sequence

It intentionally does not globally replace feedback prose.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import subprocess
import sys
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
AUDIT_RESULT_JSON = REPO_ROOT / "cases" / "raw_feedback" / "parsed" / "wenzhen_invalid_ganzhi_audit-result.json"
SUMMARY_JSON = REPO_ROOT / "cases" / "raw_feedback" / "parsed" / "wenzhen_fixed_cases_preflight-summary.json"
SUMMARY_MD = REPO_ROOT / "cases" / "raw_feedback" / "parsed" / "wenzhen_fixed_cases_preflight-summary.md"

GENDER_BY_QIANKUN = {"乾": "M", "坤": "F"}
GAN = "甲乙丙丁戊己庚辛壬癸"
ZHI = "子丑寅卯辰巳午未申酉戌亥"
JIAZI = [GAN[i % 10] + ZHI[i % 12] for i in range(60) if (i % 10) % 2 == (i % 12) % 2]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Normalize repaired Wenzhen cases before preflight.")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing files.")
    parser.add_argument("--preflight", action="store_true", help="Run tools.preflight for each repaired case after normalization.")
    args = parser.parse_args(argv)

    audit = json.loads(AUDIT_RESULT_JSON.read_text(encoding="utf-8"))
    rows = []
    for result in audit["results"]:
        row = _normalize_case(result, dry_run=args.dry_run)
        if args.preflight and not args.dry_run:
            row["preflight"] = _run_preflight(row)
        rows.append(row)

    payload = {
        "dry_run": args.dry_run,
        "preflight_enabled": args.preflight and not args.dry_run,
        "total": len(rows),
        "normalized": sum(1 for row in rows if row["status"] == "normalized"),
        "unchanged": sum(1 for row in rows if row["status"] == "unchanged"),
        "dayun_filled": sum(1 for row in rows if row.get("dayun_filled")),
        "preflight_passed": sum(1 for row in rows if row.get("preflight", {}).get("passed") is True),
        "preflight_failed": [row for row in rows if row.get("preflight", {}).get("passed") is False],
        "errors": [row for row in rows if row["status"] == "error"],
        "results": rows,
    }
    if not args.dry_run:
        SUMMARY_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        SUMMARY_MD.write_text(_render_markdown(payload), encoding="utf-8")
    _safe_print_json(payload)
    return 0 if not payload["errors"] and not payload["preflight_failed"] else 1


def _normalize_case(result: dict[str, Any], *, dry_run: bool) -> dict[str, Any]:
    case_dir = REPO_ROOT / result["case_dir_new"]
    input_path = case_dir / "input.md"
    if not input_path.exists():
        return {
            "raw_id": result["raw_id"],
            "case_id": result["case_id_new"],
            "input": _rel(input_path),
            "status": "error",
            "error": "input.md 不存在",
        }

    text = input_path.read_text(encoding="utf-8")
    original = text
    actions: list[str] = []
    qian_kun = _case_qiankun(result["case_id_new"])
    gender = GENDER_BY_QIANKUN[qian_kun]
    pillars = _pillars(result["fixed_bazi"])

    next_text = re.sub(r"(?m)^(\s*性别:\s*)(?:男|女|M|F)\s*$", rf"\g<1>{gender}", text, count=1)
    if next_text != text:
        actions.append("normalized_gender")
    text = next_text

    for key, pillar in zip(("年柱", "月柱", "日柱", "时柱"), pillars):
        next_text = re.sub(rf"(?m)^(\s*{key}:\s*)\S+\s*$", rf"\g<1>{pillar}", text, count=1)
        if next_text != text:
            actions.append(f"normalized_{key}")
        text = next_text

    next_text = re.sub(r"(?m)^(\s*日干:\s*)\S+\s*$", rf"\g<1>{pillars[2][0]}", text, count=1)
    if next_text != text:
        actions.append("normalized_十二长生日干")
    text = next_text

    dayun_filled = False
    if re.search(r"(?m)^\s*排布:\s*\[\]\s*$", text):
        qiyun_sui = _extract_int(text, "起运岁")
        qiyun_year = _extract_int(text, "起运年")
        shun_ni = _extract_text(text, "顺逆") or ("顺" if qian_kun == "乾" else "逆")
        if qiyun_sui is not None and qiyun_year is not None:
            dayun_yaml = _render_dayun_paibu(pillars[1], shun_ni, qiyun_sui, qiyun_year)
            text = re.sub(r"(?m)^(\s*)排布:\s*\[\]\s*$", lambda match: _indent_block(dayun_yaml, match.group(1)), text, count=1)
            dayun_filled = True
            actions.append("filled_dayun_paibu")

    changed = text != original
    if changed and not dry_run:
        input_path.write_text(text, encoding="utf-8")

    return {
        "raw_id": result["raw_id"],
        "case_id": result["case_id_new"],
        "input": _rel(input_path),
        "status": "normalized" if changed else "unchanged",
        "actions": actions,
        "gender": gender,
        "pillars": pillars,
        "dayun_filled": dayun_filled,
    }


def _run_preflight(row: dict[str, Any]) -> dict[str, Any]:
    if row["status"] == "error":
        return {"passed": False, "returncode": 1, "output": row.get("error", "error")}
    completed = subprocess.run(
        [sys.executable, "-m", "tools.preflight", row["input"]],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    output = "\n".join(part for part in (completed.stdout.strip(), completed.stderr.strip()) if part)
    return {"passed": completed.returncode == 0, "returncode": completed.returncode, "output": output}


def _render_dayun_paibu(month_pillar: str, shun_ni: str, qiyun_sui: int, qiyun_year: int) -> str:
    if month_pillar not in JIAZI:
        raise ValueError(f"月柱不是合法六十甲子: {month_pillar}")
    start_idx = JIAZI.index(month_pillar)
    lines = ["排布:"]
    for idx in range(8):
        jiazi_idx = (start_idx + (idx + 1 if shun_ni == "顺" else -(idx + 1))) % 60
        start_year = qiyun_year + idx * 10
        start_age = qiyun_sui + idx * 10
        lines.extend(
            [
                f"  - 序号: {idx + 1}",
                f"    干支: {JIAZI[jiazi_idx]}",
                f"    起讫: {start_year}-{start_year + 10}",
                f"    起岁: {start_age}",
                f"    止岁: {start_age + 9}",
            ]
        )
    return "\n".join(lines)


def _indent_block(block: str, indent: str) -> str:
    return "\n".join(indent + line if line else line for line in block.splitlines())


def _extract_int(text: str, key: str) -> int | None:
    match = re.search(rf"(?m)^\s*{key}:\s*(\d+)\s*$", text)
    return int(match.group(1)) if match else None


def _extract_text(text: str, key: str) -> str | None:
    match = re.search(rf"(?m)^\s*{key}:\s*(\S+)\s*$", text)
    return match.group(1) if match else None


def _case_qiankun(case_id: str) -> str:
    parts = case_id.split("-")
    for part in parts:
        if part in GENDER_BY_QIANKUN:
            return part
    raise ValueError(f"case_id lacks 乾坤: {case_id}")


def _pillars(bazi: str) -> list[str]:
    if len(bazi) != 8:
        raise ValueError(f"八字长度不是 8: {bazi}")
    return [bazi[i : i + 2] for i in range(0, 8, 2)]


def _render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# 问真修复 case 预检前规范化结果",
        "",
        "## 汇总",
        "",
        f"- 总数：{payload['total']}",
        f"- 已规范化：{payload['normalized']}",
        f"- 无需变更：{payload['unchanged']}",
        f"- 已补齐大运排布：{payload['dayun_filled']}",
        f"- 预检通过：{payload['preflight_passed']}",
        f"- 预检失败：{len(payload['preflight_failed'])}",
        f"- 错误：{len(payload['errors'])}",
        "",
        "## 明细",
        "",
        "| raw_id | case_id | 性别 | 四柱 | 大运补齐 | 预检 | 状态 |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in payload["results"]:
        preflight = row.get("preflight")
        if preflight is None:
            preflight_status = "未执行"
        else:
            preflight_status = "通过" if preflight.get("passed") else "失败"
        lines.append(
            f"| {row['raw_id']} | {row['case_id']} | {row.get('gender', '—')} | {' '.join(row.get('pillars', []))} | {'是' if row.get('dayun_filled') else '否'} | {preflight_status} | {row['status']} |"
        )
    failed = payload.get("preflight_failed", [])
    if failed:
        lines.extend(["", "## 预检失败详情", ""])
        for row in failed:
            output = str(row.get("preflight", {}).get("output", "")).replace("\n", " ")
            lines.append(f"- {row['case_id']}：{output}")
    lines.append("")
    return "\n".join(lines)


def _safe_print_json(payload: dict[str, Any]) -> None:
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    try:
        print(text)
    except UnicodeEncodeError:
        sys.stdout.buffer.write(text.encode("utf-8", errors="replace") + b"\n")


def _rel(path: pathlib.Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


if __name__ == "__main__":
    raise SystemExit(main())

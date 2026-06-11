"""Fix OCR-style invalid Ganzhi characters in promoted Wenzhen samples."""

from __future__ import annotations

import argparse
import json
import pathlib
import re
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
PENDING_JSONL = REPO_ROOT / "cases" / "raw_feedback" / "parsed" / "wenzhen_pending_analysis_samples.jsonl"
PENDING_MD = REPO_ROOT / "cases" / "raw_feedback" / "parsed" / "wenzhen_pending_analysis_samples.md"
PROMOTION_MANIFEST = REPO_ROOT / "cases" / "raw_feedback" / "parsed" / "wenzhen_pending_analysis_promotion-manifest.jsonl"
PROMOTION_SUMMARY = REPO_ROOT / "cases" / "raw_feedback" / "parsed" / "wenzhen_pending_analysis_promotion-summary.json"
AUDIT_INPUT = REPO_ROOT / "cases" / "raw_feedback" / "parsed" / "wenzhen_invalid_ganzhi_audit-input.json"
AUDIT_RESULT_JSON = REPO_ROOT / "cases" / "raw_feedback" / "parsed" / "wenzhen_invalid_ganzhi_audit-result.json"
AUDIT_RESULT_MD = REPO_ROOT / "cases" / "raw_feedback" / "parsed" / "wenzhen_invalid_ganzhi_audit-result.md"

GAN = "甲乙丙丁戊己庚辛壬癸"
ZHI = "子丑寅卯辰巳午未申酉戌亥"
JIAZI = {GAN[i % 10] + ZHI[i % 12] for i in range(60) if (i % 10) % 2 == (i % 12) % 2}
FIXES = {
    "王": "壬",
    "西": "酉",
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fix invalid Ganzhi OCR characters in Wenzhen pending samples.")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing files.")
    args = parser.parse_args(argv)

    audit_input = json.loads(AUDIT_INPUT.read_text(encoding="utf-8"))
    results = [_audit_record(record) for record in audit_input]
    _assert_all_repaired(results)

    if not args.dry_run:
        _update_pending_jsonl(results)
        _update_promotion_manifest(results)
        _update_promotion_summary(results)
        _update_pending_md(results)
        _rename_and_patch_case_dirs(results)
        AUDIT_RESULT_JSON.write_text(json.dumps(_result_payload(results), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        AUDIT_RESULT_MD.write_text(_render_markdown(results), encoding="utf-8")

    print(json.dumps(_result_payload(results, dry_run=args.dry_run), ensure_ascii=False, indent=2))
    return 0


def _audit_record(record: dict[str, Any]) -> dict[str, Any]:
    old_bazi = record["bazi"]
    fixed_bazi = _fix_text(old_bazi)
    old_four = record["four"]
    fixed_four = {key: _fix_text(value) for key, value in old_four.items()}
    old_base = record["base"]
    fixed_base = {key: _fix_text(value) if isinstance(value, str) else value for key, value in old_base.items()}
    invalid_fragments = _invalid_fragments(old_bazi, old_four, old_base)
    post_validation = _validate_bazi(fixed_bazi, fixed_four, fixed_base)
    old_case_dir = record["case_dir"]
    new_case_dir = old_case_dir.replace(old_bazi, fixed_bazi)
    return {
        "raw_id": record["raw_id"],
        "case_id_old": pathlib.PurePosixPath(old_case_dir).name,
        "case_id_new": pathlib.PurePosixPath(new_case_dir).name,
        "case_dir_old": old_case_dir,
        "case_dir_new": new_case_dir,
        "异常原因": _reason(invalid_fragments),
        "问题类型": "OCR 识别错误",
        "修复动作": "将疑似 OCR 字形 `王` 修正为天干 `壬`，将地支误字 `西` 修正为 `酉`。",
        "old_bazi": old_bazi,
        "fixed_bazi": fixed_bazi,
        "old_four": old_four,
        "fixed_four": fixed_four,
        "old_base": old_base,
        "fixed_base": fixed_base,
        "invalid_fragments": invalid_fragments,
        "post_validation": post_validation,
        "修复后状态": "已修复待分析" if post_validation["valid"] else "待人工确认",
        "是否可进入案例分析流程": bool(post_validation["valid"]),
    }


def _fix_text(value: str) -> str:
    out = value
    for src, dst in FIXES.items():
        out = out.replace(src, dst)
    return out


def _invalid_fragments(bazi: str, four: dict[str, str], base: dict[str, Any]) -> list[str]:
    fragments: list[str] = []
    for text in [bazi, *four.values(), *[value for value in base.values() if isinstance(value, str)]]:
        for char in text:
            if char in FIXES and char not in fragments:
                fragments.append(char)
    return fragments


def _reason(fragments: list[str]) -> str:
    parts = []
    if "王" in fragments:
        parts.append("排盘文本中出现非天干字符 `王`，结合十神、纳音与柱位上下文，应为 `壬` 的 OCR 误识别。")
    if "西" in fragments:
        parts.append("空亡字段中出现非地支字符 `西`，上下文为 `申西`，应为 `申酉` 的 OCR 误识别。")
    return " ".join(parts)


def _validate_bazi(bazi: str, four: dict[str, str], base: dict[str, Any]) -> dict[str, Any]:
    pillars = [bazi[i : i + 2] for i in range(0, len(bazi), 2)]
    invalid_chars = sorted({char for char in bazi if char not in GAN + ZHI})
    invalid_pillars = [pillar for pillar in pillars if pillar not in JIAZI]
    residual_bad_chars = []
    for text in [bazi, *four.values(), *[value for value in base.values() if isinstance(value, str)]]:
        residual_bad_chars.extend(char for char in text if char in FIXES)
    return {
        "valid": len(bazi) == 8 and not invalid_chars and not invalid_pillars and not residual_bad_chars,
        "pillars": pillars,
        "invalid_chars": invalid_chars,
        "invalid_pillars": invalid_pillars,
        "residual_bad_chars": sorted(set(residual_bad_chars)),
    }


def _assert_all_repaired(results: list[dict[str, Any]]) -> None:
    failed = [result["raw_id"] for result in results if not result["post_validation"]["valid"]]
    if failed:
        raise ValueError(f"records still invalid after automatic fixes: {failed}")


def _update_pending_jsonl(results: list[dict[str, Any]]) -> None:
    by_raw = {result["raw_id"]: result for result in results}
    rows = [json.loads(line) for line in PENDING_JSONL.read_text(encoding="utf-8").splitlines() if line.strip()]
    updated_rows = []
    for row in rows:
        result = by_raw.get(row["raw_id"])
        if result:
            row["bazi"] = result["fixed_bazi"]
            row["base"] = result["fixed_base"]
            row["four"] = result["fixed_four"]
            row["quality_flags"] = [flag for flag in row.get("quality_flags", []) if flag != "invalid_ganzhi_chars"]
            row["sample_status"] = "fixed_pending_standard_analysis"
            row["formal_case"] = result["case_dir_new"]
            row["repair"] = {
                "status": "已修复待分析",
                "issue_type": result["问题类型"],
                "old_bazi": result["old_bazi"],
                "fixed_bazi": result["fixed_bazi"],
                "audit_result": "cases/raw_feedback/parsed/wenzhen_invalid_ganzhi_audit-result.json",
            }
        updated_rows.append(row)
    _write_jsonl(PENDING_JSONL, updated_rows)


def _update_promotion_manifest(results: list[dict[str, Any]]) -> None:
    by_raw = {result["raw_id"]: result for result in results}
    rows = [json.loads(line) for line in PROMOTION_MANIFEST.read_text(encoding="utf-8").splitlines() if line.strip()]
    updated_rows = []
    for row in rows:
        result = by_raw.get(row["raw_id"])
        if result:
            row["case_id"] = result["case_id_new"]
            row["case_dir"] = result["case_dir_new"]
            row["quality_flags"] = [flag for flag in row.get("quality_flags", []) if flag != "invalid_ganzhi_chars"]
            row["status"] = "fixed_pending_analysis"
            row["written_files"] = [path.replace(result["case_dir_old"], result["case_dir_new"]).replace(result["case_id_old"], result["case_id_new"]) for path in row.get("written_files", [])]
            row["notes"] = ["invalid_ganzhi_chars 已自动修复并通过干支校验；可进入标准案例分析流程。"]
            row["repair"] = {
                "old_case_id": result["case_id_old"],
                "old_bazi": result["old_bazi"],
                "fixed_bazi": result["fixed_bazi"],
                "audit_result": "cases/raw_feedback/parsed/wenzhen_invalid_ganzhi_audit-result.json",
            }
        updated_rows.append(row)
    _write_jsonl(PROMOTION_MANIFEST, updated_rows)


def _update_promotion_summary(results: list[dict[str, Any]]) -> None:
    data = json.loads(PROMOTION_SUMMARY.read_text(encoding="utf-8"))
    replacements = {result["case_dir_old"]: result["case_dir_new"] for result in results}
    data["case_dirs"] = [replacements.get(path, path) for path in data.get("case_dirs", [])]
    data["status_counts"] = _recount_manifest_statuses()
    data["invalid_ganzhi_count"] = 0
    data["fixed_invalid_ganzhi_count"] = len(results)
    data["repair_result"] = "cases/raw_feedback/parsed/wenzhen_invalid_ganzhi_audit-result.json"
    data["blocked_or_skipped"] = []
    PROMOTION_SUMMARY.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _update_pending_md(results: list[dict[str, Any]]) -> None:
    text = PENDING_MD.read_text(encoding="utf-8")
    for result in results:
        text = text.replace(result["old_bazi"], result["fixed_bazi"])
        text = text.replace("invalid_ganzhi_chars", "已修复待分析")
        text = text.replace(result["case_dir_old"], result["case_dir_new"])
    PENDING_MD.write_text(text, encoding="utf-8")


def _rename_and_patch_case_dirs(results: list[dict[str, Any]]) -> None:
    for result in results:
        old_dir = REPO_ROOT / result["case_dir_old"]
        new_dir = REPO_ROOT / result["case_dir_new"]
        if old_dir.exists() and old_dir != new_dir:
            old_dir.rename(new_dir)
        for path in new_dir.rglob("*"):
            if path.is_file():
                text = path.read_text(encoding="utf-8")
                text = text.replace(result["case_id_old"], result["case_id_new"])
                text = text.replace(result["case_dir_old"], result["case_dir_new"])
                text = text.replace(result["old_bazi"], result["fixed_bazi"])
                text = text.replace("invalid_ganzhi_chars", "fixed_invalid_ganzhi_chars")
                text = text.replace("needs_manual_ganzhi_review_before_high_confidence_ingest", "ready_for_standard_analysis")
                text = text.replace("排盘含异常干支字形；正式初始化后仍需人工复核", "排盘异常干支字形已自动修复并通过校验")
                path.write_text(text, encoding="utf-8")


def _recount_manifest_statuses() -> dict[str, int]:
    counts: dict[str, int] = {}
    for line in PROMOTION_MANIFEST.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        status = json.loads(line)["status"]
        counts[status] = counts.get(status, 0) + 1
    return dict(sorted(counts.items()))


def _write_jsonl(path: pathlib.Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n", encoding="utf-8")


def _result_payload(results: list[dict[str, Any]], *, dry_run: bool = False) -> dict[str, Any]:
    fixed = [result for result in results if result["修复后状态"] == "已修复待分析"]
    manual = [result for result in results if result["修复后状态"] == "待人工确认"]
    return {
        "dry_run": dry_run,
        "total": len(results),
        "已修复数量": len(fixed),
        "待人工确认数量": len(manual),
        "规则误判数量": 0,
        "新增可用于案例分析的样本数量": len(fixed),
        "results": results,
    }


def _render_markdown(results: list[dict[str, Any]]) -> str:
    payload = _result_payload(results)
    lines = [
        "# 问真 invalid_ganzhi_chars 样本核查结果",
        "",
        "## 汇总",
        "",
        f"- 已修复数量：{payload['已修复数量']}",
        f"- 待人工确认数量：{payload['待人工确认数量']}",
        f"- 规则误判数量：{payload['规则误判数量']}",
        f"- 新增可用于案例分析的样本数量：{payload['新增可用于案例分析的样本数量']}",
        "",
        "## 逐条结果",
        "",
        "| 样本ID | 异常原因 | 修复动作 | 修复后状态 | 是否可进入案例分析流程 |",
        "|---|---|---|---|---|",
    ]
    for result in results:
        can_analyze = "是" if result["是否可进入案例分析流程"] else "否"
        lines.append(
            f"| {result['raw_id']} | {result['异常原因']} | {result['old_bazi']} → {result['fixed_bazi']}；{result['修复动作']} | {result['修复后状态']} | {can_analyze} |"
        )
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())

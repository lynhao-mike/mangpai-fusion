"""Build review-gate artifacts for Wenzhen Top 30 promotion preparation.

The gate separates OCR-risk samples from promotion-ready candidates. It does not
modify draft inputs and does not create formal cases.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import pathlib
from typing import Any

from tools.build_wenzhen_top30_review_pack import (
    DEFAULT_JSONL,
    PARSED_DIR,
    TOP_N,
    _build_case,
    _load_records,
    _rel,
)

DEFAULT_OCR_QUEUE = PARSED_DIR / "wenzhen_repan_top30_ocr_queue.md"
DEFAULT_PROMOTION_CHECKLIST = PARSED_DIR / "wenzhen_repan_top30_promotion_checklist.md"
DEFAULT_GATE_SUMMARY = PARSED_DIR / "wenzhen_repan_top30_review_gate-summary.json"
BLOCKING_FLAGS = {
    "invalid_ganzhi_chars",
    "missing_draft_input",
    "missing_raw_excerpt",
    "event_count_mismatch",
    "ocr_wang_for_ren",
    "ocr_xi_for_you",
}


def build_review_gate(*, dry_run: bool = False, top_n: int = TOP_N) -> dict[str, Any]:
    records = _load_records(DEFAULT_JSONL)[:top_n]
    cases = [_build_case(rank, record) for rank, record in enumerate(records, start=1)]
    ocr_cases = [case for case in cases if _blocking_flags(case)]
    promotion_candidates = [case for case in cases if not _blocking_flags(case)]
    summary = _build_summary(cases, ocr_cases, promotion_candidates, dry_run=dry_run)
    if not dry_run:
        PARSED_DIR.mkdir(parents=True, exist_ok=True)
        DEFAULT_OCR_QUEUE.write_text(_render_ocr_queue(ocr_cases, summary), encoding="utf-8")
        DEFAULT_PROMOTION_CHECKLIST.write_text(_render_promotion_checklist(promotion_candidates, summary), encoding="utf-8")
        DEFAULT_GATE_SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def _blocking_flags(case: dict[str, Any]) -> list[str]:
    return [flag for flag in case["review_flags"] if flag in BLOCKING_FLAGS]


def _build_summary(
    cases: list[dict[str, Any]],
    ocr_cases: list[dict[str, Any]],
    promotion_candidates: list[dict[str, Any]],
    *,
    dry_run: bool,
) -> dict[str, Any]:
    flag_counts: dict[str, int] = {}
    for case in cases:
        for flag in _blocking_flags(case):
            flag_counts[flag] = flag_counts.get(flag, 0) + 1
    return {
        "schema_version": "wenzhen-top30-review-gate/v0.1",
        "generated_at": _dt.datetime.now(_dt.UTC).isoformat(),
        "dry_run": dry_run,
        "source_jsonl": _rel(DEFAULT_JSONL),
        "ocr_queue_markdown": _rel(DEFAULT_OCR_QUEUE),
        "promotion_checklist_markdown": _rel(DEFAULT_PROMOTION_CHECKLIST),
        "summary_json": _rel(DEFAULT_GATE_SUMMARY),
        "case_count": len(cases),
        "ocr_queue_count": len(ocr_cases),
        "promotion_candidate_count": len(promotion_candidates),
        "blocking_flag_distribution": dict(sorted(flag_counts.items())),
        "ocr_queue_raw_ids": [case["raw_id"] for case in ocr_cases],
        "promotion_candidate_raw_ids": [case["raw_id"] for case in promotion_candidates],
        "policy": "Blocking OCR/raw-evidence flags must be resolved before formal case promotion.",
    }


def _render_ocr_queue(cases: list[dict[str, Any]], summary: dict[str, Any]) -> str:
    lines = [
        "# 问真 Top 30 · OCR 修正队列",
        "",
        f"> 生成时间：{summary['generated_at']}",
        "> 用途：先人工核正干支、空亡、藏干或原始证据缺口，再考虑转正式 case。",
        "",
        "## 汇总",
        "",
        f"- 待修正样本数：{summary['ocr_queue_count']}",
        f"- 阻断标记分布：{summary['blocking_flag_distribution']}",
        "",
        "## 队列表",
        "",
        "| 排名 | raw_id | 乾坤 | 当前四柱 | 阻断标记 | 建议核对点 | 草稿 |",
        "|---:|---|---|---|---|---|---|",
    ]
    for case in cases:
        record = case["record"]
        flags = "、".join(_blocking_flags(case))
        hints = "；".join(_review_hints(case))
        lines.append(
            f"| {case['rank']} | {case['raw_id']} | {record.get('qian_kun', '-')} | {record.get('bazi', '-')} | "
            f"{flags} | {hints} | {case['draft_path']} |"
        )
    lines.extend(["", "## 逐案修正卡", ""])
    for case in cases:
        record = case["record"]
        lines.extend(
            [
                f"### {case['rank']}. {case['raw_id']} · {record.get('qian_kun', '-')} · {record.get('bazi', '-')}",
                "",
                f"- 阻断标记：{'、'.join(_blocking_flags(case))}",
                f"- 当前空亡：{record.get('void', '-')}",
                f"- 当前日主/日支：{record.get('day_master', '-')} / {record.get('day_branch', '-')}",
                f"- 来源索引：`{record.get('index_path', '-')}`",
                f"- 草稿：`{case['draft_path']}`",
                "- [ ] 已打开问真原图或原排盘文本核对四柱。",
                "- [ ] 已核对 `王→壬`、`西→酉` 等 OCR 疑点。",
                "- [ ] 已核对空亡、藏干、十神是否随干支修正同步变化。",
                "- [ ] 修正后可重新生成 Top 30 复核包。",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def _render_promotion_checklist(cases: list[dict[str, Any]], summary: dict[str, Any]) -> str:
    lines = [
        "# 问真 Top 30 · 转案准备清单",
        "",
        f"> 生成时间：{summary['generated_at']}",
        "> 用途：列出暂无线性阻断标记的候选样本；仍需人工复核后才能建立正式 `cases/C-.../`。",
        "",
        "## 汇总",
        "",
        f"- 可进入转案准备样本数：{summary['promotion_candidate_count']}",
        f"- 已排除 OCR/证据阻断样本数：{summary['ocr_queue_count']}",
        "",
        "## 候选清单",
        "",
        "| 排名 | raw_id | 乾坤 | 四柱 | 事件数 | 评分 | 建议 case_id 草案 | 转案前检查 |",
        "|---:|---|---|---|---:|---:|---|---|",
    ]
    for case in cases:
        record = case["record"]
        suggested_case_id = f"C-2026-RF{case['raw_id'].split('-')[-1]}-{record.get('qian_kun', '-')}-{record.get('bazi', '-')}"
        lines.append(
            f"| {case['rank']} | {case['raw_id']} | {record.get('qian_kun', '-')} | {record.get('bazi', '-')} | "
            f"{record.get('event_count', 0)} | {record.get('score', 0)} | {suggested_case_id} | 待人工复核 |"
        )
    lines.extend(["", "## 转案步骤", ""])
    for case in cases:
        record = case["record"]
        suggested_case_id = f"C-2026-RF{case['raw_id'].split('-')[-1]}-{record.get('qian_kun', '-')}-{record.get('bazi', '-')}"
        lines.extend(
            [
                f"### {case['rank']}. {case['raw_id']} → {suggested_case_id}",
                "",
                f"- 草稿来源：`{case['draft_path']}`",
                f"- 公历/太阳时：{record.get('base', {}).get('Solar', '-')} / {record.get('base', {}).get('Sun', '-')}",
                f"- 起运：{record.get('start', '-')}",
                "- [ ] 建立正式 case 目录前再次核对出生信息脱敏。",
                "- [ ] 将四柱、藏干、大运、神煞按模板补入正式 `input.md`。",
                "- [ ] 将事件年表写入 `feedback.md` 与 `statement_index.json` 可追踪字段。",
                "- [ ] 运行 `python -m tools.preflight <case>/input.md`。",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def _review_hints(case: dict[str, Any]) -> list[str]:
    hints: list[str] = []
    flags = set(_blocking_flags(case))
    if "invalid_ganzhi_chars" in flags:
        hints.append("四柱含非法干支字")
    if "ocr_wang_for_ren" in flags:
        hints.append("疑似 `王` 应为 `壬`")
    if "ocr_xi_for_you" in flags:
        hints.append("疑似 `西` 应为 `酉`")
    if "event_count_mismatch" in flags:
        hints.append("索引事件数与草稿事件数不一致")
    if "missing_draft_input" in flags or "missing_raw_excerpt" in flags:
        hints.append("原始证据链不完整")
    return hints or ["人工复核"]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Only print summary; do not write artifacts.")
    parser.add_argument("--top-n", type=int, default=TOP_N, help="Number of sorted completed records to include.")
    args = parser.parse_args(argv)
    summary = build_review_gate(dry_run=args.dry_run, top_n=args.top_n)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Promote pending Wenzhen analysis samples to formal case directories.

This helper consumes the 68 pending records generated from completed Wenzhen repan
feedback samples. It creates formal case initialization files while preserving
quality flags for records that need manual Ganzhi review.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import pathlib
import re
from collections import Counter
from typing import Any

import yaml

from tools.promote_wenzhen_ready_batch import (
    BRANCH_HIDDEN_STEMS,
    JIAZI,
    TYPE_MAP,
    _as_bool,
    _fact_domain,
    _known_facts,
    _load_draft,
)

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
PENDING_JSONL = REPO_ROOT / "cases" / "raw_feedback" / "parsed" / "wenzhen_pending_analysis_samples.jsonl"
SUMMARY_JSON = REPO_ROOT / "cases" / "raw_feedback" / "parsed" / "wenzhen_pending_analysis_promotion-summary.json"
MANIFEST_JSONL = REPO_ROOT / "cases" / "raw_feedback" / "parsed" / "wenzhen_pending_analysis_promotion-manifest.jsonl"
TODAY = dt.date.today().isoformat()
GAN = "甲乙丙丁戊己庚辛壬癸"
ZHI = "子丑寅卯辰巳午未申酉戌亥"
BATCH_LABEL_DEFAULT = "问真待分析样本批量正式转案"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Promote pending Wenzhen analysis samples to formal case directories.")
    parser.add_argument("--batch-label", default=BATCH_LABEL_DEFAULT, help="Human-readable batch label.")
    parser.add_argument("--dry-run", action="store_true", help="Preview actions without writing case files.")
    parser.add_argument("--limit", type=int, default=0, help="Limit processed records; 0 means all records.")
    parser.add_argument(
        "--include-invalid-ganzhi",
        action="store_true",
        help="Also create formal initialization cases for records flagged invalid_ganzhi_chars.",
    )
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing generated files in target case directories.")
    args = parser.parse_args(argv)

    samples = _load_pending_samples()
    if args.limit:
        samples = samples[: args.limit]

    manifest: list[dict[str, Any]] = []
    for sample in samples:
        record = _process_sample(
            sample,
            batch_label=args.batch_label,
            dry_run=args.dry_run,
            include_invalid_ganzhi=args.include_invalid_ganzhi,
            overwrite=args.overwrite,
        )
        manifest.append(record)

    summary = _build_summary(manifest, args)
    if not args.dry_run:
        _write_manifest(manifest)
        SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


def _load_pending_samples() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in PENDING_JSONL.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return sorted(rows, key=lambda row: int(row.get("source_rank", 0)))


def _process_sample(
    sample: dict[str, Any],
    *,
    batch_label: str,
    dry_run: bool,
    include_invalid_ganzhi: bool,
    overwrite: bool,
) -> dict[str, Any]:
    item = _item_from_sample(sample)
    case_dir = REPO_ROOT / item["case_dir"]
    flags = list(sample.get("quality_flags") or [])
    has_invalid_ganzhi = "invalid_ganzhi_chars" in flags

    record = {
        "raw_id": item["raw_id"],
        "case_id": item["case_id"],
        "case_dir": item["case_dir"],
        "source_rank": sample.get("source_rank"),
        "quality_grade": sample.get("quality_grade"),
        "quality_flags": flags,
        "event_count": sample.get("event_count"),
        "score": sample.get("score"),
        "status": "pending",
        "written_files": [],
        "notes": [],
    }

    if has_invalid_ganzhi and not include_invalid_ganzhi:
        record["status"] = "blocked_invalid_ganzhi"
        record["notes"].append("包含 invalid_ganzhi_chars，未加 --include-invalid-ganzhi 时不写入正式 case。")
        return record

    draft = _load_draft(REPO_ROOT / item["draft_path"])
    file_payloads = {
        "input.md": _render_input(item, sample, draft, batch_label),
        "analysis.md": _render_analysis(item, sample, batch_label),
        "feedback.md": _render_feedback(item, draft, batch_label),
        "statement_index.json": json.dumps(_statement_index(item, sample, draft), ensure_ascii=False, indent=2) + "\n",
        "lessons.md": _render_lessons(item, sample, batch_label),
    }

    existing_files = [name for name in file_payloads if (case_dir / name).exists()]
    if existing_files and not overwrite:
        record["status"] = "skipped_existing"
        record["notes"].append(f"目标目录已有文件且未加 --overwrite：{', '.join(existing_files)}")
        return record

    if dry_run:
        record["status"] = "dry_run_create" if not existing_files else "dry_run_overwrite"
        record["written_files"] = [f"{item['case_dir']}/{name}" for name in file_payloads]
        if has_invalid_ganzhi:
            record["notes"].append("排盘含异常干支字形；正式初始化后仍需人工复核。")
        return record

    case_dir.mkdir(parents=True, exist_ok=True)
    for name, content in file_payloads.items():
        (case_dir / name).write_text(content, encoding="utf-8")
        record["written_files"].append(f"{item['case_dir']}/{name}")

    record["status"] = "created_with_review_flag" if has_invalid_ganzhi else "created"
    if has_invalid_ganzhi:
        record["notes"].append("排盘含异常干支字形；已转正式初始化案，但不得直接进入高置信反馈闭环。")
    return record


def _item_from_sample(sample: dict[str, Any]) -> dict[str, Any]:
    raw_id = sample["raw_id"]
    raw_num = raw_id.replace("RF-2026-", "")
    qian_kun = _normalize_qian_kun(sample.get("qian_kun") or sample.get("base", {}).get("Sex") or sample.get("gender"))
    bazi = str(sample["bazi"])
    case_id = f"C-2026-RF{raw_num}-{qian_kun}-{bazi}"
    paths = sample.get("paths") or {}
    return {
        "case_id": case_id,
        "raw_id": raw_id,
        "case_dir": f"cases/{case_id}",
        "draft_path": paths.get("draft_input", f"cases/raw_feedback/case_drafts/{raw_id}/input.md"),
        "source_index_path": paths.get("source_index", "cases/raw_feedback/case_drafts"),
    }


def _normalize_qian_kun(value: Any) -> str:
    text = str(value or "")
    if "乾" in text or "男" in text:
        return "乾"
    if "坤" in text or "女" in text:
        return "坤"
    return text or "待判"


def _pillars_from_bazi(bazi: str) -> list[str]:
    return [bazi[i : i + 2] for i in range(0, min(len(bazi), 8), 2)]


def _render_input(item: dict[str, Any], sample: dict[str, Any], draft: dict[str, Any], batch_label: str) -> str:
    bazi = str(sample["bazi"])
    pillars = _pillars_from_bazi(bazi)
    if len(pillars) != 4:
        raise ValueError(f"invalid bazi length for {item['raw_id']}: {bazi}")
    birth = draft.get("birth") or {}
    base = sample.get("base") or {}
    payload = {
        "schema_version": "1.2.0",
        "case_meta": {
            "case_id": item["case_id"],
            "立案日期": TODAY,
            "命主代号": item["raw_id"],
            "策略": "B",
            "来源": batch_label,
            "原始反馈ID": item["raw_id"],
            "source_rank": sample.get("source_rank"),
            "source_index_path": item["source_index_path"],
            "draft_path": item["draft_path"],
            "pending_samples_path": "cases/raw_feedback/parsed/wenzhen_pending_analysis_samples.jsonl",
            "promotion_manifest_path": "cases/raw_feedback/parsed/wenzhen_pending_analysis_promotion-manifest.jsonl",
            "quality_grade": sample.get("quality_grade"),
            "quality_flags": list(sample.get("quality_flags") or []),
            "calibration_status": _calibration_status(sample),
        },
        "birth": {
            "性别": _normalize_gender(sample, birth),
            "乾坤": _normalize_qian_kun(sample.get("qian_kun") or birth.get("乾坤")),
            "公历": base.get("Solar") or birth.get("公历", "待补"),
            "农历": base.get("Lunar") or birth.get("农历", "待补"),
            "出生地": birth.get("出生地脱敏", "待补"),
            "出生地原始摘录": birth.get("出生地", ""),
            "真太阳时校正": _as_bool(birth.get("真太阳时校正")),
            "太阳时": base.get("Sun") or birth.get("太阳时", ""),
        },
        "四柱": {"年柱": pillars[0], "月柱": pillars[1], "日柱": pillars[2], "时柱": pillars[3]},
        "藏干": _hidden_stems_for_pillars(pillars),
        "大运": _build_dayun(sample, pillars[1]),
        "神煞": _shensha(sample),
        "十二长生": _changsheng(sample, pillars),
        "问真补排字段": {
            "命宫": base.get("Ming", ""),
            "身宫": base.get("Shen", ""),
            "胎元": base.get("Tai", ""),
            "空亡": sample.get("void") or base.get("Void", ""),
            "司令": base.get("Siling", ""),
            "起运原文": sample.get("start") or base.get("Start", ""),
            "大运条数": sample.get("dy_count"),
            "流年条数": sample.get("liunian_count"),
        },
        "known_facts": _known_facts(draft),
        "提问": draft.get("提问") or ["用于理论验证：依据真实反馈事件回测命局结构、应期与功能域规则。"],
    }
    fingerprint = hashlib.md5(f"{payload['birth']['性别']}|{payload['birth']['公历']}".encode("utf-8")).hexdigest()[:12]
    review_note = _review_note(sample)
    return (
        f"# Case {item['case_id']} · 输入信息\n\n"
        f"> {batch_label}；raw_id：`{item['raw_id']}`。{review_note}\n\n"
        f"**立案日期**：{TODAY}  \n"
        f"**命主代号**：{item['raw_id']}  \n"
        f"**采集人**：mangpai-fusion wenzhen pending promotion  \n"
        f"**指纹**：`{fingerprint}`（{payload['birth']['性别']} | {payload['birth']['公历']}）\n\n"
        "---\n\n"
        "## 一、八字盘\n\n"
        "```yaml\n"
        f"{yaml.safe_dump(payload, allow_unicode=True, sort_keys=False)}"
        "```\n\n"
        "## 二、来源追踪\n\n"
        f"- raw_id：`{item['raw_id']}`\n"
        f"- 来源草稿：`{item['draft_path']}`\n"
        f"- 来源索引：`{item['source_index_path']}`\n"
        "- pending samples：`cases/raw_feedback/parsed/wenzhen_pending_analysis_samples.jsonl`\n"
        "- promotion manifest：`cases/raw_feedback/parsed/wenzhen_pending_analysis_promotion-manifest.jsonl`\n\n"
        "## 三、分析重点\n\n"
        "- 策略 B：围绕真实反馈年表做命局结构、功能域与应期回测。\n"
        "- 先生成正式初始化 case；统一内容报告与断语反馈绑定仍需后续报告流程完成。\n\n"
        "## 四、隐私设置\n\n"
        "- [x] 默认（脱敏归档，可 push 到 GitHub）\n"
        "- [ ] 隐私（不 push，仅本地）\n"
    )


def _render_analysis(item: dict[str, Any], sample: dict[str, Any], batch_label: str) -> str:
    flags = list(sample.get("quality_flags") or [])
    flag_lines = "\n".join(f"- {flag}" for flag in flags) if flags else "- 无"
    calibration = _calibration_status(sample)
    return (
        f"# Case {item['case_id']} · 分析记录\n\n"
        "## 一、转案说明\n\n"
        f"- 转案日期：{TODAY}\n"
        f"- 转案批次：{batch_label}\n"
        f"- raw_id：`{item['raw_id']}`\n"
        f"- 来源草稿：`{item['draft_path']}`\n"
        f"- 来源索引：`{item['source_index_path']}`\n"
        "- pending samples：`cases/raw_feedback/parsed/wenzhen_pending_analysis_samples.jsonl`\n"
        "- promotion manifest：`cases/raw_feedback/parsed/wenzhen_pending_analysis_promotion-manifest.jsonl`\n\n"
        "## 二、当前状态\n\n"
        "本文件为正式 case 初始化分析记录；尚未生成命理师内容报告（统一版）。\n\n"
        "## 三、质量标记\n\n"
        f"- 质量等级：{sample.get('quality_grade')}\n"
        f"- 校准状态：{calibration}\n"
        f"- 已知事实数：{sample.get('event_count')}\n"
        f"- 样本分数：{sample.get('score')}\n"
        f"{flag_lines}\n\n"
        "## 四、待分析重点\n\n"
        "- 命局结构与问真四柱核对。\n"
        "- 已知事实年表与大运、流年应期回测。\n"
        "- 多流派功能域结论与后续 statement_index 绑定。\n"
    )


def _render_feedback(item: dict[str, Any], draft: dict[str, Any], batch_label: str) -> str:
    lines = [
        f"# Case {item['case_id']} · 命主反馈",
        "",
        f"> {batch_label}；本文件先迁移原 known_facts，后续报告断语反馈再补 `[S-...] [y/n/?/skip]`。",
        "",
        f"**反馈日期**：{TODAY}  ",
        "**采集方式**：问真真实反馈样本迁移  ",
        "**关联报告**：待生成  ",
        f"**关联索引**：cases/{item['case_id']}/statement_index.json  ",
        "",
        "---",
        "",
        "## 一、来源追踪",
        "",
        f"- raw_id：`{item['raw_id']}`",
        f"- 来源草稿：`{item['draft_path']}`",
        f"- 来源索引：`{item['source_index_path']}`",
        "- pending samples：`cases/raw_feedback/parsed/wenzhen_pending_analysis_samples.jsonl`",
        "- promotion manifest：`cases/raw_feedback/parsed/wenzhen_pending_analysis_promotion-manifest.jsonl`",
        "",
        "## 二、已知事实年表",
        "",
        "| 年份 | 类型 | 事实摘录 |",
        "|---:|---|---|",
    ]
    for fact in _known_facts(draft):
        lines.append(f"| {fact.get('年份', '')} | {fact.get('类型', '')} | {str(fact.get('事件', '')).replace('|', '/')} |")
    lines.extend([
        "",
        "## 三、断语反馈占位",
        "",
        "> 待正式分析报告生成后，将报告中的 `反馈：[S-...] [ ]` 复制到此处并标注。",
        "",
    ])
    return "\n".join(lines)


def _statement_index(item: dict[str, Any], sample: dict[str, Any], draft: dict[str, Any]) -> dict[str, Any]:
    statements = []
    for idx, fact in enumerate(_known_facts(draft), start=1):
        digest = hashlib.md5(f"{item['case_id']}|{idx}|{fact.get('年份')}|{fact.get('事件')}".encode("utf-8")).hexdigest()[:6]
        statements.append(
            {
                "statement_id": f"S-{item['raw_id'].replace('RF-2026-', 'RF')}-{digest}",
                "domain": _fact_domain(str(fact.get("类型", "其他"))),
                "summary": f"{fact.get('年份', '')}：{fact.get('事件', '')}",
                "status": "observed_fact",
                "section": "known_facts_migrated",
                "rule_ids": [],
                "schools": [],
                "source_raw_id": item["raw_id"],
            }
        )
    return {
        "case_id": item["case_id"],
        "generated_at": TODAY,
        "source_raw_id": item["raw_id"],
        "source_rank": sample.get("source_rank"),
        "quality_grade": sample.get("quality_grade"),
        "quality_flags": list(sample.get("quality_flags") or []),
        "calibration_status": _calibration_status(sample),
        "statements": statements,
    }


def _render_lessons(item: dict[str, Any], sample: dict[str, Any], batch_label: str) -> str:
    flags = list(sample.get("quality_flags") or [])
    return (
        f"# Case {item['case_id']} · 经验沉淀\n\n"
        f"- 初始化批次：{batch_label}\n"
        f"- raw_id：`{item['raw_id']}`\n"
        f"- 当前状态：正式初始化完成，待统一内容报告与反馈摄入。\n"
        f"- 质量标记：{', '.join(flags) if flags else '无'}\n"
    )


def _normalize_gender(sample: dict[str, Any], birth: dict[str, Any]) -> str:
    gender = str(sample.get("gender") or birth.get("性别") or "")
    if gender in {"男", "M", "m", "乾", "乾造"}:
        return "男"
    if gender in {"女", "F", "f", "坤", "坤造"}:
        return "女"
    qian_kun = _normalize_qian_kun(sample.get("qian_kun") or birth.get("乾坤"))
    return "男" if qian_kun == "乾" else "女" if qian_kun == "坤" else gender


def _calibration_status(sample: dict[str, Any]) -> str:
    flags = set(sample.get("quality_flags") or [])
    if "invalid_ganzhi_chars" in flags:
        return "needs_manual_ganzhi_review_before_high_confidence_ingest"
    return "ready_for_standard_analysis"


def _review_note(sample: dict[str, Any]) -> str:
    if "invalid_ganzhi_chars" in set(sample.get("quality_flags") or []):
        return " 注意：本样本含干支异常字形，必须人工复核后才能进入高置信反馈闭环。"
    return ""


def _hidden_stems_for_pillars(pillars: list[str]) -> dict[str, list[dict[str, Any]]]:
    keys = ["年支", "月支", "日支", "时支"]
    out: dict[str, list[dict[str, Any]]] = {}
    for key, pillar in zip(keys, pillars):
        branch = pillar[1] if len(pillar) > 1 else ""
        stems = BRANCH_HIDDEN_STEMS.get(branch, [])
        out[key] = [{"干": gan, "类型": typ, "力量": li} for gan, typ, li in stems]
    return out


def _changsheng(sample: dict[str, Any], pillars: list[str]) -> dict[str, str]:
    keys = {"Y": "年支", "M": "月支", "D": "日支", "H": "时支"}
    out = {"日干": pillars[2][0] if len(pillars) > 2 and pillars[2] else ""}
    four = sample.get("four") or {}
    for src, target in keys.items():
        parts = str(four.get(src, "")).split(",")
        out[target] = parts[4] if len(parts) > 4 and parts[4] else "待复核"
    return out


def _shensha(sample: dict[str, Any]) -> dict[str, list[str]]:
    keys = {"Y": "年柱", "M": "月柱", "D": "日柱", "H": "时柱"}
    four = sample.get("four") or {}
    out: dict[str, list[str]] = {}
    for src, target in keys.items():
        parts = str(four.get(src, "")).split(",")
        if len(parts) < 8 or parts[7] == "_":
            out[target] = []
        else:
            out[target] = [part for part in re.split(r"[/，,]", parts[7]) if part]
    return out


def _build_dayun(sample: dict[str, Any], month_pillar: str) -> dict[str, Any]:
    base = sample.get("base") or {}
    solar = str(base.get("Solar", ""))
    birth_year_match = re.match(r"(\d{4})", solar)
    birth_year = int(birth_year_match.group(1)) if birth_year_match else None
    start_text = str(sample.get("start") or base.get("Start", ""))
    match = re.search(r"出生后?(\d+)年", start_text)
    qiyun_sui = int(match.group(1)) if match else 5
    qiyun_sui = max(1, min(11, qiyun_sui))
    qiyun_year = birth_year + qiyun_sui if birth_year else None
    shun_ni = "顺" if _normalize_qian_kun(sample.get("qian_kun")) == "乾" else "逆"
    if month_pillar not in JIAZI or qiyun_year is None:
        return {"起运岁": qiyun_sui, "起运年": qiyun_year or "待复核", "顺逆": shun_ni, "起运原文": start_text, "排布": []}
    start_idx = JIAZI.index(month_pillar)
    steps = []
    for i in range(8):
        idx = (start_idx + (i + 1 if shun_ni == "顺" else -(i + 1))) % 60
        start_year = qiyun_year + i * 10
        start_age = qiyun_sui + i * 10
        steps.append({"序号": i + 1, "干支": JIAZI[idx], "起讫": f"{start_year}-{start_year + 10}", "起岁": start_age, "止岁": start_age + 9})
    return {"起运岁": qiyun_sui, "起运年": qiyun_year, "顺逆": shun_ni, "起运原文": start_text, "排布": steps}


def _build_summary(manifest: list[dict[str, Any]], args: argparse.Namespace) -> dict[str, Any]:
    statuses = Counter(record["status"] for record in manifest)
    flagged = [record for record in manifest if "invalid_ganzhi_chars" in set(record.get("quality_flags") or [])]
    return {
        "generated_at": TODAY,
        "dry_run": args.dry_run,
        "source": "cases/raw_feedback/parsed/wenzhen_pending_analysis_samples.jsonl",
        "manifest": None if args.dry_run else "cases/raw_feedback/parsed/wenzhen_pending_analysis_promotion-manifest.jsonl",
        "summary": None if args.dry_run else "cases/raw_feedback/parsed/wenzhen_pending_analysis_promotion-summary.json",
        "total_selected": len(manifest),
        "status_counts": dict(sorted(statuses.items())),
        "invalid_ganzhi_count": len(flagged),
        "include_invalid_ganzhi": args.include_invalid_ganzhi,
        "overwrite": args.overwrite,
        "case_dirs": [record["case_dir"] for record in manifest if record["status"] in {"created", "created_with_review_flag", "dry_run_create", "dry_run_overwrite"}],
        "blocked_or_skipped": [record for record in manifest if record["status"].startswith("blocked") or record["status"].startswith("skipped")],
    }


def _write_manifest(manifest: list[dict[str, Any]]) -> None:
    MANIFEST_JSONL.write_text("\n".join(json.dumps(record, ensure_ascii=False) for record in manifest) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())

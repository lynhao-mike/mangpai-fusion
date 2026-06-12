from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.application.feedback_parser import StatementFeedback, parse_statement_feedback
from tools.feedback_ingest import build_learning_samples

CASES_ROOT = ROOT / "cases"
META_ROOT = ROOT / "META"
PHASE_300_STRATEGY = META_ROOT / "phase-300-voting-strategy.md"
COVERAGE_REPORT = META_ROOT / "historical-statement-record-coverage.md"
RECOVERY_REPORT = META_ROOT / "historical-mapping-recovery-report.md"
LEARNABLE_AUDIT = META_ROOT / "phase-1000-learnable-sample-audit.md"
MIGRATION_LOG = META_ROOT / "historical-statement-record-migration-log.json"
PRODUCT_VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip() if (ROOT / "VERSION").exists() else "unknown"
GENERATED_AT = dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
CANONICAL_RULE_RE = re.compile(r"^(?:DTS|ZP)-PROD-\d{8}-\d{3}$")
BRACKET_RE = re.compile(r"\[\s*(y|n|\?|skip|pending|hit|miss|partial|unknown|命中|未命中|部分命中|待反馈)?\s*\]", re.I)
STMT_BRACKET_RE = re.compile(r"\[?(S[-A-Za-z0-9_]+)\]?\s*\[\s*(y|n|\?|skip|pending|hit|miss|partial|unknown|命中|未命中|部分命中|待反馈)?\s*\]", re.I)
MD_TABLE_SEP = re.compile(r"^\s*\|?\s*:?-{2,}:?")


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def case_dirs() -> list[Path]:
    dirs: list[Path] = []
    for path in sorted(CASES_ROOT.iterdir()):
        if not path.is_dir():
            continue
        if path.name.startswith("_") or path.name == "raw_feedback":
            continue
        if path.name.startswith("C-") or any((path / name).exists() for name in ("input.md", "feedback.md", "statement_index.json", "statement_records.json")):
            dirs.append(path)
    return dirs


def parse_phase300_strategy(path: Path = PHASE_300_STRATEGY) -> dict[str, dict[str, str]]:
    mapping: dict[str, dict[str, str]] = {}
    if not path.exists():
        return mapping
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line.startswith("| `"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) < 5:
            continue
        rule_id = cells[0].strip("` ")
        if not CANONICAL_RULE_RE.match(rule_id):
            continue
        canon = cells[1].strip("` ")
        school = cells[2].strip("` ")
        family_raw = cells[3].strip("` ")
        rule_type = cells[4].strip("` ")
        families = [part.strip().strip("`") for part in family_raw.split(",") if part.strip().strip("`") and part.strip().strip("`") != "-"]
        mapping[rule_id] = {
            "canon": canon,
            "school": school,
            "family_raw": family_raw,
            "family_id": families[0] if len(families) == 1 else "UNMAPPED",
            "family_count": str(len(families)),
            "rule_type": rule_type,
        }
    return mapping


def statements_from_index(data: Any) -> list[dict[str, Any]]:
    if not isinstance(data, dict):
        return []
    raw = data.get("statements", [])
    if isinstance(raw, dict):
        return [dict(v, statement_id=k) if isinstance(v, dict) and not v.get("statement_id") else dict(v) for k, v in raw.items() if isinstance(v, dict)]
    if isinstance(raw, list):
        return [dict(item) for item in raw if isinstance(item, dict)]
    return []


def normalize_rule_ids(stmt: dict[str, Any]) -> list[str]:
    raw = stmt.get("rule_id") or stmt.get("rule_ids") or stmt.get("rules") or []
    if isinstance(raw, str):
        raw = [raw]
    if not isinstance(raw, list):
        return []
    out: list[str] = []
    for value in raw:
        rid = str(value or "").strip()
        if rid and rid not in out:
            out.append(rid)
    return out


def statement_text(stmt: dict[str, Any]) -> str:
    for key in ("statement_text", "statement", "summary", "feedback_summary"):
        value = str(stmt.get(key) or "").strip()
        if value:
            return value
    return str(stmt.get("domain") or "未提供断语文本").strip() or "未提供断语文本"


def confidence_snapshot(stmt: dict[str, Any]) -> dict[str, Any]:
    star = stmt.get("star")
    try:
        star_int = int(star)
    except Exception:
        star_int = 0
    percent = stmt.get("confidence_percent") or stmt.get("percent")
    try:
        percent_float = float(percent)
    except Exception:
        percent_float = 0.0
    return {
        "star": max(0, min(5, star_int)),
        "percent": max(0.0, min(100.0, percent_float)),
        "posterior_mean": None,
        "sample_n": 0,
        "source": "fallback_initial",
    }


def make_unmapped_record(case_id: str, stmt: dict[str, Any], reason: str, rule_id: str = "UNMAPPED") -> dict[str, Any]:
    return {
        "statement_id": str(stmt.get("statement_id") or "").strip(),
        "case_id": case_id,
        "rule_id": rule_id or "UNMAPPED",
        "family_id": "UNMAPPED",
        "school": "UNMAPPED",
        "canon": "UNMAPPED",
        "rule_type": "UNMAPPED",
        "statement_text": statement_text(stmt),
        "confidence_snapshot": confidence_snapshot(stmt),
        "generated_at": GENERATED_AT,
        "source_engine_version": PRODUCT_VERSION,
        "source_rule_version": "phase-300-voting-strategy",
        "domain": str(stmt.get("domain") or ""),
        "section": str(stmt.get("section") or ""),
        "year": stmt.get("year"),
        "needs_mapping_repair": True,
        "mapping_repair_reason": reason,
    }


def migrate_case(case_dir: Path, strategy: dict[str, dict[str, str]]) -> dict[str, Any]:
    case_id = case_dir.name
    index_path = case_dir / "statement_index.json"
    records_path = case_dir / "statement_records.json"
    index_data = _read_json(index_path)
    statements = statements_from_index(index_data)
    records: list[dict[str, Any]] = []
    case_stats = Counter()

    for stmt in statements:
        sid = str(stmt.get("statement_id") or "").strip()
        if not sid:
            case_stats["missing_statement_id"] += 1
            continue
        rule_ids = normalize_rule_ids(stmt)
        if not rule_ids:
            records.append(make_unmapped_record(case_id, stmt, "no_rule_id_in_statement_index"))
            case_stats["unmapped_records"] += 1
            continue
        for rid in rule_ids:
            meta = strategy.get(rid)
            if not meta:
                records.append(make_unmapped_record(case_id, stmt, "rule_id_not_in_phase300_strategy", rid))
                case_stats["unmapped_records"] += 1
                continue
            if meta["family_id"] == "UNMAPPED":
                rec = make_unmapped_record(case_id, stmt, "ambiguous_or_missing_family_id_in_phase300_strategy", rid)
                rec.update({
                    "school": meta["school"],
                    "canon": meta["canon"],
                    "rule_type": meta["rule_type"],
                    "phase300_family_raw": meta["family_raw"],
                })
                records.append(rec)
                case_stats["unmapped_records"] += 1
                continue
            records.append({
                "statement_id": sid,
                "case_id": case_id,
                "rule_id": rid,
                "family_id": meta["family_id"],
                "school": meta["school"],
                "canon": meta["canon"],
                "rule_type": meta["rule_type"],
                "statement_text": statement_text(stmt),
                "confidence_snapshot": confidence_snapshot(stmt),
                "generated_at": GENERATED_AT,
                "source_engine_version": PRODUCT_VERSION,
                "source_rule_version": "phase-300-voting-strategy",
                "domain": str(stmt.get("domain") or ""),
                "section": str(stmt.get("section") or ""),
                "year": stmt.get("year"),
                "needs_mapping_repair": False,
                "mapping_repair_reason": "",
            })
            case_stats["mapped_records"] += 1

    envelope = {
        "schema_version": "statement_record.v1",
        "case_id": case_id,
        "generated_at": GENERATED_AT,
        "source": "P5-7 historical statement record migration",
        "source_rule_version": "phase-300-voting-strategy",
        "records": records,
    }
    _write_json(records_path, envelope)
    return {
        "case_id": case_id,
        "statement_count": len(statements),
        "record_count": len(records),
        "mapped_records": case_stats["mapped_records"],
        "unmapped_records": case_stats["unmapped_records"],
        "missing_statement_id": case_stats["missing_statement_id"],
        "records_path": records_path.as_posix(),
    }


def coverage_audit(dirs: list[Path], *, before_records_count: int | None = None) -> dict[str, Any]:
    total = len(dirs)
    has_index = sum(1 for d in dirs if (d / "statement_index.json").exists())
    has_records = sum(1 for d in dirs if (d / "statement_records.json").exists())
    missing_records = total - has_records
    md = [
        "# Historical Statement Record Coverage",
        "",
        f"生成时间：`{GENERATED_AT}`",
        "",
        "## 1. 范围",
        "",
        "- 扫描范围：`cases/*` 下正式案例目录；排除 `_TEMPLATE` 与 `raw_feedback`。",
        "- 审计对象：`statement_index.json` 与 `statement_records.json`。",
        "",
        "## 2. 覆盖率统计",
        "",
        "| 指标 | 数量 |",
        "|---|---:|",
        f"| 总案例数 | {total} |",
        f"| 有 `statement_index.json` 数量 | {has_index} |",
        f"| 有 `statement_records.json` 数量 | {has_records} |",
        f"| 缺失 `statement_records.json` 数量 | {missing_records} |",
    ]
    if before_records_count is not None:
        md.extend([
            f"| 迁移前有 `statement_records.json` 数量 | {before_records_count} |",
            f"| 本轮补建后有 `statement_records.json` 数量 | {has_records} |",
        ])
    md.extend([
        "",
        "## 3. 结论",
        "",
        f"本轮覆盖率为 `{round(has_records / (total or 1) * 100, 2)}%`。",
    ])
    COVERAGE_REPORT.write_text("\n".join(md) + "\n", encoding="utf-8")
    return {"total_cases": total, "has_statement_index": has_index, "has_statement_records": has_records, "missing_statement_records": missing_records}


def verdict_from_annotation(raw: str | None, text: str = "") -> tuple[str, str]:
    s = (raw or "").strip().lower()
    t = text or ""
    if s in ("y", "hit", "命中") or "✅" in t or "应验" in t or ("命中" in t and "未命中" not in t):
        return "y", "hit"
    if s in ("n", "miss", "未命中") or "❌" in t or "失验" in t or "否认" in t:
        return "n", "miss"
    if s in ("skip", "跳过") or "skip" in t.lower() or "风险提示" in t:
        return "skip", "no_data"
    if s in ("?", "pending", "unknown", "待反馈", "") or "[ ]" in t or "⏳" in t or "未反馈" in t or "待验" in t or "未到" in t:
        return "?", "no_data"
    if s in ("partial", "部分命中", "部分") or "🟡" in t or "部分" in t:
        return "partial", "no_data"
    return "?", "no_data"


def parse_historical_feedback_signals(text: str, case_id: str) -> list[StatementFeedback]:
    signals: dict[tuple[str, str], StatementFeedback] = {}
    for match in STMT_BRACKET_RE.finditer(text):
        sid = match.group(1)
        raw = match.group(2) or ""
        line_start = text.rfind("\n", 0, match.start()) + 1
        line_end = text.find("\n", match.end())
        if line_end == -1:
            line_end = len(text)
        line = text[line_start:line_end].strip()
        annotation, verdict = verdict_from_annotation(raw, line)
        signals[(sid, line)] = StatementFeedback(statement_id=sid, annotation=annotation, verdict=verdict, raw_line=line)

    for line in text.splitlines():
        if not line.strip().startswith("|") or MD_TABLE_SEP.match(line):
            continue
        cells = [cell.strip().strip("`") for cell in line.strip().strip("|").split("|")]
        sid = None
        for cell in cells[:2]:
            mm = re.search(r"(S[-A-Za-z0-9_]+)", cell)
            if mm:
                sid = mm.group(1)
                break
        if not sid:
            continue
        verdict_cell = ""
        for cell in cells:
            if BRACKET_RE.search(cell) or any(token in cell for token in ("✅", "❌", "🟡", "⏳", "pending", "hit", "miss", "待反馈", "未反馈", "应验", "失验", "部分")):
                verdict_cell = cell
        annotation, verdict = verdict_from_annotation(verdict_cell, line)
        signals[(sid, line.strip())] = StatementFeedback(statement_id=sid, annotation=annotation, verdict=verdict, raw_line=line.strip())

    if not signals and text.strip():
        for line_no, line in enumerate(text.splitlines(), 1):
            if any(token in line for token in ("[y]", "[n]", "[?]", "[skip]", "✅", "❌", "🟡", "⏳", "pending", "unknown", "hit", "miss")):
                sid = f"UNMAPPED-{case_id}-{line_no:04d}"
                annotation, verdict = verdict_from_annotation("", line)
                signals[(sid, line.strip())] = StatementFeedback(statement_id=sid, annotation=annotation, verdict=verdict, raw_line=line.strip())
    return list(signals.values())


def all_feedbacks_by_case(dirs: list[Path]) -> dict[str, list[StatementFeedback]]:
    out: dict[str, list[StatementFeedback]] = {}
    for d in dirs:
        path = d / "feedback.md"
        if not path.exists():
            out[d.name] = []
            continue
        out[d.name] = parse_historical_feedback_signals(path.read_text(encoding="utf-8", errors="ignore"), d.name)
    return out


def recovery_audit(dirs: list[Path], feedbacks_by_case: dict[str, list[StatementFeedback]]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    stats = Counter()
    for d in dirs:
        records_data = _read_json(d / "statement_records.json") or {}
        records = records_data.get("records", []) if isinstance(records_data, dict) else []
        by_sid: dict[str, list[dict[str, Any]]] = defaultdict(list)
        if isinstance(records, list):
            for rec in records:
                if isinstance(rec, dict) and rec.get("statement_id"):
                    by_sid[str(rec["statement_id"])].append(rec)
        for fb in feedbacks_by_case.get(d.name, []):
            recs = by_sid.get(fb.statement_id, [])
            recoverable_records = [r for r in recs if not r.get("needs_mapping_repair") and str(r.get("rule_id") or "").strip() and not str(r.get("rule_id") or "").upper().startswith("UNMAPPED")]
            recoverable = bool(recoverable_records)
            stats["feedback_rows"] += 1
            stats["recoverable_rows" if recoverable else "unrecoverable_rows"] += 1
            rows.append({
                "case_id": d.name,
                "statement_id": fb.statement_id,
                "verdict": fb.verdict,
                "recoverable": recoverable,
                "record_count": len(recs),
                "recoverable_record_count": len(recoverable_records),
                "rule_ids": [r.get("rule_id") for r in recoverable_records],
                "reason": "" if recoverable else ("statement_record_missing" if not recs else "statement_record_needs_mapping_repair"),
            })
    percent = round(stats["recoverable_rows"] / (stats["feedback_rows"] or 1) * 100, 2)
    md = [
        "# Historical Mapping Recovery Report",
        "",
        f"生成时间：`{GENERATED_AT}`",
        "",
        "## 1. 恢复链路",
        "",
        "```text",
        "feedback row -> statement_id -> statement_record -> rule_id",
        "```",
        "",
        "## 2. 统计",
        "",
        "| 指标 | 数量 |",
        "|---|---:|",
        f"| feedback rows | {stats['feedback_rows']} |",
        f"| recoverable rows | {stats['recoverable_rows']} |",
        f"| unrecoverable rows | {stats['unrecoverable_rows']} |",
        f"| recoverable percent | {percent}% |",
        "",
        "## 3. 不可恢复原因分布",
        "",
        "| 原因 | 数量 |",
        "|---|---:|",
    ]
    reasons = Counter(row["reason"] for row in rows if not row["recoverable"])
    for reason, count in sorted(reasons.items()):
        md.append(f"| {reason} | {count} |")
    md.extend(["", "## 4. 明细产物", "", "- 迁移日志：`META/historical-statement-record-migration-log.json`"])
    RECOVERY_REPORT.write_text("\n".join(md) + "\n", encoding="utf-8")
    return {"rows": rows, "feedback_rows": stats["feedback_rows"], "recoverable_rows": stats["recoverable_rows"], "unrecoverable_rows": stats["unrecoverable_rows"], "recoverable_percent": percent}


def learnable_audit(dirs: list[Path], feedbacks_by_case: dict[str, list[StatementFeedback]], recovery: dict[str, Any]) -> dict[str, Any]:
    totals = Counter()
    mapped_rows: list[dict[str, Any]] = []
    samples_all: list[dict[str, str]] = []
    for d in dirs:
        feedbacks = feedbacks_by_case.get(d.name, [])
        records_data = _read_json(d / "statement_records.json") or {"records": []}
        samples, mapped, bridge_stats = build_learning_samples(feedbacks, records_data if isinstance(records_data, dict) else {"records": []})
        samples_all.extend(samples)
        for row in mapped:
            row = dict(row)
            row["case_id"] = d.name
            mapped_rows.append(row)
        totals["total"] += bridge_stats.total_rows
        totals["learnable"] += bridge_stats.learnable_rows
        totals["pending"] += bridge_stats.pending_rows
        totals["unmapped"] += bridge_stats.unmapped_rows
    totals["skip"] = sum(1 for row in mapped_rows if row.get("annotation") == "skip")
    readiness = "READY_FOR_PHASE1000" if recovery["recoverable_rows"] > 0 else "BLOCKED"
    reason = "recoverable rows > 0" if readiness == "READY_FOR_PHASE1000" else "recoverable rows = 0；feedback -> statement_record -> rule_id 链仍无可恢复样本"
    percent = round(recovery["recoverable_rows"] / (recovery["feedback_rows"] or 1) * 100, 2)
    md = [
        "# Phase-1000 Learnable Sample Audit",
        "",
        f"生成时间：`{GENERATED_AT}`",
        "",
        "## 1. build_learning_samples() 统计",
        "",
        "| 指标 | 数量 |",
        "|---|---:|",
        f"| feedback rows | {totals['total']} |",
        f"| learnable | {totals['learnable']} |",
        f"| pending | {totals['pending']} |",
        f"| skip | {totals['skip']} |",
        f"| unmapped | {totals['unmapped']} |",
        "",
        "## 2. Ready Check",
        "",
        "| 指标 | 值 |",
        "|---|---|",
        f"| recoverable rows | {recovery['recoverable_rows']} |",
        f"| recoverable percent | {percent}% |",
        f"| final status | `{readiness}` |",
        f"| reason | {reason} |",
        "",
        "## 3. 边界声明",
        "",
        "本审计只重建历史映射与学习样本计数；未进入权重学习，未更新 Dynamic Confidence，未修改任何生产规则。",
    ]
    LEARNABLE_AUDIT.write_text("\n".join(md) + "\n", encoding="utf-8")
    return {"learnable": totals["learnable"], "pending": totals["pending"], "skip": totals["skip"], "unmapped": totals["unmapped"], "readiness": readiness, "recoverable_percent": percent, "samples": samples_all, "mapped_rows": mapped_rows}


def main() -> None:
    parser = argparse.ArgumentParser(description="P5-7 Historical Mapping Recovery Implementation")
    parser.add_argument("--dry-run", action="store_true", help="只审计，不写 statement_records.json（仍写 META 报告）")
    args = parser.parse_args()

    META_ROOT.mkdir(parents=True, exist_ok=True)
    dirs = case_dirs()
    before = sum(1 for d in dirs if (d / "statement_records.json").exists())
    strategy = parse_phase300_strategy()

    migration: list[dict[str, Any]] = []
    if not args.dry_run:
        for d in dirs:
            if (d / "statement_index.json").exists():
                migration.append(migrate_case(d, strategy))
    _write_json(MIGRATION_LOG, {
        "generated_at": GENERATED_AT,
        "strategy_rule_count": len(strategy),
        "case_count": len(dirs),
        "migrated_case_count": len(migration),
        "cases": migration,
    })

    coverage = coverage_audit(dirs, before_records_count=before)
    feedbacks = all_feedbacks_by_case(dirs)
    recovery = recovery_audit(dirs, feedbacks)
    learnable = learnable_audit(dirs, feedbacks, recovery)

    print(json.dumps({
        "coverage": coverage,
        "recovery": {k: recovery[k] for k in ("feedback_rows", "recoverable_rows", "unrecoverable_rows", "recoverable_percent")},
        "learnable": {k: learnable[k] for k in ("learnable", "pending", "skip", "unmapped", "readiness", "recoverable_percent")},
        "outputs": [COVERAGE_REPORT.as_posix(), RECOVERY_REPORT.as_posix(), LEARNABLE_AUDIT.as_posix()],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

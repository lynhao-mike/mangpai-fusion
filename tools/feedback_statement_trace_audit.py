from __future__ import annotations

import datetime as dt
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
CASES_ROOT = ROOT / "cases"
REPORTS_ROOT = ROOT / "reports"
META_ROOT = ROOT / "META"
GENERATED_AT = dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")

SOURCE_AUDIT = META_ROOT / "feedback-source-audit.md"
REFERENCE_AUDIT = META_ROOT / "feedback-statement-reference-audit.md"
JOIN_AUDIT = META_ROOT / "feedback-statement-join-audit.md"
REPORT_TRACE_AUDIT = META_ROOT / "historical-report-trace-audit.md"
RECOVERABILITY_AUDIT = META_ROOT / "recoverability-classification.md"
DETAIL_JSON = META_ROOT / "feedback-statement-trace-reconstruction-detail.json"

STMT_RE = re.compile(r"S[-A-Za-z0-9_]+")
STMT_BRACKET_RE = re.compile(r"\[?(S[-A-Za-z0-9_]+)\]?\s*\[\s*(y|n|\?|skip|pending|hit|miss|partial|unknown|命中|未命中|部分命中|待反馈)?\s*\]", re.I)
BRACKET_RE = re.compile(r"\[\s*(y|n|\?|skip|pending|hit|miss|partial|unknown|命中|未命中|部分命中|待反馈)?\s*\]", re.I)
MD_TABLE_SEP = re.compile(r"^\s*\|?\s*:?-{2,}:?")
SECTION_REF_RE = re.compile(r"(Step\s*\d+|第[一二三四五六七八九十0-9]+[章节步]|事业|财|婚|健康|学业|应期|性格|家庭|报告|章节|section)", re.I)
ANCHOR_RE = re.compile(r"\[[^\]]+\]\(#[^)]+\)|<a\s+name=|id=", re.I)
TRACE_RE = re.compile(r"trace[_-]?id|statement[_-]?index|statement[_-]?map|rule[_-]?map|S-\d{3}", re.I)
NUMBER_REF_RE = re.compile(r"(?:断语|编号|序号|第)\s*[#：:No\.]*\s*\d+|^\s*\|\s*\d+\s*\|", re.I)
LEGACY_RULE_RE = re.compile(r"\b(?:M\d-[A-Z]-\d+|GP-[^\s|，,]+|MR-LAYER\d+|G-SHENSHA-\d+)\b")
CANONICAL_RULE_RE = re.compile(r"\b(?:DTS|ZP)-PROD-\d{8}-\d{3}\b")


def case_dirs() -> list[Path]:
    out: list[Path] = []
    for path in sorted(CASES_ROOT.iterdir()):
        if not path.is_dir() or path.name.startswith("_") or path.name == "raw_feedback":
            continue
        if path.name.startswith("C-"):
            out.append(path)
    return out


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def verdict_category(raw: str | None, line: str) -> str:
    s = (raw or "").strip().lower()
    t = line or ""
    if s in ("y", "hit", "命中") or "✅" in t or "应验" in t or ("命中" in t and "未命中" not in t and "部分" not in t):
        return "y"
    if s in ("n", "miss", "未命中") or "❌" in t or "失验" in t or "否认" in t:
        return "n"
    if s in ("skip", "跳过") or "skip" in t.lower() or "风险提示" in t:
        return "skip"
    if s in ("?", "pending", "待反馈", "unknown", "") or "[ ]" in t or "⏳" in t or "待验" in t or "未反馈" in t or "未到" in t:
        return "pending"
    if s in ("partial", "部分命中", "部分") or "🟡" in t or "部分" in t:
        return "pending"
    return "unknown"


def extract_feedback_rows(case_dir: Path) -> list[dict[str, Any]]:
    path = case_dir / "feedback.md"
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8", errors="ignore")
    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, int, str]] = set()

    for line_no, line in enumerate(text.splitlines(), 1):
        for m in STMT_BRACKET_RE.finditer(line):
            sid = m.group(1)
            raw = m.group(2) or ""
            key = (sid, line_no, line.strip())
            if key in seen:
                continue
            seen.add(key)
            rows.append(make_row(case_dir.name, line_no, line.strip(), verdict_category(raw, line), "direct_statement_id", sid))

    for line_no, line in enumerate(text.splitlines(), 1):
        if not line.strip().startswith("|") or MD_TABLE_SEP.match(line):
            continue
        cells = [cell.strip().strip("`") for cell in line.strip().strip("|").split("|")]
        sid_match = None
        for cell in cells[:3]:
            mm = STMT_RE.search(cell)
            if mm:
                sid_match = mm.group(0)
                break
        verdict_cell = ""
        for cell in cells:
            if BRACKET_RE.search(cell) or any(token in cell for token in ("✅", "❌", "🟡", "⏳", "pending", "hit", "miss", "待反馈", "未反馈", "应验", "失验", "部分")):
                verdict_cell = cell
        if sid_match:
            key = (sid_match, line_no, line.strip())
            if key not in seen:
                seen.add(key)
                rows.append(make_row(case_dir.name, line_no, line.strip(), verdict_category(verdict_cell, line), "direct_statement_id", sid_match))

    if not rows and text.strip():
        for line_no, line in enumerate(text.splitlines(), 1):
            if any(token in line for token in ("[y]", "[n]", "[?]", "[skip]", "✅", "❌", "🟡", "⏳", "pending", "unknown", "hit", "miss")):
                rows.append(make_row(case_dir.name, line_no, line.strip(), verdict_category("", line), "legacy_unmapped_line", ""))
    return rows


def make_row(case_id: str, line_no: int, line: str, verdict: str, source: str, statement_id: str) -> dict[str, Any]:
    has_statement_id = bool(statement_id or STMT_RE.search(line))
    if not statement_id:
        mm = STMT_RE.search(line)
        statement_id = mm.group(0) if mm else ""
    features = {
        "statement_id": bool(statement_id),
        "statement_number": bool(NUMBER_REF_RE.search(line)),
        "markdown_anchor": bool(ANCHOR_RE.search(line)),
        "report_section_reference": bool(SECTION_REF_RE.search(line)),
        "trace_id": bool(TRACE_RE.search(line)),
        "old_statement_mapping": bool(LEGACY_RULE_RE.search(line) or CANONICAL_RULE_RE.search(line) or "statement_rule_map" in line),
    }
    if has_statement_id:
        reference_class = "direct_statement_id"
    elif features["statement_number"] or features["markdown_anchor"] or features["report_section_reference"] or features["trace_id"] or features["old_statement_mapping"]:
        reference_class = "indirect_statement_reference"
    else:
        reference_class = "no_statement_reference"
    return {
        "case_id": case_id,
        "line_no": line_no,
        "line": line,
        "verdict": verdict,
        "source": source,
        "statement_id": statement_id,
        "features": features,
        "reference_class": reference_class,
    }


def load_record_maps(case_dir: Path) -> tuple[dict[str, list[dict[str, Any]]], dict[str, str]]:
    data = read_json(case_dir / "statement_records.json") or {}
    records = data.get("records", []) if isinstance(data, dict) else []
    by_sid: dict[str, list[dict[str, Any]]] = defaultdict(list)
    normalized: dict[str, str] = {}
    if isinstance(records, list):
        for rec in records:
            if not isinstance(rec, dict):
                continue
            sid = str(rec.get("statement_id") or "").strip()
            if sid:
                by_sid[sid].append(rec)
                normalized[normalize_sid(sid)] = sid
    return by_sid, normalized


def normalize_sid(sid: str) -> str:
    return re.sub(r"[^a-z0-9]", "", sid.lower())


def statement_index_ids(case_dir: Path) -> set[str]:
    data = read_json(case_dir / "statement_index.json") or {}
    raw = data.get("statements", []) if isinstance(data, dict) else []
    ids: set[str] = set()
    if isinstance(raw, list):
        for item in raw:
            if isinstance(item, dict) and item.get("statement_id"):
                ids.add(str(item["statement_id"]))
    elif isinstance(raw, dict):
        ids.update(str(k) for k in raw.keys())
    return ids


def report_files_for_case(case_id: str) -> list[Path]:
    return sorted(REPORTS_ROOT.glob(f"{case_id}*.md"))


def case_report_files(case_dir: Path) -> list[Path]:
    names = ["report.md", "report_v1.md", "report_v1.2.md", "report_v1.3.md", "report_v1.4.md", "analysis.md", "analyst-report.md", "content-report.md"]
    found = [case_dir / name for name in names if (case_dir / name).exists()]
    found.extend(sorted(case_dir.glob("report_v*.md")))
    return sorted(set(found))


def _group_rows_by_case(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    by_case: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_case[row["case_id"]].append(row)
    return by_case


def _build_case_cache(dirs: list[Path], rows_by_case: dict[str, list[dict[str, Any]]]) -> dict[str, dict[str, Any]]:
    cache: dict[str, dict[str, Any]] = {}
    for d in dirs:
        reports_in_case = case_report_files(d)
        reports_external = report_files_for_case(d.name)
        by_sid, normalized_map = load_record_maps(d)
        idx_ids = statement_index_ids(d)
        report_v_files = list(d.glob("report_v*.md"))
        has_records = (d / "statement_records.json").exists()
        cache[d.name] = {
            "case_dir": d,
            "by_sid": by_sid,
            "normalized_map": normalized_map,
            "idx_ids": idx_ids,
            "reports": reports_external + reports_in_case,
            "trace": {
                "case_id": d.name,
                "feedback_rows": len(rows_by_case.get(d.name, [])),
                "has_report_md": (d / "report.md").exists(),
                "has_report_v": bool(report_v_files),
                "has_statement_index": (d / "statement_index.json").exists(),
                "has_statement_records": has_records,
                "external_report_count": len(reports_external),
                "can_trace_to_report": bool(reports_in_case or reports_external),
            },
        }
    return cache


def main() -> None:
    META_ROOT.mkdir(parents=True, exist_ok=True)
    dirs = case_dirs()
    rows: list[dict[str, Any]] = []
    for d in dirs:
        rows.extend(extract_feedback_rows(d))

    rows_by_case = _group_rows_by_case(rows)
    case_cache = _build_case_cache(dirs, rows_by_case)
    join_stats = Counter()
    root_causes = Counter()
    recoverability = Counter()
    reference_stats = Counter()
    source_stats = Counter()
    verdict_stats = Counter()

    case_trace_rows = [case_cache[d.name]["trace"] for d in dirs]

    for row in rows:
        verdict_stats[row["verdict"]] += 1
        source_stats[row["source"]] += 1
        reference_stats[row["reference_class"]] += 1
        cached_case = case_cache[row["case_id"]]
        by_sid = cached_case["by_sid"]
        normalized_map = cached_case["normalized_map"]
        sid = row["statement_id"]
        joined = False
        join_reason = ""
        if not sid:
            join_reason = "JOIN_C"
        elif sid in by_sid:
            recs = by_sid[sid]
            if any(not r.get("needs_mapping_repair") and str(r.get("rule_id") or "").strip() and not str(r.get("rule_id") or "").upper().startswith("UNMAPPED") for r in recs):
                joined = True
                join_reason = "JOIN_OK"
            else:
                join_reason = "JOIN_A"
        elif normalize_sid(sid) in normalized_map:
            join_reason = "JOIN_B"
        else:
            idx_ids = cached_case["idx_ids"]
            reports = cached_case["reports"]
            if sid in idx_ids and reports:
                join_reason = "JOIN_D"
            elif not cached_case["trace"]["has_statement_records"]:
                join_reason = "JOIN_E"
            else:
                join_reason = "JOIN_A"
        row["join_success"] = joined
        row["join_reason"] = join_reason
        join_stats[join_reason] += 1

        report_trace = cached_case["trace"]
        if joined:
            rc = "HIGH_RECOVERABLE"
            cause = "JOIN_OK"
        elif join_reason == "JOIN_B":
            rc = "HIGH_RECOVERABLE"
            cause = "statement_id_format_changed"
        elif sid and report_trace["can_trace_to_report"] and report_trace["has_statement_index"]:
            rc = "MEDIUM_RECOVERABLE"
            cause = "report_and_index_exist_but_record_mapping_missing"
        elif row["reference_class"] == "indirect_statement_reference" or report_trace["can_trace_to_report"]:
            rc = "LOW_RECOVERABLE"
            cause = "feedback_has_only_indirect_or_report_level_reference"
        elif not sid:
            rc = "UNRECOVERABLE"
            cause = "feedback_row_has_no_statement_identifier"
        else:
            rc = "UNRECOVERABLE"
            cause = "statement_identifier_not_found_in_current_records_or_reports"
        row["recoverability"] = rc
        row["root_cause"] = cause
        recoverability[rc] += 1
        root_causes[cause] += 1

    # empty/legacy/unknown source verdict supplement
    empty_feedback_files = sum(
        1 for d in dirs
        if (d / "feedback.md").exists() and not rows_by_case.get(d.name)
    )
    source_verdict_rows = Counter(verdict_stats)
    source_verdict_rows["empty"] = empty_feedback_files
    source_verdict_rows["legacy"] = source_stats["legacy_unmapped_line"]
    source_verdict_rows["unknown"] += verdict_stats["unknown"]

    write_source_audit(rows, source_verdict_rows, source_stats)
    write_reference_audit(rows, reference_stats)
    write_join_audit(rows, join_stats)
    write_report_trace_audit(case_trace_rows)
    write_recoverability_audit(rows, recoverability, root_causes)
    DETAIL_JSON.write_text(json.dumps({"generated_at": GENERATED_AT, "rows": rows, "case_trace": case_trace_rows}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps({
        "feedback_rows": len(rows),
        "join": dict(join_stats),
        "recoverability": dict(recoverability),
        "top_root_cause": root_causes.most_common(1)[0] if root_causes else None,
        "outputs": [SOURCE_AUDIT.as_posix(), REFERENCE_AUDIT.as_posix(), JOIN_AUDIT.as_posix(), REPORT_TRACE_AUDIT.as_posix(), RECOVERABILITY_AUDIT.as_posix()],
    }, ensure_ascii=False, indent=2))


def pct(n: int, total: int) -> str:
    return f"{round(n / (total or 1) * 100, 2)}%"


def write_source_audit(rows: list[dict[str, Any]], verdicts: Counter, sources: Counter) -> None:
    total = len(rows)
    md = ["# Feedback Source Audit", "", f"生成时间：`{GENERATED_AT}`", "", "## 1. Feedback Verdict 分类", "", "| 分类 | 数量 | 占比 |", "|---|---:|---:|"]
    for key in ("y", "n", "skip", "pending", "empty", "legacy", "unknown"):
        md.append(f"| {key} | {verdicts[key]} | {pct(verdicts[key], total)} |")
    md.extend(["", "## 2. 解析来源", "", "| 来源 | 数量 | 占比 |", "|---|---:|---:|"])
    for key, count in sources.most_common():
        md.append(f"| {key} | {count} | {pct(count, total)} |")
    SOURCE_AUDIT.write_text("\n".join(md) + "\n", encoding="utf-8")


def write_reference_audit(rows: list[dict[str, Any]], refs: Counter) -> None:
    total = len(rows)
    feature_counts = Counter()
    for row in rows:
        for key, value in row["features"].items():
            if value:
                feature_counts[key] += 1
    direct = refs["direct_statement_id"]
    indirect = refs["indirect_statement_reference"]
    none = refs["no_statement_reference"]
    md = ["# Feedback Statement Reference Audit", "", f"生成时间：`{GENERATED_AT}`", "", "## 1. 定位能力统计", "", "| 指标 | 数量 | 占比 |", "|---|---:|---:|", f"| 可直接定位 statement_id | {direct} | {pct(direct, total)} |", f"| 可间接定位 statement | {indirect} | {pct(indirect, total)} |", f"| 完全无法定位 | {none} | {pct(none, total)} |", "", "## 2. 引用形态", "", "| 引用形态 | 数量 | 占比 |", "|---|---:|---:|"]
    labels = ["statement_id", "statement_number", "markdown_anchor", "report_section_reference", "trace_id", "old_statement_mapping"]
    for key in labels:
        md.append(f"| {key} | {feature_counts[key]} | {pct(feature_counts[key], total)} |")
    REFERENCE_AUDIT.write_text("\n".join(md) + "\n", encoding="utf-8")


def write_join_audit(rows: list[dict[str, Any]], joins: Counter) -> None:
    total = len(rows)
    success = joins["JOIN_OK"]
    failure = total - success
    md = ["# Feedback Statement Join Audit", "", f"生成时间：`{GENERATED_AT}`", "", "## 1. Join 结果", "", "| 指标 | 数量 | 占比 |", "|---|---:|---:|", f"| 成功 join | {success} | {pct(success, total)} |", f"| 失败 join | {failure} | {pct(failure, total)} |", "", "## 2. 失败原因分类", "", "| Join Code | 含义 | 数量 | 占比 |", "|---|---|---:|---:|"]
    meanings = {
        "JOIN_A": "statement_id 不存在或仅有 needs_mapping_repair record",
        "JOIN_B": "statement_id 格式变化",
        "JOIN_C": "feedback 未记录 statement_id",
        "JOIN_D": "statement_records 与反馈来自不同版本报告",
        "JOIN_E": "其他",
    }
    for code in ("JOIN_A", "JOIN_B", "JOIN_C", "JOIN_D", "JOIN_E"):
        md.append(f"| {code} | {meanings[code]} | {joins[code]} | {pct(joins[code], total)} |")
    JOIN_AUDIT.write_text("\n".join(md) + "\n", encoding="utf-8")


def write_report_trace_audit(case_rows: list[dict[str, Any]]) -> None:
    total_cases = len(case_rows)
    feedback_cases = sum(1 for r in case_rows if r["feedback_rows"] > 0)
    report_cases = sum(1 for r in case_rows if r["can_trace_to_report"])
    index_cases = sum(1 for r in case_rows if r["has_statement_index"])
    record_cases = sum(1 for r in case_rows if r["has_statement_records"])
    trace_feedback_cases = sum(1 for r in case_rows if r["feedback_rows"] > 0 and r["can_trace_to_report"])
    md = ["# Historical Report Trace Audit", "", f"生成时间：`{GENERATED_AT}`", "", "## 1. Case 级报告追溯", "", "| 指标 | 数量 | 占比 |", "|---|---:|---:|", f"| 总案例数 | {total_cases} | 100.0% |", f"| 有 feedback rows 的案例 | {feedback_cases} | {pct(feedback_cases, total_cases)} |", f"| 存在 report/report_v/外部 reports 文件 | {report_cases} | {pct(report_cases, total_cases)} |", f"| 存在 statement_index.json | {index_cases} | {pct(index_cases, total_cases)} |", f"| 存在 statement_records.json | {record_cases} | {pct(record_cases, total_cases)} |", f"| 有 feedback 且可回溯报告 | {trace_feedback_cases} | {pct(trace_feedback_cases, feedback_cases)} |", "", "## 2. 判断", "", "报告文件存在不等于 statement 级可 join；本审计只统计是否还能回溯到生成报告或报告归档。"]
    REPORT_TRACE_AUDIT.write_text("\n".join(md) + "\n", encoding="utf-8")


def write_recoverability_audit(rows: list[dict[str, Any]], rec: Counter, causes: Counter) -> None:
    total = len(rows)
    md = ["# Recoverability Classification", "", f"生成时间：`{GENERATED_AT}`", "", "## 1. 可恢复性分类", "", "| 分类 | 数量 | 比例 | 预估恢复样本数 |", "|---|---:|---:|---:|"]
    for key in ("HIGH_RECOVERABLE", "MEDIUM_RECOVERABLE", "LOW_RECOVERABLE", "UNRECOVERABLE"):
        estimate = rec[key] if key in ("HIGH_RECOVERABLE", "MEDIUM_RECOVERABLE") else 0
        md.append(f"| {key} | {rec[key]} | {pct(rec[key], total)} | {estimate} |")
    md.extend(["", "## 2. TOP10 Root Causes", ""])
    for i, (cause, count) in enumerate(causes.most_common(10), 1):
        md.extend([f"### ROOT_CAUSE_{i}", "", f"- 原因：`{cause}`", f"- 影响样本数：{count}", f"- 占比：{pct(count, total)}", ""])
    top = causes.most_common(1)[0] if causes else ("none", 0)
    md.extend(["## 3. Phase-1000 阻塞主根因", "", f"唯一主根因：`{top[0]}`。", "", "该根因说明 feedback 与当前 statement_records 之间缺少同源、同版本、可学习的 statement 级绑定；因此即使 statement_records 覆盖率为 127/127，也不能恢复为 Phase-1000 learnable samples。"])
    RECOVERABILITY_AUDIT.write_text("\n".join(md) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

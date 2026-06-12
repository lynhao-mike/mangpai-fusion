"""feedback_v2_preprocess.py

为最近 N 个新案例生成结构化反馈模板、自动校验 statement_id 是否在
statement_records.json::records 中存在，并把反馈归一为 verdict ∈ {y, n, skip, pending}。

设计原则：
- 只读不写：不会修改 cases/*、theory/*、engine/*、tests/*、META/project-state.json。
- 仅写入新产物：templates/feedback-v2.md（模板常量）、
  cases/<case_id>/normalized-feedback/<case_id>-feedback.md、
  META/phase-1000-feedback-mapping/<case_id>-mapping.{csv,json}、
  META/feedback-preprocess-summary.md。
- verdict 严格仅允许 y / n / skip / pending。
- statement_id 不存在于 statement_records.json 时输出 INVALID_STATEMENT_ID。
- 旧 feedback.md 中"应验/失验"自由文本不会自动转 verdict；只识别
  [S-xxxx] [y/n/skip/pending] / [y|n|skip|pending] 的显式行；缺漏一律记 pending。

调用方式：
    python tools/feedback_v2_preprocess.py                # 处理最近 10 个新案例
    python tools/feedback_v2_preprocess.py --limit 5      # 处理最近 5 个新案例
    python tools/feedback_v2_preprocess.py --case <id>    # 处理单个案例
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

ROOT = Path(".")
CASES_ROOT = ROOT / "cases"
TEMPLATE_OUT = ROOT / "templates" / "feedback-v2.md"
MAPPING_DIR = ROOT / "META" / "phase-1000-feedback-mapping"
SUMMARY_OUT = ROOT / "META" / "feedback-preprocess-summary.md"
ITERATION_STATE = ROOT / "META" / "iteration-state.json"

ALLOWED_VERDICTS = {"y", "n", "skip", "pending"}

# 匹配 [S-xxxx] [y/n/skip/pending]，允许 [S-xxx] [y]、[S-xxx] [skip] 等形式。
STMT_VERDICT_RE = re.compile(
    r"\[(S[-A-Za-z0-9_]+)\]\s*[\[【]\s*(y|n|skip|pending)\s*[\]】]",
    re.IGNORECASE,
)
# 单纯出现的 [S-xxxx]，用来发现"未在 verdict 行中给出"的句柄。
STMT_REF_RE = re.compile(r"\[(S[-A-Za-z0-9_]+)\]")

# 输入信息 (input.md) 中的关键字段提取。
GENDER_RE = re.compile(r"性别\s*[::]\s*([MF])", re.IGNORECASE)
QIANKUN_RE = re.compile(r"乾坤\s*[::]\s*([乾坤])")
BIRTH_RE = re.compile(r"公历\s*[::]\s*['\"]?(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})")
CASE_ID_RE = re.compile(r"\b(C-\d{4}-[A-Z0-9]+-[乾坤]-[^\s/]+)\b")


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_recent_case_ids(limit: int) -> list[str]:
    """从 META/iteration-state.json 的 completed_case_ids 取最近 limit 个。"""
    if not ITERATION_STATE.exists():
        raise FileNotFoundError(f"missing {ITERATION_STATE}")
    data = json.loads(ITERATION_STATE.read_text(encoding="utf-8"))
    case_ids = data.get("completed_case_ids", [])
    if not isinstance(case_ids, list):
        raise ValueError("completed_case_ids must be list")
    return case_ids[-limit:]


def load_statement_records(case_dir: Path) -> tuple[list[dict], dict[str, dict]]:
    """返回 (records 列表, 以 statement_id 为 key 的索引)。"""
    path = case_dir / "statement_records.json"
    if not path.exists():
        return [], {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return [], {}
    records = data.get("records", []) if isinstance(data, dict) else []
    by_id: dict[str, dict] = {}
    for r in records:
        sid = r.get("statement_id")
        if sid:
            by_id[sid] = r
    return records, by_id


def parse_input_meta(case_dir: Path) -> dict:
    """从 input.md 中尽量解析命主性别 / 出生 / 乾坤。"""
    path = case_dir / "input.md"
    meta = {"gender": "", "qiankun": "", "birth": "", "case_id": ""}
    if not path.exists():
        return meta
    text = path.read_text(encoding="utf-8", errors="ignore")
    if m := GENDER_RE.search(text):
        meta["gender"] = m.group(1).upper()
    if m := QIANKUN_RE.search(text):
        meta["qiankun"] = m.group(1)
    if m := BIRTH_RE.search(text):
        meta["birth"] = m.group(1)
    if m := CASE_ID_RE.search(text):
        meta["case_id"] = m.group(1)
    return meta


def parse_feedback(feedback_path: Path) -> tuple[list[dict], list[str]]:
    """从 feedback.md 中提取 verdict 行。

    返回 (signals, unreferenced_sids)：
    - signals: 每条 dict 包含 statement_id, verdict, source_line
    - unreferenced_sids: 文本里出现过 [S-...] 但未匹配到 verdict 的句柄
    """
    signals: list[dict] = []
    unreferenced: list[str] = []
    if not feedback_path.exists():
        return signals, unreferenced
    text = feedback_path.read_text(encoding="utf-8", errors="ignore")
    matched_sids: set[str] = set()
    for line in text.splitlines():
        for m in STMT_VERDICT_RE.finditer(line):
            sid = m.group(1)
            verdict = m.group(2).lower()
            matched_sids.add(sid)
            signals.append({
                "statement_id": sid,
                "verdict": verdict,
                "source_line": line.strip(),
            })
    for m in STMT_REF_RE.finditer(text):
        sid = m.group(1)
        if sid not in matched_sids and sid not in unreferenced:
            unreferenced.append(sid)
    return signals, unreferenced


def render_template(
    case_id: str,
    meta: dict,
    records: list[dict],
) -> str:
    """渲染单个案例的反馈模板（与 statement_records 严格 1:1）。"""
    lines: list[str] = []
    lines.append("# 案例反馈模板（v2）")
    lines.append("")
    lines.append("> 本模板由 `tools/feedback_v2_preprocess.py` 自动生成，"
                 "对应 `cases/<case_id>/statement_records.json::records`。")
    lines.append("> verdict 字段仅允许 `y` / `n` / `skip` / `pending`；其他写法均视为非法，"
                 "摄入阶段会被拒绝。")
    lines.append("")
    lines.append("```yaml")
    lines.append(f"case_id: {case_id}")
    lines.append(f"命主性别: {meta.get('gender') or 'UNKNOWN'}")
    lines.append(f"乾坤: {meta.get('qiankun') or 'UNKNOWN'}")
    lines.append(f"命主出生: {meta.get('birth') or 'UNKNOWN'}")
    lines.append(f"feedback_date: {now_iso()[:10]}")
    lines.append("feedback_method: <面对面/电话/微信/视频/其它>")
    lines.append("reviewer: <命理师代号>")
    lines.append("```")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 断语反馈")
    lines.append("")
    lines.append("> 严格逐条填写；遗漏行将自动标为 `pending`，无法进入 Phase-1000 学习通道。")
    lines.append("")
    if not records:
        lines.append("> ⚠ 该案例 `statement_records.json::records` 为空，"
                     "请先在 `engine/` 中生成 records 后再行反馈；本模板无可列条目。")
        lines.append("")
        return "\n".join(lines) + "\n"
    for idx, r in enumerate(records, 1):
        sid = r.get("statement_id", f"UNMAPPED-{idx:04d}")
        text = (r.get("statement_text") or "").replace("\n", " ").strip()
        rule_id = r.get("rule_id", "UNMAPPED")
        family_id = r.get("family_id", "UNMAPPED")
        school = r.get("school", "UNMAPPED")
        canon = r.get("canon", "UNMAPPED")
        rule_type = r.get("rule_type", "UNMAPPED")
        domain = r.get("domain", "")
        year = r.get("year", "")
        lines.append(f"- [{sid}] {text}")
        lines.append(f"  - rule_id: `{rule_id}` · family_id: `{family_id}` · "
                     f"school: `{school}` · canon: `{canon}` · rule_type: `{rule_type}`"
                     + (f" · domain: `{domain}`" if domain else "")
                     + (f" · year: `{year}`" if year else ""))
        lines.append("  - 反馈 (y/n/skip/pending)：____")
        lines.append("  - 备注（可选）：____")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## 模板版本")
    lines.append("")
    lines.append("v2.0 · 2026-06-12 · 由 `tools/feedback_v2_preprocess.py` 生成")
    lines.append("")
    return "\n".join(lines)


def render_normalized(
    case_id: str,
    records: list[dict],
    by_id: dict[str, dict],
    signals: list[dict],
    unreferenced: list[str],
) -> str:
    """渲染标准化反馈副本：列出每条 statement 的 verdict / 校验状态 / 来源。"""
    lines: list[str] = []
    lines.append(f"# Normalized Feedback · {case_id}")
    lines.append("")
    lines.append(f"> 由 `tools/feedback_v2_preprocess.py` 在 {now_iso()} 生成；"
                 "verdict ∈ {y, n, skip, pending}；不修改 `cases/<case_id>/feedback.md` 原文。")
    lines.append("")
    lines.append("```yaml")
    lines.append(f"case_id: {case_id}")
    lines.append(f"statement_records_total: {len(records)}")
    lines.append(f"feedback_signals_total: {len(signals)}")
    lines.append(f"unreferenced_statement_ids: {len(unreferenced)}")
    lines.append("```")
    lines.append("")
    lines.append("| statement_id | verdict | record_present | rule_id | family_id | school | canon | rule_type | domain | year | note |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|")
    for r in records:
        sid = r.get("statement_id", "")
        text = (r.get("statement_text") or "").replace("\n", " ").replace("|", "/").strip()
        sig = next((s for s in signals if s["statement_id"] == sid), None)
        if sig is None:
            verdict = "pending"
            note = "feedback 缺失 → 自动标 pending"
        else:
            verdict = sig["verdict"]
            note = "from feedback.md"
        if sid not in by_id:
            note = "INVALID_STATEMENT_ID"
        lines.append(
            f"| `{sid}` | `{verdict}` | {'yes' if sid in by_id else 'no'} | "
            f"`{r.get('rule_id', 'UNMAPPED')}` | `{r.get('family_id', 'UNMAPPED')}` | "
            f"`{r.get('school', 'UNMAPPED')}` | `{r.get('canon', 'UNMAPPED')}` | "
            f"`{r.get('rule_type', 'UNMAPPED')}` | "
            f"`{r.get('domain', '')}` | `{r.get('year', '')}` | {note} |"
        )
    if unreferenced:
        lines.append("")
        lines.append("### 未在 verdict 行中引用的 statement_id")
        lines.append("")
        for sid in unreferenced:
            lines.append(f"- `{sid}`")
        lines.append("")
    return "\n".join(lines) + "\n"


def build_mapping_rows(
    case_id: str,
    records: list[dict],
    by_id: dict[str, dict],
    signals: list[dict],
) -> tuple[list[dict], Counter]:
    """构造 (case_id, statement_id, rule_id, ..., verdict) 行，仅 verdict ∈ {y, n} 进入 learning。"""
    rows: list[dict] = []
    verdict_counter: Counter = Counter()
    for r in records:
        sid = r.get("statement_id", "")
        sig = next((s for s in signals if s["statement_id"] == sid), None)
        if sig is None:
            verdict = "pending"
        else:
            verdict = sig["verdict"]
        verdict_counter[verdict] += 1
        valid_record = sid in by_id
        learnable = valid_record and verdict in {"y", "n"}
        rows.append({
            "case_id": case_id,
            "statement_id": sid,
            "rule_id": r.get("rule_id", "UNMAPPED"),
            "family_id": r.get("family_id", "UNMAPPED"),
            "school": r.get("school", "UNMAPPED"),
            "canon": r.get("canon", "UNMAPPED"),
            "rule_type": r.get("rule_type", "UNMAPPED"),
            "verdict": verdict,
            "learnable": str(learnable).lower(),
            "record_present": str(valid_record).lower(),
            "domain": r.get("domain", ""),
            "year": str(r.get("year", "") or ""),
        })
    return rows, verdict_counter


def write_mapping(
    case_id: str,
    rows: list[dict],
) -> tuple[Path, Path]:
    MAPPING_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = MAPPING_DIR / f"{case_id}-mapping.csv"
    json_path = MAPPING_DIR / f"{case_id}-mapping.json"
    fields = [
        "case_id", "statement_id", "rule_id", "family_id", "school",
        "canon", "rule_type", "verdict", "learnable", "record_present",
        "domain", "year",
    ]
    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    json_path.write_text(
        json.dumps(rows, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return csv_path, json_path


def process_case(case_id: str) -> dict:
    case_dir = CASES_ROOT / case_id
    if not case_dir.is_dir():
        return {
            "case_id": case_id,
            "error": f"case dir not found: {case_dir}",
        }
    records, by_id = load_statement_records(case_dir)
    meta = parse_input_meta(case_dir)
    feedback_path = case_dir / "feedback.md"
    signals, unreferenced = parse_feedback(feedback_path)
    norm_dir = case_dir / "normalized-feedback"
    norm_dir.mkdir(parents=True, exist_ok=True)
    template_text = render_template(case_id, meta, records)
    template_path = norm_dir / f"{case_id}-feedback.md"
    template_path.write_text(template_text, encoding="utf-8")
    normalized_text = render_normalized(case_id, records, by_id, signals, unreferenced)
    normalized_path = norm_dir / f"{case_id}-feedback.normalized.md"
    normalized_path.write_text(normalized_text, encoding="utf-8")
    rows, verdict_counter = build_mapping_rows(case_id, records, by_id, signals)
    csv_path, json_path = write_mapping(case_id, rows)
    invalid = [r for r in rows if r["record_present"] == "false"]
    return {
        "case_id": case_id,
        "input_meta": meta,
        "records_total": len(records),
        "signals_total": len(signals),
        "unreferenced": unreferenced,
        "verdict_distribution": dict(verdict_counter),
        "learnable_total": sum(1 for r in rows if r["learnable"] == "true"),
        "pending_total": sum(1 for r in rows if r["verdict"] == "pending"),
        "invalid_statement_id_total": len(invalid),
        "template_path": template_path.as_posix(),
        "normalized_path": normalized_path.as_posix(),
        "mapping_csv": csv_path.as_posix(),
        "mapping_json": json_path.as_posix(),
    }


def render_summary(results: list[dict], source_label: str) -> str:
    lines: list[str] = []
    lines.append("# Feedback V2 Pre-Process Summary")
    lines.append("")
    lines.append(f"> 生成时间：{now_iso()}  ")
    lines.append(f"> 来源：{source_label}  ")
    lines.append("> 工具：`tools/feedback_v2_preprocess.py`  ")
    lines.append("> 约束：未修改 `theory/`、`engine/`、`tests/`、`META/project-state.json`、"
                 "`cases/*/feedback.md` 原文。")
    lines.append("")
    lines.append("## 1. 总体统计")
    lines.append("")
    total_cases = len(results)
    total_records = sum(r.get("records_total", 0) for r in results)
    total_signals = sum(r.get("signals_total", 0) for r in results)
    total_learnable = sum(r.get("learnable_total", 0) for r in results)
    total_pending = sum(r.get("pending_total", 0) for r in results)
    total_invalid = sum(r.get("invalid_statement_id_total", 0) for r in results)
    coverage = (total_signals / total_records) if total_records else 0.0
    lines.append("| metric | value |")
    lines.append("|---|---:|")
    lines.append(f"| `cases_total` | {total_cases} |")
    lines.append(f"| `statement_records_total` | {total_records} |")
    lines.append(f"| `feedback_signals_total` | {total_signals} |")
    lines.append(f"| `feedback_coverage` (signals / records) | {coverage:.1%} |")
    lines.append(f"| `learnable_samples_total` | {total_learnable} |")
    lines.append(f"| `pending_samples_total` | {total_pending} |")
    lines.append(f"| `invalid_statement_id_total` | {total_invalid} |")
    lines.append("")
    verdict_counter: Counter = Counter()
    for r in results:
        verdict_counter.update(r.get("verdict_distribution", {}))
    lines.append("## 2. verdict 分布（仅 {y, n, skip, pending}）")
    lines.append("")
    lines.append("| verdict | rows |")
    lines.append("|---|---:|")
    for v in ["y", "n", "skip", "pending"]:
        lines.append(f"| `{v}` | {verdict_counter.get(v, 0)} |")
    lines.append("")
    lines.append("## 3. 案例级明细")
    lines.append("")
    lines.append("| case_id | records | signals | y | n | skip | pending | learnable | invalid_sid |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for r in results:
        if "error" in r:
            lines.append(f"| `{r['case_id']}` | error | - | - | - | - | - | - | - |")
            continue
        vd = r.get("verdict_distribution", {})
        lines.append(
            f"| `{r['case_id']}` | {r.get('records_total', 0)} | {r.get('signals_total', 0)} | "
            f"{vd.get('y', 0)} | {vd.get('n', 0)} | {vd.get('skip', 0)} | "
            f"{vd.get('pending', 0)} | {r.get('learnable_total', 0)} | "
            f"{r.get('invalid_statement_id_total', 0)} |"
        )
    lines.append("")
    lines.append("## 4. 产物路径")
    lines.append("")
    lines.append("| case_id | 标准化 feedback | 映射 CSV | 映射 JSON |")
    lines.append("|---|---|---|---|")
    for r in results:
        if "error" in r:
            continue
        lines.append(
            f"| `{r['case_id']}` | `{r['normalized_path']}` | `{r['mapping_csv']}` | "
            f"`{r['mapping_json']}` |"
        )
    lines.append("")
    lines.append("## 5. 结论")
    lines.append("")
    lines.append("- verdict 字段已统一为 `{y, n, skip, pending}`，与 Phase-1000 学习通道对齐；"
                 "learnable 样本仅在 verdict ∈ {y, n} 且 statement_id 命中 record 时才计入。")
    lines.append("- 缺失反馈的 statement 一律记 `pending`，可在后续批次补齐后再生成映射。")
    lines.append("- `INVALID_STATEMENT_ID` 数量为 0 表示 feedback.md 引用句柄全部能 join；"
                 "出现 >0 时建议修复 feedback.md 中孤立的 `[S-...]`。")
    lines.append("- 本工具不修改任何规则/权重/置信度；学习通道消费方应读取本工具产出的 CSV/JSON。")
    lines.append("")
    return "\n".join(lines) + "\n"


def render_template_constant() -> str:
    """生成与单案例模板同构的全局模板常量，供其他工具引用。"""
    return (
        "# 案例反馈模板（v2）\n\n"
        "## 字段约定\n\n"
        "- `case_id` 必填，对应 `cases/<case_id>/` 目录名。\n"
        "- `命主性别` 必填，填写 `M` 或 `F`。\n"
        "- `命主出生` 必填，格式 `YYYY-MM-DD HH:MM`。\n"
        "- 每条 statement 反馈行格式：\n\n"
        "```\n"
        "- [<statement_id>] <statement_text>\n"
        "  - 反馈 (y/n/skip/pending)：<y|n|skip|pending>\n"
        "  - 备注（可选）：<free text, 不要重复 verdict>\n"
        "```\n\n"
        "## verdict 含义\n\n"
        "| verdict | 含义 | 是否进入学习通道 |\n"
        "|---|---|---|\n"
        "| `y` | 该 statement 与实际事件一致 | 是 |\n"
        "| `n` | 该 statement 与实际事件不一致 | 是 |\n"
        "| `skip` | 命主无可核验信息 / 不愿披露 | 否 |\n"
        "| `pending` | 尚未收集到反馈 | 否 |\n\n"
        "## 校验\n\n"
        "- 反馈中出现的 `[S-xxxx]` 必须存在于对应 `cases/<case_id>/statement_records.json::records`。"
        "- 不存在的 `statement_id` 在 normalized 副本中标记为 `INVALID_STATEMENT_ID`，"
        "并整体从学习通道中剔除。\n"
        "- verdict 字段只接受 `y` / `n` / `skip` / `pending`，其他值在摄入阶段被拒绝。\n"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="feedback v2 preprocess")
    parser.add_argument("--limit", type=int, default=10,
                        help="处理最近 N 个新案例，默认 10")
    parser.add_argument("--case", type=str, default="",
                        help="指定单个 case_id；提供时忽略 --limit")
    args = parser.parse_args(argv)

    TEMPLATE_OUT.parent.mkdir(parents=True, exist_ok=True)
    TEMPLATE_OUT.write_text(render_template_constant(), encoding="utf-8")

    if args.case:
        case_ids = [args.case]
        source_label = f"explicit case_id={args.case}"
    else:
        case_ids = load_recent_case_ids(args.limit)
        source_label = (
            f"recent {args.limit} cases from "
            f"`META/iteration-state.json::completed_case_ids`"
        )

    results: list[dict] = []
    for cid in case_ids:
        results.append(process_case(cid))

    summary_text = render_summary(results, source_label)
    SUMMARY_OUT.write_text(summary_text, encoding="utf-8")

    print(json.dumps({
        "cases_processed": len(results),
        "summary": SUMMARY_OUT.as_posix(),
        "template": TEMPLATE_OUT.as_posix(),
        "results": [
            {
                "case_id": r["case_id"],
                "records_total": r.get("records_total", 0),
                "verdict_distribution": r.get("verdict_distribution", {}),
                "learnable_total": r.get("learnable_total", 0),
            }
            for r in results
        ],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

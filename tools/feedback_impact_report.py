"""tools/feedback_impact_report.py · feedback impact visualization

Generate a one-glance Markdown report for a structured feedback case:
feedback statement -> mapped rules -> confidence delta.

This tool is read-only by default. It calls feedback_ingest.ingest(..., dry_run=True)
so the rendered before/after values describe the adjustment that will be applied by
feedback_ingest for the same case.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import sys
from collections import defaultdict
from typing import Any

from tools.feedback_ingest import find_case_dir, ingest, parse_statement_feedback

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
REPORTS_DIR = REPO_ROOT / "reports"

_VERDICT_LABELS = {
    "hit": "应验",
    "miss": "失验",
    "abstain": "部分/中性",
    "no_data": "不计数",
}

_VERDICT_ARROWS = {
    "hit": "增强",
    "miss": "削弱",
    "abstain": "观察",
    "no_data": "跳过",
}


def _safe_print(text: str) -> None:
    try:
        print(text)
    except UnicodeEncodeError:
        encoding = sys.stdout.encoding or "utf-8"
        print(text.encode(encoding, errors="replace").decode(encoding, errors="replace"))


def _load_json(path: pathlib.Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _statement_items(statement_index: dict[str, Any]) -> list[dict[str, Any]]:
    raw = statement_index.get("statements", [])
    if isinstance(raw, dict):
        return [dict(value, statement_id=key) for key, value in raw.items() if isinstance(value, dict)]
    if isinstance(raw, list):
        return [item for item in raw if isinstance(item, dict)]
    return []


def _rule_map_items(rule_map: dict[str, Any]) -> dict[str, dict[str, Any]]:
    raw = rule_map.get("statements", rule_map)
    if not isinstance(raw, dict):
        return {}
    out: dict[str, dict[str, Any]] = {}
    for sid, value in raw.items():
        if isinstance(value, dict):
            out[str(sid)] = value
        elif isinstance(value, list):
            out[str(sid)] = {"rule_ids": value}
        elif value:
            out[str(sid)] = {"rule_ids": [str(value)]}
    return out


def _bar(delta_pct: float, width: int = 20) -> str:
    filled = min(width, max(0, int(round(abs(delta_pct) / 10 * width))))
    empty = width - filled
    symbol = "█" if delta_pct >= 0 else "░"
    return symbol * filled + "·" * empty


def _format_pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def _delta_pct(update: dict[str, Any]) -> float:
    posterior = update.get("posterior", {})
    return (float(posterior.get("after", 0.0)) - float(posterior.get("before", 0.0))) * 100


def _statement_summary(case_dir: pathlib.Path) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    feedback_path = case_dir / "feedback.md"
    index_path = case_dir / "statement_index.json"
    map_path = case_dir / "statement_rule_map.json"

    feedbacks = parse_statement_feedback(feedback_path.read_text(encoding="utf-8"))
    feedback_by_sid = {item.statement_id: item for item in feedbacks}
    statements = {str(item.get("statement_id")): item for item in _statement_items(_load_json(index_path))}
    rule_map = _rule_map_items(_load_json(map_path))

    rows: list[dict[str, Any]] = []
    for sid, feedback in feedback_by_sid.items():
        statement = statements.get(sid, {})
        mapping = rule_map.get(sid, {})
        rows.append({
            "statement_id": sid,
            "annotation": feedback.annotation,
            "verdict": feedback.verdict,
            "domain": mapping.get("domain") or statement.get("domain") or "未标注",
            "summary": statement.get("summary") or feedback.raw_line,
            "section": mapping.get("section") or statement.get("section") or "",
            "year": mapping.get("year") or statement.get("year"),
            "rule_ids": [str(rid) for rid in mapping.get("rule_ids", []) if rid],
        })
    return rows, {row["statement_id"]: row for row in rows}


def render_report(case_id: str, *, output_path: str | pathlib.Path | None = None) -> pathlib.Path:
    case_dir = find_case_dir(case_id)
    result = ingest(case_dir.name, dry_run=True)
    diff = result.iteration_diff.to_dict() if result.iteration_diff else {}
    updates = diff.get("rule_updates", [])
    statement_rows, statement_by_sid = _statement_summary(case_dir)

    updates_by_sid: dict[str, list[dict[str, Any]]] = defaultdict(list)
    unmapped_updates: list[dict[str, Any]] = []
    for update in updates:
        note = str(update.get("note", ""))
        linked = False
        for sid in statement_by_sid:
            if sid in note:
                updates_by_sid[sid].append(update)
                linked = True
        if not linked:
            unmapped_updates.append(update)

    for update in unmapped_updates:
        note = str(update.get("note", ""))
        for sid, row in statement_by_sid.items():
            if row.get("section") and str(row["section"]) in note:
                updates_by_sid[sid].append(update)
                break

    total_delta = sum(_delta_pct(update) for update in updates)
    positive = sum(1 for update in updates if _delta_pct(update) > 0)
    negative = sum(1 for update in updates if _delta_pct(update) < 0)
    unchanged = len(updates) - positive - negative
    by_school: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_domain: dict[str, list[dict[str, Any]]] = defaultdict(list)
    rule_to_statement: dict[str, dict[str, Any]] = {}
    for sid, linked_updates in updates_by_sid.items():
        for update in linked_updates:
            rule_to_statement[str(update.get("rule_id"))] = statement_by_sid[sid]
    for update in updates:
        by_school[str(update.get("school", "unknown"))].append(update)
        row = rule_to_statement.get(str(update.get("rule_id")), {})
        by_domain[str(row.get("domain", "未映射"))].append(update)

    generated_at = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines: list[str] = []
    lines.append(f"# {case_dir.name} · 反馈影响路径与置信度调整可视化")
    lines.append("")
    lines.append(f"> 生成时间：{generated_at}；模式：先 dry-run 计算影响，再供正式反馈摄入应用。")
    lines.append("")
    lines.append("## 一眼总览")
    lines.append("")
    lines.append(f"- 反馈断语：{result.feedback_count} 条")
    lines.append(f"- 影响规则：{len(updates)} 条")
    lines.append(f"- 增强 / 削弱 / 不变：{positive} / {negative} / {unchanged}")
    lines.append(f"- 后验置信度净变化：{total_delta:+.1f} 个百分点")
    lines.append(f"- 状态变更：{len(diff.get('status_changes', []))} 条")
    lines.append("")
    lines.append("## 影响路径图")
    lines.append("")
    lines.append("```mermaid")
    lines.append("flowchart LR")
    lines.append(f"  Case[\"{case_dir.name}\"]")
    for row in statement_rows:
        sid = row["statement_id"]
        safe_summary = str(row["summary"]).replace('"', "'")[:36]
        verdict = _VERDICT_LABELS.get(row["verdict"], row["verdict"])
        lines.append(f"  {sid.replace('-', '_')}[\"{sid} {verdict}<br/>{safe_summary}\"]")
        lines.append(f"  Case --> {sid.replace('-', '_')}")
        for update in updates_by_sid.get(sid, []):
            rid = str(update.get("rule_id"))
            node_id = rid.replace("-", "_")
            delta = _delta_pct(update)
            direction = _VERDICT_ARROWS.get(str(update.get("verdict")), "调整")
            lines.append(f"  {sid.replace('-', '_')} -->|{direction} {delta:+.1f}pp| {node_id}[\"{rid}<br/>★{update['star']['before']}→★{update['star']['after']} {_format_pct(update['posterior']['before'])}→{_format_pct(update['posterior']['after'])}\"]")
    lines.append("```")
    lines.append("")
    lines.append("## 调整幅度排行")
    lines.append("")
    lines.append("| 排名 | 规则 | 派别 | 反馈 | 命中 | 失验 | 星级 | 后验变化 | 幅度条 |")
    lines.append("|---:|---|---|---|---|---|---|---:|---|")
    ranked = sorted(updates, key=lambda item: abs(_delta_pct(item)), reverse=True)
    for index, update in enumerate(ranked, start=1):
        delta = _delta_pct(update)
        lines.append(
            f"| {index} | {update['rule_id']} | {update['school']} | {_VERDICT_LABELS.get(update['verdict'], update['verdict'])} | "
            f"{update['hits']['before']}→{update['hits']['after']} | {update['misses']['before']}→{update['misses']['after']} | "
            f"★{update['star']['before']}→★{update['star']['after']} | {_format_pct(update['posterior']['before'])}→{_format_pct(update['posterior']['after'])} ({delta:+.1f}pp) | `{_bar(delta)}` |"
        )
    lines.append("")
    lines.append("## 按领域汇总")
    lines.append("")
    lines.append("| 领域 | 规则数 | 平均调整 | 最大调整 | 方向 |")
    lines.append("|---|---:|---:|---:|---|")
    for domain, items in sorted(by_domain.items()):
        deltas = [_delta_pct(item) for item in items]
        avg = sum(deltas) / len(deltas) if deltas else 0.0
        max_delta = max(deltas, key=abs) if deltas else 0.0
        direction = "增强" if avg > 0 else "削弱" if avg < 0 else "不变"
        lines.append(f"| {domain} | {len(items)} | {avg:+.1f}pp | {max_delta:+.1f}pp | {direction} |")
    lines.append("")
    lines.append("## 按派别汇总")
    lines.append("")
    lines.append("| 派别 | 规则数 | 平均调整 | 星级上调 | 星级下调 |")
    lines.append("|---|---:|---:|---:|---:|")
    for school, items in sorted(by_school.items()):
        deltas = [_delta_pct(item) for item in items]
        avg = sum(deltas) / len(deltas) if deltas else 0.0
        star_up = sum(1 for item in items if item["star"]["after"] > item["star"]["before"])
        star_down = sum(1 for item in items if item["star"]["after"] < item["star"]["before"])
        lines.append(f"| {school} | {len(items)} | {avg:+.1f}pp | {star_up} | {star_down} |")
    lines.append("")
    lines.append("## 断语到规则明细")
    lines.append("")
    lines.append("| 断语 | 领域 | 核验结论 | 影响规则 | 影响说明 |")
    lines.append("|---|---|---|---|---|")
    for row in statement_rows:
        linked_updates = updates_by_sid.get(row["statement_id"], [])
        if linked_updates:
            rule_ids = ", ".join(str(item.get("rule_id")) for item in linked_updates)
            impact = "; ".join(
                f"{item['rule_id']} {_format_pct(item['posterior']['before'])}→{_format_pct(item['posterior']['after'])} ({_delta_pct(item):+.1f}pp)"
                for item in linked_updates
            )
        else:
            rule_ids = "—"
            impact = "无 rule_ids 映射或反馈不计数"
        verdict = _VERDICT_LABELS.get(row["verdict"], row["verdict"])
        summary = str(row["summary"]).replace("|", " / ")
        lines.append(f"| {row['statement_id']} | {row['domain']} | {verdict} | {rule_ids} | {summary}<br/>{impact} |")
    lines.append("")
    lines.append("## 审计说明")
    lines.append("")
    lines.append("- 本报告不直接修改理论库；实际写入由 feedback_ingest 完成。")
    lines.append("- 星级与百分比来自同一次 dry-run 产生的 IterationDiff。")
    lines.append("- no_data / skip / 未映射规则不参与动态置信度计分。")

    target = pathlib.Path(output_path) if output_path else REPORTS_DIR / f"{case_dir.name}-feedback-impact.md"
    if not target.is_absolute():
        target = REPO_ROOT / target
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return target


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="生成反馈影响路径与置信度调整可视化 Markdown")
    parser.add_argument("case_id", help="案例 ID 或唯一前缀")
    parser.add_argument("--output", default=None, help="输出 Markdown 路径；默认 reports/<case_id>-feedback-impact.md")
    args = parser.parse_args(argv)
    path = render_report(args.case_id, output_path=args.output)
    _safe_print(str(path.relative_to(REPO_ROOT)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

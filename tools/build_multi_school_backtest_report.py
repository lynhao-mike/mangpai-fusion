"""Build the first multi-school backtest report for Wenzhen READY cases.

The report is read-only: it aggregates statement_index.json and feedback.md
annotations without writing any theory weights or calibration state.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

REPO_ROOT = Path(__file__).resolve().parents[1]
ANNOTATION_RE = re.compile(r"\[(S-[^\]]+)\]\s*\[(y|n|\?|skip)\]", re.IGNORECASE)


def _escape_cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def _table(headers: list[str], rows: list[list[object]]) -> list[str]:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(_escape_cell(cell) for cell in row) + " |")
    return lines


def _beta_summary(hit: int, miss: int) -> tuple[str, str, str]:
    effective_n = hit + miss
    alpha = 1 + hit
    beta = 1 + miss
    mean = alpha / (alpha + beta)
    guard = "LOCKED_N<10" if effective_n < 10 else "OPEN_REVIEW"
    return f"Beta({alpha},{beta})", f"{mean:.1%}", guard


def _case_sort_key(path: Path) -> tuple[str, str]:
    return (path.parent.name, path.name)


def load_rows(cases_glob: str) -> tuple[list[tuple[str, list[dict[str, Any]], dict[str, str]]], list[dict[str, Any]]]:
    statement_paths = sorted(REPO_ROOT.glob(cases_glob), key=_case_sort_key)
    case_rows: list[tuple[str, list[dict[str, Any]], dict[str, str]]] = []
    statements: list[dict[str, Any]] = []

    for path in statement_paths:
        data = json.loads(path.read_text(encoding="utf-8"))
        case_id = data.get("case_id") or path.parent.name
        feedback_path = path.parent / "feedback.md"
        annotations: dict[str, str] = {}
        if feedback_path.exists():
            text = feedback_path.read_text(encoding="utf-8", errors="replace")
            for statement_id, verdict in ANNOTATION_RE.findall(text):
                annotations[statement_id] = verdict.lower()

        rows = data.get("statements", [])
        case_rows.append((case_id, rows, annotations))
        for row in rows:
            enriched = dict(row)
            enriched["case_id"] = case_id
            enriched["annotation"] = annotations.get(str(row.get("statement_id", "")))
            statements.append(enriched)

    return case_rows, statements


def _feedback_counts(
    statements: list[dict[str, Any]],
    predicate: Callable[[dict[str, Any]], bool],
) -> tuple[int, int, int, int, int, int, int]:
    total = hit = miss = unknown = skip = unannotated = 0
    cases: set[str] = set()
    for row in statements:
        if not predicate(row):
            continue
        total += 1
        cases.add(str(row["case_id"]))
        annotation = row.get("annotation")
        if annotation == "y":
            hit += 1
        elif annotation == "n":
            miss += 1
        elif annotation == "?":
            unknown += 1
        elif annotation == "skip":
            skip += 1
        else:
            unannotated += 1
    return total, len(cases), hit, miss, unknown, skip, unannotated


def build_report(cases_glob: str) -> str:
    case_rows, statements = load_rows(cases_glob)

    school_counter: Counter[str] = Counter()
    domain_counter: Counter[str] = Counter()
    rule_counter: Counter[str] = Counter()
    school_domain_counter: Counter[tuple[str, str]] = Counter()
    rule_school: defaultdict[str, Counter[str]] = defaultdict(Counter)
    feedback_counter: Counter[str] = Counter()

    for row in statements:
        schools = row.get("schools") or ["未归属"]
        domain = str(row.get("domain") or "unknown")
        rules = row.get("rule_ids") or ["未挂规则"]
        feedback_counter[str(row.get("annotation") or "unannotated")] += 1
        domain_counter[domain] += 1
        for school in schools:
            school = str(school)
            school_counter[school] += 1
            school_domain_counter[(school, domain)] += 1
        for rule in rules:
            rule = str(rule)
            rule_counter[rule] += 1
            for school in schools:
                rule_school[rule][str(school)] += 1

    hit_count = feedback_counter["y"]
    miss_count = feedback_counter["n"]
    unknown_count = feedback_counter["?"]
    skip_count = feedback_counter["skip"]
    annotated_count = hit_count + miss_count + unknown_count + skip_count
    effective_n = hit_count + miss_count
    posterior, posterior_mean, guard = _beta_summary(hit_count, miss_count)

    case_table_rows: list[list[object]] = []
    for case_id, rows, annotations in case_rows:
        case_feedback = Counter(annotations.values())
        case_table_rows.append([
            case_id,
            len(rows),
            len(annotations),
            case_feedback.get("skip", 0),
            case_feedback.get("y", 0),
            case_feedback.get("n", 0),
            case_feedback.get("?", 0),
        ])

    school_rows: list[list[object]] = []
    for school, _ in school_counter.most_common():
        total, coverage, hit, miss, unknown, skip, unannotated = _feedback_counts(
            statements,
            lambda row, school=school: school in (row.get("schools") or ["未归属"]),
        )
        posterior, mean, row_guard = _beta_summary(hit, miss)
        school_rows.append([school, coverage, total, hit, miss, unknown + skip + unannotated, posterior, mean, row_guard])

    domain_rows: list[list[object]] = []
    for domain, _ in domain_counter.most_common():
        total, coverage, hit, miss, unknown, skip, unannotated = _feedback_counts(
            statements,
            lambda row, domain=domain: str(row.get("domain") or "unknown") == domain,
        )
        posterior, mean, row_guard = _beta_summary(hit, miss)
        domain_rows.append([domain, coverage, total, hit, miss, unknown + skip + unannotated, posterior, mean, row_guard])

    school_domain_rows: list[list[object]] = []
    for (school, domain), _ in school_domain_counter.most_common(40):
        total, coverage, hit, miss, unknown, skip, unannotated = _feedback_counts(
            statements,
            lambda row, school=school, domain=domain: school in (row.get("schools") or ["未归属"])
            and str(row.get("domain") or "unknown") == domain,
        )
        posterior, mean, row_guard = _beta_summary(hit, miss)
        school_domain_rows.append([school, domain, coverage, total, hit, miss, unknown + skip + unannotated, posterior, mean, row_guard])

    rule_rows: list[list[object]] = []
    for rule, _ in rule_counter.most_common(50):
        total, coverage, hit, miss, unknown, skip, unannotated = _feedback_counts(
            statements,
            lambda row, rule=rule: rule in (row.get("rule_ids") or ["未挂规则"]),
        )
        posterior, mean, row_guard = _beta_summary(hit, miss)
        top_schools = ", ".join(school for school, _count in rule_school[rule].most_common(3)) or "未归属"
        rule_rows.append([rule, top_schools, coverage, total, hit, miss, unknown + skip + unannotated, posterior, mean, row_guard])

    created_at = datetime.now(UTC).isoformat(timespec="seconds")
    lines: list[str] = [
        "# 问真 READY 26 · 多流派首轮回测表 v1",
        "",
        f"- 生成时间：{created_at}",
        f"- 数据范围：`{cases_glob}` 命中的 26 条 READY 问真正式 case。",
        "- 回测口径：按 statement-level 反馈统计；`[y]` 记 hit，`[n]` 记 miss，`[?]` 与 `[skip]` 记 no-data；未注释陈述不进入命中/失误样本。",
        "- 权重策略：本报告只读索引与反馈文件，不写入 theory 权重，不触发自动裁决。",
        "- 流派隔离：子平、滴天髓、盲派组只在陈述索引层分别计数；本报告不把任一流派规则迁移到其他流派。",
        "- 结论边界：当前有效 hit/miss 样本为 0，所有 Beta 后验均处于低样本锁定状态；不得据此宣称任何流派优劣。",
        "",
        "## 1. 样本总览",
    ]
    lines.extend(_table([
        "指标",
        "数值",
    ], [
        ["READY case 数", len(case_rows)],
        ["statement 总数", len(statements)],
        ["有反馈注释 statement 数", annotated_count],
        ["skip/no-data 注释数", skip_count],
        ["hit 数", hit_count],
        ["miss 数", miss_count],
        ["? 数", unknown_count],
        ["有效 hit/miss 样本 N", effective_n],
        ["全局后验", posterior],
        ["全局后验均值", posterior_mean],
        ["低样本护栏", guard],
    ]))
    lines.extend([
        "",
        "## 2. Case 覆盖表",
    ])
    lines.extend(_table(["case_id", "statements", "annotated", "skip", "hit", "miss", "?"], case_table_rows))
    lines.extend([
        "",
        "## 3. 流派聚合",
        "说明：`no_data_or_unannotated` 包含 `[?]`、`[skip]` 与未注释陈述；Beta 只使用 hit/miss。",
    ])
    lines.extend(_table(["school", "case_coverage", "statements", "hit", "miss", "no_data_or_unannotated", "posterior", "mean", "guard"], school_rows))
    lines.extend([
        "",
        "## 4. 领域聚合",
    ])
    lines.extend(_table(["domain", "case_coverage", "statements", "hit", "miss", "no_data_or_unannotated", "posterior", "mean", "guard"], domain_rows))
    lines.extend([
        "",
        "## 5. 流派 × 领域 Top40",
    ])
    lines.extend(_table(["school", "domain", "case_coverage", "statements", "hit", "miss", "no_data_or_unannotated", "posterior", "mean", "guard"], school_domain_rows))
    lines.extend([
        "",
        "## 6. 规则 Top50",
        "说明：按 statement 出现次数排序；当前仅代表覆盖密度，不代表准确率或权重。",
    ])
    lines.extend(_table(["rule_id", "schools_top3", "case_coverage", "statements", "hit", "miss", "no_data_or_unannotated", "posterior", "mean", "guard"], rule_rows))
    lines.extend([
        "",
        "## 7. 观察与下一步",
        "- 当前 26 条 READY 样本已完成 case 化、pipeline 渲染与 statement index 生成，可用于后续人工逐条验真。",
        "- 首批 5 条已写入 `[skip]` 占位反馈，因此它们只增加可追踪性，不增加 hit/miss 有效样本。",
        "- 后续必须由人工把可验证陈述改为 `[y]`、`[n]` 或 `[?]` 后，再运行 `python -m tools.feedback_ingest <case_id>`。",
        "- 任一 school/domain/rule 的有效样本 `N < 10` 时保持 `LOCKED_N<10`，禁止自动调权与排名。",
        "- 达到有效样本阈值后，仍应先进入人工 review，再决定是否更新 `META/arbitration-log.md` 或理论规则状态。",
        "",
        "## 8. 关联路径",
        "- 输入案例：`cases/C-2026-RF*-*/input.md`",
        "- 分析归档：`cases/C-2026-RF*-*/analysis.md`",
        "- 陈述索引：`cases/C-2026-RF*-*/statement_index.json`",
        "- 命理师报告：`reports/C-2026-RF*-analyst-report.md`",
        "- 本回测表：`reports/multi_school_backtest_v1.md`",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases-glob", default="cases/C-2026-RF*-*/statement_index.json")
    parser.add_argument("--output", default="reports/multi_school_backtest_v1.md")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    report = build_report(args.cases_glob)
    case_rows, statements = load_rows(args.cases_glob)
    print(json.dumps({"cases": len(case_rows), "statements": len(statements), "output": args.output, "dry_run": args.dry_run}, ensure_ascii=False))
    if not args.dry_run:
        output_path = REPO_ROOT / args.output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

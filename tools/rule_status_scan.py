"""tools/rule_status_scan.py · 规律状态扫描器

用途：
    扫描 theory/{duan,yang,gao,ren}/index.yaml，输出当前规则状态分布、N_eff、
    flagged_for_review/deprecated 清单与需要人工 review 的规则列表。

只读工具：不会修改理论库。

示例：
    python tools/rule_status_scan.py --format markdown
    python tools/rule_status_scan.py --format json
    python tools/rule_status_scan.py --check
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from typing import Any

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
THEORY_DIR = ROOT / "theory"
SCHOOLS = ("duan", "yang", "gao", "ren")
VALID_STATUSES = {"proposed", "candidate", "confirmed", "flagged_for_review", "deprecated"}
LEGACY_STATUS_MAP = {
    "promoted": "confirmed",
    "candidate": "candidate",
    "frozen": "deprecated",
    "retired": "deprecated",
    # 理论抽取迁移中的暂存状态：仍未归一化，不进入生命周期状态机；扫描器
    # 单独统计为 pending_normalization，避免把迁移队列误报为非法状态。
    "pending_normalization": "pending_normalization",
}
REPORT_STATUSES = VALID_STATUSES | {"pending_normalization"}


@dataclass(frozen=True)
class RuleRow:
    id: str
    school: str
    topic: str
    status: str
    normalized_status: str
    hits: int
    misses: int
    abstained: int
    quantifiable: bool
    domain_restriction: list[str] = field(default_factory=list)
    title: str = ""

    @property
    def effective_n(self) -> int:
        return self.hits + self.misses if self.quantifiable else 0

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["effective_n"] = self.effective_n
        return d


@dataclass(frozen=True)
class RuleStatusReport:
    total_rules: int
    n_eff: int
    by_status: dict[str, int]
    by_school: dict[str, dict[str, int]]
    flagged_for_review: list[RuleRow]
    deprecated: list[RuleRow]
    legacy_status_count: int
    invalid_status: list[RuleRow]

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_rules": self.total_rules,
            "n_eff": self.n_eff,
            "by_status": self.by_status,
            "by_school": self.by_school,
            "flagged_for_review": [r.to_dict() for r in self.flagged_for_review],
            "deprecated": [r.to_dict() for r in self.deprecated],
            "legacy_status_count": self.legacy_status_count,
            "invalid_status": [r.to_dict() for r in self.invalid_status],
        }


def _read_yaml(path: pathlib.Path) -> dict[str, Any]:
    if not path.exists():
        return {"rules": []}
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {"rules": []}


def _normalize_status(status: str) -> str:
    if status in REPORT_STATUSES:
        return status
    return LEGACY_STATUS_MAP.get(status, "invalid")


def _as_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def scan_rules() -> list[RuleRow]:
    rows: list[RuleRow] = []
    for school in SCHOOLS:
        path = THEORY_DIR / school / "index.yaml"
        data = _read_yaml(path)
        for entry in data.get("rules", []) or []:
            if not isinstance(entry, dict):
                continue
            status = str(entry.get("status", "proposed"))
            rows.append(RuleRow(
                id=str(entry.get("id", "")),
                school=str(entry.get("school", school)),
                topic=str(entry.get("topic", "")),
                status=status,
                normalized_status=_normalize_status(status),
                hits=_as_int(entry.get("hits", 0)),
                misses=_as_int(entry.get("misses", 0)),
                abstained=_as_int(entry.get("abstained", 0)),
                quantifiable=bool(entry.get("quantifiable", True)),
                domain_restriction=list(entry.get("domain_restriction", []) or []),
                title=str(entry.get("title", "")),
            ))
    return rows


def build_report(rows: list[RuleRow] | None = None) -> RuleStatusReport:
    rows = rows if rows is not None else scan_rules()
    by_status_counter: Counter[str] = Counter(r.normalized_status for r in rows)
    by_school_counter: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        by_school_counter[row.school][row.normalized_status] += 1

    return RuleStatusReport(
        total_rules=len(rows),
        n_eff=sum(r.effective_n for r in rows),
        by_status=dict(sorted(by_status_counter.items())),
        by_school={school: dict(sorted(counter.items())) for school, counter in sorted(by_school_counter.items())},
        flagged_for_review=sorted(
            [r for r in rows if r.normalized_status == "flagged_for_review"],
            key=lambda r: (r.school, r.id),
        ),
        deprecated=sorted(
            [r for r in rows if r.normalized_status == "deprecated"],
            key=lambda r: (r.school, r.id),
        ),
        legacy_status_count=sum(1 for r in rows if r.status in LEGACY_STATUS_MAP and r.status != r.normalized_status),
        invalid_status=sorted(
            [r for r in rows if r.normalized_status == "invalid"],
            key=lambda r: (r.school, r.id),
        ),
    )


def _status_counts_table(counts: dict[str, int]) -> list[str]:
    lines = ["| status | count |", "|---|---:|"]
    for status in sorted(counts):
        lines.append(f"| {status} | {counts[status]} |")
    return lines


def _rule_list_table(rows: list[RuleRow]) -> list[str]:
    lines = ["| id | school | topic | hits | misses | title |", "|---|---|---|---:|---:|---|"]
    if not rows:
        lines.append("| — | — | — | — | — | — |")
        return lines
    for row in rows:
        title = row.title.replace("|", "\\|")
        lines.append(f"| {row.id} | {row.school} | {row.topic} | {row.hits} | {row.misses} | {title} |")
    return lines


def report_to_markdown(report: RuleStatusReport) -> str:
    lines = [
        "# rule status scan",
        "",
        f"- total_rules: {report.total_rules}",
        f"- N_eff: {report.n_eff}",
        f"- legacy_status_count: {report.legacy_status_count}",
        "",
        "## status distribution",
        "",
        *_status_counts_table(report.by_status),
        "",
        "## by school",
        "",
    ]
    for school, counts in report.by_school.items():
        lines.append(f"### {school}")
        lines.append("")
        lines.extend(_status_counts_table(counts))
        lines.append("")

    lines.extend([
        "## flagged_for_review",
        "",
        *_rule_list_table(report.flagged_for_review),
        "",
        "## deprecated",
        "",
        *_rule_list_table(report.deprecated),
        "",
    ])
    if report.invalid_status:
        lines.extend([
            "## invalid status",
            "",
            *_rule_list_table(report.invalid_status),
            "",
        ])
    return "\n".join(lines)


def report_to_json(report: RuleStatusReport) -> str:
    return json.dumps(report.to_dict(), ensure_ascii=False, indent=2)


def check_report(report: RuleStatusReport) -> list[str]:
    problems: list[str] = []
    if report.invalid_status:
        problems.append(f"invalid status rows: {len(report.invalid_status)}")
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scan theory rule lifecycle status distribution.")
    parser.add_argument("--format", choices=("json", "markdown"), default="markdown")
    parser.add_argument("--check", action="store_true", help="exit non-zero if invalid statuses are found")
    args = parser.parse_args(argv)

    report = build_report()
    if args.check:
        problems = check_report(report)
        if problems:
            print("rule status scan failed:", file=sys.stderr)
            for p in problems:
                print(f"- {p}", file=sys.stderr)
            return 1
        print("rule status scan passed")
        return 0

    if args.format == "json":
        print(report_to_json(report))
    else:
        print(report_to_markdown(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

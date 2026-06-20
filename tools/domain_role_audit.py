"""tools/domain_role_audit.py · domain/role 分账审计矩阵

用途：
    扫描 theory/{duan,yang,gao,ren}/index.yaml 中的 domain_role_stats，输出
    rule_id × domain × role 的独立命中率矩阵，用于验证域感知 RL 分账是否生效。

只读工具：不会修改理论库。

示例：
    python tools/domain_role_audit.py
    python tools/domain_role_audit.py --format markdown --min-n 1
    python tools/domain_role_audit.py --format csv --school yang
    python tools/domain_role_audit.py --format json --include-empty
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import pathlib
import sys
from dataclasses import asdict, dataclass
from typing import Any, Iterable, Optional

ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.rule_lifecycle import (
    DomainRoleStats,
    Rule,
    RuleYamlStore,
    compute_rule_confidence,
    list_rule_ids,
)


@dataclass(frozen=True)
class DomainRoleAuditRow:
    rule_id: str
    school: str
    topic: str
    status: str
    domain: str
    role: str
    hits: int
    misses: int
    abstained: int
    n: int
    hit_rate: float
    posterior: float
    star: int

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["hit_rate_pct"] = round(self.hit_rate * 100, 2)
        data["posterior_pct"] = round(self.posterior * 100, 2)
        return data


def _safe_print(text: str = "") -> None:
    try:
        print(text)
    except UnicodeEncodeError:
        encoding = sys.stdout.encoding or "utf-8"
        print(text.encode(encoding, errors="replace").decode(encoding, errors="replace"))


def _confidence_for(stats: DomainRoleStats) -> tuple[float, int]:
    if stats.confidence_cache is not None:
        return stats.confidence_cache.posterior, stats.confidence_cache.star
    confidence = compute_rule_confidence(stats.hits, stats.misses)
    return confidence.posterior, confidence.star


def _iter_rows_for_rule(rule: Rule, *, include_empty: bool = False) -> Iterable[DomainRoleAuditRow]:
    for domain, roles in sorted(rule.domain_role_stats.items()):
        for role, stats in sorted(roles.items()):
            if not include_empty and stats.n == 0 and stats.abstained == 0:
                continue
            posterior, star = _confidence_for(stats)
            yield DomainRoleAuditRow(
                rule_id=rule.id,
                school=rule.school,
                topic=rule.topic,
                status=rule.status,
                domain=str(domain),
                role=str(role),
                hits=int(stats.hits),
                misses=int(stats.misses),
                abstained=int(stats.abstained),
                n=int(stats.n),
                hit_rate=float(stats.hit_rate),
                posterior=float(posterior),
                star=int(star),
            )


def scan_domain_role_stats(
    *,
    school: Optional[str] = None,
    min_n: int = 0,
    include_empty: bool = False,
    domain: Optional[str] = None,
    role: Optional[str] = None,
) -> list[DomainRoleAuditRow]:
    """扫描规则库并返回 rule_id × domain × role 审计行。"""
    rows: list[DomainRoleAuditRow] = []
    store = RuleYamlStore()
    for rule_id in list_rule_ids(school=school):
        rule = store.load_rule(rule_id)
        for row in _iter_rows_for_rule(rule, include_empty=include_empty):
            if row.n < min_n:
                continue
            if domain is not None and row.domain != domain:
                continue
            if role is not None and row.role != role:
                continue
            rows.append(row)
    return sorted(rows, key=lambda r: (r.school, r.rule_id, r.domain, r.role))


def _escape_md(value: Any) -> str:
    return str(value).replace("|", "\\|")


def rows_to_markdown(rows: list[DomainRoleAuditRow]) -> str:
    lines = [
        "# domain/role audit",
        "",
        f"- rows: {len(rows)}",
        "",
        "| rule_id | school | topic | status | domain | role | hits | misses | abstained | n | hit_rate | posterior | star |",
        "|---|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    if not rows:
        lines.append("| — | — | — | — | — | — | 0 | 0 | 0 | 0 | 0.0% | 0.0% | 0 |")
        return "\n".join(lines)
    for row in rows:
        lines.append(
            "| "
            + " | ".join([
                _escape_md(row.rule_id),
                _escape_md(row.school),
                _escape_md(row.topic),
                _escape_md(row.status),
                _escape_md(row.domain),
                _escape_md(row.role),
                str(row.hits),
                str(row.misses),
                str(row.abstained),
                str(row.n),
                f"{row.hit_rate * 100:.1f}%",
                f"{row.posterior * 100:.1f}%",
                str(row.star),
            ])
            + " |"
        )
    return "\n".join(lines)


def rows_to_csv(rows: list[DomainRoleAuditRow]) -> str:
    buffer = io.StringIO()
    fieldnames = [
        "rule_id",
        "school",
        "topic",
        "status",
        "domain",
        "role",
        "hits",
        "misses",
        "abstained",
        "n",
        "hit_rate",
        "posterior",
        "star",
    ]
    writer = csv.DictWriter(buffer, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({key: getattr(row, key) for key in fieldnames})
    return buffer.getvalue().rstrip("\n")


def rows_to_json(rows: list[DomainRoleAuditRow]) -> str:
    return json.dumps([row.to_dict() for row in rows], ensure_ascii=False, indent=2)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="输出 rule_id × domain × role 命中率审计矩阵")
    parser.add_argument("--format", choices=("markdown", "csv", "json"), default="markdown")
    parser.add_argument("--school", default=None, help="可选：限制派别，如 duan/yang/gao/ren 或 段/杨/高/任")
    parser.add_argument("--domain", default=None, help="可选：只输出指定 domain")
    parser.add_argument("--role", default=None, help="可选：只输出指定 role，如 evidence/trigger/misapplied/unknown")
    parser.add_argument("--min-n", type=int, default=0, help="只输出 n >= min_n 的分账桶")
    parser.add_argument("--include-empty", action="store_true", help="包含 n=0 且 abstained=0 的空桶")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    rows = scan_domain_role_stats(
        school=args.school,
        min_n=max(0, int(args.min_n)),
        include_empty=bool(args.include_empty),
        domain=args.domain,
        role=args.role,
    )
    if args.format == "json":
        _safe_print(rows_to_json(rows))
    elif args.format == "csv":
        _safe_print(rows_to_csv(rows))
    else:
        _safe_print(rows_to_markdown(rows))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

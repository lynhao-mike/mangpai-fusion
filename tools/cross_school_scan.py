"""tools/cross_school_scan.py · v1.2 Track-G 跨派一致性扫描

落地契约：
    engine/contracts/05-rule-lifecycle.md § 十一
    决策 K（每 10 案触发一次）

职责：
    对每个领域（婚姻/财运/学业/健康/事业/六亲），统计最近 N 案中
    4 派各自的 hit_rate；
    若 max - min > cross_school_gap_threshold 持续 ≥ window 案 → 标系统性偏差，
    写入 META/conflict-trends.md。

约束：
    本工具**不自动调权重**（决策 K）——只生成报告，由架构师人工 review 后
    开 PR 修 engine/domain-weights.yaml。

数据源：
    遍历 4 个 theory/{school}/index.yaml 的 applied_cases 字段。每个 case 在
    每条规律下贡献一个 hit/miss 记录；按"派别 + topic"汇总即得 hit_rate。

作者：Track-G
"""
from __future__ import annotations

import datetime as _dt
import math
import pathlib
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Optional

import yaml

from tools.rule_lifecycle import (
    LifecycleConfig,
    SCHOOL_DIR_MAP,
    SCHOOL_TO_CN,
    THEORY_DIR,
)

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
META_DIR = REPO_ROOT / "META"
CONFLICT_TRENDS = META_DIR / "conflict-trends.md"


# ============================================================
# 一、领域映射（topic → domain 中文名）
# ============================================================

# theory/{school}/index.yaml 里的 topic 字段使用拼音；这里映射到契约
# 里使用的中文领域名。
TOPIC_TO_DOMAIN: dict[str, str] = {
    "hunyin": "婚姻",
    "caiyun": "财运",
    "jiaoyu": "学业",
    "jiankang": "健康",
    "shiye": "事业",
    "liuqin": "六亲",
    # 其他 topic（lifa / geju / tiaohou / unmapped）不进领域聚合
}

DOMAINS = ["婚姻", "事业", "财运", "健康", "学业", "六亲"]


# ============================================================
# 二、报告数据结构
# ============================================================

@dataclass
class SchoolDomainStat:
    school: str          # 中文 段杨高任
    domain: str          # 中文 婚姻/事业/...
    hits: int = 0
    misses: int = 0

    @property
    def n(self) -> int:
        return self.hits + self.misses

    @property
    def hit_rate(self) -> Optional[float]:
        return (self.hits / self.n) if self.n > 0 else None

    @property
    def beta_mean(self) -> Optional[float]:
        """Beta(1,1) 先验下的后验均值，用于小样本时避免 0/100% 过度自信。"""
        return ((self.hits + 1) / (self.n + 2)) if self.n > 0 else None

    def wilson_interval(self, z: float = 1.96) -> tuple[Optional[float], Optional[float]]:
        """Wilson 置信区间；n=0 时返回空值。"""
        if self.n <= 0:
            return None, None
        phat = self.hits / self.n
        denom = 1 + z * z / self.n
        centre = phat + z * z / (2 * self.n)
        spread = z * math.sqrt((phat * (1 - phat) + z * z / (4 * self.n)) / self.n)
        return max(0.0, (centre - spread) / denom), min(1.0, (centre + spread) / denom)

    def to_report_cell(self) -> dict[str, float | int | None]:
        lo, hi = self.wilson_interval()
        return {
            "hits": self.hits,
            "misses": self.misses,
            "n": self.n,
            "hit_rate": self.hit_rate,
            "beta_mean": self.beta_mean,
            "ci_low": lo,
            "ci_high": hi,
        }


@dataclass
class SystematicBias:
    domain: str
    strong_school: str
    strong_rate: float
    weak_school: str
    weak_rate: float
    gap: float
    sample_n: int
    recommendation: str


@dataclass
class ConflictTrendsReport:
    date: str
    case_count: int
    triggered_by: str
    biases: list[SystematicBias] = field(default_factory=list)
    domain_table: dict[str, dict[str, dict[str, float | int | None]]] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    def to_markdown(self) -> str:
        lines: list[str] = []
        lines.append(f"## {self.date} · Cross-School Scan #{self.case_count}")
        lines.append("")
        lines.append(f"trigger: ingest of `{self.triggered_by}` (case_count={self.case_count})")
        lines.append("")

        # 总表
        lines.append("### 各领域 4 派 hit_rate / Beta后验 / Wilson区间")
        lines.append("")
        lines.append("| 领域 | 段 | 杨 | 高 | 任 |")
        lines.append("|---|---|---|---|---|")
        for domain in DOMAINS:
            row = self.domain_table.get(domain, {})
            cells = []
            for sch in ("段", "杨", "高", "任"):
                e = row.get(sch, {}) if isinstance(row, dict) else {}
                rate = e.get("hit_rate")
                beta = e.get("beta_mean")
                lo = e.get("ci_low")
                hi = e.get("ci_high")
                n = e.get("n", 0)
                if rate is None:
                    cells.append(f"— (n={n})")
                else:
                    cells.append(
                        f"raw={rate:.0%}, beta={beta:.0%}, "
                        f"95%CI={lo:.0%}-{hi:.0%}, n={n}"
                    )
            lines.append(f"| {domain} | " + " | ".join(cells) + " |")
        lines.append("")

        # 系统性偏差
        lines.append("### 系统性偏差")
        if not self.biases:
            lines.append("")
            lines.append("无（4 派在所有领域差距 ≤ 阈值，或样本不足）。")
        else:
            lines.append("")
            for b in self.biases:
                lines.append(
                    f"- **{b.domain}**: {b.strong_school} ({b.strong_rate:.0%}) "
                    f"vs {b.weak_school} ({b.weak_rate:.0%})，gap={b.gap:.0%}，"
                    f"sample={b.sample_n}"
                )
                lines.append(f"  - 建议：{b.recommendation}")
        lines.append("")

        if self.notes:
            lines.append("### Notes")
            lines.append("")
            for n in self.notes:
                lines.append(f"- {n}")
            lines.append("")

        return "\n".join(lines)


# ============================================================
# 三、统计逻辑
# ============================================================

def _read_yaml(p: pathlib.Path) -> dict[str, Any]:
    if not p.exists():
        return {}
    with p.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _collect_school_domain_stats() -> dict[tuple[str, str], SchoolDomainStat]:
    """遍历 4 派 yaml，按 (school_cn, domain_cn) 累加 hit/miss。"""
    stats: dict[tuple[str, str], SchoolDomainStat] = {}
    for sub in ("duan", "yang", "gao", "ren"):
        path = THEORY_DIR / sub / "index.yaml"
        if not path.exists():
            continue
        data = _read_yaml(path)
        school_cn = SCHOOL_TO_CN[sub]
        for entry in data.get("rules", []):
            topic = str(entry.get("topic", ""))
            domain = TOPIC_TO_DOMAIN.get(topic)
            if domain is None:
                continue
            applied = entry.get("applied_cases") or []
            hits = sum(1 for a in applied if a.get("hit") is True)
            misses = sum(1 for a in applied if a.get("hit") is False)
            if hits == 0 and misses == 0:
                # 兜底用 hits/misses 字段（v1.2 之前未维护 applied_cases）
                hits = int(entry.get("hits", 0))
                misses = int(entry.get("misses", 0))
            key = (school_cn, domain)
            s = stats.setdefault(key, SchoolDomainStat(school=school_cn, domain=domain))
            s.hits += hits
            s.misses += misses
    return stats


def cross_school_scan(
    *,
    triggered_by: str = "(unknown)",
    cfg: Optional[LifecycleConfig] = None,
    write: bool = True,
) -> ConflictTrendsReport:
    """05 § 十一 跨派扫描主函数。

    Parameters
    ----------
    triggered_by : str
        触发本次扫描的 case_id（用于 audit）。
    cfg : LifecycleConfig
    write : bool
        是否将结果追加到 META/conflict-trends.md。

    Returns
    -------
    ConflictTrendsReport
    """
    cfg = cfg or LifecycleConfig.from_yaml()
    today = _dt.date.today().isoformat()

    # case_count 用 cases/ 目录数（与 feedback_loop.total_case_count 同口径）
    cases_dir = REPO_ROOT / "cases"
    import re
    pattern = re.compile(r"^C-\d{4}-\d{3}-")
    case_count = sum(
        1 for p in cases_dir.iterdir()
        if cases_dir.exists() and p.is_dir() and pattern.match(p.name)
    )

    report = ConflictTrendsReport(
        date=today,
        case_count=case_count,
        triggered_by=triggered_by,
    )

    stats = _collect_school_domain_stats()

    # 构造 domain_table：同时暴露原始命中率、Beta 后验均值与 Wilson 区间。
    for domain in DOMAINS:
        row: dict[str, dict[str, float | int | None]] = {}
        for sch in ("段", "杨", "高", "任"):
            s = stats.get((sch, domain))
            if s and s.n > 0:
                row[sch] = s.to_report_cell()
            else:
                row[sch] = {
                    "hits": 0,
                    "misses": 0,
                    "n": s.n if s else 0,
                    "hit_rate": None,
                    "beta_mean": None,
                    "ci_low": None,
                    "ci_high": None,
                }
        report.domain_table[domain] = row

    gap_threshold = getattr(cfg, "cross_school_gap_threshold", 0.30)
    min_n = getattr(cfg, "cross_school_min_window", cfg.cross_school_every_n_cases)

    # 系统性偏差
    for domain in DOMAINS:
        rates = [
            (sch, stats.get((sch, domain)))
            for sch in ("段", "杨", "高", "任")
        ]
        valid = [
            (sch, s) for sch, s in rates
            if s is not None and s.n >= 2 and s.hit_rate is not None
        ]
        if len(valid) < 2:
            continue
        sample_n = sum(s.n for _, s in valid)
        if sample_n < min_n:
            continue
        max_sch, max_s = max(valid, key=lambda x: x[1].hit_rate or 0)
        min_sch, min_s = min(valid, key=lambda x: x[1].hit_rate or 0)
        max_rate = max_s.hit_rate or 0
        min_rate = min_s.hit_rate or 0
        gap = max_rate - min_rate
        if gap > gap_threshold:
            report.biases.append(SystematicBias(
                domain=domain,
                strong_school=max_sch,
                strong_rate=max_rate,
                weak_school=min_sch,
                weak_rate=min_rate,
                gap=gap,
                sample_n=sample_n,
                recommendation=(
                    f"建议人工 PR 调整 engine/domain-weights.yaml 在【{domain}】上"
                    f"提高 {max_sch} 派权重，降低 {min_sch} 派权重；"
                    f"或对 {min_sch} 派 {domain} 类规律启动 review。"
                ),
            ))

    total_n_eff = sum(s.n for s in stats.values())
    report.notes.append(f"total_n_eff={total_n_eff}；低样本领域只能作为趋势观察，不能作为四派准确率定论。")

    if not stats:
        report.notes.append(
            "尚未在 theory/*/index.yaml 中发现任何 applied_cases；可能 ingest 还没跑过。"
        )

    if write:
        _append_to_conflict_trends(report)
    return report


def _append_to_conflict_trends(report: ConflictTrendsReport) -> None:
    """追加到 META/conflict-trends.md 的"## Annotations"段之前。"""
    if not CONFLICT_TRENDS.exists():
        CONFLICT_TRENDS.parent.mkdir(parents=True, exist_ok=True)
        CONFLICT_TRENDS.write_text(
            "# conflict-trends · 跨派一致性趋势\n\n## Annotations\n",
            encoding="utf-8",
        )

    block = report.to_markdown()
    text = CONFLICT_TRENDS.read_text(encoding="utf-8")
    if "## Annotations" in text:
        before, sep, after = text.partition("## Annotations")
        new_text = before.rstrip() + "\n\n" + block.rstrip() + "\n\n---\n\n" + sep + after
    else:
        new_text = text.rstrip() + "\n\n" + block.rstrip() + "\n"
    CONFLICT_TRENDS.write_text(new_text, encoding="utf-8")


# ============================================================
# smoke
# ============================================================

def _smoke() -> None:
    report = cross_school_scan(triggered_by="(smoke)", write=False)
    print(f"[scan] case_count={report.case_count} biases={len(report.biases)}")
    for d in DOMAINS:
        row = report.domain_table.get(d, {})
        cells = []
        for sch in ("段", "杨", "高", "任"):
            e = row.get(sch, {}) if isinstance(row, dict) else {}
            rate = e.get("hit_rate")
            n = e.get("n", 0)
            if rate is None:
                cells.append(f"{sch}=—({n})")
            else:
                cells.append(f"{sch}={rate:.0%}({n})")
        print(f"  {d}: " + " ".join(cells))
    for b in report.biases:
        print(
            f"  bias[{b.domain}]: {b.strong_school}({b.strong_rate:.0%}) > "
            f"{b.weak_school}({b.weak_rate:.0%}), gap={b.gap:.0%}, n={b.sample_n}"
        )
    print(f"  notes={report.notes}")
    print("\n=== cross_school_scan.smoke 完成 ===")


if __name__ == "__main__":  # pragma: no cover
    _smoke()

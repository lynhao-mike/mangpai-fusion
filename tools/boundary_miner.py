"""tools/boundary_miner.py · v1.3 D3 边界自动挖掘

落地契约：
    plans/architecture-v1.3.md § 四 D3（核心新增）
    plans/architecture-v1.3.md § 七 (问题 3)：保守阈值 5 miss + p<0.1 + lift≥2

触发：单条规律 misses >= 5 (D3 锁定阈值)
显著性：p < 0.1 + lift >= 2 + miss_with >= 5
回放验证：加 boundary 后 hit_rate 必须不降（升才接受）

数据源：
    - rule.applied_cases（已有 case_id, hit, year, evidence_chain, note）
    - cases/{case_id}/analysis.md 抽 co-rule 协同规律 ID（启发式）

特征空间（轻量近似，不依赖完整 predicates 落盘）：
    - co_rule={rid}：协同触发的其他规律 ID（最强信号）
    - domain={X}：婚姻/学业/事业/财运/健康/六亲（从 AppliedCase.note 解析）
    - year_band={Y}-{Y+4}：5 年时代段（捕捉时代效应）

挖掘策略（W3 v1.0 版）：
    - 单变量优先：单 feature 显著富集 → 候选
    - 不做更深（决策树深度≤3 在小样本下易过拟合，先稳）
    - 后续 W4+ 可加二阶组合 / 完整 predicates 库接入

接受标准（4 个 AND）：
    1) p < 0.1（卡方 df=1，math.erfc 实现）
    2) lift ≥ 2（feature 出现时 miss 率 / 整体 miss 率）
    3) miss_with ≥ 5（feature 至少在 5 个 miss 案中出现）
    4) 回放验证：加 NOT(feature) 边界后 hit_rate 不降反升
       且 残留样本 ≥ 原 n/2（避免边界过死）

输出：
    - BoundaryMineResult（accepted / rejected / candidates / notes）
    - META/auto-mined-boundaries.md 审计日志
    - 不直接改规律 yaml（W4 由 iteration_report 决策是否合并到 auto_boundary 字段）

公开 API：
    mine_boundaries(rule_id) -> BoundaryMineResult
    mine_all() -> dict[rule_id, BoundaryMineResult]
    chi_square_p_value(table) -> float  (df=1, 2x2)

作者：Track-G v1.3
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import math
import pathlib
import re
import sys
from dataclasses import dataclass, field
from typing import Any, Iterable, Optional

from tools.rule_lifecycle import (
    AppliedCase,
    LifecycleConfig,
    Rule,
    RuleNotFoundError,
    list_rule_ids,
    load_rule,
)

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
CASES_DIR = REPO_ROOT / "cases"
META_DIR = REPO_ROOT / "META"
BOUNDARY_LOG = META_DIR / "auto-mined-boundaries.md"


# ============================================================
# 一、卡方检验（df=1, 2x2 列联表，纯 stdlib）
# ============================================================

def chi_square_p_value(table: list[list[int]]) -> float:
    """Pearson chi-square 单边 p-value（df=1，2×2 列联表）。

    table: [[a, b], [c, d]]
        a = miss_with_feature   b = miss_without_feature
        c = hit_with_feature    d = hit_without_feature

    使用：P(chi² > x) = erfc(sqrt(x/2)) for df=1
    （来自标准 chi² 分布与互补误差函数的关系）

    若 n=0 或任一 marginal 为 0 → 返回 1.0（无显著性）。
    """
    if not table or len(table) != 2 or any(len(row) != 2 for row in table):
        return 1.0
    a, b = table[0]
    c, d = table[1]
    n = a + b + c + d
    if n == 0:
        return 1.0
    row1, row2 = a + b, c + d
    col1, col2 = a + c, b + d
    if row1 == 0 or row2 == 0 or col1 == 0 or col2 == 0:
        return 1.0
    # 期望频数
    e_a = row1 * col1 / n
    e_b = row1 * col2 / n
    e_c = row2 * col1 / n
    e_d = row2 * col2 / n
    chi2 = 0.0
    for obs, exp in ((a, e_a), (b, e_b), (c, e_c), (d, e_d)):
        if exp > 0:
            chi2 += (obs - exp) ** 2 / exp
    if chi2 <= 0:
        return 1.0
    return math.erfc(math.sqrt(chi2 / 2))


# ============================================================
# 二、特征提取
# ============================================================

# 与 feedback_loop.RULE_ID_RE 同源 + 补 MR-LAYER\d+（任派应期 trace）
_RULE_ID_RE = re.compile(
    r"\b(?:"
    r"M[123]-[A-Z]-\d+"            # 段(M1)/杨(M2)/任(M3) 标准
    r"|MR-LAYER\d+"                # 任派应期 layer 标记
    r"|G(?:-[A-Z\u4e00-\u9fff]+){1,3}-?\d*"  # 高派
    r")\b"
)


def _extract_co_rules_from_case(
    case_id: str,
    *,
    cases_dir: pathlib.Path = CASES_DIR,
) -> set[str]:
    """从 cases/{case_id}/analysis.md 抽出现的所有 rule_id（除自身需 caller 排除）。

    优先级：
      1. cases/{case_id}/findings/analysis_output.json（Track-F 结构化）
      2. cases/{case_id}/analysis.md（启发式正则）
      3. 都没有 → 空集

    Returns: set of rule_id 字符串。
    """
    case_dir = cases_dir / case_id
    if not case_dir.exists():
        # 模糊匹配：case_id 可能是简化的（无 ganzhi 后缀）
        for child in cases_dir.iterdir() if cases_dir.exists() else []:
            if child.is_dir() and child.name.startswith(case_id):
                case_dir = child
                break
    if not case_dir.exists():
        return set()

    # 1) findings/analysis_output.json
    aout = case_dir / "findings" / "analysis_output.json"
    if aout.exists():
        try:
            data = json.loads(aout.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, ValueError):
            data = None
        if isinstance(data, dict):
            ids: set[str] = set()
            # final_conclusions
            for c in data.get("final_conclusions", []) or []:
                for rid in c.get("rule_ids", []) or []:
                    ids.add(str(rid))
                for ev in c.get("evidence", []) or []:
                    if isinstance(ev, dict) and ev.get("rule_id"):
                        ids.add(str(ev["rule_id"]))
            # gate_results
            for g in data.get("gate_results", []) or []:
                for ev in g.get("evidence", []) or []:
                    if isinstance(ev, dict) and ev.get("rule_id"):
                        ids.add(str(ev["rule_id"]))
            if ids:
                return ids

    # 2) analysis.md 启发式
    am = case_dir / "analysis.md"
    if am.exists():
        text = am.read_text(encoding="utf-8")
        return set(_RULE_ID_RE.findall(text))
    return set()


def _extract_features(
    case: AppliedCase,
    *,
    exclude_rule: str,
    cases_dir: pathlib.Path = CASES_DIR,
) -> set[str]:
    """从一个 AppliedCase 抽出特征集合。

    特征前缀：
      - "co_rule={rid}"：协同触发的其他规律 ID
      - "domain={X}"：从 note 解析（_apply_rule_verdicts 写的格式 "{section} | {domain} | sids=..."）
      - "year_band={Y}-{Y+4}"：5 年区间
    """
    feats: set[str] = set()

    # 1. co-rule (从案例的 analysis.md / findings 抽，排除自身)
    co_rules = _extract_co_rules_from_case(case.case_id, cases_dir=cases_dir)
    for rid in co_rules:
        if rid != exclude_rule:
            feats.add(f"co_rule={rid}")
    # 1.5 evidence_chain 中的其他 rule_id 也算
    for rid in case.evidence_chain or []:
        if rid != exclude_rule:
            feats.add(f"co_rule={rid}")

    # 2. domain：从 note 解析
    if case.note:
        # _apply_rule_verdicts 写法："{section} | {domain} | sids=s1,s2"
        parts = [p.strip() for p in case.note.split("|")]
        for p in parts:
            if not p:
                continue
            if p in ("婚姻", "学业", "事业", "财运", "健康", "六亲"):
                feats.add(f"domain={p}")
                break
            # 关键词识别
            for kw in ("婚姻", "学业", "事业", "财运", "健康", "六亲"):
                if kw in p:
                    feats.add(f"domain={kw}")
                    break

    # 3. year_band（5 年）
    if case.year is not None:
        try:
            y = int(case.year)
            band = y - (y % 5)
            feats.add(f"year_band={band}-{band + 4}")
        except (ValueError, TypeError):
            pass

    return feats


# ============================================================
# 三、结果数据结构
# ============================================================

@dataclass
class CandidateBoundary:
    rule_id: str
    feature: str           # "co_rule=M2-Y-068" / "domain=婚姻" / ...
    feature_kind: str      # "co_rule" / "domain" / "year_band"
    miss_count: int        # feature 出现次数 in miss set
    miss_total: int        # |miss set|
    hit_count: int
    hit_total: int
    p_value: float
    lift: float
    significant: bool
    accepted: bool = False
    rejected_reason: str = ""
    new_hit_rate_after_boundary: Optional[float] = None
    old_hit_rate: Optional[float] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "feature": self.feature,
            "feature_kind": self.feature_kind,
            "miss_count": self.miss_count,
            "miss_total": self.miss_total,
            "hit_count": self.hit_count,
            "hit_total": self.hit_total,
            "p_value": round(self.p_value, 4),
            "lift": round(self.lift, 3),
            "significant": self.significant,
            "accepted": self.accepted,
            "rejected_reason": self.rejected_reason,
            "old_hit_rate": (
                round(self.old_hit_rate, 3)
                if self.old_hit_rate is not None else None
            ),
            "new_hit_rate_after_boundary": (
                round(self.new_hit_rate_after_boundary, 3)
                if self.new_hit_rate_after_boundary is not None else None
            ),
        }


@dataclass
class BoundaryMineResult:
    rule_id: str
    miss_count: int = 0
    hit_count: int = 0
    candidates: list[CandidateBoundary] = field(default_factory=list)
    accepted: list[CandidateBoundary] = field(default_factory=list)
    rejected: list[CandidateBoundary] = field(default_factory=list)
    skipped: bool = False
    skip_reason: str = ""
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "miss_count": self.miss_count,
            "hit_count": self.hit_count,
            "skipped": self.skipped,
            "skip_reason": self.skip_reason,
            "candidates_total": len(self.candidates),
            "accepted": [c.to_dict() for c in self.accepted],
            "rejected": [c.to_dict() for c in self.rejected],
            "notes": self.notes,
        }


# ============================================================
# 四、主算法 mine_boundaries
# ============================================================

def mine_boundaries(
    rule_id: str,
    *,
    cfg: Optional[LifecycleConfig] = None,
    min_miss: int = 5,
    p_threshold: float = 0.1,
    lift_threshold: float = 2.0,
    cases_dir: pathlib.Path = CASES_DIR,
    dry_run: bool = False,
) -> BoundaryMineResult:
    """对单条规律挖掘候选边界。

    Args:
        rule_id:        规律 ID
        cfg:            LifecycleConfig（暂未使用，预留 W4）
        min_miss:       最少 miss 案数才触发挖掘（D3 锁定 5）
        p_threshold:    卡方 p 值阈值（D3 锁定 0.1）
        lift_threshold: lift 阈值（D3 锁定 2.0）
        cases_dir:      cases/ 目录
        dry_run:        True 则不写 META 日志

    Returns:
        BoundaryMineResult
    """
    try:
        rule = load_rule(rule_id)
    except RuleNotFoundError as exc:
        result = BoundaryMineResult(rule_id=rule_id, skipped=True,
                                    skip_reason=f"RuleNotFoundError: {exc}")
        return result

    result = BoundaryMineResult(
        rule_id=rule_id,
        miss_count=rule.misses,
        hit_count=rule.hits,
    )

    if rule.misses < min_miss:
        result.skipped = True
        result.skip_reason = f"misses={rule.misses} < min_miss={min_miss}"
        return result

    # 收集每案特征集
    hit_feats: list[set[str]] = []
    miss_feats: list[set[str]] = []
    for ac in rule.applied_cases:
        feats = _extract_features(ac, exclude_rule=rule_id, cases_dir=cases_dir)
        if ac.hit:
            hit_feats.append(feats)
        else:
            miss_feats.append(feats)

    # 注：applied_cases 与 rule.hits/misses 不一定完全一致（旧数据）
    # 以 applied_cases 为准
    n_hit = len(hit_feats)
    n_miss = len(miss_feats)
    result.hit_count = n_hit
    result.miss_count = n_miss

    if n_miss < min_miss:
        result.skipped = True
        result.skip_reason = (
            f"applied_cases 中 miss={n_miss} < {min_miss}"
            f"（rule.misses={rule.misses}，可能存在旧版无 trace 的失验）"
        )
        return result

    old_hit_rate = n_hit / max(1, n_hit + n_miss)

    # 单变量扫描所有出现过的特征
    all_features: set[str] = set()
    for s in hit_feats + miss_feats:
        all_features.update(s)

    if not all_features:
        result.notes.append(
            "无可用协同特征——cases/*/analysis.md 与 findings 都未提供任何 rule_id；"
            "boundary_miner 在没有特征时无法挖掘。建议先跑 batch_intake 把案例落到完整结构。"
        )
        return result

    candidates: list[CandidateBoundary] = []
    for feature in sorted(all_features):
        miss_with = sum(1 for s in miss_feats if feature in s)
        miss_without = n_miss - miss_with
        hit_with = sum(1 for s in hit_feats if feature in s)
        hit_without = n_hit - hit_with

        if miss_with < min_miss:
            continue  # 该特征在 miss 集出现不到 5 次，跳过

        p = chi_square_p_value([[miss_with, miss_without], [hit_with, hit_without]])

        # lift = miss-rate-given-feature / miss-rate-overall
        denom = miss_with + hit_with
        miss_rate_with = miss_with / max(1, denom)
        miss_rate_overall = n_miss / max(1, n_miss + n_hit)
        lift = miss_rate_with / max(0.001, miss_rate_overall)

        cand = CandidateBoundary(
            rule_id=rule_id,
            feature=feature,
            feature_kind=feature.split("=", 1)[0],
            miss_count=miss_with,
            miss_total=n_miss,
            hit_count=hit_with,
            hit_total=n_hit,
            p_value=p,
            lift=lift,
            significant=(p < p_threshold and lift >= lift_threshold and miss_with >= min_miss),
            old_hit_rate=old_hit_rate,
        )
        candidates.append(cand)

    candidates.sort(key=lambda c: (c.p_value, -c.lift))
    result.candidates = candidates

    significant = [c for c in candidates if c.significant]
    if not significant:
        result.notes.append(
            f"扫描 {len(candidates)} 个候选特征，无一通过 (p<{p_threshold} & lift>={lift_threshold} & miss_with>={min_miss})"
        )
        return result

    # 回放验证：加 NOT(feature) 边界后 hit_rate 是否升
    for cand in significant:
        # 加 boundary 等价于：feature 出现时不触发 → 该案不计入 hits/misses
        new_hits = sum(1 for s in hit_feats if cand.feature not in s)
        new_misses = sum(1 for s in miss_feats if cand.feature not in s)
        new_total = new_hits + new_misses
        new_hit_rate = new_hits / max(1, new_total)
        cand.new_hit_rate_after_boundary = new_hit_rate

        # 接受条件：新命中率提升 + 残留样本 ≥ 原 n/2
        if new_total < (n_hit + n_miss) / 2:
            cand.rejected_reason = (
                f"残留样本 {new_total} < 原 n {n_hit + n_miss} 的一半（边界过死）"
            )
            result.rejected.append(cand)
            continue
        if new_hit_rate <= old_hit_rate:
            cand.rejected_reason = (
                f"新 hit_rate={new_hit_rate:.2f} 未超过原 {old_hit_rate:.2f}"
            )
            result.rejected.append(cand)
            continue

        cand.accepted = True
        result.accepted.append(cand)

    if not dry_run:
        _append_boundary_log(result)

    return result


def mine_all(
    *,
    cfg: Optional[LifecycleConfig] = None,
    min_miss: int = 5,
    cases_dir: pathlib.Path = CASES_DIR,
    dry_run: bool = False,
) -> dict[str, BoundaryMineResult]:
    """对 theory 下所有规律 ID 跑挖掘（仅触发 misses>=min_miss 的）。"""
    out: dict[str, BoundaryMineResult] = {}
    for rid in list_rule_ids():
        try:
            r = mine_boundaries(
                rid, cfg=cfg, min_miss=min_miss,
                cases_dir=cases_dir, dry_run=dry_run,
            )
            if not r.skipped or r.candidates or r.notes:
                out[rid] = r
        except Exception as exc:  # noqa: BLE001
            out[rid] = BoundaryMineResult(
                rule_id=rid, skipped=True,
                skip_reason=f"exception: {exc!r}",
            )
    return out


# ============================================================
# 五、审计日志
# ============================================================

def _append_boundary_log(result: BoundaryMineResult) -> None:
    META_DIR.mkdir(parents=True, exist_ok=True)
    if not BOUNDARY_LOG.exists():
        BOUNDARY_LOG.write_text(
            "# auto-mined-boundaries · 边界自动挖掘日志\n\n"
            "> 由 `tools/boundary_miner.py` 维护。\n"
            "> D3 决策：≥5 miss + p<0.1 + lift≥2 + 回放验证 hit_rate 不降才接受。\n"
            "> 接受的 boundary 由后续 `iteration_report.py` 决策是否合并到规律 yaml 的 `auto_boundary` 字段。\n\n"
            "## Annotations\n",
            encoding="utf-8",
        )

    today = _dt.date.today().isoformat()
    lines: list[str] = []
    lines.append(f"\n## {today} · mine {result.rule_id}")
    lines.append("")
    lines.append(
        f"- applied_cases: hit={result.hit_count} miss={result.miss_count}"
    )
    if result.skipped:
        lines.append(f"- ⏭️ skipped: {result.skip_reason}")
    else:
        lines.append(
            f"- 候选 {len(result.candidates)} / 接受 {len(result.accepted)}"
            f" / 拒绝 {len(result.rejected)}"
        )

    if result.accepted:
        lines.append("")
        lines.append("### ✅ 接受的边界")
        lines.append("")
        lines.append("| feature | miss_with/total | hit_with/total | p | lift | hit_rate 改善 |")
        lines.append("|---|---|---|---|---|---|")
        for c in result.accepted:
            lines.append(
                f"| `NOT({c.feature})` | {c.miss_count}/{c.miss_total} | "
                f"{c.hit_count}/{c.hit_total} | {c.p_value:.3f} | {c.lift:.2f} | "
                f"{c.old_hit_rate:.2f} → {c.new_hit_rate_after_boundary:.2f} |"
            )

    if result.rejected:
        lines.append("")
        lines.append("### ❌ 拒绝的候选")
        lines.append("")
        lines.append("| feature | p | lift | rejected_reason |")
        lines.append("|---|---|---|---|")
        for c in result.rejected:
            lines.append(
                f"| `{c.feature}` | {c.p_value:.3f} | {c.lift:.2f} | "
                f"{c.rejected_reason} |"
            )

    if result.notes:
        lines.append("")
        for n in result.notes:
            lines.append(f"> note: {n}")

    text = BOUNDARY_LOG.read_text(encoding="utf-8")
    if "## Annotations" in text:
        before, sep, after = text.partition("## Annotations")
        new_text = (
            before.rstrip() + "\n\n" + "\n".join(lines).rstrip()
            + "\n\n---\n\n" + sep + after
        )
    else:
        new_text = text.rstrip() + "\n" + "\n".join(lines) + "\n"
    BOUNDARY_LOG.write_text(new_text, encoding="utf-8")


# ============================================================
# 六、CLI
# ============================================================

def _print_human(result: BoundaryMineResult) -> None:
    print(f"\n[boundary_miner] rule_id={result.rule_id}")
    print(f"  applied_cases: hit={result.hit_count} miss={result.miss_count}")
    if result.skipped:
        print(f"  ⏭️ skipped: {result.skip_reason}")
        return
    print(f"  候选 {len(result.candidates)} / ✅接受 {len(result.accepted)}"
          f" / ❌拒绝 {len(result.rejected)}")
    for c in result.accepted:
        print(f"  ✅ NOT({c.feature})  p={c.p_value:.3f} lift={c.lift:.2f}"
              f"  hit_rate {c.old_hit_rate:.2f}→{c.new_hit_rate_after_boundary:.2f}")
    for c in result.rejected:
        print(f"  ❌ {c.feature}  p={c.p_value:.3f} lift={c.lift:.2f}"
              f"  reason: {c.rejected_reason}")
    for n in result.notes:
        print(f"  > {n}")


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="v1.3 D3 边界自动挖掘：≥5 miss + p<0.1 + lift≥2"
    )
    parser.add_argument(
        "rule_id", nargs="?",
        help="规律 ID；不指定则跑 mine_all 全部"
    )
    parser.add_argument("--min-miss", type=int, default=5, help="最少 miss 案数（D3 锁定 5）")
    parser.add_argument("--p", type=float, default=0.1, help="卡方 p 阈值")
    parser.add_argument("--lift", type=float, default=2.0, help="lift 阈值")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    if args.rule_id:
        result = mine_boundaries(
            args.rule_id, min_miss=args.min_miss,
            p_threshold=args.p, lift_threshold=args.lift,
            dry_run=args.dry_run,
        )
        if args.json:
            print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
        else:
            _print_human(result)
    else:
        all_results = mine_all(min_miss=args.min_miss, dry_run=args.dry_run)
        if args.json:
            print(json.dumps(
                {rid: r.to_dict() for rid, r in all_results.items()},
                ensure_ascii=False, indent=2,
            ))
        else:
            print(f"\n[mine_all] 处理了 {len(all_results)} 条规律")
            ok = sum(1 for r in all_results.values() if r.accepted)
            print(f"  ✅ 找到边界: {ok}")
            print(f"  ⏭️ 跳过: {sum(1 for r in all_results.values() if r.skipped)}")
            for rid, r in all_results.items():
                if r.accepted:
                    print(f"  · {rid}: {len(r.accepted)} 边界")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())

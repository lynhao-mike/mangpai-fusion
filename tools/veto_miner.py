"""tools/veto_miner.py · v1.3 D4 候选否决兜底

落地契约：
    plans/architecture-v1.3.md § 四 D4

触发条件（4 个 AND）：
    1) rule.misses >= 5（与 D3 同一阈值）
    2) rule.n >= 10（Beta 后验有意义最低样本量）
    3) rule.confidence_cache.posterior < 40%（整体不靠谱）
    4) boundary_miner 在该规律上未找到显著边界
       （即 D3 救不回来）

动作：
    - apply_status_change(rule, "flagged_for_review",
                         reason="auto-veto: posterior<40% no boundary")
    - confidence_cache 归 0（star=0, percent=0, posterior=0），
      但 hits/misses/applied_cases 全保留
    - 不删除规律 — 命理师在月度报告看清单后可手动复活

写盘：
    - 调 save_rule(rule)（更新规律 yaml）
    - 写 META/auto-vetoed-rules.md 审计（含完整复活说明）

公开 API：
    apply_veto(rule_id, *, boundary_result=None, dry_run=False) -> VetoResult
    veto_all(*, boundary_results=None) -> dict[rule_id, VetoResult]

作者：Track-G v1.3
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import pathlib
import sys
from dataclasses import dataclass, field
from typing import Any, Optional

from tools.rule_lifecycle import (
    Confidence,
    LifecycleConfig,
    Rule,
    RuleNotFoundError,
    apply_status_change,
    list_rule_ids,
    load_rule,
    save_rule,
)

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
META_DIR = REPO_ROOT / "META"
VETO_LOG = META_DIR / "auto-vetoed-rules.md"


# ============================================================
# 一、结果数据结构
# ============================================================

@dataclass
class VetoResult:
    rule_id: str
    school: str = ""
    skipped: bool = False
    skip_reason: str = ""
    vetoed: bool = False
    posterior_before: Optional[float] = None
    posterior_after: float = 0.0
    star_before: Optional[int] = None
    star_after: int = 0
    n: int = 0
    hits: int = 0
    misses: int = 0
    status_before: str = ""
    status_after: str = ""
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "school": self.school,
            "skipped": self.skipped,
            "skip_reason": self.skip_reason,
            "vetoed": self.vetoed,
            "posterior": {
                "before": (round(self.posterior_before, 4)
                           if self.posterior_before is not None else None),
                "after": round(self.posterior_after, 4),
            },
            "star": {"before": self.star_before, "after": self.star_after},
            "n": self.n, "hits": self.hits, "misses": self.misses,
            "status": {"before": self.status_before, "after": self.status_after},
            "notes": self.notes,
        }


# ============================================================
# 二、主入口 apply_veto
# ============================================================

def apply_veto(
    rule_id: str,
    *,
    boundary_result: Optional[Any] = None,
    cfg: Optional[LifecycleConfig] = None,
    posterior_threshold: float = 0.40,
    min_n: int = 10,
    min_miss: int = 5,
    today: Optional[str] = None,
    dry_run: bool = False,
) -> VetoResult:
    """对单条规律决策是否自动停用。

    Args:
        rule_id: 规律 ID
        boundary_result: D3 boundary_miner 已跑过的结果；None 则不知道边界状态，
                         视为"无显著边界"按守恒判断（避免重复跑）
        cfg: LifecycleConfig（暂未使用）
        posterior_threshold: 后验阈值（D4 锁定 0.40）
        min_n: 最少样本量（D4 锁定 10）
        min_miss: 最少 miss 数（D4 锁定 5，与 D3 对齐）
        today: ISO 日期串
        dry_run: True 则不调 save_rule / 不写日志

    Returns:
        VetoResult
    """
    today = today or _dt.date.today().isoformat()
    try:
        rule = load_rule(rule_id)
    except RuleNotFoundError as exc:
        return VetoResult(rule_id=rule_id, skipped=True,
                          skip_reason=f"RuleNotFoundError: {exc}")

    result = VetoResult(
        rule_id=rule_id,
        school=rule.school,
        n=rule.n, hits=rule.hits, misses=rule.misses,
        status_before=rule.status,
    )

    # 触发条件检查（顺序：先快速排除）
    if rule.misses < min_miss:
        result.skipped = True
        result.skip_reason = f"misses={rule.misses} < {min_miss}"
        return result

    if rule.n < min_n:
        result.skipped = True
        result.skip_reason = (
            f"n={rule.n} < {min_n}（样本不足，Beta 后验不可靠）"
        )
        return result

    # 取/重算 posterior
    if rule.confidence_cache is None:
        rule.recompute_confidence(
            variance_threshold=cfg.variance_threshold if cfg else 0.15
        )
    assert rule.confidence_cache is not None
    result.posterior_before = rule.confidence_cache.posterior
    result.star_before = rule.confidence_cache.star

    if rule.confidence_cache.posterior >= posterior_threshold:
        result.skipped = True
        result.skip_reason = (
            f"posterior={rule.confidence_cache.posterior:.3f} >= {posterior_threshold}"
        )
        return result

    # 检查 boundary_miner 是否找到边界
    if boundary_result is not None:
        accepted = getattr(boundary_result, "accepted", None)
        if accepted is not None and len(accepted) > 0:
            result.skipped = True
            result.skip_reason = (
                f"boundary_miner 找到 {len(accepted)} 条显著边界，先试边界（D3 优先）"
            )
            return result

    # 状态已经是 deprecated 或 flagged_for_review → 不重复操作
    if rule.status in ("deprecated", "flagged_for_review"):
        result.skipped = True
        result.skip_reason = f"status 已为 {rule.status}，无需重复 veto"
        return result

    # 满足全部条件 → 停用
    new_status = "flagged_for_review"
    reason = (
        f"auto-veto: posterior={rule.confidence_cache.posterior:.2f} "
        f"<{posterior_threshold} (n={rule.n}); boundary_miner 未找到显著边界"
    )
    if not dry_run:
        apply_status_change(
            rule, new_status,
            case_id="auto-veto",
            reason=reason,
            today=today,
        )
        # 置信度归 0（保留 sample_n 供命理师判断）
        rule.confidence_cache = Confidence(
            star=0, percent=0.0, posterior=0.0, variance=0.0,
            sample_n=rule.n,
        )
        save_rule(rule)

    result.vetoed = True
    result.status_after = new_status
    result.posterior_after = 0.0
    result.star_after = 0
    result.notes.append(reason)
    if not dry_run:
        _append_veto_log(result, today)
    return result


def veto_all(
    *,
    boundary_results: Optional[dict[str, Any]] = None,
    cfg: Optional[LifecycleConfig] = None,
    dry_run: bool = False,
) -> dict[str, VetoResult]:
    """对所有规律决策。

    Args:
        boundary_results: dict[rule_id, BoundaryMineResult]，可选
                         （如已跑过 mine_all，传入避免重复挖掘）
    """
    out: dict[str, VetoResult] = {}
    for rid in list_rule_ids():
        bres = (boundary_results or {}).get(rid)
        try:
            r = apply_veto(rid, boundary_result=bres, cfg=cfg, dry_run=dry_run)
            if r.vetoed or (not r.skipped):
                out[rid] = r
        except Exception as exc:  # noqa: BLE001
            out[rid] = VetoResult(
                rule_id=rid, skipped=True,
                skip_reason=f"exception: {exc!r}",
            )
    return out


# ============================================================
# 三、审计日志
# ============================================================

def _append_veto_log(result: VetoResult, today: str) -> None:
    META_DIR.mkdir(parents=True, exist_ok=True)
    if not VETO_LOG.exists():
        VETO_LOG.write_text(
            "# auto-vetoed-rules · 自动停用规律日志\n\n"
            "> 由 `tools/veto_miner.py` 维护。\n"
            "> D4 决策：boundary 挖不出 + posterior<40% + n≥10 → status=flagged_for_review。\n"
            "> 命理师可手动复活：编辑 `theory/{school}/index.yaml` 把 status 改回 candidate/confirmed，\n"
            "> 并酌情清除 confidence_cache 让下次反馈重新计算。\n\n"
            "## Annotations\n",
            encoding="utf-8",
        )

    lines: list[str] = []
    lines.append(f"\n## {today} · veto {result.rule_id} ({result.school})")
    lines.append("")
    lines.append(
        f"- 样本：n={result.n} (hits={result.hits} miss={result.misses})"
    )
    if result.posterior_before is not None:
        lines.append(
            f"- posterior：{result.posterior_before:.3f} → {result.posterior_after:.3f}"
        )
    lines.append(
        f"- ★：{result.star_before} → {result.star_after}"
    )
    lines.append(
        f"- status：{result.status_before} → {result.status_after}"
    )
    if result.notes:
        lines.append("")
        for n in result.notes:
            lines.append(f"> {n}")

    lines.append("")
    lines.append(
        "**复活方式**：编辑 `theory/{school}/index.yaml`，把该规律的 `status` 改回 "
        "`candidate` 或 `confirmed`，删除 `confidence_cache`，下次反馈即重新计算。"
    )

    text = VETO_LOG.read_text(encoding="utf-8")
    if "## Annotations" in text:
        before, sep, after = text.partition("## Annotations")
        new_text = (
            before.rstrip() + "\n\n" + "\n".join(lines).rstrip()
            + "\n\n---\n\n" + sep + after
        )
    else:
        new_text = text.rstrip() + "\n" + "\n".join(lines) + "\n"
    VETO_LOG.write_text(new_text, encoding="utf-8")


# ============================================================
# 四、CLI
# ============================================================

def _print_human(result: VetoResult) -> None:
    print(f"\n[veto_miner] rule_id={result.rule_id} school={result.school}")
    print(f"  n={result.n} hits={result.hits} miss={result.misses}")
    if result.skipped:
        print(f"  ⏭️ skipped: {result.skip_reason}")
        return
    if result.vetoed:
        print(f"  🚫 VETOED: {result.status_before} → {result.status_after}")
        if result.posterior_before is not None:
            print(f"     posterior: {result.posterior_before:.3f} → 0.0")
            print(f"     ★: {result.star_before} → 0")
        for n in result.notes:
            print(f"     {n}")


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="v1.3 D4 候选否决兜底：posterior<40% + boundary挖不出 + n≥10 → 自动停用"
    )
    parser.add_argument("rule_id", nargs="?", help="规律 ID；不指定则跑 veto_all")
    parser.add_argument("--posterior", type=float, default=0.40,
                        help="后验阈值（D4 锁定 0.40）")
    parser.add_argument("--min-n", type=int, default=10)
    parser.add_argument("--min-miss", type=int, default=5)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    if args.rule_id:
        result = apply_veto(
            args.rule_id,
            posterior_threshold=args.posterior,
            min_n=args.min_n,
            min_miss=args.min_miss,
            dry_run=args.dry_run,
        )
        if args.json:
            print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
        else:
            _print_human(result)
    else:
        results = veto_all(dry_run=args.dry_run)
        if args.json:
            print(json.dumps(
                {rid: r.to_dict() for rid, r in results.items()},
                ensure_ascii=False, indent=2,
            ))
        else:
            vetoed = [r for r in results.values() if r.vetoed]
            print(f"\n[veto_all] 处理 {len(results)} 条规律")
            print(f"  🚫 被停用: {len(vetoed)}")
            for r in vetoed:
                print(f"  · {r.rule_id} ({r.school}): "
                      f"posterior={r.posterior_before:.2f} n={r.n}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())

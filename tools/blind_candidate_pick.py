"""tools/blind_candidate_pick.py · 盲测案例抽取器

用途
----
从 446 个 RF 案例里，按盲测要求抽出下一批案例，自动排除：
1. 已做过年份判断的案例（避免重复劳动与答案泄露风险）
2. 非 birth 口径（pillar-only 无人元司令与起运年份，流年判断不可比）
3. 有 boundary_warnings 的案例（交节/子时边界，时辰不确定）
4. 脏时间串回退的案例（fallback_from_birth）
5. 同人重复（同一出生日的多张盘只留一张，避免样本不独立）
6. 事件不足 3 条（无法生成题目）

抽取策略
--------
按 events 数量三层均衡抽样，避免"全是多事命"的选择偏差：
  high (>=7 条) / mid (4-6 条) / low (3 条)
三层的目标是各占 1/3，允许 ±1 浮动。

CLI
---
    python -m tools.blind_candidate_pick --count 12 --out .workbuddy-ai/pilot-batch2.json
    python -m tools.blind_candidate_pick --count 12 --seed 7      # 换随机种子
    python -m tools.blind_candidate_pick --count 12 --dry-run     # 只看会抽到谁
"""
from __future__ import annotations

import argparse
import json
import random
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

CASES = ROOT / "cases"
PROBES = ROOT / ".workbuddy-ai" / "year-probes"
DEFAULT_POOL = ROOT / ".workbuddy-ai" / "blind_candidate_pool.json"

_EVENT_ROW = re.compile(r"^\|\s*(\d{4})\s*\|\s*(.+?)\s*\|\s*([^|]*)\|")


def _birth_date(case_dir: Path) -> str | None:
    inp = case_dir / "input.md"
    if not inp.exists():
        return None
    m = re.search(r'公历:\s*"?(\d{4}-\d{2}-\d{2})',
                  inp.read_text(encoding="utf-8-sig", errors="replace"))
    return m.group(1) if m else None


def _event_count(case_dir: Path) -> int:
    fb = case_dir / "feedback.md"
    if not fb.exists():
        return 0
    n = 0
    for line in fb.read_text(encoding="utf-8-sig", errors="replace").splitlines():
        if _EVENT_ROW.match(line.strip()):
            n += 1
    return n


def _already_done(case: str) -> bool:
    return (PROBES / case / "year_judgments.json").exists()


def _has_boundary_warning(case_dir: Path) -> bool:
    sf = case_dir / "facts" / "facts_summary.json"
    if not sf.exists():
        return False
    try:
        d = json.loads(sf.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return False
    return bool(d.get("boundary_warnings"))


def _is_fallback(case_dir: Path) -> bool:
    sf = case_dir / "facts" / "facts_summary.json"
    if not sf.exists():
        return False
    try:
        d = json.loads(sf.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return False
    return bool(d.get("fallback_from_birth"))


def _mode(case_dir: Path) -> str:
    sf = case_dir / "facts" / "facts_summary.json"
    if not sf.exists():
        return "unknown"
    try:
        return str(json.loads(sf.read_text(encoding="utf-8-sig")).get("mode", "unknown"))
    except (OSError, json.JSONDecodeError):
        return "unknown"


def tier_of(n_events: int) -> str:
    if n_events >= 7:
        return "high"
    if n_events >= 4:
        return "mid"
    if n_events >= 3:
        return "low"
    return "insufficient"


def collect_candidates() -> tuple[list[dict[str, Any]], dict[str, int]]:
    """返回 (合格候选, 各排除原因计数)。"""
    excluded: dict[str, int] = defaultdict(int)
    rows = []
    seen_dates: dict[str, str] = {}

    for d in sorted(CASES.glob("C-2026-RF*-*")):
        if not d.is_dir():
            continue
        case = d.name
        if _already_done(case):
            excluded["already_done"] += 1
            continue
        if _mode(d) != "birth":
            excluded["not_birth_mode"] += 1
            continue
        if _is_fallback(d):
            excluded["fallback_birth"] += 1
            continue
        if _has_boundary_warning(d):
            excluded["boundary_warning"] += 1
            continue
        n = _event_count(d)
        tier = tier_of(n)
        if tier == "insufficient":
            excluded["events_lt_3"] += 1
            continue
        bd = _birth_date(d)
        if bd is None:
            excluded["no_birth_date"] += 1
            continue
        # 同人去重：同一出生日只留事件更多的那张盘
        if bd in seen_dates:
            excluded["same_person_dup"] += 1
            continue
        seen_dates[bd] = case
        rows.append({
            "case": case,
            "birth_date": bd,
            "n_events": n,
            "events_tier": tier,
        })
    return rows, dict(excluded)


def pick(rows: list[dict[str, Any]], count: int, seed: int) -> list[dict[str, Any]]:
    """按事件数三层均衡抽样。"""
    by_tier: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_tier[r["events_tier"]].append(r)

    rng = random.Random(seed)
    for t in by_tier:
        by_tier[t].sort(key=lambda x: x["case"])
        rng.shuffle(by_tier[t])

    tiers = ["high", "mid", "low"]
    base, rem = divmod(count, len(tiers))
    quota = {t: base + (1 if i < rem else 0) for i, t in enumerate(tiers)}

    chosen: list[dict] = []
    used: set[str] = set()
    # 第一轮：按配额抽
    for t in tiers:
        for r in by_tier[t]:
            if quota[t] <= 0:
                break
            if r["case"] in used:
                continue
            chosen.append({**r, "picked_by": f"tier:{t}"})
            used.add(r["case"])
            quota[t] -= 1
    # 第二轮：配额未满时从任意层补（不足层被抽空的情况）
    if len(chosen) < count:
        leftover = [r for t in tiers for r in by_tier[t] if r["case"] not in used]
        rng.shuffle(leftover)
        for r in leftover:
            if len(chosen) >= count:
                break
            chosen.append({**r, "picked_by": "backfill"})
            used.add(r["case"])
    return chosen


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="盲测案例抽取器")
    ap.add_argument("--count", type=int, default=12, help="抽取数量")
    ap.add_argument("--seed", type=int, default=20261018, help="随机种子（可复现）")
    ap.add_argument("--out", type=Path, default=None, help="输出 JSON 路径")
    ap.add_argument("--dry-run", action="store_true", help="只打印不写文件")
    args = ap.parse_args(argv)

    rows, excluded = collect_candidates()
    print(f"合格候选池: {len(rows)} 例")
    if excluded:
        print("排除统计:")
        for k, v in sorted(excluded.items(), key=lambda x: -x[1]):
            print(f"  {k:20s} {v}")
    print()

    if not rows:
        print("ERROR: 无可用候选", file=sys.stderr)
        return 1

    tier_counts = defaultdict(int)
    for r in rows:
        tier_counts[r["events_tier"]] += 1
    print(f"候选分层: {dict(tier_counts)}")

    chosen = pick(rows, args.count, args.seed)
    print(f"\n抽出 {len(chosen)} 例:")
    by_t = defaultdict(int)
    for r in chosen:
        by_t[r["events_tier"]] += 1
        print(f"  {r['case'][:46]:48s} events={r['n_events']:2d} "
              f"tier={r['events_tier']:5s} ({r['picked_by']})")
    print(f"\n分层结果: {dict(by_t)}")

    if len(chosen) < args.count:
        print(f"\n⚠️ 仅抽出 {len(chosen)} 例（要求 {args.count}），候选池已不足")

    if args.dry_run:
        print("\n[dry-run] 未写文件")
        return 0

    out = args.out or (ROOT / ".workbuddy-ai" / "pilot-batch2.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(chosen, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\n已写入 {out}")
    print("下一步:")
    print(f"  python .workbuddy-ai/make_bundle_v2.py --from-json {out}")
    print("  python -m tools.blind_year_probe --from-json " + str(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())

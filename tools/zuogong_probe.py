"""宫制星候选探针：481 盘上统计「宫（支）制星（干）」候选是否还能取到 actor。

背景：关系图不建「支→干」边，候选层原先把 actor 只给 stem 层 ke 边，
导致 zuogong(kind=制用, actor_at=D.b) 在 481 盘上全部 rejected。
本探针是那次修复的回归门禁（tests/ 为保护区，无法加用例）。

用法：python -m tools.zuogong_probe [--limit N]
退出码：0 = 至少有一盘取到宫制星候选；1 = 又退回全 rejected。
"""

from __future__ import annotations

import argparse
import collections
import pathlib
import re
import sys

from engine.api import analyze_facts, to_jsonable

ROOT = pathlib.Path(__file__).resolve().parent.parent
CASE_RE = re.compile(
    r"^(C-\d{4}-[A-Za-z0-9]+)-(乾|坤)-((?:[甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]){4})$"
)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()
    cases = [(m.group(3), m.group(2)) for p in sorted((ROOT / "cases").iterdir())
             if (m := CASE_RE.match(p.name))]
    if args.limit:
        cases = cases[:args.limit]
    total = with_cg = day_branch = 0
    actors: collections.Counter[str] = collections.Counter()
    for pillars, gender in cases:
        ps = [pillars[i:i + 2] for i in range(0, 8, 2)]
        facts = to_jsonable(analyze_facts(pillars=ps, gender=gender))
        cands = [c for c in facts["duan_zuogong"]["candidates"] if c.get("relation_kind") == "canggan_ke"]
        total += 1
        if cands:
            with_cg += 1
        if any(c.get("actor") == "D.b" for c in cands):
            day_branch += 1
        actors.update(c.get("actor", "") for c in cands)
    print(f"盘数 {total}；有宫制星候选 {with_cg} ({with_cg / max(total, 1):.1%})；"
          f"actor=D.b {day_branch} ({day_branch / max(total, 1):.1%})")
    print("候选 actor 分布:", dict(sorted(actors.items())))
    return 0 if with_cg else 1


if __name__ == "__main__":
    sys.exit(main())

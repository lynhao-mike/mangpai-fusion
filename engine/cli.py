"""engine/cli.py · Agent 专用 JSON 入口：python -m engine.cli <subcommand>。"""
from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Optional, Sequence

from engine.api.facade import analyze_facts, build_chart, to_jsonable
from engine.facts.chart_facts import ChartInputError
from engine.facts.relation_graph import build_relation_graph
from engine.facts.shensha import build_shensha_facts
from engine.facts.strength_facts import build_strength_facts
from engine.facts.structure_check import check_structures


def _dump(payload: Any) -> None:
    # ponytail: compact JSON，保证 analyze_facts 默认输出 < 15KB
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass
    sys.stdout.write(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
    sys.stdout.write("\n")


def _chart_kwargs(args: argparse.Namespace) -> dict[str, Any]:
    if not args.birth and not args.pillars:
        raise ChartInputError("必须提供 --birth 或 --pillars")
    if args.birth and args.pillars:
        raise ChartInputError("--birth 与 --pillars 不能同时使用")
    return {
        "birth_dt": args.birth,
        "pillars": None if args.pillars is None else args.pillars.split(),
        "gender": args.gender,
    }


def _run(command: str, args: argparse.Namespace) -> dict[str, Any]:
    payload = _run_facts(command, args)
    if args.pillars:
        payload["input_limitations"] = {
            "mode": "pillars",
            "unavailable": {
                "qiyun": "仅四柱无法确定出生时刻与交节时差，不能计算起运年龄及日期。",
                "dayun_calendar": "大运干支顺逆序列可确定，起止公历年份及年龄缺少起运依据。",
                "siling": "缺少出生时刻及节后天数，不能确定人元司令。",
            },
        }
    return payload


def _run_facts(command: str, args: argparse.Namespace) -> dict[str, Any]:
    extra = {"dayun_index": args.dayun_index, "liunian_year": args.liunian}
    if command == "all":
        return analyze_facts(**_chart_kwargs(args), **extra)
    chart = build_chart(**_chart_kwargs(args))
    if command == "chart":
        return to_jsonable(chart)
    if command == "relations":
        return to_jsonable(build_relation_graph(
            chart, dayun_index=args.dayun_index, liunian_year=args.liunian,
        ))
    if command == "strength":
        return to_jsonable(build_strength_facts(chart))
    if command == "shensha":
        return to_jsonable(build_shensha_facts(chart))
    graph = build_relation_graph(chart, dayun_index=args.dayun_index, liunian_year=args.liunian)
    return to_jsonable(check_structures(chart, graph, build_strength_facts(chart)))


def _parser() -> argparse.ArgumentParser:
    shared = argparse.ArgumentParser(add_help=False)
    shared.add_argument("--birth", help='公历出生时间，如 "1980-02-15 02:30"')
    shared.add_argument("--pillars", help='四柱，如 "庚申 戊寅 壬子 辛丑"')
    shared.add_argument("--gender", default="乾", help="乾/坤/M/F/男/女")
    shared.add_argument("--dayun-index", type=int, dest="dayun_index")
    shared.add_argument("--liunian", type=int)
    shared.add_argument("--json", action="store_true", default=True, help="输出 UTF-8 JSON（默认）")
    parser = argparse.ArgumentParser(prog="python -m engine.cli", description="事实引擎 JSON CLI")
    sub = parser.add_subparsers(dest="command", required=True)
    for name, help_ in (
        ("chart", "ChartFacts"),
        ("relations", "RelationGraph"),
        ("strength", "StrengthFacts"),
        ("shensha", "神煞查表事实"),
        ("structures", "子平八格构成要件"),
        ("all", "完整 analyze_facts"),
    ):
        sub.add_parser(name, parents=[shared], help=help_)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
    args = _parser().parse_args(argv)
    try:
        _dump(_run(args.command, args))
    except (ChartInputError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

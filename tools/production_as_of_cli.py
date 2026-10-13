"""生产目录约定下的 as-of CLI 别名。"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from tools.as_of_integration import (
    _parser,
    generate_report,
    load_ledger,
    parse_iso_date,
)


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return int(exc.code)

    if bool(args.as_of) != bool(args.ledger):
        print("错误：--as-of 与 --ledger 必须成对提供", file=sys.stderr)
        return 2

    cwd = Path.cwd()
    cases_dir = args.cases_dir if args.cases_dir is not None else cwd / "cases"
    reports_dir = args.reports_dir if args.reports_dir is not None else cwd / "reports"

    try:
        kwargs: dict[str, Any] = {
            "cases_dir": cases_dir,
            "reports_dir": reports_dir,
        }
        if args.as_of:
            ledger = load_ledger(args.ledger)
            kwargs.update(
                as_of_date=parse_iso_date(args.as_of),
                entries=ledger["entries"],
                daiyun_end=ledger["daiyun_end"],
                current_center=ledger["current_center"],
                reasonable_range=ledger["reasonable_range"],
                ledger_case_id=ledger["case_id"],
            )
        report_path = generate_report(args.input_md, **kwargs)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 2

    print(report_path)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from engine.application.recompute import (
    RecomputeHardGateError,
    RecomputeRequest,
    recompute_wenzhen_case,
)


ROOT = Path(__file__).resolve().parents[1]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run a hard-gated full recompute for one Wenzhen补盘 case."
    )
    parser.add_argument(
        "case_or_input",
        help="Case id under cases/ or a direct path to input.md.",
    )
    parser.add_argument(
        "--cases-dir",
        default=str(ROOT / "cases"),
        help="Cases root directory. Default: repository cases/.",
    )
    parser.add_argument(
        "--reports-dir",
        default=str(ROOT / "reports"),
        help="Reports output directory. Default: repository reports/.",
    )
    parser.add_argument(
        "--cases-index-path",
        default=None,
        help="Optional cases-index.md path passed to preflight.",
    )
    parser.add_argument(
        "--allow-empty-statement-index",
        action="store_true",
        help="Disable the recompute hard gate for statement_index.json.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON summary.",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    cases_dir = Path(args.cases_dir)
    input_path = _resolve_input(args.case_or_input, cases_dir=cases_dir)
    request = RecomputeRequest(
        input_path=input_path,
        cases_dir=cases_dir,
        reports_dir=Path(args.reports_dir),
        cases_index_path=Path(args.cases_index_path) if args.cases_index_path else None,
        require_statement_index=not args.allow_empty_statement_index,
    )

    try:
        result = recompute_wenzhen_case(request)
    except RecomputeHardGateError as exc:
        payload = {"status": "hard_gate_failed", "error": str(exc)}
        _print(payload, as_json=args.json)
        return 2
    except Exception as exc:  # noqa: BLE001 - CLI boundary
        payload = {"status": "failed", "error": str(exc)}
        _print(payload, as_json=args.json)
        return 1

    payload = {"status": "completed", **result.to_dict()}
    _print(payload, as_json=args.json)
    return 0


def _resolve_input(case_or_input: str, *, cases_dir: Path) -> Path:
    candidate = Path(case_or_input)
    if candidate.name == "input.md" or candidate.suffix == ".md":
        return candidate
    return cases_dir / case_or_input / "input.md"


def _print(payload: dict[str, object], *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    status = payload.get("status")
    case_id = payload.get("case_id", "UNKNOWN")
    print(f"status: {status}")
    print(f"case_id: {case_id}")
    if "error" in payload:
        print(f"error: {payload['error']}")
    artifacts = payload.get("artifacts")
    if isinstance(artifacts, dict):
        print(f"manifest: {artifacts.get('recompute_manifest', '')}")


if __name__ == "__main__":
    raise SystemExit(main())

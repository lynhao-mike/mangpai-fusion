"""tools/feedback_review_gate.py · 反馈复核包摄入前置闸门

用途：
    1. 校验 META/feedback-closure-review-pack-*.json 结构。
    2. 阻止仍含 pending 裁决的复核包进入 feedback_ingest。
    3. 输出人工裁决同步后可运行的逐案摄入命令。

只读工具：不会修改仓库文件。

示例：
    python tools/feedback_review_gate.py META/feedback-closure-review-pack-2026-06-11.json
    python tools/feedback_review_gate.py META/feedback-closure-review-pack-2026-06-11.json --allow-partial
    python tools/feedback_review_gate.py META/feedback-closure-review-pack-2026-06-11.json --format json
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
from dataclasses import asdict, dataclass
from typing import Any, Literal

ROOT = pathlib.Path(__file__).resolve().parent.parent
ALLOWED_VERDICTS = {"y", "n", "?", "skip"}
PENDING_VERDICT = "pending"

OutputFormat = Literal["text", "json"]


@dataclass(frozen=True)
class GateResult:
    path: str
    status: str
    total_items: int
    pending_count: int
    adjudicated_count: int
    invalid_count: int
    ingest_blocked: bool
    commands: list[str]
    problems: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _rel(path: pathlib.Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _load_json(path: pathlib.Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"review pack not found: {_rel(path)}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"review pack is not valid JSON: {exc.msg} at line {exc.lineno}") from exc
    if not isinstance(data, dict):
        raise ValueError("review pack root must be a JSON object")
    return data


def check_review_pack(path: pathlib.Path, *, allow_partial: bool = False) -> GateResult:
    data = _load_json(path)
    problems: list[str] = []

    items = data.get("items")
    if not isinstance(items, list):
        items = []
        problems.append("items must be a list")

    commands_raw = data.get("next_ingest_commands_after_human_adjudication", [])
    commands = [str(command) for command in commands_raw] if isinstance(commands_raw, list) else []
    if not commands:
        problems.append("next_ingest_commands_after_human_adjudication is missing or empty")

    pending_count = 0
    adjudicated_count = 0
    invalid_count = 0
    seen_statement_ids: set[str] = set()

    required_fields = {
        "case_id",
        "statement_id",
        "domain",
        "year",
        "rule_ids",
        "source_report",
        "case_feedback",
        "statement_rule_map",
        "verdict",
    }

    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            invalid_count += 1
            problems.append(f"items[{index}] must be an object")
            continue

        missing = sorted(field for field in required_fields if field not in item)
        if missing:
            invalid_count += 1
            problems.append(f"items[{index}] missing fields: {', '.join(missing)}")

        statement_id = item.get("statement_id")
        if isinstance(statement_id, str):
            if statement_id in seen_statement_ids:
                invalid_count += 1
                problems.append(f"duplicate statement_id: {statement_id}")
            seen_statement_ids.add(statement_id)

        rule_ids = item.get("rule_ids")
        if not isinstance(rule_ids, list) or not rule_ids or not all(isinstance(rule_id, str) for rule_id in rule_ids):
            invalid_count += 1
            problems.append(f"items[{index}] rule_ids must be a non-empty string list")

        verdict = item.get("verdict")
        if verdict == PENDING_VERDICT:
            pending_count += 1
        elif verdict in ALLOWED_VERDICTS:
            adjudicated_count += 1
        else:
            invalid_count += 1
            problems.append(f"items[{index}] invalid verdict: {verdict!r}")

    pack_blocked = bool(data.get("ingest_blocked", True))
    blocked_by_pending = pending_count > 0 and not allow_partial
    blocked_by_no_adjudication = adjudicated_count == 0
    ingest_blocked = bool(problems or pack_blocked or blocked_by_pending or blocked_by_no_adjudication)

    if pack_blocked:
        problems.append("ingest_blocked is true; clear it only after human adjudication is synced")
    if blocked_by_pending:
        problems.append(f"{pending_count} item(s) still pending")
    if blocked_by_no_adjudication:
        problems.append("no adjudicated item is available for ingestion")

    status = "blocked" if ingest_blocked else "ready"
    return GateResult(
        path=_rel(path),
        status=status,
        total_items=len(items),
        pending_count=pending_count,
        adjudicated_count=adjudicated_count,
        invalid_count=invalid_count,
        ingest_blocked=ingest_blocked,
        commands=commands,
        problems=problems,
    )


def _print_text(result: GateResult) -> None:
    print(f"feedback review gate: {result.status}")
    print(f"path: {result.path}")
    print(f"items: {result.total_items}")
    print(f"pending: {result.pending_count}")
    print(f"adjudicated: {result.adjudicated_count}")
    print(f"invalid: {result.invalid_count}")
    if result.problems:
        print("problems:")
        for problem in result.problems:
            print(f"- {problem}")
    if not result.ingest_blocked and result.commands:
        print("commands:")
        for command in result.commands:
            print(command)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check feedback review pack readiness before feedback_ingest.")
    parser.add_argument("review_pack", type=pathlib.Path)
    parser.add_argument("--allow-partial", action="store_true", help="allow adjudicated items while other items remain pending")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args(argv)

    try:
        result = check_review_pack(args.review_pack, allow_partial=args.allow_partial)
    except ValueError as exc:
        print(f"feedback review gate: error: {exc}", file=sys.stderr)
        return 2

    if args.format == "json":
        print(json.dumps(result.to_dict(), ensure_ascii=True, indent=2))
    else:
        _print_text(result)

    return 1 if result.ingest_blocked else 0


if __name__ == "__main__":
    raise SystemExit(main())

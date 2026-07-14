"""修复历史问真转案工具造成的大运方向与序列错误。

仅处理校准结果中满足以下条件的案例：
- 大运方向存在差异；
- 当前字段仍符合历史“乾顺、坤逆”固定生成模式；
- 文件内当前方向、序列与校准快照完全一致。

默认 dry-run；传入 ``--write`` 才写文件。
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


_DIRECTION_RE = re.compile(r'^(?P<prefix>\s*顺逆:\s*)(?P<quote>["\']?)(?P<value>顺|逆)(?P=quote)(?P<suffix>\s*)$')
_GANZHI_RE = re.compile(r'^(?P<prefix>\s*干支:\s*)(?P<quote>["\']?)(?P<value>[甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥])(?P=quote)(?P<suffix>\s*)$')


def _fixed_gender_pattern(record: dict[str, Any]) -> bool:
    gender = record.get("gender")
    claimed = record.get("claimed_dayun_direction")
    return (
        gender in {"M", "男"} and claimed == "顺"
    ) or (
        gender in {"F", "女"} and claimed == "逆"
    )


def select_migration_records(calibration: dict[str, Any]) -> list[dict[str, Any]]:
    """选出仅由固定乾顺坤逆模式导致方向错误的记录。"""
    return [
        record
        for record in calibration.get("records", [])
        if record.get("eligible")
        and not record.get("dayun_direction_ok")
        and _fixed_gender_pattern(record)
    ]


def migrate_case_file(
    input_path: Path,
    record: dict[str, Any],
    *,
    write: bool,
) -> dict[str, Any]:
    """安全迁移一个 input.md，仅改大运顺逆与每步干支。"""
    input_path = Path(input_path)
    text = input_path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)

    claimed_direction = str(record["claimed_dayun_direction"])
    computed_direction = str(record["computed_dayun_direction"])
    claimed_sequence = list(record["claimed_dayun_sequence"])
    computed_sequence = list(record["computed_dayun_sequence"])
    if len(claimed_sequence) != len(computed_sequence):
        raise ValueError(
            f"{record['case_id']}: 原序列与精算序列长度不一致"
        )

    in_dayun = False
    direction_index: int | None = None
    ganzhi_indexes: list[int] = []
    actual_direction: str | None = None
    actual_sequence: list[str] = []

    for index, raw_line in enumerate(lines):
        line = raw_line.rstrip("\r\n")
        if line == "大运:":
            in_dayun = True
            continue
        if in_dayun and line and not line.startswith((" ", "\t")):
            in_dayun = False
        if not in_dayun:
            continue

        direction_match = _DIRECTION_RE.match(line)
        if direction_match:
            direction_index = index
            actual_direction = direction_match.group("value")
            continue
        ganzhi_match = _GANZHI_RE.match(line)
        if ganzhi_match:
            ganzhi_indexes.append(index)
            actual_sequence.append(ganzhi_match.group("value"))

    if direction_index is None:
        raise ValueError(f"{record['case_id']}: 未找到大运.顺逆")

    if actual_direction == computed_direction and actual_sequence == computed_sequence:
        return {
            "case_id": record["case_id"],
            "path": input_path.as_posix(),
            "status": "already_fixed",
        }
    if actual_direction != claimed_direction:
        raise ValueError(
            f"{record['case_id']}: 文件方向 {actual_direction} 与快照 {claimed_direction} 不一致"
        )
    if actual_sequence != claimed_sequence:
        raise ValueError(
            f"{record['case_id']}: 文件大运序列与校准快照不一致"
        )

    direction_line = lines[direction_index]
    newline = "\r\n" if direction_line.endswith("\r\n") else "\n" if direction_line.endswith("\n") else ""
    direction_body = direction_line.rstrip("\r\n")
    match = _DIRECTION_RE.match(direction_body)
    assert match is not None
    lines[direction_index] = (
        f"{match.group('prefix')}{match.group('quote')}{computed_direction}"
        f"{match.group('quote')}{match.group('suffix')}{newline}"
    )

    for index, computed_ganzhi in zip(ganzhi_indexes, computed_sequence):
        source_line = lines[index]
        newline = "\r\n" if source_line.endswith("\r\n") else "\n" if source_line.endswith("\n") else ""
        body = source_line.rstrip("\r\n")
        match = _GANZHI_RE.match(body)
        assert match is not None
        lines[index] = (
            f"{match.group('prefix')}{match.group('quote')}{computed_ganzhi}"
            f"{match.group('quote')}{match.group('suffix')}{newline}"
        )

    if write:
        input_path.write_text("".join(lines), encoding="utf-8", newline="")
    return {
        "case_id": record["case_id"],
        "path": input_path.as_posix(),
        "status": "updated" if write else "would_update",
        "before_direction": claimed_direction,
        "after_direction": computed_direction,
        "before_sequence": claimed_sequence,
        "after_sequence": computed_sequence,
    }


def migrate_from_calibration(
    calibration_path: Path,
    *,
    write: bool,
) -> dict[str, Any]:
    calibration_path = Path(calibration_path)
    calibration = json.loads(calibration_path.read_text(encoding="utf-8"))
    records = select_migration_records(calibration)
    results = []
    for record in records:
        results.append(
            migrate_case_file(Path(record["input_path"]), record, write=write)
        )
    return {
        "schema_version": "wenzhen-dayun-direction-fix/v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "write": write,
        "selected": len(records),
        "updated": sum(item["status"] == "updated" for item in results),
        "would_update": sum(item["status"] == "would_update" for item in results),
        "already_fixed": sum(item["status"] == "already_fixed" for item in results),
        "records": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="修复问真历史转案的大运方向和序列")
    parser.add_argument(
        "--calibration",
        type=Path,
        default=Path("META/chart-validation-calibration.json"),
    )
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--log-out", type=Path)
    parser.add_argument("--expect-count", type=int, default=48)
    args = parser.parse_args()

    result = migrate_from_calibration(args.calibration, write=args.write)
    if args.log_out:
        args.log_out.parent.mkdir(parents=True, exist_ok=True)
        args.log_out.write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    print(json.dumps({key: value for key, value in result.items() if key != "records"}, ensure_ascii=False, indent=2))
    return 0 if result["selected"] == args.expect_count else 2


if __name__ == "__main__":
    raise SystemExit(main())

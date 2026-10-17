"""tools/rf_pillar_intake.py · 从真实反馈中提取「有四柱无出生时间」的案例

背景
----
`tools/as_of_raw_feedback_paipan.py` 要求记录带 `true_solar_time_raw` 或
`birth_datetime_raw`，否则拒绝。实测 `cases/raw_feedback/parsed/real_cases_990.jsonl`
992 条中：

- 已展开 443 个案例目录；
- 未展开 549 条，其中 **540 条缺 `bazi_raw`**（命主未自报四柱）、
  **549 条缺出生时间**、9 条缺性别。

关键事实：**缺出生时间但有 `bazi_raw`（命主自报四柱）的记录，仍然可以入池**——
`engine.cli --pillars` 能直接排盘，代价是没有人元司令与起运年份（即
`docs/analysis_human_touch.md` 与 `templates/report-v7-human.md` 已规范的
「条件分支实断」场景）。这类样本对盲测仍有价值：反馈事件是真的，盘面是确定的。

本工具的取舍
-----------
1. **只收有 `bazi_raw` 且有 events 的记录**。无四柱又无生时的记录无法排盘，
   收入 `reports/` 会污染准确率基线——干净比完整重要。
2. **不猜、不补、不推**。性别缺失即跳过；四柱格式不合法即跳过。
3. **标记 `pillar_only: true`**，让下游 blind_ledger 与评测知道这类样本
   缺 `siling` / 起运年份，不能用于依赖这两项的断言。
4. 幂等：已存在的案例目录拒绝覆盖。

输出
----
每个案例目录含：
- `input.md`      四柱口径输入（schema_version 1.2.0，与既有 RF 案例同构）
- `feedback.md`   真实事件年表
- `pillar_only.json` 机器可读标记（缺哪些字段、为何不入公历池）

CLI
---
    python -m tools.rf_pillar_intake --limit 600 --write
    python -m tools.rf_pillar_intake --dry-run          # 默认预览
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DEFAULT_SOURCE = ROOT / "cases" / "raw_feedback" / "parsed" / "real_cases_990.jsonl"
DEFAULT_CASES_ROOT = ROOT / "cases"

# 命主自报四柱的合法形态：8 个汉字，年柱/月柱/日柱/时柱各 2 字
_PILLAR_CHARS = set("甲乙丙丁戊己庚辛壬癸子丑寅卯辰巳午未申酉戌")
GANZHI = list("甲乙丙丁戊己庚辛壬癸")
ZHI = list("子丑寅卯辰巳午未申酉戌")

UNSAFE_FLAGS = {"privacy_sensitive", "contains_pii", "third_party_info"}


# ── 解析 ────────────────────────────────────────────────────────────────────

def _compact(value: object) -> str:
    return "".join(str(value or "").split())


def _valid_pillars(bazi: str) -> bool:
    """四柱必须 8 个合法干支字，且干支配对合法。"""
    if len(bazi) != 8:
        return False
    if any(ch not in _PILLAR_CHARS for ch in bazi):
        return False
    for i in range(0, 8, 2):
        if bazi[i] not in GANZHI or bazi[i + 1] not in ZHI:
            return False
    return True


def _gender(record: dict[str, Any]) -> tuple[str, str]:
    qian_kun = str(record.get("qian_kun", "") or "").strip()
    gender = str(record.get("gender", "") or "").strip()
    if qian_kun == "乾" or gender.startswith("男"):
        return "男", "乾"
    if qian_kun == "坤" or gender.startswith("女"):
        return "女", "坤"
    raise ValueError("缺少明确性别/乾坤")


def _is_eligible(record: dict[str, Any]) -> bool:
    """有四柱、有反馈、无危险标记。不要求出生时间。"""
    flags = {str(item) for item in (record.get("quality_flags") or [])}
    bazi = _compact(record.get("bazi_raw"))
    events = record.get("events")
    return bool(
        bazi
        and _valid_pillars(bazi)
        and isinstance(events, list)
        and events
        and not flags.intersection(UNSAFE_FLAGS)
    )


def load_records(source: Path) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if not source.exists():
        return out
    with source.open(encoding="utf-8-sig") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(rec, dict):
                out.append(rec)
    return out


def select_records(
    records: Iterable[dict[str, Any]],
    *,
    limit: int = 600,
    excluded_raw_ids: set[str] | None = None,
) -> list[dict[str, Any]]:
    excluded = excluded_raw_ids or set()
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for index, record in enumerate(records):
        raw_id = str(record.get("raw_id", ""))
        if not _is_eligible(record) or raw_id in excluded:
            continue
        key = str(record.get("duplicate_key") or record.get("raw_id") or index)
        if key in seen:
            continue
        seen.add(key)
        unique.append(record)
        if len(unique) >= limit:
            break
    return unique


# ── 渲染 ────────────────────────────────────────────────────────────────────

def _yaml_quote(value: object) -> str:
    return json.dumps(str(value or ""), ensure_ascii=False)


def _escape_table(value: object) -> str:
    return str(value or "").replace("|", "\\|").replace("\r", " ").replace("\n", " ").strip()


def _case_id(record: dict[str, Any], qian_kun: str, bazi: str) -> str:
    digits = re.sub(r"\D", "", str(record.get("raw_id", "")))
    serial = digits[-6:] if digits else "UNKNOWN"
    pillars = "".join(bazi[i:i + 2] for i in range(0, 8, 2))
    return f"C-2026-RF{serial}-{qian_kun}-{pillars}"


def render_input(record: dict[str, Any], case_id: str, bazi: str, gender: str, qian_kun: str) -> str:
    place = str(record.get("birth_place_sanitized", "") or "未提供")
    return f"""# {case_id} · 四柱口径输入（pillar-only）

> 来源：`cases/raw_feedback/parsed/real_cases_990.jsonl` 的 `{record.get('raw_id', '')}`。
> 本文件由 `tools/rf_pillar_intake.py` 生成；**命主未提供可确认的出生时刻**，
> 故采用四柱直输口径。已知事件见 `feedback.md`，未写入本文件。

```yaml
schema_version: 1.2.0
case_meta:
  case_id: {_yaml_quote(case_id)}
  立案日期: {datetime.now(timezone.utc).date().isoformat()}
  命主代号: {_yaml_quote(record.get('raw_id', ''))}
  策略: RF_PILLAR_ONLY_CANDIDATE
  来源: 真实案例反馈990个案例（四柱口径）

birth:
  性别: {gender}
  乾坤: {qian_kun}
  出生地脱敏: {_yaml_quote(place)}
  时间来源: none
  口径说明: "命主未提供出生时刻；本案例使用命主自报四柱直排，缺起运年份与人元司令。"

四柱:
  年柱: {_yaml_quote(bazi[0:2])}
  月柱: {_yaml_quote(bazi[2:4])}
  日柱: {_yaml_quote(bazi[4:6])}
  时柱: {_yaml_quote(bazi[6:8])}

known_facts: []
提问:
  - "仅作为盲断候选；已知事件见 feedback.md。"
```

## 口径边界（必读）

- 本案例**没有人元司令**（`siling`）与**起运年龄/日期**：`engine.cli --pillars` 会返回
  `input_limitations.unavailable` 的 `qiyun`、`dayun_calendar`、`siling` 三项。
- 大运干支顺逆序列可用；**起止公历年份不可用**。
- 因此本案例**不得用于**依赖大运年份或人元司令的断言；流年只做原局引动。
- 对应写作规范见 `docs/analysis_human_touch.md` 与 `templates/report-v7-human.md`
  的「条件分支实断」条款。
"""


def render_feedback(record: dict[str, Any], case_id: str) -> str:
    events = record.get("events") if isinstance(record.get("events"), list) else []
    rows = []
    for event in events:
        if not isinstance(event, dict):
            continue
        year = event.get("year", "未知")
        domains = ", ".join(str(item) for item in (event.get("domains") or []))
        rows.append(f"| {_escape_table(year)} | {_escape_table(event.get('text'))} | {_escape_table(domains)} |")
    event_rows = "\n".join(rows) or "| 未知 | 无可用事件 | |"
    return f"""# {case_id} · 原始反馈年表

> 来源：`cases/raw_feedback/parsed/real_cases_990.jsonl` 的 `{record.get('raw_id', '')}`。
> 这些是盲断后的核验材料；生成排盘时未把事件写入 input.md。

## 事件年表

| 年份 | 已知事实 | 功能域 |
|---|---|---|
{event_rows}

## 数据审计

- 质量等级：{_escape_table(record.get('quality_grade'))}
- 质量标记：{_escape_table(', '.join(str(x) for x in (record.get('quality_flags') or [])) or '无')}
- 自报四柱：{_escape_table(record.get('bazi_raw') or '无')}
- 口径：四柱直输（无出生时刻）
"""


def render_marker(record: dict[str, Any], case_id: str, bazi: str) -> str:
    payload = {
        "schema_version": "rf-pillar-only-marker/v1",
        "case_id": case_id,
        "raw_id": record.get("raw_id", ""),
        "pillar_only": True,
        "unavailable": ["qiyun", "dayun_calendar", "siling"],
        "reason": "命主未提供可确认出生时刻；使用自报四柱直排",
        "bazi_self_reported": bazi,
        "event_count": len(record.get("events") or []),
        "quality_grade": record.get("quality_grade"),
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


# ── 主流程 ──────────────────────────────────────────────────────────────────

def run(
    *,
    source: Path = DEFAULT_SOURCE,
    cases_root: Path = DEFAULT_CASES_ROOT,
    limit: int = 600,
    dry_run: bool = True,
) -> dict[str, Any]:
    records = load_records(source)
    existing = {
        f"RF-2026-{m.group(1)}"
        for p in cases_root.glob("C-2026-RF*-*")
        if (m := re.match(r"C-2026-RF(\d{6})-", p.name))
    }
    selected = select_records(records, limit=limit, excluded_raw_ids=existing)

    created: list[str] = []
    skipped: list[dict[str, str]] = []
    for record in selected:
        raw_id = str(record.get("raw_id", ""))
        try:
            gender, qian_kun = _gender(record)
            bazi = _compact(record.get("bazi_raw"))
            if not _valid_pillars(bazi):
                raise ValueError(f"四柱格式不合法: {bazi!r}")
            case_id = _case_id(record, qian_kun, bazi)
            case_dir = cases_root / case_id
            if case_dir.exists():
                raise FileExistsError(f"拒绝覆盖已存在目录: {case_dir}")
            if not dry_run:
                case_dir.mkdir(parents=True, exist_ok=False)
                (case_dir / "input.md").write_text(
                    render_input(record, case_id, bazi, gender, qian_kun), encoding="utf-8"
                )
                (case_dir / "feedback.md").write_text(
                    render_feedback(record, case_id), encoding="utf-8"
                )
                (case_dir / "pillar_only.json").write_text(
                    render_marker(record, case_id, bazi), encoding="utf-8"
                )
            created.append(case_id)
        except (ValueError, TypeError, OSError) as exc:
            skipped.append({"raw_id": raw_id, "error": str(exc)})

    return {
        "source_total": len(records),
        "already_expanded": len(existing),
        "eligible_selected": len(selected),
        "created": created,
        "skipped": skipped,
        "dry_run": dry_run,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--cases-root", type=Path, default=DEFAULT_CASES_ROOT)
    parser.add_argument("--limit", type=int, default=600)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="仅预览（默认）")
    mode.add_argument("--write", action="store_true", help="创建案例目录")
    args = parser.parse_args(argv)

    result = run(
        source=args.source,
        cases_root=args.cases_root,
        limit=args.limit,
        dry_run=not args.write,
    )
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())

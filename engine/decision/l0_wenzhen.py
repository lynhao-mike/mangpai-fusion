"""L0 问真事实账本最小解析器。

只做 parse / normalize / record_missing / preserve_unknown / validate_format。
不做命理判断，不生成事件，不仲裁。
"""

from __future__ import annotations

import hashlib
import re
from typing import Any

from engine.decision.l0_context import build_context_ledger
from engine.decision.models import ChartFactLedger, ContextFactLedger, RawWenzhenPayload

SECTION_RE = re.compile(r"^\$(?P<name>[A-Z_]+)\s*$", re.M)
BASE_LINE_RE = re.compile(r"^(?P<key>[^:\n：]+)[:：](?P<value>.*)$")
FOUR_LINE_RE = re.compile(r"^(?P<pillar>[YMDH])[:：](?P<body>.*)$")
DY_LINE_RE = re.compile(r"^(?P<kind>[#>])\s*(?P<body>.*)$")
PILLAR_KEYS = {"Y": "year", "M": "month", "D": "day", "H": "hour"}


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _sections(raw_text: str) -> dict[str, str]:
    matches = list(SECTION_RE.finditer(raw_text))
    blocks: dict[str, str] = {}
    for idx, match in enumerate(matches):
        name = match.group("name")
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(raw_text)
        blocks[name] = raw_text[start:end].strip()
    return blocks


def _parse_base(text: str, missing: list[str]) -> dict[str, str]:
    data: dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        match = BASE_LINE_RE.match(line)
        if not match:
            continue
        key = match.group("key").strip()
        value = match.group("value").strip()
        data[key] = value
        if value == "_":
            missing.append(f"$BASE.{key}")
    return data


def _parse_four(text: str, missing: list[str]) -> dict[str, str]:
    four: dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        match = FOUR_LINE_RE.match(line)
        if not match:
            continue
        key = PILLAR_KEYS[match.group("pillar")]
        body = match.group("body").strip()
        four[key] = body
        if body == "_":
            missing.append(f"$FOUR.{key}")
    for marker, key in PILLAR_KEYS.items():
        if key not in four:
            missing.append(f"$FOUR.{marker}")
    return four


def _parse_dy_loop(text: str, missing: list[str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    dayun: list[dict[str, Any]] = []
    liunian: list[dict[str, Any]] = []
    for idx, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        match = DY_LINE_RE.match(line)
        if not match:
            continue
        item = {"line_no": idx, "text": match.group("body").strip()}
        if item["text"] == "_":
            missing.append(f"$DY_LOOP.{idx}")
        if match.group("kind") == "#":
            dayun.append(item)
        else:
            liunian.append(item)
    return dayun, liunian


def parse_wenzhen_l0(raw_text: str, *, captured_at: str = "") -> tuple[RawWenzhenPayload, ChartFactLedger, ContextFactLedger]:
    """解析问真专业文本为 L0 事实账本。"""

    raw_hash = _hash_text(raw_text)
    payload = RawWenzhenPayload(raw_text=raw_text, raw_hash=raw_hash, captured_at=captured_at)
    blocks = _sections(raw_text)
    missing: list[str] = []
    for required in ("BASE", "FOUR", "DY_LOOP"):
        if required not in blocks:
            missing.append(f"${required}")

    base = _parse_base(blocks.get("BASE", ""), missing)
    four = _parse_four(blocks.get("FOUR", ""), missing)
    dayun, liunian = _parse_dy_loop(blocks.get("DY_LOOP", ""), missing)
    unknown_blocks = [name for name in blocks if name not in {"BASE", "FOUR", "DY_LOOP", "KNOWN_FACTS", "FOCUS"}]

    chart = ChartFactLedger(
        sex_marker=base.get("命式", base.get("性别", "")),
        solar_datetime=base.get("公历", base.get("阳历", "")),
        four_pillars=four,
        start_luck=base.get("起运", base.get("起运时间", "")),
        dayun_steps=dayun,
        liunian_steps=liunian,
        missing_fields=missing,
        unknown_blocks=[f"${name}\n{blocks[name]}" for name in unknown_blocks],
        raw_source_hash=raw_hash,
    )
    context = build_context_ledger(blocks, unknown_blocks)
    return payload, chart, context

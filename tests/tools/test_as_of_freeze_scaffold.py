"""tools/as_of_freeze_scaffold.py 的真实案例与文件写入测试。"""
from __future__ import annotations

import json
import re

import pytest

from tests.fixtures.cases import load_case
from tools.as_of_freeze_scaffold import (
    FreezeScaffold,
    build_freeze_scaffold,
    write_scaffold_to_file,
)


CASE_ID = "C-2026-001-乾-庚申戊寅壬子辛丑"
WINDOW_PATTERN = re.compile(r"^\d{4}-01-01/\d{4}-12-31$")


def _scaffold() -> FreezeScaffold:
    parsed = load_case(CASE_ID)
    return build_freeze_scaffold(
        parsed,
        CASE_ID,
        "2026-07-30",
        as_of_year=2026,
        domain="career",
    )


def test_builds_reviewable_scaffold_from_real_case() -> None:
    scaffold = _scaffold()

    assert isinstance(scaffold, FreezeScaffold)
    assert scaffold.case_id == CASE_ID
    assert scaffold.as_of_date == "2026-07-30"
    assert 0 < len(scaffold.scaffolded_event_candidates) <= 5
    assert scaffold.preflight_summary
    assert scaffold.daiyun_tendency_note
    assert len(scaffold.contract_gate_reminders) >= 3
    assert "草稿" in scaffold.scaffold_note

    for index, candidate in enumerate(scaffold.scaffolded_event_candidates, start=1):
        assert candidate["candidate_id"] == f"E{index}"
        assert WINDOW_PATTERN.fullmatch(candidate["window"])
        start_year, end_year = candidate["window"].split("/")
        assert start_year[:4] == end_year[:4]
        assert candidate["trigger_basis"]
        assert "关系摘要" in candidate["trigger_basis"]
        assert candidate["scoring_unit"].startswith("TODO:")
        assert candidate["center_event"].startswith("TODO:")


def test_write_refuses_to_overwrite_existing_file(tmp_path) -> None:
    output_path = tmp_path / "asof-blind-freeze.json"
    output_path.write_text("{}", encoding="utf-8")

    with pytest.raises(FileExistsError):
        write_scaffold_to_file(_scaffold(), output_path)

    assert output_path.read_text(encoding="utf-8") == "{}"


def test_write_creates_valid_json_at_new_path(tmp_path) -> None:
    scaffold = _scaffold()
    output_path = tmp_path / "draft" / "asof-blind-freeze.json"

    write_scaffold_to_file(scaffold, output_path)

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["case_id"] == CASE_ID
    assert payload["as_of_date"] == "2026-07-30"
    assert payload["scaffolded_event_candidates"] == list(
        scaffold.scaffolded_event_candidates
    )

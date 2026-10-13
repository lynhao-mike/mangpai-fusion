"""十八槽位能力状态 CLI 测试。"""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path

from engine.v5.domain_slices.contract import DomainAnalysisRequest
from engine.v5.domain_slices.orchestrator import run_domain_analysis
from tools.domain_capability_status import main


def _write_snapshot(path: Path) -> None:
    snapshot = run_domain_analysis(
        DomainAnalysisRequest(
            gender="乾",
            birth_datetime=datetime(1990, 1, 1, 12, 0),
            as_of_date=date(2026, 7, 31),
            domains=("career",),
        )
    )
    path.write_text(snapshot.to_json(), encoding="utf-8")


def test_json_and_markdown_are_rendered_from_same_metrics(tmp_path: Path, capsys) -> None:
    path = tmp_path / "one.run.json"
    _write_snapshot(path)

    assert main([str(path), "--format", "json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["slot_count"] == 18

    assert main([str(path), "--format", "markdown"]) == 0
    markdown = capsys.readouterr().out
    assert f"运行快照：{payload['run_count']}" in markdown
    assert f"十八槽位：{payload['slot_count']}" in markdown
    assert "registration status" in markdown
    assert "runtime status" in markdown
    assert "unavailable" in markdown


def test_check_accepts_valid_inputs_and_reports_deduplication(tmp_path: Path, capsys) -> None:
    path = tmp_path / "one.run.json"
    _write_snapshot(path)

    assert main([str(path), str(path), "--check"]) == 0
    output = capsys.readouterr().out
    assert "check passed" in output
    assert "deduplicated=1" in output


def test_check_rejects_wrong_suffix_malformed_json_and_tampered_hash(tmp_path: Path, capsys) -> None:
    wrong = tmp_path / "wrong.json"
    wrong.write_text("{}", encoding="utf-8")
    assert main([str(wrong), "--check"]) == 1
    assert "*.run.json" in capsys.readouterr().err

    malformed = tmp_path / "bad.run.json"
    malformed.write_text("{", encoding="utf-8")
    assert main([str(malformed), "--check"]) == 1
    assert "check failed" in capsys.readouterr().err

    tampered = tmp_path / "tampered.run.json"
    _write_snapshot(tampered)
    payload = json.loads(tampered.read_text(encoding="utf-8"))
    payload["claims"][0]["claim"] = "篡改"
    tampered.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    assert main([str(tampered), "--check"]) == 1
    assert "output hash mismatch" in capsys.readouterr().err


def test_cli_expands_directory_to_run_json_only(tmp_path: Path, capsys) -> None:
    _write_snapshot(tmp_path / "one.run.json")
    (tmp_path / "ignored.json").write_text("{}", encoding="utf-8")

    assert main([str(tmp_path), "--format", "json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["run_count"] == 1

from __future__ import annotations

import json
from pathlib import Path

from tools.feedback_review_gate import check_review_pack, main


def _base_item(statement_id: str = "S-001") -> dict[str, object]:
    return {
        "case_id": "C-TEST-001-乾-甲子乙丑丙寅丁卯",
        "statement_id": statement_id,
        "domain": "事业",
        "year": 2026,
        "rule_ids": ["MR-LAYER1"],
        "source_report": "reports/C-TEST-001-乾-甲子乙丑丙寅丁卯-content-report.md:10",
        "case_feedback": "cases/C-TEST-001-乾-甲子乙丑丙寅丁卯/feedback.md",
        "statement_rule_map": "cases/C-TEST-001-乾-甲子乙丑丙寅丁卯/statement_rule_map.json",
        "verdict": "pending",
    }


def _write_pack(tmp_path: Path, payload: dict[str, object]) -> Path:
    path = tmp_path / "review-pack.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _base_pack(items: list[dict[str, object]], *, ingest_blocked: bool) -> dict[str, object]:
    return {
        "id": "feedback-review-pack-test",
        "status": "pending_human_adjudication" if ingest_blocked else "ready_for_ingest",
        "ingest_blocked": ingest_blocked,
        "items": items,
        "next_ingest_commands_after_human_adjudication": [
            "python -m tools.feedback_ingest C-TEST-001-乾-甲子乙丑丙寅丁卯"
        ],
    }


def test_feedback_review_gate_blocks_pending_pack(tmp_path: Path) -> None:
    path = _write_pack(tmp_path, _base_pack([_base_item()], ingest_blocked=True))

    result = check_review_pack(path)

    assert result.status == "blocked"
    assert result.ingest_blocked is True
    assert result.total_items == 1
    assert result.pending_count == 1
    assert result.adjudicated_count == 0
    assert "1 item(s) still pending" in result.problems
    assert "no adjudicated item is available for ingestion" in result.problems


def test_feedback_review_gate_all_adjudicated_pack_is_ready(tmp_path: Path) -> None:
    item = _base_item()
    item["verdict"] = "y"
    path = _write_pack(tmp_path, _base_pack([item], ingest_blocked=False))

    result = check_review_pack(path)

    assert result.status == "ready"
    assert result.ingest_blocked is False
    assert result.pending_count == 0
    assert result.adjudicated_count == 1
    assert result.invalid_count == 0
    assert result.problems == []
    assert result.commands == ["python -m tools.feedback_ingest C-TEST-001-乾-甲子乙丑丙寅丁卯"]


def test_feedback_review_gate_partial_adjudication_requires_allow_partial(tmp_path: Path) -> None:
    adjudicated = _base_item("S-001")
    adjudicated["verdict"] = "n"
    pending = _base_item("S-002")
    path = _write_pack(tmp_path, _base_pack([adjudicated, pending], ingest_blocked=False))

    blocked = check_review_pack(path)
    allowed = check_review_pack(path, allow_partial=True)

    assert blocked.status == "blocked"
    assert blocked.pending_count == 1
    assert "1 item(s) still pending" in blocked.problems
    assert allowed.status == "ready"
    assert allowed.pending_count == 1
    assert allowed.adjudicated_count == 1
    assert allowed.problems == []


def test_feedback_review_gate_main_returns_nonzero_for_blocked_pack(tmp_path: Path, capsys) -> None:
    path = _write_pack(tmp_path, _base_pack([_base_item()], ingest_blocked=True))

    code = main([str(path)])
    captured = capsys.readouterr()

    assert code == 1
    assert "feedback review gate: blocked" in captured.out
    assert "1 item(s) still pending" in captured.out
    assert captured.err == ""


def test_feedback_review_gate_main_json_output_is_ascii_safe(tmp_path: Path, capsys) -> None:
    item = _base_item()
    item["verdict"] = "skip"
    path = _write_pack(tmp_path, _base_pack([item], ingest_blocked=False))

    code = main([str(path), "--format", "json"])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert code == 0
    assert payload["status"] == "ready"
    assert payload["adjudicated_count"] == 1
    assert "乾" not in captured.out
    assert "\\u4e7e" in captured.out


def test_feedback_review_gate_main_returns_error_for_missing_pack(capsys) -> None:
    code = main(["missing-review-pack.json"])
    captured = capsys.readouterr()

    assert code == 2
    assert captured.out == ""
    assert "feedback review gate: error: review pack not found" in captured.err

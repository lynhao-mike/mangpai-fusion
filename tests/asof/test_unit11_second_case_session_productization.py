from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

import pytest

from engine.asof.event_candidate import VerificationStatus
from engine.asof.session_contract import ConsultationState, SessionContractError
from tools import as_of_session_cli as cli

CASE_ID = "C-2026-RF000118-乾-己巳癸酉辛丑己丑"
FIXTURE = Path("cases") / CASE_ID / "asof_session_input.json"
TOOL = Path("tools/as_of_session_cli.py")
CONFIRMED_ID = "career-2020-job-change"
EXCLUDED_PRIOR_CASES = (
    "C-2026-024-坤-己巳壬申辛亥壬辰",
    "C-2026-RF000475-坤-戊辰辛酉己巳乙丑",
)
FORBIDDEN_IMPORTS = (
    "engine.pipeline",
    "engine.v5.runner",
    "engine.v5.preprod",
    "tools.render_report",
    "tools.feedback",
    "engine.asof.natal_capacity",
    "engine.asof.structural_track",
    "engine.asof.daiyun_context",
)


def _fixture_payload() -> dict[str, object]:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def test_unit11_second_real_case_runs_complete_session_archives_and_reads_back(tmp_path: Path) -> None:
    result = cli.run_and_archive_session(FIXTURE, archive_root=tmp_path)

    assert result.archive_result.status == "CREATED"
    assert result.archive_result.target == tmp_path / "asof-unit11-rf000118.json"
    assert result.session_result.final_envelope.state is ConsultationState.PROJECTED
    assert result.session_result.projection is not None
    assert result.artifact["artifact_id"] == "asof-unit11-rf000118"
    payload_digest = hashlib.sha256(_canonical(result.artifact["payload"])).hexdigest()
    assert result.artifact["payload_digest"] == payload_digest == result.archive_result.payload_digest
    assert result.artifact["source_digest"] == payload_digest

    second = cli.run_and_archive_session(FIXTURE, archive_root=tmp_path)
    assert second.archive_result.status == "UNCHANGED"
    assert second.archive_result.payload_digest == result.archive_result.payload_digest


def test_unit11_only_explicitly_verified_feedback_enters_success_semantics(tmp_path: Path) -> None:
    result = cli.run_and_archive_session(FIXTURE, archive_root=tmp_path)
    state = result.session_result.state_result.verified_state
    confirmed = tuple(
        entry.candidate.candidate_id
        for entry in result.session_result.state_result.ledger_entries
        if entry.candidate.verification_status is VerificationStatus.CONFIRMED
    )

    assert confirmed == state.verified_event_ids == (CONFIRMED_ID,)
    assert state.active_state_ids == (f"state:{CONFIRMED_ID}",)
    assert result.session_result.state_result.hypothesis_states == ()
    assert result.session_result.projection is not None
    assert tuple(item.candidate_id for item in result.session_result.projection.career_mainline) == (
        "career-future-from-verified-2020",
    )
    assert tuple(item.event_id for item in result.session_result.projection.wealth_decisions) == (CONFIRMED_ID,)
    assert len(result.session_result.projection.wealth_states) == 1

    archived_payload = result.artifact["payload"]
    semantic_text = json.dumps(
        {
            "ledger_entries": archived_payload["state_result"]["ledger_entries"],
            "verified_state": archived_payload["state_result"]["verified_state"],
            "projection": archived_payload["projection"],
        },
        ensure_ascii=False,
        sort_keys=True,
    )
    assert "2022年股票" not in semantic_text
    assert "2026年" not in semantic_text
    assert "2027年" not in semantic_text


def test_unit11_missing_required_field_returns_structured_cli_error(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    payload = _fixture_payload()
    del payload["draft"]
    invalid = tmp_path / "missing-draft.json"
    invalid.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    assert cli.main([str(invalid), "--archive-root", str(tmp_path / "archive")]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    error = json.loads(captured.err)
    assert error["status"] == "error"
    assert error["error_code"] == "INVALID_VALUE"
    assert error["error_type"] == "SessionContractError"
    assert "session.draft is required" in error["message"]

    with pytest.raises(SessionContractError) as caught:
        cli.run_and_archive_session(invalid, archive_root=tmp_path / "direct")
    assert caught.value.code == "INVALID_VALUE"


def test_unit11_callable_delegates_once_to_existing_runner_and_archive(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"runner": 0, "archive": 0}
    real_runner = cli.run_career_session
    real_archive = cli.archive_asof_state

    def runner(**values: object):
        calls["runner"] += 1
        return real_runner(**values)

    def archive(*args: object, **values: object):
        calls["archive"] += 1
        return real_archive(*args, **values)

    monkeypatch.setattr(cli, "run_career_session", runner)
    monkeypatch.setattr(cli, "archive_asof_state", archive)
    cli.run_and_archive_session(FIXTURE, archive_root=tmp_path)
    assert calls == {"runner": 1, "archive": 1}


def test_unit11_fixture_is_traceable_and_prior_units_never_use_second_case() -> None:
    payload = _fixture_payload()
    blind = payload["blind_input"]
    assert payload["case_id"] == CASE_ID
    assert blind["gender"] == "乾"
    assert [
        blind["pillars"][name]["stem"] + blind["pillars"][name]["branch"]
        for name in ("year", "month", "day", "hour")
    ] == ["己巳", "癸酉", "辛丑", "己丑"]
    assert [item["sequence"] for item in blind["daiyun"]] == list(range(1, 9))
    assert all(
        left["end_date"] == right["start_date"]
        for left, right in zip(blind["daiyun"], blind["daiyun"][1:])
    )
    assert "feedback.md:34" in payload["verifications"][0]["taxonomy_evidence"][0]

    for prior in (
        Path("tests/asof/test_unit8_real_case_blind_verification.py"),
        Path("tests/asof/test_unit9_real_case_future_state_projection.py"),
        Path("tests/asof/test_unit10_real_case_explicit_wealth_propagation.py"),
    ):
        assert CASE_ID not in prior.read_text(encoding="utf-8")
    fixture_text = FIXTURE.read_text(encoding="utf-8")
    assert all(case_id not in fixture_text for case_id in EXCLUDED_PRIOR_CASES)


def test_unit11_fresh_ast_import_and_manual_side_path_boundaries() -> None:
    source = TOOL.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.append(node.module or "")

    assert not [name for name in imported if name.startswith(FORBIDDEN_IMPORTS)]
    assert "run_career_session" in imported or "engine.asof.session_runner" in imported
    assert "archive_asof_state" in imported or "engine.asof.archive_integration" in imported
    assert "历史/手动" in source
    assert "手动 opt-in" in source
    assert "不切换任何生产默认入口" in source
    assert "asof-verified-artifact/v1" not in source

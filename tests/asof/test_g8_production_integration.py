from __future__ import annotations

import importlib
import json
from datetime import date
from pathlib import Path
from types import SimpleNamespace

import pytest

from engine.asof.event_candidate import (
    AnnualInteractionTrace,
    CompletionMode,
    ExtensionBoundary,
    LifeEventCandidate,
    RootLevel,
    VerificationStatus,
)
from engine.asof.natal_capacity import EvidenceRef, SourceCitation
from engine.asof.state_ledger import (
    AsOfRequest,
    DecisionAction,
    EventImpactAssessment,
    EventLedgerEntry,
    ImpactLevel,
    ImpactScope,
    Persistence,
    build_verified_state,
)


CASE_ID = "C-G8-001-乾-甲子乙丑丙寅丁卯"


def _integration():
    """在测试执行阶段导入，使首次 RED 仍能完成 pytest 收集。"""
    return importlib.import_module("tools.as_of_integration")


def _evidence(locator: str = "命局.事业", value: str = "官星有根") -> EvidenceRef:
    return EvidenceRef("case-input", locator, value)


def _entry(
    event_id: str,
    *,
    event_date: date,
    status: VerificationStatus = VerificationStatus.CONFIRMED,
    persistence: Persistence = Persistence.CROSS_DAIYUN,
    short_term_until: date | None = None,
) -> EventLedgerEntry:
    evidence = _evidence()
    trace = AnnualInteractionTrace(
        year=event_date.year,
        liunian="庚子",
        dayun_ganzhi="丙寅",
        relations=(evidence,),
        activated_node_ids=("career-authority",),
        domains=("career",),
        supporting_evidence=(evidence,),
        counter_evidence=(),
        trigger_strength="high",
        crossed_candidate_gate=True,
    )
    candidate = LifeEventCandidate(
        candidate_id=event_id,
        domain="career",
        event_type="responsibility_level_change",
        window_start=event_date,
        window_end=event_date,
        natal_evidence=(evidence,),
        daiyun_evidence=(evidence,),
        annual_trace=trace,
        root_level=RootLevel.STRONG_ROOT,
        root_evidence=(evidence,),
        source_citations=(SourceCitation("sources/test.md", 1, "测试引文"),),
        completion_mode=CompletionMode.ACTIVATE_EXISTING,
        supporting_evidence=(evidence,),
        counter_evidence=(),
        alternative_hypotheses=(),
        frozen_version="asof-prototype-v1",
        verification_status=status,
        extension_boundary=ExtensionBoundary.CROSS_DAIYUN_ELIGIBLE,
        is_primary_event=True,
    )
    assessment = EventImpactAssessment(
        event_id=event_id,
        event_date=event_date,
        event_type="responsibility_level_change",
        root_level=RootLevel.STRONG_ROOT,
        completion_mode=CompletionMode.ACTIVATE_EXISTING,
        system_suggested_impact=ImpactLevel.SIGNIFICANT,
        system_suggested_persistence=persistence,
        system_suggested_scope=ImpactScope.PRIMARY_DOMAIN,
        short_term_until=short_term_until,
        state_value=f"状态-{event_id}",
    )
    return EventLedgerEntry(candidate, assessment)


def _empty_state(as_of: date = date(2022, 12, 31)):
    return build_verified_state(
        AsOfRequest(CASE_ID, as_of),
        entries=(),
        daiyun_end=date(2025, 12, 31),
        current_center="教育管理岗位",
        reasonable_range=(),
    )


def test_parse_iso_date_accepts_only_canonical_yyyy_mm_dd() -> None:
    module = _integration()

    assert module.parse_iso_date("2022-12-31") == date(2022, 12, 31)
    for invalid in ("2022-2-03", "2022-02-30", "2022/02/03", " 2022-02-03"):
        with pytest.raises(ValueError):
            module.parse_iso_date(invalid)


@pytest.mark.parametrize(
    "argv",
    [
        ["input.md", "--as-of", "2022-12-31"],
        ["input.md", "--ledger", "ledger.json"],
    ],
)
def test_cli_requires_as_of_and_ledger_as_a_pair(argv: list[str], capsys) -> None:
    module = _integration()

    assert module.main(argv) == 2
    assert "--as-of" in capsys.readouterr().err


def test_cli_passes_explicit_ledger_context_to_generate_report(tmp_path, monkeypatch, capsys) -> None:
    module = _integration()
    ledger_path = tmp_path / "ledger.json"
    ledger_path.write_text(
        json.dumps(
            {
                "case_id": CASE_ID,
                "daiyun_end": "2025-12-31",
                "current_center": "教育管理岗位",
                "reasonable_range": ["同域权责调整"],
                "entries": [],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    expected_path = tmp_path / "report.md"
    captured: dict[str, object] = {}

    def fake_generate(input_path, **kwargs):
        captured["input_path"] = input_path
        captured.update(kwargs)
        return expected_path

    monkeypatch.setattr(module, "generate_report", fake_generate)

    exit_code = module.main(
        [
            "input.md",
            "--as-of",
            "2022-12-31",
            "--ledger",
            str(ledger_path),
            "--reports-dir",
            str(tmp_path),
        ]
    )

    assert exit_code == 0
    assert captured["as_of_date"] == date(2022, 12, 31)
    assert captured["entries"] == ()
    assert captured["daiyun_end"] == date(2025, 12, 31)
    assert captured["current_center"] == "教育管理岗位"
    assert captured["ledger_case_id"] == CASE_ID
    assert str(expected_path) in capsys.readouterr().out


def test_default_path_does_not_call_asof_and_writes_base_report(tmp_path, monkeypatch) -> None:
    module = _integration()
    output = SimpleNamespace(case_id=CASE_ID)
    calls: list[str] = []

    def fake_pipeline(*args, **kwargs):
        calls.append("pipeline")
        return output, object()

    def fake_render(*args, **kwargs):
        calls.append("render")
        return "# 原生产报告\n\n原正文\n"

    def forbidden_asof(*args, **kwargs):
        raise AssertionError("默认路径不得调用 as-of")

    monkeypatch.setattr(module, "run_pipeline_e2e", fake_pipeline)
    monkeypatch.setattr(module, "render_from_output", fake_render)
    monkeypatch.setattr(module, "build_verified_state", forbidden_asof)

    report_path = module.generate_report(
        "input.md",
        cases_dir=tmp_path / "cases",
        reports_dir=tmp_path / "reports",
    )

    assert calls == ["pipeline", "render"]
    assert report_path.read_text(encoding="utf-8") == "# 原生产报告\n\n原正文\n"
    assert "截止状态快照" not in report_path.read_text(encoding="utf-8")


def test_generate_report_calls_pipeline_render_and_asof_in_order(tmp_path, monkeypatch) -> None:
    module = _integration()
    output = SimpleNamespace(case_id=CASE_ID)
    state = _empty_state()
    calls: list[object] = []

    def fake_pipeline(input_path, **kwargs):
        calls.append(("pipeline", input_path, kwargs))
        return output, object()

    def fake_render(received_output, **kwargs):
        calls.append(("render", received_output, kwargs))
        return "# 原生产报告\n"

    def fake_build(request, **kwargs):
        calls.append(("asof", request, kwargs))
        return state

    monkeypatch.setattr(module, "run_pipeline_e2e", fake_pipeline)
    monkeypatch.setattr(module, "render_from_output", fake_render)
    monkeypatch.setattr(module, "build_verified_state", fake_build)

    report_path = module.generate_report(
        "input.md",
        as_of_date=date(2022, 12, 31),
        entries=(),
        daiyun_end=date(2025, 12, 31),
        current_center="教育管理岗位",
        reasonable_range=("同域权责调整",),
        ledger_case_id=CASE_ID,
        cases_dir=tmp_path / "cases",
        reports_dir=tmp_path / "reports",
    )

    assert [call[0] for call in calls] == ["pipeline", "render", "asof"]
    pipeline_kwargs = calls[0][2]
    assert pipeline_kwargs["do_render"] is False
    assert pipeline_kwargs["error_policy"] == "strict"
    render_kwargs = calls[1][2]
    assert render_kwargs["variant"] == "standard"
    assert render_kwargs["lint_before"] is True
    assert render_kwargs["skip_findings_save"] is True
    request = calls[2][1]
    assert request == AsOfRequest(CASE_ID, date(2022, 12, 31))
    assert report_path.exists()


def test_real_replay_excludes_future_unconfirmed_and_expired_events() -> None:
    module = _integration()
    state = build_verified_state(
        AsOfRequest(CASE_ID, date(2022, 12, 31)),
        entries=(
            _entry("active", event_date=date(2020, 1, 1)),
            _entry("future", event_date=date(2023, 1, 1)),
            _entry("unconfirmed", event_date=date(2021, 1, 1), status=VerificationStatus.UNKNOWN),
            _entry(
                "expired",
                event_date=date(2021, 1, 1),
                persistence=Persistence.SHORT_TERM,
                short_term_until=date(2021, 12, 31),
            ),
        ),
        daiyun_end=date(2025, 12, 31),
        current_center="教育管理岗位",
    )

    rendered = module.append_snapshot_section("# 原报告\n", state)

    assert "active" in rendered
    assert "future" not in rendered
    assert "unconfirmed" not in rendered
    assert "expired" not in rendered


def test_snapshot_append_preserves_base_and_is_idempotent() -> None:
    module = _integration()
    base = "# 原生产报告\n\n## 既有章节\n原正文\n"
    state = _empty_state()

    once = module.append_snapshot_section(base, state)
    twice = module.append_snapshot_section(once, state)

    marker = "## 截止状态快照"
    assert once.split(marker, 1)[0] == base.rstrip("\n") + "\n\n"
    assert once.count(marker) == 1
    assert twice == once


def test_empty_verified_state_renders_explicit_none_without_internal_ids() -> None:
    module = _integration()

    rendered = module.append_snapshot_section("# 原报告\n", _empty_state())

    assert "- 合理范围：无" in rendered
    assert "- 已核验事件：无" in rendered
    assert "- 当前有效状态：无" in rendered
    assert "- 现实路径状态：无" in rendered
    assert f"- 决策动作：{DecisionAction.OUTPUT.value}" in rendered
    assert "statement_id" not in rendered


def test_ledger_case_mismatch_fails_before_render_and_write(tmp_path, monkeypatch) -> None:
    module = _integration()
    output = SimpleNamespace(case_id=CASE_ID)
    rendered = False

    monkeypatch.setattr(module, "run_pipeline_e2e", lambda *args, **kwargs: (output, object()))

    def fake_render(*args, **kwargs):
        nonlocal rendered
        rendered = True
        return "# 不应生成\n"

    monkeypatch.setattr(module, "render_from_output", fake_render)

    with pytest.raises(ValueError, match="case_id"):
        module.generate_report(
            "input.md",
            as_of_date=date(2022, 12, 31),
            entries=(),
            daiyun_end=date(2025, 12, 31),
            current_center="教育管理岗位",
            ledger_case_id="C-WRONG",
            cases_dir=tmp_path / "cases",
            reports_dir=tmp_path / "reports",
        )

    assert rendered is False
    assert not (tmp_path / "reports").exists()


def test_existing_different_report_is_not_overwritten_and_no_temp_remains(tmp_path, monkeypatch) -> None:
    module = _integration()
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    target = reports_dir / f"{CASE_ID}-content-report.md"
    target.write_text("用户既有报告\n", encoding="utf-8")
    output = SimpleNamespace(case_id=CASE_ID)

    monkeypatch.setattr(module, "run_pipeline_e2e", lambda *args, **kwargs: (output, object()))
    monkeypatch.setattr(module, "render_from_output", lambda *args, **kwargs: "# 新报告\n")

    with pytest.raises(FileExistsError):
        module.generate_report(
            "input.md",
            cases_dir=tmp_path / "cases",
            reports_dir=reports_dir,
        )

    assert target.read_text(encoding="utf-8") == "用户既有报告\n"
    assert list(reports_dir.iterdir()) == [target]

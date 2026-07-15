from __future__ import annotations

import ast
from pathlib import Path

from engine.decision.models import ChartFactLedger
from engine.evaluation.models import BlindPrediction, BlindSchoolOutput, FrozenBlindRun, BlindTask
from engine.application.staged_parallel_runner import run_parallel


def _chart() -> ChartFactLedger:
    return ChartFactLedger(
        sex_marker="乾",
        solar_datetime="1990-06-15T12:00:00+08:00",
        four_pillars={"year": "庚午", "month": "壬午", "day": "辛亥", "hour": "甲午"},
        start_luck="1998",
        dayun_steps=[{"ganzhi": "丙辰", "start_year": 2018, "end_year": 2027}],
        liunian_steps=[{"year": 2024, "ganzhi": "甲辰"}],
    )


def _task() -> BlindTask:
    return BlindTask(
        task_id="career.path_type",
        domain="事业",
        claim_type="categorical",
        scoring_method="ordinal",
        quantifiable=True,
        high_risk=False,
        allowed_time_horizons=["ten_year"],
        required_input_fields=["four_pillars"],
        label_schema={"labels": ["employment", "entrepreneurship"]},
        evaluation_note="fixed test task",
    )


def _claim_run() -> FrozenBlindRun:
    output = BlindSchoolOutput(
        case_id="C-TASK10",
        school_id="duan",
        task_id="career.path_type",
        state="claim",
        rationale="structured fixture",
        predictions=[
            BlindPrediction(
                prediction_id="p-1",
                event_label="entrepreneurship",
                probability=0.7,
                time_window={"start_year": 2024, "end_year": 2027, "label": "ten_year"},
                evidence_refs=["e-1"],
                falsifier="not observed",
            )
        ],
    )
    return FrozenBlindRun(
        task_catalog_version="tasks/v1",
        rule_snapshot_id="rules/v1",
        frozen_at="content:fixed",
        outputs=[output],
        freeze_hash="hash-fixed",
    )


def test_parallel_runner_shares_chart_identity_but_isolates_branch_results(monkeypatch) -> None:
    chart = _chart()
    seen: dict[str, object] = {}
    legacy_snapshot = object()
    claim_snapshot = _claim_run()

    def fake_legacy_adapter(value: ChartFactLedger, *, case_id: str):
        seen["legacy_chart"] = value
        seen["case_id"] = case_id
        return object()

    def fake_run_pipeline(parsed, *, write_findings: bool):
        seen["parsed"] = parsed
        assert write_findings is False
        return legacy_snapshot

    def fake_claim_run(value, tasks, **kwargs):
        seen["claim_chart"] = value
        return claim_snapshot

    monkeypatch.setattr("engine.application.staged_parallel_runner.chart_to_parsed_input", fake_legacy_adapter)
    monkeypatch.setattr("engine.application.staged_parallel_runner.run_pipeline", fake_run_pipeline)
    monkeypatch.setattr("engine.application.staged_parallel_runner.generate_frozen_claim_run", fake_claim_run)

    result = run_parallel(chart, [_task()], case_id="C-TASK10", schools=["duan"])

    assert seen["legacy_chart"] is chart
    assert seen["claim_chart"] is chart
    assert result.legacy_snapshot is legacy_snapshot
    assert result.claim_snapshot is claim_snapshot
    assert result.legacy_error is None
    assert result.claim_error is None


def test_legacy_failure_does_not_damage_claim_snapshot(monkeypatch) -> None:
    claim_snapshot = _claim_run()
    monkeypatch.setattr(
        "engine.application.staged_parallel_runner.chart_to_parsed_input",
        lambda chart, *, case_id: object(),
    )
    monkeypatch.setattr(
        "engine.application.staged_parallel_runner.run_pipeline",
        lambda parsed, *, write_findings: (_ for _ in ()).throw(RuntimeError("legacy boom")),
    )
    monkeypatch.setattr(
        "engine.application.staged_parallel_runner.generate_frozen_claim_run",
        lambda *args, **kwargs: claim_snapshot,
    )

    result = run_parallel(_chart(), [_task()], case_id="C-TASK10", schools=["duan"])

    assert result.legacy_snapshot is None
    assert result.legacy_error == "RuntimeError: legacy boom"
    assert result.claim_snapshot is claim_snapshot
    assert result.claim_error is None
    assert result.claim_snapshot.to_dict() == claim_snapshot.to_dict()


def test_claim_failure_does_not_damage_legacy_snapshot(monkeypatch) -> None:
    legacy_snapshot = object()
    monkeypatch.setattr(
        "engine.application.staged_parallel_runner.chart_to_parsed_input",
        lambda chart, *, case_id: object(),
    )
    monkeypatch.setattr(
        "engine.application.staged_parallel_runner.run_pipeline",
        lambda parsed, *, write_findings: legacy_snapshot,
    )
    monkeypatch.setattr(
        "engine.application.staged_parallel_runner.generate_frozen_claim_run",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("claim boom")),
    )

    result = run_parallel(_chart(), [_task()], case_id="C-TASK10", schools=["duan"])

    assert result.legacy_snapshot is legacy_snapshot
    assert result.legacy_error is None
    assert result.claim_snapshot is None
    assert result.claim_error == "RuntimeError: claim boom"


def _imported_modules(path: Path) -> tuple[str, ...]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.append(node.module or "")
    return tuple(imported)


def test_parallel_and_comparison_modules_have_no_forbidden_imports() -> None:
    forbidden = (
        "feedback",
        "labels",
        "revealed",
        "report_view",
        "render_report",
        "cases",
        "school_claims",
    )
    for relative in (
        "engine/application/staged_parallel_runner.py",
        "engine/application/run_comparison.py",
    ):
        imports = _imported_modules(Path(relative))
        assert not any(token in module.lower() for token in forbidden for module in imports), relative

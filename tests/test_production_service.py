from __future__ import annotations

from pathlib import Path

from engine.application.production_service import (
    ProductionAnalysisService,
    SubmitAnalysisRequest,
)
from engine.infrastructure.analysis_store import (
    AnalysisArtifactRecord,
    SQLiteAnalysisStore,
)


def test_sqlite_store_roundtrip(tmp_path: Path) -> None:
    store = SQLiteAnalysisStore(tmp_path / "analysis.sqlite3")
    job = store.create_job(
        analysis_id="AN-test",
        input_path="cases/demo/input.md",
        input_sha256="abc",
        cache_key="cache-1",
        engine_version="1.3.0",
        render=True,
        template_name="report-v1.3.md",
        created_at="2026-05-30T00:00:00Z",
        started_at="2026-05-30T00:00:00Z",
    )

    assert job.analysis_id == "AN-test"
    assert job.status == "running"

    completed = store.complete_job(
        analysis_id="AN-test",
        case_id="C-2026-999-乾-甲子乙丑丙寅丁卯",
        summary={"final_conclusions_count": 3},
        completed_at="2026-05-30T00:00:01Z",
        artifacts=[
            AnalysisArtifactRecord(
                kind="analysis_output",
                path="cases/demo/findings/analysis_output.json",
                sha256="def",
                created_at="2026-05-30T00:00:01Z",
            )
        ],
    )

    assert completed.status == "completed"
    assert completed.summary["final_conclusions_count"] == 3
    assert completed.artifacts[0].kind == "analysis_output"


def test_cache_key_changes_when_render_options_change(tmp_path: Path) -> None:
    service = ProductionAnalysisService(
        store=SQLiteAnalysisStore(tmp_path / "analysis.sqlite3"),
        workspace_root=tmp_path,
    )

    key_a = service.compute_cache_key(
        input_sha256="abc",
        render=True,
        template_name="report-v1.3.md",
    )
    key_b = service.compute_cache_key(
        input_sha256="abc",
        render=False,
        template_name="report-v1.3.md",
    )
    key_c = service.compute_cache_key(
        input_sha256="abc",
        render=True,
        template_name="report-v1.4.md",
    )

    assert key_a != key_b
    assert key_a != key_c
    assert len(key_a) == 64


def test_submit_uses_cache_without_second_pipeline_run(monkeypatch, tmp_path: Path) -> None:
    case_dir = tmp_path / "cases" / "C-2026-999-乾-甲子乙丑丙寅丁卯"
    findings_dir = case_dir / "findings"
    reports_dir = tmp_path / "reports"
    findings_dir.mkdir(parents=True)
    reports_dir.mkdir()
    input_path = case_dir / "input.md"
    input_path.write_text("demo input", encoding="utf-8")

    class FakeOutput:
        case_id = "C-2026-999-乾-甲子乙丑丙寅丁卯"
        analysis_date = "2026-05-30"
        final_conclusions = []
        conflicts = []
        gate_results = []
        hash_chain_valid = True
        overall_confidence = None
        report_md = "# fake report\n"

    class FakeTiming:
        total_seconds = 0.01

    calls = {"count": 0}

    def fake_run_pipeline_e2e(*args, **kwargs):
        calls["count"] += 1
        (findings_dir / "analysis_output.json").write_text("{}", encoding="utf-8")
        (findings_dir / "timing.json").write_text("{}", encoding="utf-8")
        (case_dir / "statement_index.json").write_text("{}", encoding="utf-8")
        return FakeOutput(), FakeTiming()

    monkeypatch.setattr(
        "engine.application.production_service.run_pipeline_e2e",
        fake_run_pipeline_e2e,
    )

    service = ProductionAnalysisService(
        store=SQLiteAnalysisStore(tmp_path / "analysis.sqlite3"),
        workspace_root=tmp_path,
    )
    request = SubmitAnalysisRequest(
        input_path=input_path,
        render=True,
        cases_dir=tmp_path / "cases",
        reports_dir=reports_dir,
    )

    first = service.submit(request)
    second = service.submit(request)

    assert first["status"] == "completed"
    assert first["cache_hit"] is False
    assert second["status"] == "completed"
    assert second["cache_hit"] is True
    assert calls["count"] == 1
    assert any(a["kind"] == "report" for a in first["artifacts"])
    assert (reports_dir / "C-2026-999-乾-甲子乙丑丙寅丁卯-report.md").exists()

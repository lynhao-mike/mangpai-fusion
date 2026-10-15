from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

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
        template_name="report-v5.md",
        created_at="2026-05-30T00:00:00Z",
        started_at="2026-05-30T00:00:00Z",
    )

    assert job.analysis_id == "AN-test"
    assert job.status == "running"

    completed = store.complete_job(
        analysis_id="AN-test",
        case_id="C-2026-999-X",
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
        template_name="report-v5.md",
    )
    key_b = service.compute_cache_key(
        input_sha256="abc",
        render=False,
        template_name="report-v5.md",
    )
    key_c = service.compute_cache_key(
        input_sha256="abc",
        render=True,
        template_name="report-v5.md",
    )
    key_d = service.compute_cache_key(
        input_sha256="abc",
        render=True,
        template_name="report-v5.md",
        render_v6_preprod=True,
    )

    assert key_a != key_b
    assert key_a == key_c
    assert key_a != key_d
    assert len(key_a) == 64


def test_prepare_request_normalizes_paths_before_computing_cache_key(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    input_path = workspace / "cases" / "C-2026-999-X" / "input.md"
    input_path.parent.mkdir(parents=True)
    input_path.write_text("demo input", encoding="utf-8")
    service = ProductionAnalysisService(
        store=SQLiteAnalysisStore(tmp_path / "analysis.sqlite3"),
        workspace_root=workspace,
    )

    relative_request = SubmitAnalysisRequest(
        input_path=Path("cases/C-2026-999-X/input.md"),
        render=True,
        template_name="ignored-template.md",
        cases_dir=Path("cases"),
    )
    absolute_request = SubmitAnalysisRequest(
        input_path=input_path,
        render=True,
        template_name="another-ignored-template.md",
        cases_dir=workspace / "cases",
    )

    relative_normalized, relative_sha256, relative_key = service._prepare_request(relative_request)
    absolute_normalized, absolute_sha256, absolute_key = service._prepare_request(absolute_request)

    assert relative_normalized == absolute_normalized
    assert relative_normalized.input_path == input_path.resolve()
    assert relative_normalized.template_name == "report-v5.md"
    assert relative_sha256 == absolute_sha256
    assert relative_key == absolute_key


def test_prepare_request_uses_service_cache_key_method(tmp_path: Path, monkeypatch) -> None:
    workspace = tmp_path / "workspace"
    input_path = workspace / "cases" / "C-2026-999-X" / "input.md"
    input_path.parent.mkdir(parents=True)
    input_path.write_text("demo input", encoding="utf-8")
    service = ProductionAnalysisService(
        store=SQLiteAnalysisStore(tmp_path / "analysis.sqlite3"),
        workspace_root=workspace,
    )
    observed: dict[str, Any] = {}

    def fake_compute_cache_key(**kwargs: Any) -> str:
        observed.update(kwargs)
        return "service-cache-key"

    monkeypatch.setattr(service, "compute_cache_key", fake_compute_cache_key)
    normalized, input_sha256, cache_key = service._prepare_request(
        SubmitAnalysisRequest(input_path=Path("cases/C-2026-999-X/input.md"))
    )

    assert normalized.input_path == input_path.resolve()
    assert input_sha256
    assert cache_key == "service-cache-key"
    assert observed == {
        "input_sha256": input_sha256,
        "render": True,
        "template_name": "report-v5.md",
        "render_v6_preprod": False,
    }


def test_collect_artifacts_preserves_order_and_skips_missing_optional_v6_artifacts(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    case_id = "C-2026-999-X"
    case_dir = workspace / "cases" / case_id
    findings_dir = case_dir / "findings"
    reports_dir = workspace / "reports"
    findings_dir.mkdir(parents=True)
    reports_dir.mkdir(parents=True)
    for path in (
        findings_dir / "analysis_output.json",
        findings_dir / "timing.json",
        case_dir / "statement_index.json",
        case_dir / "statement_rule_map.json",
        reports_dir / f"{case_id}-v6-preprod-content-report.md",
        reports_dir / f"{case_id}-v6-preprod-content-report.v5.json",
    ):
        path.write_text("{}", encoding="utf-8")

    service = ProductionAnalysisService(
        store=SQLiteAnalysisStore(tmp_path / "analysis.sqlite3"),
        workspace_root=workspace,
    )
    artifacts = service._collect_artifacts(
        case_id=case_id,
        output=SimpleNamespace(report_md=None),
        timing=SimpleNamespace(total_seconds=0.01),
        request=SubmitAnalysisRequest(
            input_path=case_dir / "input.md",
            render=False,
            render_v6_preprod=True,
            cases_dir=workspace / "cases",
            reports_dir=reports_dir,
        ),
        completed_at="2026-05-30T00:00:00Z",
    )

    assert [artifact.kind for artifact in artifacts] == [
        "analysis_output",
        "timing",
        "statement_index",
        "statement_rule_map",
        "v6_preprod_report",
        "v5_prediction_ledger",
    ]


def test_build_summary_omits_confidence_when_unavailable(tmp_path: Path) -> None:
    service = ProductionAnalysisService(
        store=SQLiteAnalysisStore(tmp_path / "analysis.sqlite3"),
        workspace_root=tmp_path,
    )

    summary = service._build_summary(
        SimpleNamespace(
            case_id="C-2026-999-X",
            analysis_date="2026-05-30",
            final_conclusions=["a", "b"],
            conflicts=["c"],
            gate_results=["d", "e", "f"],
            hash_chain_valid=False,
            overall_confidence=None,
        ),
        SimpleNamespace(total_seconds=0.125),
    )

    assert summary == {
        "case_id": "C-2026-999-X",
        "analysis_date": "2026-05-30",
        "final_conclusions_count": 2,
        "conflicts_count": 1,
        "gate_results_count": 3,
        "hash_chain_valid": False,
        "pipeline_total_seconds": 0.125,
    }


def test_build_summary_includes_confidence_fields_when_available(tmp_path: Path) -> None:
    service = ProductionAnalysisService(
        store=SQLiteAnalysisStore(tmp_path / "analysis.sqlite3"),
        workspace_root=tmp_path,
    )

    summary = service._build_summary(
        SimpleNamespace(
            case_id="C-2026-999-X",
            analysis_date="2026-05-30",
            final_conclusions=[],
            conflicts=[],
            gate_results=[],
            hash_chain_valid=True,
            overall_confidence=SimpleNamespace(star="★★★", percent=78, label="较高"),
        ),
        SimpleNamespace(total_seconds=0.01),
    )

    assert summary["overall_confidence"] == {
        "star": "★★★",
        "percent": 78,
        "label": "较高",
    }
    assert set(summary) == {
        "case_id",
        "analysis_date",
        "final_conclusions_count",
        "conflicts_count",
        "gate_results_count",
        "hash_chain_valid",
        "pipeline_total_seconds",
        "overall_confidence",
    }


def test_submit_uses_cache_without_second_pipeline_run(monkeypatch, tmp_path: Path) -> None:
    case_dir = tmp_path / "cases" / "C-2026-999-X"
    findings_dir = case_dir / "findings"
    reports_dir = tmp_path / "reports"
    findings_dir.mkdir(parents=True)
    reports_dir.mkdir()
    input_path = case_dir / "input.md"
    input_path.write_text("demo input", encoding="utf-8")

    class FakeOutput:
        case_id = "C-2026-999-X"
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
        assert kwargs.get("report_variant") == "standard"
        assert kwargs.get("template_name") == "report-v5.md"
        for filename in (
            "analysis_output.json",
            "timing.json",
        ):
            (findings_dir / filename).write_text("{}", encoding="utf-8")
        (case_dir / "statement_index.json").write_text("{}", encoding="utf-8")
        (case_dir / "statement_rule_map.json").write_text("{}", encoding="utf-8")
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
    assert any(a["kind"] == "statement_rule_map" for a in first["artifacts"])
    assert (reports_dir / "C-2026-999-X-content-report.md").exists()


def test_submit_can_render_v6_preprod_artifacts(monkeypatch, tmp_path: Path) -> None:
    case_dir = tmp_path / "cases" / "C-2026-999-乾-甲子乙丑丙寅丁卯"
    findings_dir = case_dir / "findings"
    reports_dir = tmp_path / "reports"
    templates_dir = tmp_path / "templates"
    findings_dir.mkdir(parents=True)
    reports_dir.mkdir()
    templates_dir.mkdir()
    (templates_dir / "report-v6.md").write_text(
        (ROOT / "templates" / "report-v6.md").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    input_path = case_dir / "input.md"
    input_path.write_text(
        "# C-2026-999-乾-甲子乙丑丙寅丁卯 · 输入信息\n\n"
        "| **性别** | 男（乾造） |\n"
        "| **起运/交运** | 出生后 8 年起运 |\n\n"
        "| 柱别 | 主星 | 天干 | 地支 | 藏干 | 星运 | 空亡 | 纳音 | 神煞 |\n"
        "|---|---|---|---|---|---|---|---|---|\n"
        "| **年柱** | — | 甲 | 子 | — | — | — | — | — |\n"
        "| **月柱** | — | 乙 | 丑 | — | — | — | — | — |\n"
        "| **日柱** | — | 丙 | 寅 | — | — | — | — | — |\n"
        "| **时柱** | — | 丁 | 卯 | — | — | — | — | — |\n"
        "| 0 | 8-18 岁 | 2030-2040 | **戊辰** | — |\n",
        encoding="utf-8",
    )

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

    def fake_run_pipeline_e2e(*args, **kwargs):
        for filename in (
            "analysis_output.json",
            "timing.json",
        ):
            (findings_dir / filename).write_text("{}", encoding="utf-8")
        (case_dir / "statement_index.json").write_text("{}", encoding="utf-8")
        (case_dir / "statement_rule_map.json").write_text("{}", encoding="utf-8")
        return FakeOutput(), FakeTiming()

    monkeypatch.setattr(
        "engine.application.production_service.run_pipeline_e2e",
        fake_run_pipeline_e2e,
    )

    service = ProductionAnalysisService(
        store=SQLiteAnalysisStore(tmp_path / "analysis.sqlite3"),
        workspace_root=tmp_path,
    )
    result = service.submit(
        SubmitAnalysisRequest(
            input_path=input_path,
            render=True,
            render_v6_preprod=True,
            cases_dir=tmp_path / "cases",
            reports_dir=reports_dir,
        )
    )

    assert result["status"] == "completed", result.get("error")
    assert result["summary"]["v6_preprod_rendered"] is True
    v6_report = reports_dir / "C-2026-999-乾-甲子乙丑丙寅丁卯-v6-preprod-content-report.md"
    assert v6_report.exists()
    report_text = v6_report.read_text(encoding="utf-8")
    assert "[[" not in report_text
    assert "]([" not in report_text
    assert "[打开案例目录](../cases/C-2026-999-乾-甲子乙丑丙寅丁卯)" in report_text
    assert "[打开反馈文件](../cases/C-2026-999-乾-甲子乙丑丙寅丁卯/feedback.md)" in report_text
    assert (reports_dir / "C-2026-999-乾-甲子乙丑丙寅丁卯-v6-preprod-content-report.v5.json").exists()
    assert (reports_dir / "C-2026-999-乾-甲子乙丑丙寅丁卯-v6-preprod-content-report.decision-run.json").exists()
    kinds = {artifact["kind"] for artifact in result["artifacts"]}
    assert "v6_preprod_report" in kinds
    assert "v5_prediction_ledger" in kinds
    assert "decision_run_ledger" in kinds


def test_list_jobs_supports_status_and_case_filters(tmp_path: Path) -> None:
    store = SQLiteAnalysisStore(tmp_path / "analysis.sqlite3")
    service = ProductionAnalysisService(store=store, workspace_root=tmp_path)
    store.create_job(
        analysis_id="AN-1",
        input_path="cases/a/input.md",
        input_sha256="sha-a",
        cache_key="cache-a",
        engine_version="1.3.0",
        render=True,
        template_name="report-v5.md",
        created_at="2026-05-30T00:00:00Z",
        status="completed",
        case_id="C-A",
    )
    store.create_job(
        analysis_id="AN-2",
        input_path="cases/b/input.md",
        input_sha256="sha-b",
        cache_key="cache-b",
        engine_version="1.3.0",
        render=True,
        template_name="report-v5.md",
        created_at="2026-05-30T00:00:01Z",
        status="failed",
        case_id="C-B",
    )

    all_jobs = service.list()
    completed_jobs = service.list(status="completed")
    case_jobs = service.list(case_id="C-B")

    assert [job["analysis_id"] for job in all_jobs] == ["AN-2", "AN-1"]
    assert [job["analysis_id"] for job in completed_jobs] == ["AN-1"]
    assert [job["analysis_id"] for job in case_jobs] == ["AN-2"]


def test_enqueue_creates_queued_job(tmp_path: Path) -> None:
    case_dir = tmp_path / "cases" / "C-2026-998-X"
    case_dir.mkdir(parents=True)
    input_path = case_dir / "input.md"
    input_path.write_text("demo input", encoding="utf-8")
    service = ProductionAnalysisService(
        store=SQLiteAnalysisStore(tmp_path / "analysis.sqlite3"),
        workspace_root=tmp_path,
    )

    job = service.enqueue(SubmitAnalysisRequest(input_path=input_path, cases_dir=tmp_path / "cases"))

    assert job.status == "queued"
    assert job.input_path.endswith("input.md")
    assert job.started_at == ""
    persisted = service.store.get_job(job.analysis_id)
    assert persisted is not None
    assert persisted.status == "queued"


def test_run_queued_marks_running_then_completes(monkeypatch, tmp_path: Path) -> None:
    case_dir = tmp_path / "cases" / "C-2026-997-X"
    findings_dir = case_dir / "findings"
    findings_dir.mkdir(parents=True)
    input_path = case_dir / "input.md"
    input_path.write_text("demo input", encoding="utf-8")

    class FakeOutput:
        case_id = "C-2026-997-X"
        analysis_date = "2026-05-30"
        final_conclusions: list[Any] = []
        conflicts: list[Any] = []
        gate_results: list[Any] = []
        hash_chain_valid = True
        overall_confidence = None
        report_md = "# fake report\n"

    class FakeTiming:
        total_seconds = 0.01

    def fake_run_pipeline_e2e(*args, **kwargs):
        for filename in (
            "analysis_output.json",
            "timing.json",
        ):
            (findings_dir / filename).write_text("{}", encoding="utf-8")
        (case_dir / "statement_index.json").write_text("{}", encoding="utf-8")
        (case_dir / "statement_rule_map.json").write_text("{}", encoding="utf-8")
        return FakeOutput(), FakeTiming()

    monkeypatch.setattr(
        "engine.application.production_service.run_pipeline_e2e",
        fake_run_pipeline_e2e,
    )

    service = ProductionAnalysisService(
        store=SQLiteAnalysisStore(tmp_path / "analysis.sqlite3"),
        workspace_root=tmp_path,
    )
    request = SubmitAnalysisRequest(input_path=input_path, render=False, cases_dir=tmp_path / "cases")
    queued = service.enqueue(request)

    completed = service.run_queued(queued.analysis_id, request)

    assert completed.status == "completed"
    assert completed.started_at is not None
    assert completed.completed_at is not None
    assert completed.summary["case_id"] == "C-2026-997-X"


def test_submit_hard_fails_when_required_artifact_is_missing(monkeypatch, tmp_path: Path) -> None:
    case_dir = tmp_path / "cases" / "C-2026-996-X"
    findings_dir = case_dir / "findings"
    findings_dir.mkdir(parents=True)
    input_path = case_dir / "input.md"
    input_path.write_text("demo input", encoding="utf-8")

    class FakeOutput:
        case_id = "C-2026-996-X"
        analysis_date = "2026-05-30"
        final_conclusions: list[Any] = []
        conflicts: list[Any] = []
        gate_results: list[Any] = []
        hash_chain_valid = True
        overall_confidence = None
        report_md = "# fake report\n"

    class FakeTiming:
        total_seconds = 0.01

    def fake_run_pipeline_e2e(*args, **kwargs):
        (findings_dir / "analysis_output.json").write_text("{}", encoding="utf-8")
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
    job = service.submit(
        SubmitAnalysisRequest(
            input_path=input_path,
            render=True,
            cases_dir=tmp_path / "cases",
            reports_dir=tmp_path / "reports",
        )
    )

    assert job["status"] == "failed"
    assert "ArtifactGateError" in job["error"]
    assert "statement_rule_map" in job["error"]
    assert "timing" in job["error"]

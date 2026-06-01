from __future__ import annotations

import json
from pathlib import Path

from engine.application.job_queue import InMemoryAnalysisQueue
from engine.application.ports import PipelineAdapters
from engine.application.timing import PipelineTiming
from tools import timing_report
from tools.boundary_miner import _extract_features, mine_boundaries
from tools.rule_lifecycle import AppliedCase, Rule


def test_pipeline_timing_writes_meta_timing(tmp_path: Path) -> None:
    timing = PipelineTiming()
    with timing.step("discover"):
        pass

    path = timing.write_meta_timing(
        tmp_path,
        timing_type="feedback_ingest",
        run_id="run/001",
        case_id="C-TEST",
        extra={"ok": True},
    )

    assert path.name == "feedback_ingest-run-001.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["timing_type"] == "feedback_ingest"
    assert payload["case_id"] == "C-TEST"
    assert payload["extra"] == {"ok": True}
    assert payload["steps"]["discover"] >= 0


def test_timing_report_collects_case_and_meta_timings(monkeypatch, tmp_path: Path) -> None:
    cases_dir = tmp_path / "cases"
    meta_dir = tmp_path / "META"
    case_findings = cases_dir / "C-001" / "findings"
    meta_timings = meta_dir / "timings"
    case_findings.mkdir(parents=True)
    meta_timings.mkdir(parents=True)
    (case_findings / "timing.json").write_text(
        json.dumps({"case_id": "C-001", "total_seconds": 2.0, "steps": {"energy": 1.0}}),
        encoding="utf-8",
    )
    (meta_timings / "batch-run.json").write_text(
        json.dumps({"run_id": "batch-run", "timing_type": "batch_intake", "total_seconds": 4.0, "steps": {"discover": 1.0}}),
        encoding="utf-8",
    )
    monkeypatch.setattr(timing_report, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(timing_report, "CASES_DIR", cases_dir)
    monkeypatch.setattr(timing_report, "META_DIR", meta_dir)

    timings = timing_report.collect_timings()
    summary = timing_report.build_summary(timings)

    assert summary["case_count"] == 1
    assert summary["timing_count"] == 2
    assert summary["per_type"]["pipeline"]["count"] == 1
    assert summary["per_type"]["batch_intake"]["count"] == 1


def test_boundary_miner_reuses_co_rule_cache(monkeypatch, tmp_path: Path) -> None:
    calls = {"count": 0}

    def fake_extract(case_id: str, *, cases_dir: Path) -> set[str]:
        calls["count"] += 1
        return {"RULE-A", "RULE-B"}

    monkeypatch.setattr("tools.boundary_miner._extract_co_rules_from_case", fake_extract)
    cache: dict[str, set[str]] = {}
    case = AppliedCase(case_id="C-001", year=None, hit=False)

    first = _extract_features(case, exclude_rule="RULE-A", cases_dir=tmp_path, co_rule_cache=cache)
    second = _extract_features(case, exclude_rule="RULE-B", cases_dir=tmp_path, co_rule_cache=cache)

    assert calls["count"] == 1
    assert "co_rule=RULE-B" in first
    assert "co_rule=RULE-A" in second


def test_mine_boundaries_accepts_cache_parameter(monkeypatch, tmp_path: Path) -> None:
    fake = Rule(id="RULE-A", school="duan", topic="fake", status="confirmed", hits=0, misses=5)
    monkeypatch.setattr("tools.boundary_miner.load_rule", lambda rid: fake)

    result = mine_boundaries("RULE-A", dry_run=True, cases_dir=tmp_path, co_rule_cache={})

    assert result.rule_id == "RULE-A"
    assert result.skipped


def test_run_pipeline_e2e_accepts_explicit_adapters() -> None:
    adapters = PipelineAdapters()
    assert adapters.preflight is None
    assert adapters.renderer is None
    assert adapters.feedback is None


def test_in_memory_analysis_queue_submit_returns_queued_result() -> None:
    class FakeService:
        def __init__(self) -> None:
            self.enqueued: list[object] = []

        def enqueue(self, request):
            self.enqueued.append(request)

            class FakeRecord:
                analysis_id = "AN-queued"
                status = "queued"

            return FakeRecord()

        def run_queued(self, analysis_id, request):  # pragma: no cover - worker not started here
            raise AssertionError("worker should not run in this unit test")

    service = FakeService()
    queue = InMemoryAnalysisQueue(service)  # type: ignore[arg-type]

    result = queue.submit(object())  # type: ignore[arg-type]

    assert result.to_dict() == {
        "analysis_id": "AN-queued",
        "status": "queued",
        "queued": True,
    }
    assert service.enqueued == [service.enqueued[0]]

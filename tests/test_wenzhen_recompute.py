from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from engine.application import RecomputeRequest as ExportedRecomputeRequest
from engine.application import recompute_wenzhen_case as exported_recompute_wenzhen_case
from engine.application.recompute import (
    RecomputeHardGateError,
    RecomputeRequest,
    recompute_wenzhen_case,
)
from tools import recompute_wenzhen_case as recompute_cli


CASE_ID = "C-2026-999-乾-甲子乙丑丙寅丁卯"


class FakeOutput:
    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": CASE_ID,
            "schema_version": "1.4.0",
            "pipeline_version": "1.4.0",
            "overall_confidence": {"star": 4, "percent": 78, "posterior": 0.78},
            "final_conclusions": [
                {
                    "statement": "事业以技术型输出为主",
                    "confidence": {"star": 4, "percent": 80},
                    "trace_ids": ["R-CAREER-001"],
                }
            ],
            "conflicts": [],
            "theory_findings": {"summary": "theory ok", "confidence_summary": {"percent": 76}},
            "blind_findings": {"summary": "blind ok", "confidence_summary": {"percent": 79}},
            "fusion_findings": {"conclusions": [{"statement": "fusion ok"}]},
            "parallel_analysis": {
                "domains": [
                    {
                        "domain": "career",
                        "consensus": {"final_statement": "事业可用"},
                        "readings": [{"expert": "duan", "claim": "技术"}],
                    }
                ]
            },
        }


class FakeTiming:
    total_seconds = 0.12


def test_recompute_writes_required_artifacts(tmp_path: Path) -> None:
    case_dir = tmp_path / "cases" / CASE_ID
    findings_dir = case_dir / "findings"
    findings_dir.mkdir(parents=True)
    input_path = case_dir / "input.md"
    input_path.write_text("demo input", encoding="utf-8")
    (case_dir / "feedback.md").write_text(
        "[S-999-abc123] [y] 已验证\n[S-999-unknown] [n] 不成立\n",
        encoding="utf-8",
    )
    (findings_dir / "analysis_output.json").write_text(
        json.dumps(
            {
                "case_id": CASE_ID,
                "overall_confidence": {"star": 3, "percent": 65},
                "final_conclusions": [
                    {
                        "statement": "旧结论",
                        "confidence": {"star": 3, "percent": 65},
                        "trace_ids": ["R-OLD"],
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    def fake_pipeline(*args: Any, **kwargs: Any) -> tuple[FakeOutput, FakeTiming]:
        assert kwargs["do_render"] is True
        assert kwargs["error_policy"] == "strict"
        (case_dir / "statement_index.json").write_text(
            json.dumps(
                {
                    "case_id": CASE_ID,
                    "statements": [
                        {
                            "statement_id": "S-999-abc123",
                            "text": "事业以技术型输出为主",
                            "rule_ids": ["R-CAREER-001"],
                        }
                    ],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        return FakeOutput(), FakeTiming()

    result = recompute_wenzhen_case(
        RecomputeRequest(
            input_path=input_path,
            cases_dir=tmp_path / "cases",
            reports_dir=tmp_path / "reports",
        ),
        pipeline_runner=fake_pipeline,
    )

    assert result.case_id == CASE_ID
    for artifact in result.artifacts.values():
        assert artifact.exists()
    manifest = json.loads((case_dir / "recompute_manifest.json").read_text(encoding="utf-8"))
    assert manifest["hard_gates"]["statement_index_statement_count"] == 1
    assert manifest["artifacts"]["statement_index"].endswith("statement_index.json")
    matrix = json.loads((case_dir / "school_verdict_matrix.json").read_text(encoding="utf-8"))
    assert [row["school"] for row in matrix["schools"]] == ["theory", "blind", "fusion"]
    diff = json.loads((case_dir / "conclusion_diff.json").read_text(encoding="utf-8"))
    assert diff["added"]
    delta = json.loads((case_dir / "confidence_delta.json").read_text(encoding="utf-8"))
    assert delta["overall"]["delta_percent"] == 13
    binding = json.loads((case_dir / "feedback_binding_check.json").read_text(encoding="utf-8"))
    assert binding["structured_feedback_count"] == 2
    assert binding["structured_feedback_ready"] is False
    assert binding["unknown_structured_statement_ids"] == ["S-999-unknown"]


def test_recompute_is_exported_from_application_package() -> None:
    assert ExportedRecomputeRequest is RecomputeRequest
    assert exported_recompute_wenzhen_case is recompute_wenzhen_case


def test_recompute_hard_gate_fails_empty_statement_index(tmp_path: Path) -> None:
    case_dir = tmp_path / "cases" / CASE_ID
    case_dir.mkdir(parents=True)
    input_path = case_dir / "input.md"
    input_path.write_text("demo input", encoding="utf-8")

    def fake_pipeline(*args: Any, **kwargs: Any) -> tuple[FakeOutput, FakeTiming]:
        (case_dir / "statement_index.json").write_text(
            json.dumps({"case_id": CASE_ID, "statements": []}, ensure_ascii=False),
            encoding="utf-8",
        )
        return FakeOutput(), FakeTiming()

    with pytest.raises(RecomputeHardGateError):
        recompute_wenzhen_case(
            RecomputeRequest(input_path=input_path, cases_dir=tmp_path / "cases"),
            pipeline_runner=fake_pipeline,
        )


def test_recompute_cli_returns_hard_gate_exit_code(monkeypatch, tmp_path: Path, capsys) -> None:
    case_dir = tmp_path / "cases" / CASE_ID
    case_dir.mkdir(parents=True)
    (case_dir / "input.md").write_text("demo input", encoding="utf-8")

    def fake_recompute(request: RecomputeRequest):
        raise RecomputeHardGateError("statement index empty")

    monkeypatch.setattr(recompute_cli, "recompute_wenzhen_case", fake_recompute)

    code = recompute_cli.main([CASE_ID, "--cases-dir", str(tmp_path / "cases"), "--json"])

    captured = capsys.readouterr()
    assert code == 2
    payload = json.loads(captured.out)
    assert payload["status"] == "hard_gate_failed"
    assert "statement index empty" in payload["error"]

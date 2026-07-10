from __future__ import annotations

from pathlib import Path

from engine.application.recompute import RecomputeRequest, recompute_wenzhen_case


class _Output:
    report_md = "# auto report\n\n2031 辛亥年（首选婚期）\n"

    def to_dict(self) -> dict:
        return {
            "case_id": "C-2099-001-乾-甲子乙丑丙寅丁卯",
            "pipeline_version": "test",
            "schema_version": "test",
        }


class _Timing:
    total_seconds = 0.01


def _fake_pipeline_runner(*args, **kwargs):
    return _Output(), _Timing()


def test_recompute_writes_rendered_report_md(tmp_path: Path) -> None:
    case_id = "C-2099-001-乾-甲子乙丑丙寅丁卯"
    cases_dir = tmp_path / "cases"
    reports_dir = tmp_path / "reports"
    case_dir = cases_dir / case_id
    case_dir.mkdir(parents=True)
    input_path = case_dir / "input.md"
    input_path.write_text("# input\n", encoding="utf-8")

    result = recompute_wenzhen_case(
        RecomputeRequest(
            input_path=input_path,
            cases_dir=cases_dir,
            reports_dir=reports_dir,
            require_statement_index=False,
        ),
        pipeline_runner=_fake_pipeline_runner,
    )

    report_path = reports_dir / f"{case_id}-content-report.md"
    assert result.manifest["artifacts"]["content_report"] == str(report_path)
    assert report_path.read_text(encoding="utf-8") == _Output.report_md

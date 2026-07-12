import json
from pathlib import Path

from engine.evaluation.case_audit import audit_case, audit_cases, write_case_manifest

FIXTURES = Path("tests/fixtures/school_capability")


def test_audit_marks_feedback_calibrated_report_as_contaminated() -> None:
    record = audit_case(
        FIXTURES / "cases/C-TEST-001",
        FIXTURES / "reports",
    )

    assert record.has_input is True
    assert record.has_feedback is True
    assert record.feedback_quantifiable is True
    assert record.has_existing_report is True
    assert "feedback_calibrated_report" in record.contamination_flags
    assert record.eligibility == "development_only"


def test_audit_never_mutates_case_files() -> None:
    input_path = FIXTURES / "cases/C-TEST-001/input.md"
    before = input_path.read_bytes()

    audit_case(input_path.parent, FIXTURES / "reports")

    assert input_path.read_bytes() == before


def test_uncertain_contamination_requires_manual_review(tmp_path: Path) -> None:
    case_dir = tmp_path / "cases/C-TEST-UNCERTAIN"
    case_dir.mkdir(parents=True)
    (case_dir / "input.md").write_text("# 命盘\n四柱：甲子 乙丑 丙寅 丁卯\n", encoding="utf-8")
    (case_dir / "feedback.md").write_text("2024 年结果：通过。\n", encoding="utf-8")
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    (reports_dir / "C-TEST-UNCERTAIN-content-report.md").write_text(
        "# 报告\n参考过往情况进行判断。\n", encoding="utf-8"
    )

    record = audit_case(case_dir, reports_dir)

    assert record.eligibility == "manual_review"
    assert record.eligibility != "blind_candidate"


def test_audit_cases_ignores_non_directories_and_is_sorted(tmp_path: Path) -> None:
    cases_dir = tmp_path / "cases"
    (cases_dir / "C-TEST-002").mkdir(parents=True)
    (cases_dir / "C-TEST-001").mkdir()
    (cases_dir / "README.md").write_text("not a case", encoding="utf-8")

    records = audit_cases(cases_dir, tmp_path / "reports")

    assert [record.case_id for record in records] == ["C-TEST-001", "C-TEST-002"]


def test_write_case_manifest_serializes_all_records(tmp_path: Path) -> None:
    record = audit_case(
        FIXTURES / "cases/C-TEST-001",
        FIXTURES / "reports",
    )
    manifest_path = tmp_path / "nested/case-manifest.json"

    write_case_manifest([record], manifest_path)

    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "school-capability-case-manifest/v1"
    assert payload["generated_at"].endswith("Z")
    assert payload["records"] == [record.to_dict()]

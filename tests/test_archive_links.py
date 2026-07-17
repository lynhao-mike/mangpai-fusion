from __future__ import annotations

from pathlib import Path

from engine.v5 import run_v5
from engine.v5.report_view import build_report_v6_context, render_template_text
from tools.check_archive_links import check_links, check_sibling_reports
from tools.fix_archive_links import migrate_archive


def test_report_v6_archive_links_are_wrapped_once_and_resolve_from_report(tmp_path: Path) -> None:
    reports_dir = tmp_path / "reports"
    case_dir = tmp_path / "cases" / "C-2026-999-乾-甲子乙丑丙寅丁卯"
    reports_dir.mkdir(parents=True)
    case_dir.mkdir(parents=True)
    report_path = reports_dir / "C-2026-999-乾-甲子乙丑丙寅丁卯-v6-preprod-content-report.md"
    feedback_path = case_dir / "feedback.md"
    feedback_path.write_text("# feedback\n", encoding="utf-8")

    template_text = (
        "- 报告路径：[打开报告文件]({{ 报告路径 }})\n"
        "- 案例目录：[打开案例目录]({{ 案例目录 }})\n"
        "- 反馈入口：[打开反馈文件]({{ 反馈入口 }})\n"
    )
    output = run_v5(
        {"case_id": "C-2026-999-乾-甲子乙丑丙寅丁卯", "pillars": ["甲子", "乙丑", "丙寅", "丁卯"]}
    )
    context = build_report_v6_context(
        output,
        template_text=template_text,
        report_path=report_path.name,
        case_dir="../cases/C-2026-999-乾-甲子乙丑丙寅丁卯",
        feedback_path="../cases/C-2026-999-乾-甲子乙丑丙寅丁卯/feedback.md",
    )

    rendered = render_template_text(template_text, context)
    report_path.write_text(rendered, encoding="utf-8")

    assert "[[" not in rendered
    assert "]([" not in rendered
    assert rendered.count("[打开报告文件](") == 1
    assert rendered.count("[打开案例目录](") == 1
    assert rendered.count("[打开反馈文件](") == 1
    assert check_links({report_path: rendered}) == []


def test_sibling_reports_group_by_full_case_identity_with_injected_texts(tmp_path: Path) -> None:
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    first = reports_dir / "C-2026-034-乾-甲子乙丑丙寅丁卯-content-report.md"
    same_case_sibling = reports_dir / "C-2026-034-乾-甲子乙丑丙寅丁卯-v6-preprod-content-report.md"
    different_chart = reports_dir / "C-2026-034-坤-戊辰己巳庚午辛未-content-report.md"
    texts = {
        first: f"[{same_case_sibling.name}]({same_case_sibling.name})\n",
        same_case_sibling: f"[{first.name}]({first.name})\n",
        different_chart: "# unrelated chart with reused short case id\n",
    }

    assert check_sibling_reports(texts) == []


def test_sibling_report_check_uses_only_injected_texts(tmp_path: Path) -> None:
    report = tmp_path / "reports" / "C-2026-034-乾-甲子乙丑丙寅丁卯-content-report.md"

    assert check_sibling_reports({report: "# isolated fixture\n"}) == []


def _write(path: Path, text: str = "# fixture\n") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def test_migration_repairs_v6_root_targets_and_known_nested_links(tmp_path: Path) -> None:
    identity = "C-2026-999-乾-甲子乙丑丙寅丁卯"
    case_dir = tmp_path / "cases" / identity
    report = tmp_path / "reports" / f"{identity}-v6-preprod-content-report.md"
    _write(case_dir / "feedback.md")
    _write(
        report,
        "- [报告](reports/" + report.name + ")\n"
        "- [案例](cases/" + identity + ")\n"
        "- [打开反馈文件]([打开反馈文件](cases/" + identity + "/feedback.md))\n",
    )

    result = migrate_archive(tmp_path)
    migrated = report.read_text(encoding="utf-8")

    assert result.changed == [f"reports/{report.name}"]
    assert result.unresolved == []
    assert f"[报告]({report.name})" in migrated
    assert f"[案例](../cases/{identity})" in migrated
    assert f"[打开反馈文件](../cases/{identity}/feedback.md)" in migrated
    assert migrated.count("[打开反馈文件]") == 1


def test_case_old_report_link_changes_only_for_one_full_identity_canonical(tmp_path: Path) -> None:
    identity = "C-2026-101-坤-戊辰己巳庚午辛未"
    case_file = _write(
        tmp_path / "cases" / identity / "analysis.md",
        f"[旧报告](../../reports/{identity}-report.md)\n",
    )
    canonical = _write(tmp_path / "reports" / f"{identity}-content-report.md")

    result = migrate_archive(tmp_path)

    assert result.unresolved == []
    assert f"../../reports/{canonical.name}" in case_file.read_text(encoding="utf-8")


def test_existing_legacy_named_report_is_not_migrated_or_unresolved(tmp_path: Path) -> None:
    identity = "C-2026-RF000001-乾-甲子乙丑丙寅丁卯"
    report = _write(tmp_path / "reports" / f"{identity}-analyst-report.md")
    case_file = _write(
        tmp_path / "cases" / identity / "feedback.md",
        f"[报告](../../reports/{report.name})\n",
    )

    result = migrate_archive(tmp_path)

    assert result.changed == []
    assert result.unresolved == []
    assert report.name in case_file.read_text(encoding="utf-8")


def test_case_old_report_link_stays_unresolved_when_canonical_missing(tmp_path: Path) -> None:
    identity = "C-2026-102-乾-甲子乙丑丙寅丁卯"
    old_target = f"../../reports/{identity}-report.md"
    case_file = _write(tmp_path / "cases" / identity / "feedback.md", f"[旧报告]({old_target})\n")

    result = migrate_archive(tmp_path)

    assert case_file.read_text(encoding="utf-8") == f"[旧报告]({old_target})\n"
    assert len(result.unresolved) == 1
    assert result.unresolved[0].reason == "no canonical report for full case identity"


def test_case_old_report_link_stays_unresolved_when_canonical_is_ambiguous(tmp_path: Path) -> None:
    identity = "C-2026-103-乾-甲子乙丑丙寅丁卯"
    old_target = f"../../reports/{identity}-report.md"
    case_file = _write(tmp_path / "cases" / identity / "analysis.md", f"[旧报告]({old_target})\n")
    _write(tmp_path / "reports" / f"{identity}-content-report.md")
    _write(tmp_path / "reports" / f"{identity}-v6-preprod-content-report.md")

    result = migrate_archive(tmp_path)

    assert old_target in case_file.read_text(encoding="utf-8")
    assert len(result.unresolved) == 1
    assert result.unresolved[0].reason == "multiple canonical reports for full case identity"


def test_migration_repairs_readme_template_and_unique_event_report_target(tmp_path: Path) -> None:
    identity = "C-2026-104-坤-戊辰己巳庚午辛未"
    _write(tmp_path / "templates" / "report-v6.md")
    readme = _write(tmp_path / "reports" / "README.md", "[模板](../templates/report-v1.3.md)\n")
    canonical = _write(tmp_path / "reports" / f"{identity}-content-report.md")
    event = _write(
        tmp_path / "reports" / f"{identity}-events.md",
        f"[正式报告]({identity}-report.md)\n",
    )

    result = migrate_archive(tmp_path)

    assert result.unresolved == []
    assert "../templates/report-v6.md" in readme.read_text(encoding="utf-8")
    assert canonical.name in event.read_text(encoding="utf-8")


def test_migration_adds_bidirectional_sibling_links_by_full_identity_and_is_idempotent(tmp_path: Path) -> None:
    identity = "C-2026-105-乾-甲子乙丑丙寅丁卯"
    first = _write(tmp_path / "reports" / f"{identity}-content-report.md")
    second = _write(tmp_path / "reports" / f"{identity}-v6-preprod-content-report.md")
    unrelated = _write(tmp_path / "reports" / "C-2026-105-坤-戊辰己巳庚午辛未-content-report.md")

    first_result = migrate_archive(tmp_path)
    first_snapshot = {path: path.read_text(encoding="utf-8") for path in (first, second, unrelated)}
    second_result = migrate_archive(tmp_path)

    assert sorted(first_result.changed) == sorted([f"reports/{first.name}", f"reports/{second.name}"])
    assert second.name in first_snapshot[first]
    assert first.name in first_snapshot[second]
    assert identity not in first_snapshot[unrelated]
    assert second_result.changed == []
    assert {path: path.read_text(encoding="utf-8") for path in first_snapshot} == first_snapshot

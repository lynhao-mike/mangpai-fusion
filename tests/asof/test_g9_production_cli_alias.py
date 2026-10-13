from __future__ import annotations

import ast
import importlib
from pathlib import Path
from types import SimpleNamespace

import pytest


CASE_ID = "C-G9-P1-001-乾-甲子乙丑丙寅丁卯"
BASE_REPORT = "# 原生产报告\n\n原正文\n"


def _alias():
    """在行为阶段导入，使目标模块缺失时 pytest 仍能完成收集。"""
    return importlib.import_module("tools.production_as_of_cli")


def _install_real_report_path(monkeypatch):
    """保留真实 generate_report，只隔离其既有 pipeline/render 下层依赖。"""
    integration = importlib.import_module("tools.as_of_integration")
    output = SimpleNamespace(case_id=CASE_ID)
    monkeypatch.setattr(
        integration,
        "run_pipeline_e2e",
        lambda *args, **kwargs: (output, object()),
    )
    monkeypatch.setattr(
        integration,
        "render_from_output",
        lambda *args, **kwargs: BASE_REPORT,
    )
    return integration


def test_defaults_are_current_working_directory_production_paths(
    tmp_path, monkeypatch
) -> None:
    module = _alias()
    integration = _install_real_report_path(monkeypatch)
    original_generate = integration.generate_report
    captured: dict[str, object] = {}

    def spy_generate(input_path, **kwargs):
        captured["input_path"] = input_path
        captured.update(kwargs)
        return original_generate(input_path, **kwargs)

    monkeypatch.setattr(module, "generate_report", spy_generate)
    monkeypatch.chdir(tmp_path)

    assert module.main(["input.md"]) == 0
    assert captured["cases_dir"] == tmp_path / "cases"
    assert captured["reports_dir"] == tmp_path / "reports"
    assert (tmp_path / "reports" / f"{CASE_ID}-content-report.md").exists()


def test_explicit_directories_are_forwarded_unchanged(tmp_path, monkeypatch) -> None:
    module = _alias()
    integration = _install_real_report_path(monkeypatch)
    original_generate = integration.generate_report
    captured: dict[str, object] = {}

    def spy_generate(input_path, **kwargs):
        captured.update(kwargs)
        return original_generate(input_path, **kwargs)

    monkeypatch.setattr(module, "generate_report", spy_generate)
    cases_dir = str(tmp_path / "custom-cases")
    reports_dir = str(tmp_path / "custom-reports")

    assert (
        module.main(
            [
                "input.md",
                "--cases-dir",
                cases_dir,
                "--reports-dir",
                reports_dir,
            ]
        )
        == 0
    )
    assert captured["cases_dir"] is cases_dir
    assert captured["reports_dir"] is reports_dir


@pytest.mark.parametrize(
    "argv",
    [
        ["input.md", "--as-of", "2022-12-31"],
        ["input.md", "--ledger", "ledger.json"],
    ],
)
def test_as_of_and_ledger_must_be_provided_as_a_pair(
    argv: list[str], monkeypatch, capsys
) -> None:
    module = _alias()

    def forbidden_generate(*args, **kwargs):
        raise AssertionError("配对校验失败时不得调用 generate_report")

    monkeypatch.setattr(module, "generate_report", forbidden_generate)

    assert module.main(argv) == 2
    assert "--as-of" in capsys.readouterr().err


def test_default_mode_is_byte_identical_to_direct_integration(
    tmp_path, monkeypatch
) -> None:
    module = _alias()
    integration = _install_real_report_path(monkeypatch)
    cases_dir = tmp_path / "cases"
    reports_dir = tmp_path / "reports"

    direct_path = integration.generate_report(
        "input.md",
        cases_dir=cases_dir,
        reports_dir=reports_dir,
    )
    direct_bytes = direct_path.read_bytes()

    assert (
        module.main(
            [
                "input.md",
                "--cases-dir",
                str(cases_dir),
                "--reports-dir",
                str(reports_dir),
            ]
        )
        == 0
    )
    assert direct_path.read_bytes() == direct_bytes
    assert "截止状态快照" not in direct_path.read_text(encoding="utf-8")


def test_static_import_boundary_contains_only_the_delegated_module() -> None:
    module = _alias()
    source = Path(module.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_modules = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }
    imported_modules.update(
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    )

    assert "tools.as_of_integration" in imported_modules
    assert "engine.asof" not in imported_modules
    assert "engine.application.production_service" not in imported_modules
    assert "tools.production_api" not in imported_modules

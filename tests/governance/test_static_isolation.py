from __future__ import annotations

from pathlib import Path

from tests.governance.static_isolation_content import (
    governance_contamination_issues,
    governance_yaml_issues,
)
from tests.governance.static_isolation_scanner import (
    GOVERNANCE_OUTWARD_IMPORTS,
    ROOT,
    fact_snapshot_write_issues,
    forbidden_import_issues,
    legacy_shadow_consumer_paths,
    new_governance_python_paths,
    python_files,
    school_view_adapter_paths,
    shadow_runner_consumer_issues,
    system_time_liunian_issues,
)


def test_fixture_detects_governance_outward_imports(tmp_path: Path) -> None:
    # Given: a source fixture with a forbidden outward domain import.
    source = tmp_path / "bad_governance.py"
    source.write_text(
        "from engine.application.pipeline_runner import run_full_pipeline\n",
        encoding="utf-8",
    )

    # When: the import scanner evaluates the fixture.
    issues = forbidden_import_issues((source,), GOVERNANCE_OUTWARD_IMPORTS)

    # Then: the intended architecture violation is reported.
    assert issues == ("bad_governance.py imports engine.application.pipeline_runner",)


def test_fixture_detects_relative_governance_outward_imports(tmp_path: Path) -> None:
    # Given: governance fixtures using relative imports to escape the domain package.
    package = tmp_path / "engine" / "governance"
    package.mkdir(parents=True)
    application = package / "bad_application.py"
    infrastructure = package / "bad_infrastructure.py"
    tools = package / "bad_tools.py"
    application.write_text(
        "from ..application import governance_shadow_runner\n",
        encoding="utf-8",
    )
    infrastructure.write_text(
        "from ..infrastructure import adapters\n",
        encoding="utf-8",
    )
    tools.write_text("from ...tools import render_report\n", encoding="utf-8")

    # When: the import scanner evaluates relative imports from the fixture package.
    issues = forbidden_import_issues(
        (application, infrastructure, tools),
        GOVERNANCE_OUTWARD_IMPORTS,
    )

    # Then: relative outward imports are reported as forbidden absolute modules.
    assert issues == (
        "bad_application.py imports engine.application",
        "bad_infrastructure.py imports engine.infrastructure",
        "bad_tools.py imports tools",
    )


def test_governance_package_has_no_outward_imports() -> None:
    # Given: the Wave1 governance domain package.
    paths = python_files(ROOT / "engine" / "governance")

    # When: imports are scanned for forbidden outer layers.
    issues = forbidden_import_issues(paths, GOVERNANCE_OUTWARD_IMPORTS)

    # Then: governance remains independent from application, infrastructure, and tools.
    assert issues == ()


def test_fixture_detects_history_feedback_learning_and_label_paths(
    tmp_path: Path,
) -> None:
    # Given: a source fixture that reaches V5 runner and revealed result paths.
    source = tmp_path / "bad_labels.py"
    source.write_text(
        "import engine.v5.runner\nLABEL_PATH = 'reports/sample-hit-results.json'\n",
        encoding="utf-8",
    )

    # When: imports and path-like scalars are scanned.
    issues = governance_contamination_issues((source,))

    # Then: V5 runner and label/result path contamination are both visible.
    assert issues == (
        "bad_labels.py imports engine.v5.runner",
        "bad_labels.py contains reports/",
        "bad_labels.py contains sample-hit-results",
    )


def test_governance_package_avoids_reports_feedback_learning_v5_and_labels() -> None:
    # Given: the Wave1 governance domain package.
    paths = python_files(ROOT / "engine" / "governance")

    # When: source contamination guards scan the package.
    issues = governance_contamination_issues(paths)

    # Then: no report, feedback, learning, V5 runner, or label path leaks inward.
    assert issues == ()


def test_fixture_detects_shadow_runner_import_consumers(tmp_path: Path) -> None:
    # Given: a legacy entrypoint fixture importing the shadow runner.
    source = tmp_path / "legacy_entrypoint.py"
    source.write_text(
        "from engine.application import governance_shadow_runner\n",
        encoding="utf-8",
    )

    # When: the legacy consumer scanner runs.
    issues = shadow_runner_consumer_issues((source,))

    # Then: the shadow runner import is blocked.
    assert issues == (
        "legacy_entrypoint.py imports engine.application.governance_shadow_runner",
    )


def test_shadow_runner_is_not_consumed_by_legacy_entrypoints_or_templates() -> None:
    # Given: existing default pipelines, report surfaces, and feedback entrypoints.
    paths = legacy_shadow_consumer_paths()

    # When: they are scanned for shadow-runner imports or direct references.
    issues = shadow_runner_consumer_issues(paths)

    # Then: the new shadow path remains opt-in only.
    assert issues == ()


def test_shadow_runner_scan_covers_active_report_and_feedback_entrypoints() -> None:
    # Given: the current active report and feedback entrypoints.
    required = {
        "tools/output_linter.py",
        "tools/domain_analysis_cli.py",
        "tools/batch_review.py",
        "tools/promote_expert_weight_feedback.py",
        "tools/domain_feedback.py",
    }

    # When: shadow-runner consumer paths are discovered.
    discovered = {
        path.relative_to(ROOT).as_posix() for path in legacy_shadow_consumer_paths()
    }
    path_count = len(legacy_shadow_consumer_paths())

    # Then: every active entrypoint is covered by the isolation scan.
    assert required <= discovered
    assert path_count == len(discovered)


def test_fixture_detects_forbidden_governance_yaml_scalars(tmp_path: Path) -> None:
    # Given: a registry fixture with historical IDs, revealed labels, and host paths.
    source = tmp_path / "bad-governance.yaml"
    source.write_text(
        "case_id: C-2026-001\nprediction_label: hit\npath: F:\\cases\\x.json\n",
        encoding="utf-8",
    )

    # When: YAML scalars are parsed and scanned.
    issues = governance_yaml_issues(source)

    # Then: every forbidden scalar class is reported.
    assert issues == (
        "bad-governance.yaml contains historical case id C-2026-001",
        "bad-governance.yaml contains prediction/result label prediction_label",
        "bad-governance.yaml contains prediction/result label hit",
        "bad-governance.yaml contains absolute path F:\\cases\\x.json",
    )


def test_fixture_detects_unc_and_unix_absolute_paths(tmp_path: Path) -> None:
    # Given: a registry fixture with common absolute path forms.
    source = tmp_path / "bad-absolute-paths.yaml"
    source.write_text(
        "unc: '\\\\server\\share\\case.json'\n" "unix: /opt/project/case.json\n",
        encoding="utf-8",
    )

    # When: YAML scalars are parsed and scanned.
    issues = governance_yaml_issues(source)

    # Then: UNC and Unix absolute paths are both reported.
    assert issues == (
        "bad-absolute-paths.yaml contains absolute path \\\\server\\share\\case.json",
        "bad-absolute-paths.yaml contains absolute path /opt/project/case.json",
    )


def test_governance_registry_yaml_has_no_case_labels_results_or_paths() -> None:
    # Given: the shared Wave1 governance registry YAML.
    source = ROOT / "theory" / "multi-school-governance-v1.yaml"

    # When: parsed YAML scalars are checked.
    issues = governance_yaml_issues(source)

    # Then: the registry contains only governance configuration.
    assert issues == ()


def test_fixture_detects_school_view_fact_snapshot_writes(tmp_path: Path) -> None:
    # Given: a School View adapter fixture that tries to build a FactSnapshot.
    source = tmp_path / "bad_school_view_adapter.py"
    source.write_text(
        "from engine.governance import build_fact_snapshot\n"
        "def adapt(snapshot):\n"
        "    return build_fact_snapshot(snapshot)\n",
        encoding="utf-8",
    )

    # When: write-call scanning is applied.
    issues = fact_snapshot_write_issues((source,))

    # Then: School View FactSnapshot writes are reported.
    assert issues == ("bad_school_view_adapter.py calls build_fact_snapshot",)


def test_fixture_detects_aliased_fact_snapshot_writes(tmp_path: Path) -> None:
    # Given: a School View adapter fixture aliasing forbidden snapshot writers.
    source = tmp_path / "bad_school_view_alias_adapter.py"
    source.write_text(
        "from engine.governance import build_fact_snapshot as make_snapshot\n"
        "from engine.governance.contracts import FactSnapshot as Snapshot\n"
        "def adapt(spec):\n"
        "    make_snapshot(spec)\n"
        "    return Snapshot(spec)\n",
        encoding="utf-8",
    )

    # When: write-call scanning is applied.
    issues = fact_snapshot_write_issues((source,))

    # Then: aliased builder and constructor calls are reported.
    assert issues == (
        "bad_school_view_alias_adapter.py calls build_fact_snapshot",
        "bad_school_view_alias_adapter.py calls FactSnapshot",
    )


def test_school_view_adapter_discovery_includes_future_adapter_files(
    tmp_path: Path,
) -> None:
    # Given: a future School View adapter file in the application package.
    application = tmp_path / "engine" / "application"
    application.mkdir(parents=True)
    future = application / "governance_new_school_view_adapter.py"
    future.write_text("", encoding="utf-8")

    # When: School View adapter paths are discovered.
    paths = school_view_adapter_paths(tmp_path)

    # Then: discovery is pattern-based, not a three-file allowlist.
    assert paths == (future,)


def test_school_view_adapters_do_not_write_fact_snapshots() -> None:
    # Given: the application School View adapter surfaces.
    paths = school_view_adapter_paths()

    # When: FactSnapshot write calls are scanned.
    issues = fact_snapshot_write_issues(paths)

    # Then: only the dedicated fact builder can construct snapshots.
    assert issues == ()


def test_fixture_detects_system_time_liunian_decisions(tmp_path: Path) -> None:
    # Given: a fixture that derives liunian from the system clock.
    source = tmp_path / "bad_liunian.py"
    source.write_text(
        "from datetime import datetime\n"
        "def decide_liunian():\n"
        "    return datetime.now().year\n",
        encoding="utf-8",
    )

    # When: liunian/time source scanning runs.
    issues = system_time_liunian_issues((source,))

    # Then: the hidden clock read is reported.
    assert issues == ("bad_liunian.py reads system time while mentioning liunian",)


def test_fixture_detects_aliased_system_time_liunian_decisions(tmp_path: Path) -> None:
    # Given: fixtures deriving liunian from common clock aliases.
    datetime_alias = tmp_path / "bad_dt_alias_liunian.py"
    direct_alias = tmp_path / "bad_now_alias_liunian.py"
    datetime_alias.write_text(
        "from datetime import datetime as dt\n"
        "def decide_liunian():\n"
        "    return dt.now().year\n",
        encoding="utf-8",
    )
    direct_alias.write_text(
        "from time import time as now\n" "def decide_liunian():\n" "    return now()\n",
        encoding="utf-8",
    )

    # When: liunian/time source scanning runs.
    issues = system_time_liunian_issues((datetime_alias, direct_alias))

    # Then: aliased clock reads are reported.
    assert issues == (
        "bad_dt_alias_liunian.py reads system time while mentioning liunian",
        "bad_now_alias_liunian.py reads system time while mentioning liunian",
    )


def test_new_governance_code_does_not_read_system_time_for_liunian() -> None:
    # Given: new Wave1 governance and governance-shadow application code.
    paths = new_governance_python_paths()

    # When: system-time reads are scanned in liunian-related files.
    issues = system_time_liunian_issues(paths)

    # Then: liunian remains driven by explicit target-year facts.
    assert issues == ()


def test_legacy_yang_static_protection_remains_in_force() -> None:
    # Given: the legacy Yang static isolation guard file.
    source = (ROOT / "tests" / "yang_marriage" / "test_static_isolation.py").read_text(
        encoding="utf-8"
    )

    # When: its public-field and approved-byte guards are inspected.
    required_guards = (
        "PUBLIC_FIELDS",
        "APPROVED_BLOB_SHA256",
        "test_public_contract_fields_and_production_rule_bytes_are_unchanged",
    )

    # Then: Task12 continues to require the legacy compatibility guard.
    assert all(guard in source for guard in required_guards)

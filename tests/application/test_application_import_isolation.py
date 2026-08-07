from __future__ import annotations

import subprocess
import sys


def test_shadow_submodule_import_does_not_load_forbidden_decision_surfaces() -> None:
    # Given: a truly fresh interpreter with no application modules loaded.
    script = "\n".join(
        (
            "import sys",
            "from engine.application.governance_shadow_runner import run_governance_shadow",
            "forbidden = ('engine.application.pipeline_runner', 'engine.v5.runner', 'engine.decision.l7_report_view', 'engine.decision.l8_feedback_attribution', 'engine.decision.l9_calibration')",
            "print('\\n'.join(name for name in forbidden if name in sys.modules))",
        )
    )

    # When: only the opt-in shadow submodule is imported.
    completed = subprocess.run(
        [sys.executable, "-B", "-c", script],
        check=True,
        capture_output=True,
        text=True,
    )

    # Then: no production runner, report, feedback, or learning module was loaded.
    assert completed.stdout == "\n"


def test_application_public_exports_resolve_to_original_objects() -> None:
    # Given: the legacy package exports and their defining modules.
    script = "\n".join(
        (
            "import engine.application as package",
            "from engine.application.integration import integrate, verify_hash_chain",
            "from engine.application.pipeline_runner import run_pipeline, run_pipeline_e2e",
            "from engine.application.recompute import RecomputeHardGateError, RecomputeRequest, RecomputeResult, recompute_wenzhen_case",
            "from engine.application.timing import PipelineTiming, StepTiming",
            "expected = {'PipelineTiming': PipelineTiming, 'RecomputeHardGateError': RecomputeHardGateError, 'RecomputeRequest': RecomputeRequest, 'RecomputeResult': RecomputeResult, 'StepTiming': StepTiming, 'integrate': integrate, 'recompute_wenzhen_case': recompute_wenzhen_case, 'run_pipeline': run_pipeline, 'run_pipeline_e2e': run_pipeline_e2e, 'verify_hash_chain': verify_hash_chain}",
            "print(all(getattr(package, name) is value for name, value in expected.items()))",
            "print(','.join(package.__all__))",
        )
    )

    # When: all public names are explicitly resolved through the package.
    completed = subprocess.run(
        [sys.executable, "-B", "-c", script],
        check=True,
        capture_output=True,
        text=True,
    )

    # Then: every export retains its identity and the public list is unchanged.
    assert completed.stdout.splitlines() == [
        "True",
        "PipelineTiming,RecomputeHardGateError,RecomputeRequest,RecomputeResult,"
        "StepTiming,integrate,recompute_wenzhen_case,run_pipeline,run_pipeline_e2e,"
        "verify_hash_chain",
    ]


def test_decision_v5_public_exports_resolve_to_original_objects() -> None:
    # Given: the legacy decision package exports and their defining module.
    script = "\n".join(
        (
            "import engine.decision as package",
            "from engine.decision.v5_adapter import decision_run_from_snapshot, decision_run_from_v5",
            "print(package.decision_run_from_snapshot is decision_run_from_snapshot)",
            "print(package.decision_run_from_v5 is decision_run_from_v5)",
            "print('decision_run_from_snapshot' in package.__all__)",
            "print('decision_run_from_v5' in package.__all__)",
        )
    )

    # When: both v5 compatibility exports are resolved through the package.
    completed = subprocess.run(
        [sys.executable, "-B", "-c", script],
        check=True,
        capture_output=True,
        text=True,
    )

    # Then: the package retains both original object identities and export names.
    assert completed.stdout.splitlines() == ["True", "True", "True", "True"]


def test_decision_l7_l8_l9_public_exports_resolve_to_original_objects() -> None:
    # Given: every public L7, L8, and L9 export and its defining module.
    script = "\n".join(
        (
            "import engine.decision as package",
            "from engine.decision.l7_report_view import build_report_items",
            "from engine.decision.l8_feedback_attribution import attribute_feedback, build_feedback_attributions, build_feedback_signals",
            "from engine.decision.l9_calibration import build_calibration_actions, build_router_calibration_actions",
            "from engine.decision.orchestrator import run_decision_mvp",
            "expected = {'build_report_items': build_report_items, 'attribute_feedback': attribute_feedback, 'build_feedback_attributions': build_feedback_attributions, 'build_feedback_signals': build_feedback_signals, 'build_calibration_actions': build_calibration_actions, 'build_router_calibration_actions': build_router_calibration_actions, 'run_decision_mvp': run_decision_mvp}",
            "print(all(getattr(package, name) is value for name, value in expected.items()))",
            "print(','.join(name for name in expected if name in package.__all__))",
            "print(all(package.__dict__.get(name) is value for name, value in expected.items()))",
            "try: package.missing_export",
            "except AttributeError as error: print(f'{type(error).__name__}:{error}')",
            "package._LAZY_EXPORTS['broken_export'] = ('no.such.task14.module', 'missing')",
            "try: package.broken_export",
            "except ModuleNotFoundError as error: print(f'{type(error).__name__}:{error}:{\"broken_export\" in package.__dict__}')",
        )
    )

    # When: all seven compatibility exports are resolved through the package.
    completed = subprocess.run(
        [sys.executable, "-B", "-c", script],
        check=True,
        capture_output=True,
        text=True,
    )

    # Then: identities and public export names remain unchanged.
    assert completed.stdout.splitlines() == [
        "True",
        "build_report_items,attribute_feedback,build_feedback_attributions,"
        "build_feedback_signals,build_calibration_actions,"
        "build_router_calibration_actions,run_decision_mvp",
        "True",
        "AttributeError:module 'engine.decision' has no attribute 'missing_export'",
        "ModuleNotFoundError:No module named 'no':False",
    ]

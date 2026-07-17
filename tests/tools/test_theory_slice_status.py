from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from tools.theory_slice_status import load_executable_manifest, scan_theory_slices


def _write_manifest(path: Path, slices: str = "slices: []\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "schema_version: executable-slices/v1\n" + slices,
        encoding="utf-8",
    )


def test_metrics_keep_catalog_and_executable_counts_separate(tmp_path: Path) -> None:
    (tmp_path / "theory" / "ren").mkdir(parents=True)
    (tmp_path / "theory" / "ren" / "index.yaml").write_text(
        "rules:\n  - id: R1\n  - id: R2\n", encoding="utf-8"
    )
    _write_manifest(
        tmp_path / "theory" / "executable-slices-v1.yaml",
        "slices:\n"
        "  - slice_id: REN-CAREER-TIMING-V1\n"
        "    school_id: ren\n    task_id: career.role_change\n"
        "    target_layer: L5\n    status: staged_verified\n"
        "    artifacts: [engine/decision/ren_career_timing.py]\n",
    )

    result = scan_theory_slices(tmp_path)

    assert result["schools"]["ren"] == {
        "catalog_count": 2,
        "executable_slice_count": 1,
    }


def test_catalog_count_supports_real_repository_mapping_with_rules(tmp_path: Path) -> None:
    (tmp_path / "theory" / "ziping").mkdir(parents=True)
    (tmp_path / "theory" / "ziping" / "index.yaml").write_text(
        "schema_version: production-rules-v1\n"
        "status: active\n"
        "expert_system: ziping\n"
        "rules:\n  - id: ZP1\n  - id: ZP2\n  - id: ZP3\n",
        encoding="utf-8",
    )
    _write_manifest(tmp_path / "theory" / "executable-slices-v1.yaml")

    result = scan_theory_slices(tmp_path)

    assert result["schools"]["ziping"]["catalog_count"] == 3


def test_manifest_rejects_unknown_keys(tmp_path: Path) -> None:
    path = tmp_path / "manifest.yaml"
    _write_manifest(
        path,
        "slices:\n"
        "  - slice_id: X\n    school_id: ren\n    task_id: x\n"
        "    target_layer: L5\n    status: staged_verified\n"
        "    artifacts: []\n    extra: bad\n",
    )

    with pytest.raises(ValueError, match="unknown slice keys"):
        load_executable_manifest(path)


def test_manifest_rows_are_sorted_deterministically(tmp_path: Path) -> None:
    path = tmp_path / "manifest.yaml"
    _write_manifest(
        path,
        "slices:\n"
        "  - slice_id: Z-SLICE\n    school_id: gao\n    task_id: z\n"
        "    target_layer: L2\n    status: existing_audited\n    artifacts: []\n"
        "  - slice_id: A-SLICE\n    school_id: duan\n    task_id: a\n"
        "    target_layer: L2\n    status: production_active\n    artifacts: []\n",
    )

    rows = load_executable_manifest(path)

    assert [row["slice_id"] for row in rows] == ["A-SLICE", "Z-SLICE"]


def test_cli_emits_json_for_explicit_root(tmp_path: Path) -> None:
    _write_manifest(tmp_path / "theory" / "executable-slices-v1.yaml")

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "tools.theory_slice_status",
            "--format",
            "json",
            "--root",
            str(tmp_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(completed.stdout)
    assert payload["schema_version"] == "theory-slice-status/v1"
    assert list(payload["schools"]) == [
        "gao",
        "duan",
        "yang",
        "ren",
        "ziping",
        "tiaohou_ditiansui",
    ]


def test_real_repository_reports_one_ziping_executable_slice() -> None:
    status = scan_theory_slices(Path("."))
    assert status["schools"]["ziping"] == {
        "catalog_count": 933,
        "executable_slice_count": 1,
    }

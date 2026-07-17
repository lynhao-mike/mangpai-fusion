"""Read-only catalog and executable theory-slice metrics."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Sequence

import yaml

_REQUIRED = {"slice_id", "school_id", "task_id", "target_layer", "status", "artifacts"}
_ALLOWED_STATUS = {"existing_audited", "staged_verified", "production_active"}
_SCHOOLS = ("gao", "duan", "yang", "ren", "ziping", "tiaohou_ditiansui")


def load_executable_manifest(path: Path) -> list[dict[str, Any]]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or set(raw) != {"schema_version", "slices"}:
        raise ValueError("manifest requires exactly schema_version and slices")
    if raw["schema_version"] != "executable-slices/v1" or not isinstance(raw["slices"], list):
        raise ValueError("invalid executable-slices manifest")

    seen: set[str] = set()
    rows: list[dict[str, Any]] = []
    for item in raw["slices"]:
        if not isinstance(item, dict):
            raise ValueError("slice record must be mapping")
        unknown = set(item) - _REQUIRED
        if unknown:
            raise ValueError(f"unknown slice keys: {sorted(unknown)}")
        if set(item) != _REQUIRED:
            raise ValueError("slice record missing required keys")
        if item["slice_id"] in seen:
            raise ValueError(f"duplicate slice_id: {item['slice_id']}")
        if item["status"] not in _ALLOWED_STATUS or not isinstance(item["artifacts"], list):
            raise ValueError("invalid slice status or artifacts")
        seen.add(item["slice_id"])
        rows.append(dict(item))
    return sorted(rows, key=lambda row: row["slice_id"])


def _catalog_count(path: Path) -> int:
    """Count catalog records without interpreting or modifying lifecycle state."""
    if not path.exists():
        return 0
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if isinstance(raw, list):
        return len(raw)
    if isinstance(raw, dict):
        for key in ("rules", "entries", "items"):
            if isinstance(raw.get(key), list):
                return len(raw[key])
    return 0


def scan_theory_slices(root: Path) -> dict[str, object]:
    manifest = load_executable_manifest(root / "theory" / "executable-slices-v1.yaml")
    schools: dict[str, dict[str, int]] = {}
    for school in _SCHOOLS:
        catalog = _catalog_count(root / "theory" / school / "index.yaml")
        executable = sum(1 for row in manifest if row["school_id"] == school)
        schools[school] = {
            "catalog_count": catalog,
            "executable_slice_count": executable,
        }
    return {
        "schema_version": "theory-slice-status/v1",
        "schools": schools,
        "slices": manifest,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--format", choices=("json",), default="json")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)
    print(
        json.dumps(
            scan_theory_slices(args.root),
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

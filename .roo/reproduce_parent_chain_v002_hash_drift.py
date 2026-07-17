from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
from pathlib import Path

from engine.evaluation.prospective_artifacts import canonical_artifact_sha256
import engine.evaluation.prospective_single_case as module


spec = importlib.util.spec_from_file_location(
    "migration_test_helpers",
    Path("tests/evaluation/test_single_case_parent_chain_migration.py"),
)
assert spec is not None and spec.loader is not None
helpers = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helpers)

with tempfile.TemporaryDirectory(prefix="pcv2-hash-trace-") as name:
    root = Path(name)
    chain = helpers._v001_chain(root)
    kwargs = helpers._migration_kwargs(root, chain)
    kwargs.update(
        freeze_at="2026-07-17T05:40:00Z",
        executed_at="2026-07-17T05:40:30Z",
        reason="Approved whole parent-chain revision before first formal freeze",
        approved_by="human-approver-01",
    )
    captured: list[dict[str, str]] = []
    real_builder = module.prepare_single_case_blind_bundle

    def traced_builder(
        intake,
        question,
        tasks_path,
        rule_snapshot_path,
        target_dir,
        *,
        dry_run,
        revision=None,
        **kwargs,
    ):
        result = real_builder(
            intake,
            question,
            tasks_path,
            rule_snapshot_path,
            target_dir,
            dry_run=dry_run,
            revision=revision,
            **kwargs,
        )
        captured.append(
            {
                "target": Path(target_dir).as_posix(),
                "question_path": question["artifact_path"],
                "question_hash": question["artifact_sha256"],
                "manifest_hash": result["artifact_sha256"],
                "bundle_hash": result["bundle_sha256"],
                "future_member_hash": result["files"]["future-question.json"],
            }
        )
        return result

    module.prepare_single_case_blind_bundle = traced_builder
    try:
        plan = module.prepare_parent_chain_v002_migration(**kwargs)
        kwargs["dry_run"] = False
        published = module.prepare_parent_chain_v002_migration(**kwargs)
    finally:
        module.prepare_single_case_blind_bundle = real_builder

    artifacts = published["artifacts"]
    formal_root = Path(artifacts["blind_bundle"]["artifact_path"]).parent
    actual_manifest = json.loads(
        (formal_root / "bundle-manifest.json").read_text(encoding="utf-8")
    )
    actual_frozen = json.loads(
        Path(artifacts["frozen_run"]["artifact_path"]).read_text(encoding="utf-8")
    )

    print("REPRO_ROOT_TEMP", root)
    print("FIXED_TIMES", kwargs["freeze_at"], kwargs["executed_at"])
    for index, row in enumerate(captured, 1):
        print("BUILDER_CALL", index, json.dumps(row, ensure_ascii=False, sort_keys=True))
    print(
        "PLAN_EQ_PUBLISH_MEMORY",
        plan["artifacts"]["blind_bundle"] == artifacts["blind_bundle"],
    )
    print(
        "MEMORY_MANIFEST",
        artifacts["blind_bundle"]["artifact_sha256"],
        artifacts["blind_bundle"]["bundle_sha256"],
        artifacts["blind_bundle"]["files"]["future-question.json"],
    )
    print(
        "DISK_MANIFEST",
        actual_manifest["artifact_sha256"],
        actual_manifest["bundle_sha256"],
        actual_manifest["files"]["future-question.json"],
    )
    print(
        "DISK_FROZEN_REFS",
        actual_frozen["bundle_manifest_sha256"],
        actual_frozen["bundle_sha256"],
        actual_frozen["parents"][-1]["artifact_sha256"],
    )
    print(
        "ONLY_CHANGED_MEMBER",
        [
            key
            for key in actual_manifest["files"]
            if actual_manifest["files"][key]
            != artifacts["blind_bundle"]["files"][key]
        ],
    )
    print(
        "FORMAL_FQ_MEMBER_BYTES",
        hashlib.sha256((formal_root / "future-question.json").read_bytes()).hexdigest(),
    )
    print("FORMAL_MANIFEST_CANONICAL", canonical_artifact_sha256(actual_manifest))
    print(
        "MISMATCH_REPRODUCED",
        actual_frozen["bundle_manifest_sha256"]
        != actual_manifest["artifact_sha256"]
        and actual_frozen["bundle_sha256"] != actual_manifest["bundle_sha256"],
    )

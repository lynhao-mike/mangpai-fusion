from __future__ import annotations

import hashlib
import json
import os
from collections import Counter
from datetime import datetime
from pathlib import Path

from engine.evaluation.prospective_artifacts import canonical_artifact_sha256

plan_path = Path(os.environ["TEMP"]) / "mangpai-v003-dry-run.json"
plan = json.loads(plan_path.read_text(encoding="utf-8"))
artifacts = plan["artifacts"]
question, intake, manifest, frozen = (
    artifacts[key]
    for key in ("future_question", "intake", "blind_bundle", "frozen_run")
)
case_id = question["case_id"]
subject_hash = question["subject_id_hash"]
assert plan["status"] == "DRY_RUN"
assert question["case_id"] == intake["case_id"] == manifest["case_id"] == frozen["case_id"] == case_id
assert question["subject_id_hash"] == intake["subject_id_hash"] == manifest["subject_id_hash"] == frozen["subject_id_hash"] == subject_hash

root = Path("META/prospective-go/single-cases") / case_id
v2_question_path = root / f"{case_id}--future-question-registration--v002.json"
v2_intake_path = root / f"{case_id}--intake--v002.json"
v2_manifest_path = root / f"{case_id}--blind-bundle--v002" / "bundle-manifest.json"
v2_documents = [
    json.loads(path.read_text(encoding="utf-8"))
    for path in (v2_question_path, v2_intake_path, v2_manifest_path)
]
expected = [
    (v2_question_path.as_posix(), v2_documents[0]["artifact_sha256"]),
    (v2_intake_path.as_posix(), v2_documents[1]["artifact_sha256"]),
    (v2_manifest_path.as_posix(), v2_documents[2]["artifact_sha256"]),
]
assert [
    (question["supersedes"], question["supersedes_sha256"]),
    (intake["supersedes"], intake["supersedes_sha256"]),
    (manifest["supersedes"], manifest["supersedes_sha256"]),
] == expected
assert (frozen["supersedes"], frozen["supersedes_sha256"]) == expected[2]
assert frozen["revision_scope"] == "parent_chain"
assert frozen["superseded_chain_terminal_kind"] == "blind-bundle"
assert all(
    artifact["reason"] == "recover_v002_bundle_frozen_hash_drift_before_any_reveal"
    and artifact["approved_by"] == "human-user-approval-20260717"
    for artifact in (question, intake, manifest, frozen)
)
assert plan["freeze_at"] == question["observation_window"]["start_at"] == frozen["freeze_at"] == frozen["frozen_run"]["frozen_at"]
freeze_time = datetime.fromisoformat(frozen["freeze_at"].replace("Z", "+00:00"))
execution_time = datetime.fromisoformat(frozen["executed_at"].replace("Z", "+00:00"))
delta = (execution_time - freeze_time).total_seconds()
assert 0 <= delta <= 60
for artifact in artifacts.values():
    assert "--v003" in artifact["artifact_path"]
    assert not Path(artifact["artifact_path"]).exists()

# Reproduce the actual formal publisher semantics instead of trusting the dry-run manifest.
files = dict(manifest["files"])
files["future-question.json"] = hashlib.sha256(
    json.dumps(
        question, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
).hexdigest()
actual_manifest = {
    **manifest,
    "files": files,
    "bundle_sha256": hashlib.sha256(
        json.dumps(files, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest(),
}
actual_manifest["artifact_sha256"] = canonical_artifact_sha256(actual_manifest)
actual_frozen = {
    **frozen,
    "bundle_sha256": actual_manifest["bundle_sha256"],
    "bundle_manifest_sha256": actual_manifest["artifact_sha256"],
}
actual_frozen["parents"] = [
    *frozen["parents"][:-1],
    {
        "artifact_path": actual_manifest["artifact_path"],
        "artifact_sha256": actual_manifest["artifact_sha256"],
    },
]
actual_frozen["artifact_sha256"] = canonical_artifact_sha256(actual_frozen)
assert actual_frozen["bundle_sha256"] == actual_manifest["bundle_sha256"]
assert actual_frozen["bundle_manifest_sha256"] == actual_manifest["artifact_sha256"]
assert actual_frozen["parents"][-1] == {
    "artifact_path": actual_manifest["artifact_path"],
    "artifact_sha256": actual_manifest["artifact_sha256"],
}
assert actual_frozen["task_catalog_sha256"] == files["tasks.json"]
assert actual_frozen["rule_snapshot_sha256"] == files["rule-snapshot.json"]
assert intake["future_question"] == manifest["parents"][1] == frozen["parents"][1] == {
    "artifact_path": question["artifact_path"],
    "artifact_sha256": question["artifact_sha256"],
}
assert manifest["parents"][0] == frozen["parents"][0] == {
    "artifact_path": intake["artifact_path"],
    "artifact_sha256": intake["artifact_sha256"],
}
outputs = frozen["frozen_run"]["outputs"]
tasks = intake["records"][0]["task_ids"]
grid = {(row["school_id"], row["task_id"]) for row in outputs}
assert len(outputs) == len(grid) == 24 == 6 * len(tasks)
states = Counter(row["state"] for row in outputs)
assert set(states) <= {"claim", "abstain", "unsupported"}

print("TIME", frozen["freeze_at"], frozen["executed_at"], "delta_seconds", delta)
print("PLAN_HASHES", question["artifact_sha256"], intake["artifact_sha256"], manifest["artifact_sha256"], frozen["artifact_sha256"])
print("ACTUAL_FORMAL_SEMANTIC_HASHES", question["artifact_sha256"], intake["artifact_sha256"], actual_manifest["artifact_sha256"], actual_frozen["artifact_sha256"])
print("MEMBER_HASHES", json.dumps(files, ensure_ascii=False, sort_keys=True))
print("BUNDLE_SHA256", actual_manifest["bundle_sha256"])
print("PARENT_CHAIN", json.dumps(expected, ensure_ascii=False))
print("FROZEN_TERMINAL", frozen["supersedes"], frozen["supersedes_sha256"])
print("GRID", len(grid), dict(states))
print("COMMAND_OUTPUT_DRIFT", manifest["artifact_sha256"] != actual_manifest["artifact_sha256"], frozen["artifact_sha256"] != actual_frozen["artifact_sha256"])

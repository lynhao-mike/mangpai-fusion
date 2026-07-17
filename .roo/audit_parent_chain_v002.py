from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

from engine.evaluation.prospective_artifacts import (
    ArtifactRef,
    canonical_artifact_sha256,
    validate_parent_ref,
)
from engine.evaluation.prospective_single_case import SIX_SCHOOLS, verify_single_case_bundle

CASE_ID = "P-GO-2026-001-坤-壬戌己酉乙卯丁亥"
case_dir = Path("META/prospective-go/single-cases") / CASE_ID
question_path = case_dir / f"{CASE_ID}--future-question-registration--v002.json"
intake_path = case_dir / f"{CASE_ID}--intake--v002.json"
bundle_root = case_dir / f"{CASE_ID}--blind-bundle--v002"
manifest_path = bundle_root / "bundle-manifest.json"
frozen_path = case_dir / f"{CASE_ID}--frozen-run--v002.json"
paths = [question_path, intake_path, manifest_path, frozen_path]
documents = [json.loads(path.read_text(encoding="utf-8")) for path in paths]

for path, document in zip(paths, documents):
    assert canonical_artifact_sha256(document) == document["artifact_sha256"]
    assert validate_parent_ref(ArtifactRef(path.as_posix(), document["artifact_sha256"])) == document
    print(
        "ARTIFACT",
        path.as_posix(),
        f"artifact_sha256={document['artifact_sha256']}",
        f"bytes_sha256={hashlib.sha256(path.read_bytes()).hexdigest()}",
    )

question, intake, manifest, frozen = documents
assert verify_single_case_bundle(bundle_root)["manifest"] == manifest
for relative_path, digest in manifest["files"].items():
    actual = hashlib.sha256((bundle_root / relative_path).read_bytes()).hexdigest()
    assert actual == digest
    print("MEMBER", relative_path, digest)

bundle_input = json.dumps(
    manifest["files"], ensure_ascii=False, sort_keys=True, separators=(",", ":")
).encode("utf-8")
calculated_bundle = hashlib.sha256(bundle_input).hexdigest()
assert calculated_bundle == manifest["bundle_sha256"]
print("BUNDLE_SHA256", calculated_bundle)

assert question["case_id"] == intake["case_id"] == manifest["case_id"] == frozen["case_id"] == CASE_ID
assert (
    question["subject_id_hash"]
    == intake["subject_id_hash"]
    == manifest["subject_id_hash"]
    == frozen["subject_id_hash"]
)
assert intake["future_question"] == {
    "artifact_path": question["artifact_path"],
    "artifact_sha256": question["artifact_sha256"],
}
assert manifest["parents"] == [
    {"artifact_path": intake["artifact_path"], "artifact_sha256": intake["artifact_sha256"]},
    {"artifact_path": question["artifact_path"], "artifact_sha256": question["artifact_sha256"]},
]
for parent in frozen["parents"][:2]:
    validate_parent_ref(ArtifactRef(**parent))
for parent in frozen["parents"][2:4]:
    assert hashlib.sha256(Path(parent["artifact_path"]).read_bytes()).hexdigest() == parent["artifact_sha256"]
validate_parent_ref(ArtifactRef(**frozen["parents"][4]))

assert question["supersedes"].endswith("--future-question-registration--v001.json")
assert intake["supersedes"].endswith("--intake--v001.json")
assert manifest["supersedes"].endswith("--blind-bundle--v001/bundle-manifest.json")
assert frozen["supersedes"] == manifest["supersedes"]
assert frozen["supersedes_sha256"] == manifest["supersedes_sha256"]
assert frozen["revision_scope"] == "parent_chain"
assert frozen["superseded_chain_terminal_kind"] == "blind-bundle"
assert question["observation_window"]["start_at"] == frozen["freeze_at"] == frozen["frozen_run"]["frozen_at"]
assert frozen["freeze_at"] <= frozen["executed_at"]

outputs = frozen["frozen_run"]["outputs"]
tasks = intake["records"][0]["task_ids"]
expected_grid = {(school, task) for school in SIX_SCHOOLS for task in tasks}
actual_grid = {(row["school_id"], row["task_id"]) for row in outputs}
assert actual_grid == expected_grid
assert len(outputs) == len(actual_grid) == 24
statuses = Counter(row["status"] for row in outputs)
assert set(statuses) <= {"claim", "abstain", "unsupported"}
print("GRID", len(tasks), "tasks_x", len(SIX_SCHOOLS), "schools=", len(outputs), "statuses=", dict(statuses))
print("TASKS", json.dumps(tasks, ensure_ascii=False))
print("REVISION_SCOPE", frozen["revision_scope"])
print("TERMINAL_KIND", frozen["superseded_chain_terminal_kind"])
print("FREEZE_AT", frozen["freeze_at"])
print("EXECUTED_AT", frozen["executed_at"])
print("APPROVED_BY", frozen["approved_by"])
print("REASON", frozen["reason"])

before = json.loads(Path(".roo/v001-parent-hashes-before.json").read_text(encoding="utf-8"))
for name, byte_hash, artifact_hash in before:
    path = Path(name)
    document = json.loads(path.read_text(encoding="utf-8"))
    assert hashlib.sha256(path.read_bytes()).hexdigest() == byte_hash
    assert document["artifact_sha256"] == artifact_hash
    print("V001_UNCHANGED", name, byte_hash, artifact_hash)

staging = list(Path("META/prospective-go/single-cases").glob(".pcv2.*"))
assert not staging
print("STAGING_CLEAN", True)

from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import datetime
from pathlib import Path

from engine.evaluation.prospective_artifacts import canonical_artifact_sha256
from engine.evaluation.prospective_single_case import verify_single_case_bundle

BASE = Path("META/prospective-go/single-cases")
case_dirs = [path for path in BASE.iterdir() if path.is_dir() and path.name.startswith("P-GO-2026-001-")]
assert len(case_dirs) == 1, case_dirs
case_dir = case_dirs[0]
case_id = case_dir.name

def artifact_path(version: int, kind: str) -> Path:
    if kind == "blind-bundle":
        return case_dir / f"{case_id}--blind-bundle--v{version:03d}" / "bundle-manifest.json"
    return case_dir / f"{case_id}--{kind}--v{version:03d}.json"

kinds = ("future-question-registration", "intake", "blind-bundle", "frozen-run")
paths = {version: [artifact_path(version, kind) for kind in kinds] for version in (1, 2, 3)}
for path in paths[3]:
    assert path.exists() and path.is_file(), path

question, intake, manifest, frozen = [json.loads(path.read_text(encoding="utf-8")) for path in paths[3]]
for path, document in zip(paths[3], (question, intake, manifest, frozen)):
    assert canonical_artifact_sha256(document) == document["artifact_sha256"]

verified = verify_single_case_bundle(paths[3][2].parent)
assert verified["manifest"] == manifest
for relative, digest in manifest["files"].items():
    assert hashlib.sha256((paths[3][2].parent / relative).read_bytes()).hexdigest() == digest
bundle_sha = hashlib.sha256(json.dumps(manifest["files"], ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
assert bundle_sha == manifest["bundle_sha256"]
assert frozen["bundle_sha256"] == bundle_sha
assert frozen["bundle_manifest_sha256"] == manifest["artifact_sha256"]
assert frozen["parents"][-1] == {"artifact_path": manifest["artifact_path"], "artifact_sha256": manifest["artifact_sha256"]}
assert frozen["task_catalog_sha256"] == manifest["files"]["tasks.json"]
assert frozen["rule_snapshot_sha256"] == manifest["files"]["rule-snapshot.json"]

v2 = [json.loads(path.read_text(encoding="utf-8")) for path in paths[2]]
assert [question["supersedes"], intake["supersedes"], manifest["supersedes"], frozen["supersedes"]] == [
    paths[2][0].as_posix(), paths[2][1].as_posix(), paths[2][2].as_posix(), paths[2][2].as_posix(),
]
assert [question["supersedes_sha256"], intake["supersedes_sha256"], manifest["supersedes_sha256"], frozen["supersedes_sha256"]] == [
    v2[0]["artifact_sha256"], v2[1]["artifact_sha256"], v2[2]["artifact_sha256"], v2[2]["artifact_sha256"],
]
assert frozen["revision_scope"] == "parent_chain"
assert frozen["superseded_chain_terminal_kind"] == "blind-bundle"
assert all(document["approved_by"] == "human-user-approval-20260717" and document["reason"] == "recover_v002_bundle_frozen_hash_drift_before_any_reveal" for document in (question, intake, manifest, frozen))
assert question["case_id"] == intake["case_id"] == manifest["case_id"] == frozen["case_id"] == case_id
assert question["subject_id_hash"] == intake["subject_id_hash"] == manifest["subject_id_hash"] == frozen["subject_id_hash"]
assert question["observation_window"]["start_at"] == frozen["freeze_at"] == frozen["frozen_run"]["frozen_at"]
freeze = datetime.fromisoformat(frozen["freeze_at"].replace("Z", "+00:00"))
executed = datetime.fromisoformat(frozen["executed_at"].replace("Z", "+00:00"))
delta = (executed - freeze).total_seconds()
assert 0 <= delta <= 60
outputs = frozen["frozen_run"]["outputs"]
grid = {(row["school_id"], row["task_id"]) for row in outputs}
assert len(outputs) == len(grid) == 24
states = Counter(row["state"] for row in outputs)
assert set(states) <= {"claim", "abstain", "unsupported"}

v1_record = json.loads(Path(".roo/v001-parent-hashes-before.json").read_text(encoding="utf-8"))
for name, byte_hash, artifact_hash in v1_record:
    path = Path(name)
    assert hashlib.sha256(path.read_bytes()).hexdigest() == byte_hash
    assert json.loads(path.read_text(encoding="utf-8"))["artifact_sha256"] == artifact_hash
published_v2 = json.loads(Path(".roo/parent-chain-v002-published.json").read_text(encoding="utf-8"))["artifacts"]
for path, key in zip(paths[2], ("future_question", "intake", "blind_bundle", "frozen_run")):
    current = json.loads(path.read_text(encoding="utf-8"))
    if key == "blind_bundle":
        assert current["artifact_sha256"] == "df1cb4abed54a49c00925706b5dfbcb60389f001ad9aa955984c921ddbfd8f98"
    else:
        assert current["artifact_sha256"] == published_v2[key]["artifact_sha256"]
forbidden = ("witness", "verification", "feedback", "retrospective", "observation", "report", "label", "reveal")
assert not any(any(word in path.name.lower() for word in forbidden) for path in case_dir.iterdir())
assert not list(BASE.glob(".pcv3.*"))

print("CASE", case_id)
print("FORMAL_HASHES", question["artifact_sha256"], intake["artifact_sha256"], manifest["artifact_sha256"], frozen["artifact_sha256"])
print("MEMBER_HASHES", json.dumps(manifest["files"], ensure_ascii=False, sort_keys=True))
print("BUNDLE_SHA256", bundle_sha)
print("TIME", frozen["freeze_at"], frozen["executed_at"], "delta_seconds", delta)
print("GRID", len(grid), dict(states))
print("SUPERSEDES_V002", True)
print("V001_V002_UNCHANGED", True)
print("STAGING_CLEAN", True)
print("DOWNSTREAM_ABSENT", True)

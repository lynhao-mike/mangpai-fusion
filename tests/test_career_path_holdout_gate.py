from __future__ import annotations

import hashlib
import json
from pathlib import Path

from tools.career_path_holdout_gate import check_holdout_admission


def _write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def _fixture(
    tmp_path: Path,
    labels: list[str],
    *,
    overlap: bool = False,
    labels_revealed: bool = False,
) -> tuple[Path, Path, Path, Path]:
    registry_path = tmp_path / "registry.json"
    preregistration_path = tmp_path / "preregistration.json"
    labels_path = tmp_path / "labels.jsonl"
    manifest_path = tmp_path / "manifest.json"
    development_id = "DEV-001"
    _write_json(
        registry_path,
        {
            "development_datasets": [
                {
                    "classification": "development_replay_only",
                    "promotion_eligible": False,
                    "holdout_eligible": False,
                    "case_ids": [development_id],
                }
            ]
        },
    )
    _write_json(
        preregistration_path,
        {
            "registered_at": "2026-07-31T00:00:00Z",
            "status": "holdout_frozen_awaiting_predictions",
            "holdout_ready": True,
            "labels_revealed": labels_revealed,
            "minimum_strict_binary_cases": 30,
            "minimum_cases_per_class": 10,
            "models": [{"model_id": "a"}, {"model_id": "b"}, {"model_id": "c"}],
            "metrics": ["balanced_accuracy"],
            "promotion_thresholds": {"min_balanced_accuracy": 0.6},
            "freeze_policy": {
                "one_shot_freeze": True,
                "one_score_only": True,
                "post_label_tuning_permitted": False,
            },
        },
    )
    rows = []
    case_ids = []
    for index, label in enumerate(labels):
        case_id = development_id if overlap and index == 0 else f"H-{index:03d}"
        case_ids.append(case_id)
        rows.append(
            {
                "case_id": case_id,
                "label": label,
                "review_status": "double_review_agreed",
                "reviewers": ["human-reviewer-a", "human-reviewer-b"],
                "reviewer_labels": [label, label],
            }
        )
    _write_jsonl(labels_path, rows)
    _write_json(
        manifest_path,
        {
            "frozen_at": "2026-07-31T01:00:00Z",
            "case_ids": case_ids,
            "case_count": len(case_ids),
            "labels_sha256": hashlib.sha256(labels_path.read_bytes()).hexdigest(),
            "labels_revealed": False,
            "one_shot_freeze": True,
        },
    )
    return manifest_path, labels_path, registry_path, preregistration_path


def _check(paths: tuple[Path, Path, Path, Path]) -> dict:
    return check_holdout_admission(*paths)


def test_labels_crlf_checkout_is_not_a_hash_mismatch(tmp_path: Path) -> None:
    """标签文件被 Windows 检出成 CRLF 时，labels_hash_matches_manifest 必须仍为 True。

    manifest 里记的是 LF 下的 hash；工作区行尾翻转到 CRLF 时内容完全一致，
    不得判为标签被改（KB-001）。否则每次 Windows 检出门禁都假失败。
    """
    paths = _fixture(tmp_path, ["employment"] * 15 + ["entrepreneurship"] * 15)
    manifest_path, labels_path, _, _ = paths
    # 先把 labels 固定成 LF，再让 manifest 记录 LF hash（模拟 LF 环境下冻结）
    lf_bytes = labels_path.read_bytes().replace(b"\r\n", b"\n")
    labels_path.write_bytes(lf_bytes)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["labels_sha256"] = hashlib.sha256(lf_bytes).hexdigest()
    _write_json(manifest_path, manifest)
    recorded_lf = manifest["labels_sha256"]
    assert recorded_lf == hashlib.sha256(labels_path.read_bytes()).hexdigest()
    # 翻成 CRLF 后必须仍放行
    labels_path.write_bytes(lf_bytes.replace(b"\n", b"\r\n"))
    assert b"\r\n" in labels_path.read_bytes()

    result = _check(paths)

    assert result["checks"]["labels_hash_matches_manifest"] is True
    assert result["ready"] is True
    # 行尾一致时不写诊断噪声
    assert result["diagnostics"].get("labels_digest", {}).get("digest_verdict") in (
        None, "match", "match_eol_normalized"
    )


def test_labels_real_tampering_still_rejected_with_diagnostics(tmp_path: Path) -> None:
    """真篡改必须继续拦截，且诊断能区分于行尾差异。"""
    paths = _fixture(tmp_path, ["employment"] * 15 + ["entrepreneurship"] * 15)
    manifest_path, labels_path, _, _ = paths
    labels_path.write_text(labels_path.read_text(encoding="utf-8") + "{}\n", encoding="utf-8")

    result = _check(paths)

    assert result["checks"]["labels_hash_matches_manifest"] is False
    assert "labels_hash_matches_manifest" in result["failures"]
    diag = result["diagnostics"]["labels_digest"]
    assert diag["digest_verdict"] == "mismatch"
    # 三种归一化都试过仍不匹配 → 确认真漂移
    assert diag["recorded_sha256"] != diag["actual_sha256"]
    assert diag["recorded_sha256"] != diag["actual_sha256_lf"]
    assert diag["recorded_sha256"] != diag["actual_sha256_crlf"]


def test_current_repository_is_honestly_not_ready() -> None:
    result = check_holdout_admission(None, None)

    assert result["status"] == "not_ready"
    assert result["ready"] is False
    assert result["failures"] == ["unseen_holdout_not_registered"]


def test_development_overlap_is_rejected(tmp_path: Path) -> None:
    paths = _fixture(
        tmp_path,
        ["employment"] * 15 + ["entrepreneurship"] * 15,
        overlap=True,
    )

    result = _check(paths)

    assert result["status"] == "rejected"
    assert result["checks"]["development_set_disjoint"] is False
    assert result["metrics"]["development_overlap_count"] == 1


def test_fewer_than_thirty_strict_cases_is_not_ready(tmp_path: Path) -> None:
    paths = _fixture(tmp_path, ["employment"] * 14 + ["entrepreneurship"] * 15)

    result = _check(paths)

    assert result["status"] == "not_ready"
    assert result["checks"]["minimum_strict_binary_cases"] is False


def test_too_few_cases_in_one_class_is_not_ready(tmp_path: Path) -> None:
    paths = _fixture(tmp_path, ["employment"] * 21 + ["entrepreneurship"] * 9)

    result = _check(paths)

    assert result["status"] == "not_ready"
    assert result["checks"]["minimum_cases_per_class"] is False


def test_labels_revealed_before_freeze_is_rejected(tmp_path: Path) -> None:
    paths = _fixture(
        tmp_path,
        ["employment"] * 15 + ["entrepreneurship"] * 15,
        labels_revealed=True,
    )

    result = _check(paths)

    assert result["status"] == "rejected"
    assert result["checks"]["labels_not_revealed"] is False


def test_valid_unseen_double_reviewed_holdout_is_ready(tmp_path: Path) -> None:
    paths = _fixture(tmp_path, ["employment"] * 15 + ["entrepreneurship"] * 15)

    result = _check(paths)

    assert result["status"] == "ready"
    assert result["ready"] is True
    assert result["failures"] == []
    assert all(result["checks"].values())


def test_mixed_and_unknown_are_retained_but_excluded_from_strict_denominator(tmp_path: Path) -> None:
    paths = _fixture(
        tmp_path,
        ["employment"] * 15 + ["entrepreneurship"] * 15 + ["mixed", "unknown"],
    )

    result = _check(paths)

    assert result["status"] == "ready"
    assert result["metrics"]["retained_cases"] == 32
    assert result["metrics"]["strict_binary_cases"] == 30
    assert result["metrics"]["nonbinary_retained_cases"] == 2


def test_agent_reviewer_is_rejected(tmp_path: Path) -> None:
    paths = _fixture(tmp_path, ["employment"] * 15 + ["entrepreneurship"] * 15)
    manifest_path, labels_path, registry_path, preregistration_path = paths
    rows = [json.loads(line) for line in labels_path.read_text(encoding="utf-8").splitlines()]
    rows[0]["reviewers"][0] = "agent-roo"
    _write_jsonl(labels_path, rows)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["labels_sha256"] = hashlib.sha256(labels_path.read_bytes()).hexdigest()
    _write_json(manifest_path, manifest)

    result = check_holdout_admission(manifest_path, labels_path, registry_path, preregistration_path)

    assert result["status"] == "rejected"
    assert result["checks"]["labels_double_reviewed_or_adjudicated"] is False

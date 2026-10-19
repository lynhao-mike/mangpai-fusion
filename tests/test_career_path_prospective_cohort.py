from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from tools.career_path_prospective_cohort import (
    build_candidate_manifest,
    finalize_cohort,
    finalize_label,
    intake_candidate,
    register_finalized_holdout,
    submit_label_review,
    validate_temporal_observation,
)


def _registry() -> dict[str, Any]:
    return {
        "schema_version": "career-path-dataset-registry/v1",
        "development_datasets": [
            {
                "dataset_id": "old-40",
                "classification": "development_replay_only",
                "promotion_eligible": False,
                "holdout_eligible": False,
                "case_ids": ["P-2026-001"],
                "identities": ["乾|甲子|乙丑|丙寅|丁卯"],
            }
        ],
        "unseen_holdout": {
            "dataset_id": None,
            "status": "not_ready",
            "case_count": 0,
            "manifest_path": None,
            "labels_path": None,
            "promotion_eligible": False,
        },
    }


def _intake(case_id: str = "U-2026-001", *, sex: str = "坤") -> dict[str, Any]:
    return {
        "case_id": case_id,
        "pillars": {
            "year": "甲子",
            "month": "乙丑",
            "day": "丙寅",
            "hour": "丁卯",
        },
        "sex": sex,
        "chart_source": "human-verified-wenzhen",
        "as_of_date": "2026-07-01",
        "dayun_intervals": [
            {"start": "2020-01-01", "end": "2029-12-31", "pillar": "戊辰"}
        ],
    }


def _review(case_id: str, reviewer: str, label: str) -> dict[str, Any]:
    return {
        "schema_version": "career-path-label-review/v1",
        "case_id": case_id,
        "reviewer_id": reviewer,
        "label": label,
        "signed_at": "2026-08-01T00:00:00Z",
    }


def _candidate(tmp_path: Path, case_id: str = "U-2026-001", *, sex: str = "坤") -> Path:
    source = tmp_path / f"{case_id}.json"
    source.write_text(json.dumps(_intake(case_id, sex=sex), ensure_ascii=False), encoding="utf-8")
    target = tmp_path / f"{case_id}.intake.json"
    intake_candidate(source, target, registry=_registry(), write=True, ingested_at="2026-07-31T12:00:00Z")
    return target


@pytest.mark.parametrize(
    "field",
    [
        "occupation",
        "feedback",
        "known_facts",
        "labels",
        "report",
        "model_prediction",
        "reality_status",
    ],
)
def test_intake_rejects_leakage_fields(tmp_path: Path, field: str) -> None:
    payload = _intake()
    payload[field] = "forbidden"
    source = tmp_path / "source.json"
    source.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    with pytest.raises(ValueError, match="leakage|field"):
        intake_candidate(source, tmp_path / "out.json", registry=_registry())


def test_intake_is_default_dry_run_create_only_and_rejects_development_overlap(tmp_path: Path) -> None:
    source = tmp_path / "source.json"
    source.write_text(json.dumps(_intake(), ensure_ascii=False), encoding="utf-8")
    target = tmp_path / "out.json"

    result = intake_candidate(source, target, registry=_registry(), ingested_at="2026-07-31T12:00:00Z")
    assert result["source_sha256"] == hashlib.sha256(source.read_bytes()).hexdigest()
    assert result["production_switch_permitted"] is False
    assert not target.exists()

    intake_candidate(source, target, registry=_registry(), write=True, ingested_at="2026-07-31T12:00:00Z")
    with pytest.raises(ValueError, match="must not exist"):
        intake_candidate(source, target, registry=_registry(), write=True, ingested_at="2026-07-31T12:00:00Z")

    old = _intake("P-2026-001")
    old["pillars"]["year"] = "庚午"
    source.write_text(json.dumps(old, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(ValueError, match="development"):
        intake_candidate(source, tmp_path / "old.json", registry=_registry())


def test_identity_fingerprint_blocks_changed_id_reentry(tmp_path: Path) -> None:
    first = _candidate(tmp_path, "U-2026-001")
    second_source = tmp_path / "changed-id.json"
    second_source.write_text(json.dumps(_intake("U-2026-999"), ensure_ascii=False), encoding="utf-8")
    second = tmp_path / "second.json"
    intake_candidate(second_source, second, registry=_registry(), write=True, ingested_at="2026-07-31T12:01:00Z")

    with pytest.raises(ValueError, match="identity"):
        build_candidate_manifest([first, second], cohort_id="cohort-1", registry=_registry())


def test_candidate_manifest_detects_source_hash_tampering_and_preserves_order(tmp_path: Path) -> None:
    first = _candidate(tmp_path, "U-2026-001", sex="坤")
    second_payload = _intake("U-2026-002", sex="乾")
    second_payload["pillars"]["hour"] = "戊辰"
    source = tmp_path / "U-2026-002.json"
    source.write_text(json.dumps(second_payload, ensure_ascii=False), encoding="utf-8")
    second = tmp_path / "U-2026-002.intake.json"
    intake_candidate(source, second, registry=_registry(), write=True, ingested_at="2026-07-31T12:02:00Z")

    manifest = build_candidate_manifest([second, first], cohort_id="cohort-1", registry=_registry())
    assert manifest["case_ids"] == ["U-2026-001", "U-2026-002"]
    assert manifest["status"] == "collecting"
    assert manifest["ready"] is False

    bound_source = Path(json.loads(first.read_text(encoding="utf-8"))["source_path"])
    bound_source.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="hash"):
        build_candidate_manifest([first], cohort_id="cohort-1", registry=_registry())


def test_bound_source_survives_windows_crlf_checkout(tmp_path: Path) -> None:
    """绑定源文件被 Windows 检出成 CRLF 时不得判为篡改（KB-001）。

    记录侧存的是 LF 下的 hash；工作区行尾翻转到 CRLF 时内容完全一致，
    必须放行。否则每次 Windows 检出都会让 cohort 校验失败。
    """
    payload = _intake("U-2026-001", sex="坤")
    source = tmp_path / "U-2026-001.json"
    # 多行 LF 形式，便于验证行尾翻转（单行 JSON 无换行则无法测）
    source.write_bytes(
        (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    )
    first = tmp_path / "U-2026-001.intake.json"
    intake_candidate(source, first, registry=_registry(), write=True, ingested_at="2026-07-31T12:00:00Z")

    lf_bytes = source.read_bytes()
    assert b"\r\n" not in lf_bytes, "fixture 必须先归一化为 LF"
    recorded_lf = hashlib.sha256(lf_bytes).hexdigest()
    assert json.loads(first.read_text(encoding="utf-8"))["source_sha256"] == recorded_lf, (
        "记录侧不是 LF hash；本测试无法验证 match_eol_normalized 分支"
    )
    # 翻成 CRLF，模拟 Windows 检出
    source.write_bytes(lf_bytes.replace(b"\n", b"\r\n"))
    assert b"\r\n" in source.read_bytes()

    manifest = build_candidate_manifest([first], cohort_id="cohort-1", registry=_registry())
    assert manifest["case_ids"] == ["U-2026-001"]


def test_bound_source_crlf_recorded_also_survives_lf_checkout(tmp_path: Path) -> None:
    """反向：记录侧存 CRLF hash、工作区是 LF，同样必须放行。

    行尾差异有两个方向，只归一化一个方向会漏（KB-001 教训 4）。
    """
    payload = _intake("U-2026-003", sex="坤")
    source = tmp_path / "U-2026-003.json"
    source.write_bytes(
        (json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8").replace(b"\n", b"\r\n")
    )
    record_path = tmp_path / "U-2026-003.intake.json"
    intake_candidate(source, record_path, registry=_registry(), write=True, ingested_at="2026-07-31T12:03:00Z")
    # 记录侧此时是 CRLF 的 hash；把工作区转回 LF 模拟另一平台检出
    source.write_bytes(source.read_bytes().replace(b"\r\n", b"\n"))

    manifest = build_candidate_manifest([record_path], cohort_id="cohort-1", registry=_registry())
    assert manifest["case_ids"] == ["U-2026-003"]


def test_review_requires_human_distinct_reviewers_and_adjudication() -> None:
    first = submit_label_review(_review("U-1", "human-a", "employment"))
    second = submit_label_review(_review("U-1", "human-b", "entrepreneurship"))

    with pytest.raises(ValueError, match="human"):
        submit_label_review(_review("U-1", "agent-roo", "employment"))
    with pytest.raises(ValueError, match="different"):
        finalize_label(first, _review("U-1", "human-a", "employment"))

    unresolved = finalize_label(first, second)
    assert unresolved["status"] == "not_ready"
    assert unresolved["reason"] == "adjudication_required"

    with pytest.raises(ValueError, match="third independent human"):
        finalize_label(
            first,
            second,
            {
                "schema_version": "career-path-label-adjudication/v1",
                "case_id": "U-1",
                "adjudicator_id": "human-a",
                "label": "employment",
                "rationale": "人工核验资料后的裁决。",
                "signed_at": "2026-08-02T00:00:00Z",
            },
        )


def test_mixed_and_unknown_are_retained_but_excluded_from_binary_denominator(tmp_path: Path) -> None:
    finals = []
    for index, label in enumerate(["employment", "entrepreneurship", "mixed", "unknown"]):
        case_id = f"U-{index}"
        finals.append(finalize_label(_review(case_id, f"human-a{index}", label), _review(case_id, f"human-b{index}", label)))

    result = finalize_cohort(finals, cohort_id="cohort-1", output_dir=tmp_path / "final")

    assert result["status"] == "not_ready"
    assert result["metrics"]["retained_cases"] == 4
    assert result["metrics"]["strict_binary_cases"] == 2
    assert result["production_switch_permitted"] is False
    assert not (tmp_path / "final").exists()


def test_temporal_validation_rejects_overlapping_dayun_and_unverified_events() -> None:
    observation = {
        "case_id": "U-1",
        "as_of_date": "2026-07-01",
        "reality_state": "employed",
        "dayun_intervals": [
            {"start": "2020-01-01", "end": "2025-01-01", "pillar": "甲子"},
            {"start": "2025-01-01", "end": "2030-01-01", "pillar": "乙丑"},
        ],
        "career_transition_events": [],
    }
    with pytest.raises(ValueError, match="overlap"):
        validate_temporal_observation(observation)

    observation["dayun_intervals"][1]["start"] = "2025-01-02"
    observation["career_transition_events"] = [
        {"date": "2025-06-01", "state": "entrepreneurial", "verified_by": "agent-roo"}
    ]
    with pytest.raises(ValueError, match="human"):
        validate_temporal_observation(observation)


def test_missing_temporal_data_is_not_ready_without_invalidating_static_label() -> None:
    final = finalize_label(_review("U-1", "human-a", "employment"), _review("U-1", "human-b", "employment"))
    assert final["status"] == "ready"
    assert final["temporal_status"] == "not_ready_for_temporal_metrics"


def test_registry_update_is_controlled_and_cannot_admit_not_ready(tmp_path: Path) -> None:
    registry_path = tmp_path / "registry.json"
    registry_path.write_text(json.dumps(_registry(), ensure_ascii=False, indent=2), encoding="utf-8")
    result = {"status": "not_ready", "metrics": {"strict_binary_cases": 0}}

    with pytest.raises(ValueError, match="ready"):
        register_finalized_holdout(
            registry_path,
            finalized=result,
            manifest_path=tmp_path / "manifest.json",
            labels_path=tmp_path / "labels.jsonl",
            reviewed_by="human-controller",
            write=True,
        )

    unchanged = json.loads(registry_path.read_text(encoding="utf-8"))
    assert unchanged["unseen_holdout"]["status"] == "not_ready"
    assert unchanged["unseen_holdout"]["case_count"] == 0
    assert unchanged["unseen_holdout"]["promotion_eligible"] is False

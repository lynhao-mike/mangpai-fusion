from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest
import yaml

from engine.application.weight_profile_service import WeightProfileService
from tools import promote_expert_weight_feedback as promotion


def _profile_payload() -> dict:
    return {
        "schema_version": "expert-weight-profile/v1",
        "status": "active",
        "profile_id": "expert-domain-prior-test",
        "profile_version": "test-v1",
        "updated_at": "2026-07-27T00:00:00Z",
        "source": "engine/expert-weights.yaml",
        "weights": {
            "财运": {
                "blind": 0.30,
                "ziping": 0.45,
                "tiaohou_ditiansui": 0.25,
            }
        },
        "feedback_overlay": {
            "version": "no-feedback-overlay",
            "source_path": "inline:none",
            "min_effective_sample_for_adjustment": 11,
            "low_sample_max_delta": 0.02,
            "mature_sample_max_delta": 0.15,
            "entries": [],
        },
    }


def _write_profile(tmp_path: Path) -> Path:
    path = tmp_path / "engine" / "expert-weights.yaml"
    path.parent.mkdir(parents=True)
    path.write_text(
        yaml.safe_dump(_profile_payload(), allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    return path


def _stub_feedback(monkeypatch: pytest.MonkeyPatch) -> None:
    stats = {
        "items": [
            {
                "domain": "财运",
                "expert_system": "ziping",
                "hits": 3,
                "misses": 0,
                "n_eff": 3.0,
                "beta_mean": 0.8,
                "wilson_lower": 0.438503,
                "sample_warning": True,
            }
        ]
    }
    proposal = {
        "schema_version": "expert-domain-weight-proposal/v0.2",
        "min_n_eff": 1,
        "proposal_count": 1,
        "proposals": [
            {
                "domain": "财运",
                "expert_system": "ziping",
                "n_eff": 3.0,
                "beta_mean": 0.8,
                "wilson_lower": 0.438503,
                "proposed_feedback_multiplier": 1.1,
                "requires_human_review": True,
                "source": "expert_domain_feedback_stats",
            }
        ],
        "diagnostics": [],
    }
    monkeypatch.setattr(promotion, "get_expert_domain_stats", lambda: deepcopy(stats))
    monkeypatch.setattr(
        promotion,
        "compute_weight_update_proposal",
        lambda min_n_eff=10: deepcopy(proposal),
    )


def test_promotion_defaults_to_dry_run_and_shows_diff_without_writing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    profile_path = _write_profile(tmp_path)
    before = profile_path.read_bytes()
    _stub_feedback(monkeypatch)

    result = promotion.promote_expert_weight_feedback(
        profile_path=profile_path,
        min_n_eff=1,
    )

    assert result["applied"] is False
    assert result["dry_run"] is True
    assert result["current_version"] == "no-feedback-overlay"
    assert result["next_version"] == "feedback-overlay-v1"
    assert "feedback_overlay" in result["preview_diff"]
    assert "human_confirmed" in result["preview_diff"]
    assert profile_path.read_bytes() == before


def test_promotion_requires_explicit_human_reviewer_for_write(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    profile_path = _write_profile(tmp_path)
    before = profile_path.read_bytes()
    _stub_feedback(monkeypatch)

    with pytest.raises(ValueError, match="reviewed_by"):
        promotion.promote_expert_weight_feedback(
            profile_path=profile_path,
            min_n_eff=1,
            dry_run=False,
        )

    assert profile_path.read_bytes() == before


def test_promotion_writes_human_confirmed_overlay_and_preserves_prior_weights(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    profile_path = _write_profile(tmp_path)
    prior_weights = deepcopy(_profile_payload()["weights"])
    _stub_feedback(monkeypatch)

    result = promotion.promote_expert_weight_feedback(
        profile_path=profile_path,
        min_n_eff=1,
        dry_run=False,
        reviewed_by="浩哥",
    )

    payload = yaml.safe_load(profile_path.read_text(encoding="utf-8"))
    overlay = payload["feedback_overlay"]
    assert result["applied"] is True
    assert payload["weights"] == prior_weights
    assert overlay["version"] == "feedback-overlay-v1"
    assert overlay["status"] == "human_confirmed"
    assert overlay["reviewed_by"] == "浩哥"
    assert overlay["requires_human_review"] is False
    assert overlay["entries"] == [
        {
            "expert_system": "ziping",
            "domain": "财运",
            "rule_group": "parallel-domain",
            "n_eff": 3.0,
            "success_count": 3.0,
            "failure_count": 0.0,
            "beta_alpha": 4.0,
            "beta_beta": 1.0,
            "beta_mean": 0.8,
            "wilson_lower_bound": 0.438503,
        }
    ]


def test_promotion_increments_version_and_rejects_reuse(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    profile_path = _write_profile(tmp_path)
    _stub_feedback(monkeypatch)

    first = promotion.promote_expert_weight_feedback(
        profile_path=profile_path,
        min_n_eff=1,
        dry_run=False,
        reviewed_by="Reviewer A",
    )
    second = promotion.promote_expert_weight_feedback(
        profile_path=profile_path,
        min_n_eff=1,
        dry_run=False,
        reviewed_by="Reviewer B",
    )

    assert first["next_version"] == "feedback-overlay-v1"
    assert second["current_version"] == "feedback-overlay-v1"
    assert second["next_version"] == "feedback-overlay-v2"

    before_reuse = profile_path.read_bytes()
    with pytest.raises(ValueError, match="严格递增"):
        promotion.promote_expert_weight_feedback(
            profile_path=profile_path,
            min_n_eff=1,
            dry_run=False,
            reviewed_by="Reviewer C",
            version="feedback-overlay-v2",
        )
    assert profile_path.read_bytes() == before_reuse


def test_feedback_ingest_to_runtime_weight_end_to_end(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import tools.feedback_ingest as feedback_ingest
    from tools.feedback_loop import IterationDiff

    workspace = tmp_path / "workspace"
    profile_path = workspace / "engine" / "expert-weights.yaml"
    profile_path.parent.mkdir(parents=True)
    canonical_payload = yaml.safe_load(
        Path("engine/expert-weights.yaml").read_text(encoding="utf-8")
    )
    profile_path.write_text(
        yaml.safe_dump(canonical_payload, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )

    baseline = WeightProfileService(workspace_root=workspace).build_weight_profile("财运")
    assert baseline.feedback_modulations == {
        "blind": 1.0,
        "ziping": 1.0,
        "tiaohou_ditiansui": 1.0,
    }
    assert baseline.domain_weights["ziping"] == pytest.approx(0.45)

    case_dir = workspace / "cases" / "C-TEST-PARALLEL-E2E"
    case_dir.mkdir(parents=True)
    statement_id = "S-999-pde2e01"
    (case_dir / "feedback.md").write_text(
        f"反馈：[{statement_id}] [y]\n",
        encoding="utf-8",
    )
    (case_dir / "statement_records.json").write_text(
        json.dumps(
            {
                "records": [
                    {
                        "statement_id": statement_id,
                        "rule_id": "M1-D-001",
                        "family_id": "FAM-M1",
                        "school": "段",
                        "canon": "duan",
                        "rule_type": "runtime_rule",
                        "domain": "财运",
                    }
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (case_dir / "statement_index.json").write_text(
        json.dumps(
            {
                "case_id": case_dir.name,
                "statements": [
                    {
                        "statement_id": statement_id,
                        "section": "parallel_domain_adjudication",
                        "domain": "财运",
                        "summary": "财运结构可用",
                        "reading_ids": ["RD-E2E-财运-ZIPING-001"],
                        "adjudication_id": "ADJ-E2E-财运",
                        "expert_systems": ["ziping"],
                        "supporting_experts": ["ziping"],
                        "dissenting_experts": [],
                        "abstained_experts": ["blind", "tiaohou_ditiansui"],
                        "consensus_layer": "单专家判断",
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    expert_log = workspace / "engine" / "logs" / "expert_domain_feedback.jsonl"
    monkeypatch.setattr(feedback_ingest, "find_case_dir", lambda _case_id: case_dir)
    monkeypatch.setattr(feedback_ingest, "EXPERT_DOMAIN_FEEDBACK_LOG", expert_log)
    monkeypatch.setattr(
        feedback_ingest,
        "ADJUDICATION_ACCURACY_LOG",
        workspace / "engine" / "logs" / "adjudication_accuracy.jsonl",
    )
    monkeypatch.setattr(
        feedback_ingest,
        "WEIGHT_CHANGES_LOG",
        workspace / "engine" / "logs" / "weight-changes.jsonl",
    )
    monkeypatch.setattr(
        feedback_ingest,
        "run_learning_update",
        lambda *_args, **_kwargs: {
            "updated_count": 0,
            "observable_confidence_changes": [],
        },
    )
    monkeypatch.setattr(
        feedback_ingest,
        "_apply_rule_verdicts",
        lambda case_id, *_args, **_kwargs: IterationDiff(
            case_id=case_id,
            ts="2026-07-27T00:00:00",
            case_count=1,
        ),
    )
    monkeypatch.setattr(feedback_ingest, "append_iteration_log", lambda _diff: None)
    monkeypatch.setattr(feedback_ingest, "write_snapshot", lambda _diff: None)
    monkeypatch.setattr(feedback_ingest, "_bump_state", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        feedback_ingest,
        "_write_ingest_timing",
        lambda *_args, **_kwargs: None,
    )

    feedback_ingest.ingest(case_dir.name)

    log_rows = [
        json.loads(line)
        for line in expert_log.read_text(encoding="utf-8").splitlines()
    ]
    assert len(log_rows) == 1
    assert log_rows[0]["expert_system"] == "ziping"
    stats = feedback_ingest.get_expert_domain_stats()
    assert stats["items"][0]["n_eff"] == 1.0
    proposal = feedback_ingest.compute_weight_update_proposal(min_n_eff=1)
    assert proposal["proposal_count"] == 1
    assert proposal["proposals"][0]["n_eff"] == 1.0

    before_dry_run = profile_path.read_bytes()
    preview = promotion.promote_expert_weight_feedback(
        profile_path=profile_path,
        min_n_eff=1,
    )
    assert preview["applied"] is False
    assert "feedback-overlay-v1" in preview["preview_diff"]
    assert profile_path.read_bytes() == before_dry_run

    promotion.promote_expert_weight_feedback(
        profile_path=profile_path,
        min_n_eff=1,
        dry_run=False,
        reviewed_by="E2E Reviewer",
    )
    adjusted = WeightProfileService(workspace_root=workspace).build_weight_profile("财运")

    assert adjusted.feedback_overlay_version == "feedback-overlay-v1"
    assert adjusted.n_eff_summary["ziping"]["n_eff"] == 1.0
    assert adjusted.feedback_modulations["ziping"] == pytest.approx(0.98826196)
    assert abs(adjusted.feedback_modulations["ziping"] - 1.0) <= 0.02
    assert adjusted.domain_weights == pytest.approx(
        {
            "blind": 0.301593050078,
            "ziping": 0.447079408189,
            "tiaohou_ditiansui": 0.251327541732,
        }
    )
    assert round(sum(adjusted.domain_weights.values()), 12) == 1.0

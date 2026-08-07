from __future__ import annotations

import json
from pathlib import Path

import yaml


def _write_synthetic_jsonl(path: Path, rows: list[dict]) -> None:
    """Write synthetic test fixture data; never targets real engine/logs files."""

    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n",
        encoding="utf-8",
    )


def test_aggregate_expert_domain_feedback_across_multiple_cases(tmp_path: Path) -> None:
    """Synthetic fixture proves aggregation consumes all historical JSONL rows."""

    from tools.parallel_domain_weight_status_scan import aggregate_expert_domain_feedback

    expert_log = tmp_path / "synthetic-expert-domain-feedback.jsonl"
    _write_synthetic_jsonl(
        expert_log,
        [
            {
                "case_id": "C-SYNTHETIC-001",
                "domain": "财运",
                "expert_system": "ziping",
                "verdict": "hit",
            },
            {
                "case_id": "C-SYNTHETIC-002",
                "domain": "财运",
                "expert_system": "ziping",
                "verdict": "miss",
            },
            {
                "case_id": "C-SYNTHETIC-002",
                "domain": "财运",
                "expert_system": "ziping",
                "verdict": "hit",
            },
        ],
    )

    items = aggregate_expert_domain_feedback(expert_log)

    assert items == [
        {
            "domain": "财运",
            "expert_system": "ziping",
            "hits": 2,
            "misses": 1,
            "n_eff": 3.0,
            "beta_mean": 0.6,
            "wilson_lower": 0.207655,
        }
    ]


def _write_synthetic_profile(path: Path, *, entries: list[dict]) -> None:
    """Write a synthetic canonical-profile fixture under tmp_path only."""

    path.write_text(
        yaml.safe_dump(
            {
                "schema_version": "expert-weight-profile/v1",
                "constraints": {"min_effective_sample_for_adjustment": 3},
                "feedback_overlay": {
                    "version": "feedback-overlay-v1" if entries else "no-feedback-overlay",
                    "min_effective_sample_for_adjustment": 3,
                    "entries": entries,
                },
            },
            allow_unicode=True,
            sort_keys=False,
        ),
        encoding="utf-8",
    )


def test_pending_promotion_review_detects_missing_and_current_overlay(tmp_path: Path) -> None:
    """Synthetic fixtures prove threshold/staleness comparison without production files."""

    from tools.parallel_domain_weight_status_scan import build_status_report

    expert_log = tmp_path / "synthetic-expert-domain-feedback.jsonl"
    adjudication_log = tmp_path / "synthetic-adjudication-accuracy.jsonl"
    profile_path = tmp_path / "synthetic-expert-weights.yaml"
    _write_synthetic_jsonl(
        expert_log,
        [
            {
                "case_id": f"C-SYNTHETIC-{index:03d}",
                "domain": "财运",
                "expert_system": "ziping",
                "verdict": "hit" if index < 3 else "miss",
            }
            for index in range(4)
        ],
    )
    _write_synthetic_jsonl(adjudication_log, [])
    _write_synthetic_profile(profile_path, entries=[])

    missing_report = build_status_report(
        expert_log_path=expert_log,
        adjudication_log_path=adjudication_log,
        profile_path=profile_path,
    )

    assert missing_report["min_effective_sample_for_adjustment"] == 3.0
    assert missing_report["pending_promotion_review"] == [
        {
            "domain": "财运",
            "expert_system": "ziping",
            "log_n_eff": 4.0,
            "overlay_n_eff": None,
            "reason": "missing_overlay_entry",
        }
    ]

    _write_synthetic_profile(
        profile_path,
        entries=[{"domain": "财运", "expert_system": "ziping", "n_eff": 4.0}],
    )
    current_report = build_status_report(
        expert_log_path=expert_log,
        adjudication_log_path=adjudication_log,
        profile_path=profile_path,
    )

    assert current_report["pending_promotion_review"] == []


def test_cli_formats_and_check_exit_codes(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    """Synthetic CLI fixtures prove markdown/json output and check semantics."""

    from tools import parallel_domain_weight_status_scan as scan

    expert_log = tmp_path / "synthetic-expert-domain-feedback.jsonl"
    adjudication_log = tmp_path / "synthetic-adjudication-accuracy.jsonl"
    profile_path = tmp_path / "synthetic-expert-weights.yaml"
    _write_synthetic_jsonl(
        expert_log,
        [
            {
                "case_id": f"C-SYNTHETIC-{index:03d}",
                "domain": "事业",
                "expert_system": "blind",
                "verdict": "hit",
            }
            for index in range(3)
        ],
    )
    _write_synthetic_jsonl(
        adjudication_log,
        [
            {
                "case_id": "C-SYNTHETIC-001",
                "domain": "事业",
                "verdict": "hit",
            }
        ],
    )
    _write_synthetic_profile(profile_path, entries=[])
    monkeypatch.setattr(scan, "EXPERT_FEEDBACK_LOG", expert_log)
    monkeypatch.setattr(scan, "ADJUDICATION_ACCURACY_LOG", adjudication_log)
    monkeypatch.setattr(scan, "CANONICAL_PROFILE", profile_path)

    assert scan.main(["--format", "markdown"]) == 0
    markdown_output = capsys.readouterr().out
    assert "# parallel domain weight status scan" in markdown_output
    assert "pending_promotion_review" in markdown_output

    assert scan.main(["--format", "json"]) == 0
    json_output = json.loads(capsys.readouterr().out)
    assert json_output["pending_promotion_review_count"] == 1

    assert scan.main(["--check"]) == 1
    check_output = capsys.readouterr()
    assert "parallel domain weight status scan failed" in check_output.err
    assert "事业 / blind" in check_output.err

    _write_synthetic_profile(
        profile_path,
        entries=[{"domain": "事业", "expert_system": "blind", "n_eff": 3.0}],
    )
    assert scan.main(["--check"]) == 0
    assert "parallel domain weight status scan passed" in capsys.readouterr().out

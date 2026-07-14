from pathlib import Path

from engine.evaluation.models import BlindTask
from tools.school_capability_batch import (
    build_historical_blind_artifacts,
    build_historical_reviewed_manifest,
    parse_case_summary,
    parse_case_summary_with_audit,
    parse_feedback_labels,
    render_historical_baseline,
    score_historical_batch,
)


def test_parse_case_summary_strips_sources_and_returns_unique_canonical_cases(tmp_path: Path) -> None:
    source = tmp_path / "shuru-input.md"
    source.write_text(
        """# 汇总

## P-2026-001 · 乾 · 戊申癸亥戊戌癸亥
- 性别：男（乾）
- 公历生日：1968-11-24 22:33
- 四柱：戊申 癸亥 戊戌 癸亥
- 大运：5岁起运；甲子→乙丑→丙寅
- 来源：https://example.invalid/feedback

---

## P-2026-002 · 坤 · 癸亥戊午乙亥戊寅
- 性别：女（坤）
- 公历生日：1983-06-16 03:30
- 四柱：癸亥 戊午 乙亥 戊寅
- 大运：7岁起运；己未→庚申→辛酉
- 来源：https://example.invalid/report
""",
        encoding="utf-8",
    )

    cases = parse_case_summary(source)

    assert [case.case_id for case in cases] == [
        "P-2026-001-乾-戊申癸亥戊戌癸亥",
        "P-2026-002-坤-癸亥戊午乙亥戊寅",
    ]
    assert cases[0].four_pillars == ("戊申", "癸亥", "戊戌", "癸亥")
    assert cases[0].sex_marker == "乾"
    assert cases[0].solar_datetime == "1968-11-24 22:33"
    assert cases[0].dayun_sequence == ("甲子", "乙丑", "丙寅")
    assert "来源" not in cases[0].isolated_input
    assert "feedback" not in cases[0].isolated_input.lower()
    assert "report" not in cases[1].isolated_input.lower()


def test_parse_case_summary_rejects_duplicate_subjects(tmp_path: Path) -> None:
    source = tmp_path / "shuru-input.md"
    source.write_text(
        """## P-2026-001 · 乾 · 甲子乙丑丙寅丁卯
- 公历生日：2000-01-01 01:00
- 四柱：甲子 乙丑 丙寅 丁卯
---
## P-2026-002 · 乾 · 甲子乙丑丙寅丁卯
- 公历生日：2000-01-01 01:00
- 四柱：甲子 乙丑 丙寅 丁卯
""",
        encoding="utf-8",
    )

    try:
        parse_case_summary(source)
    except ValueError as error:
        assert "duplicate subject" in str(error)
    else:
        raise AssertionError("duplicate subjects must be rejected")


def test_parse_case_summary_audit_mode_keeps_more_complete_duplicate(tmp_path: Path) -> None:
    source = tmp_path / "shuru-input.md"
    source.write_text(
        """## P-2026-001 · 乾 · 甲子乙丑丙寅丁卯
- 公历生日：来源未提供
- 四柱：甲子 乙丑 丙寅 丁卯
- 大运：来源未提供
---
## P-2026-002 · 乾 · 甲子乙丑丙寅丁卯
- 公历生日：2000-01-01 01:00
- 四柱：甲子 乙丑 丙寅 丁卯
- 大运：3岁起运；戊辰→己巳→庚午
""",
        encoding="utf-8",
    )

    result = parse_case_summary_with_audit(source)

    assert [case.case_id for case in result.cases] == ["P-2026-002-乾-甲子乙丑丙寅丁卯"]
    assert result.duplicates == [{
        "discarded_case_id": "P-2026-001-乾-甲子乙丑丙寅丁卯",
        "kept_case_id": "P-2026-002-乾-甲子乙丑丙寅丁卯",
        "reason": "duplicate_subject_less_complete",
    }]


def test_build_historical_blind_artifacts_freezes_without_source_or_feedback_text(tmp_path: Path) -> None:
    source = tmp_path / "shuru-input.md"
    source.write_text(
        """## P-2026-001 · 乾 · 戊申癸亥戊戌癸亥
- 性别：男（乾）
- 公历生日：1968-11-24 22:33
- 四柱：戊申 癸亥 戊戌 癸亥
- 大运：5岁起运；甲子→乙丑→丙寅
- 来源：https://example.invalid/feedback
""",
        encoding="utf-8",
    )
    task = BlindTask(
        task_id="structure.overview",
        domain="总体",
        claim_type="structure_claim",
        scoring_method="portrait_agreement",
        quantifiable=False,
        high_risk=False,
        allowed_time_horizons=["lifetime"],
        required_input_fields=["four_pillars"],
        label_schema={},
        evaluation_note="fixture",
    )

    artifacts = build_historical_blind_artifacts(
        source,
        [task],
        schools=["ziping", "ren"],
        task_catalog_version="tasks-test",
        rule_snapshot_id="rules-test",
        frozen_at="2026-07-14T00:00:00Z",
    )

    assert artifacts["schema_version"] == "school-capability-historical-batch/v1"
    assert artifacts["classification"] == "historical_blind_candidate"
    assert len(artifacts["cases"]) == 1
    assert len(artifacts["frozen_run"]["outputs"]) == 2
    assert artifacts["frozen_run"]["frozen_at"] == "2026-07-14T00:00:00Z"
    serialized = str(artifacts).lower()
    assert "example.invalid" not in serialized
    assert "feedback" not in serialized


def test_parse_feedback_labels_extracts_only_explicit_low_risk_facts(tmp_path: Path) -> None:
    feedback = tmp_path / "fankui-feedback.md"
    feedback.write_text(
        """## P-2026-001 · 乾 · 戊申癸亥戊戌癸亥 · 1968-11-24
**来源级别**：一级来源（命主本人）
### 命主背景
- 学历：本科
- 职业：长期打工，2012年开始创业
### 关键事件
| 年份 | 事件 |
|---|---|
| 2008 | 结婚 |
| 2012 | 离职后创业 |
| 约2014 | 可能发生破财 |
""",
        encoding="utf-8",
    )
    case_id = "P-2026-001-乾-戊申癸亥戊戌癸亥"

    labels = parse_feedback_labels(feedback, {case_id}, reviewer="human-reviewer-01")
    indexed = {(item["case_id"], item["task_id"]): item for item in labels}

    assert indexed[(case_id, "education.attainment_band")]["label"] == "tertiary"
    assert indexed[(case_id, "career.path_type")]["label"] == "mixed"
    assert indexed[(case_id, "career.change_window")]["label"] == {"occurred": True, "year": 2012}
    assert indexed[(case_id, "marriage.event_window")]["label"] == {"occurred": True, "year": 2008}
    assert not any(item["task_id"] == "wealth.major_loss_window" for item in labels)
    assert all(item["source"].startswith("cases/fankui-feedback.md:") for item in labels)
    assert all(item["reviewer"] == "human-reviewer-01" for item in labels)


def test_parse_feedback_labels_skips_discarded_duplicate_and_unknown_cases(tmp_path: Path) -> None:
    feedback = tmp_path / "fankui-feedback.md"
    feedback.write_text(
        """## P-2026-010 · 乾 · 戊午辛酉癸巳甲寅
**来源级别**：一级来源
- 学历：本科
---
## P-2026-999 · 乾 · 甲子乙丑丙寅丁卯
**来源级别**：一级来源
- 学历：本科
""",
        encoding="utf-8",
    )

    assert parse_feedback_labels(
        feedback,
        {"P-2026-045-乾-戊午辛酉癸巳甲寅"},
        reviewer="human-reviewer-01",
    ) == []


def test_score_historical_batch_preserves_freeze_and_scores_all_outputs(tmp_path: Path) -> None:
    source = tmp_path / "shuru-input.md"
    source.write_text(
        """## P-2026-001 · 乾 · 戊申癸亥戊戌癸亥
- 公历生日：1968-11-24 22:33
- 四柱：戊申 癸亥 戊戌 癸亥
""",
        encoding="utf-8",
    )
    task = BlindTask(
        task_id="structure.overview", domain="总体", claim_type="structure_claim",
        scoring_method="portrait_agreement", quantifiable=False, high_risk=False,
        allowed_time_horizons=["lifetime"], required_input_fields=["four_pillars"],
        label_schema={}, evaluation_note="fixture",
    )
    artifact = build_historical_blind_artifacts(
        source, [task], schools=["ziping", "ren"],
        task_catalog_version="tasks-test", rule_snapshot_id="rules-test",
        frozen_at="2026-07-14T00:00:00Z",
    )
    freeze_hash = artifact["frozen_run"]["freeze_hash"]

    result = score_historical_batch(
        artifact,
        [task],
        labels=[],
        reviewer="human-reviewer-01",
        evaluated_at="2026-07-14T01:00:00Z",
    )

    assert result["freeze_hash"] == freeze_hash
    assert result["scored_output_count"] == 2
    assert result["label_count"] == 0
    assert result["posteriors"] == []
    assert result["status"] == "HOLD"
    assert "no probability claims" in result["hold_reasons"]


def test_manifest_and_report_publish_only_labelled_candidates_without_internal_ids(tmp_path: Path) -> None:
    source = tmp_path / "shuru-input.md"
    source.write_text(
        """## P-2026-001 · 乾 · 戊申癸亥戊戌癸亥
- 公历生日：1968-11-24 22:33
- 四柱：戊申 癸亥 戊戌 癸亥
""",
        encoding="utf-8",
    )
    task = BlindTask(
        task_id="structure.overview", domain="总体", claim_type="structure_claim",
        scoring_method="portrait_agreement", quantifiable=False, high_risk=False,
        allowed_time_horizons=["lifetime"], required_input_fields=["four_pillars"],
        label_schema={}, evaluation_note="fixture",
    )
    artifact = build_historical_blind_artifacts(
        source, [task], schools=["ziping", "ren"],
        task_catalog_version="tasks-test", rule_snapshot_id="rules-test",
        frozen_at="2026-07-14T00:00:00Z",
    )
    labels = [{
        "case_id": artifact["cases"][0]["case_id"], "task_id": "structure.overview",
        "label": "structure", "source": "cases/fankui-feedback.md:1",
        "observed_at": "2026-07-14", "confidence_grade": "B",
        "quantifiable": False, "conflict_state": "none", "reviewer": "human-reviewer-01",
    }]
    manifest = build_historical_reviewed_manifest(
        artifact, [task], labels=labels, reviewer="human-reviewer-01",
        generated_at="2026-07-14T01:00:00Z",
    )
    scores = score_historical_batch(
        artifact, [task], labels=labels, reviewer="human-reviewer-01",
        evaluated_at="2026-07-14T01:00:00Z",
    )

    assert manifest["records"][0]["eligibility"] == "historical_blind_candidate"
    text = render_historical_baseline(manifest, scores)
    assert "HOLD" in text
    assert "structure.overview" not in text
    assert artifact["cases"][0]["case_id"] not in text
    assert "prediction-" not in text

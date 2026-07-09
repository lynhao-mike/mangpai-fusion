"""H3 · feedback_ingest 解析正确率 ≥ 99%

落地：plans/architecture-v1.3.md § 六 H3
要求：100 条人工标注样本，feedback_ingest 解析正确率 ≥ 99%

策略：
    - 自动构造 100 条标注（覆盖 4 种标注 × 各类前后缀干扰）
    - parse_statement_feedback 解析后比对 (sid, verdict)
    - 正确率 = (正确解析行) / 100 ≥ 0.99
"""
from __future__ import annotations

import pytest


pytestmark = pytest.mark.v1_3_acceptance


def _generate_100_samples() -> list[tuple[str, str, str]]:
    """生成 100 条 (line_text, expected_sid, expected_verdict)。

    覆盖 4 种标注（y/n/?/skip）× 多种行格式：
        反馈：[S-001-aaaaaa] [y]
        [S-001-aaaaaa] [n]   <- 无前缀
        反馈：[S-001-aaaaaa] [?]
        反馈：[S-001-aaaaaa] [skip]
        反馈：[S-001-aaaaaa]    [y]    <- 多空格
        | 表格行 | [S-001-aaaaaa] [n] | <- 表格内
    """
    samples = []
    # 准备 25 个 sid（4 标注各占 25 个 → 100 行）
    sids = [f"S-{(i % 999):03d}-{(i + 1) * 1234:06x}"[:14] for i in range(100)]
    # 修正格式: S-NNN-XXXXXX
    sids = []
    for i in range(100):
        nnn = f"{(i + 1) % 1000:03d}"
        suffix = f"{(i * 31337 + 0xa1b2c3) % 0xffffff:06x}"
        sids.append(f"S-{nnn}-{suffix}")

    annotations = ["y", "n", "?", "skip"]
    verdicts = {"y": "hit", "n": "miss", "?": "no_data", "skip": "no_data"}
    formats = [
        "反馈：[{sid}] [{ann}]",
        "[{sid}] [{ann}]",
        "  反馈：[{sid}]  [{ann}]  ",  # 多空格
        "**反馈**：[{sid}] [{ann}]",  # markdown 加粗
        "| 表格 | [{sid}] [{ann}] |",  # 表格行
    ]
    for i in range(100):
        ann = annotations[i % 4]
        fmt = formats[i % len(formats)]
        line = fmt.format(sid=sids[i], ann=ann)
        samples.append((line, sids[i], verdicts[ann]))
    return samples


def test_h3_parsing_100_samples_accuracy_ge_99pct():
    """100 条标注样本解析正确率 ≥ 99%。"""
    from tools.feedback_ingest import parse_statement_feedback

    samples = _generate_100_samples()
    assert len(samples) == 100

    # 把 100 行拼成一个 markdown 文档（与真实 feedback.md 一致）
    text = "\n".join(line for line, _, _ in samples)
    parsed = parse_statement_feedback(text)
    parsed_map = {f.statement_id: f for f in parsed}

    correct = 0
    errors = []
    for line, expected_sid, expected_verdict in samples:
        if expected_sid not in parsed_map:
            errors.append(f"未解析: {line[:80]}  → 期望 sid={expected_sid}")
            continue
        got_verdict = parsed_map[expected_sid].verdict
        if got_verdict == expected_verdict:
            correct += 1
        else:
            errors.append(
                f"verdict 错: {line[:60]}  期望 {expected_verdict} 实得 {got_verdict}"
            )

    accuracy = correct / 100
    assert accuracy >= 0.99, (
        f"解析正确率 {accuracy:.1%} < 99% 阈值\n"
        f"errors (前 5 条):\n  " + "\n  ".join(errors[:5])
    )


def test_h3_priority_question_skip_to_no_data():
    """`?` 与 `skip` 都映射到 no_data（D5 决策：入库不计数）。"""
    from tools.feedback_ingest import (
        ANNOTATION_TO_VERDICT,
        parse_statement_feedback,
    )

    assert ANNOTATION_TO_VERDICT["?"] == "no_data"
    assert ANNOTATION_TO_VERDICT["skip"] == "no_data"

    text = """
    反馈：[S-001-aaaaaa] [?]
    反馈：[S-001-bbbbbb] [skip]
    """
    parsed = parse_statement_feedback(text)
    assert all(p.verdict == "no_data" for p in parsed)


def test_h3_duplicate_sid_takes_last_annotation():
    """同 sid 多次出现 → 取最后一次（命理师改主意）。"""
    from tools.feedback_ingest import parse_statement_feedback

    text = """
    反馈：[S-001-deadbe] [y]
    后来想起来其实是失验，改成 n：
    反馈：[S-001-deadbe] [n]
    """
    parsed = parse_statement_feedback(text)
    assert len(parsed) == 1
    assert parsed[0].verdict == "miss"


def test_h3_no_match_when_no_annotations():
    """全空文档 → 0 条结果（兜底）。"""
    from tools.feedback_ingest import parse_statement_feedback

    assert parse_statement_feedback("") == []
    assert parse_statement_feedback("# 命主反馈\n纯文字无标注") == []


def test_h3_fanout_decisive_priority():
    """fanout 决断力优先（miss > hit > abstain > no_data）。"""
    from tools.feedback_ingest import (
        StatementFeedback,
        fanout_to_rules,
    )

    statement_records = {
        "records": [
            {"statement_id": "S-001-aaaaaa", "rule_id": "M1-D-001", "family_id": "FAM-M1", "school": "段", "canon": "duan", "rule_type": "runtime_rule", "domain": "婚姻"},
            {"statement_id": "S-001-cccccc", "rule_id": "M2-Y-068", "family_id": "FAM-M2", "school": "杨", "canon": "yang", "rule_type": "runtime_rule", "domain": "婚姻"},
            {"statement_id": "S-001-bbbbbb", "rule_id": "M1-D-001", "family_id": "FAM-M1", "school": "段", "canon": "duan", "rule_type": "runtime_rule", "domain": "事业"},
        ],
    }
    feedbacks = [
        StatementFeedback("S-001-aaaaaa", "y", "hit"),
        StatementFeedback("S-001-cccccc", "y", "hit"),
        StatementFeedback("S-001-bbbbbb", "n", "miss"),
    ]
    rule_verdicts, unknown = fanout_to_rules(feedbacks, statement_records)
    # M1-D-001 同时被 hit + miss 标注的两条断语支撑 → miss 优先
    assert rule_verdicts["M1-D-001"][0] == "miss", (
        "M1-D-001 应取 miss（决断力优先），实得 "
        f"{rule_verdicts['M1-D-001'][0]}"
    )
    # M2-Y-068 仅被 hit 标注的断语支撑 → hit
    assert rule_verdicts["M2-Y-068"][0] == "hit"
    assert unknown == []


def test_h3_standard_list_schema_without_rule_ids_is_blocked_from_learning():
    """无 statement_records 规则桥时阻断规则学习。"""
    from tools.feedback_ingest import StatementFeedback, fanout_to_rules

    statement_index = {
        "case_id": "C-2026-025-坤-辛未乙未甲辰乙亥",
        "generated_at": "2026-05-30",
        "statements": [
            {
                "statement_id": "S-025-d1a001",
                "domain": "事业/财富",
                "summary": "财厚劫透，适合资源整合，忌人情财务混杂",
                "status": "pending",
            }
        ],
    }
    rule_verdicts, unknown = fanout_to_rules(
        [StatementFeedback("S-025-d1a001", "y", "hit")],
        statement_index,
    )
    assert rule_verdicts == {}
    assert unknown == ["S-025-d1a001"]


def test_h3_statement_records_enable_fanout():
    """statement_records 是规则级 fanout 唯一来源。"""
    from tools.feedback_ingest import StatementFeedback, fanout_to_rules

    statement_records = {
        "records": [
            {"statement_id": "S-025-d1a001", "rule_id": "M1-D-013", "family_id": "FAM-M1", "school": "段", "canon": "duan", "rule_type": "runtime_rule", "section": "Step 1"},
        ]
    }
    rule_verdicts, unknown = fanout_to_rules(
        [StatementFeedback("S-025-d1a001", "y", "hit")],
        statement_records,
    )

    assert set(rule_verdicts) == {"M1-D-013"}
    assert all(v[0] == "hit" for v in rule_verdicts.values())
    assert unknown == []


def test_h3_non_hash_statement_id_is_supported():
    """手工归档 statement_id（如 S-025-d1a001）必须被统一协议解析。"""
    from tools.feedback_ingest import parse_statement_feedback

    parsed = parse_statement_feedback("- [S-025-d1a001] [y] 事实：命中")
    assert len(parsed) == 1
    assert parsed[0].statement_id == "S-025-d1a001"
    assert parsed[0].verdict == "hit"


def test_h3_parallel_feedback_fanout_stats_and_weight_proposal(tmp_path, monkeypatch):
    """并行域 statement 反馈应写入 reading/adjudication 级日志并可聚合提案。"""
    import tools.feedback_ingest as fi
    from tools.feedback_ingest import (
        StatementFeedback,
        compute_weight_update_proposal,
        fanout_to_parallel_feedback,
        get_expert_domain_stats,
    )

    expert_log = tmp_path / "expert_domain_feedback.jsonl"
    adjudication_log = tmp_path / "adjudication_accuracy.jsonl"
    monkeypatch.setattr(fi, "EXPERT_DOMAIN_FEEDBACK_LOG", expert_log)
    monkeypatch.setattr(fi, "ADJUDICATION_ACCURACY_LOG", adjudication_log)
    statement_index = {
        "statements": [
            {
                "statement_id": "S-PD-001",
                "section": "parallel_domain_adjudication",
                "domain": "财运",
                "summary": "财运可用",
                "claim": "财运可用",
                "decision": "yes",
                "reading_ids": ["RD-C-TEST-财运-BLIND-001", "RD-C-TEST-财运-ZIPING-001"],
                "adjudication_id": "ADJ-C-TEST-财运",
                "expert_systems": ["blind", "ziping"],
                "supporting_experts": ["blind", "ziping"],
                "dissenting_experts": [],
                "abstained_experts": ["tiaohou_ditiansui"],
                "consensus_layer": "双专家共识",
            }
        ]
    }

    counts = fanout_to_parallel_feedback(
        [StatementFeedback("S-PD-001", "y", "hit")],
        statement_index,
        case_id="C-TEST",
    )

    assert counts == {"expert_feedback_rows": 2, "adjudication_feedback_rows": 1}
    stats = get_expert_domain_stats(domain="财运", expert="blind")
    assert stats["items"][0]["hits"] == 1
    assert stats["items"][0]["sample_warning"] is True
    proposal = compute_weight_update_proposal(min_n_eff=1)
    assert proposal["proposal_count"] >= 1
    assert proposal["proposals"][0]["requires_human_review"] is True


def test_h3_weight_proposal_low_sample_only_warns(tmp_path, monkeypatch):
    """n_eff < 5 时只提示样本不足，不产生调整 proposal。"""
    import json
    import tools.feedback_ingest as fi
    from tools.feedback_ingest import compute_weight_update_proposal

    expert_log = tmp_path / "expert_domain_feedback.jsonl"
    monkeypatch.setattr(fi, "EXPERT_DOMAIN_FEEDBACK_LOG", expert_log)
    rows = [
        {"domain": "财运", "expert_system": "blind", "verdict": "hit"},
        {"domain": "财运", "expert_system": "blind", "verdict": "miss"},
        {"domain": "财运", "expert_system": "blind", "verdict": "miss"},
        {"domain": "财运", "expert_system": "blind", "verdict": "miss"},
    ]
    expert_log.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")

    proposal = compute_weight_update_proposal(min_n_eff=5)

    assert proposal["proposal_count"] == 0
    assert proposal["diagnostics"][0]["n_eff"] == 4.0
    assert proposal["diagnostics"][0]["adjustment_allowed"] is False
    assert "样本不足" in proposal["diagnostics"][0]["reason"]


def test_h3_weight_proposal_allows_larger_adjustment_at_n_eff_10(tmp_path, monkeypatch):
    """n_eff >= 10 时允许进入 0.70~1.30 的较大调整区间。"""
    import json
    import tools.feedback_ingest as fi
    from tools.feedback_ingest import compute_weight_update_proposal

    expert_log = tmp_path / "expert_domain_feedback.jsonl"
    monkeypatch.setattr(fi, "EXPERT_DOMAIN_FEEDBACK_LOG", expert_log)
    rows = [{"domain": "财运", "expert_system": "ziping", "verdict": "hit"} for _ in range(10)]
    expert_log.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")

    proposal = compute_weight_update_proposal(min_n_eff=10)

    assert proposal["proposal_count"] == 1
    assert proposal["proposals"][0]["n_eff"] == 10.0
    assert proposal["proposals"][0]["proposed_feedback_multiplier"] == 1.3


def test_h3_consecutive_misses_trigger_downweight_proposal(tmp_path, monkeypatch):
    """连续 miss 应触发降权 proposal。"""
    import json
    import tools.feedback_ingest as fi
    from tools.feedback_ingest import compute_weight_update_proposal

    expert_log = tmp_path / "expert_domain_feedback.jsonl"
    monkeypatch.setattr(fi, "EXPERT_DOMAIN_FEEDBACK_LOG", expert_log)
    rows = [{"domain": "婚姻", "expert_system": "blind", "verdict": "miss"} for _ in range(10)]
    expert_log.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")

    proposal = compute_weight_update_proposal(min_n_eff=10)

    assert proposal["proposal_count"] == 1
    assert proposal["proposals"][0]["expert_system"] == "blind"
    assert proposal["proposals"][0]["proposed_feedback_multiplier"] == 0.7


def test_h3_apply_weight_proposal_preview_normalizes_and_does_not_write(tmp_path):
    """未人工确认时只返回归一化 preview，不写入任何权重文件。"""
    from tools.feedback_ingest import apply_weight_update_proposal

    output_path = tmp_path / "feedback_overlay.json"
    base_profile = {
        "profile_id": "domain-prior-test",
        "profile_version": "test-v1",
        "weights": {
            "财运": {"blind": 0.30, "ziping": 0.45, "tiaohou_ditiansui": 0.25},
        },
    }
    proposal = {
        "proposals": [
            {
                "domain": "财运",
                "expert_system": "ziping",
                "proposed_feedback_multiplier": 1.30,
                "requires_human_review": True,
            },
            {
                "domain": "财运",
                "expert_system": "blind",
                "proposed_feedback_multiplier": 0.70,
                "requires_human_review": True,
            },
        ]
    }

    result = apply_weight_update_proposal(
        proposal,
        base_profile=base_profile,
        output_path=output_path,
    )

    assert result["applied"] is False
    assert output_path.exists() is False
    weights = result["overlay"]["weights"]["财运"]
    assert round(sum(weights.values()), 6) == 1.0
    assert weights["ziping"] > base_profile["weights"]["财运"]["ziping"]
    assert weights["blind"] < base_profile["weights"]["财运"]["blind"]
    assert "feedback_overlay" in result["preview_diff"]


def test_h3_apply_weight_proposal_requires_confirmation_to_write(tmp_path):
    """应用型入口必须显式人工确认后才写 overlay 文件。"""
    import json
    from tools.feedback_ingest import apply_weight_update_proposal

    output_path = tmp_path / "feedback_overlay.json"
    base_profile = {
        "profile_id": "domain-prior-test",
        "profile_version": "test-v1",
        "weights": {
            "事业": {"blind": 0.25, "ziping": 0.50, "tiaohou_ditiansui": 0.25},
        },
    }
    proposal = {
        "proposals": [
            {
                "domain": "事业",
                "expert_system": "ziping",
                "proposed_feedback_multiplier": 0.70,
                "requires_human_review": True,
            },
        ]
    }

    result = apply_weight_update_proposal(
        proposal,
        base_profile=base_profile,
        confirm=True,
        output_path=output_path,
    )

    assert result["applied"] is True
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["status"] == "human_confirmed"
    assert round(sum(payload["weights"]["事业"].values()), 6) == 1.0


def test_v5_feedback_attachment_validation_ok(tmp_path):
    from engine.v5 import V5FeedbackAttachment, V5RunSnapshot, run_v5_snapshot
    from tools.feedback_ingest import _validate_v5_feedback_attachment

    case_dir = tmp_path / "C-TEST-ATTACH-OK"
    case_dir.mkdir()
    snapshot = run_v5_snapshot({"case_id": "C-TEST-ATTACH-OK", "pillars": ["鐢插瓙", "涔欎笐", "涓欏瘏", "涓佸嵂"]})
    run_path = case_dir / "case.run.json"
    attachment_path = case_dir / "case.feedback-attachment.json"
    run_path.write_text(snapshot.to_json(), encoding="utf-8")
    attachment_path.write_text(
        V5FeedbackAttachment.from_run_snapshot(snapshot, feedback_path=(case_dir / "feedback.md").as_posix()).to_json(),
        encoding="utf-8",
    )

    summary = _validate_v5_feedback_attachment(case_dir, "C-TEST-ATTACH-OK")

    assert summary == {
        "status": "ok",
        "attachment_path": attachment_path.as_posix(),
        "run_snapshot_path": run_path.as_posix(),
        "case_id": "C-TEST-ATTACH-OK",
        "run_id": snapshot.run_id,
        "target_counts": {
            "claims": len(snapshot.claims),
            "predictions": len(snapshot.prediction_ledger.predictions),
            "signals": len(snapshot.learning_signals),
        },
        "issues": [],
    }


def test_v5_feedback_attachment_validation_missing(tmp_path):
    from tools.feedback_ingest import _validate_v5_feedback_attachment

    case_dir = tmp_path / "C-TEST-ATTACH-MISSING"
    case_dir.mkdir()

    summary = _validate_v5_feedback_attachment(case_dir, "C-TEST-ATTACH-MISSING")

    assert summary["status"] == "missing"
    assert summary["attachment_path"] == ""
    assert summary["run_snapshot_path"] == ""
    assert summary["case_id"] == "C-TEST-ATTACH-MISSING"
    assert summary["run_id"] == ""
    assert summary["target_counts"] == {"claims": 0, "predictions": 0, "signals": 0}
    assert summary["issues"] == ["feedback attachment not found"]


def test_v5_feedback_attachment_validation_reports_target_mismatch(tmp_path):
    from engine.v5 import V5FeedbackAttachment, run_v5_snapshot
    from tools.feedback_ingest import _validate_v5_feedback_attachment

    case_dir = tmp_path / "C-TEST-ATTACH-MISMATCH"
    case_dir.mkdir()
    snapshot = run_v5_snapshot({"case_id": "C-TEST-ATTACH-MISMATCH", "pillars": ["鐢插瓙", "涔欎笐", "涓欏瘏", "涓佸嵂"]})
    payload = V5FeedbackAttachment.from_run_snapshot(snapshot).to_dict()
    payload["target_prediction_ids"].append("missing-prediction")
    (case_dir / "case.run.json").write_text(snapshot.to_json(), encoding="utf-8")
    (case_dir / "case.feedback-attachment.json").write_text(
        V5FeedbackAttachment.from_dict(payload).to_json(),
        encoding="utf-8",
    )

    summary = _validate_v5_feedback_attachment(case_dir, "C-TEST-ATTACH-MISMATCH")

    assert summary["status"] == "mismatch"
    assert "feedback target prediction_id not found in run snapshot: missing-prediction" in summary["issues"]


def test_ingest_includes_v5_feedback_attachment_summary_without_unblocking_learning(tmp_path, monkeypatch):
    import tools.feedback_ingest as fi
    from engine.v5 import V5FeedbackAttachment, run_v5_snapshot

    case_dir = tmp_path / "C-TEST-INGEST-ATTACH"
    case_dir.mkdir()
    (case_dir / "feedback.md").write_text("鍙嶉锛歔S-ATTACH-001] [y]", encoding="utf-8")
    snapshot = run_v5_snapshot({"case_id": "C-TEST-INGEST-ATTACH", "pillars": ["鐢插瓙", "涔欎笐", "涓欏瘏", "涓佸嵂"]})
    (case_dir / "case.run.json").write_text(snapshot.to_json(), encoding="utf-8")
    (case_dir / "case.feedback-attachment.json").write_text(
        V5FeedbackAttachment.from_run_snapshot(snapshot).to_json(),
        encoding="utf-8",
    )
    monkeypatch.setattr(fi, "find_case_dir", lambda case_id: case_dir)

    result = fi.ingest("C-TEST-INGEST-ATTACH", dry_run=True)

    assert result.skipped_no_index is True
    assert result.learning_sample_count == 0
    assert result.phase_a_learning_summary["v5_feedback_attachment"]["status"] == "ok"
    assert result.phase_a_learning_summary["v5_feedback_attachment"]["run_id"] == snapshot.run_id


def test_v5_feedback_attachment_validation_selects_matching_run_id_in_multi_run_case(tmp_path):
    from dataclasses import replace

    from engine.v5 import V5FeedbackAttachment, run_v5_snapshot
    from tools.feedback_ingest import _validate_v5_feedback_attachment

    case_dir = tmp_path / "C-TEST-ATTACH-MULTIRUN"
    case_dir.mkdir()
    right = run_v5_snapshot({"case_id": "C-TEST-ATTACH-MULTIRUN", "pillars": ["鐢插瓙", "涔欎笐", "涓欏瘏", "涓佸嵂"]})
    wrong = replace(right, run_id="run-wrong-newer")
    right_path = case_dir / "right.run.json"
    wrong_path = case_dir / "wrong.run.json"
    attachment_path = case_dir / "case.feedback-attachment.json"
    right_path.write_text(right.to_json(), encoding="utf-8")
    wrong_path.write_text(wrong.to_json(), encoding="utf-8")
    attachment_path.write_text(V5FeedbackAttachment.from_run_snapshot(right).to_json(), encoding="utf-8")
    # Make the wrong snapshot newer; old implementation picked this and reported mismatch.
    wrong_path.touch()

    summary = _validate_v5_feedback_attachment(case_dir, "C-TEST-ATTACH-MULTIRUN")

    assert summary["status"] == "ok"
    assert summary["run_id"] == right.run_id
    assert summary["run_snapshot_path"] == right_path.as_posix()
    assert summary["issues"] == []


def test_v5_feedback_attachment_validation_reports_no_matching_run_id(tmp_path):
    from dataclasses import replace

    from engine.v5 import V5FeedbackAttachment, run_v5_snapshot
    from tools.feedback_ingest import _validate_v5_feedback_attachment

    case_dir = tmp_path / "C-TEST-ATTACH-NO-RUN-MATCH"
    case_dir.mkdir()
    snapshot = run_v5_snapshot({"case_id": "C-TEST-ATTACH-NO-RUN-MATCH", "pillars": ["鐢插瓙", "涔欎笐", "涓欏瘏", "涓佸嵂"]})
    wrong = replace(snapshot, run_id="run-not-the-attachment")
    (case_dir / "wrong.run.json").write_text(wrong.to_json(), encoding="utf-8")
    (case_dir / "case.feedback-attachment.json").write_text(
        V5FeedbackAttachment.from_run_snapshot(snapshot).to_json(),
        encoding="utf-8",
    )

    summary = _validate_v5_feedback_attachment(case_dir, "C-TEST-ATTACH-NO-RUN-MATCH")

    assert summary["status"] == "mismatch"
    assert summary["attachment_path"] == (case_dir / "case.feedback-attachment.json").as_posix()
    assert summary["run_snapshot_path"] == ""
    assert summary["case_id"] == "C-TEST-ATTACH-NO-RUN-MATCH"
    assert summary["run_id"] == snapshot.run_id
    assert summary["target_counts"] == {
        "claims": len(snapshot.claims),
        "predictions": len(snapshot.prediction_ledger.predictions),
        "signals": len(snapshot.learning_signals),
    }
    assert summary["issues"] == [
        f"run snapshot for feedback attachment run_id not found: {snapshot.run_id}"
    ]

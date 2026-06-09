from __future__ import annotations

from tools.output_linter import lint


def test_parallel_domain_statement_traceability_requires_conflict_explanations_even_without_dissent() -> None:
    row = {
        "statement_id": "STMT-C-TEST-001",
        "section": "parallel_domain_adjudication",
        "reading_ids": ["RD-C-TEST-财运-blind"],
        "adjudication_id": "ADJ-C-TEST-财运",
        "expert_systems": ["blind"],
        "domain": "财运",
        "consensus_layer": "独门",
        "supporting_experts": ["blind"],
        "dissenting_experts": [],
        "abstained_experts": [],
        "feedback_state": "no-feedback-overlay",
    }

    result = lint({"statement_index": {"statements": [row]}})

    messages = [issue.message for issue in result.errors if issue.code == "E14"]
    assert any("conflict_explanations" in message for message in messages)


    row = {
        "statement_id": "STMT-C-TEST-001",
        "section": "parallel_domain_adjudication",
        "reading_ids": ["RD-C-TEST-财运-blind"],
        "adjudication_id": "ADJ-C-TEST-财运",
        "expert_systems": ["blind"],
        "domain": "财运",
        "consensus_layer": "单专家采纳",
        "supporting_experts": ["blind"],
        "dissenting_experts": [],
        "abstained_experts": [],
        "feedback_state": "no-feedback-overlay",
        "conflict_explanations": ["无专家强冲突。"],
    }

    result = lint({"statement_index": {"statements": [row]}})

    assert not [issue for issue in result.errors if issue.code == "E14"]


def test_parallel_domain_statement_traceability_blocks_missing_reading_ids_or_adjudication_id() -> None:
    row = {
        "statement_id": "STMT-C-TEST-001",
        "section": "parallel_domain_adjudication",
        "reading_ids": [],
        "adjudication_id": "",
        "expert_systems": ["blind"],
        "domain": "财运",
        "consensus_layer": "独门",
        "supporting_experts": ["blind"],
        "dissenting_experts": [],
        "abstained_experts": [],
        "feedback_state": "no-feedback-overlay",
        "conflict_explanations": ["无专家强冲突。"],
    }

    result = lint({"statement_index": {"statements": [row]}})

    messages = [issue.message for issue in result.errors if issue.code == "E14"]
    assert any("reading_ids" in message for message in messages)
    assert any("adjudication_id" in message for message in messages)


    row = {
        "statement_id": "STMT-C-TEST-001",
        "section": "parallel_domain_adjudication",
        "reading_ids": ["RD-C-TEST-财运-blind"],
        "consensus_layer": "单专家采纳",
        "dissenting_experts": ["ziping"],
    }

    result = lint({"statement_index": {"statements": [row]}})

    messages = [issue.message for issue in result.errors if issue.code == "E14"]
    assert any("adjudication_id" in message for message in messages)
    assert any("expert_systems" in message for message in messages)
    assert any("domain" in message for message in messages)
    assert any("supporting_experts" in message for message in messages)
    assert any("abstained_experts" in message for message in messages)
    assert any("feedback_state" in message for message in messages)
    assert any("conflict_explanations" in message for message in messages)


def test_parallel_domain_markdown_gate_blocks_missing_trace_fields() -> None:
    md = """
### 多专家功能域裁判（v1.5 旁路）

| 功能域 | 裁判层级 | 主结论 |
|---|---|---|
| 财运 | 单专家采纳 | 财运可用 |
"""

    result = lint(md)

    messages = [issue.message for issue in result.errors if issue.code == "E14"]
    assert any("reading_ids" in message for message in messages)
    assert any("adjudication_id" in message for message in messages)
    assert any("expert_systems" in message for message in messages)
    assert any("domain" in message for message in messages)
    assert any("consensus_layer" in message for message in messages)
    assert any("supporting_experts" in message for message in messages)
    assert any("dissenting_experts" in message for message in messages)
    assert any("abstained_experts" in message for message in messages)
    assert any("feedback_state" in message for message in messages)
    assert any("conflict 解释" in message for message in messages)


def test_parallel_domain_markdown_gate_accepts_required_trace_fields() -> None:
    md = """
### 多专家功能域裁判（v1.5 旁路）

| domain | consensus_layer | 主结论 | reading_ids | adjudication_id | expert_systems | supporting_experts | dissenting_experts | abstained_experts | feedback_state | 冲突解释 |
|---|---|---|---|---|---|---|---|---|---|---|
| 财运 | 单专家采纳 | 财运可用 | RD-C-TEST-财运-blind | ADJ-C-TEST-财运 | blind | blind | 无 | ziping,tiaohou_ditiansui | no-feedback-overlay | 无专家强冲突。 |
"""

    result = lint(md)

    assert not [issue for issue in result.errors if issue.code == "E14"]

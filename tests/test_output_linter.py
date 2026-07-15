"""报告文本内部标识禁显规则测试。"""

from tools.output_linter import lint_internal_ids, lint_report_text


def test_lint_internal_ids_rejects_claim_hash() -> None:
    errors = lint_report_text("合规标题\nclaim-abcdef1234567890abcdef")

    assert any("claim_id" in error for error in errors)


def test_lint_internal_ids_rejects_statement_index_field() -> None:
    errors = lint_report_text("statement_index: 12")

    assert any("statement_index" in error for error in errors)


def test_lint_internal_ids_covers_all_forbidden_public_tokens() -> None:
    text = "\n".join(
        [
            "prediction-abcdef1234567890",
            "statement_id: x",
            "capability_posterior: {}",
            "school_capability snapshot",
            "Agent 工作记录",
        ]
    )

    errors = lint_internal_ids(text)

    assert len(errors) == 5


def test_lint_internal_ids_accepts_compliant_report() -> None:
    assert lint_report_text("事业判断：当前证据支持稳步发展。\n风险窗口：2028—2030 年需关注。") == []

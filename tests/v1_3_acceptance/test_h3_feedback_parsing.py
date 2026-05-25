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

    statement_index = {
        "statements": {
            "S-001-aaaaaa": {
                "section": "consensus",
                "statement": "婚姻晚",
                "rule_ids": ["M1-D-001", "M2-Y-068"],  # 共支撑两条规律
                "domain": "婚姻",
                "year": None,
                "star": 4,
            },
            "S-001-bbbbbb": {
                "section": "consensus",
                "statement": "公职",
                "rule_ids": ["M1-D-001"],  # M1-D-001 同时被这条断语支撑
                "domain": "事业",
                "year": None,
                "star": 5,
            },
        },
    }
    feedbacks = [
        StatementFeedback("S-001-aaaaaa", "y", "hit"),  # 婚姻 hit
        StatementFeedback("S-001-bbbbbb", "n", "miss"),  # 公职 miss
    ]
    rule_verdicts, unknown = fanout_to_rules(feedbacks, statement_index)
    # M1-D-001 同时被 hit + miss 标注的两条断语支撑 → miss 优先
    assert rule_verdicts["M1-D-001"][0] == "miss", (
        "M1-D-001 应取 miss（决断力优先），实得 "
        f"{rule_verdicts['M1-D-001'][0]}"
    )
    # M2-Y-068 仅被 hit 标注的断语支撑 → hit
    assert rule_verdicts["M2-Y-068"][0] == "hit"
    assert unknown == []

"""六源三领域命理师 Markdown 报告骨架测试。"""

from __future__ import annotations

from dataclasses import replace
from datetime import date, datetime

import pytest

from engine.v5.domain import V5ArbitrationResult, V5Claim, V5Confidence, V5Evidence
from engine.v5.domain_slices.contract import DomainAnalysisRequest
from engine.v5.domain_slices.orchestrator import run_domain_analysis
from engine.v5.domain_analysis_report import render_domain_analysis_report
from tools.output_linter import lint_report_text


def test_report_shows_chart_time_scope_and_explicit_abstentions_without_internal_ids() -> None:
    snapshot = run_domain_analysis(
        DomainAnalysisRequest(
            gender="乾",
            birth_datetime=datetime(1990, 1, 1, 12, 0),
            as_of_date=date(2026, 7, 31),
            output_dir="reports/domain-analysis",
        )
    )

    report = render_domain_analysis_report(snapshot)

    assert "# 六源三领域命理分析报告（乾造）" in report
    assert "己巳｜丙子｜丙寅｜甲午" in report
    assert "## 事业分析" in report
    assert "## 财富分析" in report
    assert "## 婚姻分析" in report
    assert "2026 丙午" in report
    assert "融合判断：**" in report
    assert "目标级裁决状态：" in report
    assert "现实映射状态：NO_MAPPING" in report
    assert "任付红" in report
    assert snapshot.run_id not in report
    assert "claim_id" not in report
    assert "v5cl-" not in report
    assert lint_report_text(report) == []


def test_report_displays_real_high_risk_gate_status_and_manual_review_reason() -> None:
    snapshot = run_domain_analysis(
        DomainAnalysisRequest(
            gender="乾",
            birth_datetime=datetime(1990, 1, 1, 12, 0),
            as_of_date=date(2026, 7, 31),
            domains=("wealth",),
            output_dir="reports/domain-analysis",
        )
    )
    high_risk_claims = [claim for claim in snapshot.claims if claim.metadata.get("high_risk")]
    assert high_risk_claims

    report = render_domain_analysis_report(snapshot)

    assert "高风险门禁：" in report
    assert "需人工复核" in report
    assert "门禁通过不表示现实准确" in report
    assert "门禁状态不可用" not in report


def _claim(
    school: str,
    *,
    claim: str,
    stance: str = "support",
    claim_type: str = "event_claim",
    evidence: str = "命局与岁运形成可核验的作用关系。",
    timing_hints: list[dict[str, object]] | None = None,
    falsifiable: str = "若对应阶段未出现该类变化，则本判断需降权。",
    high_risk: bool = False,
    slice_status: str = "implemented",
) -> V5Claim:
    return V5Claim(
        claim_id=f"v5cl-secret-{school}-{stance}",
        school=school,  # type: ignore[arg-type]
        domain="财富",
        claim=claim,
        claim_type=claim_type,  # type: ignore[arg-type]
        stance=stance,  # type: ignore[arg-type]
        confidence=V5Confidence(tier="★★★★", score=0.78, note="模型证据强度，不是现实概率"),
        evidence=[
            V5Evidence(
                evidence_id=f"v5ev-secret-{school}-{stance}",
                source="internal/source.yaml",
                text=evidence,
                rule_ids=["INTERNAL-RULE-001"],
            )
        ],
        timing_hints=list(timing_hints or []),
        falsifiable=falsifiable,
        metadata={"high_risk": high_risk, "slice_status": slice_status, "task_id": "wealth.debt"},
    )


def test_report_workbench_renders_fused_conclusion_and_six_source_claim_cards() -> None:
    base = run_domain_analysis(
        DomainAnalysisRequest(
            gender="坤",
            birth_datetime=datetime(1990, 1, 1, 12, 0),
            as_of_date=date(2026, 7, 31),
            domains=("wealth",),
            output_dir="reports/domain-analysis",
        )
    )
    claims = [
        _claim("ziping", claim="财务结构以稳定积累为主。"),
        _claim("ditiansui", claim="财气流通但需防阶段性阻滞。", stance="oppose"),
        _claim("gao_dechen", claim="做功可形成收入转化。", high_risk=True),
        _claim("duan_jianye", claim="财富事件存在扩张与回撤并行。"),
        _claim("yang_qingjuan", claim="本派在该领域暂不支持。", stance="abstain", slice_status="unsupported"),
        _claim(
            "ren_fuhong",
            claim="应期验证集中在 2027 年。",
            claim_type="timing_claim",
            timing_hints=[{"start_year": 2027, "end_year": 2028, "label": "财务波动窗口"}],
        ),
    ]
    snapshot = replace(
        base,
        claims=claims,
        arbitration_results=[
            V5ArbitrationResult(
                domain="财富",
                stage="event_realization",
                conclusion="财富以积累为主，但扩张期需控制回撤。",
                conflict_type="direction_conflict",
                confidence=V5Confidence(tier="★★★", score=0.66, note="融合证据强度"),
                rationale="支持与反对命题并存，保留少数意见。",
            )
        ],
    )

    report = render_domain_analysis_report(snapshot)

    assert "目标级裁决状态：未决" in report
    assert "当前不形成唯一主断" in report
    assert "没有已批准的现实指标映射" in report
    assert "融合结论：**同一目标存在支持与反对命题，当前不形成唯一主断。**" in report
    assert "### 六源逐命题工作台" in report
    for school_name in ("子平", "滴天髓", "高德臣", "段建业", "杨清娟", "任付红"):
        assert school_name in report
    assert "判断：财务结构以稳定积累为主。" in report
    assert "证据：命局与岁运形成可核验的作用关系。" in report
    assert "立场：反对" in report
    assert "双轨置信度：★★★★（78%）" in report
    assert "应期：2027—2028（财务波动窗口）" in report
    assert "反证条件：若对应阶段未出现该类变化，则本判断需降权。" in report
    assert "冲突摘要：方向冲突" in report
    assert "暂不支持" in report and "原因：" in report
    assert "时点验证，不参与结构裁决" in report
    assert "需人工复核" in report
    assert "现实概率" not in report
    assert lint_report_text(report) == []


def test_report_does_not_publish_domain_conclusion_when_same_target_is_unresolved() -> None:
    base = run_domain_analysis(
        DomainAnalysisRequest(
            gender="乾",
            birth_datetime=datetime(1990, 1, 1, 12, 0),
            as_of_date=date(2026, 7, 31),
            domains=("wealth",),
        )
    )
    claims = [
        _claim("ziping", claim="财富来源支持经营。", stance="support"),
        _claim("duan_jianye", claim="财富来源反对经营。", stance="oppose"),
    ]
    snapshot = replace(
        base,
        claims=claims,
        arbitration_results=[
            V5ArbitrationResult(
                domain="财富",
                stage="event_realization",
                conclusion="旧汇总不应覆盖未决目标。",
            )
        ],
    )

    report = render_domain_analysis_report(snapshot)

    assert "目标级裁决状态：未决" in report
    assert "当前不形成唯一主断" in report
    assert "旧汇总不应覆盖未决目标" not in report


@pytest.mark.parametrize(
    ("slot", "secret"),
    [
        ("claim", "v5cl-secret-public-text"),
        ("evidence", "v5ev-secret-public-text"),
        ("falsifier", "INTERNAL-RULE-001"),
        ("timing", "statement-123456"),
        ("confidence", "run-domain-secret-001"),
        ("conclusion", "internal/private/source.yaml"),
        ("rationale", "statement_id=secret-001"),
    ],
)
def test_report_rejects_internal_identifiers_in_every_public_text_slot(slot: str, secret: str) -> None:
    base = run_domain_analysis(
        DomainAnalysisRequest(
            gender="乾",
            birth_datetime=datetime(1990, 1, 1, 12, 0),
            as_of_date=date(2026, 7, 31),
            domains=("wealth",),
        )
    )
    claim = _claim(
        "ziping",
        claim=secret if slot == "claim" else "财富判断。",
        evidence=secret if slot == "evidence" else "公开证据。",
        falsifiable=secret if slot == "falsifier" else "若未发生则降权。",
        timing_hints=[{"start_year": 2027, "label": secret if slot == "timing" else "公开窗口"}],
    )
    if slot == "confidence":
        claim = replace(claim, confidence=replace(claim.confidence, note=secret))
    arbitration = V5ArbitrationResult(
        domain="财富",
        stage="event_realization",
        conclusion=secret if slot == "conclusion" else "公开结论。",
        rationale=secret if slot == "rationale" else "公开理由。",
    )
    snapshot = replace(base, claims=[claim], arbitration_results=[arbitration])

    with pytest.raises(ValueError, match="internal|identifier|path|公开文本"):
        render_domain_analysis_report(snapshot)


def test_report_public_text_guard_does_not_reject_normal_chinese() -> None:
    base = run_domain_analysis(
        DomainAnalysisRequest(
            gender="乾",
            birth_datetime=datetime(1990, 1, 1, 12, 0),
            as_of_date=date(2026, 7, 31),
            domains=("wealth",),
        )
    )
    snapshot = replace(
        base,
        claims=[_claim("ziping", claim="财富结构以稳健积累为主。", evidence="命局关系可供后续核验。")],
    )

    assert "财富结构以稳健积累为主。" in render_domain_analysis_report(snapshot)


def test_report_workbench_public_view_does_not_leak_internal_identifiers() -> None:
    base = run_domain_analysis(
        DomainAnalysisRequest(
            gender="乾",
            birth_datetime=datetime(1990, 1, 1, 12, 0),
            as_of_date=date(2026, 7, 31),
            domains=("wealth",),
            output_dir="reports/domain-analysis",
        )
    )
    snapshot = replace(base, claims=[_claim("ziping", claim="财富判断。")])

    report = render_domain_analysis_report(snapshot)

    for secret in (
        "v5cl-secret",
        "v5ev-secret",
        "INTERNAL-RULE-001",
        "internal/source.yaml",
        "claim_id",
        "evidence_id",
        "statement_id",
        "statement_index",
        snapshot.run_id,
    ):
        assert secret not in report

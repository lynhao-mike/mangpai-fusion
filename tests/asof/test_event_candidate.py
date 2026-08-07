from __future__ import annotations

import ast
from datetime import date
from pathlib import Path

import pytest

from engine.asof.event_candidate import (
    AnnualInteractionTrace,
    CompletionMode,
    ExtensionBoundary,
    RootLevel,
    VerificationStatus,
    evaluate_event_candidate,
)
from engine.asof.natal_capacity import EvidenceRef, SourceCitation


CASE_ID = "C-2026-028-乾-壬戌癸卯壬子乙巳"


def _chart(locator: str = "四柱.年柱", excerpt: str = "壬戌") -> EvidenceRef:
    return EvidenceRef(f"cases/{CASE_ID}/input.md", locator, excerpt)


def _citation() -> SourceCitation:
    return SourceCitation(
        "sources/gao/2018弟子班_大运流年篇_55页.md",
        139,
        "大运完成原局未尽组合；后天组合原局无根源力量很小",
    )


def _trace(*, crossed: bool = True) -> AnnualInteractionTrace:
    relation = _chart("2020作用链", "流年—大运—原局权责节点")
    return AnnualInteractionTrace(
        year=2020,
        liunian="庚子",
        dayun_ganzhi="丙寅",
        relations=(relation,) if crossed else (),
        activated_node_ids=("career-authority",) if crossed else (),
        domains=("career",),
        supporting_evidence=(relation,),
        counter_evidence=(),
        trigger_strength="high",
        crossed_candidate_gate=crossed,
    )


def _decision(root: RootLevel, mode: CompletionMode, *, citations: tuple[SourceCitation, ...] | None = None, crossed: bool = True):
    chart = _chart()
    return evaluate_event_candidate(
        candidate_id=f"synthetic-{root.value}-{mode.value}",
        event_type="responsibility_level_change",
        window_start=date(2020, 1, 1),
        window_end=date(2020, 12, 31),
        annual_trace=_trace(crossed=crossed),
        root_level=root,
        completion_mode=mode,
        natal_evidence=(chart,),
        daiyun_evidence=(_chart("大运.排布[4]", "丙寅"),),
        root_evidence=(chart,),
        source_citations=(_citation(),) if citations is None else citations,
        supporting_evidence=(chart,),
        counter_evidence=(_chart("四柱.时柱", "乙巳/伤官"),),
        alternative_hypotheses=("同域同方向的教学权责扩大",),
    )


@pytest.mark.parametrize(
    ("root", "mode", "boundary"),
    (
        (RootLevel.STRONG_ROOT, CompletionMode.ACTIVATE_EXISTING, ExtensionBoundary.CROSS_DAIYUN_ELIGIBLE),
        (RootLevel.STRONG_ROOT, CompletionMode.REPAIR_DEFECT, ExtensionBoundary.CROSS_DAIYUN_ELIGIBLE),
        (RootLevel.WEAK_ROOT, CompletionMode.COMPLETE_LATENT, ExtensionBoundary.REMAINDER_ONLY_RECHECK_CROSS_DAIYUN),
        (RootLevel.WEAK_ROOT, CompletionMode.TEMPORARY_SUBSTITUTE, ExtensionBoundary.REMAINDER_ONLY_RECHECK_CROSS_DAIYUN),
        (RootLevel.NO_ROOT, CompletionMode.TEMPORARY_SUBSTITUTE, ExtensionBoundary.SHORT_TERM_ONLY),
    ),
)
def test_registered_primary_combinations_pass_double_evidence_gate(
    root: RootLevel, mode: CompletionMode, boundary: ExtensionBoundary
) -> None:
    """合成组合矩阵；不是案例 C-2026-028 的真实历史归类。"""
    decision = _decision(root, mode)
    assert decision.accepted is True
    assert decision.reason_code == "CANDIDATE_FROZEN"
    assert decision.candidate is not None
    assert decision.candidate.is_primary_event is True
    assert decision.candidate.verification_status is VerificationStatus.FROZEN
    assert decision.candidate.root_evidence
    assert decision.candidate.source_citations
    assert decision.candidate.extension_boundary is boundary


@pytest.mark.parametrize("root", tuple(RootLevel))
def test_any_root_with_invalid_completion_is_withheld_and_never_primary(root: RootLevel) -> None:
    """合成反证边界；INVALID_COMPLETION 是第六类登记组合。"""
    decision = _decision(root, CompletionMode.INVALID_COMPLETION, crossed=False)
    assert decision.accepted is True
    assert decision.reason_code == "INVALID_COMPLETION_WITHHELD"
    assert decision.candidate is not None
    assert decision.candidate.verification_status is VerificationStatus.WITHHELD
    assert decision.candidate.is_primary_event is False


@pytest.mark.parametrize(
    ("root", "mode", "reason"),
    (
        (RootLevel.NO_ROOT, CompletionMode.ACTIVATE_EXISTING, "LOGICAL_CONTRADICTION_NO_EXISTING_FUNCTION"),
        (RootLevel.NO_ROOT, CompletionMode.COMPLETE_LATENT, "NO_ROOT_CANNOT_COMPLETE_LATENT"),
        (RootLevel.STRONG_ROOT, CompletionMode.COMPLETE_LATENT, "UNREGISTERED_COMBINATION"),
    ),
)
def test_non_whitelist_combinations_are_logically_rejected_without_candidate(
    root: RootLevel, mode: CompletionMode, reason: str
) -> None:
    decision = _decision(root, mode)
    assert decision.accepted is False
    assert decision.reason_code == reason
    assert decision.candidate is None


def test_missing_primary_source_fails_second_evidence_gate() -> None:
    decision = _decision(RootLevel.STRONG_ROOT, CompletionMode.ACTIVATE_EXISTING, citations=())
    assert decision.accepted is False
    assert decision.reason_code == "MISSING_PRIMARY_SOURCE_EVIDENCE"
    assert decision.candidate is None


def test_annual_trace_below_gate_cannot_generate_normal_candidate() -> None:
    decision = _decision(RootLevel.WEAK_ROOT, CompletionMode.TEMPORARY_SUBSTITUTE, crossed=False)
    assert decision.accepted is False
    assert decision.reason_code == "ANNUAL_TRACE_BELOW_CANDIDATE_GATE"
    assert decision.candidate is None


def test_event_candidate_module_has_no_f09_or_reality_backfill_imports() -> None:
    tree = ast.parse(Path("engine/asof/event_candidate.py").read_text(encoding="utf-8"))
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.append(node.module or "")
    assert not [name for name in imported if name.startswith("engine.f09")]
    assert not [name for name in imported if any(token in name for token in ("feedback", "reports", "pipeline"))]

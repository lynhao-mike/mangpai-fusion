from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from engine.asof.hypothesis_state import (
    CompetingHypothesis,
    CompetingHypothesisSet,
    HypothesisCondition,
    apply_verification_result,
    make_competing_hypothesis,
)
from engine.asof.natal_capacity import EvidenceRef
from engine.asof.state_ledger import VerifiedState


def _evidence(locator: str, excerpt: str) -> EvidenceRef:
    return EvidenceRef(
        source="cases/C-2026-RF000900/input.md",
        locator=locator,
        excerpt=excerpt,
    )


def _hypothesis(
    hypothesis_id: str = "H-career-001",
    summary: str = "成长型专业执行岗已形成",
) -> CompetingHypothesis:
    return make_competing_hypothesis(
        hypothesis_id=hypothesis_id,
        domain="career",
        summary=summary,
        activation_trigger="现实核验确认截止日已有持续任职、职责与稳定收入",
        discriminator_question="截止日是否已有持续三个月以上的正式岗位与收入？",
        refutation_condition="截止日没有任职记录、持续收入或实际岗位职责",
        diverges_from_fact_baseline=("职业中心已经形成", "收入来源相对稳定"),
        affected_future_conclusions=("后运从既有职业中心升级，而非从待业状态重建",),
        supporting_evidence=(_evidence("原局.事业", "学习输出与专业执行能力"),),
        counter_evidence=(_evidence("流年.阻滞", "职业兑现受阻信号"),),
    )


def test_competing_hypothesis_is_physically_separate_from_verified_state() -> None:
    assert CompetingHypothesis is not VerifiedState
    assert CompetingHypothesis.__module__ == "engine.asof.hypothesis_state"
    assert VerifiedState.__module__ == "engine.asof.state_ledger"
    assert not issubclass(CompetingHypothesis, VerifiedState)


def test_factory_creates_frozen_unverified_hypothesis() -> None:
    hypothesis = _hypothesis()

    assert hypothesis.verification_status == "UNVERIFIED"
    with pytest.raises(FrozenInstanceError):
        hypothesis.summary = "不得回写"  # type: ignore[misc]


def test_apply_verification_result_returns_new_object_without_mutating_original() -> None:
    original = _hypothesis()

    confirmed = apply_verification_result(original, "CONFIRMED")

    assert confirmed is not original
    assert confirmed.verification_status == "CONFIRMED"
    assert original.verification_status == "UNVERIFIED"
    assert confirmed.summary == original.summary


@pytest.mark.parametrize("result", ("UNVERIFIED", "UNKNOWN", ""))
def test_apply_verification_result_rejects_unsupported_result(result: str) -> None:
    with pytest.raises(ValueError):
        apply_verification_result(_hypothesis(), result)


def test_competing_hypothesis_set_rejects_non_unverified_hypothesis() -> None:
    confirmed = apply_verification_result(_hypothesis(), "CONFIRMED")

    with pytest.raises(ValueError):
        CompetingHypothesisSet(
            hypotheses=(confirmed,),
            created_at_phase="asof-blind-freeze-v1",
            note="与事实快照隔离",
        )


def test_competing_hypothesis_set_rejects_empty_hypotheses() -> None:
    with pytest.raises(ValueError):
        CompetingHypothesisSet(
            hypotheses=(),
            created_at_phase="asof-blind-freeze-v1",
            note="与事实快照隔离",
        )


@pytest.mark.parametrize(
    ("activation_trigger", "discriminator_question", "refutation_condition"),
    (
        ("", "最小问题", "反证条件"),
        ("成立条件", "", "反证条件"),
        ("成立条件", "最小问题", ""),
        ("   ", "最小问题", "反证条件"),
    ),
)
def test_hypothesis_condition_rejects_any_blank_field(
    activation_trigger: str,
    discriminator_question: str,
    refutation_condition: str,
) -> None:
    with pytest.raises(ValueError):
        HypothesisCondition(
            activation_trigger=activation_trigger,
            discriminator_question=discriminator_question,
            refutation_condition=refutation_condition,
        )


def test_competing_hypothesis_rejects_empty_baseline_divergence() -> None:
    with pytest.raises(ValueError):
        make_competing_hypothesis(
            hypothesis_id="H-career-003",
            domain="career",
            summary="无实质差异的候选",
            activation_trigger="若核验成立",
            discriminator_question="是否成立？",
            refutation_condition="若核验不成立",
            diverges_from_fact_baseline=(),
        )


def test_rf000900_competing_hypotheses_can_be_frozen_and_retrieved() -> None:
    formed = _hypothesis()
    unrealized = make_competing_hypothesis(
        hypothesis_id="H-career-002",
        domain="career",
        summary="学习输出能力存在但截止日无业并有债务",
        activation_trigger="现实核验确认截止日无稳定职业、无持续收入且存在债务",
        discriminator_question="截止日是否处于无业状态，并有尚未清偿的债务？",
        refutation_condition="核验确认已有持续任职、稳定收入且不存在债务压力",
        diverges_from_fact_baseline=("职业能力尚未兑现为稳定岗位", "截止日存在无业与债务状态"),
        affected_future_conclusions=("后运先处理生计与债务，再讨论职业成长",),
        supporting_evidence=(_evidence("流年.阻滞", "现实兑现受阻信号"),),
        counter_evidence=(_evidence("原局.事业", "具备学习输出能力"),),
    )
    hypotheses = CompetingHypothesisSet(
        hypotheses=(formed, unrealized),
        created_at_phase="asof-blind-freeze-v1",
        note="竞争假设独立于 VerifiedState，不写入事实快照",
    )

    assert hypotheses.get_unverified() == (formed, unrealized)
    assert hypotheses.get_confirmed() == ()
    assert hypotheses.get_rejected() == ()

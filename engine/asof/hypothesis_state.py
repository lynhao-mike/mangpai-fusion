"""方向级别的未核验竞争假设。

核心文档 plans/as-of-life-state-reasoning-design-2026-07-18.md §5.7 描述的
竞争性人生状态在本模块中命名为 ``CompetingHypothesis``：它表达方向级别的
竞争假设，即截止日基本面存在根本不同的可能，并与 ``VerifiedState`` /
``reality_track`` 保持隔离。

请勿与 ``engine.asof.state_ledger.HypothesisState`` 混淆：本模块的
``CompetingHypothesis`` 是方向级别的竞争假设；后者是基于已有候选的未核验
分支状态。两者语义与字段不同，不可互相替代。

设计约束（来自核心文档 §3.7）：
- 未核验候选可以形成盲断和条件分支，但不得作为既成事实写入稳定人生状态。
- 已否定候选进入反证记录，不得继续影响事实快照。
- ``CompetingHypothesis`` 不得混入事实快照（``VerifiedState``）。

关键区分（防止误用）：
- alternatives（同方向不同类型备选）≠ ``CompetingHypothesis``
  前者是"职业中心已确定方向，但不知道具体是哪类岗位"；
  后者是"截止日基本面本身是否已形成，存在两种根本不同的可能"。
- 本模块只建立 ``CompetingHypothesis`` 对象；何时生成哪些假设，由盲断冻结
  阶段的人工判断决定，本模块不自动推断。
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Protocol

from engine.asof.natal_capacity import EvidenceRef


_VERIFICATION_STATUSES = frozenset({"UNVERIFIED", "CONFIRMED", "REJECTED"})
_FINAL_VERIFICATION_RESULTS = frozenset({"CONFIRMED", "REJECTED"})


class HypothesisEvidenceSignal(Protocol):
    """假设构造阶段允许读取的最小证据信号表面。

    协议仅描述可审计证据的形状，不赋予任何事实状态语义，也不允许把
    ``VerifiedState`` 或 ``reality_track`` 适配为竞争假设。
    """

    source: str
    locator: str
    excerpt: str


@dataclass(frozen=True, slots=True)
class HypothesisCondition:
    """单个假设分支的成立条件与消歧信息。"""

    activation_trigger: str
    discriminator_question: str
    refutation_condition: str

    def __post_init__(self) -> None:
        if not all(
            (
                self.activation_trigger.strip(),
                self.discriminator_question.strip(),
                self.refutation_condition.strip(),
            )
        ):
            raise ValueError("hypothesis condition requires trigger, discriminator and refutation")


@dataclass(frozen=True, slots=True)
class CompetingHypothesis:
    """未核验的方向级别竞争假设；不得混入事实快照。

    表达"若重大候选成立，命主截止日的基本面将是什么"。每个竞争假设对应
    一条与事实主线（或另一假设分支）存在实质性差异的竞争性状态。
    """

    hypothesis_id: str
    domain: str
    summary: str
    condition: HypothesisCondition
    diverges_from_fact_baseline: tuple[str, ...]
    affected_future_conclusions: tuple[str, ...]
    supporting_evidence: tuple[EvidenceRef, ...]
    counter_evidence: tuple[EvidenceRef, ...]
    verification_status: str

    def __post_init__(self) -> None:
        if not all((self.hypothesis_id.strip(), self.domain.strip(), self.summary.strip())):
            raise ValueError("hypothesis requires identity, domain and summary")
        if not isinstance(self.condition, HypothesisCondition):
            raise ValueError("hypothesis requires a structured condition")
        if self.verification_status not in _VERIFICATION_STATUSES:
            raise ValueError("unsupported hypothesis verification status")
        if not self.diverges_from_fact_baseline:
            raise ValueError("hypothesis requires at least one fact-baseline divergence")


@dataclass(frozen=True, slots=True)
class CompetingHypothesisSet:
    """与同一事实主线竞争的全部假设集合。

    不得包含事实主线本身；所有假设的 verification_status 在冻结时均为
    'UNVERIFIED'，反馈揭示后才能更新（通过创建新对象，不得回写）。
    """

    hypotheses: tuple[CompetingHypothesis, ...]
    created_at_phase: str
    note: str

    def __post_init__(self) -> None:
        if not self.hypotheses:
            raise ValueError("hypothesis set requires at least one hypothesis")
        if any(hypothesis.verification_status != "UNVERIFIED" for hypothesis in self.hypotheses):
            raise ValueError("frozen hypothesis set only accepts unverified hypotheses")

    def get_unverified(self) -> tuple[CompetingHypothesis, ...]:
        """返回尚未核验的竞争假设。"""

        return tuple(item for item in self.hypotheses if item.verification_status == "UNVERIFIED")

    def get_confirmed(self) -> tuple[CompetingHypothesis, ...]:
        """返回已确认假设；冻结集合在创建时该结果必为空。"""

        return tuple(item for item in self.hypotheses if item.verification_status == "CONFIRMED")

    def get_rejected(self) -> tuple[CompetingHypothesis, ...]:
        """返回已否定假设；冻结集合在创建时该结果必为空。"""

        return tuple(item for item in self.hypotheses if item.verification_status == "REJECTED")


def make_competing_hypothesis(
    hypothesis_id: str,
    domain: str,
    summary: str,
    activation_trigger: str,
    discriminator_question: str,
    refutation_condition: str,
    diverges_from_fact_baseline: tuple[str, ...],
    affected_future_conclusions: tuple[str, ...] = (),
    supporting_evidence: tuple[EvidenceRef, ...] = (),
    counter_evidence: tuple[EvidenceRef, ...] = (),
) -> CompetingHypothesis:
    """创建一个处于 UNVERIFIED 状态的竞争性假设。

    所有假设在创建时均为 UNVERIFIED；核验结果通过 apply_verification_result()
    生成新对象，不回写。
    """

    return CompetingHypothesis(
        hypothesis_id=hypothesis_id,
        domain=domain,
        summary=summary,
        condition=HypothesisCondition(
            activation_trigger=activation_trigger,
            discriminator_question=discriminator_question,
            refutation_condition=refutation_condition,
        ),
        diverges_from_fact_baseline=diverges_from_fact_baseline,
        affected_future_conclusions=affected_future_conclusions,
        supporting_evidence=supporting_evidence,
        counter_evidence=counter_evidence,
        verification_status="UNVERIFIED",
    )


def apply_verification_result(
    hypothesis: CompetingHypothesis,
    result: str,
) -> CompetingHypothesis:
    """返回验证结果已更新的新假设对象；不修改原对象。"""

    if result not in _FINAL_VERIFICATION_RESULTS:
        raise ValueError("verification result must be CONFIRMED or REJECTED")
    return replace(hypothesis, verification_status=result)


__all__ = (
    "CompetingHypothesis",
    "CompetingHypothesisSet",
    "HypothesisCondition",
    "HypothesisEvidenceSignal",
    "apply_verification_result",
    "make_competing_hypothesis",
)

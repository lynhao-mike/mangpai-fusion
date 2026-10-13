from __future__ import annotations

import pytest

from engine.asof.reality_translation import (
    ConditionalBranch,
    FrozenLandingSet,
    LandingPoint,
    LandingVerdict,
    RealityConstraint,
    select_output_branches,
    translate_landing,
    verify_landing,
)


def _point(name: str, *, domain: str = "career", direction: str = "authority_up") -> LandingPoint:
    return LandingPoint(name, domain, direction)


def _frozen(*alternatives: LandingPoint) -> FrozenLandingSet:
    return FrozenLandingSet(
        function_candidate="权责上升",
        center=_point("组织内升迁"),
        alternatives=alternatives or (_point("团队权责扩大"), _point("平台资质上升")),
        weak_hit_boundary="仅职称变化且权责未扩大属于弱命中",
        falsifiers=("职责与平台均未变化",),
        exclusions=("财富增长", "感情事件"),
        frozen_version="landing-v1-before-outcome",
    )


def test_freeze_requires_one_center_and_at_most_two_same_function_alternatives() -> None:
    frozen = _frozen()
    assert frozen.center.name == "组织内升迁"
    assert len(frozen.alternatives) == 2

    with pytest.raises(ValueError):
        _frozen(_point("团队权责扩大"), _point("平台资质上升"), _point("经营组织化"))
    with pytest.raises(ValueError):
        _frozen(_point("财富增长", domain="wealth", direction="wealth_up"))
    with pytest.raises(ValueError):
        _frozen(_point("职责下降", direction="authority_down"))


def test_reachable_center_is_retained_without_translation() -> None:
    decision = translate_landing(_frozen())
    assert decision.reason_code == "CENTER_REACHABLE"
    assert decision.selected_landing == _point("组织内升迁")
    assert decision.closed_original_landing is None


def test_unverified_reality_constraint_cannot_translate() -> None:
    constraint = RealityConstraint(
        state_id="state-startup",
        description="声称创业但尚未核验",
        closed_landing_names=("组织内升迁",),
        reachable_landing_names=("团队权责扩大",),
        verified=False,
    )
    decision = translate_landing(_frozen(), constraint=constraint)
    assert decision.selected_landing is None
    assert decision.reason_code == "UNVERIFIED_CONSTRAINT_CANNOT_TRANSLATE"


def test_verified_constraint_selects_only_reachable_frozen_alternative() -> None:
    constraint = RealityConstraint(
        state_id="state-startup-confirmed",
        description="已核验创业且原雇佣路径关闭",
        closed_landing_names=("组织内升迁",),
        reachable_landing_names=("平台资质上升",),
        verified=True,
    )
    decision = translate_landing(_frozen(), constraint=constraint)
    assert decision.original_function_candidate == "权责上升"
    assert decision.closed_original_landing == "组织内升迁"
    assert decision.triggering_constraint_id == "state-startup-confirmed"
    assert decision.selected_landing == _point("平台资质上升")
    assert decision.reason_code == "FROZEN_ALTERNATIVE_SELECTED"


def test_no_legal_frozen_alternative_abstains_instead_of_inventing_landing() -> None:
    constraint = RealityConstraint(
        state_id="state-path-closed",
        description="原组织路径关闭",
        closed_landing_names=("组织内升迁",),
        reachable_landing_names=("核验后才想到的新落点",),
        verified=True,
    )
    decision = translate_landing(_frozen(), constraint=constraint)
    assert decision.selected_landing is None
    assert decision.reason_code == "NO_LEGAL_FROZEN_ALTERNATIVE"


@pytest.mark.parametrize(
    ("actual", "verdict"),
    (
        (_point("组织内升迁"), LandingVerdict.CENTER_HIT),
        (_point("团队权责扩大"), LandingVerdict.ALTERNATIVE_HIT),
    ),
)
def test_only_pre_frozen_center_or_alternative_counts_as_hit(
    actual: LandingPoint,
    verdict: LandingVerdict,
) -> None:
    verification = verify_landing(_frozen(), actual=actual)
    assert verification.verdict is verdict
    assert verification.frozen_landing_name == actual.name


def test_post_outcome_new_landing_never_counts_as_hit_and_can_be_taxonomy_gap() -> None:
    """核验后新增落点不得回写 landing-v1-before-outcome 或计作命中。"""
    actual = _point("经营组织化")
    constraint = RealityConstraint(
        state_id="state-startup-confirmed",
        description="已核验创业且原雇佣路径关闭",
        closed_landing_names=("组织内升迁",),
        reachable_landing_names=("经营组织化",),
        verified=True,
    )
    frozen = _frozen()
    verification = verify_landing(
        frozen,
        actual=actual,
        explicit_constraint=constraint,
        taxonomy_evidence=("原始语料定位", "命盘结构依据", "案例事实依据"),
    )
    assert verification.verdict is LandingVerdict.TAXONOMY_GAP
    assert verification.frozen_landing_name is None
    assert actual not in frozen.alternatives
    assert frozen.frozen_version == "landing-v1-before-outcome"


@pytest.mark.parametrize(
    ("actual", "constraint", "evidence"),
    (
        (_point("收入增长", domain="wealth", direction="wealth_up"), True, ("语料", "结构", "案例")),
        (_point("职责下降", direction="authority_down"), True, ("语料", "结构", "案例")),
        (_point("经营组织化"), False, ("语料", "结构", "案例")),
        (_point("经营组织化"), True, ()),
    ),
)
def test_taxonomy_gap_requires_same_domain_direction_verified_constraint_and_evidence(
    actual: LandingPoint,
    constraint: bool,
    evidence: tuple[str, ...],
) -> None:
    reality_constraint = RealityConstraint(
        state_id="state-constraint",
        description="现实路径约束",
        closed_landing_names=("组织内升迁",),
        reachable_landing_names=(actual.name,),
        verified=constraint,
    )
    verification = verify_landing(
        _frozen(),
        actual=actual,
        explicit_constraint=reality_constraint,
        taxonomy_evidence=evidence,
    )
    assert verification.verdict is LandingVerdict.MISS


def test_internal_branches_are_preserved_but_output_is_stably_pruned_to_two() -> None:
    branches = (
        ConditionalBranch("branch-low", 1, 4, "是否发生？"),
        ConditionalBranch("branch-best", 3, 4, "是否已正式任命？"),
        ConditionalBranch("branch-second", 3, 3, "原路径是否关闭？"),
        ConditionalBranch("branch-third", 2, 4, "收入是否随职责变化？"),
    )
    selected = select_output_branches(branches)
    assert len(branches) == 4
    assert tuple(branch.branch_id for branch in selected) == ("branch-best", "branch-second")
    assert len(selected) <= 2

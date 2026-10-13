from __future__ import annotations

from engine.predicates.ten_god_structures import (
    StructurePhase,
    TenGodStructureKind,
    assess_ten_god_structure,
)
from engine.predicates.types import Bazi, Dayun, DayunStep, GanZhi, ParsedInput


def _parsed(chart: str, dayun: tuple[tuple[str, int, int], ...]) -> ParsedInput:
    pillars = tuple(GanZhi.parse(chart[index : index + 2]) for index in range(0, 8, 2))
    steps = [
        DayunStep(
            序号=index,
            干支=GanZhi.parse(ganzhi),
            起岁=start - 1980,
            止岁=end - 1981,
            起讫年=(start, end),
        )
        for index, (ganzhi, start, end) in enumerate(dayun, start=1)
    ]
    return ParsedInput(
        case_id="TEST-TEN-GOD-STRUCTURE",
        bazi=Bazi(
            年柱=pillars[0],
            月柱=pillars[1],
            日柱=pillars[2],
            时柱=pillars[3],
        ),
        dayun=Dayun(起运岁=8.0, 起运年=1988, 顺逆="顺", 排布=steps),
        birth={"year": 1980},
    )


def test_food_god_controls_killing_when_both_sides_are_rooted_and_balanced() -> None:
    parsed = _parsed("戊辰庚申甲寅丙寅", (("己酉", 2000, 2010),))

    assessment = assess_ten_god_structure(
        parsed,
        TenGodStructureKind.FOOD_GOD_CONTROLS_KILLING,
    )

    assert assessment.natal.phase is StructurePhase.NATAL_ESTABLISHED
    assert not assessment.natal.blockers


def test_ten_god_coexistence_does_not_prove_food_god_controls_killing() -> None:
    parsed = _parsed("庚申庚申甲子戊寅", (("己酉", 2000, 2010),))

    assessment = assess_ten_god_structure(
        parsed,
        TenGodStructureKind.FOOD_GOD_CONTROLS_KILLING,
    )

    assert assessment.natal.phase is StructurePhase.LATENT
    assert "食神力量不足，尚未形成有效制杀" in assessment.natal.blockers


def test_pianyin_disrupts_food_god_control_instead_of_counting_as_control() -> None:
    parsed = _parsed("壬申庚申甲寅丙寅", (("己酉", 2000, 2010),))

    assessment = assess_ten_god_structure(
        parsed,
        TenGodStructureKind.FOOD_GOD_CONTROLS_KILLING,
    )

    assert assessment.natal.phase is StructurePhase.DISRUPTED
    assert "枭神夺食" in assessment.natal.blockers


def test_food_hurting_officer_and_seal_structures_are_not_conflated() -> None:
    parsed = _parsed("戊辰庚申甲寅丙寅", (("己酉", 2000, 2010),))

    food = assess_ten_god_structure(
        parsed,
        TenGodStructureKind.FOOD_GOD_CONTROLS_KILLING,
    )
    hurting = assess_ten_god_structure(
        parsed,
        TenGodStructureKind.HURTING_OFFICER_CONTROLS_KILLING,
    )
    seal = assess_ten_god_structure(
        parsed,
        TenGodStructureKind.KILLING_GENERATES_SEAL,
    )

    assert food.natal.phase is StructurePhase.NATAL_ESTABLISHED
    assert hurting.natal.phase is StructurePhase.ABSENT
    assert seal.natal.phase is not StructurePhase.NATAL_ESTABLISHED


def test_hurting_officer_controls_killing_is_assessed_independently() -> None:
    parsed = _parsed("戊辰庚申甲寅丁卯", (("己酉", 2000, 2010),))

    hurting = assess_ten_god_structure(
        parsed,
        TenGodStructureKind.HURTING_OFFICER_CONTROLS_KILLING,
    )
    food = assess_ten_god_structure(
        parsed,
        TenGodStructureKind.FOOD_GOD_CONTROLS_KILLING,
    )

    assert hurting.natal.phase is StructurePhase.NATAL_ESTABLISHED
    assert food.natal.phase is StructurePhase.LATENT


def test_killing_generates_seal_counts_the_seal_as_body_support() -> None:
    parsed = _parsed("壬子庚申甲子癸酉", (("己酉", 2000, 2010),))

    assessment = assess_ten_god_structure(
        parsed,
        TenGodStructureKind.KILLING_GENERATES_SEAL,
    )

    assert assessment.natal.phase is StructurePhase.NATAL_ESTABLISHED


def test_dayun_can_complete_a_structure_missing_from_the_natal_chart() -> None:
    parsed = _parsed("戊辰庚申甲子戊辰", (("丙寅", 2000, 2010),))

    assessment = assess_ten_god_structure(
        parsed,
        TenGodStructureKind.FOOD_GOD_CONTROLS_KILLING,
    )

    assert assessment.natal.phase is StructurePhase.ABSENT
    assert assessment.dayun[0].phase is StructurePhase.DAYUN_COMPLETED
    assert "大运补入食神" in assessment.dayun[0].evidence


def test_dayun_evidence_records_partial_strength_that_completes_natal_signal() -> None:
    parsed = _parsed("戊辰庚申甲寅戊寅", (("甲寅", 2000, 2010),))

    assessment = assess_ten_god_structure(
        parsed,
        TenGodStructureKind.FOOD_GOD_CONTROLS_KILLING,
    )

    assert assessment.natal.phase is StructurePhase.LATENT
    assert assessment.dayun[0].phase is StructurePhase.DAYUN_COMPLETED
    assert "大运补入食神" in assessment.dayun[0].evidence


def test_liunian_is_evaluated_inside_its_dayun_and_can_activate_structure() -> None:
    parsed = _parsed("戊辰庚申甲子戊辰", (("甲寅", 2020, 2030),))

    assessment = assess_ten_god_structure(
        parsed,
        TenGodStructureKind.FOOD_GOD_CONTROLS_KILLING,
        target_year=2026,
    )

    assert assessment.dayun[0].phase is StructurePhase.LATENT
    assert assessment.liunian is not None
    assert assessment.liunian.ganzhi == GanZhi.parse("丙午")
    assert assessment.liunian.phase is StructurePhase.LIUNIAN_ACTIVATED
    assert "流年补入食神" in assessment.liunian.evidence


def test_liunian_is_not_inferred_when_target_year_is_omitted() -> None:
    parsed = _parsed("戊辰庚申甲子戊辰", (("甲寅", 2020, 2030),))

    assessment = assess_ten_god_structure(
        parsed,
        TenGodStructureKind.FOOD_GOD_CONTROLS_KILLING,
    )

    assert assessment.liunian is None


def test_liunian_is_not_forced_into_dayun_outside_arranged_years() -> None:
    parsed = _parsed("戊辰庚申甲子戊辰", (("甲寅", 2020, 2030),))

    assessment = assess_ten_god_structure(
        parsed,
        TenGodStructureKind.FOOD_GOD_CONTROLS_KILLING,
        target_year=2035,
    )

    assert assessment.liunian is None


def test_liunian_clash_can_disrupt_a_natal_controller() -> None:
    parsed = _parsed("戊辰辛酉乙卯丙午", (("己丑", 2015, 2025),))

    assessment = assess_ten_god_structure(
        parsed,
        TenGodStructureKind.FOOD_GOD_CONTROLS_KILLING,
        target_year=2020,
    )

    assert assessment.natal.phase is StructurePhase.NATAL_ESTABLISHED
    assert assessment.liunian is not None
    assert assessment.liunian.phase is StructurePhase.DISRUPTED
    assert "流年子冲原局时支午，食神受损" in assessment.liunian.interactions


def test_liunian_clash_removes_body_support_supplied_by_dayun() -> None:
    parsed = _parsed("戊戌庚午甲戌戊辰", (("丙寅", 2025, 2035),))

    assessment = assess_ten_god_structure(
        parsed,
        TenGodStructureKind.FOOD_GOD_CONTROLS_KILLING,
        target_year=2028,
    )

    assert assessment.dayun[0].phase is StructurePhase.DAYUN_COMPLETED
    assert assessment.liunian is not None
    assert assessment.liunian.phase is StructurePhase.LATENT
    assert "流年申冲大运支寅，比肩受损" in assessment.liunian.interactions

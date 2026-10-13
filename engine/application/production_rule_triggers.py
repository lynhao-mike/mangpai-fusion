from __future__ import annotations

from engine.application.production_rule_models import ProductionRule
from engine.energy.types import EnergyFindings
from engine.picture.types import PictureFindings
from engine.predicates.palace import find_shishen_in_bazi
from engine.predicates.relations import zhi_chong
from engine.predicates.shensha import has_shensha
from engine.predicates.ten_god_structures import (
    StructurePhase,
    TenGodStructureKind,
    assess_ten_god_structure,
)
from engine.predicates.types import (
    GAN_TO_WUXING,
    ZHI_TO_WUXING,
    Gan,
    PalaceName,
    ParsedInput,
    Shishen,
    Zhi,
)


def rule_triggered(
    rule: ProductionRule,
    *,
    parsed: ParsedInput | None,
    energy: EnergyFindings,
    picture: PictureFindings,
) -> bool:
    trigger = rule.conditions.trigger
    if trigger == "always":
        return parsed is not None
    if trigger == "has_wealth_picture":
        return bool(getattr(picture, "caifu", None) or getattr(picture, "wealth_level", None))
    if trigger == "has_official_picture":
        return bool(getattr(picture, "guanming", None))
    if trigger == "has_marriage_picture":
        return bool(getattr(picture, "marriage_picture", None))
    if trigger == "has_tiaohou_advice":
        return bool(getattr(picture, "tiaohou_advice", None))
    if trigger == "wuxing_imbalanced":
        return _is_wuxing_imbalanced(parsed)
    if trigger == "has_zhi_chong":
        return _has_zhi_chong(parsed)
    if trigger == "has_energy_structure":
        return bool(
            getattr(energy, "tiyong", None)
            and getattr(energy, "layer_count", 0) >= 1
        )
    if trigger in ("has_dayun", "has_xiaoyun"):
        return parsed is not None and bool(parsed.dayun.排布)
    if trigger in ("has_liunian", "has_suiyun_interaction"):
        return parsed is not None
    if trigger == "has_sanhe_partial":
        return parsed is not None and (
            has_shensha("三合", parsed) or has_shensha("半三合", parsed)
        )
    if trigger == "has_sanxing":
        return parsed is not None and has_shensha("三刑", parsed)
    if trigger == "has_kongwang":
        return parsed is not None and has_shensha("空亡", parsed)
    if trigger == "has_zaisha":
        return parsed is not None and has_shensha("灾煞", parsed)
    if trigger == "has_goujiao":
        return parsed is not None and (
            has_shensha("勾绞", parsed) or has_shensha("绞煞", parsed)
        )
    if trigger == "has_guchen_guasu":
        return parsed is not None and (
            has_shensha("孤辰", parsed) or has_shensha("寡宿", parsed)
        )
    if trigger == "has_tianluodiwang":
        return parsed is not None and (
            has_shensha("天罗", parsed) or has_shensha("地网", parsed)
        )
    if trigger == "has_shie_dabai":
        return parsed is not None and has_shensha("十恶大败", parsed)
    if trigger == "has_qisha_with_control":
        return _has_qisha_with_control(parsed)
    if trigger == "has_food_god_controls_qisha":
        return _has_qisha_structure(
            parsed,
            TenGodStructureKind.FOOD_GOD_CONTROLS_KILLING,
        )
    if trigger == "has_hurting_officer_controls_qisha":
        return _has_qisha_structure(
            parsed,
            TenGodStructureKind.HURTING_OFFICER_CONTROLS_KILLING,
        )
    if trigger == "has_qisha_generates_seal":
        return _has_qisha_structure(
            parsed,
            TenGodStructureKind.KILLING_GENERATES_SEAL,
        )
    if trigger == "has_hour_qisha":
        return _has_hour_qisha(parsed)
    if trigger == "has_guansha_mixed":
        return _has_guansha_mixed(parsed)
    if trigger == "has_yi_day_bingzi_hour":
        return (
            parsed is not None
            and parsed.bazi.日柱.gan == "乙"
            and parsed.bazi.时柱.gan == "丙"
            and parsed.bazi.时柱.zhi == "子"
        )
    if trigger == "has_xin_day_wuzi_hour":
        return (
            parsed is not None
            and parsed.bazi.日柱.gan == "辛"
            and parsed.bazi.时柱.gan == "戊"
            and parsed.bazi.时柱.zhi == "子"
        )
    if trigger in (
        "child_chart_health_assessment",
        "child_chart_guansha",
        "liuqin_star_location_assessment",
        "spouse_star_location_assessment",
        "children_star_location_assessment",
        "female_chart_spouse_children_assessment",
    ):
        return parsed is not None
    return False


def _shishen_locations(
    parsed: ParsedInput | None,
    shishen: Shishen,
) -> tuple[tuple[PalaceName, Gan | Zhi], ...]:
    if parsed is None:
        return ()
    return tuple(find_shishen_in_bazi(shishen, parsed.bazi))


def _has_shishen(parsed: ParsedInput | None, *shishens: Shishen) -> bool:
    return any(_shishen_locations(parsed, shishen) for shishen in shishens)


def _has_qisha_with_control(parsed: ParsedInput | None) -> bool:
    return any(_has_qisha_structure(parsed, kind) for kind in TenGodStructureKind)


def _has_qisha_structure(
    parsed: ParsedInput | None,
    kind: TenGodStructureKind,
) -> bool:
    if parsed is None:
        return False
    assessment = assess_ten_god_structure(parsed, kind)
    return assessment.natal.phase is StructurePhase.NATAL_ESTABLISHED


def _has_hour_qisha(parsed: ParsedInput | None) -> bool:
    return any(
        location in {"时柱", "时支"}
        for location, _ in _shishen_locations(parsed, "七杀")
    )


def _has_guansha_mixed(parsed: ParsedInput | None) -> bool:
    return _has_shishen(parsed, "正官") and _has_shishen(parsed, "七杀")


def _is_wuxing_imbalanced(parsed: ParsedInput | None) -> bool:
    if parsed is None:
        return False
    counts = {"木": 0, "火": 0, "土": 0, "金": 0, "水": 0}
    for _, gan in parsed.bazi.all_gans():
        wuxing = GAN_TO_WUXING.get(gan)
        if wuxing:
            counts[wuxing] += 1
    for _, zhi in parsed.bazi.all_zhis():
        wuxing = ZHI_TO_WUXING.get(zhi)
        if wuxing:
            counts[wuxing] += 1
    values = list(counts.values())
    return max(values) - min(values) >= 2 or any(value == 0 for value in values)


def _has_zhi_chong(parsed: ParsedInput | None) -> bool:
    if parsed is None:
        return False
    zhis = [zhi for _, zhi in parsed.bazi.all_zhis()]
    return any(
        zhi_chong(left, right)
        for index, left in enumerate(zhis)
        for right in zhis[index + 1 :]
    )

"""engine/yingqi · v1.2 D3 任派应期三层门引擎

v1.2 灵魂条款（04-gate-protocol.md）：
    "原局有 + 大运到位 + 流年引爆 = 三层齐备 → 铁口断 ★★★★★"

主入口：
    from engine.yingqi import gate_yingqi

    result = gate_yingqi(
        year=2005, candidate_event="结婚", domain="婚姻",
        energy=energy_findings, picture=picture_findings, parsed=parsed_input,
    )
    if result.passed_layers == 3:
        # ★★★★★ 铁断
        ...

模块结构（08 § 二 Track-C 可写区）：
    types        - GateResult / LayerCheck / TriggerEvent / Door
    keys         - domain → 关键字映射
    threelayer   - L1/L2/L3 三层判定
    chufa        - 6 触发引擎
    menshu       - 12 道门分类
    gate         - gate_yingqi 主入口（含 picture 钳制 + confidence）

作者：Track-C
"""

from engine.yingqi.types import (  # noqa: F401
    DoorType,
    Domain,
    GateLayer,
    GateResult,
    LayerCheck,
    PASSED_LAYERS_TO_STAR_CEILING,
    TRIGGER_PRIORITY,
    TriggerEvent,
    TriggerType,
)

from engine.yingqi.keys import (  # noqa: F401
    chars_in_yuanju,
    get_primary_keys,
    get_required_dayun_chars,
    get_secondary_keys,
    infer_sub_domain,
)

from engine.yingqi.threelayer import (  # noqa: F401
    layer1_check,
    layer2_check,
    layer3_check,
)

from engine.yingqi.chufa import (  # noqa: F401
    detect_all_triggers,
    detect_benzi_dao,
    detect_canggan_tou,
    detect_daoxiang,
    detect_fuyin,
    detect_hechong,
    detect_muku,
    pick_primary_trigger,
)

from engine.yingqi.menshu import (  # noqa: F401
    classify_into_12_doors,
    debug_all_door_matches,
)

from engine.yingqi.gate import (  # noqa: F401
    check_against_energy,
    check_against_picture,
    compute_yingqi_confidence,
    gate_yingqi,
)


__all__ = [
    # 类型（types.py）
    "GateResult", "LayerCheck", "TriggerEvent",
    "TriggerType", "DoorType", "GateLayer", "Domain",
    "PASSED_LAYERS_TO_STAR_CEILING", "TRIGGER_PRIORITY",
    # 关键字（keys.py）
    "get_primary_keys", "get_secondary_keys", "get_required_dayun_chars",
    "infer_sub_domain", "chars_in_yuanju",
    # 三层（threelayer.py）
    "layer1_check", "layer2_check", "layer3_check",
    # 6 触发（chufa.py）
    "detect_all_triggers", "pick_primary_trigger",
    "detect_benzi_dao", "detect_fuyin", "detect_hechong",
    "detect_muku", "detect_canggan_tou", "detect_daoxiang",
    # 12 道门（menshu.py）
    "classify_into_12_doors", "debug_all_door_matches",
    # 主入口（gate.py）
    "gate_yingqi", "compute_yingqi_confidence",
    "check_against_energy", "check_against_picture",
]

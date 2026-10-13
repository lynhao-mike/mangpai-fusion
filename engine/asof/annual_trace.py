"""逐年力量场到 as-of 年度作用轨迹的隔离适配层。

L1/L2 集成边界：当前 ``layer1_check``/``layer2_check`` 不需要候选事件文本，
但需要 ``domain`` 和完整 ``ParsedInput``；L2 还需要年份，并通过完整大运排布、
出生年与起运信息自行定位大运，不能只接收 ``bazi`` + 单个 ``dayun_gz``。
因此本模块不伪造缺失上下文，也不提供会产生错误门判定的升级适配器。调用方若有
完整 ``ParsedInput``、领域和年份，可先调用两层检查，再把裁决结果通过
``adapt_flow_year_energy(crossed_candidate_gate=True)`` 显式传入。
"""
from __future__ import annotations

import inspect
from typing import Protocol

from engine.asof.event_candidate import AnnualInteractionTrace
from engine.asof.natal_capacity import EvidenceRef
from engine.predicates.types import ParsedInput
from engine.yingqi.retrospective import scan_retrospective
from engine.yingqi.threelayer import layer1_check, layer2_check


class FlowYearEnergySignal(Protocol):
    """只声明允许从既有 ``FlowYearEnergy`` 消费的结构信号表面。

    这些字段描述逐年力量场，不包含现实事件后果，也不等同于候选证据门裁决。
    """

    year: int
    liunian: str
    dayun: str
    relations: list[str]
    main_energy: str
    strength: str
    domains: list[str]


NatalNode = tuple[str, str, str]
_STRENGTH_MAP = {"▲": "high", "●": "medium", "▽": "low"}
_SOURCE = "engine.yingqi.retrospective.FlowYearEnergy"


def probe_layer_gate_compatibility() -> dict[str, object]:
    """只读检查 L1/L2 是否可由 ``bazi`` + 单个 ``dayun_gz`` 直接调用。

    返回真实必需参数及缺失的语义输入；不执行门函数，也不构造或修改命盘数据。
    ``energy`` 虽是 L2 的必需形参，但其类型允许传 ``None``，故不视为 as-of
    阶段缺失的数据。结果同时明确当前 API 不依赖 ``candidate_event``。
    """

    from engine.yingqi.threelayer import layer1_check, layer2_check

    def required_parameters(function: object) -> tuple[str, ...]:
        signature = inspect.signature(function)
        return tuple(
            name
            for name, parameter in signature.parameters.items()
            if parameter.default is inspect.Parameter.empty
            and parameter.kind
            not in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)
        )

    layer1_required = required_parameters(layer1_check)
    layer2_required = required_parameters(layer2_check)
    all_parameters = set(inspect.signature(layer1_check).parameters)
    all_parameters.update(inspect.signature(layer2_check).parameters)
    missing_inputs = tuple(
        name
        for name in ("domain", "parsed", "year")
        if name in all_parameters
    )

    return {
        "layer1_required_parameters": layer1_required,
        "layer2_required_parameters": layer2_required,
        "requires_candidate_event": "candidate_event" in all_parameters,
        "compatible_with_bazi_dayun_only": not missing_inputs,
        "missing_inputs": missing_inputs,
    }


def _activated_node_ids(
    relations: list[str],
    natal_nodes: tuple[NatalNode, ...],
) -> tuple[str, ...]:
    """按“柱位标签+本字”精确词元识别被触发的原局节点。

    ``natal_nodes`` 每项为 ``(node_id, label, char)``。仅当关系描述包含由既有
    扫描器生成的完整词元（例如 ``日支子``、``月干乙`` 或伏吟格式
    ``月支(寅)``）时才命中；不以单个干支字符做模糊匹配，因而同字出现在多柱时
    不会误激活其他柱。输出遵循原局年、月、日、时及干、支的输入顺序并去重。
    """

    activated: list[str] = []
    for node_id, label, char in natal_nodes:
        plain_token = f"{label}{char}"
        parenthesized_token = f"{label}({char})"
        if any(plain_token in relation or parenthesized_token in relation for relation in relations):
            if node_id not in activated:
                activated.append(node_id)
    return tuple(activated)


def adapt_flow_year_energy(
    signal: FlowYearEnergySignal,
    *,
    natal_nodes: tuple[NatalNode, ...],
    crossed_candidate_gate: bool = False,
    counter_evidence: tuple[EvidenceRef, ...] = (),
) -> AnnualInteractionTrace:
    """把既有逐年力量场适配为独立 ``AnnualInteractionTrace``。

    ``strength`` 仅按 ``▲/●/▽`` 映射为 ``high/medium/low``；关系为空时无论旧
    强度为何都降为 ``low``。旧力量场明确“不下应期铁断”，所以本函数绝不根据
    强度自动越门：``crossed_candidate_gate`` 默认 ``False``，只有调用方显式
    裁决为真、且适配后同时存在作用关系与被精确识别的原局节点时才保留为真。
    这使候选门裁决与自由文本/粗粒度结构强度保持隔离并可审计。
    """

    relation_refs = tuple(
        EvidenceRef(
            source=_SOURCE,
            locator=f"year[{signal.year}].relations[{index}]",
            excerpt=relation,
        )
        for index, relation in enumerate(signal.relations)
        if relation.strip()
    )
    relation_texts = [ref.excerpt for ref in relation_refs]
    activated = _activated_node_ids(relation_texts, natal_nodes)
    strength = _STRENGTH_MAP.get(signal.strength, "low") if relation_refs else "low"
    crossed = bool(crossed_candidate_gate and relation_refs and activated)

    supporting: list[EvidenceRef] = []
    if signal.main_energy.strip():
        supporting.append(
            EvidenceRef(
                source=_SOURCE,
                locator=f"year[{signal.year}].main_energy",
                excerpt=signal.main_energy,
            )
        )
    supporting.append(
        EvidenceRef(
            source=_SOURCE,
            locator=f"year[{signal.year}].strength",
            excerpt=signal.strength,
        )
    )

    return AnnualInteractionTrace(
        year=signal.year,
        liunian=signal.liunian,
        dayun_ganzhi=signal.dayun,
        relations=relation_refs,
        activated_node_ids=activated,
        domains=tuple(dict.fromkeys(signal.domains)),
        supporting_evidence=tuple(supporting),
        counter_evidence=counter_evidence,
        trigger_strength=strength,
        crossed_candidate_gate=crossed,
    )


def _natal_nodes(parsed: ParsedInput) -> tuple[NatalNode, ...]:
    nodes: list[NatalNode] = []
    english_names = {"年柱": "year", "月柱": "month", "日柱": "day", "时柱": "hour"}
    for pillar_name, ganzhi in parsed.bazi.all_pillars():
        prefix = english_names[pillar_name]
        nodes.append((f"natal.{prefix}.stem", pillar_name[0] + "干", ganzhi.gan))
        nodes.append((f"natal.{prefix}.branch", pillar_name[0] + "支", ganzhi.zhi))
    return tuple(nodes)


def build_annual_traces(
    parsed_input: ParsedInput,
    *,
    current_year: int,
    until_present_only: bool = True,
) -> tuple[AnnualInteractionTrace, ...]:
    """扫描逐年力量场并构建未越候选门的 as-of 年度轨迹元组。

    批量入口只拥有命盘与截止年，没有逐候选事件的独立证据裁决，因此生成项的
    ``crossed_candidate_gate`` 一律保持 ``False``。调用方可在候选形成阶段对单年
    信号完成显式裁决后，直接调用 ``adapt_flow_year_energy`` 传入真值。
    """

    report = scan_retrospective(
        parsed_input,
        current_year=current_year,
        until_present_only=until_present_only,
    )
    natal_nodes = _natal_nodes(parsed_input)
    return tuple(
        adapt_flow_year_energy(flow_year, natal_nodes=natal_nodes)
        for segment in report.segments
        for flow_year in segment.flow_years
    )


def build_annual_traces_with_gate(
    parsed_input: ParsedInput,
    domain: str,
    *,
    current_year: int,
    until_present_only: bool = True,
) -> tuple[AnnualInteractionTrace, ...]:
    """逐年运行 L1/L2 应期门，生成带门控判定的年度轨迹。

    对每个流年分别检查原局结构与大运是否到位。仅当 L1、L2 均通过时才向适配器
    提交越门判定；适配器还会保证该年存在作用关系及被激活的原局节点。
    """

    report = scan_retrospective(
        parsed_input,
        current_year=current_year,
        until_present_only=until_present_only,
    )
    natal_nodes = _natal_nodes(parsed_input)
    traces: list[AnnualInteractionTrace] = []
    for segment in report.segments:
        for flow_year in segment.flow_years:
            passed_layers = sum(
                (
                    layer1_check(domain, parsed_input).passed,
                    layer2_check(flow_year.year, domain, None, parsed_input).passed,
                )
            )
            traces.append(
                adapt_flow_year_energy(
                    flow_year,
                    natal_nodes=natal_nodes,
                    crossed_candidate_gate=passed_layers == 2,
                )
            )
    return tuple(traces)

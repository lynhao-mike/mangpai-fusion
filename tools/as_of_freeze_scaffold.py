"""as-of 盲断闭环 · 冻结草稿脚手架生成器。

基于命盘数据自动填充事件候选窗口、大运倾向和结构信号，生成一个带算法
提示的冻结草稿 JSON——让冻结者从"对着空白模板猜"变成"在有提示的草稿
上填写"。

本工具只写草稿文件，不创建最终冻结文件；生成的草稿必须由命理师审查
和填写，并用 tools.as_of_contract_gate 预检后才能成为正式冻结产物。
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path

from engine.asof.daiyun_context import suggest_daiyun_path_tendencies
from engine.predicates.types import ParsedInput
from tools.as_of_freeze_preflight import YearTriggerSignal, run_freeze_preflight

__all__ = (
    "FreezeScaffold",
    "build_freeze_scaffold",
    "write_scaffold_to_file",
)

_CONTRACT_GATE_REMINDERS = (
    "职业中心描述中'或'连接词应少于3个，避免覆盖面过宽",
    "若 completion_mode=ACTIVATE_EXISTING 且缺少显性财官证据，必须添加不完整兑现备选",
    "事件窗口已预设单年，不要扩展为多年",
)


@dataclass(frozen=True, slots=True)
class FreezeScaffold:
    """生成的冻结草稿内容（写入前可审查）。"""

    case_id: str
    as_of_date: str
    preflight_summary: str
    daiyun_tendency_note: str
    scaffolded_event_candidates: tuple[dict, ...]
    contract_gate_reminders: tuple[str, ...]
    scaffold_note: str


def _trigger_basis(signal: YearTriggerSignal, domain: str) -> str:
    domain_text = "、".join(signal.domain_hints) if signal.domain_hints else "无明确领域提示"
    relation_text = (
        "；".join(signal.relation_summaries)
        if signal.relation_summaries
        else "无可用关系明细"
    )
    return (
        f"{signal.year}年流年{signal.liunian}，处于{signal.dayun_ganzhi}大运；"
        f"与原局形成{signal.relation_count}项干支关系，结构触发强度为高；"
        f"关系摘要：{relation_text}；领域提示：{domain_text}。"
        f"本草稿关注领域：{domain}。"
    )


def _event_candidate(
    signal: YearTriggerSignal,
    index: int,
    domain: str,
) -> dict[str, str]:
    year = signal.year
    return {
        "candidate_id": f"E{index}",
        "scoring_unit": "TODO: 填写事件类型",
        "window": f"{year:04d}-01-01/{year:04d}-12-31",
        "center_event": "TODO: 填写具体事件描述",
        "trigger_basis": _trigger_basis(signal, domain),
        "_scaffold_reminder": "窗口已限定单年，事件类型请具体描述，避免多选'或'",
    }


def build_freeze_scaffold(
    parsed_input: ParsedInput,
    case_id: str,
    as_of_date: str,
    *,
    as_of_year: int,
    domain: str = "career",
) -> FreezeScaffold:
    """生成冻结草稿，整合 preflight 和大运倾向建议。"""

    parsed_as_of_date = date.fromisoformat(as_of_date)
    if parsed_as_of_date.year != as_of_year:
        raise ValueError("as_of_date 的年份必须与 as_of_year 一致")

    preflight = run_freeze_preflight(parsed_input, as_of_year=as_of_year)
    high_signals = preflight.high_trigger_years[:5]
    summary = (
        "高触发年：" + "、".join(
            f"{signal.year}({signal.liunian}，{signal.relation_count}项关系)"
            for signal in high_signals
        )
        if high_signals
        else "截至当前日期未扫描到高触发年；请人工复核中、低触发年与现实条件。"
    )

    current_dayun = parsed_input.dayun.at_year(as_of_year)
    if current_dayun is None:
        daiyun_note = "当前年份未落入已提供的大运排布，无法生成大运倾向；需人工补录或复核。"
    else:
        tendency = suggest_daiyun_path_tendencies(current_dayun.干支, parsed_input.bazi)
        open_domains = "、".join(tendency.open_or_amplify_domains)
        suppress_domains = "、".join(tendency.suppress_or_close_domains)
        daiyun_note = (
            f"当前{tendency.dayun_ganzhi}大运：天干{tendency.stem_shishen}"
            f"（{tendency.stem_class}），地支主气{tendency.branch_shishen_hint}"
            f"（{tendency.branch_class}）；可能开放或放大：{open_domains}；"
            f"可能抑制或关闭：{suppress_domains}。{tendency.note}"
        )

    candidates = tuple(
        _event_candidate(signal, index, domain)
        for index, signal in enumerate(high_signals, start=1)
    )
    return FreezeScaffold(
        case_id=case_id,
        as_of_date=as_of_date,
        preflight_summary=summary,
        daiyun_tendency_note=daiyun_note,
        scaffolded_event_candidates=candidates,
        contract_gate_reminders=_CONTRACT_GATE_REMINDERS,
        scaffold_note=(
            "这是算法预填充草稿，不是正式冻结文件；必须由命理师审查并填写 TODO 字段，"
            "再使用 tools.as_of_contract_gate 完成预检。"
        ),
    )


def write_scaffold_to_file(
    scaffold: FreezeScaffold,
    output_path: Path,
) -> None:
    """将草稿写入 JSON 文件；目标已存在时拒绝覆盖。"""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(asdict(scaffold), ensure_ascii=False, indent=2) + "\n"
    with output_path.open("x", encoding="utf-8", newline="\n") as file:
        file.write(payload)

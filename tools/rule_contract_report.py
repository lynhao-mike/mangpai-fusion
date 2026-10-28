"""T-152 · 产品规则契约化干跑：``triggered`` / ``outcome`` 与反条件压制面。

对 ``theory/production/claim-rules-v1.yaml`` 的 10 条生产规则逐条 ``evaluate_rule``：

* 语料固定为 ``META/timing-eval-set-v1.json`` 中 ``usable_for_timing=true`` 的 382 例；
* 用 ``birth_dt`` + ``gender``（男→乾、女→坤）建盘，``build_chart_feature_vector`` 取特征；
* 上下文按 ``engine/v5/{duan,gao,yang}_runner.py`` 的原样构造，**只评估 runner 会选中的那条规则**
  （handler 提前返回、或同一 handler 选中另一条规则时，该规则本卡不计入 ``n_evaluated``）；
* 本卡不改 ``matched``：报告里的 ``n_suppressed_if_flipped`` 只是「若下一卡把 matched 改为
  ``triggered and outcome != 'fail'``，会被压掉多少例」的预演，不改变任何产品输出。

产物（默认前缀 ``META/rule-contract-dryrun-v1``）：

* ``<prefix>.json``（全量，含被压掉的 case_id）
* ``<prefix>.md``（人读）
* 控制台 10 行表 + 每条规则被压掉的前 20 个 case_id

用法::

    python -m tools.rule_contract_report
    python -m tools.rule_contract_report --out-prefix META/rule-contract-dryrun-v2

``--out-prefix`` 接受不带扩展名的路径前缀（相对路径按仓库根解析）；默认仍写
``META/rule-contract-dryrun-v1``，现有调用行为不变。前缀所在目录必须已存在。

两次运行输出必须逐字节一致（无时间戳、case 按 case_id 排序）。
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from engine.api.facade import build_chart
from engine.claims.rule_loader import (
    ExecutableClaimRule,
    RuleCondition,
    evaluate_rule,
    load_claim_rule_registry,
)
from engine.decision.models import ChartFactLedger
from engine.energy.tiyong import evaluate_tiyong
from engine.energy.zuogong import evaluate_zuogong
from engine.features import ChartFeatureVector, build_chart_feature_vector
from engine.predicates.types import Bazi, GanZhi, adapt_bazi

# ADR-006 冻结 engine.v5：干跑工具不 import v5，按 duan_runner.chart_ledger_to_bazi
# 的同一套 predicate 原语（GanZhi.parse + adapt_bazi 自动填藏干）重建 Bazi。

ROOT = Path(__file__).resolve().parents[1]
EVAL_PATH = ROOT / "META" / "timing-eval-set-v1.json"
DEFAULT_OUT_PREFIX = "META/rule-contract-dryrun-v1"

SCHEMA = "rule-contract-dryrun/v1"
TASK_ID = "T-152"
GENDER_MARKERS = {"男": "乾", "女": "坤"}
CONSOLE_CASE_LIMIT = 20

_OP_TEXT = {
    "eq": "==", "ne": "!=", "gte": ">=", "lte": "<=",
    "in": "∈", "not_in": "∉", "truthy": "为真", "falsy": "为假",
}
_PILLAR_NAMES = ("year", "month", "day", "hour")


@dataclass(frozen=True)
class _Selection:
    """runner 会提交给 ``evaluate_rule`` 的一条规则及其上下文。"""

    rule_id: str
    context: Mapping[str, Any]


# ---------------------------------------------------------------------------
# 条件渲染
# ---------------------------------------------------------------------------

def _format_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, tuple):
        return "[" + ", ".join(_format_value(item) for item in value) + "]"
    if isinstance(value, float):
        return repr(value)
    return str(value)


def _describe_condition(condition: RuleCondition) -> str:
    op = _OP_TEXT.get(condition.op, condition.op)
    if condition.op in {"truthy", "falsy"}:
        return f"{condition.fact} {op}"
    return f"{condition.fact} {op} {_format_value(condition.value)}"


def _describe_conditions(conditions: tuple[RuleCondition, ...]) -> list[str]:
    return [_describe_condition(condition) for condition in conditions]


# ---------------------------------------------------------------------------
# 建盘与特征
# ---------------------------------------------------------------------------

def _count(features: ChartFeatureVector, *names: str) -> int:
    return sum(int(features.ten_god_counts.get(name, 0)) for name in names)


def _build_ledger(case: Mapping[str, Any]) -> ChartFactLedger:
    marker = GENDER_MARKERS[str(case["gender"])]
    facts = build_chart(birth_dt=str(case["birth_dt"]), gender=marker)
    pillars = {name: pillar.ganzhi for name, pillar in zip(_PILLAR_NAMES, facts.pillars)}
    return ChartFactLedger(
        sex_marker=facts.gender,
        solar_datetime=str(case["birth_dt"]),
        four_pillars=pillars,
    )


def _ledger_to_bazi(ledger: ChartFactLedger) -> Bazi:
    """等价重建 ``duan_runner.chart_ledger_to_bazi``（不 import 冻结的 engine.v5）。"""
    pillars: dict[str, GanZhi] = {}
    for chinese, english in (
        ("年柱", "year"), ("月柱", "month"), ("日柱", "day"), ("时柱", "hour"),
    ):
        raw = str(ledger.four_pillars.get(english, "")).strip()
        if len(raw) != 2:
            raise ValueError("duan structure requires four complete pillars")
        pillars[chinese] = GanZhi.parse(raw)
    return adapt_bazi(pillars)


def _duan_active_path_count(ledger: ChartFactLedger) -> int:
    bazi = _ledger_to_bazi(ledger)
    tiyong = evaluate_tiyong(bazi)
    return len([path for path in evaluate_zuogong(bazi, tiyong) if path.layer_count >= 1])


def _day_branch(ledger: ChartFactLedger) -> str:
    day = str(ledger.four_pillars.get("day", "")).strip()
    return day[1] if len(day) == 2 else ""


# ---------------------------------------------------------------------------
# runner 上下文（与 engine/v5/{duan,gao,yang}_runner.py 逐字对齐）
# ---------------------------------------------------------------------------

def _duan_career_role_change(features: ChartFeatureVector, active_path_count: int) -> _Selection:
    output_count = _count(features, "食神", "伤官")
    official_count = _count(features, "正官", "七杀")
    movement_structure = features.mixed_official_kill or features.branch_conflict_intensity >= 0.35
    return _Selection(
        "DUAN-EVENT-CAREER-ROLE-CHANGE-V1",
        {
            "evidence_completeness": features.evidence_completeness,
            "has_official": features.has_official,
            "has_output": features.has_output,
            "output_count": output_count,
            "official_count": official_count,
            "movement_structure": movement_structure,
            "active_path_count": active_path_count,
            "branch_conflict_intensity": features.branch_conflict_intensity,
        },
    )


def _duan_career_path_type(
    features: ChartFeatureVector, active_path_count: int
) -> _Selection | None:
    employment_score = _count(features, "正官", "七杀", "正印", "偏印")
    entrepreneurship_score = _count(features, "食神", "伤官", "正财", "偏财")
    if (
        employment_score >= 4
        and entrepreneurship_score >= 4
        and features.branch_conflict_intensity >= 0.35
    ):
        predicted_label = "mixed"
    elif employment_score >= 4 and employment_score - entrepreneurship_score >= 3:
        predicted_label = "employment"
    elif entrepreneurship_score >= 4 and entrepreneurship_score - employment_score >= 3:
        predicted_label = "entrepreneurship"
    else:
        return None
    return _Selection(
        f"DUAN-EVENT-CAREER-PATH-{predicted_label.upper()}-V1",
        {
            "evidence_completeness": features.evidence_completeness,
            "predicted_label": predicted_label,
            "employment_score": employment_score,
            "entrepreneurship_score": entrepreneurship_score,
            "employment_advantage": employment_score - entrepreneurship_score,
            "entrepreneurship_advantage": entrepreneurship_score - employment_score,
            "branch_conflict_intensity": features.branch_conflict_intensity,
            "active_path_count": active_path_count,
        },
    )


def _duan_wealth_debt(features: ChartFeatureVector, active_path_count: int) -> _Selection:
    wealth_count = _count(features, "正财", "偏财")
    peer_pressure = _count(features, "比肩", "劫财")
    return _Selection(
        "DUAN-EVENT-WEALTH-DEBT-V1",
        {
            "evidence_completeness": features.evidence_completeness,
            "has_wealth": features.has_wealth,
            "wealth_count": wealth_count,
            "peer_pressure": peer_pressure,
            "support_drain_imbalance": features.draining_count - features.supporting_count,
            "branch_conflict_intensity": features.branch_conflict_intensity,
            "active_path_count": active_path_count,
        },
    )


def _duan_marriage(
    ledger: ChartFactLedger, features: ChartFeatureVector, active_path_count: int
) -> _Selection:
    day_branch = _day_branch(ledger)
    day_branch_disrupted = any(
        day_branch in pair for pair in (*features.chong_pairs, *features.xing_hai_pairs)
    )
    independent_signals = (
        int(day_branch_disrupted)
        + int(features.mixed_official_kill)
        + int(bool(features.chong_pairs) and bool(features.xing_hai_pairs))
    )
    return _Selection(
        "DUAN-EVENT-MARRIAGE-DIVORCE-REMARRIAGE-V1",
        {
            "evidence_completeness": features.evidence_completeness,
            "independent_signal_count": independent_signals,
            "active_path_count": active_path_count,
        },
    )


def _gao_wealth_debt(features: ChartFeatureVector) -> _Selection:
    wealth_count = _count(features, "正财", "偏财")
    peer_count = _count(features, "比肩", "劫财")
    signals = {
        "wealth_exposed": features.has_wealth and wealth_count >= 2,
        "peer_competition": peer_count >= 3,
        "support_drain_imbalance": features.draining_count - features.supporting_count >= 3,
        "branch_conflict": features.branch_conflict_intensity >= 0.55,
        "concentrated_or_withered": features.element_concentration >= 0.50
        or len(features.missing_elements) >= 2,
    }
    pressure_count = sum(int(value) for key, value in signals.items() if key != "wealth_exposed")
    return _Selection(
        "GAO-WEALTH-DEBT-STRUCTURAL-CORROBORATION-V1",
        {
            "evidence_completeness": features.evidence_completeness,
            "wealth_exposed": signals["wealth_exposed"],
            "pressure_signal_count": pressure_count,
        },
    )


def _gao_health_system_risk(features: ChartFeatureVector) -> _Selection | None:
    strong_signals = {
        "severe_support_drain_imbalance": features.draining_count - features.supporting_count >= 4,
        "climate_extreme": features.climate_extreme
        and max(abs(features.cold_warm_axis), abs(features.dry_wet_axis)) >= 0.65,
        "element_concentration": features.element_concentration >= 0.50
        or len(features.missing_elements) >= 2,
        "branch_conflict": features.branch_conflict_intensity >= 0.55,
    }
    signal_count = sum(int(value) for value in strong_signals.values())
    if signal_count >= 3:
        predicted_label = "high"
    elif signal_count >= 2:
        predicted_label = "moderate"
    else:
        return None
    return _Selection(
        f"GAO-HEALTH-SYSTEM-RISK-{predicted_label.upper()}-V1",
        {
            "evidence_completeness": features.evidence_completeness,
            "predicted_label": predicted_label,
            "risk_signal_count": signal_count,
        },
    )


def _yang_marriage(
    ledger: ChartFactLedger, features: ChartFeatureVector, sex: str
) -> _Selection | None:
    day_branch = _day_branch(ledger)
    if not day_branch:
        return None
    chong_pairs = {frozenset(pair) for pair in features.chong_pairs if day_branch in pair}
    xing_hai_pairs = {frozenset(pair) for pair in features.xing_hai_pairs if day_branch in pair}
    palace_pair_count = len(chong_pairs | xing_hai_pairs)
    palace_disrupted = bool(chong_pairs) or bool(xing_hai_pairs)

    if sex == "male":
        spouse_star_basis = "wealth"
        spouse_count = _count(features, "正财", "偏财")
        spouse_present = features.has_wealth and spouse_count > 0
    else:
        spouse_star_basis = "official"
        spouse_count = _count(features, "正官", "七杀")
        spouse_present = features.has_official and spouse_count > 0

    peer_competition = _count(features, "比肩", "劫财") >= 3
    output_heavy = _count(features, "食神", "伤官") >= 4
    signals = {
        "spouse_palace_disrupted": palace_disrupted,
        "spouse_star_weak": not spouse_present or spouse_count <= 1,
        "peer_competition": peer_competition,
        "output_spouse_conflict": output_heavy and spouse_present,
        "female_mixed_official": sex == "female" and features.mixed_official_kill,
        "compound_distinct_palace_pairs": palace_pair_count >= 2
        and bool(chong_pairs)
        and bool(xing_hai_pairs),
    }
    return _Selection(
        "YANG-MARRIAGE-DIVORCE-REMARRIAGE-RISK-V1",
        {
            "evidence_completeness": features.evidence_completeness,
            "sex": sex,
            "spouse_star_basis": spouse_star_basis,
            "independent_signal_count": sum(int(value) for value in signals.values()),
        },
    )


def _selections(
    ledger: ChartFactLedger,
    features: ChartFeatureVector,
    sex: str,
    active_path_count: int | None,
) -> list[_Selection]:
    """复现三个 runner 的 dispatch：只有会被 evaluate_rule 的规则才进入统计。"""
    if features.evidence_completeness != "full":
        return []
    selections: list[_Selection] = []
    if active_path_count is not None:
        selections.append(_duan_career_role_change(features, active_path_count))
        career_path = _duan_career_path_type(features, active_path_count)
        if career_path is not None:
            selections.append(career_path)
        selections.append(_duan_wealth_debt(features, active_path_count))
        selections.append(_duan_marriage(ledger, features, active_path_count))
    selections.append(_gao_wealth_debt(features))
    health = _gao_health_system_risk(features)
    if health is not None:
        selections.append(health)
    yang = _yang_marriage(ledger, features, sex)
    if yang is not None:
        selections.append(yang)
    return selections


# ---------------------------------------------------------------------------
# 汇总
# ---------------------------------------------------------------------------

def _new_stats() -> dict[str, Any]:
    return {
        "n_evaluated": 0,
        "n_matched": 0,
        "n_triggered": 0,
        "n_counter": 0,
        "n_suppressed_if_flipped": 0,
        "n_outcome_success": 0,
        "n_outcome_fail": 0,
        "n_outcome_unknown": 0,
        "n_exclusion_veto": 0,
        "n_condition_unmet": 0,
        "counter_hits": Counter(),
        "suppressed_case_ids": [],
    }


def _evaluate_corpus(
    cases: list[Mapping[str, Any]], rules: Mapping[str, ExecutableClaimRule]
) -> tuple[dict[str, dict[str, Any]], list[dict[str, str]]]:
    stats = {rule_id: _new_stats() for rule_id in rules}
    failures: list[dict[str, str]] = []
    for case in sorted(cases, key=lambda item: str(item["case_id"])):
        case_id = str(case["case_id"])
        try:
            ledger = _build_ledger(case)
            features = build_chart_feature_vector(ledger)
        except Exception as exc:  # noqa: BLE001 - 建盘失败必须逐例列原因，不许静默
            failures.append(
                {"case_id": case_id, "stage": "build", "error": f"{type(exc).__name__}: {exc}"}
            )
            continue
        try:
            active_path_count: int | None = _duan_active_path_count(ledger)
        except (KeyError, TypeError, ValueError) as exc:
            # 与 duan_runner.generate_claims 的兜底一致：段派结构失败只影响段派规则。
            failures.append(
                {
                    "case_id": case_id,
                    "stage": "duan_structure",
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )
            active_path_count = None
        sex = "male" if str(case["gender"]) == "男" else "female"
        for selection in _selections(ledger, features, sex, active_path_count):
            rule = rules[selection.rule_id]
            result = evaluate_rule(rule, selection.context)
            entry = stats[selection.rule_id]
            entry["n_evaluated"] += 1
            entry["n_matched"] += int(result.matched)
            entry["n_triggered"] += int(result.triggered)
            entry[f"n_outcome_{result.outcome}"] += 1
            if result.matched_counter_conditions:
                entry["n_counter"] += 1
                for condition in result.matched_counter_conditions:
                    entry["counter_hits"][_describe_condition(condition)] += 1
            if result.triggered and result.matched_counter_conditions:
                entry["n_suppressed_if_flipped"] += 1
                entry["suppressed_case_ids"].append(case_id)
            if not result.triggered and result.matched_exclusions:
                entry["n_exclusion_veto"] += 1
            if not result.triggered and result.failed_conditions:
                entry["n_condition_unmet"] += 1
    return stats, failures


def _rule_payload(rule: ExecutableClaimRule, stats: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "rule_id": rule.rule_id,
        "school_id": rule.school_id,
        "task_scope": list(rule.task_scope),
        "predicted_label": rule.predicted_label,
        "conditions": _describe_conditions(rule.conditions),
        "exclusions": _describe_conditions(rule.exclusions),
        "counter_conditions": _describe_conditions(rule.counter_conditions),
        "n_evaluated": stats["n_evaluated"],
        "n_matched": stats["n_matched"],
        "n_triggered": stats["n_triggered"],
        "n_counter": stats["n_counter"],
        "n_suppressed_if_flipped": stats["n_suppressed_if_flipped"],
        "n_outcome_success": stats["n_outcome_success"],
        "n_outcome_fail": stats["n_outcome_fail"],
        "n_outcome_unknown": stats["n_outcome_unknown"],
        "n_exclusion_veto": stats["n_exclusion_veto"],
        "n_condition_unmet": stats["n_condition_unmet"],
        "counter_hits": dict(sorted(stats["counter_hits"].items())),
        "suppressed_case_ids": list(stats["suppressed_case_ids"]),
    }


def _build_payload(
    registry_rules: tuple[ExecutableClaimRule, ...],
    stats: Mapping[str, Mapping[str, Any]],
    cases: list[Mapping[str, Any]],
    failures: list[dict[str, str]],
) -> dict[str, Any]:
    rule_payloads = [_rule_payload(rule, stats[rule.rule_id]) for rule in registry_rules]
    matched_equals_triggered = all(
        item["n_matched"] == item["n_triggered"] for item in rule_payloads
    )
    build_failure_ids = {item["case_id"] for item in failures if item["stage"] == "build"}
    return {
        "schema": SCHEMA,
        "task": TASK_ID,
        "semantics": {
            "triggered": "conditions 全中且 exclusions 未中",
            "outcome": "triggered 且 counter 命中 → fail；triggered 且 counter 未中 → success；未触发 → unknown",
            "matched": "旧语义，本卡未改：conditions 全中且 exclusions 未中；当前取值与 triggered 相同",
            "n_evaluated": "该规则在生产 runner 中实际进入 evaluate_rule 的盘数（handler 提前返回或选中别的规则时不计）",
            "n_counter": "进入 evaluate_rule 且任一反条件命中的盘数",
            "n_suppressed_if_flipped": "triggered 且反条件命中；若下一卡把 matched 改为 triggered and outcome != 'fail'，这些条会被压掉",
        },
        "corpus": {
            "path": "META/timing-eval-set-v1.json",
            "filter": "usable_for_timing=true",
            "n_cases": len(cases),
            "n_built": len(cases) - len(build_failure_ids),
            "n_build_failed": len(build_failure_ids),
            "build_failures": failures,
        },
        "matched_equals_triggered": matched_equals_triggered,
        "rules": rule_payloads,
        "totals": {
            "n_evaluated": sum(item["n_evaluated"] for item in rule_payloads),
            "n_triggered": sum(item["n_triggered"] for item in rule_payloads),
            "n_counter": sum(item["n_counter"] for item in rule_payloads),
            "n_suppressed_if_flipped": sum(
                item["n_suppressed_if_flipped"] for item in rule_payloads
            ),
        },
    }


# ---------------------------------------------------------------------------
# 输出
# ---------------------------------------------------------------------------

def _print_table(payload: Mapping[str, Any]) -> None:
    header = (
        f"{'rule_id':48s} {'eval':>5s} {'trig':>5s} {'cntr':>5s} {'supp':>5s} {'succ':>5s}"
    )
    print(header)
    print("-" * len(header))
    for item in payload["rules"]:
        print(
            f"{item['rule_id']:48s} {item['n_evaluated']:5d} {item['n_triggered']:5d} "
            f"{item['n_counter']:5d} {item['n_suppressed_if_flipped']:5d} "
            f"{item['n_outcome_success']:5d}"
        )
    totals = payload["totals"]
    print("-" * len(header))
    print(
        f"{'TOTAL':48s} {totals['n_evaluated']:5d} {totals['n_triggered']:5d} "
        f"{totals['n_counter']:5d} {totals['n_suppressed_if_flipped']:5d}"
    )


def _print_counter_detail(payload: Mapping[str, Any]) -> None:
    print()
    print("反条件明细（triggered 且反条件命中的 case_id，控制台最多 20 个，JSON 全量）")
    for item in payload["rules"]:
        hits = item["counter_hits"] or {}
        counter_text = "；".join(item["counter_conditions"]) or "（无）"
        hits_text = "；".join(f"{text} × {count}" for text, count in hits.items()) or "无命中"
        print(
            f"- {item['rule_id']}: 反条件=[{counter_text}] 命中统计={hits_text} "
            f"压掉={item['n_suppressed_if_flipped']}"
        )
        ids = item["suppressed_case_ids"]
        if ids:
            shown = ", ".join(ids[:CONSOLE_CASE_LIMIT])
            suffix = f" …（共 {len(ids)} 例，余下见 JSON）" if len(ids) > CONSOLE_CASE_LIMIT else ""
            print(f"    case_ids: {shown}{suffix}")


def _render_markdown(payload: Mapping[str, Any]) -> str:
    corpus = payload["corpus"]
    lines = [
        "# T-152 规则契约干跑报告（v1）",
        "",
        f"- 语料：`{corpus['path']}`，`{corpus['filter']}`，共 {corpus['n_cases']} 例",
        f"- 建盘成功：{corpus['n_built']} 例；建盘失败：{corpus['n_build_failed']} 例",
        "- 语义：本卡只新增 `triggered` / `outcome`；`matched` 仍是旧语义"
        "（conditions 全中且 exclusions 未中），未改产品输出。",
        "- `n_suppressed_if_flipped`：若下一卡把 `matched` 改为 `triggered and outcome != 'fail'`，"
        "会被压掉的条数（预演，不是当前产品行为）。",
        f"- `matched == triggered`：{payload['matched_equals_triggered']}",
        "",
        "## 1. 汇总表",
        "",
        "| rule_id | eval | triggered | counter 命中 | 若反条件生效会压掉 | outcome=success |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for item in payload["rules"]:
        lines.append(
            f"| `{item['rule_id']}` | {item['n_evaluated']} | {item['n_triggered']} | "
            f"{item['n_counter']} | {item['n_suppressed_if_flipped']} | {item['n_outcome_success']} |"
        )
    totals = payload["totals"]
    lines.append(
        f"| **合计** | {totals['n_evaluated']} | {totals['n_triggered']} | "
        f"{totals['n_counter']} | {totals['n_suppressed_if_flipped']} | "
        f"{sum(item['n_outcome_success'] for item in payload['rules'])} |"
    )
    lines += ["", "## 2. 建盘 / 段派结构失败", ""]
    if corpus["build_failures"]:
        for failure in corpus["build_failures"]:
            lines.append(
                f"- `{failure['case_id']}`（{failure['stage']}）：{failure['error']}"
            )
    else:
        lines.append("无。")
    lines += ["", "## 3. 逐条规则", ""]
    for item in payload["rules"]:
        lines += [
            f"### `{item['rule_id']}`",
            "",
            f"- 流派 / 任务：{item['school_id']} / {', '.join(item['task_scope'])}",
            f"- 正条件：{'；'.join(item['conditions'])}",
            f"- 排除条件：{'；'.join(item['exclusions']) or '（无）'}",
            f"- 反条件：{'；'.join(item['counter_conditions']) or '（无）'}",
            f"- 数字：n_evaluated={item['n_evaluated']}，n_matched={item['n_matched']}，"
            f"n_triggered={item['n_triggered']}，n_counter={item['n_counter']}，"
            f"n_suppressed_if_flipped={item['n_suppressed_if_flipped']}，"
            f"n_outcome_success={item['n_outcome_success']}",
            f"- 未触发：exclusion 否决 {item['n_exclusion_veto']} 例；"
            f"正条件未满足 {item['n_condition_unmet']} 例",
        ]
        hits = item["counter_hits"] or {}
        if hits:
            lines.append(
                "- 反条件命中统计："
                + "；".join(f"`{text}` × {count}" for text, count in hits.items())
            )
        ids = item["suppressed_case_ids"]
        if ids:
            lines.append(
                f"- 若反条件生效会被压掉的 case_id（{len(ids)} 例，最多列 "
                f"{CONSOLE_CASE_LIMIT} 个，全量见 JSON）："
                + ", ".join(f"`{case_id}`" for case_id in ids[:CONSOLE_CASE_LIMIT])
            )
        else:
            lines.append("- 若反条件生效会被压掉的 case_id：无")
        lines.append("")
    return "\n".join(lines) + "\n"


def _resolve_out_prefix(raw: str) -> Path:
    """相对前缀按仓库根解析，使默认值与旧版固定路径等价。"""
    prefix = Path(raw)
    return prefix if prefix.is_absolute() else ROOT / prefix


def _output_paths(prefix: Path) -> tuple[Path, Path]:
    """前缀不带扩展名：实际写 ``<prefix>.json`` 与 ``<prefix>.md``。"""
    return Path(f"{prefix}.json"), Path(f"{prefix}.md")


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="T-152 规则契约干跑报告")
    parser.add_argument(
        "--out-prefix",
        default=DEFAULT_OUT_PREFIX,
        metavar="PATH",
        help=(
            "输出路径前缀，不带扩展名（相对路径按仓库根解析）；"
            f"实际写 <prefix>.json 与 <prefix>.md，默认 {DEFAULT_OUT_PREFIX}"
        ),
    )
    return parser


def _write_outputs(json_path: Path, md_path: Path, payload: Mapping[str, Any]) -> bool:
    """写两个产物；任一失败或只写成功一个文件都返回 False（调用方退出码 2）。"""
    try:
        json_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        md_path.write_text(_render_markdown(payload), encoding="utf-8")
    except OSError as exc:
        print(f"错误：写出失败：{exc}", file=sys.stderr)
        return False
    missing = [str(path) for path in (json_path, md_path) if not path.is_file()]
    if missing:
        print("错误：未同时写出 JSON 与 Markdown：" + "、".join(missing), file=sys.stderr)
        return False
    return True


def main(argv: Sequence[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

    args = _build_arg_parser().parse_args(argv)
    json_path, md_path = _output_paths(_resolve_out_prefix(args.out_prefix))
    directory = json_path.parent
    if not directory.is_dir():
        print(f"错误：输出目录不存在：{directory}", file=sys.stderr)
        return 2

    document = json.loads(EVAL_PATH.read_text(encoding="utf-8"))
    cases = [case for case in document["cases"] if case.get("usable_for_timing") is True]
    registry = load_claim_rule_registry()
    rules = {rule.rule_id: rule for rule in registry.rules}

    stats, failures = _evaluate_corpus(cases, rules)
    payload = _build_payload(registry.rules, stats, cases, failures)

    if not _write_outputs(json_path, md_path, payload):
        return 2

    print(f"语料：{len(cases)} 例（usable_for_timing=true）；建盘失败 {payload['corpus']['n_build_failed']} 例")
    structure_failures = [
        item for item in payload["corpus"]["build_failures"] if item["stage"] != "build"
    ]
    if structure_failures:
        print(f"段派结构失败 {len(structure_failures)} 例（只影响段派规则，逐例见 JSON）")
    _print_table(payload)
    _print_counter_detail(payload)
    print()
    print(f"已写出：{_display_path(json_path)}")
    print(f"已写出：{_display_path(md_path)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

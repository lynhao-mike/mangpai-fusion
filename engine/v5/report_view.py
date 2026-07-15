"""engine.v5.report_view · report-v6 最小 ViewModel。

该模块只负责把 V5Output 转成 templates/report-v6.md 可消费的中文上下文。
不做命理规则推断，不泄露 claim_id、prediction_id、结构图 ID 或学习信号 ID。
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING, Any, Sequence

from engine.decision.l6_staged_arbitration import StageDecision
from engine.evaluation.models import BlindTask, FrozenBlindRun
from engine.v5.domain import V5ArbitrationResult, V5Output, V5Prediction

if TYPE_CHECKING:
    from engine.application.run_comparison import RunComparison


PLACEHOLDER_RE = re.compile(r"{{\s*([^}]+?)\s*}}")
DOMAINS = ("学业", "事业", "财富", "婚姻", "健康")
SCHOOLS = {
    "ziping": "子平类",
    "ditiansui": "滴天髓类",
    "gao_dechen": "高德臣",
    "duan_jianye": "段建业",
    "yang_qingjuan": "杨清娟",
}
SCHOOL_PLACEHOLDER_SUFFIX = {
    "ziping": "子平类",
    "ditiansui": "滴天髓类",
    "gao_dechen": "高德臣",
    "duan_jianye": "段建业",
    "yang_qingjuan": "杨清娟",
}


def extract_template_placeholders(template_text: str) -> set[str]:
    """提取模板中的 Jinja 风格占位符名。"""

    return {match.strip() for match in PLACEHOLDER_RE.findall(template_text)}


def default_context_for_template(template_text: str) -> dict[str, str]:
    """为模板所有占位符提供兜底值，避免未渲染变量外泄。"""

    return {name: "待补充" for name in extract_template_placeholders(template_text)}


def render_template_text(template_text: str, context: dict[str, Any]) -> str:
    """极简模板替换；只处理 {{ name }}，并移除 report-v6 的轻量循环块。"""

    # report-v6 当前仅大运速览使用 Jinja 循环；MVP 不执行循环，直接保留大运速览兜底块。
    template_text = re.sub(
        r"\{%\s*if\s+大运列表\s*%\}.*?\{%\s*endif\s*%\}",
        "",
        template_text,
        flags=re.DOTALL,
    )
    template_text = template_text.replace("{% if not 大运列表 %}", "").replace("{% endif %}", "")

    def replace(match: re.Match[str]) -> str:
        key = match.group(1).strip()
        return str(context.get(key, "待补充"))

    return PLACEHOLDER_RE.sub(replace, template_text)


def _confidence_label(tier: str, score: float) -> str:
    if score >= 0.7:
        state = "高"
    elif score >= 0.45:
        state = "中"
    else:
        state = "低"
    padded = (tier + "☆☆☆☆☆")[:5]
    return f"{state}（{padded}）"


def _arbitration_by_domain(output: V5Output) -> dict[str, dict[str, V5ArbitrationResult]]:
    grouped: dict[str, dict[str, V5ArbitrationResult]] = {}
    for item in output.arbitration_results:
        grouped.setdefault(item.domain, {})[item.stage] = item
    return grouped


def _claims_by_domain_school(output: V5Output) -> dict[tuple[str, str], list[str]]:
    grouped: dict[tuple[str, str], list[str]] = {}
    for claim in output.claims:
        if claim.stance == "abstain":
            text = "弃权：runner 待接入"
        else:
            text = claim.claim
            if len(text) > 64:
                text = text[:64] + "……"
        grouped.setdefault((claim.domain, claim.school), []).append(text)
    return grouped


def _first_prediction(output: V5Output, domain: str) -> V5Prediction | None:
    for item in output.prediction_ledger.predictions:
        if item.domain == domain:
            return item
    return None


def _prediction_window(prediction: V5Prediction | None) -> str:
    if prediction is None:
        return "待登记"
    return str(prediction.time_window.get("label") or prediction.time_window or "待登记")


def _prediction_trigger(prediction: V5Prediction | None) -> str:
    if prediction is None:
        return "待登记"
    return "；".join(prediction.trigger_conditions) or "待登记"


def _prediction_probability(prediction: V5Prediction | None) -> str:
    if prediction is None:
        return "待登记"
    low, high = prediction.probability_range
    return f"{int(low * 100)}%–{int(high * 100)}%"


def _prediction_confidence_state(prediction: V5Prediction | None) -> str:
    if prediction is None:
        return "待登记"
    if prediction.confidence.score >= 0.7:
        return "高"
    if prediction.confidence.score >= 0.45:
        return "中"
    return "低"


def _prediction_star(prediction: V5Prediction | None) -> str:
    if prediction is None:
        return "待登记"
    return (prediction.confidence.tier + "☆☆☆☆☆")[:5]


def _prediction_falsifier(prediction: V5Prediction | None) -> str:
    if prediction is None:
        return "待登记"
    return prediction.falsifier or "若时间窗内未发生该事件，则失验。"


def _prediction_feedback(prediction: V5Prediction | None) -> str:
    if prediction is None:
        return "待登记"
    mapping = {
        "pending": "待反馈",
        "hit": "命中",
        "miss": "失验",
        "partial": "半命中",
        "skipped": "跳过",
    }
    return mapping.get(prediction.feedback_state, str(prediction.feedback_state))


def _get(obj: Any, key: str) -> Any:
    """兼容 dict 与 dataclass 两种形态的字段读取。"""

    if isinstance(obj, dict):
        return obj.get(key)
    return getattr(obj, key, None)


def _l7_school_evidence_for_domain(
    domain: str,
    report_items: list,
    arbitration_decisions: list,
) -> dict[str, list[str]]:
    domain_by_decision = {
        _get(decision, "decision_id"): _get(decision, "domain")
        for decision in (arbitration_decisions or [])
    }
    grouped: dict[str, list[str]] = {}
    for item in report_items or []:
        if domain_by_decision.get(_get(item, "decision_id")) != domain:
            continue
        evidence = _get(item, "school_evidence") or {}
        for school, statements in evidence.items():
            bucket = grouped.setdefault(str(school), [])
            for statement in statements:
                text = str(statement)
                if text not in bucket:
                    bucket.append(text)
    return grouped


def _l7_conflict_for_domain(
    domain: str,
    report_items: list,
    arbitration_decisions: list,
) -> str:
    item_decision_ids = {
        _get(item, "decision_id")
        for item in report_items or []
    }
    results = [
        str(_get(decision, "result"))
        for decision in arbitration_decisions or []
        if _get(decision, "domain") == domain
        and _get(decision, "decision_id") in item_decision_ids
    ]
    return "、".join(results) if results else "待判"


def _l7_conclusion_for_domain(domain: str, report_items: list, arbitration_decisions: list) -> str | None:
    """聚合 L7 report_items 中指定域的全部裁决文本；找不到返回 None。"""

    domain_by_decision = {
        _get(d, "decision_id"): _get(d, "domain")
        for d in (arbitration_decisions or [])
    }
    conclusions = [
        str(text)
        for item in report_items or []
        if domain_by_decision.get(_get(item, "decision_id")) == domain
        if (text := _get(item, "display_text"))
    ]
    return "；".join(conclusions) if conclusions else None


def _domain_context(output: V5Output, domain: str) -> dict[str, str]:
    arbitrations = _arbitration_by_domain(output).get(domain, {})
    event_result = arbitrations.get("event_realization")
    structure_result = arbitrations.get("structure_legality")
    timing_result = arbitrations.get("probability_timing")
    prediction = _first_prediction(output, domain)
    confidence = event_result.confidence if event_result else None
    confidence_text = _confidence_label(confidence.tier, confidence.score) if confidence else "待补充"
    evidence = "；".join(
        item.rationale
        for item in (structure_result, event_result, timing_result)
        if item and item.rationale
    ) or "五派命题待接入"
    conclusion = event_result.conclusion if event_result else "五派事件裁决待生成"
    conflict = event_result.conflict_type if event_result else "待判"
    return {
        f"{domain}裁决结论": conclusion,
        f"{domain}共识结论": conclusion,
        f"{domain}冲突状态": conflict,
        f"{domain}证据链": evidence,
        f"{domain}置信度": confidence_text,
        f"{domain}应期": _prediction_window(prediction),
        f"{domain}反馈回写": "命中 / 失验 / 半命中 / 跳过",
    }


def build_report_v6_context(
    output: V5Output,
    *,
    template_text: str,
    report_path: str = "",
    case_dir: str = "",
    feedback_path: str = "",
    report_items: list | None = None,
    arbitration_decisions: list | None = None,
) -> dict[str, str]:
    """构造 report-v6 渲染上下文。"""

    context = default_context_for_template(template_text)
    chart = output.chart
    claims = _claims_by_domain_school(output)

    def _link(text: str, url: str) -> str:
        return f"[{text}]({url})" if url else text

    context.update(
        {
            "案例编号": output.case_id,
            "命式": str(chart.get("gender_marker") or chart.get("命式") or chart.get("sex") or "乾/坤"),
            "当前大运": str(chart.get("current_dayun") or chart.get("当前大运") or "待补充"),
            "起运时间": str(chart.get("start_luck") or chart.get("起运时间") or "待补充"),
            "分析状态": "预生产最小闭环",
            "报告路径": _link("打开报告文件", report_path),
            "案例目录": _link("打开案例目录", case_dir),
            "反馈入口": _link("打开反馈文件", feedback_path),
            "年干": str(chart.get("year_stem") or chart.get("年干") or ""),
            "年支": str(chart.get("year_branch") or chart.get("年支") or ""),
            "月干": str(chart.get("month_stem") or chart.get("月干") or ""),
            "月支": str(chart.get("month_branch") or chart.get("月支") or ""),
            "日干": str(chart.get("day_stem") or chart.get("日干") or ""),
            "日支": str(chart.get("day_branch") or chart.get("日支") or ""),
            "时干": str(chart.get("hour_stem") or chart.get("时干") or ""),
            "时支": str(chart.get("hour_branch") or chart.get("时支") or ""),
            "大运速览": str(chart.get("dayun_summary") or chart.get("大运速览") or "见案例输入"),
            "体结构资源": "由五派结构裁判汇总，MVP 阶段待细化。",
            "用现实目标": "由事件裁判与预测账本汇总，MVP 阶段待细化。",
            "做功路径": "五派 runner 接入后输出自力、平台、配偶、贵人、经营等路径。",
            "人生主线": "先形成可反馈主线，再由反馈校准。",
            "性格判断": "性格作为解释变量，不进入主要事件概率层。",
            "性格证据链": "来自结构裁判与事件裁判的长期底色。",
            "性格置信度": "中（★★★☆☆）",
            "性格应期": "长期底色，不单列概率应期",
        }
    )

    for domain in DOMAINS:
        context.update(_domain_context(output, domain))
        if domain == "事业":
            career_evidence = _l7_school_evidence_for_domain(
                domain, report_items or [], arbitration_decisions or []
            )
            for school, suffix in SCHOOL_PLACEHOLDER_SUFFIX.items():
                items = career_evidence.get(school) or ["待接入"]
                context[f"{domain}{suffix}"] = "；".join(items)
            context[f"{domain}冲突状态"] = _l7_conflict_for_domain(
                domain, report_items or [], arbitration_decisions or []
            )
            l7_text = _l7_conclusion_for_domain(
                domain, report_items or [], arbitration_decisions or []
            ) or "待接入"
            context[f"{domain}裁决结论"] = l7_text
            context[f"{domain}共识结论"] = l7_text
            continue
        for school, suffix in SCHOOL_PLACEHOLDER_SUFFIX.items():
            items = claims.get((domain, school)) or claims.get(("总体", school)) or ["待接入"]
            context[f"{domain}{suffix}"] = "；".join(items[:2])

    for domain in DOMAINS:
        if domain == "事业":
            continue
        l7_text = _l7_conclusion_for_domain(domain, report_items or [], arbitration_decisions or [])
        if l7_text:
            context[f"{domain}裁决结论"] = l7_text
            context[f"{domain}共识结论"] = l7_text

    # 主要事项结构字段：适度复用领域裁决结果，避免模板空洞。
    context.update(
        {
            "学历层次判断": context.get("学业裁决结论", "待补充"),
            "学校层级判断": "待反馈细分学校层级",
            "学业表现判断": "待反馈学习表现",
            "学科倾向判断": "待反馈专业方向",
            "职业层级判断": context.get("事业裁决结论", "待补充"),
            "单位层级判断": "待反馈单位性质与层级",
            "权力层级判断": "待反馈管理半径与正式任命",
            "成就等级判断": "待反馈项目成果与组织评价",
            "收入层级判断": context.get("财富裁决结论", "待补充"),
            "资产层级判断": "待反馈资产与负债",
            "财富状态判断": "待反馈现金流与波动",
            "感情状态判断": context.get("婚姻裁决结论", "待补充"),
            "婚姻质量判断": "待反馈关系稳定性",
            "配偶学历判断": "待反馈",
            "配偶事业判断": "待反馈",
            "配偶财富判断": "待反馈",
            "配偶外貌判断": "待反馈",
            "配偶气质判断": "待反馈",
            "体质判断": context.get("健康裁决结论", "待补充"),
            "疾病风险判断": "待反馈体检、病史与风险事件",
            "健康状态判断": "待反馈健康状态",
            "寿元倾向判断": "只表达健康管理窗口，不预测具体死亡年龄",
        }
    )

    # 十五层摘要。
    context.update(
        {
            "十五层一原局承载": "由 chart 与结构裁判生成；MVP 已登记。",
            "十五层二月令气候": "由子平类与滴天髓类 runner 负责细化。",
            "十五层三用忌病药": "由结构命题与反证命题共同生成。",
            "十五层四做功路径": "由高德臣与段建业 runner 负责细化。",
            "十五层五十神宫位": "由段建业与杨清娟 runner 负责细化。",
            "十五层六事件类型": "由事件裁判输出，并进入预测账本。",
            "十五层七人物画面": "由杨清娟 runner 与反馈画像校准。",
            "十五层八正向证据": "五派支持命题汇总。",
            "十五层九反证降级": "反证命题、反馈失验与降级条件汇总。",
            "十五层十跨派冲突": "冲突由结构图边与裁判层记录，正文只展示冲突状态。",
            "十五层十一结构裁决": "结构合法性裁判已生成。",
            "十五层十二事件裁决": "事件落地裁判已生成。",
            "十五层十三应期触发": "概率应期裁判与主要事件账本共同生成。",
            "十五层十四预测登记": "主要事件 prediction-first 已登记。",
            "十五层十五可反馈断语": "每条主要预测保留证伪口径和反馈状态。",
        }
    )

    # 预测账本前五条。
    predictions = list(output.prediction_ledger.predictions)[:5]
    labels = ("一", "二", "三", "四", "五")
    for label, prediction in zip(labels, predictions):
        context[f"预测事件{label}领域"] = prediction.domain
        context[f"预测事件{label}应事"] = prediction.event_label
        context[f"预测事件{label}窗口"] = _prediction_window(prediction)
        context[f"预测事件{label}触发条件"] = _prediction_trigger(prediction)
        context[f"预测事件{label}概率区间"] = _prediction_probability(prediction)
        context[f"预测事件{label}置信状态"] = _prediction_confidence_state(prediction)
        context[f"预测事件{label}星级"] = _prediction_star(prediction)
        context[f"预测事件{label}证伪口径"] = _prediction_falsifier(prediction)
        context[f"预测事件{label}反馈状态"] = _prediction_feedback(prediction)

    # 待反馈区。
    for idx, prediction in enumerate(predictions[:3], start=1):
        zh = ("一", "二", "三")[idx - 1]
        context[f"预测反馈{zh}优先级"] = _prediction_star(prediction)
        context[f"预测反馈{zh}领域"] = prediction.domain
        context[f"预测反馈{zh}窗口"] = _prediction_window(prediction)
        context[f"预测反馈{zh}应事"] = prediction.event_label
        context[f"预测反馈{zh}要点"] = _prediction_falsifier(prediction)

    return {key: str(value) for key, value in context.items()}


def render_report_v6_from_output(
    output: V5Output,
    *,
    template_path: str | Path = "templates/report-v6.md",
    report_path: str = "",
    case_dir: str = "",
    feedback_path: str = "",
    report_items: list | None = None,
    arbitration_decisions: list | None = None,
) -> str:
    """从 V5Output 渲染 report-v6 Markdown。"""

    template_text = Path(template_path).read_text(encoding="utf-8")
    context = build_report_v6_context(
        output,
        template_text=template_text,
        report_path=report_path,
        case_dir=case_dir,
        feedback_path=feedback_path,
        report_items=report_items,
        arbitration_decisions=arbitration_decisions,
    )
    return render_template_text(template_text, context)


# ── 从结构化 run/decision 构建 report context ──────────────────────────────

_REPORT_DOMAINS = ("学业", "事业", "财富", "婚姻", "健康", "性格")
_STAGE_SUMMARY_KEYS = {
    "structure": "structure_summary",
    "event": "event_summary",
    "timing": "timing_summary",
}
_PUBLIC_SCHOOL_NAMES = {
    **SCHOOLS,
    "ren_tieshu": "任付红",
    "ren_fuhong": "任付红",
}
_INTERNAL_TOKEN_RE = re.compile(
    r"(?i)\b(?:claim|prediction)-[0-9a-z]+\b|\b(?:statement_id|statement_index|capability_posterior)\b|school_capability snapshot|Agent 工作记录"
)


def _public_school_name(school_id: str) -> str:
    return _PUBLIC_SCHOOL_NAMES.get(school_id, school_id.replace("_", " "))


def _safe_display_text(value: object) -> str:
    """删除结构化上游文本中不应进入展示层的内部标识。"""

    return re.sub(r"\s{2,}", " ", _INTERNAL_TOKEN_RE.sub("", str(value))).strip(" ：:；,，")


def _decision_leaves(decisions: Sequence[StageDecision]) -> list[StageDecision]:
    leaves: list[StageDecision] = []
    for decision in decisions:
        leaves.extend(decision.domain_decisions or (decision,))
    return leaves


def _decision_note(decision: StageDecision) -> str:
    labels = {
        "winner": "形成主结论",
        "coexist": "多派观点并列",
        "unresolved": "冲突未决",
        "conflict_resolved": "冲突已消解",
        "reject_all": "证据不足/本派克制",
    }
    rationale = _safe_display_text(decision.rationale)
    base = f"{decision.domain or '相关领域'}：{labels[decision.result]}"
    return f"{base}；{rationale}" if rationale else base


def build_report_context_from_frozen_run(
    frozen_run: FrozenBlindRun,
    tasks: Sequence[BlindTask],
    stage_decisions: Sequence[StageDecision] | None = None,
) -> dict[str, Any]:
    """从 FrozenBlindRun + StageDecision 构建不含内部 ID 的报告 ViewModel。"""

    task_by_id = {task.task_id: task for task in tasks}
    decisions = _decision_leaves(stage_decisions or ())
    decisions_by_task_stage = {(item.task_id, item.stage): item for item in decisions}
    winner_ids = {value for item in decisions for value in item.winner_claim_ids}
    minority_ids = {value for item in decisions for value in item.minority_claim_ids}
    has_explicit_sides = bool(winner_ids or minority_ids)

    domains: dict[str, dict[str, list[str]]] = {
        domain: {
            "conclusions": [],
            "minority_views": [],
            "high_risk_notes": [],
            "abstentions": [],
            "stage_notes": [],
        }
        for domain in _REPORT_DOMAINS
    }
    seen_task_ids: set[str] = set()

    for output in frozen_run.outputs:
        task = task_by_id.get(output.task_id)
        if task is None or task.domain not in domains:
            continue
        seen_task_ids.add(task.task_id)
        bucket = domains[task.domain]
        school_name = _public_school_name(output.school_id)
        if output.state == "unsupported":
            continue
        if output.state == "abstain":
            bucket["abstentions"].append(f"证据不足/本派克制（{school_name}）")
            continue

        for prediction in output.predictions:
            event = _safe_display_text(prediction.event_label)
            rationale = _safe_display_text(output.rationale)
            window = _safe_display_text(prediction.time_window.get("label", ""))
            detail = f"{school_name}：{event}"
            if rationale:
                detail += f"；{rationale}"
            if window:
                detail += f"；应期：{window}"

            is_minority = prediction.prediction_id in minority_ids
            is_winner = prediction.prediction_id in winner_ids
            if is_minority or (has_explicit_sides and not is_winner and any(
                item.task_id == task.task_id and item.result in {"winner", "conflict_resolved"}
                for item in decisions
            )):
                bucket["minority_views"].append(f"少数派观点：{detail}")
            elif task.high_risk:
                bucket["high_risk_notes"].append(f"高风险提示：{detail}，需关注风险窗口。")
            else:
                bucket["conclusions"].append(detail)

    for task in tasks:
        if task.domain not in domains:
            continue
        bucket = domains[task.domain]
        if task.task_id not in seen_task_ids or not any(
            bucket[key] for key in ("conclusions", "minority_views", "high_risk_notes", "abstentions")
        ):
            bucket["abstentions"].append("证据不足/本派克制")

    for decision in decisions:
        if decision.domain in domains:
            domains[decision.domain]["stage_notes"].append(_decision_note(decision))

    context: dict[str, Any] = {
        "domains": domains,
        "structure_summary": [],
        "event_summary": [],
        "timing_summary": [],
    }
    for decision in decisions:
        context[_STAGE_SUMMARY_KEYS[decision.stage]].append(_decision_note(decision))
    return context


def build_comparison_summary(comparison: RunComparison) -> dict[str, Any]:
    """提取结构化并跑差异；仅保留公开领域、学派名与差异值。"""

    summary: dict[str, list[dict[str, Any]]] = {
        "coverage_delta": [],
        "state_diff": [],
        "high_risk_diff": [],
    }
    dimensions = (
        ("coverage_delta", "task_coverage"),
        ("state_diff", "claim_state"),
        ("high_risk_diff", "risk_flag"),
    )
    for item in comparison.items:
        for public_key, field_name in dimensions:
            difference = getattr(item, field_name)
            if difference.status in {"same", "both_missing"}:
                continue
            summary[public_key].append(
                {
                    "domain": item.domain,
                    "school": _public_school_name(item.school_id),
                    "status": difference.status,
                    "legacy": difference.legacy,
                    "structured": difference.claim,
                }
            )
    return summary

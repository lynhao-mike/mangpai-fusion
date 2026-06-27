"""ZiPing Fusion Engine v5 最小 runner 骨架。

该 runner 只建立五派命题图最小闭环，不实现具体命理断语。
真实规则应在后续 school runner 中独立产出 V5Claim，再交给本模块建图与仲裁。
"""

from __future__ import annotations

import hashlib
from collections import defaultdict
from pathlib import Path
from typing import Any

import yaml

from engine.application.production_rule_loader import ProductionRule, load_default_production_library
from engine.v5.domain import (
    V5ArbitrationResult,
    V5Claim,
    V5Confidence,
    V5Evidence,
    V5LearningSignal,
    V5Output,
    V5Prediction,
    V5PredictionLedger,
    V5StructureGraph,
    V5_SCHOOLS,
)

PROBABILISTIC_DOMAIN_WHITELIST = {"学业", "事业", "财富", "婚姻", "健康"}
STRUCTURE_SCHOOLS = {"ziping", "ditiansui", "gao_dechen"}
EVENT_SCHOOLS = {"gao_dechen", "duan_jianye", "yang_qingjuan"}

BLIND_SCHOOL_INDEX_FILES: dict[str, str] = {
    "gao_dechen": "theory/gao/index.yaml",
    "duan_jianye": "theory/duan/index.yaml",
    "yang_qingjuan": "theory/yang/index.yaml",
}
BLIND_SCHOOL_SOURCE_IDS: dict[str, str] = {
    "gao_dechen": "gao",
    "duan_jianye": "duan",
    "yang_qingjuan": "yang",
}
BLIND_TOPIC_DOMAINS: dict[str, str] = {  # ponytail: 按实测覆盖调整，后续有遗漏再加
    "caiyun": "财富",
    "wealth": "财富",
    "career": "事业",
    "zhiye": "事业",
    "guan": "事业",
    "hunyin": "婚姻",
    "marriage": "婚姻",
    "jiankang": "健康",
    "health": "健康",
    "xueye": "学业",
    "education": "学业",
    "shensha": "健康",
    "dayun": "事业",
    "lifa": "事业",
    "xiangfa": "性格",
    "mingong": "总体",
}


def _stable_id(prefix: str, *parts: object) -> str:
    raw = "|".join(str(part) for part in parts)
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]
    return f"{prefix}-{digest}"


def _chart_label(chart: dict[str, Any]) -> str:
    pillars = chart.get("pillars") or chart.get("四柱") or chart.get("bazi") or "未提供四柱"
    if isinstance(pillars, dict):
        return "".join(str(pillars.get(key, "")) for key in ("year", "month", "day", "hour")) or str(pillars)
    if isinstance(pillars, list):
        return "".join(str(item) for item in pillars)
    return str(pillars)


def _confidence_from_production_rule(rule: ProductionRule) -> V5Confidence:
    tier = "★" * max(1, min(5, int(rule.confidence.star)))
    return V5Confidence(
        tier=tier,
        score=float(rule.confidence.posterior),
        note=f"来自生产规则库；N={rule.confidence.sample_n}。",
    )


def _claim_type_from_production_rule(rule: ProductionRule) -> str:
    trigger = rule.conditions.trigger
    if trigger in {"has_dayun", "has_xiaoyun", "has_liunian", "has_suiyun_interaction"}:
        return "timing_claim"
    return "structure_claim"


def build_ziping_production_claims(case_id: str, *, workspace_root: str = ".", chart: dict[str, Any] | None = None) -> list[V5Claim]:
    """把子平正式生产规则转为 v5 structure_law 命题。

    ponytail: 只输出 quantifiable=True 的规则；False 的规则保留在 YAML 中
    作为 knowledge base 备查，不进入裁判器命题池。
    """

    library = load_default_production_library(workspace_root=workspace_root)
    ziping_rules = library.rule_sets.get("ziping")
    if not ziping_rules:
        return []

    selected = [rule for rule in ziping_rules.rules if rule.quantifiable]
    if chart is not None:
        selected.sort(key=lambda rule: _production_rule_rank(rule, chart))

    claims: list[V5Claim] = []
    for rule in selected:
        evidence = V5Evidence(
            evidence_id=_stable_id("v5ev", case_id, rule.id),
            source=rule.source.path,
            text=rule.source.excerpt,
            node_refs=["chart:root"],
            rule_ids=[rule.id],
            metadata={
                "expert_system": rule.expert_system,
                "topic": rule.topic,
                "trigger": rule.conditions.trigger,
                "source_scope": "production_rules",
            },
        )
        claims.append(
            V5Claim(
                claim_id=_stable_id("v5cl", case_id, rule.id),
                school="ziping",
                domain=rule.domains[0] if rule.domains else "总体",
                claim=rule.output.statement,
                claim_type=_claim_type_from_production_rule(rule),  # type: ignore[arg-type]
                stance="support",
                polarity="neutral",
                confidence=_confidence_from_production_rule(rule),
                evidence=[evidence],
                probabilistic=False,
                falsifiable=rule.output.falsifiable,
                metadata={
                    "case_id": case_id,
                    "rule_id": rule.id,
                    "topic": rule.topic,
                    "layer": rule.layer,
                    "review_notes": rule.review_notes,
                    "source_scope": "production_rules",
                    "runner_state": "production_rule",
                },
            )
        )
    return claims


def _wuxing_counts(text: str) -> dict[str, int]:
    """按干支粗略统计五行分布，供滴天髓 MVP 判断偏枯与流通。"""

    mapping = {
        "木": set("甲乙寅卯"),
        "火": set("丙丁巳午"),
        "土": set("戊己辰戌丑未"),
        "金": set("庚辛申酉"),
        "水": set("壬癸亥子"),
    }
    return {wuxing: sum(1 for char in text if char in chars) for wuxing, chars in mapping.items()}


def _dominant_wuxing(counts: dict[str, int]) -> tuple[str, int]:
    return max(counts.items(), key=lambda item: item[1])


def _missing_wuxing(counts: dict[str, int]) -> list[str]:
    return [name for name, count in counts.items() if count == 0]


def _evidence(case_id: str, source: str, text: str, *parts: object, rule_id: str = "") -> V5Evidence:
    """构造 v5 MVP 证据片段。"""

    return V5Evidence(
        evidence_id=_stable_id("v5ev", case_id, source, *parts),
        source=source,
        text=text,
        node_refs=["chart:root"],
        rule_ids=[rule_id] if rule_id else [],
        metadata={"source_scope": "v5_mvp_runner"},
    )


def _chart_pillars_text(chart: dict[str, Any]) -> str:
    pillars = chart.get("pillars") or {}
    if isinstance(pillars, dict):
        return "".join(str(pillars.get(key, "")) for key in ("year", "month", "day", "hour"))
    return _chart_label(chart)


def _chart_has_zhi_chong(chart: dict[str, Any]) -> bool:
    text = _chart_pillars_text(chart) + str(chart.get("current_dayun") or "") + str(chart.get("current_year") or "")
    return any(left in text and right in text for left, right in (("子", "午"), ("丑", "未"), ("寅", "申"), ("卯", "酉"), ("辰", "戌"), ("巳", "亥")))


def _production_rule_text(rule: ProductionRule) -> str:
    return "".join(
        [
            rule.id,
            rule.topic,
            rule.title,
            rule.output.statement,
            rule.source.excerpt,
            rule.conditions.trigger,
        ]
    )


def _production_rule_chart_score(rule: ProductionRule, chart: dict[str, Any]) -> int:
    """按命盘文本给生产规则轻量排序分。

    ponytail: 不新增命理判断，只让已存在规则中明示的干支、冲合、岁运词优先。
    """

    rule_text = _production_rule_text(rule)
    chart_text = _chart_pillars_text(chart) + str(chart.get("current_dayun") or "") + str(chart.get("current_year") or "")
    score = sum(1 for char in set(chart_text) if char in "甲乙丙丁戊己庚辛壬癸子丑寅卯辰巳午未申酉戌亥" and char in rule_text)
    if _chart_has_zhi_chong(chart) and any(token in rule_text for token in ("冲", "刑", "穿", "破", "悖")):
        score += 3
    if any(token in rule.conditions.trigger for token in ("dayun", "liunian", "suiyun", "xiaoyun")) or any(token in rule_text for token in ("大运", "流年", "岁运", "应期")):
        score += 2
    return score


def _production_rule_rank(rule: ProductionRule, chart: dict[str, Any]) -> tuple[int, int, float, str]:
    return (-_production_rule_chart_score(rule, chart), _domain_rank(rule), -rule.confidence.posterior, rule.id)


def _ditiansui_rule_triggered(rule: ProductionRule, chart: dict[str, Any]) -> bool:
    trigger = rule.conditions.trigger
    if trigger in {"always", "has_energy_structure", "has_tiaohou_advice"}:
        return True
    if trigger == "wuxing_imbalanced":
        return bool(_missing_wuxing(_wuxing_counts(_chart_pillars_text(chart))))
    if trigger == "has_zhi_chong":
        return _chart_has_zhi_chong(chart)
    return False


def _domain_rank(rule: ProductionRule) -> int:
    preferred = ("事业", "财富", "婚姻", "健康", "学业", "性格", "总体")
    for idx, domain in enumerate(preferred):
        if domain in rule.domains:
            return idx
    return len(preferred)


def build_ditiansui_production_claims(
    chart: dict[str, Any],
    case_id: str,
    *,
    workspace_root: str = ".",
    limit: int = 12,
) -> list[V5Claim]:
    """筛选滴天髓生产规则转为 v5 气势命题。

    ponytail: 只输出 quantifiable=True 的规则；False 的规则是纯原文堆叠，
    保留在 YAML 中作为 knowledge base 备查，不进入裁判器命题池。
    """

    library = load_default_production_library(workspace_root=workspace_root)
    rule_set = library.rule_sets.get("tiaohou_ditiansui")
    if not rule_set:
        return []

    selected = [rule for rule in rule_set.rules if rule.quantifiable and _ditiansui_rule_triggered(rule, chart)]
    selected.sort(key=lambda rule: _production_rule_rank(rule, chart))
    claims: list[V5Claim] = []
    for rule in selected[:limit]:
        evidence = V5Evidence(
            evidence_id=_stable_id("v5ev", case_id, rule.id),
            source=rule.source.path,
            text=rule.source.excerpt,
            node_refs=["chart:root"],
            rule_ids=[rule.id],
            metadata={
                "expert_system": rule.expert_system,
                "topic": rule.topic,
                "trigger": rule.conditions.trigger,
                "source_scope": "production_rules",
            },
        )
        claims.append(
            V5Claim(
                claim_id=_stable_id("v5cl", case_id, rule.id),
                school="ditiansui",
                domain=rule.domains[0] if rule.domains else "总体",
                claim=rule.output.statement,
                claim_type="structure_claim",
                stance="support",
                polarity="neutral",
                confidence=_confidence_from_production_rule(rule),
                evidence=[evidence],
                probabilistic=False,
                falsifiable=rule.output.falsifiable,
                metadata={
                    "case_id": case_id,
                    "rule_id": rule.id,
                    "topic": rule.topic,
                    "layer": rule.layer,
                    "review_notes": rule.review_notes,
                    "source_scope": "production_rules",
                    "runner_state": "production_rule",
                    "selection": "v6_preprod_limited",
                },
            )
        )
    return claims


def build_minimal_ditiansui_claims(chart: dict[str, Any], case_id: str) -> list[V5Claim]:
    """滴天髓 / 调候 MVP runner。

    重点先输出结构合法性命题：五行偏全、寒暖燥湿、气势顺逆、冲合流通。
    """

    pillars = _chart_pillars_text(chart)
    current_dayun = str(chart.get("current_dayun") or "当前大运")
    current_year = str(chart.get("current_year") or "当前流年")
    counts = _wuxing_counts(pillars)
    dominant, dominant_count = _dominant_wuxing(counts)
    missing = _missing_wuxing(counts)
    has_chong = ("寅" in pillars and "申" in pillars) or ("子" in pillars and "午" in (pillars + current_dayun + current_year)) or ("丑" in pillars and "未" in (pillars + current_dayun + current_year))
    has_flow = len([name for name, count in counts.items() if count > 0]) >= 4

    if missing:
        structure = f"五行有缺项（{','.join(missing)}），气势偏枯，事件判断需降级并寻找岁运补偏。"
        polarity = "negative"
        score = 0.56
    elif dominant_count >= 4:
        structure = f"{dominant}气偏旺，命局重在流通与制化，不能只按单一旺神取断。"
        polarity = "mixed"
        score = 0.58
    else:
        structure = "五行分布相对可流通，重点看顺逆、有情无情与岁运引动。"
        polarity = "positive"
        score = 0.6

    flow_note = "有冲动，流通与破格并见。" if has_chong else "冲动不显，先看原局气势顺逆。"
    if has_flow:
        flow_note += " 五行覆盖较全，具备流通讨论基础。"
    else:
        flow_note += " 五行覆盖不足，偏枯风险较高。"

    return [
        V5Claim(
            claim_id=_stable_id("v5cl", case_id, "ditiansui", pillars, current_dayun),
            school="ditiansui",
            domain="总体",
            claim=f"滴天髓气势裁判：{structure}{flow_note}",
            claim_type="structure_claim",
            stance="support",
            polarity=polarity,  # type: ignore[arg-type]
            confidence=V5Confidence(tier="★★★", score=score, note="滴天髓 MVP 气势 / 偏枯 / 流通 runner"),
            evidence=[_evidence(case_id, "ditiansui_mvp", f"五行统计={counts}；{flow_note}", pillars, rule_id="DTS-MVP-001")],
            counter_evidence=[],
            timing_hints=[{"label": f"{current_year} 至下一交运前", "basis": current_dayun}],
            probabilistic=False,
            falsifiable="若反馈显示该偏枯、流通或顺逆判断不能解释主要事件落地，则滴天髓 MVP 命题需降权或重写。",
            metadata={"runner_state": "mvp", "school_role": "qi_momentum", "wuxing_counts": counts},
        )
    ]


def _load_blind_school_rules(school: str, *, workspace_root: str = ".") -> list[dict[str, Any]]:
    """加载三盲派 index.yaml 规则。"""

    rel = BLIND_SCHOOL_INDEX_FILES[school]
    root = Path(workspace_root).resolve()
    path = (root / rel).resolve()
    if not path.exists():
        return []
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    rules = data.get("rules", [])
    return [item for item in rules if isinstance(item, dict)]


def _blind_rule_domain(rule: dict[str, Any]) -> str:
    topic = str(rule.get("topic", "")).lower()
    topic_label = str(rule.get("topic_label", "")).lower()
    title = str(rule.get("title", ""))
    conclusion = str(rule.get("conclusion", ""))
    haystack = " ".join([topic, topic_label, title, conclusion]).lower()
    for key, domain in BLIND_TOPIC_DOMAINS.items():
        if key.lower() in haystack:
            return domain
    if any(token in title + conclusion for token in ("财", "资产", "收入")):
        return "财富"
    if any(token in title + conclusion for token in ("官", "事业", "职业", "工作")):
        return "事业"
    if any(token in title + conclusion for token in ("婚", "配偶", "夫妻")):
        return "婚姻"
    if any(token in title + conclusion for token in ("病", "灾", "血", "寿", "健康")):
        return "健康"
    if any(token in title + conclusion for token in ("学", "文昌", "词馆")):
        return "学业"
    return "总体"


def _blind_rule_rank(rule: dict[str, Any]) -> tuple[int, float, str]:
    status = str(rule.get("status", "candidate"))
    status_rank = {"confirmed": 0, "promoted": 1, "active": 1, "candidate": 2}.get(status, 3)
    score = float(rule.get("candidate_score", 0.0) or 0.0)
    return (status_rank, -score, str(rule.get("id", "")))


def _blind_rule_chart_score(rule: dict[str, Any], chart: dict[str, Any]) -> int:
    """按命盘文本给三盲派规则一个轻量触发分。

    ponytail: 不写新命理规则，只让 index.yaml 中明确提到的干支、冲合、岁运词优先。
    """

    rule_text = "".join(str(rule.get(key, "")) for key in ("topic", "topic_label", "title", "conclusion"))
    chart_text = _chart_pillars_text(chart) + str(chart.get("current_dayun") or "") + str(chart.get("current_year") or "")
    score = sum(1 for char in set(chart_text) if char in "甲乙丙丁戊己庚辛壬癸子丑寅卯辰巳午未申酉戌亥" and char in rule_text)
    if _chart_has_zhi_chong(chart) and any(token in rule_text for token in ("冲", "刑", "穿", "破")):
        score += 3
    if any(token in chart_text for token in ("大运", "流年", "运")) and any(token in rule_text for token in ("大运", "流年", "应期", "交运")):
        score += 2
    return score


def _blind_rule_chart_rank(rule: dict[str, Any], chart: dict[str, Any]) -> tuple[int, int, float, str]:
    status_rank, neg_score, rule_id = _blind_rule_rank(rule)
    return (-_blind_rule_chart_score(rule, chart), status_rank, neg_score, rule_id)


def build_blind_school_rule_claims(
    chart: dict[str, Any],
    case_id: str,
    *,
    school: str,
    workspace_root: str = ".",
    limit: int = 8,
) -> list[V5Claim]:
    """把三盲派 index.yaml 规则筛选为 v5 命题。"""

    raw_rules = _load_blind_school_rules(school, workspace_root=workspace_root)
    if not raw_rules:
        return []
    source_school = BLIND_SCHOOL_SOURCE_IDS[school]
    selected = [
        rule for rule in raw_rules
        if str(rule.get("school", "")) == source_school
        and str(rule.get("status", "candidate")) not in {"deprecated", "rejected"}
    ]
    selected.sort(key=lambda rule: _blind_rule_chart_rank(rule, chart))
    claims: list[V5Claim] = []
    for rule in selected[:limit]:
        rule_id = str(rule.get("id", _stable_id("blindrule", school, rule.get("title", ""))))
        conclusion = str(rule.get("conclusion") or rule.get("title") or "三盲派规则参与。")
        domain = _blind_rule_domain(rule)
        evidence = V5Evidence(
            evidence_id=_stable_id("v5ev", case_id, rule_id),
            source=str(rule.get("raw_file") or BLIND_SCHOOL_INDEX_FILES[school]),
            text=conclusion,
            node_refs=["chart:root"],
            rule_ids=[rule_id],
            metadata={
                "school": school,
                "topic": str(rule.get("topic", "")),
                "status": str(rule.get("status", "")),
                "source_scope": "school_index_rules",
            },
        )
        claims.append(
            V5Claim(
                claim_id=_stable_id("v5cl", case_id, rule_id),
                school=school,  # type: ignore[arg-type]
                domain=domain,
                claim=f"{SCHOOL_DISPLAY_NAMES.get(school, school)}规则参与：{conclusion}",
                claim_type="event_claim" if domain in PROBABILISTIC_DOMAIN_WHITELIST else "structure_claim",  # type: ignore[arg-type]
                stance="support",
                polarity="neutral",
                confidence=V5Confidence(tier="★★★", score=0.55, note="三盲派 index.yaml 规则筛选接入"),
                evidence=[evidence],
                timing_hints=[{"label": f"{chart.get('current_year', '当前流年')} 至下一交运前", "basis": str(chart.get("current_dayun") or "当前大运")}],
                probabilistic=domain in PROBABILISTIC_DOMAIN_WHITELIST,
                falsifiable="若反馈显示该规则不能解释对应领域事件，则该规则需降权、合并或转入反证清单。",
                metadata={
                    "case_id": case_id,
                    "rule_id": rule_id,
                    "topic": str(rule.get("topic", "")),
                    "source_scope": "school_index_rules",
                    "runner_state": "school_rule",
                    "selection": "v6_preprod_blind_limited",
                },
            )
        )
    return claims


SCHOOL_DISPLAY_NAMES = {
    "gao_dechen": "高德臣",
    "duan_jianye": "段建业",
    "yang_qingjuan": "杨清娟",
}


def build_minimal_three_blind_claims(chart: dict[str, Any], case_id: str) -> list[V5Claim]:
    """高德臣 / 段建业 / 杨清娟三派 MVP 事件 runner。

    该实现只使用 chart DTO，可在旧 ParsedInput 未接入时先产出真实可裁判命题。
    后续可替换为各派完整 runner。
    """

    pillars = _chart_pillars_text(chart)
    current_dayun = str(chart.get("current_dayun") or "当前大运")
    current_year = str(chart.get("current_year") or "当前流年")
    claims: list[V5Claim] = []

    has_zi_wu = "子" in pillars and "午" in (pillars + current_dayun + current_year)
    has_yin_shen = "寅" in pillars and "申" in pillars
    has_zi_chou = "子" in pillars and "丑" in pillars
    has_metal_water = any(x in pillars for x in ("庚", "辛", "申")) and any(x in pillars for x in ("壬", "癸", "子"))

    # 高德臣：旁证、神煞、健康灾厄、贵人资源。
    gao_evidence = []
    if has_zi_wu:
        gao_evidence.append("子午冲或运年冲日支信号，健康、婚姻与压力事件需入预测账本")
    if has_yin_shen:
        gao_evidence.append("寅申冲动月令，事业环境与外部资源易被触发")
    if not gao_evidence:
        gao_evidence.append("高派 MVP 未发现强冲，先登记神煞旁证待完整 runner 接入")
    claims.append(
        V5Claim(
            claim_id=_stable_id("v5cl", case_id, "gao_dechen", pillars, current_dayun),
            school="gao_dechen",
            domain="健康" if has_zi_wu else "事业",
            claim="高德臣旁证：" + "；".join(gao_evidence),
            claim_type="event_claim",
            stance="support",
            polarity="mixed",
            confidence=V5Confidence(tier="★★★", score=0.58, note="高派 MVP 旁证 runner，待神煞库全量接入"),
            evidence=[_evidence(case_id, "gao_dechen_mvp", "；".join(gao_evidence), pillars, rule_id="G-MVP-001")],
            timing_hints=[{"label": f"{current_year} 至下一交运前", "basis": current_dayun}],
            probabilistic=True,
            falsifiable="若时间窗内无健康、压力、外部环境或资源事件，则本旁证预测降权。",
            metadata={"runner_state": "mvp", "school_role": "work_transformation"},
        )
    )

    # 段建业：体用、做功、事业财富落地。
    duan_text = "段建业事件框架："
    duan_points = []
    if has_metal_water:
        duan_points.append("印比资源明显，宜走平台、资质、组织身份与规则系统")
    if has_yin_shen:
        duan_points.append("月令被冲，事业做功有折损，成事更依赖外部结构和阶段性机会")
    if not duan_points:
        duan_points.append("做功路径待完整段派 runner 接入，本轮先登记事业财富可反馈槽位")
    claims.append(
        V5Claim(
            claim_id=_stable_id("v5cl", case_id, "duan_jianye", pillars, current_dayun),
            school="duan_jianye",
            domain="事业",
            claim=duan_text + "；".join(duan_points),
            claim_type="event_claim",
            stance="support",
            polarity="neutral",
            confidence=V5Confidence(tier="★★★", score=0.6, note="段派 MVP 事业财富 runner，待做功层数接入"),
            evidence=[_evidence(case_id, "duan_jianye_mvp", "；".join(duan_points), pillars, rule_id="M1-MVP-001")],
            timing_hints=[{"label": f"{current_year} 至下一交运前", "basis": current_dayun}],
            probabilistic=True,
            falsifiable="若时间窗内无事业职责、平台、项目、财富或资源变化，则本事业预测降权。",
            metadata={"runner_state": "mvp", "school_role": "event_framework"},
        )
    )
    claims.append(
        V5Claim(
            claim_id=_stable_id("v5cl", case_id, "duan_jianye", "wealth", pillars),
            school="duan_jianye",
            domain="财富",
            claim="段建业财富落地：财富先随事业平台、项目资源与组织身份变化，不先断投机暴发。",
            claim_type="event_claim",
            stance="support",
            polarity="neutral",
            confidence=V5Confidence(tier="★★", score=0.48, note="MVP 财富事件槽位"),
            evidence=[_evidence(case_id, "duan_jianye_mvp", "财富随事业平台与项目资源落地", pillars, rule_id="M1-MVP-002")],
            timing_hints=[{"label": f"{current_year} 至下一交运前", "basis": current_dayun}],
            probabilistic=True,
            falsifiable="若时间窗内收入、资产、项目资金和重大支出均无变化，则本预测失验。",
            metadata={"runner_state": "mvp", "school_role": "event_framework"},
        )
    )

    # 杨清娟：婚姻、人物画面、关系资源。
    yang_points = []
    if has_zi_chou:
        yang_points.append("子丑合提示婚姻、家庭责任或资源绑定，不宜简单等同婚破")
    if has_yin_shen:
        yang_points.append("寅申冲提示关系中的外部环境、迁动或资源变化")
    if not yang_points:
        yang_points.append("人物关系画面待完整象法 runner 接入，本轮先登记婚姻家庭反馈槽位")
    claims.append(
        V5Claim(
            claim_id=_stable_id("v5cl", case_id, "yang_qingjuan", pillars, current_dayun),
            school="yang_qingjuan",
            domain="婚姻",
            claim="杨清娟象法：" + "；".join(yang_points),
            claim_type="event_claim",
            stance="support",
            polarity="mixed",
            confidence=V5Confidence(tier="★★★", score=0.56, note="杨派 MVP 婚姻家庭 runner，待象法规则全量接入"),
            evidence=[_evidence(case_id, "yang_qingjuan_mvp", "；".join(yang_points), pillars, rule_id="M2-MVP-001")],
            timing_hints=[{"label": f"{current_year} 至下一交运前", "basis": current_dayun}],
            probabilistic=True,
            falsifiable="若时间窗内婚恋关系、家庭责任、配偶资源或关系压力均无变化，则本预测失验。",
            metadata={"runner_state": "mvp", "school_role": "image_detail"},
        )
    )
    return claims


def build_abstain_claims(
    chart: dict[str, Any],
    case_id: str,
    *,
    schools: tuple[str, ...] = V5_SCHOOLS,
) -> list[V5Claim]:
    """为尚未接入真实规则的流派生成占位命题。"""

    label = _chart_label(chart)
    school_claim_text = {
        "ziping": "子平类 runner 尚未接入生产规则；当前仅登记结构法度待判。",
        "ditiansui": "滴天髓类 runner 尚未接入生产规则；当前仅登记气势清浊待判。",
        "gao_dechen": "高德臣 runner 尚未接入生产规则；当前仅登记做功转化待判。",
        "duan_jianye": "段建业 runner 尚未接入生产规则；当前仅登记事件框架待判。",
        "yang_qingjuan": "杨清娟 runner 尚未接入生产规则；当前仅登记象法细节待判。",
    }
    claim_type = {
        "ziping": "structure_claim",
        "ditiansui": "structure_claim",
        "gao_dechen": "event_claim",
        "duan_jianye": "event_claim",
        "yang_qingjuan": "event_claim",
    }
    claims: list[V5Claim] = []
    for school in schools:
        evidence = V5Evidence(
            evidence_id=_stable_id("v5ev", case_id, school, label),
            source="chart_model",
            text=f"五派共用同一 Chart Model：{label}",
            node_refs=["chart:root"],
            metadata={"runner_state": "stub"},
        )
        claims.append(
            V5Claim(
                claim_id=_stable_id("v5cl", case_id, school, label),
                school=school,  # type: ignore[arg-type]
                domain="总体",
                claim=school_claim_text[school],
                claim_type=claim_type[school],  # type: ignore[arg-type]
                stance="abstain",
                polarity="neutral",
                confidence=V5Confidence(tier="★", score=0.1, note="runner 骨架占位，不进入正式断语"),
                evidence=[evidence],
                probabilistic=False,
                falsifiable="接入真实五派 runner 后，占位命题应消失。",
                metadata={"case_id": case_id, "school_role": "see V5_SCHOOL_ROLES", "runner_state": "stub"},
            )
        )
    return claims


def build_default_claims(chart: dict[str, Any], case_id: str, *, workspace_root: str = ".") -> list[V5Claim]:
    """默认运行子平 / 滴天髓生产规则 + 三盲派规则筛选 runner。

    ponytail: 子平独立分析的两层结构命题（月令旺衰 + 格局用神）以最高优先级
    前置，让结构合法性仲裁拿到更精确的定性命题，不依赖旧生产规则平铺顺序。
    """

    from engine.v5.ziping_runner import run_ziping_independent  # ponytail: lazy import，避免循环
    ziping_independent_claims = run_ziping_independent(chart, case_id)

    ziping_claims = build_ziping_production_claims(case_id, workspace_root=workspace_root, chart=chart)
    # 去重：独立分析命题与生产规则命题可能覆盖同一 domain，但 claim_id 不同，保留两者。
    ziping_claims = ziping_independent_claims + ziping_claims
    ditiansui_claims = build_ditiansui_production_claims(chart, case_id, workspace_root=workspace_root)
    if not ditiansui_claims:
        ditiansui_claims = build_minimal_ditiansui_claims(chart, case_id)
    blind_rule_claims: list[V5Claim] = []
    for school in ("gao_dechen", "duan_jianye", "yang_qingjuan"):
        blind_rule_claims.extend(build_blind_school_rule_claims(chart, case_id, school=school, workspace_root=workspace_root))
    blind_claims = blind_rule_claims or build_minimal_three_blind_claims(chart, case_id)
    active_schools = {claim.school for claim in ziping_claims + ditiansui_claims + blind_claims}
    stub_schools = tuple(school for school in V5_SCHOOLS if school not in active_schools)
    return ziping_claims + ditiansui_claims + blind_claims + build_abstain_claims(chart, case_id, schools=stub_schools)


def build_structure_graph(case_id: str, chart: dict[str, Any], claims: list[V5Claim]) -> V5StructureGraph:
    """把 chart、五派命题、证据与领域挂入最小结构图。"""

    nodes: list[dict[str, Any]] = [
        {"id": "chart:root", "type": "chart", "label": _chart_label(chart), "payload": dict(chart)},
    ]
    edges: list[dict[str, Any]] = []
    seen_domains: set[str] = set()

    for claim in claims:
        claim_node_id = f"claim:{claim.claim_id}"
        domain_node_id = f"domain:{claim.domain}"
        if claim.domain not in seen_domains:
            nodes.append({"id": domain_node_id, "type": "domain", "label": claim.domain})
            seen_domains.add(claim.domain)
        nodes.append(
            {
                "id": claim_node_id,
                "type": "claim",
                "label": claim.claim,
                "school": claim.school,
                "school_role": claim.role,
                "claim_type": claim.claim_type,
            }
        )
        edges.append({"source": "chart:root", "target": claim_node_id, "type": "feeds"})
        edges.append({"source": claim_node_id, "target": domain_node_id, "type": "targets"})

        for evidence in claim.evidence:
            evidence_node_id = f"evidence:{evidence.evidence_id}"
            nodes.append({"id": evidence_node_id, "type": "evidence", "label": evidence.text, "source": evidence.source})
            edges.append({"source": evidence_node_id, "target": claim_node_id, "type": "supports"})

        for evidence in claim.counter_evidence:
            evidence_node_id = f"evidence:{evidence.evidence_id}"
            nodes.append({"id": evidence_node_id, "type": "evidence", "label": evidence.text, "source": evidence.source})
            edges.append({"source": evidence_node_id, "target": claim_node_id, "type": "weakens"})

    return V5StructureGraph(case_id=case_id, nodes=nodes, edges=edges)


def arbitrate_claims(claims: list[V5Claim]) -> list[V5ArbitrationResult]:
    """生成最小三段式仲裁结果。

    MVP 只根据 claim_type、stance、school role 形成可解释骨架；真实权重、生命周期、
    历史命中率与冲突分类后续接入。
    """

    claims_by_domain: dict[str, list[V5Claim]] = defaultdict(list)
    for claim in claims:
        claims_by_domain[claim.domain].append(claim)

    results: list[V5ArbitrationResult] = []
    for domain, domain_claims in sorted(claims_by_domain.items()):
        support_claims = [c for c in domain_claims if c.stance == "support"]
        oppose_claims = [c for c in domain_claims if c.stance == "oppose"]
        abstain_claims = [c for c in domain_claims if c.stance == "abstain"]
        structure_claims = [c for c in domain_claims if c.school in STRUCTURE_SCHOOLS or c.claim_type == "structure_claim"]
        event_claims = [c for c in domain_claims if c.school in EVENT_SCHOOLS or c.claim_type == "event_claim"]
        probabilistic_allowed = domain in PROBABILISTIC_DOMAIN_WHITELIST and any(c.probabilistic for c in domain_claims)
        conflict_type = "stance_conflict" if support_claims and oppose_claims else "none"

        structure_winners = [c.school for c in structure_claims if c.stance != "abstain"]
        event_winners = [c.school for c in event_claims if c.stance != "abstain"]
        minority = [c.claim_id for c in oppose_claims]

        if len(abstain_claims) == len(domain_claims):
            structure_conclusion = "五派 runner 尚未产生可仲裁结构命题。"
            event_conclusion = "五派 runner 尚未产生可仲裁事件命题。"
            confidence = V5Confidence(tier="★", score=0.1, note="全员弃权，占位输出")
        else:
            structure_conclusion = "结构合法性仲裁已形成候选结论。"
            event_conclusion = "事件落地仲裁已形成候选结论。"
            confidence = V5Confidence(tier="★★★", score=0.6, note="MVP 仲裁，尚未接入历史校准")

        results.append(
            V5ArbitrationResult(
                domain=domain,
                stage="structure_legality",
                conclusion=structure_conclusion,
                winning_schools=structure_winners,
                minority_claims=minority,
                support_score=float(len([c for c in structure_claims if c.stance == "support"])),
                opposition_score=float(len([c for c in structure_claims if c.stance == "oppose"])),
                conflict_type=conflict_type,
                confidence=confidence,
                rationale="子平类、滴天髓类与高德臣优先参与结构合法性判断。",
                probabilistic_allowed=False,
            )
        )
        results.append(
            V5ArbitrationResult(
                domain=domain,
                stage="event_realization",
                conclusion=event_conclusion,
                winning_schools=event_winners,
                minority_claims=minority,
                support_score=float(len([c for c in event_claims if c.stance == "support"])),
                opposition_score=float(len([c for c in event_claims if c.stance == "oppose"])),
                conflict_type=conflict_type,
                confidence=confidence,
                rationale="高德臣、段建业、杨清娟优先参与事件落地判断，子平/滴天髓提供结构约束。",
                probabilistic_allowed=probabilistic_allowed,
            )
        )
        results.append(
            V5ArbitrationResult(
                domain=domain,
                stage="probability_timing",
                conclusion="仅白名单事件且具备时间窗与反馈标签时允许概率化。",
                winning_schools=[c.school for c in domain_claims if c.probabilistic],
                minority_claims=[],
                support_score=float(len([c for c in domain_claims if c.probabilistic])),
                opposition_score=0.0,
                conflict_type="none",
                confidence=V5Confidence(tier="★★", score=0.4, note="概率层 MVP 只登记许可，不伪精确"),
                rationale="性格、格局高低、宽泛气质描述不进入概率层。",
                probabilistic_allowed=probabilistic_allowed,
            )
        )
    return results


def _default_prediction_specs(chart: dict[str, Any]) -> list[dict[str, Any]]:
    """主要事件 prediction-first 的 MVP 默认账本。

    在真实 school runner 尚未全量接入前，先保证每个主要事件都有
    可反馈预测槽位。后续由 claims、taxonomy 与反馈统计逐步替换默认文案。
    """

    current_dayun = str(chart.get("current_dayun") or chart.get("当前大运") or "当前大运")
    current_year = str(chart.get("current_year") or chart.get("当前流年") or "当前流年")
    return [
        {
            "domain": "事业",
            "event_label": "事业职责、岗位或组织关系出现可反馈变化",
            "time_window": {"label": f"{current_year} 至下一交运前", "basis": current_dayun},
            "trigger_conditions": ["大运触发", "流年触发", "结构裁判允许事件落地"],
            "falsifier": "若时间窗内无岗位、职责、组织关系、项目压力或考核变化，则本预测失验。",
            "probability_range": (0.45, 0.65),
            "tier": "★★★",
            "score": 0.55,
        },
        {
            "domain": "财富",
            "event_label": "收入、项目资金、资源调动或支出压力出现变化",
            "time_window": {"label": f"{current_year} 至下一交运前", "basis": current_dayun},
            "trigger_conditions": ["财官事件落地", "事业平台牵动财富", "反馈口径可量化"],
            "falsifier": "若时间窗内收入、资产、负债、项目资金与重大支出均无变化，则本预测失验。",
            "probability_range": (0.4, 0.6),
            "tier": "★★★",
            "score": 0.5,
        },
        {
            "domain": "婚姻",
            "event_label": "婚恋关系、配偶资源、家庭责任或关系压力出现可反馈变化",
            "time_window": {"label": f"{current_year} 至下一交运前", "basis": current_dayun},
            "trigger_conditions": ["夫妻宫或配偶资源被触发", "事业财富牵动家庭", "事件裁判允许落地"],
            "falsifier": "若时间窗内婚恋关系、配偶资源、家庭责任与关系压力均无明显变化，则本预测失验。",
            "probability_range": (0.35, 0.55),
            "tier": "★★",
            "score": 0.45,
        },
        {
            "domain": "健康",
            "event_label": "体检异常、慢病指标、突发伤病或压力性健康问题需要关注",
            "time_window": {"label": f"{current_year} 至下一交运前", "basis": current_dayun},
            "trigger_conditions": ["健康风险白名单", "冲合刑害或神煞旁证", "必须以反馈确认"],
            "falsifier": "若时间窗内无体检异常、伤病、手术、慢病指标波动或明显压力症状，则本预测失验。",
            "probability_range": (0.3, 0.5),
            "tier": "★★",
            "score": 0.4,
        },
        {
            "domain": "学业",
            "event_label": "考试、证照、培训、学历或技能升级出现可反馈节点",
            "time_window": {"label": f"{current_year} 至下一交运前", "basis": current_dayun},
            "trigger_conditions": ["印星或学习类结构触发", "存在现实学习目标", "反馈口径可定义"],
            "falsifier": "若时间窗内无考试、证照、培训、学历或技能升级事项，则本预测失验或跳过。",
            "probability_range": (0.25, 0.45),
            "tier": "★★",
            "score": 0.35,
        },
    ]


def build_prediction_ledger(case_id: str, claims: list[V5Claim], chart: dict[str, Any] | None = None) -> V5PredictionLedger:
    """从可概率化命题生成受限概率 ledger。

    v5 概率层只登记具体、可反馈、处于白名单领域的事件命题；
    性格、总体结构、无时间窗的宽泛判断不生成概率条目。
    若 runner 尚未产生足够可概率化命题，则生成主要事件 MVP 预测槽位，
    保证 prediction-first 闭环可见。
    """

    predictions: list[V5Prediction] = []
    for spec in _default_prediction_specs(chart or {}):
        predictions.append(
            V5Prediction(
                prediction_id=_stable_id("v5pred", case_id, spec["domain"], spec["event_label"]),
                domain=spec["domain"],
                event_label=spec["event_label"],
                probability_range=spec["probability_range"],
                confidence=V5Confidence(tier=spec["tier"], score=spec["score"], note="prediction-first MVP 默认主要事件槽位"),
                time_window=spec["time_window"],
                trigger_conditions=list(spec["trigger_conditions"]),
                falsifier=spec["falsifier"],
                calibration_note="默认主要事件预测；后续由五派 runner、反馈样本与事件 taxonomy 校准。",
            )
        )

    existing_domains = {item.domain for item in predictions}
    for claim in claims:
        if not claim.probabilistic or claim.domain not in PROBABILISTIC_DOMAIN_WHITELIST or claim.domain in existing_domains:
            continue
        time_window = dict(claim.timing_hints[0]) if claim.timing_hints else {}
        predictions.append(
            V5Prediction(
                prediction_id=_stable_id("v5pred", case_id, claim.claim_id, claim.domain),
                domain=claim.domain,
                event_label=claim.claim,
                probability_range=(0.35, 0.55),
                confidence=V5Confidence(tier="★★", score=0.4, note="MVP 概率范围，需反馈校准"),
                time_window=time_window,
                trigger_conditions=["可概率化命题", "白名单领域", "等待反馈校准"],
                falsifier=claim.falsifiable or "若时间窗内未发生该事件，则本预测失验。",
                calibration_note="由可概率化 V5Claim 登记；样本不足，暂不伪精确。",
            )
        )
        existing_domains.add(claim.domain)
    return V5PredictionLedger(case_id=case_id, predictions=predictions)


def build_learning_signals(case_id: str, claims: list[V5Claim], ledger: V5PredictionLedger) -> list[V5LearningSignal]:
    """生成学习信号占位，确保反馈回归有稳定挂载点。"""

    signals: list[V5LearningSignal] = []
    for claim in claims:
        signals.append(
            V5LearningSignal(
                signal_id=_stable_id("v5sig", case_id, claim.claim_id),
                case_id=case_id,
                target_id=claim.claim_id,
                signal_type="claim_trace_registered",
                value="pending_feedback",
                note="命题已进入 v5 图谱，等待 feedback.md 或 prediction ledger 绑定。",
            )
        )
    for prediction in ledger.predictions:
        signals.append(
            V5LearningSignal(
                signal_id=_stable_id("v5sig", case_id, prediction.prediction_id),
                case_id=case_id,
                target_id=prediction.prediction_id,
                signal_type="prediction_registered",
                value="pending_feedback",
                note="受限概率预测已登记，等待反馈校准。",
            )
        )
    return signals


def run_v5(
    chart: dict[str, Any],
    *,
    case_id: str = "",
    claims: list[V5Claim] | None = None,
    workspace_root: str = ".",
) -> V5Output:
    """运行 v5 五派命题图最小闭环。

    参数：
    - chart：五派共享的标准命盘对象。
    - case_id：案例 ID；缺省时从 chart.case_id 推断。
    - claims：外部真实 school runner 产出的命题；传入时完全覆盖默认生产规则。
    - workspace_root：生产规则库根目录；测试隔离时使用。
    """

    resolved_case_id = case_id or str(chart.get("case_id", "V5-UNTRACKED"))
    resolved_claims = (
        list(claims)
        if claims is not None
        else build_default_claims(chart, resolved_case_id, workspace_root=workspace_root)
    )
    graph = build_structure_graph(resolved_case_id, chart, resolved_claims)
    arbitration_results = arbitrate_claims(resolved_claims)
    ledger = build_prediction_ledger(resolved_case_id, resolved_claims, chart)
    learning_signals = build_learning_signals(resolved_case_id, resolved_claims, ledger)
    return V5Output(
        case_id=resolved_case_id,
        chart=dict(chart),
        claims=resolved_claims,
        structure_graph=graph,
        arbitration_results=arbitration_results,
        prediction_ledger=ledger,
        learning_signals=learning_signals,
    )

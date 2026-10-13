"""ZiPing Fusion Engine v5 最小 runner 骨架。

该 runner 只建立五派命题图最小闭环，不实现具体命理断语。
真实规则应在后续 school runner 中独立产出 V5Claim，再交给本模块建图与仲裁。
"""

from __future__ import annotations

import hashlib
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

import yaml

from engine.application.production_rule_loader import ProductionRule, load_default_production_library
from engine.predicates.condition_evaluator import (
    evaluate_trigger,
    rank_blind_rule,
    score_blind_rule,
)
from engine.v5.domain import (
    V5ArbitrationResult,
    V5Claim,
    V5Confidence,
    V5Evidence,
    V5LearningSignal,
    V5Output,
    V5Prediction,
    V5RunSnapshot,
    V5PredictionLedger,
    V5StructureGraph,
    V5_SCHOOLS,
)
from engine.v5.adjudication import build_v5_adjudication_units

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

_DOMAIN_TARGET_PREFIXES = {
    "事业": "career",
    "财富": "wealth",
    "婚姻": "marriage",
    "健康": "health",
    "学业": "education",
    "性格": "personality",
    "总体": "overall",
}


def _target_id_from_existing_topic(domain: str, *topics: object) -> str:
    """把已有规则 topic 规范成内部 target_id；不创造现实 outcome 标签。"""

    topic = next((str(item).strip() for item in topics if str(item).strip()), "")
    if not topic:
        return ""
    normalized = re.sub(r"[^0-9A-Za-z\u3400-\u9fff]+", "_", topic).strip("_").lower()
    prefix = _DOMAIN_TARGET_PREFIXES.get(domain, "")
    return f"{prefix}.{normalized}" if prefix and normalized else ""


# ── 婚姻应期推导（杨清娟 M2-Y-141: 印来+配偶星到=结婚年） ──────────────────────

_YIN_BRANCHES = {"亥", "子"}  # 水=印（甲木）
_CAI_STEMS = {"己", "戊"}     # 土=财（正财/偏财，甲木视角）

_JIAZI_CYCLE: list[str] = [
    "甲子", "乙丑", "丙寅", "丁卯", "戊辰", "己巳", "庚午", "辛未", "壬申", "癸酉",
    "甲戌", "乙亥", "丙子", "丁丑", "戊寅", "己卯", "庚辰", "辛巳", "壬午", "癸未",
    "甲申", "乙酉", "丙戌", "丁亥", "戊子", "己丑", "庚寅", "辛卯", "壬辰", "癸巳",
    "甲午", "乙未", "丙申", "丁酉", "戊戌", "己亥", "庚子", "辛丑", "壬寅", "癸卯",
    "甲辰", "乙巳", "丙午", "丁未", "戊申", "己酉", "庚戌", "辛亥", "壬子", "癸丑",
    "甲寅", "乙卯", "丙辰", "丁巳", "戊午", "己未", "庚申", "辛酉", "壬戌", "癸亥",
]

def _ganzhi_for_year(year: int) -> str:
    """返回公历年对应的干支。"""
    idx = (year - 4) % 60
    return _JIAZI_CYCLE[idx]


def _estimate_marriage_timing(chart: dict[str, Any]) -> list[dict[str, Any]]:
    """最小婚期推导：只对乾造（男命）执行。

    杨清娟 M2-Y-141 判断条件：印来 + 配偶星到。
    MVP 口径：若大运已是财运（配偶星到运），则财年为次选、亥年合动夫妻宫为首选。
    返回 timing_hints 列表，按优先级排序。
    """
    gender = str(chart.get("gender_marker", "")).lower()
    if gender not in {"乾", "m", "male"}:
        return []

    day_branch = str(chart.get("day_branch", ""))
    dayun_summary = str(chart.get("dayun_summary", ""))
    results: list[tuple[int, str, str]] = []  # (priority, label, year_gz)

    # 从 dayun_summary 解析各大运干支与起讫年
    import re as _re
    for m in _re.finditer(r"([^：；]+)运：(\d{4})-(\d{4})", dayun_summary):
        dy_gz = m.group(1).strip()
        dy_start = int(m.group(2))
        dy_end = int(m.group(3))
        dy_stem = dy_gz[:1] if dy_gz else ""
        # 只扫财星运（天干为土=己/戊）
        if dy_stem not in _CAI_STEMS:
            continue
        for yr in range(dy_start, dy_end):
            gz = _ganzhi_for_year(yr)
            stem = gz[:1]
            branch = gz[1:]
            has_cai_year = stem in _CAI_STEMS
            has_spouse_palace_he = day_branch == "寅" and branch == "亥"
            if has_spouse_palace_he:
                results.append((0, f"{yr} {gz}年（首选婚期，财运中印来+夫妻宫六合，±1年）", gz))
            elif has_cai_year:
                results.append((1, f"{yr} {gz}年（次选婚期，财运中财星流年触发，±1年）", gz))

    if not results:
        return []
    results.sort(key=lambda x: x[0])
    return [{"label": r[1], "basis": "杨清娟婚期三步法（M2-Y-141）"} for r in results[:3]]


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
        target_id = _target_id_from_existing_topic(rule.domains[0] if rule.domains else "总体", rule.topic)
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
                    "task_id": target_id,
                    "target_id": target_id,
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


def _production_rule_chart_score(rule: ProductionRule, chart: dict[str, Any]) -> float:
    """用谓词求值替代字符袋计数给生产规则排序分。

    ponytail: 触发器匹配 + condition_evaluator 打分，不写新命理。
    """
    # 触发器不匹配直接返回 0，不浪费排序权重
    if not evaluate_trigger(rule.conditions.trigger, chart):
        return 0.0
    # 基础分 = 置信度后验
    base = float(rule.confidence.posterior)
    # 触发器涉及大运流年的规则在有岁运时额外加分
    if any(tok in rule.conditions.trigger for tok in ("dayun", "liunian", "suiyun", "xiaoyun")):
        base += 0.05
    return base


def _production_rule_rank(rule: ProductionRule, chart: dict[str, Any]) -> tuple[float, int, float, str]:
    return (-_production_rule_chart_score(rule, chart), _domain_rank(rule), -rule.confidence.posterior, rule.id)


def _ditiansui_rule_triggered(rule: ProductionRule, chart: dict[str, Any]) -> bool:
    """用 evaluate_trigger 替代硬编码 4 条触发器。"""
    return evaluate_trigger(rule.conditions.trigger, chart)


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
        target_id = _target_id_from_existing_topic(rule.domains[0] if rule.domains else "总体", rule.topic)
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
                    "task_id": target_id,
                    "target_id": target_id,
                },
            )
        )
    return claims


def build_minimal_ditiansui_claims(chart: dict[str, Any], case_id: str) -> list[V5Claim]:
    """滴天髓候补 runner：无生产规则时返回空列表。

    ponytail: 原来的 if/else 文本模板不是推理，是字符串生成。
    无真实规则时诚实返回空列表，让结构门禁正确处理"无结构基础"情况，
    比输出无根据的结构命题更有利于仲裁器准确性。
    """
    return []  # ponytail: 无生产规则 → 无命题，不造假结论


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


def _blind_rule_chart_rank(rule: dict[str, Any], chart: dict[str, Any]) -> tuple[float, int, str]:
    """用 condition_evaluator.rank_blind_rule 替代字符袋排名器。"""
    return rank_blind_rule(rule, chart)


def build_blind_school_rule_claims(
    chart: dict[str, Any],
    case_id: str,
    *,
    school: str,
    workspace_root: str = ".",
    limit: int = 15,
    min_candidate_score: float = 0.0,
) -> list[V5Claim]:
    """把三盲派 index.yaml 规则筛选为 v5 命题。

    变更：
    - limit 从 8 提升到 15，覆盖更多高质量规则
    - 用 score_blind_rule() 谓词评分替代固定 0.55 置信度
    - 加 min_candidate_score 门槛过滤低质候选
    """

    raw_rules = _load_blind_school_rules(school, workspace_root=workspace_root)
    if not raw_rules:
        return []
    source_school = BLIND_SCHOOL_SOURCE_IDS[school]
    selected = [
        rule for rule in raw_rules
        if str(rule.get("school", "")) == source_school
        and str(rule.get("status", "candidate")) not in {"deprecated", "rejected"}
        and float(rule.get("candidate_score") or 0.0) >= min_candidate_score
    ]
    selected.sort(key=lambda rule: _blind_rule_chart_rank(rule, chart))
    claims: list[V5Claim] = []
    for rule in selected[:limit]:
        rule_id = str(rule.get("id", _stable_id("blindrule", school, rule.get("title", ""))))
        conclusion = str(rule.get("conclusion") or rule.get("title") or "三盲派规则参与。")
        domain = _blind_rule_domain(rule)
        target_id = _target_id_from_existing_topic(
            domain,
            rule.get("topic"),
            rule.get("topic_label"),
        )
        # 用谓词评分驱动置信度，而非硬编码
        relevance_score = score_blind_rule(rule, chart)
        star_count = max(2, min(5, round(relevance_score * 5)))
        tier = "★" * star_count
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
                "relevance_score": round(relevance_score, 3),
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
                confidence=V5Confidence(
                    tier=tier,
                    score=relevance_score,
                    note=f"谓词评分={relevance_score:.2f}；candidate_score={rule.get('candidate_score', 0)}",
                ),
                evidence=[evidence],
                timing_hints=(
                    _estimate_marriage_timing(chart)
                    or [{"label": f"{chart.get('current_year', '当前流年')} 至下一交运前", "basis": str(chart.get("current_dayun") or "当前大运")}]
                ) if domain == "婚姻" else [{"label": f"{chart.get('current_year', '当前流年')} 至下一交运前", "basis": str(chart.get("current_dayun") or "当前大运")}],
                probabilistic=domain in PROBABILISTIC_DOMAIN_WHITELIST,
                falsifiable="若反馈显示该规则不能解释对应领域事件，则该规则需降权、合并或转入反证清单。",
                metadata={
                    "case_id": case_id,
                    "rule_id": rule_id,
                    "topic": str(rule.get("topic", "")),
                    "source_scope": "school_index_rules",
                    "runner_state": "school_rule",
                    "selection": "v6_preprod_blind_predicate",
                    "relevance_score": round(relevance_score, 3),
                    "task_id": target_id,
                    "target_id": target_id,
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
    """盲派三校候补 runner：无 index.yaml 规则命中时返回空列表。

    ponytail: 原 if/else 字符串模板（"子午冲就输出健康压力"）不是命理推理，是文本生成。
    无真实规则时诚实返回空列表，让结构门禁正确处理"无事件基础"情况。
    有真实规则时由 build_blind_school_rule_claims() 负责，不在此重复。
    """
    return []  # ponytail: 无规则 → 无命题，结构门禁将降权悬空的事件判断


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
        "ren_fuhong": "任付红 runner 尚未接入 v5 领域应期规则；当前仅登记应期验证待判。",
    }
    claim_type = {
        "ziping": "structure_claim",
        "ditiansui": "structure_claim",
        "gao_dechen": "event_claim",
        "duan_jianye": "event_claim",
        "yang_qingjuan": "event_claim",
        "ren_fuhong": "timing_claim",
    }
    claims: list[V5Claim] = []
    for school in schools:
        evidence = V5Evidence(
            evidence_id=_stable_id("v5ev", case_id, school, label),
            source="chart_model",
            text=f"六源共用同一 Chart Model：{label}",
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
                falsifiable="接入真实六源 runner 后，占位命题应消失。",
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
    from engine.v5.ditiansui_runner import run_ditiansui_independent  # ponytail: lazy import
    ziping_independent_claims = run_ziping_independent(chart, case_id)
    ditiansui_independent_claims = run_ditiansui_independent(chart, case_id)

    ziping_claims = build_ziping_production_claims(case_id, workspace_root=workspace_root, chart=chart)
    # 去重：独立分析命题与生产规则命题可能覆盖同一 domain，但 claim_id 不同，保留两者。
    ziping_claims = ziping_independent_claims + ziping_claims
    ditiansui_prod_claims = build_ditiansui_production_claims(chart, case_id, workspace_root=workspace_root)
    if not ditiansui_prod_claims:
        ditiansui_prod_claims = build_minimal_ditiansui_claims(chart, case_id)
    # 独立 runner + 生产规则拼接；独立结构命题优先前置
    ditiansui_claims = ditiansui_independent_claims + ditiansui_prod_claims
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


def _apply_structure_gate(claims: list[V5Claim]) -> list[V5Claim]:
    """结构门禁：无子平/滴天髓 structure_claim 时，event_claim 置信度强制降权。

    八层框架原则"基础决定上层"的工程实现：
    事件落地判断必须建立在格局/旺衰结构命题已存在的前提上。
    """
    active_structure = [
        c for c in claims
        if c.claim_type == "structure_claim"
        and c.school in STRUCTURE_SCHOOLS
        and c.stance not in ("abstain",)
        and c.confidence.score >= 0.4
    ]
    if active_structure:
        return claims  # 有结构基础，放行

    # 无结构基础 → event_claim 降权 60%，打标记
    patched: list[V5Claim] = []
    for c in claims:
        if c.claim_type == "event_claim":
            new_score = round(c.confidence.score * 0.4, 3)
            new_tier = "★" if new_score < 0.3 else "★★"
            patched_meta = dict(c.metadata)
            patched_meta["structure_gate"] = "downgraded_no_structure_foundation"
            patched.append(
                V5Claim(
                    claim_id=c.claim_id,
                    school=c.school,
                    domain=c.domain,
                    claim=c.claim,
                    claim_type=c.claim_type,
                    stance=c.stance,
                    polarity=c.polarity,
                    confidence=V5Confidence(
                        tier=new_tier,
                        score=new_score,
                        note=f"结构门禁降权（原={c.confidence.score:.2f}）：无子平/滴天髓结构命题作为基础",
                    ),
                    evidence=c.evidence,
                    counter_evidence=c.counter_evidence,
                    timing_hints=c.timing_hints,
                    probabilistic=False,  # 无结构基础不允许概率化
                    falsifiable=c.falsifiable,
                    metadata=patched_meta,
                )
            )
        else:
            patched.append(c)
    return patched


# 十神家族：用于把事件命题文本映射到方向标签（favor/avoid/yao）
_SHISHEN_TOKENS = (
    "比肩", "劫财", "食神", "伤官",
    "正财", "偏财", "正官", "七杀",
    "正印", "偏印",
)


def _extract_shishen_from_claim(claim_text: str) -> set[str]:
    """从事件命题文本中提取涉及的十神名。

    ponytail: 事件 runner 输出的自由文本没有结构化十神字段，只能靠关键词匹配。
    命中率低于结构化字段但覆盖所有派别产出。
    """
    return {token for token in _SHISHEN_TOKENS if token in claim_text}


def _collect_geju_directives(claims: list[V5Claim]) -> dict[str, Any]:
    """收集 L3 格局命题和 L5 病药命题的方向十神。

    返回：
        favor: 顺格局/顺药方向的十神集合（事件命题涉及这些十神应加分）
        avoid: 逆格局方向的十神集合（事件命题涉及这些十神应降权或翻转）
        geju_type: 格局类型标签
        yao_favor: 药方向十神集合（专门用于 P1 加分）
    """
    favor: set[str] = set()
    avoid: set[str] = set()
    yao_favor: set[str] = set()
    geju_type = ""
    for c in claims:
        meta = c.metadata or {}
        layer = str(meta.get("layer", ""))
        if layer == "L3_geju_type":
            favor.update(meta.get("favor_shishen", []) or [])
            avoid.update(meta.get("avoid_shishen", []) or [])
            geju_type = geju_type or str(meta.get("geju_type", ""))
        elif layer == "L5_bingyao":
            yao_favor.update(meta.get("yao_favor_shishen", []) or [])
    return {
        "favor": favor,
        "avoid": avoid,
        "yao_favor": yao_favor,
        "geju_type": geju_type,
    }


def _apply_geju_yao_constraints(claims: list[V5Claim]) -> list[V5Claim]:
    """P0b + P1：让 L3 格局约束和 L5 药方向真正过滤/加分事件命题。

    规则：
      - 事件命题涉及 avoid 十神 → 置信度 × 0.5，polarity 翻负，打标 "geju_conflict"
      - 事件命题涉及 favor 十神 → 置信度 × 1.15（上限 0.85）
      - 事件命题涉及 yao_favor 十神 → 置信度 × 1.10（上限 0.85），叠加 favor 效果
      - 不涉及任何十神 → 不变（无法判断方向的命题不能误伤）
      - 结构命题不受影响
    """
    directives = _collect_geju_directives(claims)
    favor = directives["favor"]
    avoid = directives["avoid"]
    yao_favor = directives["yao_favor"]
    geju_type = directives["geju_type"]

    if not favor and not avoid and not yao_favor:
        return claims  # 无约束，直接放行

    patched: list[V5Claim] = []
    for c in claims:
        if c.claim_type != "event_claim":
            patched.append(c)
            continue

        involved = _extract_shishen_from_claim(c.claim)
        if not involved:
            patched.append(c)
            continue

        hit_avoid = involved & avoid
        hit_favor = involved & favor
        hit_yao = involved & yao_favor

        if not (hit_avoid or hit_favor or hit_yao):
            patched.append(c)
            continue

        new_score = c.confidence.score
        new_polarity = c.polarity
        new_stance = c.stance
        marks: list[str] = []

        if hit_avoid:
            new_score = round(new_score * 0.5, 3)
            new_polarity = "negative"  # type: ignore[assignment]
            new_stance = "oppose"  # type: ignore[assignment]
            marks.append(f"geju_conflict[{geju_type}]:avoid={sorted(hit_avoid)}")
        if hit_favor:
            new_score = round(min(0.85, new_score * 1.15), 3)
            marks.append(f"geju_align:favor={sorted(hit_favor)}")
        if hit_yao:
            new_score = round(min(0.85, new_score * 1.10), 3)
            marks.append(f"yao_align:yao_favor={sorted(hit_yao)}")

        new_tier = "★★★★★" if new_score >= 0.75 else "★★★★" if new_score >= 0.6 else "★★★" if new_score >= 0.45 else "★★" if new_score >= 0.3 else "★"
        patched_meta = dict(c.metadata)
        patched_meta["geju_constraint"] = "；".join(marks)

        patched.append(
            V5Claim(
                claim_id=c.claim_id,
                school=c.school,
                domain=c.domain,
                claim=c.claim,
                claim_type=c.claim_type,
                stance=new_stance,
                polarity=new_polarity,
                confidence=V5Confidence(
                    tier=new_tier,
                    score=new_score,
                    note=f"格局约束调整（原={c.confidence.score:.2f}）：{'；'.join(marks)}",
                ),
                evidence=c.evidence,
                counter_evidence=c.counter_evidence,
                timing_hints=c.timing_hints,
                probabilistic=c.probabilistic and not hit_avoid,  # 冲突命题禁止进入概率层
                falsifiable=c.falsifiable,
                metadata=patched_meta,
            )
        )
    return patched


def _extract_structure_verdict(structure_claims: list[V5Claim]) -> str:
    """从子平/滴天髓结构命题中提取可读 verdict，替代硬编码固定字符串。"""
    if not structure_claims:
        return "无有效结构命题，事件判断缺乏基础。"
    active = [c for c in structure_claims if c.stance == "support" and c.confidence.score >= 0.4]
    if not active:
        return "结构命题均为弃权或低置信，事件判断需降级。"
    # 提取核心断言（取置信度最高的命题文本）
    top = max(active, key=lambda c: c.confidence.score)
    # 统计支持方向
    support_n = len([c for c in structure_claims if c.stance == "support"])
    oppose_n = len([c for c in structure_claims if c.stance == "oppose"])
    conflict_note = f"；有{oppose_n}条反证" if oppose_n else ""
    return f"结构裁决（{support_n}条支持{conflict_note}）：{top.claim[:80]}…"


def _extract_event_verdict(event_claims: list[V5Claim], structure_verdict: str, has_structure: bool) -> str:
    """从事件命题中提取可读 verdict，以结构裁决为约束前提。"""
    if not event_claims:
        return "无有效事件命题。"
    if not has_structure:
        return f"事件命题因结构门禁降权，仅供参考（结构基础：{structure_verdict[:40]}）。"
    active = [c for c in event_claims if c.stance == "support" and c.confidence.score >= 0.35]
    if not active:
        return "事件命题均为低置信，不形成强事件结论。"
    top = max(active, key=lambda c: c.confidence.score)
    support_n = len([c for c in event_claims if c.stance == "support"])
    oppose_n = len([c for c in event_claims if c.stance == "oppose"])
    conflict_note = f"；有{oppose_n}条反证" if oppose_n else ""
    return f"事件裁决（{support_n}条支持{conflict_note}，基于结构基础）：{top.claim[:80]}…"


def arbitrate_claims(claims: list[V5Claim]) -> list[V5ArbitrationResult]:
    """角色化三段式仲裁器。

    替换原有"数 support/oppose 数量 + 输出固定字符串"的假仲裁。
    实现"基础决定上层"：
      段1 结构合法性（子平+滴天髓）→ 段2 事件落地（三盲派，以段1为前提）
      → 段3 概率应期（只接受通过段2的命题）
    """
    # 结构门禁：无结构基础则 event_claim 强制降权
    gated_claims = prepare_claims_for_adjudication(claims)

    # 全局结构命题（跨domain，用于判断整体结构基础是否建立）
    global_structure_claims = [
        c for c in gated_claims
        if c.claim_type == "structure_claim"
        and c.school in STRUCTURE_SCHOOLS
        and c.stance not in ("abstain",)
    ]
    has_global_structure = len(global_structure_claims) >= 1

    claims_by_domain: dict[str, list[V5Claim]] = defaultdict(list)
    for claim in gated_claims:
        claims_by_domain[claim.domain].append(claim)

    results: list[V5ArbitrationResult] = []
    for domain, domain_claims in sorted(claims_by_domain.items()):
        oppose_claims = [c for c in domain_claims if c.stance == "oppose"]
        minority = [c.claim_id for c in oppose_claims]

        # ── 段1：结构合法性（子平+滴天髓 structure_claim）─────────────────────
        structure_claims = [
            c for c in domain_claims
            if (c.school in STRUCTURE_SCHOOLS or c.claim_type == "structure_claim")
            and c.stance != "abstain"
        ]
        # 补充全局结构命题（总体域的结构命题可作为所有域的基础）
        if domain != "总体":
            for gc in global_structure_claims:
                if gc.domain == "总体" and gc not in structure_claims:
                    structure_claims.append(gc)

        has_domain_structure = len([c for c in structure_claims if c.stance == "support"]) >= 1
        structure_verdict = _extract_structure_verdict(structure_claims)
        structure_winners = list({c.school for c in structure_claims if c.stance == "support"})
        struct_support = len([c for c in structure_claims if c.stance == "support"])
        struct_oppose = len([c for c in structure_claims if c.stance == "oppose"])
        struct_confidence_score = min(0.85, 0.45 + struct_support * 0.08) if struct_support else 0.2
        struct_confidence_tier = "★★★★" if struct_confidence_score >= 0.7 else "★★★" if struct_confidence_score >= 0.5 else "★★"
        struct_conflict = "stance_conflict" if struct_support and struct_oppose else "none"

        results.append(
            V5ArbitrationResult(
                domain=domain,
                stage="structure_legality",
                conclusion=structure_verdict,
                winning_schools=structure_winners,
                minority_claims=minority,
                support_score=float(struct_support),
                opposition_score=float(struct_oppose),
                conflict_type=struct_conflict,
                confidence=V5Confidence(
                    tier=struct_confidence_tier,
                    score=struct_confidence_score,
                    note=f"子平+滴天髓结构命题={struct_support}条；结构门禁={'通过' if has_domain_structure or has_global_structure else '未通过'}",
                ),
                rationale=f"子平类、滴天髓类、高德臣优先参与结构合法性判断。结构基础：{'已建立' if has_domain_structure or has_global_structure else '缺失，事件命题已降权'}。",
                probabilistic_allowed=False,
            )
        )

        # ── 段2：事件落地（三盲派，以段1为前提）─────────────────────────────
        event_claims = [
            c for c in domain_claims
            if (c.school in EVENT_SCHOOLS or c.claim_type == "event_claim")
            and c.stance != "abstain"
        ]
        event_verdict = _extract_event_verdict(event_claims, structure_verdict, has_domain_structure or has_global_structure)
        event_winners = list({c.school for c in event_claims if c.stance == "support"})
        event_support = len([c for c in event_claims if c.stance == "support"])
        event_oppose = len([c for c in event_claims if c.stance == "oppose"])
        # 无结构基础则事件置信度上限 0.45
        event_base_score = min(0.80, 0.40 + event_support * 0.07) if event_support else 0.2
        if not (has_domain_structure or has_global_structure):
            event_base_score = min(0.45, event_base_score)
        event_tier = "★★★★" if event_base_score >= 0.7 else "★★★" if event_base_score >= 0.5 else "★★" if event_base_score >= 0.35 else "★"
        event_conflict = "stance_conflict" if event_support and event_oppose else "none"
        probabilistic_allowed = domain in PROBABILISTIC_DOMAIN_WHITELIST and any(c.probabilistic for c in domain_claims)

        results.append(
            V5ArbitrationResult(
                domain=domain,
                stage="event_realization",
                conclusion=event_verdict,
                winning_schools=event_winners,
                minority_claims=minority,
                support_score=float(event_support),
                opposition_score=float(event_oppose),
                conflict_type=event_conflict,
                confidence=V5Confidence(
                    tier=event_tier,
                    score=event_base_score,
                    note=f"事件命题={event_support}条；结构前提={'满足' if has_domain_structure or has_global_structure else '不满足，已降权'}",
                ),
                rationale=f"高德臣、段建业、杨清娟参与事件落地；结构约束来自：{structure_verdict[:40]}。",
                probabilistic_allowed=probabilistic_allowed,
            )
        )

        # ── 段3：概率应期（只接受通过段2、在白名单域、有时间窗的命题）────────
        prob_claims = [
            c for c in domain_claims
            if c.probabilistic
            and domain in PROBABILISTIC_DOMAIN_WHITELIST
            and (has_domain_structure or has_global_structure)
        ]
        prob_conclusion = (
            f"概率应期：{len(prob_claims)}条命题允许进入受限概率层，需有时间窗与反馈标签。"
            if prob_claims
            else "概率应期：无满足条件的命题（需结构基础 + 白名单域 + 可反馈时间窗）。"
        )
        results.append(
            V5ArbitrationResult(
                domain=domain,
                stage="probability_timing",
                conclusion=prob_conclusion,
                winning_schools=list({c.school for c in prob_claims}),
                minority_claims=[],
                support_score=float(len(prob_claims)),
                opposition_score=0.0,
                conflict_type="none",
                confidence=V5Confidence(
                    tier="★★★" if prob_claims else "★",
                    score=0.55 if prob_claims else 0.15,
                    note="性格、格局高低、宽泛气质描述不进入概率层。",
                ),
                rationale="仅白名单事件（学业/事业/财富/婚姻/健康）且有结构基础时允许概率化。",
                probabilistic_allowed=bool(prob_claims),
            )
        )
    return results


def prepare_claims_for_adjudication(claims: list[V5Claim]) -> list[V5Claim]:
    """复用既有结构门禁与格局约束，供裁决结果和单位协议使用。"""

    gated_claims = _apply_structure_gate(claims)
    return _apply_geju_yao_constraints(gated_claims)


def _default_prediction_specs(chart: dict[str, Any]) -> list[dict[str, Any]]:
    """主要事件 prediction-first 的 MVP 默认账本。

    在真实 school runner 尚未全量接入前，先保证每个主要事件都有
    可反馈预测槽位。后续由 claims、taxonomy 与反馈统计逐步替换默认文案。
    """

    current_dayun = str(chart.get("current_dayun") or chart.get("当前大运") or "当前大运")
    current_year = str(chart.get("current_year") or chart.get("当前流年") or "当前流年")
    marriage_timing = _estimate_marriage_timing(chart)
    marriage_window = marriage_timing[0] if marriage_timing else {"label": f"{current_year} 至下一交运前", "basis": current_dayun}
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
            "time_window": marriage_window,
            "trigger_conditions": ["印来", "配偶星到", "夫妻宫或配偶资源被触发"],
            "falsifier": "若时间窗内婚恋关系、配偶资源、家庭责任与关系压力均无明显变化，则本预测失验。",
            "probability_range": (0.35, 0.55),
            "tier": "★★★",
            "score": 0.55,
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


def _prediction_from_claim(case_id: str, claim: V5Claim) -> V5Prediction:
    """把经过格局约束调整的真实事件命题转成受限概率预测。

    ponytail: 概率范围直接由命题置信度派生，不再用硬编码固定区间，
    让格局约束（P0b/P1）对置信度的调整真正传导到预测层。
    """
    score = claim.confidence.score
    # 置信度 → 概率区间：以 score 为中心，±0.1 带宽，clamp 到 [0.1, 0.9]
    low = round(max(0.1, score - 0.1), 2)
    high = round(min(0.9, score + 0.1), 2)
    time_window = dict(claim.timing_hints[0]) if claim.timing_hints else {}
    geju_note = claim.metadata.get("geju_constraint", "") if claim.metadata else ""
    calib = "由真实事件命题登记；概率区间随格局约束调整。"
    if geju_note:
        calib += f"（格局约束：{geju_note}）"
    return V5Prediction(
        prediction_id=_stable_id("v5pred", case_id, claim.claim_id, claim.domain),
        domain=claim.domain,
        event_label=claim.claim,
        probability_range=(low, high),
        confidence=claim.confidence,
        time_window=time_window,
        trigger_conditions=["真实事件命题", "白名单领域", "已过结构门禁与格局约束"],
        falsifier=claim.falsifiable or "若时间窗内未发生该事件，则本预测失验。",
        calibration_note=calib,
    )


def build_prediction_ledger(case_id: str, claims: list[V5Claim], chart: dict[str, Any] | None = None) -> V5PredictionLedger:
    """从可概率化命题生成受限概率 ledger。

    P2：优先消费真实事件命题（已过结构门禁 + 格局约束），
    每个白名单域取置信度最高的支持性事件命题生成预测；
    缺失真实命题的白名单域才用默认槽位兜底，保证 prediction-first 闭环可见。
    """

    predictions: list[V5Prediction] = []
    filled_domains: set[str] = set()

    # 1. 优先消费真实事件命题：每个白名单域取最强支持命题
    claims_by_domain: dict[str, list[V5Claim]] = defaultdict(list)
    for claim in claims:
        if (
            claim.probabilistic
            and claim.claim_type == "event_claim"  # 只有具体事件命题可占概率槽；结构命题不进概率层
            and claim.domain in PROBABILISTIC_DOMAIN_WHITELIST
            and claim.stance == "support"
            and claim.confidence.score >= 0.35
        ):
            claims_by_domain[claim.domain].append(claim)

    for domain, domain_claims in claims_by_domain.items():
        top = max(domain_claims, key=lambda c: c.confidence.score)
        predictions.append(_prediction_from_claim(case_id, top))
        filled_domains.add(domain)

    # 2. 缺失的白名单域用默认槽位兜底
    for spec in _default_prediction_specs(chart or {}):
        if spec["domain"] in filled_domains:
            continue
        predictions.append(
            V5Prediction(
                prediction_id=_stable_id("v5pred", case_id, spec["domain"], spec["event_label"]),
                domain=spec["domain"],
                event_label=spec["event_label"],
                probability_range=spec["probability_range"],
                confidence=V5Confidence(tier=spec["tier"], score=spec["score"], note="prediction-first 默认槽位（无真实事件命题兜底）"),
                time_window=spec["time_window"],
                trigger_conditions=list(spec["trigger_conditions"]),
                falsifier=spec["falsifier"],
                calibration_note="该域暂无真实事件命题，用默认槽位保证反馈闭环；有命题后自动替换。",
            )
        )
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
    """运行 v5 六源命题图最小闭环。

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
    adjudication_units = build_v5_adjudication_units(
        prepare_claims_for_adjudication(resolved_claims)
    )
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
        adjudication_units=list(adjudication_units),
    )


def run_v5_snapshot(
    chart: dict[str, Any],
    *,
    case_id: str = "",
    claims: list[V5Claim] | None = None,
    workspace_root: str = ".",
    engine_version: str = "",
    artifact_bindings: dict[str, str] | None = None,
) -> V5RunSnapshot:
    """运行 v5 并返回 run-centric 快照。"""

    return V5RunSnapshot.from_output(
        run_v5(chart, case_id=case_id, claims=claims, workspace_root=workspace_root),
        engine_version=engine_version,
        artifact_bindings=artifact_bindings,
    )

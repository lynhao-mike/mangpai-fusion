"""event_semantics_loader.py · v4.2 事件语义配置加载器

从 theory/prediction_models/event-semantics.yaml 加载事件语义映射。
替代 prediction_signals.py 中的硬编码 _DOMAIN_MEANINGS。
"""
from __future__ import annotations

import yaml
from pathlib import Path
from typing import Any

from engine.domain.prediction import SymbolicEventCandidate


# ── 全局缓存 ────────────────────────────────────────────────
_SEMANTICS_CACHE: dict[str, Any] | None = None


def load_event_semantics(force_reload: bool = False) -> dict[str, Any]:
    """加载事件语义配置（带缓存）。

    Args:
        force_reload: 强制重新加载，忽略缓存

    Returns:
        解析后的 YAML 配置字典
    """
    global _SEMANTICS_CACHE

    if _SEMANTICS_CACHE is not None and not force_reload:
        return _SEMANTICS_CACHE

    # 定位配置文件（相对于本文件的位置）
    config_path = (
        Path(__file__).parent.parent.parent
        / "theory"
        / "prediction_models"
        / "event-semantics.yaml"
    )

    if not config_path.exists():
        # 降级：配置文件不存在时，返回硬编码默认值
        _SEMANTICS_CACHE = _get_fallback_semantics()
        return _SEMANTICS_CACHE

    try:
        with config_path.open("r", encoding="utf-8") as f:
            _SEMANTICS_CACHE = yaml.safe_load(f) or {}
        return _SEMANTICS_CACHE
    except (yaml.YAMLError, OSError, ValueError) as e:
        # 降级：解析失败时使用默认值，但记录错误
        import logging
        logging.warning(f"Failed to load event-semantics.yaml: {e}, using fallback")
        _SEMANTICS_CACHE = _get_fallback_semantics()
        return _SEMANTICS_CACHE


def get_domain_meanings(
    domain: str,
    *,
    school: str | None = None,
    include_weights: bool = False,
) -> list[str] | list[dict[str, Any]]:
    """获取指定领域的事件语义列表。

    Args:
        domain: 领域名称（婚姻/财运/事业/健康/学业/六亲/其他）
        school: 可选，指定流派（ziping/dtt/mp）获取流派特殊语义
        include_weights: 是否返回完整语义对象（含权重/紧急度）

    Returns:
        - include_weights=False: ['语义1', '语义2', ...]
        - include_weights=True: [{'meaning': ..., 'weight': ..., 'urgency': ...}, ...]
    """
    config = load_event_semantics()
    domains = config.get("domains", {})

    # 1. 获取通用语义
    domain_config = domains.get(domain, {})
    semantics = domain_config.get("semantics", [])

    # 2. 如果指定了流派，尝试合并流派特殊语义
    if school:
        overrides = config.get("school_overrides", {}).get(school, {})
        school_domain = overrides.get(domain, {})
        extra = school_domain.get("extra_semantics", [])
        semantics = list(semantics) + list(extra)  # 合并

    # 3. 应用 RL 动态权重调整
    rl_adjustments = config.get("rl_adjustments", {})
    if rl_adjustments:
        semantics = _apply_rl_adjustments(semantics, domain, rl_adjustments)

    # 4. 返回格式
    if include_weights:
        return semantics  # 返回完整对象
    else:
        return [s.get("meaning", "事件待定") for s in semantics]


def _apply_rl_adjustments(
    semantics: list[dict[str, Any]],
    domain: str,
    adjustments: dict[str, float],
) -> list[dict[str, Any]]:
    """应用 RL 动态权重调整到语义列表。"""
    adjusted = []
    for sem in semantics:
        sem_copy = dict(sem)
        meaning = sem_copy.get("meaning", "")
        # RL 键格式：{domain}_{meaning}_{timestamp}
        # 取最新的调整值
        matching_keys = [
            k for k in adjustments.keys()
            if k.startswith(f"{domain}_{meaning}_")
        ]
        if matching_keys:
            latest_key = max(matching_keys)  # 字典序最大 = 时间戳最新
            sem_copy["weight"] = adjustments[latest_key]
            sem_copy["rl_adjusted"] = True
        adjusted.append(sem_copy)
    return adjusted


def get_domain_time_sensitivity(domain: str) -> dict[str, Any]:
    """获取领域的时间敏感度配置。

    Returns:
        {'base_width': int, 'urgency': str}
    """
    # 从 time_window_estimator.py 的 DOMAIN_TIME_SENSITIVITY 同步
    # 这里硬编码，因为它是算法参数，不适合外部化
    sensitivity_map = {
        "婚姻": {"base_width": 1, "urgency": "high"},
        "感情": {"base_width": 1, "urgency": "high"},
        "事业": {"base_width": 2, "urgency": "medium"},
        "财富": {"base_width": 2, "urgency": "medium"},
        "学业": {"base_width": 2, "urgency": "medium"},
        "健康": {"base_width": 0, "urgency": "critical"},
        "意外": {"base_width": 0, "urgency": "critical"},
        "default": {"base_width": 2, "urgency": "medium"},
    }
    return sensitivity_map.get(domain, sensitivity_map["default"])


def extract_symbolic_events_from_config(
    domain: str,
    candidate_event: str,
    year: int,
    *,
    confidence_percent: float = 0.5,
    passed_layers: int = 1,
    school: str | None = None,
) -> list[SymbolicEventCandidate]:
    """基于配置文件生成象法候选事件（替代硬编码逻辑）。

    Args:
        domain: 领域
        candidate_event: 候选事件名称
        year: 年份
        confidence_percent: 置信度百分比（0-1）
        passed_layers: 通过层数（0-3）
        school: 流派

    Returns:
        SymbolicEventCandidate 列表
    """
    semantics = get_domain_meanings(domain, school=school, include_weights=True)

    symbol = f"{candidate_event}({year}年)"
    weight = (passed_layers / 3.0 + confidence_percent) / 2.0
    weight = max(0.0, min(1.0, weight))

    # 取前 3 个高权重语义作为候选
    sorted_semantics = sorted(
        semantics,
        key=lambda s: s.get("weight", 0.0),
        reverse=True
    )[:3]

    meanings = [s.get("meaning", "事件待定") for s in sorted_semantics]

    return [SymbolicEventCandidate(
        symbol=symbol,
        meaning_candidates=meanings,
        probability_weight=weight,
    )]


def _get_fallback_semantics() -> dict[str, Any]:
    """降级：配置文件加载失败时的硬编码默认值。"""
    return {
        "schema_version": "event_semantics.v1.fallback",
        "domains": {
            "婚姻": {
                "semantics": [
                    {"meaning": "婚变/离合", "weight": 0.6, "urgency": "high"},
                    {"meaning": "情感纠葛", "weight": 0.5, "urgency": "high"},
                    {"meaning": "配偶健康", "weight": 0.4, "urgency": "critical"},
                ]
            },
            "财运": {
                "semantics": [
                    {"meaning": "财源增减", "weight": 0.7, "urgency": "medium"},
                    {"meaning": "投资置业", "weight": 0.5, "urgency": "medium"},
                    {"meaning": "破财风险", "weight": 0.6, "urgency": "high"},
                ]
            },
            "事业": {
                "semantics": [
                    {"meaning": "职位变动", "weight": 0.6, "urgency": "medium"},
                    {"meaning": "创业机遇", "weight": 0.4, "urgency": "medium"},
                    {"meaning": "事业受挫", "weight": 0.5, "urgency": "medium"},
                ]
            },
            "健康": {
                "semantics": [
                    {"meaning": "伤病风险", "weight": 0.7, "urgency": "critical"},
                    {"meaning": "手术外伤", "weight": 0.5, "urgency": "critical"},
                    {"meaning": "慢性耗损", "weight": 0.4, "urgency": "medium"},
                ]
            },
            "学业": {
                "semantics": [
                    {"meaning": "考学升迁", "weight": 0.7, "urgency": "medium"},
                    {"meaning": "学业受阻", "weight": 0.5, "urgency": "medium"},
                ]
            },
            "六亲": {
                "semantics": [
                    {"meaning": "六亲变故", "weight": 0.6, "urgency": "critical"},
                    {"meaning": "人际争端", "weight": 0.5, "urgency": "high"},
                ]
            },
            "其他": {
                "semantics": [
                    {"meaning": "意外变化", "weight": 0.5, "urgency": "high"},
                ]
            },
        },
        "school_overrides": {},
        "rl_adjustments": {},
        "metadata": {"fallback": True},
    }

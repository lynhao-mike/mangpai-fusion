"""parallel-domain canonical constants.

本模块是六功能域顺序与三专家顺序的唯一事实源。
"""

from __future__ import annotations

from engine.domain.parallel import DomainName, ExpertSystem

CANONICAL_EXPERT_ORDER: tuple[ExpertSystem, ...] = ("blind", "ziping", "tiaohou_ditiansui")
CANONICAL_DOMAINS: tuple[DomainName, ...] = ("学业", "事业", "财运", "婚姻", "健康", "性格")
CANONICAL_WEIGHT_DOMAINS: tuple[DomainName, ...] = CANONICAL_DOMAINS

EXPERT_LABELS: dict[ExpertSystem, str] = {
    "blind": "盲派综合组",
    "ziping": "子平格局派",
    "tiaohou_ditiansui": "滴天髓调候派",
}

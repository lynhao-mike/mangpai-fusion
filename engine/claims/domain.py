"""L2 独立命题层的不可变领域契约。"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Literal, Mapping

ClaimType = Literal["structure_claim", "event_claim", "timing_claim", "portrait_claim"]
ClaimStance = Literal["support", "oppose"]
ClaimPolarity = Literal["positive", "negative", "neutral"]


def stable_claim_id(school_id: str, task_id: str, chart_signature: str, rule_id: str) -> str:
    """按学派、任务、命盘与规则生成确定性命题 ID。"""
    raw = "|".join((school_id, task_id, chart_signature, rule_id))
    return "claim-" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:20]


@dataclass(frozen=True)
class TimeWindow:
    start_year: int
    end_year: int
    label: str = "annual"

    def __post_init__(self) -> None:
        if self.start_year > self.end_year:
            raise ValueError("time_window requires start_year <= end_year")
        if not self.label.strip():
            raise ValueError("time_window label is required")

    def to_dict(self) -> dict[str, int | str]:
        return {"start_year": self.start_year, "end_year": self.end_year, "label": self.label}


@dataclass(frozen=True)
class Evidence:
    evidence_id: str
    fact_refs: tuple[str, ...]
    feature_refs: tuple[str, ...]
    rule_id: str
    text: str

    def __post_init__(self) -> None:
        if not self.evidence_id.strip():
            raise ValueError("evidence_id is required")
        if not self.fact_refs and not self.feature_refs:
            raise ValueError("evidence requires at least one fact_ref or feature_ref")
        if not self.rule_id.strip():
            raise ValueError("evidence rule_id is required")
        if not self.text.strip():
            raise ValueError("evidence text is required")
        object.__setattr__(self, "fact_refs", tuple(self.fact_refs))
        object.__setattr__(self, "feature_refs", tuple(self.feature_refs))

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "fact_refs": list(self.fact_refs),
            "feature_refs": list(self.feature_refs),
            "rule_id": self.rule_id,
            "text": self.text,
        }


@dataclass(frozen=True)
class Claim:
    claim_id: str
    school_id: str
    task_id: str
    claim_type: ClaimType
    stance: ClaimStance
    statement: str
    evidence: tuple[Evidence, ...]
    falsifier: str
    time_window: TimeWindow | None
    confidence_basis: str
    applicability_snapshot: Mapping[str, Any]
    domain: str = "总体"
    polarity: ClaimPolarity = "neutral"
    magnitude: float | None = None
    confidence: float = 1.0
    high_risk: bool = False
    target_id: str = ""

    def __post_init__(self) -> None:
        for name in ("claim_id", "school_id", "task_id", "statement", "falsifier", "confidence_basis"):
            if not str(getattr(self, name)).strip():
                raise ValueError(f"{name} is required")
        if self.claim_type not in {"structure_claim", "event_claim", "timing_claim", "portrait_claim"}:
            raise ValueError("invalid claim_type")
        if self.stance not in {"support", "oppose"}:
            raise ValueError("invalid stance")
        if not self.domain.strip():
            raise ValueError("domain is required")
        if self.polarity not in {"positive", "negative", "neutral"}:
            raise ValueError("invalid polarity")
        if self.magnitude is not None and not 0.0 <= self.magnitude <= 1.0:
            raise ValueError("magnitude must be between 0 and 1")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        if type(self.high_risk) is not bool:
            raise ValueError("high_risk must be boolean")
        if not self.target_id:
            object.__setattr__(self, "target_id", self.task_id)
        if not self.evidence:
            raise ValueError("claim evidence must be non-empty")
        if self.claim_type in {"event_claim", "timing_claim"} and self.time_window is None:
            raise ValueError("event/timing claim requires time_window")
        if self.claim_type in {"structure_claim", "portrait_claim"} and self.time_window is not None:
            raise ValueError("structure/portrait claim cannot contain time_window")
        object.__setattr__(self, "evidence", tuple(self.evidence))
        object.__setattr__(self, "applicability_snapshot", MappingProxyType(dict(self.applicability_snapshot)))

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "school_id": self.school_id,
            "task_id": self.task_id,
            "claim_type": self.claim_type,
            "stance": self.stance,
            "statement": self.statement,
            "evidence": [item.to_dict() for item in self.evidence],
            "falsifier": self.falsifier,
            "time_window": self.time_window.to_dict() if self.time_window else None,
            "confidence_basis": self.confidence_basis,
            "applicability_snapshot": dict(self.applicability_snapshot),
            "domain": self.domain,
            "polarity": self.polarity,
            "magnitude": self.magnitude,
            "confidence": self.confidence,
            "high_risk": self.high_risk,
            "target_id": self.target_id,
        }


_STATEMENT_FACT_SEPARATOR = "｜本盘依据："


def _format_statement_value(value: Any) -> str:
    """把本盘事实值格式化为稳定的 repr 风格，浮点保留 4 位。"""
    if isinstance(value, bool):
        return "True" if value else "False"
    if isinstance(value, float):
        return f"{value:.4f}"
    if isinstance(value, str):
        return repr(value)
    if value is None:
        return "None"
    return repr(value)


def _resolve_statement_fact(context: Mapping[str, Any], fact: str) -> Any:
    current: Any = context
    for part in fact.split("."):
        if not isinstance(current, Mapping) or part not in current:
            raise KeyError(f"missing context fact: {fact}")
        current = current[part]
    return current


def render_statement(rule: Any, result: Any, context: Mapping[str, Any]) -> str:
    """把规则结论模板与本盘命中的 fact=value 装配成断语句子。

    只取 ``result.matched_conditions`` 里的 fact，从 ``context`` 取值，按 fact 名排序。
    至少输出一个 ``fact=value``；若一条命中条件都没有，显式追加 ``[no-fact]``，不静默退回模板。
    """
    facts = sorted({condition.fact for condition in result.matched_conditions})
    pairs = [
        f"{fact}={_format_statement_value(_resolve_statement_fact(context, fact))}"
        for fact in facts
    ]
    if not pairs:
        return f"{rule.conclusion_template}{_STATEMENT_FACT_SEPARATOR}[no-fact]"
    return f"{rule.conclusion_template}{_STATEMENT_FACT_SEPARATOR}" + "；".join(pairs)


class TaskUnsupported(ValueError):
    """runner 的知识范围不覆盖指定任务。"""

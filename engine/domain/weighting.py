"""三专家功能域权重与反馈 overlay 领域模型。

本模块提供等效强校验，不依赖外部 Pydantic 运行时，避免扩大当前测试依赖。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from math import sqrt
from typing import Any, Mapping

from engine.domain.parallel import DomainName, ExpertSystem
from engine.domain.parallel_constants import CANONICAL_DOMAINS, CANONICAL_EXPERT_ORDER

EXPERT_SYSTEMS: tuple[ExpertSystem, ...] = CANONICAL_EXPERT_ORDER
DOMAINS: tuple[DomainName, ...] = CANONICAL_DOMAINS


@dataclass(frozen=True)
class ExpertDomainFeedbackStats:
    """单个 expert_system × domain × rule_group 的反馈统计。"""

    expert_system: ExpertSystem
    domain: DomainName
    rule_group: str
    n_eff: float
    success_count: float
    failure_count: float
    beta_alpha: float
    beta_beta: float
    beta_mean: float | None = None
    wilson_lower_bound: float | None = None

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "ExpertDomainFeedbackStats":
        expert_system = _validate_expert(data.get("expert_system"))
        domain = _validate_domain(data.get("domain"))
        rule_group = str(data.get("rule_group") or "default")
        n_eff = _required_non_negative_float(data, "n_eff")
        success_count = _required_non_negative_float(data, "success_count")
        failure_count = _required_non_negative_float(data, "failure_count")
        beta_alpha = _required_positive_float(data, "beta_alpha")
        beta_beta = _required_positive_float(data, "beta_beta")
        beta_mean = data.get("beta_mean")
        wilson_lower_bound = data.get("wilson_lower_bound")
        if beta_mean is None:
            beta_mean = beta_alpha / (beta_alpha + beta_beta)
        beta_mean = _bounded_float(beta_mean, "beta_mean")
        if wilson_lower_bound is None:
            wilson_lower_bound = _wilson_lower_bound(success_count, failure_count)
        wilson_lower_bound = _bounded_float(wilson_lower_bound, "wilson_lower_bound")
        return cls(
            expert_system=expert_system,
            domain=domain,
            rule_group=rule_group,
            n_eff=n_eff,
            success_count=success_count,
            failure_count=failure_count,
            beta_alpha=beta_alpha,
            beta_beta=beta_beta,
            beta_mean=beta_mean,
            wilson_lower_bound=wilson_lower_bound,
        )

    def performance_score(self) -> float:
        """反馈表现分，优先使用 Wilson 下界，缺失时退回 beta_mean。"""

        if self.wilson_lower_bound is not None:
            return self.wilson_lower_bound
        if self.beta_mean is not None:
            return self.beta_mean
        return 0.5

    def to_audit_dict(self) -> dict[str, Any]:
        return {
            "expert_system": self.expert_system,
            "domain": self.domain,
            "rule_group": self.rule_group,
            "n_eff": self.n_eff,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "beta_alpha": self.beta_alpha,
            "beta_beta": self.beta_beta,
            "beta_mean": self.beta_mean,
            "wilson_lower_bound": self.wilson_lower_bound,
        }


FeedbackOverlayEntry = ExpertDomainFeedbackStats


@dataclass(frozen=True)
class FeedbackOverlay:
    """运行期反馈叠加配置。"""

    version: str = "no-feedback-overlay"
    source_path: str = "inline:none"
    min_effective_sample_for_adjustment: float = 11.0
    low_sample_max_delta: float = 0.02
    mature_sample_max_delta: float = 0.15
    entries: tuple[ExpertDomainFeedbackStats, ...] = field(default_factory=tuple)

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any] | None) -> "FeedbackOverlay":
        if data is None:
            return cls()
        entries_raw = data.get("entries", [])
        if not isinstance(entries_raw, list):
            raise ValueError("feedback_overlay.entries 必须是 list。")
        return cls(
            version=str(data.get("version") or "feedback-overlay-inline"),
            source_path=str(data.get("source_path") or data.get("source") or "inline"),
            min_effective_sample_for_adjustment=_positive_float(
                data.get("min_effective_sample_for_adjustment", 11),
                "feedback_overlay.min_effective_sample_for_adjustment",
            ),
            low_sample_max_delta=_bounded_float(data.get("low_sample_max_delta", 0.02), "feedback_overlay.low_sample_max_delta"),
            mature_sample_max_delta=_bounded_float(
                data.get("mature_sample_max_delta", 0.15),
                "feedback_overlay.mature_sample_max_delta",
            ),
            entries=tuple(ExpertDomainFeedbackStats.from_mapping(entry) for entry in entries_raw),
        )

    def entries_for(self, expert_system: ExpertSystem, domain: DomainName) -> tuple[ExpertDomainFeedbackStats, ...]:
        return tuple(entry for entry in self.entries if entry.expert_system == expert_system and entry.domain == domain)

    def modulation_for(self, expert_system: ExpertSystem, domain: DomainName) -> float:
        entries = self.entries_for(expert_system, domain)
        if not entries:
            return 1.0
        total_n_eff = sum(entry.n_eff for entry in entries)
        if total_n_eff <= 0:
            return 1.0
        performance = sum(entry.performance_score() * entry.n_eff for entry in entries) / total_n_eff
        centered = performance - 0.5
        if total_n_eff < self.min_effective_sample_for_adjustment:
            max_delta = self.low_sample_max_delta
        else:
            max_delta = self.mature_sample_max_delta
        delta = max(-max_delta, min(max_delta, centered * 2 * max_delta))
        return max(0.0, 1.0 + delta)

    def n_eff_summary_for_domain(self, domain: DomainName) -> dict[str, Any]:
        summary: dict[str, Any] = {}
        for expert in EXPERT_SYSTEMS:
            entries = self.entries_for(expert, domain)
            summary[expert] = {
                "n_eff": round(sum(entry.n_eff for entry in entries), 6),
                "rule_groups": len({entry.rule_group for entry in entries}),
            }
        return summary

    def audit_summary_for_domain(self, domain: DomainName) -> dict[str, Any]:
        return {
            "feedback_overlay_version": self.version,
            "feedback_overlay_source_path": self.source_path,
            "n_eff_summary": self.n_eff_summary_for_domain(domain),
        }


@dataclass(frozen=True)
class WeightProfilePayload:
    """canonical runtime 权重 profile。"""

    schema_version: str
    status: str
    profile_id: str
    profile_version: str
    updated_at: str
    source: str
    weights: dict[DomainName, dict[ExpertSystem, float]]
    feedback_overlay: FeedbackOverlay = field(default_factory=FeedbackOverlay)

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any], *, source_path: str) -> "WeightProfilePayload":
        schema_version = str(data.get("schema_version") or "")
        if schema_version != "expert-weight-profile/v1":
            raise ValueError(f"expert weights schema_version 必须为 expert-weight-profile/v1，实际为 {schema_version!r}")
        status = str(data.get("status") or "")
        if status != "active":
            raise ValueError(f"expert weights status 必须为 active，实际为 {status!r}")
        profile_id = _required_string(data, "profile_id")
        profile_version = _required_string(data, "profile_version")
        updated_at = _required_string(data, "updated_at")
        source = _required_string(data, "source") if "source" in data else source_path
        weights_raw = data.get("weights")
        if not isinstance(weights_raw, Mapping):
            raise ValueError("expert weights 缺少 weights mapping。")
        weights = _validate_weights(weights_raw)
        return cls(
            schema_version=schema_version,
            status=status,
            profile_id=profile_id,
            profile_version=profile_version,
            updated_at=updated_at,
            source=source,
            weights=weights,
            feedback_overlay=FeedbackOverlay.from_mapping(data.get("feedback_overlay")),
        )

    def audit_summary_for_domain(self, domain: DomainName) -> dict[str, Any]:
        overlay = self.feedback_overlay.audit_summary_for_domain(domain)
        return {
            "weight_profile_version": self.profile_version,
            "source_path": self.source,
            **overlay,
        }


ExpertWeightProfilePayload = WeightProfilePayload


def _validate_weights(weights_raw: Mapping[Any, Any]) -> dict[DomainName, dict[ExpertSystem, float]]:
    weights: dict[DomainName, dict[ExpertSystem, float]] = {}
    for domain in DOMAINS:
        domain_weights = weights_raw.get(domain)
        if not isinstance(domain_weights, Mapping):
            raise ValueError(f"{domain} 权重必须是 mapping。")
        missing = set(EXPERT_SYSTEMS) - set(domain_weights)
        if missing:
            raise ValueError(f"{domain} 缺少专家权重：{sorted(missing)}")
        unexpected = set(domain_weights) - set(EXPERT_SYSTEMS)
        if unexpected:
            raise ValueError(f"{domain} 包含未知专家权重：{sorted(unexpected)}")
        converted: dict[ExpertSystem, float] = {expert: _bounded_float(domain_weights[expert], f"{domain}.{expert}") for expert in EXPERT_SYSTEMS}
        total = sum(converted.values())
        if abs(total - 1.0) > 1e-6:
            raise ValueError(f"{domain} 权重和必须为 1.0，实际为 {total:.6f}")
        weights[domain] = converted
    return weights


def _validate_expert(value: Any) -> ExpertSystem:
    if value not in EXPERT_SYSTEMS:
        raise ValueError(f"未知 expert_system：{value!r}")
    return value


def _validate_domain(value: Any) -> DomainName:
    if value not in DOMAINS:
        raise ValueError(f"未知 domain：{value!r}")
    return value


def _required_non_negative_float(data: Mapping[str, Any], key: str) -> float:
    if key not in data:
        raise ValueError(f"feedback stats 缺少 {key}。")
    return _non_negative_float(data[key], key)


def _required_positive_float(data: Mapping[str, Any], key: str) -> float:
    if key not in data:
        raise ValueError(f"feedback stats 缺少 {key}。")
    return _positive_float(data[key], key)


def _required_string(data: Mapping[str, Any], key: str) -> str:
    value = str(data.get(key) or "")
    if not value:
        raise ValueError(f"expert weights 缺少 {key}。")
    return value


def _non_negative_float(value: Any, label: str) -> float:
    converted = float(value)
    if converted < 0:
        raise ValueError(f"{label} 不得为负数。")
    return converted


def _positive_float(value: Any, label: str) -> float:
    converted = float(value)
    if converted <= 0:
        raise ValueError(f"{label} 必须大于 0。")
    return converted


def _bounded_float(value: Any, label: str) -> float:
    converted = float(value)
    if converted < 0 or converted > 1:
        raise ValueError(f"{label} 必须位于 [0, 1]。")
    return converted


def _wilson_lower_bound(success_count: float, failure_count: float, *, z: float = 1.96) -> float:
    n = success_count + failure_count
    if n <= 0:
        return 0.5
    phat = success_count / n
    denominator = 1 + z * z / n
    centre = phat + z * z / (2 * n)
    margin = z * sqrt((phat * (1 - phat) + z * z / (4 * n)) / n)
    return max(0.0, min(1.0, (centre - margin) / denominator))

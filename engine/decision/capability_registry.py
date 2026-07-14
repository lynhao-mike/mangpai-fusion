"""评估能力后验快照到 L1 的只读查询边界。"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Mapping

from engine.evaluation.models import CapabilityPosterior

_MIN_N_EFF = 5.0
_BACKOFF_WIDENING = {
    "prototype_backoff": 0.08,
    "task_backoff": 0.12,
    "domain_prior": 0.18,
}


@dataclass(frozen=True)
class CapabilityQuery:
    posterior_mean: float
    credible_interval: tuple[float, float]
    n_eff: float
    incremental_gain: float
    evidence_grade: str
    shrink_level: str
    resolved_identity: Mapping[str, str]
    coverage_rate: float = 0.0
    discrimination_score: float = 0.0
    calibration_error: float | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "resolved_identity", MappingProxyType(dict(self.resolved_identity)))


class CapabilityRegistry:
    """不可变能力后验注册表；不写生产权重、不读取标签。"""

    def __init__(self, posteriors: tuple[CapabilityPosterior, ...], snapshot_id: str) -> None:
        self._posteriors = posteriors
        self.snapshot_id = snapshot_id

    @property
    def posterior_count(self) -> int:
        return len(self._posteriors)

    @classmethod
    def from_snapshot(cls, path: str | Path) -> "CapabilityRegistry":
        source = Path(path)
        payload_bytes = source.read_bytes()
        try:
            raw = json.loads(payload_bytes.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError(f"invalid capability snapshot JSON: {exc}") from exc
        if not isinstance(raw, dict) or not isinstance(raw.get("posteriors"), list):
            raise ValueError("capability snapshot requires posteriors array")
        posteriors: list[CapabilityPosterior] = []
        for index, row in enumerate(raw["posteriors"]):
            if not isinstance(row, dict):
                raise ValueError(f"posterior[{index}] must be an object")
            try:
                posteriors.append(CapabilityPosterior.from_dict(row))
            except (KeyError, TypeError, ValueError) as exc:
                raise ValueError(f"invalid posterior[{index}]: {exc}") from exc
        identity_keys = [
            (
                item.school_id, item.task_id, item.chart_prototype_id, item.claim_type,
                item.time_horizon, item.evidence_completeness_band,
            )
            for item in posteriors
        ]
        if len(identity_keys) != len(set(identity_keys)):
            raise ValueError("duplicate capability posterior identity")
        digest = hashlib.sha256(payload_bytes).hexdigest()[:20]
        return cls(tuple(posteriors), f"cap-{digest}")

    @staticmethod
    def _aggregate(rows: list[CapabilityPosterior], level: str, identity: dict[str, str]) -> CapabilityQuery:
        if not rows:
            return CapabilityQuery(0.5, (0.0, 1.0), 0.0, 0.0, "E0", "global_prior", identity)
        weights = [max(item.n_eff, 1.0) for item in rows]
        total_weight = sum(weights)
        mean = sum(item.posterior_mean * weight for item, weight in zip(rows, weights)) / total_weight
        low = min(item.credible_interval[0] for item in rows)
        high = max(item.credible_interval[1] for item in rows)
        widening = _BACKOFF_WIDENING.get(level, 0.0)
        interval = (max(0.0, low - widening), min(1.0, high + widening))
        effective_n = sum(item.n_eff for item in rows)
        gain = sum(item.incremental_gain * weight for item, weight in zip(rows, weights)) / total_weight
        coverage = sum(item.coverage_rate * weight for item, weight in zip(rows, weights)) / total_weight
        discrimination = sum(item.discrimination_score * weight for item, weight in zip(rows, weights)) / total_weight
        calibrated = [(item.calibration_error, weight) for item, weight in zip(rows, weights) if item.calibration_error is not None]
        calibration = None if not calibrated else sum(value * weight for value, weight in calibrated) / sum(weight for _, weight in calibrated)
        grade = max((item.evidence_grade for item in rows), default="E0")
        return CapabilityQuery(mean, interval, effective_n, gain, grade, level, identity, coverage, discrimination, calibration)

    def query(
        self,
        *,
        school_id: str,
        task_id: str,
        chart_prototype_id: str,
        claim_type: str,
        time_horizon: str,
        evidence_completeness_band: str,
    ) -> CapabilityQuery:
        requested = {
            "school_id": school_id,
            "task_id": task_id,
            "chart_prototype_id": chart_prototype_id,
            "claim_type": claim_type,
            "time_horizon": time_horizon,
            "evidence_completeness_band": evidence_completeness_band,
        }
        school_rows = [row for row in self._posteriors if row.school_id == school_id]
        exact = [
            row for row in school_rows
            if all(getattr(row, key) == value for key, value in requested.items() if key != "school_id")
        ]
        if exact and exact[0].n_eff >= _MIN_N_EFF:
            return self._aggregate(exact, "exact", requested)

        prototype_rows = [
            row for row in school_rows
            if row.task_id == task_id and row.chart_prototype_id == chart_prototype_id and row.claim_type == claim_type
        ]
        prototype_usable = [row for row in prototype_rows if row.n_eff >= _MIN_N_EFF]
        if prototype_usable:
            resolved = {**requested, "time_horizon": "*", "evidence_completeness_band": "*"}
            return self._aggregate(prototype_usable, "prototype_backoff", resolved)
        task_rows = [row for row in school_rows if row.task_id == task_id]
        task_usable = [row for row in task_rows if row.n_eff >= _MIN_N_EFF]
        if task_usable:
            resolved = {"school_id": school_id, "task_id": task_id, "chart_prototype_id": "*", "claim_type": "*", "time_horizon": "*", "evidence_completeness_band": "*"}
            return self._aggregate(task_usable, "task_backoff", resolved)
        domain = task_id.split(".", 1)[0]
        domain_rows = [row for row in school_rows if row.task_id.split(".", 1)[0] == domain and row.n_eff >= _MIN_N_EFF]
        if domain_rows:
            resolved = {"school_id": school_id, "domain": domain, "task_id": "*", "chart_prototype_id": "*", "claim_type": "*", "time_horizon": "*", "evidence_completeness_band": "*"}
            return self._aggregate(domain_rows, "domain_prior", resolved)

        # 有覆盖记录但所有层级均低样本：保留审计身份与 N_eff，供 L1 输出 abstain；
        # 完全无该派证据时才是 unsupported/global prior。
        low_sample_rows = task_rows or prototype_rows or exact
        if low_sample_rows:
            resolved = {"school_id": school_id, "task_id": task_id, "chart_prototype_id": "*", "claim_type": "*", "time_horizon": "*", "evidence_completeness_band": "*"}
            return self._aggregate(low_sample_rows, "task_backoff", resolved)
        return CapabilityQuery(0.5, (0.0, 1.0), 0.0, 0.0, "E0", "global_prior", {"school_id": school_id, "domain": "global"})

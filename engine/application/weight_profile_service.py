"""canonical expert weights 加载与裁判权重服务。"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

import yaml

from engine.domain.parallel import DomainName, ExpertSystem, WeightProfile
from engine.domain.parallel_constants import CANONICAL_EXPERT_ORDER
from engine.domain.weighting import FeedbackOverlay, WeightProfilePayload

CANONICAL_WEIGHT_PROFILE_SOURCE = "engine/expert-weights.yaml"
CANONICAL_WEIGHT_PROFILE_PATH = Path(CANONICAL_WEIGHT_PROFILE_SOURCE)
LEGACY_FOUR_SCHOOL_WEIGHT_SOURCE = "engine/domain-weights.yaml"
RAW_REVIEW_DRAFT_WEIGHT_SOURCE = "theory/raw/yaml/domain_weight_profile_2026-06-05.yaml"


class WeightProfileService:
    """裁判层唯一 runtime 权重服务。"""

    def __init__(
        self,
        *,
        workspace_root: str | Path = ".",
        source_path: str | Path = CANONICAL_WEIGHT_PROFILE_SOURCE,
        payload: WeightProfilePayload | None = None,
        feedback_overlay: Mapping[str, Any] | FeedbackOverlay | None = None,
    ) -> None:
        self.workspace_root = Path(workspace_root)
        self.source_path = str(source_path)
        if str(source_path).replace("\\", "/") == LEGACY_FOUR_SCHOOL_WEIGHT_SOURCE:
            raise ValueError("engine/domain-weights.yaml 是 legacy four-school arbitration matrix，不得作为 parallel-domain runtime 权重源。")
        if str(source_path).replace("\\", "/") == RAW_REVIEW_DRAFT_WEIGHT_SOURCE:
            raise ValueError("raw review draft 权重不得作为 runtime 默认源；请使用 engine/expert-weights.yaml。")
        self.payload = payload or load_expert_weight_profile_payload(
            workspace_root=self.workspace_root,
            source_path=source_path,
        )
        if feedback_overlay is None:
            self.feedback_overlay = self.payload.feedback_overlay
        elif isinstance(feedback_overlay, FeedbackOverlay):
            self.feedback_overlay = feedback_overlay
        else:
            self.feedback_overlay = FeedbackOverlay.from_mapping(feedback_overlay)

    def build_weight_profile(self, domain: DomainName) -> WeightProfile:
        prior = self.payload.weights[domain]
        modulated: dict[ExpertSystem, float] = {
            expert: prior[expert] * self.feedback_overlay.modulation_for(expert, domain)
            for expert in prior
        }
        normalized = _normalize_weights(modulated)
        return WeightProfile(
            profile_id=self.payload.profile_id,
            profile_version=self.payload.profile_version,
            source=self.payload.source,
            domain_weights=normalized,
            feedback_modulations={
                expert: self.feedback_overlay.modulation_for(expert, domain)
                for expert in prior
            },
            feedback_overlay_version=self.feedback_overlay.version,
            feedback_overlay_source_path=self.feedback_overlay.source_path,
            n_eff_summary=self.feedback_overlay.n_eff_summary_for_domain(domain),
        )


def load_expert_weight_profile_payload(
    *,
    workspace_root: str | Path = ".",
    source_path: str | Path = CANONICAL_WEIGHT_PROFILE_SOURCE,
) -> WeightProfilePayload:
    """加载 canonical runtime expert weights，并执行强校验。"""

    normalized_source = str(source_path).replace("\\", "/")
    if normalized_source == LEGACY_FOUR_SCHOOL_WEIGHT_SOURCE:
        raise ValueError("engine/domain-weights.yaml 是 legacy four-school arbitration matrix，不得作为 parallel-domain runtime 权重源。")
    path = (Path(workspace_root) / source_path).resolve()
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, Mapping):
        raise ValueError(f"expert weights 顶层必须是 mapping：{path}")
    return WeightProfilePayload.from_mapping(raw, source_path=normalized_source)


def load_domain_weight_profile_payload(*, workspace_root: str | Path = ".") -> dict[str, Any]:
    """兼容旧调用名：默认加载 canonical expert weights payload。"""

    payload = load_expert_weight_profile_payload(workspace_root=workspace_root)
    return _payload_to_dict(payload)


def load_raw_review_draft_weight_profile_payload(*, workspace_root: str | Path = ".") -> dict[str, Any]:
    """迁移辅助：读取 raw review draft，不参与 runtime 默认路径。"""

    path = Path(workspace_root) / RAW_REVIEW_DRAFT_WEIGHT_SOURCE
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, Mapping):
        raise ValueError(f"raw review draft 顶层必须是 mapping：{path}")
    return dict(raw)


def _payload_to_dict(payload: WeightProfilePayload) -> dict[str, Any]:
    return {
        "schema_version": payload.schema_version,
        "status": payload.status,
        "profile_id": payload.profile_id,
        "profile_version": payload.profile_version,
        "updated_at": payload.updated_at,
        "source": payload.source,
        "weights": payload.weights,
        "feedback_overlay": payload.feedback_overlay.audit_summary_for_domain("财运"),
    }


def _normalize_weights(weights: Mapping[ExpertSystem, float]) -> dict[ExpertSystem, float]:
    total = sum(float(value) for value in weights.values())
    if total <= 0:
        equal = 1 / len(CANONICAL_EXPERT_ORDER)
        return {expert: equal for expert in CANONICAL_EXPERT_ORDER}
    return {expert: float(weights.get(expert, 0.0)) / total for expert in CANONICAL_EXPERT_ORDER}

"""Claim 证据引用解析与完整性门禁。"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from engine.claims.domain import Claim
from engine.decision.models import ChartFactLedger
from engine.features import ChartFeatureVector


def _resolve(root: Any, ref: str) -> Any:
    current = root
    for part in ref.split("."):
        if isinstance(current, Mapping):
            if part not in current:
                raise KeyError(ref)
            current = current[part]
        elif isinstance(current, Sequence) and not isinstance(current, (str, bytes)) and part.isdigit():
            index = int(part)
            if index >= len(current):
                raise KeyError(ref)
            current = current[index]
        elif hasattr(current, part):
            current = getattr(current, part)
        else:
            raise KeyError(ref)
    return current


def validate_claim_evidence(
    claim: Claim,
    chart: ChartFactLedger,
    features: ChartFeatureVector,
) -> None:
    """拒绝跨命盘或指向不存在命盘事实/特征节点的命题证据。"""
    from engine.features import build_chart_feature_vector

    expected_chart_id = build_chart_feature_vector(chart, schema_version=features.schema_version).chart_id
    if expected_chart_id != features.chart_id:
        raise ValueError("claim evidence and features must belong to the same chart")
    for evidence in claim.evidence:
        for ref in evidence.fact_refs:
            try:
                _resolve(chart, ref)
            except KeyError as exc:
                raise ValueError(f"unresolved fact_ref: {ref}") from exc
        for ref in evidence.feature_refs:
            try:
                _resolve(features, ref)
            except KeyError as exc:
                raise ValueError(f"unresolved feature_ref: {ref}") from exc

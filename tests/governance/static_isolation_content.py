from __future__ import annotations

import re
from pathlib import Path
from typing import Final

import yaml

from tests.governance.static_isolation_scanner import (
    display_path,
    forbidden_import_issues,
)


GOVERNANCE_CONTAMINATION_IMPORTS: Final = (
    "engine.decision.l7",
    "engine.decision.l8",
    "engine.decision.l9",
    "engine.v5.runner",
    "engine.v5.yang_runner",
)
GOVERNANCE_CONTAMINATION_TOKENS: Final = (
    "cases/",
    "feedback.md",
    "learning/",
    "learning_log",
    "predictions/",
    "reports/",
    "sample-hit-results",
    "sample_hit_results",
    "label_path",
)
CASE_ID_PATTERN: Final = re.compile(r"\b(?:C|P-GO|NEW-P)-20\d{2}(?:-[A-Za-z0-9]+)*\b")
ABSOLUTE_PATH_PATTERN: Final = re.compile(
    r"(?:[A-Za-z]:[\\/][^\s]+|\\\\[^\\/\s]+[\\/][^\s]+|/(?!/)[^\s:]+/[^\s]+)"
)
PREDICTION_RESULT_LABELS: Final = frozenset(
    {
        "feedback_verdict",
        "hit",
        "hit_result",
        "miss",
        "partial",
        "prediction_label",
        "sample_hit",
        "sample_hits",
    }
)

type YamlScalar = str | int | float | bool | None
type YamlNode = YamlScalar | list[YamlNode] | dict[YamlScalar, YamlNode]


def source_token_issues(
    paths: tuple[Path, ...], tokens: tuple[str, ...]
) -> tuple[str, ...]:
    issues: list[str] = []
    for path in paths:
        source = path.read_text(encoding="utf-8")
        issues.extend(
            f"{display_path(path)} contains {token}"
            for token in tokens
            if token in source
        )
    return tuple(issues)


def governance_contamination_issues(paths: tuple[Path, ...]) -> tuple[str, ...]:
    return (
        *forbidden_import_issues(paths, GOVERNANCE_CONTAMINATION_IMPORTS),
        *source_token_issues(paths, GOVERNANCE_CONTAMINATION_TOKENS),
    )


def yaml_scalars(path: Path) -> tuple[str, ...]:
    loaded: YamlNode = yaml.safe_load(path.read_text(encoding="utf-8"))
    return _yaml_value_scalars(loaded)


def _yaml_value_scalars(value: YamlNode) -> tuple[str, ...]:
    if isinstance(value, str):
        return (value,)
    if isinstance(value, list):
        return tuple(scalar for item in value for scalar in _yaml_value_scalars(item))
    if isinstance(value, dict):
        return tuple(
            scalar
            for key, item in value.items()
            for scalar in (*_yaml_value_scalars(key), *_yaml_value_scalars(item))
        )
    return ()


def governance_yaml_issues(path: Path) -> tuple[str, ...]:
    issues: list[str] = []
    for scalar in yaml_scalars(path):
        for case_id in CASE_ID_PATTERN.findall(scalar):
            issues.append(f"{display_path(path)} contains historical case id {case_id}")
        if scalar in PREDICTION_RESULT_LABELS:
            issues.append(
                f"{display_path(path)} contains prediction/result label {scalar}"
            )
        for absolute_path in ABSOLUTE_PATH_PATTERN.findall(scalar):
            issues.append(
                f"{display_path(path)} contains absolute path {absolute_path}"
            )
    return tuple(issues)

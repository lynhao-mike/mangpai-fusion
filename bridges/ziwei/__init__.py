"""紫微斗数旁证接入：同参映射、只读查表、L1 盘面核验、证据信封。

三层约定见 docs/ziwei-corroboration-bridge.md：
事实层 engine.cli / 理论层 query_theory / 旁证层 evidence-envelope/v1。
"""
from .case_key import BRANCHES, CaseKey, build_case_key, hour_index, parse_birth
from .chart_l1 import (
    DEFAULT_CLAIMS, chart_fingerprint, evaluate_assertions, generate_chart, summarize_chart,
)
from .envelope import (
    ATTRIBUTION, ENVELOPE_VERSION, NOT_USABLE_AS, POLICY,
    build_envelope, build_l1_envelope,
)
from .lookup import load_config, lookup

__all__ = [
    "BRANCHES",
    "CaseKey",
    "build_case_key",
    "hour_index",
    "parse_birth",
    "DEFAULT_CLAIMS",
    "chart_fingerprint",
    "evaluate_assertions",
    "generate_chart",
    "summarize_chart",
    "ATTRIBUTION",
    "ENVELOPE_VERSION",
    "NOT_USABLE_AS",
    "POLICY",
    "build_envelope",
    "build_l1_envelope",
    "load_config",
    "lookup",
]

"""v5 冻结白名单快照（ADR-006 / ADR-007 D9）。

本文件是**数据快照**，不含逻辑。冻结时间 2026-10-27（T-144），扫描口径：
全仓 `*.py` 中 `import engine.v5[.*]` 或 `from engine import v5`（AST 级，非文本 grep）。

**只减不增**：任何新增 `import engine.v5` 都会让
`tests/governance/test_v5_import_freeze.py` 变红。要让门禁变绿只有一条路——把引用删掉，
**不许**往这里加路径；加路径同时会触犯条目数上限断言。
"""

from __future__ import annotations

from typing import Final

#: 冻结时刻的命中文件数上限。新增引用 = 需要往白名单加路径 = 超过上限 = 红。
FROZEN_IMPORTER_COUNT_MAX: Final[int] = 85

#: 冻结时刻的真实命中集合（85 个：engine 34 / tools 8 / tests 43）。
FROZEN_V5_IMPORTERS: Final[frozenset[str]] = frozenset(
    {
        "engine/application/production_service.py",
        "engine/asof/career_event_prediction.py",
        "engine/claims/runner_registry.py",
        "engine/decision/l2_v5_claims.py",
        "engine/decision/r10_ziping_career.py",
        "engine/decision/v5_adapter.py",
        "engine/decision/yang_marriage_slice.py",
        "engine/evaluation/blind_adapter.py",
        "engine/evaluation/career_event_replay.py",
        "engine/evaluation/domain_prospective.py",
        "engine/evaluation/dual_line_interop.py",
        "engine/v5/__init__.py",
        "engine/v5/adjudication.py",
        "engine/v5/ditiansui_runner.py",
        "engine/v5/domain_analysis_report.py",
        "engine/v5/domain_capability_metrics.py",
        "engine/v5/domain_feedback.py",
        "engine/v5/domain_metadata_integrity.py",
        "engine/v5/domain_report_view.py",
        "engine/v5/domain_slices/__init__.py",
        "engine/v5/domain_slices/career/__init__.py",
        "engine/v5/domain_slices/context.py",
        "engine/v5/domain_slices/contract.py",
        "engine/v5/domain_slices/marriage/__init__.py",
        "engine/v5/domain_slices/orchestrator.py",
        "engine/v5/domain_slices/registry.py",
        "engine/v5/domain_slices/wealth/__init__.py",
        "engine/v5/duan_runner.py",
        "engine/v5/gao_runner.py",
        "engine/v5/high_risk_gate.py",
        "engine/v5/preprod.py",
        "engine/v5/report_view.py",
        "engine/v5/runner.py",
        "engine/v5/ziping_runner.py",
        "tests/asof/test_career_event_prediction.py",
        "tests/claims/test_claim_engine.py",
        "tests/claims/test_duan_runner.py",
        "tests/claims/test_duan_timing.py",
        "tests/claims/test_gao_timing.py",
        "tests/claims/test_ren_binary_career.py",
        "tests/claims/test_runner_registry.py",
        "tests/claims/test_school_strength_runners.py",
        "tests/decision/test_staged_arbitration.py",
        "tests/evaluation/test_blind_adapter.py",
        "tests/evaluation/test_domain_prospective.py",
        "tests/evaluation/test_dual_line_interop.py",
        "tests/features/test_chart_feature_vector.py",
        "tests/r10/test_r10_ziping_career_acceptance.py",
        "tests/r10/test_r10_ziping_career_l2.py",
        "tests/test_archive_links.py",
        "tests/test_decision_v5_adapter.py",
        "tests/test_l4_event_type.py",
        "tests/test_l9_router_calibration.py",
        "tests/tools/test_domain_analysis_cli.py",
        "tests/tools/test_domain_capability_status.py",
        "tests/tools/test_domain_feedback.py",
        "tests/tools/test_domain_prospective_cohort.py",
        "tests/v1_3_acceptance/test_h3_feedback_parsing.py",
        "tests/v5/domain_slices/test_career_slices.py",
        "tests/v5/domain_slices/test_wealth_marriage_slices.py",
        "tests/v5/test_domain_analysis_context.py",
        "tests/v5/test_domain_analysis_orchestrator.py",
        "tests/v5/test_domain_analysis_report.py",
        "tests/v5/test_domain_capability_metrics.py",
        "tests/v5/test_domain_feedback.py",
        "tests/v5/test_domain_slice_contract.py",
        "tests/v5/test_high_risk_gate.py",
        "tests/v5/test_manifest_isolation.py",
        "tests/v5/test_render_report_v5_bridge.py",
        "tests/v5/test_render_report_v6.py",
        "tests/v5/test_report_reads_l7.py",
        "tests/v5/test_report_view.py",
        "tests/v5/test_v5_adjudication_units.py",
        "tests/v5/test_v5_contracts.py",
        "tests/v5/test_v5_output_linter.py",
        "tests/yang_marriage/fixtures.py",
        "tests/yang_marriage/test_slice_layers.py",
        "tools/domain_analysis_cli.py",
        "tools/domain_capability_status.py",
        "tools/domain_feedback.py",
        "tools/domain_prospective_cohort.py",
        "tools/feedback_ingest.py",
        "tools/p_series_career_blind_harness.py",
        "tools/render_report.py",
        "tools/render_report_v6.py",
    }
)

#: 冻结时刻已存在的「无法用当前解释器解析」文件（PEP 695 `type X = ...`，需 3.12+）。
#: 它们不含任何 engine.v5 引用（人工核对 + 文本 grep 双查）。**不得新增**：
#: 出现新的不可解析文件时门禁直接报红，避免用「解析失败」当免检通道。
FROZEN_UNPARSEABLE: Final[frozenset[str]] = frozenset(
    {
        "engine/governance/structure_catalog_models.py",
        "engine/governance/structure_catalog_types.py",
    }
)

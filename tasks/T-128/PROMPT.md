# T-128 · v5 退役（避免双推理链干扰）

- 状态：🔵 Ready for Execution
- 优先级：P1（你已定为「优先退役」）
- 创建：2026-10-26（中枢）
- 决策依据：ADR-001（引擎=事实+候选，Agent=裁决）、10-20 决策「v5 仅保留为度量链」

## 1. 实测依赖（2026-10-26）

| 项 | 数量 |
|---|---|
| 引用 `engine.v5` 的 Python 文件 | 129（含 `.worktrees/` 副本；主工作区约 60） |
| `engine/v5/` 文件数 / 体积 | 100 个 / 1.5 MB |
| 生产入口依赖 | `tools/render_report.py`、`tools/domain_analysis_cli.py`、`tools/domain_capability_status.py`、`tools/domain_feedback.py`、`tools/feedback_ingest.py`、`tools/p_series_career_blind_harness.py` |
| 测试 | `tests/v5/`（默认 addopts 已 ignore）、`tests/r10/`（4 failed） |

**结论：不能直接删。** 三个 `active_report_entrypoints` 被 `tests/test_project_metadata.py` 精确断言，删 v5 会连带改入口实现，必须分阶段。

## 2. 四阶段（strangler，绞杀者模式）

| 阶段 | 做什么 | 工时 | 立即收益 |
|---|---|---|---|
| **P0 冻结** | `engine/v5/__init__.py` 加 `LEGACY` 标记；`META/project-state.json` 与 `AGENTS.md` 写明「v5 = 仅度量链，禁止新增调用」；新代码引用 v5 视为违规 | 半天 | **立刻消除「两条推理链」的混淆**，这是你说的干扰 |
| **P1 渲染路径去 v5** | `tools/render_report.py` 内部改为新链路（facts + claim-condition 候选 + 模板），对外参数与输出不变 | 3–5 天 | 用户可见报告不再经过 v5 |
| **P2 度量链接管** | 用 blind ledger + claim-condition 产出与 `balanced_accuracy` 等价的指标；`domain_prospective` 链路切到新实现 | 1 周 | B 指标不再依赖 v5 |
| **P3 归档** | `engine/v5/` → `_archive/v5/`；删除 import；`tests/v5` 一并归档；跑全量门禁 | 2–3 天 | 依赖清零 |

## 3. 硬约束

- **不得**修改 `tests/test_project_metadata.py` 的 `active_report_entrypoints` 断言；P1 只换实现，不换入口清单。
- **不得**在 P2 完成前删除 `balanced_accuracy` 相关链路，否则 B 指标断供。
- P3 前必须确认 `.worktrees/` 不受影响（它是独立工作树，不在本轮范围）。

## 4. 验收

```bash
python -m pytest -q                     # 无新增失败
python -m tools.render_report <case>    # 输出与 P1 前逐段对比，除措辞外无结构差异
python -m tools.domain_analysis_cli status
grep -rn "engine.v5" --include=*.py engine tools | wc -l   # P3 后应为 0
```

## 5. File Scope

- `engine/v5/`（P0 加标记；P3 归档）
- `tools/render_report.py`、`tools/domain_analysis_cli.py`、`tools/domain_capability_status.py`
- `tools/domain_feedback.py`、`tools/feedback_ingest.py`
- `META/project-state.json`（仅新增 `v5_status` 键，不动被断言字段）
- `AGENTS.md` §2（导航图标注 v5 为 legacy）

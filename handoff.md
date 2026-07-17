# HANDOFF · 短期交接

> 更新时间：2026-07-17（Asia/Shanghai）
>
> 本文件仅记录下一步和本轮清理，不是长期事实源；当前状态以正式制品与 [`META/project-state.json`](META/project-state.json:1) 为准。

## 1. 当前结论

- 事实源漂移已修复。
- `prediction_capability_candidate_gate_v1 = HOLD`。
- `future_empirical_gate_v1 = HOLD`。
- `historical_platform_baseline_2026_07_15 = HOLD`。
- 生产默认仍为 static routing；staged 仅用于并跑和离线评估，`production_switch=false`，不得据此修改生产入口、规则或权重。

## 2. 首案当前状态与下一动作

首案：[`P-GO-2026-001-坤-壬戌己酉乙卯丁亥`](META/prospective-go/single-cases/P-GO-2026-001-坤-壬戌己酉乙卯丁亥/)

- [`v004 immutable frozen run`](META/prospective-go/single-cases/P-GO-2026-001-坤-壬戌己酉乙卯丁亥/P-GO-2026-001-坤-壬戌己酉乙卯丁亥--frozen-run--v004.json:1) 已存在。
- [`feedback-release v001`](META/prospective-go/single-cases/P-GO-2026-001-坤-壬戌己酉乙卯丁亥/P-GO-2026-001-坤-壬戌己酉乙卯丁亥--feedback-release--v001.json:1) 已存在且为 `RELEASED`；不要再执行 `issue-feedback-release`。
- 实查尚无首案 immediate retrospective、bound 或 case completion 制品。
- 下一合法业务链：基于 [`prospective immediate retrospective template`](templates/prospective-immediate-retrospective-v1.json:1) 释放即时回顾模板 → 收集 freeze 前已发生的事实 → 对高风险事实执行双人独立复核，冲突则第三方仲裁 → bind → completion。
- freeze 后才发生的事实不得混入即时回顾；预注册 future question 仅在观察窗成熟后进入独立 future observation 账。
- 不覆盖既有 intake、blind bundle、future registration、frozen run 或 release 制品。

## 3. 本轮清理结果

以下数字仅描述本次仓库清理，不是运行时规则状态：

- 临时 SDD 13 份、1557 行已删除。
- 历史增量临时目录已提升为正式 [`historical incremental evidence manifest`](META/historical-incremental-evidence-manifest-2026-07-16.json:1) 后删除；正式提升制品与来源摘要以该 manifest 为准。
- 已执行计划 22 份、8692 行已清理。
- 已删除计划和临时材料不得从旧路径恢复；历史追溯使用 Git。

## 4. 新会话最小必读

1. [`AGENTS.md`](AGENTS.md:1)：仓库规则与事实源矩阵。
2. [`META/project-state.json`](META/project-state.json:1)：当前机器状态。
3. [`META/prospective-intake-protocol-v1.md`](META/prospective-intake-protocol-v1.md:1)：prospective 正式协议。
4. [`单案当天冻结与即时回顾反馈设计规格`](docs/superpowers/specs/2026-07-16-single-case-immediate-freeze-feedback-design.md:1)：单案链、分账与两层新门禁契约。
5. [`首案正式制品目录`](META/prospective-go/single-cases/P-GO-2026-001-坤-壬戌己酉乙卯丁亥/)：执行前按实际文件确认进度。
6. [`历史增量证据 manifest`](META/historical-incremental-evidence-manifest-2026-07-16.json:1)：已删除临时目录的正式 provenance 入口。

[`handoff.md`](handoff.md:1) 自身不列为长期事实源；若与正式制品冲突，以正式制品和 [`META/project-state.json`](META/project-state.json:1) 为准。

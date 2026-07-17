# HANDOFF · 最小盲测闭环与双门禁 HOLD 交接

> 写给一个完全没有上下文的新会话。
>
> 更新时间：2026-07-17（Asia/Shanghai）
>
> 本文件只作短期交接，不是长期事实源；当前事实必须回到 [`AGENTS.md`](AGENTS.md:1)、[`META/project-state.json`](META/project-state.json:1) 与正式门禁制品确认。

## 1. 必读事实源

1. [`README.md`](README.md:1)
2. [`AGENTS.md`](AGENTS.md:1)
3. [`META/project-state.json`](META/project-state.json:1)
4. [`META/prospective-intake-protocol-v1.md`](META/prospective-intake-protocol-v1.md:1)
5. [`docs/superpowers/specs/2026-07-16-single-case-immediate-freeze-feedback-design.md`](docs/superpowers/specs/2026-07-16-single-case-immediate-freeze-feedback-design.md:1)
6. [`plans/upgrade-guides/post-gate-action-plan-2026-07-15.md`](plans/upgrade-guides/post-gate-action-plan-2026-07-15.md:314)
7. [`tools/README.md`](tools/README.md:154)
8. [`META/six-month-platform-gate-2026-07-15.md`](META/six-month-platform-gate-2026-07-15.md:1) 与 [`META/six-month-platform-gate-2026-07-15.json`](META/six-month-platform-gate-2026-07-15.json:1)

## 2. 当前门禁状态

- `prediction_capability_candidate_gate_v1 = HOLD`：即时回顾完成数尚未满足 20 案及其余 15 条正反例、校准、竞争、selection change、utility、高风险与审计条件。
- `future_empirical_gate_v1 = HOLD`：到期未来观察完成数尚未满足 10 案及其余同类任务 8 条正反例等严格条件。
- `historical_platform_baseline_2026_07_15 = HOLD`：只读、独立；不得以 `20 immediate + 10 future` 或任何新门禁样本冲抵原 30 案 baseline。
- 两个新门禁均为仅离线评估。离线 GO 不代表平台 GO 或生产 GO；`production_switch=false`。
- 生产默认继续使用 static routing；staged 只用于并跑和评估，不修改 [`run_pipeline()`](engine/application/pipeline_runner.py:1)、[`DEFAULT_RUNNER_REGISTRY`](engine/claims/runner_registry.py:1)、生产规则或权重。

## 3. 首案下一合法动作

首案 v004 的 immutable frozen result 已正式存在。下一合法动作是复算其 canonical hash、内部 freeze hash 与父链；通过后直接以 [`issue-feedback-release`](tools/school_capability_dataset.py:1200) 的 `--frozen-run` 参数生成 create-only release，再接收命主信息或登记待核验盲测结果。

1. 不覆盖 v001—v004 的 intake、blind bundle 或 frozen run。
2. freeze 前事实进入 `prediction_first_immediate_retrospective`；预注册 future question 仅在窗口成熟后进入独立 `future_observation`。两账完成数、label identity 与高风险审查不得复用。
3. witness / witness key / 外部 root / freeze verification 仅为可选审计兼容入口，不是反馈前置条件；不得为补链伪造任何制品。
4. 每累计 10 个回顾完成案只创建父引用 cohort；10 案不控制单案 intake、freeze 或反馈释放。

## 4. 可选 Witness 审计边界

- 仅在明确需要增强审计时使用；不参与最小反馈门槛。
- 若使用，见证人仍须独立，agent 不接触密钥值、外部 root 或终端环境。
- 可选审计失败只影响 witness 审计声明，不允许借机覆盖或重冻已封存结果。

## 5. 禁止事项

- 不运行真实 gate，不生成空或伪造 prospective/gate 制品。
- 不把 immediate retrospective 称为 future outcome，不把 `no_data` 当负例。
- 不混算两个新门禁，也不重算、覆盖 historical baseline。
- 不把离线 GO 写成平台 GO 或生产 GO。
- 不自动触发生产反馈学习；生产反馈仍只走 [`tools/feedback_ingest.py`](tools/feedback_ingest.py:1) 的独立流程。
- 不 commit / push 未经明确授权的真实数据制品、外部 root、终端记录或任何秘密。

# HANDOFF · 单案当天冻结与双门禁 HOLD 交接

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

下一合法动作不是等待或补齐 10 案，而是对已授权首案执行“每案 dry-run 后当天正式 single-case intake”，不等待 10 案：

1. 复验首案脱敏 [`input.md`](cases/P-GO-2026-001-坤-壬戌己酉乙卯丁亥/input.md:1) 不含经历、当前现状、反馈、标签、旧报告或 known facts。
2. 由授权人批准恰好 1 个 freeze 后三个月内可核验的 binary future question；agent 不得猜测答案。
3. 按 [`tools/school_capability_dataset.py`](tools/school_capability_dataset.py:1306) 的真实 parser 先运行 `single-case-intake --dry-run`，人工核对后才允许正式写入不存在的单案路径。
4. 每案独立执行 bundle / freeze / witness / verification；每个写操作先 dry-run，禁止覆盖父制品。
5. 独立人类见证人在其临时 `cmd.exe` 中私下持有真实 key。agent 不得读取、请求、记录或展示 key，只能引用环境变量名 `SCHOOL_CAPABILITY_WITNESS_KEY`。
6. verification 是人工硬停点：verification=VERIFIED 前禁止反馈释放，不得读取或请求反馈，也不得创建即时回顾、future observation、report 或 label。
7. VERIFIED 后，freeze 前事实进入 `prediction_first_immediate_retrospective`；预注册 future question 仅在窗口成熟后进入独立 `future_observation`。两账完成数、label identity 与高风险审查不得复用。
8. 每累计 10 个回顾完成案只创建父引用 cohort；10 案不控制单案 intake、freeze、verification 或反馈释放。

## 4. Witness 人工边界

- 见证人必须独立于 intake operator、runner operator、outcome custodian、reviewer A/B 与 adjudicator。
- agent 只提供实际父路径和 SHA-256，不接触密钥值、终端屏幕、命令历史、环境、剪贴板或日志。
- 见证人亲自先 dry-run 后正式签署并验证实际 intake、bundle、frozen run、registry 与仓库外 root。
- 完成后见证人执行 `set "SCHOOL_CAPABILITY_WITNESS_KEY="`，只运行 SET / NOT SET 存在性检查；预期为 `NOT SET`，随后关闭临时终端。
- 只有独立人类明确确认 verification 制品存在且 `status=VERIFIED`，流程才可越过人工硬停点。

## 5. 禁止事项

- 不运行真实 gate，不生成空或伪造 prospective/gate 制品。
- 不把 immediate retrospective 称为 future outcome，不把 `no_data` 当负例。
- 不混算两个新门禁，也不重算、覆盖 historical baseline。
- 不把离线 GO 写成平台 GO 或生产 GO。
- 不自动触发生产反馈学习；生产反馈仍只走 [`tools/feedback_ingest.py`](tools/feedback_ingest.py:1) 的独立流程。
- 不 commit / push 未经明确授权的真实数据制品、外部 root、终端记录或任何秘密。

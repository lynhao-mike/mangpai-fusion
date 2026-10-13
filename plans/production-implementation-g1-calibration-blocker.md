# PI-195 · G1 状态校准独立验收与阻断包

> 日期：2026-07-19（Asia/Shanghai）
>
> 任务：`PI-195`
>
> 父任务：`PI-100`
>
> 模式：独立验收；只读调查，不修复

## 1. 裁决

`BLOCKED`

现有源码足以重建 PI-110、PI-120、PI-130 所需的大部分架构盘点，但现有仓库证据不足以把 [`handoff.md`](../handoff.md) 中的“PI-190 已独立裁决 G1 = PASS”校准写成权威完成状态。

阻断发生在治理证据完整性，不等于否定既有技术发现，也不表示 F01–F12 已实现。

## 2. 阻断问题

1. 唯一动态任务状态源 [`production-implementation-control.md`](production-implementation-control.md) 仍将 G1 标为 `READY`，PI-100 标为 `READY`，PI-110、PI-120、PI-130、PI-190 标为 `BLOCKED`。
2. 仓库中未定位到三个盘点任务各自的持久化交付物，也未定位到 PI-190 的独立裁决记录。
3. 完成与 PASS 声明只见于短期交接 [`handoff.md`](../handoff.md)，但该文件明确声明动态任务状态只能以总控为准。
4. 总控治理规则要求：父任务不能只凭子任务摘要宣称完成；任务必须同时具备交付物与验收证据；阶段门只能由独立验收 PASS。

因此不能把“可从源码重新证明架构发现”替代成“此前 PI-110/120/130 的交付物及 PI-190 独立裁决已经存在”。

## 3. 已复核的技术证据

### 3.1 PI-110：输入与 pipeline

生产默认链可定位为：

```text
ProductionAnalysisService._run_existing_job
→ run_pipeline_e2e
→ default_pipeline_adapters
→ ToolsPreflightAdapter.parse
→ tools.preflight.parse
→ adapt_parsed
→ run_pipeline
→ integrate
→ findings repository
```

可确认：命盘、已知事实与问题能被入口解析和跨适配层保留；D1–D4 与整合输出有明确调用链和持久化点。

不可扩大为：

- `questions` 已被默认候选生成逻辑消费；当前候选提取只遍历已知事实；
- 全部已知事实都进入 D3；当前仅带年份且含事件或内容的事实子集进入；
- 已有统一外部时间范围协议。

### 3.2 PI-120：findings、决策、冲突和五动作

现有模型可表达 findings、跨派冲突、并行域裁判和 run-centric 决策，但这些能力分布于生产默认链、旁路和 staged/preprod 链，不能混写为一个统一生产协议。

生产默认整合返回的结构化冲突列表为空；未证明默认链自动发现并裁决结构化冲突。

`OUTPUT`、`CONDITIONAL`、`ASK`、`ABSTAIN`、`HUMAN_REVIEW` 尚无统一运行时协议；现有代码只有分散的近似状态，且未定位到统一 `ASK` 动作。

### 3.3 PI-130：报告、statement 与 feedback

标准报告链可生成报告，并尝试生成 `statement_index.json` 与 `statement_records.json`。结构化反馈入口以 statement records 作为规则 fanout 来源，旧 statement index 不再单独构成 Dynamic Confidence fanout 来源。

仍须保留以下边界：

- 默认 pipeline feedback adapter 与当前结构化 feedback ingest 入口语义不同；
- 生产提交默认关闭自动自迭代，报告到反馈不是单次提交内自动闭合事务；
- statement artifact 写入失败可警告降级，报告成功不保证反馈桥完整。

### 3.4 生产与 staged/preprod 分账

| 轨道 | 结论 |
|---|---|
| 生产默认链 | 生产服务到 D1–D4、整合与标准渲染可定位 |
| 生产兼容适配 | preflight、标准 renderer、旧 feedback loop 适配可定位，但反馈语义需分账 |
| 旁路能力 | 并行域输出和跨域扫描可复用，不等于默认生产能力 |
| staged/preprod | v5 snapshot、DecisionRun 和 feedback attachment 为 opt-in 证明链，不得冒充生产默认 |
| F01–F12 机器附录 | 声明性冻结数据；未发现运行时消费证据，不是已实现执行逻辑 |

## 4. 影响

- G1 不能从 `READY` 校准为 `COMPLETED`。
- PI-100、PI-110、PI-120、PI-130、PI-190 不能仅依据 handoff 摘要补写为 `COMPLETED`。
- G2 及下游 DAG 必须停止；不得启动 PI-200、PI-210、PI-220、PI-230、PI-290。
- 不得进入 G3、G4，不得生成 G5 实现计划，不得修改生产代码或默认行为。

## 5. 可选处置

| 选项 | 动作 | 影响 |
|---|---|---|
| A（推荐） | 在允许写入的 [`plans/`](./) 下补建 PI-110、PI-120、PI-130 三份持久化盘点交付物；再创建新的 PI-190 独立验收实例形成裁决记录；最后重新执行 PI-195 | 保持治理证据链完整；工作量较高，但不触碰冻结语义和生产代码 |
| B | 用户明确裁决 handoff 中的历史 PASS 可作为一次性迁移证据，并授权在总控登记该例外 | 证据链较弱；需记录人工例外，不应成为后续阶段门惯例 |
| C | 取消本轮生产实现设计 | G1 及下游保持阻断或取消，不产生实现设计 |

## 6. 解除条件

选择 A 时必须同时满足：

1. PI-110、PI-120、PI-130 各自存在可定位交付物，包含文件、符号、行号或调用链证据；
2. 三份交付物明确区分已证明能力、缺口、生产默认链与 staged/preprod 链；
3. PI-190 由与盘点任务分离的独立验收实例裁决并形成持久化记录；
4. 总控中的任务状态、产物、验收证据、阻断项和唯一下一动作同步更新；
5. 新的 PI-195 独立状态校准返回 PASS。

## 7. 所需用户决策

需要用户在 A、B、C 中作出明确选择。用户作出选择前，本工作停在 G1 `BLOCKED`，下游保持 `BLOCKED`。

## 8. 验证说明

本次仅执行静态证据核验，未修改生产或数据文件，未运行会改仓库数据的命令，也未声称测试通过。

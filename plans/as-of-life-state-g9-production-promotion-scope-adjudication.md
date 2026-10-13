# as-of-life-state G9 · 生产 promotion 范围裁决

> 状态：`ADMISSION — PASS`；`CONTRACT — 待用户互斥选项裁决`。本文只裁决范围，不实现、不测试、不改变任何生产默认行为。
>
> 唯一写入：本文件。未修改 `engine/asof/`、`engine/application/production_service.py`、`tools/production_api.py`、`tools/as_of_integration.py`、任何测试或 G0-G8 冻结文档。

## 1. 权威输入与当前事实

按冲突优先级：

1. [`plans/as-of-life-state-reasoning-design-2026-07-18.md`](as-of-life-state-reasoning-design-2026-07-18.md:1) §15 架构不变量——唯一业务语义事实源；
2. [`plans/as-of-life-state-g0-g5-execution-plan-for-terra.md`](as-of-life-state-g0-g5-execution-plan-for-terra.md:1) §1 硬性纪律——生产零改动、单案深耕、GitHub 永久禁止；
3. [`plans/as-of-life-state-g8-production-integration-spec.md`](as-of-life-state-g8-production-integration-spec.md:1)——已冻结的薄接线单向依赖与账本协议；
4. [`reports/as-of-life-state-g8-production-integration-report.md`](../reports/as-of-life-state-g8-production-integration-report.md:1)——G8 evidence-bounded freeze，仅证明 CLI/程序 API 薄层，未接入 `ProductionAnalysisService` 或 `tools/production_api.py`；
5. 运行时 public surface：[`engine/application/production_service.py`](../engine/application/production_service.py:1)（`SubmitAnalysisRequest`、`ProductionAnalysisService._run_existing_job()`）、[`tools/production_api.py`](../tools/production_api.py:1)（无鉴权 stdlib HTTP JSON API）。

**已完成、不得重判：** G0-G8 均为 `PASS / COMPLETE — EVIDENCE-BOUNDED FREEZE` 或等价收口；`tools/as_of_integration.py` 是唯一新增薄层，未接入任何 production-default 入口；`engine/asof/` 零 diff。

**当前 production-default 事实：**

- [`SubmitAnalysisRequest`](../engine/application/production_service.py:41) 无 `as_of_date`、`event_ledger` 或等价字段；
- [`ProductionAnalysisService._run_existing_job()`](../engine/application/production_service.py:141) 固定调用 `run_pipeline_e2e(..., error_policy="strict")`，不调用 `engine.asof`；
- [`tools/production_api.py`](../tools/production_api.py:1) 是**无鉴权** stdlib HTTP JSON 服务，仅建议本地/内部 MVP 部署；任何 promotion 方案若扩大其网络暴露面，必须独立标注该安全边界，不得默认新增无鉴权网络能力。

## 2. 候选范围与互斥选项

promotion 的核心矛盾：as-of 回放要求**显式、受控的事件账本**（`entries`/`daiyun_end`/`current_center`/`ledger_case_id`），而当前生产请求协议（HTTP JSON / `SubmitAnalysisRequest`）没有该输入通道，也没有账本的持久化事实源。三个互斥方案代表三种不同的"账本从哪来"裁决，不能都选：

### P1（保守）：CLI-only 生产别名，不改公共 API

- 范围：新增 `tools/production_as_of_cli.py`（或类似名称）作为 `tools/as_of_integration.py` 的生产路径别名，仅补齐 `--cases-dir`/`--reports-dir` 默认值对齐生产目录约定；**不修改** `SubmitAnalysisRequest`、`ProductionAnalysisService`、`tools/production_api.py`。
- 账本来源：调用方仍需在命令行显式提供 `--ledger` JSON 文件；不建立账本持久化或审批流程。
- 影响面：零 public schema 变更；零 HTTP API 变更；风险最低。
- 代价：不能通过 HTTP API 触发 as-of 回放；仍是运营者手动调用的旁路能力，"promotion" 只是路径规范化，不是真正的生产集成。

### P2（干净）：`ProductionAnalysisService` opt-in 字段

- 范围：为 `SubmitAnalysisRequest` 新增可选字段（如 `as_of_date`、`event_ledger_path`），默认 `None`；仅当显式提供时才在 `_run_existing_job()` 内追加调用 G8 薄层的 as-of 分支；未提供时行为与当前逐字节相同。
- 账本来源：调用方随请求提供账本文件路径或内嵌 JSON；服务端仍不做自动推导或持久化账本审批，只做 schema 扩展和参数透传。
- 影响面：**public API schema 扩展**——这是新增字段而非删除或收窄，向后兼容，但需要独立 CONTRACT 冻结字段名、类型、校验失败语义、artifact 归档位置，并重新过 PI-230 式追溯绑定检查。
- 代价：工程量高于 P1；一旦 schema 冻结，字段语义变更需要走新的治理轮次；`tools/production_api.py` 若同步暴露该字段，会把无鉴权服务的攻击面扩大到"任意调用方可提交任意事件账本声称为已核验事实"，必须显式标注为高风险并单独裁决是否经 API 暴露。

### P3（分阶段）：先影子试跑，不接生产请求协议

- 阶段 1：只对**历史已完成** case（如 G6/G7 验证用例）用 `tools/as_of_integration.py` CLI 批量生成 as-of 报告，写入独立 `reports/as-of-shadow/` 目录，作为运营辅助材料，不接入任何生产请求路径。
- 阶段 2（需新裁决）：若阶段 1 证明账本维护成本可控，再评估是否需要 P1 或 P2。
- 影响面：本阶段零 schema 变更、零 API 变更；只有新增 CLI 批处理脚本和独立报告目录。
- 代价：进度最慢；把"是否接入生产协议"的裁决推迟到下一轮，等于本轮 G9 只完成前置试跑，不完成真正的 promotion。

### 非目标（三个选项共同排除）

- 不建立事件账本的自动推导、自动核验或自动审批流程——违反 [`reasoning-design`](as-of-life-state-reasoning-design-2026-07-18.md:1) §3.5 根源不可回填与账本证据边界；
- 不默认开启 as-of 回放（任何选项下 `as_of_date=None` 必须是默认值且零副作用）；
- 不修改 `engine/asof/` 内部算法或 G0-G7 冻结契约；
- 不在未经独立裁决前扩大 [`tools/production_api.py`](../tools/production_api.py:1) 的无鉴权网络暴露面；
- 不做样本外后验校准、Beta 切换或统计学习层——这些属于 as-of 轨道尚未讨论的另一个方向，不属于本次 G9。

## 3. 风险登记

| 风险 | 影响 | 触发方案 | 缓解 |
|---|---|---|---|
| R1 | HTTP API 暴露账本注入通道，无鉴权环境下任意调用方可伪造"已核验事件" | P2（若同步暴露） | 若选 P2，account 字段必须先只在程序 API/CLI 生效，HTTP `production_api.py` 暴露需独立单开安全 Gate，不随 P2 自动获批 |
| R2 | Schema 一旦冻结，字段语义变更成本高 | P2 | 独立 CONTRACT 阶段冻结字段名/类型/校验失败语义前不得实现 |
| R3 | 影子试跑产物被误用为生产结论 | P3 | 报告目录与命名必须显式标注 `shadow`，且不进入 `reports/` 主目录评分或反馈闭环 |
| R4 | 三选项均不解决"账本谁来维护"的运营问题 | 全部 | 无论选哪个，都需要用户后续明确账本的人工维护流程；本文不裁决该运营问题 |

## 4. Gate 与唯一下一合法动作

**ADMISSION verdict：`PASS`。** 唯一活跃候选是"G9 = as-of 生产 promotion 范围裁决"，其前置条件（G0-G8 冻结、当前生产 schema 事实）已满足且已收敛为三个互斥方案。

**CONTRACT verdict：`AUTHORIZATION_REQUIRED`。** P1/P2/P3 是材料上不同的 public API/schema 及安全暴露面选择，属于业务权衡，不在标准局部授权范围内自动裁决；必须由用户明确选择一项（或提出新方案）后，才能起草可实施的 G9 CONTRACT。

**唯一下一合法动作：** 向用户呈现 P1/P2/P3 三个互斥选项及其风险，取得明确选择；选择确定后，为该选项单独起草 G9 CONTRACT（冻结 exact 签名/字段/write set/STOP 条件），并在该 CONTRACT 获得 fresh independent PASS 后才可进入 IMPLEMENT。

不得推导：本文档不授权任何实现、测试、schema 变更或 API 暴露；不构成 P1/P2/P3 任一方案的 CONTRACT PASS；不改变 G0-G8 已收口结论。

---

## 5. fresh independent read-only 复核记录

- **Reviewer role：** logical fresh reviewer；不采纳作者自检，重新核对第 1–4 节与源文件。
- **审查输入：** 本文件、[`as-of-life-state-reasoning-design-2026-07-18.md`](as-of-life-state-reasoning-design-2026-07-18.md:1) §3.5/§14/§15、[`engine/application/production_service.py`](../engine/application/production_service.py:41)、[`tools/production_api.py`](../tools/production_api.py:37)、[`as-of-life-state-g8-production-integration-report.md`](../reports/as-of-life-state-g8-production-integration-report.md:1)。
- **副作用边界：** 仅本地文档读取与本节写回；未执行 Python、pytest、Git、远端或 GitHub-mutating operation。

### 5.1 Observed facts

1. 核对 [`SubmitAnalysisRequest`](../engine/application/production_service.py:41) 字段集（`input_path`/`render`/`force`/`template_name`/`render_v6_preprod`/`cases_dir`/`reports_dir`/`cases_index_path`），确认无 as-of 相关字段，第 1 节陈述准确。
2. 核对 [`ProductionAPIHandler`](../tools/production_api.py:37) 的 `do_GET`/`do_POST`，未发现任何鉴权头校验或 token 检查，确认第 1 节"无鉴权"陈述准确，且 R1 风险成立。
3. 第 2 节三个选项的写入范围互斥且各自可独立验证：P1 零 schema 改动，P2 唯一新增 schema 字段，P3 零 schema/API 改动。三者不存在可以同时选择而不产生冗余工作的组合，因此"互斥"陈述成立。
4. 非目标列表与 [`reasoning-design`](as-of-life-state-reasoning-design-2026-07-18.md:634) §14 现有非目标（不训练概率模型、不强行生成事件、不平均投票、不无条件跨领域传播）不冲突，且新增的"不扩大无鉴权网络暴露面"是本次新增风险点的合理补充，未见遗漏 §15 架构不变量条款。
5. G8 报告第 172 行已确认生产隔离测试通过，第 5.5 节确认 `engine/asof/` 零 diff；本文档第 1 节的"未接入 production-default"陈述与该证据一致，未发现过时或伪造引用。

### 5.2 Falsifier disposition

- 若 `SubmitAnalysisRequest` 或 `production_api.py` 已存在鉴权/账本字段，则第 1 节陈述及 R1 风险应改判；实际读取未发现该字段，falsifier 未成立。
- 若三个选项存在可合并的第四方案且本文未列出，则"唯一下一动作=用户选择"应改为"先补充第四方案"；本次复核未发现被遗漏的材料不同选项——P1/P2/P3 已覆盖"不改协议/扩协议/延后决定"的完整分支空间。
- 若非目标列表与冻结架构不变量冲突，则本文档 CONTRACT 边界应 REVISE；未发现冲突。

### 5.3 Verdict

**Verdict：`PASS`。** 本文档的事实陈述、三选项互斥性、风险登记与非目标边界在当前授权与只读证据范围内一致、完整、无内部矛盾。`ADMISSION=PASS`、`CONTRACT=AUTHORIZATION_REQUIRED` 的裁决保持不变。

**不得推导：** 本 PASS 不选择 P1/P2/P3 中的任何一项，不授权实现，不改变 production-default，不构成 GitHub 同步声明。

**唯一下一合法动作：** 向用户呈现本文档，取得 P1/P2/P3（或新方案）的明确选择。

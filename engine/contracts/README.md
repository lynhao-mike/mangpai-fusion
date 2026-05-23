# engine/contracts/ · v1.2 双层引擎契约目录

> v1.2 重构的"地基"。所有 agent、所有规律、所有报告必须遵守。
> **W1 阶段（S0 契约设计）的核心交付物。**

---

## 契约清单（10 份）

| 编号 | 文件 | 状态 | 摘要 |
|---|---|---|---|
| 00 | [OVERVIEW](./00-OVERVIEW.md) | ✅ W1.1 已交付 | 架构总览 + 数据流 + 决策摘要 + 8 agent 矩阵 |
| 01 | 01-input-schema.md | ⏳ W1.2 待写 | 命主输入严格 schema（问真 APP 字段映射） |
| 02 | 02-predicate-library.md | ⏳ W1.2 待写 | 60 个 Python 谓词函数签名（共用底层） |
| 03 | 03-findings-schema.md | ⏳ W1.2 待写 | EnergyFindings / PictureFindings / GateResult / SupportFindings JSON Schema |
| 04 | 04-gate-protocol.md | ⏳ W1.3 待写 | 应期三层门接口 + 6 触发判定 |
| 05 | 05-rule-lifecycle.md | ⏳ W1.3 待写 | 规律生命周期状态机 + Beta 算法实现 |
| 06 | 06-confidence-model.md | ⏳ W1.3 待写 | 双轨置信度（★+%）→ Beta 分布的精确公式 |
| 07 | 07-pipeline-flow.md | ⏳ W1.4 待写 | W1-W4 流水线数据流的精确定义 |
| 08 | 08-agent-handoff.md | ⏳ W1.4 待写 | 8 个 agent 的契约边界 + 集成日流程 |
| 09 | [09-naming-convention](./09-naming-convention.md) | ✅ W1.1 已交付 | 文件命名规范 + 旧案重命名清单 |

---

## W1 交付节奏

| 子阶段 | 工作日 | 交付 |
|---|---|---|
| **W1.1** | Day 1（已完成） | 00 + 09 + 本 README → 让架构师/User 审整体方向 |
| **W1.2** | Day 2-3 | 01 + 02 + 03 → 输入/谓词/Findings 定义 |
| **W1.3** | Day 4-5 | 04 + 05 + 06 → 应期/生命周期/置信度算法 |
| **W1.4** | Day 6-7 | 07 + 08 → 流水线 + agent 边界，**冻结契约** |
| **W2 起** | Day 8+ | 8 个 agent 各自分支启动 |

---

## 修改契约的流程

详见 `00-OVERVIEW.md § 十`。

简言之：
1. PR title 前缀 `[CONTRACT]`
2. 必须列出影响的 agent
3. 整合 agent 批准
4. 重大修改（影响 ≥3 agent）暂停作业 1 工作日

---

## v1.2 决策摘要（已锁定）

详见 `00-OVERVIEW.md § 四`。13 项决策（A-M）已全部锁定：

- A 排盘外部化（问真 APP）
- B YAML + Python 谓词
- C 浮点 + 序数双显
- D 引擎产骨架，AI 仅润色画像段
- E Beta 分布置信度
- F 全自动 + G 3 次降级缓冲
- H 各 agent 各分支 + 整合 agent 合并
- I 必须严格优于 v1.0
- J 自动抽取应期到 predictions/
- K 每 10 案跨派扫描
- L 案例命名加干支
- M 优先级保底：E > A > C > G > 其他

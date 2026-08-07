# as-of 真实盲断闭环·持续扩样 R1 增量报告

- 执行日期：2026-07-29
- 执行范围：本地仓库、固定队列、两阶段盲态冻结后揭示
- 状态：**LOCAL ONLY / NOT PUSHED**
- Git / GitHub：本轮未执行任何 Git 或 GitHub 操作

## 一、协议与边界

本轮严格执行以下不可逆顺序：

1. 仅从候选 [`input.md`](../cases/C-2026-RF000190-乾-己卯辛未丁卯丁未/input.md) 读取现实边界前投影。
2. 使用 [`truncate_blind_section()`](../tools/as_of_blind_judgment_probe.py:98) 截断，并使用 [`detect_table_embedded_annotation()`](../tools/as_of_blind_judgment_probe.py:77) 排除表内现实注释。
3. 在反馈封闭状态下完成根气、十二长生、十神透藏、原局承载、大运完成方式、竞争解释和有限现实落点判断。
4. 使用真实 [`freeze_career_draft()`](../engine/asof/consultation_freeze.py:563) 生成冻结包，以 create-only 模式落盘。
5. 从磁盘独立重算 canonical SHA-256，确认摘要一致、窗口不越截止日、`feedback_opened=false` 和拒绝覆盖。
6. 只有上述门禁全部通过后，才读取对应 [`feedback.md`](../cases/C-2026-RF000243-坤-己卯己巳戊午丁巳/feedback.md)。
7. 有效样本使用 [`record_career_verification()`](../engine/asof/consultation_freeze.py:700) 按冻结字符串裁决；无效样本不牵强生成 verified result。

本轮没有修改 [`engine/asof/`](../engine/asof)、[`tools/as_of_blind_judgment_probe.py`](../tools/as_of_blind_judgment_probe.py)、既有案例输入/反馈/索引、历史报告、测试或 [`handoff.md`](../handoff.md)。

## 二、候选库存与纠错

机械枚举口径：`cases/C-2026-RF*`，且目录内同时存在 `input.md` 与 `feedback.md`。

| 项目 | 数量 |
|---|---:|
| RF 目录总数 | 98 |
| 同时具有 input / feedback 的案例 | 98 |
| 历史已触碰、污染、无效或失败尝试排除 | 14 |
| 历史排除后剩余 | 84 |
| 盲态边界审计安全候选 | 84 |
| 盲态边界审计不安全候选 | 0 |

历史排除清单最初遗漏 RF000475。通过 [`as-of-life-state-blind-judgment-first-proof-point-report.md`](as-of-life-state-blind-judgment-first-proof-point-report.md) 的历史证据确认该案已被触碰后，排除数由 13 修正为 14，剩余候选由 85 修正为 84。本轮固定队列据此从 RF000190 开始，随后进入 RF000243。

### 审计词表假阳性

首次修正版现实词扫描将宽泛模板词“反馈”视为泄露，错误产生 84/84 假阳性。为避免输出现实正文，仅用“行号 + 触发词名称”诊断，确认命中来自模板元数据；删除宽泛词后重新审计为 84 个安全候选、0 个不安全候选。

该次运行属于候选审计词表/合同缺口导致的无效运行，不是候选污染，也不是产品行为失败。

## 三、逐案结果

### 3.1 RF000190：窗口内证据不足，无效样本

- 案例：[`C-2026-RF000190-乾-己卯辛未丁卯丁未`](../cases/C-2026-RF000190-乾-己卯辛未丁卯丁未)
- 盲态边界：`yaml_key`，截断行 158，表内注释命中 0
- 截止日：2026-06-11
- 事件窗口：2024-07-14 至 2026-06-11
- 主组合：`STRONG_ROOT + REPAIR_DEFECT`
- 竞争解释：`STRONG_ROOT + ACTIVATE_EXISTING`
- 中心落点：专业/技术型项目交付或标准化专业服务责任增强
- 冻结替代：流程、质量或文档类执行协调职责增强但未形成正式管理职权
- 冻结制品：[`asof-blind-judgment-continuous-r1-frozen-draft.json`](../cases/C-2026-RF000190-乾-己卯辛未丁卯丁未/asof-blind-judgment-continuous-r1-frozen-draft.json)
- 冻结包 SHA-256：`d146a444a39ced18504d6993ca0fd6e14cfb58bc544d86b975ada83a9f0c94b8`

磁盘独立核验确认：canonical 哈希一致、摘要与完整包一致、冻结时反馈封闭、事件窗口未越截止日、create-only 覆盖被拒绝。

揭示后的 [`feedback.md`](../cases/C-2026-RF000190-乾-己卯辛未丁卯丁未/feedback.md)仅记录 2023 年 8 月搜狐游戏运营实习，早于冻结窗口起点 2024-07-14。窗口内没有可评分事业事件，因此本案裁为**无效样本**：保留 frozen draft，不创建 verified result，不进入有效分母，不将其解释为 `REJECTED`。

### 3.2 RF000243：有效样本，REJECTED / MISS

- 案例：[`C-2026-RF000243-坤-己卯己巳戊午丁巳`](../cases/C-2026-RF000243-坤-己卯己巳戊午丁巳)
- 盲态边界：`yaml_key`，截断行 151，表内注释命中 0
- 截止日：2026-06-08
- 事件窗口：2023-06-08 至 2026-06-08
- 主组合：`STRONG_ROOT + ACTIVATE_EXISTING`
- 竞争解释：`STRONG_ROOT + REPAIR_DEFECT`
- 中心落点：专业内容、方案或技术成果的独立输出责任增强
- 冻结替代：运营、项目执行或流程交付职责增强但未形成正式管理职权
- 排除：正式官职跃迁、纯财富跃迁、仅凭学历推断事业命中
- 冻结制品：[`asof-blind-judgment-continuous-r1-frozen-draft.json`](../cases/C-2026-RF000243-坤-己卯己巳戊午丁巳/asof-blind-judgment-continuous-r1-frozen-draft.json)
- 核验制品：[`asof-blind-judgment-continuous-r1-verified-result.json`](../cases/C-2026-RF000243-坤-己卯己巳戊午丁巳/asof-blind-judgment-continuous-r1-verified-result.json)
- 冻结包 SHA-256：`28880985a0f857a4ec3c0b197e69d3672437c1b428a448e2b0461009e49e6b78`

磁盘独立核验确认：canonical 哈希一致、摘要与完整包一致、冻结时反馈封闭、窗口未越截止日、create-only 覆盖被拒绝。

揭示后的 [`feedback.md`](../cases/C-2026-RF000243-坤-己卯己巳戊午丁巳/feedback.md:38)记录：2023 年 6 月离职，在家休养两个月后转去施工单位做文员。这是窗口内可评分事业变动，因此本案有效；但岗位转换本身不等于冻结中心或替代落点要求的“职责增强”，反馈也没有记载专业内容、方案、技术成果、运营项目或流程交付责任增强。

按冻结字符串和弱命中边界，不以同义扩张追认命中。正式 API 裁决为：

- verification verdict：`REJECTED`
- landing verdict：`MISS`
- reason code：`OUTSIDE_FROZEN_LANDINGS`
- decision action：`REJECTED_NO_STATE_BUILD`
- verified event IDs：空

由于结果为 `REJECTED`，未构造影响建议、人工影响裁决或状态构建，避免把未命中的事件写入现实状态账本。

## 四、fresh evidence review

独立终审从磁盘重新读取制品并复算，不复用冻结或正式核验脚本中的内存对象。以下检查全部通过：

- RF000190 冻结包 canonical 哈希一致。
- RF000190 冻结时 `feedback_opened=false`。
- RF000190 窗口不越截止日。
- RF000190 不存在本轮 verified result。
- RF000243 冻结包 canonical 哈希一致。
- RF000243 冻结时 `feedback_opened=false`。
- RF000243 窗口不越截止日。
- RF000243 verified result 引用的冻结哈希一致。
- RF000243 为 `REJECTED / MISS`。
- RF000243 未执行状态构建，verified event IDs 为空。

## 五、技术失败、无效与污染

| 分类 | 数量 | 说明 |
|---|---:|---|
| 技术/无效运行 | 2 | 一次长 `python -c` 退出码为 0 但无可用输出；一次宽泛词“反馈”造成 84/84 候选审计假阳性 |
| 无效案例 | 1 | RF000190 的唯一事业事实早于冻结事件窗口 |
| 有效拒绝案例 | 1 | RF000243，`REJECTED / MISS` |
| 污染案例 | 0 | 两案均在冻结及独立磁盘核验后才首次读取反馈 |

两次技术/无效运行不计为产品行为失败，不进入命中观察分母，也不改变污染计数。

## 六、本轮与累计观察

| 口径 | 有效 N | 命中或部分命中 | 观察比例 |
|---|---:|---:|---:|
| 本轮 | 1 | 0 | 0/1 |
| 继承历史 | 8 | 5 | 5/8 |
| 合并累计 | 9 | 5 | 5/9 |

First Proof Point 不重复加入既有 N5+R2 分母。本表只是固定队列下的小样本观察计数，不是“真实准确率”、不是“引擎准确性”，也不构成“系统有效性证明”。

## 七、直接证明与禁止推断

### 本轮直接证明

1. 两个新案例均能在反馈封闭状态下通过真实 as-of API 构造 create-only 冻结包。
2. 两份冻结包可由磁盘 canonical 投影独立复算得到相同 SHA-256。
3. 无效样本可保持只有 frozen draft，不被牵强核验。
4. 有效但不匹配的事实可由正式 API 稳定裁为 `REJECTED / MISS`，且不进入状态构建。
5. 固定落点与精确匹配边界能够阻止揭示后的同义扩张和追认命中。

### 禁止推断

本轮不能用于推断：

- 总体无偏准确率或生产环境表现；
- 规则、派别或组合的优劣；
- 应调整生产规则、路由权重或置信度；
- 现有生产 pipeline 已成为经过盲测验证的推理系统；
- 5/9 可以外推至随机命盘、其他功能域或未来样本；
- 单个 `REJECTED` 足以证伪整个命理体系或 as-of 架构。

原因包括：样本极小、固定队列、非随机选择、反馈粒度不均、窗口覆盖不完整、事业事实文本可能缺少职责层细节。本轮证据只支持该协议在这些具体制品上的可审计执行结果。

## 八、新增文件与写集

本轮新增并保留：

1. [`RF000190 frozen draft`](../cases/C-2026-RF000190-乾-己卯辛未丁卯丁未/asof-blind-judgment-continuous-r1-frozen-draft.json)
2. [`RF000243 frozen draft`](../cases/C-2026-RF000243-坤-己卯己巳戊午丁巳/asof-blind-judgment-continuous-r1-frozen-draft.json)
3. [`RF000243 verified result`](../cases/C-2026-RF000243-坤-己卯己巳戊午丁巳/asof-blind-judgment-continuous-r1-verified-result.json)
4. [`本增量报告`](as-of-life-state-blind-judgment-continuous-extension-r1-report.md)

本轮临时冻结、磁盘核验、正式核验、库存审计和 fresh evidence review 脚本均已删除。没有修改历史报告、历史合同、案例 input/feedback/index、引擎、探针、测试或 [`handoff.md`](../handoff.md)。

## 九、最终裁决

本轮本地闭环完成：RF000190 为窗口内证据不足的无效样本；RF000243 为有效 `REJECTED / MISS`。本轮新增有效 N=1、命中或部分命中 0；累计有效 N=9、命中或部分命中 5/9；污染计数 0。

**LOCAL ONLY / NOT PUSHED**

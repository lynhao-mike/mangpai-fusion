# 架构方案 · v1.3 · 命理师主导的自迭代闭环

> **状态**：DRAFT，待 review
> **目标版本**：v1.3.0（上一发布候选 v1.2.0）
> **关键词**：过后反馈 · 断语级颗粒度 · 边界自动挖掘 · 案例驱动迭代

---

## 〇、本方案要解决的命理师真实工作流

| # | 命理师约束 | 工程含义 |
|---|---|---|
| 1 | **冷读场景**：拿到八字直接出全面分析，由命理师向命主解释；解释过程中或结束后命主反馈实际情况；过一年半载偶尔回流新事件 | 输出需自带分支假设和强弱标记；反馈采集走"过后回填"流；应期类反馈走独立的延迟通道 |
| 2 | **近 1 个月密集注入案例**：先系统分析 → 命理师反馈 → 充实案例库以驱动迭代 | 必须有批量入库 / 批量复盘吞吐型工作流；迭代节奏跟着案例量走，不按日历 |
| 3 | 命理师本人 CS 本科可动手 | CLI / Python / Markdown 即可，不做 Web UI |
| 4 | **不要**让命理师做规律可靠性论证、边界条件挖掘、新否决条件设计；置信度升降全部由系统自迭代 | 边界发现、否决条件、置信度调整必须**全部由系统从反馈自动挖**；命理师只做"应验/失验/未知"标注 |

> 第 4 条是 v1.3 主要扩建方向。v1.2 已具备规律命中率重算与升降级，但**还没有从反馈自动挖掘边界 / 否决条件**的能力。这是本方案核心新增。

---

## 一、与 v1.2 的关系（保留 / 改造 / 新增 一览）

| 模块 | v1.2 状态 | v1.3 动作 |
|---|---|---|
| `engine/pipeline.py`（D1→D2→D3→D4）| 已落地 | **保留**，不动 |
| `engine/predicates/` `engine/mechanical_rules.py` | 已落地 | **保留** |
| 三层护栏（preflight / output_linter / three_layer_check）| 已落地 | **保留** |
| `tools/render_report.py` | 单版三段式报告 | **改**：双版输出 + 每条断语挂 statement_id |
| `tools/feedback_loop.py` `tools/calibrate.py` | 规律级入口 | **改**：入口改为 statement_id；保留规律级别公式 |
| `cases/_TEMPLATE/feedback.md` | 自由文本 | **改**：报告即反馈表，断语行尾带 `[ ]` 反馈位 |
| `tools/extract_predictions.py` | 封存 ★4+ 应期 | **改**：增加事件签名字段（婚姻/升职/健康事件等） |
| `tools/cross_school_scan.py` `tools/drift_detect.py` `tools/rule_lifecycle.py` | 已落地，独立调用 | **保留**，由迭代报告统一调度 |
| **`tools/feedback_ingest.py`** | 不存在 | **新增**（D5）|
| **`tools/late_feedback.py`** | 不存在 | **新增**（D7） |
| **`tools/boundary_miner.py`** | 不存在 | **新增**（D3，核心）|
| **`tools/veto_miner.py`** | 不存在 | **新增**（D4） |
| **`tools/batch_intake.py`** | 不存在 | **新增**（D6） |
| **`tools/batch_review.py`** | 不存在 | **新增**（D6） |
| **`tools/iteration_report.py`** | 不存在 | **新增**（D8） |
| **`META/iteration-state.json`** | 不存在 | **新增**（D8 计数状态）|
| **`META/iteration-report-NNN.md`** | 不存在 | **新增**（D8 输出，每 10 反馈案触发）|

---

## 二、三大工作流

```
┌────────────────────────────────────────────────────────────────────┐
│ A · 冷读分析（每案触发 1 次）                                       │
│                                                                    │
│ 问真排盘 ──► input.md ──► pipeline ──► render_report               │
│                              │            ├─ master.md（含分支/弱项│
│                              │            │   每条断语挂 statement │
│                              │            │   _id + 行尾 [ ] 反馈位│
│                              │            └─ client.md（精简口语化│
│                              │                                     │
│                              └──► predictions/  自动封存 ★4+ 应期 │
│                                   （含事件签名）                   │
└────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────┐
│ B · 过后反馈（每案触发 0~1 次，命理师事后回填）                     │
│                                                                    │
│ 命理师另存 master.md ──► feedback.md（填 [y]/[n]/[?]/[skip]）      │
│                                │                                   │
│                                ▼                                   │
│              tools/feedback_ingest.py C-XXXX                       │
│                                │                                   │
│                                ├──► feedback_loop  规律命中率重算 │
│                                ├──► 反馈完成计数器 +1              │
│                                └──► 计数 % 10 == 0  → 触发工作流 C │
└────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────┐
│ C · 自迭代（每 10 反馈案自动触发，命理师不参与）                    │
│                                                                    │
│   1. calibrate.py             规律命中率 Beta 重算 + 升降级       │
│   2. boundary_miner.py        ≥5 miss → 自动挖盘面边界            │
│   3. veto_miner.py            ≥5 miss 且边界挖不出 → 自动停用     │
│   4. cross_school_scan.py     跨派一致性扫描                       │
│   5. drift_detect.py          漂移告警                             │
│   6. rule_lifecycle.py        status 自动迁移                     │
│                                │                                   │
│                                ▼                                   │
│   META/iteration-report-NNN.md  ← 命理师唯一需主动看的输出         │
└────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────┐
│ 旁路 · 应期延迟反馈（每年 0~3 次，稀少但价值最高）                  │
│                                                                    │
│ 命主 1+ 年后回流事件 → tools/late_feedback.py C-XXXX --year YYYY   │
│                                  --event marriage --hit yes        │
│   ──► 匹配 predictions/ 内封存预测 (year, event)                  │
│   ──► 应期类规律命中率独立统计（不与画像类混淆）                  │
└────────────────────────────────────────────────────────────────────┘
```

---

## 三、组件图（v1.2 基础上的增量）

```
┌─────────────────────────────────────────────────────────────┐
│ INTAKE 层                                                   │
│  templates/input-from-wenzhen.md                            │
│  tools/preflight.py（已有）                                 │
│  ✚ tools/batch_intake.py（v1.3 新增）                       │
└──────────────┬──────────────────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────────────────┐
│ PIPELINE 层（v1.2 维度引擎，不动）                          │
│  D1 段 → D2 杨 → D3 任 → D4 高                              │
│  predicates / mechanical_rules / arbitration                │
└──────────────┬──────────────────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────────────────┐
│ RENDER 层                                                   │
│  ✚ tools/render_report.py 双版输出 + statement_id 注入      │
│       statement_id = S-{case}-{trace_hash[:6]}              │
│  output_linter + three_layer_check（已有）                  │
└──────────────┬──────────────────────────────────────────────┘
               │
        ┌──────┴──────┐
        ▼             ▼
┌──────────────┐  ┌──────────────────────────────────────────┐
│ predictions/ │  │ FEEDBACK 层                              │
│ ✚ 含事件签名│  │  cases/C-XXXX/feedback.md（报告即表）   │
│              │  │  ✚ tools/feedback_ingest.py             │
│              │  │  feedback_loop.py（规律级重算，已有）    │
└──────┬───────┘  └──────────────┬───────────────────────────┘
       │                         │
       │ ✚ tools/late_feedback   │ 反馈完成计数器 +1
       │    应期到点匹配         │
       └──────────┬──────────────┘
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ SELF-ITERATION 层（每 10 反馈案触发整套）                   │
│                                                             │
│  ✚ tools/iteration_report.py  调度器，依次跑：              │
│      1. calibrate.py（已有）                                │
│      2. ✚ boundary_miner.py（v1.3 核心新增）                │
│      3. ✚ veto_miner.py（v1.3 新增）                        │
│      4. cross_school_scan.py（已有）                        │
│      5. drift_detect.py（已有）                             │
│      6. rule_lifecycle.py（已有）                           │
│                          │                                  │
│                          ▼                                  │
│  META/iteration-report-NNN.md  ← 命理师唯一看的总结         │
│  META/iteration-state.json     ← 计数状态                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 四、决策面板（D1~D8 全部锁定）

> 沿用 v1.2 决策面板风格（参考 `engine/contracts/decisions-locked.md` A-M）。本方案 D1-D8 经评审锁定。

### D1 · 断语级 ID（statement_id）

| 项 | 锁定值 |
|---|---|
| 形式 | `S-{case_id}-{trace_hash[:6]}` |
| 稳定性 | 同一案多次重跑 pipeline 必须保持一致；hash 基于"支撑该断语的规律 ID 集合（排序后）"计算，而非随生成顺序变化 |
| 落地位置 | `tools/render_report.py` 注入；`statement_id → [rule_id...]` 映射写入 `analysis.md` 隐藏区（HTML comment 块） |
| 反馈接入 | feedback 仅按 statement_id 标注；`feedback_ingest.py` 自动 fanout 到所有支撑规律 |

**理由**：颗粒度从规律推到断语，命理师只需对自己讲过的话打勾，不必懂规律编号；trace_hash 保证可重现，避免反馈失锚。

---

### D2 · 双版输出（master / client）

| 项 | 锁定值 |
|---|---|
| master 版 | `reports/C-XXXX-master.md`：保留弱项标记、分支假设、内部置信度数值、备选解释；每条断语行尾 `[ ]` 反馈位 |
| client 版 | `reports/C-XXXX-client.md`：剔除弱项 + 仅保留 ★4+ 主线 + 命理师可裁剪段；不含反馈位 |
| AI polish 边界 | 仅 client 画像段允许 `[AI-polish]`，沿用 v1.2 决策 |
| 落地位置 | `tools/render_report.py` 增 `--variant master|client|both`，默认 both |

**理由**：冷读必有失验，命理师需要看到所有备选支撑分支；命主只需要清晰主线。两份分离避免讲解时互相干扰。

---

### D3 · 边界自动挖掘 boundary_miner（v1.3 核心新增）

| 项 | 锁定值 |
|---|---|
| 触发条件 | 单条规律累计 miss 次数 **≥ 5** |
| 候选特征域 | 现有 predicates 库的全集（合化 / 墓库 / 调候 / 宫位空亡 / 神煞 等结构化布尔特征） |
| 挖掘算法 | 决策树深度 ≤ 3 + 单变量卡方 / 二阶组合；**只用可解释模型**，不上黑盒 |
| 显著阈值 | **p < 0.1 且 lift ≥ 2**，且 miss 集合中富集计数 ≥ 5 |
| 落地动作 | 给原规律追加 `auto_boundary: NOT(predicate)` 字段（写入 `theory/{school}/*.yaml` 的 `auto_boundary` 段，不动原 trigger） |
| 验证 | 加完 boundary 后回放历史所有该规律案例：命中率提升才保留，未提升或下降则自动回退并在日志登记 |
| 命理师参与 | 完全不参与；只在 `META/auto-mined-boundaries.md` 看日志，决定是否合并到 confirmed 字段 |

**理由**：保守阈值（5 miss / p<0.1 / lift≥2）避免边界过拟合；仅用可解释决策树/卡方，命理师 CS 背景能直接看懂、必要时人工 override。

---

### D4 · 候选否决 veto_miner（兜底）

| 项 | 锁定值 |
|---|---|
| 触发条件 | 单条规律累计 miss ≥ 5 **且** boundary_miner 未找到显著边界 |
| 命中率统计 | Beta 后验，要求样本 ≥ 10 才计算；否则保持原状 |
| 自动停用阈值 | 后验均值 < 40% |
| 落地动作 | 自动 `status: candidate → flagged_for_review`，置信度归 0，停止采用 |
| 命理师参与 | 不参与；月度报告列出近期被自动停用的规律清单，命理师可选择复活（也可放任系统管） |

**理由**：边界挖不出且命中率持续偏低 → 规律本身偏弱，应整体停用而非局部修补。

---

### D5 · 过后反馈工作流（"报告即反馈表"）

| 项 | 锁定值 |
|---|---|
| 反馈采集时机 | **过后回填**（解释结束后 / 当晚 / 几天内），不做现场交互式 CLI |
| 反馈载体 | 命理师将 `reports/C-XXXX-master.md` 另存为 `cases/C-XXXX/feedback.md`，把每行末尾的 `[ ]` 填为 `[y]` / `[n]` / `[?]` / `[skip]` |
| 标注语义 | `y`=应验、`n`=失验、`?`=命主当场不知道、`skip`=未讲到/不适用 |
| `?` 处理 | **入库不计数**（既不算 hit 也不算 miss）；保留在 review 视图中等延迟反馈兑现 |
| `skip` 处理 | 入库不计数，不进入 review 队列 |
| 入库工具 | `tools/feedback_ingest.py C-XXXX` 解析填好的文件 → 写结构化反馈 → 触发 feedback_loop |

**理由**：现场交互打勾干扰解说节奏；事后凭印象批量回填更符合真实工作流。

---

### D6 · 批量工作流（吞吐型）

| 项 | 锁定值 |
|---|---|
| `tools/batch_intake.py` | 扫 `cases/inbox/*.md` → 逐案跑 preflight + pipeline + render → 自动建 `cases/C-YYYY-NNN-{干支}/` 目录结构 |
| `tools/batch_review.py` | 扫所有"已有反馈但未跑过 ingest"的案例 → 一条龙跑完 ingest + iteration_report（如达 10 案）→ 输出汇总 diff |
| 单跑入口 | 全部保留，向下兼容 |
| 失败策略 | 单案失败不阻塞批次，错误写入 `META/batch-errors.log` |

**理由**：1 个月内密集注入需要吞吐型工具；保留单跑入口便于调试。

---

### D7 · 应期延迟反馈通道

| 项 | 锁定值 |
|---|---|
| 封存增强 | `tools/extract_predictions.py` 在 ★4+ 应期封存时增加事件签名字段（如 `event: marriage`、`event: promotion`、`event: major_health`），应验窗口默认 ±1 年 |
| 入库工具 | `tools/late_feedback.py C-XXXX --year 2027 --event marriage --hit yes` |
| 匹配规则 | 找到该 case 封存预测里 `(year, event)` 匹配项；窗内 hit 计 1.0、窗外 hit（同 event 但年份偏 1~2 年）计 0.5、整年内未发生计 miss |
| 统计隔离 | 应期类规律的命中率**单独维护**，不与画像类规律统计混淆，避免应期晚验把画像统计带歪 |

**理由**：应期反馈稀少但价值最高；隔离统计避免污染画像规律。

---

### D8 · 自迭代触发：每 10 完成反馈案

| 项 | 锁定值 |
|---|---|
| 触发口径 | **完成反馈的案例数**每 +10 触发一次（不是入库 +10；入库未反馈跑等于空转） |
| 触发位置 | `tools/feedback_ingest.py` 写完反馈后检查计数器；达阈值则调用 `tools/iteration_report.py` |
| 计数状态 | `META/iteration-state.json`，字段：`feedback_completed_count`、`last_iteration_at_count`、`iteration_seq` |
| 输出文件 | `META/iteration-report-{N:03d}.md`，N=`iteration_seq`（如 `iteration-report-002.md` 表示完成第 11~20 反馈案后产出） |
| 报告内容 | 本周期吃进的 10 案 ID 列表 / 升级规律 / 降级规律 / 新挖边界 / 自动停用 / 漂移告警 / 跨派冲突新增 |
| 命理师视角 | 只需扫"漂移告警"段，其他全自动 |

**理由**：迭代节奏跟数据量走，密集注入期会触发多轮迭代；自动调度避免空跑日志污染。

---

## 五、落地路线（贴 1 个月密集注入节奏）

| 周 | 目标 | 命理师做什么 | 系统侧落地 |
|---|---|---|---|
| **W1** | 现场反馈基础设施就绪 | 用现有 v1.2 跑 5~10 案打底 | D1（statement_id）+ D2（双版报告）+ D5（feedback_ingest） |
| **W2** | 密集注入开跑 | 每天 3~5 案，事后回填反馈 | D6（batch_intake / batch_review）+ D7（late_feedback 通道） |
| **W3** | 自迭代上线 | 啥也不做，看迭代报告 | D3（boundary_miner）+ D4（veto_miner） + D8（iteration_report 调度） |
| **W4** | 闭环验证 | 抽 3 案双盲复测，看自动调整后命中率是否真涨 | 回归测试 + 文档归档 |

> 反馈样本 ≥ 30（决策 E 阈值，见 v1.2 决策面板）后，`feedback_loop.py` 自动从线性加权切到 Beta 后验。

---

## 六、验收门槛（v1.3 发布红线）

延续 v1.2 G1-G6 风格，新增 H1-H6：

| 指标 | 限值 | 说明 |
|---|---|---|
| H1 statement_id 稳定性 | 同一 input 重跑 5 次，statement_id 集合完全一致 | D1 落地正确性 |
| H2 双版报告差分校验 | client 版断语数 ≤ master 版；client 版无 ★ ≤3 断语；client 版无弱项标记 | D2 落地正确性 |
| H3 反馈摄入正确率 | 100 条人工标注样本，feedback_ingest 解析正确率 ≥ 99% | D5 落地正确性 |
| H4 边界挖掘可解释性 | 任意 boundary_miner 产出，命理师能在 5 分钟内读懂为什么这么挖 | D3 可解释性 |
| H5 自迭代不退化 | 跑完 D8 整套调度后，G1-G6 6 项 v1.2 指标不能下降 | 不引入回归 |
| H6 完整闭环跑通 | 给 10 案 + 全反馈 → 自动产出 iteration-report-001.md，内容非空且无错误 | 端到端 |

> H1-H6 全部 PASS 才能打 v1.3.0 tag。

---

## 七、风险与回滚

| 风险 | 缓解 |
|---|---|
| boundary_miner 误挖坏边界 → 规律命中率反而下降 | D3 已自带"加完后回放、未提升则自动回退"机制；迭代报告显式登记被回退的 boundary |
| veto_miner 误停用真规律 | flagged_for_review 不删除，命理师可手动 reactive；月报显式列清单 |
| trace_hash 因规律集合变动失效 | 给 trace_hash 加 `engine_version` 前缀，跨版本不复用；旧版本反馈在 ingest 时自动迁移 |
| 批量入库时单案 pipeline 失败被吞掉 | `META/batch-errors.log` 显式登记，CI 检查 log 非空就告警 |
| 自迭代日志膨胀 | 迭代报告 N 进制递增，每 100 个滚一次到 `META/archive/` |

回滚策略：v1.3 全部新增工具都是独立脚本，不动 v1.2 pipeline；如需回滚，删除新增工具 + 还原 render_report.py 即可，pipeline 行为不变。

---

## 八、开放问题（已全部锁定）

| # | 问题 | 锁定值 | 决策位置 |
|---|---|---|---|
| 1 | statement_id 形式 | `S-{case}-{trace_hash[:6]}` | D1 |
| 2 | 反馈 `?` 标注处理 | 入库不计数；review 视图保留 | D5 |
| 3 | boundary_miner 显著阈值 | 保守版：≥ 5 miss + p<0.1 + lift≥2 | D3 |
| 4 | 反馈采集时机 | 过后回填，不做现场交互 | D5 |
| 5 | 自迭代触发口径 | 每 **10 完成反馈案** 触发（非入库 10 案）| D8 |

---

## 九、相关文档

- 历史架构 review：[`plans/architecture-review.md`](./architecture-review.md)
- v1.2 决策面板：`engine/contracts/decisions-locked.md` A-M
- 自迭代基础：`META/calibration-methodology.md`
- 规律生命周期：`engine/contracts/05-rule-lifecycle.md`

---

## 十、签收

- [ ] 命理师 review：决策面板 D1-D8 全部确认
- [ ] 进入 W1 实施

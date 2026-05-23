# mangpai-fusion v1.2 · 双层引擎架构契约总览

> **本文是 v1.2 重构的"宪法"。所有 agent、所有规律、所有报告都必须遵守此文档。**
> 修改本文件需要在 PR 中显式说明，并通知所有运行中的 agent。

最后更新：2026-05-23（W1 · S0 契约设计阶段）
版本：v1.2.0-draft
适用分支：`v1.2-build`

---

## 一、v1.2 架构核心理念

```
┌─────────────────────────────────────────────────────────────┐
│  八字是已存在的事实，任务是解读，不是强加。                 │
│  做功 = 核心。有功有势 = 好命。无功无势 = 平庸。            │
│  应期 = 原局有 + 大运到位 + 流年引爆。三层齐备才下铁口断。  │
└─────────────────────────────────────────────────────────────┘
```

v1.0 把 4 派**平铺**为领域权重矩阵（婚姻/财运/职业…）。
v1.2 把 4 派**立体化**为维度引擎：

| 维度 | 派别 | 回答的问题 | 引擎 |
|---|---|---|---|
| **D1 能量** | 段派（lead）| 这命能转化多大能量（级别）| `energy_evaluator` |
| **D2 画面** | 杨派（lead）| 具体是什么人/什么事（细节）| `picture_matcher` |
| **D3 时间** | 任派（lead）| 什么时候发生（应期）| `yingqi_gate` |
| **D4 旁证** | 高派（lead）| 神煞/健康/灾厄补强（辅助）| `pangzheng_engine` |

D1 是**底层**——D2 必须以 D1 输出为约束；D3 必须以 D1+D2 输出为约束；D4 横向补强。


---

## 二、数据流（W1-W4 流水线）

```
        ┌──────────────────────────────────┐
        │  ① 命主输入（input.md, schema化）│
        │     · 四柱 + 大运 + 神煞（问真APP）│
        │     · 命主代号 + 性别 + 已知信息  │
        └────────────────┬─────────────────┘
                         │
              ┌──────────▼──────────┐
              │  ② preflight.py     │  ← 兜底护栏 #1
              │  schema 校验失败=拒绝│
              └──────────┬──────────┘
                         │ ParsedInput
              ┌──────────▼──────────┐
              │  W1 · D1 能量评估    │  段派
              │  energy_evaluator   │
              │  → EnergyFindings   │  做功结构 + 层数 + 势党 + 体用
              └──────────┬──────────┘
                         │
              ┌──────────▼──────────┐
              │  W2 · D2 画面合拍    │  杨派（消费 D1）
              │  picture_matcher    │
              │  → PictureFindings  │  五步 + 五合 + 暗引 + 财富7等
              └──────────┬──────────┘
                         │
              ┌──────────▼──────────┐
              │  W3 · D3 应期三层门  │  任派（消费 D1+D2）
              │  yingqi_gate        │
              │  → GateResults[]    │  逐年 0/1/2/3 层通过
              └──────────┬──────────┘
                         │
              ┌──────────▼──────────┐
              │  W4 · D4 旁证补强    │  高派（横向旁证）
              │  pangzheng_engine   │
              │  → SupportFindings  │  神煞 + 健康 + 灾厄 + 词馆
              └──────────┬──────────┘
                         │
              ┌──────────▼──────────┐
              │  ③ output_linter.py │  ← 兜底护栏 #2
              │  双轨置信度 / 派别标签│
              │  / 可证伪检查 / 黑名单│
              └──────────┬──────────┘
                         │
              ┌──────────▼──────────┐
              │  ④ render_report.py │  三段式报告骨架
              │  → report.md (skel) │  铁断不可改
              └──────────┬──────────┘
                         │
              ┌──────────▼──────────┐
              │  ⑤ AI 润色（限定段） │  仅画像版/对命主话术
              │  [AI-polish] 标记    │
              └──────────┬──────────┘
                         │
                ┌────────▼────────┐
                │  ⑥ 自动归档      │
                │  + 抽取应期      │
                │  → predictions/  │
                └─────────────────┘
```


---

## 三、自迭代闭环（事件触发，非时间触发）

```
新案归档 → 命主反馈 → feedback_loop.py
              │
              ├─ 解析 应验/失验/部分 标签
              ├─ 顺 trace_id 找到支撑规律
              ├─ 更新 hits/misses/abstained
              ├─ Beta 重算置信度
              │     posterior = (hits+1) / (hits+misses+2)
              │     变异度 > 0.15 → 强制 -1 ★
              │
              ├─ 生命周期判定（全自动 + 3次缓冲）
              │     proposed → candidate → confirmed
              │     confirmed 失验 1 次 = 计数+1（不动 status）
              │     confirmed 失验 3 次 = → flagged_for_review
              │     flagged_for_review → deprecated（仍自动，但需 META 审计登记）
              │
              ├─ 漂移检测（last 5 案滑动窗）
              │     hit_rate < 50% & n≥8 → flagged_for_review
              │
              ├─ 写入 META/iteration-log.md（diff 落盘审计）
              │
              └─ case_count % 10 == 0 → 触发 cross_school_scan
                    → META/conflict-trends.md 生成跨派一致性报告
                    → 必要时调 dimension-weights.yaml（人工 PR）

         紧急回滚开关：engine/calibration.yaml → freeze_iteration: true
```

---

## 四、决策摘要表（已锁定，修改需 PR + Architect 同意）

| ID | 决策 | 选定值 |
|---|---|---|
| A | 排盘+大运+神煞 | 全部外部化，靠问真 APP，input.md 严格 schema |
| B | DSL 形态 | YAML 结构 + Python 谓词函数库（约 60 个原子） |
| C | 做功能量量化 | 浮点 0-1 内部计算，序数 5 级（无/弱/中/强/极强）外显 |
| D | 引擎/AI 边界 | 引擎产骨架结论（铁断不可改），AI 仅润色"画像版/对命主话术"段，标 `[AI-polish]` |
| E | 置信度模型 | Beta 分布：`(hits+1) / (hits+misses+2)`，变异度>0.15 强制 -1 ★ |
| F | 生命周期 | 全自动（升降级都自动），但降级需累计 3 次失验 |
| G | confirmed 降级阈值 | 累计 3 次失验 → flagged_for_review |
| H | agent 协作 | 各 agent 各自分支，最后整合 agent 合并到 v1.2-build |
| I | v1.2 发布门槛 | 旧案回放 + **必须严格优于** v1.0（6 项量化指标见 H 章） |
| J | 预测封存 | 引擎自动从报告 ★★★★+ 应期抽取 → 自动入库 predictions/ |
| K | 跨派扫频率 | 每 10 个案例触发一次（事件驱动，非月频） |
| L | 案例命名 | 含八字干支：`C-2026-001-甲子甲戌癸卯壬戌`（详见 09 契约） |
| M | 优先级保底 | E（兜底）> A（段派）> C（任派）> G（自迭代）> 其他 |


---

## 五、引擎组件清单（v1.2 物理结构）

```
engine/
├── contracts/                    ← 本目录（10 份契约）
│   ├── 00-OVERVIEW.md           ← 本文件（架构总览）
│   ├── 01-input-schema.md       ← 命主输入严格 schema（问真APP格式）
│   ├── 02-predicate-library.md  ← 60 个 Python 谓词函数签名
│   ├── 03-findings-schema.md    ← 4 个 Findings JSON Schema
│   ├── 04-gate-protocol.md      ← 应期三层门接口
│   ├── 05-rule-lifecycle.md     ← 规律生命周期 schema
│   ├── 06-confidence-model.md   ← Beta 分布置信度算法
│   ├── 07-pipeline-flow.md      ← 3+1 流水线数据流详细
│   ├── 08-agent-handoff.md      ← 8 个 agent 的契约边界
│   └── 09-naming-convention.md  ← 文件命名规范（含干支）
│
├── energy/                      ← Track-A 段派 D1 引擎（Python 包）
│   ├── __init__.py
│   ├── evaluator.py             ← evaluate_energy(bazi, dayun) -> EnergyFindings
│   ├── zuogong.py               ← 6 种做功（制/化/生泄/合/墓/复合）
│   ├── tiyong.py                ← 体用判别
│   ├── shidang.py               ← 势与党 12 种组合
│   └── zeishen.py               ← 贼神捕神 + 5 制法力度
│
├── picture/                     ← Track-B 杨派 D2 引擎
│   ├── matcher.py               ← match_picture(energy, bazi) -> PictureFindings
│   ├── wubu.py                  ← 五步算命法
│   ├── wuhe.py                  ← 天干五合（化成/合绊/搅局）
│   ├── anyin.py                 ← 十神暗引 5 公式
│   └── caifu.py                 ← 财富 7 等 + 官命 9 取
│
├── yingqi/                      ← Track-C 任派 D3 引擎
│   ├── gate.py                  ← gate_yingqi(year, energy, picture) -> GateResult
│   ├── chufa.py                 ← 6 触发引擎
│   ├── menshu.py                ← 12 道门
│   └── threelayer.py            ← 三层叠加铁律检查
│
├── pangzheng/                   ← Track-D 高派 D4 旁证引擎
│   ├── support.py               ← support_with_shensha(bazi, findings)
│   ├── shensha.py               ← 神煞旁证
│   └── jibing.py                ← 健康灾厄专项
│
├── predicates/                  ← Track-A/B/C/D 共用 谓词原子库
│   ├── ganzhi.py                ← 干支基础（藏干/合冲刑穿）
│   ├── palace.py                ← 12 宫位判定
│   ├── strength.py              ← 五行强弱
│   └── tools.py                 ← 通用工具
│
├── dimension-weights.yaml       ← 维度权重（替代 v1.0 的 domain-weights）
├── mechanical-rules.yaml        ← 机械铁断 + 黑名单（v1.0 → yaml 升级）
├── confidence.yaml              ← Beta 参数 + 双轨配置（v1.2 升级）
├── calibration.yaml             ← 自迭代开关 + 阈值
└── arbitration.md               ← 仲裁规则（保留 v1.0 文档）
```

---

## 六、工具脚本清单（tools/）

```
tools/
├── preflight.py             ← 兜底护栏 #1：input schema 校验
├── output_linter.py         ← 兜底护栏 #2：输出格式 + 黑名单
├── three_layer_check.py     ← 兜底护栏 #3：应期三层 gate 强制
├── render_report.py         ← 三段式报告渲染器（Findings → Markdown）
├── feedback_loop.py         ← 自迭代主循环（反馈 → Beta 更新）
├── rule_lifecycle.py        ← 规律生命周期状态机
├── drift_detect.py          ← 漂移检测（5 案滑动窗）
├── cross_school_scan.py     ← 每 10 案跨派一致性扫描
├── extract_predictions.py   ← 报告 → predictions/ 自动入库
├── calibrate.py             ← 校准（v1.0 保留）
├── build_indexes.py         ← 索引重建（v1.0 保留）
└── seal_prediction.py       ← 预测封存（v1.0 保留，被 extract_predictions 调用）
```


---

## 七、8 agent 职责矩阵（W2-W4 并行）

| Agent | 专属可写区 | 只读依赖 | 关键交付物 | 验收测试 |
|---|---|---|---|---|
| **A · 段派 D1** | `engine/energy/`<br>`engine/predicates/`（部分）<br>`theory/duan/promoted/` | S0 全部契约 | `evaluate_energy()` + 做功结构量化 | 5 个回归测试通过 |
| **B · 杨派 D2** | `engine/picture/`<br>`theory/yang/promoted/` | S0 + EnergyFindings schema | `match_picture()` + 五步法 + 五合判别 | 4 个回归测试通过 |
| **C · 任派 D3** | `engine/yingqi/`<br>`theory/ren/promoted/` | S0 + Energy/Picture Findings | `gate_yingqi()` 三层判定 + 6 触发 | 5 个回归测试通过 |
| **D · 高派 D4** | `engine/pangzheng/`<br>`theory/gao/promoted/` | S0 + 神煞输入 | `support_with_shensha()` + 健康专项 | 3 个回归测试通过 |
| **E · 兜底护栏** | `tools/preflight.py`<br>`tools/output_linter.py`<br>`tools/three_layer_check.py`<br>`engine/mechanical-rules.yaml` | 全部只读 | 3 个脚本 + 1 yaml + checklist | 8 条铁律的负向测试 |
| **F · 报告渲染** | `templates/report-v1.2.md`<br>`tools/render_report.py` | S0 + A/B/C/D Findings schema | mock findings → sample 报告 | linter 通过 |
| **G · 自迭代** | `tools/feedback_loop.py`<br>`tools/rule_lifecycle.py`<br>`tools/drift_detect.py`<br>`tools/cross_school_scan.py`<br>`engine/calibration.yaml`<br>`META/iteration-log.md`<br>`tools/extract_predictions.py` | 全部只读 + theory/index.yaml 写权限 | 用 C-2026-001/002/014 失验数据回放 | 输出正确 diff 报告 |
| **H · 测试夹具** | `tests/`<br>`tests/fixtures/`<br>`tests/regression_baseline.yaml` | 全部只读 | 14 案 fixture + 6 项量化基准 | pytest 一键跑通 |

---

## 八、v1.2 发布门槛（决策 I 量化）

`tests/regression_baseline.yaml` 必须满足以下 6 项中的至少 5 项：

| 指标 | v1.0 基线 | v1.2 必须 |
|---|---|---|
| 三个真实案例（001/002/014）的核心断语命中率 | 当前命中数据 | ≥ v1.0 + 1 条 |
| 婚期误差（C-2026-001） | 8 年 | ≤ 3 年 |
| 婚姻定性失验数（C-2026-002） | 4 条 | ≤ 1 条 |
| 学历过判档数（C-2026-014） | +1 档 | 0 档 |
| 平均断语 trace_id 覆盖率 | 0%（手写） | 100%（自动） |
| ★★★★★ 断语三层 gate 通过率 | 0%（无 gate） | 100% |

---

## 九、v1.0 → v1.2 迁移路径

| 项 | 处理 |
|---|---|
| `main` 分支 | 冻结，继续服务 v1.0 已交付报告 |
| `v1.2-build` 分支 | 长枝，所有 agent 工作合入此分支 |
| 14 个旧案目录 | **独立"重命名 PR"**先行：加干支，不动内容 |
| v1.0 报告模板 | 保留为 `templates/report-v1.0.md`，新案不再使用 |
| v1.0 domain-weights.yaml | 保留只读，被 dimension-weights.yaml 引用 |
| v1.0 mechanical-rules.md | 升级为 `engine/mechanical-rules.yaml`，原文件归档 `META/legacy/` |
| 14 个旧 analysis.md | 不强制迁移，标 `# v1.0 schema` |

---

## 十、修改本契约的流程

1. 任何对本契约的修改 = PR 到 `v1.2-build`，title 前缀 `[CONTRACT]`
2. PR 必须列出影响的 agent（A-H 哪几个）
3. 必须由整合 agent（架构 agent）批准
4. 合并后所有 agent 必须 pull 最新契约才能继续工作
5. 重大修改（影响 ≥3 个 agent）必须暂停所有 agent 作业 1 个工作日

---

**契约总览结束。下一份请阅读 `09-naming-convention.md`（命名规范，最先落地）。**

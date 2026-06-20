# mangpai-fusion 架构契约总览

> **本文是 v1.2 重构 + v1.3 自迭代闭环的"宪法"。所有 agent、所有规律、所有报告都必须遵守此文档。**
> 修改本文件需要在 PR 中显式说明，并通知所有运行中的 agent。

最后更新：2026-05-29（v1.3.0 已发布 / v1.4 schema 与报告收口）
契约版本：**v1.4.0-schema-current**
代码版本：见仓库根 [`VERSION`](../../VERSION)
适用分支：`main`（v1.2-build 已于 v1.2 发布时合并；v1.3 PR #26-#37 已合 main）

---

## 〇、版本对应表（单一信息源）

> **架构师红线**：每次发版（修改 [`VERSION`](../../VERSION)）必须同步更新此表。**任何文档若与本表冲突，以本表为准**（基准评审 § 七 第 6 条精神）。

| 项 | 值 | 来源 / 说明 |
|---|---|---|
| 当前发布版本 | **v1.3.0** | [`VERSION`](../../VERSION) |
| 当前契约版本 | **v1.4.0-schema-current** | 本文件标头；产品发布版本仍以 [`../../VERSION`](../../VERSION) 为准 |
| 主分支 | `main` | git symbolic-ref refs/remotes/origin/HEAD |
| 主分支 HEAD | `git rev-parse HEAD`（运行时查询，不在文档中硬编码） | 历史教训：handoff.md / STATUS.md 各自硬编码 commit 短 SHA 必然漂移 |
| 已锁定决策 | A-M（v1.2 重构）+ D1-D8（v1.3 自迭代）+ V1-V6 / V8（v1.4 已落地）+ V7（模板存在、默认发布门禁收口）| 见 [`decisions-locked.md`](decisions-locked.md) + [`../../plans/architecture-v1.3.md`](../../plans/architecture-v1.3.md) + [`../../plans/architecture-v1.4.md`](../../plans/architecture-v1.4.md) |
| 下一里程碑 | v1.4 报告默认发布门禁（V7 ViewModel / linter / 快照验收）+ 全量测试收口 | [`../../plans/architecture-v1.4.md`](../../plans/architecture-v1.4.md) § 三 |

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

> **v1.3 D1-D8 状态**：✅ 全部上线（PR #26-#29 + W4 验收 PR #37）。下文是当前生效的实现，不再是规划。

```
新案归档 → 命主反馈（C-2026-025 唯一标准报告对应的 statement_index.json） → tools/feedback_ingest.py
              │
              ├─ D5: 解析 [y]/[n]/[?]/[skip] 四标注，?+skip 入库不计数
              ├─ D1: 顺 statement_id 反查 statement_index.json → 找规律 ID
              ├─ D5: fanout 到 rule_verdicts，决断力优先 (miss > hit > abstain > no_data)
              ├─ V1/V2 跳过门（v1.4 W1 已落地）：
              │     · quantifiable=False     → 框架性心法整体跳过
              │     · domain_restriction 非空且当前 domain 不匹配 → 跳过该规律本次计分
              ├─ feedback_loop._apply_rule_verdicts:
              │     · 更新 hits/misses/abstained + recent_5
              │     · Beta 重算 confidence_cache
              │     · maybe_upgrade / maybe_downgrade / detect_drift
              │     · save_rule
              │
              ├─ D7: 应期延迟反馈（±1 年窗口；半年外 hit=0.5）独立隔离不污染主画像
              │     tools/late_feedback.py
              │
              ├─ 写入 META/iteration-log.md（diff 落盘审计）+ snapshot
              │
              ├─ D6: batch_intake / batch_review（inbox→pipeline / pending→ingest）
              │
              ├─ D3: boundary_miner（≥5 miss + p<0.1 + lift≥2 + 回放 hit_rate 升 → 候选边界）
              ├─ D4: veto_miner（≥5 miss + n≥10 + posterior<40% + boundary 空 → flagged_for_review）
              │
              └─ D8: 完成反馈案数 % 10 == 0 → 自动产出 META/iteration-report-NNN.md
                    异常 warn-only 不阻塞 ingest（命理师不会被 boundary_miner 挂掉拦下）
                    case_count % 10 == 0 触发 cross_school_scan → META/conflict-trends.md

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
| H | agent 协作 | v1.2 期间采用各 agent 分支后整合；当前 `v1.2-build` 已合 main，日常流程以 [`../../AGENTS.md`](../../AGENTS.md) 为准 |
| I | v1.2 发布门槛 | 旧案回放 + **必须严格优于** v1.0（6 项量化指标见 H 章） |
| J | 预测封存 | 引擎自动从报告 ★★★★+ 应期抽取 → 自动入库 predictions/ |
| K | 跨派扫频率 | 每 10 个案例触发一次（事件驱动，非月频） |
| L | 案例命名 | 含性别命式段与八字干支：`C-2026-001-乾-甲子甲戌癸卯壬戌`（详见 09 契约） |
| M | 优先级保底 | E（兜底）> A（段派）> C（任派）> G（自迭代）> 其他 |

### 4.1 v1.3 自迭代闭环锁定项（PR #26 锁定，2026-05-25）

| ID | 决策 | 选定值 | 状态 |
|---|---|---|---|
| D1 | statement_id 公式 | `S-{case_seq}-{sha256(sorted_rule_ids)[:6]}`（排序无关 + 跨案不撞 + 短期可读）| ✅ 已上线 |
| D2 | 唯一标准报告 | 固化 C-2026-025 命理师内部版结构；所有历史用户报告分支均作废，不得作为新案默认入口 | ✅ 已上线 |
| D3 | 边界自动挖掘阈值 | ≥5 miss + p<0.1 + lift≥2 + 回放 hit_rate 升 | ✅ 已上线 |
| D4 | 候选否决兜底 | ≥5 miss + n≥10 + posterior<40% + boundary 空 → flagged_for_review | ✅ 已上线 |
| D5 | 反馈四标注 | `[y]/[n]/[?]/[skip]`，?+skip 入库不计数 | ✅ 已上线 |
| D6 | 批量工作流 | batch_intake (inbox→pipeline) + batch_review (pending→ingest) | ✅ 已上线 |
| D7 | 应期延迟反馈 | ±1 年窗口；半年外 hit=0.5；统计独立隔离不污染主画像 | ✅ 已上线 |
| D8 | 自迭代触发 | 每 10 完成反馈案（非入库）→ 自动产出 iteration-report；异常 warn-only | ✅ 已上线 |

详细设计：[`../../plans/architecture-v1.3.md`](../../plans/architecture-v1.3.md)

### 4.2 v1.4 W1 锁定项（本 PR，2026-05-26）

| ID | 决策 | 选定值 | 状态 |
|---|---|---|---|
| V1 | 规律 yaml 增加 `quantifiable: bool` | 默认 `true`；`false` = 框架性心法（如 M3-R-003 "原局定层次..."），整体跳过 hit/miss 计分 | ✅ 已落地 |
| V2 | 规律 yaml 增加 `domain_restriction: list[str]` | 空 = 所有域；非空 = 仅在列出的域内 ingest 时计 hit/miss（如 M3-R-031 仅 `[应期]`）| ✅ 已落地 |
| V3 | ingest 跳过策略 | quantifiable=False → 整条跳过；domain 不匹配 → 跳过该规律本次计分（domain 为空时不强制，由决断力合并兜底）| ✅ 已落地 |
| V4 | GateResult 增加 `event_type_hypotheses: list[str]` | 默认 `[]`；体制内案例的"财源/置业"应期注入 `["职级升迁", "财源/置业"]` 双解 | ✅ 已落地（types.py + gate.\_infer_event_type_hypotheses）|

V5-V8（PictureFindings.industry_path / wealth_level.framework / 报告耦合提示 / 历史回溯扫描）见 [`../../plans/architecture-v1.4.md`](../../plans/architecture-v1.4.md) § 二，**不在 v1.4 W1 范围内**——它们涉及 03-findings-schema 大动（schema_version 1.2.0 → 1.4.0），独立 PR 处理。


---

## 五、引擎组件清单（v1.2 物理结构）

```
engine/
├── contracts/                    ← 本目录（12 份契约，00-09 为 v1.x 基础契约，10-11 为 v5/taxonomy 扩展契约）
│   ├── 00-OVERVIEW.md           ← 本文件（架构总览）
│   ├── 01-input-schema.md       ← 命主输入严格 schema（问真APP格式）
│   ├── 02-predicate-library.md  ← 60 个 Python 谓词函数签名
│   ├── 03-findings-schema.md    ← 4 个 Findings JSON Schema
│   ├── 04-gate-protocol.md      ← 应期三层门接口
│   ├── 05-rule-lifecycle.md     ← 规律生命周期 schema
│   ├── 06-confidence-model.md   ← Beta 分布置信度算法
│   ├── 07-pipeline-flow.md      ← 3+1 流水线数据流详细
│   ├── 08-agent-handoff.md      ← 8 个 agent 的契约边界
│   ├── 09-naming-convention.md  ← 文件命名规范（含干支）
│   ├── 10-ziping-fusion-v5.md   ← 五派命理推理操作系统契约
│   └── 11-outcome-taxonomy-v1.md ← 可训练 outcome taxonomy 契约
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
│   ├── __init__.py              ← 包入口，re-export support_with_shensha
│   ├── pangzheng.py             ← support_with_shensha(parsed, energy, picture, gate_results)
│   ├── support.py               ← 兼容包装 / 旧调用适配
│   ├── shensha_lib.py           ← 神煞旁证表与查询
│   ├── loader.py                ← 神煞数据加载
│   └── types.py                 ← SupportFindings / HealthFinding / ShenshaSupport
│
├── predicates/                  ← Track-A/B/C/D 共用 谓词原子库
│   ├── __init__.py              ← 统一导出
│   ├── types.py                 ← 共用类型
│   ├── ganzhi.py                ← 干支基础（藏干/合冲刑穿）
│   ├── wuxing.py                ← 五行关系
│   ├── relations.py             ← 合冲刑穿破
│   ├── palace.py                ← 宫位与十神
│   ├── cycles.py                ← 大运流年
│   ├── tou_cang.py              ← 透藏关系
│   ├── strength.py              ← 五行强弱
│   └── shensha.py               ← 神煞辅助查询
│
├── domain-weights.yaml          ← 9 大领域 × 4 派 lead/co/audit 权重矩阵
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
├── output_linter.py         ← 兜底护栏 #2：输出格式 + 黑名单 + W9 跨域 + W10 学制盲区
├── three_layer_check.py     ← 兜底护栏 #3：应期三层 gate 强制
├── render_report.py         ← C-2026-025 唯一标准报告渲染器（命理师内部版；D1+D2）
├── feedback_loop.py         ← v1.0 启发式 + v1.3 _apply_rule_verdicts 共用核心
├── feedback_ingest.py       ← v1.3 D5 结构化反馈入口（[y]/[n]/[?]/[skip]）
├── batch_intake.py          ← v1.3 D6 批量入库（inbox→pipeline）
├── batch_review.py          ← v1.3 D6 批量复盘（pending→ingest）
├── late_feedback.py         ← v1.3 D7 应期延迟反馈（半年外 hit=0.5）
├── boundary_miner.py        ← v1.3 D3 边界自动挖掘
├── veto_miner.py            ← v1.3 D4 候选否决兜底
├── iteration_report.py      ← v1.3 D8 自迭代调度器（每 10 案自动产出报告）
├── rule_lifecycle.py        ← 规律生命周期状态机（含 v1.4 V1/V2 quantifiable + domain_restriction 字段）
├── drift_detect.py          ← 漂移检测（5 案滑动窗）
├── cross_school_scan.py     ← 每 10 案跨派一致性扫描
├── extract_predictions.py   ← 报告 → predictions/ 自动入库
├── timing_report.py         ← 全局 pipeline 耗时聚合（pipeline.PipelineTiming）
├── tool_registry.py         ← 工具注册表生成 / 校验器
├── rule_status_scan.py      ← 规律状态运行时扫描器
├── calibrate.py             ← v1.0 反馈入口（v1.3.0 起 deprecated，含 guard）
└── build_indexes.py         ← 索引重建（v1.0 保留）
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
| **F · 报告渲染** | `templates/report-v1.3.md`<br>`tools/render_report.py` | S0 + A/B/C/D Findings schema | mock findings → C-2026-025 唯一标准 sample 报告 + statements 列表对象映射 | linter 通过 |
| **G · 自迭代** | `tools/feedback_loop.py`<br>`tools/rule_lifecycle.py`<br>`tools/drift_detect.py`<br>`tools/cross_school_scan.py`<br>`engine/calibration.yaml`<br>`META/iteration-log.md`<br>`tools/extract_predictions.py` | 全部只读 + theory/index.yaml 写权限 | 用 C-2026-001-乾-庚申戊寅壬子辛丑/002/014 失验数据回放 | 输出正确 diff 报告 |
| **H · 测试夹具** | `tests/`<br>`tests/fixtures/`<br>`tests/regression_baseline.yaml` | 全部只读 | 14 案 fixture + 6 项量化基准 | pytest 一键跑通 |

---

## 八、发布门槛

### 8.1 v1.2 发布门槛（决策 I 量化，✅ 已达标 — 6/6 PASS，详见 [`../../STATUS.md`](../../STATUS.md)）

`tests/regression_baseline.yaml` 必须满足以下 6 项中的至少 5 项：

| 指标 | v1.0 基线 | v1.2 必须 | v1.2 实测 |
|---|---|---|---|
| G1 三个真实案例（001/002/014）的核心断语命中数 | 5 | ≥ v1.0 + 1 | **7** ✅ |
| G2 婚期误差（C-2026-001-乾-庚申戊寅壬子辛丑） | 8 年 | ≤ 3 年 | **0 年** ✅ |
| G3 婚姻定性失验数（C-2026-002-坤-壬戌庚戌戊辰丙辰） | 4 条 | ≤ 1 条 | **0** ✅ |
| G4 学历过判档数（C-2026-014-乾-丙戌庚子乙亥辛巳） | +1 档 | 0 档 | **0** ✅ |
| G5 平均断语 trace_id 覆盖率 | 0%（手写） | 100%（自动） | **100%** ✅ |
| G6 ★★★★★ 断语三层 gate 通过率 | 0%（无 gate） | 100% | **100%** ✅ |

### 8.2 v1.3 验收门槛（H1-H6，✅ 已达标 — 5/5 PASS）

| 指标 | 含义 | 状态 |
|---|---|---|
| H1 | statement_id 稳定性（同 input 重跑 5 次 sid 一致 + 跨案不撞 + 排序无关）| ✅ tests/v1_3_acceptance/test_h1_*.py |
| H2 | 唯一标准报告校验（C-2026-025 章节、历史 variant 入参收敛、★≤3 过滤、statements 列表映射）| ✅ tests/v1_3_acceptance/test_h2_*.py |
| H3 | 反馈解析正确率 ≥ 99% + ?/skip→no_data + 重复取最后 + fanout 决断力优先 | ✅ tests/v1_3_acceptance/test_h3_*.py |
| H4 | boundary 自挖 | ⚠️ smoke 已覆盖（boundary_miner 自带 `_smoke()`），pytest acceptance 待补 |
| H5 | v1.2 G1-G6 不退化 | ✅ tests/regression/test_v1_2_vs_v1_0.py（H5 即 v1.2 回归门） |
| H6 | 完整闭环调度（10 案触发 + 重复案不重计 + warn-only） | ✅ tests/v1_3_acceptance/test_h6_*.py |

### 8.3 v1.4 W1 验收门槛（H7-H11，本 PR 收编入 pytest）

| 指标 | 含义 | 状态 |
|---|---|---|
| H7 | quantifiable=False 不计分（M3-R-003 ingest miss → hits/misses 不变 + V1 note）| smoke ✅ + pytest 本 PR |
| H8 | domain_restriction 跳过域不匹配（M3-R-031 在"婚姻"域跳过，在"应期"域计 hit）| smoke ✅ + pytest 本 PR |
| H9 | event_type_hypotheses round-trip + 注入逻辑（V4，体制内财源 → 双解）| smoke ✅ + pytest 本 PR |
| H10 | social_clock_check 学制盲区律强制前置（CFL-C014-003）| smoke ✅ + pytest 本 PR |
| H11 | output_linter W10 学制盲区报告级扫描 | smoke ✅ + pytest 本 PR |

---

## 九、v1.0 → v1.2 → v1.3 → v1.4 演进路径

### 9.1 v1.0 → v1.2 迁移（已完成）

| 项 | 处理 |
|---|---|
| `main` 分支 | v1.2 发布时已合并；现为发布分支 |
| `v1.2-build` 分支 | 已合 main，分支删除 |
| 14 个旧案目录 | 已加干支后缀（决策 L）|
| v1.0 报告模板 | 历史报告模板已作废并从当前模板目录删除；新案只允许 `templates/report-v1.3.md` |
| v1.0 domain 权重 | 已收敛到当前 `engine/domain-weights.yaml`，不存在 `dimension-weights.yaml` 事实源 |
| v1.0 mechanical-rules.md | 已升级为 `engine/mechanical-rules.yaml` |
| `tools/calibrate.py` | v1.3.0 起 deprecated（含 guard，详见 `plans/architecture-review-2026-05-26-postrelease.md`）|

### 9.2 v1.2 → v1.3 迁移（已完成）

| 项 | 处理 |
|---|---|
| 报告模板 | `templates/report-v1.3.md` 固化为 C-2026-025 唯一标准命理师内部版；不再按 master/client 分支输出，且默认不生成用户报告 |
| 反馈入口 | `tools/feedback_ingest.py` 新增（结构化路径），`tools/feedback_loop.py` 重构出 `_apply_rule_verdicts` 共用核心 |
| theory yaml schema | 新增 `recent_5` / `misses_at_confirmed` / `misses_at_flagged` / `applied_cases.note` 字段 |
| 案例归档 | `cases/_TEMPLATE/feedback.md` v1.3 模板（报告即反馈表）|
| 反馈完成计数器 | `META/iteration-state.json` 落盘，每 10 案触发 D8 |

### 9.3 v1.3 → v1.4 演进（进行中）

| Track | 内容 | 状态 |
|---|---|---|
| W1 | V1/V2/V3/V4 字段（quantifiable + domain_restriction + GateResult.event_type_hypotheses）+ 文档同步 + H4-H11 入 pytest + STATUS 同步 | ✅ 已落地 |
| W2 / Track 1 | 03-findings-schema 升级（schema_version 1.2.0 → 1.4.0）+ V5/V6 字段（industry_path / wealth_level.framework）| ⏳ 计划 |
| W3 / Track 4 | 跨维度耦合 gate 已进入唯一标准报告/linter 收口；不再保留独立报告模板入口 | ⏳ 计划 |
| Track 5 | 婚姻应期模型（依赖反馈样本 N_eff ≥ 30 切 Beta）| ⏳ 延 v1.5 |

---

## 十、修改本契约的流程

1. 任何对本契约的修改 = PR 到 `main`，title 前缀 `[CONTRACT]`
2. PR 必须列出影响的工作流环节（D1-D8 / V1-V8 哪几个）
3. 必须由架构师 review 批准
4. 合并后所有 agent 必须 pull 最新契约才能继续工作
5. 重大修改（影响 ≥3 个 D/V 项）必须暂停所有 agent 作业 1 个工作日

> **架构师红线**（基准评审 § 七 第 6 条）：版本号 / HEAD / 实测指标 三类信息**只能有一个权威来源**——见本文件 § 〇 单一信息源表。其他文档若需要展示这些值，必须**链接回本表 / [`../../VERSION`](../../VERSION) / 运行时查询**，不得硬编码再次声明。

---

**契约总览结束。下一份请阅读 [`09-naming-convention.md`](09-naming-convention.md)（命名规范）。**

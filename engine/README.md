# engine/ · 核心引擎代码与运行时配置

本目录同时存放五派并行核心、旧四派维度素材、共用谓词库、流水线整合层与运行时配置。目标主流程以 [`v5/`](v5/) 的五派命题、结构图、三段式仲裁与预测账本为方向；当前已落地运行入口仍以 [`application/pipeline_runner.py`](application/pipeline_runner.py) 为 staged fallback / 对照验证入口。根部 [`pipeline.py`](pipeline.py) 若存在仅作历史兼容入口。报告渲染、反馈摄入与生产 API 入口见 [`../tools/README.md`](../tools/README.md)。

## 代码子系统

| 路径 | 职责 |
|---|---|
| [`application/pipeline_runner.py`](application/pipeline_runner.py) | 当前已落地兼容入口；提供 `run_pipeline()` 与 `run_pipeline_e2e()`，用于 staged fallback / 对照验证，不代表长期主流程。 |
| [`application/production_service.py`](application/production_service.py) | 生产 MVP 同步服务封装：任务元数据、缓存、制品清单。 |
| [`pipeline.py`](pipeline.py) | 历史兼容入口；新实现优先使用 `application/pipeline_runner.py`。 |
| [`energy/`](energy/) | 旧 D1 段派素材：能量、做功、体用、贼神捕神；后续挂入盲派综合 runner 内部。 |
| [`picture/`](picture/) | 旧 D2 杨派素材：画像、五步法、财富/官命、婚姻、调候；后续挂入盲派综合 runner 内部。 |
| [`yingqi/`](yingqi/) | 旧 D3 任系素材：三层门、触发器、应期候选；后续作为 timing enhancer。 |
| [`pangzheng/`](pangzheng/) | 旧 D4 高派素材：神煞、健康、旁证补强；后续作为结构旁证与事件反证素材。 |
| [`predicates/`](predicates/) | 共用干支、五行、宫位、关系、强弱等基础谓词。 |
| [`features/`](features/) | L0 共享派生层；从 `ChartFactLedger` 确定性构建版本化 `ChartFeatureVector`，供路由、仲裁与学习层复用。 |
| [`claims/`](claims/) | L2 独立命题层：稳定命题 ID、证据引用校验，以及 `generate_blind_outputs()` / `generate_frozen_claim_run()` 的 Chart→feature→task→freeze 默认评估链。 |
| [`decision/chart_prototype.py`](decision/chart_prototype.py) | L1 命盘原型映射：消费 `cfv-v1` 与外置原型注册表，确定性返回主原型、边界备选与命中条件。 |
| [`decision/capability_registry.py`](decision/capability_registry.py) | L1 能力回流只读边界：加载评估后验快照，执行 exact→prototype→task→domain→global 层级收缩。 |
| [`decision/l1_school_router.py`](decision/l1_school_router.py) | L1 并行路由入口：默认保留 `static`；显式 `learned` 时按能力效用、不确定性与互补增益生成逐任务路由。 |
| [`decision/routing_holdout.py`](decision/routing_holdout.py) | learned/static 留出集对照门禁：强制训练集隔离，并检查效用、校准误差与高风险假阳性。 |
| [`decision/routing_holdout_artifacts.py`](decision/routing_holdout_artifacts.py) | 留出制品治理：按性别+四柱分组确定性切分、用 cfv-v1 重算原型，并审计同案同任务多流派可评分竞争覆盖。 |
| [`decision/l6_staged_arbitration.py`](decision/l6_staged_arbitration.py) | L6 对照入口：消费 L2 Claim 与 L1 权重，执行结构/事件/应期三段裁决、显式对立消解和结构优先级传播；不替换旧生产入口。 |
| [`decision/conflict-rules.yaml`](decision/conflict-rules.yaml) | L6 显式冲突规则集：能力加权、证据完整度与高风险保守兜底。 |
| [`learning/`](learning/) | L9 条件化学习：以六维能力身份治理反馈信号，按 N_eff 分级，生成不可变、可回滚且可被 L1 registry 消费的独立能力快照。 |
| [`contracts/`](contracts/) | 架构契约与跨模块数据交换约定。 |
| [`v5/`](v5/) | ZiPing Fusion Engine v5 并行核心：五派命题、结构图、三段式仲裁、受限概率账本。 |

## 运行时配置

| 文件 | 职责 |
|---|---|
| [`confidence.yaml`](confidence.yaml) | 双轨制置信度计算配置（★ + %）。 |
| [`domain-weights.yaml`](domain-weights.yaml) | 9 大领域 × 4 派 lead/co/audit 权重矩阵。 |
| [`mechanical-rules.yaml`](mechanical-rules.yaml) | 机械铁断 + 黑名单。 |
| [`calibration.yaml`](calibration.yaml) | 旧规则生命周期自迭代开关与阈值。 |
| [`conditional-learning.yaml`](conditional-learning.yaml) | L9 条件化学习的中样本 / 成熟样本门槛、部分反馈权重与单次变化上限；执行器不得硬编码这些阈值。 |
| [`arbitration.md`](arbitration.md) | 派别仲裁规则（冲突裁定 + 联立加权）。 |

L1 learned 路由不会自动读取最新文件或覆盖生产权重；调用方必须显式注入冻结的能力快照与任务列表。L9 也只写独立内容寻址快照，不回灌 `expert-weights.yaml`、`domain-weights.yaml`、生产规则或历史 run snapshot。当前留出证据状态见 [`../reports/l1-routing-holdout-comparison.md`](../reports/l1-routing-holdout-comparison.md)，在门禁达到 GO 前正式入口继续使用 `static`。

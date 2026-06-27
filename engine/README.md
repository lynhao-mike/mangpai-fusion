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
| [`contracts/`](contracts/) | 架构契约与跨模块数据交换约定。 |
| [`v5/`](v5/) | ZiPing Fusion Engine v5 并行核心：五派命题、结构图、三段式仲裁、受限概率账本。 |

## 运行时配置

| 文件 | 职责 |
|---|---|
| [`confidence.yaml`](confidence.yaml) | 双轨制置信度计算配置（★ + %）。 |
| [`domain-weights.yaml`](domain-weights.yaml) | 9 大领域 × 4 派 lead/co/audit 权重矩阵。 |
| [`mechanical-rules.yaml`](mechanical-rules.yaml) | 机械铁断 + 黑名单。 |
| [`calibration.yaml`](calibration.yaml) | 自迭代开关与阈值。 |
| [`arbitration.md`](arbitration.md) | 派别仲裁规则（冲突裁定 + 联立加权）。 |

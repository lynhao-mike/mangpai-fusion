# engine/ · 核心引擎代码与运行时配置

本目录同时存放四派维度引擎代码、共用谓词库、流水线整合层与运行时配置。当前应用层运行入口以 [`application/pipeline_runner.py`](application/pipeline_runner.py) 为准；根部 [`pipeline.py`](pipeline.py) 若存在仅作历史兼容入口。报告渲染、反馈摄入与生产 API 入口见 [`../tools/README.md`](../tools/README.md)。

## 代码子系统

| 路径 | 职责 |
|---|---|
| [`application/pipeline_runner.py`](application/pipeline_runner.py) | 当前 D1-D4 编排入口；提供 `run_pipeline()` 与 `run_pipeline_e2e()`。 |
| [`application/production_service.py`](application/production_service.py) | 生产 MVP 同步服务封装：任务元数据、缓存、制品清单。 |
| [`pipeline.py`](pipeline.py) | 历史兼容入口；新实现优先使用 `application/pipeline_runner.py`。 |
| [`energy/`](energy/) | D1 段派：能量、做功、体用、贼神捕神。 |
| [`picture/`](picture/) | D2 杨派：画像、五步法、财富/官命、婚姻、调候。 |
| [`yingqi/`](yingqi/) | D3 任派：三层门、触发器、应期候选。 |
| [`pangzheng/`](pangzheng/) | D4 高派：神煞、健康、旁证补强。 |
| [`predicates/`](predicates/) | 共用干支、五行、宫位、关系、强弱等基础谓词。 |
| [`contracts/`](contracts/) | 架构契约与跨模块数据交换约定。 |

## 运行时配置

| 文件 | 职责 |
|---|---|
| [`confidence.yaml`](confidence.yaml) | 双轨制置信度计算配置（★ + %）。 |
| [`domain-weights.yaml`](domain-weights.yaml) | 9 大领域 × 4 派 lead/co/audit 权重矩阵。 |
| [`mechanical-rules.yaml`](mechanical-rules.yaml) | 机械铁断 + 黑名单。 |
| [`calibration.yaml`](calibration.yaml) | 自迭代开关与阈值。 |
| [`arbitration.md`](arbitration.md) | 派别仲裁规则（冲突裁定 + 联立加权）。 |

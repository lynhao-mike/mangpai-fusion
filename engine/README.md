# engine/ · 核心引擎规则

本目录存放运行时引擎的**配置规则**（非代码）。

```
engine/
├── confidence.yaml       双轨制置信度计算配置（★+%）
├── domain-weights.yaml   9 大领域 × 4 派 lead/co/audit 权重矩阵
├── mechanical-rules.yaml 机械铁断 + 黑名单
├── calibration.yaml      自迭代开关与阈值
└── arbitration.md        派别仲裁规则（冲突裁定 + 联立加权）
```

运行时入口以 [`engine/pipeline.py`](pipeline.py) 为准；报告渲染与反馈入口见 [`tools/README.md`](../tools/README.md)。

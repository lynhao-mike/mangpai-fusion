# engine/ · 核心引擎规则

本目录存放运行时引擎的**配置规则**（非代码）。

```
engine/
├── confidence.yaml       双轨制置信度计算引擎（★+%）
├── domain-weights.yaml   9 大领域 × 4 派 lead/co/audit 权重矩阵
└── arbitration.md        派别仲裁规则（冲突裁定 + 联立加权）
```

引擎规则被 `.kiro/skills/analyst.md` 主分析器在每次推断时调用。

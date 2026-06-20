# mapping/ · 映射矩阵与 outcome taxonomy

本目录登记跨派规律之间的**关系**，并保存 v5 以后可训练现实结果标签本体的机器可读定义。

```
mapping/
├── consensus.md              底层 · 共识层（4 派全认可铁律）
├── complementary.md          中层 · 互补层（2~3 派同向，路径不同）
├── exclusive.md              上层 · 独门层（单派独有，含历史命中数据）
├── conflicts.md              冲突仲裁登记（多派结论相反）
└── outcome-taxonomy-v1.yaml  v5 · 一级领域 / 二级指标 / L0-L14 / 描述 / 案例映射标签本体
```

## Outcome taxonomy 输出原则

`outcome-taxonomy-v1.yaml` 是报告、反馈、五派推理与仲裁共同引用的现实结果标签事实源；模板不得重新定义训练标签。

```text
一级领域 → 二级指标 → L0-L14 等级 → 展示描述 → 案例映射 / 反馈字段
```

契约语义见 [`../engine/contracts/11-outcome-taxonomy-v1.md`](../engine/contracts/11-outcome-taxonomy-v1.md)。

## 共识金字塔输出原则

```
查询时按层匹配 → 输出按层排序 → 顶层共识优先 → 独门补充末端 → 冲突警告显式
```

详细仲裁规则见 [`../engine/arbitration.md`](../engine/arbitration.md)。

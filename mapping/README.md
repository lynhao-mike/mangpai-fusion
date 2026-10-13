# mapping/ · 映射矩阵、outcome taxonomy 与现实功能卡

本目录登记跨派规律之间的**关系**，并保存现实结果标签本体和现实功能证据卡的机器可读定义。

```
mapping/
├── consensus.md                              底层 · 共识层（4 派全认可铁律）
├── complementary.md                          中层 · 互补层（2~3 派同向，路径不同）
├── exclusive.md                              上层 · 独门层（单派独有，含历史命中数据）
├── conflicts.md                              冲突仲裁登记（多派结论相反）
├── outcome-taxonomy-v1.yaml                  v5 · 现实结果等级标签本体
├── chart-l2-measurement-registry-v1.json     CHART_L2 → 现实测量候选与准入状态
└── real-world-function-evidence-cards-v1.yaml F01–F12 · 现实功能证据卡机器附录
```

## Outcome taxonomy 输出原则

`outcome-taxonomy-v1.yaml` 是报告、反馈、五派推理与仲裁共同引用的现实结果标签事实源；模板不得重新定义训练标签。

```text
一级领域 → 二级指标 → L0-L14 等级 → 展示描述 → 案例映射 / 反馈字段
```

契约语义见 [`../engine/contracts/11-outcome-taxonomy-v1.md`](../engine/contracts/11-outcome-taxonomy-v1.md)。

## 现实功能证据卡原则

`real-world-function-evidence-cards-v1.yaml` 保存 F01–F12 的枚举、字段、冻结卡片数据、竞争关系和出处索引，不承载可执行判定逻辑。契约语义见 [`../engine/contracts/12-real-world-function-evidence-cards-v1.md`](../engine/contracts/12-real-world-function-evidence-cards-v1.md)。

当前文件为安全恢复版：共同纪律与 F12 已恢复，F01–F04 仅保留可核验摘要，F05–F11 原裁决待恢复；不得依据空字段推断规则。

## 共识金字塔输出原则

```
查询时按层匹配 → 输出按层排序 → 顶层共识优先 → 独门补充末端 → 冲突警告显式
```

详细仲裁规则见 [`../engine/arbitration.md`](../engine/arbitration.md)。

## CHART_L2 测量注册表

[`chart-l2-measurement-registry-v1.json`](chart-l2-measurement-registry-v1.json) 只登记命局语义到现实测量对象的候选、审批、冻结和 pilot 准入状态。`UNRESOLVED`、`PROPOSED` 与 `REJECTED` 均不得进入现实评分；当前注册表为 `PROPOSAL_ONLY`。校验入口为 [`../tools/measurement_registry.py`](../tools/measurement_registry.py)。

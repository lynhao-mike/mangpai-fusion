# Kill List 归档裁决 v1（2026-10-29，中枢）

> 对象：`META/kill-list-dependency-audit-v1.json` / `.md`（T-171）
> 结论：**接受审计；先冻结，不批量移动。** 清场不是当前关键路径。

## 0. 一句话

343 个 Kill List 条目里，**真正能立刻搬的只有 130**（117 个脚手架测试 + 9 个引擎叶子 + 4 个工具），
其余被 `engine/facts`、`tests/api` 尺子、`tests/claims`、`tests/governance` 和活代码锁着；
**4 个 `engine/asof` 模块一动就破 481/0**。所以不做「物理删除 85%」，先冻结。

## 1. 已验证

| 项 | 结果 |
|---|---|
| Kill List 条目 | **343**（340 .py + 2 数据 + 1 文档目录） |
| 安全归档 / 有引用 / 尺子 / 不可判 | **194 / 145 / 3 / 1** |
| 首批（真正能搬） | **130**：117 脚手架测试 + 9 引擎叶子 + 4 个 m2y395 工具 |
| 后续批次 | 2a=37、2b=108、2c=64、3=1、保留=3 |
| 一动就破 481/0 | **4**：`engine/asof/{__init__,qiyun_calculator,daiyun_context,natal_capacity}` |
| 硬入口闭包 | facts 22 / api 25 / cli 26 / engine_audit 26 / relations_audit 26 / query_theory 2 |
| 481/0 现场 | engine_audit 481 盘 0 错；relations 全通过 |
| 测试 | 9 passed；全量 **1374 passed / 1 skipped** |
| 确定性 | 两次运行 JSON `28c43cb4…` 一致 |

## 2. 为什么不动

1. **condition_ir 是尺子**：`tests/api/test_facade_zuogong_fields.py:18` 直接 import `atoms`；
   删了不是「清死代码」，是拆尺子。3 个文件必须保留。
2. **asof 4 个是 481/0 的硬耦合**：`engine/facts/chart_facts.py:463` 函数内延迟 import
   `qiyun_calculator`；`--pillars` 不触发，birth/大运路径触发。要归档，先把 `calc_qiyun`
   抽到 `engine/facts`，那是另一张卡，不是归档顺手做。
3. **v5 / claim-rules 被门禁钉住**：`tests/claims` 测 5 个 v5 runner；
   `test_production_entrypoints_unchanged.py:57` 钉 claim-rules sha256；
   `test_project_metadata.py:159-162` 用 `is_file` 断言 4 个 v5 文件。归档=改门禁，必须显式改 pyproject/测试。
4. **117 个测试先不动**：它们大多不在门禁，但「移动测试」会缩小可见范围；
   当前第一优先级是分析能力，不是把仓库变小。
5. **清场不是关键路径**：golden-20 已就绪，下一步是跨派覆盖与事实三原语；
   搬 130 个文件不会让系统多分析一张盘。

## 3. 裁决

1. **冻结**：Kill List 模块不再新增/修改；文档标 `DEPRECATED`（本裁决 + handoff 即可）。
2. **不批量移动**；不删 `condition_ir`、`asof`、`v5`、`claim-rules`、`tests/claims`、`tests/governance`。
3. **若将来清场**：先做 **pilot 13**（9 engine 叶子 + 4 个 m2y395 工具），
   移到 `archive/`、跑全量 pytest + 481/0；不碰测试与硬耦合；另立卡。
4. **跨派覆盖优先**：先补 `yang/ren/ziping` 的 natal-only 集（只测①–③），再谈清场。
5. **事实三原语**（藏干地址、地支克边、冲刑穿方向/救应）另立规格卡；动 `engine/facts` 前先写迁移与回归方案。

## 4. 什么会改变这个裁决

- 人类明确要求「现在就清场」：按 §3.3 的 pilot 13 开工，仍不碰 tests/v5/asof/condition_ir。
- 独立 Agent 复审认为「仓库规模本身是瓶颈」：再评估批量归档，但仍须先解决 asof 抽取与测试钉住。
- golden-20/跨派盲推发现事实层瓶颈：优先修事实，而不是搬文件。

## 5. 证据

- 审计：`META/kill-list-dependency-audit-v1.md`（136KB，逐条 imported_by）
- 工具：`tools/kill_list_dependency_audit.py`；测试 `tests/tools/test_kill_list_dependency_audit.py`（9 passed）
- 卡：`tasks/T-171/PROMPT.md`

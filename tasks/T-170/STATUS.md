# T-170 STATUS

- 状态：✅ **已验收**（2026-10-29 09:10，中枢亲自复跑；接受为 duan-only v1）
- 执行者：子代理 V
- 任务卡：`tasks/T-170/PROMPT.md`
- 简报：`tasks/T-170/BRIEF.md`（Worker 写）
- 验收：中枢亲自看；盲测输入不得含答案

## Execution Log

| 时间 | 动作 |
|---|---|
| 09:20 | 中枢建卡并派发；与 T-171（依赖审计）/T-169（规格）并行，File Scope 无重叠 |
| 09:05 | Worker 交付：`META/golden-20-v1.json`（20 例盲测输入）、`META/golden-20-answers-v1.json`（答案，物理分离）、`META/golden-20-v1.md`、`tests/tools/test_golden_20_schema.py`。四类 6/4/5/5；137 条 source_refs 全逐字命中；`pytest -q` 1365 passed / 1 skipped；engine CLI 抽查 5 例 rc=0 且四柱回读逐字一致。缺口：化用仅 2 例有原书应期（未达 3 例线）、跨派样本 0（全 duan）、18/20 例起运年龄 null。按 T-169 两条实测约束，答案不写裸边号，`struct_refs.status` 全为 `book_text_only`（未作结构绑定，不冒充金标）。 |
| 09:10 | 中枢验收：blind 仅 8 键、无答案泄漏；20/20 有 `chart_snapshot`；`struct_refs` 全 `book_text_only`、edge_ids 空；7 tests；全量 1365/1。裁决：**接受为 duan-only v1**；75/60 只对段派成立；3 例 timing=null 按 fail 计（主门槛 15/20，另报 17 例次级）；跨派主张必须另做 natal-only 集。详见 `docs/reviews/golden-20-coverage-verdict-v1.md`。提交 |

## Blockers

- 无阻塞项。已按 T-169 追加两条实测约束进答案 schema（快照三要素 / candidate 与 edge 双路），
  并写进 `META/golden-20-v1.md` §5.6 与 BRIEF §3.6。

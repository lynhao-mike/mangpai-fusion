# T-156 STATUS

- 状态：✅ **已验收**（2026-10-29 00:14，中枢亲自复跑）
- 执行者：子代理 I
- 任务卡：`tasks/T-156/PROMPT.md`
- 简报：`tasks/T-156/BRIEF.md`（Worker 写）
- 验收：中枢亲自跑；`matched` 零变化
- 执行：Worker 完成 2026-10-28 23:49；中枢验收 00:14

## Execution Log

| 时间 | 动作 |
|---|---|
| 23:40 | 中枢建卡并派发；与 T-157 并行，File Scope 无重叠（本卡只动 YAML 的 counter_conditions） |
| 23:44 | 子代理 I：读完 AGENTS / 本卡 / 10 条规则全文 / `rule_loader.evaluate_rule`；逐条定类 A7 / B3 / C0；删 7 条 A 类 `counter_conditions`（`git diff --stat` = 7 insertions, 14 deletions，无其他 hunk）；v1 干跑产物 SHA256 快照 + 临时备份 |
| 23:45 | 发现卡内冲突：T-152 的 `test_positive_and_counter_overlap_is_triggered_fail_but_still_matched` 拿 MIXED / WEALTH-DEBT 的**生产 YAML** 边界夹具，删反条件后 `matched_counter_conditions=()` → 2 failed；卡 §5「禁改既有测试」与 §6「0 failed」互斥，已上报中枢 |
| 23:46 | 中枢裁决 §9.1：允许解耦（三条原断言保留 + `dataclasses.replace` 钉旧反条件 + `assert production_rule.counter_conditions == ()`）；按裁决执行，`test_rule_contract.py` 8 例 + 新测试全绿 |
| 23:47 | 重跑 `python -m tools.rule_contract_report`（退出码 0，382 例建盘失败 0）→ 复制为 `META/rule-contract-dryrun-v2.{json,md}`（仅加 task/provenance/标题与出处说明，数字未重算）→ 按 SHA256 还原 v1；v1/v2 的 `n_evaluated`/`n_matched`/`n_triggered` 逐条相同，A 类 `n_counter`/`n_suppressed` 全 0（`supp` 641→185） |
| 23:48 | 新建 `META/counter-condition-audit-v1.md`（A7/B3/C0 + 阈值重叠点 + 28 个引用片段逐字校验）与 `tests/claims/test_counter_conditions.py`（38 passed）；核对 YAML diff 仍只有 7 处 |
| 23:49 | 中枢裁决 §9.3：`tests/test_production_entrypoints_unchanged.py` 的 YAML 哈希重新基线（只换哈希 + 一行注释）；全量 `pytest -q` = **1142 passed, 1 skipped, 0 failed**（exit 0）；写 BRIEF |
| 00:10 | 中枢验收：先备份 v1（JSON `E3ED1318…` / MD `A68311AB…`）→ 跑 `rule_contract_report`（v2：A 类 7 条 counter/supp 全 0，B 类 ROLE 307/113、ENTREP 72/72；合计 379/185）→ 用备份**二进制还原** v1，哈希与 HEAD 一致、`git status` 为空 |
| 00:12 | 中枢独立比对 v1/v2：10/10 规则 `n_matched` / `n_triggered` 相同（965/965）；`n_evaluated` 2219/2219；suppression 641→185 |
| 00:13 | 中枢读 diff：YAML 只有 7 处 `counter_conditions`；两条测试改动均为解耦/重新基线，断言未降级；实测 YAML SHA `14d34dea…` 与哈希测试一致 |
| 00:14 | 中枢实跑全量：**1142 passed / 1 skipped / 0 failed**；提交 |

## Blockers / 风险（Worker 记录）

1. **工具硬编码写 v1**：`tools/rule_contract_report.py:52–53` 输出路径写死 `META/rule-contract-dryrun-v1.{json,md}`。
   中枢验收若跑该命令，会用 v2 数字覆盖 v1，§9.2 的「`git diff` 为空」当场失效。还原方法见 BRIEF §3.4
   （`git show HEAD:…` 覆写，不用被禁止的 `restore`/`checkout`；本机另有备份 `%TEMP%\t156_v1_backup\`）。
   工具属只读范围，未自行加 `--out` 参数。
2. **B 类压制面**：3 条 B 类仍有反条件，`n_suppressed_if_flipped` = 185/965（19.2%；v1 66.4%）。
   这是阈值校准问题，需人类另裁；本卡未动 B 类、未改任何阈值。
3. **EMPLOYMENT 的 B 判据出处**：卡面引的「存在有效做功路径」实属 ENTREPRENEURSHIP 的
   `confidence_basis`；本条按旁证判 B（保留），严口径可降 C（动作不变，v2 数字不变）。见审计表 §3.10。
4. **两处既有测试改动**均按中枢书面裁决（§9.1、§9.3），断言强度未降级；`test_counter_conditions.py`
   快照正条件/结论/依据与 A/B 分类，防止后续偷改。

# T-178 STATUS

- 状态：✅ **已验收**（2026-10-29 13:20，中枢；4/4 engine_wrong）
- 执行者：子代理 AB
- 任务卡：`tasks/T-178/PROMPT.md`
- 验收：中枢亲自看；只读规格/审计

## Execution Log

| 时间 | 动作 |
|---|---|
| 13:00 | 中枢建卡并派发；与 T-179（候选修复）并行 |
| 12:55 | 交付（只读审计/规格）：四条墓用 **4/4 `engine_wrong`**、0 `label_wrong`、0 `convention_conflict`——原文力向＝库→入库方（`22:L2274` 墓=得到/控制/拥有/占据、`L2288`「未墓寅」、`L2294`「辰墓了丑」、`L2326`「被辰所控制」、`L2338`「丑也有墓酉之象」；任 `L21`「墓库表示收藏，得到…控制」/`L23` 墓库=制），标注 `a=库、actor=库` 与之一致；引擎墓用候选 `members=(入库方,库)、actor=入库方` 反了（`structure_check.py:498-506`；四条现场 `engine.cli` 复核一致）。故方向主分母 **16 只在冻结时成立、审计后应回 20**（16 降为 sensitivity；四条不改不剔，H14/H16 有 quote 证据缺口、建议补）。规则表 `docs/specs/actor-rules-v1.md` 九类全覆盖（每类 `source_ref`+正例+反例+引擎映射；对称类保持 `null`，墓改 `actor=库`）。`pytest -q`=**1420 passed / 1 skipped / exit 0**；两次运行 JSON 一致（canonical `66a39037…`、file `0ac2c7fe…`）；quote 44/44 逐字（含 22 条 JSON quote）。产物 `META/p1-muku-actor-audit-v1.{json,md}`；未改 answers / hold-out / engine / 规则 / 测试，未跑评分器，无 git 写操作。详见 `BRIEF.md` |
| 13:20 | 中枢验收：4/4 `engine_wrong` 成立；quote 44/44；1420/1；规则表九类。裁决：**方向主分母改回 20**（freeze v2 的 16 作废；16/18 只作敏感性）；冻结 v3；T-179 追加墓用候选翻向（`members=(库,入库方)`、`actor=库`）；评分器注释同步。失败档案 M-08。提交 |

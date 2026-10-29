# T-177 STATUS

- 状态：✅ **已验收**（2026-10-29 12:55，中枢亲自复跑；只读评分）
- 执行者：子代理 AA
- 任务卡：`tasks/T-177/PROMPT.md`
- 验收：中枢亲自跑；只读评分，不改 engine

## Execution Log

| 时间 | 动作 |
|---|---|
| 12:50 | 中枢建卡并派发；独立分支尚无新提交，先用当前引擎出 pre-fix 基线 |
| 12:37（本机时钟；比上一行早，仅照实记） | 子代理 AA 完成：`tools/p1_holdout_eval.py` + `tests/tools/test_p1_holdout_eval.py`（39 passed）+ `META/p1-holdout-baseline-v1.json/.md` + `BRIEF.md`。pre-fix 基线（HEAD `c4c7ea5a`，20 条）：**edge 8/20 (40.0%)、candidate 14/20 (70.0%)、directed 1/20 (5.0%)**；16 例敏感性 6/16、11/16、0/16；muku 等价边召回 12/20（仅敏感性）。两次运行 JSON/MD 逐字节一致；`pytest -q` 1420 passed, 1 skipped, 0 failed。只读评分：engine/规则/测试/hold-out/answers 未动，无 git 写操作。 |
| 12:55 | 中枢验收：39 tests；全量 1420/1；输入哈希与 freeze 一致；基线 `7086c461…`。裁决：口径 v2（关系覆盖=edge or muku；方向主分母剔 4 墓=16）；**三处修复范围不够**——12 条边未中里 8 条是支克/支生（G3）、4 条是墓；需先补 G3 + muku 等价 + 墓 actor 约定，再补三处；不得用 hold-out 调规则。提交 |

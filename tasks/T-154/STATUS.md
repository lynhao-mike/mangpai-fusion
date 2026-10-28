# T-154 STATUS

- 状态：✅ **已验收**（2026-10-28，中枢独立复算 4 组 2×2）
- 执行者：子代理 G
- 任务卡：`tasks/T-154/PROMPT.md`
- 简报：`tasks/T-154/BRIEF.md`（Worker 写）
- 验收：中枢亲自跑；只用 `triggered`，不用 `outcome`

## Execution Log

| 时间 | 动作 |
|---|---|
| 22:55 | 中枢建卡并派发；与 T-155 并行，File Scope 无重叠 |
| 23:05 | Worker 报两个卡面问题，中枢裁决：①敏感性 335→**336**（947 是 unknown，不在 342，不许另挑 1 例）；②判定改两比例检验（triggered vs not-triggered，Newcombe CI + Fisher p），因为单标签规则下 `baseline_single` 退化、accuracy 恒等于基线。写入卡 §7 |
| 23:10 | 子代理 G 完成：新建 `tools/product_claim_eval.py`、`META/eval-protocols/product-marriage-{duan,yang}-v1.yaml`、`META/product-marriage-score-v1.json`、`META/product-marriage-report-v1.md`；342 段派 138 触发（76/138=55.07%）、杨派 204（107/204=52.45%）；两比例检验 342/336 均「无差异 / 样本不足」、未翻转；pytest 1099 passed 1 skipped；两次运行哈希一致；详见 `BRIEF.md` |
| 23:20 | 中枢验收：`product_claim_eval` 连跑两次 `diff_count=0`；最终哈希 JSON `89e1016a…` / MD `b69f044c…` / 工具 `906986ee…` 与 Worker 补充一致。首次哈希不同是 Worker 仍在改产物，不是不确定性 |
| 23:22 | 中枢独立复算 4 组 2×2：触发/未触发负率、差值、Fisher p、Newcombe CI **逐项一致**；全量 `pytest -q` **1099 passed / 1 skipped / 0 failed** |
| 23:24 | 裁决：两规则均「无差异 / 样本不足」，**不晋升**；杨派 `sex truthy` 初判为 bug、**复核后撤回**（规则性别中立，`sex` 门=「性别已知」）；写入 `docs/reviews/product-marriage-verdict-v1.md` |

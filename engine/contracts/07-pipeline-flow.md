# engine/contracts/07-pipeline-flow.md · 流水线数据流

本契约描述当前主干的端到端数据流。报告出口已统一为 C-2026-025 标准：产品 v1.3.0、pipeline/schema v1.4.0、命理师内部版；除非收到明确“用户报告 / 客户报告 / 命主可读报告 / 对外报告”命令，否则不生成用户报告。

## 九、Step render_report

| 项 | 值 |
|---|---|
| 入口 | `tools/render_report.py render_from_output(analysis_output, variant="standard")` |
| 输入 | `AnalysisOutput`（lint 通过后） |
| 输出 | Markdown 报告；固定使用 `templates/report-v1.3.md` 的 C-2026-025 命理师内部版结构 |
| 落盘 | `reports/C-XXX-{乾/坤}-{干支}-analyst-report.md` 与 `cases/C-XXX-{乾/坤}-{干支}/analysis.md` |
| 对象映射 | `cases/C-XXX-{乾/坤}-{干支}/statement_index.json`，顶层 `statements` 为列表 |

标准报告章节：

```text
## 0. 基本盘面
## 一、命局核心结论
## 二、体用、病药与人生主线
## 三、五维定位
## 四、婚恋与家庭
## 五、事业与财富
## 六、关键应期
## 七、健康与生活风险
## 八、行动建议
## 九、总评
## 归档信息
```

历史 `master` / `client` / `v1.2` / `v1.4` 报告版本已作废，不再作为新案入口；`template_name` 与 `variant` 参数仅为兼容旧调用，不允许改变输出结构。

## 十、Step archive + predict

```python
# tools/extract_predictions.py（自动从 ★★★★+ 应期抽取）
for gate_r in analysis_output.gate_results:
    if gate_r.confidence.star >= 4:
        create_prediction_file(gate_r, case_id)
        # → predictions/PRED-YYYY-NNN-CXXXXXXX-{乾/坤}-{干支}-{event}.md
```

同时执行归档：

- `reports/C-XXX-{乾/坤}-{干支}-analyst-report.md` 落盘。
- `cases/C-XXX-{乾/坤}-{干支}/input.md`、`analysis.md`、`feedback.md`、`statement_index.json` 落盘。
- `cases-index.md` 自动追加一行。
- 反馈入口使用 `tools.feedback_ingest`；底层规则回流由 `tools.feedback_loop` 执行。

## 十一、错误处理 & 中断恢复

| 错误发生位置 | 行为 |
|---|---|
| preflight 失败 | 整个流水线不启动，返回错误信息 |
| W1 内部异常 | 写 `cases/C-XXX/findings/energy_error.json`，流水线中断 |
| W2 upstream_hash 不匹配 | 拒绝运行 W2，要求重跑 W1 |
| W3 无任何 passed_layers≥1 的候选 | 输出空 gate_results，报告关键应期段标注暂无高置信应期 |
| output_linter 拒绝 | 流水线中断，不落盘报告；findings 保留以便 debug |

## 十二、性能约束

| 步骤 | 目标时间 | 备注 |
|---|---|---|
| preflight | < 2s | 纯解析 |
| W1 | < 5s | 无外部 IO |
| W2 | < 5s | 无外部 IO |
| W3 | < 10s | 扫描 ~50 年 × ~5 事件 = 250 次 gate |
| W4 | < 3s | 查表 |
| integrate | < 2s | 纯聚合 |
| render | < 2s | 模板渲染 + lint |

# T-197c · P0 第三方重推（只凭 CLI+锚点）

- 状态：🔵 Ready
- 依据：P0 4 卡；6 个事实答案；P0 report
- 前置：`META/p0-cards-v1.json`、`META/p0-report-v1.md`

## 0. 一句话

你是第三方复核者：只读 4 卡、`sources/duan/` 原文、`engine.cli`；**不读答案/评分/其他模型结论**；
逐卡重推方向/状态，判断卡上的 `selected_option`/`state_selected` 是否能由 CLI + 锚点复现。

## 1. 任务

- 4 卡：P0-01 婚、P0-02 事业、P0-03 健康、P0-04 财；
- 对每张卡：核地址/边/十神/引文；按 `anchor_q` 的 `anchor_a` 和 `elimination` 重推；
- 记录：可复现/不可复现、差异、缺证据；
- 不评分、不改卡、不做 git 写；不发明事实。

## 2. 产物

- `META/p0-thirdparty-v1.json`（逐卡：重推结果/差异/证据）
- `tasks/T-197c/BRIEF.md` + `STATUS.md`
- 中枢比较：重推一致率 ≥90% 为 P0 gate 通过；<90% 列差异，不改卡。

## 3. 边界

- 只读 CLI/原文/卡；不读答案、不读评分、不读其他模型结论；
- 不碰 engine/保护区；不做 git 写。

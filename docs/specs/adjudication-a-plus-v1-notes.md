# A+ v1.3 执行口径补记（T-189b/T-190）

> 只补“规格没写死、执行必须先定”的四项；不改 A+ v1.3 的阈值。

## 1. chart 聚类 ≥78% 的口径

- **pass 指标 = macro accuracy（每盘等权）**；A+ v1.3 的 “chart 聚类 ≥78%” 指这个。
- `all_correct_chart_rate`（整盘全对率）只作诊断披露，不单独判 pass/kill。
- 理由：macro 与“每盘一个断言”的产品单元一致；全对率会因每盘 2 条的相关性过度惩罚。

## 2. chart_id / four_pillars / source_refs 的合并

- 评分器/runner 从 `META/p1-anchor-60-blind-v1.json` 按 `case_id` 合并 `chart_id`、`four_pillars`、`gender`；
  答案文件不强制重复这些字段；缺失时以 blind 为准。
- 多行 ambiguous 的 loader 用 `source_refs`（或多个 `source_texts`）；单行 `source_texts` 仍可。
- 若 blind 与 answer 的 `four_pillars` 不一致，直接退出 2，不做静默合并。

## 3. fixed 10 的端点字集

- 当前 anchor-60 的 fixed 10 **全部是地支端点**（未/子、午/酉、戌/亥、亥/卯、巳/辰、卯/巳、子/申、辰/午、未/寅、辰/未）；
  T-189a 的“单地支字”契约够用，**本 anchor 不放宽**。
- 未来 fixed 若出现天干，另开卡扩字集；不在本轮临时放宽。

## 4. margin 与 mutual

- margin = dynamic.correct − max(B1,B2)，两条基线按 dynamic 40 全分母，弃权按不中。
- 3 条 mutual 会被 B1/B2 记为不中，margin **结构性偏高 ≤+3**；报告必须同时给
  `margin_without_mutual = margin − 3`（或按实际 mutual 条数），并在结论里说明。
- 不因 margin 偏高而改阈值；+8 仍是 +8，但读的时候要扣这条解释。

## 5. A/B 双人复核（T-190b）

- fixed 10/10、dynamic 37/40=92.5%、ambiguous 10/10；≥75%，复核通过。
- 3 条 dynamic 分歧：
  - A60-046（未戌刑）：A mutual / B 未→戌；B 原书引文支持单向 → 按 B 修。
  - A60-050（丑戌刑）：A mutual / B 丑→戌；B 原书引文支持单向 → 按 B 修。
  - A60-020（辰戌冲）：A 辰→戌（30/命理瑰宝 L691–695）/ B 戌→辰（26/段建业 L2503）；
    两书冲突，**不能硬当 decidable**；先按 source hierarchy 裁，裁不了移 ambiguous；final 暂不冻。
- 在 A60-020 解决前，不跑 anchor-60、不宣称任何结果。

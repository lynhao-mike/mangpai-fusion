# anchor-60 final v2（2026-10-29）

- A/B 双人复核：fixed 10/10、dynamic 37/40=92.5%、ambiguous 10/10；≥75% 通过。
- 与 A 的修正：
  - **A60-042**：盲卷 target_relation 原标 `mechanism=刑`，原文/engine 为「卯戌合」；B 抓出，v2 盲卷改 **合**，答案用 B（卯→戌，`disputed=true`）。
  - **A60-020**（辰戌冲）：A 辰→戌 / B 戌→辰，两书冲突（30/命理瑰宝 vs 26/段建业）；按段派 source hierarchy 用 B。
  - **A60-046 / A60-050**（未戌刑 / 丑戌刑）：A 默认 mutual，B 按原文判单向（未→戌 / 丑→戌）；用 B。
  - **8 条 gender「未注明」**：B 据原书/同盘补定 7 乾、1 坤（A60-048 坤）；v2 用 B。
- hash：
  - blind：`cc88d10ea15ac68c72bcb82ac1ba982ab177e169e678897bfd6f2010aadb7292`
  - answers：`754caa14f4fcffb36385bebf636eef150ae8f6c967fa539463f42ddde6c189d2`
- v1 `9d4306f1…` 作废（未修 A60-042/8 gender），保留为历史。
- 下一步：T-191 三次未污染盲跑；T-189b 评分；A+ v1.3 判定；3 卡门禁。


> canonical scoring answers (schema/kind/flatten, used by T-191) = 754caa14f4fcffb36385bebf636eef150ae8f6c967fa539463f42ddde6c189d2; pre-schema = 4c6ee69a3a303de5d335af1e4fa20f84f5bf0bf7c9b9f5c9706d0de78902cd53.

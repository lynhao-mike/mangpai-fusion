# T-185 STATUS

- 状态：🟢 交付完成（2026-10-29，含 WB 追加路由例；待中枢验收）
- 执行者：子代理 AI（策展 / 标注人）
- 任务卡：`tasks/T-185/PROMPT.md`
- 简报：`tasks/T-185/BRIEF.md`
- 验收：中枢亲自跑命令；标注/运行分离

## 交付物

| 文件 | 说明 |
|---|---|
| `META/p1-fresh-40-v1.json` | 盲测输入（40 例；只含 case_id / chart_id / 四柱 / 性别 / source） |
| `META/p1-fresh-40-answers-v1.json` | 答案（40 条 relation + 逐字 quote + source_ref + 注） |
| `META/p1-fresh-40-routing-blind-v1.json` | 路由例盲测输入（5 例 needs_judgment，WB 追加） |
| `META/p1-fresh-40-routing-v1.json` | 路由例答案（5 条，`expected_direction="needs_judgment"`） |
| `META/p1-fresh-40-v1.md` | 清单 / 盘数 / 类型 / 非 dev 校验 / sha256 / 缺口 / 路由例（§9） |
| `tests/tools/test_p1_fresh_40_schema.py` | 13 个 schema/分离/非 dev/冻结/路由用例 |

## 规模（以文件为准）

- 主集：40 条 / 37 张不同盘 / 每盘 ≤2 条（3 盘各 2 条）
- mechanism：冲 7 · 合 8 · 穿 6 · 刑 5 · 墓 5 · 克 3 · 生 4 · 化 2（8 类全覆盖）
- kind：制 16 · 合 5 · 墓 5 · 生 4 · 克 3 · 穿 3 · 化 2 · 冲 1 · 刑 1
- 性别：乾 29 / 坤 11；来源 6 本书
- 非 dev：与 `golden-20-v1.json` + `p1-holdout-v1.json` 共 40 例 **四柱 0 重合、source 行 0 重叠**
- 路由例：5 条 / 5 盘（穿制 1 · 合绊 1 · 保护 1 · 制净 1 · Δ=0 1）；与主集/两套 dev 均不同盘；**未用 P1-H02 / P1-H05**；不进主集分母
- 合并盘数：42（主集 37 + 路由 5，≥25 达标）

## 冻结 hash

```
META/p1-fresh-40-v1.json             13790 B  3446c9707e92aa71cbbd60c9e9fb16623f7312e9c4803f5d51c64a78903b6950
META/p1-fresh-40-answers-v1.json     23958 B  478d1a5959016b5c5b1d1f36a9457828ad4a95f7ebe64d2d2a0f252fd0730555
META/p1-fresh-40-routing-blind-v1.json 2033 B  b64f05b79dc5ea2a829d540035bea5b023d66723c9daf77a673f135d6725bf99
META/p1-fresh-40-routing-v1.json       3968 B  d45dcf18a2a0a1a6d3b0a53b9b108f8ab31b1e5a3776dcc9de07f3204b16b504
```

## 门禁

```
python -m pytest -q -o addopts="-ra --tb=short" tests/tools/test_p1_fresh_40_schema.py
13 passed in 0.19s
```

## Blockers

- 无（任务卡未要求凑满 40 条即可交付；实际凑满 40 条 / 37 盘，另附 5 条路由例）。
- 已知口径风险（非阻塞，见 `BRIEF.md` §3）：克/生/化 偏少（3/4/2）；`化` 取「化者＝印」为 a，若按引擎 `sheng` 边方向评分可能判 `reversed`；同盘双条 3 组，建议按 `chart_id` 聚类报分；路由例 `PF-R04` 的 mechanism 记「制」、`PF-R03` 性别「未注明」，均只用于路由统计、不进主集分布。

## Execution Log

| 时间 | 动作 |
|---|---|
| 14:50 | 中枢建卡并派发；与 T-183/T-184 并行 |
| 15:00 | 读任务卡、两套 dev（仅 case_id/四柱/source）、`sources/duan/` 讲义与案例；筛出候选断言池 |
| 15:06 | 逐条回读原文窗口，剔除跨案例/大运/dev 盘误挂的候选（闫锡山例=G20-003、乙未己卯丁丑庚戌=G20-006 等） |
| 15:08 | 生成盲测输入 + 答案，计算 sha256 并写入 MD；补 schema 测试 |
| 15:09 | 门禁 `tests/tools/test_p1_fresh_40_schema.py` 9 passed；写 BRIEF/STATUS |
| 15:14 | 接 WB 追加：另策 5 条 needs_judgment 路由例（穿制/合绊/保护/制净/Δ=0），单独成册，不动已冻结 40 条 |
| 15:16 | 路由例回读原文（19 书 L965/L509、22 书 L1726/L2722、23 书 L483）；修 R03 quote 空格；扩展测试至 13 例 |
| 15:19 | 四份 JSON 的 sha256 写入 MD §0/§9；门禁 13 passed；刷新 BRIEF/STATUS |

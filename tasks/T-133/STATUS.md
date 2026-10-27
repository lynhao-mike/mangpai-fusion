# T-133 · STATUS

- 状态：✅ Done（待中枢验收）
- 优先级：P1（B1 编译前置）
- 执行者：执行子代理（T-133 Worker）
- 更新：2026-10-27
- 产物：`theory/claims/drafts/duan-marriage-anchors.yaml`（16 条锚点记录 / 6 组判据）
- 简报：`tasks/T-133/BRIEF.md`

## 交付结论（六条）

| # | 判据 | status | 锚点数 |
|---|---|---|---|
| 1 | 克者被合绊 | anchored | 4 |
| 2 | 克者无根 | anchored | 2 |
| 3 | 力量相当 | anchored | 4 |
| 4 | 穿中带生不能制 | anchored | 2 |
| 5 | 目标旺透得长生 | **not_found** | 0 |
| 6 | 制净 / 制尽（是否有稳定阈值） | **unmodeled** | 3 |

「制净 / 制尽」查证结论：**原文只有定性用词，无量化阈值**（M1-D-047 明言「未找到净与尽之间稳定的术语分级或数值阈值」）。B1 不得自造阈值。

## 验收（本机实跑）

```
.venv\Scripts\python.exe -m pytest -q
→ 220 passed, 1 skipped          # 与基线一致

git status --porcelain theory/_ir sources
→ （空）                          # 未碰原文语料
```

## Blockers

无硬阻塞。两处**需中枢裁定**（已在 BRIEF §5 写明，未擅自决定）：

1. 「克者无根」与「力量相当」是多锚点**合成**，原文无单句直述。若中枢坚持单句原则，两条应降级 `not_found`。
2. 「目标旺透得长生」标 `not_found` 是我的判断（三部分证据谓词各不相同，拼接即自造判据）。若中枢认为可接受组合式锚点，需另行授权并在 PROMPT 的 Amendments 中说明。

## Execution Log

- 2026-10-27 · 读 PROMPT + pilot-20.yaml，确认字段口径与保护区（`theory/_ir/`、`sources/` 只读）。
- 2026-10-27 · 发现 `--per-school-cap` 默认 2 会截断段派命中，取证统一改用 `--per-school-cap 0`；任务卡原命令仍原样执行并记录。
- 2026-10-27 · 跑 16 条 query_theory 检索（Q01–Q16），收集 72 个 distinct 命中，从中选锚点。
- 2026-10-27 · 用一次性脚本从 CLI 返回 JSON 的 `statement` 逐字切片生成 YAML（脚本内断言 `quote in statement`），避免手抄失真。
- 2026-10-27 · 复核原未被审阅的命中（M1-D-176/194/074/083/085），补 M1-D-194（婚姻域合绊）、M1-D-085（「克尽」措辞）两条。
- 2026-10-27 · 跑验收两条命令，全绿；写 BRIEF.md / STATUS.md。

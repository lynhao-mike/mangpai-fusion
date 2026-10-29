# A+ v1.3 方向产品 · 研究归档

> **DISPOSITION: KILLED** · 2026-10-29 · 任务卡 `tasks/T-192/PROMPT.md`
>
> 本目录封存已 kill 的「A+ 自动方向产品」。它不是可执行规格，不是演示，也不是能力证明。
> 答案/标签/污染清单在 `restricted/`，**runner 不可读**。3 张旧卡在 `../demo/`，只作研究归档。

## 1. 裁决

按 A+ v1.3 §8 预注册死线自动 kill；不调阈值、不重跑同卷、不复活党势。

| 死线 | 实测 | 阈值 |
|---|---:|---:|
| 3 次方向一致率 | **47.5%**（19/40） | ≥90% |
| margin（correct − max(B1,B2)） | **+3** | ≥+8 |
| chart 聚类 macro | **72.5%** | ≥78% |
| ambiguous | **1/10** | ≥7/10 |
| 引文违规 | **18/20** | ≤2/40 |

- fixed 10/10 通过；dynamic 单跑最好 39/40（r2），但 r1/r3 均 29/40，3 次一致仅 19/40。
- 去掉 3 条污染后，57 条独立集上 margin/一致性/引文仍触死线（`t191-a-plus-verdict-v1.md` §3）。
- **保留**：`engine.cli` 事实层（481/0、relations）、固定克/生/化/墓（只作事实）、分流/检索、原文锚点。
- **关停**：自动方向产品（冲/合/穿/刑方向裁决）、阈值调参、党势方向、旧卡当证明。

## 2. 目录

| 路径 | 内容 | 可读性 |
|---|---|---|
| `adjudication-a-plus-v1.md` | A+ v1.3 规格副本；头部 `DISPOSITION: KILLED` | 公开 |
| `t191-a-plus-verdict-v1.md` | T-191 裁决副本 | 公开 |
| `ANCHOR.md` | anchor-60 归档锚点：60 行 case_id/layer/chart_id，3 条标 `contaminated` | 公开 |
| `anchor/` | `p1-anchor-60-blind-final-v2.json`、`p1-anchor-60-final-v2.md`（blind/final v2） | 公开 |
| `t191-runs/` | T-191 r1/r2/r3 三份 runner 输出（预测，不是答案） | 公开 |
| `scorers/` | T-186 `p1_assertion_eval.py`、T-191 所用 `p1_assertion_eval_v2.py` 副本（只归档，主测试未移动） | 公开 |
| `restricted/` | answers（A/B/final v2）、`labels-v1.json`、`contamination-list-v1.json` | **runner 不可读** |
| `../demo/` | 3 张单盘卡原样封存（md + json） | 公开（研究 artifact） |

`t191-runs/` 的 runner 输出含 case 级预测方向与引文；它们是**待评分输出**，不是答案。答案只在 `restricted/`。

## 3. 污染与永久排除

- **A60-020 / A60-046 / A60-050** 在 `ANCHOR.md` 标 `contaminated`。
- 原因：T-192 之前的 `docs/specs/adjudication-a-plus-v1-notes.md` §5 写明了这 3 条的方向与 A/B 分歧，T-191 三份 run 的这 3 条不独立。
- 处置：**永久排除**未来盲集、演示、评分与公开证据；答案详情只在 `restricted/contamination-list-v1.json`，本文件与 `ANCHOR.md` 不复述方向。
- 该污染不改变 kill 结论：去污染后的 57 条独立集仍触死线。

## 4. 读取与出包规则

1. `restricted/` 不得进入任何 runner/Agent 输入包，不得被 runner 读取或引用。
2. 公开文档只能引用本 README/`ANCHOR.md` 的治理信息，不得复述 restricted 里的方向/端点/引文答案。
3. 任何 bundle 交付前必须跑：

   ```powershell
   .venv\Scripts\python.exe -m tools.check_bundle_case_ids <bundle.zip|bundle-dir>
   ```

   退出码 0 才可交付；命中 `A60-/PF-/P1-H/G20` 任一 case_id 即退出 1。
4. 不要对 `archive/` 目录跑上面的扫描：`ANCHOR.md`/README 为了治理**有意**保留 case_id 与 `contaminated` 标记。

## 5. 完整性与已知差异

| 文件 | sha256 |
|---|---|
| `anchor/p1-anchor-60-blind-final-v2.json` | `cc88d10ea15ac68c72bcb82ac1ba982ab177e169e678897bfd6f2010aadb7292` |
| `restricted/p1-anchor-60-answers-final-v2.json` | `754caa14f4fcffb36385bebf636eef150ae8f6c967fa539463f42ddde6c189d2` |
| `adjudication-a-plus-v1.md` | `95b06d41fa130ba63eb5562ebdfe8b37c713f89124f5f8fb91cc4ef85b6c79b3` |
| `t191-a-plus-verdict-v1.md` | `248dd8644703b1cbc926bf398040891f26743c6f83c21ac9b19a471b1bcbdbe8` |
| `../demo/single-chart-cards-v1.md` | `6695e45058eaf3b06f4063cf3a9b067df11ccce2776e42cf3018078ecd8761e7` |
| `../demo/single-chart-cards-v1.json` | `a644b900fd8adc53662a64f90e85fbaa53e26663a96e2dae4e21106556798e65` |

完整清单见 `MANIFEST.sha256`（`sha256sum` 格式）。

**已知 hash 差异（未修，待中枢核）**：

- `anchor/p1-anchor-60-final-v2.md` 记 answers 冻结值 `4c6ee69a…`；
- 归档所取工作区 `META/p1-anchor-60-answers-final-v2.json`（schema `p1-adjudication-answers/v2`，scorer v2 实际读取形状）为 `754caa14…`；
- 仓库 HEAD 版本为旧 schema `p1-anchor-60-answers/v1`，为 `9fd63ada…`。
- T-192 **不改答案、不做合并**；三值原样保留，差异见 `tasks/T-192/BRIEF.md`。归档时工作区该文件已有未提交修改（非 T-192 所为）。

## 6. 3 张旧卡

- `../demo/` 原样封存 T-176 的 3 张卡；原件头部已加 `STATUS: ARCHIVED_RESEARCH_ARTIFACT`。
- 三卡 `direction_known=false` 3/3、`rescue_judged=未判` 3/3；方向产品 kill 后不再作为方向证明，也不进 R-tool 演示。

## 7. 验证

```powershell
.venv\Scripts\python.exe tasks\T-192\verify.py
```

`verify.py` 只依赖标准库：核对本目录清单/哈希、`DISPOSITION`、notes §5 脱敏、demo 状态头、3 条污染标记，并用合成 fixture 验收 `tools/check_bundle_case_ids.py`（不扫真实 bundle）。

## 8. 来源

- `docs/specs/adjudication-a-plus-v1.md`（归档副本已加 `DISPOSITION`）
- `docs/reviews/t191-a-plus-verdict-v1.md`
- `META/p1-anchor-60-blind-final-v2.json` / `p1-anchor-60-answers-final-v2.json` / `p1-anchor-60-final-v2.md`
- `META/p1-system-run-r1.json` / `r2` / `r3`（T-191）
- `tools/p1_assertion_eval.py`（T-186）、`tools/p1_assertion_eval_v2.py`（T-189b/T-191 评分）
- `tasks/T-192/PROMPT.md`

T-192 只做归档/规格/工具，未改 `engine/`、答案、测试、`AGENTS.md`、`report-v7-human.md`；未做 git 写操作。

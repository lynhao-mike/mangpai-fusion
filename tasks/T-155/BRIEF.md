# T-155 BRIEF · M2-Y-395 v2：换「婚姻质量」标签重测方向

- 执行者：子代理 H
- 任务卡：`tasks/T-155/PROMPT.md`（卡内 §1 即预注册，未改一字）
- 结论一句话：**最终判定 = 「样本不足」**（n_scored=43 < 50 硬门槛）。342 与敏感性两套一致，不翻转，所以**不是**「标签不足以裁决」；也没有达到预注册的「否证」条件（Wilson 上界未低于基线）。

---

## 1. 改动文件

**新建（仅此 7 个，无一处改动既有文件）**

| 文件 | 作用 |
|---|---|
| `tools/m2y395_real_direction.py` | 方向重建：382 例建盘 → 日支 `D.b` 冲边 → 按人聚合方向；**不读标签**（grep `negative|label|marriage-quality` = 0 命中） |
| `tools/m2y395_real_score.py` | 并入 T-153 标签 → `answer_letter`（negative→N, positive→P）→ 跑 `engine.claims.metrics.score`，342 / 敏感性两套；生成 scored.json 与 report.md |
| `META/eval-protocols/m2y395-v2.yaml` | 预注册 11 字段（protocol_id / claim_id / frozen_at / commit / trigger_definition / direction_rule / label_map / prediction_rule / scored_set_rule / baseline / decision_rule） |
| `META/m2y395-v2-cases.json` | 382 例方向（`case_id`、`pillars`、`day_branch`、`edges`、`direction`、`prediction_letters`、`triggered`） |
| `META/m2y395-v2-scored.json` | 342 例计分（+`answer_letter`、`label`、`branch`、`claim_id`、`outcome`） |
| `META/m2y395-v2-report.md` | 报告：预注册、触发率、两套敏感性、判定、风险 |
| `tasks/T-155/BRIEF.md` | 本文件 |

**读取但未改**：`tools/m2y395_direction.py`（只 `import direction_of`）、`engine/**`、`META/timing-eval-set-v1.json`、`META/marriage-quality-labels-v1.json`、`tasks/T-153/PROMPT.md` §9（只取 7 例名单）。

`git status --porcelain` 里属于本卡的只有上面这些；`M tasks/T-153/PROMPT.md`、`tasks/T-154/*`、`META/product-*`、`tools/product_claim_eval.py` 是中枢/并行 Worker 的改动，与 T-155 无关。

方向逻辑**未复制第二份**：`direction_of` 直接从 `tools/m2y395_direction.py:124-130` import，`KE_MAP` / `ZHI_TO_WUXING` 从 `engine/predicates/types.py:60-79` import。

---

## 2. 原始输出

### 2.1 四条验收命令（全部 EXIT=0）

```text
$ .venv\Scripts\python.exe -m tools.m2y395_real_direction
==========================================================================
T-155 · M2-Y-395 v2 方向重建（不读标签）
==========================================================================
可评测案例        : 382
建盘成功 / 失败    : 382 / 0
日支有冲（人数）    : 67（触发率 17.54%）
  self_controls   : 20
  other_controls  : 28
  no_ke           : 19
  ambiguous       : 0
  no_chong        : 315
歧义拆分          : 正反相冲 0 / 含 no_ke 混合 0
跳过的异常冲边    : 0
--------------------------------------------------------------------------
产物              : META\m2y395-v2-cases.json
EXIT=0
```

```text
$ .venv\Scripts\python.exe -m tools.m2y395_real_score
--------------------------------------------------------------------------
【1】342 例全集（label ∈ negative/positive）
--------------------------------------------------------------------------
  n_total=342  n_triggered=60  n_scored=43  n_correct=23
  n_abstain=17（no_ke=17 / ambiguous=0）  n_not_triggered=282
  方向人数  : self=20  other=23  no_ke=17  ambiguous=0
  计入 scored: self=20  other=23
  accuracy=0.5349  baseline_single(N)=0.5814  baseline_same_k=0.5814（乐观参考）
  wilson_ci_95=[0.3892, 0.6749]
  by_branch no_chong: 0/0 = n/a
  by_branch no_ke: 0/0 = n/a
  by_branch other_controls: 14/23 = 0.6087
  by_branch self_controls: 9/20 = 0.4500
--------------------------------------------------------------------------
【2】敏感性集（342 − 名单命中 6 例 = 336；卡内写 335）
--------------------------------------------------------------------------
  n_total=336  n_triggered=60  n_scored=43  n_correct=23
  n_abstain=17（no_ke=17 / ambiguous=0）  n_not_triggered=276
  方向人数  : self=20  other=23  no_ke=17  ambiguous=0
  计入 scored: self=20  other=23
  accuracy=0.5349  baseline_single(N)=0.5814  baseline_same_k=0.5814（乐观参考）
  wilson_ci_95=[0.3892, 0.6749]
  by_branch no_chong: 0/0 = n/a
  by_branch no_ke: 0/0 = n/a
  by_branch other_controls: 14/23 = 0.6087
  by_branch self_controls: 9/20 = 0.4500
--------------------------------------------------------------------------
342 全集判定  : 样本不足（n_scored=43 < 50（硬门槛，不看区间））
敏感性集判定  : 样本不足（n_scored=43 < 50（硬门槛，不看区间））
最终判定      : 样本不足
--------------------------------------------------------------------------
产物          : META\m2y395-v2-scored.json
报告          : META\m2y395-v2-report.md
EXIT=0
```

```text
$ .venv\Scripts\python.exe -m tools.claim_metric --protocol META/eval-protocols/m2y395-v2.yaml --cases META/m2y395-v2-scored.json
[claim_metric] protocol=m2y395-v2 claim=M2-Y-395
  n_total=342  n_scored=43  n_correct=23  n_abstain=17  n_not_triggered=282  n_missing_answer=0
  accuracy=0.5349  baseline_single(N)=0.5814  baseline_same_k=0.5814（乐观上界，只作参考）  wilson_ci_95=[0.3892, 0.6749]
  by_branch no_chong: 0/0 = n/a
  by_branch no_ke: 0/0 = n/a
  by_branch other_controls: 14/23 = 0.6087
  by_branch self_controls: 9/20 = 0.4500
  input_sha256=461863bd219f5c40099769964c9c084903732e6a8d9e0fa29bc46917e395deca
EXIT=0
```

```text
$ .venv\Scripts\python.exe -m pytest -q
SKIPPED [1] tests\tools\test_bundle_pii.py:34: 本地脱敏脚本缺失 … （T-114 已知 skip）
1099 passed, 1 skipped, 1 warning in 97.73s (0:01:37)
EXIT=0
```

### 2.2 两套敏感性表（同一 `score()` 实现，与 `tools.claim_metric` 同源）

| 指标 | 342 全集 | 敏感性集（336） |
|---|---:|---:|
| n_total | 342 | 336 |
| n_triggered | 60 | 60 |
| n_scored | 43 | 43 |
| n_correct | 23 | 23 |
| n_abstain（no_ke/ambiguous） | 17（17/0） | 17（17/0） |
| n_not_triggered | 282 | 276 |
| n_self（触发人数） | 20 | 20 |
| n_other（触发人数） | 23 | 23 |
| n_no_ke | 17 | 17 |
| n_ambiguous | 0 | 0 |
| accuracy | 0.5349 | 0.5349 |
| baseline_single | N / 0.5814 | N / 0.5814 |
| baseline_same_k（乐观参考） | 0.5814 | 0.5814 |
| wilson_ci_95 | [0.3892, 0.6749] | [0.3892, 0.6749] |
| 判定 | 样本不足 | 样本不足 |

### 2.3 抽查 3 人（中枢可逐项复核）

| case_id | 四柱 | 日支 | 冲边 | 对方 | 方向 | 预测 | 标签 | 命中 |
|---|---|---|---|---|---|---|---|---|
| RF-2026-000130 | 丙寅 己亥 甲申 乙丑 | 申（金） | `e010` | 寅（木） | KE_MAP[金]=木 → self_controls | P | negative | ✗ |
| RF-2026-000081 | 壬申 壬子 壬午 辛丑 | 午（火） | `e008` | 子（水） | KE_MAP[水]=火 → other_controls | N | negative | ✓ |
| RF-2026-000034 | 甲子 庚午 戊戌 丙辰 | 戌（土） | `e011` | 辰（土） | 同五行 → no_ke（弃权） | [] | unknown（不在 342） | — |

### 2.4 确定性

两次独立运行：`m2y395-v2-cases.json` / `m2y395-v2-scored.json` / `m2y395-v2-report.md` 的 SHA-256 逐次一致（无时间戳、无随机数）。scored 的 `input_sha256` = `461863bd…`（342）/ `02477ab8…`（336）。

---

## 3. 未完成与风险

1. **卡内数字与现场不符：335 → 实际 336（**需要中枢裁决**）**
   - 卡 §1.1 写「剔除 T-153 §9 的 7 例 → 335」。但 §9 名单里的 `RF-2026-000947` 在冻结标签中是 `unknown`（`unknown_reason=neutral`），本就不在 342 分母里。
   - 按名单剔除，342 里实际只命中 **6** 例 → **336**，不是 335。要凑 335 就得再挑一例不在名单里的标签样本，那违反「不许按标签挑案例」，所以**没有凑**。
   - 已按「名单优先」执行并把差异写进 `META/m2y395-v2-report.md` §4 与 `STATUS.md` Blockers。**请中枢在卡内 Amendments 说明以 336 为准，或给出第 8 例的具体 case_id。**
2. **敏感性集对计分毫无影响**：名单命中的 6 例全部 `triggered=false`（均无日支冲），所以两套的 n_scored / accuracy / Wilson **完全相同**。这不是我算错，是名单性质决定的——它证明「判定不依赖这 6 例」，但**不能**用来检验 scored 集内的标签噪声。
3. **触发率低**：按人计 67/382 = 17.54%；落到 342 标签集只剩 60 人触发（self 20 / other 23 / no_ke 17）。即使不设 50 门槛，这个量级也不足以支撑任何宣称。
4. **点估计低于基线（记录，不改判定）**：accuracy 0.5349 < baseline_single（N）0.5814；self_controls 分支 9/20=0.4500，低于「无脑猜 N」。但预注册的「否证」要求 Wilson **上界** < 基线，实际 0.6749 > 0.5814，故按 §1.4 只能判「样本不足」，**不得**自行升级成「否证」。
5. **建盘失败 0 例**；`skipped_edges` 0 条；`ambiguous` 0 人（只有 2 人有 2 条冲边，且各自同向，按人聚合后方向不变）。
6. **标签噪声来自上游**：T-153 是关键词/极性标签，另有 `RF-2026-000066`（positive 实为「找到对象」）、`RF-2026-000704`（negative 实为抑郁文本）等已知上游噪声；本报告不修标签、不折 unknown。
7. **未做**（卡外，不扩范围）：不建四态、不接产品、不动 T-151/T-153/T-148 产物、不 commit。

---

## 4. 下游须知

- **最终判定词 = 「样本不足」**（四选一里唯一合法的那个）。342 与敏感性两套一致 → **不触发**「标签不足以裁决」；同时**没有**达到「否证」的预注册条件，所以也**不能**写成「否证」。
- 对 T-151 那个问题的回答（供中枢写结论，不是本卡的判定词）：**这次重测既没有把方向救活，也没有把它钉死**。换标签后 scored 集只有 43 例、Wilson 区间 [0.3892, 0.6749] 横跨基线，点估计还低于基线——没有任何「上次否定是标签伪影」的迹象，但样本量不足以把「假设错」写成结论。
- 口径变更提醒：**计数单位从 T-151 的「一条冲边一例」改成「一个人一例」**，两份报告的数字不可直接对比 accuracy，只能对比「方向是否被否证」这个判断。
- 复跑顺序固定：`tools.m2y395_real_direction` → `tools.m2y395_real_score` → `tools.claim_metric`；score 会重写 scored.json 与 report.md，且逐字节确定。
- 标签文件与评测集都是冻结产物，本卡只读；若要求 335，需要中枢先修卡（见 §3.1），不要直接改 `tools/m2y395_real_score.py` 的 `SENSITIVITY_EXCLUDE` 名单以外的东西。

# T-177 BRIEF · P1 hold-out 评分器 + 当前引擎 pre-fix 基线（只读）

- 仓库 HEAD：`c4c7ea5a`（跑基线时的 HEAD；`META/p1-holdout-freeze-v1.json` 记的 `git_head` 是 `17095645`，为冻结时点）
- 执行：子代理 AA；只读评分，**未改** engine / 规则 / 测试 / hold-out / answers，无 git 写操作
- 性质：**pre-fix 基线**（当前引擎）。三处修复落地后须整体重跑对比，本表数字不得当修复后结果引用

## 1. 改动文件

新建：

| 文件 | 作用 |
|---|---|
| `tools/p1_holdout_eval.py` | 评分器（CLI `--holdout --answers [--json]`，默认写 `META/p1-holdout-baseline-v1.json` / `.md`） |
| `tests/tools/test_p1_holdout_eval.py` | 39 个合成 fixture 测试（不读真实答案做断言） |
| `META/p1-holdout-baseline-v1.json` | pre-fix 基线（机器可读，逐例 + 分子/分母 + 口径） |
| `META/p1-holdout-baseline-v1.md` | 同上人读版（含 kind 映射表与风险） |
| `tasks/T-177/BRIEF.md` | 本文件 |
| `tasks/T-177/STATUS.md` | 仅追加 Execution Log 一行 |

`git status --short` 复核：只多出上表 5 个新文件（+ 仓库原有的 `mangpai-fusion-offline-04677d2c.zip` 未跟踪文件，非本次产物）；engine/、tests 既有文件、`META/p1-holdout-*.json`、sources/ 全部未动。

输入完整性（与 freeze 对齐）：

```text
holdout sha256 593f4dbea76a4959550c326eea31a8d9feae895cb9272028813982de96bbf045  ← freeze 同值
answers sha256 b1075a394dc1954f27e7de1b06b38283174223e223e3d6b17993723bef37762f  ← freeze 同值
```

## 2. 原始输出

### 2.1 基线（主命令）

```text
> .venv\Scripts\python.exe -m tools.p1_holdout_eval --holdout META/p1-holdout-v1.json --answers META/p1-holdout-answers-v1.json
P1 hold-out pre-fix 基线（20 条）：edge 8/20 (40.0%) · candidate 14/20 (70.0%) · directed 1/20 (5.0%)
方向分布：{'actor_none': 6, 'no_candidate': 1, 'no_edge': 5, 'ok': 1, 'reversed': 7}
写盘：E:\Git hub\mangpai-fusion\META\p1-holdout-baseline-v1.json；E:\Git hub\mangpai-fusion\META\p1-holdout-baseline-v1.md
```

### 2.2 主口径 20 条

| 指标 | 分子/分母 | 百分比 |
|---|---|---|
| 边召回 `edge_recall` | **8/20** | **40.0%** |
| 候选召回 `candidate_recall` | **14/20** | **70.0%** |
| 方向召回 `directed_recall` | **1/20** | **5.0%** |
| 评到 | 20/20 | — |
| 方向分母（actor 非空） | 20 | — |

方向分布：`ok` 1（H17）· `reversed` 7（H09/H10/H11/H14/H15/H16/H18）· `actor_none` 6（H01/H03/H04/H05/H08/H20）· `no_candidate` 1（H02）· `no_edge` 5（H06/H07/H12/H13/H19）。

### 2.3 敏感性 16 例（剔除 F28 救应 H17–H20；同 freeze 的 `exclude_f28_and_gender_uncertain`）

| 指标 | 分子/分母 | 百分比 |
|---|---|---|
| 边召回 | **6/16** | **37.5%** |
| 候选召回 | **11/16** | **68.8%** |
| 方向召回 | **0/16** | **0.0%** |

方向分布：`reversed` 6 · `actor_none` 5 · `no_edge` 4 · `no_candidate` 1（`ok` 归零，唯一 ok 是被剔除的 H17）。

### 2.4 失败分解（20 条，逐例明细见 baseline `.md` §3）

| 层 | 命中 | 未命中 case | 主因 |
|---|---|---|---|
| 边 | 8/20 | H06 H07 H09 H10 H11 H12 H13 H14 H15 H16 H18 H19 | 地支不建克边/生边（G3）· 跨层不建边 · 墓不是边 |
| 候选 | 14/20 | H02 H06 H07 H12 H13 H19 | 体用不交不生成候选 · 支-支克无候选 · 支-干跨层无候选 · H13 墓 体用不交 |
| 方向 | 1/20 ok | — | 仅 H17（stem `ke` 候选 actor=己.s ∈ a） |

按缺口归类：

- **G3 地支不建克/生边**：边未命中 9 条（H06 H07 H09 H10 H11 H12 H18 H19 + H13 之外的墓地支行）；其中 H06/H07/H19 是「支克支 / 支克干」。
- **化=生 但支-支无 sheng 边**：H09/H10/H11/H12/H18 边全灭；候选层靠 `sheng(main_qi)` 派生补上 4 条，但方向全部 `reversed`（引擎的生源=生者，答案 actor=化者）。
- **墓不是边**：H13–H16 边恒 ✗（engine 只有 `relations.muku` 与「墓用」候选）；候选 3/4 命中，方向全 `reversed`（墓用候选 actor=入库方，答案 a=库）。
- **候选漏边**：H02（酉戌穿两端皆体）、H13（辰/丑皆体）、H06/H07/H12/H19（体用不交或无该层候选）。
- **方向**：`edges` 无 actor（G2），冲/穿/合候选 actor 一律 null → `actor_none` 6 条；这是事实缺口，不是评分器省略。

### 2.5 测试与门禁

```text
> .venv\Scripts\python.exe -m pytest tests/tools/test_p1_holdout_eval.py -q -o addopts="-ra --tb=short"
39 passed in 0.44s

> .venv\Scripts\python.exe -m pytest -q
1420 passed, 1 skipped, 1 warning in 135.37s (0:02:15)     ← 0 failed；skip 是 T-114 既知的那条
[exit code: 0]
```

### 2.6 两次运行逐字节一致

```text
> 连跑两次（同一命令、同一引擎），比对产物：
JSON identical: True    sha256 7086c4611f5165f0f90af9380e4934237e013e9da67ca627c6994ab54458f01d
MD   identical: True    sha256 94c66ea49615d65d4fef8ba840e020f305885b59ad9c59ebc353135d0982e68e
```

产物无时间戳（`generated_at` 之类一律不写）、地址集合排序、case 顺序取 answers 文件顺序 → 同引擎重跑逐字节稳定。

## 3. 未完成与风险

1. **这是 pre-fix 基线**：引擎未改。三处修复（G2 方向原语 / G3 支上克生边 / 墓的表达）任何一处落地，本表三个数字都会变，必须整体重跑，不得只改一格。
2. **主口径不含 muku（需中枢裁决）**：任务卡 §2.2 只认 `relations.edges` + `candidates`，故 墓 4 例边召回恒 0；dev 工具把 `relations.muku` 入库当成边。已同时在 JSON/MD 里给出 muku 等价边召回 **12/20（60.0%）/ 16 例 10/16（62.5%）** 作敏感性，**不混算**。若中枢认 muku 可算边，基线边召回改按 12/20 读，其余口径不动。
3. **`制` 不过滤 kind**：沿用 dev 的「克/制未说种类 → 不过滤」。本版只有 H01 依赖此条（子午按 chong 命中，按 ke 则不中）；若改判只认 `ke`，边召回 8/20 → 7/20。
4. **`墓` 方向与 dev 标注相反**：dev 写 `muku:{enter:a, ku:b}`，本 hold-out 写 a=库。评分器按 hold-out 的 `field_semantics`（a=施力方=库）实现，故墓类命中候选时方向为 `reversed`。两边口径对立，需中枢确认以哪边为准，**不要**直接判引擎错。
5. **地址多解会抬高召回上限**：9 例端点一字多址（H06/H09/H10/H13/H14/H15/H16/H18/H19，H18 两端都多址），按「任一组合命中即算」，属必要条件检验（宽松只会抬高上限）。多解清单已写进 baseline `.md` §4。
6. **`化` 借 `sheng`**：engine 无「化」边，映射到 sheng 是 dev 同口径近似；这使 4 条化例在候选层可命中但方向必然 `reversed`，属语义侧风险，不是数值噪声。
7. **未登记 kind/mechanism 直接 `ValueError`**：尺子不认的答案不许悄悄按「不过滤」算，未来 hold-out v2 加值必须先改映射表（走任务卡）。
8. **性别**：H17/H18 未注明 → 按乾起盘（`gender_used` 逐例可见）；P1 评原局关系，方向召回不依赖性别。H19/H20 的 `inferred_from_occupation` 不影响本次评分。
9. **OCR 变体未处理**：单字端点按标准干支解析，不做「戍→戌」修补；本 hold-out 的 a/b 无此问题（dev 那条修补规则不适用本 set）。
10. **不在本卡范围**：不与 dev 33 条比较；未设 P1 verdict 阈值（卡未给阈值，工具只出分子/分母/百分比）；未读 `sources/` 原文（`quote`/`source_ref` 仅作展示字段）。

## 4. 下游须知

1. **复跑命令（固定）**：

   ```bash
   .venv\Scripts\python.exe -m tools.p1_holdout_eval --holdout META/p1-holdout-v1.json --answers META/p1-holdout-answers-v1.json
   ```

   修复后**不要**直接覆盖 pre-fix 基线：先留存 `META/p1-holdout-baseline-v1.json`（或先复制一份），再用
   `--out-json META/p1-holdout-postfix-v1.json --out-md META/p1-holdout-postfix-v1.md` 输出新表，三数字与
   `direction_breakdown` 逐项对比。
2. **对比时看四个数**：`edge_recall` 8/20、`candidate_recall` 14/20、`directed_recall` 1/20、
   `muku_equivalent_edge_recall` 12/20；任一项下降须说明原因（同 ADR-004 基线尺子规则）。
3. **最敏感的 case（按口径杠杆排序）**：
   - **H13–H16（墓）**：muku 算不算边，一改就是 4 条边召回（40% ↔ 60%）。是最敏感的一组。
   - **H17**：唯一 `direction=ok`；也是 16 例方向召回 0/16 的全部来源（剔除它即归零）。
   - **H01**：唯一依赖「`制` 不过滤 kind」的命中。
   - **H09/H10/H11/H18（化）**、**H14/H15/H16（墓）**：`reversed` 主体，方向修复必须同时决定「化/墓的施力方定义」否则永远是 reversed。
   - **H06/H07/H19**：支-支 / 支-干克边缺口；**H02/H13**：两端皆体不进候选（补候选策略后才会动）。
4. **不要拿本基线反推规则**：hold-out 只用于评分与回归对比，不得用于调规则（freeze `scoring_owner` / 卡 §0）。
5. 评分器是可复用尺子：换 `--holdout/--answers` 即可评新集合；口径改动只允许改 `MECHANISM_TO_*_KINDS`（并在卡里说明），不许在报告里手改数字。

# T-148 · BRIEF（Worker D）

- 任务卡：`tasks/T-148/PROMPT.md`（含 §7 Amendments）
- 执行：子代理 D，2026-10-28
- 一句话结论：脚本 `python -m tools.timing_eval_set` 退出码 0，任务卡 §2 的 **392 例 / 11.2% / 45.2% / 48.7% / 62.5% 五个数字全部现场复现**；但复现所需的样本口径是**未去重**（详见「未完成与风险」第 1 条，须中枢裁决）。

## 1. 改动文件

| 文件 | 动作 | 说明 |
|---|---|---|
| `tools/timing_eval_set.py` | 新建 | 评测集构建器；`python -m tools.timing_eval_set` 可复跑，退出码语义见模块 docstring |
| `META/timing-eval-set-v1.json` | 新建 | 评测集：411 个候选案例（其中 382 可评测）、548 条逐条剔除原因、29 条候选不可评测原因、27 组重复明细、农历验证 |
| `META/timing-baseline-v1.json` | 新建 | 冻结基线：`frozen_at=2026-10-28T21:52:03+08:00`、`git_head=6b1ffead`、filter 定义、样本量、四个年龄带命中率、`payload_sha256`、清洗口径参考、差异分类 |
| `META/timing-eval-set-v1.md` | 新建 | 人读报告：解析漏斗、失败分类、基线表、差异分类、农历抽样验证 |
| `tasks/T-148/BRIEF.md` | 新建 | 本文件 |
| `tasks/T-148/STATUS.md` | 追加 | Execution Log 两行 |

未改动（逐项核对）：`cases/raw_feedback/parsed/real_cases_990.jsonl`、`engine/**`、`theory/**`、`sources/**`、`tiekoulu_1507_to_1428.json`、`pyproject.toml`、既有测试。未执行任何 git 写操作。

## 2. 原始输出

### 2.1 `.venv\Scripts\python.exe -m tools.timing_eval_set`（exit 0）

```text
[T-148] 婚姻应期评测集
  source   : cases/raw_feedback/parsed/real_cases_990.jsonl（992 条，读取失败 0）
  dedupe   : 992 -> 959（重复组 27，多余 33）
  funnel   : gender=950 birth_date=952 birth_time=947 marriage_cases=415 candidates=411 usable=382
  baseline : n=392（任务卡口径：未去重 + 出生字段原值 + 合理婚龄窗口）
    age_26      44/392 =  11.2%  (card 11.2%)
    age_24_30  177/392 =  45.2%  (card 45.2%)
    age_22_28  191/392 =  48.7%  (card 48.7%)
    age_20_30  245/392 =  62.5%  (card 62.5%)
  cleaned  : n=382  age_26=11.8%  age_24_30=45.3%  age_22_28=49.2%  age_20_30=63.1%
  lunar    : records=359 match=287 late_zi=10 other=0 no_pattern=61
  baseline : 已冻结，指纹一致（52853c76d35e…），未改写
  wrote    : eval=unchanged report=unchanged cases=411
  status   : OK（任务卡 §2 四个年龄带与 n=392 现场复现）
```

复跑幂等：第二次执行三个产物均 `unchanged`，无文件改动。

### 2.2 `.venv\Scripts\python.exe -m pytest -q`（exit 0）

```text
1066 passed, 1 skipped, 1 warning in 86.52s (0:01:26)
```

skip 为 AGENTS.md 记录的 T-114 已知项（`tests/tools/test_bundle_pii.py`，脚本缺失），与改动前基线一致。

### 2.3 `git status --porcelain cases/ META/`（Worker 收尾时）

```text
?? META/eval-protocols/
?? META/m2y395-cases-v1.json
?? META/m2y395-report-v1.md
?? META/m2y395-scored-v1.json
?? META/timing-baseline-v1.json
?? META/timing-eval-set-v1.json
?? META/timing-eval-set-v1.md
```

`git status --porcelain cases/` **为空**（jsonl 未动）。本卡只有 3 个 `timing-*` 文件；其余 `m2y395-*` 与 `eval-protocols/` 由并行会话在本卡执行期间生成（21:47–21:57），我未读写、未删除。并行会话仍在写 `META/`，中枢复跑时该列表可能继续变化。

另：`git diff --name-only` 有 3 个已跟踪文件被改（`tasks/T-148/PROMPT.md`、`docs/dispatch/README.md`、`docs/reviews/direction-decisions-v1.md`），均为中枢侧未提交改动（PROMPT.md 的 diff 就是 §7 Amendments），**不是本 Worker 的改动**。

### 2.4 卡 §1 数字对账（本脚本口径）

| 卡上数字 | 实测 | 判定 |
|---|---:|---|
| 992 例 | 992 | ✅ |
| 有性别 983 | 983 | ✅ |
| 出生含时刻 971 | 976（未去重）/ 947（去重） | ⚠️ 差 5，见风险 2 |
| 有婚姻事件且带年份 426 | 426 | ✅ |
| 事件 3379（有效年份 3370） | 3379（`year<=2026` 为 3370） | ✅ |
| 婚姻域事件 595 条 / 涉及 417 例 | 595 条；417 = 未去重+性别+时刻+婚姻 | ✅（417 的口径见风险 3） |
| 有性别+有出生时刻+有婚姻事件 415 | 417（未去重）/ 409（去重）；**415 = 去重后婚姻案例数** | ⚠️ 标签与数值不是同一口径 |
| `duplicate_key` 唯一 959 / 27 例重复 | 959 唯一 / 27 组 / 多余 33 条 | ✅（「27 例」= 27 组） |

## 3. 未完成与风险

1. **【必须裁决】392 是未去重口径，且带一个任务卡未写明的过滤。** 只有「**不去重** + `birth_datetime_raw` 按原值 + **剔除年龄 < 15 的婚姻事件**（案例需至少剩 1 条）」才同时复现 392 与 44/177/191/245（11.2/45.2/48.7/62.5）。「15 岁下限」是我从数字反推出来的，任务卡 §2 并未写明；不加上它样本是 419，卡上四个百分比全部对不上。我没有调年龄带（四个带严格按卡原文 26 / 24–30 / 22–28 / 20–30），也没有为凑数改带或改年龄算法。三种口径的实际差别：
   - 卡口径（未去重）：n=392，44/177/191/245 → 11.2 / 45.2 / 48.7 / 62.5；
   - 去重（§3.1 要求）：n=385，44/174/189/242 → 11.4 / 45.2 / 49.1 / 62.9；
   - 去重 + 农历换算 + 出生时刻齐备（= `usable_for_timing`）：n=382，45/173/188/241 → 11.8 / 45.3 / 49.2 / 63.1。
   冻结文件按 §2/§7.1 取 392，并把后两套写入 `cleaned_reference` 与 `difference_classification`。**45.2% 门槛在三套口径下都成立**，但下游若在 382 例上评分，必须用同口径的 45.3% 作参照，不能用 392 的分母。
2. **971 与实测差 5。** 实测「出生含时刻」= 976（未去重）/ 947（去重）；差 5 全部是时刻格式边角（`6 点` 这类整点、`24:00 分`、`0 点`、`晚上 18:00` 等）。基线只用出生**年份**，不受影响。
3. **415 / 417 标签错位。** 415 精确等于「去重后含婚姻域事件的案例数」；「性别+时刻+婚姻」= 417（未去重）/ 409（去重）。任务卡 §1 把 415 描述成后者，数值对不上，已在 §2.4 写清。
4. **农历不能二次换算。** 359 条 `calendar_type=lunar` 中，298 条原文含「排盘所用公历」，`birth_datetime_raw` **已经是公历**（287 例日期完全一致 + 10 例晚子时出生钟表日差一日 + 1 例无出生）；若再统一按农历换算，会有 42+ 例跨公历年、直接改变基线。其余 61 条无该标记（数字农历），由本脚本按农历换算（54 成功、0 失败、9 例跨公历年），**没有把农历当公历直接用**。
5. **年龄口径**：`event.year - birth.year` 整年差，无月日修正；15–50 岁窗口的上限 50 是非约束（本数据最大 50），下限 15 是剔除「婚姻事件年份早于 15 岁」的数据噪声（27 例），这是复现 392 的必要条件。
6. **依赖**：`lunar-python`（`requirements.txt` 已声明，venv 已装 1.4.8）。缺失时脚本抛 `RuntimeError` fail closed，不做静默降级。
7. **冻结机制**：基线文件存在且 `payload_sha256` 不符时脚本 **exit 3 拒绝覆盖**；复跑不改写任何文件。要改口径只能另建 v2。
8. **并行会话污染**：执行期间 HEAD 由 `bb65122f` 前进到 `6b1ffead`（他人在提交），基线记录生成时 HEAD `6b1ffead`；`META/` 另有并行产物（`m2y395-*`、`eval-protocols/`），非本卡产物，我未触碰。中枢复跑时若列表继续增长，属并行会话行为，不是本卡越界。

## 4. 下游须知

- **评测样本**：只用 `cases[].usable_for_timing == true` 的 **382 例**；`cases` 里共 411 条，另外 29 条是「有性别+出生+婚姻」但缺时刻或无 15–50 岁事件，见 `unusable_cases`。
- **事件数**：382 例可用案例内婚姻事件 547 条（其中合理婚龄窗口内 534 条）；去重后全部婚姻域事件 582 条（未去重 595 条）。
- **无预测字段**：`timing-eval-set-v1.json` 只有 `year / age / age_plausible / polarity / text` 等数据事实；脚本内置 `_assert_no_prediction_fields` 自检，出现 predict/forecast/probability/score 类键即报错退出。
- **时间口径**：286 例 `true_solar`（ADR-005 优先用 `true_solar_time_raw`）、125 例 `clock_beijing`。
- **出生来源**：255 `solar_asis`、138 `solar_from_paipan`（农历原文已换算）、18 `lunar_converted`（本脚本换算）。
- **复跑**：`.venv\Scripts\python.exe -m tools.timing_eval_set`，正常 exit 0；若基线数字将来对不上会 exit 2 并打印差异分类，**不会**自动调参对齐。
- **回答问题（卡 §6）**：**够。** 382 例可用、534 条合理婚龄事件，约为铁口箓 36 例的 10 倍；但门槛是人口学基线 45.2%（同口径 45.3%），任何应期模型必须先赢它才有意义。

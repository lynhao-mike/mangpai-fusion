# 职业路径真正未见 prospective cohort 工作流契约 v1

> 状态：staged / offline-only  
> 实现：[`tools/career_path_prospective_cohort.py`](../../tools/career_path_prospective_cohort.py:1)  
> 准入门禁：[`tools/career_path_holdout_gate.py`](../../tools/career_path_holdout_gate.py:1)  
> 上位评估协议：[`14-career-path-evaluation-protocol-v1.md`](14-career-path-evaluation-protocol-v1.md:1)

## 一、目的与当前阻塞

本契约建立真正未见职业路径 cohort 的采集、隔离、双人复核、分歧裁决、时序标签与准入链。它不运行模型、不评分、不创建新模型身份、不切生产。

当前仓库没有真实新样本，因此事实状态保持：

- `status = not_ready`
- `case_count = 0`
- `promotion_eligible = false`
- `formal_scoring_permitted = false`
- `production_switch_permitted = false`

禁止创建占位 case、伪造 30 案、伪造专家或人工审核。旧 P-series 40 案继续是 `development_replay_only`，绝不可进入本 cohort。

## 二、阶段与不可逆边界

```text
真实安全源文件
  → intake（白名单、源内容 SHA-256、身份指纹）
  → candidate manifest（按入组时间排序、开发集排他、身份去重）
  → 预测冻结（由既有后续流程负责；本工具不预测）
  → 两名人类 reviewer 独立提交标签
  → 一致确认 / 第三人裁决
  → 可选时序现实核验
  → finalize（满足真实双审后才生成 labels + holdout manifest）
  → holdout gate
  → 受控 registry successor（不覆盖原 registry）
```

所有写命令默认 dry-run。正式写入必须显式 `--write`，目标必须不存在，路径链不得有 symlink。源文件、intake、review、裁决、final manifest 和 labels 均不可覆盖。

## 三、prospective intake

单案源文件只能包含：

- `case_id`
- `pillars`：严格包含 `year/month/day/hour`
- `sex`：`乾/坤`
- 可选 `birth`
- 可选 `chart_source`
- `as_of_date`
- `dayun_intervals`

递归禁止至少包括：

- `occupation`
- `feedback`
- `known_fact/known_facts`
- `label/labels/career_label`
- `report/reports`
- `prediction/predictions/model_prediction`
- `reality/reality_state/reality_status`
- 通用 `status`

不得从 RF occupation、反馈文本、known facts、报告或模型预测自动猜标签。intake 必须记录原始源文件绝对路径和原始 bytes 的 SHA-256；后续 manifest 构建必须重新核验该 hash。

## 四、身份隔离与 candidate manifest

每案至少按 `case_id` 去重；同时用 `sex + 四柱` 的 canonical SHA-256 形成稳定身份指纹，防止只改 case ID 后重入。注册表可逐步补充开发集 `identity_fingerprints`；无指纹时仍强制 case ID 排他。

candidate manifest 必须：

1. 重新核验每个源文件 hash 与 intake 身份指纹；
2. 与所有 `development_replay_only` 数据排他；
3. 按 `ingested_at`、`case_id` 确定性排序；
4. 记录每个 intake 和源文件的路径、SHA-256、入组时间、身份指纹；
5. 固定 `labels_revealed=false`；
6. 在采集阶段只声明 `status=collecting / ready=false`，绝不因空清单或样本不足伪称 ready。

## 五、标签双审与裁决

标签严格枚举：

- `employment`
- `entrepreneurship`
- `mixed`
- `unknown`

每案必须有两个不同的 `human-*` reviewer。agent、模型、自动程序不得充当 reviewer。两人标签一致时状态为 `double_review_agreed`；分歧时保持 `not_ready / adjudication_required`，且必须由不同于两位 reviewer 的第三个 `human-*` 裁决，保留两份原始提交、裁决理由和最终标签。

`mixed/unknown` 必须保留在正式 labels 中，但不进入严格二分类分母。准入最低要求仍是严格二分类不少于 30，且 `employment/entrepreneurship` 各不少于 10。

预测冻结前，标签不得进入盲包、candidate manifest 或任何模型输入。本工具只管理人工标签制品，不提供任何标签推断接口。

## 六、时序子集

现实状态严格枚举：

- `employed`
- `entrepreneurial`
- `mixed`
- `transitioning`
- `unknown`

时序记录必须有可靠 `as_of_date`。大运区间是闭区间，必须 `start <= end`，并满足后一段 `start >` 前一段 `end`，因此端点相同也视为重叠。职业转换事件只能来自已核验人工输入，每个事件必须有 `human-* verified_by`。

缺少时序材料时标记 `not_ready_for_temporal_metrics`；这不否定已经合法完成双审的静态标签，也不阻止其作为静态样本保存。

## 七、finalize 与准入

只有所有传入标签均已完成真实双审/裁决，且严格二分类总数与分布达到预注册门槛时，finalize 才允许 create-only 生成：

- `labels.jsonl`
- `manifest.json`（`career-path-holdout-manifest/v1`）
- labels SHA-256
- cohort canonical SHA-256

产物 schema 由 [`career_path_holdout_gate.check_holdout_admission()`](../../tools/career_path_holdout_gate.py:121) 消费。`labels_revealed=false` 表示预测侧仍不得读取标签；它不表示 labels 文件不存在，而表示揭示阶段尚未发生。

注册表更新只能通过受控函数/命令生成新的 successor 文件，禁止覆盖原注册表。即使成功登记也固定 `promotion_eligible=false` 和 `production_switch_permitted=false`；评分和生产 promotion 属于独立后续任务。

## 八、当前 not_ready 证据

以下命令只读并应返回非零退出码及 `not_ready`：

```bat
python -m tools.career_path_prospective_cohort status
python -m tools.career_path_holdout_gate
```

其证据源是 [`career-path-dataset-registry-v1.json`](../../META/as-of-evaluation/career-path-dataset-registry-v1.json:82) 中 `unseen_holdout.status=not_ready`、`case_count=0`，以及预注册仍为 `labels_revealed=false / awaiting_unseen_holdout`。不得为使命令变绿而制造数据。

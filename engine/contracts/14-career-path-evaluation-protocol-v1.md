# 职业路径未见验证评估协议 v1

## 1. 目的

本协议定义职业路径模型进入一次性竞争评估前的数据准入边界。它只判定数据是否有资格成为 promotion holdout，不运行模型、不读取预测结果、不生成分数，也不切换生产入口。

机器可读事实源：

- 数据用途注册表：`META/as-of-evaluation/career-path-dataset-registry-v1.json`
- 预注册：`META/as-of-evaluation/career-path-holdout-preregistration-v1.json`
- 准入门禁：`tools/career_path_holdout_gate.py`

## 2. 开发集封存

P 系列旧 40 案统一分类为 `development_replay_only`。这些案例已经被旧预测、v1-v3 分类器冻结产物或开发标签观察，因此只允许用于开发回放、回归测试和失败分析。

旧 40 案禁止用于：

1. promotion 证据；
2. 新 holdout 成员；
3. holdout 评分；
4. 阈值选择；
5. 模型选择。

无论历史产物曾使用何种“holdout”措辞，均不改变本协议下的开发集归类。

## 3. 未见 holdout 准入

候选清单必须是 JSON 对象，至少包含：

```json
{
  "schema_version": "career-path-holdout-manifest/v1",
  "cohort_id": "...",
  "frozen_at": "ISO-8601 UTC timestamp",
  "case_ids": ["..."],
  "case_count": 30,
  "labels_path": "...",
  "labels_sha256": "64 lowercase hex",
  "labels_revealed": false,
  "one_shot_freeze": true
}
```

准入必须同时满足：

- case_id 唯一；
- 与数据注册表中所有开发数据完全排他；
- 严格二分类有效样本不少于 30；
- `employment` 与 `entrepreneurship` 每类不少于 10；
- 每案标签只能是上述两个枚举；不得把 `mixed`、`transitioning`、`unknown` 静默压缩成二分类；
- 每案有两个不同的人工复核者；
- 复核一致时状态为 `double_review_agreed`；不一致时必须有裁决者、裁决标签和 `adjudicated` 状态；
- 标签文件 SHA256 与 manifest 一致；
- manifest 冻结时间不得早于预注册时间；
- `labels_revealed=false`；
- `one_shot_freeze=true`；
- 预注册仍处于标签未揭示、尚未评分状态。

## 4. 标签文件格式

标签文件采用 JSONL，每行至少包含：

```json
{
  "case_id": "...",
  "label": "employment",
  "review_status": "double_review_agreed",
  "reviewers": ["reviewer-a", "reviewer-b"]
}
```

发生分歧时还必须包含：

```json
{
  "review_status": "adjudicated",
  "reviewers": ["reviewer-a", "reviewer-b"],
  "reviewer_labels": ["employment", "entrepreneurship"],
  "adjudicator": "reviewer-c",
  "adjudicated_label": "employment"
}
```

`adjudicated_label` 必须等于最终 `label`，裁决者不得与两名初审者相同。

## 5. 预注册冻结内容

预注册固定且不得在标签揭示后修改：

- 三个竞争模型：多数类/弃权基线、冻结旧计数基线、新关系模型；
- 指标：balanced accuracy、两类 recall、coverage、majority baseline，以及职业柱定位一致率、trace 完整率、mixed/transitioning 识别指标；
- promotion 门槛；
- 每类最低样本与总样本门槛；
- 一次冻结、一次评分、预测先于标签揭示；
- cohort、标签、预注册、预测、代码或规则的哈希要求。

## 6. 状态语义

门禁输出：

- `ready`：所有准入检查通过，只表示数据可进入后续冻结预测阶段；
- `not_ready`：真实材料不足或预注册明确处于等待状态；不得生成成绩；
- `rejected`：输入违反排他性、标签隐藏、哈希、复核、时间或枚举约束。

仓库当前状态必须是 `not_ready`：尚无真实、未见、满足至少 30 个严格二分类样本的新 holdout。不得用占位 ID、复制案例或旧 40 案伪造准入。

## 7. 非目标

本协议不修改 v1-v3 分类器，不运行任何新模型评分，不生成竞争结果，不将关系模型切入生产默认路由。正式评分属于后续任务，且只能在本门禁返回 `ready` 后进行。

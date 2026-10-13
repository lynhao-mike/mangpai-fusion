# 职业关系模型专家中间结构标注契约 v1

> 状态：staged / offline-only  
> 实现：[`tools/career_relation_expert_annotation.py`](../../tools/career_relation_expert_annotation.py)  
> 冻结前提：[`career-relation-model-v1-disposition.json`](../../META/as-of-evaluation/career-relation-model-v1-disposition.json)

## 一、目的与硬边界

本契约只为真实专家建立职业关系模型的中间结构真值。数据仅允许用于：

1. `structural_mechanism_audit`：审计五步定位、左柱与关系结构；
2. `new_model_id_design`：为新模型身份及后续预注册提供设计输入。

`career-path-relation-model-v1` 已冻结为 `invalidated_requires_new_model_id`。本工作流不得：

- 把标注结果解释为旧 model-v1 已恢复有效；
- 执行正式评分、promotion 或生产切换；
- 实现通用入墓、成格星等 unresolved 谓词；
- 摄入旧 P 系列 40 案作为 unseen holdout；
- 由 agent、模型或自动程序代填专家值；
- 生成就业 / 创业终态标签。

无真实人工双审数据时，状态必须为 `not_ready`，不得把缺数据记成 0 分。

## 二、中间结构标注对象

每份 `career-relation-expert-annotation/v1` 必须与一个盲包哈希绑定，并包含：

| 字段 | 约束 |
|---|---|
| `case_id` | 盲包中的案例身份 |
| `blind_packet_sha256` | 64 位小写 SHA-256 |
| `reviewer_id` | 真实人工身份，格式 `human-*` |
| `career_pillar` | `year/month/day/hour`；弃权时可为 `null` |
| `selected_stage` | 下列五步之一；弃权时可为 `null` |
| `left_pillar` | `year/month/day/hour`；弃权时可为 `null` |
| `key_relations` | 去重后的关系描述集合；不由工具推断 |
| `nature_labels` | `正财/偏财/印/食伤/官杀/比劫` 的去重子集 |
| `strength_state` | `无/弱/中/强/极强/unresolved` |
| `semantic_layers` | 五个语义层分别记录状态和值 |
| `unresolved_items` | 专家明确保留的未决项 |
| `conflicts` | 专家发现的理论或结构冲突 |
| `abstention_reason` | 未能给出结构值时的明确理由，否则为 `null` |
| `signed_at` | 专家签署时间；工具不自动生成或代填 |

### 2.1 五步定位枚举

- `step_1_self_officer_killing`
- `step_2_self_officer_killing_tomb`
- `step_3_other_officer_killing_linked_to_hour`
- `step_4_wealth_or_wealth_tomb`
- `step_5_formation_star_linked_to_self`

这些名称复用冻结结构契约，但不代表步骤 2、步骤 5 的 unresolved 谓词已经实现或验证。

### 2.2 五层语义隔离

`semantic_layers` 必须且只能分别包含：

- `career_type`
- `career_nature`
- `income_mode`
- `organization_form`
- `reality_state`

每层使用 `{status, value}`，其中 `status` 为 `annotated/unresolved/abstained/out_of_scope`。盲标阶段 `reality_state` 必须固定为 `{status: out_of_scope, value: null}`。

禁止出现 `employment_inclined`、`entrepreneurship_inclined`、`employment`、`entrepreneurship` 或其他终态压缩字段。职业类型、职业性质、收入方式、组织形态和现实状态不得互相代填。

## 三、盲标包

`career-relation-blind-packet/v1` 只包含：

1. 安全命盘事实；
2. 冻结规则 / 理论引用；
3. `intermediate_structure_only` 标注范围。

递归禁止字段至少包括：

- `occupation`
- `feedback`
- `known_fact/known_facts`
- 职业标签或通用 `label/labels`
- 模型预测或通用 `prediction/predictions`
- `reality_state/reality_status`

引用必须显式包含 `path`、`sha256`、`scope`。工具按引用内容排序，以 canonical JSON 的 SHA-256 生成确定性 `content_sha256`。

所有写操作默认 dry-run；只有显式 `--write` 才执行 create-only 写入。目标或路径链中存在 symlink、目标已存在时必须拒绝。

## 四、双专家与裁决

1. 每案必须有两个不同的真实 `reviewer_id`；
2. 原始提交只能 create-only，不得覆盖或就地修订；
3. 两份标注必须绑定同一 `case_id` 与 `blind_packet_sha256`；
4. 任一门禁字段不一致即构成分歧；
5. 分歧没有裁决时返回 `not_ready / adjudication_required`；
6. 裁决者必须是不同于两位 reviewer 的第三个 `human-*` 身份；
7. 裁决必须保留两份原始标注、理由及独立 resolution，不得重写原始提交。

## 五、一致率门禁

门禁至少输出下列指标：

| 指标 | 算法 | 可计分条件 |
|---|---|---|
| `career_pillar` | 精确一致 1/0 | 双方均非 `null` |
| `selected_stage` | 精确一致 1/0 | 双方均非 `null` |
| `left_pillar` | 精确一致 1/0 | 双方均非 `null` |
| `key_relation_set` | Jaccard | 并集非空 |
| `nature_label_set` | Jaccard | 并集非空 |
| `abstention` | 双方是否弃权的一致性 1/0 | 有完整双审 |

每项固定输出：

```json
{
  "numerator": 0,
  "denominator": 0,
  "value": null
}
```

只有可计分样本才增加分母。分母为 0 时 `value` 必须为 `null`，整体保持 `not_ready`。裁决解决数据可用性，但不得覆盖或抬高原始双审一致率。

本契约只固定输出结构与缺失语义，不在无真实专家数据时预设通过阈值。阈值必须由后续新 model_id 的独立预注册声明，不能追溯套用到 invalidated model-v1。

## 六、当前状态与子任务 3 输入

仓库当前没有真实人工标注，因此：

- `status = not_ready`
- `failures = [no_human_annotations]`
- `promotion_eligible = false`
- `formal_scoring_permitted = false`
- `production_switch_permitted = false`

后续子任务 3 若启动，只能接收以下结构真值输入：

1. 真实、独立、不可覆盖的双专家原始提交；
2. 与每份提交匹配的盲包 canonical SHA-256；
3. 分歧案的第三方裁决及理由；
4. 六项一致率的 numerator、denominator、value；
5. 专家保留的 unresolved、冲突、弃权原因和力量状态；
6. 分离的五层语义，不含就业 / 创业终态压缩；
7. 一个新的 `model_id` 与标签揭示前冻结的新预注册。

上述条件不齐时必须继续 `not_ready`。即使条件齐备，也只允许设计或审计新模型，不得直接解禁旧 model-v1。

# 三领域 prospective 盲测评估契约 v1

> 本契约仅定义事业、财富、婚姻三领域的 prospective 盲测基线。它是离线评估协议，不是生产规则、权重、路由或发布许可。

## 1. 范围与边界

- 领域固定为 `career`、`wealth`、`marriage`。
- 轨道固定为 `prospective` 与 `historical`，两者必须独立分账。
- 规范输入复用 [`DomainAnalysisRequest`](../v5/domain_slices/contract.py:18)。
- 冻结运行复用 [`V5RunSnapshot`](../v5/domain.py:370)。
- 制品使用 canonical JSON 与 SHA-256；写入由 [`publish_new_json()`](../evaluation/prospective_artifacts.py:64) 提供 create-only、原子发布语义。
- 本协议不得写生产规则、权重或路由，不得把历史案例冒充 prospective 案例，也不得制造真人样本或准确率。

## 2. 制品链

```text
blind intake
  → V5RunSnapshot
  → immutable freeze
  → post-freeze labels
  → reveal bound to freeze_hash
  → deterministic score
  → cohort status
```

各制品 schema：

| 制品 | `schema_version` | 关键绑定 |
|---|---|---|
| intake | `domain-prospective-intake/v1` | case、track、规范请求、identity hash |
| freeze | `domain-prospective-freeze/v1` | intake hash、snapshot hash、完整 snapshot、claim 列表、freeze hash |
| labels input | `domain-prospective-labels/v1` | freeze hash、完整 claim 标签 |
| reveal | `domain-prospective-reveal/v1` | case、track、freeze hash、reveal hash |
| score | `domain-prospective-score/v1` | freeze hash、reveal hash、指标、score hash |
| status | `domain-prospective-status/v1` | 分轨案例数与固定失败关闭状态 |

## 3. Intake 盲态白名单

intake 顶层只允许：

- `schema_version`
- `case_id`
- `track`
- `gender`
- `birth_datetime`
- `as_of_date`
- `domains`

任何额外字段均拒绝。对象与数组内部递归拒绝 feedback、label(s)、report、known facts、prediction(s)、occupation、reality status 及其规范化变体。

去重同时检查：

1. `case_id` 不得重复；
2. 由规范化性别和出生时间计算的 `identity_hash` 不得重复。

## 4. Freeze

[`freeze_snapshot()`](../evaluation/domain_prospective.py:335) 必须：

1. 校验 intake 与 snapshot 的 `case_id` 一致；
2. 校验 [`V5RunSnapshot.output_hash_matches()`](../v5/domain.py:470)；
3. 将 intake 的规范化 `gender`、`birth_datetime`、`as_of_date`、完整有序 `domains` 与 snapshot 输入及 metadata 严格比较；字段缺失或不一致均失败关闭；
4. 绑定稳定 [`V5RunSnapshot.hash()`](../v5/domain.py:473)；
5. 只接受 intake 请求领域内的 claim；
6. 保留 snapshot metadata 中 `domain_evaluation_claims` 的冻结顺序；
7. 拒绝重复 claim identity；
8. 计算覆盖完整冻结载荷的 `freeze_hash`。

正式 producer 必须在生成 snapshot 时从真实 runtime claim 确定性投影 `domain_evaluation_claims`，freeze 不得从报告、展示字段或外部现实标签临时推导。可评估子集仅纳入同时满足以下条件的命题：

- 有稳定 `task_id`，且以规范化领域加 `.` 为前缀；
- `stance` 不是 `abstain`；
- `school` 是注册流派；
- `claim_type` 是 `structure_claim`、`event_claim` 或 `timing_claim`；
- 有证据且有非空可证伪条件。

不满足条件的 runtime claim 必须逐条写入 `domain_evaluation_exclusions`，记录 source claim hash 与确定性排除原因；不得猜测 task 或把 timing claim 冒充结构结论。正式冻结命题身份包含：

- 派生的 evaluation `claim_id`；
- `domain` 与 `task_id`；
- `school` 与 `claim_type`；
- `source_claim_id` 与完整 canonical `source_claim_hash`；
- `state`，当前 producer 纳入子集时固定为 `claim`。

派生 evaluation ID 必须绑定上述 source identity，避免 source claim ID 跨领域复用导致碰撞。producer 同时生成 `domain_evaluation_integrity`；`capability_integrity` 必须覆盖 manifest、exclusion audit 与 evaluation integrity。freeze 必须从 snapshot 中的 runtime claims 重算投影并精确比较，因而仅修改 manifest 后重算 capability digest 仍应失败关闭。正式 producer 若没有任何可评估命题，不得制造命题，freeze 继续失败关闭。

CLI 写入必须 create-only，已存在目标不得覆盖。任何 snapshot、runtime claim、manifest、exclusion audit 或 hash 篡改均失败关闭。

冻结 claim 状态只有：

- `claim`：进入 hit/miss 分母；
- `abstain`：兼容既有冻结制品，可保留并统计，但不进入命中率分母，也不得计作命中；正式 producer 的 abstain runtime claim 进入 exclusion audit，而不进入正向 evaluation manifest。

## 5. Reveal

[`reveal_labels()`](../evaluation/domain_prospective.py:357) 只能消费已通过完整性校验的 freeze。labels 文档必须精确绑定该 `freeze_hash`，并完整覆盖每个冻结 claim。

每条标签固定包含：

- `claim_id`
- `domain`
- `task_id`
- `outcome`，仅允许 `hit` 或 `miss`

重复、遗漏、额外或身份不一致的标签均拒绝。reveal 之前缺少 freeze、freeze 被篡改或 hash 不匹配时不得生成制品。

## 6. Score 与分账

[`score_revealed()`](../evaluation/domain_prospective.py:423) 必须从已验证 freeze 与 reveal 确定性重算，不读取生产权重或现实报告。

指标至少包含：

- `overall`
- `by_domain`
- `by_task`
- `by_claim`

聚合桶记录 claim、scored、hit、miss、abstain 数量与 accuracy。`abstain` 只增加 `abstain_count`；accuracy 分母仅为非 abstain 的 `scored_count`。

## 7. Status 与生产门禁

[`summarize_status()`](../evaluation/domain_prospective.py:463) 的旧 score-only 参数只用于兼容和观察原始 score 数；孤立 score 无法证明 intake → freeze → reveal → score 父链或真人 admission，因此合格 case 数固定为 0，并返回 `unverified_artifact_chain`。historical 数量不得补足 prospective 门槛。

当前版本尚无经人工治理的真人 admission manifest，因此不存在可将案例计为 genuine prospective 的正向入口。后续 manifest 必须逐层验证 publisher `artifact_sha256`、各制品 canonical hash、父 hash、case/track/identity 一致性，并按 `identity_hash` 去重；在该治理制品落地前一律失败关闭，不得仅凭 30 份 score 进入 ready。

少于 30 个唯一 prospective 已评分案例时：

- `status = not_ready`
- CLI 退出码为 1
- `production_ready = false`
- `production_switch_permitted = false`
- failures 包含 `insufficient_genuine_prospective_cases`

达到 30 案只表示本 cohort 协议的样本数条件满足；本任务不授予生产切换许可，因此 `production_ready` 与 `production_switch_permitted` 仍固定为 false。生产许可需要任务范围之外的真实 prospective 质量、标签治理、统计门禁与人工裁决。

## 8. CLI

入口为 [`domain_prospective_cohort.py`](../../tools/domain_prospective_cohort.py:1)：

```bash
python -m tools.domain_prospective_cohort intake --input intake-candidate.json --out intake.json
python -m tools.domain_prospective_cohort freeze --intake intake.json --snapshot run.json --out freeze.json
python -m tools.domain_prospective_cohort reveal --freeze freeze.json --labels labels.json --out reveal.json
python -m tools.domain_prospective_cohort score --freeze freeze.json --reveal reveal.json --out score.json
python -m tools.domain_prospective_cohort status --score score.json  # 兼容观察；孤立 score 永远 not_ready
```

退出码：

- 0：命令成功，或 status 非 `not_ready`；
- 1：status 为 `not_ready`；
- 2：输入、schema、文件、绑定或 hash 校验失败。

所有输入必须是 UTF-8 JSON 普通文件；symlink 与非普通文件拒绝。publisher 制品在读取时必须重算并验证 `artifact_sha256`。所有输出均为 create-only。intake 默认扫描输出目录中的 publisher intake 制品进行 case/identity 去重；`--existing` 只作为额外显式来源，不再是唯一去重依据。

## 9. 真人边界

工程实现只能交付协议、CLI、测试与失败关闭状态。仍需真人提供并治理 30–50 个真正未见案例：

1. 在任何反馈、报告或现实标签揭示前完成 intake；
2. 在预测冻结后采集现实结果；
3. 按 claim 形成可审计标签并处理争议；
4. 审核 prospective 身份、独立性、完整性与合格条件。

在这些现实工作完成前，不存在真实 prospective 准确率，也不得声称生产就绪。

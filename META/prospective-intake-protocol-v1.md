# Prospective GO 新案采集协议 v1

> 状态：冻结采集契约  
> 适用任务目录：`META/prospective-go-task-catalog-v1.json`  
> 适用批次：`prospective-go-b01` 及后续全新批次  
> 目的：在不降低门槛、不伪造前瞻证据的前提下，建立 prediction-first 的真实新案证据链。

## 1. 硬门槛

- 完成的唯一真实 prospective 案例必须不少于 30；招募数、在途数和失访数不能代替完成数。
- `career.role_change` 或 `marriage.divorce_or_remarriage` 至少一个目标 binary 任务必须有不少于 20 条可评分标签，并同时包含 `occurred` 与 `not_observed`。
- 至少一个路由竞争任务必须有不少于 5 条同案同任务多派可评分记录；后续 learned/static 门禁要求 selection change 不少于 1。
- 校准门禁保持 `calibration_error < 0.2`，严格小于 0.2。
- `wealth.debt`、`marriage.divorce_or_remarriage`、`health.system_risk` 的可评分 A 级标签必须由两名独立人类 reviewer 形成；意见冲突时必须由第三方 adjudicator 仲裁。
- 任一泄漏、hash 篡改、重复命主冒充新案或 freeze 前揭示 outcome，整批 STOP。

## 2. Prospective 身份与唯一性

1. 案例必须是规则和路由版本冻结后进入系统的真实新命主。
2. 既有 `P-2026-*`、990、Top30、feedback-first 案例、同命主重复报告及复制命盘均不得计入 prospective/E3。
3. 同一 `sex_marker + four_pillars` 只允许入组一次；其稳定摘要作为 `subject_id_hash` 去重依据。改 case ID 不能绕过去重。
4. 首批仅预留 `P-GO-2026-001` 至 `P-GO-2026-010` 的任务槽位。现有 [`prospective-go-b01-tasks-by-case.json`](prospective-go/prospective-go-b01-tasks-by-case.json:1) 继续保留短槽位键；[`prospective-intake`](../tools/school_capability_dataset.py:683) 会在本次输入中唯一解析至完整 `P-GO-2026-NNN-{乾/坤}-{四柱}` case ID，无需也不得为真实四柱另生成改写版任务文件。首案及每 5 案 dry-run 可继续传入同批完整冻结表：严格符合 `P-GO-YYYY-NNN`、与本次输入同批、从 `001` 连续预注册且任务全部合法的尚未到达短槽位允许暂不匹配；本次已到达输入仍必须各自唯一命中。完整 case 键零匹配、短槽位格式错误、跨批、编号缺口、全部短槽位均未命中、同槽位多匹配或短/完整键重复解析至同案时必须拒绝。
5. 真实 case 目录只在取得授权的新命主到达后创建，不提前创建示例命盘或任何空 intake、空盲包、空 frozen run、空 witness registry。
6. 正负例必须由连续真实入组和完整观察窗自然产生，不按已知结果挑选、复制、删除或改写案例。

## 3. 时间顺序

每案必须满足以下不可逆顺序：

```text
received / enrolled
< prospective intake
< blind bundle prepared
< runner outputs freeze
< external witness signs freeze
< observation window ends or outcome occurs
< observation created
< independent reviews / adjudication
< labels bound and reveal witnessed
```

- 入组时间必须早于 freeze。
- outcome custodian 在 freeze witness 完成前不得释放观察资料。
- observation、review、label 和 reveal provenance 只能在 freeze 之后创建。
- 历史 frozen run、labels、scores、capability snapshot 不得覆盖；每批必须使用全新且不存在的目标路径。
- 盲包安全白名单只包含 `intake.json`、`tasks.json`、`rule-snapshot.json`、`bundle-manifest.json` 与 `cases/<case_id>/chart.json`；不得包含原始 `input.md`、反馈、标签、报告、known facts 或其他旁路文件。
- staged 冻结必须使用 [`school_capability_prospective.py stage-frozen-run`](../tools/school_capability_prospective.py:339)，规则快照固定为 [`prospective-go-rule-snapshot-v1.json`](prospective-go-rule-snapshot-v1.json:1)。
- freeze witness 必须使用 [`school_capability_prospective.py witness-freeze-chain`](../tools/school_capability_prospective.py:346)，一次安全生成或追加每案完整 `registered → prepared → freeze` 三事件段；该步骤不得提前创建 reveal。HMAC key 仅从 `--witness-key-env` 指定的环境变量读取，不得写入仓库、参数值或制品。
- 所有会写制品的 CLI 命令必须先执行 `--dry-run`；真实数据尚未到达时继续 HOLD，不运行正式写入命令，也不创建空制品占位。

## 4. 职责分离

| 角色 | 允许接触 | 禁止接触或兼任 |
|---|---|---|
| intake operator | 授权后的出生事实、四柱、大运、逐年流年 | outcome、反馈、旧报告、预测；不得兼任高风险 reviewer |
| runner operator | blind bundle、任务目录、规则快照 | 命主经历、观察、标签、反馈、旧报告 |
| witness | 事件摘要、时间、registry root | 不需要读取预测内容或 outcome |
| outcome custodian | 冻结后到达的真实观察资料 | freeze witness 前不得向 runner 或 reviewer 释放 |
| reviewer A/B | 相同 observation packet | 预测概率、runner 输出、报告文本、对方意见；两人必须独立 |
| adjudicator | observation 与两份冲突意见 | 不得兼任 reviewer A/B、intake operator 或 runner operator |
| evaluation operator | frozen run、bound labels、manifest | 不得改写任何父制品 |

## 5. 输入与 timing 完整度

1. `input.md` 只能包含出生事实、性别、四柱、起运、大运和逐年流年等预测输入，不得包含 known facts、outcome、feedback、labels、report 或真实经历。
2. timing case 必须使用可被 dataset canonical parser 解析的 `$DY_LOOP`；只列十年大运不构成逐年流年完整。
3. canonical `chart.json` 的 `liunian_steps` 必须非空，且每步至少包含真实 `year` 与 `ganzhi`；观察窗涉及大运时同时保留对应 `dayun_steps`。
4. 分配 timing 任务但 `liunian_steps` 为空时，该案对 timing 门禁为 HOLD。不得补造逐年流年，也不得覆盖已冻结输出。
5. 无真实岁运触发时 runner 的 `abstain` 是正确克制；不得为覆盖率强迫生成 Claim。

## 6. 观察与标签语义

- `occurred`：事件在预先定义的 observation window 内真实发生，且满足任务目录的精确定义。
- `not_observed`：完整 observation window 已结束、来源可核验，并明确未发生；只表示该观察窗内未发生，不表示终身不会发生。
- `no_data`：失访、观察窗未结束、来源冲突、资料不足或无法确认；不得进入 binary 校准分母，不得当作负例。
- `marriage.divorce_or_remarriage` 只标真实离婚或再婚，关系压力不是正例。
- `wealth.debt` 只标显著债务事件，正常信用消费不是正例。
- `health.system_risk` 必须有可核验健康资料或结构化访谈，只作风险分层，不冒充医学诊断。
- observation 不得包含 prediction probability、runner output、报告文本或 reviewer 结论。

## 7. 高风险双审

1. 三项高风险任务必须由两名独立人类 reviewer 阅读相同 observation hash 后分别提交意见。
2. reviewer A 与 reviewer B 身份必须不同，且均不得是 intake operator、runner operator 或 outcome custodian。
3. 两审一致时才可生成 A 级最终标签。
4. 两审冲突时保持 HOLD，必须由身份独立的第三方 adjudicator 仲裁；两份原始意见永久保留。
5. 单审、同一人使用不同名称、自动 reviewer 或删除冲突记录均不能生成 A 级标签。

## 8. 首批任务配额

| 任务 | 最低完成标签 | 首批规则 |
|---|---:|---|
| `career.role_change` | 20 | 全部 prospective 案例登记；首批 10 案全部分配 |
| `marriage.divorce_or_remarriage` | 20 | 对婚姻状态可观察案例登记；首批轮转 |
| `wealth.debt` | 12 | 连续入组，首批轮转 |
| `health.system_risk` | 12 | 需要可核验资料，首批轮转 |
| `career.change_window` | 10 | 必须有真实 `liunian_steps` |
| `marriage.event_window` | 10 | 必须有真实 `liunian_steps` |
| `health.event_window` | 8 | 必须有真实 `liunian_steps` |
| `wealth.major_loss_window` | 8 | 必须有真实 `liunian_steps` |

这些是采集下限，不替代总完成案不少于 30、binary 不少于 20、竞争不少于 5、selection change 不少于 1、校准误差严格小于 0.2 或高风险 A 级双审门槛。

## 9. 每批冻结与见证操作

1. 用真实完整 case 路径、现有短槽位 tasks-by-case 与十任务目录执行 `prospective-intake --dry-run`；唯一解析成功且隔离检查通过后，才允许正式写全新 intake。
2. 使用 [`prospective-go-rule-snapshot-v1.json`](prospective-go-rule-snapshot-v1.json:1) 执行 `prepare-blind --dry-run`；核对盲包只含安全白名单后，才允许正式创建全新目录。
3. 对正式盲包执行 `stage-frozen-run --dry-run`；核对六来源三态输出、任务 hash 与规则快照 hash 后，才允许正式写全新 frozen run。
4. 独立见证方在环境中提供 HMAC key，执行 `witness-freeze-chain --dry-run`；核对每案完整三事件段后，才允许正式写全新 registry。追加既有链时用 `--registry` 读取旧 registry，并将 `--out` 指向全新路径，禁止覆盖。
5. 上述链只到 freeze 为止。outcome custodian 继续封存真实结果，直至观察窗结束；reveal 必须走后续冻结后流程，不能由本阶段提前生成。

## 10. 反馈与停止条件

- 生产 case 反馈只允许通过 `tools/feedback_ingest.py`，并先执行 dry-run；评估 observation 不由该工具生成。
- 不使用、恢复或引用 `calibrate.py` 作为新反馈入口。
- 发现以下任一情况立即整批 STOP：预测前接触 outcome/反馈/标签/旧报告；review packet 含预测；重复命主跨批计数；witness 顺序断裂；hash 不一致；历史案例改名；历史冻结制品被改写。

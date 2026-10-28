# META/eval-protocol-v1.md · 断语评测预注册格式 v1（T-150）

> 本文只是**格式说明**，不是任何一条断语的生效协议。生效协议是具体文件
> （建议 `META/eval-protocols/<protocol_id>.yaml`），跑分时由
> `python -m tools.claim_metric --protocol <file> --cases <file>` 读取。
>
> 铁律：**先写协议、后跑分**。协议缺失或字段缺失时工具退出码 2，拒绝出分（fail-closed）；
> 不许「先看答案、再补口径」。

## 1. 为什么必须预注册

「结构不存在」与「结构存在但失败」混在一起时，任何正确率都可以被事后解释：
命中率低，可以说是结构没出现；命中率高，可以说是结构对了。预注册的作用是把
**触发定义、方向规则、计分集合、基线、判定门槛**先钉死，跑分阶段只能执行、不能改。

配套字段来自契约 23 §5.1：每条断语求值输出 `triggered`（结构是否触发）与
`outcome`（触发后成败）。**评测只在 `triggered is True` 的集合内计分。**

## 2. 协议文件必填字段

| 字段 | 类型 | 说明 |
|---|---|---|
| `protocol_id` | str | 协议唯一 ID，与文件名一致 |
| `claim_id` | str | 被评测断语的 ID（一次一条，不许批量复用口径） |
| `frozen_at` | str | 冻结时间（ISO 8601，带时区） |
| `commit` | str | 冻结时所在提交（哈希或 `pre-<task>`） |
| `trigger_definition` | str | 「触发」指什么：前置条件 + 框架前置全部成立 |
| `direction_rule` | str | 方向从何而来（原文锚点/机制），**追认答案不算** |
| `label_map` | map | 标签 -> 字母列表，如 `{低学历: [A, B]}` |
| `prediction_rule` | map | 分支 -> 标签，如 `{self_controls: 一婚}`；标签必须在 `label_map` 中 |
| `scored_set_rule` | str | 计分集合定义；必须写明 `triggered is True` 且有预测、且有答案 |
| `baseline` | str | 判定基线（`baseline_single`）；`baseline_same_k` 仅作乐观参考 |
| `decision_rule` | str | 判定门槛（如：accuracy 严格高于 baseline_single，且 Wilson 下界高于基线） |

缺失任一项、`label_map` 为空、`prediction_rule` 引用了未定义标签，工具一律拒绝运行。

## 3. cases 文件格式

列表，或 `{"cases": [...]}`。每例：

```json
{"case_id": "P01", "claim_id": "M1-D-298", "branch": "self_controls",
 "triggered": true, "outcome": "success",
 "prediction_letters": ["B"], "answer_letter": "B"}
```

- `triggered`：`true` / `false` / `null`（三值，`null` = 事实不足，**不是** `false`）。
- `outcome`：`success` / `fail` / `unknown`；`triggered` 不是 `true` 时必须是 `unknown`
  （否则工具拒绝：禁止 `triggered=false` + `outcome=fail`）。
- `prediction_letters`：预测字母列表；缺省时按 `prediction_rule[branch] -> label_map` 派生；
  显式 `[]` 表示**弃权**，不会被派生覆盖。
- `answer_letter`：标准答案；`null` / 空串表示缺失。
- `case_id` 必须唯一，输出按 `case_id` 排序，保证逐字节可复现。

## 4. 计分口径（写死，跑分中不许改）

- **scored 集** = `triggered is True` 且预测字母非空**且**有标准答案。
- 三个排除项分别计数、不静默丢弃：`n_abstain`（触发但预测为空）、
  `n_not_triggered`（`triggered` 不是 `true`）、`n_missing_answer`（触发且有预测、无答案）。
  `n_total = n_scored + n_abstain + n_not_triggered + n_missing_answer`。
- `n_correct` = 答案 ∈ 预测字母；`accuracy = n_correct / n_scored`。
- **`n_scored == 0` 抛错（退出码 2）**，禁止 0/0 静默出分。
- `baseline_single`：scored 集上出现最多的单个字母的命中率（并列按字母序）。**这是判定基线。**
- `baseline_same_k`：每例按自己的 `k`，取 scored 集上频率最高的 `k` 个字母当常量预测的命中率。
  多猜字母天然占便宜，所以它只作**乐观参考**，不参与判定。
- `wilson_ci_95`：accuracy 的 Wilson 区间（4 位小数）。
- `by_branch`：按 `branch` 分组报 `n / correct / accuracy`（该分支无 scored 样本时 accuracy 为 `null`）。
- `input_sha256`：cases 规范化 JSON（按 `case_id` 排序、键排序、紧凑分隔）的 SHA-256。
- 确定性：无时间戳、无随机数，同一输入两次运行输出逐字节一致。

## 5. 判定顺序（建议写法，写进 `decision_rule`）

```text
1. 先看 n_scored 是否够（协议里可写最低样本量；不够就报「不可判」而不是报低分）
2. accuracy > baseline_single            —— 未超过基线即「与瞎猜无异」
3. wilson_ci_95 下界 > baseline_single   —— 未超过即「样本不足，不能宣称有区分力」
4. by_branch 不得靠单一分支撑起整体分数  —— 逐分支报告，避免以偏概全
```

`baseline_same_k` 只用来回答「多猜字母是不是把分数撑起来的」，不参与通过/不通过。

## 6. 退出码

| 码 | 含义 |
|---|---|
| 0 | 正常出分 |
| 1 | `--self-check` 手算断言失败（实现与手算值不符） |
| 2 | fail-closed：文件缺失 / 预注册缺字段 / 违约组合 / scored 集为空 |

## 7. 示例（格式演示，不是生效协议）

```yaml
protocol_id: demo-v1
claim_id: DEMO-001
frozen_at: "2026-10-28T00:00:00+08:00"
commit: pre-T-151
trigger_definition: 前置条件与框架前置全部成立
direction_rule: 原文「…」→ 方向=一婚，不追认答案
label_map:
  一婚: [B]
  多婚: [C, D]
prediction_rule:
  self_controls: 一婚
scored_set_rule: triggered is true 且预测非空且有答案；缺答案单列不入分母
baseline: baseline_single（scored 集出现最多的单个字母）
decision_rule: accuracy 严格高于 baseline_single 且 Wilson 下界高于基线
```

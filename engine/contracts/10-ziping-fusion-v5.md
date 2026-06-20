# ZiPing Fusion Engine v5 契约 · 10-ziping-fusion-v5

> 本契约定义 v5 Staged clean path 的并行核心：子平类 / 滴天髓类 / 高德臣 / 段建业 / 杨清娟五派独立推理 + 结构图建模 + 三段式角色化仲裁 + 受限概率预测 + 回归学习优化。v5 当前为并行核心，不替换正式报告出口；正式报告仍遵守既有统一报告归档与展示层禁显约束。

---

## 一、定位

v5 不是把旧 D1-D4 pipeline 改名，也不是给规则增加派别标签。v5 的目标是建立一个可并行验证的五派命理推理操作系统：

```text
ParsedInput / Chart
  → 子平类独立推理
  → 滴天髓类独立推理
  → 高德臣独立推理
  → 段建业独立推理
  → 杨清娟独立推理
  → 命题结构图统一表达
  → 结构合法性仲裁
  → 事件落地仲裁
  → 受限概率 / 应期仲裁
  → Prediction Ledger
  → Learning Signal
```

五派在 v5 中定义为工程推理流派，不宣称为传统史学上的固定宗派划分。子平类与滴天髓类必须是一等命题生产者，而不是隐藏在底层的隐性前提。

---

## 二、非谈判原则

1. **五派隔离**：每个 school runner 只读取同一份 chart 输入，不读取其他 runner 的中间结论。
2. **同协议输出**：五派全部输出 `V5Claim`，不得直接拼接自然语言报告。
3. **角色化仲裁**：五派不是平权投票器；子平类、滴天髓类偏结构约束，三盲派偏事件落地。
4. **图谱统一**：五派输出必须进入结构图，仲裁器不得直接拼接自然语言。
5. **仲裁显式**：每个领域至少区分结构合法性、事件落地、概率应期三段裁决。
6. **概率受限**：只有可定义、可反馈、可校准的事件进入概率层；性格、格局高低、宽泛画像默认不概率化。
7. **学习可追踪**：反馈首先生成 learning signal，不得在小样本阶段自动改核心规则。
8. **出口不泄密**：统一报告不得暴露 claim_id、prediction_id、内部结构图 ID、仲裁索引或学习信号编号。

---

## 三、五派定义

| school_id | 展示名 | 工程角色 | 主要强项 | 仲裁位 |
|---|---|---|---|---|
| `ziping` | 子平类 | structure_law / 基础法度派 | 旺衰、格局、十神、用忌、调候、岁运承载 | 结构合法性主权重 |
| `ditiansui` | 滴天髓类 | qi_momentum / 气势审美派 | 清浊、气势、流通、寒暖燥湿、成败层次 | 结构反证与层次修正主权重 |
| `gao_dechen` | 高德臣 | work_transformation / 做功结构派 | 做功、宾主、制化、体用、事业财富落点 | 结构合法性 + 事件转化双权重 |
| `duan_jianye` | 段建业 | event_framework / 盲派理法事件派 | 宫位、十神落实、事件框架、人生主线 | 事件落地主权重 |
| `yang_qingjuan` | 杨清娟 | image_detail / 象法细节派 | 人物画像、婚恋家庭、健康细节、生活事件 | 细节取象与婚恋健康主权重 |

---

## 四、最小数据契约

### 4.1 V5Claim

每个独立 runner 只能输出 `V5Claim`：

| 字段 | 含义 |
|---|---|
| `claim_id` | 稳定命题 ID；内部使用，报告禁显 |
| `school` | 五派之一：`ziping` / `ditiansui` / `gao_dechen` / `duan_jianye` / `yang_qingjuan` |
| `school_role` | 工程角色：structure_law / qi_momentum / work_transformation / event_framework / image_detail |
| `domain` | 学业 / 事业 / 财富 / 婚姻 / 健康 / 性格 / 总体 |
| `claim` | 核心命题 |
| `claim_type` | structure_claim / event_claim / timing_claim / evidence_claim / counter_claim |
| `stance` | support / oppose / mixed / abstain |
| `polarity` | positive / negative / mixed / neutral |
| `confidence` | 命题置信度，不等于最终仲裁置信度，也不等于事件概率 |
| `evidence` | 支持证据链 |
| `counter_evidence` | 反证条件或削弱证据 |
| `timing_hints` | 大运、流年、年龄段等时间线索 |
| `probabilistic` | 是否允许进入受限概率层 |
| `falsifiable` | 可证伪条件 |
| `metadata` | 内部扩展信息 |

### 4.2 Claim Type 语义

| claim_type | 用途 | 典型生产者 |
|---|---|---|
| structure_claim | 格局、旺衰、用忌、清浊、流通、原局承载 | 子平类、滴天髓类、高德臣 |
| event_claim | 婚恋、事业、财富、健康、家庭等事件判断 | 高德臣、段建业、杨清娟 |
| timing_claim | 大运、流年、年龄段触发 | 五派均可输出 |
| evidence_claim | 单独证据片段或结构事实 | 五派均可输出 |
| counter_claim | 反证、降级、否决条件 | 子平类、滴天髓类、高德臣优先 |

### 4.3 StructureGraph

结构图最小元素：

- chart 节点：四柱、日主、月令、大运摘要。
- claim 节点：五派命题。
- evidence 节点：证据片段。
- domain 节点：六大领域及总体。
- relation 边：feeds / contains / supports / weakens / conflicts / targets / timed_by / prerequisites。

结构图不是为了画图，而是为了让仲裁器知道冲突发生在哪里：结构冲突、事件冲突、时间冲突、程度冲突、表达冲突必须分开处理。

### 4.4 ArbitrationResult

每个 domain 至少输出三段仲裁：

1. `structure_legality`：结构合法性仲裁。
2. `event_realization`：事件落地仲裁。
3. `probability_timing`：受限概率与应期仲裁。

每段仲裁输出：

- 主结论。
- 胜出流派。
- 少数派观点。
- 支持分、反对分、冲突类型。
- 置信度。
- 仲裁理由。
- 是否允许概率化。

### 4.5 PredictionLedger

概率层只写入 ledger，不直接改报告：

- `prediction_id`。
- `domain`。
- `event_label`。
- `probability_range`。
- `confidence`。
- `time_window`。
- `calibration_note`。
- `feedback_state`。

概率只允许输出范围，不允许伪精确到个位数。没有时间窗、事件定义、反馈标签的命题不得概率化。

### 4.6 LearningSignal

反馈首先进入 learning signal：

- 命题是否被反馈命中、失验、部分命中或跳过。
- 受限概率预测是否命中以及时间偏差。
- 哪个 school、claim_type、domain、rule_id 受到影响。
- 是否达到自动统计阈值。
- 是否需要人工裁决。

小样本阶段 learning signal 不得直接改写生产规则。

---

## 五、三段式角色化仲裁

### 5.1 结构合法性仲裁

主要参与者：子平类、滴天髓类、高德臣。

回答：这个判断在命盘结构上是否站得住？

典型问题：

- 是否身能任财。
- 格局是否成败有据。
- 气势是否流通。
- 寒暖燥湿是否有救。
- 做功路径是否成立。

### 5.2 事件落地仲裁

主要参与者：高德臣、段建业、杨清娟；子平类与滴天髓类提供结构约束。

回答：这个结构会表现为什么现实事件？

典型问题：

- 婚姻不稳、迟婚、关系反复还是配偶压力。
- 财动表现为收入增长、投资损失、财务压力还是资源调动。
- 官杀动表现为职业变动、权责上升、压力增大还是健康风险。

### 5.3 概率 / 应期仲裁

五派均可参与，但只有白名单事件进入概率层。

允许概率化的对象：

- 时间窗明确的事业变动、婚恋波动、财务压力、健康风险。
- 领域明确且可反馈的升学压力、职业变动、关系破裂、投资损失、疾病风险。

禁止概率化的对象：

- 性格气质宽泛描述。
- 格局高低、层次审美等缺少反馈标签的判断。
- 无时间窗、无事件定义的笼统吉凶。

---

## 六、Staged clean path 验收

第一阶段验收只要求并行核心可运行：

1. 同一 case 输入能产出五派独立命题。
2. 五派命题统一进入结构图。
3. 仲裁器能按结构合法性、事件落地、概率应期三段输出结果。
4. 概率层只对白名单事件输出概率，对性格与宽泛结构判断拒绝概率化。
5. 输出对象可 `to_dict()` / `from_dict()` / `to_json()` / `from_json()` 往返。
6. v5 结果不替代正式报告出口，不泄露内部 ID 到统一报告。

---

## 七、暂不做

- 不切换正式 `render_report.py` 默认出口。
- 不把 v5 内部 ID 写入用户可见报告。
- 不引入黑箱机器学习。
- 不自动改写生产规则权重。
- 不把五派做成平权投票器。
- 不让任付红系进入五派 MVP；如后续保留，应作为 timing enhancer 或 evidence enhancer 讨论。

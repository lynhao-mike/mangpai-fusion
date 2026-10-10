# as-of 双模式重构 Phase 2：事业事件预测能力施工与开发回放证据

> 日期：2026-09-30  
> 范围：事业角色变化切片；共享历史/未来预测机制、冻结后揭示、多维历史回放、legacy/shared 开发比较。  
> 结论：**工程施工与 development replay 比较已完成，但没有形成正式准确率提升证据。**

---

## 1. Phase 2 目标与边界

Phase 1 证明了无反馈 `BLIND_BASELINE` 可以被隔离、冻结和归档，但没有证明预测正确。Phase 2 因此把首个高杠杆改动限定为事业角色变化，并要求历史与未来共享一条可证伪链：

```text
Chart
→ Structural Qualification
→ Qualified Career Event
→ Annual Timing
```

本阶段明确不做：

- 不切换生产入口；
- 不修改生产路由、全局权重或反馈闭环；
- 不进入 Calibration；
- 不将已暴露历史样本冒充 unseen holdout；
- 不依据单个案例写规则补丁；
- 不用 coverage 或 claim 数量替代准确率。

---

## 2. 准确率瓶颈审计

跨案例审计确认三个主要瓶颈：

1. **旧 Ren 顺序倒置**：岁运出现冲、合、刑、穿或伏吟后，直接声明事业事件存在；缺少命局是否具备事业角色变化结构的资格门，容易产生 timing-only 假阳性。
2. **事件语义过粗**：预测只输出广义 `career.role_change`，不能稳定区分入职、跳槽、调动、晋升、辞退、失业和创业失败；方向也被 legacy 的固定 `negative` 或 shared 结构规则的 `neutral` 限制。
3. **真实评估数据不足**：仓库没有正式 unseen holdout；历史文本多为复合事件，且明确无事件年份稀缺，因此当前只能执行 development replay，不能完成正式能力 promotion。

---

## 3. 已实施的共享预测机制

### 3.1 共享 Structure → Event → Timing 预测器

[`engine/asof/career_event_prediction.py`](../engine/asof/career_event_prediction.py) 新增独立模型：

```text
career-role-change-shared-predictor-v1
```

公开入口只接受：

```text
case_id
chart
window
```

不接受 known facts、feedback、verification、labels 或 calibration。历史和未来只通过同一 `CareerPredictionWindow` 的 `mode` 与年份区分。

实际链路为：

1. 从 `ChartFactLedger` 生成 `cfv-v1`；
2. 运行段派事业角色变化结构资格门；
3. 结构通过后构造 `StructuralVerdict`；
4. 从结构裁决构造 `EventHypothesis`；
5. 任派 timing 层只消费已成立事件；
6. 无结构时 `structure_abstain`，无年度触发时 `timing_abstain`。

这使历史回放和未来预测不再使用两套机制。

### 3.2 legacy Ren 比较适配器

[`engine/evaluation/career_event_replay.py`](../engine/evaluation/career_event_replay.py) 增加：

```text
career-role-change-legacy-ren-timing-event-v1
```

适配器把旧 Ren `Timing → Event` 路径投影到与 shared 模型相同的最小评分契约，但不改写旧 runner 本身。两模型因此可以共享：

- 同一 case-year cohort；
- 同一 chart-only 输入；
- 同一事件标签；
- 同一五维评分方法；
- 各自独立 freeze hash。

---

## 4. 历史回放与防泄漏评估层

[`engine/evaluation/career_event_replay.py`](../engine/evaluation/career_event_replay.py) 实现：

```text
predict
→ project
→ freeze
→ reveal labels
→ score
```

### 4.1 冻结前预测投影

预测投影只保留：

```text
case_id
model_id
status
observation window
predicted window
domain
event_type
direction
magnitude
```

禁止携带 known facts、feedback、verification、labels、truth、observed、calibration 或事件原文。

### 4.2 冻结与揭示

- 预测按 case ID 确定性排序；
- canonical JSON 计算 SHA-256；
- 单个 frozen replay 只能包含一个 model ID；
- 标签文档必须绑定完全匹配的 `freeze_hash`；
- 未冻结案例不得揭示；
- dataset classification 不得漂移；
- 每个冻结评价单元必须显式属于 event 或 no-event，不能把标签缺失当负例。

### 4.3 五维评分

每个评价单元输出：

- 时间命中；
- 事件类型命中；
- 领域命中；
- 方向命中；
- 重大性命中；
- predicted / observed；
- false positive / false negative。

汇总同时报告 coverage、abstain、五维命中率、FP 和 FN。

---

## 5. 真实 development replay cohort 与物理隔离

首批小型 cohort 已拆成两个物理独立 artifact：

- [`META/as-of-evaluation/career-event-development-replay-blind-cohort-v1.json`](../META/as-of-evaluation/career-event-development-replay-blind-cohort-v1.json)：只含性别标记、四柱、大运区间和评价年份；
- [`META/as-of-evaluation/career-event-development-replay-labels-v1.json`](../META/as-of-evaluation/career-event-development-replay-labels-v1.json)：只含规范化事件、显式 no-event、来源引用和标签治理信息。

数据规模与治理：

- 3 个真实命盘；
- 10 个 case-year 评价单元；
- 9 个明确事业事件单元；
- 1 个由原文“工作平稳”支持的显式 no-event 单元；
- 同年“调动、升职”保留为多个候选标签；
- income-only 事件不自动纳入 role change；
- 全部分类为 `development_replay_only`；
- `promotion_eligible = false`；
- `unseen_holdout_evidence = none`。

评价单元使用：

```text
<source-case-id>@<calendar-year>
```

[`tools/career_event_replay_harness.py`](../tools/career_event_replay_harness.py) 以三个命令建立进程级边界：

```text
predict-freeze --blind-cohort ...
→ reveal-score --freeze ... --labels ...
→ compare --score ...
```

`predict-freeze` 的 parser 没有 labels 参数，且只打开 blind cohort；`reveal-score` 必须先读取并验证 freeze bundle，验证通过后才打开独立 labels artifact；`compare` 只读取 score bundle。物理隔离测试会拦截预测阶段读取标签路径，以及冻结无效时提前打开标签文件。

---

## 6. legacy vs shared 开发回放结果

阶段制品与比较制品：

- [`META/as-of-evaluation/career-event-development-replay-freeze-bundle-v1.json`](../META/as-of-evaluation/career-event-development-replay-freeze-bundle-v1.json)
- [`META/as-of-evaluation/career-event-development-replay-score-bundle-v1.json`](../META/as-of-evaluation/career-event-development-replay-score-bundle-v1.json)
- [`META/as-of-evaluation/career-event-development-replay-comparison-v1.json`](../META/as-of-evaluation/career-event-development-replay-comparison-v1.json)
- [`reports/as-of-phase-2-career-event-development-replay-comparison-2026-09-30.md`](as-of-phase-2-career-event-development-replay-comparison-2026-09-30.md)

当前证据链哈希：

```text
blind_cohort_digest = db649c962498da8ea7c5cef4b6295bc843b5b3f15de6710b96c2ae3c2f918ad3
labels_digest       = f2da11b673cfc40e8682bc6ca92c5482e40c0c686b4f3009004bd15c683d8d7c
freeze_bundle_hash  = a615b8135facbc4195d6ecbe370c82115864cc1a974258bb09c479c2ae8b6f67
score_bundle_hash   = cff9cf15f87e3d65addb58243dff2cfbf838ba30da7ee00655a2f27b69e9c3b5
comparison_hash     = 33416188dcd29544e567dc2665cde19f92fdae5d7f716006eea74c2290437d88
```

| 指标 | legacy Ren | shared Structure→Event→Timing | shared - legacy |
|---|---:|---:|---:|
| 预测单元数 | 8 | 2 | -6 |
| 弃权单元数 | 2 | 8 | +6 |
| coverage | 0.800000 | 0.200000 | -0.600000 |
| 时间命中率 | 0.777778 | 0.222222 | -0.555556 |
| 事件类型命中率 | 0.777778 | 0.222222 | -0.555556 |
| 领域命中率 | 0.777778 | 0.222222 | -0.555556 |
| 方向命中率 | 0.111111 | 0.111111 | 0.000000 |
| 重大性命中率 | 0.555556 | 0.222222 | -0.333334 |
| false positive | 1 | 0 | -1 |
| false negative | 2 | 7 | +5 |

### 6.1 可以支持的结论

1. 结构资格门确实阻断了明确 no-event 年份上的旧 timing-only 假阳性：FP 从 1 降至 0。
2. 这一收益以严重降低覆盖为代价：coverage 从 0.80 降至 0.20。
3. shared 模型在该 cohort 上漏掉大量真实事业变化：FN 从 2 增至 7。
4. 因此首个结构门实现证明了“阻断机制有效”，但**没有证明总体预测能力提升**。

### 6.2 新暴露的最高优先级瓶颈

当前段派结构资格规则过窄，只承认一个命盘的事业变化结构，导致另外两个具有多次真实职业变动的命盘全部 `structure_abstain`。这表明下一步不应调整权重或做 Calibration，而应：

1. 对被结构门拒绝但有明确事件的命盘做结构级错误分析；
2. 判断缺失的是官杀/食伤计数条件、做功适配，还是规则覆盖面；
3. 通过新的开发案例交叉验证后，才允许形成跨案例候选结构规则；
4. 同时建立独立的事件类型与方向判别层，停止用固定 `negative` 或 `neutral` 代替方向预测。

---

## 7. 测试与回归

新增或扩展测试：

- [`tests/asof/test_career_event_prediction.py`](../tests/asof/test_career_event_prediction.py)
- [`tests/evaluation/test_career_event_replay.py`](../tests/evaluation/test_career_event_replay.py)
- [`tests/evaluation/test_career_event_replay_harness.py`](../tests/evaluation/test_career_event_replay_harness.py)

物理隔离与核心定向回归：

```text
uv run --with pytest --with PyYAML pytest \
  tests/evaluation/test_career_event_replay.py \
  tests/evaluation/test_career_event_replay_harness.py \
  tests/asof/test_career_event_prediction.py -q

27 passed in 32.52s
```

扩展事业切片回归：

```text
uv run --with pytest --with PyYAML pytest \
  tests/evaluation/test_career_event_replay_harness.py \
  tests/evaluation/test_career_event_replay.py \
  tests/asof/test_career_event_prediction.py \
  tests/claims/test_duan_runner.py \
  tests/claims/test_ren_binary_career.py -q

42 passed in 26.10s
```

更宽的 `tests/evaluation` 集合在收集阶段被仓库既有环境/缺件阻断：缺少 `engine.evaluation.prospective_capability_identity`，并缺少 `lunar_python`、`sxtwl` 可选依赖。该失败发生在本次改动之外的模块导入阶段，未出现本切片测试失败；因此报告分别记录“核心/扩展通过”和“全 evaluation 未能完成”，不把后者伪装成通过。

覆盖内容包括：

- 结构门阻断旧 timing-only 假阳性；
- 历史和未来共享预测器；
- predictor API 无现实输入；
- blind artifact 不含 labels、source_ref、known facts、feedback、verification 或 observed 字段；
- `predict-freeze` CLI 不打开 labels artifact；
- 无效 freeze 在标签文件打开前失败关闭；
- 投影字段最小化；
- 冻结顺序无关和 hash 防篡改；
- 标签只能在匹配 freeze 后揭示；
- 显式负标签要求；
- 五维评分、FP、FN 与 abstain；
- legacy adapter 与 generic single-model freeze；
- 双模型使用完全相同的真实 case-year cohort；
- development replay 不具 promotion 资格。

---

## 8. Phase 2 验收结论

| 验收项 | 结果 |
|---|---|
| 审计 Phase 1 预测对象真实来源 | 通过 |
| 找出跨案例 Top 3 瓶颈 | 通过 |
| 共享历史/未来事业事件预测器 | 通过 |
| Structure → Event → Timing | 通过 |
| predictor 防现实标签泄漏 | 通过 |
| chart-only / labels 物理 artifact 拆分 | 通过 |
| 预测进程不读取标签文件 | 通过 |
| 冻结校验后才打开标签文件 | 通过 |
| 冻结后揭示 | 通过 |
| 显式 event/no-event 标签 | 通过 |
| 时间/类型/领域/方向/重大性五维评分 | 通过 |
| legacy/shared 同 cohort 比较 | 通过 |
| 核心定向回归 | 27 passed |
| 扩展事业切片回归 | 42 passed |
| 全 evaluation 回归 | 收集阶段被既有缺件/依赖阻断，未伪报通过 |
| 证明正式准确率提升 | **未通过 / 无证据** |
| unseen holdout | **0 案 / none** |
| production promotion | **禁止** |
| Calibration | **未进入** |

**Phase 2 的工程目标已经完成，准确率目标尚未达成。** 当前最可信的证据不是“shared 更准”，而是：结构门消除了一个已知假阳性，同时因规则覆盖过窄造成显著假阴性。下一阶段必须围绕结构资格召回率和方向/事件类型判别能力继续施工，并使用新的隔离开发数据；在获得真实 unseen holdout 前，不得发布正式准确率或生产晋级声明。

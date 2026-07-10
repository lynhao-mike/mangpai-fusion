# 格局判断 · 分层 L0-L9 系统重构结论

> 日期：2026-07-10  
> 输入：[`META/l0-l9-architecture-gap-investigation-2026-07-10.md`](../META/l0-l9-architecture-gap-investigation-2026-07-10.md) 的四缺口调查事实  
> 方法：geju 格局判断（大胆假设，小心求证）  
> 本文是方向结论，不是执行计划；落地拆解交 writing-plans。

---

## 0. Thesis（核心判断）

**四个缺口不是四个独立 bug，而是同一个病的四个部位：DecisionRun 是 v5 算完之后的"事后转录账本"，不是驱动分析的主干。**

一句话：**v5 在推理，L0-L9 在抄写。**

真正给命主看的报告 Markdown 走的是 [`render_report_v6_from_output(output)`](../engine/v5/report_view.py:304) 从 V5Output 直渲染的路径；DecisionRun 是旁边并列的 [`decision_run_from_snapshot(snapshot)`](../engine/decision/v5_adapter.py:300) 派生物。两条路互不消费。所以 L0-L9 分层裁判链**从未真正决定过报告里的任何一句话**。

这与 R1 里发现的"先让流派发言、再反推谁适用"是**同一种倒置**的不同部位：真正的推理在 v5 里发生，分层 stack 只是它的事后转录。

---

## 1. Confidence（置信度）

**高置信度（针对病灶定位）；中置信度（针对根治路径的工程量）。**

高的依据（全部来自调查实证）：

1. 报告与 DecisionRun 并列旁路，见 [`engine/v5/preprod.py:242`](../engine/v5/preprod.py:242)：`report_md` 与 `decision_run` 是两条独立赋值。
2. L4 事件类型硬编码 `"v5_prediction"`，见 [`engine/decision/v5_adapter.py:139`](../engine/decision/v5_adapter.py:139)——事件类型不是推导出来的，是转录时贴的标签。
3. L3 只用 `confidence<=0.1` 才 reject，见 [`engine/decision/l3_structure.py:20`](../engine/decision/l3_structure.py:20)——结构审查没有命局知识，只有阈值。
4. L1 因 `dayun_steps=[]` 无法判 abstain，见 [`engine/decision/v5_adapter.py:64`](../engine/decision/v5_adapter.py:64)——路由拿不到大运，因为 v5 只给了 `dayun_summary` 字符串。

中的原因：根治要动的是"谁是主干"这个架构决策，牵涉 v5 runner、v5_adapter、preprod、report_view 四处，工程量不小；且必须保证 R1-R5 已交付的能力不回退。

---

## 2. The Trap（陷阱）

真正的陷阱不是"四个占位符没填"，而是**以为把四个占位符各自补好，系统就符合设计了**。

| 表象 | 诱导的错误动作 | 为什么错 |
|---|---|---|
| L1 缺 abstain | 去 v5 runner 补 `dayun_steps` 列表 | 治标。补完 L1 能 abstain，但报告仍不消费 L1，学不到"该不该用任派" |
| L3 无 reject | 给 L3 加更多 confidence 阈值规则 | 治标。L3 拿到的是 v5 转录后的 claim，没有原始命局结构，加再多阈值也是拍脑袋 |
| L4 是占位符 | 给 `_events()` 写一个 event_type 映射表 | 治标。事件类型仍是"转录时贴标签"，不是"从结构推导" |
| 报告与 L7 分离 | 让报告模板去读 decision-run.json | 治标且危险。会造出"报告读账本、账本读 v5"的三层转录，更绕 |

**四个治标动作加起来，仍然是"v5 推理 + 事后抄写"，病灶纹丝不动。**

---

## 3. High-格局 Direction（目标模型）

**让 DecisionRun 成为分析主干，v5 各派 runner 降为"L2 命题供应器"。报告只读 L7，L7 只读 L6，逐层向下，直到 L0。**

```text
现状（倒置）：
  v5 runner → V5Output → 报告Markdown（主交付）
                      ↘ decision_run（旁路账本，无人消费）

目标（扶正）：
  L0 事实 → L1 路由 → L2 各派命题（v5 runner 在此供应）
         → L3 结构审查（有真实命局知识，能 reject）
         → L4 事件落地（从通过审查的命题推导具体事件类型）
         → L5 应期 → L6 裁判 → L7 报告视图 → 报告Markdown（主交付）
  报告里每句话都能反查到 L0。
```

关键：**v5 不再是"先算完的引擎"，而是 L2 这一层的实现**。它产出各派独立命题，然后交给 L3 及以上的裁判链。报告渲染从"消费 V5Output"改为"消费 L7 ReportViewItem"。

---

## 4. Frame-Opening Move（开框动作）

**Kill The Wrong Concept：杀掉"v5 是推理引擎、decision 是账本"这个概念。**

反问（Zero-Legacy）：如果今天从零建，会不会让 v5 先算完一整套报告、再另写一套 L0-L9 账本去转录它？不会。会让 v5 各派 runner 直接作为 L2 供应器插进分层链。

这暴露出：**v5_adapter 这个"适配器"本身就是错误概念的化身**——它的存在假设了"v5 输出"和"decision 输入"是两个需要翻译的世界。正确模型里它们是同一个世界的相邻两层，不需要适配器，只需要 L2 直接调用各派 runner。

---

## 5. Bold Takes（大胆判断）

1. **该删的概念**：`v5_adapter.py` 作为"事后转录器"的定位应被删除。它的 `_school_applicability`（R1 已改）、`_events`、`_decisions`、`_report_items` 都是"把 v5 结果翻译成 decision 结构"的转录函数——目标模型里这些应该是各层 runner 自己产出的，不是事后翻译。
2. **该扶正的主干**：报告 Markdown 必须改为消费 L7 ReportViewItem。这是检验"分层是否真的驱动分析"的唯一硬标准。
3. **该下沉的**：v5 的五派 runner（ziping/ditiansui/gao/duan/yang）下沉为 L2 的实现，产出 SchoolClaim，不再产出"完整 V5Output"。
4. **该真做的 L3**：L3 需要真实命局知识（日主旺衰、用神成立、神煞是否孤证），而不是 confidence 阈值。这是唯一一个"不是配管、是真命理逻辑"的缺口，也是最难的。
5. **不保留**：不保留"报告和 DecisionRun 两套平行产物"。长期只能有一个事实主干。

---

## 6. Options（三条路，取舍）

| Option | 描述 | 优点 | 代价 | Verdict |
|---|---|---|---|---|
| A. 补丁四缺口 | 各自填 dayun_steps / L3 阈值 / L4 映射表 / 报告读账本 | 改动小、快 | 病灶不动，四个治标叠加仍是"v5推理+抄写"，且报告读账本更绕 | **Reject** |
| B. 扶正主干（大重构） | v5 runner 下沉为 L2，报告改读 L7，删 v5_adapter 转录，L3 接真实命局审查 | 终态干净，真正符合设计 | 工程量大，牵涉四处，风险高，一次做完易失控 | Not now（作为北极星，不作为下一步） |
| C. 单向扶正切片 | 先只扶正一条：报告 L7 链路。让报告的**一个域**（如事业）改为消费 L7 ReportViewItem，证明"分层能驱动报告"，再逐域迁移 | 最短路径证明主干可扶正；风险局部化；不动 L3 命理逻辑 | 有一段"部分域走 L7、部分域走旧渲染"的双轨期 | **Recommend** |

**结论：目标按 B 定，下一步按 C 走。**

先不碰最难的 L3 真实命局审查，也不一次性删 v5_adapter。先证明"报告能被 L7 驱动"这一条最关键的扶正切片——因为它是"分层是否真的有用"的试金石。如果连一个域都无法让报告改读 L7，那 B 就是空想。

---

## 7. What Not To Do（明确不做）

1. 不去 v5 runner 补 `dayun_steps` 当作"修好了 L1"——那只是让旁路账本更好看，报告仍不消费它。
2. 不让报告模板直接读 decision-run.json——那是"报告读账本、账本读 v5"的三层转录，比现在更绕。
3. 不在这一步碰 L3 真实命局审查——它是真命理逻辑，需要独立的知识建模，不该和"扶正主干"的配管工作混在一起。
4. 不一次性删 v5_adapter——它还在支撑 R1-R5 已交付的能力，必须等报告 L7 链路证明可行后再逐步降级。
5. 不为了"看起来完整"去填 L4 event_type 映射表——事件类型必须从结构推导，映射表是另一个占位符。

---

## 8. First Proof Point（第一证明物）

**让 C-2026-035 报告的"事业"域，改为消费 L7 ReportViewItem 渲染，而不是从 V5Output 直渲染。**

最小验收：

1. 报告"事业"域的裁决结论文本，来自某条 `report_items[*].display_text`。
2. 该 report_item 能反查到 L6 decision → L4 event → L3 verdict → L2 claim → L1 applicability → L0 chart（`validate_trace()` 已保证链路，这里验证报告文本确实取自链路末端）。
3. 其余五个域暂时保持旧渲染（双轨期）。
4. 报告里"事业"域出现的结论，与 decision-run.json 里事业 decision 的裁决**文本一致**（证明不是两套说法）。

如果事业域能被 L7 驱动且结论一致，方向 C→B 成立。

---

## 9. Falsifier（证伪口径）

1. **如果报告"事业"域改读 L7 后，L7 ReportViewItem 的 display_text 信息量远不如旧 V5Output 渲染**（比如只有一句"事业 winner"，没有五派依据、15 层判断），说明 L7 ViewModel 太贫瘠，扶正主干前必须先让 L6→L7 携带足够信息——这会把工程量推回 B，需重新评估。
2. **如果发现 L3/L4 因为拿不到 v5 中间结构（旺衰、用神、做功路径）而根本无法产出有信息量的 verdict/event**，则证明"v5 runner 下沉为 L2"不是简单下沉，而是要 v5 把中间结构也暴露出来——这是比预期大的改动，方向 B 的代价被低估。
3. **如果双轨期两套渲染对同一域给出矛盾结论**，说明 V5Output 和 DecisionRun 已经语义漂移，扶正前必须先对齐语义。

---

## 10. 给决策者的一句话

现在的系统是"v5 认真推理，L0-L9 在旁边记流水账，命主看的是 v5 的账，不是分层裁判的账"。四个缺口都是这个倒置的症状。

不要逐个补症状。先做一件事证明分层能翻身当家：**让一个域的报告改读 L7**。这条切片成立，才谈得上把 v5 runner 下沉为 L2、把报告主干交给分层链。

**下一步**：若你认可方向 C，切到 writing-plans 把"事业域报告改读 L7 的最小切片"拆成 bite-sized TDD 任务。此文只钉方向。

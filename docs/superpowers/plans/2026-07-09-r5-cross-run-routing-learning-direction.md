# R5 方向决策：跨 run 流派路由学习（格局判断）

> 本文是**方向决策文档**，不是代码执行计划。目的：在写任何 R5 代码前，用 geju 把"跨 run 学习如何改变未来路由"这个架构岔路口讲透，给出取舍与证伪口径，再决定实现路线。
>
> 事实源：[`tools/feedback_loop.py`](../../../tools/feedback_loop.py)、[`tools/rule_lifecycle.py`](../../../tools/rule_lifecycle.py)、[`engine/decision/l1_school_router.py`](../../../engine/decision/l1_school_router.py)、[`engine/decision/l9_calibration.py`](../../../engine/decision/l9_calibration.py)、[`plans/layered-decision-system.md`](../../../plans/layered-decision-system.md)。
> 承接：R1（路由前置）、R2（结构信号路由）、R3（失验回打责任流派）、R4（分层准确率看板）均已交付。

---

## 0. 这是一个决策，不是一个任务

R1-R4 是架构 §18 明确定义的四阶段闭环，已全部交付。**§18 到 R4 为止，没有预定义的 R5。** 再往下是四份计划都反复显式延后的同一块：**跨 run 学习、真正改变未来路由**。

它不能机械续写，因为它触及一个真实架构决策：仓库**已经有**一套成熟的跨 case 学习机器在为规则运行。R5 的第一个问题不是"怎么写"，而是"**复用它，还是新建一套**"。选错方向会直接违反本次重构一路坚持的纪律——不建并行系统。

---

## 1. Thesis（核心判断）

**R5 不应新建"流派画像学习子系统"。流派适用性（school × domain × role → 准不准）应当被建模成 feedback_loop 已有生命周期机器里的一种"可学习对象"，复用 Beta 后验 + 升降级 + 滑动窗，而不是另起炉灶。**

一句话：**学习机器已经有了，R5 要做的是把"流派路由"喂进去，不是再造一台。**

决定性证据：[`DomainRoleStats`](../../../tools/rule_lifecycle.py:245) 已经存在——它是"同一对象在不同 (domain, role) 下各自独立记 hits/misses/recent_5/confidence_cache 的 Beta 账本"。"某派在某域某角色下到底准不准"需要的抽象，**这台机器已经具备**，只是目前只喂了"规律"，没喂"流派路由"。

---

## 2. Confidence（置信度）

**中高置信度（针对"复用而非新建"这个方向）；中置信度（针对具体接入形态）。**

高的部分：

1. [`DomainRoleStats`](../../../tools/rule_lifecycle.py:245)、[`beta_posterior()`](../../../tools/rule_lifecycle.py:124)、[`maybe_upgrade`/`maybe_downgrade`](../../../tools/rule_lifecycle.py:428) 的抽象与"流派适用性学习"高度同构：都是"对象 × 上下文 → 命中率 → 升降级"。
2. R3 已经把失验精确定位到"责任流派"，产出 `target_type="router"、target_id=流派名` 的校准信号——学习的**输入端已就绪**。
3. R2 的 [`route_schools()`](../../../engine/decision/l1_school_router.py:52) 是纯规则打分，天然留了"再叠加一个学习到的先验/调整量"的位置——学习的**输出端有落点**。

不判高的部分：

1. feedback_loop 现在的键是 `rule_id`（挂在 `theory/{school}/index.yaml` 的规律上）。"流派路由"没有天然的 rule_id 宿主，需要决定它挂在哪、以什么 id 记账。
2. 学习到的"流派适用性画像"如何回灌 route_schools，涉及 engine（纯函数、无 IO）与 tools（有文件 IO）的分层边界——接错会让 [`route_schools()`](../../../engine/decision/l1_school_router.py:52) 变成有 IO 副作用的非纯函数，破坏 R1-R4 的可测性。

---

## 3. The Trap（陷阱）

真正的陷阱不是"没有学习能力"，而是**误以为要新建一套学习系统**。

| 继承形态 | 表象 | 是否真实约束 | 判断 |
|---|---|---|---|
| feedback_loop 只认 rule_id | 似乎流派路由无处安放，得新建 | 不真实 | `DomainRoleStats` 已是"对象×上下文"通用账本；缺的是宿主键约定，不是新机器。 |
| route_schools 是纯函数 | 似乎要让它直接读学习结果 | 部分真实 | 纯函数不该做 IO；学习先验应作为**入参注入**，而不是让 route_schools 自己去读文件。 |
| R3 信号 run 后即弃 | 似乎必须马上建持久化 | 真实但要克制 | 需要持久化，但应复用 feedback_loop 的落盘路径，不新造 JSON 存储层。 |
| "流派画像"听起来是新概念 | 似乎值得一个新模块 | 不真实 | 它就是"school-domain-role 维度的 DomainRoleStats"，是既有概念的新实例，不是新概念。 |

**最大的坑**：为了"干净"，新写一个 `school_profile_store.py` + 一套自己的 Beta + 自己的升降级阈值。这会造出与 feedback_loop 语义重叠、阈值可能漂移、且要单独维护的并行学习系统——正是 geju/ponytail 要杀死的东西。

---

## 4. High-格局 Direction（目标模型）

```text
反馈(miss/hit)
  → R3 定位责任流派 (school, domain, role)
  → 作为一种 DomainRoleStats 记账对象，喂进 feedback_loop 既有生命周期
  → Beta 后验 + 升降级 产出"流派适用性画像"（school×domain×role 的置信/状态）
  → 画像作为先验，在 route_schools 调用时【注入】，微调打分与角色
  → 分层准确率看板(R4)观测：注入学习先验后，L1 routing accuracy 是否上升
```

关键设计原则（非协商项）：

1. **一台学习机器**：流派路由学习复用 feedback_loop 的 Beta + 升降级 + 滑动窗，不新建平行 Beta。
2. **route_schools 保持纯函数**：学习先验以**入参**注入（如 `route_schools(chart, context, *, learned_prior=None)`），默认 None 时行为与 R2 完全一致；读盘由 tools 层完成，engine 层不做 IO。
3. **持久化复用既有落盘**：流派画像落在 feedback_loop 已有的落盘体系内，不新造独立存储格式。
4. **可回退**：learned_prior 为空即退回纯规则路由，保证 R1-R4 所有测试不依赖学习数据。

---

## 5. Frame-Opening Move（用了哪个开框动作）

**Kill The Wrong Concept + Zero-Legacy 反问。**

反问："如果今天从零建流派路由学习，会不会新写一个 Beta 记账器？" 答案是不会——因为 [`DomainRoleStats`](../../../tools/rule_lifecycle.py:245) 已经是"对象×(domain,role)→独立 Beta 账本"的通用形状。这暴露出："流派画像"不是新概念，而是既有 `DomainRoleStats` 抽象的一个**新实例**。要 kill 的错误概念是"流派画像需要一套自己的学习系统"。

---

## 6. Bold Takes（大胆判断）

1. **该删的念头**：删掉"新建 school_profile 学习子系统"的设想。
2. **该合并的**：把"流派适用性学习"合并进 feedback_loop 的 DomainRoleStats 生命周期，作为一类记账对象。
3. **该拆分的**：拆开"学习"（tools 层，有 IO、有持久化）与"应用学习结果"（engine 层，纯函数、先验入参注入）——这条边界是 R5 不破坏 R1-R4 可测性的关键。
4. **不保留**：不保留"route_schools 自己去读画像文件"的任何设计——那会让纯函数带上隐藏 IO 副作用。

---

## 7. Options（三条路，取舍）

| Option | 描述 | 优点 | 代价 | Verdict |
|---|---|---|---|---|
| A. 复用 feedback_loop（学习）+ 先验注入（应用） | 流派适用性作为 DomainRoleStats 类对象进既有生命周期；route_schools 加可选 `learned_prior` 入参 | 一台学习机器、不违反不建并行系统、route_schools 保持纯函数可回退 | 需定义"流派路由"在 feedback_loop 里的宿主键与落盘位置 | **推荐** |
| B. 新建最小流派画像 JSON 存储 + route_schools 启动读回 | 独立 school-profile store，路由启动读学到的角色偏置 | 闭环最直观、改动局部 | 造并行学习系统、阈值易漂移、route_schools 变非纯函数、与 feedback_loop 语义重叠 | Reject |
| C. 停在 R4，不做跨 run 学习 | 等真实反馈样本积累再启动 | 零新代码、零误建风险 | 闭环停在"能观测、不能自我改进" | 数据不足时的合理默认，但不是终态 |

**结论：选 A。** 目标模型按 A 定；若短期真实反馈样本不足以驱动升降级，可先按 C 停在观测态，但**不要**用 B 抄近路——B 的技术债（并行学习系统）比它省下的工期贵得多。

---

## 8. What Not To Do（明确不做）

1. 不新写平行的 Beta / 升降级 / 滑动窗；复用 [`rule_lifecycle.py`](../../../tools/rule_lifecycle.py)。
2. 不让 [`route_schools()`](../../../engine/decision/l1_school_router.py:52) 读文件；学习先验只能作为入参注入。
3. 不新造独立的流派画像存储格式；复用 feedback_loop 落盘体系。
4. 不在真实反馈样本不足时假装学习已生效——那会让 R4 看板显示虚假的"路由准确率提升"。
5. 不改 R1-R4 已交付的行为；learned_prior 缺省时必须逐字回退到 R2 纯规则路由。

---

## 9. First Proof Point（最小证明物）

> 状态：已落地。route_schools(chart, context, *, learned_prior=None) 已实现，缺省零回归、合成低命中先验能下调对应流派，见 tests/test_l1_learned_prior.py 与执行计划 docs/superpowers/plans/2026-07-09-r5-learned-prior-injection-refactor.md。R5-B（真实反馈聚合 + 持久化回灌）待启动。

**不是"跑通完整学习"，而是证明"注入学习先验能改变路由、且缺省时零影响"。**

最小切片（未来 R5 实现计划的验收锚点）：

1. 给 [`route_schools()`](../../../engine/decision/l1_school_router.py:52) 加可选入参 `learned_prior`（默认 None）。
2. `learned_prior=None` 时，输出与当前 R2 逐字一致（用现有 [`tests/test_l1_structural_signals.py`](../../../tests/test_l1_structural_signals.py) 全绿证明零回归）。
3. 构造一个"某派在某域历史命中率极低"的合成先验，注入后该派在该域的 role 被下调（如 co_lead→evidence_only），score 下降。
4. 该先验的数据结构直接复用 [`DomainRoleStats`](../../../tools/rule_lifecycle.py:245) 的 hit_rate / confidence，不新造。

若这个切片成立：说明"复用既有学习对象 + 先验注入"方向可行，再谈把 feedback_loop 的落盘接上。

---

## 10. Falsifier（什么情况说明方向错了）

1. **如果 `DomainRoleStats` 无法承载 school×domain×role**（例如它硬绑 rule_id 语义、拆不出来复用），则 Thesis 的"复用"前提被推翻，需要重新评估是否真的得新建——回到 §7 重判 A vs B。
2. **如果先验注入后，route_schools 无论如何都无法在缺省时逐字回退**（例如签名改动被迫波及所有调用方并改变默认行为），则"不破坏 R1-R4"的原则守不住，方向需调整。
3. **如果真实反馈样本长期不足以让任何流派跨过升降级阈值**，则 R5 的"自我改进"在现实中不发生——此时应诚实停在 C（观测态），而不是调低阈值制造虚假学习。
4. **如果注入学习先验后 R4 看板的 L1 routing accuracy 不升反降**，说明"用历史命中率当未来路由先验"这个假设本身有问题，需回到 §1 重判，而不是继续加权重。

---

## 11. 给决策者的一句话总结

学习机器已经存在（feedback_loop + DomainRoleStats + Beta 生命周期），R3 已经把失验定位到责任流派，R4 已经能观测分层准确率。R5 的正确动作是**把流派路由喂进已有的学习机器、并以先验入参的方式回灌纯函数路由**，而不是新建一套并行的流派画像学习系统。若真实反馈样本暂时不足，宁可停在"能观测"的 R4 态，也不要用抄近路的并行存储制造技术债。

决定"选 A 并开始写 R5 执行计划"后，再进入 writing-plans 阶段拆 bite-sized 任务；在此之前，本文只负责把方向钉死。

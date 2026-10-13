# as-of 下一长任务候选 · geju 格局裁决（2026-07-28）

> 状态：裁决记录，不是实现合同；本文件本身不授权任何实现。
> 触发场景：阶段 B（本地仓库调研 + 下一长任务提示词生成协议）已完成候选池整理，初步候选为"婚姻域 as-of G0-G5 原型"；用户要求用 [`geju`](../.roo/skills/geju/SKILL.md) skill 重新审视该方向，产生本裁决。
> 直接产物：[`plans/as-of-life-state-blind-judgment-first-proof-point-kickoff-prompt.md`](as-of-life-state-blind-judgment-first-proof-point-kickoff-prompt.md)（最终选定长任务的执行提示词）。

## 1. 裁决结论

**婚姻域 as-of G0-G5 未被采纳。** 改为更高杠杆方向：**as-of 真实盲断闭环 First Proof Point**——用一个从未被任何 as-of 工作触碰过的案例，严格执行"先冻结盲断、后揭示核验"两阶段协议，产出项目历史上第一份关于"as-of 推理本身是否真的能盲断准确"的证据。

## 2. Thesis

"填补 [`future_projection.py`](../engine/asof/future_projection.py:295) 里婚姻域的 `NOT_IMPLEMENTED`"是一个被代码占位形状引诱出来的局部优化，不是项目真正卡住的地方。真正的缺口不是"as-of 还差几个领域"，而是 as-of 从 Unit8 到 G9-P1 的全部证据都是"历史回放"（答案已知再验证内部一致性），从未做过一次真正意义上的盲断—冻结—揭示—评分。同时项目里已存在解决"如何不泄底"的成熟基础设施（[`tools/school_capability_prospective.py`](../tools/school_capability_prospective.py) 的 blind-bundle 隔离协议），但从未接到 as-of 引擎上。

## 3. Confidence

- **等级**：medium-high
- **不确定的原因**：真正的盲评闭环需要一个"没看过 feedback.md"的干净上下文；本轮调研过程中已经大范围检索了仓库案例，可能已经"污染"了不少候选案例的背景认知，限制了"就地验证"的即时可行性——这也是最终提示词里必须显式设计案例排除清单与污染检测步骤的原因。

## 4. The Trap（继承来的约束）

- **继承来的约束**：`engine/asof/future_projection.py:295-297` 明确列出 `family/education/marriage/health` 四个 `NOT_IMPLEMENTED`；案例池里确实存在婚姻事件链条完整的案例（`C-2026-018`、`C-2026-012` 等）。代码形状本身在暗示"下一个该做的是选一个填上"。
- **Is it real?**：partially。案例池和代码占位是真的，但"填占位=正确下一步"是假的——这只是把 G0-G9 已验证过的同一套方法论（历史回放）在第三个领域上再跑一遍，不产生新的认识论证据。
- **Why**：[`AGENTS.md`](../AGENTS.md:6) 明确写着现有生产 pipeline"从未在'不知道答案'的条件下被测试过盲断准确率"，这句话对 as-of 同样成立——Unit8-11 每份报告都自我声明"不得推导：本轮不证明命理预测准确率"。加婚姻域不会解除这个免责声明，加了照样还得写同一句话。

## 5. High-格局 Direction

as-of 引擎和 prospective-go 的盲评隔离协议应该是**同一套盲评基础设施的两个可插拔引擎**（静态五派 runner / as-of 状态机），而不是两条永不相交的治理轨道。下一步不是"选一个新领域喂给 as-of"，而是"把 as-of 接到已经解决了泄底问题的现成盲评管线上，产出这个项目历史上第一份真正的盲断—核验闭环证据"。

## 6. Frame-Opening Move

- **使用的打法**：kill the wrong concept + 十倍问题
- **揭示的洞察**：把"再做 10 个领域切片"当作十倍放大的思想实验——10 份历史回放依然是 0 份盲断准确率证据，说明领域覆盖广度不是当前的杠杆所在。同时"kill"揭示了一个更具体的问题：Unit8-11 报告里反复出现的"盲断"（[`consultation_freeze.py`](../engine/asof/consultation_freeze.py)）其实是人工手写的 dataclass fixture，构造者本来就知道 `feedback.md` 里写了什么——这不是设计文档 §9 说的"命理师现场表达"，是伪盲断。真正的盲评隔离机制（[`tools/school_capability_prospective.py`](../tools/school_capability_prospective.py) 的 `prepare-single-case-blind`/`stage-frozen-run`）项目里早就有，但只喂给了静态 runner。两条轨道从未合流，这才是该杀的错误假设——"as-of 的盲断不需要借用既有隔离机制，自己手写 fixture 就够了"。

## 7. Bold Takes

- Unit8-11 的"盲断"命名本身是误导性的：它们证明的是"会话制品化"，不是"盲断"。报告自己也这么说，只是没人把这个当作下一步的输入。
- 婚姻域现在不该加。加了只是第 3 个"内部一致性证明"，边际价值递减，而且会让"我们从未测试过盲断准确率"这句免责声明继续原样躺在下一份报告里。
- 项目里存在**两套独立发明的盲评/冻结机制**：`engine/asof/consultation_freeze.py`（as-of 专用）和 `tools/school_capability_prospective.py` 的 blind-bundle 协议（五派专用）。这是该合并/该让 as-of 复用后者的信号，不是"两个领域各自有一套很正常"。
- `P-GO-2026-001` 这个项目唯一的真实 prospective 案例，用的分析引擎是静态五派 runner，不是 as-of——这意味着这个项目目前投入最大治理成本的那条"真盲评"轨道，恰恰没有验证 `AGENTS.md` 认为最该验证的那套推理系统。

## 8. Options

| Option | 优化目标 | 代价 | 裁决 |
|---|---|---|---|
| 保守路线：婚姻域 as-of G0-G5（原方案） | 领域覆盖广度、复用已验证的 Gate 流程 | 低风险，但产出仍是"历史回放"，不解除任何免责声明 | reject——不产生新证据类型 |
| 干净目标：给 as-of 接上既有 blind-bundle 隔离协议，跑通一次真正盲断→冻结→揭示→评分闭环 | 直接回应 `AGENTS.md` 点名的认识论缺口，产生项目历史上第一份盲断准确率证据 | 需要设计"as-of 引擎作为 blind-bundle 消费者"的适配层；需要干净上下文避免污染 | recommended（中长期） |
| 分阶段：先用现有事业域（已实现，零新代码）+ 一个未被本轮调研污染的案例，手工模拟隔离（先写盲断到磁盘，再读 feedback），验证"是否可行" | 用最小成本先验证方向本身可行，再决定是否值得做适配层 | 仍是单案例，样本量小；隔离靠流程自律而非机制强制 | **已采纳**，作为 First Proof Point |

## 9. What Not To Do

- 不要因为代码里有 `NOT_IMPLEMENTED` 占位就把"填占位"当成任务；占位的存在不等于它是当前最高杠杆的工作。
- 不要用"再写一份 fixture，构造者已经知道答案，但起个名字叫'盲断'"的方式伪造盲评证据——Unit8-11 已经这么做过三次，报告已经自曝这不算数，不要做第四次。
- 不要在还没解决"agent 如何避免看到 feedback.md"这个具体机制问题之前，就贸然设计一个"承诺不看"的软性隔离——本轮调研本身就已经证明这种自律不可靠（Stage A 广泛检索时已读到多个案例的 feedback 内容）。

## 10. First Proof Point（已采纳，见配套 kickoff prompt）

选一个本轮调研没有读取过 feedback 内容的真实案例，用现有 `engine/asof` 事业域能力，在同一受控流程内严格分两步执行且落盘留痕：① 只读 `input.md` + 指定 `as_of_date`，构造原局承载图/大运阶段/事件候选并冻结写入磁盘（不打开 `feedback.md`）；② 冻结完成后才打开 `feedback.md`，构造核验输入跑完整 `run_career_session`，比较"盲断候选"与"实际核验结果"的吻合度。完整执行细节见 [`plans/as-of-life-state-blind-judgment-first-proof-point-kickoff-prompt.md`](as-of-life-state-blind-judgment-first-proof-point-kickoff-prompt.md)。

## 11. Falsifier

如果尝试后发现：agent 在"冻结阶段"事实上无法排除对该案例任何背景信息的先验知识（例如该案例此前已被别的会话分析过、或案例本身在仓库检索中大量出现过），那么"就地手工隔离"这条路不可行，必须退回到 Options 表中的"干净目标"——正式借用 blind-bundle 协议的目录级隔离机制，而不是流程自律。如果连这样都做不到干净盲断，说明当前 agent 架构下"真正盲断证据"本身就需要更大的基础设施投入，这本身就是一个值得单独立项的发现。

## 12. Payoff Ledger

| Move | 现在付出的代价 | 换来什么 | 收益兑现的信号 |
|---|---|---|---|
| 放弃"婚姻域 G0-G5"作为下一步 | 放弃一个已规划好、风险低、马上能出 evidence-bounded freeze 报告的任务 | 避免第三次产出"我们仍未证明盲断准确率"的免责声明报告，把治理精力从广度切换到项目自己点名的核心缺口 | 立刻——下一份报告不再需要重复同一句免责声明 |
| 设计"as-of 盲断隔离验证"作为 First Proof Point | 需要重新设计验证流程（不能照抄 Unit8-11 的 fixture 写法），且必须先核实候选案例未被本轮会话污染 | 项目历史上第一份关于"as-of 推理是否真的能盲断准确"的证据，直接回应 `AGENTS.md` 最高优先级里"从未测试盲断准确率"的缺口 | 该单案例验证完成、拿到吻合度结果的那一刻 |
| （中期，未授权）把 as-of 接到 `school_capability_prospective` 的 blind-bundle 隔离协议 | 需要新写一个适配层，让 as-of 成为该协议的第二个可插拔引擎；工程量比单案例手工验证更大 | 消除"两套独立发明的盲评机制永不相交"的架构裂缝，让 as-of 未来能用项目已投入大量治理成本建好的隔离/审计/cohort 基础设施 | 当第一个 as-of 驱动的 prospective 案例走完 intake→blind-bundle→frozen-run 全链路时 |

## 13. 不得推导

- 本裁决不构成"婚姻域 as-of 永久不做"的结论；只是本轮判断它当前杠杆低于盲断闭环验证，未来若 First Proof Point 完成且证明方向站得住，婚姻域仍可作为后续领域扩展候选之一。
- 本裁决不授权"接入 blind-bundle 协议"这个中期干净目标的实现；该项仍需用户在看到 First Proof Point 结果后另行明确授权。
- 本裁决不改变任何既有 as-of Unit8-11、G0-G9 系列的冻结结论。

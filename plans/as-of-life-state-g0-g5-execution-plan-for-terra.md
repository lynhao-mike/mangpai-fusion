# 原局—大运—流年—截止状态推理系统 · G0-G5 首个原型执行计划（terra 专用 · 修订版）

> 状态：READY，尚未启动
> 原始版本由 GPT-5.6 产出；本版由 Claude Opus 修订，补充预审结论、风险登记与可执行命令
> 设计事实源：[`as-of-life-state-reasoning-design-2026-07-18.md`](as-of-life-state-reasoning-design-2026-07-18.md)
> 审计事实源：[`../reports/as-of-life-state-reasoning-audit-2026-07-26.md`](../reports/as-of-life-state-reasoning-audit-2026-07-26.md)
> 范围：**只到 G5**（历史回放验证 + 生产隔离）；G6 需另行独立授权
> 写集：只新增 `engine/asof/` 与 `tests/asof/`，不修改任何现有文件

---

## 0. 强制先读顺序

1. [`AGENTS.md`](../AGENTS.md)
2. 本文件全文（含 §1 纪律、§6 风险登记）
3. [`as-of-life-state-reasoning-design-2026-07-18.md`](as-of-life-state-reasoning-design-2026-07-18.md) 全文 —— **唯一业务语义事实源**，不得重新解释或简化冻结条款
4. [`../reports/as-of-life-state-reasoning-audit-2026-07-26.md`](../reports/as-of-life-state-reasoning-audit-2026-07-26.md) —— 特别注意 §2.2（字段缺口）、§2.5（pre-existing failures）、§2.6（案例预审）

只读参考（**禁止修改**）：
- [`../engine/yingqi/retrospective.py`](../engine/yingqi/retrospective.py) —— 信号来源，非最终对象
- [`../tests/ziping_career/`](../tests/ziping_career/)、[`../tests/ren_timing/`](../tests/ren_timing/) —— 判别层素材与隔离测试写法范本
- [`../engine/f09/`](../engine/f09/) —— **架构模式**参考；字段与数据模型不可复用，命名不得冲突

---

## 1. 硬性纪律（贯穿 G0-G5）

1. **加法禁令**：任何裁决点禁止用分数加权求和代替证据门/状态机裁决（设计 §3.6、§6.7）。
2. **双轨物理分离**：命理结构轨与现实状态轨必须是两个**独立的 dataclass**，不得合并为单一可变对象再用字段区分（设计 §3.3）。
3. **根源不可回填**：现实履历、事件后果、岁运完成方式、置信度均不得反向抬升原局根源等级（设计 §3.5、§6.4）。
4. **跨域零默认传播**：财富状态变化只能由 §11.2 显式传播边触发；任何隐式联动都是缺陷。
5. **生产零改动**：不修改 `engine/application/`、`engine/decision/`、`engine/yingqi/`、任何 production loader、任何默认 registry。新增代码只允许落在 `engine/asof/` 与 `tests/asof/`。
6. **范围锁定**：仅设计 §11 首个原型——主领域事业（§11.1 七类事件的子集），财富仅作显式传播领域（§11.2）。不做其余五大基本面，不做统计学习层（设计 §14）。
7. **单案深耕**：G0-G5 全程只用**一个**案例打穿，不摊薄到多案例浅尝。
8. **命名防冲突**：`DaiyunContext` 与既有 `DaiyunSegment`（`retrospective.py:76`）语义相近。G0 必须裁定最终命名（建议 `DaiyunStage` 或保留 `DaiyunContext` 但在 docstring 明确与 `DaiyunSegment` 的区别），并在所有后续 Gate 保持一致。
9. **每 Gate 独立 evidence-bounded freeze**：必须运行该 Gate 的 focused pytest 并记录真实 passed 计数与退出码；不得凭代码审查或散文声称通过。
10. **失败即停**：若必须修改设计文档冻结条款或生产代码才能推进，立即停止该 Gate 并写明冲突点。
11. **GitHub 永久禁止**：不 push、不建 PR/Issue/Release。LOCAL ONLY / NOT PUSHED。

---

## 2. 子任务与自主推进协议

允许在同一对话内将 G0-G5 拆为子任务，每个子任务消息必须明确：`任务目标 / 允许读取范围 / 允许写入文件清单 / 完成条件 / 失败返回条件`。

**不得在每一步都停下等待确认。** 仅以下四种情况必须停止并请求用户输入：

| 停止条件 | 判定标准 |
|---|---|
| 需修改设计文档冻结条款 | 设计条款与实现存在不可调和矛盾 |
| 需修改任何现有生产文件 | `git diff --name-only` 对生产目录有非空输出 |
| 出现第 3 个及以上全仓失败 | 已知 2 个 pre-existing failures 见审计 §2.5，**不计入** |
| G5 完成后是否进入 G6 | 需新独立授权，不可从 G0-G5 继承 |

每个 Gate 完成后必须**落盘**更新 `reports/as-of-life-state-career-wealth-slice-g0-g5-verification.md`（增量追加），不得只在对话里口头总结。

---

## 3. G0 案例选择（已预审，可直接采用）

审计 §2.6 已完成案例池预审。**建议直接采用 `C-2026-028-乾-壬戌癸卯壬子乙巳`**：

- `input.md`、`feedback.md`、`statement_index.json` 均存在；
- 已核验事业事件三个：2020 年校分拆兼任两校校长、2022 年晋升正股级、2025 年调任较大初中并兼任原初中校长；
- 可设置至少三个 `as_of_date` 截止点：2019（无职务）/ 2021（兼任双校）/ 2025 后（调任）；
- 覆盖设计 §11.1 中的「升迁或职责层级显著变化」与「工作地点迁移并改变职业路径」两类事件。

备选：`C-2026-024-坤-己巳壬申辛亥壬辰`、`C-2026-022-坤-癸亥庚申戊寅己未`（同样通过三条件核验，详见审计 §2.6）。

若 terra 复核发现 C-2026-028 的 `input.md` 排盘信息不足以构造原局承载图，切换至备选案例，**不得降低三条件标准**。

---

## 4. Gate 定义（按优先级顺序执行，不得跳跃）

### G0 · 规格与案例冻结 · 优先级 P0

**目标**：冻结案例、最小对象字段子集、事件类型白名单、`as_of_date` 输入契约、命名方案。

**必须产出的五项裁定**：
1. 选定案例 + 选择理由（对照三条件逐条核验）；
2. `NatalCapacityGraph` 最小字段子集（仅事业域所需，逐条标注"本次启用/不启用"，对照设计 §5.1）；
3. `DaiyunContext`（或裁定后的新名）最小字段子集，对照设计 §5.2，并说明与既有 `DaiyunSegment` 的语义区别；
4. **`as_of_date` 输入契约**：明确它是新建 request dataclass 的必填字段（推荐）还是函数入参；必须禁止默认值与隐式读取系统当前日期（设计 §9）；
5. 根源 × 完成方式白名单——直接采用设计 §6.6 已登记的六个组合，不得新增。

**产物**：`plans/as-of-life-state-prototype-spec.md`

**完成条件**：五项裁定齐备，且字段清单逐条对照设计文档标注启用状态，无遗漏。

**STOP**：三条件均不满足的案例池耗尽 → 停止并报告，不降低条件。

---

### G1 · 纯判别层（原局承载图 + 大运上下文）· 优先级 P0

**目标**：构造纯函数式的原局承载图与大运上下文，零副作用、零事件判定。

**实施要点（依据审计 §2.2）**：`retrospective.py` 的 `feature`/`domains` 是自由文本，**不能直接映射**为设计要求的结构化路径集合。必须在 `engine/asof/` 内新建适配函数，把既有对象当**信号源**消费，输出全新结构。禁止继承或修改既有类。

**产物**：`engine/asof/__init__.py`、`engine/asof/natal_capacity.py`、`engine/asof/daiyun_context.py`、`tests/asof/__init__.py`、`tests/asof/test_natal_capacity.py`、`tests/asof/test_daiyun_context.py`

**完成条件**：
- 确定性：同一输入重复调用逐字段相等；
- 可追溯：每个字段能追溯到具体命盘事实或既有模块产出，无无来源字段。

**验证命令**：
```
python -m pytest tests/asof/test_natal_capacity.py tests/asof/test_daiyun_context.py -q
```

**STOP**：若必须修改 `engine/yingqi/` 函数签名 → 停止，改为在 `engine/asof/` 内新增适配函数。

---

### G2 · 事件候选与证据门 · 优先级 P0

**目标**：实现 `AnnualInteractionTrace`、`LifeEventCandidate`，及设计 §6.4-6.6 的根源分级与五种完成方式判定。

**完成条件**：
- 设计 §6.6 六个白名单组合各有至少一个通过的测试用例；
- 非白名单组合（如 `NO_ROOT + ACTIVATE_EXISTING`）在测试中断言为**逻辑拒绝**，不生成候选；
- 任意根源 + `INVALID_COMPLETION` 断言不生成目标主事件；
- 双证据门：每个候选可追溯到命盘结构证据 + 可定位语料引用（可沿用 [`theory/`](../theory/) 既有索引，不要求撰写新语料）。

**产物**：`engine/asof/event_candidate.py`、`tests/asof/test_event_candidate.py`

**验证命令**：
```
python -m pytest tests/asof/test_event_candidate.py -q
```

**STOP**：案例事件无法在六个白名单组合内定位根源 → 弃权登记为 `WITHHELD` 并记录缺口，**不得自行扩大白名单**。

---

### G3 · 双轨状态机 · 优先级 P0 · ⚠️ 最高复杂度 Gate

**目标**：实现 `EventImpactAssessment`（四级影响度 × 持续时间 × 影响范围 × 根源性 × 完成方式 → 裁决框架，**非加权求和**）、`VerifiedState`、`HypothesisState`，双轨物理分离。

**完成条件**（对应设计 §12.3、§12.4、§12.7）：
| 测试 | 断言 |
|---|---|
| 候选污染测试 | 未核验/已否定事件不出现在 `VerifiedState` 任一字段 |
| 持续期测试 | 显著临时状态超有效期后失效；本运持续状态换运时重新评估 |
| 冻结审计测试 | `practitioner_final_*` 不覆盖/不删除 `system_suggested_*`，两者同时可读 |

**产物**：`engine/asof/structural_track.py`、`engine/asof/reality_track.py`、`engine/asof/state_ledger.py`、`tests/asof/test_state_ledger.py`

**验证命令**：
```
python -m pytest tests/asof/test_state_ledger.py -q
```

**预期难点**：单案例真实数据大概率无法触发"持续期失效"与"换运重新评估"全部路径。允许构造合成边界测试（tests-only，不写入 `cases/`），但产物文档必须逐条标注"合成边界用例，非该案例真实历史"。

---

### G4 · 跨域传播边（财富）+ 现实落点转译 · 优先级 P1

**目标**：实现设计 §11.2 至少两条显式传播边，以及 §7.4-7.5 的现实落点转译与 `TAXONOMY_GAP` 机制。

**预告（依据审计 §2.6）**：推荐案例 C-2026-028 的 `feedback.md` **无财富事件反馈**。G4 应预期以合成传播边为主，并在产物文档明确标注。这是预期结果，不是缺陷。

**完成条件**（对应设计 §12.5、§12.6）：
- 无显式传播边时财富状态不自动变化；
- 传播条件不满足时不更新目标领域；
- 分支爆炸：内部可保留完整候选树，最终输出合格条件分支 ≤ 2（设计 §8.1、§15.11）；
- 落点转译：核验后新增落点不得计作本次命中；未覆盖但同域同方向的结果登记为 `TAXONOMY_GAP`。

**产物**：`engine/asof/wealth_propagation.py`、`engine/asof/reality_translation.py`、`tests/asof/test_wealth_propagation.py`、`tests/asof/test_reality_translation.py`

**验证命令**：
```
python -m pytest tests/asof/test_wealth_propagation.py tests/asof/test_reality_translation.py -q
```

---

### G5 · 历史回放验证 + 生产隔离 · 优先级 P0

**目标**：证明同一命盘不同 `as_of_date` 生成不同事实快照，且对生产默认路径零影响。

**完成条件**：
1. **历史回放**：至少两个 `as_of_date`（分别早于/晚于核验事件）产生**不同**的 `VerifiedState`；断言系统未读取截止日之后的事实（设计 §9）；
2. **生产隔离**（镜像 [`tests/ziping_career/test_production_isolation.py`](../tests/ziping_career/test_production_isolation.py) 写法）：
   - 默认 runner registry digest 未变化；
   - 正式 pipeline 签名未变化；
   - 报告入口与公共 schema 未变化；
   - `engine/asof/` 不出现在任何默认 registry 或默认 pipeline 的 import 链中；
3. **终验报告**：`reports/as-of-life-state-career-wealth-slice-g0-g5-verification.md`，格式对照 [`ziping-career-structure-slice-g0-g5-verification.md`](../reports/ziping-career-structure-slice-g0-g5-verification.md)，含结论行 `staged_verified_production_unchanged` 与"未进入 G6，需独立冻结样本后验和另行审批"。

**验证命令（完整，无占位符）**：
```
python -m pytest tests/asof -q
python -m pytest tests/asof/test_production_isolation.py -q
python -m pytest tests/test_production_entrypoints_unchanged.py tests/test_performance_and_ports.py -q
python -m pytest tests/ziping_career/test_production_isolation.py tests/ren_timing -q
git diff --name-only -- engine/application engine/decision engine/domain engine/yingqi engine/v5
git status --short
```

第五条命令**预期无输出**。如有输出，立即停止并报告，不尝试就地缩小 diff。

**可选全仓 sanity**（耗时约 20 分钟）：
```
python -m pytest -q
```
预期结果：**2 failed**（即审计 §2.5 记录的两个 pre-existing failures）+ 6 skipped。**出现第 3 个失败才触发 STOP。**

---

## 5. 明确不做（永久排除在本计划外）

- 不做样本外后验校准、不做置信度 Beta 切换、不做生产 promotion；
- 不扩展到六大基本面全量；
- 不修改任何 F01-F12 卡片契约；
- 不建立统一五动作 dispatcher 跨卡复用层；
- 不做任何 GitHub 服务端操作。

进入 G6 需用户在本计划完成后另行明确授权，授权范围不可从 G0-G5 继承。

---

## 6. 风险登记与应对措施

| # | 风险 | 影响 Gate | 概率 | 影响 | 应对措施 |
|---|---|---|---|---|---|
| R1 | `retrospective.py` 自由文本字段无法结构化，导致原局承载图字段无来源 | G1 | 高 | 高 | 在 `engine/asof/` 建适配层，直接从 `engine/predicates/` 原子谓词取结构化信号，绕过 `retrospective.py` 的文本字段；若仍不足，G0 缩小字段子集并标注"本次不启用" |
| R2 | 双轨物理分离在实现中退化为单对象+字段区分 | G3 | 中 | 高 | G3 增加架构断言测试：`VerifiedState` 与 `HypothesisState` 必须是不同类型，且 `VerifiedState` 无任何指向未核验候选的字段 |
| R3 | 从 F09 复制根源/完成方式字段，静默丢失"延伸边界"语义 | G2 | 中 | 高 | G2 禁止 import 任何 `engine.f09.*`；增加测试断言根源等级对未来推演延伸范围形成实际约束 |
| R4 | 单案例数据不足以触发全部状态转移路径 | G3、G4 | 高 | 中 | 允许合成边界测试，但必须逐条标注为合成；不得虚构案例真实历史 |
| R5 | 命名与既有 `DaiyunSegment` 冲突造成后续混淆 | G0-G5 | 中 | 低 | G0 前置裁定命名；所有新类 docstring 必须说明与既有同名/近义类的区别 |
| R6 | 误把 2 个 pre-existing failures 当成自己引入的回归而早停 | G5 | 中 | 中 | 已在审计 §2.5 与本文件 §2、G5 三处明确记录；terra 遇到时对照测试名核验即可继续 |
| R7 | 加权求和悄悄进入影响度裁决 | G3 | 中 | 高 | G3 增加代码级断言：`EventImpactAssessment` 模块内不得出现 `sum(`、`* weight`、`+ score` 等加权模式（参照 `tests/f09` 的 AST 断言写法） |
| R8 | 实现过程中不自觉修改了生产文件 | 全程 | 低 | 高 | 每个 Gate 收口时运行 `git diff --name-only -- engine/application engine/decision engine/yingqi`，预期无输出 |

---

## 7. 执行记录

（terra 按 Gate 顺序在此追加，或写入 `reports/as-of-life-state-career-wealth-slice-g0-g5-verification.md`）

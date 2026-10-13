# as-of 真实盲断闭环·持续扩样 R3 增量报告

- 执行日期：2026-07-29
- 执行范围：本地仓库、固定字典序队列、两阶段盲态冻结后揭示
- 状态：**LOCAL ONLY / NOT PUSHED**
- Git / GitHub：本受控会话未执行 Git 或 GitHub 操作
- 最终裁决：**PASS / COMPLETE — EVIDENCE-BOUNDED FREEZE**

## 一、本轮协议与保护边界

本轮按不可逆顺序执行：

1. 新鲜机械枚举 [`cases/`](../cases/) 中规范 RF 目录，要求同时存在 `input.md` 与 `feedback.md`。
2. 排除历史报告中所有已触碰、污染、无效或失败案例。
3. 对剩余候选调用 [`truncate_blind_section()`](../tools/as_of_blind_judgment_probe.py:98) 与 [`detect_table_embedded_annotation()`](../tools/as_of_blind_judgment_probe.py:77)，并执行窄现实词扫描；候选审计只输出安全元数据，不输出候选正文。
4. 按规范 RF ID 字典序选择首个安全候选 [`C-2026-RF000249-坤-乙亥乙酉庚午戊寅`](../cases/C-2026-RF000249-坤-乙亥乙酉庚午戊寅)。
5. 阶段一只读取 [`input.md`](../cases/C-2026-RF000249-坤-乙亥乙酉庚午戊寅/input.md:1) 的安全截断视图，不读取现实字段和反馈。
6. 在反馈封闭状态下独立冻结根气、完成方式、事件窗口、竞争解释、有限现实落点与 falsifiers。
7. 调用真实 [`evaluate_event_candidate()`](../engine/asof/event_candidate.py:130)、[`freeze_career_draft()`](../engine/asof/consultation_freeze.py:563) 和 canonical 哈希 API，以 create-only 模式落盘 frozen draft。
8. 从磁盘独立复算 canonical SHA-256，并验证截止日、落点闭集、`feedback_opened=false` 与覆盖拒绝；全部通过后才首次读取反馈。
9. 调用真实 [`open_verification()`](../engine/asof/consultation_freeze.py:591)、[`record_career_verification()`](../engine/asof/consultation_freeze.py:700)、[`adjudicate_career_verifications()`](../engine/asof/career_state_builder.py:372) 与 [`build_career_states()`](../engine/asof/career_state_builder.py:496) 完成正式核验和状态构建。
10. 对 verified result 再做 create-only 覆盖拒绝证明及跨制品哈希核验。

本轮未修改任何既有案例输入、反馈、索引、历史报告、契约、探针、测试、[`engine/asof/`](../engine/asof/) 或 [`handoff.md`](../handoff.md)。

## 二、新鲜库存与排除

机械枚举口径为规范 RF 目录且目录内同时存在 `input.md` 和 `feedback.md`。

| 项目 | 数量 |
|---|---:|
| 符合机械枚举的 RF 目录 | 98 |
| 历史已触碰案例 | 17 |
| 历史排除后新鲜候选 | 81 |
| 完成安全审计 | 81 |
| 安全候选 | 81 |
| 审计标记 | 0 |
| 字典序首个安全候选 | RF000249 |

历史排除清单：RF000026、RF000057、RF000108、RF000118、RF000121、RF000123、RF000125、RF000149、RF000164、RF000171、RF000175、RF000178、RF000179、RF000190、RF000243、RF000244、RF000475。

RF000249 安全审计结果：

- 边界类型：`yaml_key`
- 截断行：154
- [`detect_table_embedded_annotation()`](../tools/as_of_blind_judgment_probe.py:77) 命中：0
- 窄现实词命中：0
- 裁决：`SAFE`

81 个候选全部通过本轮指定审计，只证明这些机械检测未发现已定义的泄露信号，不证明绝对无泄露。

## 三、RF000249 盲态冻结

- 四柱：乙亥、乙酉、庚午、戊寅
- 截止日：2026-06-08
- 事件窗口：2016-01-01 至 2026-06-08
- 根气与完成方式：`STRONG_ROOT + ACTIVATE_EXISTING`
- 主事件：强根承财并激活资源、项目或经营绩效责任
- 中心落点：资源/项目经营责任增强并承担明确绩效结果
- 替代落点一：组织内专业职能责任增强但经营权有限
- 替代落点二：自主经营或业务拓展责任增强
- 竞争解释一：印官主导的稳定专业岗位，而非经营或项目责任增强
- 竞争解释二：财星只形成资源与绩效压力，未形成职责层级跃迁

盲态结构依据：庚金生酉月，酉为帝旺且酉中辛金提供强根；时干戊印透，午、寅亦藏印；年月两乙正财透，寅亥藏甲财；午藏丁官、寅藏丙杀。由此冻结为强根承财、既有事业承载被激活，同时因官杀未透而保留稳定专业岗位和仅有绩效压力两种竞争解释。

原典证据来自：

- [`《三命通会》`](../sources/ziping/《三命通会》.md:14)：八月建酉，酉中庚辛用事。
- [`千里命稿_part3.md`](../sources/qianliminggao/千里命稿_part3.md:641)：秋令金旺。
- [`2021年课程基础讲解`](../sources/yang/MinerU_markdown_2021年课程基础讲解_2056036810585997312.md:1446)：庚辛在地支见申酉为有根。

冻结制品：[`asof-blind-judgment-continuous-r3-frozen-draft.json`](../cases/C-2026-RF000249-坤-乙亥乙酉庚午戊寅/asof-blind-judgment-continuous-r3-frozen-draft.json)

- frozen draft 文件 SHA-256：`3a1469ffd5cfbf21c8116fea08ba31c38af377dd362233502e1b50d3847ffd9b`
- freeze package canonical SHA-256：`ce89f16a8d463029f2f483a88de5879d010628461fa67934c67df36be206a12d`
- 冻结状态：`FROZEN`
- 冻结时反馈标记：`false`
- 事件窗口截止日核验：通过
- 冻结落点闭集核验：通过
- create-only 重复写入：`FileExistsError`，覆盖被拒绝

冻结件持久化了 `frozen_at_utc = 2026-07-29T06:28:25Z`，核验件持久化了 `feedback_opened_at_utc = 2026-07-29T06:37:33Z`，记录顺序与本受控会话的工具调用顺序一致。但这些时间均由同一受控会话记录，不构成加密学隔离证明；冻结先于反馈揭示仍只能由顺序执行记录、冻结件中的 `feedback_opened=false`、两份时间记录及先完成冻结哈希核验后才读取反馈共同支持。

## 四、揭盲、裁决与状态构建

冻结门全部通过后首次读取 [`feedback.md`](../cases/C-2026-RF000249-坤-乙亥乙酉庚午戊寅/feedback.md:33)。反馈明确记载：2021 年学习之余去超市打工，迅速被提拔为店长，年末毕业。

该事实同时满足：

- 位于冻结事件窗口内；
- 具有可识别的岗位职责增强；
- 具有经营和结果责任；
- 精确落入冻结中心，而不是揭示后新增的解释。

正式 API 裁决：

- verification verdict：`CONFIRMED`
- landing verdict：`CENTER_HIT`
- actual landing：资源/项目经营责任增强并承担明确绩效结果
- impact：`SIGNIFICANT`
- persistence：`SHORT_TERM`
- scope：`PRIMARY_DOMAIN`
- 代表事件日期：2021-06-30；反馈只精确到年份，因此使用年中代表日期
- 短期到期日：2021-12-31
- 最终 envelope state：`STATE_BUILT`
- decision action：`OUTPUT`

核验制品：[`asof-blind-judgment-continuous-r3-verified-result.json`](../cases/C-2026-RF000249-坤-乙亥乙酉庚午戊寅/asof-blind-judgment-continuous-r3-verified-result.json)

- verified result 文件 SHA-256：`a6dd80cfc90f9bb241dad6d8c864f39587fae783a3a62c1dbc711aa51ab14411`
- 引用冻结包 SHA-256：`ce89f16a8d463029f2f483a88de5879d010628461fa67934c67df36be206a12d`
- predicted center 与 actual landing：逐字一致
- hypothesis state count：0
- create-only 重复写入：`FileExistsError`，覆盖被拒绝

### 截止日现实轨解释

2021 年店长状态在 2021-12-31 到期，而求测截止日为 2026-06-08。根据 [`build_reality_track()`](../engine/asof/reality_track.py:65) 只保留截止日仍有效的已核验状态，因此正式结果正确记录：

- `verified_event_ids = []`
- `active_state_ids = []`
- `expired_before_as_of = true`

这不否认历史事件已确认。真实状态构建过程中 ledger 保留一条 `CONFIRMED` 历史事件；空现实轨只表示该短期状态在截止日前已经失效。本轮没有把 2021 年短期店长职责外推为截至 2026 年仍活跃，也没有外推为跨运状态。

## 五、新鲜验证、静态复核与失败账本

逻辑新鲜复核从磁盘重新读取正式制品，不继承编排器自评。得到：

1. freeze package canonical SHA-256 与 frozen draft、verified result 三者一致。
2. frozen draft 文件 SHA-256 与 verified result 文件 SHA-256 已独立计算。
3. 冻结件保持 `feedback_opened=false`。
4. 事件窗口终点等于截止日，没有越界。
5. 表内注释命中与窄现实词命中均为 0。
6. verified result 为 `CONFIRMED / CENTER_HIT / STATE_BUILT`。
7. 中心预测与实际落点逐字一致。
8. 截止日现实轨为空、无假设分支，与短期状态已到期的语义一致。
9. 两个正式目标路径均通过 create-only 覆盖拒绝证明。
10. 五份本轮临时脚本和盲态视图已删除。

### 技术失败、无效运行与安全证据

| 分类 | 数量 | 说明 | 是否进入观察分母 |
|---|---:|---|---|
| `TECHNICAL_FAILURE / PROTOCOL_SHAPE_MISMATCH` | 1 | 临时大运适配对象缺少真实协议要求的 `year_range`；修正为实际协议形状后重跑成功 | 否 |
| `TECHNICAL_FAILURE / STATE_EXPECTATION_MISMATCH` | 1 | 临时阶段二断言错误地要求已过期短期事件仍出现在截止日 `verified_event_ids`；按 [`build_reality_track()`](../engine/asof/reality_track.py:65) 语义修正后重跑成功 | 否 |
| `TECHNICAL_FAILURE / EVIDENCE_SELECTOR_MISMATCH` | 1 | 独立证据命令错误查找不存在的 `created_at_utc`，而实际字段名为 `frozen_at_utc`；该失败运行提供零时间顺序证据，按实际 schema 重跑后确认冻结与反馈时间记录顺序一致 | 否 |
| 原典路径定位失败 | 1 | 首次使用了不存在的杨派文件尾号；通过目录事实定位正确文件后读取 | 否 |
| create-only 覆盖拒绝 | 2 | frozen draft 与 verified result 各一次 `FileExistsError` | 安全证据，不是故障 |
| 无效案例 | 0 | RF000249 有窗口内可评分事业事实 | 不适用 |
| 污染案例 | 0 | 反馈只在冻结、磁盘哈希与覆盖拒绝门通过后揭示 | 不适用 |
| 有效确认案例 | 1 | RF000249，`CONFIRMED / CENTER_HIT` | 是 |

所有技术失败均发生于正式写盘前或只读证据命令中，失败运行不作为行为通过证据，也不改变已冻结合同和正式裁决。

## 六、本轮与累计观察账本

| 口径 | 有效 N | CONFIRMED | PARTIAL_HIT | REJECTED | `CONFIRMED + PARTIAL_HIT` | 观察分数 |
|---|---:|---:|---:|---:|---:|---:|
| 本轮 R3 | 1 | 1 | 0 | 0 | 1 | 1/1 |
| 继承至 R2 | 10 | 2 | 3 | 5 | 5 | 5/10 |
| 合并累计 | 11 | 3 | 3 | 5 | 6 | 6/11 |

历史及本轮另有 5 个无效样本（RF000123、RF000171、RF000175、RF000178、RF000190），均不进入有效分母；历史污染案例继续排除，本轮新增污染为 0。

`6/11` 只能称为固定、非随机字典序选择方式下的累计观察分数。样本小、选择非随机，并存在由目录可用性、历史排除、安全边界、反馈粒度和固定队列共同造成的系统性选择偏差。

该分数不是“真实准确率”，不是引擎准确性，也不构成命理规则、as-of 架构或当前生产系统有效性的证明。

## 七、直接证明与禁止推断

### 本轮直接证明

1. RF000249 能在反馈封闭状态下通过真实 as-of API 生成候选和冻结包。
2. 冻结包可由磁盘 canonical 投影独立复算为同一 SHA-256。
3. create-only 保护能拒绝覆盖 frozen draft 与 verified result。
4. 窗口内反馈可由真实核验 API 严格裁为 `CONFIRMED / CENTER_HIT`。
5. 非拒绝样本完成影响裁决和完整状态构建链。
6. 已确认但在截止日前到期的短期状态不会错误进入截止日现实轨，历史确认事件仍由状态构建 ledger 保留。
7. 本轮固定协议新增一个有效观察，累计观察账本从 5/10 变为 6/11。

### 禁止推断

本轮不能证明或推断：

- `6/11` 是总体、无偏或真实准确率；
- as-of 引擎或命理规则具有约 54.5% 的准确性；
- 本轮 `1/1` 表明系统性能提升；
- 当前生产 pipeline 已经通过盲测验证；
- `STRONG_ROOT + ACTIVATE_EXISTING` 比其他白名单组合更优；
- 某一派别、规则、根源组合或完成方式应被提升、降权或淘汰；
- 单个中心命中足以证明命理体系或 as-of 架构有效；
- 81 个候选通过机械审计等于绝对无泄露；
- 2021 年短期店长职责持续到 2026 年或跨越大运。

方法论限制包括：有效样本仅 11 个；候选选择固定且非随机；历史可用目录和排除规则产生系统性选择偏差；反馈粒度不均；本案事件日期只精确到年份；现实文本不能覆盖所有职责细节；窄现实词扫描只能降低而不能消除污染风险；同一会话记录的时间字段不能独立证明盲态隔离。

## 八、已知的方法论局限（历史继承并追加）

以下限制继承历史全部轮次，继续有效：

1. 单会话自我执行的“先冻结后揭示”协议无法用加密学证明阶段一未获得结果信息；文件时间、`feedback_opened=false` 与工具调用顺序只能形成可审计记录，不能自证绝对隔离。
2. 搜索结果上下文、排盘头部来源或命主代号、以及大运表格内嵌括号注释都可能成为现实履历污染载体；章节/YAML 截断只降低风险，不能覆盖所有变体。
3. 现实事实词表曾出现 boilerplate 假阳性，且历史完整词表没有持久化；本轮重建的窄词“大学、秘书、公务员”不能声称与历史词表逐字相同，也不能证明零假阴性。
4. RF 严格 schema 在既往轮次中比旧格式池少见结构性泄露，但这只是特定候选上的观察，不构成 RF 候选绝对安全的推断。
5. 候选按固定字典序选择，不是随机抽样；目录可用性、历史排除、安全审计与反馈粒度共同产生系统性选择偏差。
6. 样本量仍小，反馈覆盖与职责细节不均；窗口内缺少事业事件时只能记为无效样本，不能把“未记载”自动解释为失验。
7. `as_of_date` 与命主年龄、事业阶段的匹配会显著影响无效样本率；优先选择成年后、大运中后段窗口只能降低无效概率，也会进一步改变选择机制。
8. 每案独立的根气、十神、原局承载、大运适配、竞争解释与落点冻结是不可批量模板化的判读产能瓶颈；压缩这一步会把扩样退化为伪证据。
9. PARTIAL_HIT/CONFIRMED 的实际落点必须逐字匹配冻结闭集；该约束防止揭示后同义扩张，但也要求脚本参数严格遵循冻结字符串。
10. 本案反馈事件日期只精确到年份，年中代表日期是执行所需的约定值；短期状态于 2021 年末到期，不得外推为截至 2026 年仍活跃或跨运持续。

本轮没有发现足以消除上述任何限制的新证据。不得推断 as-of 引擎存在某个“真实准确率”；本轮及历史累计的所有分数都只是特定选择方式下的观察值，不构成对总体的无偏估计。

## 九、本轮实际持久化写集

本轮新增并保留：

1. [`RF000249 frozen draft`](../cases/C-2026-RF000249-坤-乙亥乙酉庚午戊寅/asof-blind-judgment-continuous-r3-frozen-draft.json)
2. [`RF000249 verified result`](../cases/C-2026-RF000249-坤-乙亥乙酉庚午戊寅/asof-blind-judgment-continuous-r3-verified-result.json)
3. [`本增量报告`](as-of-life-state-blind-judgment-continuous-extension-r3-report.md)

本轮已删除：库存枚举脚本、盲态截断视图、冻结编排器、独立冻结核验器、阶段二裁决编排器，共五份临时文件。

未修改：既有案例源文件、历史制品、历史报告、引擎、契约、探针、测试、项目状态与 [`handoff.md`](../handoff.md)。

## 十、证据有界最终裁决与续行边界

RF000249 是有效样本，正式裁决为 `CONFIRMED / CENTER_HIT`；本轮新增有效 N=1、命中或部分命中 1；累计有效 N=11，固定、非随机选择方式下的累计观察分数为 `6/11`；本轮污染计数为 0。

本轮裁决：**PASS / COMPLETE — EVIDENCE-BOUNDED FREEZE**。

**LOCAL ONLY / NOT PUSHED**

该声明仅表示本受控会话未执行 Git 或 GitHub 操作，不表示或暗示 GitHub 已同步、PR 已创建、变更已合并、部署或发布已经发生。

下一轮应在独立受控会话中，从当前仓库重新新鲜枚举，同时把 RF000249 及此前全部已触碰案例加入排除集；不得直接沿用本轮库存快照，不得预读下一候选反馈。

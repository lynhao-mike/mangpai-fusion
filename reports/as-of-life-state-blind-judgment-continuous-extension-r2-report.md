# as-of 真实盲断闭环·持续扩样 R2 增量报告

- 执行日期：2026-07-29
- 执行范围：本地仓库、固定字典序队列、两阶段盲态冻结后揭示
- 状态：**LOCAL ONLY / NOT PUSHED**
- Git / GitHub：本受控会话未执行 Git 或 GitHub 操作

## 一、本轮协议与保护边界

本轮按不可逆顺序执行：

1. 新鲜枚举 `cases/C-2026-RF*` 且同时具有 `input.md`、`feedback.md` 的目录。
2. 排除历史报告中所有已触碰、污染、无效或失败案例。
3. 对剩余候选调用 [`truncate_blind_section()`](../tools/as_of_blind_judgment_probe.py:98) 和 [`detect_table_embedded_annotation()`](../tools/as_of_blind_judgment_probe.py:77)，并执行重建的窄现实词扫描；扫描只输出元数据，不输出源文片段。
4. 按字典序选择首个安全候选 [`C-2026-RF000244-乾-戊寅甲寅辛丑戊戌`](../cases/C-2026-RF000244-乾-戊寅甲寅辛丑戊戌)。
5. 只读取候选 [`input.md`](../cases/C-2026-RF000244-乾-戊寅甲寅辛丑戊戌/input.md:1) 第 1—171 行；第 172 行现实边界及其后内容保持未读。
6. 在反馈封闭状态下独立完成根气、十神结构、大运完成方式、竞争解释和有限现实落点判断。
7. 使用真实 [`evaluate_event_candidate()`](../engine/asof/event_candidate.py:130) 和 [`freeze_career_draft()`](../engine/asof/consultation_freeze.py:563) 构造冻结包，以 create-only 模式落盘，并从磁盘 canonical 投影复算 SHA-256。
8. 只有冻结状态、磁盘哈希和 `feedback_opened=false` 全部验证后，才首次读取 [`feedback.md`](../cases/C-2026-RF000244-乾-戊寅甲寅辛丑戊戌/feedback.md:1)。
9. 使用真实 [`open_verification()`](../engine/asof/consultation_freeze.py:591) 与 [`record_career_verification()`](../engine/asof/consultation_freeze.py:700) 按冻结落点裁决。

本轮未修改案例输入、反馈、索引、历史报告、契约、探针、测试、`engine/asof/` 或 `handoff.md`。

## 二、新鲜库存与排除

机械枚举口径为 `cases/C-2026-RF*` 且目录内同时存在 `input.md` 和 `feedback.md`。

| 项目 | 数量 |
|---|---:|
| 符合机械枚举的 RF 目录 | 98 |
| 历史已触碰案例 | 16 |
| 历史排除后剩余 | 82 |
| 通过重建审计 | 82 |
| 审计标记 | 0 |
| 字典序首个安全候选 | RF000244 |

历史排除清单：RF000026、RF000057、RF000108、RF000118、RF000121、RF000123、RF000125、RF000149、RF000164、RF000171、RF000175、RF000178、RF000179、RF000190、RF000243、RF000475。

### 库存纠错史

本轮有两次机械匹配错误，均在读取候选前发现并作废：

1. 首次把完整目录名与裸 case ID 比较，导致历史排除数错误为 0。
2. 第二次固定长度切片保留了 case ID 后的连字符，历史排除仍未命中。
3. 第三次改为正则提取规范 ID `C-2026-RF\d+`，得到 98 / 16 / 82 的有效库存。

前两次运行不是 admission 证据，也没有造成候选污染。

窄现实词表为重建值“大学、秘书、公务员”，不能声称与历史未持久化词表逐字相同。双结构审计与该重建扫描均未标记 82 个剩余候选，但这不证明绝对无泄露。

## 三、RF000244 盲态冻结

- 盲态边界：`yaml_key`，截断行 172
- 表内注释命中：0
- 截止日：2026-06-11
- 事件窗口：2021-01-01 至 2026-06-11
- 主组合：`WEAK_ROOT + COMPLETE_LATENT`
- 竞争解释一：`WEAK_ROOT + TEMPORARY_SUBSTITUTE`
- 竞争解释二：财旺驱动的市场经营或自主求财路径
- 中心落点：体制或专业组织内的项目执行与管理责任增强
- 冻结替代：专业技术或职能岗位责任增强但未形成正式管理职权
- 定性置信：medium

盲态结构判断：辛金生寅月，双寅财星当令；日支丑与时支戌均藏辛，年时双戊印透，因此判断为财旺、印护、身偏弱而非无根。丙辰、丁巳运连续引入官印作用，冻结为“弱根结构在官印运中补足组织化承载”的候选；同时保留自主求财与平台暂时替代承载两种竞争解释。

主要原典引用来自 [`《子平真诠》`](../sources/ziping/《子平真诠》.md:137)、[`《子平真诠》`](../sources/ziping/《子平真诠》.md:140) 与 [`《子平真诠》`](../sources/ziping/《子平真诠》.md:204)。

冻结制品：[`asof-blind-judgment-continuous-r2-frozen-draft.json`](../cases/C-2026-RF000244-乾-戊寅甲寅辛丑戊戌/asof-blind-judgment-continuous-r2-frozen-draft.json)

- blind input SHA-256：`b46b8982c3717794d88368e1e1578d8cd673a6de2087d9129cb4375c6287e5e0`
- freeze package SHA-256：`91b37c24f2789ba21f56ec546b012b4c59384d5e807e7865ed43d155dc6fbc7f`
- 冻结状态：`FROZEN`
- 候选门结果：`CANDIDATE_FROZEN`
- 冻结时反馈标记：`false`

## 四、揭盲与正式裁决

冻结及磁盘哈希验证完成后，首次读取反馈。反馈提供窗口内连续且可评分的事业事实：

- 2021 年：土木工作做不下去，不知道做什么好；
- 2022 年：不知道做什么；
- 2023 年：仍不知道做什么，暂时无业。

这些事实覆盖冻结窗口，因此样本有效；但现实职业主轴为工作中断、持续职业迷茫和暂时无业，不等于冻结中心或替代落点要求的组织化职责增强。

正式 API 裁决：

- verification verdict：`REJECTED`
- landing verdict：`MISS`
- reason code：`OUTSIDE_FROZEN_LANDINGS`
- decision action：`REJECTED_NO_STATE_BUILD`
- verified event IDs：空

核验制品：[`asof-blind-judgment-continuous-r2-verified-result.json`](../cases/C-2026-RF000244-乾-戊寅甲寅辛丑戊戌/asof-blind-judgment-continuous-r2-verified-result.json)

- 结果文件 SHA-256：`f93a7114b073dab618722e4e111c94a57bf74f51aa88ae8133d5e182d2b77e58`
- 引用冻结包 SHA-256：`91b37c24f2789ba21f56ec546b012b4c59384d5e807e7865ed43d155dc6fbc7f`

由于裁决为 `REJECTED`，本轮未构造影响建议、影响裁决、fundamental adjudication，未调用完整状态构建或 [`run_career_session()`](../engine/asof/session_runner.py:53)。这是协议要求，不是技术缺失。

## 五、新鲜验证与失败账本

逻辑新鲜复核重新从磁盘读取两个制品，不继承实现者自评。独立验证得到：

- canonical 冻结包哈希与冻结件、结果件引用三者一致；
- 冻结时间早于反馈开启时间；
- 事件窗口未越截止日；
- 冻结件仍为 `feedback_opened=false`；
- 两个目标路径再次以 `x` 模式打开均返回 `FileExistsError`，create-only 覆盖被拒绝；
- 结果为 `REJECTED / MISS`；
- 状态构建未执行，verified event IDs 为空。

### 技术与无效运行

| 分类 | 数量 | 说明 |
|---|---:|---|
| 库存收集器无效运行 | 2 | 完整目录名与裸 ID 比较错误；固定长度切片保留尾部连字符 |
| 验证收集器失败 | 1 | Windows `cmd.exe` 内嵌换行转义导致 `SyntaxError`，提供零行为证据；随后用独立临时验证脚本精确重跑通过 |
| 无效案例 | 0 | RF000244 具有窗口内可评分事业事实 |
| 有效拒绝案例 | 1 | RF000244，`REJECTED / MISS` |
| 污染案例 | 0 | 反馈在冻结落盘及磁盘哈希验证后才首次读取 |

上述技术失败不进入行为观察分母，也不改写有效裁决。

## 六、本轮与累计观察账本

| 口径 | 有效 N | 命中或部分命中 | 观察计数 |
|---|---:|---:|---:|
| 本轮 R2 | 1 | 0 | 0/1 |
| 继承至 R1 | 9 | 5 | 5/9 |
| 合并累计 | 10 | 5 | 5/10 |

这是固定、非随机字典序选择下的小样本观察计数，不是“真实准确率”，不是引擎准确性，不构成系统有效性证明，也不能外推至随机命盘、其他功能域或未来样本。

## 七、直接证明与禁止推断

### 本轮直接证明

1. RF000244 能在反馈封闭状态下通过真实 as-of API 生成候选和冻结包。
2. 冻结包可由磁盘 canonical 投影独立复算为同一 SHA-256。
3. create-only 保护能拒绝覆盖两个既有产物。
4. 窗口内不匹配事实能由真实核验 API 裁为 `REJECTED / MISS`。
5. 拒绝样本未进入状态构建。
6. 本轮固定协议新增一个有效观察，累计观察账本从 5/9 变为 5/10。

### 禁止推断

本轮不能证明或推断：

- 5/10 是总体、无偏或真实准确率；
- as-of 引擎或命理规则具有 50% 准确性；
- 当前生产 pipeline 已经过盲测验证；
- 某一派别、规则、根源组合或完成方式应被提升、降权或淘汰；
- 单个拒绝足以证伪整个命理体系或 as-of 架构；
- 82 个候选的安全审计等于绝对无泄露。

限制包括：样本极小、选择非随机、反馈粒度不均、2024—截止日缺少新增事业记录、现实文本未覆盖全部职责细节、窄词表为重建值、候选边界审计只能降低而不能消除污染风险。

## 八、本轮实际持久化写集

本轮新增并保留：

1. [`RF000244 frozen draft`](../cases/C-2026-RF000244-乾-戊寅甲寅辛丑戊戌/asof-blind-judgment-continuous-r2-frozen-draft.json)
2. [`RF000244 verified result`](../cases/C-2026-RF000244-乾-戊寅甲寅辛丑戊戌/asof-blind-judgment-continuous-r2-verified-result.json)
3. [`本增量报告`](as-of-life-state-blind-judgment-continuous-extension-r2-report.md)

本轮一次性冻结与独立验证脚本均已删除。没有修改现有案例源文件、历史制品、历史报告、引擎、契约、探针、测试、项目状态或 `handoff.md`。

## 九、最终裁决与唯一合法续行动作

本轮本地闭环的证据有界裁决为：RF000244 是有效样本，正式结果为 `REJECTED / MISS`；本轮新增有效 N=1、命中或部分命中 0；累计有效 N=10、观察命中或部分命中 5/10；污染计数 0。

**LOCAL ONLY / NOT PUSHED**

唯一合法续行动作：下一轮重新从当前仓库新鲜枚举同时具有 `input.md` 与 `feedback.md` 的 RF 目录，把 RF000244 及此前全部已触碰案例加入排除集，重新执行双结构安全审计和窄现实词扫描，再按字典序选择首个安全候选；不得直接沿用本轮库存快照或预读下一候选反馈。

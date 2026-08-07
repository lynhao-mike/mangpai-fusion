# as-of 真实盲断闭环 · 持续扩样 R6 增量报告

> 状态：LOCAL ONLY / NOT PUSHED  
> 执行日期：2026-07-29  
> 本轮案例：C-2026-RF000286-坤-戊辰丙辰癸丑壬子  
> 本轮裁决：2021 冻结窗口粒度不足的无效样本；保留 frozen draft，不创建 verified result，不进入有效观察分母。

## 一、范围与协议

本轮继续执行反馈封闭的两阶段 as-of 协议：

1. 从规范 RF 案例目录机械枚举同时存在 `input.md` 与 `feedback.md` 的候选；
2. 从十份既有 as-of 盲断报告提取长写和短写案例 ID，排除全部历史已触碰案例，包括有效、无效、污染、失败与跨阶段阻断案例；
3. 对新鲜候选调用 `truncate_blind_section()`，并在截断后的盲态文本上调用 `detect_table_embedded_annotation()`；
4. 额外只扫描窄现实词“大学、秘书、公务员”，库存审计不输出候选现实正文；
5. 按规范案例 ID 字典序选择首个安全候选，不按预期命中难易选案；
6. 只读取现实边界之前的安全排盘，独立冻结根源、完成方式、大运、年度作用链和有限现实落点；
7. 通过真实 `engine.asof` 公共 API 构造候选与冻结包，以 create-only 方式写盘；
8. 从磁盘 JSON 重建 blind input 与 freeze package，重新计算并验证两类 canonical SHA-256；
9. 只有冻结、磁盘哈希、窗口与反馈封闭门全部通过后，才首次读取 `feedback.md`；
10. 无冻结窗口内可评分事业事实时记为无效样本，不牵强进入四选一裁决，不生成 verified result。

本轮没有修改引擎、探针、测试、历史报告、案例源文件、反馈源文件、项目状态或 `handoff.md`。受控执行未运行任何 Git 或 GitHub 命令，也未执行任何 GitHub-mutating operation。

## 二、候选库存、历史排除与安全审计

### 2.1 机械库存

可信库存运行结果：

- as-of 历史盲断报告：10 份；
- 同时存在 `input.md` 与 `feedback.md` 的规范 RF 目录：98 个；
- 历史已触碰案例：20 个；
- 历史排除后新鲜候选：78 个；
- 完成双重污染审计：78 个；
- 安全候选：78 个；
- 标记候选：0 个；
- 字典序首个安全候选：`C-2026-RF000286`；
- 库存阶段反馈正文读取：否。

库存程序同时识别 `C-2026-RF######` 与 `RF######` 并规范化，避免遗漏历史报告中的短写 ID。选择是字典序机械结果，不是对易命中案例的人工挑选。

首次通过 Windows `cmd.exe` 普通重定向生成的库存 JSON 出现中文乱码。该运行因编码环境不可靠而作废，没有用于正式选案。设置 `PYTHONUTF8=1` 后精确重跑，才形成上述可信库存结果。

### 2.2 RF000286 安全审计

实际案例目录：[`C-2026-RF000286-坤-戊辰丙辰癸丑壬子`](../cases/C-2026-RF000286-坤-戊辰丙辰癸丑壬子)。

- 截断边界类型：`yaml_key`；
- 截断行：166；
- 盲态行数：165；
- 盲态视图 SHA-256：`05fec4cb08a9ed83459bcb88fbd601e862e69a3ff7723fcc11f170c84203af0a`；
- 源输入字节 SHA-256：`3ada45967cede97d13b3a9305d607d3293e724788ee76a5b5a75c6abd8d2fbac`；
- 表格内嵌注释命中：0；
- “大学、秘书、公务员”命中：0；
- 冻结前反馈读取：否。

该审计只能证明探针与窄词表在本次输入上没有命中，不能证明绝对无泄露或覆盖所有现实履历表达。

## 三、反馈封闭下的独立判读与冻结合同

### 3.1 安全排盘

- 性别：坤；
- 四柱：戊辰、丙辰、癸丑、壬子；
- 日主：癸水；
- 时柱壬子，癸日主在子为临官，子藏癸，形成直接比劫、禄根；
- 年、月双辰均藏癸，辰为水库；
- 日支丑藏己、癸、辛，癸有气并含辛印；
- 年干戊官透，辰月戊土司令，双辰与丑形成持续制度约束和职责压力；
- 月干丙财透，时柱壬子帮身，资源任务与执行承载并存；
- 木仅藏于双辰而不透，纯创意或纯市场拓展不作为中心；
- 冻结机制所属大运：癸丑，API 闭区间为 2015-01-01 至 2024-12-31；
- 年度作用轨迹：2021 辛丑；
- 截止日：2026-06-11；
- 主事件窗口：2021-01-01 至 2021-12-31。

### 3.2 原始理论证据

本轮使用三条可定位原始语料支持根气与藏干判断：

1. [`杨清娟课程基础讲解`](../sources/yang/MinerU_markdown_2021年课程基础讲解_2056036810585997312.md:1446)：壬癸水在地支见子为本五行根，见辰库亦为有根；
2. [`杨清娟课程基础讲解`](../sources/yang/MinerU_markdown_2021年课程基础讲解_2056036810585997312.md:1448)：壬癸水在地支见丑为有气；
3. [`千里命稿`](../sources/qianliminggao/千里命稿_part1.md:338)：子藏癸，丑藏己、辛、癸，辰藏乙、癸、戊。

理论引用只支持根气、藏干及由此形成的原局承载判断，不直接证明任何具体职业事件或现实命中。

### 3.3 根源与完成方式

正式冻结组合：

`STRONG_ROOT + ACTIVATE_EXISTING`

理由：壬子时柱提供直接比劫、禄根，双辰提供水库根，丑中癸为余气且含辛印；原局戊官、湿土制度约束、丙财资源任务与水根承载已经构成组织责任、流程衔接和执行落实的可行路径。癸丑运与 2021 辛丑只触发、放大既有结构，不补造原局不存在的事业功能。

禁止从该组合推断：

- 必然升职、增收或取得正式职级；
- 年度触发强度等于现实影响度；
- 必然进入特定职业、行业或单位性质；
- 2025 年后壬子运事实可以倒证 2021 事件机制。

### 3.4 年度作用链

冻结年度为 2021 辛丑：辛印出现，流年丑与癸丑大运、日支丑重叠，集中激活官杀责任、比肩承载与印星规范支持。该结构允许职责和流程责任上行，也存在重复事务、压力固化或进展迟滞的竞争解释。

冻结候选事件类型：`既有组织职责与流程统筹强化`。

### 3.5 冻结现实闭集

中心落点：

- 既有组织中职责升级并承担流程或资源统筹。

同域、同方向替代落点：

1. 专业支持转为项目协调或结果责任；
2. 稳定平台内岗位调整并增加跨环节协调。

弱命中边界：只有在 2021 年出现同一组织或稳定平台内可辨识的职责边界扩大、项目协调、流程统筹或结果责任增加，且未达到中心完整强度时，才可判替代命中；单纯加班、事务量增加或泛称更忙不计命中。

证伪项：

1. 2021 年没有任何事业职责、流程协调、项目责任或岗位边界变化；
2. 2021 年主要事业变化是退出稳定组织、纯销售拓展或完全独立创业，且无冻结职责方向；
3. 相关事业事实只发生在 2025 年后壬子运，无法核验癸丑运内候选。

排除项：

- 不冻结具体职业名称、单位性质、职级、收入变化或创业结果；
- 不把日常工作量增加、情绪压力或泛化忙碌视为职责升级；
- 不使用 2025 年后壬子运事实替代 2021 年事件窗口证据；
- 揭盲后不得扩张中心、替代落点或同义落点。

## 四、真实 API 冻结与技术运行记录

正式冻结制品：[`asof-blind-judgment-continuous-r6-frozen-draft.json`](../cases/C-2026-RF000286-坤-戊辰丙辰癸丑壬子/asof-blind-judgment-continuous-r6-frozen-draft.json)。

冻结使用真实公共 API：

- `build_natal_capacity_graph()`；
- `adapt_daiyun_segment()`；
- `evaluate_event_candidate()`；
- `create_initial_envelope()`；
- `transition_session()`；
- `freeze_career_draft()`；
- `compute_freeze_package_sha256()`；
- `verify_freeze_package_hash()`。

### 4.1 写盘前盲视图校验失败与最小修复

冻结器首次执行在正式文件创建前报 `RuntimeError: blind view content drift`。字节级诊断确认源截断文本与盲视图原始字节解码完全相等，两边均含 165 个 CRLF；差异来自 Windows 文本模式把 CRLF 通用转换为 LF，而非数据漂移。

最小修复只将盲视图比较从 `Path.read_text()` 改为 `Path.read_bytes().decode("utf-8")`。该修复没有改变命盘判断、根源组合、年度窗口、现实闭集或正式 frozen 内容。失败发生在 create-only 文件打开之前，没有生成部分正式制品，也没有读取反馈。

### 4.2 成功冻结输出

成功冻结并从磁盘重建验证后得到：

```text
STATUS=FROZEN_DISK_VERIFIED
BLIND_BOUNDARY=yaml_key@166
BLIND_LINE_COUNT=165
TABLE_HITS=0
TERM_HITS=0
ROOT_COMPLETION=STRONG_ROOT+ACTIVATE_EXISTING
EVENT_DAYUN=癸丑
EVENT_YEAR=2021
CENTER=既有组织中职责升级并承担流程或资源统筹
ALTERNATIVE_COUNT=2
FEEDBACK_OPENED=false
BLIND_INPUT_SHA256=c4cb85656a608a02c9efccddbfc0e5d3e0d8ce95ccc78ba2a2f3873eb1332d53
FREEZE_PACKAGE_SHA256=f638a95eae0c408e71e5fa740cc703815b77fbe4bcf7f81fa8bb6f3aa217de96
```

### 4.3 磁盘独立核验

正式 JSON 落盘后，从磁盘数据重新构造 `BlindChartInput` 与 `CareerFreezePackage`，并通过 canonical API 重算和验证：

```text
SCHEMA=asof-blind-judgment-continuous-r6/v1
BLIND_HASH_MATCH=true
PACKAGE_HASH_MATCH=true
EVENT_WINDOW=2021-01-01..2021-12-31
DAYUN=癸丑
LANDING_COUNT=3
FEEDBACK_OPENED_AT_FREEZE=false
VERIFIED_EXISTS=false
```

核验直接确认：

- blind input canonical SHA-256 与正式字段一致；
- freeze package canonical SHA-256 与正式字段一致；
- 事件窗口完整位于癸丑运 2015-01-01 至 2024-12-31 内；
- 中心加两个替代落点共三个，均为事业域、同一责任上行方向；
- 冻结时 `feedback_opened=false`；
- case 目录中的正式 R6 JSON 只有 frozen draft，verified result 不存在。

### 4.4 VERIFY 载具失败账本

第一次动态重建命令尝试将含 `.tmp.py` 的冻结器作为普通包导入，得到 `ModuleNotFoundError`。该结果只证明验证载具选择错误，提供零 frozen/API 行为证据，未修改正式制品。

第二次改用 `importlib.util` 按路径加载，但未在执行前把动态模块注册到 `sys.modules`，Python 3.14 的 `dataclass()` 因而报 `AttributeError`。该结果同样只是验证载具错误，提供零 frozen/API 行为证据，未修改正式制品。

第三次在 `exec_module()` 前注册动态模块后，完整执行上述磁盘重建、哈希、schema、窗口、落点、反馈标记及写集断言，结论为 `VERIFY_PASS`。前两次失败没有被包装成通过证据，也未从失败历史中删除。

### 4.5 create-only 反向验证

再次执行同一冻结器时，`open("x")` 以 `FileExistsError` 拒绝覆盖既有 frozen draft。该非零退出是 create-only 覆盖保护证据，不是产品故障，也没有改变正式 frozen。

## 五、揭盲与裁决

冻结、磁盘哈希、窗口与反馈封闭门全部通过后，才首次读取 [`feedback.md`](../cases/C-2026-RF000286-坤-戊辰丙辰癸丑壬子/feedback.md)。

反馈中的相关事业事实为：

- “2019～2023……工作学习都很好，换了不错的工作，补了学历”；
- “2023 换工作后突然被新公司辞退”。

这些事实不足以可靠核验冻结的 2021 年闭集：

1. 2019～2023 是跨五年的宽区间，不能把其中“换了不错的工作、补了学历”机械分配给 2021；
2. 反馈没有给出 2021 年职责升级、流程统筹、项目协调、结果责任增加或岗位边界扩大的可定位事实；
3. 2023 被辞退不在 2021 冻结窗口内，不能跨年核验或否定 2021；
4. “反馈未记载 2021 精确事实”不等于现实中已证明没有事件；
5. 因此不能可靠裁为 `CONFIRMED`、`PARTIAL_HIT`、`REJECTED` 或 `UNKNOWN`。

按既有协议，本案裁为**冻结年度粒度不足的无效样本**：

- 保留 frozen draft；
- 不创建 verified result；
- 不进入有效观察分母或命中分子；
- 不运行 `run_career_session()`；
- 不构造 suggestion、impact adjudication、fundamental adjudication 或现实状态；
- 不扩张冻结中心、替代落点或同义边界。

## 六、逻辑新鲜 STATIC_REVIEW

独立逻辑复核不继承实现者自评，重新检查正式 frozen、反馈、年度窗口、闭集和无效样本协议，结论为 `PASS`：

1. 2021 辛丑事件窗口完整位于癸丑运；
2. 中心、两个替代、弱命中边界、证伪项和排除项均在揭盲前冻结；
3. 本案命理结构、年度机制与现实闭集为独立构造，没有复制 R5 个案判断；
4. 反馈只有 2019～2023 宽区间及 2023 事实，不能可靠评分 2021；
5. 无效样本只保留 frozen、不生成 verified，符合冻结协议；
6. 没有跨年、跨运追认，也没有使用反馈措辞扩张闭集。

唯一 LOW 发现：candidate 的 `daiyun_evidence` 中同一条癸丑运证据重复出现两次。这是 frozen 内的证据冗余，不能视为两份独立证据；schema 不要求去重，该冗余不改变事件窗口、根源组合、闭集、canonical 哈希或无效样本裁决。frozen 已不可变，揭盲后不为此重开或改写。

## 七、逻辑新鲜 EVIDENCE_REVIEW

Evidence Reviewer 仅基于冻结合同、正式 frozen、盲态审计元数据、原始反馈和有效 VERIFY 输出重新裁决，不继承实现者或 Static Reviewer 的结论。

### 7.1 有效证据

- 正式 frozen 可从磁盘重建，blind input 与 freeze package 两类 canonical 哈希均匹配；
- schema、2021 窗口、癸丑运、三个冻结落点及 `feedback_opened=false` 均通过动态断言；
- create-only 反向执行实际拒绝覆盖；
- 原始反馈没有足以把宽区间事实定位到 2021 的事业粒度；
- verified result 不存在，与无效样本协议一致。

### 7.2 无效或仅限故障证明的证据

- 首次换行比较失败只证明 Windows 文本读取方式不适合字节级比较；
- 前两次 VERIFY 导入失败只证明验证载具有误；
- create-only 的 `FileExistsError` 只证明覆盖保护，不证明命理判断正确；
- `daiyun_evidence` 重复项不能当作两份独立支持证据。

### 7.3 Falsifier 复核

- 空扫描或不完整扫描：未发现；库存 78 个新鲜候选均完成截断、表格注释与窄词审计；
- 错误案例或角色：未发现；正式 frozen、反馈与 case ID 一致；
- selector 漂移：未发现；动态重建明确断言 schema、哈希、窗口、落点和写集；
- 静态/动态不一致：未发现影响裁决的不一致；冻结闭集一中心加两替代，动态计数为 3；
- 旧证据冒充新证据：未发现；两次载具失败被保留为无效证据；
- 未授权证据用于 PASS：未发现；审查只使用本轮本地只读及已授权动态证据；
- 失败历史遗漏：未发现；乱码、换行、两次导入失败与覆盖拒绝均记账；
- 局部证据扩张为系统结论：明确禁止。

### 7.4 裁决

```text
Verdict: PASS
Static/dynamic reconciliation: YES
Directly proven boundary: RF000286 完成反馈封闭冻结、磁盘 canonical 哈希核验，以及揭盲后的无效样本分流
Not-proven boundary: 不证明冻结事业判断被现实确认或拒绝，不证明引擎准确性或系统有效性
Freeze eligible: YES
Minimum next legal action: create-only 持久化本报告，随后删除 R6 临时文件并执行最终文件清单验证
```

## 八、技术失败、无效与污染账本

| 分类 | 数量 | 说明 | 是否进入有效分母 |
|---|---:|---|---|
| 库存编码无效运行 | 1 | Windows 普通重定向导致中文乱码；设置 `PYTHONUTF8=1` 精确重跑 | 否 |
| 盲视图比较失败 | 1 | `read_text()` 通用换行转换造成假漂移；字节级诊断后单点修复 | 否 |
| VERIFY 载具导入失败 | 2 | `.tmp.py` 普通导入失败；动态模块未注册导致 dataclass 失败 | 否 |
| create-only 覆盖拒绝 | 1 | 既有 frozen draft 被 `FileExistsError` 保护 | 安全证据 |
| STATIC_REVIEW LOW | 1 | 同一大运证据重复，不能视为两份独立证据 | 不改变裁决 |
| 新增无效案例 | 1 | RF000286 无可定位到 2021 的可评分事业事实 | 否 |
| 新增有效案例 | 0 | 本轮无有效核验样本 | 不适用 |
| 新增污染案例 | 0 | 反馈在冻结与磁盘验证门通过后才读取 | 不适用 |

失败运行不作为行为通过证据，也不改变已冻结合同和正式裁决。

## 九、本轮与累计观察账本

| 口径 | 有效 N | CONFIRMED | PARTIAL_HIT | REJECTED | 命中或部分命中 | 观察分数 | 无效样本 |
|---|---:|---:|---:|---:|---:|---:|---:|
| 继承至 R5 | 11 | 3 | 3 | 5 | 6 | 6/11 | 6 |
| 本轮 R6 增量 | 0 | 0 | 0 | 0 | 0 | 不适用 | 1 |
| 合并累计 | 11 | 3 | 3 | 5 | 6 | 6/11 | 7 |

R4 的 RF000281 为跨大运阶段核验错配的 `BLOCKED` 历史案例，不进入有效分母、命中分子或无效样本计数；本轮没有重开或改写其任何产物。

`6/11` 只能称为固定、非随机、字典序机械选择方式下的累计观察分数。样本量小，候选不是随机抽样；目录可用性、历史排除、安全边界、反馈粒度和固定队列共同形成系统性选择偏差。该分数不是总体或无偏准确率，不是引擎准确性，也不构成命理规则、as-of 架构或生产系统有效性的证明。

## 十、直接证明与禁止推断

### 10.1 本轮直接证明

1. RF000286 能在反馈封闭状态下通过真实 as-of 公共 API 形成 create-only frozen draft；
2. blind input 与 freeze package 可从磁盘对象重建并独立复算为相同 canonical SHA-256；
3. 事件窗口严格位于冻结的癸丑大运阶段；
4. create-only 能实际拒绝覆盖既有 frozen draft；
5. 揭盲后缺少可定位到 2021 的可评分事业事实时，可以保持无效样本而不牵强生成 verified result；
6. 固定年度窗口阻止了把 2019～2023 宽区间或 2023 辞退跨年追认为 2021 的命中或拒绝。

### 10.2 本轮不能证明或推断

- RF000286 的冻结事业判断已被现实确认、部分确认、拒绝或形成 taxonomy gap；
- 反馈未记载 2021 精确事实等于现实中确定没有该事件；
- 2019～2023 的“换了不错的工作、补了学历”发生在 2021；
- 2023 被辞退能够否定 2021 的冻结候选；
- `STRONG_ROOT + ACTIVATE_EXISTING` 优于其他合法组合；
- 癸丑运或辛丑年必然带来职责升级、升职或增收；
- 累计 `6/11` 是总体、无偏或真实准确率；
- as-of 引擎或任何命理规则具有约 54.5% 的准确性；
- 本轮无效样本支持调整生产规则、路由权重或置信度；
- 当前生产 pipeline 已通过不知道答案条件下的盲测验证；
- 78 个候选通过机械审计等于绝对无泄露；
- 本地完成意味着 GitHub 同步、PR、合并、部署或发布；
- 未观察到 GitHub 命令即可证明 GitHub 服务端在所有外部主体下 wholly unchanged。

## 十一、方法论局限

1. 单会话的先冻结后揭示流程形成可审计顺序，但不能用文件时间或自报标记加密学证明绝对隔离；
2. YAML/Markdown 截断和窄现实词扫描只能降低污染风险，不能证明零假阴性；
3. 本轮词表仅为“大学、秘书、公务员”，不能覆盖所有现实履历表达；
4. 候选按固定字典序选择，不是随机抽样；
5. 反馈粒度不均，宽区间记录不能被可靠分配给冻结年度；
6. 严格年度窗口降低跨阶段、跨年追认风险，也会提高无效样本率；
7. 每案独立根气、十神、承载、大运、年度轨迹和闭集冻结不能由批量模板替代；
8. frozen 内的大运证据重复是表示层冗余，不能增加证据权重；
9. 一个新增无效样本既不支持也不反对冻结命理机制。

## 十二、本轮实际持久化写集

新增并保留：

1. [`asof-blind-judgment-continuous-r6-frozen-draft.json`](../cases/C-2026-RF000286-坤-戊辰丙辰癸丑壬子/asof-blind-judgment-continuous-r6-frozen-draft.json)；
2. [`as-of-life-state-blind-judgment-continuous-extension-r6-report.md`](as-of-life-state-blind-judgment-continuous-extension-r6-report.md)。

明确未创建：

- `cases/C-2026-RF000286-坤-戊辰丙辰癸丑壬子/asof-blind-judgment-continuous-r6-verified-result.json`。

所有 `_asof_continuous_r6_*` 一次性库存、盲态视图、冻结器和报告生成器必须在最终文件清单验证前删除，不作为项目正式产物保留。

## 十三、最终裁决与续行边界

EVIDENCE_REVIEW 裁决：`PASS`，本轮具备 `EVIDENCE-BOUNDED FREEZE` 条件。其范围只限于：RF000286 已完成反馈封闭冻结、磁盘哈希核验和揭盲后的无效样本裁决；它不包含现实命中结论，不增加有效样本数，也不改变累计观察分数。

本报告 create-only 持久化后，控制器仍须删除全部 `_asof_continuous_r6_*` 临时文件并执行最终清单验证。只有清理验证确认正式 frozen 与本报告存在、verified 不存在且临时文件为零后，本地收尾才可记为 `PASS / COMPLETE — EVIDENCE-BOUNDED FREEZE`。

下一轮若继续扩样，必须把 RF000286 加入历史已触碰排除集，从剩余规范候选中重新机械枚举字典序首个安全案例，并重复完整的先冻结后揭示协议。不得重开 RF000286 以补造 2021 事实或改写冻结闭集。

**LOCAL ONLY / NOT PUSHED**

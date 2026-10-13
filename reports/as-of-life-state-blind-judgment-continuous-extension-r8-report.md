# as-of 真实盲断闭环 · 持续扩样 R8 增量报告

## 一、范围、授权与保护边界

- 本轮为本地、固定字典序、非随机的持续扩样；没有固定样本量目标。
- 本轮实际新增并触碰 1 个案例：`C-2026-RF000301-乾-乙亥辛巳壬寅癸卯`。
- 只允许新增本案 frozen draft、本报告及执行期临时载具；本案缺少冻结窗口核验事实，因此不允许创建 verified result。
- 未修改 `engine/asof/`、探针、历史报告、既有案例源文件、测试、`handoff.md` 或其他仓库事实源。
- 本受控会话没有执行 Git 或 GitHub 命令；本报告仅陈述本地证据，不推断仓库外状态。

## 二、新鲜候选库存

### 2.1 机械枚举

临时只读库存脚本扫描全部 12 份历史 as-of 盲断报告，并同时规范化长写 `C-2026-RF######` 与短写 `RF######`：

- 历史已触碰规范 ID：22 个；
- 同时具有 `input.md` 与 `feedback.md` 的 RF 案例：98 个；
- 排除全部历史已触碰案例后，新鲜候选：76 个；
- 通过当前安全审计：76 个；
- 污染或无安全边界拒绝：0 个；
- 按规范案例 ID 字典序机械选中：`C-2026-RF000301`。

历史已触碰集合包含此前跨阶段失败的 `C-2026-RF000281` 及历史报告中出现的 `C-2026-RF000475`，两者均未重新进入候选池。

### 2.2 安全审计

目标输入经 `truncate_blind_section()` 截断：

- `cut_line=156`；
- `boundary_type=yaml_key`；
- 盲视图 155 行；
- `detect_table_embedded_annotation()` 命中 0；
- 窄现实词“大学、秘书、公务员”命中 0。

该审计只证明当前探针与窄词表未命中，不证明绝对不存在所有潜在污染或假阴性。冻结成功前没有读取目标案例 `feedback.md`。

## 三、独立盲态合同

### 3.1 安全排盘

- 乾造：乙亥 / 辛巳 / 壬寅 / 癸卯；
- 壬日十二长生：亥临官、巳绝、寅病、卯死；
- 选定大运：戊寅，2016-2026；
- 冻结年度：2024 甲辰；
- 冻结窗口：2024-01-01 至 2024-12-31。

### 3.2 原局根气、十神与竞争解释

- 年支亥藏壬本气，且为壬日临官；时干癸劫财透出，故不能裁为 `NO_ROOT`。
- 壬水生巳月处绝，巳亥冲使年支本气根受动；月干辛印透但坐巳，稳定支持有限。
- 年干乙、亥寅所藏甲及寅卯形成食伤输出链；巳寅均藏戊，大运戊寅显出规则与责任信号。
- 最强竞争解释：食伤增强可能只形成学习、技能、表达或任务量增加，未转成明确职责升级。

根源与完成方式冻结为：

```text
WEAK_ROOT + COMPLETE_LATENT
```

这是引擎白名单中的合法组合；延伸边界由 API 确定为：

```text
REMAINDER_ONLY_RECHECK_CROSS_DAIYUN
```

### 3.3 年度作用链

2024 甲辰：

1. 甲食神透出，强化原局寅卯乙的输出路径；
2. 辰藏癸、戊、乙：癸提供弱根补充，戊承接戊寅运规则责任信号，乙延续输出；
3. 在戊寅运中形成“输出承接规则责任”的补足链；
4. 结构触发强度冻结为 `medium`，仅是结构信号，不等于现实影响度。

### 3.4 原始理论锚点及限制

- `theory/raw/ziping/extracted/子平_穷通宝鉴_part2_候选理论提取_2026-06-06.md:101`：壬水月令取用需结合戊庚辛丙甲配置，支持不能只据旺弱直接推出事业事件。该条是总纲且不含巳月专条，生产化宜拆月，不能单独证明具体事业事件。
- `theory/raw/tiaohou_ditiansui/extracted/滴天髓阐微_part1_候选理论提取_2026-06-06.md:85`：“生方怕动库宜开，败地逢冲仔细推”，且仍须天干调剂、用神有力与岁运辅助。该条支持巳亥冲须结合强弱喜忌细推，不能单独证明职业变化或现实落点。

### 3.5 冻结现实闭集

事件类型：`career_responsibility_upgrade`。

- 中心：专业输出转为明确项目或结果责任；
- 替代一：岗位职责范围扩大；
- 替代二：转入需要协调资源的工作角色。

三项均固定为 `domain=career`、`direction=upgrade`。

弱命中边界：只有学习、技能输出、任务量或短期协作增加，但没有职责范围、项目结果责任或资源协调角色的可核验变化。

Falsifiers：

- 2024 年全年没有职责范围、项目结果责任或资源协调角色变化；
- 唯一可核验事业变化明确发生在 2024 年窗口之外。

排除项：

- 单纯薪资涨跌不计入命中；
- 学习、考试或证书变化本身不计入事业职责升级；
- 婚恋、健康或家庭事件不计入事业落点；
- 不得事后追认具体单位、行业、职级或收入数额。

## 四、真实 API 冻结与持久化证据

冻结载具真实调用：

- `blind_chart_input_from_mapping()`；
- `create_initial_envelope()`；
- `verify_envelope_hash()`；
- `build_natal_capacity_graph()`；
- `adapt_daiyun_segment()`；
- `evaluate_event_candidate()`；
- `transition_session(..., BLIND_DRAFTED)`；
- `freeze_career_draft()`；
- `compute_freeze_package_sha256()`；
- `verify_freeze_package_hash()`。

create-only 目标：

```text
cases/C-2026-RF000301-乾-乙亥辛巳壬寅癸卯/asof-blind-judgment-continuous-r8-frozen-draft.json
```

哈希：

```text
blind input SHA-256:
af147564751ea8b3366d23685b40bcb45b1cbbae00dfbb5077bfa2c57941afbc

freeze package SHA-256:
177295ff596bbe861cada8a5b3f35dca2a5d4471da3a946d7d00570f4cb502f9
```

写盘后从 JSON 磁盘字节独立重建 canonical 投影并验证：

- blind input hash：PASS；
- freeze package hash：PASS；
- `feedback_opened=false`：PASS；
- 截断边界与 155 行盲视图：PASS；
- `WEAK_ROOT + COMPLETE_LATENT`：PASS；
- 2024 冻结窗口：PASS；
- 三项有限落点闭集：PASS；
- 第二次以 `xb` 打开同一路径被 `FileExistsError` 拒绝：PASS。

## 五、揭盲与裁决

冻结及独立验证全部成功后，首次读取目标案例 `feedback.md`。事实年表只到 2023 年，未提供 2024 年任何事业事实。

因此本案裁决为：

```text
无效样本 / 缺少冻结窗口核验事实
```

严格后果：

- 不判 `CONFIRMED`、`PARTIAL_HIT`、`REJECTED` 或 `UNKNOWN`；
- 不创建 R8 verified result；
- 不调用完整 `run_career_session()`；
- 不构建现实状态、影响账本或未来投影；
- 不用 2023 或其他年份事实跨年度、跨窗口追认。

## 六、STATIC_REVIEW 与 VERIFY

逻辑新鲜结构复核确认：

- 目标案例目录只新增 frozen，没有 R8 verified 文件；
- frozen 窗口、根源组合、落点闭集与盲边界符合合同；
- 无效样本停止在 frozen，未误入现实核验与状态构建链；
- 没有修改受保护的引擎、探针、测试、历史报告或案例源文件。

精确动态测试：

```text
python -m pytest \
  tests/asof/test_session_contract.py \
  tests/asof/test_natal_capacity.py \
  tests/asof/test_daiyun_context.py \
  tests/asof/test_event_candidate.py \
  tests/asof/test_consultation_freeze.py -q
```

结果：

```text
199 passed in 1.07s
```

独立证据审查再次直接从磁盘重算，以下 9 项全部为真：

- blind hash；
- freeze hash；
- feedback flag；
- blind boundary；
- event window；
- root/completion combination；
- landing closed set；
- no verified result；
- feedback has no 2024 row。

## 七、技术失败、无效与污染账本

### 7.1 本轮

- 技术失败：0；
- 污染拒绝：0；
- 新增有效样本：0；
- 新增无效样本：1（RF000301，反馈缺少 2024 冻结窗口事实）；
- 新增命中或失验裁决：0。

### 7.2 历史持续保留

- RF000281：跨大运错配导致执行失败，继续永久排除；不计有效或无效，不计任何 verdict。
- 历史其余无效样本继续按既有报告账本保留，不重新解释。

## 八、本轮与累计观察账本

本轮实际新增触碰案例：1。

本轮新增有效样本：0；本轮新增无效样本：1。

截至 R8：

- 有效样本：11；
- `CONFIRMED`：3；
- `PARTIAL_HIT`：3；
- `REJECTED`：5；
- 命中或部分命中观察计数：6；
- 无效样本：9；
- `BLOCKED / 执行失败`：1（RF000281，不计有效或无效）。

累计观察分数保持 `6/11`；该分数样本很小、固定非随机且存在系统性偏差，只是既有有限样本账本的观察计数，不是“真实准确率”，也不能证明引擎准确性或命理学有效性。

## 九、方法论局限

- 候选按固定字典序从历史 RF 案例中机械选择，并非随机抽样；
- 案例来自既有反馈库，存在来源、记录密度、年份覆盖和迁移格式偏差；
- 安全审计依赖有限探针与窄词表，零命中不能证明绝对零污染；
- 本轮只有 1 个新增触碰案例，且因窗口事实缺失而无效；
- 反馈缺失不能解释为事件未发生，也不能解释为预测成立；
- 理论锚点只支持结构判断边界，不提供现实事件的独立证明；
- 观察账本没有对照组、随机化、预注册总体抽样框或统计功效保证。

## 十、直接证明与禁止推断

### 10.1 本轮直接证明

- 在反馈封闭状态下，对 RF000301 按已审计盲视图形成了独立合同；
- 真实 `engine.asof` API 成功构造不可变对象并冻结包；
- frozen 以 create-only 成功持久化，覆盖尝试被拒绝；
- 两个 canonical SHA-256 可从磁盘投影独立重算一致；
- 反馈没有 2024 年事实，因此本案不能进入有效核验；
- 精确相关 API 测试在本次运行中为 199 passed。

### 10.2 禁止推断

本轮不能证明或推断：

- RF000301 的冻结事件真实发生或未发生；
- 冻结候选是命中、部分命中、失验或 taxonomy gap；
- 命理学被证明或证伪；
- 引擎具有某种“真实准确率”或已被证明有效；
- 本轮测试代表全仓库、全系统或生产行为均正确；
- 没执行 GitHub 变更命令即可证明 GitHub 服务端绝对未发生任何外部变化。

## 十一、本轮持久化写集

新增正式文件：

1. `cases/C-2026-RF000301-乾-乙亥辛巳壬寅癸卯/asof-blind-judgment-continuous-r8-frozen-draft.json`
2. `reports/as-of-life-state-blind-judgment-continuous-extension-r8-report.md`

未创建 verified result。执行期临时脚本在最终核验前删除，不属于最终持久化写集。

## 十二、最终裁决与续行边界

```text
PASS / COMPLETE — EVIDENCE-BOUNDED FREEZE
LOCAL ONLY / NOT PUSHED
```

该裁决只覆盖 R8 本地单元：RF000301 已完成先冻结后揭示，且因缺少 2024 冻结窗口事实被诚实裁为无效样本。它不扩大为全系统正确性、命理有效性或统计准确率结论。

下一轮继续使用同一提示词，重新机械枚举并排除包括 RF000301 在内的全部历史已触碰案例；仍须逐案独立判读、真实 API create-only 冻结、磁盘独立哈希验证后才可揭示反馈。

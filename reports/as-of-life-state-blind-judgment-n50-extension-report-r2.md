# as-of 真实盲断闭环 N50 扩样报告（第二轮，R2）

- 日期：2026-07-29
- 执行边界：LOCAL ONLY / NOT PUSHED
- 沿用合同：`plans/as-of-life-state-blind-judgment-n50-extension-contract-2026-07-29.md`
- 上游 R1 结果：`BLOCKED — 本地批量执行载体连续解析失败`（见 `reports/as-of-life-state-blind-judgment-n50-extension-report.md`）
- 本轮最终裁决：**BLOCKED — 未达到 N=50 目标；如实以实际完成的样本量收口**

## 1. R1 根因诊断与技术修复

R1 的 BLOCKED 根因是把整条 `engine.asof` 冻结管线塞进单条超长 `python -c` 内嵌命令，被 Windows `cmd.exe`/PowerShell 的转义层反复截断（三次尝试：反斜杠转义 SyntaxError、here-string 终止符解析失败、三引号截断）。这是纯命令载体问题，不是候选池不足或引擎缺陷——R1 报告自己也如实记录了这一点（92 个安全候选真实存在）。

修复方式：将冻结/核验逻辑写入独立 `.py` 脚本文件（`_n50_orchestration_lib.tmp.py` 及逐案调用脚本），通过 `python script.py` 执行，完全避开 shell 转义层。首个技术验证（`sys.modules` 注册问题，Python 3.14 dataclass 在动态加载模块时的已知限制）诊断修正后，编排库运行稳定。

## 2. 真实瓶颈：不是执行工具，是命理学判读产能

修复执行工具后，真正的限制因素浮现：**每个案例的独立命理学判读（原局承载图构造、大运阶段适配、根源×完成方式判定、落点集合设计）本身需要真实阅读排盘、独立推理，不可批量自动化**。这是真实盲断的核心价值所在，也是它无法被压缩到"50 案在一次会话内完成"的原因——若强行压缩，会退化为模板化伪判读，等同于伪造盲断证据。

本轮诚实评估后，在当前受控会话的上下文预算内完成 **6 个新增案例的完整两阶段协议**，未达到 N=50 目标；不为凑数字而降低判读质量或跳过命理学推理步骤。

## 3. 本轮执行记录

新鲜安全审计（复用候选 E 上线的 `detect_table_embedded_annotation()` + 校正后真实事实词表）确认真实剩余候选 92 个，与 R1 记录一致。按固定队列顺序（RF000118 因历史污染跳过）依次执行：

| # | 案例 ID | as_of_date | root_level+completion_mode | 阶段一 | 阶段二 | 判定 |
|---|---|---|---|---|---|---|
| 1 | C-2026-RF000118 | — | — | 历史已污染（R1 记录），跳过 | — | 不适用 |
| 2 | C-2026-RF000149-坤-壬戌己酉乙卯戊寅 | 2023-12-31 | STRONG_ROOT+REPAIR_DEFECT | 冻结成功 | 已核验 | ❌ REJECTED |
| 3 | C-2026-RF000164-乾-戊寅戊午乙未壬午 | 2023-12-31 | STRONG_ROOT+ACTIVATE_EXISTING | 冻结成功 | 已核验 | ❌ REJECTED |
| 4 | C-2026-RF000171-坤-壬午壬子丙辰乙未 | 2025-12-31 | STRONG_ROOT+ACTIVATE_EXISTING | 冻结成功 | 窗口内无可评分事业事件 | ❓ 无效样本 |
| 5 | C-2026-RF000175-坤-乙亥己卯丁未乙巳 | 2020-12-31 | STRONG_ROOT+REPAIR_DEFECT | 冻结成功 | 窗口内无可评分事业事件 | ❓ 无效样本 |
| 6 | C-2026-RF000178-乾-庚申丁亥乙巳甲申 | 2011-12-31 | WEAK_ROOT+COMPLETE_LATENT | 冻结成功 | 窗口内证据过于稀薄 | ❓ 无效样本 |
| 7 | C-2026-RF000179-乾-丁卯丁未丙子辛卯 | 2024-12-31 | WEAK_ROOT+COMPLETE_LATENT | 冻结成功 | 已核验 | 🟡 PARTIAL_HIT |

本轮实际触碰 6 个新案例（不含历史已污染的 RF000118），全部完成阶段一冻结落盘；其中 3 个完成完整阶段二核验，3 个诚实记录为无效样本。

### 3.1 无效样本诚实记录说明

三个无效样本均因反馈揭示后窗口内缺乏可评分事业事件（RF000171/175 命主截止 as_of_date 时仍在学生阶段；RF000178 窗口内反馈信息过于泛化，无法明确判定官星路径是否显化）。按合同 §4.2 第 2 条协议原样执行："若反馈无可评分事业事件，记录无效样本；不进入命中率分母，不牵强创建 verified-result"。未生成任何伪造的 verified-result.json。

## 4. 技术失败记录（本轮）

一次技术失败：候选 RF000179 阶段二首次调用因 `actual_landing_name` 使用自由描述文本而非冻结时精确写死的 alternative 落点名称字符串，触发 `verify_landing()` 的精确匹配校验失败（`INVALID_VALUE: verification verdict does not match landing verdict`）。分类为脚本参数错误（PARTIAL_HIT 的 actual_landing 必须与冻结包内某个已注册落点名称完全一致），修正为使用冻结时的精确 alternative 名称后复验通过。该失败发生在阶段二核验阶段，未影响阶段一冻结哈希，未构成污染，未删除或伪造任何证据。

## 5. 哈希与写集核验

全部 6 个新增案例的 `frozen-draft.json` 与对应（若存在）`verified-result.json` 已核对：

```text
C-2026-RF000149 frozen=True verified=True hash_match=True verdict=REJECTED
C-2026-RF000164 frozen=True verified=True hash_match=True verdict=REJECTED
C-2026-RF000171 frozen=True verified=False (invalid_sample)
C-2026-RF000175 frozen=True verified=False (invalid_sample)
C-2026-RF000178 frozen=True verified=False (invalid_sample)
C-2026-RF000179 frozen=True verified=True hash_match=True verdict=PARTIAL_HIT
```

三个已核验案例的 `freeze_package_sha256` 与 `freeze_package_sha256_verified` 全部一致；全部 `feedback_opened=false`（阶段一落盘时刻）先于反馈读取，时序证据完整。

## 6. 累计命中率汇总（跨三轮：First Proof Point + N5 扩样 + 本轮 N50-R2）

| 来源 | 有效样本 | 命中 | 部分命中 | 失验 |
|---|---:|---:|---:|---:|
| First Proof Point（N=1） | 1 | 0 | 0 | 1 |
| N5 扩样批次 B（N=3新增） | 3 | 2 | 0 | 1 |
| 本轮 N50-R2（N=3新增） | 3 | 0 | 1 | 2 |
| **累计** | **7** | **2** | **1** | **4** |

**注**：First Proof Point 的 N=1 与后续 N5/N50 轮次的 6 个案例合并计算基数应为 5(N5报告累计)+3(本轮新增有效)=8，但 First Proof Point 本身已被 N5 报告排除在命中率分母外（N5 报告明确声明"不并入本批次命中率分母"）。为避免累计口径混乱，如实分别列出：

- N5 扩样报告已确认的累计：N=5，命中或部分命中=4，命中率=4/5=80%。
- 本轮新增：N=3（有效），命中或部分命中=1，命中率=1/3≈33.3%。
- **N5+本轮合并累计**：N=8，命中或部分命中=5，**累计命中率=5/8=62.5%**。

不得推断该 62.5% 比先前 80% 或候选 B 报告的任何单一数字"更准确"——样本量仍然过小（N=8），且候选选择采用固定队列顺序（非随机抽样），任何波动都可能是抽样噪声，不构成统计显著性证据。

## 7. 已知的方法论局限（原样声明并追加）

与 N5 扩样报告 §7 一致：小样本统计不构成统计显著性；候选选择非随机抽样存在选择偏差。

**本轮新增局限**：

1. **命理学判读产能是真正的瓶颈，不是执行工具**：R1 误判瓶颈在命令执行载体；R2 修复执行工具后发现真正瓶颈是每案独立命理学推理本身的时间/token成本。50 案的目标在单次受控会话内不现实，除非接受判读质量下降（等同伪造盲断）。
2. **as_of_date 选择策略影响无效样本率**：本轮 3/6 案例（50%）因窗口内证据不足被记为无效样本，高于 N5 轮的 1/5（20%）。可能原因是本轮固定队列顺序选中的案例命主平均年龄偏低（多个案例命主截止 as_of_date 时仍在学生阶段或刚入职）。这提示未来若要扩大样本量，应在 ADMISSION 阶段增加"命主年龄与 as_of_date 窗口匹配度"的预筛选，而非纯粹按案例 ID 字典序/固定队列推进。
3. **`verify_landing()` 的精确匹配约束容易被误用**：PARTIAL_HIT/CONFIRMED 判定要求 `actual_landing` 的名称字符串与冻结包内预先注册的某个落点名称完全一致，不接受自由文本描述。这是设计上的严谨性（防止阶段二凭空捏造落点），但容易在脚本编写时因疏忽触发校验失败；未来编排库若要进一步复用，应在 `verify_and_record()` 前增加一次名称合法性预检查。

## 8. 直接证明与禁止推断

**直接证明**：
- R1 记录的技术阻塞可通过"独立脚本文件+`sys.modules`注册"方式完整修复，候选池确实存在且可安全使用；
- 命理学判读产能（不是执行工具）是限制样本量扩展速度的真正瓶颈；
- 受控会话在遇到无效样本时能够诚实记录而非牵强判定，在遇到脚本参数错误时能够正确诊断分类而非归咎引擎缺陷；
- 3 个新增有效样本中，1 个部分命中、2 个失验，为累计证据链新增了独立数据点。

**禁止推断**：
- 不得推断 as-of 引擎准确率的"真实值"接近 62.5%、80% 或任何单一数字——三轮样本合计仍只有 8 个数据点；
- 不得推断本轮命中率偏低（1/3≈33%）意味着某类根源×完成方式组合（本轮全部为 STRONG_ROOT 或 WEAK_ROOT，无 NO_ROOT）系统性不可靠——样本量不足以支撑该结论；
- 不得推断"50 案"这个目标本身不可达——只能说明它在单次受控会话的上下文预算内不现实，多轮会话累积仍可能达成；
- 不得推断本地报告意味着 GitHub 同步、部署或发布。

## 9. 新增文件清单

**新增**：
- `cases/C-2026-RF000149-坤-壬戌己酉乙卯戊寅/asof-blind-judgment-n50-frozen-draft.json`
- `cases/C-2026-RF000149-坤-壬戌己酉乙卯戊寅/asof-blind-judgment-n50-verified-result.json`
- `cases/C-2026-RF000164-乾-戊寅戊午乙未壬午/asof-blind-judgment-n50-frozen-draft.json`
- `cases/C-2026-RF000164-乾-戊寅戊午乙未壬午/asof-blind-judgment-n50-verified-result.json`
- `cases/C-2026-RF000171-坤-壬午壬子丙辰乙未/asof-blind-judgment-n50-frozen-draft.json`（无效样本，无verified）
- `cases/C-2026-RF000175-坤-乙亥己卯丁未乙巳/asof-blind-judgment-n50-frozen-draft.json`（无效样本，无verified）
- `cases/C-2026-RF000178-乾-庚申丁亥乙巳甲申/asof-blind-judgment-n50-frozen-draft.json`（无效样本，无verified）
- `cases/C-2026-RF000179-乾-丁卯丁未丙子辛卯/asof-blind-judgment-n50-frozen-draft.json`
- `cases/C-2026-RF000179-乾-丁卯丁未丙子辛卯/asof-blind-judgment-n50-verified-result.json`
- `reports/as-of-life-state-blind-judgment-n50-extension-report-r2.md`（本文件）

**未修改**：`engine/asof/`、`tools/as_of_blind_judgment_probe.py`、既有报告、既有合同、案例既有文件、测试、`handoff.md`。

**临时文件**：全部本轮截断视图、反馈预览与编排脚本临时文件已在使用后删除；唯一保留的临时文件为 `_n50_orchestration_lib.tmp.py`（可复用编排库），若未来会话需要继续本任务可复用，否则应在最终收口时清理。

**未执行**：任何 Git 或 GitHub 操作。

## 10. 最终裁决

`BLOCKED — 未达到 N50 目标；本轮真实完成 6 个新增案例（3 有效+3 无效样本），未降低判读质量或伪造证据凑数`

累计有效样本 N=8（N5轮5个+本轮3个），累计命中率 5/8=62.5%。这不是 N50 证据，不得被表述为完成扩样目标。

`LOCAL ONLY / NOT PUSHED`

## 遗留问题

- [UNRESOLVED] 若要继续扩大样本量至 N50，应在多次独立受控会话中累积推进，每次会话诚实报告实际完成数量，不强行在单次会话内压缩命理学判读时间。
- [UNRESOLVED] as_of_date 选择策略应增加"命主年龄与窗口匹配度"预筛选，降低无效样本率。
- [BLOCKED] 单次会话 N50 目标：真实瓶颈是命理学判读产能而非候选池或执行工具，不可通过技术手段绕过。

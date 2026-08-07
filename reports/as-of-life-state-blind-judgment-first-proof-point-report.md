# as-of 真实盲断闭环 First Proof Point 报告（R1 修订版）

> R0 版本裁决为 `BLOCKED`（因把 input.md 标准小节误判为污染而过早 STOP）。
> geju 格局审计发现该判断过于保守，修订阶段一盲态输入粒度为"排盘小节截断"后
> 重新执行，本次（R1）取得 `PASS / COMPLETE — EVIDENCE-BOUNDED FREEZE`。
> R0 的完整执行记录保留在合同 [`as-of-life-state-blind-judgment-first-proof-point-contract.md`](../plans/as-of-life-state-blind-judgment-first-proof-point-contract.md) §3.3，不重复粘贴于此。

## 1. 最终状态

`PASS / COMPLETE — EVIDENCE-BOUNDED FREEZE`

## 2. 选用案例与排除核对

**选用案例**：`C-2026-002-坤-壬戌庚戌戊辰丙辰`，`as_of_date = 2020-12-31`（丙午大运 2013-2023 内，命主约38岁）。

**排除已用案例核对**（8 个既有 as-of 案例）：

| 案例 ID | 已知 as-of 使用 | 本轮状态 |
|---|---|---|
| `C-2026-028-乾-壬戌癸卯壬子乙巳` | G0-G5 | 已排除 |
| `C-2026-024-坤-己巳壬申辛亥壬辰` | G6、Unit8、Unit9 | 已排除 |
| `C-2026-022-坤-癸亥庚申戊寅己未` | G6，跳过 | 已排除 |
| `C-2026-016-坤-甲子丙子丙戌戊子` | G7 | 已排除 |
| `C-2026-026-坤-癸未甲寅壬戌丙午` | G7 | 已排除 |
| `C-2026-027-乾-丁卯壬寅甲午乙丑` | G7 | 已排除 |
| `C-2026-RF000118-乾-己巳癸酉辛丑己丑` | Unit10、Unit11 | 已排除 |
| `C-2026-RF000475-坤-戊辰辛酉己巳乙丑` | Unit9 | 已排除 |

**本轮额外排除**（因本轮受控会话内的知情/污染/合成数据原因，均在 §3 记录理由）：

| 案例 ID | 排除原因 |
|---|---|
| `C-2026-013-坤-壬申甲辰丙辰己丑` | R0 已读全文，本会话已知情污染 |
| `C-2026-014-乾-丙戌庚子乙亥辛巳` | R0 已读全文，本会话已知情污染 |
| `C-2026-015-乾-甲寅乙亥丙辰辛卯` | R1 真实污染事件：截断函数第一版未命中 YAML `known_facts:` 边界，随后 grep 搜索结果上下文直接显示反馈内容 |
| `C-2026-029-坤-乙亥戊寅辛酉癸巳` | 排盘头部 `case_meta.来源` 字段标明"随机生成（用于系统报告流程 smoke）"，非真实案主，不构成污染（未读取任何反馈） |

## 3. 受控会话工具调用顺序（真实记录）

1. R0：读取权威入口、既有 as-of API、只读 013/014 `input.md` 全文，误判污染，STOP，产出 `BLOCKED` 报告。
2. geju 审计：读取 `templates/input-from-wenzhen.md`、抽样 20+ 案例，确认"命主已知信息"小节是模板标准结构，判定 R0 过度保守。
3. 修复：新建 [`tools/as_of_blind_judgment_probe.py`](../tools/as_of_blind_judgment_probe.py) 的 `truncate_blind_section()`，先只检测 Markdown 标题边界。
4. 对 013、014 用截断函数验证可行性（此时两案对本会话已知情污染，仅用于验证截断机制本身，不作为盲断候选）。
5. 尝试 015：截断函数第一版未命中该案例的 YAML `known_facts:` 边界，原样返回全文；随后 grep 搜索该目录，搜索结果上下文片段显示了具体反馈内容——**真实污染事件**，立即停止使用该案例。
6. 升级截断函数：同时检测 `heading` 与 `yaml_key` 两种边界。
7. 内容盲扫描（只输出布尔值/行号/边界类型，不展示正文片段）批量核对候选池 121 个未排除目录的截断可行性。
8. 尝试 029：截断成功（第93行，`yaml_key`），但截断视图头部显示该案例是合成 smoke 测试数据，排除（未读取任何反馈）。
9. 尝试 002：截断成功（第60行，`heading`），排盘信息完整，选定为本次案例。
10. **阶段一（Gate B）**：只基于 002 截断后的排盘视图（四柱、藏干、十神、大运、关键结构），构造 `NatalCapacityGraph`、`DaiyunStage`（丙午运 2013-2023）、事件候选（`STRONG_ROOT + ACTIVATE_EXISTING`），调用 `evaluate_event_candidate()` 接受候选，构造 `CareerBlindDraft`，调用 `freeze_career_draft()` 生成 `CareerFreezePackage`，写入 `cases/C-2026-002-坤-壬戌庚戌戊辰丙辰/asof-blind-judgment-first-proof-point-frozen-draft.json`（含 `"feedback_opened": false`、UTC 时间戳、写死的原始预测）。此步骤完成前未打开该案例 `feedback.md`。
11. **阶段二（Gate C）**：阶段一冻结产物落盘后，首次打开 `cases/C-2026-002-坤-壬戌庚戌戊辰丙辰/feedback.md`，读取真实反馈；构造 `VerificationInput`（判定 `REJECTED`），调用 `run_career_session()` 完成完整核验→状态构建流程；写入 `cases/C-2026-002-坤-壬戌庚戌戊辰丙辰/asof-blind-judgment-first-proof-point-verified-result.json`。
12. 幂等复跑：重新运行阶段一冻结脚本与阶段二核验脚本各一次，确认同输入产生同哈希（`a9387da2a4bb2d66e3d351af7f62be7b29651bcf5d2485081c5d7d7b7eb90d99`），核验结果稳定为 `STATE_BUILT` / `verified_event_ids=()`。
13. 全程未修改 `engine/asof/` 任何文件、任何既有测试、任何案例既有文件；未执行任何 Git 或 GitHub 操作。

## 4. Gate B 冻结时刻原始预测全文（逐字保留，来自落盘 JSON）

```json
{
  "as_of_date": "2020-12-31",
  "case_id": "C-2026-002-坤-壬戌庚戌戊辰丙辰",
  "feedback_opened": false,
  "freeze_package_sha256": "a9387da2a4bb2d66e3d351af7f62be7b29651bcf5d2485081c5d7d7b7eb90d99",
  "frozen_at_utc": "2026-07-28T16:35:03.512491+00:00",
  "frozen_prediction": {
    "candidate_id": "career-output-2013-2023-bingwu",
    "completion_mode": "ACTIVATE_EXISTING",
    "confidence_qualitative": "中等偏高：食伤双戌同藏根基深厚（STRONG_ROOT），但大运丙午为偏印非正印，激活力道不如正印直接，故不判定为高确信",
    "domain": "career",
    "event_type": "career_deepening",
    "falsifier": "截止窗口末仍未在专业输出方向获得任何实质深化或提升",
    "predicted_alternative_landing": "专业输出型副业或第二职业身份的建立",
    "predicted_center_landing": "专业技术/知识输出岗位的持续深化或职级提升",
    "root_level": "STRONG_ROOT",
    "window": ["2013-01-01", "2020-12-31"]
  },
  "schema_version": "asof-blind-judgment-first-proof-point-frozen-draft/v1",
  "session_id": "S-20261028T161000Z-0002af01"
}
```

盲断依据（只基于截断后排盘事实）：戊土日主四柱全土、比肩帮身极旺；月干庚食神透干 + 年支/月支双戌同藏辛伤官（食伤根基深厚，判定 `STRONG_ROOT`）；官星（乙）只藏于日支/时支辰，不透干（弱），故管理职权路径判定为潜在但未激活；大运丙午（2013-2023）偏印透干，放大既有专业输出路径的自我提升倾向（`ACTIVATE_EXISTING`）。据此预测：截至 2020-12-31，该命主在专业技术/知识输出方向应有实质深化或职级提升。

## 5. Gate C 真实反馈对照与逐条判定

**反馈揭示的关键事实**（`cases/C-2026-002-坤-壬戌庚戌戊辰丙辰/feedback.md`）：
- 2005 年结婚（约23岁），儿子为 `C-2026-014` 案例命主；
- 现职业：**县级卫健局事业单位工作人员**（体制内稳定岗位）；
- 财富来源主要为父亲（局长）与配偶（正科）资源，反馈明确指出"实际财富来源 = 家庭资源（父亲权力 + 配偶收入）≠ 自身劳作"；
- 反馈未提及任何职级提升、专业技术深化或副业信息。

| 冻结候选 | 预测中心落点 | 真实落点 | 判定 | 理由 |
|---|---|---|---|---|
| `career-output-2013-2023-bingwu` | 专业技术/知识输出岗位的持续深化或职级提升 | 体制内事业单位稳定岗位，未见职级提升或专业技术深化证据 | **❌ 失验（REJECTED）** | 反馈明确指出该命主的财富与地位主要来自家庭资源（父亲、配偶），而非自身专业输出深化；反馈未提供任何支持"专业深化/职级提升"的证据。这与冻结时写死的证伪条件（"截止窗口末仍未在专业输出方向获得任何实质深化或提升"）完全一致，故判定失验。 |

`session_runner.run_career_session()` 核验结果：`final_envelope_state = ConsultationState.STATE_BUILT`，`verified_event_ids = ()`（空，唯一候选被拒绝，无核验通过事件进入验证状态）。

## 6. 命中率汇总

| 指标 | 数值 | 解释 |
|---|---:|---|
| 有效盲断样本 | 1 | 案例 002 成功走完两阶段协议 |
| 冻结候选事件 | 1 | `career-output-2013-2023-bingwu` |
| 命中 | 0 | — |
| 部分命中 | 0 | — |
| 失验 | 1 | 唯一候选判定为 REJECTED |
| 证据不足 | 0 | 反馈信息充分支持判定（未落入"证据不足"分类） |
| 命中率 | **0/1 = 0%** | 单案例结果，不构成统计显著性证据 |

## 7. 已知的方法论局限（原样声明）

单会话自我执行的"先冻结后揭示"协议，**无法被加密学证明**该会话在阶段一真的没有获得任何案例结果信息——唯一的证据是文件写入时间戳和你对自己工具调用顺序的如实记录。如果未来有独立审查者怀疑纪律是否被遵守，本次结果不能自证清白；更严格的证明需要引入项目里已有的、面向多方隔离的 `tools/school_capability_prospective.py` blind-bundle 协议（本任务不做这件事，只做最小可行的单会话验证）。

**本轮新增的方法论局限**：本次执行本身就发生过一次真实污染事件（案例 015），根因是"内容显现式的 grep/搜索本身也是污染载体"，不比直接 `read_file` 更安全。这意味着即使阶段一改用截断函数处理 `input.md`，任何后续对案例目录的自由文本搜索（而非只输出布尔判定的内容盲脚本）仍可能意外泄露反馈内容。本次通过立即停止、更换案例、把批量筛选脚本改为只输出布尔值/行号来规避，但这只是流程自律层面的补救,不是机制强制的隔离。

## 8. 直接证明与禁止推断

**直接证明**：
- 阶段一盲态输入粒度从"整份 input.md"降级为"排盘小节截断"后，候选池的可用性从"2 次尝试后耗尽"变为可继续筛选出真实可用样本；
- 两阶段协议（冻结盲断→落盘→揭示核验→评分）在本地可完整执行、产出可复验的冻结哈希与核验结果；
- 幂等复跑确认同输入产生同哈希，结果稳定可复现；
- 受控会话在真实遇到污染（015）时能够立即停止、诚实记录、更换案例，而不是假装没看到继续使用。

**禁止推断**：
- 不得推断 as-of 推理系统整体的盲断准确率——本次 0/1 只是一个数据点，不构成统计显著性证据；
- 不得推断命理学有效或无效；
- 不得推断"专业技术输出深化"这一预测方向本身选择不当——本次失验的根因是原局承载图未建模"依附家庭资源"这条路径（`competing_explanations` 中确实列出"以财富/资产管理为主而非专业技术输出"作为竞争解释，但未列出"依附父辈/配偶资源"这一具体形式），这是原局承载图设计留白，不是引擎逻辑错误；
- 不得推断其他 120 个未使用候选目录一定都能通过截断规则处理成安全样本——本次只验证了 121 个目录中的 3 个（015 污染、029 排除、002 使用）；
- 不得推断本地报告意味着 GitHub 同步、PR、合并、部署或发布。

## 9. 新增或修改的文件清单

**新增**：
- `plans/as-of-life-state-blind-judgment-first-proof-point-contract.md`（R0 创建，R1 修订）
- `tools/as_of_blind_judgment_probe.py`（R0 创建，R1 修订：新增 YAML 边界检测）
- `cases/C-2026-002-坤-壬戌庚戌戊辰丙辰/asof-blind-judgment-first-proof-point-frozen-draft.json`
- `cases/C-2026-002-坤-壬戌庚戌戊辰丙辰/asof-blind-judgment-first-proof-point-verified-result.json`
- `reports/as-of-life-state-blind-judgment-first-proof-point-report.md`（本文件，R0 创建，R1 全量重写）

**未修改**：`engine/asof/` 下任何文件、任何既有测试、任何案例既有的 `input.md`/`feedback.md`/`statement_index.json`、任何既有 as-of 报告或合同。

**未执行**：任何 Git 或 GitHub 操作（本地与远端均不可）。

## 10. 最终裁决

`PASS / COMPLETE — EVIDENCE-BOUNDED FREEZE`

协议可执行、可留痕、产出可比较的盲断/事实对照，结果为失验（0/1）。这是本项目历史上第一份关于"as-of 推理在不知道答案的情况下能否盲断准确"的真实单案例证据。

`LOCAL ONLY / NOT PUSHED`

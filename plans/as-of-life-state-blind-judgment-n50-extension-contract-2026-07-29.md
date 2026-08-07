# as-of 真实盲断闭环 N50 扩样执行合同

- 日期：2026-07-29
- 状态：FROZEN FOR LOCAL EXECUTION
- 执行边界：LOCAL ONLY / NOT PUSHED
- 目标：从历史累计有效 N=5 扩展到累计有效 N≥50；若 92 个新鲜机械安全候选全部执行后仍不足，则以全部实际有效数量收口并判定 BLOCKED。

## 1. 历史基线与排除集

历史累计有效基线：N=5，CONFIRMED=2，PARTIAL_HIT=2，REJECTED=1，命中或部分命中率 4/5=80%。另有 1 个已冻结但无可评分事业事件的无效样本。

排除已触碰 RF 案例：

- C-2026-RF000026
- C-2026-RF000057
- C-2026-RF000108
- C-2026-RF000121
- C-2026-RF000123
- C-2026-RF000125

排除旧格式池触碰案例：C-2026-007、008、009、010、011、012、017。它们不属于本轮 92 个 RF 候选。

## 2. 新鲜机械盘点

只读枚举条件：cases/ 下目录名以 C-2026-RF 开头，且 input.md 与 feedback.md 均存在；盘点只检查 feedback.md 是否存在，不读取内容。

排除后候选数：92。

对每个 input.md 实际调用 truncate_blind_section() 和 detect_table_embedded_annotation()，结果：

- cut is None：0
- 表格内嵌注释命中：0
- 重建真实事实词表命中：0
- create-only 目标文件已存在：0
- 机械安全候选：92

### 2.1 真实事实词表恢复偏差

历史报告没有持久化完整的“校正后真实事实词表”，仓库搜索也未找到实现或完整清单，因此本轮不得声称精确继承历史词表。本轮仅依据历史报告明确留下的真实事实示例重建为：大学、秘书、公务员。

该重建词表只能作为一层保守扫描，不能证明绝对无污染；结构层仍必须独立调用 detect_table_embedded_annotation()。任何人工读取盲态输入时新发现的现实事实泄露，均按污染事件处理。

## 3. 固定执行队列

为避免按反馈挑案，按 RF 六位编号升序预先冻结。

### 3.1 首批 50 案

000118、000149、000164、000171、000175、000178、000179、000190、000243、000244、000249、000281、000284、000286、000287、000301、000331、000343、000344、000345、000353、000354、000373、000374、000388、000396、000408、000412、000417、000421、000422、000441、000444、000448、000449、000452、000464、000466、000475、000500、000510、000514、000524、000531、000535、000543、000548、000551、000572、000576。

### 3.2 后备 42 案

000592、000595、000606、000632、000654、000663、000671、000684、000713、000714、000735、000737、000763、000771、000788、000796、000797、000805、000807、000861、000864、000865、000868、000877、000894、000897、000900、000903、000914、000916、000918、000957、000963、000965、000968、000970、000975、000977、000980、000986、000989、000990。

只有在首批阶段二完成后，累计有效 N 仍小于 50，才按上述顺序逐案启用后备；不得跳号挑选。

## 4. 每案不可逆两阶段协议

### 4.1 阶段一

1. 只读取该案 input.md。
2. 调用 truncate_blind_section()；cut 必须非 None。
3. 对截断文本运行重建事实词表扫描与 detect_table_embedded_annotation()。
4. 若任一审计命中或人工发现污染，立即停止该案，不打开反馈，不写伪冻结包，并计入污染预算。
5. 只依据截断盲态输入构造 CareerBlindDraft；主事件只允许 §5 白名单组合。
6. 通过真实 engine.asof API 创建 SessionEnvelope、冻结 CareerBlindDraft，并调用 compute_freeze_package_sha256()。
7. create-only 写入该案 asof-blind-judgment-n50-frozen-draft.json，明确 feedback_opened=false。
8. 从落盘内容重建或保留真实 CareerFreezePackage，调用 verify_freeze_package_hash()；同一规范投影复算哈希必须相同。
9. 在第 7–8 步成功前，严禁读取该案 feedback.md。

允许先批量完成全部入选案阶段一，再批量阶段二。

### 4.2 阶段二

1. 仅当对应 frozen-draft 文件已 create-only 落盘且哈希复验通过后，才读取该案 feedback.md。
2. 若反馈无可评分事业事件，记录无效样本；不进入命中率分母，不牵强创建 verified-result。
3. 有可评分事业事件时，构造 VerificationInput 并通过真实核验 API 生成权威记录。
4. 四选一结果口径：CONFIRMED、PARTIAL_HIT、REJECTED、UNKNOWN（证据不足）。WITHHELD 若由引擎产生，报告中归入证据不足，不计命中。
5. 非 REJECTED 事件如运行完整 session runner，必须为每个事件提供一一对应的 CareerImpactSuggestion 与 CareerImpactAdjudication，并选择冻结包内的 CareerFundamentalAdjudication；不得绕过哈希、身份或状态门。
6. create-only 写入该案 asof-blind-judgment-n50-verified-result.json。

## 5. 根源 × 完成方式白名单

主事件仅允许：

- STRONG_ROOT + ACTIVATE_EXISTING
- STRONG_ROOT + REPAIR_DEFECT
- WEAK_ROOT + COMPLETE_LATENT
- WEAK_ROOT + TEMPORARY_SUBSTITUTE
- NO_ROOT + TEMPORARY_SUBSTITUTE

INVALID_COMPLETION 仅允许用于反证审计，不得作为主事件写入冻结包。

## 6. 污染预算与停止条件

污染预算为 3 次。污染事件包括：在对应阶段一冻结落盘前读取该案 feedback.md 或反馈类制品；搜索/命令输出候选反馈正文；盲态截断后仍含明确现实履历而继续执行；冻结后改写预测以贴合反馈。

- 第 1–2 次：停止当前案，记录事件，重新进行安全审查后方可继续下一固定候选。
- 第 3 次：第一段立即 BLOCKED，不得降低标准或继续凑数；仍按用户要求进入第二段 geju 裁决。

## 7. 统计与裁决

新增有效样本：反馈中存在可评分事业事件，且完成冻结先于反馈、哈希复验、权威核验四选一。

命中分子：CONFIRMED + PARTIAL_HIT。

累计分母：历史有效 N=5 + 本轮新增有效数。无效样本、污染淘汰、UNKNOWN/WITHHELD 的处理必须分别披露；UNKNOWN/WITHHELD 若已经构成可评分事业事件则进入有效分母但不计命中，不得静默删除。

第一段唯一裁决：

- PASS / COMPLETE — EVIDENCE-BOUNDED FREEZE：累计有效 N≥50，协议、哈希与写集验证通过；
- BLOCKED — <具体原因>：污染预算耗尽、92 案用尽仍不足 N=50、create-only 冲突、引擎合同无法满足或证据不完整。

## 8. 新增文件白名单

只允许新增：

1. 本合同；
2. 被执行案例目录内的 asof-blind-judgment-n50-frozen-draft.json；
3. 有效可核验案例目录内的 asof-blind-judgment-n50-verified-result.json；
4. reports/as-of-life-state-blind-judgment-n50-extension-report.md；
5. plans/as-of-life-state-next-task-geju-adjudication-2026-07-29.md。

禁止修改任何既有文件，尤其是 engine/asof/、tools/as_of_blind_judgment_probe.py、既有报告、既有合同、案例原文件、测试与 handoff.md。禁止 Git 与 GitHub 操作。

## 9. 第二段边界

第一段无论 PASS 或 BLOCKED 都继续 geju 裁决。第二段只裁决候选 A/C/D，不实施任何候选；必须在第一段报告落盘后读取指定证据并加载 geju skill。
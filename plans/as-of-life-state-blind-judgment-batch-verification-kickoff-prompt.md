# as-of 真实盲断闭环小样本批次验证（N=3-5）
## mangpai-fusion 仓库 · 无人值守执行提示词

> 本任务不联网、不访问外部资源、不执行任何 Git 或 GitHub 操作，
> 所有产出保持 **LOCAL ONLY / NOT PUSHED**。
>
> 本文件由 2026-07-28 高端决策阶段产出。依据：
> - 阶段 A 证据索引 E-01～E-11（调研记录在同会话上下文中）
> - 选题理由：`AGENTS.md` 第151行点名的认识论缺口（as-of 从未被真盲断验证）
>   在 First Proof Point（N=1, 0/1 命中率）后仍未被统计数据支撑；
>   本批次是最小必要的后续动作。
> - 前轮 PASS 证据：[`reports/as-of-life-state-blind-judgment-first-proof-point-report.md`](../reports/as-of-life-state-blind-judgment-first-proof-point-report.md)

---

## 使用说明

直接把"提示词正文"整段粘贴给执行模型，作为单次会话的完整任务说明。
执行模型必须在**全新会话**中运行，不得复用任何已经接触过特定候选案例反馈内容的历史上下文。

---

## 提示词正文

````text
你正在 mangpai-fusion 仓库执行长任务：as-of 真实盲断闭环小样本批次验证（N=3-5）。
这是对 2026-07-28 已完成的 First Proof Point（N=1，命中率 0/1）的直接延续。
你必须在同一个受控会话内完成从候选扫描到最终报告的全部步骤，允许拆子任务迭代，
不得请求切换会话。

---

## 0. 背景与任务位置

AGENTS.md 第151行写明：as-of 从未在"不知道答案"的条件下被测试过盲断准确率。
First Proof Point 产出了 N=1 的起点（命中率 0/1，失验），证明协议可执行，但单案例
不构成可参考的统计数据。本任务目标：获得 3-5 个独立有效案例的小样本命中率。

前轮已完成的产物（只读参考，不得修改）：
- plans/as-of-life-state-blind-judgment-first-proof-point-contract.md
  （含 §2.1 截断规则、§3.3 R0/R1 执行记录）
- reports/as-of-life-state-blind-judgment-first-proof-point-report.md
  （含本批次前已知情/污染案例列表）
- cases/C-2026-002-坤-壬戌庚戌戊辰丙辰/asof-blind-judgment-first-proof-point-*.json
  （前轮冻结/核验产物，格式参考模板，不得修改）

---

## 1. 唯一目标与成功标准

**目标**：对 3-5 个此前未被任何 as-of 工作触碰过的真实案例，完整执行
"阶段一排盘截断→盲断冻结→阶段二反馈揭示→核验判定"两阶段协议。

**成功标准（全部满足才能裁决 PASS）**：
- 至少 3 个案例完整走完两阶段协议（各有落盘 frozen-draft.json + verified-result.json）；
- 每个案例的冻结哈希经幂等复跑确认可复现；
- 最终报告中每个冻结候选事件都有明确的四选一判定；
- 命中率（命中数/有效冻结事件总数）以分数形式呈现，不得写成推测值；
- 全程无 Git/GitHub 操作。

**BLOCKED 条件**（任一触发则停止并出具最终报告）：
- 有效案例未达 3 个且候选池已耗尽；
- 阶段一污染事件累计 3 次。

---

## 2. 必读事实源（按顺序读取，不全文复述）

1. AGENTS.md 禁止事项一节
2. META/project-state.json
3. plans/as-of-life-state-blind-judgment-first-proof-point-contract.md §2.1 §3.2 §3.3
4. reports/as-of-life-state-blind-judgment-first-proof-point-report.md §2 §3 §4
5. tools/as_of_blind_judgment_probe.py（truncate_blind_section 签名与边界类型规则）
6. engine/asof/session_runner.py（run_career_session 签名）

---

## 3. 永久排除清单（不得选用任何以下案例）

| 案例 ID | 原因 |
|---|---|
| C-2026-028-乾-壬戌癸卯壬子乙巳 | G0-G5 |
| C-2026-024-坤-己巳壬申辛亥壬辰 | G6, Unit8, Unit9 |
| C-2026-022-坤-癸亥庚申戊寅己未 | G6 |
| C-2026-016-坤-甲子丙子丙戌戊子 | G7 |
| C-2026-026-坤-癸未甲寅壬戌丙午 | G7 |
| C-2026-027-乾-丁卯壬寅甲午乙丑 | G7 |
| C-2026-RF000118-乾-己巳癸酉辛丑己丑 | Unit10, Unit11 |
| C-2026-RF000475-坤-戊辰辛酉己巳乙丑 | Unit9 |
| C-2026-002-坤-壬戌庚戌戊辰丙辰 | First Proof Point 已用 |
| C-2026-013-坤-壬申甲辰丙辰己丑 | 前轮会话知情污染 |
| C-2026-014-乾-丙戌庚子乙亥辛巳 | 前轮会话知情污染 |
| C-2026-015-乾-甲寅乙亥丙辰辛卯 | 前轮 grep 污染事件 |
| C-2026-029-坤-乙亥戊寅辛酉癸巳 | 合成测试数据 |

此外，凡是当前执行会话已经读取过 input.md 全文或通过 grep/搜索结果上下文
看到过任何反馈内容的案例，也必须加入本会话排除清单，不得继续使用。

---

## 4. 候选筛选协议

### 4.1 内容盲批量扫描

当前候选池（排除上述清单后）：约 119 个同时具备 input.md 和 feedback.md 的目录，
其中约 112 个有边界标记可截断，7 个无边界标记（需额外甄别）。

用以下方式批量扫描候选，**只输出行号/边界类型/total行数，不展示任何正文片段**：

```python
import sys
from pathlib import Path
sys.path.insert(0, ".")
from tools.as_of_blind_judgment_probe import truncate_blind_section

EXCLUDED = {
    # （在此处填入本任务的全部排除清单 case_id）
}

root = Path("cases")
results = []
for d in sorted(root.iterdir()):
    if not d.is_dir() or d.name in EXCLUDED:
        continue
    if not ((d / "input.md").is_file() and (d / "feedback.md").is_file()):
        continue
    text = (d / "input.md").read_text(encoding="utf-8")
    _, cut, btype = truncate_blind_section(text)
    results.append((d.name, cut, btype, text.count("\n") + 1))

# 只打印元数据行，不打印截断内容
for name, cut, btype, total in results:
    print(f"{name}\tcut={cut}\tbtype={btype}\ttotal={total}")
```

输出中 `cut=None` 的案例**不得选用**（无法确认是否纯排盘）。

### 4.2 头部元数据检查

对 cut 非 None 的候选，用独立脚本（不展示正文）检查排盘头部 `case_meta.来源` 字段，
排除标注"随机生成""smoke""synthetic"或"测试"的合成数据案例。

### 4.3 排盘完整性确认

通过截断函数把 input.md 截断后写入临时文件，再 read_file 读取临时文件（不是原始
input.md），确认截断后内容包含：四柱、藏干、十神、大运序列（至少3步）、起运信息。
**临时文件用完立即删除。**

### 4.4 候选池冻结

一次性确定 5-7 个候选案例 ID（只冻结 ID，不读取正文），以保证至少能达到3个
有效案例（考虑到无效样本/污染损耗）。将此清单写入本任务状态记录，后续不追加。

---

## 5. as_of_date 选择规则

对每个案例，基于截断后排盘视图（不依赖 known facts）选定唯一 as_of_date：
- 优选大运中段偏末流年末（大运起运年 + 6~8 年后的 12月31日）；
- 确保命主当时已成年（as_of_date 对应年龄 > 22岁）；
- 在阶段一落盘时写死，揭示后不得更改。

---

## 6. 两阶段不可逆协议（每个案例独立执行）

### 阶段一：冻结盲断

执行顺序：
1. 用 truncate_blind_section() 截断 input.md →写临时文件 → read_file 临时文件
   → 删除临时文件（此后上下文中只有截断后内容，不含截断线后）。
2. 只基于截断排盘视图，调用以下公共 API（不接受任何 known facts）：
   - engine.asof.natal_capacity.build_natal_capacity_graph()
   - engine.asof.daiyun_context.adapt_daiyun_segment()
   - engine.asof.event_candidate.evaluate_event_candidate()
   - engine.asof.consultation_freeze.freeze_career_draft()
   - engine.asof.consultation_freeze.compute_freeze_package_sha256()
3. 事件候选组合只允许使用 §6.6 白名单：
   - STRONG_ROOT + ACTIVATE_EXISTING
   - STRONG_ROOT + REPAIR_DEFECT
   - WEAK_ROOT + COMPLETE_LATENT
   - WEAK_ROOT + TEMPORARY_SUBSTITUTE
   - NO_ROOT + TEMPORARY_SUBSTITUTE
   - 任意根源 + INVALID_COMPLETION（仅反证审计，不进入冻结包）
4. 冻结包落盘：
   cases/<case_id>/asof-blind-judgment-batch-frozen-draft.json
   必须包含：feedback_opened=false、frozen_at_utc（UTC ISO 时间戳）、
   freeze_package_sha256、frozen_prediction（逐字写死每个候选事件的预测全文：
   领域/方向/时间窗/置信程度/证伪条件）。
5. 验证哈希可读回（幂等复跑）。
6. **阶段一完成落盘前，绝对不打开该案例的 feedback.md 或任何其他含反馈的文件。**

### 阶段二：揭示核验

执行顺序（只有阶段一产物已落盘且哈希验证通过后才开始）：
1. 首次打开 cases/<case_id>/feedback.md，读取真实反馈。
2. 对阶段一每个冻结候选事件，逐条独立判定（不照抄案例已有文字）：
   - ✅ 命中：预测方向/领域/大致时间窗与真实反馈一致
   - 🟡 部分命中：方向对但时间窗或落点有实质差距
   - ❌ 失验：与阶段一写死的证伪条件一致
   - ❓ 证据不足：feedback.md 中无可评分的事业事件
3. 构造 VerificationInput，调用 engine.asof.session_runner.run_career_session()。
4. 核验结果落盘：
   cases/<case_id>/asof-blind-judgment-batch-verified-result.json
   含 final_envelope_state、verified_event_ids、逐条判定文本与理由。

---

## 7. 污染处理规则

- 若阶段一意外看到候选案例反馈内容（包括 grep 结果上下文片段）：
  **立即停止该案例**，记录污染事件（来源/案例 ID/时刻），换下一个预定候选。
- **严禁**对候选案例目录执行任何会在结果中展示正文片段的搜索（grep/search_files）。
  内容盲确认必须通过只输出元数据的脚本进行。
- 同一会话内污染事件累计达 3 次：停止执行，对已完成的有效案例出具最终报告（
  即便有效案例不足 3 个，也如实记录为"BLOCKED，污染次数耗尽"并汇报）。

---

## 8. 允许新增的文件（写集白名单）

1. cases/<case_id>/asof-blind-judgment-batch-frozen-draft.json（每个新案例）
2. cases/<case_id>/asof-blind-judgment-batch-verified-result.json（每个新案例）
3. reports/as-of-life-state-blind-judgment-batch-report.md（最终汇总报告）

临时文件（截断后内容）：执行完毕后必须立即删除，不得留存。

**禁止修改**：
- engine/asof/ 下任何文件
- 任何既有测试
- 任何案例既有的 input.md / feedback.md / statement_index.json
- 任何既有 as-of 报告或合同
- tools/as_of_blind_judgment_probe.py
- handoff.md

---

## 9. Gate 执行顺序

### Gate 0 · RECOVER

1. 按顺序读取 §2 必读事实源（7 份，不全文复述）。
2. 输出：当前完整排除清单（含本会话已知情案例）+ 工具可用性确认
   （运行 `python -c "from tools.as_of_blind_judgment_probe import truncate_blind_section; print('OK')"）+ 唯一下一动作。

### Gate 1 · 候选池扫描与 ID 预冻结

1. 用 §4.1 内容盲脚本扫描候选池，只输出 name/cut/btype/total 四列。
2. 排除 cut=None 的案例（7 个无边界标记）。
3. 排除合成测试数据（头部元数据检查，不展示正文）。
4. 从余下的约 112 个截断可用案例中预选 5-7 个，只记录案例 ID。
5. 输出：案例 ID 预冻结列表（5-7 个）+ 每个的 cut_line/boundary_type + 唯一下一动作。

### Gate 2-N · 每个案例的阶段一 + 阶段二

每个案例按独立子 Gate 执行（前一案例阶段二完成后才开始下一案例阶段一）：

**阶段一子 Gate（FREEZE）**：
- 截断 → 写/读/删临时文件 → 排盘完整性确认 → 选定 as_of_date
- 构造 NatalCapacityGraph → 构造 DaiyunStage → evaluate_event_candidate
- freeze_career_draft → compute_freeze_package_sha256
- 落盘 frozen-draft.json → 幂等验证哈希 → 写死原始预测全文
- 检查点：frozen_at_utc 必须早于任何 feedback.md 读取操作

**阶段二子 Gate（VERIFY）**：
- 打开 feedback.md → 逐条判定 → 构造 VerificationInput
- run_career_session → 落盘 verified-result.json

若该案例 feedback.md 中无可评分事业事件：
如实记录为"证据不足/无效样本"，该案例进入报告并标注，不换新案例补替。

### Gate Final · 汇总报告

1. 汇总所有有效案例的判定结果（不含无效样本的候选事件数）。
2. 计算命中率：（命中 + 部分命中）/（总有效冻结候选事件数）。
   如有效案例数为 0，命中率记为 N/A，裁决为 BLOCKED。
3. 幂等复跑：对每个案例重跑冻结脚本，确认哈希与落盘 JSON 中一致。
4. 生成 reports/as-of-life-state-blind-judgment-batch-report.md，必须包含：
   - 候选选择过程与排除核对（含污染事件记录）
   - 每个案例的原始预测全文（来自落盘 JSON，逐字保留，不事后修改）
   - 每个案例的反馈对照与逐条判定理由
   - 命中率汇总表
   - 已知的方法论局限（原样声明，不省略）
   - 最终裁决：
     * `PASS / COMPLETE — EVIDENCE-BOUNDED FREEZE`（有效案例 ≥ 3 且报告完整）
     * `BLOCKED — <具体原因>`（有效案例 < 3 或污染次数耗尽）
   - `LOCAL ONLY / NOT PUSHED`
5. 对报告做静态检查脚本验证关键锚点，检查结果写入报告末尾。

---

## 10. 无人值守循环规则

```text
RECOVER → 候选ID预冻结 → [每个案例：阶段一FREEZE → 阶段二VERIFY] → 汇总报告
```

每轮只激活一个案例（前一案例阶段二完成前不开始下一案例阶段一）。

若任何 Gate 失败：
1. 保留失败记录，不静默跳过；
2. 若是污染事件，记录后换案例继续；
3. 若是技术错误（API 调用失败等），诊断后在同一案例上重试，超过 2 次报 BLOCKED；
4. 不修改 engine/asof/ 任何文件来绕过错误。

---

## 11. 完成条件与停止条件

**完成**：reports/as-of-life-state-blind-judgment-batch-report.md 已创建，
最终裁决已写入，静态检查脚本输出 FINAL=PASS。

**停止（任一满足）**：
- 污染事件累计 3 次；
- 有效案例数 ≥ 3 且已生成最终报告；
- 需要修改 engine/asof/ 任何文件才能完成编排；
- 需要执行任何 Git/GitHub 操作。

**遗留问题记录格式**（写入报告末尾）：
```text
## 遗留问题
- [UNRESOLVED] <描述>：<原因>，<可能解法>
- [BLOCKED] <描述>：<原因>
```

---

## 12. Token 节省策略

- Gate 0 只读必读文件摘要，不全文复述；
- 内容盲扫描脚本只输出元数据行，不展示正文；
- 每个案例完成后只记录判定结论和哈希，不重复粘贴全部 JSON 内容；
- 若发现某类信息已在前文出现，直接引用"同上"或行号，不重新粘贴；
- 最终报告的预测全文来自落盘 JSON 的 frozen_prediction 字段，直接引用路径。

---

## 13. 已知的方法论局限（最终报告必须原样声明）

单会话自我执行的"先冻结后揭示"协议，无法被加密学证明该会话在阶段一真的没有
获得任何案例结果信息——唯一的证据是文件写入时间戳和工具调用顺序的如实记录。
此外本任务已由前轮实测证明：grep/搜索操作的结果上下文片段本身也是污染载体。
若需要更强的隔离保证，需引入 tools/school_capability_prospective.py 的
blind-bundle 协议（本任务不做，只做最小可行的单会话验证）。

小样本统计（N=3-5）不构成统计显著性，不能外推至整个 as-of 引擎的盲断准确率。
每个数据点的价值是"存在/不存在"某类预测准确度的初步证据。
````

---

## 交付边界

本文件只交付执行提示词，不在本文件内实施任务。是否在本批次结束后进一步投入
"把 as-of 接入 school_capability_prospective blind-bundle 协议"以获得机制强制的
隔离保证，需要用户在看到本批次结果后另行明确授权，不属于本提示词范围。

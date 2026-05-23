---
inclusion: always
description: v1.2 报告生成前 AI 必须执行的自检清单（软约束 / 兜底护栏 #4）
---

# v1.2 输出前自检清单

> **角色**：本文件是 v1.2 流水线 ② preflight + ⑥ output_linter 之外的**第三层兜底**——
> "AI 自律层"。每次生成 `cases/C-XXX/analysis.md` 或 `reports/*.md` **之前**，
> AI 必须显式逐条勾选下列 8 条铁律 + 三层 gate 自检，并将结果**追加在 analysis.md 末尾**作为审计痕迹。
>
> 本清单与 `tools/output_linter.py` 11 项检查互为镜像：
> - linter 是程序兜底（机器读 yaml 黑名单 + 区间一致 + passed_layers 强等价）
> - checklist 是 AI 兜底（语义层、画像层、风险层）
>
> 任何一条没勾 → 报告必须降级 1 ★ 或回流到 D2/D3 引擎重跑。

---

## 一、8 条铁律自检（硬约束）

每生成一份报告，在 `cases/C-XXX/analysis.md` 末尾追加以下 checklist 块：

```markdown
## v1.2 输出前自检（@track-E checklist）

立案: C-2026-NNN-{干支}
生成时间: YYYY-MM-DD HH:MM
checker: AI-{model}/{run_id}

- [ ] 1. 双轨置信度：每条断语都含 `★N (XX%)`，且 ★ 与 % 在 06-confidence § 二 区间表内一致
- [ ] 2. 派别标签：每条断语含 `[段/杨/任/高/共识/互补/独门/冲突仲裁]` 中至少一种
- [ ] 3. evidence 链：每条断语挂 ≥1 个规律编号（MR-XXX / M1-D-XXX / M2-Y-XXX / M3-R-XXX / G-XX-XXX）
- [ ] 4. 应期断语完整：含 `yingqi_year`（具体年份）+ `falsifiable`（证伪条件）
- [ ] 5. 三层 gate：所有 ★★★★★ 应期 `passed_layers == 3`；★★★★ ≥ 2；★★★ ≥ 1
- [ ] 6. 黑名单：未引用 `engine/mechanical-rules.yaml` 中 blacklist 任何条目（XF-001/XF-002/XF-003 等）
- [ ] 7. 禁忌词：报告中无「未来某年」「可能」「一定」「肯定」「必然」「绝对」等被禁措辞（除非引用 MR 铁断且 gate 三层全过）
- [ ] 8. 一致性：EnergyFindings / PictureFindings / GateResult / SupportFindings 的 hash 链一致；cases-index.md / reports/ / predictions/ 在同一 commit 同步更新
```

**勾选规则**：
- ✅ 全勾 → 可正式输出
- ⚠️ 任一软警告（W7/W11/W8）→ 加 `[降级]` 标记并 -1 ★
- ❌ 任一硬错误（E1-E10）→ **不许输出**，回流到对应 agent

---

## 二、三层 gate 显式自检（应期专用）

对**每条** ★★★★+ 的应期断语，在 `analysis.md` 内追加：

```markdown
### 应期 X.Y · {事件} · {YYYY 年}

| 层 | 是否通过 | 关键字 | 说明 |
|---|---|---|---|
| L1 原局有     | ✅/❌ | 触发字 = `?`     | 例：日支子（婚宫）+ 月支寅藏丙偏财 |
| L2 大运到位   | ✅/❌ | 必需字 = `?`     | 例：庚辰运辰为财库对冲 |
| L3 流年引爆   | ✅/❌ | 6 触发哪一条 = `?` | 例：触发 3 合冲引动（流年与年支申合） |

passed_layers = `{N}`
★ 上限 = `{0/3/4/5}`（按 04-gate-protocol § 七）
最终 ★ = `min(规律置信度上限, gate 上限) - 变异度惩罚 - 过渡期惩罚`
```

**强一致**：表格的 `passed_layers` 与该条断语的 ★ 必须满足
`tools/three_layer_check.check_yingqi()`，否则 linter 会拒绝。

---

## 三、上游约束自检（D2/D3 越界检查）

报告输出前，AI 显式回答以下问题（追加到 analysis.md 一节"上游约束自检"）：

1. **D2 是否违背 D1 wealth_ceiling？**
   - 例：D1 给 `中富级·上`，D2 不能输出"千万级收入画面"
2. **D3 是否违背 D2 marriage_picture？**
   - 例：D2 给 `初婚窗口 [22, 28]`，D3 不能在 35 岁判初婚（这是 v1.0 → v1.2 的核心修正）
3. **D4 是否新提结论（违反"旁证"原则）？**
   - 例：D4 不能独立预测未来事件，只能 boost 已有 D1/D2/D3 结论
4. **跨派冲突是否登记？**
   - 任何 ≥2 派对立必须挂 `CrossSchoolConflict`，仲裁后写入 `META/arbitration-log.md`

---

## 四、与 v1.0 失败的对比检查

特殊提醒：以下三种 v1.0 失败模式 **绝对禁止**重复：

| v1.0 失败模式 | v1.2 自检拦截点 | linter 错误码 |
|---|---|---|
| C-2026-001 婚期差 8 年（2013 vs 2005） | 三层 gate + D2 marriage_picture 上游约束 | E6（passed_layers≠3） |
| C-2026-002 "五凶煞=婚凶"被当铁断 | XF-002 黑名单 | E10 |
| C-2026-014 学历 985/211 高估一档 | 共识层不允许跨派单独升 ★ + D2 上游约束 | W11/E2 |

每次生成婚姻 / 学历 / 应期断语，AI 必须显式标注："我已确认未重复 v1.0 这条失败模式 X"。

---

## 五、checklist 失败时的回流流程

```
checklist 不通过
     │
     ├─ E1 (★/% 区间不符) ────► 回 render_report 重跑置信度计算
     ├─ E2 (无派别标签)    ────► AI 补 [XX] 标签即可
     ├─ E3 (无 evidence)   ────► 回 D1/D2/D3/D4 各引擎补 trace_id
     ├─ E4/E5 (应期不全)   ────► 回 D3 yingqi_gate 重跑或丢弃该候选
     ├─ E6 (gate 不达标)   ────► 降级该断语 ★ 或丢弃
     ├─ E7 (禁忌词)        ────► AI 改写为具体年份/概率化措辞
     ├─ E10 (黑名单)       ────► 删除该断语 + 用 replacement_rules 重写
     └─ W11 (断语过少)     ────► 仅警告，可加 ⚠️ 标记后输出
```

---

## 六、版本演进

| 版本 | 日期 | 变更 |
|---|---|---|
| v1.2.0 | 2026-05-23 | 初版（Track-E 兜底护栏 5 件套之一） |

任何修改本清单 = PR 标 `[CHECKLIST]`，整合 agent 批准。

---

**自检清单结束。每份报告必须在末尾追加本清单的勾选块，否则视为不合规交付。**

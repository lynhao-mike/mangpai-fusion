# Case C-2026-016-甲子丙子丙戌戊子 · 教训登记

> 本案 = v1.3.0 + v1.4 W1 上线后**首例真实命主跑通完整 pipeline 的案例**。
> 由命理师于 2026-05-26 提交（用户对话直贴问真八字 APP 排盘信息）。
> 本文记录命理师 / 架构师在产出 master 报告过程中暴露的引擎问题（CFL）+ 校准建议。

---

## 一、Pipeline 端到端验证

| 步骤 | 状态 | 备注 |
|---|---|---|
| preflight 11 步 schema 校验 | ✅ PASS | 指纹 `d9637d73ffee`；首次踩 2 个 schema 边界（见 § 二）|
| D1 段派能量评估 | ✅ | 做功 1 层 / 体用结构 / 财富天花板=小富级·中 |
| D2 杨派画面合拍 | ✅ | wealth_level=旺官 / 行业方向=公门/技术/文教 / 五步法全跑通 |
| D3 任派应期三层门 | ⚠️ | 12/12 候选全 passed=3/3 → 全 ★5 (95%) 怀疑"宽进"|
| D4 高派旁证 | ✅ | 孤鸾煞挂日柱 / 学业辅佐 +3% / career 域 boost +16% |
| integrate | ✅ | 16 条 final_conclusions / overall ★5 (91.2%) |
| render_both | ✅ | master 15960 字符 / 20 sid / client 14775 字符 / 1 sid |
| output_linter | （未跑）| TODO 命理师定稿前应跑一次 W9/W10 |

---

## 二、首例工程债（CFL · v1.4 backlog）

### CFL-C016-001 · preflight 起运年公式过于简化（P2）

**症状**：用户提供的真实起运时间 = 出生后 3 年 7 月 1 天 19 时（≈3.586 实岁）。
preflight 公式 `起运年 = birth_year + floor(起运岁)` = 1984 + 3 = **1987**。
但实际命主 1987 仍在小运，1988 年 7 月才入第 1 大运乙亥。本案 yaml 中
`起运岁` 被迫四舍五入为 4.0 才能让 preflight 过——损失精度。

**根因**：preflight 的公式假设"出生后整年 = 一岁起运"，但真实命理是
"出生后多少年多少月多少天起运"——分数部分 > 0.5 时应该 ceil 而非 floor。

**建议修复（v1.4 W2/W3）**：
- `tools/preflight._check_dayun` 改为允许 `起运岁` 是浮点 + 起运年使用 `round()`
- 或新增 `起运精确时间: "3年7月1天19时"` 字段保留精度

**锚点**：
- 触发条件：`起运岁` 小数部分 ≥ 0.5
- 影响案例：C-2026-016（本案）

### CFL-C016-002 · D3 应期"宽进"问题（P1）

**症状**：本案 12 条候选事件全部 passed_layers=3/3 → 全部 ★5 (95%)。这违背了
"三层齐备才下铁口断"的设计意图——铁口断应该是稀有信号，不应该每年都给。

**疑似原因**：
1. `gate_yingqi` 的 L1/L2/L3 检查对"官杀重 + 戌库 + 印食并透"这种
   富 evidence 命局太宽容
2. **没有"挫折/凶应"的对照 gate**——只有"事件可发生"的肯定推理，没有"事件不应发生"的否定推理
3. 本案三子聚水 + 大运壬申 (2018-2027) 全期都是"杀才"动 → 几乎所有年份都满足 L2 / L3

**建议修复（v1.4 Track 5 婚姻应期模型 + 后续 v1.5 应期 v2）**：
- 增加 `gate_falsifiability_check`：当 N 年内 ≥3 条 ★5 时，提醒命理师"是否过密"
- D3 的 ★5 上限改为 4 当上下游 known_facts 缺失时（即"前向预测"模式 → ★4 顶）
- 加入"凶应反向 gate"：戊辰冲日支戌时，应触发婚变/工作变动的"反向警示"而非和"正应期"同列

**锚点**：
- 影响 G6（v1.2 ★5 三层 gate 通过率 = 100%）的语义——通过率高不代表准确率高
- 关联 v1.4 Track 5 婚姻应期模型（依赖 N_eff ≥ 30 切 Beta）

### CFL-C016-003 · "整体能量：无 (23%)" vs "段派置信度 ★5 (94%)" 自相矛盾（P3）

**症状**：master 报告 § 一 显示：

```
**整体能量**：无 (23%)
<!-- 段派 D1 置信度：5星 / 94% -->
```

23% 是极低的能量评分，但置信度却是 ★5/94%。这是命理师/命主肉眼立刻就能发现的矛盾。

**根因**：D1 EnergyFindings 把"评估出来的能量值"和"评估这个值的置信度"两个概念混在了一起渲染。
应该分别表达：
- "命主能量等级 = 无（23/100）"——这是**结论**
- "本结论置信度 ★5 (94%)"——这是**对结论的置信度**

**建议修复（v1.4 W2/W3 报告模板）**：
- `templates/report-v1.3.md` § 一 区分两行：
  - 结论行：`命主整体能量：弱 / 评分 23/100`
  - 置信度行：`本结论引擎置信度 ★5 (94%)（来源：M1-D-001 段派 4 层签字律）`

### CFL-C016-004 · render 没把 parsed 挂到 output._parsed（P2 工程层）

**症状**：`run_pipeline(parsed)` 返回的 `AnalysisOutput` 没有 `_parsed` 字段。
导致 `render_from_output` 的 fallback 走 `_minimal_parsed_from_energy` 构造 stub
→ 报告头部 `命主：—命 · —` 全是 dash。

**绕开方法**（已在本案使用）：
```python
out = run_pipeline(parsed, write_findings=True)
object.__setattr__(out, "_parsed", parsed)  # 关键
both = render_both(out)
```

**建议修复（v1.4 W2 一行改）**：
- `engine/pipeline.run_pipeline` 在 return 前加 `object.__setattr__(output, "_parsed", parsed)`

### CFL-C016-005 · retrospective scan `'DayunStep' object has no attribute '起讫年'`（P3）

**症状**：pipeline 跑完时 stderr 显示
`retrospective scan 失败：'DayunStep' object has no attribute '起讫年'`。
不影响主流程（warn-only），但 retrospective 模块功能丢失。

**根因**：`engine.yingqi.retrospective` 期望 DayunStep 有 `起讫年` 属性，
但 `engine.predicates.types.DayunStep` 只有 `起讫`（YYYY-YYYY 字符串）。

**建议修复（v1.4 W2 一行改）**：
- 在 `DayunStep` 加 `@property def 起讫年(self) -> tuple[int, int]:` 解析 self.起讫
- 或 retrospective 改用 `step.起讫.split("-")` 兼容字符串

---

## 三、本盘的命理观察（命理师视角）

> 注：以下为命理师对引擎产出的批注，**不进入引擎置信度计算**——仅供后续案例对照。

1. **格局判读**：丙日主 / 三子聚官 / 食神制官 + 偏印化官 + 比劫帮身——这是一个
   "印化食制"双向解决官攻身的中等格局。引擎产出"小富级·中（L4-L6）" 与命理师
   直觉一致。
2. **婚姻**：当前 41 岁 + 婚姻最佳窗口 22-28 岁已过 14 年——引擎自动提示"⚠️ 已无指导意义"。
   若命主仍未婚，关注 2024 甲辰（辰戌冲夫宫）+ 2028 戊申（申冲戌再来）的窗口。
3. **事业**：引擎 12 条事业应期全 ★5 → 实战检验需命主反馈。命理师初判：当前壬申大运
   2026/2027 是"动荡年"（午冲子三子 + 申冲戌夫宫），不是"晋升年"。引擎给"事业变动"
   是合理的，但 95% 置信度过高。
4. **2028 换辛未大运**——辛财透 + 未未来不冲（本命无未）→ 是"财源开启"信号。引擎
   也判 2028 财源/置业 ★5——这一条命理师认同，但仍建议下调到 ★4。

---

## 四、跨派一致性快照

- 段派 D1 / 杨派 D2 / 任派 D3 / 高派 D4 全部产出非空结论
- 共识层 0 条 / 互补层 3 条 / 独门层 13 条 / 冲突仲裁 0 条
- **独门层占 81%** → 跨派映射 27% 覆盖率的预期（mapping/INDEX.md）
- 本案归档后 case_count 应 +1（待 ingest_feedback 后）

---

## 五、后续行动

1. **本案不立即触发 D8**——case_count 在 ingest 后才 +1。本案是新归档，无 feedback。
2. **等命主反馈到位后**：命理师按 § 一 工作流补 feedback.md 的 [y]/[n]/[?]/[skip]，
   然后跑 `python3 -m tools.feedback_ingest C-2026-016-甲子丙子丙戌戊子`。
3. **架构师 v1.4 W2 优先级**（基于本案教训）：
   - CFL-C016-002 P1 D3 宽进问题——可能需要 v1.5 应期 v2
   - CFL-C016-001 P2 preflight 起运年公式——简单修
   - CFL-C016-004 P2 _parsed 挂载 + CFL-C016-005 P3 retrospective 兼容——一行修
   - CFL-C016-003 P3 模板矛盾显示——模板改一行

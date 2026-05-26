# Case C-2026-016-甲子丙子丙戌戊子 · 教训登记

> 本案 = v1.3.0 + v1.4 W1 上线后**首例真实命主跑通完整 pipeline 的案例**。
> 由命理师于 2026-05-26 提交（用户对话直贴问真八字 APP 排盘信息）。
> 本文记录命理师 / 架构师在产出 master 报告过程中暴露的引擎问题（CFL）+ 校准建议。

> **2026-05-26 更新**：5 条 CFL 全部已修复并合并主线（PR #42）。详见 § 二 各条 "✅ 已修复" 标记。

---

## 一、Pipeline 端到端验证

| 步骤 | 状态 | 备注 |
|---|---|---|
| preflight 11 步 schema 校验 | ✅ PASS | 指纹 `d9637d73ffee`；首次踩 2 个 schema 边界（已修复）|
| D1 段派能量评估 | ✅ | 做功 1 层 / 体用结构 / 财富天花板=小富级·中 |
| D2 杨派画面合拍 | ✅ | wealth_level=旺官 / 行业方向=公门/技术/文教 / 五步法全跑通 |
| D3 任派应期三层门 | ✅ | 12/12 候选 verified=False → ★4 (84%)（CFL-002 修复后）|
| D4 高派旁证 | ✅ | 孤鸾煞挂日柱 / 学业辅佐 +3% / career 域 boost +16% |
| integrate | ✅ | 16 条 final_conclusions / overall ★4 (91.2%) |
| render_both | ✅ | master 含命主信息 + 反馈位 / client 隐藏 sid |
| output_linter | ✅ | render_both 内嵌 lint 0 ERROR |

---

## 二、首例工程债（CFL · 全部已修复 · PR #42）

### CFL-C016-001 · preflight 起运年公式过于简化（P2）✅ 已修复

**症状**：用户提供的真实起运时间 = 出生后 3 年 7 月 1 天 19 时（≈3.586 实岁）。
preflight 公式 `起运年 = birth_year + floor(起运岁)` = 1984 + 3 = **1987**。
但实际命主 1987 仍在小运，1988 年 7 月才入第 1 大运乙亥。本案 yaml 中
`起运岁` 被迫四舍五入为 4.0 才能让 preflight 过——损失精度。

**根因**：preflight 的公式假设"出生后整年 = 一岁起运"，但真实命理是
"出生后多少年多少月多少天起运"——分数部分 > 0.5 时应该 ceil 而非 floor。

**已修复**（[`tools/preflight.py`](../../tools/preflight.py) `_check_dayun`）：
- `int(qiyun_sui)` → `round(qiyun_sui)`，3.586 → 4 → birth_year+4=1988 ✓
- 整数起运岁 9.0 不受影响（C-2026-015 兼容回归 PASS）
- 旧 floor 行为（3.586 + 起运年=1987）现在显式拒绝，错误信息提示用 round
- C-2026-016 input.md 已恢复为真实值 `起运岁: 3.586`
- 测试：`tests/v1_3_acceptance/test_cfl_c016_fixes.py::TestCFLC016_001_*` (4 cases)

### CFL-C016-002 · D3 应期"宽进"问题（P1）✅ 已修复

**症状**：本案 12 条候选事件全部 passed_layers=3/3 → 全部 ★5 (95%)。这违背了
"三层齐备才下铁口断"的设计意图——铁口断应该是稀有信号，不应该每年都给。

**疑似原因**：
1. `gate_yingqi` 没区分"已应验回填"和"前向预测候选"两种语义
2. 命理师注入的"候选时机"（应验度=0）和命主反馈的"已应验事件"（应验度=1）走同一计算路径

**已修复**（[`engine/yingqi/gate.py`](../../engine/yingqi/gate.py) `compute_yingqi_confidence` + `gate_yingqi`）：
- `compute_yingqi_confidence(verified: bool = True)` 新增参数：
  - `verified=True`（默认，向后兼容） → ★ 上限走 PASSED_LAYERS_TO_STAR_CEILING（3 层齐备 = ★5）
  - `verified=False`（前向预测）→ gate_ceiling -1，3 层齐备最高 ★4
- `gate_yingqi(verified: bool = True)` 透传到 confidence 计算
- `compute_yingqi_confidence` 内 ★ 被压低后，posterior 同步 cap 到该 ★ 区间
  上限（避免 ★4+95% 区间不一致触发 output_linter E1）
- `KnownFact.应验度: float = 1.0` 新字段（默认 1.0 兼容 legacy）：
  - ≥ 0.7 → verified=True；< 0.7 → verified=False
  - `tools/preflight._check_known_facts` 解析 yaml 中的 `应验度` 字段
  - `engine.predicates.types.adapt_parsed` 透传字段
- `engine.pipeline._extract_candidates` 返回 4 元组 `(year, event, domain, verified)`
- `run_pipeline` 把 verified 透传到 `gate_yingqi`

**实测**（C-2026-016 重跑）：
```
2010 婚姻       3/3 verified=False ★3 (66%)   <- 触发 +0.05 类型加成
2014-2035 全部  3/3 verified=False ★4 (84%)   <- 上限 4 ✓
```

- 测试：`tests/v1_3_acceptance/test_cfl_c016_fixes.py::TestCFLC016_002_*` (8 cases)

### CFL-C016-003 · "整体能量：无 (23%)" vs "段派置信度 ★5 (94%)" 自相矛盾（P3）✅ 已修复

**症状**：master 报告 § 一 显示：

```
**整体能量**：无 (23%)
<!-- 段派 D1 置信度：5星 / 94% -->
```

23% 是极低的能量评分，但置信度却是 ★5/94%。这是命理师/命主肉眼立刻就能发现的矛盾。

**根因**：模板把"评估出来的能量值"和"对该评估的置信度"挤在一行，前者用 % 单位
后者也用 %，肉眼无法区分。

**已修复**（[`templates/report-v1.3.md`](../../templates/report-v1.3.md) § 一）：
分两行显示：
```
**命主能量等级**：无（评分 23/100）
**引擎置信度（D1 段派）**：5 星 / 94%
```
- "评分 X/100" 明确是结论的能量值（绝对评分）
- "X 星 / Y%" 明确是引擎对结论的把握度
- 用文字"星 / %"格式而非 ★ 字符，避免该元信息行被 output_linter E2/E3 当
  断语扫描（误报"未含派别标签"+"缺 evidence 链"）
- 测试：`tests/v1_3_acceptance/test_cfl_c016_fixes.py::TestCFLC016_003_*`

### CFL-C016-004 · render 没把 parsed 挂到 output._parsed（P2 工程层）✅ 已修复

**症状**：`run_pipeline(parsed)` 返回的 `AnalysisOutput` 没有 `_parsed` 字段。
导致 `render_from_output` 的 fallback 走 `_minimal_parsed_from_energy` 构造 stub
→ 报告头部 `命主：—命 · —` 全是 dash。

**已修复**（[`engine/pipeline.py`](../../engine/pipeline.py) `run_pipeline`）：
- 入口 `parsed = adapt_parsed(parsed)`（idempotent，已是 ParsedInput 时直接 return）
- 出口 `object.__setattr__(output, "_parsed", parsed)` 把 adapt 后的 parsed
  挂到 output（不进 to_dict/to_json，仅供 render 取用）
- 测试：`TestCFLC016_004_005_PipelineAdaptAndMount::test_output_parsed_attribute_set`

### CFL-C016-005 · retrospective scan `'DayunStep' object has no attribute '起讫年'`（P3）✅ 已修复

**症状**：pipeline 跑完时 stderr 显示
`retrospective scan 失败：'DayunStep' object has no attribute '起讫年'`。
不影响主流程（warn-only），但 retrospective 模块功能丢失。

**根因**：preflight.DayunStep 用 `起讫: str` 字符串，engine.predicates.types.DayunStep
用 `起讫年: tuple[int, int]`。`scan_retrospective` 期望后者。但 `run_pipeline` 没在
入口统一 adapt，导致 retrospective 收到了未 adapt 的 preflight DayunStep。

**已修复**：与 CFL-C016-004 共享同一个修复（入口 adapt_parsed）。
- 测试：`TestCFLC016_004_005_PipelineAdaptAndMount::test_retrospective_no_attribute_error`

---

## 三、本盘的命理观察（命理师视角）

> 注：以下为命理师对引擎产出的批注，**不进入引擎置信度计算**——仅供后续案例对照。

1. **格局判读**：丙日主 / 三子聚官 / 食神制官 + 偏印化官 + 比劫帮身——这是一个
   "印化食制"双向解决官攻身的中等格局。引擎产出"小富级·中（L4-L6）" 与命理师
   直觉一致。
2. **婚姻**：当前 41 岁 + 婚姻最佳窗口 22-28 岁已过 14 年——引擎自动提示"⚠️ 已无指导意义"。
   若命主仍未婚，关注 2024 甲辰（辰戌冲夫宫）+ 2028 戊申（申冲戌再来）的窗口。
3. **事业**：CFL-002 修复后引擎产出 11 条 ★4 (84%) + 1 条 ★3 (66%) 应期断语，
   置信度合理（前向预测就该 ★4 顶）。命主反馈到位后，对应应验的年份会上 ★5。
4. **2028 换辛未大运**——辛财透 + 未未来不冲（本命无未）→ 是"财源开启"信号。引擎
   也判 2028 财源/置业 ★4 (84%)——命理师认同。

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
3. **5 条 CFL 全部已修复**（PR #42）。架构师 v1.4 W3 焦点可转向：
   - V5/V6 PictureFindings.industry_path / wealth_level.framework
   - 跨维度耦合 gate（CFL-C015-002 余债）
   - 婚姻应期模型 v2（依赖 N_eff ≥ 30 切 Beta）

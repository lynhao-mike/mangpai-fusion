# T-159 · 事业标签可行性审计（只读，不建标签）

- 状态：🔵 Ready for Execution
- 优先级：**P1（与 T-158 并行）**
- 创建：2026-10-29（中枢）
- 依据：`occupation` 620 例有事件，但事业规则有 4 条：角色变化（二值）+ 受雇/创业/混合（三分类）
- 前置：无

## 0. 一句话

判断 `occupation` 事件能否造出「角色变化」二值标签与「受雇 / 创业 / 混合」三分类标签。
**本卡只做审计与提案：不建标签、不评分、不建盘。**

## 1. 已核实的数据现状（中枢探针）

- `occupation` 事件 **957 条 / 620 例**（去重后）；polarity：neg 448 / pos 391 / unknown 118。
- 事件文本是长段落，常混多个域、常夹提问；**提问里的关键词不算证据**。
- 产品规则映射：`DUAN-EVENT-CAREER-ROLE-CHANGE-V1`、`DUAN-EVENT-CAREER-PATH-{EMPLOYMENT,ENTREPRENEURSHIP,MIXED}-V1`。

## 2. 审计内容（只读）

### 2.1 角色变化（二值）可行性

- 关键词候选：`升职`、`晋升`、`提拔`、`跳槽`、`换工作`、`换岗`、`调动`、`转行`、`辞职`、`裸辞`、
  `下岗`、`失业`、`岗位变化`、`职责变化`、`任职`、`入职`。
- 报：命中案例数、命中事件数、按 polarity 拆分、chart_ready 内命中数；
- 抽 20 例逐条看：关键词是否指命主本人、是否指角色变化而非泛泛「工作」；
- 给出建议定义与已知误判类型（不写标签文件）。

### 2.2 职业路径三分类（受雇 / 创业 / 混合）可行性

- 受雇候选词：`单位`、`公司`、`上班`、`职员`、`公务员`、`编制`、`国企`、`外企`、`私企`、`打工`、`任职`；
- 创业候选词：`创业`、`生意`、`开店`、`公司法人`、`自由职业`、`个体`、`经商`、`工作室`；
- 报：明确受雇 / 明确创业 / 两类都出现 / 两类都没有 的案例数；chart_ready 内各多少；
- 抽 20 例（尽量覆盖四类）判断三分类是否可判、主要歧义是什么；
- 给出「可判 / 勉强可判 / 不可判」的明确结论与理由。

### 2.3 边界

- 本卡不判断命主「实际职业路径」的真值，只判断**文本是否足以支撑标签**。
- 不建盘、不读八字、不评分；标签只从事件文本与 polarity 来。

## 3. 产物

- `tools/career_label_feasibility.py`（只读、幂等：`python -m tools.career_label_feasibility`）
- `META/career-label-feasibility-v1.json`：计数、关键词命中、20 例编号、结论
- `META/career-label-feasibility-v1.md`：漏斗、四类分布、20 例审计表、建议定义、可判性结论
- `tests/tools/test_career_label_feasibility.py`（确定性 + 提问不误判；可选）

**禁止**新建标签文件（`*labels*`）、禁止评分、禁止建盘。

## 4. File Scope

**允许新建**

- `tools/career_label_feasibility.py`
- `META/career-label-feasibility-v1.json`
- `META/career-label-feasibility-v1.md`
- `tests/tools/test_career_label_feasibility.py`

**只读**

- `cases/raw_feedback/parsed/real_cases_990.jsonl`
- `tools/timing_eval_set.py`（解析助手，只读 import）
- `theory/production/claim-rules-v1.yaml`（只看 4 条事业规则的 falsifier/conclusion）

**禁止**

- 建标签、评分、建盘、用盘面字段
- 改 JSONL、engine/**、theory/**、sources/**、既有测试
- `git commit / push / checkout / stash / reset / clean`

## 5. 验收（中枢亲自跑）

```bash
.venv\Scripts\python.exe -m tools.career_label_feasibility     # 退出码 0
.venv\Scripts\python.exe -m pytest -q                           # 0 failed，passed >= 1142
```

中枢额外检查：

- 计数可加（明确受雇 + 明确创业 + 两类都出现 + 两类都没有 = 有 occupation 事件的案例数）；
- 20 例审计表能回原文；
- 结论必须明确写「可判 / 勉强可判 / 不可判」，不许和稀泥；
- 没有偷偷生成标签文件。

## 6. 回报格式（`tasks/T-159/BRIEF.md` + `STATUS.md`）

1. **改动文件**
2. **原始输出**（计数 + 20 例审计）
3. **未完成与风险**（歧义类型、chart_ready 损失）
4. **下游须知**（角色变化是否可建、三分类是否可建、建议定义）

## 7. 禁止

- 不许用「大概像创业」这种模糊判断代替计数。
- 不许把「不可判」写成「勉强可判」来让任务显得完成。

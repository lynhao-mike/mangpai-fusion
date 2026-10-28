# T-161 · 事业角色变化标签 v1（1/null，去重文本）

- 状态：🔵 Ready for Execution
- 优先级：**P1（事业 4 条规则里唯一可判的标签）**
- 创建：2026-10-29（中枢）
- 依据：`META/career-label-feasibility-v1.md`（T-159）：角色变化「勉强可判」，路径三分类「不可判」
- 前置：T-159 已完成（`50819db9`）

## 0. 一句话

从 `occupation` 事件造 `role_change` 标签：**1 = 有角色变化证据；null = 无可用证据**。
**不造 0**（0 侧是沉默不是证据，T-159 已裁决）。只从事件文本与 polarity 来，不用任何盘面字段。

## 1. 已核实的数据现状（T-159，直接使用）

- `occupation` 案例 **620** / 事件 **957**；chart_ready **614**。
- 角色变化命中 **107 例**（17.3%），20 例审计 **17/20 成立（85%）**；误判类型：他人主体 2、意向语 1。
- 提问整段排除 79 条事件；**56 例全部事件都是提问**。
- 513 例非命中里：**411 例只提工作不提变化**、**102 例无事业话语** → 0 侧不可信。
- 去重后仍有 **19 组 40 条同文 occupation 事件**，其中跨案例 **16 组 32 条** → 建标签前必须按文本哈希再剔重。

## 2. 标签定义（预注册，不得中途改）

### 2.1 基础集

- `duplicate_key` 去重（992→959）；`gender ∈ {男,女}`；出生日期可解析；`chart_ready = 有出生时刻`。
- **文本再去重**：对 `occupation` 事件文本做规范化（去首尾空白、连续空白合一）后取 sha256；
  跨案例同文只保留 `raw_id` 最小的一条，其余记 `dropped_duplicate_text`；同案例内同文折叠。
- 先剔除提问文本，再判关键词。

### 2.2 关键词

`升职`、`晋升`、`提拔`、`跳槽`、`换工作`、`换岗`、`调动`、`转行`、`辞职`、`裸辞`、
`下岗`、`失业`、`岗位变化`、`职责变化`、`任职`、`入职`。

### 2.3 排除（任一命中即该事件不作证据）

- **他人主体**：关键词附近含 `父母/父亲/母亲/爸/妈/老公/老婆/妻子/丈夫/儿子/女儿/孩子/家人/家属/
  兄弟/姐妹/亲戚/朋友/爷爷/奶奶/姥姥/姥爷/公公/婆婆/岳父/岳母/兄长/姐姐/妹妹`，且不含 `我/本人/自己`。
- **意向语**：含 `希望/打算/准备/想/能否/是否/计划/有望`。
- **否定**：关键词前 6 字内出现 `无/没/没有/未/差点/并非`。
- **提问**：含 `？/?/是否/能否/请问/怎么样/吗/么/呢`。

### 2.4 标签

- `role_change = 1`：任一 `occupation` 事件通过上述过滤且命中关键词。
- `role_change = null`：其余（没有可用证据）。**不产生 0。**
- 另记 `work_no_change = 1`：案例有非提问 occupation 文本、但无干净命中（供未来敏感性，不是标签）。

## 3. 产物

- `tools/career_role_change_labels.py`（幂等：`python -m tools.career_role_change_labels`）
- `META/career-role-change-labels-v1.json`：
  - `schema`、`definition`、`frozen_at`、`source`（含 JSONL sha256）
  - `counts`：620 / 614 / role_change 1 / null / work_no_change / dropped_duplicate_text
  - `baseline`：`1/(1+null)`，全样本与 chart_ready 各一
  - `cases`：`case_id`（raw_id）、`gender`、`birth_datetime_raw`、`birth_dt`、`time_basis`、
    `chart_ready`、`role_change`（1/null）、`work_no_change`（0/1）、`evidence_events`
- `META/career-role-change-labels-v1.md`：漏斗、计数、基线、关键词/排除、**20 例审计**、已知误判、去重明细
- `tests/tools/test_career_role_change_labels.py`

复用：`tools/timing_eval_set.py` 的 `parse_clock_datetime`（只读 import）。

## 4. 基线

- `1/(1+null)`：全 620 例与 chart_ready 614 例各报一次。
- 另报 `work_no_change` 占比（仅参考，不进基线），以及去重删掉多少条事件、涉及多少案例。

## 5. File Scope

**允许新建**

- `tools/career_role_change_labels.py`
- `META/career-role-change-labels-v1.json`
- `META/career-role-change-labels-v1.md`
- `tests/tools/test_career_role_change_labels.py`

**只读**

- `cases/raw_feedback/parsed/real_cases_990.jsonl`
- `tools/timing_eval_set.py`、`META/career-label-feasibility-v1.json`
- `engine/**`（不建盘）

**禁止**

- 造 0 标签；用盘面字段；评分；建盘
- 改 JSONL、T-148/T-153/T-158/T-159 产物、engine/**、theory/**、sources/**、既有测试
- `git commit / push / checkout / stash / reset / clean`

## 6. 验收（中枢亲自跑）

```bash
.venv\Scripts\python.exe -m tools.career_role_change_labels      # 退出码 0
.venv\Scripts\python.exe -m pytest tests/tools/test_career_role_change_labels.py -q -o addopts="-ra --tb=short"
.venv\Scripts\python.exe -m pytest -q                             # 0 failed，passed >= 1246
git status --porcelain cases/                                     # 必须为空
```

中枢额外检查：

- 两次运行 JSON 哈希一致；
- `role_change` 只有 1/null，**没有 0**；
- 20 例审计能回原文；他人主体/意向/否定/提问四类误判都列出来；
- 去重明细可复跑；工具里无 `bazi/engine/ganzhi` 等盘面字段。

## 7. 回报格式（`tasks/T-161/BRIEF.md` + `STATUS.md`）

1. **改动文件**
2. **原始输出**（计数 + 基线 + 20 例审计 + 去重明细）
3. **未完成与风险**（误判类型、null 比例、去重影响）
4. **下游须知**（标签语义、可建盘案例、work_no_change 的用途）

## 8. 禁止

- 不许造 0；不许把「只提工作不提变化」折成 0。
- 不许用盘面特征打标。
- 不许为了阳性率调词；误判列出来。

## 9. 中枢裁决（2026-10-29 01:05）

1. **v1 验收通过**：`role_change` 1=85 / null=535，**无 0**；`work_no_change`=473；chart_ready=614；
   基线 15.86% / 16.04%；29 tests；两次运行哈希一致。
2. **20 例审计 18/20**，两例失败是词表缺口：`000066`「媳妇换工作」、`000236`「机会晋升」。
   另有「想/未」过排除 21 例真阳性、近似重复 `000537/000538`、`000667/000668` 仍可能泄漏。
   这些**本轮不扩词、不修**，只记录；要修另立 v2。
3. **标签性质**：1/null，`null` = 无可用证据，**不是阴性**；本标签只作审计资产，
   **不用于产品裁决**，直到 v2 修好词表/过排除并另做预注册的精度/提升检验。
4. 去重键按卡 §2.1 更严口径（规范化后移除全部空白再 sha256），以复现 T-159 的 19 组/40 条；
   已在 JSON `definition` 与 MD 记录。

# 审阅范围说明 · 2026-10-26（给 Gemini 4 / 任意外部审阅者）

> 这份文件只说明**该审什么、不该审什么、怎么验**。裁决依据以 `docs/adr/` 与 `META/project-state.json` 为准。
> 若只给审阅者一份文件，给这份；若给仓库，按下面「二、审阅顺序」读。

## 一、这一轮改了什么（9 个文件）

| 文件 | 类型 | 一句话 |
|---|---|---|
| `docs/adr/ADR-001-engine-agent-boundary.md` | 新增 · 已接受 | 引擎产事实+候选+护栏，Agent 裁决；取代旧决策 D |
| `docs/adr/ADR-002-delivery-vs-metric.md` | 新增 · 已接受 | 交付评分为主、准确率为副、四条一票否决 |
| `docs/adr/ADR-003-claim-conditions-and-school-routing.md` | 新增 · 已接受 | 先定局→再授权→再条件→最后裁决；三类框架依赖 |
| `docs/adr/README.md` | 新增 | ADR 索引与状态词 |
| `engine/contracts/23-claim-condition-protocol-v1.md` | 新增 · 已接受 | 三值逻辑、42 个带地址原子、`conditions_v2`、编译三态、5 条验收指标 |
| `engine/contracts/00-OVERVIEW.md` | 修改 | 决策 D 标注「已被 ADR-001 取代」，原文保留；契约树补 22/23 |
| `engine/contracts/README.md` | 修改 | 决策摘要 D 同步标注被取代 |
| `META/project-state.json` | 修改 | `current_phase` / `last_updated` / 新增 `decision_log`、`claim_condition_protocol`；被测试断言的字段未动 |
| `META/validation-corpus-v1.json` | 新增 | 验证题库分层清单（48 / 108 / 328 + 铁口箓 36 期） |

另有两份**非裁决**材料：`META/REVIEW-PACKET-2026-10-26.md`（给外部模型的 7 个问题）、本文件。

## 二、审阅顺序

1. `docs/adr/ADR-003`（核心：为什么人能用、系统不能；四段协议）
2. `engine/contracts/23-claim-condition-protocol-v1.md`（可执行细节：三值逻辑、原子表、框架依赖）
3. `docs/adr/ADR-001` / `ADR-002`（边界与记分）
4. `META/validation-corpus-v1.json` 的 `method` 与 `caveats`（题库口径）

## 三、不要把「未实现」当「已坏」

本轮只交付**协议与裁决**，**没有**交付代码：

- `engine/claims/`（原子求值器、条件 IR、编译器）**尚不存在**；
- `theory/claims/conditions-v2/`（条件化数据）**尚不存在**；
- 第一批 120 条断语（婚姻 + 学历）**尚未编译**。

审阅应针对「这个协议能否实现、是否自洽、指标是否可测」，而不是「为什么没跑起来」。

## 四、复核用的关键数字（2026-10-26 实测）

| 项 | 数值 | 出处 |
|---|---|---|
| 规则总数 | 3699（A 类 1658 + B 类 2041） | `theory/*/index.yaml` |
| A 类带触发条件 | 414 / 1658，且为中文散文 | 同上 |
| 现行谓词 | 16 个，全部整盘级 | `engine/predicates/condition_evaluator.py` |
| 6 张盘上的通过集合 | 3 种（理论上限 8） | `tasks/T-105/STATUS.md` |
| 六要素生产断语 | 16 条 | `theory/production/` |
| 盲测严格准确率 | 45.3%（77/170，18 例） | `META/blind-baseline-v1-2026-10-18.md` |
| 职业二分类 | 0.3625（门槛 0.425 / 0.60） | 同上 |
| 可用案例 | 48 例（≥3 年份事件，其中 14 例 ≥5） | `META/validation-corpus-v1.json` |
| 铁口箓 | 284 期 / 2392 题；有性别 36 期 / 299 题 | 同上 |

## 五、请审阅者回答的 5 个问题

1. ADR-001 与 ADR-003 的职责是否有重叠或隐含冲突？（引擎出候选 / Agent 裁决 / L3 结构否决三者的边界）
2. 契约 23 的三值逻辑 + 地址变量绑定（`as` / `$var`），是否足以表达 414 条散文条件？举出它**表达不了**的至少一类条件。
3. `requires_school_frame`（需本派框架）在 L3 的执行，是否引入循环依赖——frame 命题本身也要条件求值，谁先谁后？
4. 5 条验收指标（可求值率 / 地址绑定率 / 区分度 / 语义支持率 / 未知显性率）能否真的区分「编译对了」和「编译错了」？缺哪条最致命？
5. 有没有更省事的替代路径（例如先人工标注 200 条条件、再谈自动编译），能把第一批 120 条的时间压下来？

## 六、怎么验（本机命令）

```powershell
# 元数据一致性（应 18 passed）
.venv\Scripts\python.exe -m pytest tests/test_project_metadata.py -q

# 默认门禁：当前为红，原因见下节
.venv\Scripts\python.exe -m pytest -q

# 排除先天损坏的测试后可全绿（应 238 passed）
.venv\Scripts\python.exe -m pytest -q -o addopts="-ra --tb=short" tests/facts tests/api tests/predicates tests/tools/test_query_theory.py tests/tools/test_human_touch_linter.py tests/tools/test_blind_ledger.py tests/tools/test_anchor_span.py tests/tools/test_blind_toolchain.py tests/tools/test_gao_split.py tests/test_project_metadata.py
```

## 七、已知红灯（审阅时请当作既有缺陷，不是本轮引入）

`tests/tools/test_bundle_pii.py` 在**导入阶段**加载 `.workbuddy-ai/make_bundle_v2.py`；该目录被 `.gitignore` 忽略且本机不存在，因此 `pytest -q` 在收集阶段直接失败。修复方案待定（见对话中的 S1–S6 方案对比），**不要**为了让门禁变绿而删除该测试。

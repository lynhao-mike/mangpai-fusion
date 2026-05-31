# Agent 边界契约 · 08-agent-handoff

> **历史说明**：本文记录 v1.2 多 agent 并行重构期间的分支、可写区、交付验收标准与集成日流程。
> 当前 `v1.2-build` 已合并到 `main`，日常 AI / agent 入口以仓库根 [`AGENTS.md`](../../AGENTS.md) 与 [`META/project-state.json`](../../META/project-state.json) 为准；本文不再作为当前分支策略事实源。

最后更新：2026-05-28（历史契约归档说明同步）
版本：v1.2.0-historical

---

## 〇、当前使用边界

- 当前主分支：`main`。
- 当前产品版本与阶段：以 [`../../VERSION`](../../VERSION) 与 [`../../META/project-state.json`](../../META/project-state.json) 为准。
- 当前工具入口：以 [`../../tools/README.md`](../../tools/README.md) 与 [`../../tools/tool_registry.py`](../../tools/tool_registry.py) 为准。
- 下文中的 `v1.2-build`、`v1.2-track-*`、集成日流程均为 v1.2 发布前历史流程，保留用于追溯，不得据此新建分支或判定当前交付状态。

---

## 一、总原则（v1.2 历史）

1. **每个 agent 只能写自己的专属目录**——违规提交被整合 agent 拒绝
2. **所有 agent 从 `v1.2-build` 切子分支**，命名 `v1.2-build/track-X`（X=A-H）
3. **交付形式 = PR 到 v1.2-build**，整合 agent review + merge
4. **跨 agent 接口变更 = "请假条"**：必须先开 issue，整合 agent 同步给下游 agent

---

## 二、8 Agent 详细定义

### Agent A · 段派 D1 能量引擎

| 项 | 值 |
|---|---|
| 分支 | `v1.2-track-A` |
| **可写区** | `engine/energy/` · `engine/predicates/`（ganzhi/wuxing/relations/strength 四个文件）· `theory/raw/duan/promoted/` |
| **只读区** | 所有 contracts/ · 其他 engine/ 子目录 · cases/ · reports/ |
| **交付物** | `evaluate_energy(parsed) → EnergyFindings` 完整实现 |
| **验收** | 5 个回归测试通过（见下 § 六） |
| **依赖上游** | 无（D1 是流水线第一步） |
| **为下游提供** | EnergyFindings JSON Schema 实例 |

### Agent B · 杨派 D2 画面合拍

| 项 | 值 |
|---|---|
| 分支 | `v1.2-track-B` |
| **可写区** | `engine/picture/` · `theory/raw/yang/promoted/` |
| **只读区** | 所有 contracts/ · engine/energy/（只读调用）· cases/ · reports/ |
| **交付物** | `match_picture(energy, parsed) → PictureFindings` 完整实现 |
| **验收** | 4 个回归测试通过 |
| **依赖上游** | Agent A 的 EnergyFindings（可用 mock 先行开发，集成日换真） |
| **为下游提供** | PictureFindings JSON Schema 实例 |

### Agent C · 任派 D3 应期三层门

| 项 | 值 |
|---|---|
| 分支 | `v1.2-track-C` |
| **可写区** | `engine/yingqi/` · `engine/predicates/cycles.py` · `engine/predicates/tou_cang.py` · `theory/raw/ren/promoted/` |
| **只读区** | 所有 contracts/ · engine/energy/ · engine/picture/（只读调用） |
| **交付物** | `gate_yingqi(...)` 完整实现 + 6 触发 + 12 道门 |
| **验收** | 5 个回归测试通过（含 C-2026-001 婚期 2005 vs 2013 对比） |
| **依赖上游** | Agent A + Agent B 的 Findings |

### Agent D · 高派 D4 旁证引擎

| 项 | 值 |
|---|---|
| 分支 | `v1.2-track-D` |
| **可写区** | `engine/pangzheng/` · `engine/predicates/shensha.py` · `theory/raw/gao/promoted/` |
| **只读区** | 所有 contracts/ · 其他 engine/ |
| **交付物** | `support_with_shensha(...)` 完整实现 |
| **验收** | 3 个回归测试通过 |
| **依赖上游** | Agent A/B/C 的 Findings（可用 mock） |

### Agent E · 兜底护栏 5 件套

| 项 | 值 |
|---|---|
| 分支 | `v1.2-track-E` |
| **可写区** | `tools/preflight.py` · `tools/output_linter.py` · `tools/three_layer_check.py` · `engine/mechanical-rules.yaml` · `.kiro/steering/pre-output-checklist.md` |
| **只读区** | 所有 contracts/ · engine/ 其他 |
| **交付物** | 3 个 Python 脚本 + 1 YAML + 1 steering MD |
| **验收** | 8 条铁律的负向测试全过（输入违规数据 → 正确拒绝） |
| **依赖上游** | 无（E 与 A-D 并行） |

### Agent F · 标准报告渲染器

| 项 | 值 |
|---|---|
| 分支 | `main` 当前标准 |
| **可写区** | `templates/report-v1.3.md` · `tools/render_report.py` |
| **只读区** | 所有 contracts/ · engine/ · 旧 templates/ |
| **交付物** | mock findings → C-2026-025 唯一标准 sample 报告（lint 通过）+ statements 列表对象映射 |
| **验收** | output_linter 对 sample 报告 0 error；历史模板/variant 入参不得改变输出结构 |
| **依赖上游** | A/B/C/D 的 Findings Schema（用 mock 实例） |

### Agent G · 自迭代引擎

| 项 | 值 |
|---|---|
| 分支 | `v1.2-track-G` |
| **可写区** | `tools/feedback_loop.py` · `tools/rule_lifecycle.py` · `tools/drift_detect.py` · `tools/cross_school_scan.py` · `tools/extract_predictions.py` · `engine/calibration.yaml` · `META/iteration-log.md` |
| **只读区** | 所有 contracts/ · engine/ 其他 · theory/ 的 index.yaml（**写权限** 仅限 status/hits/misses 字段） |
| **交付物** | 用 C-2026-001 失验数据回放 → 输出正确 diff 报告 |
| **验收** | 回放后 M2-Y-073 的 misses += 1、confidence 正确降级 |
| **依赖上游** | 无（G 与 A-D 并行） |

### Agent H · 测试夹具 + 回归基准

| 项 | 值 |
|---|---|
| 分支 | `v1.2-track-H` |
| **可写区** | `tests/` · `tests/fixtures/` · `tests/regression_baseline.yaml` |
| **只读区** | 所有 contracts/ · cases/ · reports/（用作 fixture 来源） |
| **交付物** | pytest 一键跑通 + 6 项量化基准定义 |
| **验收** | `pytest tests/ --run` 0 fail（用 mock 引擎） |
| **依赖上游** | 无（H 与 A-D 并行） |

---

## 三、分支策略图（v1.2 历史）

```
main (v1.0 冻结)
  └── v1.2-build (长枝)
        ├── v1.2-track-A (段派引擎)
        ├── v1.2-track-B (杨派引擎)
        ├── v1.2-track-C (任派引擎)
        ├── v1.2-track-D (高派引擎)
        ├── v1.2-track-E (兜底护栏)
        ├── v1.2-track-F (报告渲染)
        ├── v1.2-track-G (自迭代)
        └── v1.2-track-H (测试)
```

**merge 方向**：各 track → v1.2-build（PR + review）→ 最终 v1.2-build → main（v1.2 发布）

---

## 四、集成日流程（v1.2 历史，每周一次）

```
1. 整合 agent 拉最新 v1.2-build
2. 逐个 merge 各 track 的 PR（有冲突则通知对应 agent 解决）
3. 跑 Agent H 的 pytest（全量回归）
4. 如果 fail：
   a. 定位是哪个 agent 的 commit 引入的
   b. 通知该 agent revert 或 fix
   c. 其他 agent 暂停
5. 如果 pass：
   a. 标记 "集成日 YYYY-MM-DD 通过"
   b. 所有 agent 从 v1.2-build pull 最新后继续
```

---

## 五、跨 Agent 接口变更流程（v1.2 历史“请假条”）

当 Agent A 发现 EnergyFindings 需要新增字段：

```
1. Agent A 开 issue: "[INTERFACE] EnergyFindings 需加 xxx 字段"
2. 整合 agent 评估影响范围（哪些下游 agent 受影响）
3. 整合 agent 在 issue 中 @所有受影响 agent
4. 受影响 agent 回复"OK"或"需要讨论"
5. 全部 OK → 整合 agent 发 [CONTRACT] PR 修 03-findings-schema
6. 契约 PR 合并后 → 各 agent 从 v1.2-build pull → 继续
```

**时间约束**：接口变更从 issue → 契约 merge 不超过 2 工作日。超时则驳回变更请求。

---

## 六、各 Agent 回归测试清单

### Agent A 回归测试（5 项）

| 测试 | 输入 | 期望 |
|---|---|---|
| A-001 | C-2026-001 bazi | layer_count=2, wealth_ceiling=大富级·下 |
| A-002 | C-2026-002 bazi | layer_count=1, wealth_ceiling=中富级·中 |
| A-003 | C-2026-014 bazi | layer_count=1, wealth_ceiling=中富级·上 |
| A-004 | C-2026-011 bazi（省府秘书）| layer_count≥2 |
| A-005 | C-2026-012 bazi（正处长）| layer_count≥2 |

### Agent B 回归测试（4 项）

| 测试 | 输入 | 期望 |
|---|---|---|
| B-001 | C-2026-001 energy+bazi | 职业=公门/国企, caifu.rank≤4 |
| B-002 | C-2026-001 energy+bazi | marriage_picture.初婚窗口 含 [22,28] |
| B-003 | C-2026-002 energy+bazi | 职业=服务/公共, energy_consistent=True |
| B-004 | C-2026-014 energy+bazi | 学业=一本+, energy_consistent=True |

### Agent C 回归测试（5 项）

| 测试 | 输入 | 期望 |
|---|---|---|
| C-001 | C-2026-001 year=2005 婚姻 | passed_layers=3, ★≥4 |
| C-002 | C-2026-001 year=2013 婚姻 | passed_layers≤1（picture_consistent=False）|
| C-003 | C-2026-001 year=2020 六亲 | passed_layers=3, ★★★★★ |
| C-004 | C-2026-001 year=2020 事业 | passed_layers≥2 |
| C-005 | C-2026-014 year=2024 学业 | passed_layers≥2 |

### Agent D 回归测试（3 项）

| 测试 | 输入 | 期望 |
|---|---|---|
| D-001 | C-2026-001 金舆在时柱 | boost marriage ≥ 0.04 |
| D-002 | C-2026-014 词馆+天乙×2 | boost 学业 ≤ 0.10（不能过高） |
| D-003 | C-2026-001 驿马 | boost 含"奔波/调动"标签 |

### Agent E 回归测试（8 项 = 8 条铁律的负向）

| 测试 | 输入 | 期望 |
|---|---|---|
| E-001 | 缺 schema_version 的 input.md | preflight FAIL |
| E-002 | 四柱含非法字"甲丑" | preflight FAIL |
| E-003 | ★5(50%) 的断语 | linter FAIL |
| E-004 | 应期断语无 yingqi_year | linter FAIL |
| E-005 | 引用 blacklisted 规律 | linter FAIL |
| E-006 | ★★★★★ 但 passed_layers=2 | three_layer_check FAIL |
| E-007 | 含"未来某年" | linter WARNING |
| E-008 | 指纹重复 | preflight FAIL |

### Agent F 回归测试（1 项）

| 测试 | 输入 | 期望 |
|---|---|---|
| F-001 | mock AnalysisOutput | 生成报告通过 output_linter 0 error |

### Agent G 回归测试（1 项）

| 测试 | 输入 | 期望 |
|---|---|---|
| G-001 | C-2026-001 feedback（婚姻失验）| M2-Y-073 misses += 1, confidence 正确降级 |

### Agent H 回归测试

Agent H 本身**是**测试基础设施——验收标准 = `pytest tests/ --run` 0 fail。

---

## 七、优先级保底（决策 M）

当资源紧张（如某 agent 卡住），按以下优先级保保底 agent 先完成：

```
E（兜底护栏） > A（段派能量） > C（任派应期） > G（自迭代） > B > D > F > H
```

含义：
- E 不完成 → 流水线没有护栏 = 等于没重构
- A 不完成 → D1 不存在 = D2/D3 都跑不了
- C 不完成 → "三层齐备才铁口断" 无法落地
- G 不完成 → 自迭代不工作（但不影响首次推断）

---

## 八、W2 启动检查清单（v1.2 历史）

**以下全部满足 = 8 agent 可以开工**：

- [x] 00-OVERVIEW.md 已锁定
- [x] 01-input-schema.md 已锁定
- [x] 02-predicate-library.md 已锁定
- [x] 03-findings-schema.md 已锁定
- [x] 04-gate-protocol.md 已锁定
- [x] 05-rule-lifecycle.md 已锁定
- [x] 06-confidence-model.md 已锁定
- [x] 07-pipeline-flow.md 已锁定
- [x] 08-agent-handoff.md 已锁定（本文件）
- [x] 09-naming-convention.md 已锁定
- [x] 10 旧案已重命名
- [x] `v1.2-build` 分支已建立
- [x] 决策 A-M 已全部在 00 § 四 记录

**契约冻结声明**：自本 PR 合并之时起，`engine/contracts/` 目录进入**冻结状态**。任何修改必须走 § 五 的"请假条"流程。

---

## 九、后续时间表

| 周 | 工作 |
|---|---|
| W2 | 8 agent 全面启动，E/A/G/H 先行 |
| W3 | 第 1 次集成日（merge + pytest） |
| W4 | A/B/C/D 收尾 + F 接真 findings |
| W5 | 整合 + 回放 001/002/014 三案 |
| W6 | 新案验收 + v1.2 发布候选 |

---

**W1 全部 10 份契约到此完成。契约冻结。8 agent 可以启动。**

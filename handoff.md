# v1.2 重构 Handoff · 2026-05-25

> 本文记录 v1.2 重构在 main 分支落定后的状态，供下一个 session/agent 无损接续。
> 取代 2026-05-23 旧版（W2 末快照，已完全过期）。

---

## 一、v1.2 当前状态：发布候选已就绪

**版本**：`VERSION` = `1.2.0`
**主分支**：`main`，HEAD = `5aa37ff` (PR #18 合并点)
**v1.2 整体**：通过 PR #12 squash 入 `main`（2026-05-24）

### 发布门槛（决策 I · G1-G6）全部达成

| 指标 | v1.0 基线 | v1.2 限值 | v1.2 实测 | 状态 |
|---|---|---|---|---|
| G1 三案核心铁断命中 | 5 | ≥ v1.0 + 1 | **7** | ✅ |
| G2 C-001 婚期误差 | 8 年 | ≤ 3 年 | **0 年** | ✅ |
| G3 C-002 婚姻失验数 | 4 | ≤ 1 | **0** | ✅ |
| G4 C-014 学历过判档数 | 1 | = 0 | **0** | ✅ |
| G5 trace_id 覆盖率 | 0% | 100% | **100%** | ✅ |
| G6 ★5 三层 gate 通过率 | 0% | 100% | **100%** | ✅ |

6/6 全部 PASS，远超"≥5/6"红线。落地于 PR #17（W3 集成日）。

### pytest 全量

```
tests/regression/test_v1_2_vs_v1_0.py        7 passed   ← 发布门槛
tests/                                       69 passed / 2 xfailed
```

xfailed 两项均为 A-003 严格层数计数已知偏高（`engine/contracts/08-agent-handoff.md § 六 A-003`），不阻塞发布。

---

## 二、已完成交付（按 PR 顺序）

| PR | 标题 | 合并时间 | 关键产出 |
|---|---|---|---|
| #5 | v1.2 W1.1 contracts 00 + 09 | 2026-05-23 | `engine/contracts/00-OVERVIEW.md`、`09-naming-convention.md` |
| #6 | rename: 10 旧案加干支 | 2026-05-23 | `cases/C-2026-NNN-{干支}/` |
| #7 | track-E 兜底护栏 5 件套 | 2026-05-23 | `tools/{preflight,output_linter,three_layer_check}.py` + `engine/mechanical-rules.yaml` |
| #8 | track-A 段派 D1 能量引擎 | 2026-05-23 | `engine/energy/` + `engine/predicates/{ganzhi,wuxing,relations,strength}.py` |
| #9 | track-G 自迭代引擎 | 2026-05-23 | `tools/{feedback_loop,rule_lifecycle,drift_detect,cross_school_scan,extract_predictions}.py` |
| #10 | track-H 测试夹具 + 回归基准 | 2026-05-23 | `tests/{fixtures,regression}/` + `pyproject.toml` |
| #11 | track-B 杨派 D2 画面合拍 | 2026-05-23 | `engine/picture/` + `engine/predicates/palace.py` |
| #13 | track-C 任派 D3 应期三层门 | 2026-05-23 | `engine/yingqi/` + `engine/predicates/{cycles,tou_cang}.py` |
| #14 | track-D 高派 D4 旁证引擎 | 2026-05-23 | `engine/pangzheng/` + `engine/predicates/shensha.py` |
| #15 | [DECISION] 决策面板永久锁定 | 2026-05-23 | `engine/contracts/decisions-locked.md`（13 项 A-M）|
| #16 | track-F 三段式报告渲染器 | 2026-05-23 | `tools/render_report.py` + `templates/report-v1.2.md` |
| #17 | W3 集成日：G1-G6 全 PASS | 2026-05-23 | 把 `gate_yingqi`/`support_with_shensha` 接入 `tests/regression/test_v1_2_vs_v1_0.py` |
| #12 | V1.2 build → main | 2026-05-24 | squash 合并 v1.2-build 整支到 main |
| #18 | docs: v1.0→v1.2 architecture review | 2026-05-25 | `plans/architecture-review.md` |

---

## 三、当前工作区拓扑

```
engine/
├── contracts/              10 份契约 + decisions-locked.md（已冻结）
├── predicates/             36 个共用谓词（ganzhi/wuxing/relations/palace/cycles/tou_cang/strength/shensha）
├── energy/                 D1 段派能量引擎（evaluate_energy）
├── picture/                D2 杨派画面合拍引擎（match_picture）
├── yingqi/                 D3 任派应期三层门（gate_yingqi）+ 6 触发 + 12 道门
├── pangzheng/              D4 高派旁证引擎（support_with_shensha）+ 26 神煞规则
├── pipeline.py             v1.2 流水线主入口
├── confidence.yaml         置信度阈值（v1.0 双轨制）
├── domain-weights.yaml     领域权重（v1.0 仲裁兜底）
├── mechanical-rules.yaml   黑名单 + 禁忌词（linter 加载）
├── calibration.yaml        自迭代阈值 + freeze_iteration 紧急开关
└── arbitration.md          v1.0 仲裁宪法（保留作为 v1.2 兜底）

tools/
├── preflight.py / output_linter.py / three_layer_check.py    护栏 3 件套
├── feedback_loop.py / rule_lifecycle.py / drift_detect.py    自迭代闭环
├── cross_school_scan.py / extract_predictions.py             跨派扫描 + 预测封存
├── render_report.py                                          v1.2 三段式渲染
└── calibrate.py / build_indexes.py                           v1.0 工具（保留）

tests/
├── conftest.py             sys.path + 全局 fixture（依赖 PyYAML）
├── fixtures/               cases.py + ground truth + v1.0 baseline
├── regression/             test_a_energy / test_e_guardrails / test_g_iteration / test_v1_2_vs_v1_0
├── track_a..g_smoke/       各 Track 自带 smoke
└── regression_baseline.yaml  G1-G6 量化指标定义
```

---

## 四、运行环境约定

- **Python**：3.10 / 3.11 / 3.13 任一均可（v1.2 代码无版本特性依赖）
- **依赖**：`pip install -r requirements-dev.txt` 安装 `pytest>=7.0,<9.0`、`PyYAML>=6.0`
- **沙箱注意**：若在 `INTEGRATIONS_ONLY` 网络隔离环境（无 PyPI 访问）跑测试，需手工把 PyYAML wheel 放进 site-packages，或临时 vendoring。这是环境约束，不是仓库职责。

```bash
pip install -r requirements-dev.txt
pytest tests/                                          # 全量
pytest tests/regression/test_v1_2_vs_v1_0.py -v        # 仅发布门槛
```

---

## 五、未完成 · 下一步建议

按 `plans/architecture-review.md § 八` 的演进路径，v1.3+ 候选议题：

| 优先级 | 议题 | 入口 |
|---|---|---|
| P1 | 把 `.kiro/skills/analyst.md` 改造为 `engine/pipeline.run_pipeline()` 的编排层 | `.kiro/skills/analyst.md` 仍是 v1.0 LLM 解释执行 |
| P2 | 反馈样本累积到 ≥ 30 后，触发 Beta 分布置信度切换（决策 E） | `tools/rule_lifecycle.py` 已实现 Beta，等数据 |
| P2 | 加轻量 metrics：每步落盘 `cases/C-XXX/findings/timing.json`，超 60s 告警 | `engine/pipeline.py` |
| P3 | 命宫长生诀自动算法、问真 APP input.md 直接解析 | v1.0 ROADMAP 遗留 |
| P3 | 八字指纹相似案检索 | `cases/cases-index.md` 指纹区已就位 |

详细建议见 `plans/architecture-review.md § 八`（5 条具体建议）。

---

## 六、决策红线（已锁定，修改需 [DECISION] PR）

详见 `engine/contracts/decisions-locked.md`（PR #15）。要点：

- **B**：判定逻辑全纯 Python，YAML 仅 metadata / 阈值
- **D**：引擎产骨架 + AI 仅润色"画像段"（必须标 `[AI-polish]`）
- **E**：现用线性加权，≥ 30 反馈后 Track-G 自动切 Beta
- **F**：升级自动 / 降级人工
- **G**：累计 3 次失验降级
- **H**：v1.2 期间 PR-based，发布后恢复直推 main
- **I**：发布门槛 G1-G6 严格优于 v1.0
- **K**：每 10 案触发 `cross_school_scan`

---

## 七、关键入口速查

| 用途 | 路径 |
|---|---|
| v1.2 流水线主入口 | `engine/pipeline.py :: run_pipeline()` |
| D1 段派能量 | `engine/energy/evaluator.py :: evaluate_energy(parsed)` |
| D2 杨派画面 | `engine/picture/matcher.py :: match_picture(energy, parsed)` |
| D3 任派应期 | `engine/yingqi/gate.py :: gate_yingqi(...)` |
| D4 高派旁证 | `engine/pangzheng/pangzheng.py :: support_with_shensha(...)` |
| 神煞外算注入 | `engine/pangzheng/loader.py :: attach_shensha(parsed)` |
| 报告渲染 | `tools/render_report.py :: render(energy, picture, gates, parsed, support)` |
| 案例加载 | `tests/fixtures/cases.py :: load_case(case_id)` |
| 三层校验 | `tools/three_layer_check.py :: check_yingqi(gate_result)` |
| 反馈回流 | `tools/feedback_loop.py :: ingest_feedback(case_id)` |
| 10 份契约 | `engine/contracts/00..09-*.md` |
| 决策锁定 | `engine/contracts/decisions-locked.md` |
| 架构评审 | `plans/architecture-review.md`（2026-05-25） |

---

**本 handoff 由 v1.2 收尾 session 于 2026-05-25 写入。**
**v1.2 发布候选就绪，main 分支即可作为 v1.2.0 发布点。**

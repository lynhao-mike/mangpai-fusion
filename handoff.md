# v1.2 重构 Handoff · 2026-05-23

> 本文记录当前 session 工作终止时的精确状态，供下一个 agent/session 无损接续。

---

## 一、已完成交付

| Track | PR | 状态 | 关键文件 |
|---|---|---|---|
| A 段派 D1 | #8 | ✅ 已合 v1.2-build | engine/energy/ |
| B 杨派 D2 | #11 | ✅ 已合 v1.2-build | engine/picture/ |
| C 任派 D3 | #13 | ✅ 已合 v1.2-build | engine/yingqi/ + engine/predicates/{cycles,tou_cang}.py |
| D 高派 D4 | #14 | 🟡 **冲突已修复，可合并** | engine/pangzheng/ + engine/predicates/shensha.py |
| E 兜底护栏 | (v1.2-build 内) | ✅ | tools/{preflight,output_linter,three_layer_check}.py |
| G 自迭代 | #9 | ✅ 已合 | tools/{feedback_loop,rule_lifecycle,drift_detect}.py |
| H 测试基准 | #10 | ✅ 已合 | tests/{fixtures,regression}/ |
| decisions | #15 | 🟢 **新建，可合并** | engine/contracts/decisions-locked.md |

---

## 二、待合并 PR（按顺序 merge）

1. **PR #14** (v1.2-track-D) → v1.2-build
   - 已 force-push 含 merge commit `da8e174`，模拟 GitHub merge "went well"
   - 直接点 Merge 即可

2. **PR #15** (v1.2-decisions-lock) → v1.2-build
   - 无冲突，1 个文件（decisions-locked.md）

---

## 三、未完成 · 下一步

### #2 启动 Track-F（报告渲染器）

**分支**：从 v1.2-build（合并 #14/#15 后）切 `v1.2-track-F`

**需要交付的文件**：
- `templates/report-v1.2.md` — 三段式报告模板
- `tools/render_report.py` — 渲染主入口
  - 输入：EnergyFindings + PictureFindings + GateResult + SupportFindings + ParsedInput
  - 输出：三段式 Markdown 报告
  - 三段 = 铁断段（三层齐的 ★★★★★ 断语）+ 画像段（画像版描述）+ 应期段（应期时间轴）
  - AI 润色边界（决策 D）：仅"画像版"段允许 AI 润色，必须标 `[AI-polish]`
  - trace_id 全覆盖（解决 G5）：每条断语含 `evidence.rule_id` 链
- `tests/track_f_smoke/test_f_render.py` — 验收测试

**验收标准（08 § 六 Track-F 行）**：
- F-001: mock findings 生成 1 份 sample 报告，结构通过 output_linter
- F-002: 报告含 trace_id 覆盖率 = 100%
- F-003: 铁断段只含 passed_layers=3 的断语

### #3 W3 集成日（G1/G2/G3/G4 regression 接入）

**分支**：从 v1.2-build 切 `v1.2-w3-integration`

**需要做的**：
- `tests/regression/test_v1_2_vs_v1_0.py` 中有 4 个 TODO 占位（v1_2_value = -1）
- 接入方式：
  ```python
  # G1: 
  from engine.yingqi import gate_yingqi
  from engine.energy.evaluator import evaluate_energy
  from engine.picture.matcher import match_picture
  # 对 3 个真实案例的 ground truth 事件 逐年跑 gate_yingqi，
  # 统计 passed_layers=3 且 star>=4 的命中数 = v1_2_value

  # G2:
  # 找 C-001 婚姻在 [2002,2013] 中最强的应期年，与 2005 的距离 = error
  # v1_2_value = error

  # G4:
  # 对 C-014 教育预测，比对 D2 level-scales 判定层级 vs 实际层级
  # overshot = 0 则 v1_2_value = 0
  ```
- 从 Track-C 的 `tests/track_c_smoke/test_c_gate.py::test_G2_holy_grail_c001_vs_c002` 可复制 G2 逻辑

**验收**：
- G1 不再 skip/fail
- G2 不再 skip/fail（应 PASS，误差 0 年）
- G4 不再 skip/fail（需 D2 + D4 联合判定学历层级）

---

## 四、决策面板（已锁定）

详见 `engine/contracts/decisions-locked.md`（PR #15）。

核心红线：
- **B**: 判定逻辑全纯 Python，YAML 仅 metadata/阈值
- **E**: 现用线性加权，≥30 反馈后由 Track-G 自动切 Beta
- **H**: v1.2 期间 PR-based，发布后恢复直推 main

---

## 五、分支地图

```
main (v1.0 + Track-C commit 52d9a9a, 不影响 v1.2-build 工作)
 └── v1.2-build (远端 69f2d77, 含 A/B/C/E/G/H)
      ├── v1.2-track-D (da8e174, PR #14 待合)
      ├── v1.2-decisions-lock (bbd7d69, PR #15 待合)
      ├── v1.2-track-F (未创建，下一步)
      └── v1.2-w3-integration (未创建，#3)
```

---

## 六、pytest 全量状态（基于 v1.2-track-D 合并后）

```
62 passed, 2 xfailed
3 failed (G1/G2/G4 regression TODO 占位 — 待 #3 W3 集成接入)
```

Track-C 本地验收 10/10 PASS
Track-D 本地验收 9/9 PASS
G2 圣杯端到端 PASS（2005 三层 ★5 / 2013 一层 ★2）

---

## 七、关键文件引用

| 用途 | 路径 |
|---|---|
| Track-C 入口 | `engine/yingqi/gate.py :: gate_yingqi()` |
| Track-D 入口 | `engine/pangzheng/pangzheng.py :: support_with_shensha()` |
| Track-A 入口 | `engine/energy/evaluator.py :: evaluate_energy()` |
| Track-B 入口 | `engine/picture/matcher.py :: match_picture()` |
| 案例加载 | `tests/fixtures/cases.py :: load_case(case_id)` |
| 神煞加载 | `engine/pangzheng/loader.py :: attach_shensha(parsed)` |
| 三层校验 | `tools/three_layer_check.py :: check_yingqi(gate_result)` |
| 10 份契约 | `engine/contracts/00~09-*.md` |
| 决策锁定 | `engine/contracts/decisions-locked.md` |

---

**本 handoff 由 Track-C/D agent 于 2026-05-23 session 末写入。**
**下一个 session 优先合并 PR #14 + #15，然后启动 Track-F。**

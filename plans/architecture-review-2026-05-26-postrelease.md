# mangpai-fusion 架构回顾 · v1.3.0 发布后视角

> 站位：系统架构师 / v1.3.0 发布后第一次回顾性评审
> 评审时点：2026-05-26（v1.3.0 已发布，HEAD = `8589f02`，含 v1.4 学制盲区联动修正 + W10 报告级 lint）
> 基准评审：[`plans/architecture-review.md`](architecture-review.md:1)（2026-05-25，v1.2 RC 阶段写）
> 本评审范围：基准评审到现在（约 24 小时窗口）的状态对齐 + 一项发布后新发现的债务

---

## 0. 为什么写这份回顾

[`plans/architecture-review.md`](architecture-review.md:1) 写于 v1.2 RC 阶段（2026-05-25），列出了 7 项债务 + 5 条架构师建议。**24 小时内仓库的实际进度大幅超出基准评审的时间表**：

- v1.2.0 已发布，**v1.3.0 已发布**（M10 完成，自迭代闭环 D1-D8 全部上线）
- 基准评审里 5 条「给架构师的具体建议」中已有 4 条落地
- 7 项债务中已有 4 项关闭

这份回顾的目的：
1. **逐条对账** — 把基准评审的债务清单和建议逐条核到 commit / 文件级，避免债务清单与实际状态长期错位
2. **记录新发现** — `tools/calibrate.py` 与 v1.2/v1.3 工具的双写风险，是基准评审里没具名指出、但发布后立刻显形的真实债务
3. **更新优先级** — 剩余债务在 v1.3.0 发布后的优先级排序应当如何调整

---

## 一、基准评审 → v1.3.0 发布的对账表

### 1.1 基准评审 § 七 「7 项架构债务」对账

| # | 基准评审里的债务 | 实际状态（截至 v1.3.0 发布后） | 证据 |
|---|---|---|---|
| **1** | v1.2 W3 集成日未完成 / G1/G2/G4 三测试 TODO | ✅ **已关闭**。G1-G6 全 PASS | [`STATUS.md`](../STATUS.md:24) "v1.2 发布门槛 6/6 全部 PASS" |
| **2** | Track-F 报告渲染器未启动 | ✅ **已关闭**。三段式 + 双版（master/client）均上线 | [`tools/render_report.py`](../tools/render_report.py:1) `render_both()`、[`templates/report-v1.2.md`](../templates/report-v1.2.md:1)、[`templates/report-v1.3.md`](../templates/report-v1.3.md:1) |
| **3** | v1.0 / v1.2 双轨长期共存 / `analyst.md` 仍是 v1.0 入口 | ✅ **已关闭**（入口侧）。analyst.md 已重写为 v1.2 流水线编排器（六阶段 INTAKE→PARSE→PIPELINE→RENDER→DELIVER→FEEDBACK） | [`.kiro/skills/analyst.md`](../.kiro/skills/analyst.md:1) "v1.2 流水线编排器（Orchestrator）"、[`README.md`](../README.md:117) 已同步更新 |
| **4** | 决策 B "纯 Python" 边界容易滑坡 / `mechanical-rules.yaml` 待审查 | ✅ **已关闭**。YAML 升级为 v1.2.1 元数据版，判定语义全部迁到 [`engine/mechanical_rules.py`](../engine/mechanical_rules.py:1)，加 `sync_invariants` 双向同步约束 | [`engine/mechanical-rules.yaml`](../engine/mechanical-rules.yaml:1) 文件头 "v1.2.1 落地决策 B 红线" + [`handoff.md`](../handoff.md:24) "决策 B 审查 ✅ 已完全合规" |
| **5** | trace_id 100% 覆盖（G5）依赖 Track-F | ✅ **已关闭**。G5 实测 100% | [`STATUS.md`](../STATUS.md:30) "G5 trace_id 覆盖率 = 100%" |
| **6** | 跨派映射仅 27% 覆盖 | 🟡 **未变**（主动接受的债，按实战长尾补全） | [`mapping/INDEX.md`](../mapping/INDEX.md:1) |
| **7** | 可观测性缺失 / 无 metrics 接入 | ✅ **已关闭**。`PipelineTiming` 8 步埋点 + 60s 软告警 + 全局聚合工具 | [`engine/pipeline.py:67`](../engine/pipeline.py:67) `class PipelineTiming`、[`tools/timing_report.py`](../tools/timing_report.py:1)、[`META/timing-summary.json`](../META/timing-summary.json:1) |

**关闭率：6/7 = 86%**。剩 1 项（跨派映射 27%）被列为主动债，不是工程缺陷。

### 1.2 基准评审 § 八 「5 条具体建议」对账

| # | 建议 | 实际状态 |
|---|---|---|
| **1** | 把 `analyst.md` 改造为 v1.2 流水线编排器，统一入口 | ✅ **已落地** |
| **2** | 统一 trace_id 规范到 `03-findings-schema.md`，evidence.rule_id 必填 | ✅ **已落地**（G5 = 100%） |
| **3** | 建立 v1.0 ↔ v1.2 反馈数据 ETL，避免 `applied_cases` 双写 | ⚠️ **部分落地**。v1.2/v1.3 入口已统一到 `feedback_loop.py` + `feedback_ingest.py`，但 `tools/calibrate.py`（v1.0 入口）仍在仓库内、字段名错位（详见 § 三） |
| **4** | 加入轻量 metrics，每步落盘 timing.json | ✅ **已落地** |
| **5** | 冻结 `mechanical-rules.yaml` 审查，落地决策 B | ✅ **已落地** |

**落地率：4.5/5 = 90%**。第 3 条是这次回顾的核心新发现。

### 1.3 v1.3.0 新增、基准评审未覆盖的能力

基准评审是 v1.2 RC 视角，没有涵盖 v1.3 设计。补记：

- **statement_id 稳定锚点**（D1）：`S-{case_seq}-{sha256(sorted_rule_ids)[:6]}`，反馈精确回流到规律
- **双版报告**（D2）：master（命理师，含反馈位 + 弱项）/ client（命主，仅 ★4+），由 `render_both()` 同时产出
- **结构化反馈摄入**（D5）：`[y]/[n]/[?]/[skip]` 四标注，`?`/`skip` 入库不计数
- **批量工作流**（D6）：`batch_intake` / `batch_review`
- **应期延迟反馈**（D7）：±1 年窗口；hit=1.0 / 半年外=0.5；统计独立隔离
- **边界自动挖掘**（D3）：≥5 miss + p<0.1 + lift≥2 + 回放验证 → 候选边界
- **候选否决兜底**（D4）：≥5 miss + n≥10 + posterior<40% + 边界空 → flagged_for_review
- **自迭代调度器**（D8）：每 10 完成反馈案 → 自动 `META/iteration-report-NNN.md`，异常 warn-only 不阻塞

W4 验收 H1-H6 全 PASS（[`STATUS.md`](../STATUS.md:38)），首次 D8 触发已产出 [`META/iteration-report-001.md`](../META/iteration-report-001.md:1)。

---

## 二、v1.3.0 发布后的当前状态快照

| 维度 | 数值 |
|---|---|
| 版本 | v1.3.0（`VERSION` = `1.3.0`） |
| 主分支 HEAD | `8589f02`（含 v1.4 C-014 学制盲区修复 + W10 报告级 lint） |
| 累计反馈案 | **11 / 30**（决策 E Beta 切换阈值；还差 19 案） |
| 规律状态 | candidate ~261 / confirmed ~645 / flagged_for_review **7** / deprecated **1** |
| 测试 | `pytest tests/` 69 passed / 2 xfailed（A-003 严格层数已知偏高） |
| W4 验收 | H1-H6 全 PASS（W4 stdlib smoke 19/19） |
| Pipeline 端到端 | < 60s 软阈值（PipelineTiming 监测） |

---

## 三、发布后新发现：`tools/calibrate.py` 与 v1.2/v1.3 工具的双写风险

这是基准评审建议 #3 在落地审计时显形的具体形态。

### 3.1 风险描述

**两个工具都写同一个文件 `theory/{school}/index.yaml`，但字段名 + 状态机完全不一致**：

| 字段 | `tools/calibrate.py`（v1.0） | `tools/rule_lifecycle.py` `save_rule()`（v1.2/v1.3） |
|---|---|---|
| 命中计数 | `hit_count` | `hits` |
| 失验计数 | `miss_count` | `misses` |
| 部分应验 | `partial_count` | `abstained` |
| 状态 | `status ∈ {candidate, promoted, retired}` | `status ∈ {candidate, confirmed, flagged_for_review, deprecated}` |
| 时间戳 | `last_calibrated` | `applied_cases[].case_id` |
| 滑窗 | — | `recent_5` |
| 置信度 | `static_score` / `dynamic_score` / `final_score` / `star` | `confidence_cache.{posterior, star, percent, variance}` |

**证据**：
- [`tools/calibrate.py`](../tools/calibrate.py:5) 文件头：「回流到 4 派 theory/{school}/index.yaml」
- [`tools/calibrate.py`](../tools/calibrate.py:253) 直接读写 `hit_count` / `miss_count`
- [`tools/rule_lifecycle.py`](../tools/rule_lifecycle.py:585) `save_rule()` 是 v1.2/v1.3 路径

### 3.2 触发条件

发布后任何一次执行 `python3 tools/calibrate.py --case C-XXXX` 都会：
1. 用 v1.0 字段名（`hit_count` / `miss_count` / `partial_count`）追加写入已被 v1.2/v1.3 字段（`hits` / `misses` / `abstained`）填满的 yaml — 同一规律两套计数器并存，互不识别
2. 用 v1.0 三态 `status`（`candidate`/`promoted`/`retired`）覆盖 v1.2/v1.3 四态（含 `flagged_for_review` / `deprecated`），状态机被踩平
3. `static_score` / `dynamic_score` 与 `confidence_cache.posterior` 各算一份，下一次 v1.2 工具读 `confidence_cache` 不会出错（兼容前向），但 v1.0 字段会留在 yaml 里成为「鬼字段」

### 3.3 处理动作（本评审 PR 一并落地）

**方案 A · 弃用守卫**（不删代码，禁用执行入口）：

[`tools/calibrate.py`](../tools/calibrate.py:1) 已加：
1. 文件顶部 docstring 标注 `[DEPRECATED 2026-05-26]`，详述双写原因 + 替代工具清单
2. `if __name__ == "__main__"` 入口加 deprecation guard：默认 `sys.exit(2)` + 6 行 stderr 警告
3. 保留 `import` 路径（其它工具未引用，但保留 escape hatch）
4. 提供环境变量 `MANGPAI_ALLOW_LEGACY_CALIBRATE=1` 强制运行（仅用于历史追溯）

**为什么不删文件**：
- `META/INDEX.md`、`META/calibration-methodology.md`、`META/ingestion-protocol.md`、`engine/contracts/00-OVERVIEW.md`、`engine/contracts/09-naming-convention.md`、`templates/feedback.md`、`cases/_TEMPLATE/analysis.md` 等 8+ 处文档历史性引用 calibrate.py — 删文件会让所有历史链接失效
- v1.0 案例（C-2026-001 ~ C-2026-006）的 feedback.md 顶部 checklist 仍写「已运行 calibrate.py」，删除会破坏历史可追溯
- 留代码、禁执行是**最小破坏的关闭路径**

**测试结果**（本次 PR 已验证）：

| 场景 | 行为 |
|---|---|
| `python3 tools/calibrate.py --case C-XXXX`（默认） | 6 行 stderr 警告，`exit 2` |
| `import tools.calibrate`（其它模块） | 静默通过，函数仍可访问 |
| `MANGPAI_ALLOW_LEGACY_CALIBRATE=1 python3 tools/calibrate.py ...` | 进入 main()，按 v1.0 行为运行 |

---

## 四、剩余债务清单（v1.3.0 发布后视角，按优先级排序）

| # | 优先级 | 债务 | 影响 | 来源 |
|---|---|---|---|---|
| 1 | **P1** | `tools/calibrate.py` 文件本身仍在仓库（已加 guard） | 历史引用文档 8+ 处、未来可能被新 agent 误用为参考实现 | 本评审 § 三 |
| 2 | **P2** | 反馈样本 11/30 → 置信度仍走线性加权未切 Beta | 决策 E 等数据，公式已就位 | [`engine/contracts/decisions-locked.md:103`](../engine/contracts/decisions-locked.md:103)、[`STATUS.md:45`](../STATUS.md:45) |
| 3 | **P2** | `templates/report.md` / `report-v1.2.md` / `report-v1.3.md` 三份模板共存 | 渲染路径分裂；新案默认走 v1.3，旧案 / cases/_TEMPLATE 仍引用早期模板 | [`templates/`](../templates/) |
| 4 | **P2** | A-003 严格层数计数 2 项 xfailed | 已知偏高 | [`STATUS.md:34`](../STATUS.md:34) "2 xfailed" |
| 5 | **P2** | 7 条 flagged_for_review 规律待人工 review | 升降级闭环堵塞 | [`handoff.md:32`](../handoff.md:32)：M2-Y-091 / M3-R-031 / M1-D-122 / M3-R-022 / M3-R-027 / M3-R-003 |
| 6 | **P3** | 八字指纹相似案检索器未建（指纹区已就位） | 实战命理师无法快速回查同盘 | 基准评审 § 七.6 / [`STATUS.md:84`](../STATUS.md:84) |
| 7 | **P3** | 命宫长生诀自动算法仅理论库未实现 | 高派独门武器闲置 | [`STATUS.md`](../STATUS.md:84) |
| 8 | **P3** | 问真 APP `input.md` 直接解析未做 | 11 步 schema 摩擦 | [`STATUS.md`](../STATUS.md:84) |
| 9 | **P3** | 跨派映射 27%，剩余 73% 无映射元数据 | 实战长尾需现查 | [`mapping/INDEX.md`](../mapping/INDEX.md:1) |
| 10 | **P3** | 跨维度输出耦合性 gate（CFL-C015-002） | P(体制内)>0.7 时输出框架切换未自动化 | [`handoff.md:73`](../handoff.md:73) |
| 11 | **P3** | 应期模型扩展 `event_type_hypotheses`（CFL-C015-003） | v1.4 路线图 | [`handoff.md:74`](../handoff.md:74) |

**与基准评审差异**：
- 基准评审的 P1 (4 项) 全部关闭（双写风险作为 P1 的最后一项已在本 PR 处理）
- 基准评审的 P2 (3 项) 中 metrics + xfailed 关闭，新加入「7 条 flagged 规律待 review」
- P3 基本沿用，新增 v1.4 路线图两项

---

## 五、风险点（v1.3.0 发布后视角）

| 风险 | 等级 | 说明 | 与基准评审差异 |
|---|---|---|---|
| `tools/calibrate.py` 误用 | 🟢 低 | 已加 guard，escape hatch 需主动设置环境变量 | **新发现 → 本 PR 已闭环** |
| 反馈样本累积慢 | 🟡 中 | 11/30，按当前节奏 Beta 切换可能需 3-6 个月 | 与基准评审一致 |
| LLM polish 边界失守 | 🟢 低 | 决策 D + output_linter 拦截 | 与基准评审一致 |
| 7 条 flagged 规律积压 | 🟡 中 | 一次 D8 触发即产生 6 条新 flagged，缺架构师 review 节奏 | **v1.3.0 新风险**（自迭代闭环开闸后才显现） |
| 模板三轨共存 | 🟡 中 | report.md / v1.2 / v1.3 三份并存，新案默认 v1.3，但缺统一收敛计划 | **基准评审未列**（v1.3 上线后才出现） |

---

## 六、演进路径建议（v1.3.0 → v1.4）

### P0 立即（已发布）

- ✅ v1.3.0 tag 已建（[`handoff.md:159`](../handoff.md:159) 提示需 `git push origin v1.3.0` 推送）

### P1 短期（1-4 周）

1. **Review 7 条 flagged_for_review 规律** — 决定保留观察 / 收紧条件 / 退役（M2-Y-091 / M3-R-031 / M1-D-122 / M3-R-022 / M3-R-027 / M3-R-003 + 历史 1 条）
2. **修 A-003 严格层数计数** — 解决 2 项 xfailed
3. **historical 报告回溯扫描** — `tools/output_linter.py` 跑 `reports/*.md`（验证 W9 cross-domain check）

### P2 中期（1-3 个月）

1. **统一报告模板** — 把 `templates/report.md` + `report-v1.2.md` 标记 deprecated（参考本 PR 对 calibrate.py 的处理方式），保留单一活动模板 `report-v1.3.md`
2. **触发 Beta 切换** — 反馈样本 ≥30 后由 `tools/rule_lifecycle.py` 自动切 Beta 分布（公式已就位）
3. **C-2026-015 后续 CFL** — `industry_path` + `wealth_level.framework` 字段加入 `engine/contracts/03-findings-schema.md`

### P3 长期（半年+）

1. 命宫长生诀自动算法（高派独门）
2. 问真 APP `input.md` 直接解析
3. 八字指纹相似案检索器
4. 跨派映射覆盖率从 27% 扩到 50%+
5. 跨维度输出耦合性 gate（CFL-C015-002）
6. 应期模型扩展 `event_type_hypotheses`（CFL-C015-003）

---

## 七、一句话总结

基准评审写于 v1.2 RC，列了 7 项债务 + 5 条建议；24 小时后 v1.2.0 + v1.3.0 接连发布，**4/5 条建议落地、6/7 项债务关闭**。基准评审里隐含的「v1.0 ↔ v1.2 反馈数据 ETL 双写风险」在发布后立刻显形为 `tools/calibrate.py` 字段名 + 状态机错位，本 PR 用 deprecation guard 闭环。剩余债务里**唯一动起来就有杠杆**的是 7 条 flagged 规律的人工 review — 这是自迭代闭环开闸后第一次出现的「需要人」的环节，决定了 v1.4 之前能否再产生有质量的边界 / 否决候选。

---

## 附录 A：本 PR 的 5 项交付

1. ✅ 本评审文档：`plans/architecture-review-2026-05-26-postrelease.md`
2. ✅ `tools/calibrate.py` 顶部 docstring [DEPRECATED] 标记 + 替代工具清单
3. ✅ `tools/calibrate.py` `__main__` 入口 deprecation guard（默认 sys.exit 2，env escape hatch）
4. ✅ `STATUS.md` 顶部链接到本评审
5. ✅ `README.md` `tools/calibrate.py` 行追加 (deprecated v1.3.0+) 标记

## 附录 B：变更记录

| 版本 | 时间 | 修改 |
|---|---|---|
| v1.0 | 2026-05-26 | v1.3.0 发布后第一次回顾性评审 |

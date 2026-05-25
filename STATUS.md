# STATUS · 当前进度

**最后更新**：2026-05-25
**版本**：**v1.3.0**（自迭代闭环上线；`VERSION` = `1.3.0`）
**当前里程碑**：M10 完成（v1.3 自迭代闭环 D1-D8 全部上线，W4 验收通过）+ 历史反馈回补 10/10 ✅（首次 D8 触发 → [`META/iteration-report-001.md`](META/iteration-report-001.md:1)）

---

## 总体进度

| 里程碑 | 内容 | 状态 |
|---|---|---|
| M1 | 仓库骨架 + schema + 语料迁入 | ✅ 完成 |
| M2 | 高派 + 段派规律入库 | ✅ 完成（550/550 = 100%） |
| M3 | 杨派 + 任派规律入库 | ✅ 完成（363/363 = 100%） |
| M4 | 跨派映射矩阵（共识/互补/独门/冲突） | ✅ 完成（242 个映射点） |
| M5 | 双轨置信度引擎 + 仲裁引擎 | ✅ 完成（v1.0） |
| M6 | 主分析器 + 输入输出模板 | ✅ 完成（v1.0） |
| M7 | META 自迭代 + 校准工具 + 案例归档 | ✅ 完成（v1.0） |
| M8 | v1.2 双层引擎契约 10/10 + 决策面板锁定 | ✅ 完成（PR #5/#15） |
| M9 | v1.2 D1-D4 维度引擎 + 三层护栏 + W3 集成日 | ✅ 完成（PR #7~#17） |
| **M10** | **v1.3 自迭代闭环 D1-D8 上线（statement_id / 双版报告 / feedback_ingest / batch / late_feedback / boundary_miner / veto_miner / iteration_report）** | **✅ 完成（PR #26~#29 + W4 验收）** |

---

## v1.2 发布门槛（决策 I）

| 指标 | v1.0 基线 | v1.2 限值 | v1.2 实测 | 状态 |
|---|---|---|---|---|
| G1 三案铁断命中 | 5 | ≥ v1.0 + 1 | **7** | ✅ |
| G2 C-001 婚期误差 | 8 年 | ≤ 3 年 | **0 年** | ✅ |
| G3 C-002 婚姻失验数 | 4 | ≤ 1 | **0** | ✅ |
| G4 C-014 学历过判档数 | 1 | = 0 | **0** | ✅ |
| G5 trace_id 覆盖率 | 0% | 100% | **100%** | ✅ |
| G6 ★5 三层 gate 通过率 | 0% | 100% | **100%** | ✅ |

6/6 全部 PASS。`pytest tests/regression/test_v1_2_vs_v1_0.py` → 7 passed。
`pytest tests/` 全量 → 69 passed / 2 xfailed（A-003 严格层数已知偏高，不阻塞发布）。

---

## v1.3 W4 验收门槛（H1-H6）

| 指标 | 含义 | 实测 | 状态 |
|---|---|---|---|
| H1 statement_id 稳定性 | 同 input 重跑 5 次 sid 集合一致 + 跨案不撞 + 排序无关 | 5/5 PASS | ✅ |
| H2 双版报告差分 | master 含反馈位、保留弱项；client 反馈位=0、★≤3 过滤 | 5/5 PASS | ✅ |
| H3 反馈解析正确率 | 100 条标注样本 ≥ 99% + ?/skip→no_data + 重复取最后 + fanout 决断力优先 | 5/5 PASS（100/100 = 100%） | ✅ |
| H6 完整闭环调度 | 10 案 → seq=1 + 报告产出；20 案 → seq=2；异常 warn-only；重复案不重计 | 4/4 PASS | ✅ |

W4 stdlib smoke：**19/19 全 PASS**（沙箱无 PyYAML/pytest，桩 yaml 后跑通）。
H4（boundary 自挖）/ H5（v1.2 G1-G6 不退化）由 CI 单独验证（W3 落地已含）。

W4 修复：`tools/render_report.py` `_render_template` 嵌套 `{% if %}` 错配（外层 `endif` 被吃成内层）→ 用负前瞻 + 内层优先 while 循环修复，client 模式不再泄漏反馈位。

---

## v1.3 能做什么（在 v1.2 基础上新增）

✅ **statement_id 稳定锚点**：`S-{case_seq}-{sha256(sorted_rule_ids)[:6]}`（D1）→ 报告每条断语带稳定 ID，反馈表精确回流到规律。
✅ **双版报告**：master（命理师内部用，含 sid 锚点 + 反馈位 + 弱项）/ client（命主可读，仅 ★4+ 主线，无反馈位）→ `tools/render_report.py render_both()`（D2）。
✅ **结构化反馈摄入**：`[y]/[n]/[?]/[skip]` 四标注 → `tools/feedback_ingest.py`（D5），`?` 与 `skip` 入库不计数（等待延迟反馈兑现）。
✅ **批量工作流**：`tools/batch_intake.py`（inbox→pipeline）+ `tools/batch_review.py`（pending→ingest）（D6）。
✅ **应期延迟反馈**：±1 年窗口；hit=1.0 / 半年外=0.5；统计独立隔离不污染主画像（D7）`tools/late_feedback.py`。
✅ **边界自动挖掘**：≥5 miss + p<0.1 + lift≥2 + 回放验证 hit_rate 升 → 候选边界（D3）`tools/boundary_miner.py`。
✅ **候选否决兜底**：≥5 miss + n≥10 + posterior<40% + boundary 空 → flagged_for_review（D4）`tools/veto_miner.py`。
✅ **自迭代调度器**：每 10 完成反馈案（非入库）→ 自动产出 `META/iteration-report-NNN.md`（D8）`tools/iteration_report.py`，异常 warn-only 不阻塞 ingest。

## v1.2 能做什么（v1.3 全部继承）

✅ **维度立体化**：4 派从横向权重平铺改为纵向串联（D1 段→D2 杨→D3 任→D4 高），上游约束下游边界。
✅ **应期三层门**：原局有 + 大运到位 + 流年引爆，三层齐备才下 ★5 铁断（`engine/yingqi/gate.py`）。
✅ **画面合拍钳制**：D2 输出婚姻/事业/财运/学业画面窗口，D3 用 `picture_consistent` 钳制应期年份。
✅ **三层护栏**：preflight（入口）+ output_linter（出口）+ three_layer_check（W3 内部）拒绝越界输出。
✅ **trace_id 全链路**：每条断语含 `evidence.rule_id` 链 → render 报告时倒推完整证据链。
✅ **决策 B 红线**：判定逻辑全纯 Python，YAML 仅承载 metadata + 阈值。
✅ **三段式报告**：铁断段 / 画像段（仅此段允许 `[AI-polish]`）/ 应期段，由 `tools/render_report.py` 渲染。
✅ **自迭代闭环**：feedback → Beta 重算 → 升降级 → 漂移检测 → 每 10 案跨派扫描。

## v1.0 能做什么（v1.2 全部继承）

✅ 4 派融合 / 双轨制置信度（★+%）/ 派别冲突显式呈现 / 仲裁裁决
✅ 9 大领域权重矩阵（婚/事/财/学/健/六亲 + 格局/富贵/玄学）
✅ 反馈回流校准（`tools/calibrate.py` v1.0 + `tools/feedback_loop.py` v1.2）
✅ 案例归档（`cases/C-YYYY-NNN-{干支}/` + `reports/C-YYYY-NNN-{干支}-report.md`）

✅ **理论库覆盖**：高派 261 / 段派 290 / 杨派 163 / 任派 200 = **914 条规律全量索引**
✅ **跨派映射**：共识 16 组 / 互补 22 组 / 独门 200 条 / 冲突 20 条

---

## v1.3 还不能做的事（v1.4+ 路线图）

- ❌ 没有可视化网页（仍是纯 Markdown 报告）
- ❌ 命宫长生诀自动算法（仅理论库未实现）
- ❌ 神煞自动识别（依赖问真 APP 提供，决策 A 锁定外算）
- ❌ 自动排盘（用户必须先用问真 APP 排好）
- ❌ 八字指纹相似案检索（指纹区已就位，检索器待建）
- ❌ 反馈样本不足 30 → 置信度公式仍走线性加权，未切 Beta（决策 E 阈值）
- ❌ 中医五运六气整合 / 风水堪舆整合

---

## 当前规律状态

| 类型 | 数量 |
|---|---|
| candidate（候选） | ~261（高派为主）|
| confirmed（已确认）| ~650（段杨任派；扣除下行 3 条）|
| flagged_for_review（待人工审）| **3**（**M2-Y-091** / **M3-R-005** / **M3-R-031**，2026-05-25 历史回补累计 misses 触发）|
| deprecated（已弃用）| 0 |

> 3 条 `flagged_for_review` 来源：[`META/rule-changelog.md`](META/rule-changelog.md:1) "2026-05-25 · v1.3 历史案例反馈回补"。架构师待 review 是否替代或退役。

> v1.0 的 promoted/retired/frozen 三态在 v1.2 重命名为 candidate / confirmed / flagged_for_review / deprecated（`engine/contracts/05-rule-lifecycle.md`），`tools/rule_lifecycle.py` 已自动迁移旧 status。

---

## 关键决策记录（含 v1.2 重构 13 项锁定）

| 日期 | 决策 | 理由 |
|---|---|---|
| 2026-05-23 | 采用方案🅒共识金字塔 + 双轨制置信度 | 用户偏好"宁慢不假"，置信度优先 |
| 2026-05-23 | 4 派权重按领域分工而非平均 | 实战经验各派擅长领域不同 |
| 2026-05-23 | 静态分:动态分 = 4:6 | 实战应验权重高于纸面理论 |
| 2026-05-23 | 沿用 META 自迭代体系 | 已经验证可用 |
| 2026-05-23 | 4 派 914 条规律全量索引 + 仅 27% 跨派映射（按需扩充）| 覆盖最常用 80% 场景 |
| 2026-05-23 | **v1.2 重构 13 项决策面板永久锁定**（PR #15）| 见 `engine/contracts/decisions-locked.md` A-M |
| 2026-05-23 | 决策 B：判定逻辑全纯 Python，YAML 仅 metadata + 阈值 | W2 末实战发现 YAML 表达分支逻辑过脆 |
| 2026-05-23 | 决策 I：v1.2 必须严格优于 v1.0 的 G1-G6 6 项指标 | 发布红线 |
| 2026-05-25 | **v1.3 D1-D8 自迭代闭环决策面板锁定**（PR #26）| 见 `plans/architecture-v1.3.md` |
| 2026-05-25 | D1：statement_id = `S-{case_seq}-{sha256(sorted_rule_ids)[:6]}` | 排序无关 + 跨案不撞 + 短期可读 |
| 2026-05-25 | D2：双版报告（master 含反馈位 + 弱项；client 仅 ★4+）| 命理师 / 命主关注点不同 |
| 2026-05-25 | D5：反馈四标注 `[y]/[n]/[?]/[skip]`，?+skip 入库不计数 | 命主当场不知道 ≠ 失验 |
| 2026-05-25 | D8：每 10 完成反馈案（非入库）触发 iteration_report；异常 warn-only | 阻塞设计会让命理师不敢 ingest |

---

## v1.2 流水线（立即可用的工作流）

```
1. 用问真八字 APP 排盘 → 复制 → 按 templates/input-from-wenzhen.md 整理
2. tools/preflight.py 校验 input.md（11 步 schema）
3. engine/pipeline.run_pipeline() 顺序调用：
     evaluate_energy   (D1 段)
     match_picture     (D2 杨)
     gate_yingqi       (D3 任，含三层门 + 6 触发 + 12 道门)
     support_with_shensha (D4 高，神煞外算注入)
4. tools/output_linter.py + tools/three_layer_check.py 兜底护栏校验
5. tools/render_report.py 渲染三段式 Markdown 报告
6. AI polish（仅画像段，必须标 [AI-polish]）
7. 与命主对话，记录反馈到 cases/C-YYYY-NNN-{干支}/feedback.md
8. tools/feedback_loop.py ingest_feedback(case_id) 触发：
     Beta 重算 → 升降级 → 漂移检测 → 落审计
9. 每 10 案 tools/cross_school_scan.py 自动跑跨派一致性扫描
10. tools/extract_predictions.py 把 ★4+ 应期封存到 predictions/
```

---

## 下一步行动（用户 / 架构师）

立即可做：
1. v1.3 自迭代闭环已上线 → 投入实战；命理师按 master 报告填 `[y]/[n]/[?]/[skip]` 即可触发反馈回流
2. 每 10 完成反馈案自动产出 `META/iteration-report-NNN.md`（D8）→ 架构师 review 是否合并候选边界 / 否决候选
3. **review 3 条 flagged_for_review 规律**（M2-Y-091 / M3-R-005 / M3-R-031）→ 决定保留观察 / 收紧条件 / 退役（参考 [`META/iteration-report-001.md`](META/iteration-report-001.md:1) §一）

短期（1-3 个月）：
- **决策 E Beta 切换阈值 ≥ 30，当前 10/30，还差 20 案** → 累积到位后置信度公式从线性加权（4:6）切 Beta 后验
- 加轻量 metrics（每步落盘 timing.json，超 60s 告警）
- 一次性审查 `engine/mechanical-rules.yaml`，把"含判定语义"字段挪到 Python（彻底落地决策 B）

中期（半年）：
- 命宫长生诀自动算法
- 问真 APP input.md 直接解析（减少手动输入）
- 八字指纹相似案检索

详细建议见 `plans/architecture-review.md § 八`（5 条具体建议）。

---

## v1.0 vs v1.2 维度对比

| 维度 | v1.0 | v1.2 |
|---|---|---|
| 4 派组织方式 | 横向：领域权重矩阵 | 纵向：D1→D2→D3→D4 串联 |
| 调用方式 | LLM 解释 YAML | 纯 Python 函数 |
| 应期判定 | 关键字 + 启发式 | 三层门：原局/大运/流年齐备才铁断 |
| 报告形式 | 4 段式（共识/互补/独门/冲突）| 三段式（铁断/画像/应期）+ AI polish 边界 |
| 上下游一致性 | 仲裁权重协调 | upstream_hash 强校验 + 钳位 |
| 护栏 | linter + checklist（软）| preflight + output_linter + three_layer_check（硬，违规中断）|
| trace_id 覆盖 | 0% | 100%（每条断语含 evidence.rule_id 链）|
| 测试基础设施 | 无 | pytest + 14 案 fixture + G1-G6 回归门槛 |
| 自迭代 | calibrate.py（半自动）| feedback_loop + rule_lifecycle + drift_detect + cross_school_scan |
| 置信度公式 | 静态:动态 = 4:6 线性加权 | 线性加权（≥ 30 反馈后切 Beta） |

# STATUS · 当前进度

**最后更新**：2026-05-25
**版本**：**v1.2.0**（发布候选；`VERSION` = `1.2.0`）
**当前里程碑**：M9 完成（v1.2 重构落地，发布门槛 G1-G6 全 PASS）

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
| **M9** | **v1.2 D1-D4 维度引擎 + 三层护栏 + W3 集成日** | **✅ 完成（PR #7~#17）** |

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

## v1.2 能做什么（在 v1.0 基础上新增）

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

## v1.2 还不能做的事（v1.3+ 路线图）

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
| confirmed（已确认）| ~653（段杨任派）|
| flagged_for_review（待人工审）| 0 |
| deprecated（已弃用）| 0 |

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
1. v1.2 发布候选已就绪 → 打 v1.2.0 tag → 投入实战
2. 累积新案例反馈数据（目标 ≥ 30 反馈样本，触发置信度公式 Beta 切换）

短期（1-3 个月）：
- ✅ 已完成：把 `.kiro/skills/analyst.md` 改为 `engine/pipeline.run_pipeline()` 的编排层（v1.2.0 编排器，2026-05-25）
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

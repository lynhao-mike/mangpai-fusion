# 规律变更日志

> 4 派每条规律的新增/晋级/退役/冻结操作都必须登记在此。

格式：
```
## YYYY-MM-DD
### 新增（candidate）
- {rule_id} · {title} · 来源：{source.file}

### 晋级（candidate → promoted）
- {rule_id} · {title} · 命中率 X/Y = Z%

### 退役（promoted → retired）
- {rule_id} · {title} · 失验率 X/Y = Z%

### 冻结（* → frozen）
- {rule_id} · {title} · 原因：...
```

---

## 2026-05-23 · v0.1.0 仓库启动

### 仓库初始化
- M1 阶段完成：仓库骨架 + schema + 来源迁入
- 0 条规律已结构化（M2/M3 阶段产出）
- 4 派原始语料全量迁入：
  - sources/gao/ 11 份
  - sources/duan/ 44 份
  - sources/yang/ 26 份
  - sources/ren/ 30 份
- 已结构化候选规律全量迁入 theory/raw/：
  - gao: extracted 9 份 + promoted 9 份
  - duan: theory 11 份 + promoted 5 份
  - yang: theory 7 份 + promoted 8 份
  - ren: theory 8 份 + promoted 5 份

### 待执行
- M2: 高派 ~249 条 + 段派 ~290 条 → theory/{gao,duan}/*.yaml
- M3: 杨派 ~163 条 + 任派 ~200 条 → theory/{yang,ren}/*.yaml
- M4: 跨派映射（共识/互补/独门/冲突）
- M5: 双轨置信度引擎 + 仲裁
- M6: 主分析器 + 模板
- M7: META 自迭代 + 校准工具


---

## 2026-05-23 · 铁断册诞生 + C-2026-013-坤-壬申甲辰丙辰己丑 v2.1 校准

### 新增引擎规则文件
- `engine/mechanical-rules.md` v1.0 · **机械铁断规则册**
  - 收录正式铁断 6 条（MR-001 ~ MR-006）
  - 收录失验黑名单 1 条（XF-001）
  - 定义铁断认定标准、软化判断指南、升降级流程

### 晋级（candidate → promoted/MR）
- `MR-001` · 月柱印星伏吟 → 母亲婚姻反复 · 杨派主导 · 命中 1/1（C-2026-013-坤-壬申甲辰丙辰己丑）· ★★★★★ (92%)
- `MR-002` · 命局土极旺(≥55%) → 肤色偏暗 · 高派主导 · 命中 1/1（C-2026-013-坤-壬申甲辰丙辰己丑）· ★★★★★ (93%)
- `MR-003` · 丙日主+食伤透干 → 大眼·嘴大·开朗 · 高派主导 · 命中 1/1（C-2026-013-坤-壬申甲辰丙辰己丑）· ★★★★★ (90%)
- `MR-004` · 空亡支被流年冲动 → 应期可发生 · 任派主导 · 命中 1/1（C-2026-013-坤-壬申甲辰丙辰己丑）· ★★★★★ (91%)
- `MR-005` · 财动婚动 → 坤造婚期触发条件 · 任派主导 · 命中 1/1（C-2026-013-坤-壬申甲辰丙辰己丑）· ★★★★★ (90%)
- `MR-006` · 年柱壬申驿马 → 配偶含流动/远方/军职属性 · 杨派主导 · 命中 1/1（C-2026-013-坤-壬申甲辰丙辰己丑）· ★★★★ (85%)

### 退役/黑名单（promoted → retired）
- `XF-001` · 正官藏不透 → 晚婚铁律 · 杨派初判 · 失验 1/1（C-2026-013-坤-壬申甲辰丙辰己丑）
  - 失验原因：官藏不透 ≠ 晚婚，应判"婚路曲折"
  - 替代规则：MR-005 + MR-004 + 多派联合判断"婚路曲折再婚命"
  - 强制校准：坤造判婚期必须三项联检（官杀格局/财动婚动/空亡冲实）

### 新增 candidate
- 候选 · 贵人神煞高密度（≥10 处）+ 格局非顶级 = 县域内贵人帮扶显著但层次参差 · 高+杨+段联合 · ★★★★ (84%)
  - 来源：C-2026-013-坤-壬申甲辰丙辰己丑 v2.1 首次系统化提出
  - 状态：candidate-MR · 待累计 ≥3 案例后升级为正式 MR

### 用户反馈学习（已沉淀至 mechanical-rules.md）
- 用户反馈 1：报告中富贵等级不能只输出 `L+数字`，必须附年收入或可量化说明 → 已在 `engine/level-scales.md` 强制
- 用户反馈 2：尽量减少分析中的单条机械铁断 → 已在 `engine/mechanical-rules.md §四 软化判断指南` 强制
- 用户反馈 3：必须保留的机械铁断必须形成可查列表 → 本次创建 `engine/mechanical-rules.md` 落实

### 案例版本变更
- C-2026-013-坤-壬申甲辰丙辰己丑 报告：v2.0 → v2.1
  - 共识层：3 条 → 4 条（新增 CON-4 贵人专项）
  - 互补层：4 条 → 5 条（新增 COMP-5 贵人帮扶系统）
  - 软化所有非铁断判断为多派联合表达
  - 新增贵人神煞专项判断（县域分层视角）

---

## 2026-05-25 · v1.3 历史案例反馈回补（10/10 完成 → seq=1 闭环触发）

### 背景
v1.3 D5 自迭代闭环上线前已沉淀的 10 份历史 `feedback.md` 从未走结构化摄入。
本次按"v1.0 启发式 fallback"通道回灌，目的：
1. 给 4 派规律计入历史 hits/misses，供 D5 Beta 重算 + D8 漂移检测；
2. 让 `feedback_completed_count` 0 → 10，触发首次 D8 `iteration-report-001`；
3. 推进决策 E（Beta 切换阈值 ≥30 案）样本累积。

### 锁定原则
- **A**：v6/v7 后期案 (007/009/010/011/012/013) `analysis.md` 无可抽 rule_id 时只 bump 计数不 fanout；
- **B**：双盘案（C-001↔C-002 夫妻 / C-002↔C-014 母子）算独立两次，保留信号强度；
- **C**：未来 ⏳ 应期段一律 `no_data` 跳过。

### 涉及案例（10 案）
- C-2026-001 / 002 / 007 / 008 / 009 / 010 / 011 / 012 / 013 / 014

### 工具补丁（[`tools/feedback_loop.py`](tools/feedback_loop.py:1)）
1. **扩展反馈标注词表**（[`_HIT/_MISS/_ABSTAIN/_NODATA_MARKERS`](tools/feedback_loop.py:121)）：
   - 新增 hit：`铁应验 / 命中 / 铁断 / 铁证`
   - 新增 miss：`完全失验 / 完全证伪`
   - 新增 abstain：`部分应验 / 🟠 / ◐ / ⚠️`
   - 新增 no_data：`未提供 / 未明确 / ⏳ / 进行中 / 待时间触发 / 待回测 / 待验`
2. **放宽表格列阈** [`parse_feedback_md`](tools/feedback_loop.py:212)：`cells<4` → `cells<3`，兼容 C-008/009/010 简表。
3. **新增** [`match_verdict_for_rule(rule_id, conclusion, feedback_rows)`](tools/feedback_loop.py:350)：
   按 `rule_id` 在 `raw_line` 中精确出现优先匹配，priority `miss>hit>abstain>no_data`，无精确匹配再走 domain fallback。
4. **重构** [`ingest_feedback`](tools/feedback_loop.py:801) fanout：
   逐 `rule_id` 查 verdict（取代原"按 conclusion 整体匹配再均摊"），修复 C-014 一条 conclusion 含多 rule_id 时被 OR 合并掉的 bug。

### 摄入产出（来自 [`META/iteration-state.json`](META/iteration-state.json:1) + [`META/iteration-log.md`](META/iteration-log.md:1)）
- `feedback_completed_count`：0 → **10**
- `iteration_seq`：0 → **1**（[`META/iteration-report-001.md`](META/iteration-report-001.md:1) 已生成）
- `META/calibration/`：9 个新 snapshot（C-001 因首案先于补丁完成，未入快照）
- 跨派扫描触发：✅ `META/conflict-trends.md` 同步刷新

### 自动降级（confirmed → flagged_for_review · 累计 misses 触发缓冲阈值）
| rule_id | 派别 | 触发原因 |
|---|---|---|
| **M2-Y-091** | 杨 | 多案累计 miss 越阈，需架构师 review |
| **M3-R-005** | 任 | 同上 |
| **M3-R-031** | 任 | 同上 |

### 升级
- 升级：**0 条**（≥3 案铁应验门槛尚未达成；M1-D-241 / M2-Y-070 等多次 hit 进入候选观察）

### 边界自挖（D3）+ 否决（D4）
- D3 boundary_miner：本周期无显著边界候选（miss<5 或 p/lift 不达标）
- D4 veto_miner：本周期 0 条满足全部触发条件

### 跨派一致性
- 本周期相关冲突计数：**10**（来源 [`META/conflict-trends.md`](META/conflict-trends.md:1)）

### 决策 E 进度
- 累计反馈样本：**10 / 30**（Beta 切换阈值），还差 20 案。
- 当前置信度公式仍走线性加权（4:6）。

### 留待人工 review（架构师）
- 3 条 `flagged_for_review` 规律的合理性与替代规则候选；
- 是否将 M1-D-241 / M2-Y-070（连续多案 hit）提前进入 candidate-MR 观察名单。



## 2026-05-25 · CFL-C015-001/002/003 落规则文件（C-2026-015 反馈触发）

### 背景
首例正厅级体制内命主反馈（C-2026-015 甲寅乙亥丙辰辛卯）暴露三处工程问题，触发 3 条仲裁记录入库。详见 [`META/arbitration-log.md`](arbitration-log.md) CFL-C015-001/002/003 完整推导。

### 1. CFL-C015-001 · 段派做功层数封顶律的"体制路径例外条款"

**变更性质**：新增候选规则（candidate）

**新规则**：[`mapping/exclusive.md`](../mapping/exclusive.md) § 2.6 `EXC-D-LIFA-CAP-001`
- 触发：纯体制路径 + 化杀生枭/官印相生 + 驿马 ≥ 2 验证
- 兑现：M1-D-173 默认映射上调 1 档（最多 +1，不叠加）
- 起始置信度：★★★ (65%)
- 升级路径：candidate → confirmed（再有 1 例正厅及以上体制内命主复现）

**关联文件改动**：
- [`engine/level-scales.md`](../engine/level-scales.md) § 七 判定规则映射 — 新增 `EXC-D-LIFA-CAP-001` 行
- [`engine/level-scales.md`](../engine/level-scales.md) § 九·四 — 新增完整触发逻辑伪代码 + 排除场景
- [`mapping/exclusive.md`](../mapping/exclusive.md) § 2.6 — 完整 YAML 规则定义 + evidence_cases

### 2. CFL-C015-002 · 跨维度输出耦合性 gate

**变更性质**：引擎工程改进（非规则纠偏）

**核心问题**：报告同时输出"公门首选 90%"+ "中富下 L9 财富 85%"，二者隐含矛盾（体制内薪酬走公务员体系，与市场财富 7 等不直接映射）。规则本身没错，是输出层耦合 gate 缺失。

**规则集变化**：
- [`engine/level-scales.md`](../engine/level-scales.md) § 十一 — 新增"跨维度输出耦合性 gate"完整规范
  - 三档分流：P(体制内) > 0.7 / 0.3-0.7 / < 0.3
  - 实操检查清单（v1.4 实施待办）
  - 与 § 九·四 体制路径例外条款的关系图

**代码变化**：
- [`tools/output_linter.py`](../tools/output_linter.py)
  - 新增 `_lint_cross_domain_coupling(md, res)` 全局检查函数
  - 新增 `_INSTITUTIONAL_KEYWORDS` / `_MARKET_WEALTH_KEYWORDS` / `_COUPLING_ANNOTATIONS` 三个关键词表
  - 新增 W9 严重等级（cross-domain incoherence warning）
  - 已挂入 `lint()` 主入口的 markdown 模式（dataclass 模式暂不适用，待 03-findings-schema.md 增加 industry_path 字段后启用）
  - 新增 2 个 smoke test 用例（_SMOKE_BAD_CROSS_DOMAIN / _SMOKE_GOOD_CROSS_DOMAIN）

### 3. CFL-C015-003 · 应期"事件类型"vs"时间窗"分流（建议性）

**变更性质**：仲裁原则记录（暂未落规则文件，等 v1.4 应期模型升级时一并处理）

**核心观察**：2010 庚寅应期"财源/置业"在时间上完美命中，但实际事件是"职级升迁"。说明应期判定应分 `time_window` + `event_type` 两层独立评估，"庚透财"在体制内案例可解读为"职级象征性收益"。

**v1.4 待办**（标记 backlog）：
- [`engine/yingqi/threelayer.py`](../engine/yingqi/threelayer.py) — 应期断语数据模型新增 `event_type_hypotheses: list[str]` 字段
- 体制内案例的"财星显象"应期 → 输出 `["职级升迁", "财源/置业"]` 两个候选事件类型，而非锁定单一类型

### 升级 / 降级影响

- **新增**：1 条候选规则（EXC-D-LIFA-CAP-001 / 段派独门）
- **维持**：M1-D-173（做功层次计量）默认置信度不变 — 规则在民营/体制外案例仍正确
- **置信度调整**（已通过 case feedback.md 落审计但未自动 ingest，待本地 `feedback_ingest` 触发）：
  - M2-Y-042 化杀生枭=官命第 1 取 ↑7%（杨派理论上限律 vs 段派封顶律之争 → 杨派胜出）
  - M1-D-005..008 段派做功 2 层映射 ↓10%（体制内案例偏严，由本例外条款补偿）
  - 应期 2020 庚子 ↑10% / 2025 乙巳 ↑8% / 2024 甲辰 ↑7% / 2015 乙未 ↑8% / 2004 甲申 ↑7%
  - 公门首选铁律 ↑2% / 官印相生 ↑3% / 驿马铁律 ↑4% / 复合做功 ↑2%

### 工程动作清单（已完成）

- [x] EXC-D-LIFA-CAP-001 在 mapping/exclusive.md 注册
- [x] level-scales.md § 七 / § 九·四 / § 十一 同步更新
- [x] tools/output_linter.py 新增 W9 cross-domain check
- [x] META/arbitration-log.md 追加 CFL-C015-001/002/003 三条仲裁记录
- [x] META/rule-changelog.md 本条目落审计

### 工程动作清单（已于 2026-05-29 执行）

- [x] 本地运行 `python -m tools.feedback_ingest C-2026-015-乾-甲寅乙亥丙辰辛卯` 触发置信度自动重算（fanout 15 条，状态变更 3 条；Windows 安全打印已修复）
- [x] v1.4 在 `engine/contracts/03-findings-schema.md` 增加 `industry_path` + `wealth_level.framework` 字段
- [x] v1.4 在 templates/report.md § 八财富等级评估前增加"§ 八·零 行业路径耦合提示"段落
- [x] v1.4 应期模型扩展 `event_type_hypotheses` 字段（CFL-C015-003）
- [x] 历史报告回溯扫描：新增 `tools/cross_domain_consistency_check.py --backfill`，复用 `tools/output_linter.py` W9 扫描 reports/*.md



---

## 2026-05-26 · v1.4 W1 · 测量字段就位（V1/V2/V3）+ 契约文档同步（G3）

> 本条目记录 v1.4 W1 文档/测试同步 PR 的规律层影响。**无新规律入库 / 无规律状态变更**——本 PR 仅落契约文档 + 把 V1/V2 字段从代码层映射到契约层 + 测试入 pytest。

### 触发

架构师视角第二次评审（接续基准评审 + v1.3.0 后置评审）暴露三类系统性问题：
- **S1**（高优先级）：v1.3 D5/D8 自迭代闭环把规律命中率推到"自动升降级"位，但**测量基础设施缺底层字段** → 框架性心法（M3-R-003 "原局定层次..."）+ 域专用规律（M3-R-031 "六合婚姻应期"被错误用于婚姻域）每次都被算成 miss → D8 误降级。
- **G3**（中优先级）：契约文档 v1.2.0-draft / VERSION v1.3.0 / handoff HEAD vs STATUS HEAD 三处不同步。
- **E3**（中优先级）：H7-H11 验收 smoke 已就位但未入 pytest，CI 不会自动拦下 v1.4 schema 变更带来的退化。

### 决策（v1.4 W1 锁定项）

| ID | 字段 | 默认 | 行为 |
|---|---|---|---|
| **V1** | 规律 yaml `quantifiable: bool` | `true` | `false` = 框架性心法整体跳过 hit/miss 计分 |
| **V2** | 规律 yaml `domain_restriction: list[str]` | `[]` | 非空时仅在列出的域内 ingest 计分；当前 domain ∉ list → 跳过该规律本次计分（domain 为空时不强制） |
| **V3** | ingest 跳过策略 | — | V1 守门先于 V2；跳过原因写入 `IterationDiff.notes`，前缀 `[v1.4-V1]` / `[v1.4-V2]`；不污染 `skipped_rule_ids`（该通道留给 RuleNotFoundError） |

字段定义详见 [`engine/contracts/05-rule-lifecycle.md`](../engine/contracts/05-rule-lifecycle.md) § 六 + § 6.1 + § 6.2（向后兼容）。

### 规律层落地（已通过历史 ingest 在本 PR 之前完成；本条目仅审计登记）

| 规律 ID | 派别 | 字段 | 值 | 当前 status |
|---|---|---|---|---|
| **M3-R-003** | 任 | `quantifiable` | `false` | `flagged_for_review`（保留等待架构师 review 是否退役 — 已不参与 hit/miss 计分） |
| **M3-R-031** | 任 | `domain_restriction` | `[应期]` | `confirmed`（架构师 REVIEW-BATCH-001 从 flagged → confirmed，5 hit/3 miss 中 3 miss 均为婚姻域误用） |

其他 5 条曾被 D8 触发降级的规律保持默认值（`quantifiable: true`, `domain_restriction: []`）：
- M1-D-122 / M3-R-022：维持 `flagged_for_review`，等架构师 review
- M3-R-005 / M3-R-027 / M2-Y-091：累计 ≥4 miss，已 deprecated

### 验收门槛（H7-H11 入 pytest）

| 指标 | 含义 |
|---|---|
| H7 | quantifiable=False 不计分（含 hit/miss/skip_rule_ids 三向断言）|
| H8 | domain_restriction 跳过域不匹配（含多域 + 空域兜底 + V1 优先级）|
| H9 | event_type_hypotheses round-trip + 注入逻辑（V4，体制内财源 → 双解）|
| H10 | social_clock_check 学制盲区律强制前置（CFL-C014-003）|
| H11 | output_linter W10 学制盲区报告级扫描 |

文件位置：`tests/v1_3_acceptance/test_h{4,5,7,8,9,10,11}_*.py`，pyproject 注册 `v1_4_acceptance` marker。

### 工程动作清单（已完成）

- [x] V1/V2 字段在 `tools/rule_lifecycle.py:Rule` 落地（含 round-trip）
- [x] V3 跳过策略在 `tools/feedback_loop.py:_apply_rule_verdicts` 落地
- [x] M3-R-003 / M3-R-031 yaml 回填
- [x] V4 `engine/yingqi/types.py:GateResult.event_type_hypotheses` + `engine/yingqi/gate.py:_infer_event_type_hypotheses` 落地（含体制内关键词字典）
- [x] 契约文档 00/05/06 升 v1.3.0-current
- [x] STATUS.md + handoff.md 去硬编码 HEAD（单一信息源 = 00-OVERVIEW § 〇）
- [x] H7-H11 入 pytest，H4 / H5 补 v1.3 验收锚点
- [x] 06-confidence-model § 2.1 锁定 N_eff Beta 切换计数公式

### 工程动作清单（v1.4 W2/W3 接力）

- [x] V5 `PictureFindings.industry_path: dict`（含 P_institutional / primary_path）
- [x] V6 `wealth_level.framework: Literal["market_wealth", "power_hierarchy", "dual"]`
- [x] V7 report-v1.4 模板 § 八·零 行业路径耦合提示
- [x] V8 `tools/cross_domain_consistency_check.py --backfill` 历史报告回溯扫描工具落地
- [x] 03-findings-schema.md schema_version 1.2.0 → 1.4.0（V5/V6 一并落，避免 schema 改两次）
- [ ] 婚姻应期模型专项（依赖 N_eff ≥ 30 切 Beta，延 v1.5）

### 升降级影响

无。本 PR 不触发任何规律状态变更。M3-R-003 加 `quantifiable=false` 后，下次 ingest 不会再因为它产生 miss → 但其 `status: flagged_for_review` 维持不变，等待架构师明确 review 决议（保留观察 / 收紧条件 / 退役）。

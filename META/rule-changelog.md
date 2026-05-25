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

## 2026-05-23 · 铁断册诞生 + C-2026-013-壬申甲辰丙辰己丑 v2.1 校准

### 新增引擎规则文件
- `engine/mechanical-rules.md` v1.0 · **机械铁断规则册**
  - 收录正式铁断 6 条（MR-001 ~ MR-006）
  - 收录失验黑名单 1 条（XF-001）
  - 定义铁断认定标准、软化判断指南、升降级流程

### 晋级（candidate → promoted/MR）
- `MR-001` · 月柱印星伏吟 → 母亲婚姻反复 · 杨派主导 · 命中 1/1（C-2026-013-壬申甲辰丙辰己丑）· ★★★★★ (92%)
- `MR-002` · 命局土极旺(≥55%) → 肤色偏暗 · 高派主导 · 命中 1/1（C-2026-013-壬申甲辰丙辰己丑）· ★★★★★ (93%)
- `MR-003` · 丙日主+食伤透干 → 大眼·嘴大·开朗 · 高派主导 · 命中 1/1（C-2026-013-壬申甲辰丙辰己丑）· ★★★★★ (90%)
- `MR-004` · 空亡支被流年冲动 → 应期可发生 · 任派主导 · 命中 1/1（C-2026-013-壬申甲辰丙辰己丑）· ★★★★★ (91%)
- `MR-005` · 财动婚动 → 坤造婚期触发条件 · 任派主导 · 命中 1/1（C-2026-013-壬申甲辰丙辰己丑）· ★★★★★ (90%)
- `MR-006` · 年柱壬申驿马 → 配偶含流动/远方/军职属性 · 杨派主导 · 命中 1/1（C-2026-013-壬申甲辰丙辰己丑）· ★★★★ (85%)

### 退役/黑名单（promoted → retired）
- `XF-001` · 正官藏不透 → 晚婚铁律 · 杨派初判 · 失验 1/1（C-2026-013-壬申甲辰丙辰己丑）
  - 失验原因：官藏不透 ≠ 晚婚，应判"婚路曲折"
  - 替代规则：MR-005 + MR-004 + 多派联合判断"婚路曲折再婚命"
  - 强制校准：坤造判婚期必须三项联检（官杀格局/财动婚动/空亡冲实）

### 新增 candidate
- 候选 · 贵人神煞高密度（≥10 处）+ 格局非顶级 = 县域内贵人帮扶显著但层次参差 · 高+杨+段联合 · ★★★★ (84%)
  - 来源：C-2026-013-壬申甲辰丙辰己丑 v2.1 首次系统化提出
  - 状态：candidate-MR · 待累计 ≥3 案例后升级为正式 MR

### 用户反馈学习（已沉淀至 mechanical-rules.md）
- 用户反馈 1：报告中富贵等级不能只输出 `L+数字`，必须附年收入或可量化说明 → 已在 `engine/level-scales.md` 强制
- 用户反馈 2：尽量减少分析中的单条机械铁断 → 已在 `engine/mechanical-rules.md §四 软化判断指南` 强制
- 用户反馈 3：必须保留的机械铁断必须形成可查列表 → 本次创建 `engine/mechanical-rules.md` 落实

### 案例版本变更
- C-2026-013-壬申甲辰丙辰己丑 报告：v2.0 → v2.1
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

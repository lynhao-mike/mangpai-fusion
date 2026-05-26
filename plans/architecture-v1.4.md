# v1.4 架构方案 · 2026-05-26

> **版本**：v1.4.0（规划）
> **基线**：v1.3.0（已发布，main HEAD = `eeacce7`）
> **触发**：CFL-C015-001/002/003 + 7 条 flagged-for-review 规律审查 → 暴露三类系统性问题。

---

## 一、目标

v1.4 的核心目标是**修复 v1.3 自迭代闭环暴露的三类系统性问题**：

1. **域定位错误放大 miss 计数**（review 关键发现 #3）
2. **框架性心法被错误计入量化评分**（review 关键发现 #2）
3. **跨维度输出耦合 gate 缺失**（CFL-C015-002）+ **应期事件类型单一化**（CFL-C015-003）

不引入新功能，专注**工程债务清理 + 输出层一致性**。

---

## 二、决策面板（v1.4 锁定项）

| # | 决策 | 锁定值 | 关联 review/CFL |
|---|---|---|---|
| **V1** | 规律 yaml 增加 `quantifiable` 字段 | `bool`，默认 `true`；`false` 表示框架性心法（不参与 hit/miss 计数） | REV-007 (M3-R-003) |
| **V2** | 规律 yaml 增加 `domain_restriction` 字段 | `list[str]`，空表示所有域；非空表示**仅在列出的域**内 ingest 时计 hit/miss | REV-003 (M3-R-031) |
| **V3** | ingest 跳过策略 | `quantifiable=false` → 整体跳过（不计 hit/miss/abstain）；域不匹配 → 跳过该 conclusion 的该规律 | V1 + V2 |
| **V4** | GateResult 增加 `event_type_hypotheses` | `list[str]`，默认 `[]`；体制内案例的"财星显象"应期注入 ≥ 2 个候选事件类型 | CFL-C015-003 |
| **V5** | PictureFindings 增加 `industry_path` | `dict`：`{ "P_institutional": float, "primary_path": str }` | CFL-C015-002 |
| **V6** | wealth_level 增加 `framework` 字段 | `Literal["market_wealth", "power_hierarchy", "dual"]` | CFL-C015-002 |
| **V7** | report-v1.4.md 模板 § 八·零 行业路径耦合提示 | 强制按 V5 输出对应分级框架 | CFL-C015-002 |
| **V8** | 历史报告回溯扫描器 `tools/cross_domain_consistency_check.py --backfill` | 扫描历史报告，输出 W9 触发清单 | CFL-C015-002 |

---

## 三、5 Track 计划

### Track 1 · Schema 升级（D1-D4 大改）⚠️ 高风险

**范围**：
- `engine/contracts/03-findings-schema.md` schema_version 1.2.0 → 1.4.0
- `PictureFindings.industry_path` 新增（V5）
- `wealth_level.framework` 新增（V6）
- 各 D1-D4 引擎 to_dict / from_dict / hash 兼容
- `analysis_output.json` 历史快照 round-trip 验证

**预计工作量**：3-5 sessions（涉及多个 dataclass + 历史 fixture 兼容）。

**延后**至独立 session 执行（V1.4 W2）。

---

### Track 2 · 应期事件类型分流（CFL-C015-003）✅ 本 session 实施

**范围**：
- `engine/yingqi/types.py` GateResult 增加 `event_type_hypotheses: list[str]`
- `engine/yingqi/gate.py` 在体制内案例的"财星显象"应期注入多候选事件类型
- 现有逻辑保持不变（向后兼容：默认空 list）

**预计工作量**：1 session。

---

### Track 3 · 规律生命周期字段补全（review 关键发现）✅ 本 session 实施

**范围**：
- `tools/rule_lifecycle.py` Rule dataclass 增加 `quantifiable` + `domain_restriction`
- `tools/feedback_loop.py` ingest 时按字段做跳过
- 回填 7 条 reviewed 规律的 yaml 标注：
  - **M3-R-003**: `quantifiable: false`（框架性心法）
  - **M3-R-031**: `domain_restriction: ["应期"]`
  - 其他规律保持默认值
- `theory/*/index.yaml` schema 增加这两个字段

**预计工作量**：本 session 完成。

---

### Track 4 · 跨维度耦合 gate 完整落地（CFL-C015-002）⚠️ 中风险

**范围**：
- `templates/report-v1.4.md` 新模板（含 § 八·零 行业路径耦合提示）
- `tools/cross_domain_consistency_check.py --backfill` 历史报告扫描器
- W9 警告精度提升（结合 V5/V6 字段而非纯关键词匹配）

**预计工作量**：2 sessions（模板重写 + UX 校准）。

**延后**至独立 session 执行（V1.4 W3）。

---

### Track 5 · 婚姻应期模型专项（review 关键发现 #1）⚠️ 高风险 / 需更多样本

**范围**：
- 婚姻域 gate 强制走联检（MR-005 + 画像窗口 + 三层 gate 三选二）
- C-001/002 婚姻域全 miss 的根因修复

**前置条件**：累计反馈样本 ≥ 30（决策 E Beta 切换阈值，当前 11/30）。

**延后**至 V1.5（样本充足后再统计建模）。

---

## 四、本 session 实施范围（Track 2 + Track 3）

```
Track 3a: rule_lifecycle Rule dataclass 字段
  └─ quantifiable: bool = True
  └─ domain_restriction: list[str] = []

Track 3b: feedback_loop.ingest_feedback 跳过逻辑
  └─ load_rule(rid).quantifiable == False → skip 整体
  └─ load_rule(rid).domain_restriction != [] AND conclusion.domain not in domain_restriction → skip

Track 3c: 回填 7 条 review 规律
  └─ M3-R-003: quantifiable=false
  └─ M3-R-031: domain_restriction=["应期"]
  └─ 其他 5 条保持默认（保留观察 / 已 deprecated）

Track 2a: GateResult.event_type_hypotheses 字段
  └─ default_factory=list

Track 2b: gate.py 体制内财星应期注入候选
  └─ 触发条件：D2 industry_pointers 含"公门/国企/体制" + 触发器含"庚透财/财星显象"
  └─ 输出：["职级升迁", "财源/置业"]
```

---

## 五、不在 v1.4 范围内的事

- ❌ Beta 后验置信度切换（决策 E，需 ≥ 30 反馈样本）
- ❌ 命宫长生诀自动算法（高风险，延 v1.5+）
- ❌ 问真 APP input.md 直接解析（v1.5+）
- ❌ 八字指纹相似案检索器（v1.5+）
- ❌ 可视化 Web（v2.0）

---

## 六、验收标准（H7-H9 新增）

> H1-H6 是 v1.3 验收标准，v1.4 继承并新增 H7-H9。

| 指标 | 含义 | 验收方法 |
|---|---|---|
| **H7** | quantifiable=false 不计分 | smoke：模拟 ingest 包含 M3-R-003 → hits/misses 不变 |
| **H8** | domain_restriction 跳过域不匹配 | smoke：模拟 M3-R-031 在"婚姻"域 ingest → 跳过；在"应期"域 → 计 hit |
| **H9** | event_type_hypotheses round-trip | smoke：构造 GateResult 含 event_type_hypotheses → to_json/from_json 一致 |

---

## 七、提交计划

| 分支 | 内容 | 状态 |
|---|---|---|
| `feat/v1.4-track-2-3` | Track 2 + Track 3 实施（本 session） | 🔜 |
| `feat/v1.4-track-1-schema` | Track 1 schema 升级 | 延后 |
| `feat/v1.4-track-4-coupling` | Track 4 跨域耦合 + 模板 | 延后 |
| `feat/v1.4-track-5-marriage` | Track 5 婚姻模型 | 延后到 v1.5 |

---

**本文件由 v1.4 启动 session 于 2026-05-26 创建。**
**v1.3.0 基线已发布；v1.4 Track 2+3 即将开工。**

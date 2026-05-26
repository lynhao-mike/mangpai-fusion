# iteration-log · 自迭代审计日志

> Track-G 自迭代引擎的"行车记录仪"。每次 `tools/feedback_loop.ingest_feedback()`
> 都会向本文件追加一段，记录所有 hits/misses 变更、status 跃迁、漂移触发、跨派扫描结果。
>
> **行格式参考 `engine/contracts/05-rule-lifecycle.md § 八`。**
>
> **不可手工编辑 `## YYYY-MM-DD` 段落**——只能由 `feedback_loop.py` 追加。
> 手工内容请放到末尾"Annotations"段。
>
> 配套快照：每次 ingest 同步落 `META/calibration/{date}-after-{case_id}.snapshot.yaml`，
> 用于一键回滚。

---

## 2026-05-23 · Track-G 初始化

case_count: 14
trigger: Track-G PR 创建
schema_version: 1.2.0

### 状态

v1.2 自迭代引擎首次部署。等待第一个真实 feedback 触发。

- `tools/feedback_loop.py` ingest 入口已就绪
- `tools/rule_lifecycle.py` 5 状态自动机 + Beta 算法已就绪
- `tools/drift_detect.py` 5-案滑动窗已就绪
- `tools/cross_school_scan.py` 每 10 案扫描已就绪
- `tools/extract_predictions.py` ★★★★+ 应期自动入库已就绪
- `engine/calibration.yaml` freeze_iteration=false（正常运行模式）

### Rule Updates

(尚无规律变更——本条目为初始化标记)

### Status Changes

(尚无状态变化)

### Cross-School Scan

未触发（case_count = 14，下一次扫描在 case_count=20 时触发，距 6 案）。

### Rollback Hint

若需还原到本初始化前：
```
git revert <track-G 初始化 commit>
```

---

## 2026-05-25 21:04 · ingest C-2026-001-庚申戊寅壬子辛丑

case_count: 10
trigger: ingest_feedback

### Rule Updates (16 条)

| rule_id | 派 | hits 旧→新 | misses 旧→新 | conf ★ 旧→新 | status 旧→新 | verdict |
|---|---|---|---|---|---|---|
| M1-D-122 | duan | 0→1 | 0→0 | ★2→★3 | confirmed→confirmed | hit |
| M1-D-253 | duan | 0→1 | 0→0 | ★2→★3 | confirmed→confirmed | hit |
| M1-D-001 | duan | 0→1 | 0→0 | ★2→★3 | confirmed→confirmed | hit |
| M2-Y-091 | yang | 0→0 | 0→1 | ★2→★1 | confirmed→confirmed | miss |
| M2-Y-049 | yang | 0→0 | 0→1 | ★2→★1 | confirmed→confirmed | miss |
| M2-Y-070 | yang | 0→0 | 0→1 | ★2→★1 | confirmed→confirmed | miss |
| M2-Y-064 | yang | 0→0 | 0→1 | ★2→★1 | confirmed→confirmed | miss |
| M2-Y-014 | yang | 0→0 | 0→1 | ★2→★1 | confirmed→confirmed | miss |
| M2-Y-068 | yang | 0→0 | 0→1 | ★2→★1 | confirmed→confirmed | miss |
| G-LF-022 | gao | 0→0 | 0→1 | ★2→★1 | candidate→candidate | miss |
| G-LF-006 | gao | 0→0 | 0→1 | ★2→★1 | candidate→candidate | miss |
| M3-R-031 | ren | 0→0 | 0→1 | ★2→★1 | confirmed→confirmed | miss |
| M3-R-027 | ren | 0→0 | 0→1 | ★2→★1 | confirmed→confirmed | miss |
| M3-R-003 | ren | 0→0 | 0→1 | ★2→★1 | confirmed→confirmed | miss |
| M3-R-005 | ren | 0→0 | 0→1 | ★2→★1 | confirmed→confirmed | miss |
| M3-R-022 | ren | 0→0 | 0→1 | ★2→★1 | confirmed→confirmed | miss |

### Skipped Rule IDs (in analysis but not in theory yaml)

- G-DY
- G-CH
- G-BD
- G-BD-词馆
- G-CH-车祸婚姻
- G-CHE-车祸篇
- G-BD-词馆神煞应用宝典
- G-时柱神煞

### Cross-School Scan
- 已触发（case_count=10，每 10 案） → META/conflict-trends.md 已更新

### Rollback Hint

```
# 回滚到本次 ingest 前：
git revert <commit-hash>
# 或恢复快照：
META/calibration/2026-05-25-after-C-2026-001-庚申戊寅壬子辛丑.snapshot.yaml
```

---

## 2026-05-25 21:04 · ingest C-2026-002-壬戌庚戌戊辰丙辰

case_count: 10
trigger: ingest_feedback

### Rule Updates (15 条)

| rule_id | 派 | hits 旧→新 | misses 旧→新 | conf ★ 旧→新 | status 旧→新 | verdict |
|---|---|---|---|---|---|---|
| M1-D-122 | duan | 1→1 | 0→1 | ★3→★2 | confirmed→confirmed | miss |
| M1-D-001 | duan | 1→1 | 0→1 | ★3→★2 | confirmed→confirmed | miss |
| M2-Y-091 | yang | 0→0 | 1→2 | ★1→★1 | confirmed→confirmed | miss |
| M2-Y-068 | yang | 0→0 | 1→2 | ★1→★1 | confirmed→confirmed | miss |
| M2-Y-014 | yang | 0→0 | 1→2 | ★1→★1 | confirmed→confirmed | miss |
| G-LF-006 | gao | 0→0 | 1→2 | ★1→★1 | candidate→candidate | miss |
| M3-R-003 | ren | 0→0 | 1→2 | ★1→★1 | confirmed→confirmed | miss |
| M3-R-027 | ren | 0→0 | 1→2 | ★1→★1 | confirmed→confirmed | miss |
| M3-R-031 | ren | 0→0 | 1→2 | ★1→★1 | confirmed→confirmed | miss |
| M3-R-022 | ren | 0→0 | 1→2 | ★1→★1 | confirmed→confirmed | miss |
| M3-R-005 | ren | 0→0 | 1→2 | ★1→★1 | confirmed→confirmed | miss |
| M2-Y-070 | yang | 0→0 | 1→1 | ★1→★1 | confirmed→confirmed | abstain |
| M2-Y-076 | yang | 0→1 | 0→0 | ★2→★3 | confirmed→confirmed | hit |
| M2-Y-035 | yang | 0→0 | 0→0 | ★2→★2 | confirmed→confirmed | abstain |
| M2-Y-099 | yang | 0→0 | 0→0 | ★2→★2 | confirmed→confirmed | abstain |

### Skipped Rule IDs (in analysis but not in theory yaml)

- G-BD
- G-CH
- G-CHE

### Cross-School Scan
- 已触发（case_count=10，每 10 案） → META/conflict-trends.md 已更新

### Rollback Hint

```
# 回滚到本次 ingest 前：
git revert <commit-hash>
# 或恢复快照：
META/calibration/2026-05-25-after-C-2026-002-壬戌庚戌戊辰丙辰.snapshot.yaml
```

---

## 2026-05-25 21:04 · ingest C-2026-007-乙丑庚辰己丑庚午

case_count: 10
trigger: ingest_feedback

### Rule Updates (2 条)

| rule_id | 派 | hits 旧→新 | misses 旧→新 | conf ★ 旧→新 | status 旧→新 | verdict |
|---|---|---|---|---|---|---|
| M2-Y-120 | yang | 0→0 | 0→1 | ★2→★1 | confirmed→confirmed | miss |
| M2-Y-070 | yang | 0→0 | 1→1 | ★1→★1 | confirmed→confirmed | abstain |

### Cross-School Scan
- 已触发（case_count=10，每 10 案） → META/conflict-trends.md 已更新

### Rollback Hint

```
# 回滚到本次 ingest 前：
git revert <commit-hash>
# 或恢复快照：
META/calibration/2026-05-25-after-C-2026-007-乙丑庚辰己丑庚午.snapshot.yaml
```

---

## 2026-05-25 21:05 · ingest C-2026-008-壬申癸卯丁未壬寅

case_count: 10
trigger: ingest_feedback

### Rule Updates (3 条)

| rule_id | 派 | hits 旧→新 | misses 旧→新 | conf ★ 旧→新 | status 旧→新 | verdict |
|---|---|---|---|---|---|---|
| M3-R-031 | ren | 0→1 | 2→2 | ★1→★2 | confirmed→confirmed | hit |
| M3-R-022 | ren | 0→1 | 2→2 | ★1→★2 | confirmed→confirmed | hit |
| M2-Y-141 | yang | 0→1 | 0→0 | ★2→★3 | confirmed→confirmed | hit |

### Cross-School Scan
- 已触发（case_count=10，每 10 案） → META/conflict-trends.md 已更新

### Rollback Hint

```
# 回滚到本次 ingest 前：
git revert <commit-hash>
# 或恢复快照：
META/calibration/2026-05-25-after-C-2026-008-壬申癸卯丁未壬寅.snapshot.yaml
```

---

## 2026-05-25 21:05 · ingest C-2026-009-庚辰乙酉丙申乙未

case_count: 10
trigger: ingest_feedback

### Rule Updates (3 条)

| rule_id | 派 | hits 旧→新 | misses 旧→新 | conf ★ 旧→新 | status 旧→新 | verdict |
|---|---|---|---|---|---|---|
| M1-D-118 | duan | 0→1 | 0→0 | ★2→★3 | confirmed→confirmed | hit |
| M2-Y-070 | yang | 0→0 | 1→1 | ★1→★1 | confirmed→confirmed | abstain |
| M3-R-031 | ren | 1→2 | 2→2 | ★2→★2 | confirmed→confirmed | hit |

### Cross-School Scan
- 已触发（case_count=10，每 10 案） → META/conflict-trends.md 已更新

### Rollback Hint

```
# 回滚到本次 ingest 前：
git revert <commit-hash>
# 或恢复快照：
META/calibration/2026-05-25-after-C-2026-009-庚辰乙酉丙申乙未.snapshot.yaml
```

---

## 2026-05-25 21:05 · ingest C-2026-010-甲子丁卯癸卯庚申

case_count: 10
trigger: ingest_feedback

### Rule Updates (3 条)

| rule_id | 派 | hits 旧→新 | misses 旧→新 | conf ★ 旧→新 | status 旧→新 | verdict |
|---|---|---|---|---|---|---|
| M1-D-186 | duan | 0→1 | 0→0 | ★2→★3 | confirmed→confirmed | hit |
| M3-R-031 | ren | 2→3 | 2→2 | ★2→★3 | confirmed→confirmed | hit |
| M3-R-022 | ren | 1→2 | 2→2 | ★2→★2 | confirmed→confirmed | hit |

### Cross-School Scan
- 已触发（case_count=10，每 10 案） → META/conflict-trends.md 已更新

### Rollback Hint

```
# 回滚到本次 ingest 前：
git revert <commit-hash>
# 或恢复快照：
META/calibration/2026-05-25-after-C-2026-010-甲子丁卯癸卯庚申.snapshot.yaml
```

---

## 2026-05-25 21:05 · ingest C-2026-011-乙丑乙酉丁丑癸卯

case_count: 10
trigger: ingest_feedback

### Rule Updates (1 条)

| rule_id | 派 | hits 旧→新 | misses 旧→新 | conf ★ 旧→新 | status 旧→新 | verdict |
|---|---|---|---|---|---|---|
| M3-R-031 | ren | 3→4 | 2→2 | ★3→★3 | confirmed→confirmed | hit |

### Cross-School Scan
- 已触发（case_count=10，每 10 案） → META/conflict-trends.md 已更新

### Rollback Hint

```
# 回滚到本次 ingest 前：
git revert <commit-hash>
# 或恢复快照：
META/calibration/2026-05-25-after-C-2026-011-乙丑乙酉丁丑癸卯.snapshot.yaml
```

---

## 2026-05-25 21:05 · ingest C-2026-012-壬戌癸丑丙申壬辰

case_count: 10
trigger: ingest_feedback

### Notes

- analysis.md 中未检出任何含规律 ID 的结论段

### Cross-School Scan
- 已触发（case_count=10，每 10 案） → META/conflict-trends.md 已更新

### Rollback Hint

```
# 回滚到本次 ingest 前：
git revert <commit-hash>
# 或恢复快照：
META/calibration/2026-05-25-after-C-2026-012-壬戌癸丑丙申壬辰.snapshot.yaml
```

---

## 2026-05-25 21:05 · ingest C-2026-013-壬申甲辰丙辰己丑

case_count: 10
trigger: ingest_feedback

### Notes

- analysis.md 中未检出任何含规律 ID 的结论段

### Cross-School Scan
- 已触发（case_count=10，每 10 案） → META/conflict-trends.md 已更新

### Rollback Hint

```
# 回滚到本次 ingest 前：
git revert <commit-hash>
# 或恢复快照：
META/calibration/2026-05-25-after-C-2026-013-壬申甲辰丙辰己丑.snapshot.yaml
```

---

## 2026-05-25 21:05 · ingest C-2026-014-丙戌庚子乙亥辛巳

case_count: 10
trigger: ingest_feedback

### Rule Updates (14 条)

| rule_id | 派 | hits 旧→新 | misses 旧→新 | conf ★ 旧→新 | status 旧→新 | verdict |
|---|---|---|---|---|---|---|
| M1-D-044 | duan | 0→0 | 0→1 | ★2→★1 | confirmed→confirmed | miss |
| M1-D-022 | duan | 0→0 | 0→1 | ★2→★1 | confirmed→confirmed | miss |
| M1-D-122 | duan | 1→1 | 1→2 | ★2→★2 | confirmed→confirmed | miss |
| M2-Y-011 | yang | 0→0 | 0→1 | ★2→★1 | confirmed→confirmed | miss |
| G-LF-002 | gao | 0→0 | 0→1 | ★2→★1 | candidate→candidate | miss |
| M2-Y-091 | yang | 0→0 | 2→3 | ★1→★1 | confirmed→flagged_for_review | miss |
| M3-R-005 | ren | 0→0 | 2→3 | ★1→★1 | confirmed→flagged_for_review | miss |
| M1-D-241 | duan | 0→1 | 0→0 | ★2→★3 | confirmed→confirmed | hit |
| M2-Y-070 | yang | 0→1 | 1→1 | ★1→★2 | confirmed→confirmed | hit |
| M2-Y-042 | yang | 0→0 | 0→1 | ★2→★1 | confirmed→confirmed | miss |
| M3-R-026 | ren | 0→0 | 0→1 | ★2→★1 | confirmed→confirmed | miss |
| G-LF-022 | gao | 0→0 | 1→2 | ★1→★1 | candidate→candidate | miss |
| G-LF-014 | gao | 0→0 | 0→1 | ★2→★1 | candidate→candidate | miss |
| M3-R-031 | ren | 4→4 | 2→3 | ★3→★3 | confirmed→flagged_for_review | miss |

### Status Changes

- M2-Y-091: confirmed → flagged_for_review  (auto-downgrade (累计 misses 触发缓冲阈值))
- M3-R-005: confirmed → flagged_for_review  (auto-downgrade (累计 misses 触发缓冲阈值))
- M3-R-031: confirmed → flagged_for_review  (auto-downgrade (累计 misses 触发缓冲阈值))

### Skipped Rule IDs (in analysis but not in theory yaml)

- G-BD
- G-CH

### Cross-School Scan
- 已触发（case_count=10，每 10 案） → META/conflict-trends.md 已更新

### Rollback Hint

```
# 回滚到本次 ingest 前：
git revert <commit-hash>
# 或恢复快照：
META/calibration/2026-05-25-after-C-2026-014-丙戌庚子乙亥辛巳.snapshot.yaml
```

---

## 2026-05-26 05:35 · ingest C-2026-015-甲寅乙亥丙辰辛卯

case_count: 11
trigger: ingest_feedback

### Rule Updates (16 条)

| rule_id | 派 | hits 旧→新 | misses 旧→新 | conf ★ 旧→新 | status 旧→新 | verdict |
|---|---|---|---|---|---|---|
| M1-D-199 | duan | 0→0 | 0→1 | ★2→★1 | confirmed→confirmed | miss |
| M1-D-014 | duan | 0→1 | 0→0 | ★2→★3 | confirmed→confirmed | hit |
| M1-D-009 | duan | 0→0 | 0→1 | ★2→★1 | confirmed→confirmed | miss |
| M1-D-171 | duan | 0→0 | 0→1 | ★2→★1 | confirmed→confirmed | miss |
| M1-D-122 | duan | 1→1 | 2→3 | ★2→★1 | confirmed→flagged_for_review | miss |
| M1-D-005 | duan | 0→0 | 0→0 | ★2→★2 | confirmed→confirmed | abstain |
| M2-Y-042 | yang | 0→1 | 1→1 | ★1→★2 | confirmed→confirmed | hit |
| M2-Y-119 | yang | 0→1 | 0→0 | ★2→★3 | confirmed→confirmed | hit |
| M2-Y-120 | yang | 0→1 | 1→1 | ★1→★2 | confirmed→confirmed | hit |
| M2-Y-035 | yang | 0→0 | 0→0 | ★2→★2 | confirmed→confirmed | abstain |
| M3-R-005 | ren | 0→0 | 3→4 | ★1→★1 | flagged_for_review→deprecated | miss |
| M3-R-022 | ren | 2→2 | 2→3 | ★2→★2 | confirmed→flagged_for_review | miss |
| M3-R-027 | ren | 0→0 | 2→3 | ★1→★1 | confirmed→flagged_for_review | miss |
| M3-R-003 | ren | 0→0 | 2→3 | ★1→★1 | confirmed→flagged_for_review | miss |
| M3-R-031 | ren | 4→5 | 3→3 | ★3→★3 | flagged_for_review→flagged_for_review | hit |
| M2-Y-070 | yang | 1→2 | 1→1 | ★2→★3 | confirmed→confirmed | hit |

### Status Changes

- M1-D-122: confirmed → flagged_for_review  (auto-downgrade (累计 misses 触发缓冲阈值))
- M3-R-005: flagged_for_review → deprecated  (auto-downgrade (累计 misses 触发缓冲阈值))
- M3-R-022: confirmed → flagged_for_review  (auto-downgrade (累计 misses 触发缓冲阈值))
- M3-R-027: confirmed → flagged_for_review  (auto-downgrade (累计 misses 触发缓冲阈值))
- M3-R-003: confirmed → flagged_for_review  (auto-downgrade (累计 misses 触发缓冲阈值))

### Skipped Rule IDs (in analysis but not in theory yaml)

- G-DY
- G-BD-XL-MIX

### Cross-School Scan
- 未触发（case_count=11，下一次在 case_count % 10 == 0 时）

### Rollback Hint

```
# 回滚到本次 ingest 前：
git revert <commit-hash>
# 或恢复快照：
META/calibration/2026-05-26-after-C-2026-015-甲寅乙亥丙辰辛卯.snapshot.yaml
```

---

## 2026-05-26 14:00 · v1.4 W1 文档/测试同步（非 ingest）

trigger: 架构师评审（基准评审 + 后置评审 + v1.4 启动评审三合一）→ 文档/测试一致性 PR
case_count: 16（无 ingest，本条目为契约/工程级 annotation）
branch: `feat/v1.4-w1-docs-and-tests`

### 工程改动（无规律 hits/misses 变更）

| 改动类别 | 说明 |
|---|---|
| 契约文档 G3 | `engine/contracts/00-OVERVIEW.md` 升 v1.3.0-current；新增 § 〇 单一信息源表（HEAD/版本/N_eff 不再多处硬编码）；§ 4.1/4.2 锁定 D1-D8 + V1-V4；§ 八 三阶发布门槛分层（v1.2/v1.3/v1.4 W1）；§ 九 v1.0→v1.4 演进路径 |
| 契约文档 V1/V2 | `engine/contracts/05-rule-lifecycle.md` § 六 schema 增 `quantifiable: bool` + `domain_restriction: list[str]` 字段示例；§ 6.1 V3 ingest 跳过策略 + 决策动机（M3-R-003 框架性心法 / M3-R-031 域错位）；§ 6.2 向后兼容默认值 |
| 契约文档 G2 | `engine/contracts/06-confidence-model.md` § 2.1 决策 E Beta 切换计数公式 N_eff = N_y + N_n + 0.5·(N_late_hit + N_late_miss)；统一 STATUS / handoff 的 "11/30" 口径 |
| 状态文档 | `STATUS.md` + `handoff.md` 去除硬编码 HEAD 短 SHA；规律计数从错误的 "7 flagged + 1 deprecated" 修正为实际的 **3 flagged + 3 deprecated + 1 restored**（M2-Y-091 / M3-R-005 / M3-R-027 deprecated；M1-D-122 / M3-R-003 / M3-R-022 flagged；M3-R-031 经 architect review 恢复 confirmed） |
| 测试收编 E3 | 新增 7 个 pytest 验收文件 `tests/v1_3_acceptance/`：H4（boundary_miner D3 阈值）/ H5（v1.2 不退化锚点）/ H7（V1 quantifiable）/ H8（V2 domain_restriction）/ H9（V4 event_type_hypotheses）/ H10（social_clock）/ H11（W10 lint）；`pyproject.toml` 注册 `v1_4_acceptance` marker |

### 验证

- 契约文档结构 sniff：00=19 H2 / 05=26 H2 / 06=16 H2，链接路径自洽
- 既存 stdlib smoke 全过：H7+H8+H9 25/25 / H10 36/36 / H11 24/24 = **85/85 PASS**（同一份代码路径）
- `tools.rule_lifecycle._smoke` 5/5 PASS（Rule round-trip 含 quantifiable + domain_restriction）
- 7 个新 pytest 文件 ast.parse 全 OK

### 范围之外（v1.4 W2/W3 处理）

- V5 PictureFindings.industry_path
- V6 wealth_level.framework
- V7 report-v1.4 模板 § 八·零 行业路径耦合提示
- V8 历史报告回溯扫描器 `tools/cross_domain_consistency_check.py --backfill`
- 上述 4 项均涉及 `engine/contracts/03-findings-schema.md` schema_version 升级，独立 PR 处理（避免 schema 一次升级两次）

### Rollback Hint

```
# 本 PR 全部为文档/测试改动，无 yaml/规律状态变更
# 回滚仅需 git revert 本 PR 的 squash commit
```

---

## Annotations

(本段允许手工备注；不影响自动化流程)

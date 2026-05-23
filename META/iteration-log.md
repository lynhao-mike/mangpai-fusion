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

## Annotations

(本段允许手工备注；不影响自动化流程)

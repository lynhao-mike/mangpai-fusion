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

# T-108: P0 构建链 + 门禁 + 归一化 — Status

**Status:** 🔵 Ready for Execution
**Current Step:** Not Started
**Last Updated:** 2026-10-19
**Iteration:** 0
**Size:** L

> ⚠️ 三项必须同批：只做 P0 会让 duan/yang 召回从 92/134 降到 57/98。

---

### Step 0: 备份
**Status:** ⬜ Not Started

- [ ] 备份 7 个文件到 .p0_backup/
- [ ] .p0_backup/ 加进 .gitignore

---

### Step 1: 改 theory_content.py
**Status:** ⬜ Not Started

- [ ] 正则扩 M2-Y
- [ ] YAML 列表拆包
- [ ] Markdown 混排容错
- [ ] 行号匹配用 ^[ \t]*-?[ \t]*rule_id:

---

### Step 2: 改 build_indexes.py
**Status:** ⬜ Not Started

- [ ] 导入 raw_rule_bodies
- [ ] 修 REN_SECTION_TO_TOPIC
- [ ] merge_raw_rule_bodies
- [ ] write_yaml 行尾自适应
- [ ] 修 date 命令 Bug

---

### Step 3: 改 condition_evaluator.py
**Status:** ⬜ Not Started

- [ ] 门禁短路修复（evaluable 才短路）
- [ ] 分数归一化（>1.0 除以 5）

---

### Step 4: 重跑构建
**Status:** ⬜ Not Started

- [ ] python -m tools.build_indexes
- [ ] python -m tools.query_theory --rebuild-index

---

### Step 5: 验证
**Status:** ⬜ Not Started

- [ ] 7 项 Completion Criteria 全部实跑

---

## Execution Log

| Timestamp | Action | Outcome |
|---|---|---|
| 2026-10-19 | Task staged | PROMPT.md and STATUS.md created |

---

## Blockers

*None*

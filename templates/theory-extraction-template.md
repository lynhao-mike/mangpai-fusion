# 原理教案 → 理论规则提取模板

> 用途：从子平格局派、滴天髓调候派等原始教案中提取可归档、可审校、可回测的理论规则。

---

## 1. 原始资料信息

```yaml
source_meta:
  source_path: sources/ziping/ZP-YYYYMMDD-主题-001.md
  expert_system: ziping
  title: 原始资料标题
  source_type: course_note
  provided_by: user
  provided_date: YYYY-MM-DD
  extraction_date: YYYY-MM-DD
  extractor: ai_or_human
```

---

## 2. 原文摘录

> 保留最小必要原文，不整段搬运；只摘录支撑规则判断的关键句。

```text
在这里粘贴关键原文摘录。
```

---

## 3. 理论命题

```yaml
proposition:
  title: 规则标题
  expert_system: ziping
  domain:
    - 财运
    - 事业
  topic: geju
  claim: 简明断语，例如“财格得用且格局清纯，事业财运上限较高”
  polarity: positive
```

---

## 4. 触发条件

```yaml
conditions:
  required:
    - 条件 1
    - 条件 2
  optional:
    - 可增强条件 1
  exclusions:
    - 排除条件 1
```

---

## 5. 输出断语

```yaml
output:
  statement: 面向报告的断语文本
  confidence_hint: candidate
  falsifiable: 可证伪条件，例如“若实际长期无对应事业/财运表现，则该规则失验”
  domains:
    - 财运
    - 事业
```

---

## 6. 与其他流派关系

```yaml
cross_expert_relation:
  blind_school_relation: complementary
  ziping_relation: source
  ditiansui_relation: unknown
  possible_conflicts:
    - 与某流派某规则可能冲突的说明
```

取值建议：

- `source`：本规则所属专家体系。
- `complementary`：互补。
- `conflict`：可能冲突。
- `orthogonal`：不同维度。
- `unknown`：待审校。

---

## 7. 可执行化建议

```yaml
implementation_hint:
  predicates_needed:
    - 月令判断
    - 透干判断
    - 根气判断
  existing_predicates:
    - engine.predicates.tou_cang
    - engine.predicates.strength
  missing_predicates:
    - 待新增谓词
  suggested_analyzer: ZipingWealthAnalyzer
```

---

## 8. 规则草案 YAML

```yaml
- id: ZP-CAND-YYYYMMDD-001
  school: ziping
  expert_system: ziping
  topic: geju
  topic_label: 格局成败
  domain_restriction:
    - 财运
    - 事业
  title: 规则标题
  text: 规则原文或提炼文本
  conditions:
    required: []
    optional: []
    exclusions: []
  output:
    statement: 输出断语
    falsifiable: 可证伪条件
  quantifiable: true
  status: candidate
  source:
    path: sources/ziping/ZP-YYYYMMDD-主题-001.md
    excerpt: 关键摘录
  feedback:
    hits: 0
    misses: 0
    abstained: 0
```

---

## 9. 审校清单

- [ ] 是否保留了原始出处路径。
- [ ] 是否区分了原文、提炼命题、可执行条件。
- [ ] 是否标记了功能域。
- [ ] 是否标记了 expert_system。
- [ ] 是否有可证伪条件。
- [ ] 是否避免把理论心法强行量化。
- [ ] 是否说明与盲派 / 子平 / 滴天髓的关系。
- [ ] 是否注明哪些谓词已存在、哪些需要新增。

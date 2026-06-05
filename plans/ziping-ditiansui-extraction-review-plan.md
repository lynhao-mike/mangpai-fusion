# 子平格局派、滴天髓调候派原文理论提取审查方案

> 目的：在不直接改变生产引擎、不直接确认规则有效性的前提下，从已投放原文中提取“可追溯、可审校、可回测、可进入多专家系统”的候选规则。本文为提取前审查稿，供人工确认后执行。

---

## 1. 已投放原文盘点

### 1.1 子平格局派资料

当前入口：[`sources/ziping/`](../sources/ziping/)

已投放文件：

| 文件 | 初步定位 | 提取优先级 |
|---|---|---:|
| [`sources/ziping/《子平真诠》.md`](../sources/ziping/《子平真诠》.md) | 子平格局法核心文本，重点在格局、用神、成败救应、清浊高低 | P0 |
| [`sources/ziping/《三命通会》.md`](../sources/ziping/《三命通会》.md) | 综合命理大典，内容广，需分层筛选，避免无差别抽取 | P1 |
| [`sources/ziping/穷通宝鉴-明-余春台_part1.md`](../sources/ziping/穷通宝鉴-明-余春台_part1.md) | 调候与月令气候材料，因放在子平目录，提取时需标明其更偏调候/用神 | P1 |
| [`sources/ziping/穷通宝鉴-明-余春台_part2.md`](../sources/ziping/穷通宝鉴-明-余春台_part2.md) | 调候与月令气候材料续篇 | P1 |
| [`sources/ziping/README.md`](../sources/ziping/README.md) | 目录说明，不作为理论原文抽取对象 | 不抽取 |

### 1.2 滴天髓调候派资料

当前入口：[`sources/tiaohou_ditiansui/`](../sources/tiaohou_ditiansui/)

已投放文件：

| 文件 | 初步定位 | 提取优先级 |
|---|---|---:|
| [`sources/tiaohou_ditiansui/滴天髓_part1.md`](../sources/tiaohou_ditiansui/滴天髓_part1.md) | 滴天髓原文分卷，适合作为核心命题来源 | P0 |
| [`sources/tiaohou_ditiansui/滴天髓_part2.md`](../sources/tiaohou_ditiansui/滴天髓_part2.md) | 滴天髓原文分卷 | P0 |
| [`sources/tiaohou_ditiansui/滴天髓_part3.md`](../sources/tiaohou_ditiansui/滴天髓_part3.md) | 滴天髓原文分卷 | P0 |
| [`sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part1.md`](../sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part1.md) | 注解与阐释，适合提取条件化规则，但需区分原文与注解 | P1 |
| [`sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part2.md`](../sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part2.md) | 注解与阐释 | P1 |
| [`sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part3.md`](../sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part3.md) | 注解与阐释 | P1 |
| [`sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md`](../sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md) | 注解与阐释 | P1 |
| [`sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md`](../sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md) | 注解与阐释 | P1 |
| [`sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md`](../sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md) | 注解与阐释 | P1 |
| [`sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part7.md`](../sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part7.md) | 注解与阐释 | P1 |
| [`sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part8.md`](../sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part8.md) | 注解与阐释 | P1 |
| [`sources/tiaohou_ditiansui/README.md`](../sources/tiaohou_ditiansui/README.md) | 目录说明，不作为理论原文抽取对象 | 不抽取 |

---

## 2. 提取总原则

1. **先提取候选命题，不直接入生产规则**
   所有输出先进入审查稿或候选 YAML，默认状态为 `candidate`，不得标为 confirmed、promoted 或可执行。

2. **先原文定位，再理论归纳，再规则化**
   每条规则必须有原文出处、关键摘录、解释、触发条件、排除条件、输出断语、证伪条件。

3. **区分原文、注解、AI 归纳**
   尤其是《滴天髓》与《滴天髓阐微》，必须记录命题来自原文、注解，还是 AI 对多段文本的综合归纳。

4. **流派隔离**
   子平格局派、滴天髓调候派分别形成独立候选规则；即使出现同一主题，也不合并成单条跨派规则，只在 `cross_expert_relation` 中记录互补或冲突。

5. **功能域映射必须保守**
   原文只谈格局高低时，不强行映射到婚姻或健康；原文只谈寒暖燥湿时，不直接推出财运结论，除非原文或注解明确连接现实领域。

6. **可证伪优先**
   无法形成可验证条件的玄学心法、泛泛格言、价值判断，先进入“概念词表/解释层”，不进入规则层。

---

## 3. 分层提取模型

本次提取分 5 层，人工审查时也按 5 层验收。

### L0：目录与来源索引层

目标：建立资料清单，不抽规则。

输出字段：

```yaml
source_doc:
  source_id: ZP-SRC-001
  expert_system: ziping
  path: sources/ziping/《子平真诠》.md
  title: 子平真诠
  source_kind: classical_text
  extraction_status: pending
  notes: 子平格局核心资料
```

验收要求：

- 每个原文文件有唯一 `source_id`。
- 明确属于子平、滴天髓或需特别标注的交叉资料。
- 不在本层生成规则。

### L1：术语与概念层

目标：抽取术语，不直接生成断语。

适合内容：

- 子平：格局、用神、相神、忌神、月令、成格、破格、救应、清浊、真假、顺逆。
- 滴天髓：寒暖、燥湿、气势、流通、病药、通关、调候、源流、旺衰气机。

输出字段：

```yaml
concept:
  id: ZP-CONCEPT-001
  expert_system: ziping
  term: 用神
  definition: 从原文提炼的定义
  source:
    path: sources/ziping/《子平真诠》.md
    excerpt: 支撑定义的关键原文
  review_status: pending
```

验收要求：

- 术语定义必须有原文摘录。
- 不得把术语定义直接当作预测规则。

### L2：结构判断层

目标：抽取“什么条件成立什么结构”的规则。

适合内容：

- 子平：某格成立、某格破格、某用神得力、某相神受伤、格局清浊。
- 滴天髓：寒暖偏枯、燥湿失衡、五行流通受阻、病药成立。

输出字段：

```yaml
structural_rule:
  id: ZP-STRUCT-CAND-001
  expert_system: ziping
  topic: geju
  title: 财格成立条件
  source:
    path: sources/ziping/《子平真诠》.md
    excerpt: 关键原文
  conditions:
    required:
      - 条件 1
    optional:
      - 增强条件 1
    exclusions:
      - 排除条件 1
  structural_output: 财格成立/不成立/受损/可救
  quantifiable: true
  status: candidate
```

验收要求：

- 条件必须能落到八字结构谓词，例如月令、透干、藏干、根气、合冲刑害、旺衰、寒暖燥湿。
- 若条件无法程序化，应标记 `quantifiable: false`。

### L3：功能域映射层

目标：把结构判断谨慎映射到学业、事业、财富、婚姻、健康、性格等功能域。

适合内容：

- 子平：格局成败与事业/财富上限，用神受伤与人生主题，官杀印食财的功能域含义。
- 滴天髓：气候平衡与健康/性格/事业状态，寒暖燥湿与身心表现，病药与改善方向。

输出字段：

```yaml
domain_rule:
  id: DTS-DOMAIN-CAND-001
  expert_system: tiaohou_ditiansui
  topic: tiaohou
  domain_restriction:
    - 健康
    - 性格
  source_structural_rule: DTS-STRUCT-CAND-001
  claim: 寒湿偏重且火土不振时，健康与行动力容易受寒湿拖累
  polarity: risk
  output:
    statement: 面向报告的保守断语
    falsifiable: 若实际长期无寒湿类体感、精力低迷或相关健康表现，则该条失验
  status: candidate
```

验收要求：

- 必须能回链到 L2 结构判断。
- 没有原文支撑的现实域映射不得进入 L3。
- 断语必须保守，不输出绝对化吉凶。

### L4：可执行化准备层

目标：为后续 `engine/ziping/`、`engine/tiaohou_ditiansui/` 预留实现信息。

输出字段：

```yaml
implementation_hint:
  rule_id: ZP-DOMAIN-CAND-001
  predicates_needed:
    - 月令取格
    - 十神定位
    - 透干判断
    - 根气判断
  existing_predicates: []
  missing_predicates:
    - ziping_geju_classifier
  suggested_analyzer: ZipingCareerWealthAnalyzer
  executable_status: theory_only
```

验收要求：

- 只记录实现建议，不写生产代码。
- `executable_status` 初始必须是 `theory_only`。

---

## 4. 两派分别提取重点

### 4.1 子平格局派提取重点

优先从 [`sources/ziping/《子平真诠》.md`](../sources/ziping/《子平真诠》.md) 开始，因为它最适合作为子平格局专家的骨架。

提取顺序：

1. 格局总论：月令、格局、成败、救应。
2. 用神体系：用神、相神、忌神、喜神、仇神。
3. 十神格局：财、官、印、食伤、杀、刃等。
4. 清浊高低：格局层次、富贵贫贱上限。
5. 功能域映射：事业、财富、婚姻、学业、性格。
6. 与调候关系：涉及气候、寒暖、燥湿时只记录关系，不抢归滴天髓规则。

首批建议产物：

| 产物 | 数量建议 | 说明 |
|---|---:|---|
| 术语概念 | 20-40 条 | 用于统一子平术语 |
| 结构规则 | 30-60 条 | 格局成立、破格、救应 |
| 功能域规则 | 15-30 条 | 优先事业、财富、婚姻 |
| 实现谓词清单 | 1 份 | 给后续 analyzer 使用 |

### 4.2 滴天髓调候派提取重点

优先从 [`sources/tiaohou_ditiansui/滴天髓_part1.md`](../sources/tiaohou_ditiansui/滴天髓_part1.md)、[`sources/tiaohou_ditiansui/滴天髓_part2.md`](../sources/tiaohou_ditiansui/滴天髓_part2.md)、[`sources/tiaohou_ditiansui/滴天髓_part3.md`](../sources/tiaohou_ditiansui/滴天髓_part3.md) 抽取原文命题，再用《滴天髓阐微》系列解释条件。

提取顺序：

1. 气势总论：旺衰、源流、清浊、流通。
2. 寒暖燥湿：四时、五行气候、偏枯。
3. 病药关系：病在哪里、药是什么、药是否有力。
4. 通关流通：冲突五行如何流通、何时停滞。
5. 功能域映射：健康、性格优先，其次事业、婚姻、财运。
6. 大运流年：气候改变与病药触发。

首批建议产物：

| 产物 | 数量建议 | 说明 |
|---|---:|---|
| 术语概念 | 20-40 条 | 寒暖燥湿、病药、流通等 |
| 结构规则 | 30-60 条 | 气候偏枯、病药成立、流通受阻 |
| 功能域规则 | 15-30 条 | 优先健康、性格、事业 |
| 实现谓词清单 | 1 份 | 给后续 analyzer 使用 |

---

## 5. 最终输出文件建议

### 5.1 第一阶段：审查型 Markdown

先不直接写 YAML 主库，先生成可人工审查的提取稿：

| 文件 | 用途 |
|---|---|
| `theory/raw/ziping/extracted/子平格局派_候选理论提取_YYYY-MM-DD.md` | 子平提取审查稿 |
| `theory/raw/tiaohou_ditiansui/extracted/滴天髓调候派_候选理论提取_YYYY-MM-DD.md` | 滴天髓提取审查稿 |

每条候选规则使用 [`templates/theory-extraction-template.md`](../templates/theory-extraction-template.md) 的结构。

### 5.2 第二阶段：候选 YAML

人工审查通过后，再写入：

| 文件 | 用途 |
|---|---|
| `theory/ziping/index.yaml` | 子平格局派候选规则 |
| `theory/tiaohou_ditiansui/index.yaml` | 滴天髓调候派候选规则 |

初始规则状态：

```yaml
status: candidate
feedback:
  hits: 0
  misses: 0
  abstained: 0
executable_status: theory_only
```

### 5.3 第三阶段：多专家系统接入准备

进入代码实现前，另行输出：

| 文件 | 用途 |
|---|---|
| `theory/ziping/predicate_requirements.md` | 子平 analyzer 所需谓词清单 |
| `theory/tiaohou_ditiansui/predicate_requirements.md` | 滴天髓 analyzer 所需谓词清单 |
| `plans/ziping-tiaohou-adapter-plan.md` | 两派如何转换为 `ExpertReading` 的实现方案 |

---

## 6. ID 与字段规范

由于现有 [`theory/SCHEMA.md`](../theory/SCHEMA.md) 仍以四派盲派为主，建议新增扩展前缀，不复用旧 `E`、`F` 占位含义。

推荐 ID：

| 专家体系 | ID 前缀 | 示例 |
|---|---|---|
| 子平格局派 | `ZP` | `ZP-GEJU-CAND-001` |
| 滴天髓调候派 | `DTS` | `DTS-TIAOHOU-CAND-001` |
| 子平概念 | `ZP-CONCEPT` | `ZP-CONCEPT-001` |
| 滴天髓概念 | `DTS-CONCEPT` | `DTS-CONCEPT-001` |

推荐字段：

```yaml
- id: ZP-GEJU-CAND-001
  school: ziping
  expert_system: ziping
  topic: geju
  topic_label: 格局成败
  domain_restriction:
    - 事业
    - 财运
  title: 规则标题
  source:
    path: sources/ziping/《子平真诠》.md
    excerpt: 关键摘录
    source_layer: original_text
  interpretation: AI 或人工解释，必须与原文分开
  conditions:
    required: []
    optional: []
    exclusions: []
  output:
    statement: 面向报告的保守断语
    falsifiable: 可证伪条件
  cross_expert_relation:
    blind_school_relation: unknown
    ziping_relation: source
    ditiansui_relation: complementary
  quantifiable: true
  executable_status: theory_only
  status: candidate
  feedback:
    hits: 0
    misses: 0
    abstained: 0
```

---

## 7. 审查重点

请人工重点审查以下问题：

1. **是否允许把《穷通宝鉴》放入子平提取流？**
   当前文件位于 [`sources/ziping/`](../sources/ziping/)，但内容天然偏调候。建议允许提取，但必须标注 `topic: tiaohou` 或 `cross_expert_relation.ditiansui_relation: complementary`，不把它伪装成纯格局规则。

2. **是否先从经典骨架抽取，而不是全库铺开？**
   建议先做两份样板：子平从《子平真诠》抽 10-20 条，滴天髓从《滴天髓》原文抽 10-20 条，再审查质量。

3. **是否接受 L0-L4 分层？**
   该分层能避免把术语、心法、结构判断、现实断语混在一起。

4. **是否允许 AI 归纳？**
   建议允许，但必须写入 `interpretation`，并与 `source.excerpt` 分离。

5. **是否先生成 Markdown 审查稿，再写 YAML？**
   建议必须如此，避免大量候选规则直接污染主规则库。

---

## 8. 禁止事项

1. 不直接把整段原文复制进规则库。
2. 不把没有可执行条件的心法硬转成规则。
3. 不把候选规则标为 confirmed、promoted 或 active。
4. 不伪造命中率、反馈数、案例验证。
5. 不把子平与滴天髓规则合并成一条规则。
6. 不直接修改生产报告、pipeline 或反馈摄入工具。
7. 不在低样本下比较“哪派最准”。

---

## 9. 建议审查后执行顺序

如果本方案通过，建议执行：

1. 建立 `theory/raw/ziping/extracted/` 与 `theory/raw/tiaohou_ditiansui/extracted/`。
2. 从 [`sources/ziping/《子平真诠》.md`](../sources/ziping/《子平真诠》.md) 抽取第一批 10-20 条样板。
3. 从 [`sources/tiaohou_ditiansui/滴天髓_part1.md`](../sources/tiaohou_ditiansui/滴天髓_part1.md) 抽取第一批 10-20 条样板。
4. 人工审查样板质量。
5. 修订模板和字段。
6. 再批量扩展到其他原文。

---

## 10. 建议结论

推荐采用“先样板、后批量；先 Markdown 审查稿、后 YAML 候选库；先 theory_only、后 analyzer 接线”的三阶段方案。

第一轮不要追求数量，而要验证：

- 原文出处是否可靠。
- 条件拆解是否可执行。
- 功能域映射是否保守。
- 子平与滴天髓是否保持隔离。
- 规则是否能进入未来 `ExpertReading` 协议。

只有第一轮样板经人工确认后，再进入大规模抽取。

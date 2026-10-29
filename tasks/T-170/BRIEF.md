# T-170 BRIEF · Golden-20 教材真盘盲推集（只读策展）

> Worker 简报。四项：改动文件 / 原始输出 / 未完成与风险 / 下游须知。
> **Worker 的「通过」不算数**：下列命令与数字请中枢现场重跑。

## 1. 改动文件

| 文件 | 性质 | 说明 |
|---|---|---|
| `META/golden-20-v1.json` | 新建 | 盲测输入，20 例；仅 8 个键（case_id/school/four_pillars/gender/dayun_start_age/dayun_direction/dayun/source） |
| `META/golden-20-answers-v1.json` | 新建 | 答案，与输入物理分离；每字段带 `source_refs`（path+line+quote 逐字） |
| `META/golden-20-v1.md` | 新建 | 清单、四类覆盖、缺口、选例理由、20 例索引、schema 说明 |
| `tests/tools/test_golden_20_schema.py` | 新建 | 7 条校验：分离性、逐字锚点、四类覆盖、无重复盘、边号必须挂快照 |
| `tasks/T-170/BRIEF.md` | 新建 | 本文件 |
| `tasks/T-170/STATUS.md` | 追加 | Execution Log 一行 |

**未改**：`sources/**`、`theory/**`、`engine/**`、规则、评测集、既有测试；未跑任何 git 写操作。
`tasks/T-170/PROMPT.md` 未改（无 Amendments 需求）。

## 2. 原始输出（现场可复现）

### 2.1 数量与四类

```text
cases: 20
categories: {'制用': 6, '化用': 4, '墓用': 5, '救应': 5}
null fields: {'original_analysis': 0, 'core_work': 0, 'role_direction': 1,
              'adjudication': 0, 'rescue': 14, 'timing': 3}
source_refs 总数: 137（全部逐字命中源文件对应行）
```

- 起运年龄：G20-006、G20-019 = 3 岁（书上有岁数表）；其余 18 例 `null`（原书未给）。
- 学校分布：duan 20 / yang 0 / ren 0 / ziping 0（理由见 §3.2）。

### 2.2 分离性校验

```text
python -m pytest tests/tools/test_golden_20_schema.py -q -o addopts="-ra --tb=short"
→ 7 passed
```

校验内容：输入侧键集合 ⊆ 允许键；答案字段名不得出现在盲测文本；答案字段**正文**
（≥8 字）不得出现在盲测文本；每个非 null 字段必须有同名字段的 `source_refs`；
每条 `quote` 必须是对应文件对应行的**逐字子串**；四类各 ≥3；同盘不重复；
`edge_ids` 非空时必须挂快照且 `candidate_ids` 非空。

### 2.3 四柱/大运 engine 复核（抽查 5 例，一例覆盖四类）

```text
rc=0 G20-001 input='庚午 乙酉 庚子 壬午' chart='庚午 乙酉 庚子 壬午' dir=顺 dayun6=丙戌 丁亥 戊子 己丑 庚寅 辛卯
rc=0 G20-007 input='壬寅 丙午 戊寅 乙卯' chart='壬寅 丙午 戊寅 乙卯' dir=顺 dayun6=丁未 戊申 己酉 庚戌 辛亥 壬子
rc=0 G20-013 input='乙酉 己卯 乙未 癸未' chart='乙酉 己卯 乙未 癸未' dir=逆 dayun6=戊寅 丁丑 丙子 乙亥 甲戌 癸酉
rc=0 G20-016 input='壬寅 丁未 丁巳 庚戌' chart='壬寅 丁未 丁巳 庚戌' dir=顺 dayun6=戊申 己酉 庚戌 辛亥 壬子 癸丑
rc=0 G20-019 input='壬申 己酉 癸巳 辛酉' chart='壬申 己酉 癸巳 辛酉' dir=顺 dayun6=庚戌 辛亥 壬子 癸丑 甲寅 乙卯
```

命令：`.venv\Scripts\python.exe -m engine.cli all --pillars "<四柱>" --gender 乾 --json`

### 2.4 大运与原书逐例比对

- 14 例书表与 engine 十步**逐字一致**；
- 6 例书表首项多一月柱（`月柱起首`体例），去掉首项后与 engine 一致；
- 盲测输入取 engine 十步，`dayun_direction` 取 engine 顺/逆。

### 2.5 全量回归

```text
.venv\Scripts\python.exe -m pytest -q
→ 1365 passed, 1 skipped（skip = T-114 已知红灯，与本卡无关）
```

## 3. 未完成与风险

### 3.1 化用类应期缺口（真实缺口）

4 例化用中只有 2 例（G20-007、G20-008）原书给了大运吉凶；G20-009、G20-010 原书只给
结构判断，`timing` 为 `null`。**若按「必须含应期」严卡，化用 = 2 例，未达 3 例线。**
《盲派初级命理学》本身写明「这种结构比较少」，属于语料上限，不是筛选偷懒。

### 3.2 派别单一（真实缺口）

20 例全部来自 `sources/duan/`。杨派、任派教材的命例普遍**不列大运干支表**
（全书检索：带完整大运序列的案例几乎只在段派讲义里），而「制用/化用/墓用/救应」
本身是段派做功体系术语。按卡上「每例必须有大运序列」的硬标准，杨/任无法产生合规样本。
**跨派样本 = 0，这是本集最大的代表性缺陷。**

### 3.3 起运年龄

18/20 例 `dayun_start_age = null`。不要用「出生年 + 3 岁」之类反推补值。

### 3.4 同造双解（弱对照）

G20-013（乙酉 己卯 乙未 癸未）原书 L910–912 与 L926–928 有两套读法（墓库牢狱 /
两未制财）。本集只取前者，答案里 `curator_notes` 已标。**该例只宜作弱对照。**

### 3.5 OCR 残损

G20-014 日支原文作「屈」，正文自证「主位辰」，四柱按 辰 复原；G20-016 原文「戍」即「戌」。
引用保留原字，未改原文。

### 3.6 结构绑定：本版**没有** edge_id / candidate_id（按 T-169 约束）

- 本集答案只锚定原书文本，`struct_refs.status` 全部 `book_text_only`；
- 原因是 T-169 的两条实测：①叠加 `--dayun-index/--liunian` 后 `edge_id` 全量重编号
  （同字 `e012` 由 `liuhe[M.b,D.b]` 变 `ke[M.s,LN2026.s]`，边数 16→39）；
  ②`duan_zuogong.candidates` 不是关系边全集（三盘夫妻宫各漏 3/4/1 条）。
- 因此本版**没有裸边号**，但**也没有任何已绑定结构**。每条只给原局 `chart_snapshot.chart_id`
  供下游 join。**风险：若把本集当"已绑定结构"的金标使用，会高估覆盖面。**
- 若后续要补：必须 `candidate_id` + `relations.edge_id` 双路，且新快照
  `{chart_id, dayun_index, liunian_year}`；只有 candidate 的标 `candidate_only`。

## 4. 下游须知

1. **schema 不走样**：盲测输入只有 8 个键；`category` 只在答案侧（进输入等于泄题）。
2. **字段空值是有信息量的**：`rescue: null` = 原书没有救应判断，不是「没有救应」。
3. **`source_refs` 是逐字锚点**：`quote` 一定是该行子串，可直接回原文；不要改写成白话。
4. **多句应期是数组**：单句是字符串，多句是 `list`，下游解析要兼容两种。
5. **评分不要用本集做统计**：n=20，四类 6/4/5/5，只够做「盲推复原」的四标准人工判定
   （零幻觉 / 主功一致 / 成败救应不错位 / 岁运机理同构），不够任何 p 值或比例检验。
6. **exactly-once 数据约定**：`case_id` 稳定（G20-001…020），后续加例请从 G20-021 起，
   不要重排——下游可能已按 case_id 存盲推结果。

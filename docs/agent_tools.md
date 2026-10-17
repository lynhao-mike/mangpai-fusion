# Agent 工具调用手册与五步推演 SOP

WP-7 工具行为补充：

- 四柱输入的所有 CLI 分项均返回 `input_limitations`，说明缺少出生时刻时不能计算起运年龄/日期、大运公历起止年份与人元司令；大运干支顺逆序列仍可使用。
- 两个 CLI 在解析参数之前将标准输出、标准错误显式设为 UTF-8，重定向输出和子进程读取也应使用 UTF-8 解码。
- 段派 290 条、任派 200 条规则的正文由原稿按规则 ID 提取，保存在 `theory/_light_index.json` 的 `conclusion`，并保留 `raw_file`、`raw_anchor`；检索摘要仍限制为 200 字，完整条件与边界须按来源回读。找不到正文时，结果显式返回 `content_status: title_only` 及非空缺项说明。
- 《穷通宝鉴》120 条日干/月支摘录已加入子平检索；查询可使用“壬水 寅月”“壬日 正月”等语境。专论日干/月令冲突会降权，排序只表示检索相关度。
- 来源锚点优先采用 `line:行号`；原索引缺少有效定位时，以摘录或标题定位原稿。索引、段任原稿、经典源文件及调候表变化会触发缓存重建。

本手册规定 Agent 获取盘面事实、检索理论证据及组织分析的标准路径。确定性事实由引擎生成，理论条目由检索器定位；工具输出是证据材料，不自动构成命理结论。

## 工具 1：确定性盘面事实 CLI

入口：[`engine.cli`](../engine/cli.py)，底层无状态 API 位于 [`engine/api/`](../engine/api/)。仅以工具返回的 JSON 作为盘面事实依据。

### 调用方式

```bash
# 公历排盘全量事实
python -m engine.cli all --birth "1980-02-15 02:30" --gender 乾 --json

# 四柱直接分析，叠加第 3 步大运及 2026 流年
python -m engine.cli all --pillars "庚申 戊寅 壬子 辛丑" --gender 乾 --dayun-index 3 --liunian 2026 --json

# 分项调用：chart / relations / strength / structures
python -m engine.cli chart --birth "1980-02-15 02:30" --gender 乾 --json
python -m engine.cli relations --birth "1980-02-15 02:30" --gender 乾 --json
python -m engine.cli strength --birth "1980-02-15 02:30" --gender 乾 --json
python -m engine.cli structures --birth "1980-02-15 02:30" --gender 乾 --json
```

`all`、`chart`、`relations`、`strength`、`structures` 均接受 `--birth` 或 `--pillars`，两者必须且只能提供一个；性别可用 `乾` / `坤`。岁运参数为 `--dayun-index N`、`--liunian YYYY`，会影响关系图及做功候选。四柱直接输入时若要查询大运，需确认输入盘的大运信息可用；不得自行补推。

### 盘面地址与段派宾主

| 地址 | 含义 |
|---|---|
| `Y.s` / `M.s` / `D.s` / `H.s` | 年 / 月 / 日 / 时干 |
| `Y.b` / `M.b` / `D.b` / `H.b` | 年 / 月 / 日 / 时支 |
| `DY{n}.s` / `DY{n}.b` | 第 n 步大运干 / 支 |
| `LN{year}.s` / `LN{year}.b` | 指定年份流年干 / 支 |

段派宾主四层按地址位置判断：第 1 层以日干为主、其余七字为宾；第 2 层以日柱为主、其余三柱为宾；第 3 层以日柱与时柱为主、年月为宾；第 4 层以原局八字为主、岁运为宾。宾主位置是分析视角，不等同于吉凶或做功结论。

关系边 ID（如 `e003`）用于指回本次 `relations` 返回的具体关系；应原样引用，不要自行编号或把不同次输出的 ID 当作同一事实。

### 核心返回字段

`all` 返回完整分析对象，主要顶层字段如下：

- `chart`：四柱、藏干、十神、旬空、起运/大运信息及使用的口径 `profile`；注意 `boundary_warnings` 与 `variants`。此入口会裁剪部分冗余数据。
- `relations`：关系图。含 `edges`（关系边、参与地址、距离、间隔地址、组完整度、属性及出处）、`pair_index`（地址组合到边 ID 的索引）、`muku`（墓库事实、入墓候选、开闭相关边与需裁决提示）以及 `variants`。`all` 为控制体积会省略 `pair_index`；需直接查索引时调用 `relations` 子命令获取完整关系图。
- `strength`：原子能量事实，不输出旺衰总分或强弱结论。重点查看 `siling`（人元司令）、`roots`（通根与印气地址）、`camp_counts`（分层阵营计数）及 `climate.tiaohou_lookup`（《穷通宝鉴》调候查表用字、在盘位置与出处）。
- `shensha`：神煞事实及对应位置/出处；须核对适用口径，不得直接转成断语。
- `structures`：子平格局的构成要件、破格/救应检查及证据。状态可能为 `met`、`unmet`、`not_evaluable` 或 `needs_judgment`；要件命中不代表已经成格，力量判断由 Agent 结合证据裁决。
- `duan_zuogong`：段派 `tiyong` 体用视图及 `candidates` 做功候选（如制用、化用、生泄用、合用、墓用）。候选不等于已经做成功，也不自动代表吉凶。

若需核验各字段的完整 schema，查看 [`engine/facts/types.py`](../engine/facts/types.py)、[`engine/facts/relation_graph.py`](../engine/facts/relation_graph.py)、[`engine/facts/strength_facts.py`](../engine/facts/strength_facts.py) 与 [`engine/facts/structure_check.py`](../engine/facts/structure_check.py)。

## 工具 2：六源理论语料库原子检索器

入口：[`tools.query_theory`](../tools/query_theory.py)。检索结果提供条目 ID、来源、简述和 `source_ref`，用于定位理论依据，不是自动裁决。

覆盖六源：

- 四派盲派：`gao` 高德臣、`duan` 段建业、`yang` 杨清娟、`ren` 任付红。
- 传统经典：`ziping` 含《子平真诠》《三命通会》《穷通宝鉴》《千里命稿》；`ditiansui` / `tiaohou_ditiansui` 对应《滴天髓》《滴天髓阐微》及调候派提取条目。

### 调用方式

```bash
# 跨派综合检索
python -m tools.query_theory --query "寅申冲 食神制杀" --top-k 5 --per-school-cap 2 --json

# 按流派与领域定向检索
python -m tools.query_theory --query "夫妻宫 穿" --schools yang duan ren ziping --domain 婚姻 --top-k 5 --json
```

`--query` 支持空格或逗号分隔关键词；`--schools` 后的流派名称按空格分隔（不可用逗号拼成单个名称）。`--domain` 限定领域，`--top-k` 范围为 1–10，`--per-school-cap` 控制每源命中数（`0` 表示不限）。默认输出 JSON 需显式加 `--json`。可用 `--rebuild-index` 强制重建轻量索引。

逐条检查 `school`、`classic_name`、`title`、`statement` 及 `source_ref.path` / `source_ref.anchor`；引用时保留来源与定位，并回到对应原文核对上下文、触发条件和适用边界。检索未命中或来源不足时应说明证据缺口，不得补造引文。

## 标准五步推演 SOP

### Step 1：排盘与边界核验

调用 `engine.cli chart` 或 `engine.cli all`。核对输入模式、性别、四柱及 `profile`；检查 `boundary_warnings`，尤其交节前后 2 小时内的 `near_jie` 与晚子时相关警告，并检查 `variants` 是否显示不同口径下盘面/岁运差异。真太阳时是否校正由输入方确认；工具未确认时不假设已校正。出现边界差异时先并列记录，不悄然选定一种口径。

### Step 2：提取结构、关系与能量事实

- 从 `relations` 检查关系边的地址、`distance` / `between`、三合与三刑的 `completeness`，以及 `muku` 中的墓库开闭边、入墓候选、排除项和 `requires_judgment`。
- 从 `strength` 检查人元司令 `siling`、各干 `roots`、`camp_counts` 分层计数，以及 `climate.tiaohou_lookup` 所列调候字在盘中的位置。
- 从 `structures` 对照子平格局要件、破格和救应状态；保留 `needs_judgment` 与 `not_evaluable`，不把程序核对结果等同格局成败。
- 从 `duan_zuogong` 查看体用与五类做功候选，回到对应关系边和地址判断宾主，不把候选写成既成结论。

### Step 3：围绕矛盾定向检索

依据 Step 2 中实际出现的核心矛盾或问题（如“伤官见官”“亥入辰墓”“寒木向阳”）调用 `tools.query_theory`。定向覆盖相关盲派与《子平真诠》《滴天髓》《穷通宝鉴》等原文/提取条目；逐条读取 `source_ref`，确认触发条件、论述语境和适用范围。不要为凑齐流派而引用无关命中。

### Step 4：冲突裁决与多维推理

分别比较子平格局要件与成败、滴天髓/穷通的气候与源流、盲派宾主体用及做功路径。明确证据在哪些点一致、哪些点因流派规则或口径不同而分歧；结合用户所问事项、原局事实和岁运引动解释取舍。区分工具确定事实、理论规则、推理假设和最终判断；证据不足或口径会改变结论时，保留分歧并说明影响，不用单一流派抹除其他有效证据。

### Step 5：结构化输出与可追溯引用

报告中对关键事实引用盘面地址（如 `M.b`、`DY3.b`）及关系边 ID（如 `e003`），并对理论判断引用流派/典籍与 `source_ref`。说明规则触发条件、适用边界、推理路径、岁运语境及不确定性；将事实、候选、理论依据和 Agent 裁决分开表述。未由工具返回或来源未核实的内容，明确标记不确定，不以心算补齐。

### Step 6：裁决显式化与人话报告生成（强制执行）

> **前置声明 1**：Step 6 **不放宽** Step 1–5 的事实纪律。「敢拍板」指的是对有证据支撑的分歧给出主次取舍，不是无据断言。
> **前置声明 2**：Step 6 与人话规范**对引擎变更免疫**——规范、模板、Linter 的风格类检查（`docs/analysis_human_touch.md` §3.5.1 永续层）不随 `engine/` 变更而失效；若 Linter 报「契约失效」，按该文档 §3.5.2 同步清单处理，**不得通过删改规范来迁就**。

当产出「人话版 / 说人话 / 命主可读」报告时，按下述六条执行：

- **a. 主脑定调**：开篇用一句话写出本命最核心的张力与主线（不超 80 字，禁修辞套话与免责词）。
- **b. 免责关笼、正文敢拍板**：所有缺项说明与免责统一收拢在《先把话说死》；正文第一至五节至少给出 3 个以上明确的「大概率」主断，严禁在正文中逐段写「不能据此断……」「不等于必然……」等自我拆台句。
- **c. 结构必翻译**：所有干支关系进入正文前必须按 `docs/analysis_human_touch.md` §3.2 翻译成现实人事场景；边号与理论 ID 收拢为节末简注或文末《附：关键依据索引与可核验断语表》。
- **d. 分歧必站队**：出现流派分歧必须给出「我采信 X 为主，理由是……」的明确裁决；「各有道理 / 尚难定论」视为任务未完成。
- **e. 建议必执行**：每条建议必须符合「动词 + 对象 + 场景 + 时限」句式。
- **f. 输出后必过 Linter**：生成报告后调用 `python -m tools.human_touch_linter <报告文件>` 自检，确保零 ERROR 再交付。

模板与门禁入口：[`templates/report-v7-human.md`](../templates/report-v7-human.md)（结构）、[`docs/analysis_human_touch.md`](../docs/analysis_human_touch.md)（写法纪律）、[`tools/human_touch_linter.py`](../tools/human_touch_linter.py)（防骑墙门禁）。归档规则见 [`../reports/README.md`](../reports/README.md)。

# B1 全量锚点审计报告（2026-10-18）

> **范围**：`theory/raw/{yang,duan,gao,ren}/promoted/deep-extract-*.md` 共 12 个文件、**417** 条记录（yang 237 / duan 138 / gao 36 / ren 6）。
> **方法**：逐条验证 ① raw_file 存在性；② `line:N` 行号不越界（1 ≤ N ≤ 文件行数）；③ verify_fragment 去空白后在第 N-5..N+5 行窗口内逐行命中（1-based）。
> **纪律**：本审计只读 `theory/` 与 `sources/`，未修改任何语料/索引/缓存，未运行 `tools/build_indexes.py`；唯一写入为本报告与 `.workbuddy-ai/` 下的审计脚本/结果 JSON。
> **可复现**：`PYTHONIOENCODING=utf-8 python .workbuddy-ai/b1_anchor_audit.py`（Python 3.14.5 / PyYAML 6.0.3）。

## 0. 结论摘要

- **三项验证 417/417 全部通过**：12 个文件全部存在；417 个 `line:N` 全部不越界；417 条 verify_fragment 全部在 ±5 行窗口内命中。按任务书四类未命中口径，**line-drift / transcription / path-error / fabricated 均为 0**。
- **但存在 18 条"容差内潜在漂移"**（占 4.3%）：片段确实在窗口内，但不在锚点行上，实际落在锚点行附近（+2 行 14 条、+4 行 3 条、-1 行 1 条）。锚点行精确命中 399 条（95.7%）。这类记录能过校验器，但回读时按锚点行定位会读错段，建议修正。
- **计数口径差异**：任务书写的"430"与实测 417 差 **13 条**，在仓库现有 12 个提取文件中无法复现 430；本报告以实测 **417** 为准（明细见 §3.7）。
- **最值得注意的系统性问题**：① 杨派 b01 的 12/41 条锚点指向"引子行"，片段在下一非空行（+2/+4 偏移）；② 任派 6 条的 `raw_file` 指向理论重写稿而非 `sources/ren` 原稿（5/6 片段在原稿中不存在）；③ 杨派提取稿存在 `theory/yang/` 与 `theory/raw/yang/promoted/` 两份完全相同的副本（237×2 条）。

## 1. 汇总

### 1.1 任务书口径（四类未命中）

| 学派 | 总数 | 命中 | line-drift | transcription | path-error | fabricated |
|---|---|---|---|---|---|---|
| yang | 237 | 237 | 0 | 0 | 0 | 0 |
| duan | 138 | 138 | 0 | 0 | 0 | 0 |
| gao | 36 | 36 | 0 | 0 | 0 | 0 |
| ren | 6 | 6 | 0 | 0 | 0 | 0 |
| **合计** | **417** | **417** | **0** | **0** | **0** | **0** |

**自检**：按学派分别自洽 —— yang: 237 = 237+0+0+0+0；duan: 138 = 138+0+0+0+0；gao: 36 = 36+0+0+0+0；ren: 6 = 6+0+0+0+0；合计 417 = 417。**PASS**

### 1.2 补充口径（精确行命中 vs 窗口内偏移）

> 任务书把 ±5 行内一律记为"命中"；下表把"命中"再拆成"锚点行精确命中"与"窗口内偏移"，用于暴露容差内潜在漂移（不计入 §1.1 的四类未命中）。

| 学派 | 总数 | 锚点行精确命中 | 窗口内偏移 | 精确率 |
|---|---|---|---|---|
| yang | 237 | 221 | 16 | 93.2% |
| duan | 138 | 136 | 2 | 98.6% |
| gao | 36 | 36 | 0 | 100.0% |
| ren | 6 | 6 | 0 | 100.0% |
| **合计** | **417** | **399** | **18** | **95.7%** |

### 1.3 按提取文件细分

| 提取文件 | 学派 | 总数 | 精确命中 | 窗口内偏移 | 偏移分布 |
|---|---|---|---|---|---|
| `deep-extract-duan-b01.md` | duan | 40 | 39 | 1 | +2×1 |
| `deep-extract-duan-b02.md` | duan | 40 | 39 | 1 | -1×1 |
| `deep-extract-duan-b03.md` | duan | 32 | 32 | 0 | — |
| `deep-extract-duan-b04.md` | duan | 26 | 26 | 0 | — |
| `deep-extract-gao-fix-b01.md` | gao | 36 | 36 | 0 | — |
| `deep-extract-ren-fix-b01.md` | ren | 6 | 6 | 0 | — |
| `deep-extract-yang-b01.md` | yang | 41 | 29 | 12 | +2×9、+4×3 |
| `deep-extract-yang-b02.md` | yang | 45 | 43 | 2 | +2×2 |
| `deep-extract-yang-b03.md` | yang | 45 | 45 | 0 | — |
| `deep-extract-yang-b04.md` | yang | 50 | 50 | 0 | — |
| `deep-extract-yang-b05.md` | yang | 42 | 40 | 2 | +2×2 |
| `deep-extract-yang-b06.md` | yang | 14 | 14 | 0 | — |

## 2. 未命中明细

### 2.1 四类未命中

**无。** 417 条记录全部在 `raw_file` 存在、`line:N` 不越界、verify_fragment 在 ±5 行窗口内命中三项上通过，因此 line-drift / transcription / path-error / fabricated 四类均为 0 条，无需给出建议修正。

### 2.2 容差内潜在漂移明细（不属四类未命中，但建议修正）

共 **18** 条：verify_fragment 在 ±5 行窗口内，但不在 `raw_anchor` 指定的行上。

| id | 学派 | 提取文件 | 锚点行 | 实际命中行 | 偏移 | 类型 | 建议修正 |
|---|---|---|---|---|---|---|---|
| `M1-D-307` | duan | `deep-extract-duan-b01.md` | line:362 | line:364 | +2 | C 跨段合并/摘要 | 补 anchor_span line:360-366（含锚点行 line:362 与命中行 line:364，覆盖 statement 100%） |
| `M1-D-370` | duan | `deep-extract-duan-b02.md` | line:148 | line:147 | -1 | C 跨段合并/摘要 | 补 anchor_span line:146-148（含锚点行 line:148 与命中行 line:147，覆盖 statement 83%，未达 85%，建议人工复核该段） |
| `M2-Y-184` | yang | `deep-extract-yang-b01.md` | line:218 | line:220 | +2 | B 合并型（锚点行+命中行） | 补 anchor_span line:218-220（锚点可保留 line:218） |
| `M2-Y-185` | yang | `deep-extract-yang-b01.md` | line:224 | line:226 | +2 | C 跨段合并/摘要 | 补 anchor_span line:224-230（含锚点行 line:224 与命中行 line:226，覆盖 statement 88%） |
| `M2-Y-188` | yang | `deep-extract-yang-b01.md` | line:248 | line:250 | +2 | C 跨段合并/摘要 | 补 anchor_span line:248-252（含锚点行 line:248 与命中行 line:250，覆盖 statement 93%） |
| `M2-Y-189` | yang | `deep-extract-yang-b01.md` | line:254 | line:258 | +4 | C 跨段合并/摘要 | 补 anchor_span line:254-260（含锚点行 line:254 与命中行 line:258，覆盖 statement 89%） |
| `M2-Y-190` | yang | `deep-extract-yang-b01.md` | line:262 | line:264 | +2 | C 跨段合并/摘要 | 补 anchor_span line:262-268（含锚点行 line:262 与命中行 line:264，覆盖 statement 77%，未达 85%，建议人工复核该段） |
| `M2-Y-193` | yang | `deep-extract-yang-b01.md` | line:290 | line:292 | +2 | C 跨段合并/摘要 | 补 anchor_span line:290-306（含锚点行 line:290 与命中行 line:292，覆盖 statement 79%，未达 85%，建议人工复核该段） |
| `M2-Y-194` | yang | `deep-extract-yang-b01.md` | line:308 | line:310 | +2 | A 锚点错位 | raw_anchor 改为 line:310 |
| `M2-Y-195` | yang | `deep-extract-yang-b01.md` | line:312 | line:316 | +4 | C 跨段合并/摘要 | 补 anchor_span line:312-318（含锚点行 line:312 与命中行 line:316，覆盖 statement 90%） |
| `M2-Y-197` | yang | `deep-extract-yang-b01.md` | line:334 | line:338 | +4 | C 跨段合并/摘要 | 补 anchor_span line:334-346（含锚点行 line:334 与命中行 line:338，覆盖 statement 96%） |
| `M2-Y-198` | yang | `deep-extract-yang-b01.md` | line:348 | line:350 | +2 | C 跨段合并/摘要 | 补 anchor_span line:348-352（含锚点行 line:348 与命中行 line:350，覆盖 statement 89%） |
| `M2-Y-199` | yang | `deep-extract-yang-b01.md` | line:354 | line:356 | +2 | C 跨段合并/摘要 | 补 anchor_span line:354-356（含锚点行 line:354 与命中行 line:356，覆盖 statement 30%，未达 85%，建议人工复核该段） |
| `M2-Y-203` | yang | `deep-extract-yang-b01.md` | line:378 | line:380 | +2 | B 合并型（锚点行+命中行） | 补 anchor_span line:378-380（锚点可保留 line:378） |
| `M2-Y-220` | yang | `deep-extract-yang-b02.md` | line:2856 | line:2858 | +2 | B 合并型（锚点行+命中行） | 补 anchor_span line:2856-2858（锚点可保留 line:2856） |
| `M2-Y-243` | yang | `deep-extract-yang-b02.md` | line:2778 | line:2780 | +2 | B 合并型（锚点行+命中行） | 补 anchor_span line:2778-2780（锚点可保留 line:2778） |
| `M2-Y-350` | yang | `deep-extract-yang-b05.md` | line:2708 | line:2710 | +2 | A 锚点错位 | raw_anchor 改为 line:2710 |
| `M2-Y-351` | yang | `deep-extract-yang-b05.md` | line:2710 | line:2712 | +2 | A 锚点错位 | raw_anchor 改为 line:2712 |

> 说明：A 类为 statement 与命中行高度重合（覆盖率 ≥80%）而锚点行几乎不覆盖（<50%），属锚点写错行，建议直接把 `raw_anchor` 改到命中行；B 类为 statement 同时覆盖锚点行与命中行（并集覆盖率 ≥80%），属合并型条目只锚了首行，建议补 `anchor_span` 保留锚点；C 类为跨段合并或摘要改写，脚本从命中行出发按「内容行」贪心扩边（不跨小节标题），给出覆盖率最高且同时含锚点行与命中行的连续区间；标注"未达 85%"者为摘要型改写，区间只能覆盖部分原文，仍需人工复核。

## 3. 系统性发现

### 3.1 杨派 b01「引子行锚点」模式（+2 / +4 偏移）

18 条容差内偏移里，**14 条为 +2、3 条为 +4、1 条为 -1**。按 raw_file 分组：

| raw_file | 记录数 | 偏移分布 | 涉及 id |
|---|---|---|---|
| `MinerU_markdown_04清娟盲派八字命理讲座（内部资料篇）_2056033547019026432.md` | 12 | +2×9、+4×3 | M2-Y-184、M2-Y-185、M2-Y-188、M2-Y-189、M2-Y-190、M2-Y-193、M2-Y-194、M2-Y-195、M2-Y-197、M2-Y-198、M2-Y-199、M2-Y-203 |
| `MinerU_markdown_01.杨清娟命理基础电子书261页_2056033743757049856.md` | 2 | +2×2 | M2-Y-220、M2-Y-243 |
| `MinerU_markdown_01杨清娟-盲派八字命理《教学体系命例集细解》-无水印245页(高清版)_2056033706247389184.md` | 2 | +2×2 | M2-Y-350、M2-Y-351 |
| `MinerU_markdown_婚姻专辑_2056044010230448128.md` | 1 | +2×1 | M1-D-307 |
| `MinerU_markdown_墓__穿_2056043829099421696.md` | 1 | -1×1 | M1-D-370 |

**证据（12/41 条 = 29%）**：该文件所在原稿 `sources/yang/MinerU_markdown_04清娟盲派八字命理讲座（内部资料篇）…md` 的正文是「一行正文 + 一行空行」的排版。这些条目的 `raw_anchor` 指向段首引子行（如 `# 十神暗引：`、`# ④官杀暗引财星` 或上一段结论句），verify_fragment 实际取自紧随其后的正文行，中间恰好隔 1 个空行 → 行号 +2；若锚点与片段之间还隔了 1 行正文，则为 +4。

典型样例（锚点行 → 实际命中行）：

| id | 锚点行原文（截断） | 实际命中行原文（截断） |
|---|---|---|
| `M2-Y-184` | ⑥穿是抢夺，穿了，得到的东西不完整。 | 体穿印枭财时，易带孝 |
| `M2-Y-185` | 看力量，水旺能穿坏未中的丁火及己土（水多土散火熄），未土旺能穿坏子水，土克水。 | 子遇辰拱水力量大，遇申力量更大，女的多往子宫肌留，妇科方面断，男的多为前列腺，肾功能方面。 |
| `M2-Y-188` | 互穿看力量，卯辰相穿时，卯木力量大时克辰土，穿坏了水，辰力量大则腐朽了卯木，互穿都不完整，… | 卯被穿，烂根了，立不住了，如果卯为官时，官立不住了，不能再当官。女命（官人）则要离婚了。 |
| `M2-Y-189` | # 4，酉戌穿：为实实在在的东西，为实际存在的事。 | 酉戌穿，也是爆炸的象。比如鞭炮爆炸，炸药爆炸。 |
| `M2-Y-190` | # 5，申亥穿：生穿 | 疾病：一是腰背筋骨方面：筋骨，骨胳，颈椎，腰肩盘突出， |
| `M2-Y-193` | # 十神暗引： | 食伤暗引比劫 （枭 印） |

> 判断：这是**提取时把"段标题/引子"当作锚点、片段却取自正文**造成的系统性偏移，不是原稿行号变化。由于 ±5 容差兜住了全部 18 条，校验器全 PASS，但人工按锚点回读会先读到引子行。建议按 §2.2 的建议行号改锚，或对合并型条目补 `anchor_span`。

### 3.2 标题行锚点（15 条）

417 条中有 **15** 条的锚点行是 Markdown 标题（`#`）。其中 7 条片段就在标题内（精确命中，无需改动），8 条片段在标题之后的正文行（即 §3.1 的偏移）。

| id | 学派 | 提取文件 | 锚点行 | 片段在标题内 | 实际命中行 | 标题原文 |
|---|---|---|---|---|---|---|
| `G-MG-024` | gao | `deep-extract-gao-fix-b01.md` | line:1376 | 是 | line:1376 | # 6、日时不可三煞年命： |
| `G-BD-024` | gao | `deep-extract-gao-fix-b01.md` | line:2706 | 是 | line:2706 | # 一）、以日干通地支起太岁看一生祸福 |
| `G-BD-019` | gao | `deep-extract-gao-fix-b01.md` | line:2737 | 是 | line:2737 | # 三）、以流年地支起太岁看一年四季应事 |
| `G-XF-021` | gao | `deep-extract-gao-fix-b01.md` | line:1245 | 是 | line:1245 | # 辰未自带印 华盖星坐命 |
| `G-XF-006` | gao | `deep-extract-gao-fix-b01.md` | line:233 | 是 | line:233 | # 3、发表归根定体用技法 |
| `G-CH-035` | gao | `deep-extract-gao-fix-b01.md` | line:1482 | 是 | line:1482 | # 4、八字中，天干同时透官星和伤官的人； |
| `G-CH-033` | gao | `deep-extract-gao-fix-b01.md` | line:1110 | 是 | line:1110 | # 二、以双方日柱天干五行相合看姻缘。 |
| `M2-Y-189` | yang | `deep-extract-yang-b01.md` | line:254 | 否 | line:258 | # 4，酉戌穿：为实实在在的东西，为实际存在的事。 |
| `M2-Y-190` | yang | `deep-extract-yang-b01.md` | line:262 | 否 | line:264 | # 5，申亥穿：生穿 |
| `M2-Y-193` | yang | `deep-extract-yang-b01.md` | line:290 | 否 | line:292 | # 十神暗引： |
| `M2-Y-194` | yang | `deep-extract-yang-b01.md` | line:308 | 否 | line:310 | # 十食暗引的必要条件： |
| `M2-Y-195` | yang | `deep-extract-yang-b01.md` | line:312 | 否 | line:316 | # ①食伤暗引比劫 |
| `M2-Y-197` | yang | `deep-extract-yang-b01.md` | line:334 | 否 | line:338 | # ③比劫暗引印枭 |
| `M2-Y-198` | yang | `deep-extract-yang-b01.md` | line:348 | 否 | line:350 | # ④官杀暗引财星 |
| `M2-Y-199` | yang | `deep-extract-yang-b01.md` | line:354 | 否 | line:356 | # ⑤财星暗引食伤 |

### 3.3 长行锚点与共用锚点

**长行锚点**：16 条记录的锚点行长度 > 200 字符（最长 323 字符），而 verify_fragment 仅 8–47 字。片段确实在长行内（全部精确命中），但锚点粒度粗，人工回读需在整段中二次定位。

| id | 学派 | 锚点行 | 锚点行长度 | 片段长度 |
|---|---|---|---|---|
| `M1-D-331` | duan | line:2 | 227 | 16 |
| `M1-D-332` | duan | line:2 | 227 | 17 |
| `M1-D-333` | duan | line:2 | 227 | 21 |
| `M1-D-404` | duan | line:175 | 263 | 19 |
| `M1-D-405` | duan | line:175 | 263 | 26 |
| `M1-D-407` | duan | line:286 | 271 | 12 |
| `M1-D-419` | duan | line:1637 | 323 | 20 |
| `G-DY-003` | gao | line:67 | 318 | 10 |
| `G-LF-023` | gao | line:425 | 213 | 47 |
| `G-BD-002` | gao | line:296 | 224 | 8 |
| `G-SS-016` | gao | line:566 | 277 | 9 |
| `M2-Y-211` | yang | line:2817 | 318 | 11 |
| `M2-Y-228` | yang | line:2894 | 221 | 17 |
| `M2-Y-244` | yang | line:2946 | 217 | 14 |
| `M2-Y-274` | yang | line:2344 | 201 | 8 |
| `M2-Y-281` | yang | line:2382 | 240 | 23 |

**共用锚点**：7 组记录共用同一 (raw_file, raw_anchor)，最多 3 条规则锚同一行。这些行本身是长段落或总述，多条规则各自摘取其中一句，verify_fragment 均能命中，但 `line:N` 无法区分具体摘的是哪一句，建议后续补 `anchor_span` 或行内偏移。

| raw_file | 锚点 | 共用条数 | ids |
|---|---|---|---|
| `MinerU_markdown_体用_2056043694349017088.md` | line:2 | 3 | M1-D-331、M1-D-332、M1-D-333 |
| `MinerU_markdown_宾主作用_2056044174571667456.md` | line:152 | 2 | M1-D-356、M1-D-357 |
| `MinerU_markdown_宾主作用_2056044174571667456.md` | line:155 | 2 | M1-D-360、M1-D-361 |
| `MinerU_markdown_21.大连段建业-面授讲义（合集）134页_2056045222002622464.md` | line:175 | 2 | M1-D-404、M1-D-405 |
| `MinerU_markdown_28.命理指要_2056045424658808832.md` | line:2216 | 2 | M1-D-420、M1-D-421 |
| `MinerU_markdown_28.命理指要_2056045424658808832.md` | line:3119 | 2 | M1-D-424、M1-D-425 |
| `MinerU_markdown_01杨清娟-盲派八字命理《教学体系命例集细解》-无水印245页(高清版)_2056033706247389184.md` | line:1018 | 2 | M2-Y-377、M2-Y-385 |

### 3.4 任派 6 条的 provenance：raw_file 指向理论重写稿

任派 6 条的 `raw_file` 均为 `theory/raw/ren/r29-r30-theory.md`（任派**理论整理稿**），而不是 `sources/ren/` 下的任付红原稿。逐条在 `sources/ren/` 全量搜索 verify_fragment 的结果：

| id | raw_anchor | verify_fragment | 在 sources/ren 原稿命中 |
|---|---|---|---|
| `M3-R-181` | line:12 | 寅、申、巳、亥见各自墓库即入墓 | **未命中** |
| `M3-R-182` | line:28 | 一般不作入墓论，当拱局看 | **未命中** |
| `M3-R-183` | line:42 | 见各自墓库则入墓（不再论拱局） | **未命中** |
| `M3-R-184` | line:56 | 天干坐自己的墓库不以入墓论 | **未命中** |
| `M3-R-185` | line:68 | 辰为土墓也为水墓 | `MinerU_markdown_16、任付红-民间实用八字-地支四墓库的使用方法_2056026785004060672.md` line:111 |
| `M3-R-186` | line:81 | 不仅要看墓库五行含义，更要看所墓之十神含义 | **未命中** |

**证据**：6 条中仅 **1 条**（M3-R-185「辰为土墓也为水墓」）能在任派原稿 `sources/ren/MinerU_markdown_16、任付红-民间实用八字-地支四墓库的使用方法…md` 找到对应原文，其余 5 条是理论整理稿对原稿的**二次归纳表述**（原稿为口语/表格，整理稿改写为「**规则**：…」句式）。

> 判断：锚点校验本身通过（`r29-r30-theory.md` 存在、行号有效、片段命中），但 provenance 层级是「理论整理稿」而非「一手原稿」。按仓库「引用结论保留 source_ref」的纪律，建议给这 6 条标注 `anchor_type=theory-rewrite`，或对可回溯的 M3-R-185 补一手锚点`sources/ren/MinerU_markdown_16、任付红-民间实用八字-地支四墓库的使用方法_2056026785004060672.md` line:111。

### 3.5 派生索引与真源锚点漂移（_light_index.json）

`theory/_light_index.json`（3846 条）中，本批 417 条全部存在；其中 **6** 条的 `raw_file`/`raw_anchor` 与提取稿不一致：

| id | 学派 | 提取稿锚点 | 派生索引锚点 | 说明 |
|---|---|---|---|---|
| `M3-R-181` | ren | line:12 | line:10 | 提取稿锚在「**规则**」行，派生索引锚在上一级标题行，相差 2 行 |
| `M3-R-182` | ren | line:28 | line:26 | 提取稿锚在「**规则**」行，派生索引锚在上一级标题行，相差 2 行 |
| `M3-R-183` | ren | line:42 | line:40 | 提取稿锚在「**规则**」行，派生索引锚在上一级标题行，相差 2 行 |
| `M3-R-184` | ren | line:56 | line:54 | 提取稿锚在「**规则**」行，派生索引锚在上一级标题行，相差 2 行 |
| `M3-R-185` | ren | line:68 | line:66 | 提取稿锚在「**规则**」行，派生索引锚在上一级标题行，相差 2 行 |
| `M3-R-186` | ren | line:81 | line:79 | 提取稿锚在「**规则**」行，派生索引锚在上一级标题行，相差 2 行 |

> 原因：`tools/query_theory.raw_rule_bodies()` 对任派/段派按「标题行」提取正文并生成`line:{标题行}` 锚点，覆盖了 index.yaml/提取稿的行锚。差值固定为 2 行（标题行 → 空行 → `**规则**` 行），仍在 ±5 容差内，故不影响校验；但 `source_ref` 指向标题行而非片段行，回读时需再下移 2 行。若后续收紧容差或做逐字回读，这 6 条会先暴露。

### 3.6 杨派提取稿双副本（237×2 条）

`theory/yang/deep-extract-yang-b0*.md`（6 个文件、237 条）与 `theory/raw/yang/promoted/` 下的 237 条**完全重复**：raw_file/raw_anchor/verify_fragment/statement/title 全部一致的 **237/237** 条；仅旧副本 0 条、仅新副本 0 条。

> 影响：① 任何"全量校验/计数"若同时扫描两处会把 237 条重复计成 474 条 —— 仓库既有文档中的"586 条"即可由 `237（theory/yang）+ 237（theory/raw/yang/promoted）+ 112（duan b01–b03）` 精确复现，属双份计数而非真实条目数；② 双副本需同步维护（历史记录显示 M2-Y-223 的 verify_fragment 空格问题就曾需要在两处同步修复）。建议把 `theory/yang/` 下副本收敛为单一真源（或明确标注为镜像并在校验脚本中排除）。

### 3.7 计数口径：任务书 430 vs 实测 417

| 口径 | 数值 | 构成/说明 |
|---|---|---|
| 任务书 | 430 | 无法由现有 12 个提取文件复现；与实测差 **13 条** |
| 实测（本报告） | **417** | yang 237 + duan 138 + gao 36 + ren 6 |
| 旧文档（语义复核） | 586 | 237（theory/yang 旧副本）+ 237（theory/raw/yang/promoted）+ 112（duan b01–b03），双份计数 |

12 个文件 front matter 的 `record_count` 与实际 YAML 条目数 **12/12 全部一致**，且 yang id 164–400、duan id 291–428 均连续无缺号，说明 417 是当前真源稿的准确条目数。**结论：以 417 为准，建议把任务书/后续文档中的 430 更正为 417。**

### 3.8 其他一致性与健壮性检查

| 检查项 | 结果 |
|---|---|
| raw_file 存在性 | 417/417 存在（24 个不同原稿文件，跨 4 派） |
| 行号越界 | 0 条越界；锚点行范围 line:2–line:3119，窗口均未被文件头/尾截断（仅 2 条贴近 EOF，窗口仍含锚点行） |
| source_ref 与 raw_file/raw_anchor 一致 | 417/417 一致（0 条错配） |
| 缺字段 | 0 处缺失 |
| 重复 id | 0 个 |
| content_status | {'full': 416, 'title_only': 1} |
| 片段含空白字符 | 15 条（如 `M2-Y-223` 的 `A 的力量`、`G-CS-022` 的 `月柱管 19-36 岁运程`），去空白后全部命中 |
| 不做空白归一化时的窗口命中 | 417/417（即本批 417 条对空白归一化不敏感，归一化只增加稳健性） |

> 说明：`M2-Y-199`（content_status=`title_only`）锚点 `line:354` 为标题 `# ⑤财星暗引食伤`，verify_fragment「课堂上没有细讲」在其下一行 `line:356`，属 §3.1 的 +2 偏移；该条 statement 本身已声明「原稿仅列名未给条件与结论，暂不可用」，内容状态与原文一致，无编造风险。

## 4. 修复建议（按优先级）

| 优先级 | 事项 | 范围 | 具体动作 |
|---|---|---|---|
| P1 | 容差内潜在漂移 | 18 条 | 按 §2.2 建议：A 类改 `raw_anchor` 到实际命中行；B/C 类补 `anchor_span: line:N-M`（并让 build_indexes/校验器支持区间锚） |
| P2 | 任派 provenance | 6 条 | 标注 `anchor_type=theory-rewrite`；M3-R-185 可补 `sources/ren` 一手锚点 line:111 |
| P3 | 杨派双副本 | 237×2 | 收敛为单真源，或在校验/计数脚本中显式排除 `theory/yang/` 镜像 |
| P4 | 长行/共用锚点 | 16 条长行、7 组共用 | 补 `anchor_span` 或行内偏移，提升逐字回读精度 |
| P5 | 计数口径 | 文档 | 430 → 417；避免"586"式双份计数再被引用 |

> 注：P1/P2/P4 均属"精度提升"，不涉及断语内容修改；本审计按纪律**未改动任何 theory/ 文件**。

## 5. 复现与产物

```bash
# 环境：Python 3.14.5 + PyYAML 6.0.3；系统 locale 为 GBK，必须设 PYTHONIOENCODING
cd /f/综合盲派/mangpai-fusion
PYTHONIOENCODING=utf-8 python .workbuddy-ai/b1_anchor_audit.py

# 交叉验证：仓库自带校验器（只读，不重建索引）
PYTHONIOENCODING=utf-8 python -m tools.extraction_validator check \
  theory/raw/yang/promoted/deep-extract-yang-b0*.md \
  theory/raw/duan/promoted/deep-extract-duan-b0*.md \
  theory/raw/gao/promoted/deep-extract-gao-fix-b01.md \
  theory/raw/ren/promoted/deep-extract-ren-fix-b01.md
```

| 产物 | 说明 |
|---|---|
| `META/anchor-audit-2026-10-18.md` | 本报告（由脚本实测生成） |
| `.workbuddy-ai/b1_anchor_audit.py` | 审计脚本（只读语料，唯一写本报告与结果 JSON） |
| `.workbuddy-ai/b1_anchor_audit_result.json` | 417 条逐条结果（status/命中行/偏移/建议） |

**交叉验证结果**：`tools/extraction_validator check` 对 12 个文件 417 条输出 `PASS 417 / SUSPECT 0 / FORGE 0`，与本报告 §1.1 的 417 命中一致。


---
batch: ren-fix-b01
school: ren
scope: 任派 6 条 pending_normalization 补全（M3-R-181..186 · 地支四墓库体系）
date: 2026-10-17
record_count: 6
note: |
  原 index.yaml 中 M3-R-181..186 为 "(待补)" pending_normalization，
  根因是 m3-rules-registry.md §19.17 的两列表格未被旧解析器识别（需三列）。
  本批按 r29-r30-theory.md §一 补全正文，raw_anchor 为真实行号，
  verify_fragment 为原文精确子串。同名 id 在 build_indexes 合并时覆盖占位条目。
---

# 任派修正 · b01（M3-R-181..186 · 地支四墓库体系补全）

```yaml
- id: M3-R-181
  school: ren
  classic_name: 任付红盲派
  title: "寅申巳亥入墓库法"
  domain: lifa
  topic: lifa
  tags: [墓库, 寅申巳亥, 入墓, 库不开]
  statement: "寅、申、巳、亥见各自墓库即入墓（寅见未/申见丑/巳见戌/亥见辰）；墓库表收藏、得到、占有、控制，有时表死亡；入墓后若库不开（无刑冲破）则所入之物被彻底关住，事物有伤不可得"
  conclusion: "寅、申、巳、亥见各自墓库即入墓（寅见未/申见丑/巳见戌/亥见辰）；墓库表收藏、得到、占有、控制，有时表死亡；入墓后若库不开（无刑冲破）则所入之物被彻底关住，事物有伤不可得"
  content_status: full
  raw_file: "theory/raw/ren/r29-r30-theory.md"
  raw_anchor: "line:12"
  source_ref: {path: "theory/raw/ren/r29-r30-theory.md", anchor: "line:12"}
  verify_fragment: "寅、申、巳、亥见各自墓库即入墓"

- id: M3-R-182
  school: ren
  classic_name: 任付红盲派
  title: "子午卯酉见墓一般不入墓法"
  domain: lifa
  topic: lifa
  tags: [墓库, 子午卯酉, 拱局, 例外]
  statement: "子、午、卯、酉见各自墓库一般不作入墓论、当拱局看（子辰拱水/卯未拱木/午戌拱火/酉丑拱金）；例外：极弱被制受伤时方入墓（如子被未穿卯破、见辰当入墓）"
  conclusion: "子、午、卯、酉见各自墓库一般不作入墓论、当拱局看（子辰拱水/卯未拱木/午戌拱火/酉丑拱金）；例外：极弱被制受伤时方入墓（如子被未穿卯破、见辰当入墓）"
  content_status: full
  raw_file: "theory/raw/ren/r29-r30-theory.md"
  raw_anchor: "line:28"
  source_ref: {path: "theory/raw/ren/r29-r30-theory.md", anchor: "line:28"}
  verify_fragment: "一般不作入墓论，当拱局看"

- id: M3-R-183
  school: ren
  classic_name: 任付红盲派
  title: "多而入墓库法"
  domain: lifa
  topic: lifa
  tags: [墓库, 多而入墓, 不论拱, 库开库不开]
  statement: "天干或地支合在一起有两个或两个以上者，见各自墓库则入墓、不再论拱局（辛酉见丑/庚辛见丑/两卯见未/水多见辰）；多入墓后库开则有用、不开则无用"
  conclusion: "天干或地支合在一起有两个或两个以上者，见各自墓库则入墓、不再论拱局（辛酉见丑/庚辛见丑/两卯见未/水多见辰）；多入墓后库开则有用、不开则无用"
  content_status: full
  raw_file: "theory/raw/ren/r29-r30-theory.md"
  raw_anchor: "line:42"
  source_ref: {path: "theory/raw/ren/r29-r30-theory.md", anchor: "line:42"}
  verify_fragment: "见各自墓库则入墓（不再论拱局）"

- id: M3-R-184
  school: ren
  classic_name: 任付红盲派
  title: "天干坐墓不入墓法"
  domain: lifa
  topic: lifa
  tags: [墓库, 天干坐墓, 丙戌, 乙未]
  statement: "天干坐自己的墓库不以入墓论（丙戌一柱丙不入戌墓、乙未一柱乙不入未墓），此为普遍原则，适用于所有天干坐库"
  conclusion: "天干坐自己的墓库不以入墓论（丙戌一柱丙不入戌墓、乙未一柱乙不入未墓），此为普遍原则，适用于所有天干坐库"
  content_status: full
  raw_file: "theory/raw/ren/r29-r30-theory.md"
  raw_anchor: "line:56"
  source_ref: {path: "theory/raw/ren/r29-r30-theory.md", anchor: "line:56"}
  verify_fragment: "天干坐自己的墓库不以入墓论"

- id: M3-R-185
  school: ren
  classic_name: 任付红盲派
  title: "土之墓库特殊规则"
  domain: lifa
  topic: lifa
  tags: [墓库, 辰, 丑未冲, 土墓, 财入库]
  statement: "辰为土墓也为水墓：丑入辰墓、未也入辰墓；但当丑未辰同时出现时因丑未相冲，丑未都不入辰墓；推论：未入辰库则财入别人处，乙合庚控辰则自己可得库中之物"
  conclusion: "辰为土墓也为水墓：丑入辰墓、未也入辰墓；但当丑未辰同时出现时因丑未相冲，丑未都不入辰墓；推论：未入辰库则财入别人处，乙合庚控辰则自己可得库中之物"
  content_status: full
  raw_file: "theory/raw/ren/r29-r30-theory.md"
  raw_anchor: "line:68"
  source_ref: {path: "theory/raw/ren/r29-r30-theory.md", anchor: "line:68"}
  verify_fragment: "辰为土墓也为水墓"

- id: M3-R-186
  school: ren
  classic_name: 任付红盲派
  title: "墓库看十神含义法"
  domain: lifa
  topic: lifa
  tags: [墓库, 十神, 官杀库, 财库, 食伤库, 比劫库]
  statement: "看墓库不仅要看五行含义，更要看所墓十神含义：比劫羊刃库=军队/坏人集团；官杀入库+自己控制=管理官杀之人（贵命）；财入库+自己合控=可得财；食伤入库=才华自由被收"
  conclusion: "看墓库不仅要看五行含义，更要看所墓十神含义：比劫羊刃库=军队/坏人集团；官杀入库+自己控制=管理官杀之人（贵命）；财入库+自己合控=可得财；食伤入库=才华自由被收"
  content_status: full
  raw_file: "theory/raw/ren/r29-r30-theory.md"
  raw_anchor: "line:81"
  source_ref: {path: "theory/raw/ren/r29-r30-theory.md", anchor: "line:81"}
  verify_fragment: "不仅要看墓库五行含义，更要看所墓之十神含义"
```

## 说明

- 6 条占位条目的根因：`m3-rules-registry.md §19.17` 使用两列表格（`| rule_id | 标题 |`），旧解析器需三列，故落入兜底 "(待补)"。
- 本批正文取自 `theory/raw/ren/r29-r30-theory.md §一`（任付红《地支四墓库的使用方法》），非新造内容。
- build_indexes 深水区读取器按 id 覆盖，同名条目以本批为准；占位条目随之消失。

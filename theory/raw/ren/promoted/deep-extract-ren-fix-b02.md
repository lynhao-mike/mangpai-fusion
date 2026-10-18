---
batch: ren-fix-b02
school: ren
scope: |
  盲测归因（ATTR-1）任务 2：M3-R-181 锚点精度修正。statement 一字未动（语义复核判
  「忠实」）；仅追加 anchor_span（line:A-B），覆盖 statement 实际合并的原稿区间。
date: 2026-10-18
record_count: 1
source_batches:
- deep-extract-ren-fix-b01.md（M3-R-181）
note: |
  M3-R-181：statement 合并 r29-r30-theory.md 第 12-18 行（12 规则句 + 13-16 对应关系
    四行 + 18 墓库含义句）。原 raw_anchor line:12 只锚规则首句。按 validator 的 span
    约束（A 必须等于 raw_anchor 的 N=12，保持不动）补 anchor_span line:12-18。
  provenance 备注（anchor-audit §3.4）：本批 6 条 raw_file 均指任派理论整理稿
    r29-r30-theory.md 而非 sources/ren 一手原稿，属 theory-rewrite 层级；本条不在
    本轮改动范围，仅在此声明。
  同名 id 在 build_indexes 合并时覆盖 fix-b01 中的旧条目（与 fix-b01 同机制）。
---

# 任派修正 · fix-b02（M3-R-181 · 锚点精度）

> 真源稿。自检：`PYTHONIOENCODING=utf-8 python -m tools.extraction_validator check <本文件>` → PASS（FORGE=0，2026-10-18 实测）。

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
  anchor_span: "line:12-18"
  source_ref: {path: "theory/raw/ren/r29-r30-theory.md", anchor: "line:12"}
  verify_fragment: "寅、申、巳、亥见各自墓库即入墓"
```

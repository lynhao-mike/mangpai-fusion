---
batch: yang-fix-b02
school: yang
scope: |
  盲测归因（ATTR-1）任务 2：3 条存疑条目的锚点精度修正。statement/conclusion 一字未动
  （语义复核判「忠实」，问题在锚点不覆盖整条 statement）；仅追加 anchor_span（line:A-B），
  并让 tools/extraction_validator 已有 span 校验（A 必须等于 raw_anchor 的 N）通过。
date: 2026-10-18
record_count: 3
source_batches:
- deep-extract-yang-b02.md（M2-Y-211）
- deep-extract-yang-b03.md（M2-Y-252、M2-Y-286）
note: |
  M2-Y-211：锚点 line:2817 为 318 字长行（anchor-audit §3.3 长行锚点），逐字回读该条
    statement（应象六句 + 边界三句）全部在这同一行内，故 anchor_span 记 line:2817-2817，
    确认「单行覆盖」；今后如需行内二次定位，另立行内偏移方案（P4）。
  M2-Y-252：statement 合并原稿两段——line:2246「伤官见官一定要制官…是错误的」+
    line:2248「条件：伤官力量小于等于官…」。原 raw_anchor 2248 只锚条件段。按 fix 纪律
    前移 raw_anchor 至 statement 首行 2246，anchor_span line:2246-2248 覆盖两句；
    旧值留 legacy_anchor: line:2248，source_ref 同步。
  M2-Y-286：锚点 line:2400 为 191 字单段，statement 全部取自该行，anchor_span 记
    line:2400-2400，确认单行覆盖。
  同名 id 在 build_indexes 合并时覆盖 b02/b03 中的旧条目（与 fix-b01 同机制）。
---

# 杨派修正 · fix-b02（M2-Y-211/252/286 · 锚点精度）

> 真源稿。自检：`PYTHONIOENCODING=utf-8 python -m tools.extraction_validator check <本文件>` → PASS（FORGE=0，2026-10-18 实测）。

```yaml
- id: M2-Y-211
  school: yang
  classic_name: 杨清娟盲派
  title: 库不开而杀无制的经验应象（附边界）
  topic: jiankang
  domain: jiankang
  tags:
  - 墓库
  - 杀库
  - 经验
  - 边界
  - 自杀
  - 情绪
  statement: 库不开而库中五行为杀且杀制不住时的前辈经验应象：水库不开想哭、杀库不开想投河、土库想喝药跳楼、金库想割腕、木库想上吊、火库触电。原稿明确此为前辈个人经验，只应于杀制不住之局，不可见库不开即断生死
  conclusion: 库不开而库中五行为杀且杀制不住时的前辈经验应象：水库不开想哭、杀库不开想投河、土库想喝药跳楼、金库想割腕、木库想上吊、火库触电。原稿明确此为前辈个人经验，只应于杀制不住之局，不可见库不开即断生死
  content_status: full
  raw_file: sources/yang/MinerU_markdown_01.杨清娟命理基础电子书261页_2056033743757049856.md
  raw_anchor: line:2817
  anchor_span: line:2817-2817
  source_ref:
    path: sources/yang/MinerU_markdown_01.杨清娟命理基础电子书261页_2056033743757049856.md
    anchor: line:2817
  verify_fragment: 以上皆为前辈们个人经验
- id: M2-Y-252
  school: yang
  classic_name: 杨清娟盲派
  title: 伤官见官为祸百端的条件
  topic: geju
  domain: geju
  tags:
  - 伤官见官
  - 官灾
  - 条件
  - 医院
  - 法院
  statement: 伤官见官一定要制官是错误的（官是衣食父母、应感恩）；伤官见官为祸百端、不进法院进医院的条件是：伤官力量小于等于官的力量且伤官是日主自己的，大运流年再给官加力就应灾——或官灾或身体病灾
  conclusion: 伤官见官一定要制官是错误的（官是衣食父母、应感恩）；伤官见官为祸百端、不进法院进医院的条件是：伤官力量小于等于官的力量且伤官是日主自己的，大运流年再给官加力就应灾——或官灾或身体病灾
  content_status: full
  raw_file: sources/yang/MinerU_markdown_01.杨清娟命理基础电子书261页_2056033743757049856.md
  raw_anchor: line:2246
  anchor_span: line:2246-2248
  legacy_anchor: line:2248
  source_ref:
    path: sources/yang/MinerU_markdown_01.杨清娟命理基础电子书261页_2056033743757049856.md
    anchor: line:2246
  verify_fragment: 条件是伤官的力量小于等于官的力量
- id: M2-Y-286
  school: yang
  classic_name: 杨清娟盲派
  title: 制枭发财还是当官的分野
  topic: caiyun
  domain: caiyun
  tags:
  - 枭神
  - 制枭
  - 发财
  - 当官
  - 食神
  statement: 原命有枭神夺食的，制了枭就发财还要看组合：食神是日主自己的，制枭就发财、制枭就当官；原命食神不是日主的，制了食神就发财不能当官；枭神旺则命主一生肯定有灾，看食神代表什么定灾型：代表管理者有被裁员撤职时、代表权利有牢狱灾、代表财富主破财或高处掉落摔伤；枭夺食求谋不顺利、处处阻逆
  conclusion: 原命有枭神夺食的，制了枭就发财还要看组合：食神是日主自己的，制枭就发财、制枭就当官；原命食神不是日主的，制了食神就发财不能当官；枭神旺则命主一生肯定有灾，看食神代表什么定灾型：代表管理者有被裁员撤职时、代表权利有牢狱灾、代表财富主破财或高处掉落摔伤；枭夺食求谋不顺利、处处阻逆
  content_status: full
  raw_file: sources/yang/MinerU_markdown_01.杨清娟命理基础电子书261页_2056033743757049856.md
  raw_anchor: line:2400
  anchor_span: line:2400-2400
  source_ref:
    path: sources/yang/MinerU_markdown_01.杨清娟命理基础电子书261页_2056033743757049856.md
    anchor: line:2400
  verify_fragment: 原命有枭神夺食的，制了枭就发财，还要看组合
```

# T-191 · BRIEF · runner r1（未污染盲跑）

- Runner：r1（独立子代理；未参与策展、未读 A/B 答案、未读 dev/holdout/fresh/golden）
- 日期：2026-10-29
- 产物：`META/p1-system-run-r1.json`
- 状态：**已交付，未评分**（不宣称通过、不自评）

## 1. 改动文件

| 文件 | 说明 |
|---|---|
| `META/p1-system-run-r1.json` | 新建；60 条 runner 输出 |
| `tasks/T-191/BRIEF-r1.md` | 本文件 |
| `tasks/T-191/STATUS-r1.md` | runner 状态与执行日志 |

未改盲卷、答案、engine、阈值、测试；未做任何 git 写操作。

## 2. 原始输出

- **60/60 条**：fixed 10 / dynamic 40 / ambiguous 10；`case_id` 无重复。
- fixed 10：全部 `actor→target`。
- dynamic 40：`actor→target` 37 条 + `mutual` 3 条；**decidable 上 `needs_judgment` = 0**。
- ambiguous 10：全部 `direction="needs_judgment"`；每条 `conflict_quotes[2]`（正反逐字）+ `source_refs[2]` + `source_ref`。
- `edge_id`：非 fixed 50 条全部非空，且逐条回查 `engine.cli` 对应快照 `relations.edges`（id 存在、members 与盲卷地址对一致）。fixed 10 条为 `null`，原因见 §3。
- `verbatim_quote`：60/60 非空；共 40 个不同引文（同一规则跨案复用，非复制错误）。每条引文已由本地校验脚本逐字验证为 `source_ref` 所指行的子串（含 OCR 空格）；该脚本不是评分器。
- 3 条 `mutual`：A60-041（未戌刑，"两个都坏了"）、A60-045（寅巳刑，原文"寅刑巳/巳刑寅"双向且本盘无单向句）、A60-047（子卯刑，"卯与子两伤"）。
- 是否读到答案：**否**。未打开 `META/p1-anchor-60-*answers*`、`META/p1-anchor-60-B-v1.md`、`META/p1-system-run*`、任何 fresh/holdout/golden answers、dev-20 答案。
- 是否跑评分器：**否**。是否 git 写：**否**。

## 3. 未完成与风险

1. **fixed 10 的 `edge_id=null`**：`engine.cli` 的 `relations.edges` 只发冲/合/穿/刑/破/三合/暗合等边，**不发射分支的克/生/化/墓边**；`duan_zuogong.candidates` 里对应的 `zhi_ke` 等候选无 `edge_id`。按 `party-direction-v1` 的 "推得关系填 null 并写 derived" 处理。若 T-189b 对 fixed 也强制非空 `edge_id`，这 10 条会被计为缺边；我没有编造边号。
2. **a/b 语义**：单向条目 `a=actor`、`b=target`；`mutual` / `needs_judgment` 条目 `a/b` 保持盲卷顺序。另存 `blind_a`、`blind_b`、`blind_addr_a`、`blind_addr_b` 供回查。若上游约定 `a/b` 必须等于盲卷 `char_a/char_b`，需按 `blind_a/blind_b` 重排；r1 的 9 条发生 swap：A60-014、015、018、021、026、028、034、036、038（049 已按"巳刑寅"改回盲序）。
3. **方向不确定项（无答案可对）**：
   - A60-015（卯酉冲）：通用句"卯酉冲，卯被克坏"取酉→卯；同盘出处讲的是大运卯冲去酉，原局方向仍可能有争议。
   - A60-020（辰戌冲）：按同盘原文"戌土被辰冲"取辰→戌，与 T-190 notes 的 A 说一致（B 说相反）。
   - A60-041/045：`mutual` 判断；若答案按单向计，这两条会错。
   - A60-043/044/050（丑戌刑）：按盘势取 043/044 戌→丑、050 丑→戌；050 依 T-190 notes 的 B 修正，043/044 依"戌旺时灭丑中水"。
   - A60-016（丑未冲）：按"金水湿土成势，丑可坏未"取丑→未（偏离 B2 主位规则）。
4. **引文复用**：同一规则句用于多条同机制 case。若评分器要求"每案独立 locator"而非"逐字可检出"，会显示大量重复；引文本身逐字可检出。
5. 未做任何自评/通过率估计；一切以中枢 T-189b 现场评分为准。

## 4. 下游须知

- 文件形状：`{"schema_version","task","runner","blind","generated_at","case_count","cases":[...]}`；请按 `cases` 读取。
- 每条必填字段齐全：`case_id/a/b/kind/direction/edge_id/basis/state/source_ref/verbatim_quote`；ambiguous 另有 `source_refs[2]`、`conflict_quotes[2]`。
- `edge_id=null` 仅出现在 fixed 10 条。
- `basis`：fixed 克/生用 `fixed_wuxing`；化/墓及全部 dynamic/ambiguous 用 `source_text`。
- `state`：fixed/dynamic 用 `成`/`败`；ambiguous 用 `needs_judgment`。未把 `needs_judgment` 用在 decidable 方向。
- 未污染声明：本 runner 只读了任务卡允许的盲卷、A+ 规格/notes、`engine.cli` 输出、`query_theory` 与 `sources/duan/` 原文；未读任何答案文件。

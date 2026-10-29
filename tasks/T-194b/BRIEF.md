# T-194b BRIEF · annotator B（fixed-20 独立复核）

- 日期：2026-10-29
- 角色：annotator B；只读盲卷 + `sources/duan/` + `engine.cli`
- 状态：**交付完成**（20/20；克/生/化/墓各 5）
- 明细与逐条 quote：`META/p1-fixed-20-B-v1.md`；答案：`META/p1-fixed-20-answers-B-v1.json`

## 1. 改动文件

| 文件 | 动作 | 说明 |
|---|---|---|
| `META/p1-fixed-20-answers-B-v1.json` | 新增 | 20 条 B 答案；sha256 `cdc956271bb026d989b1ff99db05971a4b2045213eaa0215de7419f48cdc14a6` |
| `META/p1-fixed-20-B-v1.md` | 新增 | 清单/对齐/预检/hash/裁量/风险；sha256 `f8a22a98eda9a579c1b19b6b00570007f0668c55073a7730d0c560bf0fe120c5` |
| `tasks/T-194b/BRIEF.md` | 新增 | 本文件 |
| `tasks/T-194b/STATUS.md` | 更新 | 状态与 Execution Log |

未改 `sources/`、`engine/`、`tests/`、A 答案、规则表；未跑评分器；无 git 写。

## 2. 原始输出

自检（stdlib，独立读取写出的 JSON；未用评分器）：

```text
answers-B sha256: cdc956271bb026d989b1ff99db05971a4b2045213eaa0215de7419f48cdc14a6
blind sha256   : f7bdf96f7cb8cf58e619384948671d72ae0624205ac1ba9bf237aacb7ed743f5
mechanisms: {'克': 5, '生': 5, '化': 5, '墓': 5}
same_line: 6 doctrine_only: 14
PASS: 20/20 fixed-B, 5/5/5/5, quotes verbatim, source_ref in range
```

engine.cli 预检（`chart` 20 盘逐条）：

```text
SUMMARY 20/20 OK
chart_id 20/20 对齐；Y.b/M.b/D.b/H.b 端点字 20/20 对齐
boundary_warnings: F20-013 / F20-015 / F20-020 hour_stem_next_day（late_zi_split，晚子时口径）
F20-012: blind=未注明，CLI 以乾仅作解析（答案仍记未注明）
```

B 侧 actor→target 速查（供中枢 A/B 逐条对比）：

```text
001 戌→亥   002 午→酉   003 午→酉   004 戌→亥   005 卯→未
006 酉→亥   007 卯→巳   008 午→辰   009 申→子   010 卯→巳
011 亥→酉   012 子→申   013 未→亥   014 子→申   015 寅→子
016 未→寅   017 丑→酉   018 辰→亥   019 丑→申   020 丑→酉
```

## 3. 未完成与风险

1. **未做 A/B 对比**：本卡禁止读 A 答案，一致率/分歧清单由中枢执行；B 不预判、不静默改 A。
2. **未核 interval 与 anchor/holdout/fresh/golden 是否重叠**：查这些集合的 answers 会违反「不读任何 answers」约束。B 的 `source_ref` 一律单行 `Lx-Lx`，若中枢要跑 T-194 verify 的区间零重叠校验，请中枢侧执行。
3. **3 条化字裁量的规则张力**（已在 md §3 单列）：
   - F20-013 亥未拱局 → B 取 actor=未；§4.8「合化成局」本可判 `null`。
   - F20-014 申子辰三合 → B 取 actor=子；§6 三合表外本可判 `null`。
   - F20-015 子水被寅化 → B 取 actor=寅（被动句施动方），无合局歧义。
   - 另 F20-011「自化」句 B 取 actor=亥（化者=受生端），存在取酉（句法主语）的反向可能。
4. **F20-012 性别**：原书未标乾坤；B 记 `未注明`（不补造），若强判倾向乾但标为推断。与 A 的乾可能构成 1 条性别分歧。
5. **F20-017 / F20-020**：`丑墓酉`（P22:L2338、P22:L2116、P35:L1720）与 P21:L724「丑墓申不墓酉」存在原书内部张力；B 按盲卷机制「墓」取库=丑，只记张力，不改机制。
6. 14 条 `doctrine_only` 引的是同字对定向句（非本造段落）；若中枢要求 fixed 必须 `same_line`，应降级/换例，不应改 actor。

## 4. 下游须知

1. 读 B JSON：`cases[].relation` 为 `{a,b,mechanism,actor,target}`；`a/b` 按盲卷 `char_a/char_b` 原序（**不是** actor/target 顺序）；`source_ref` 为 `path:Lx-Lx`，`quote_line` 为单行行号，`quote` 必须逐字。
2. 比对口径：只比 `relation.actor`（及 `target`）；`a/b` 顺序一致是硬约束。B 的机制与盲卷 20/20 一致。
3. 3 条化 + 1 条性别单独看：F20-013/014/015、F20-012；其余 16 条按句法方向应为高置信一致区。
4. 不要用引擎 `relations`/`structure_check` 的 `sheng`/`ke` 方向反推 B 的 actor：B 按 actor-rules-v1 的句法/力向（尤其化=化者=受生端、墓=库）标注；引擎生边方向与化相反是已知口径。
5. A 卷不改；若 A/B 不一致，按双人复核规则先列分歧，由中枢裁决，B 不覆盖 A。

Blockers：无。

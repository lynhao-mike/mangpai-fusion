# 单盘分析：断语卡骨架 + 可选报告外壳 v1（`single-chart-report-skeleton-v1`）

> 配套规格：`docs/specs/single-chart-analysis-v1.md`（下称「规格」）。本文件只给**模板**，不含任何一张盘的结论。
> 使用约定：
> - 最小交付单元是**一张五元组断语卡**（§1–§3）；报告（§5）只是通过 Linter 的卡片集合 + 一层外壳。
> - 以 `>` 开头的「填写要求」行是模板指令，**交付前必须删除或替换成正文**。
> - 3 张盘的事实与缺口见 `META/single-chart-cases-v1.json`；任何字段值都必须能在 `engine.cli` 对应快照里找到。

---

## 1 · 卡模板（人读块，一屏一张）

```text
### [<case序号>-<两位>] <一句话标题：本卡说的是哪条作用>
- ① 原局象：<年|月|日|时(palace)> / <地址=字 十神，如 D.b=未 比肩> / <edge_id kind[members] group/completeness>
- ② 体用宾主：体=<地址…> 用=<地址…> 双属=<地址…>；第 <n> 层 主=<地址…> 宾=<地址…>；
               方向=<克|生|制|化|合|墓|冲|刑|穿|害|破|none>（<actor → target> | 方向未定）
- ③ 三态：<成局|破局|逢救应化解>；依据=<kind=edge:edge_id/assert | kind=structure_item:structure_id.item_id/status> evidence=<…>；救应=<未判>
- ④ 落事：<1–2 句，结构→人事形态>；引动=<kind> @ <against_addr> × <suiyun_addr>（<condition>；path=<…>）
- ⑤ 锚点：地址=<edge_ids + addrs>；原文=<entry_id> <path:line>
- statement：<本盘结论，必须含 ① 的至少 1 个地址>
- 边界：成立=<…>；不成立=<…>
- confidence：<高|中|低>；unknowns：<G2/G3/G4/G5/muku_open_close/no_spouse_star/boundary_zi_shi/near_jie/suiyun_ten_god>
- 快照：chart_id=<cf-…> dayun_index=<null|N> liunian_year=<null|YYYY>
```

> 填写要求：
> - 五元组**一行都不能少**；缺任一行 → 该卡被 Linter `L01` 拦截，不得进报告。
> - ① 的 `edge_id` 必须来自**本卡快照**；换快照要整卡重跑（规格 §1.3）。
> - ② 若 `actor` 为空，必须写「方向未定」，**不许**写「A 冲 B」（G2）。
> - ③ 只能三态之一；`basis.kind` 只有 `edge` 与 `structure_item` 两种。
> - ④ 的落事禁年份/概率/事件；引动只写「什么岁运地址 + 什么边种」。
> - ⑤ 的原文只引**支持结构**的那半句；原文里的吉凶断言不引（A-04）。

---

## 2 · 卡模板（机器 JSON 骨架）

```json
{
  "card_id": "<C1|C2|C3>-<两位>",
  "case_id": "RF-2026-XXXXXX",
  "snapshot": {"chart_id": "cf-…", "dayun_index": null, "liunian_year": null},

  "t1_local_image": {
    "palace": "year|month|day|hour|—",
    "addrs": ["D.b"],
    "ten_gods": ["比肩"],
    "relations": [
      {"kind": "chong", "edge_id": "e013", "members": ["D.b", "H.b"], "group": null, "completeness": null}
    ],
    "no_relation": false
  },

  "t2_role_and_force": {
    "tiyong": {"actor_role": "体", "target_role": "体"},
    "binzhu_layer": 3,
    "direction": "冲",
    "direction_known": false,
    "actor": null,
    "target": null
  },

  "t3_outcome": {
    "state": "破局",
    "basis": [
      {"kind": "edge", "edge_id": "e013", "assert": "目标受冲", "evidence": ["D.b", "H.b"]}
    ],
    "rescue_judged": "未判"
  },

  "t4_scene_and_activation": {
    "scene": "<结构→人事形态的 1–2 句>",
    "scene_refs": ["<其他 card_id>", "<其他 card_id>"],
    "activation": {
      "kind": "chong",
      "against_addr": "D.b",
      "suiyun_addr": "LN{year}.b",
      "edge_id": null,
      "condition": "<在什么岁运条件下被引动>",
      "path": "relations.edges[scope=liunian, members∋D.b]"
    }
  },

  "t5_dual_anchor": {
    "address_anchor": {"edge_ids": ["e013"], "addrs": ["D.b", "H.b"]},
    "text_anchor": {"entry_id": "M1-D-298", "path": "sources/…md", "line": 48}
  },

  "statement": "<含地址的本盘结论>",
  "boundary": {"holds_when": "<…>", "fails_when": "<…>"},
  "confidence": "中",
  "unknowns": ["G2"]
}
```

> 填写要求：
> - `snapshot` 三个字段一个都不能省；没有岁运就写 `null`（`L19`）。
> - `t1.relations[]` 里 `kind`/`members` 必须与 `engine.cli` 一字不差（`L03/L04`）。
> - `t2.actor/target` 与 `direction_known` 必须同向：置 `false` 时两者必须 `null`（`L06`）。
> - `t3.state` 三选一；`rescue_judged` 本版一律 `未判`（`L08/L09`）。
> - `t4.scene_refs` ≥2 条且同 `case_id`，不得含本卡（`L20/L21`）。
> - `t5.address_anchor` 必须覆盖 `t1.addrs` 的全部地址与边（`L14`）。
> - `statement` 不得只写计数（`L18`），必须含地址（`L15`）。

---

## 3 · 岁运卡模板差异（当 `snapshot.dayun_index/liunian_year` 非 `null`）

```text
- ① 的 edge_id 全部来自岁运快照（边数会从 N 涨到 M，编号全变）
- ② 只能写原局一侧的体用；岁运字的十神取不到 → unknowns 追加 "suiyun_ten_god"
- ④ 的 activation.edge_id 可以写该快照的边号（因为卡本身就建在这个快照上）
- confidence ≤ 中
```

> 填写要求：**同一张卡里不许混两个快照的边号**（`L12`）。要同时说原局与岁运，拆成两张卡，在 `scene_refs` 互相引用。

---

## 4 · 三张反例卡（写出来就会被拦）

| 反例 | 缺哪一元组 | 命中的规则 | 应该怎么写 |
|---|---|---|---|
| 「本盘七杀透干、伤官制杀，事业有成」 | ① 无地址；② 无 actor/target；⑤ 无原文 | `L01` `L02` `L13` | ① `Y.s=丁 七杀`；② `e002 ke[M.s,Y.s] actor=M.s`；⑤ `M1-D-009` |
| 「夫妻宫受冲，婚姻多波折」 | ② 无方向；③ 无三态；④ 无引动 | `L06` `L07` `L11` | ② `e013 [D.b,H.b]` + `direction_known=false`；③ 三态择一；④ 补引动 |
| 「日支被冲，20xx 年有变动」 | ④ 含年份（禁止射程） | `L10`（整卡不可用） | 删年份，改「流年支与 `D.b` 成冲时被引动」 |

---

## 5 · 可选报告外壳（8 节；每节必须引用 `card_id`）

```text
# 单盘分析：<case_id> / <四柱> / <乾|坤>

- case_id / 四柱 / 性别 / 出生时刻与口径 / 快照参数（dayun_index, liunian_year）
- 边界警告（以 engine.cli chart 为准，all 会删空值）：<…>
- variants：<轴=替代值 → 差异 | 无>
- 通过 Linter 的卡：<N> 张（关系型 <a> / 归属型 <b>）；被拦截：<M> 张（列出 card_id + 错误码）
- 报告定位：解释层（不承诺事件/年份/吉凶）

## 1. 盘面事实（只列事实，不解释）
<8 地址 + 8 十神 + 藏干 addr⊕char + 空亡 hits + 大运前 8 步 + profile 三轴 + boundary_warnings>
（本节不产卡）

## 2. 宾主
<引用归属型卡 card_id；每层主/宾地址集合；说明略过了哪些层及理由>

## 3. 体用
<引用归属型卡 card_id；体/用/双属三组地址，和 = 8；写清「不是子平用神」>

## 4. 做功路径
<逐卡列出卡块（§1 格式）：每张含 ①–⑤；能定方向的在前，方向未定的在后>
<另列「未进候选但必须登记的边」表：edge_id / kind / members / 不在候选的原因>

## 5. 成败/救应
<三态卡：成局 / 破局 / 逢救应化解；本盘无某态就写「本盘无此态」并给理由>

## 6. 取象/落事
<汇总第 4/5 节各卡的 t4.scene（不得新增内容，不得改写原句而不重跑 Linter）>

## 7. 这张盘不能说什么
<按 gaps_present 逐条：缺口 ID / 本盘表现（地址或字段）/ 因此不能说的话 / 正文是否已遵守>
<另列被拦截卡的 unknowns>

## 8. 证据索引
<8.1 卡索引：card_id / 类型 / 等级 / 快照>
<8.2 关系边表：edge_id / kind / members / group·completeness / 被引用于>
<8.3 做功候选表：mode / kind / edge_id / members / actor / 被引用于>
<8.4 结构项表：structure_id / item_id / kind / status / evidence / 被引用于>
<8.5 原文锚点表：entry_id / path:line / 支持的是哪张卡的哪条结构 / 是否引用了吉凶半句（必须为「否」）>
<8.6 复现命令表>
```

> 填写要求：
> - 第 4–6 节里出现的每条断语都要能指回 `card_id`；指不回 = 自由发挥（按 `L15` 降级并计入「泛泛」）。
> - 第 7 节列出的「不能说」，第 2–6 节一条都不许说；违反 → 整份「不可用」。
> - 第 6 节不得新增内容，只做汇总；汇总时改了措辞就要重跑 Linter。

---

## 6 · 交付前自检（逐项打勾）

```text
[ ] 每张卡：五元组齐全（L01）；① 有地址 + 边（L02）；边号在本快照存在且内容一致（L03/L04）
[ ] 每张卡：② 方向与边种相容（L05）；actor 为空时 actor/target 必为 null（L06）
[ ] 每张卡：③ 是三态之一、basis.kind 合法（L07）；救应标「未判」（L08/L09）
[ ] 每张卡：④ 无年份/概率/事件（L10）；有引动条件（L11）；无跨快照边号（L12）
[ ] 每张卡：⑤ 原文锚点可解析（L13）；地址锚点覆盖 ①（L14）；statement 含地址（L15）；边界双向（L16）
[ ] 每张卡：snapshot 三字段齐全（L19）；scene_refs 存在且不指向自己（L20/L21）；unknowns 合法（L17）
[ ] 报告：关系型卡 ≥3 张；第 4–6 节断语都能指回 card_id
[ ] 报告：第 7 节覆盖 gaps_present；第 2–6 节无违反
[ ] 报告：没有「可能有风险」类空话；没有规则原文冒充结论（A-04）；没有把「不知道」写成「没有」
[ ] 没有把计数（候选 N 个 / active_path_count）当结论
```

> 自检不通过时，按规格 §6.1 的 12 步判定顺序逐条定位；不要靠「再润色一遍」。

---

## 7 · 判定入口（交给判定人）

判定人用规格 §6.1（单卡）与 §6.2（整份），把结果填进规格 §6.5 的《判定记录卡》。
**写卡的人不能判自己**（规格 §6.3）。3 份报告里 ≥2 份判「模板」→ 触发 Kill criterion。

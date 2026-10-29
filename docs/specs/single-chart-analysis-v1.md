# 单盘分析规格 v1（五元组断语卡 + 可选报告外壳）

- 任务卡：`tasks/T-169/PROMPT.md`
- 状态：**v1.1 草案**（2026-10-29；v1 的「七段报告」已按 `docs/reviews/external-audit-adjudication-v2.md` §1.1 / §7 改为「五元组断语卡」）
- 依据：`docs/reviews/external-audit-adjudication-v2.md`（五元组、Linter 强制）、`docs/reviews/direction-audit-2026-10-29.md`（A 解释层）、`docs/reviews/failure-ledger-v1.md`（§0 与 A-01 / A-02 / A-04）、`META/address-level-evidence-audit-v1.md`（T-164）、`META/timing-feasibility-audit-v1.md`（T-165）
- 事实唯一来源：`python -m engine.cli`；理论唯一来源：`python -m tools.query_theory`
- 产物：本规格（卡怎么定义、怎么拦）、`META/single-chart-report-skeleton-v1.md`（卡模板 + 可选报告外壳）、`META/single-chart-cases-v1.json`（3 张盘的事实与缺口）

---

## 0 · 一句话

**产品的最小存在单元是一条五元组断语卡，不是一份报告。** 一条卡必须同时带齐：

| 元组 | 内容 | 一句话判据 |
|---|---|---|
| **① 原局象** | 宫位 + 十神 + 关系边/地址 | 有地址、有边号、有宫位 |
| **② 体用宾主与施力方向** | 体/用/双属 + 主/宾 + `actor → target` | 谁作用于谁，或明确写「方向未定」 |
| **③ 成败救应三态** | 成局 / 破局 / 逢救应化解 | 三态之一，不许压成布尔 |
| **④ 落事 + 岁运引动** | 结构→人事形态 + 该结构在什么岁运地址下被引动 | 有落点、有引动条件 |
| **⑤ 双锚点** | 盘面地址/`edge_id` + 原文 `path:line`/条目 ID | 两个锚点都能回查 |

**缺任一元组 → 该卡被 Linter 拦截，不得进入报告。** 报告只是通过 Linter 的卡片集合 + 一层外壳（§5）。

### 0.1 「分析」的操作定义：五元组没有丢掉 T-169 卡的 5 条门槛

| T-169 §2 原条件 | 在新架构里的落点 | 拦截码 |
|---|---|---|
| **A1 有盘面地址**（宫位 + 十神 + 关系边/地址） | 元组① `palace/addrs/ten_gods/relations` + 元组⑤ `address_anchor` | L02 / L14 |
| **A2 有作用方向**（谁作用于谁，不能只有 count） | 元组② `direction/actor/target/direction_known` | L05 / L06 / L18 |
| **A3 有原文/理论锚点** | 元组⑤ `text_anchor{entry_id,path,line}` | L13 |
| **A4 有适用边界**（成立 + 不成立） | 卡级 `boundary{holds_when, fails_when}` | L16 |
| **A5 可回查**（按 edge_id/地址逐项对上） | `snapshot` + 元组① 的 `edge_id` + 元组⑤ | L03 / L04 / L12 / L19 |

> 一句话：**5 条门槛一条没丢，只是从「报告里的句子」搬到了「卡的字段」**；原来靠人读，现在靠 Linter 拦。

## 1 · 定位：为什么最小单元是卡，不是报告

### 1.1 证据 → 约束

| 证据 | 结论 | 对本规格的约束 |
|---|---|---|
| `external-audit-adjudication-v2` §1.1：最小单元是 Address-Grounded Structural Verdict，五元组缺一不可 | 报告作为单元太粗 | 卡 = 单元；报告 = 集合（§5） |
| 同上 §1.3：聚合规则 / 46 原子 / 测量脚手架不构成分析能力 | 旧层不是能力 | 卡只引用事实层与原文，不引用 `claim-rules-v1.yaml` 的结论 |
| T-164 §2：12 个婚姻信号 **0 条有直接地址** | 聚合丢地址 | 计数类字段只能当脚注（§7.2） |
| failure-ledger **A-01**：`actor=None` 523/3179 | 冲/刑/穿/破无主客 | 元组②必须允许并**强制**写「方向未定」 |
| failure-ledger **A-02**：R1–R4 17.28% vs 随机 18.02%，p=0.679 | edge-count 不预测年份 | 元组④的「岁运引动」只写**引动条件**，不写年份事件（§2.4、§9.9） |
| failure-ledger **A-04**：`statement = conclusion_template` | 规则原文冒充结论 | 元组⑤强制双锚点；`statement` 必须含本盘地址 |
| T-165 §2 P4：合开墓库只有边、无开/闭结论 | 「库开」写不出来 | 元组③不许写「库已开」（§7.3） |

### 1.2 与「七段」的关系

七段没有消失，**降级为报告外壳的组织顺序**（§5.1）。判定的对象从「段」变成「卡」：一份报告里可以有 12 张卡，也可以一段里 0 张卡（该段只做事实陈列）。

### 1.3 三条铁律

1. **一卡一快照**：卡里的所有 `edge_id` 必须来自同一个 `(chart_id, dayun_index, liunian_year)` 快照。加 `--dayun-index/--liunian` 会给**全部**边重新编号（实测：`RF-2026-000125` 原局 `e012 liuhe[M.b,D.b]`，在 `--dayun-index 5 --liunian 2026` 快照里 `e012` 变成 `ke[M.s,LN2026.s]`；边数 16 → 39）。跨快照引用 = 错。
2. **缺元即拦**：五元组任一为空 → Linter 拦截（§4，L01）。
3. **报告只是集合**：报告不得引入卡里没有的结论；报告里出现的每条断语都必须能指回某张 `card_id`。

## 2 · 五元组：定义与判据

### 2.1 ① 原局象（`t1_local_image`）

- **必填**：`palace`（`year/month/day/hour` 或 `—`）、`addrs[]`（≥1，形如 `D.b`、`D.b⊕己`）、`ten_gods[]`（与 `addrs` 等长）、`relations[]`（每项 `{kind, edge_id, members, group, completeness}`）。
- **判据**：至少 1 个物理地址 + 至少 1 条关系（或显式 `no_relation: true` 并说明「本地址在本快照无边」，此时该卡不得声称有任何作用）。
- **不许**：只写十神不写地址；只写「日支被冲」不写 `D.b`/`e0xx`。
- **来源**：`chart.pillars[]`（`palace/stem.addr/stem.ten_god/branch.addr/branch.main_ten_god/branch.hidden[]`）+ `relations.edges[]`。

### 2.2 ② 体用宾主与施力方向（`t2_role_and_force`）

- **必填**：`tiyong{actor_role, target_role}` ∈ {体, 用, 双属}（取自 `duan_zuogong.tiyong`）、`binzhu_layer`（1–4，取自 `d01-deep-read.md:85-92` 的四层表）、`direction`（枚举见 §3.3）、`direction_known`（bool）、`actor`、`target`。
- **判据**：
  - `direction_known=true` → `actor`/`target` 必须与引擎一致（`ke` 取 `members[0]`；`candidate.actor` 取引擎值）；
  - `direction_known=false` → `actor`/`target` **必须为 `null`**，且 `direction ∈ {冲, 刑, 穿, 害, 破, 合}`（G2：引擎对这些 kind 不设 actor）。
- **不许**：`direction_known=false` 却写「A 冲 B」；把 `can_control` 当「制得住」（L-04）；把「用」写成子平用神（L-05）。
- **来源**：`duan_zuogong.tiyong`、`duan_zuogong.candidates[].actor/tiyong/mode`、`relations.edges[].kind/members`、`--full` 的 `candidates[].binzhu`。

### 2.3 ③ 成败救应三态（`t3_outcome`）

- **必填**：`state` ∈ {`成局`, `破局`, `逢救应化解`}（三态之一，**不许布尔**）、`basis[]`（每项 `{kind, edge_id|structure_id+item_id, status, evidence}`）、`rescue_judged` ∈ {`已判`, `未判`}。
- **判据**：
  - `成局`：元组① 的结构成立且无破边/破项 → 必须列支撑边；
  - `破局`：`structures[].items[kind=breaker].status=met` 或某条边对目标构成冲/刑/穿 → 必须给 `evidence`；
  - `逢救应化解`：必须有 `items[kind=rescuer].status=met` 的 `evidence`，且 `rescue_judged` 必须显式写。
- **`basis` 只有两种 `kind`**（不许自创）：
  - `structure_item`：`structures[]` 里的项，必须带 `status` 与 `evidence`；
  - `edge`：`relations.edges` 里的边，必须带 `assert`（「目标受冲/刑/穿/破」之一）与 `evidence`（地址）。
  - **`破局` 判定的依据只能来自这两类**；把「有冲边」直接等于「破局」而不给原文依据（⑤）→ 在 §6.1 第 7 步（查原文）判「错」。
- **v1 硬约束**：`rescue_judged=已判` 只允许在「救应原语 + 外部审计编号」同时存在时使用；**本版一律写 `未判`**（G5：盲派域无救应事实），否则 Linter 拦截（L09）。
- **不许**：把救应当「没发生」；把 `met` 说成「成格」；写「库已开/已闭」（合开墓库无结论）。
- **来源**：④ 的边 + `structures[].items[]` + `relations.muku[].openers/binders`。

### 2.4 ④ 落事 + 岁运引动（`t4_scene_and_activation`）

- **必填**：`scene`（1–2 句）+ `scene_refs[]`（引用的其他 `card_id`，≥2 且同 `case_id`）+ `activation{kind, against_addr, suiyun_addr, edge_id|null, condition, path}`。
- **判据（落事）**：把**结构**翻译成**人事关系的形态**（谁与谁、在哪一宫、以何种作用相连）；必须能指回本卡 ① 的地址。
- **判据（引动）**：写出「该结构在什么岁运地址下被引动」——`kind`（边种）+ `against_addr`（原局地址）+ `suiyun_addr`（`DY{n}.b` / `LN{year}.b`，或通配 `LN{year}.b`）。若在该快照中未见引动边，写 `activation.kind="none_observed"` + 该快照的边数证据（T-165：「无岁运边 0/6112 表示 False 是真否定」）。
- **禁止的射程**（出现即整卡「不可用」，L10）：年份/年龄/期限（`20xx`、「三十岁前后」）；概率/程度词（大概率、一定、必定、注定、必然）；事件断言（结婚/离婚/疾病/破财/升职的具体发生）；只靠十神名称的形容词。
- **来源**：`engine.cli all --dayun-index N --liunian YYYY --json` 的 `relations.edges[scope=dayun|liunian|dayun+liunian]`。
- **缺口**：岁运字的十神/体用**不在 CLI 输出里**（`chart.pillars` 只有 4 柱，`tiyong` 只有 8 个原局地址）→ 该卡必须写 `unknowns:["suiyun_ten_god"]`，且不得对岁运字下十神判断（§7.3）。

### 2.5 ⑤ 双锚点（`t5_dual_anchor`）

- **必填**：`address_anchor{edge_ids[], addrs[]}` + `text_anchor{entry_id, path, line}`。
- **判据**：
  - `address_anchor` 必须**覆盖**元组① 的全部地址与边（不能只锚一半）；
  - `text_anchor` 必须是 `path:line` 或 `tools.query_theory` 的条目 ID，且**支持的是该句的结构，不是该句的吉凶**（原文里的吉凶断言不得引用，A-04）。
- **不许**：只写「盲派认为」；引用原文的吉凶半句来支撑结构结论。

### 2.6 缺元判定（Linter 的第一道门）

| 缺失 | 错误码 | 动作 | 修复方向 |
|---|---|---|---|
| 五元组任一为空 | `L01` | **拦截** | 补齐该元组，或把该断语降级为「假设」（不进报告） |
| ① 无地址或无关系 | `L02` | **拦截** | 补 `addrs`/`edge_id`；确实无边则写 `no_relation` 且整卡不称作用 |
| ② 无方向且未声明「方向未定」 | `L06` | **拦截** | 补 `direction_known=false` + `actor/target=null` |
| ③ 缺 state 或是布尔 | `L07` | **拦截** | 三态择一 |
| ④ 无落事或无引动 | `L10/L11` | **拦截** | 补 `scene`/`activation` |
| ⑤ 缺原文或地址锚点 | `L13/L14` | **拦截** | 补锚点 |

## 3 · 卡片 schema

### 3.1 人读卡块（报告里一屏一张）

```text
### [C2-03] <一句话标题>
- ① 原局象：<宫位> / <地址+十神> / <edge_id kind[members] group/completeness>
- ② 体用宾主：体=<…> 用=<…>；第 n 层主=<…> 宾=<…>；方向=<克|…>（actor → target | 方向未定）
- ③ 三态：<成局|破局|逢救应化解>；依据=<edge_id / structure_id.item_id status evidence>；救应=<已判|未判>
- ④ 落事：<1–2 句>；引动=<kind> @ <against_addr> × <suiyun_addr>（<condition>）
- ⑤ 锚点：地址=<edge_ids/addrs>；原文=<entry_id path:line>
- statement：<本盘结论，含地址>
- 边界：成立=<…>；不成立=<…>
- confidence：<高|中|低|未知>；unknowns：<G2/…>
- 快照：chart_id=<…> dayun_index=<…> liunian_year=<…>
```

### 3.2 机器 JSON（字段即 Linter 输入）

| 字段 | 类型 | 约束 |
|---|---|---|
| `card_id` | string | `<case序号>-<两位>`，如 `C2-03`；同报告内唯一 |
| `case_id` | string | 必须与 `META/single-chart-cases-v1.json` 的 `case_id` 一致 |
| `snapshot` | object | `{chart_id, dayun_index, liunian_year}`；无岁运时也必须写 `null` |
| `t1_local_image` | object | 见 §2.1 |
| `t2_role_and_force` | object | 见 §2.2 |
| `t3_outcome` | object | 见 §2.3 |
| `t4_scene_and_activation` | object | 见 §2.4 |
| `t5_dual_anchor` | object | 见 §2.5 |
| `statement` | string | 必须含 `t1_local_image.addrs` 里至少 1 个地址 |
| `boundary` | object | `{holds_when, fails_when}`，两项非空 |
| `confidence` | enum | `高/中/低/未知`（§3.3） |
| `unknowns` | string[] | 只接受 §7.3 的缺口 ID |

### 3.3 枚举与引擎映射

`direction` 与引擎的映射（**不许自行扩展**）：

| direction | 引擎依据 | `direction_known` | `actor` |
|---|---|---|---|
| `克` | `edge.kind=ke`（members 有序 from→to） | true | `members[0]` |
| `制` | `candidate.mode=制用` 且 `actor` 非空 | true | 引擎 `actor` |
| `生` / `泄` | `edge.kind=sheng` 或 `candidate.relation_kind=sheng(main_qi)` | true | 引擎 `actor` |
| `化` | `candidate.mode=化用`（官杀→印） | true | 引擎 `actor` |
| `合` | `kind ∈ {wuhe,liuhe,zhi_anhe,ganzhi_zihe}` | **false** | `null` |
| `墓` | `candidate.mode=墓用`（入墓字 → 库） | true | 引擎 `actor` |
| `冲`/`刑`/`穿`/`害`/`破` | `kind ∈ {chong,xing,chuan,po}`、`stem_chong` 另计 | **false** | `null`（G2） |

`confidence`：

| 取值 | 条件 |
|---|---|
| **高** | 五元组齐全 + 回查逐项一致（`edge_id`+`members`+`actor` 都对上）+ 边界双向具体 |
| **中** | 五元组齐全，但 ⑤ 的原文只能引到同一 anchor 的不同层，或 ② 的双属归属需说明 |
| **低** | 五元组齐全，但方向靠候选推定（`双属` 择端），或 ④ 的引动是条件式而非本快照实测 |
| **未知** | 事实缺口导致该断语不能成立；只允许出现在「假设」栏与 ⑦，**不进入通过 Linter 的卡** |

`state`（③）：`成局` / `破局` / `逢救应化解`。**没有第四种**；无法判断时该卡不成立（降级为假设），不许写「部分成局」。

### 3.4 合格卡示例（C2 原局快照）

```json
{
  "card_id": "C2-03",
  "case_id": "RF-2026-000438",
  "snapshot": {"chart_id": "cf-f10b5515f2019638f42f", "dayun_index": null, "liunian_year": null},
  "t1_local_image": {
    "palace": "day",
    "addrs": ["D.b", "H.b"],
    "ten_gods": ["比肩", "比肩"],
    "relations": [
      {"kind": "chong", "edge_id": "e013", "members": ["D.b", "H.b"], "group": null, "completeness": null},
      {"kind": "xing", "edge_id": "e014", "members": ["D.b", "H.b"], "group": "丑戌未", "completeness": "partial"}
    ]
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
      {"kind": "edge", "edge_id": "e013", "assert": "目标受冲", "evidence": ["D.b", "H.b"]},
      {"kind": "edge", "edge_id": "e014", "assert": "目标受刑", "evidence": ["D.b", "H.b"]}
    ],
    "rescue_judged": "未判"
  },
  "t4_scene_and_activation": {
    "scene": "夫妻宫 D.b=未 同时受 H.b=丑 的冲边与刑边，『本位』长期被同一处外力顶住。",
    "scene_refs": ["C2-01", "C2-02"],
    "activation": {"kind": "chong", "against_addr": "D.b", "suiyun_addr": "LN{year}.b", "edge_id": null, "condition": "流年支与 D.b 成冲时被引动", "path": "relations.edges[scope=liunian, members∋D.b]"}
  },
  "t5_dual_anchor": {
    "address_anchor": {"edge_ids": ["e013", "e014"], "addrs": ["D.b", "H.b"]},
    "text_anchor": {"entry_id": "M1-D-298", "path": "sources/duan/MinerU_markdown_婚姻专辑_2056044010230448128.md", "line": 48}
  },
  "statement": "D.b=未 与 H.b=丑 构成冲边 e013 与刑边 e014（方向未定，G2）；按 M1-D-298「夫妻宫位要安静，如有用，不能被刑坏，冲破，穿倒」，本盘夫妻宫属被冲破/刑坏的一类。",
  "boundary": {"holds_when": "以 D.b=未 为夫妻宫，且 e013/e014 在同一原局快照内成立", "fails_when": "换快照后 edge_id 失效（加 --dayun-index/--liunian 会全量重编号）；或夫妻宫改按其他口径取柱；或 M1-D-298 的「如有用」前提不成立（夫妻宫为所忌之神时该条不适用，见同文件 :50）"},
  "confidence": "中",
  "unknowns": ["G2"]
}
```

> 说明：
> - 本卡**不写**「丑冲未」的主客（G2）：虽然 `M3-R-034`（`theory/raw/ren/r01-r04-theory.md:174`）给了六冲克向「丑未冲→土冲变虚」，但事实层 `actor=None`，本规格 v1 不允许用原文补引擎缺口（§9.12）。
> - `state=破局` 的**依据是两条边 + `M1-D-298` 的原文判据**，不是「有冲边就等于破」；`basis` 里没有结构项，因为婚姻域没有对应结构（G5）。
> - `rescue_judged=未判`：本盘 `structures` 有 3 条 `rescuer.met`（`e003`/`Y.s,M.s`/`e006`），但它们属子平八格，不是夫妻宫救应。

### 3.5 岁运卡示例（C1，DY5 + 2026 快照）

- 快照：`--dayun-index 5 --liunian 2026`；此时边数 39（原局 16），`e033 chong[D.b,DY5.b]`、`e034 xing[D.b,DY5.b]`、`e035 chuan[D.b,LN2026.b]`。
- 元组① 用该快照的 `e033/e034/e035`；**不得**引用原局快照的 `e015/e016`（编号已变）。
- 元组② 只能写「D.b（体）与 DY5.b 构成冲/刑」；**DY5.b 的十神不可得**（§2.4 缺口）→ `unknowns:["G2","suiyun_ten_god"]`，`confidence ≤ 中`。
- 元组④ 的 `activation.edge_id` 可以写 `e033`，因为该卡快照就是岁运快照。

### 3.6 三张反例卡（各缺一元组）

| 反例 | 缺什么 | 会被哪条拦 | 正确写法 |
|---|---|---|---|
| 「本盘七杀透干、伤官制杀，事业有成」 | ① 无地址、② 无 actor/target、⑤ 无原文 | `L01` / `L02` / `L13` | 补 `Y.s=丁 七杀`、`e002 ke[M.s,Y.s] actor=M.s`、`M1-D-009` |
| 「夫妻宫受冲，婚姻多波折」 | ② 无方向（`actor=None`）、④ 无引动、③ 无三态 | `L06` / `L11` / `L07` | 写 `e013 [D.b,H.b] 方向未定`；③ 择一态；④ 补引动条件 |
| 「日支被冲，20xx 年有变动」 | ④ 含年份（禁止射程） | `L10`（整卡不可用） | 删年份；改为「流年支与 D.b 成冲时被引动」 |

## 4 · Linter 规则（写规格，不写代码）

### 4.1 两种动作

- **拦截**：该卡不得进入报告；报告里出现被拦截的卡 → 整份报告「不可用」。
- **降级**：该卡可以进报告，但等级上限为「泛泛」，且必须在卡上标 `degraded: true` 与原因码。

### 4.2 规则表

| 码 | 检查 | 触发条件 | 动作 | 依据 |
|---|---|---|---|---|
| **L01** | 五元组齐全 | `t1..t5` 任一缺失/为空对象 | **拦截** | §2.6、adjudication v2 §1.1 |
| L02 | ① 有地址 + 有关系 | `addrs` 为空，或 `relations` 为空且无 `no_relation` | 拦截 | §2.1 |
| L03 | ① 边号存在 | `edge_id` 不在该快照 `relations.edges[].id` | 拦截 | A5 可回查 |
| L04 | ① 边内容一致 | `kind`/`members` 与引擎不一致 | 拦截 | 上 |
| L05 | ② 方向与边种相容 | `direction` 与 `kind` 违反 §3.3 映射（如 `chong` 配 `制` 且 actor 非空） | 拦截 | §3.3 |
| L06 | ② 方向未定即置空 | `direction_known=false` 但 `actor/target` 非空，或反之 | 拦截 | G2 |
| L07 | ③ 三态非布尔 | `state` 不在三态内、或是 `true/false`；或 `basis[].kind` 不在 `{structure_item, edge}` 内 | 拦截 | §2.3 |
| L08 | ③ 救应须标示 | `state=逢救应化解` 但无 rescuer `evidence`，或 `rescue_judged` 缺失 | 拦截 | G5 |
| L09 | ③ 救应不得擅判 | `rescue_judged=已判` 且无「救应原语 + 外部审计编号」 | 拦截 | §2.3、§9.2 |
| **L10** | ④ 禁止射程 | `scene` 命中年份/概率/事件词表 | **拦截（整卡不可用）** | §2.4 |
| L11 | ④ 引动不得缺 | `activation.kind` 为空；或 `none_observed` 但未给该快照边数证据 | 拦截 | §2.4 |
| L12 | ④ 引动不得跨快照 | `activation.edge_id` 存在但 `scope`/快照与卡不一致 | 拦截 | §1.3 铁律 1 |
| L13 | ⑤ 原文锚点可解析 | `text_anchor` 既非 `path:line` 也非 `entry_id`；或 `entry_id` 检索不命中 | 拦截 | A3 |
| L14 | ⑤ 地址锚点覆盖 | `address_anchor` 未覆盖 ① 的地址/边 | 拦截 | A5 |
| L15 | statement 含地址 | `statement` 不含 ① 的任何地址 | **降级** | A1 |
| L16 | 边界双向 | `holds_when`/`fails_when` 任一为空 | **降级** | A4 |
| L17 | 缺口 ID 合法 | `unknowns` 引用 §7.3 之外的 ID | 拦截 | §7.3 |
| L18 | 计数句 | `statement` 只含计数表述、无地址/边 | **降级** | T-164 D4 |
| L19 | 快照字段齐全 | `snapshot` 缺 `chart_id`/`dayun_index`/`liunian_year`（`null` 也要写） | 拦截 | §1.3 |
| L20 | 引用卡存在 | `scene_refs` 引用的 `card_id` 不存在，或跨 `case_id` | 拦截 | §2.4 |
| L21 | 卡未被重复引用为自身 | `scene_refs` 含本卡 `card_id` | 拦截 | 循环引用 |

### 4.3 Linter 输入/输出契约（交给实现卡）

- 输入：一份卡的 JSON（§3.2）+ 生成该卡的 `engine.cli` 快照（同参数重跑）。
- 输出：`{"card_id":…, "verdict":"pass|blocked|degraded", "codes":["L01",…], "fix_hint":"…"}`。
- 本卡**不实现** Linter；本节只定义判据。实现归 T-169 之后的任务卡，且不得放宽本表。
- 报告级：`all(card.verdict != "blocked")` 才允许发布；`degraded` 卡计入「泛泛」分母（§6.2）。

## 5 · 可选报告外壳（七段 → 卡片集合）

### 5.1 段 ↔ 卡映射

| 段 | 产不产卡 | 卡片类型 | 必填地址 | 失败模式 |
|---|---|---|---|---|
| ① 排盘 | **不产卡** | — | 8 个物理地址 + 宫位 + 十神 + 空亡 + 大运 + `boundary_warnings` | 心算/编造；不看 `variants`；用 `all` 的缺键当「无警告」 |
| ② 宾主 | 产「归属型卡」 | `t2` 用「主→宾」作方向 | 每层主/宾的地址集合（L1–L4） | 只列十神不定主宾；把宾主写成吉凶 |
| ③ 体用 | 产「归属型卡」 | `t2` 用「体→用」作方向 | 8 个地址全部归入 体/用/双属 | 把「用」写成子平用神（L-05）；`双属` 强行择一不写理由 |
| ④ 做功 | 产「关系型卡」（主卡） | `direction` 取 §3.3 | 每条：`edge_id` + `members` + `actor` + `target` | 只有 count；只抄 `candidates`（漏 `po`/三合/同体边） |
| ⑤ 成败/救应 | 产「关系型卡」 | `state` 三态 | 每态的依据边/结构项 + `evidence` | 把救应当「没发生」；压成布尔；把 `met` 说成成格 |
| ⑥ 取象/落事 | **不单独产卡** | — | 每张卡的 `t4.scene` 必须指回本卡 ① 的地址 + ≥2 条 `scene_refs` | 输出「可能有风险」类空话；句子里没有地址 |
| ⑦ 不确定 | **不产卡** | — | 缺口 ID + 受影响的地址/边 | 把「不知道」写成「没有」；正文违反 ⑦ |
| ⑧ 证据索引 | **不产卡** | — | 卡索引 + edge_id/原文行对照 | 引用了不存在的边号或原文锚点 |

> 关键变化：⑥ 不再是「一段 1–2 句」，而是**每张卡的 `t4.scene`**；报告里若想单列「取象」，只能汇总已通过 Linter 的卡的 `scene`，不得新增内容。

### 5.2 报告 8 节（保留，但每节必须引用 `card_id`）

```text
# 单盘分析：<case_id> / <四柱> / <乾|坤>
## 1. 盘面事实（只列事实，不解释）        ← 不产卡；须含 8 地址/十神/藏干/空亡/大运/边界/variants
## 2. 宾主                                ← 引 [C?-01 …]
## 3. 体用                                ← 引 [C?-0x …]
## 4. 做功路径                            ← 主卡区：逐卡列出 ①–⑤
## 5. 成败/救应                           ← 三态卡
## 6. 取象/落事                           ← 汇总 ④ 的 scene（不得新增）
## 7. 这张盘不能说什么                    ← 覆盖 gaps_present；列出被拦截卡的 unknowns
## 8. 证据索引                            ← 卡索引 + edge/原文对照表
```

### 5.3 报告级门槛

- 一份报告至少 **3 张通过 Linter 的关系型卡**；不足 3 张时报告直接判「模板」，不再看其他项。
- 报告正文出现的每个断语必须能指回 `card_id`；指不回的句子视为「自由发挥」，按 `L15` 降级并计入「泛泛」。
- 报告不得改写卡的 `statement` 以求通顺；改写后必须重新过 Linter（改写可能删掉地址）。

## 6 · 判定表（给人类用）

### 6.1 单卡四等级

| 等级 | 定义 |
|---|---|
| **有依据** | 五元组齐全；地址/边/原文锚点齐全，方向明确（或显式「方向未定」），能回查 |
| **泛泛** | 有地址但只到「某支被冲」，没有作用方向/主体；或 `degraded=true`（L15/L16/L18） |
| **错** | 地址或方向与 `engine.cli` 不符，或原文锚点不支持，或引用不存在的边号，或跨快照引用 |
| **无法判** | 事实缺口（`actor=None`、合开墓库、无配偶星、`suiyun_ten_god`）导致该断语不能成立；应降级为「假设」 |

**判定顺序（按序，任一步失败即止）**：

1. **L01**：五元组齐不齐？缺 → 直接「无法判/拦截」，不再往下。
2. **查地址**（L03/L04/L14）：每个地址/边号在 `all` 输出里能否找到？不能 → **错**。
3. **查方向**（L05/L06）：`actor`/`target` 与引擎一致？`actor=None` 的边却写了主客 → **错**。
4. **查三态**（L07/L08/L09）：是不是三态之一？救应有没有标「已判/未判」？擅判 → **错**。
5. **查落事**（L10）：有没有年份/概率/事件？有 → **不可用**。
6. **查引动**（L11/L12）：有没有引动条件？跨快照 → **错**；缺 → **拦截**。
7. **查原文**（L13）：`source_ref` 支持的是结构还是吉凶？支持吉凶 → **错**。
8. **查边界**（L16）：`holds_when`/`fails_when` 都具体？缺 → **泛泛**。
9. **可替换性检验**：换一张盘的同名地址后句子仍成立 → **泛泛**。
10. **反事实检验**：删掉引用的边后句子仍成立 → **泛泛**（伪引用）。
11. **缺口检验**（L17）：句子是否落在 §7.3「不能写」清单上？落在 → **无法判**。
12. 全过 → **有依据**。

### 6.2 整份报告

| 判定 | 标准（全部满足才算） |
|---|---|
| **真分析** | （a）≥3 张「有依据」的关系型卡；（b）每张卡的 `t4.scene` 都无年份/概率/事件断言，且能指回该卡地址；（c）⑦ 覆盖本盘 `gaps_present`，正文未违反 ⑦；（d）无「错」卡，且无被拦截的卡混入 |
| **模板** | 多数卡是「泛泛」/模板句；地址只在标题或只在第 1 节；④ 只有 count 没有方向；或通过 Linter 的关系型卡 <3 张 |
| **不可用** | 关键地址/方向错误（≥1 张「错」卡且在 ④–⑥ 区）；或把「不知道」写成「没有」；或出现年份/概率/事件断言（违反 §2.4） |

**分母定义**：

- 计「卡数」= 通过 Linter 的关系型卡（②③ 的归属型卡不计入「≥3 张」门槛，但计入「多数」的分母）。
- 「多数」= 泛泛 + `degraded` 卡 > 总卡数 × 50%。
- 出现 1 条 §2.4 禁止射程 → 整份直接「不可用」，不再看其他项。

### 6.3 Kill criterion

> **3 份报告里 ≥2 份被判「模板」→ 这个产品形态停。**

- 不追加测量、不换盘、不换 K、不调阈值、不删 Linter 规则来「救」它（一切「让失败变绿」的改动都算违规）。
- 停项后只有两条出路：**回到理论建模**（需领域专家，另立卡、另走外部审计）或**停项**。
- 「不可用」不等于「模板」：出现「错」卡或「把不知道写成没有」，说明是**执行事故**，先修流程再重判，不触发 Kill。
- 判定必须由**未参与写作的人**执行（写卡的人不能判自己）。

### 6.4 判定示例（全部取自本卡 3 张盘，可回查）

| 示例 | 卡/句子 | 等级 | 理由 |
|---|---|---|---|
| 合格 | C2 卡：① `D.b=未` / `H.b=丑` + `e013 chong`、`e014 xing`；② 体→体、方向「冲」但 `direction_known=false`；③ `破局`（`basis.kind=edge`：`e013` 目标受冲、`e014` 目标受刑，`rescue_judged=未判`）；④ 落事「夫妻宫被同一处外力顶住」+ 引动「流年支与 `D.b` 成冲」；⑤ 地址锚点 `e013/e014` + 原文 `M1-D-298`（`sources/duan/MinerU_markdown_婚姻专辑_2056044010230448128.md:48`）；边界双向 | **有依据** | 五元组齐全；冲/刑按 G2 标「方向未定」，没有用 `M3-R-034` 的克向去补；原文支持的是「夫妻宫不能被刑坏/冲破」这一结构判据，不是吉凶断言；可回查 |
| 泛泛 | 「`RF-2026-000438` 日支被冲，婚姻宫不稳。」 | **泛泛** | 只有 `D.b` + 「被冲」，无主体、无 `e013`、④ 无引动（L11/L15/L18 命中） |
| 错 | 「`RF-2026-000438`：`M.b=寅` 冲 `D.b=未`。」 | **错** | `M.b` 与 `D.b` 之间没有任何边（`e008` 是 `[Y.b,M.b]`，`e012` 是 `[M.b,H.b]`）；夫妻宫冲边是 `e013 [D.b,H.b]` |
| 错（跨快照） | 「C1 卡引用 `e012 liuhe[M.b,D.b]`，但快照写 `--dayun-index 5 --liunian 2026`。」 | **错** | 该快照里 `e012` 是 `ke[M.s,LN2026.s]`；原局 `e012` 只在 `dayun_index=null` 的快照成立（L12） |
| 无法判 | 「C1：`D.b=丑` 库被 `e012` 合开。」 | **无法判** | `e012` 是 `binders`，`e015/e016` 是 `openers`；开/闭无事实（合开墓库缺口），应降级为假设 |
| 不可用 | 「`RF-2026-000894`：无财星，故终身无婚。」 | **不可用** | 把「没有配偶星地址」写成「没有婚姻」；且 `late_zi` 盘日柱可变为 `辛丑`，四柱不唯一 |

### 6.5 判定记录卡（每份报告填一张）

```text
报告：<case_id> / <判定人> / <日期>
通过 Linter 的卡：__ 张（关系型 __ / 归属型 __）；被拦截：__ 张
有依据: __   泛泛: __   错: __   无法判: __
④ scene 含年份/概率/事件: 是/否
⑦ 覆盖 gaps_present: 是/否；正文违反 ⑦: 是/否
整份判定: 真分析 / 模板 / 不可用
触发条款: <6.2 的哪一行> / <6.3 是否触发>
```

## 7 · 地址词汇表、快照规则、缺口清单

### 7.1 算地址（可直接引用）

| 类 | 字段（`engine.cli` 输出路径） | 形态 | 备注 |
|---|---|---|---|
| 物理地址 | `chart.pillars[].stem.addr` / `.branch.addr` | `Y.s…H.b` | 每盘 8 个；岁运 `DY{n}.s/.b`、`LN{year}.s/.b` 只出现在边 members 里 |
| 宫位 | `chart.pillars[].palace` | `year/month/day/hour` | 报告写「年(year)」双写 |
| 十神（干/支本气） | `stem.ten_god` / `branch.main_ten_god` | `七杀/正财/…` | 日干为「日主」 |
| 十神（藏干） | `branch.hidden[]`（`c/q/g`） | **`D.b⊕己`** | 藏干无独立地址（G4） |
| 关系边 | `relations.edges[]` | `e013 chong[D.b,H.b]` | 边号只在本快照有效（§1.3） |
| 地址对索引 | `relations.pair_index` | `D.b\|H.b → [e015,e016]` | 仅 `engine.cli relations` 返回 |
| 墓库 | `relations.muku[].openers/binders/chuan_po/...` | `D.b=丑 openers=[e015,e016]` | 只给边，不给开/闭结论 |
| 做功候选 | `duan_zuogong.candidates[].actor/mode/members/edge_id/tiyong` | `制用 ke e002 [M.s,Y.s] actor=M.s` | `actor` 空 = 无方向（G2） |
| 体用 | `duan_zuogong.tiyong` | `{"D.b":"体","M.s":"双属"}` | **只有 8 个原局地址，无 DY/LN** |
| 通根/印气 | `strength.day_master.roots[]`、`resource_in_branches[]` | `addr=D.b hidden_char=辛 qi=余气` | 藏干用 `addr + hidden_char` 拼 |
| 空亡 | `chart.kongwang.hits[]` | `[["D.b","year"]]` | 地址型，不是吉凶 |
| 子平结构 | `structures[].items[].evidence` | `rsc_he_qu_shang met evidence=["e001"]` | `met` 只表示要件命中 |
| 神煞 | `shensha.hits[]` | `桃花 anchor=Y.b target=M.b` | 本规格不要求使用 |

### 7.2 不算地址（出现即降级）

| 字段 | 为什么不算 | 处理 |
|---|---|---|
| `features.ten_god_counts` / `strength.camp_counts` | 计数无地址（T-164 §5.1：比劫≥3 真值 288，能写 3 个地址的只有 243） | 只能当脚注，必须另给地址清单 |
| `active_path_count` / `layer_count` / `palace_pair_count` / `independent_signal_count` | 聚合（T-164 D4/Y7：0/382 可写地址） | 不得单独成句（L18） |
| 任何 `xx >= N` 的布尔 | 无主体无方向 | 同上 |

### 7.3 缺口清单 → 「不能写」对照表

| 缺口 ID | 事实现状（来源） | 不能写 | 只能写 |
|---|---|---|---|
| **G2** | 冲/刑/穿/破不设 actor（`structure_check.py:475-478`），523/3179 | 「A 冲 B」的主客；**也不许用原文克向去补**（`M3-R-034` 虽有「丑未冲→土冲变虚」，见 §9.12） | 「`D.b` 与 `H.b` 构成冲边 `e013`（方向未定）」 |
| **G3** | 地支不建克边（880 对，边 0 条） | 「比劫夺财/伤官制官」双方都在支上的结论 | 「支上克向存在，事实层无边，故不判」 |
| **G4** | 藏干无独立地址（`types.py:69-74`） | 以藏干为主体的独立地址 | `D.b⊕己` 复合串 |
| **G5** | 盲派域无救应/反制事实（只覆盖子平八格） | 「有忌象得救应化解」作为结论 | 「有救应候选边，是否化解不判」 |
| **muku_open_close** | `muku[]` 只给 `openers`（冲/刑）与 `binders`，无开/闭结论（T-165 P4） | 「库被冲开/被合住」 | 「开边与合边并存，孰胜不判」 |
| **no_spouse_star** | 20/382 无财（乾）/无官杀（坤） | 任何「配偶星受制」的句子 | 「本盘无配偶星地址」 |
| **boundary_zi_shi** | 晚子时日柱随口径变（`variants[axis=zi_shi]`） | 把当前四柱当唯一 | 并列 `alt_chart_id` |
| **near_jie** | 交节 ±2h，月/年柱可能不同 | 把月柱当唯一 | 并列 `boundary_warnings` 细节 |
| **suiyun_ten_god** | `chart` 只有 4 柱，`tiyong` 只有 8 个原局地址 → DY/LN 的十神/体用取不到（T-165 E3） | 对岁运字下十神判断 | 只写边种 + 地址；`unknowns:["suiyun_ten_god"]` |

### 7.4 读取口径的 4 个坑（已在 3 张盘上验证）

1. **`all` 删空值**：`boundary_warnings: []` 时整个键消失；边界必须用 `engine.cli chart`。（`RF-2026-000125`/`-000438` 的 `all` 无该键、`chart` 返回 `[]`；`-000894` 的 `all` 有该键且只一条 `late_zi`。）
2. **`all` 削掉** `candidates[].binzhu`/`distance`、`edges[].chars`/`between`、`relations.nodes`、`pair_index`。
3. **加岁运会全量重编号**：`RF-2026-000125` 原局 16 条边 → DY5+2026 快照 39 条；`e012` 从 `liuhe[M.b,D.b]` 变成 `ke[M.s,LN2026.s]`。
4. **候选不是边的全集**：`candidates` 只扫「体用相交」且 `kind ∈ {ke,stem_chong,chong,xing,chuan} ∪ {wuhe,liuhe,zhi_anhe,ganzhi_zihe}`（`structure_check.py:363-364,472`）。实测漏边：

| 盘 | 边数 | 进候选 | 落在夫妻宫却不在候选的边（原因） |
|---|---|---|---|
| `RF-2026-000125` | 16 | 10 | `e013 sanhui[M.b,D.b]`（kind 不在清单）、`e015 chong[D.b,H.b]`、`e016 xing[D.b,H.b]`（两端皆体） |
| `RF-2026-000438` | 14 | 7 | `e009 liuhe[Y.b,D.b]`、`e013 chong[D.b,H.b]`、`e014 xing[D.b,H.b]`（两端皆体）、`e010 sanhui[Y.b,D.b]`（kind） |
| `RF-2026-000894` | 12 | 5 | `e009 po[M.b,D.b]`（`po` 不在清单） |

## 8 · 3 张盘

| # | case_id | 四柱 | 性别 | `chart_id` | 角色 | 选择理由 |
|---|---|---|---|---|---|---|
| C1 | `RF-2026-000125` | `丁卯 壬子 辛丑 乙未` | 乾 | `cf-5735e1472538ad92664b` | 结构完整 | 17 个做功候选、12 个 `actor` 非空；夫妻宫 4 条边中 3 条不在候选里；墓库 `openers`+`binders` 并存 |
| C2 | `RF-2026-000438` | `庚午 戊寅 己未 乙丑` | 坤 | `cf-f10b5515f2019638f42f` | 配偶星可查 | 官杀配偶星 4 个地址；夫妻宫 4 条边**全部**不在候选里；`H.b` 落空亡 |
| C3 | `RF-2026-000894` | `壬戌 己酉 庚子 戊子` | 乾 | `cf-8b541a506fc413884431` | 边界盘 | 晚子时（`rollover_23` → 日柱 `辛丑`，`alt_chart_id=cf-62995823c069f1deacba`）+ **无配偶星** + 夫妻宫落年旬空 + 夫妻宫唯一关系边是 `po` |

逐盘事实、`gaps_present`、`edges_not_in_candidates` 见 `META/single-chart-cases-v1.json`。

## 9 · 待外部审计确认（本卡**不裁决**）

| # | 待确认项 | 现状（可回查） | 为什么不裁决 |
|---|---|---|---|
| 9.1 | **合能否开墓库** | `binders` 与 `openers` 并存无判定；`M1-D-013` 原文只讲「冲为库、不冲不刑是墓」，不含合 | 需原文层与领域裁决；T-165 P4 已记缺口 |
| 9.2 | **救应是否化解** | 盲派域无救应事实（G5），只有子平八格 `rescuer` | 无原语，写「已判」就是编（L09 拦） |
| 9.3 | **宾主第 3/4 层的独立锚点** | 四层表在 `theory/raw/duan/d01-deep-read.md:85-92`，但 `M1-D-001..004` 共用 anchor `:75` | 能否各自单独引用，需索引确认 |
| 9.4 | **`双属` 是否必须择一** | `tiyong_view` 刻意不择；原文「食神更近于体，伤官则接近于用」 | 择端会改变 `mode` 归类；本规格只要求「择了写理由」 |
| 9.5 | **`po`（破）是否该进制用候选** | `_ZHI_KINDS` 不含 `po`；C3 夫妻宫唯一关系边因此不在候选内 | 是否算一种做功，需原文/领域确认 |
| 9.6 | **无配偶星盘的口径** | 20/382；T-165 P3 记「语义：部分」 | 是否用宫位代星，本卡不裁决 |
| 9.7 | **⑥ 落事的射程** | 本规格限定「结构→人事形态」，禁年份/概率/事件 | 「多具体算落事、多具体算预测」需人类拍板 |
| 9.8 | **`met` 与「成格」的距离** | `docs/agent_tools.md`：要件命中不代表已成交 | ③ 的「成局」门槛需领域确认 |
| 9.9 | **「岁运引动」算不算预测** | 本规格只要求「引动条件」（`kind + 地址`），不给年份 | 与 T-169 卡 §7「不做应期」的边界需人类确认；v1 取最窄读法 |
| 9.10 | **卡片粒度与最小卡数** | 本规格取「一条边/一个结构项 ≈ 一张卡」，「≥3 张」沿用 T-169 的「≥3 条」 | 一条卡合并多条边是否允许，需确认 |
| 9.11 | **Linter 的实现边界** | 本卡只写判据（§4），不写代码 | 实现归后续卡；不得为通过而放宽 L 表 |
| 9.12 | **原文克向能否补引擎的 `actor=None`** | `M3-R-034`（`theory/raw/ren/r01-r04-theory.md:174`）给了六冲克向（「丑未冲→土冲变虚」），但引擎 `actor=None` | v1 取最窄读法：**不许用原文补引擎缺口**；若外部审计认为可以，需同时规定「原文克向 ≠ 制得住」（L-04） |
| 9.13 | **「破局」能否只靠「原文判据 + edge」** | 婚姻域无结构项（G5），C2 的 `破局` 用 `M1-D-298`（夫妻宫不能被刑坏/冲破）+ `e013/e014` 作依据，`basis.kind=edge` | 这是本规格唯一一处「非结构项」的三态判定，是否算「新增判据」需外部审计拍板；若否，C2 这类卡只能**不成立**（降级为假设，三态里没有第四种） |

## 10 · 非目标

1. **不新增任何命理判据**：不含旺衰分数、格局成败阈值、制死/制净/制不住、救应化解、吉凶方向、应期。
2. **不做预测**：不写年份、年龄、概率、事件；出现即「不可用」（§2.4、§6.2）。
3. **不做评分器**：`confidence` 是证据强度，不是命理置信度。
4. **不改 `engine/**`、不改规则 YAML、不改评测集、不改既有测试。**
5. **不把 `statement` 说成地址版**（A-04）。
6. **不做 golden-20 的策展与盲测**（归 T-170）；本规格只提供卡的格式。
7. **不评价命主**：不写性格评价、健康/财富/事业断语。

## 11 · 复现命令

```bash
# 原局快照（卡快照 dayun_index=null, liunian_year=null）
.venv\Scripts\python.exe -m engine.cli all --birth "1987-12-18 13:15:00" --gender 乾 --json   # C1
.venv\Scripts\python.exe -m engine.cli all --birth "1990-02-23 01:48:00" --gender 坤 --json   # C2
.venv\Scripts\python.exe -m engine.cli all --birth "1982-09-14 23:55:00" --gender 乾 --json   # C3

# 边界警告（all 删空值，必须用 chart）
.venv\Scripts\python.exe -m engine.cli chart --birth "1982-09-14 23:55:00" --gender 乾 --json

# 岁运快照（边号会全量重编号，卡里必须写清快照）
.venv\Scripts\python.exe -m engine.cli all --birth "1987-12-18 13:15:00" --gender 乾 --dayun-index 5 --liunian 2026 --json   # C1 岁运卡
.venv\Scripts\python.exe -m engine.cli all --birth "1990-02-23 01:48:00" --gender 坤 --dayun-index 4 --liunian 2026 --json   # C2 岁运卡
.venv\Scripts\python.exe -m engine.cli all --birth "1982-09-14 23:55:00" --gender 乾 --dayun-index 4 --liunian 2026 --json   # C3 岁运卡

# binzhu / chars / pair_index
.venv\Scripts\python.exe -m engine.cli all --birth "1987-12-18 13:15:00" --gender 乾 --json --full
.venv\Scripts\python.exe -m engine.cli relations --birth "1990-02-23 01:48:00" --gender 坤 --json

# 原文锚点
.venv\Scripts\python.exe -m tools.query_theory --query "宾主 四层" --schools duan --top-k 4 --json
.venv\Scripts\python.exe -m tools.query_theory --query "做功 制用 化用 生泄用 合用 墓用" --schools duan --top-k 5 --json
.venv\Scripts\python.exe -m tools.query_theory --query "夫妻宫 穿 合" --schools duan yang --top-k 5 --json
```

## 12 · 变更记录

| 日期 | 版本 | 变更 |
|---|---|---|
| 2026-10-29 | v1 草案 | 七段工作流 + 5 条地址门槛 + 判定表 + Kill criterion + 3 张真实盘 |
| 2026-10-29 | **v1.1** | 按 `external-audit-adjudication-v2` §1.1/§7：最小单元改为**五元组断语卡**；七段降级为可选报告外壳；新增卡 schema（§3）、Linter 规则 L01–L21（§4）、段↔卡映射（§5.1）、一卡一快照铁律（§1.3）、`suiyun_ten_god` 缺口（§7.3）、待确认 9.9–9.13。3 张盘、判定表四等级、整份三判定、Kill criterion 不变 |
| 2026-10-29 | **v1.2** | T-176 三张 pre-P1 卡暴露 4 处冲突：①standalone 卡 `scene_refs=[]` 可接受；②§2.3 加「破」；③原局卡用 `none_observed`、岁运卡才用 `DY/LN`；④9.13 维持有条件允许。详见 §13 |

## 13 · v1.2 修订（2026-10-29 12:25，中枢）

T-176 三张 pre-P1 卡暴露 4 处规格冲突，裁定如下；**不改变 P1 判据**。

1. **standalone / pre-P1 卡**：`scene_refs` 可为 `[]`，但卡必须 `standalone: true`
   （或顶层 `pre_p1: true`）；这类卡不是报告卡，不受 §5.3「≥3 张」门槛约束；
   报告卡仍要求 `scene_refs ≥2` 且 ≥3 张。
2. **§2.3 加入「破」**：edge 依据的 `assert` 含「目标受破」；`po` 是 `relations.edges` 的边、
   不在 `duan_zuogong.candidates`（A-06），方向仍按 G2 写 `direction_known=false`。
3. **§2.4 与 §3.4 的口径**：原局快照卡（`dayun_index`/`liunian_year` 均 null）的 `activation`
   必须 `none_observed` + 该快照边数证据；岁运卡（有 DY/LN）才用 `kind` + `DY{n}`/`LN{year}`。
   §3.4 示例是岁运卡，不构成冲突。
4. **9.13 维持有条件允许**：婚姻域无 `structure_item` 时，`basis.kind=edge` + 原文结构判据
   （如 `M1-D-298`）可以判「破局」，但必须双锚点、`rescue_judged=未判`、只用于本卡、
   不升级为通用规则。C1/C2 卡成立为**卡级判断**，不作为 P1 证据；
   若外部审计否掉，降级为假设。

# 契约 23 · 断语条件协议 v1（Claim Condition Protocol）

> 状态：`accepted`（已接受）· 2026-10-26
> 上位裁决：[ADR-001](../../docs/adr/ADR-001-engine-agent-boundary.md)、[ADR-003](../../docs/adr/ADR-003-claim-conditions-and-school-routing.md)
> 本契约只定义**断语如何被条件化、如何求值、如何被否决**。它不新增理论、不改生产权重与路由，也不授权任何规则晋升。

---

## 一、范围与硬边界

1. 本契约适用于 A 类盲派候选规则（1658 条）与 B 类生产规则（2041 条）的**条件化改造**。
2. `theory/*/index.yaml` 是自动生成物（文件头 `DO NOT EDIT BY HAND`），**不得手改**。条件化结果写入独立文件 `theory/claims/conditions-v2/<school>.yaml`（以 `rule_id` 为键），由 `tools/build_indexes.py` 在构建期合并为生成物中的 `conditions_v2` 字段；旧 `trigger` / `condition` 字段保留供追溯。
3. 所有条件化断语初始状态一律 `candidate`（候选），晋升须走 [`05-rule-lifecycle.md`](05-rule-lifecycle.md)。
4. 不得把「求值结果为未知」静默当作「不成立」。未知必须显式记录并输出。

---

## 二、三值逻辑（核心）

每个原子谓词（atom）求值只允许三种结果：

| 值 | 含义 | 典型原因 |
|---|---|---|
| `true`（真） | 事实齐备且条件成立 | — |
| `false`（假） | 事实齐备且条件不成立 | — |
| `unknown`（未知） | 事实缺失或口径冲突，无法判断 | 无出生时刻→无大运；边界交节；`profile` 变体分歧 |

组合规则：

```text
all: 任一分量为 false → false；否则任一分量为 unknown → unknown；否则 true
any: 任一分量为 true → true；否则任一分量为 unknown → unknown；否则 false
not: true→false；false→true；unknown→unknown（未知取反仍是未知）
```

**禁止**：把 `unknown` 折叠成 `false`（会误杀），或折叠成 `true`（会误放）。折叠即违约。

---

## 三、条件 IR（中间表示，intermediate representation）

```yaml
conditions_v2:
  preconditions:            # 前置条件：全真才可进入候选
    all:
      - atom: visible_god
        args: {god: 正官, at: [M.s, Y.s]}
      - atom: edge
        args: {type: 穿, between: [Y.b, D.b]}
      - not:
          atom: kongwang
          args: {at: D.b}
  invalidators:             # 失效条件：任一为真即撤销本条
    any:
      - atom: edge
        args: {type: 六合, between: [M.s, D.s]}
  counter_conditions:       # 反条件：为真则降权，不撤销
    any:
      - atom: camp_count
        args: {side: 印, op: gte, value: 3}
  bindings:                 # 需要回填的地址变量，供报告引用
    subject: D.s
    object: M.s
  time_window: natal | dayun | liunian | any
  framework_dependency: standalone | requires_school_frame | requires_pair
  pair_with: [M1-D-045]      # requires_pair 时必填：配对断语 ID
  source_ref: {path: theory/raw/ren/r21-r26-theory.md, line: 171}
  falsifier: 若 XX 年出现该事但前置条件实际不成立，则本条编译有误
```

字段约束：

| 字段 | 必填 | 说明 |
|---|---|---|
| `preconditions` | 是 | 至少 1 个原子 |
| `invalidators` | 是 | 允许为空树（`any: []` 视为「无失效条件」，需在评审中说明理由） |
| `counter_conditions` | 否 | 只影响排序与置信度 |
| `framework_dependency` | 是 | 缺省视为 `requires_school_frame`（保守默认） |
| `source_ref` | 是 | 必须能定位到原稿行号 |
| `falsifier` | 是 | 一句话，可事后核对 |

---

## 四、原子谓词表 v1（46 个，`v1.2`）

> 全部原子只能读 [`engine.facts`](../../engine/facts/) 已产出的字段；不得自行计算新事实。
> 缺字段时返回 `unknown`，不得猜测。
>
> **岁运隔离（ADR-007 D3，v1.1）**：`edge` / `edge_touches` / `chong_at` / `he_at` /
> `chuan_at` / `xing_at` / `po_at` / `group_complete` / `muku_open` **默认只扫
> `scope == "natal"` 的关系边**。`relation_graph._nodes()` 一旦带 `dayun_index` /
> `liunian_year` 就会产出 `DY{n}.*` / `LN{year}.*` 节点与 `scope ∈ {dayun, liunian,
> dayun+liunian}` 的边；不过滤就会让原局静态断语被流年干支错误点燃。需要岁运边时用
> `edge(scope="dayun" | "liunian" | "dayun+liunian" | "any")` 显式查询。

### 4.1 位置与透藏（8）

| 原子 | 参数 | 语义 | 缺字段时 |
|---|---|---|---|
| `visible_god` | `god`, `at?` | 某十神透于指定柱干（缺省＝任一干） | unknown |
| `hidden_god` | `god`, `at?`, `qi?` | 某十神藏于地支（可限定本/中/余气） | unknown |
| `stem_is` | `at`, `gan` | 指定柱天干为某字 | unknown |
| `branch_is` | `at`, `zhi` | 指定柱地支为某字 | unknown |
| `sits_on` | `god`, `zhi` | 某十神坐某支 | unknown |
| `palace_holds` | `god`, `palace` | 宫位十神（年/月/日/时） | unknown |
| `rooted` | `god`, `min_qi?` | 某十神通根（可限定最低气级） | unknown |
| `day_master` | `gan` | 日主为某干 | unknown |

### 4.2 关系（10，全部引用关系边 ID）

| 原子 | 参数 | 语义 |
|---|---|---|
| `edge` | `type`, `between?`, `scope?` | 存在指定类型关系边（合/冲/刑/穿/破/害/三合/三会/暗合/克/生）；`scope` 缺省 `natal`，可传 `dayun` / `liunian` / `dayun+liunian` / `any` |
| `edge_touches` | `type`, `at` | 某地址被指定类型关系边触及（原局边） |
| `chong_at` | `at` | 某地址被冲（原局边） |
| `he_at` | `at`, `with_god?`, `exclude_god?` | 某地址被合：**只认六合 `liuhe` 与地支暗合 `zhi_anhe`**（见下） |
| `chuan_at` | `at` | 某地址被穿（原局边） |
| `xing_at` | `at` | 某地址被刑（原局边） |
| `po_at` | `at` | 某地址被破（原局边） |
| `group_complete` | `type` | 三合/三会成局完整（原局边） |
| `distance_leq` | `a`, `b`, `n` | 两地址间距 ≤ n |
| `same_pillar` | `a`, `b` | 两地址同柱 |

#### 4.2.1 `he_at` 的合口径（v1.1 收窄）

v1.0 把 `wuhe` / `sanhe` / `sanhui` / `ganzhi_zihe` 一律算「被合」，导致 `he_at(D.b)` 在
481 盘上命中 412 盘（85.7%）——一张盘只要挂着半三合或半三会就算「夫妻宫被合」，断语几乎
没有区分度。v1.1 按原文收窄：

| 边 | 是否算被合 | 依据 |
|---|---|---|
| `liuhe`（地支六合） | ✅ | `sources/duan/MinerU_markdown_婚姻专辑_2056044010230448128.md:48`「或六合，暗合他星」 |
| `zhi_anhe`（地支暗合） | ✅ | 同上「暗合他星」 |
| `sanhe` / `sanhui` 的 `completeness ∈ {partial, half_sheng, half_mu, gong}` | ❌ | 半局/拱局不是「合」；原文只举六合与暗合 |
| `sanhe` / `sanhui` 的 `completeness == "full"` | ❌（待裁定） | 原文无据；**待中枢裁定**是否算「被合」。需要完整局时用 `group_complete` |
| `ganzhi_zihe`（日柱自合） | ❌ | 自合不涉他星，与「合他星」相反 |
| `wuhe`（天干五合） | ❌ | 原文「男命天干合财、女命天干合官」是婚姻**信息**，不是「宫被合」判据 |

`exclude_god`：排除「合它的是该十神」的边（例如排除配偶星本星相合），缺省不启用。

### 4.3 状态与力量（9）

| 原子 | 参数 | 语义 |
|---|---|---|
| `kongwang` | `at` | 某地址落空亡 |
| `muku_present` | `zhi?` | 盘中有墓库（可指定地支） |
| `muku_open` | `zhi` | 某墓库被冲开 |
| `ru_mu` | `at`, `muku` | 某字入某墓 |
| `siling` | `god?` | 人元司令为某十神（可空＝任取） |
| `camp_count` | `side`, `op`, `value` | 阵营计数比较（印/比/食伤/财/官杀） |
| `de_ling` | `god` | 某十神得令 |
| `tiaohou_at` | `char` | 调候字在盘中（含出处） |
| `shensha` | `name`, `at?` | 神煞命中（须带口径，不得孤证主审） |

### 4.4 结构与做功（7）

| 原子 | 参数 | 语义 |
|---|---|---|
| `geju_met` | `geju_type?` | 格局要件满足（`structures.status == met`） |
| `geju_state` | `state` | 格局状态为 met / unmet / not_evaluable / needs_judgment |
| `zuogong` | `kind` | 做功候选类型（制/化/生泄/合/墓） |
| `tiyong` | `role` | 体用判定结果（体/用） |
| `binzhu` | `layer`, `side?`, `at?` | 宾主层级（1–4）：某地址在该层为主/为宾 |
| `structure_break` | `check` | 破格检查命中 |
| `structure_rescue` | `check` | 救应检查命中 |

> v1.1 起 `binzhu` 真正读事实（v1.0 恒返回 `unknown("facts 未提供宾主层级")`，是空壳）。
> 事实来源有二，同一 SSOT：① 做功候选自带的 `binzhu` 读数（`structure_check._binzhu()`
> 产出的 `layer / sides / direction`）；② 候选未覆盖该地址时回落到事实层纯位置函数
> `chart_facts.binzhu_side(addr, layer)`。第 4 层「原局为主、岁运为宾」需要岁运节点；
> 本次输入未提供岁运时，`side="宾"` 判 `false` 并注明「无岁运节点」。

### 4.5 岁运（6，v1.2 起全部实装）

| 原子 | 参数 | 语义 | 缺字段时 |
|---|---|---|---|
| `dayun_present` | — | 有大运信息 | false（这是事实，不是未知） |
| `liunian_present` | `year?` | 有指定流年 | false |
| `suiyun_edge` | `type`, `at`, `scope?` | 某地址在岁运层构成指定关系；`scope` 精确限定 `dayun`/`liunian`/`dayun+liunian`，命中绑定 `edge_id` + `scope` | unknown「未提供大运/流年上下文」 |
| `sanhe_with_suiyun` | `zhi_set?` | 岁运与原局共同构成**完整**三合/三会（`completeness == "full"`）；`zhi_set` 限定必须包含的支 | unknown（同上） |
| `chong_kai_muku` | `zhi?`, `year?` | 原局墓库被 `scope ∈ {dayun, liunian}` 且 `kind ∈ {chong, xing}` 的边冲开；`year` 限定触发流年 | unknown（同上） |
| `suiyun_arrives` | `at`, `via?` | 段派「到位」：`通禄`（原局天干在运年地支见禄）/ `原身`（原局地支所藏之干在运年天干透出）；`via` 缺省按地址层级自动选 | unknown（同上） |

> **与 §4 开头的镜像关系**：§4 的关系原子被隔离在 `scope == "natal"`，岁运原子则**只扫
> `scope != "natal"`**，两者不交叉。岁运边由 `relation_graph._nodes(chart, dayun_index,
> liunian_year)` 产出，原子层不重造；未指定 `dayun_index` 时不会有大运边，因此
> 「排得出大运」不等于「提供了大运上下文」——`dayun_present` 答前者，`suiyun_edge` 答后者。
>
> `suiyun_arrives` 的原文边界（`theory/raw/duan/d01-deep-read.md:287`，M1-D-042）：
> 「如运中出现八字中的字就为八字中的字到了，反客为主了。有两种方式：一为通禄，二为现原身。」
> 原身表按 D-02 M1-D-058 `related_table`（甲↔寅 / 乙↔卯 / 丙戊↔巳 / 丁己↔午 / 庚↔申 /
> 辛↔酉 / 壬↔亥 / 癸↔子）实现，即禄表的逆映射；**辰戌丑未无原身**（同条 `falsifiable_by`），
> 此 4 支判 `false` 并在 note 说明，不补造土支原身。M1-D-059 的「遁藏透干」（原局地支任一藏干
> 透于运年天干）是更宽的独立规则，本版本**未实现**，只在 `原身` 范围内作答。

### 4.6 元谓词（3）

| 原子 | 参数 | 语义 |
|---|---|---|
| `count` | `atom`, `op`, `value` | 满足某原子的数量比较 |
| `exists` | `atom` | 至少一处满足 |
| `cite` | `claim_id` | 引用另一条命题的裁决结果（用于 `requires_pair`） |

### 4.7 禄与显式未知（2，v1.1 新增）

| 原子 | 参数 | 语义 | 缺字段时 |
|---|---|---|---|
| `lu_at` | `gan?`, `at?` | 某天干的**禄支**是否落在指定（缺省＝任一）地支上；命中绑定该地支地址 | unknown（无日主且未给 `gan`） |
| `needs_judgment` | `reason` | **恒返回 unknown**，`reason` 必填，写明缺哪一步判断 | 恒 unknown |

新增理由（登记于 §九）：

- `lu_at`：禄（甲禄寅、乙禄卯、丙戊禄巳、丁己禄午、庚禄申、辛禄酉、壬禄亥、癸禄子）
  早已在事实层 `chart_facts._LU`，但原子表里没有对应谓词，导致「人生三宝印食禄」这类
  断语只能标 `needs_human`。禄表从事实层导入，不在原子层另造。
- `needs_judgment`：ADR-007 D12 判定「未知率 0.0」是**设计失效**——pilot 把不会算的
  子条件删进 `unmapped_prose` 再标 `compiled`，未知率恒为 0。有此原子后，未量化的子条件
  必须显式挂在条件树里：
  `False AND Unknown = False` → `rejected`（过滤不相关盘）；
  `True AND Unknown = Unknown` → `needs_fact`（推给 Agent 裁决）。
  **凡含未量化子条件的断语，禁止删条件冒充 `compiled`。**

### 4.8 力量比较（1，v1.2 新增）

| 原子 | 参数 | 语义 | 缺字段时 |
|---|---|---|---|
| `can_control` | `actor`, `target` | 段派核心判据「制得住 / 制不住」：三值 `True` 制得住 / `False` 制不住 / `unknown` 力量相当不可裁。参数可写地址（`"M.b"`）或单字干支（`"亥"`）；命中绑定 `actor_addr` / `target_addr` | unknown（无法定位地址 / 五行计数缺失） |

原文依据（`sources/duan/MinerU_markdown_22.盲派初级命理学_2056045493286002688.md`）：

- `:1762`「冲神之旺衰判断，**以多则为旺，寡则为衰；以合局会局为旺，以孤立受克为衰；
  以得令为旺，以失令为衰**。」→ 旺项 = {得令, 多, 合局会局}，衰项 = {失令, 寡, 孤立受克}。
- `:1812`「戌辰**力量相当，互相制不了**」/ `:1824`「原局金水党和火土党对抗，**谁也制不了谁**」（任务卡 T-145 原引 :1844 / :1850 有偏差，此处取实测行号）
  → 双方各有旺项时，`unknown` 不是算不出来，而是原文的结论。
- 六党对（`MinerU_22:426`「木火可以一党，金水可以一党，水木可以一党；火与燥土可以为一党，
  金与湿土可以为一党，水与湿土也可以为一党」）与党→所制（`:428`）→ 党势并入「多」这一项，
  不单独作第四条判据；跨五行的六党对聚合本版本未实现（见 T-145 BRIEF「未实现」）。

判定规则（ADR-007 D4）：

| 结果 | 条件 |
|---|---|
| `True` | `actor` 旺项 ≥ 2，`target` 旺项 = 0 且衰项 ≥ 1 |
| `False` | `target` 旺项 ≥ 2，`actor` 旺项 = 0 且衰项 ≥ 1 |
| `unknown` | 其余全部情形（双方均有根气 / 两党对抗 / 力量相当） |

`note` 恒附双方旺项与衰项明细（如 `制者 水（…）旺项[得令、多(5字)]衰项[无]`），
承接 `structure_check.py:255 strength_judgment` 的代码铁律「力量对比不由代码裁决」——
本原子只在极端清晰盘面裁真伪，其余交 Agent 结合命主问题裁决。

> ⚠ `DUO_MIN = 3`（多）、`GUA_MAX = 1`（寡）、`STRONG_MIN = 2`（旺项门槛）均为**工程取值**，
> 原文只说「多 / 寡 / 得令 / 失令」而未给数。三者集中在 `atoms.py` 顶部常量，
> 改动必须同时更新 T-145 BRIEF 的「工程取值 vs 原文数值」清单。

---

## 五、求值输出（机器可读）

```json
{
  "claim_id": "M1-D-247",
  "state": "candidate | needs_fact | rejected",
  "value": true,
  "bindings": {"subject": "M.s", "object": "Y.b", "edges": ["e012"]},
  "failed_atoms": [],
  "unknown_facts": ["dayun.current"],
  "near_miss": ["edge(穿, [Y.b,D.b]) 未成立"],
  "framework_check": {"dependency": "requires_school_frame", "frame_claim": "M1-D-005", "verdict": "pass"}
}
```

`state` 判定顺序：

```text
invalidators 任一为真        → rejected（撤销，记原因）
preconditions 任一为 false   → rejected（不成立）
preconditions 含 unknown     → needs_fact（缺事实，不出口）
框架前置不成立               → evidence_only（降级为旁证）
全部为真                     → candidate（进入裁决）
```

`near_miss`（差一条件）必须输出：它是「规则边界」的直接证据，供人工复核与反馈归因使用。

---

## 六、框架依赖的执行（L3 结构合法性）

| 类别 | L3 检查 | 不通过时 |
|---|---|---|
| `standalone` | 仅检查自身 `preconditions` | rejected |
| `requires_school_frame` | 同派 frame 命题存在且 `verdict == pass`；该派 L1 角色为 `lead`/`co_lead` | `unknown` → 降为 `evidence_only`，不得进 L4 |
| `requires_pair` | `pair_with` 指向的断语已求值为 `candidate` | rejected |

`frame`（框架）命题的认定：由各派在 L2 显式产出的结构判定，例如段派体用判定、子平格局成败、滴天髓气势判定、任派原局结构成立、杨派宫位与星位判定。

### 6.1 硬否决只对 `false`；`unknown` 必须透传

- **硬否决（rejected）** 只允许两种依据：某个前置条件求值为 `false`，或 ADR-002 的四条一票否决。
- 求值为 `unknown` 时**不得丢弃**：输出 `needs_fact`（缺事实）或 `evidence_only`（框架未定），并携带 `unknown_facts` / `framework.frame_claim`，交 Agent 在全盘语境下裁决。
- 依据：静默丢弃未知，等于引擎替 Agent 做了单点定局，违反 ADR-001。

### 6.2 分层求值（Pass 0 / 1 / 2，禁止跨层引用）

```text
Pass 0  原子层：只跑 46 个基础原子，得真值表（无流派偏好）
Pass 1  定局层：frame 准入条件只允许引用 Pass 0 的原子结果，产出 active_frames
Pass 2  断语层：只对 active_frames 内的断语求值 conditions_v2
```

禁止：`frame_atom` 内出现 `cite`，或引用任何 `requires_school_frame` 的断语——否则会形成「求 F 需先求 C，求 C 需先授权 F」的循环。求值图因此被限制为深度 2 的 DAG（有向无环图）。

### 6.3 已识别但尚未实现的表达缺口

| 缺口 | 例子 | 现状 |
|---|---|---|
| 相对强弱比较 `compare($x,$y,metric)` | 「财轻劫重」「杀旺身弱」 | 未实现；pilot 用计数阈值代理，属设计取值 |
| 集合基数 | 「满盘官杀无制」「刑冲多见」 | `count` 只支持「某原子在 8 个地址上的命中数」，不支持任意模式 |
| 例外 / 解救 | 「逢冲本凶，得合则解」 | 部分由 `invalidators` 覆盖；尚无优先级消解算子 |
| 时间轴作用域 | 「原局有象，行运方发」 | `suiyun_edge` 等 3 个原子在 pilot 恒为 `unknown` |

---

## 七、编译三态（不允许猜）

| 状态 | 含义 | 处理 |
|---|---|---|
| `compiled`（已编译） | 条件树可求值，且原文支持 | 进入求值 |
| `uncompilable`（不可编译） | 现有原子表无法表达 | 记缺口清单，不生成条件 |
| `needs_human`（需人工确认） | 可编译但语义存疑（否定词、多重前提、含混措辞） | 挂起，交命理师确认 |

统计口径：`可编译率 = compiled / 总数`；不可编译与需人工确认都必须出现在批次报告中，不得隐藏。

---

## 八、验收指标（每批）

| # | 指标 | 定义 | 门槛 |
|---|---|---|---|
| 1 | 可求值率 | 输出 `true/false` 的比例（不含 `unknown`） | 100% 的断语至少能在完整事实盘上给出确定值 |
| 2 | 地址绑定率 | 至少 1 个地址或关系边绑定的比例 | ≥90% |
| 3 | 区分度 | 固定 20 张盘上通过集合的种类数；单条开火率 | ≥12 种；开火率 5%–95% |
| 4 | 语义支持率 | 独立抽样 20 条，原文确实支持编译条件 | ≥90% |
| 5 | 未知显性率 | `unknown` 被显式记录而非静默折叠的比例 | 100% |

---

## 九、版本与变更

- 原子表版本：`v1.2`；新增/修改原子必须更新本契约并登记变更原因。
- 条件字段版本：`conditions_v2`；独立文件 `theory/claims/conditions-v2/<school>.yaml` 是**唯一事实源**，生成物中的 `conditions_v2` 字段不得手改；旧 `trigger`/`condition` 字段保留，不再写入新值。
- 任何批量条件化必须记录到 `META/rule-changelog.md`，并附批次报告路径。

### 9.1 变更登记

| 日期 | 版本 | 变更 | 依据 |
|---|---|---|---|
| 2026-10-26 | v1-draft | 42 个原子首次成表 | ADR-001 / ADR-003 |
| 2026-10-27 | v1.1 | 原子表 42 → 44：新增 `lu_at`（禄）、`needs_judgment`（显式未知占位） | 本文 §4.7；ADR-007 D3 / D12；任务卡 T-142 |
| 2026-10-27 | v1.1 | 关系原子默认只扫 `scope == "natal"` 的边；`edge` 增 `scope?` | ADR-007 D3「必须先加原局隔离，否则污染」 |
| 2026-10-27 | v1.1 | `he_at` 收窄为六合 / 地支暗合，排除半局拱局、完整局（待裁定）、日柱自合、天干五合；增 `exclude_god?` | §4.2.1；`sources/duan/MinerU_markdown_婚姻专辑_2056044010230448128.md:48` |
| 2026-10-27 | v1.1 | `binzhu` 由恒 `unknown` 改为读事实；增 `side?` / `at?` | ADR-007 D5；`chart_facts.binzhu_side` / `structure_check._binzhu` |
| 2026-10-27 | v1.2 | 原子表 44 → 46：新增 `suiyun_arrives`（到位）、`can_control`（三值力量比较） | §4.5 / §4.8；ADR-007 D3 / D4；任务卡 T-145 |
| 2026-10-27 | v1.2 | 3 个空壳岁运原子实装：`suiyun_edge` / `sanhe_with_suiyun` / `chong_kai_muku` 由恒 `unknown` 改为消费 `scope != natal` 的边；`suiyun_edge` 的 `layer?` 换为 `scope?`，`sanhe_with_suiyun.zhi_set` 改可选，`chong_kai_muku` 增 `zhi?` | §4.5；`relation_graph.py:85 _nodes()`；MinerU_22 :1762 / :1812 / :1824 |
| 2026-10-27 | v1.2 | `liunian_present` 改从岁运节点反推年份（`facts.chart.cycles.liunian` 恒为 null，旧实现永假） | §4.5；T-142 BRIEF 遗留项 |
| 2026-10-27 | v1.1 | `ir._label()` 支持 `all` / `any` / `not` 组合节点递归输出（原实现只认 `atom`，失败时给出 `?()`） | ADR-007 D12「人无法追责到具体子条件」 |

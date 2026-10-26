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

## 四、原子谓词表 v1（42 个，`v1-draft`）

> 全部原子只能读 [`engine.facts`](../../engine/facts/) 已产出的字段；不得自行计算新事实。
> 缺字段时返回 `unknown`，不得猜测。

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
| `edge` | `type`, `between?`, `scope?` | 存在指定类型关系边（合/冲/刑/穿/破/害/三合/三会/暗合/克/生） |
| `edge_touches` | `type`, `at` | 某地址被指定类型关系边触及 |
| `chong_at` | `at` | 某地址被冲 |
| `he_at` | `at`, `with_god?` | 某地址被合（可限定合的是哪个十神） |
| `chuan_at` | `at` | 某地址被穿 |
| `xing_at` | `at` | 某地址被刑 |
| `po_at` | `at` | 某地址被破 |
| `group_complete` | `type` | 三合/三会成局完整 |
| `distance_leq` | `a`, `b`, `n` | 两地址间距 ≤ n |
| `same_pillar` | `a`, `b` | 两地址同柱 |

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
| `binzhu` | `layer` | 宾主层级（1–4） |
| `structure_break` | `check` | 破格检查命中 |
| `structure_rescue` | `check` | 救应检查命中 |

### 4.5 岁运（5）

| 原子 | 参数 | 语义 | 缺字段时 |
|---|---|---|---|
| `dayun_present` | — | 有大运信息 | false（这是事实，不是未知） |
| `liunian_present` | `year?` | 有指定流年 | false |
| `suiyun_edge` | `type`, `at`, `layer?` | 岁运与某地址构成关系 | unknown |
| `sanhe_with_suiyun` | `zhi_set` | 岁运与原局成三合 | unknown |
| `chong_kai_muku` | `year?` | 流年冲开墓库 | unknown |

### 4.6 元谓词（3）

| 原子 | 参数 | 语义 |
|---|---|---|
| `count` | `atom`, `op`, `value` | 满足某原子的数量比较 |
| `exists` | `atom` | 至少一处满足 |
| `cite` | `claim_id` | 引用另一条命题的裁决结果（用于 `requires_pair`） |

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
Pass 0  原子层：只跑 42 个基础原子，得真值表（无流派偏好）
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

- 原子表版本：`v1-draft`；新增/修改原子必须更新本契约并登记变更原因。
- 条件字段版本：`conditions_v2`；独立文件 `theory/claims/conditions-v2/<school>.yaml` 是**唯一事实源**，生成物中的 `conditions_v2` 字段不得手改；旧 `trigger`/`condition` 字段保留，不再写入新值。
- 任何批量条件化必须记录到 `META/rule-changelog.md`，并附批次报告路径。

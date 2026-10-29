# T-184 BRIEF · 党势方向预注册 + needs_judgment / mutual schema

- 状态：✅ **交付待验收**（只写规格；未写代码、未跑盘、未改 engine / hold-out / answers / 测试；无 git 写操作）
- 分支：`main`（主检出，未 commit；本卡不产生分支）
- 一句话：把段派「一方之党一定要大于另一方之党」写成**只用整序数、只允许严格大于**的预注册——
  计数口径（A 天干 / B 地支本气 / C 中余气同字透干 / D 得令）先写死，打平一律 `needs_judgment`，
  穿制因原文内部冲突一律 `needs_judgment`，刑默认 `mutual`；正文 sha256 已写入 prereg JSON，**hash 后正文未再改**。

---

## 1 · 改动文件

| 文件 | 类型 | 内容 |
|---|---|---|
| `docs/specs/party-direction-v1.md` | **新建**（588 行 / 37,767 B） | 规则正文：§1 冻结纪律、§2 计数口径（A–D + 党映射 + 得令 + 邻隔同柱 + Δ 判定 + 回执 + 合成算例 V1a/V1b）、§3 R1–R7 逐类规则（含 H02 落点）、§4 断言 schema、§5 下游接口、§6 覆盖矩阵与 H05 落点、§7 禁止项 15 条、§8 已知缺口 G1–G8、§9 变更流程、§10 自检表 |
| `META/party-direction-prereg-v1.json` | **新建**（390 行 / 28,474 B） | `spec_sha256` / `spec_bytes` / `frozen_at`、35 条 `source_refs`（path + line + 逐字 quote + role）、`counting_rubric`（机读口径 + 回执不变量 + 自测算例）、9 条 `party_direction_rules`、`assertion_schema`、2 条 `validation_instances`、15 条 `forbidden`、6 条 `freeze_discipline`、8 条 `known_gaps` |
| `tasks/T-184/BRIEF.md` | **新建** | 本文件 |
| `tasks/T-184/STATUS.md` | **更新** | 状态 + 执行日志 + 交付哈希 + Blockers |

**未改**：`engine/**`、`META/p1-holdout-answers-v1.json`、`META/p1-holdout-freeze-v*.json`、`META/p1-holdout-*.json`（baseline 的 `M` 是进入本卡前既有的脏文件，mtime `14:02:40`，早于本会话）、`tests/**`、`docs/specs/actor-rules-v1.md`、`tasks/T-184/PROMPT.md`。

**未碰**：`dev-20`、`fresh-40`（`META/p1-fresh-40-*` 是 T-185 并发 Worker 的新建文件，非本卡产生）。

---

## 2 · 原始输出

### 2.1 哈希（最终值）

```text
docs/specs/party-direction-v1.md
  sha256 = 922ede83d9f3af340162edf39ed924f2959c23fab5f682934189bb02523cbc2c
  bytes  = 37767
  lines  = 588

META/party-direction-prereg-v1.json
  sha256 = 243f80ba05b3a2c3eddbec7afe28499d00dd9b1ce55b8d7e34e67b0a35dd36e7
  bytes  = 28474
  lines  = 390
```

JSON 内 `spec_sha256` / `spec_bytes` 与上表一致；重算 md 哈希两次均相同（见 §2.5）。

### 2.2 逐字引用校验（0 miss）

校验脚本写在 `%TEMP%`（`dsh-t184-verify.py`，只依赖标准库，未写入仓库——卡面禁止写代码）：
读 JSON `source_refs` 的 `path:line` + `quote`，逐条检查 quote 是否是该行的**子串**；
再解析 md 正文里全部 `` `alias:Lnnn`「quote」 `` 内联引用，按别名表展开后做同样检查；
另校验 md sha256/字节数、JSON 无浮点对象、自测算例求和。

```text
$ .venv\Scripts\python.exe %TEMP%\dsh-t184-verify.py
checks_ok=83 fails=0 inline_quotes=30
spec_sha256=922ede83d9f3af340162edf39ed924f2959c23fab5f682934189bb02523cbc2c
json_sha256=243f80ba05b3a2c3eddbec7afe28499d00dd9b1ce55b8d7e34e67b0a35dd36e7
[exit code: 0]
```

- 结构化 `source_refs` 35 条：**35/35 命中**；
- md 内联引用 30 处：**30/30 命中**；
- 合计 65 处逐字引用，**0 miss**。
- 校验期间发现并修正 2 处引用错误（见 §2.6），修正后才重新冻结 hash；冻结后未再改正文。

### 2.3 整数 / 比值 / 权重扫描

| 检查 | 结果 |
|---|---|
| JSON 里是否存在浮点对象 | **0**（Python `walk` 断言 `isinstance(float)` 失败即报错） |
| 是否有 `%` | **0**（md + JSON） |
| `\d+\.\d+` 命中 | md 66 / JSON 12：全部是章节号（`§2.2`、`§3.4.1`）或书名文件名（`22.盲派…`、`26..段建业…`），**无一个数值字段** |
| `\d+:\d+` 命中 | md 2 处、JSON 4 处：md 2 处都在「禁止比值」条内（`4:1`、`5:2` 作为被禁对象列举）；JSON 4 处是 `frozen_at` 时区 `+08:00`、`d01:251-260`、`d01:236:` 这类引用，**无一条作判据** |
| `"weight" / "ratio" / "score" / "percent"` 键名 | **0**；JSON 内仅 `forbidden` 数组有 `"ratios: 4:1, 5:2, percentages, multiples"` 与 `"weights: …"` 两条**禁止项**文本 |

### 2.4 合成算例复核（V1a / V1b）

| 变体 | 天干 | B（4 支固定） | C | D | 合计 | 判定 |
|---|---|---|---|---|---|---|
| V1a | 甲 戊 辛 壬 | 子W 午F 辰W 戌F | 戌藏辛同字透 → W | 午月 → F | **F=4 / W=5 / Δ=−1** | 金水党严格大于 |
| V1b | 甲 戊 庚 壬 | 同上 | 无（庚不使辛透、壬不使癸透） | 午月 → F | **F=4 / W=4 / Δ=0** | `needs_judgment` |

判别点：若把「透干」误做成「同五行」，V1a 的 `壬` 会让 `辰` 藏的 `癸` 透出，W 变 6、Δ 变 −2；
本规格取**同字**，故 W=5。脚本两变体求和与 `delta` 全部通过。

### 2.5 两次运行一致

```text
run1: checks_ok=83 fails=0 inline_quotes=30
      spec_sha256=922ede83…c2c   json_sha256=243f80ba…367
run2: checks_ok=83 fails=0 inline_quotes=30
      spec_sha256=922ede83…c2c   json_sha256=243f80ba…367
```

md / JSON 均为纯文本、无时间戳随机源、字段顺序固定；两次独立进程重算一致。

### 2.6 校验期修正记录（在冻结之前）

| # | 问题 | 修正 |
|---|---|---|
| 1 | `S13`「制官杀不干净」误记在 `22:L2179`，实为 **`23:L2179`** | JSON `S13.path` 改 `23`；md §3.6 与 §6.1 的三处 `22:L2179` 改 `23:L2179`，别名表补 `23` |
| 2 | md §2.4 表格用「木火可以一党……」带省略号，逐字校验失败 | 改为「木火可以一党」，与原文逐字一致 |

修正后重算 md sha256（`31191717…` → `922ede83…`），JSON 的 `spec_sha256` / `spec_bytes` 同步改写；**此后正文未再改动**。

### 2.7 git / 工作区

```text
$ git -C "E:\Git hub\mangpai-fusion" branch --show-current
main

$ git status --short
 M META/p1-holdout-baseline-v1.json      ← 进入本卡前既有（mtime 14:02:40），非本卡
 M META/p1-holdout-baseline-v1.md        ← 同上
?? META/p1-fresh-40-answers-v1.json      ← T-185 并发产物，非本卡
?? META/p1-fresh-40-v1.json              ← 同上
?? META/party-direction-prereg-v1.json   ← 本卡
?? docs/specs/party-direction-v1.md      ← 本卡
?? mangpai-fusion-offline-04677d2c.zip   ← 非本卡
```

无 `git add` / `commit` / `push` / `checkout` / `stash` / `reset`。

**未跑 `pytest`**：本卡零代码、零测试改动，规格验收由中枢按 §10 自检表逐条核；跑全量只会验证与本卡无关的既有代码。
**未跑 `engine.cli`**：卡面「不跑盘」；本规格刻意不含任何真实盘的 `n_F/n_W`（预写即等于提前跑盘）。

---

## 3 · 未完成与风险

### 3.1 未做（按卡）

1. **未实现**党势计数、`party` 回执、`needs_judgment` 输出——卡面禁止写代码；规格已写到可直接实现的程度（§2.2 伪代码式口径 + §2.8 回执不变量 + 合成算例）。
2. **未跑任何盘**，包括 H02/H05；H05 的 `n_F/n_W` 必须由实现现算（§6.3）。
3. **未改 answers / freeze / baseline / scorer**：H02 答案层 `a=酉、actor=酉` 保持；预注册层判 `needs_judgment`（§3.4.1）。

### 3.2 风险

| # | 风险 | 说明 / 缓解 |
|---|---|---|
| R1 | **H05 可能判 `needs_judgment`** | R1 只看整数 Δ；若 Δ=0，预注册层记 `needs_judgment`，**不得**为让 H05 变绿改映射或改边界。三种落点都已写进 §6.3。 |
| R2 | **H02 与答案层不同向** | 这是设计：答案层记句法施力方，预注册层判「穿制是否成立」。评分器必须新增 `needs_judgment` 枚举，否则会被误记 `reversed`。 |
| R3 | **穿制冲突未消解** | `21:L2425`「唯有穿制不了」 vs `21:L3717`「穿也为制了」 vs `22:L2980`「都可以相制」；本规格按卡判 `needs_judgment`，并写明「很强大的力量」不可整数化（G5）。若中枢要赋向，须新卡。 |
| R4 | **二元党简化** | 木固定归 F，原文「水木一党」未实现（G1）；土重的盘党数偏小（G7）。都是**已声明**的代价，不是隐藏假设。 |
| R5 | **`22:L430` 默认方向未采用** | 「辰戌一般戌被辰制」与 `22:L1812`「力量相当互相制不了」冲突，且会绕过严格大于；记录在 G3，采用须新卡。 |
| R6 | **`state=成` 依赖标注人** | 已用 `state_evidence`（必须是 quote 子串）+ 双人复核约束（G8）；本卡不替标注人判任何真实盘的 `state`。 |
| R7 | 并发写 | T-183 / T-185 同时在跑；本卡只新建 2 个文件 + 改 `STATUS.md`，与它们无文件交集。 |

### 3.3 Blockers

**无 Blockers。** 规格可交付、可实施；未发现卡面自相矛盾。
唯一需要中枢拍板的口径问题：**H05 若落到 Δ=0**，是否接受 `needs_judgment` 进主口径（§6.3 已给三选一，默认按预注册如实记）。
建议：接受，并把 `needs_judgment` 单列，不计入 ok/reversed。

---

## 4 · 下游须知

1. **冻结已生效**：`META/party-direction-prereg-v1.json` 的 `spec_sha256` = 正文哈希。
   **任何盘只能在这次 hash 之后跑**；跑完不得回改 `docs/specs/party-direction-v1.md`。要改只能新建 v2。
2. **实现入口**（下一张实现卡）：
   - 产出 §2.8 的 `party` 回执（`fire/water/delta/items/excluded`），必须能逐项重算；
   - 只对 R1 / R2 / R3 / R5 丑戌 计算党势；其余关系不读 `n_F/n_W`；
   - `needs_judgment` 必须是**独立输出**，不得降级成 `actor=null` 后被下游当「无关系」。
3. **评分器**：新增 `needs_judgment` 结果枚举；不得记成 `ok` / `reversed` / `no_candidate`；
   `needs_judgment` 是否进分母须另卡预注册（本规格不规定分母）。
4. **H02**：`PD-H02-01` = `direction=needs_judgment`、`state=needs_judgment`、`basis=source_text`、
   `syntax_subject=actor`、`source_ref=22:L2252`、`quote=戌酉穿， 羊刃穿了官杀库`、`edge=e013`。
   答案层 `actor=酉` **不改**。
5. **H05**：属 R1；计数现算，三种落点（同向 / 打平 / 反向）都合法，反向时如实记录、不调规则。
6. **不要**把本规格的 `state` 当「整盘成败」——它只表示「所引句所述结果是否成立」（§4.5）。
7. **不要**把 `party` 计数写进 `strength` / `can_control`（§5.1 第 3 条、§7 第 15 条）。

---

## 5 · 中枢直接核（对应规格 §10）

| 卡面验收项 | 看哪里 | 现场命令 / 判据 |
|---|---|---|
| 计数口径可复现、无浮点/比值/权重 | 规格 §2、JSON `counting_rubric` | 重算 md sha256 = JSON `spec_sha256`；JSON 无 float 对象；§2.4 扫描 |
| 每条规则有 `source_ref` + 正例 + 反例 | 规格 §3.1–3.7、§6.1 | 35 条 `source_refs` 全命中（§2.2） |
| H02 明确 `needs_judgment` | 规格 §3.4.1、§6.2；JSON `validation_instances[0]` | `direction=needs_judgment` |
| 刑有 `mutual` | 规格 §3.5、§6.1 R5 | `direction=mutual` + `mutual=true` |
| 规格 hash 写入 JSON、hash 后未改 | JSON `spec_sha256` | `Get-FileHash` 重算一致 |

# T-181 BRIEF · 化用候选方向修复（只翻 mode=化用）

- 状态：✅ 交付待验收（代码 + 测试 + 两份 docs 已提交到 `p1/hua`；BRIEF/STATUS 未入 commit，按卡只提交 5 个文件）
- 分支 / commit：`p1/hua` @ **`a293afbc`**（父提交 `8a2029b7`，worktree `E:\Git hub\mangpai-fusion-hua`）
- diffstat：5 files changed, 93 insertions(+), 13 deletions(-)
  （`engine/facts/structure_check.py`、`tests/facts/test_structure_check.py`、`tests/api/test_engine_reset_regression.py`、
  `docs/specs/single-chart-analysis-v1.md`、`docs/specs/actor-rules-v1.md`）
- 一句话：**只翻 `mode=化用`**——`members=(化者,被化者)=(受生端,生端)`、`actor=化者`；`sheng`/`生泄用` 的 actor 仍是生者。
  H09–H11 按方向契约 reversed→ok，H12（财→杀）不扩类、仍 reversed（`known_gap`）。

---

## 1. 改动文件

| 文件 | 改动 |
|---|---|
| `engine/facts/structure_check.py` | `sheng_mode()` → `sheng_view(src,dst)`：化用（`gods[src]∈官杀 ∧ gods[dst]∈印`，检测仍在生方向）返回 `("化用",(dst,src),dst)`；否则返回 `("生泄用",(src,dst),src)`。两处调用（`graph.edges` 的 `sheng` 分支、`_derived_sheng` 的 `sheng(main_qi)` 分支）改用其返回值。`sheng(main_qi)` kind、edge_id、distance、`_derived_sheng_adjacent` 的 `mode="sheng"` 分支、`ke`/`muku`/合用 **未动**。 |
| `tests/facts/test_structure_check.py` | ① 旧化用 fixture 按反向契约改（见 §2.1）；② 新增 `_HUA_CASES` + `test_hua_candidate_actor_is_hua_zhe_t180_fixture`（H09/H10/H11，3 个 parametrize）；③ `test_h12_cai_sha_hua_known_gap`；④ `test_hua_flip_does_not_touch_sheng_or_shengxie_t181`。 |
| `tests/api/test_engine_reset_regression.py` | 同一份旧化用 fixture（JSON 视图）按反向契约改（见 §2.1）。 |
| `docs/specs/single-chart-analysis-v1.md` | L165 `化` 行 actor 列：「引擎 `actor`」→「引擎 `actor`=化者（受生端；被化者→化者）」。其余行未动。 |
| `docs/specs/actor-rules-v1.md` | §4.8 陷阱句按 T-180 §9.1 文本替换为「化的力向与生相反——被化者（生端）→ 化者（受生端）……只翻 mode=化用，sheng/生泄用 不动」；同节引擎行同步为「化用候选 (化者,被化者)、actor=化者；sheng/生泄用 仍 (生者,被生者)、actor=生者」。§4.8 其余条款、§3/§5.1 未动（§5.1 化行「(化者,被化者)｜members[0]｜保持」修复后才与实现一致，不需要再改）。 |

**未改**：`META/**`（answers / hold-out / freeze / postfix / baseline）、`tools/**`、`engine/facts/relation_graph.py`、
`engine/facts/energy*`、`conditions_ir` / 规则数据、`pyproject.toml`、其他 specs 与模板。
**未做**：未跑 hold-out 评分器（按要求，P1 由中枢一次性跑）；未 push；未碰 `rethink/*`、`p1/candidates`、main。

## 2. 原始输出

### 2.1 契约变更（旧 actor 断言 → 新契约，单列）

两处既有断言（**未删、未 skip、未放宽**；仍是精确相等断言，只按反向契约改值）：

| 文件:位置 | 旧断言 | 新断言 | 说明 |
|---|---|---|---|
| `tests/facts/test_structure_check.py::test_zuogong_kaishan_1342_sha_sheng_yin_and_zihe`（原 L147-148） | `mode=化用, members=("H.b","D.b")`, `ten_gods=("七杀","偏印")`, `actor="H.b"` | `members=("D.b","H.b")`, `ten_gods=("偏印","七杀")`, `actor="D.b"` | 辰印=化者（受生端）→ actor；direction 两条断言（2 层正向、3 层同在主位）不变 |
| `tests/api/test_engine_reset_regression.py::test_duan_zuogong_hua_yong_and_ganzhi_zihe_without_fugui_score`（原 L135-136） | 同上（JSON list） | 同上 | 同一 fixture 的 API 视图 |

契约变更本身：**化用候选** `members` 由 `(生者=被化者, 受生者=化者)` 改为 `(化者, 被化者)`，`actor` 由「生者=被化者」改为「化者=受生端」。
`relation_kind` 仍是 `sheng`/`sheng(main_qi)`（引擎无「化」kind，freeze v2 映射不变）；`edge_id`/`distance`/`binzhu` 判读不变
（`_ti_yong_ends` 按体用补位，2 层仍「正向」）。**生 / 生泄用 不变**（新增测试钉住）。

### 2.2 四条化的候选现场（改后，`build_duan_zuogong_candidates`）

```text
== P1-H09 癸巳 乙卯 己巳 己巳 ==
  mode=化用 sheng(main_qi) members=Y.b,M.b chars=巳,卯 gods=正印,七杀 actor=Y.b
  mode=化用 sheng(main_qi) members=D.b,M.b chars=巳,卯 gods=正印,七杀 actor=D.b
  mode=化用 sheng(main_qi) members=H.b,M.b chars=巳,卯 gods=正印,七杀 actor=H.b
== P1-H10 戊午 戊午 戊午 甲寅 ==
  mode=化用 sheng(main_qi) members=Y.b,H.b chars=午,寅 gods=正印,七杀 actor=Y.b
  mode=化用 sheng(main_qi) members=M.b,H.b chars=午,寅 gods=正印,七杀 actor=M.b
  mode=化用 sheng(main_qi) members=D.b,H.b chars=午,寅 gods=正印,七杀 actor=D.b
== P1-H11 乙巳 己丑 庚午 庚辰 ==（只列跨答案端点的一对）
  mode=化用 sheng(main_qi) members=H.b,Y.b chars=辰,巳 gods=偏印,七杀 actor=H.b
  其余化用：(M.b,Y.b) 丑,巳 actor=M.b；(M.b,D.b) 丑,午 actor=M.b；(H.b,D.b) 辰,午 actor=H.b
== P1-H12 乙巳 乙酉 戊子 甲寅 ==（答案端 子/寅）
  mode=生泄用 sheng(main_qi) members=D.b,H.b chars=子,寅 gods=正财,七杀 actor=D.b   # 仍是被化者，known_gap
```

- H09：答案 `a=巳`（Y.b/D.b/H.b）、`b=卯`（M.b）；化用 actor 全部落在 a 端 → `reversed → ok`。
- H10：`a=午`（Y/M/D.b）、`b=寅`（H.b）；actor 落在 a 端 → `ok`。
- H11：`a=辰`（H.b）、`b=巳`（Y.b）；跨端点候选 `(H.b,Y.b)` actor=H.b → `ok`。
- H12：`a=寅`（H.b）、`b=子`（D.b）；同对只有 `生泄用 (D.b,H.b)` actor=D.b（b 端）→ **仍 `reversed`**。

> 方向 ok/reversed 是按 `tools/p1_holdout_eval.py::_direction`（候选按 `_spans` 过滤后 `any(actor∈a)`→ok、`any(actor∈b)`→reversed）
> 的契约推演，**未跑评分器**，以中枢实跑为准。

### 2.3 测试

```text
$ .venv\Scripts\python.exe -m pytest tests/facts/test_structure_check.py tests/api/test_engine_reset_regression.py -q -o addopts="-ra --tb=short"
34 passed in 0.85s

$ .venv\Scripts\python.exe -m pytest -q
1430 passed, 1 skipped, 1 warning in 151.25s      exit 0
SKIPPED [1] tests\tools\test_bundle_pii.py:34: 本地脱敏脚本缺失 …（T-114 已知项）
```

- 基线 1425 passed（T-180）→ 1430：新增 5 个用例（H09/H10/H11 parametrize 3 个 + H12 known_gap 1 个 + 不全局翻 sheng 1 个），**没有删/跳过任何旧用例**。
- 新增断言强度：H09–H11 逐条比对**全部** `mode=化用` 的 `(members, actor)` 精确集合，并逐条校验
  `actor==members[0]`、`wuxing_relation(chars[1],chars[0])=="生"`（被化者生入化者，化者=受生端）、十神对为 官杀→印。
- `known_gap` 用**测试名 + docstring** 标记（`--strict-markers` 下未注册 marker 会报错，未改 `pyproject.toml`）。

### 2.4 引擎审计 / 关系图 / 15KB

```text
$ python -m tools.engine_audit
案例 481；有问题 0；问题种类 0；口径说明 32                       exit 0

$ python -m tools.relations_audit
案例总数: 481    缺边统计: 无    假边统计: 无
三合: 515/515 = 100.00%    三会: 495/495 = 100.00%    结论: 全部通过   exit 0

$ python -m engine.cli all --pillars "庚申 戊寅 壬子 辛丑" --gender 乾 --json | bytes
14804 B（main 8a2029b7 = 14804 B，未变；< 15,000）
```

15KB 门禁（`tests/api/test_engine_reset_regression.py::test_cli_all_json_under_15kb`）在 2.3 的 targeted/full 中均通过。

### 2.5 git

```text
branch p1/hua, HEAD a293afbc82109dad2a3008f401138396e3a44140
parent 8a2029b7
5 files changed, 93 insertions(+), 13 deletions(-)
```

注：执行期间中枢已把 T-180 产物提交到 main（`61586a5a`，父 `8a2029b7`）。`p1/hua` 仍按要求以 `8a2029b7` 为基，
与 `61586a5a` 的改动文件不相交（对方是 META/docs/reviews/tasks），合并应无冲突。本 BRIEF/STATUS 未提交（见 §3.5）。

## 3. 未完成与风险

1. **H12 财→杀 未修（known_gap，中）**：引擎化用谓词只认「官杀→印」，H12（子财→寅杀）仍是 `mode=生泄用`、
   `actor=子`，方向仍 `reversed`。按卡**不扩类**；扩类须另卡 + 原文判据（T-180 只有 1 条正例），**不得用 hold-out 反推**。
2. **转化句 `actor=null` 未写入规则表（中）**：`21:L1461`「七杀化印再生身」这类不及物转化句，T-180 §9.1 建议在 §4.8
   显式写 `actor=null`；本卡只授权改「陷阱句」，故**未加**。现状由 §5.4「未知即 null」兜底，建议另卡补条款（T-180 R2）。
3. **评测器口径说明未补化（中）**：`tools/p1_holdout_eval.py` L41-46 的「口径差异」只写了墓；T-180 §6.2 建议补「kind 映射 ≠ actor 等价」。
   该文件不在本卡 File Scope，**未改**；下游引用该说明时注意化的 actor 契约已变。
4. **方向结果未实测（提示）**：未跑 hold-out；H09–H11 的 ok 是按评测器 `_direction` 契约推演（见 §2.2 注）。
   中枢跑后若与推演不符，先查候选 `_spans` 过滤与 `MECHANISM_TO_CAND_KINDS` 映射，不要回头改规则。
5. **BRIEF/STATUS 未入 commit（低）**：按卡 commit 只含 structure_check + 测试 + 两份 docs；本文件与 `STATUS.md` 留在主检出
   `tasks/T-181/`，未提交到 `p1/hua`。
6. **15KB 门禁覆盖面（低）**：门禁只测 `庚申 戊寅 壬子 辛丑`（14804 B）；化用盘非门禁对象（如 H11 盘 16172 B），本卡未改其规模。
7. **无 Blocker**。

## 4. 下游须知

1. **读化方向**：`candidate.mode=化用` → `member=actors[0]=化者=受生端`，`members[1]=被化者=生端`；被化者生入化者。
   不要用 `relation_kind=sheng` 的 kind 去推 actor（生/生泄用 的 actor 仍是生者）。
2. **members 顺序变了**：化用候选 `members[0]` 从「被化者」变为「化者」。按 `members[0]` 取被化者的下游要改；
   `edge_id`、`distance`、`binzhu` 判读、候选召回（`_spans` 只看集合）不变。
3. **生不是化**：同一对字可同时出现 `mode=化用`（actor=化者）与 `mode=生泄用`/`sheng`（actor=生者），两套约定并存，
   已由 `test_hua_flip_does_not_touch_sheng_or_shengxie_t181` 钉住（巳→辰 同盘两读）。
4. **H12 口径**：写报告时按 `reversed` 计，不得剔除、不得改标「生」；缺口在化用谓词，不在答案。
5. **规则同步**：`single-chart-analysis-v1.md` L165 与 `actor-rules-v1.md` §4.8 已按新契约改；若中枢冻结 v4，引用这两处。
6. **验证入口**：`pytest -q`、`python -m tools.engine_audit`、`python -m tools.relations_audit`、15KB 测试；
   中枢需在 worktree 内用自己的解释器重跑（数字以现场为准）。

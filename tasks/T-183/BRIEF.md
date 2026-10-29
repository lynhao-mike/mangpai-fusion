# T-183 BRIEF · 固定五行三处 + E-08 评分器防覆盖

- 分支：`p1/fixed5`（worktree `..\mangpai-fusion-fixed5`，基于 main `f230e5b2`）
- 代码 commit：`79367f1d`（6 files，+235/−32；未 push）
- 文档/产物 commit：见本文件所在 commit（BRIEF + STATUS + `META/p1-dev20-veto-v1.json`）
- 授权变更：中枢 2026-10-29 会话内授权 ①facade 默认视图削候选 `tiyong` ②评分器加 kind 别名
  （原文：「15KB：选 (a) facade 压缩」「评分器 kind：授权通用别名」），均见 §1.2「契约变更」。

## 1. 改动文件

| 文件 | 改动 |
|---|---|
| `engine/facts/structure_check.py` | ① 新增 `_derived_zhi_ke`：地支本气五行两两相克，返回 `(克方,被克方,柱距)`；候选 `mode="制用"`、`relation_kind="zhi_ke"`、`actor=克方`、`edge_id=None`。② 新增 `_derived_gan_ke_zhi`：天干克地支（**含同柱盖头**，dist=0），候选 `mode="制用"`、`relation_kind="gan_ke_zhi"`、`actor=天干`、`edge_id=None`。③ 同对天干既有 `ke` 又有 `wuhe` 时，`ke` 候选排在 `wuhe` 前（按 pair 预取 ke 边、先发；**不去重**、**不改 `RelationGraph.edges`**）；`ke` 的 actor 规则仍 `members[0]`。不写党势/比值/权重/浮点；不实现 H02/H05 冲穿方向；合/冲/刑/穿 `actor=None` 保持（T-178）。 |
| `engine/api/facade.py` | 默认 compact 视图 `_AGENT_OMIT_CANDIDATE_KEYS` 增 `tiyong`：候选 `tiyong` 由 `duan_zuogong.tiyong[addr]` 逐地址还原；`analyze_facts`/`--full` 全量视图逐字段保留（`zuogong` 原子仍用全量视图判 target）。 |
| `tools/p1_holdout_eval.py` | **E-08**：`--out-json/--out-md` 默认 `None`，不传则只打 stdout、不写 `META/p1-holdout-baseline-v1.*`；目标已存在且未 `--force` 时拒绝覆盖（退出 2，stderr 说明）；`--force` 才覆盖；`--artifact-label` 保留。**kind 别名**：`CAND_KIND_ALIASES={"zhi_ke":"ke","gan_ke_zhi":"ke"}`，在 `base_kind()` 归一（与 `sheng(main_qi)` 剥括号同类），只影响 `mechanism=克` 的候选匹配，不改任何 mechanism 映射表、不按 case 特判。 |
| `tests/facts/test_structure_check.py` | 旧 `test_zuogong_has_no_branch_branch_ke_edge_or_candidate` → `test_zuogong_branch_ke_candidate_without_branch_ke_edge`（T-183 反向契约：边仍不建、候选必须有）；新增 `test_zuogong_gan_ke_zhi_candidate_all_pairs`、`test_zuogong_ke_candidate_precedes_wuhe_for_same_pair_t183`。 |
| `tests/api/test_facade_zuogong_fields.py` | 默认视图断言改：候选无 `tiyong`、可由 top-level `tiyong` 还原；全量视图仍有 `tiyong`；CLI 分档同时校验还原路径。 |
| `tests/tools/test_p1_holdout_eval.py` | 新增别名测试 2 条（别名只影响克、映射表不变；`zhi_ke`/`gan_ke_zhi` 候选可评到 ok）+ E-08 测试 3 条（默认不写、已存在拒绝、`--force` 允许）。 |

### 1.2 契约变更（单列；diff 可见，非放宽）

1. **候选 kind 新增两个值**：`zhi_ke`、`gan_ke_zhi`（`mode="制用"`、`edge_id=None`、`actor=克方/天干`）。
   `ZuogongCandidate.relation_kind` 注释同步。二者是**证据 kind**，不是关系边 kind；`relations.edges` 零变化。
2. **同对 ke/wuhe 排序**：同一对 members 的候选顺序从 `wuhe, ke` 改为 `ke, wuhe`（`wuhe.actor` 仍 None）。
3. **默认 compact 视图削 `candidates[].tiyong`**（中枢授权）：由 `duan_zuogong.tiyong[addr]` 还原；
   全量视图不变。默认视图字节因此回到 15KB 内。
4. **`p1_holdout_eval` 默认不写盘 + 拒绝覆盖 + `--force`**（E-08）；退出码 2 新增「目标已存在未 --force」。
5. **评分器 kind 别名**（中枢授权）：`zhi_ke`/`gan_ke_zhi` → `ke`；`MECHANISM_TO_*_KINDS` 表本身未改。
6. 测试 1 条反向契约（§1 第 4 行）+ 2 条断言更新（facade 投影），均为授权范围内的契约同步，不是删断言。

## 2. 原始输出

### 2.1 测试 / 审计（worktree `..\mangpai-fusion-fixed5`）

```text
$ .venv\Scripts\python.exe -m pytest -q
1443 passed, 1 skipped, 1 warning in 132.29s (0:02:12)
# T-182 基线 1436 passed / 1 skipped；+7 = 本轮新增测试（2 structure + 2 别名 + 3 E-08）

$ .venv\Scripts\python.exe -m tools.engine_audit
案例 481；有问题 0；问题种类 0；口径说明 32
exit=0   # 481/0

$ .venv\Scripts\python.exe -m tools.relations_audit
缺边/假边/重复边：无；三合 515/515 = 100.00%、三会 495/495 = 100.00%
结论: 全部通过
exit=0

$ .venv\Scripts\python.exe -m tools.verify_baseline --compare
{"pytest_passed":1443,"pytest_failed":0,"audit_errors":0,"relations_ok":true,"zuogong_charts":481,"zuogong_day_branch":374,...}
【基线未退步】
exit=0
```

### 2.2 15KB 测试盘（`庚申 戊寅 壬子 辛丑`，`engine.cli all --json` 默认 compact 视图）

```text
改前（f230e5b2）                    14,804 B / 27 候选
只加支克/干克支（未压）             15,451–15,452 B / 33 候选   → 两条 guard 测试红（断言实测 15,451）
facade 削 candidates[].tiyong 后    14,654 B / 33 候选   < 15,000 ✅（guard 断言未改）
--full 全量视图                     > 15,000 B（测试断言仍要求 full 更大）
```

### 2.3 H03 / H06 / H07 事实层（worktree 内直查候选）

```text
== P1-H03 丙午 辛卯 丁卯 壬子
  idx=0 ke      mode=制用 members=('Y.s','M.s') chars=('丙','辛') actor=Y.s dist=1 edge=e002
  idx=1 wuhe    mode=合用 members=('Y.s','M.s') chars=('丙','辛') actor=None dist=1 edge=e001
== P1-H06 辛丑 丁酉 癸酉 戊午
  idx=27 zhi_ke mode=制用 members=('H.b','M.b') chars=('午','酉') actor=H.b dist=2 edge=None
  idx=28 zhi_ke mode=制用 members=('H.b','D.b') chars=('午','酉') actor=H.b dist=1 edge=None
== P1-H07 乙巳 戊子 丁巳 庚戌
  idx=31 gan_ke_zhi mode=制用 members=('M.s','M.b') chars=('戊','子') actor=M.s dist=0 edge=None
```

### 2.4 dev-20 否决（显式一次：`--out-json META/p1-dev20-veto-v1.json --artifact-label dev20_veto`）

```text
P1 hold-out dev20_veto（20 条）：edge 8/20 (40.0%) · candidate 20/20 (100.0%) · directed 13/20 (65.0%)
方向分布：{'ok': 13, 'reversed': 1, 'actor_none': 6}
```

与改前诊断产物 `META/p1-holdout-postfix-hua-v1.json`（directed 9/20、candidate 17/20）逐例对比：

| case | 机制 / a→b | 改前 | 改后 |
|---|---|---|---|
| P1-H01 | 制 / 子→午 | actor_none | **ok**（zhi_ke 子克午，actor=子） |
| P1-H06 | 克 / 午→酉 | no_edge | **ok**（zhi_ke，actor=午） |
| P1-H07 | 克 / 戊→子 | no_edge | **ok**（gan_ke_zhi，actor=戊） |
| P1-H19 | 克（救应）/ 午→申 | no_edge | **ok**（zhi_ke，actor=午） |
| P1-H03 | 合 / 丙→辛 | actor_none | actor_none（见 §3.1） |

- **既有 ok 一条未丢**：改前 ok 9 = H09/H10/H11/H13/H14/H15/H16/H17/H18；改后全部仍在（lost = 无）。
- 唯一 `reversed` 仍是 H12（财→杀 `known_gap`，T-180 §6.3 不扩类）。
- **本表只作否决口径**：不是官方 P1，不在 dev-20 上宣称提升；未跑官方 P1、未碰 fresh-40、未改 hold-out/answers/分母。

### 2.5 E-08 实测（worktree 内三次调用）

```text
1) 默认（不传 --out-json/--out-md）
P1 hold-out pre_fix_baseline（20 条）：edge 8/20 … directed 13/20 (65.0%)
未写盘：未传 --out-json/--out-md（只打 stdout）
META/p1-holdout-baseline-v1.json sha256 前后一致（7086C4611F5165F0…），未被覆盖

2) 目标已存在、未 --force
[p1_holdout_eval] 目标已存在，拒绝覆盖（确认覆盖请加 --force）：…\t183-sentinel.json
exit=2；文件内容仍为 SENTINEL

3) 加 --force
写盘：…\t183-sentinel.json；exit=0；artifact=probe_force（relations=20）
```

（第 1 次是 E-08 证据跑，不落盘、不作任何指标声明；dev-20 显式落盘只有 §2.4 一次。）

### 2.6 候选增量（481 审计案例，`cases/`）

```text
charts=481  cand_total=15374  before=12755  zhi_ke=1114  gan_ke_zhi=1505
charts_with_new=469 (97.5%)  avg_compact=15433B  max_compact=21256B
```

候选总量 +2,619（+20.5%）；默认视图平均/最大字节仍受各盘规模影响（T-179 已记录全盘超 15KB 是既有状态，
本轮只保证 15KB 测试盘护栏，不承诺全盘）。

## 3. 未完成与风险

1. **H03 在评分器里仍是 `actor_none`（事实层已修）**：丙辛对的 `ke e002 actor=丙` 已排在 `wuhe` 前，
   但冻结映射 `合 → {wuhe, liuhe}` 不会去匹配 `ke`；要让它 ok 只能把 `合` 映射到 `ke`（语义上等于「合按克算」），
   与中枢「仍不做合」冲突，故未做。H04（巳申合）、H05/H08（冲）同因：**支克候选存在但机制=合/冲时评分器看不见**。
2. **H12 仍 `reversed`**：财→杀 `known_gap`（T-180），不扩类、不剔分母。
3. **15KB 只是测试盘护栏**：默认视图削了候选 `tiyong` 才回到 14,654 B；全盘平均 15,433 B、最大 21,256 B，
   与 T-179 记录一致（不是本轮回归）。若产品要求全盘 <15KB，需另立裁剪任务。
4. **`verify_baseline --compare` 在 worktree 里靠临时 `.venv` junction 才跑通**（`.venv/` 已 gitignore，
   未进提交）；换盘/合并后请在 main 用自带 venv 复跑。
5. 未跑官方 P1、未跑 fresh-40、未 push main、未碰其他 worktree。
6. 未做党势/比值/浮点；未为 H02/H05 写冲穿方向规则；引擎仍不判穿制。

## 4. 下游须知

1. **默认视图还原**：候选 `tiyong` 不再随候选下发，用 `duan_zuogong.tiyong[addr]` 逐 `members` 查表；
   需要原件用 `engine.cli all --full`。`zuogong` 原子内部仍走 `analyze_facts`（全量），不受影响。
2. **新 kind 是证据 kind**：`zhi_ke`/`gan_ke_zhi` 的 `edge_id` 恒为 `None`；`relations.edges` 边数/ID/kind/members
   与改前逐字节一致（关系审计 100% 通过）。下游若对 `relation_kind` 做穷举映射，需加这两个值；
   评分器侧已加通用别名（仅 `ke`）。
3. **不要把 `zhi_ke` 当「制净/成局」**：候选只是固定五行方向证据；制净与否仍 `needs_judgment`（T-184）。
4. **合并**：分支基于 `f230e5b2`；main 现为 `16efd26a`（仅 docs + T-183/184/185 任务卡），无代码冲突。
   **不要 push main**，由中枢合并并亲自跑验收；本 BRIEF 的「通过」不算数。
5. **复现命令**（在 worktree 内，用主仓 venv）：
   ```text
   ..\mangpai-fusion\.venv\Scripts\python.exe -m pytest -q
   ..\mangpai-fusion\.venv\Scripts\python.exe -m tools.engine_audit
   ..\mangpai-fusion\.venv\Scripts\python.exe -m tools.relations_audit
   ..\mangpai-fusion\.venv\Scripts\python.exe -m tools.p1_holdout_eval --out-json META/p1-dev20-veto-v1.json --artifact-label dev20_veto --force
   ```

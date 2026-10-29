# T-188 BRIEF · 自刑候选过滤（A+ v1.3 Step 1）

- 分支：`p1/selfxing`（worktree `..\mangpai-fusion-selfx`）
- 基线：`76c2b26e`（= 任务卡前置 `fd4188aa` + 一张 docs 提交：T-188/189/190 任务卡；
  `engine/`、`tests/` 树与 `fd4188aa` 逐字节一致。选它作 base 是为了让 `tasks/T-188/STATUS.md` 在树内可直接追加，
  避免 add/add 冲突）
- 代码 commit：`2e80c5fb`（2 files，+87/−1；未 push）
- 文档/产物 commit：见本文件所在 commit（BRIEF + STATUS + `META/p1-dev20-selfx-veto.json`）
- 依据：`docs/specs/adjudication-a-plus-v1.md` §2 自刑条款

## 1. 改动文件

| 文件 | 改动 |
|---|---|
| `engine/facts/structure_check.py` | ① 新增 `_is_zixing_edge(e)`：`e.kind == "xing"` 且（`e.completeness == "zixing"` 或两端 `chars` 同字）。② `build_duan_zuogong_candidates` 的 `_ZHI_KINDS` 分支在 `emit_zhi_edge(e)` 前跳过自刑边，并 `logger.debug("duan_zuogong 剔除自刑候选 edge=%s chars=%s", e.id, e.chars)` **逐条**记录。③ 不删边、不改 ID、不改 `RelationGraph`；不碰 party/方向/其他 kind；不生成新候选。 |
| `tests/facts/test_structure_check.py` | 新增 7 条：4 个自刑盘（酉酉/亥亥/午午/辰辰）断言「候选无自刑边 + 边仍在且 ID/members/completeness 逐项不变 + 逐条 logged + 同盘其他候选保留」；2 个非自刑 partial 刑（丑戌/未戌）断言「仍候选、actor=None、edge_id 对应 partial 边」；1 条子卯 huxing「仍候选」（防一刀切）。 |

### 1.2 契约变更（单列；diff 可见，非放宽）

1. `duan_zuogong.candidates` 少 73 条自刑 `制用` 候选（481 盘合计：15,374 → 15,301）。
   `relations.edges` 边数 / ID / kind / members / completeness **零变化**（关系审计 100% 通过）。
2. 剔除记录只走 `logger.debug`（默认 INFO 下不可见）；如需审计请开 DEBUG 或按 §4.3 对比边与候选。
3. 无结构变更：`ZuogongCandidate` / `RelationGraph` / facade 投影 / 评分器均未动。

## 2. 原始输出

### 2.1 测试 / 审计（worktree `..\mangpai-fusion-selfx`）

```text
$ ..\mangpai-fusion\.venv\Scripts\python.exe -m pytest -q
1496 passed, 1 skipped, 1 warning in 142.67s (0:02:22)
# 任务卡基线 1489 + 本轮新增 7 = 1496；0 failed

$ ... -m tools.engine_audit
案例 481；有问题 0；问题种类 0；口径说明 32
exit=0   # 481/0

$ ... -m tools.relations_audit
缺边/假边/重复边：无；三合 515/515 = 100.00%、三会 495/495 = 100.00%
结论: 全部通过
exit=0

$ ... -m tools.verify_baseline --compare
{"pytest_passed":1496,"pytest_failed":0,"audit_errors":0,"relations_ok":true,
 "zuogong_charts":481,"zuogong_day_branch":374,...}
【基线未退步】
exit=0
```

### 2.2 15KB 测试盘（`庚申 戊寅 壬子 辛丑`，`engine.cli all --json` 默认 compact 视图）

```text
bytes 14,653 < 15,000 ✅   candidates 33
xing 候选仅 e008 = 申/寅（寅巳申 partial，非自刑，按卡保留）
zixing 边：本盘无同字地支 = 0（故字节与 T-183 记录 14,654 仅测量尾差，guard 断言未改）
```

### 2.3 481 盘自刑盘点（本地临时探针，跑完即删、未提交）

```text
charts=481
charts_with_zixing=66
zixing_edges_excluded=73      by_char={'辰':15,'酉':18,'午':21,'亥':19}
candidates_now=15,301         candidates_before=15,374   （−73，与 T-183 记录的 15,374 精确对齐）
non_selfxing_xing_candidates_now=272
charts_with_zero_candidates=0
leaked_or_wrong=0             （自刑边无一条变成候选；关系图边全部仍在）
```

### 2.4 dev-20 否决（显式一次：`--out-json META/p1-dev20-selfx-veto.json --artifact-label dev20_selfx_veto`）

```text
P1 hold-out dev20_selfx_veto（20 条）：edge 8/20 (40.0%) · candidate 20/20 (100.0%) · directed 13/20 (65.0%)
方向分布：{'ok': 13, 'reversed': 1, 'actor_none': 6}
写盘：META\p1-dev20-selfx-veto.json；exit=0
```

与改前否决产物 `META/p1-dev20-veto-v1.json`（T-183，`dev20_veto`）逐例比对：

```text
cases 20 vs 20；逐例 JSON 全等 diff_count=0
primary：scored 20 / directed 20 / edge 8/20 / candidate 20/20 / directed 13/20 / 方向分布 —— 全部逐项一致
```

**结论：无回退**（20 条里没有一条依赖自刑候选；本表只作否决口径，不是官方 P1，不在 dev-20 上宣称提升）。

## 3. 未完成与风险

1. **剔除只打 DEBUG 日志**：INFO 级别下看不到记录。卡允许 `logger.debug`，但生产环境若要追「哪些边被剔除」，
   需开 DEBUG 或按 §4.3 对比 `relations.edges` 与 `candidates`。
2. **候选总量 −73**：下游若把自刑 `xing` 候选当可评证据，会少 73 条（481 盘）；dev-20 实测 0/20 变化。
   是否要把自刑边以 `excluded` 字段显式下发，留给后续卡（本卡不改结构/签名）。
3. **多字组边本来就不进候选**：`len(e.members) != 2` 的既有过滤（如三字齐全的寅巳申 full 边）与本卡无关，未改。
4. **`verify_baseline --compare` 需要临时 `.venv` junction**（worktree 内 `.venv/` 已 gitignore；本轮用完已
   `rmdir` 删除 junction，未进提交、未触碰主仓 `.venv` 内容）。
5. 未跑 fresh-40 / anchor-60；未跑官方 P1；未改 hold-out/answers/分母；未碰 party/党势/方向；未 push main。

## 4. 下游须知

1. **边仍是事实**：`relations.edges` 的边数、ID、kind、members、completeness 与改前逐字节一致；
   `completeness="zixing"` 的边仍在，`relations_audit` 100% 通过。
2. **候选层**：`duan_zuogong.candidates` 不再出现自刑 `xing`（两端 chars 同字）；
   非自刑 `xing`（申/寅 寅巳申、丑/戌、未/戌、子/卯）仍在，`actor` 仍为 `None`（T-178 契约未动）。
3. **如何审计剔除**：`logger.debug("duan_zuogong 剔除自刑候选 edge=… chars=…")`；或取
   `relations.edges` 中 `kind=="xing" and completeness=="zixing"` 的 ID，确认它们不在 `candidates[].edge_id`。
4. **合并**：分支基于 `76c2b26e`（`fd4188aa` + 任务卡 docs）；若 main 已前进，预期只有 docs 差异、无代码冲突。
   **不要 push main**，由中枢合并并亲自跑验收；本 BRIEF 的「通过」不算数。
5. **复现命令**（worktree 内，用主仓 venv）：
   ```text
   ..\mangpai-fusion\.venv\Scripts\python.exe -m pytest -q
   ..\mangpai-fusion\.venv\Scripts\python.exe -m tools.engine_audit
   ..\mangpai-fusion\.venv\Scripts\python.exe -m tools.relations_audit
   ..\mangpai-fusion\.venv\Scripts\python.exe -m tools.p1_holdout_eval --out-json META/p1-dev20-selfx-veto.json --artifact-label dev20_selfx_veto --force
   ```
   （`verify_baseline --compare` 需先 `cmd /c mklink /J .venv <主仓 .venv>`，跑完 `cmd /c rmdir .venv`。）

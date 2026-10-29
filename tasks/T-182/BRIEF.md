# T-182 BRIEF · P1 评分器口径同步（artifact 标签 + 墓/化注释 + fixture）

- 状态：✅ 交付待验收（代码 + 测试已提交到 `p1/ruler`；BRIEF/STATUS 按 T-181 惯例留在主检出，未入 commit）
- 分支 / commit：`p1/ruler` @ **`7063f221`**（父提交 `ba688aec`，worktree `E:\Git hub\mangpai-fusion-ruler`）
- diffstat：2 files changed, 140 insertions(+), 27 deletions(-)
  （`tools/p1_holdout_eval.py`、`tests/tools/test_p1_holdout_eval.py`）
- 一句话：只改评分器与测试——新增 `--artifact-label`（默认 `pre_fix_baseline`，正式 P1 用 `official_p1`，诊断用 `post_fix_*`），
  墓/化注释与 fixture 同步到 T-178/T-179、T-180/T-181 的新约定；**评分逻辑、分母、阈值、hold-out、answers、engine 全部未动，未跑真实 hold-out**。

---

## 1. 改动文件

| 文件 | 改动 |
|---|---|
| `tools/p1_holdout_eval.py` | **artifact 标签**：新增 `DEFAULT_ARTIFACT_LABEL = "pre_fix_baseline"` 与 `--artifact-label`；`main()` 把它传给 `run(..., artifact_label=...)`，写入 JSON 的 `artifact`、MD 头 `- artifact：...` 与控制台标题（`P1 hold-out <label>（N 条）`）。`note`/MD 性质句改为「同一 artifact 标签内可比，不得跨标签引用」。<br>**墓注释**：T-178 审计 4/4 `engine_wrong`；引擎墓用候选应为 `members=(库,入库方)`、`actor=库`，T-179 已修，命中候选应 `ok`；删除「口径对立、不是 bug」的旧说法。<br>**化注释**：T-180 审计 4/4 `engine_wrong`；化=被化者→化者、化者=受生端，`化→sheng` 只是 kind 映射、不等于 actor 等价；T-181 已修 H09–H11，H12（财→杀）仍 `reversed`（`known_gap`，不扩类、不剔分母）。 |
| `tests/tools/test_p1_holdout_eval.py` | ① 墓 fixture 改新约定：`cand("muku", "Y.b", "M.b", actor="Y.b", mode="墓用")`，即 `(库,入库方)`、`actor=库`，期望 `ok`（原断言 `reversed`）。<br>② `test_candidate_kind_suffix_is_stripped` 的化方向按新契约改为 `ok`；新增 `test_hua_candidate_actor_is_hua_zhe_t180`（H09 盘 `癸巳 乙卯 己巳 己巳`，3 条 `mode=化用` 候选 `(化者,被化者)/actor=化者`，期望 `ok`）与 `test_h12_cai_sha_hua_known_gap_t180`（H12 盘 `乙巳 乙酉 戊子 甲寅`，`mode=生泄用`、`(子,寅) actor=子`，期望 `reversed`；测试名 + docstring 标 `known_gap`）。<br>③ 新增 `test_run_artifact_label_default_and_override` 与参数化 `test_cli_artifact_label_in_json_and_console_title`（`None`/`official_p1`/`post_fix_hua`），断言 JSON `artifact`、控制台首行标题、MD artifact 行。 |

**未改**：`engine/**`、`META/**`（hold-out / answers / freeze / baseline）、kind 映射、`_direction`、分母/阈值、`pyproject.toml`、docs、其他 tools/tests。
**未做**：未跑真实 hold-out（合成 fixture 全程 monkeypatch `facts_for`）；未 push；未碰 main 与其他 worktree。

---

## 2. 原始输出

### 2.1 契约变更（单列，未删/未 skip/未放宽）

| 文件::测试 | 旧断言 | 新断言 | 依据 |
|---|---|---|---|
| `tests/tools/test_p1_holdout_eval.py::test_muku_candidate_and_excluded_filter` | 候选 `(入库方,库)`、`actor=入库方` → `reversed` | 候选 `(库,入库方)`、`actor=库` → `ok` | T-178 判定墓=库→入库方、4/4 `engine_wrong`；T-179 已修引擎。评分器 `_direction` 未动，只换 fixture 的 engine 约定。 |
| `tests/tools/test_p1_holdout_eval.py::test_candidate_kind_suffix_is_stripped` | 化用候选 `actor=被化者` → `reversed` | 化用候选 `actor=化者` → `ok` | T-180 判定化=被化者→化者、4/4 `engine_wrong`；T-181 已修 `mode=化用`。仍为精确相等断言。 |
| 新增 `test_h12_cai_sha_hua_known_gap_t180` | — | `reversed`（明确 `known_gap`，不转 `ok`、不剔分母） | T-180 §6.3 / T-181：H12 财→杀不被化用谓词识别；扩类须另卡 + 原文判据。 |

- 生产评分器契约不变：`kind` 映射、`_direction`、分母、muku 敏感性口径均未改；`run()` 只多一个 keyword-only `artifact_label`，位置参数调用不受影响。
- 既有断言无删除、无 skip、无 `in`/`>=` 等放宽；两处旧值仅按反向契约改为新值（上表）。
- `test_run_splits_primary_and_f28_subsets` 原 `artifact == "pre_fix_baseline"` 断言保留，作为默认值回归。

### 2.2 测试

```text
$ .venv\Scripts\python.exe -m pytest tests/tools/test_p1_holdout_eval.py -q
.............................................                            [100%]
45 passed in 0.33s

$ .venv\Scripts\python.exe -m pytest -q
1436 passed, 1 skipped, 1 warning in 133.26s (0:02:13)      exit 0
SKIPPED [1] tests\tools\test_bundle_pii.py:34: 本地脱敏脚本缺失 …（T-114 已知项，非本卡引入）
```

- 定向 45 passed / 0 failed；全套 1436 passed（T-181 基线 1430 + 本卡新增 6 个用例：artifact run 1 + CLI 参数化 3 + 化 1 + H12 1）。
- 墓 fixture 结果：`direction == "ok"`；化 fixture 结果：`direction == "ok"`；H12：`direction == "reversed"`（`known_gap`）。
- 未跑真实 hold-out；测试里 `facts_for` 全部 monkeypatch 为手写事实视图，不触引擎真实盘面。

### 2.3 artifact label 行为

```text
默认（不传 --artifact-label）：
  JSON  artifact = "pre_fix_baseline"
  控制台首行 = "P1 hold-out pre_fix_baseline（N 条）：edge …"
  MD    "- artifact：`pre_fix_baseline`（默认 `pre_fix_baseline` 即 pre-fix 基线；…）"

自定义：
  --artifact-label official_p1   → JSON artifact="official_p1"，控制台首行与控制台标题同步
  --artifact-label post_fix_hua  → JSON artifact="post_fix_hua"，控制台首行与控制台标题同步
```

标签只影响 `artifact` 与展示文本；`primary`/`sensitivity`/逐例方向与不传标签时完全一致（测试断言 JSON 数值不变）。

### 2.4 git

```text
branch p1/ruler
HEAD   7063f22152fe83ae7e64e1e0568b6c46f480e5e9
parent ba688aec48d2e74eec82f19b9467f9f735226639
2 files changed, 140 insertions(+), 27 deletions(-)
  tests/tools/test_p1_holdout_eval.py | 100 +++++++++++++++++++++++++++++++++---
  tools/p1_holdout_eval.py            |  67 ++++++++++++++++--------
```

BRIEF/STATUS 未入 commit（沿用 T-181：分支 commit 只含 code + tests）；`tasks/T-182/` 留在主检出。

---

## 3. 未完成与风险

1. **未跑真实 P1（按卡）**：正式评分由中枢用 `--artifact-label official_p1` 一次性跑；本卡所有方向结论均为合成 fixture 断言，不是 hold-out 结果。
2. **H12 仍 `reversed`（known_gap，预期）**：T-181 只翻转 `mode=化用`，财→杀不被化用谓词识别；本卡只把它固化为测试，不修引擎、不扩类、不剔分母。
3. **`task` 字段仍是 `T-177`**：卡只授权 `artifact` 标签，未改 `task`/`schema_version`；产物区分以 `artifact` 为准。T-180 R4 提到 header 的 `task` 不符，若中枢要改须另开卡。
4. **MD 头新增 artifact 行属于卡面「JSON + 控制台」之外的同步**：为避免 `official_p1` 产物 MD 仍写「pre-fix 基线」而误导；保留 `pre-fix 基线` 字样使既有 MD 断言不受影响，评分内容不变。
5. **默认输出路径仍是 baseline 路径**：不传 `--out-json/--out-md` 时 `--artifact-label official_p1` 会覆盖 `META/p1-holdout-baseline-v1.json/.md`。正式跑请显式指定独立产物路径（下游须知 §4.1）。
6. **BRIEF/STATUS 未提交**：与 T-181 一致；若中枢要求 docs 也进分支，可另行 cherry-pick/补提交。
7. **无 Blockers。**

---

## 4. 下游须知

1. **正式 P1 命令**：`python -m tools.p1_holdout_eval --artifact-label official_p1 --out-json META/<official>.json --out-md META/<official>.md`；不传 `--out-*` 会写默认 baseline 路径。诊断用 `post_fix_candidates` / `post_fix_hua`，不要复用 `pre_fix_baseline`。
2. **读方向仍按候选 `actor`**：墓看 `members=(库,入库方)`、`actor=库`；化看 `mode=化用` 的 `members=(化者,被化者)`、`actor=化者=members[0]`；`sheng`/`生泄用` 的 actor 仍是生者，不要用 `relation_kind=sheng` 反推化的方向。
3. **H12 口径**：写报告按 `reversed` 计，不得剔除、不得改标「生」；缺口在化用谓词，不在答案。
4. **测试是引擎契约快照**：墓/化 fixture 锁的是 T-179/T-181 后的 `(members, actor)` 约定；引擎若再改，按新契约改 fixture 值并在 BRIEF 单列，不得放宽断言或 skip。
5. **验证入口**：`python -m pytest tests/tools/test_p1_holdout_eval.py -q`（本卡门禁）、`python -m pytest -q`（全量）；中枢需在 worktree 内用自己的解释器重跑，数字以现场为准。

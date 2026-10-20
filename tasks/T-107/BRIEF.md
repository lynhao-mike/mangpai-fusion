# T-107 BRIEF · 仓库瘦身零风险项（误入库文件清理）

**结论：4 项中 3 项已删除并验证，第 4 项（`theory/ziping/index-new.yaml`）核实不成立，已停止未删。**

`index-new.yaml` 的任务前提是「废弃草稿，index.yaml 才是产物」。实测推翻该前提：
`index.yaml` 的 933 条规则与 `index-new.yaml` 的 236 条规则**零重叠**（按 id、按 title、按 claim
三重比对全部为 0），`index-new.yaml` 里有 **155 条规则在全仓库再无第二处副本**，
且其中 6 条已被 5 个已冻结 case 的 `asof-blind-freeze.json` 逐条引用。它不是草稿，
是一份**独立的、未被并入主索引的规则集**，删除等于销毁唯一副本。详见 §3。

---

## 1. 改动文件

删除 4 个文件的 git 跟踪（`git rm --cached`），其中 2 个同时删除工作区文件：

| # | 文件 | 原大小 | 工作区 | 为什么安全 |
|---|---|---|---|---|
| 1 | `plans/v5-learning-governance/phase1-registry/dhdgffkkebhmkfjojejmpbldmpobfkfo_5.4.1_chrome.zzzmh.cn.crx` | 1,676,270 B (1.60 MiB) | **已删** | 文件头 magic = `Cr24`，确为 Chrome 扩展安装包（Tampermonkey 5.4.1）。全仓库零引用：`.py`/`.yaml`/`.toml`/`.md` 均无命中，唯一提及是 `META/project-status-2026-10-17.md:91` 的待办条目「仓库清理（.crx / 三个工具缓存）」。该目录除它之外只剩 `plans/v5-learning-governance/*.md` 设计文档，与本包无关 |
| 2 | `theory/_light_index.json` | 7,267,962 B (6.93 MiB) | **已删** | 纯派生缓存。`tools/query_theory.py:216` 在 `cache_path` 缺省时写这个路径，`:245-247` 在签名不匹配或缺失时**无条件重建并写回**。`tools/build_indexes.py:28` 注释明写「是**缓存**」。`tools/extraction_validator.py:49` 也标注为缓存。删后实测：跑一次 CLI 即重新生成，大小逐字节相同（7,267,962 B） |
| 3 | `theory/tiaohou_ditiansui/_extracted_rules.json` | 3,101,374 B (2.96 MiB) | **保留** | 抽取中间产物。`tools/extract_ditiansui_production_rules.py:15` 定义 `OUTPUT_JSON` 指向它，`:316` 只写不读；全仓库没有任何 `.py` 读取该 JSON（grep `_extracted_rules.json` 仅命中两个 `OUTPUT_JSON` 定义处）。删跟踪保留工作区，避免影响仍在引用旧路径的本地流程 |
| 4 | `theory/ziping/_extracted_rules.json` | 2,865,866 B (2.73 MiB) | **保留** | 同上，`tools/extract_ziping_production_rules.py:15` + `:322`。注意该脚本真正产物是 `OUTPUT_YAML = theory/ziping/index.yaml`（`:14`），JSON 是附带 dump |

**合计移出仓库跟踪：14,911,472 B ≈ 14.22 MiB**（工作区实际腾出 8.94 MiB，另 5.70 MiB 保留在盘上）。

**`.gitignore` 新增 5 条**（`.gitignore:79-86`）：

```
plans/v5-learning-governance/phase1-registry/*.crx
theory/_light_index.json
theory/ziping/_extracted_rules.json
theory/tiaohou_ditiansui/_extracted_rules.json
```

用通配 `*.crx` 而非具体文件名，防止再次误下载其它扩展包入库。

---

## 2. 验证原始输出

### 2.1 删除前基线

```
$ python -m pytest -q
........................................................................ [ 31%]
........................................................................ [ 62%]
........................................................................ [ 94%]
.............                                                            [100%]
229 passed in 16.32s
```

### 2.2 删除后

```
$ python -m pytest -q
........................................................................ [ 31%]
........................................................................ [ 62%]
........................................................................ [ 94%]
.............                                                            [100%]
229 passed in 17.13s
```

229 passed，与基线一致，无新增失败。

### 2.3 `git status --porcelain`

```
 M .gitignore
 M engine/v5/preprod.py
D  plans/v5-learning-governance/phase1-registry/dhdgffkkebhmkfjojejmpbldmpobfkfo_5.4.1_chrome.zzzmh.cn.crx
 M tests/r10/test_r10_ziping_career_acceptance.py
 M tests/v5/test_render_report_v6.py
 M tests/v5/test_report_reads_l7.py
D  theory/_light_index.json
D  theory/tiaohou_ditiansui/_extracted_rules.json
D  theory/ziping/_extracted_rules.json
 M tools/render_report_v6.py
?? tests/v5/test_manifest_isolation.py
```

4 个目标文件均为 `D `（已暂存删除），无 `D` + `??` 的重复项，说明 `_extracted_rules.json`
两份确实只是从索引移除、工作区文件被 `.gitignore` 接管，不会以 untracked 形式再次出现。

` M engine/v5/preprod.py`、` M tests/r10/...`、` M tests/v5/...`、` M tools/render_report_v6.py`、
`?? tests/v5/test_manifest_isolation.py` 均为**其它任务遗留的既有改动**（T-104 / T-106），
本任务未触碰 `engine/`、`tests/`、`tools/` 下任何文件。

### 2.4 `.gitignore` 生效验证

```
$ git check-ignore -v theory/_light_index.json theory/ziping/_extracted_rules.json
.gitignore:82:theory/_light_index.json	theory/_light_index.json
.gitignore:85:theory/ziping/_extracted_rules.json	theory/ziping/_extracted_rules.json
```

### 2.5 缓存自愈验证

删除 `theory/_light_index.json` 后跑一次检索，缓存自动重建且 `git status` 仍只显示 `D `：

```
$ python -m tools.query_theory --query "伤官见官" --json
[{"id":"G-SP-058","school":"gao",...}]

$ stat -c '%s' theory/_light_index.json
7267962          # 与删除前逐字节同尺寸

$ git status --porcelain theory/_light_index.json
D  theory/_light_index.json      # 仅暂存删除，重建的文件被 gitignore 忽略
```

**这是最重要的一条验证**：证明删除缓存对功能零影响，且不会因重建而重新变成待提交文件。

### 2.6 缓存内容等价性验证（删前做）

删除前用 `build_light_index(cache_path=<临时路径>, rebuild=True)` 全量重建到临时文件比对：

```
current cache records: 4215
rebuilt records: 4215
id sets equal: True
only in cache: 0 []
only in rebuild: 0
```

4215 条记录、id 集合完全相等，确认现有缓存与真源派生结果一致，不存在「只存在于缓存」的条目
（即不存在 `extraction_validator.py` 警告的那种持久化通道冲突）。临时文件已清理。

---

## 3. 未完成与风险

### 3.1 `theory/ziping/index-new.yaml` — 未删，前提不成立（阻塞项）

任务描述称其为「废弃草稿，index.yaml 才是产物」。实测三条独立证据均不支持该判断：

**(a) 规则集零重叠。** 解析 `index-new.yaml` 得到 236 条规则（文件内有三段 `rules:`，行号 6 / 3157 / 7410，
分别 81 / 114 / 41 条）；`index.yaml` 有 933 条。逐条比对：

```
index.yaml ids: 933
index-new ids also in index.yaml: 0
index-new ids NOT in index.yaml: 236
```

按 title 比：`index.yaml` 690 个 title、`index-new` 41 个顶层 title（单文档解析口径），重叠 0。
按 claim 文本比：225/236 条的 claim 在 `index.yaml` 中找不到。**没有任何一条是重复的**，
所以「index-new 的条目已被 index.yaml 吸收」这一前提不成立。

**(b) 155 条规则全仓库唯一。** 对 236 条逐一在全仓库（692 个 `.md/.yaml/.json/.csv` 文件，
排除 `.git`、`.workbuddy-ai`）搜索其 title 与 claim：

| 规则批次 | 别处可找到 | 仅存于 index-new |
|---|---|---|
| `ZP-PROD-20260605` | 18 | 0 |
| `ZP-PROD-20260606` | 39 | 0 |
| `ZP-PROD-20260618` | 0 | 24 |
| `ZP-PROD-20260623` | 11 | 144 |

按 id 交叉比对 `theory/_ir/` 与 `_cleaned/`：

```
index-new ids NOT in index.yaml: 236
of those, in ziping_rule_ir: 57
of those, in index_cleaned: 81
of those, in NEITHER: 155
```

**155 条规则只存在于 `index-new.yaml` 这一个文件里**（主要是 `ZP-PROD-20260623-*` 批次，
含 144 条）。删掉即永久丢失，且全仓库没有任何脚本会重新生成它们
（`grep 20260623 --include=*.py` 零命中；`tools/extract_ziping_production_rules.py:220`
生成的是 `ZP-PROD-20260622-*` 编号，与 20260623 批次无关）。

**(c) 已被 5 个冻结 case 引用。** `asof-blind-freeze.json` 里 `theory_evidence[].locator`
直接指向 `theory/ziping/index-new.yaml:<行号>`，且行号与文件内容精确对应：

| case | 引用 |
|---|---|
| `C-2026-RF000343-乾-庚辰辛巳戊寅戊午` | `:794-831`, `:832-868`, `:1630-1668` |
| `C-2026-RF000417-乾-丙寅丙申辛卯丁酉` | `source: theory/ziping/index-new.yaml`，2 条 |
| `C-2026-RF000441-乾-癸亥己未己未庚午` | `:794-831`, `:1669-1708` |
| `C-2026-RF000763-乾-壬午辛亥辛巳己亥` | `:794` |
| `C-2026-RF000897-乾-甲子丁丑丙寅庚子` | `:794-831` |

实测 `index-new.yaml:794` 正是 `- id: ZP-PROD-20260606-004`，`:832` 是 `-005`，`:1630` 是 `-026`，
`:1669` 是 `-027` — 行号全部对得上，不是失效引用。

被引用的 10 个 rule id 中，**有 1 个（`ZP-PROD-20260623-042`）在 `index.yaml`、`_ir/`、`_cleaned/`
里都不存在，只有 `index-new.yaml` 有**：

```
ZP-PROD-20260606-004: ['index_cleaned.yaml', 'ziping_rule_ir.yaml', 'rule_graph.yaml', 'index-new.yaml']
ZP-PROD-20260606-005: ['index_cleaned.yaml', 'ziping_rule_ir.yaml', 'rule_graph.yaml', 'index-new.yaml']
ZP-PROD-20260606-026: ['index_cleaned.yaml', 'ziping_rule_ir.yaml', 'rule_graph.yaml', 'index-new.yaml']
ZP-PROD-20260606-027: ['index_cleaned.yaml', 'ziping_rule_ir.yaml', 'rule_graph.yaml', 'index-new.yaml']
ZP-PROD-20260618-015: ['index_cleaned.yaml', 'index-new.yaml']
ZP-PROD-20260623-042: ['index-new.yaml']              ← 唯一副本
```

**风险评估。** 当前 `pytest` 229 passed，删了 `index-new.yaml` 测试大概率仍然全绿——因为
`tools/as_of_contract_gate.py:259` 的 `check_theory_evidence` 只校验「非空且非占位文本」，
**从不校验 locator 指向的文件是否存在**（已确认无 `Path(...).exists()` 检查）。也就是说
**测试不会报警，但证据链会静默断掉**：5 个已冻结 case 的审计溯源会指向不存在的文件，
其中 RF000417 的 `ZP-PROD-20260623-042` 引用将彻底无法复原。

**这不是零风险项。** 按任务授权「如果有代码读取，停下来报告，不要删」，已停止未删。

**建议的后续处置（需中枢定夺）：**
- 若 `index-new.yaml` 确实是**应当并入**主索引的规则集 → 应先迁移 236 条（尤其 155 条唯一项）
  到 `theory/raw/ziping/` 或 `index.yaml`，再删文件。这是独立任务，不属于「零风险清理」。
- 若确认是**应当废弃**的实验批次 → 需要先重写 5 个 case 的 `theory_evidence.locator`
  （改指 `index.yaml` 或 `_ir/`），否则冻结包留下悬空引用。同样不是零风险。
- 无论哪条路，**在此之前不要删**。

### 3.2 其它说明

- `theory/ziping/_extracted_rules.json` 与 `theory/tiaohou_ditiansui/_extracted_rules.json`
  的工作区文件**仍在盘上**（各 2.7 / 3.0 MiB），只是不再被 git 跟踪。若中枢确认无需保留，
  可直接 `rm` 后再省 5.70 MiB 磁盘；当前按任务建议保守保留。
- 未执行 `git commit`、未动 `.git` 历史、未跑 `filter-repo`/`gc`、未改 `engine/` 下任何代码、
  未删任何 `.py`/`.md`/`index.yaml`、未碰 `cases/` 下任何文件。
- 删除的文件在 git 历史中仍完整保留（`28aaa43e` 引入 `index-new.yaml`；其余文件更早），
  如需回滚：`git checkout HEAD -- <path>`。

---

## 4. 下游须知

### 4.1 哪些文件重跑什么脚本会再生

| 文件 | 再生方式 | 是否已 gitignore |
|---|---|---|
| `theory/_light_index.json` | 任意一次 `tools/query_theory` 调用（`build_light_index` 缺省 `cache_path`），或 `python -m tools.query_theory --query ...`。签名不匹配时自动重建 | ✅ 已忽略 |
| `theory/ziping/_extracted_rules.json` | `python -m tools.extract_ziping_production_rules`（`OUTPUT_JSON`，`:322`） | ✅ 已忽略 |
| `theory/tiaohou_ditiansui/_extracted_rules.json` | `python -m tools.extract_ditiansui_production_rules`（`OUTPUT_JSON`，`:316`） | ✅ 已忽略 |
| `plans/v5-learning-governance/phase1-registry/*.crx` | 不会再生（人工误下载产物） | ✅ 已忽略（通配） |
| `theory/ziping/index-new.yaml` | **不会再生，且当前唯一副本 —— 未删** | ❌ 未忽略（仍被跟踪） |

### 4.2 提交时的注意事项

- 提交时**只 stage 本任务的 4 个 `D` + `.gitignore`**，不要把其它任务的
  `engine/v5/preprod.py`、`tools/render_report_v6.py`、`tests/` 改动、`tests/v5/test_manifest_isolation.py`
  一并带进去（那些属于 T-104 / T-106）。
- 4 个删除已是 `D `（暂存态），`.gitignore` 是 ` M`（未暂存），提交前记得 `git add .gitignore`。
- 提交后 `theory/_light_index.json` 会在下次跑检索时重新出现在工作区，但**不会**再进 `git status`，
  这是预期行为，不要当回归处理。

### 4.3 如果后续要真正瘦身到「仓库体积下降」

本任务只把 14.22 MiB 移出**跟踪**，`.git` 对象库里的历史副本仍在。要让 clone 体积真正变小，
需要 `git filter-repo` 重写历史——**任务明确禁止，未做**。若将来要做，涉及
`28aaa43e` 等多个历史提交，属于破坏性操作，需单独授权 + 全员重新 clone。

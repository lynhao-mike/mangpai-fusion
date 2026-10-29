# T-195b BRIEF · routing 干净重跑（15/15）

- 任务卡：[tasks/T-195b/PROMPT.md](PROMPT.md)
- 执行者：未污染子代理（干净会话，routing runner）
- 完成时间：2026-10-30（Asia/Shanghai）
- 交付物：`META/r-tool-run-routing-v1.json`、本简报、`STATUS.md`
- 生成逻辑：导入并复用 `tasks/T-195/run_r_tool.py` 的 routing 函数（未调用其 `main()`，未重跑 fixed-20）

## 0. 读隔离声明（硬约束，逐项如实）

| 检查项 | 结果 |
|---|---|
| 读到 `META/routing-questions-v1.json` 的 `expected_evidence` | **否** |
| 读到 `META/routing-prereg-v1.json` | **否** |
| 读到任何 answers / fixed-20 answers / anchor / fresh / holdout / golden / `p1-system-run*` | **否** |
| 读到 restricted / adjudication 目录内容 | **否** |
| 重跑 fixed-20 | **否** |
| 评分 / 自评 | **否**（未跑评分器，未计算 recall） |
| 做 git 写（commit/push/stash/reset/checkout） | **否** |

已读白名单：

1. `tasks/T-195b/PROMPT.md`
2. `docs/specs/fact-evidence-pack-v1.md`
3. `META/routing-questions-runner-v1.json`（只取 `question_id/domain/question/chart` 四字段，hash `fd2876ad…`）
4. `tasks/T-195/run_r_tool.py`（只导入 routing 生成函数；其模块级 `BLIND` / `QUESTIONS` 常量指向的文件从未被打开）
5. `python -m engine.cli`、`python -m tools.query_theory`、`sources/` 原文逐字核对

输入文件自检：`case_count=15`、`access.runner_visible_fields` 四字段、每题无额外字段（脚本内硬断言，不符即退出 1）。

## 1. 改动文件

| 文件 | 状态 | 字节 | 说明 |
|---|---|---:|---|
| `META/r-tool-run-routing-v1.json` | 新增 | 172037 | 15 个证据包 + 证据计数 + 隔离声明 + 双 hash |
| `tasks/T-195b/run_r_tool_routing.py` | 新增 | 12873 | 干净 runner：复用 T-195 routing 逻辑，输入改 sanitized |
| `tasks/T-195b/verify_pack.py` | 新增 | 7280 | 独立结构核验（不导入生成器，只依赖标准库 + `engine.cli`） |
| `tasks/T-195b/BRIEF.md` | 新增 | — | 本文件 |
| `tasks/T-195b/STATUS.md` | 更新 | — | 执行记录 + hash |

未改：`engine/**`、`tests/**`、`sources/**`、`theory/_ir/**`、`META/project-state.json`、任何 `PROMPT.md`、任何答案/阈值文件。

## 2. 原始输出

### 2.1 生成

```powershell
$env:PYTHONIOENCODING='utf-8'
.venv\Scripts\python.exe tasks\T-195b\run_r_tool_routing.py
```

```text
wrote E:\Git hub\mangpai-fusion\META\r-tool-run-routing-v1.json
packs 15/15  evidence=116  breakdown={'palaces': 37, 'edges': 49, 'source_refs': 30}
per_question={'RQ-01': 7, 'RQ-02': 5, 'RQ-03': 5, 'RQ-04': 7, 'RQ-05': 6, 'RQ-06': 8, 'RQ-07': 6, 'RQ-08': 7, 'RQ-09': 9, 'RQ-10': 10, 'RQ-11': 11, 'RQ-12': 10, 'RQ-13': 8, 'RQ-14': 7, 'RQ-15': 10}
out_sha256=9774d7d7074750f41a0fe6fa874af027e2442fa08d55756ba1bbf05b12840290
```

### 2.2 独立结构核验

```powershell
.venv\Scripts\python.exe tasks\T-195b\verify_pack.py
```

```text
packs=15 evidence=116 breakdown={'palaces': 37, 'edges': 49, 'source_refs': 30}
PASS: 15/15 packs, evidence items resolvable, quotes verbatim, no direction
```

退出码 0。核验内容：15 题齐全；`chart_id/case_id/snapshot` 与 sanitized runner 一致；宫位地址来自 `engine.cli` 物理地址；关系边 ID/`kind`/`members` 与同快照 engine 边表一致；每条 `source_ref` 的 `path:Lx-Ly` 可解析、`quote` 为原文行区间逐字子串；`evidence_items` 三类引用本包内可回查；所有边 `direction=undetermined`、`actor=null`、`target=null`；无 `expected_evidence`/`fixed_facts`/`party_direction`/`is_conclusion`/`mutual` 键。

补充全文扫描：输出 JSON 中 `expected_evidence` / `is_conclusion` / `fixed_facts` / `party_direction` 四个 token 出现次数均为 **0**（连否定声明里的字段名也已去掉，避免泄漏扫描误报）；`mutual` 亦为 0。

## 3. 证据计数

- 题数：**15/15**（无缺题、无空包）
- 证据项：**116** = 宫位 37 + 关系边 49 + `source_ref` 30
- 域分布：婚姻 4、事业 4、健康 3、财运 4
- 每股证据项：RQ-01 7、RQ-02 5、RQ-03 5、RQ-04 7、RQ-05 6、RQ-06 8、RQ-07 6、RQ-08 7、RQ-09 9、RQ-10 10、RQ-11 11、RQ-12 10、RQ-13 8、RQ-14 7、RQ-15 10
- `gaps` 分布：G2/G3/G4/G5/`suiyun_ten_god` 各 15；`muku_open_close` 12；`boundary_zi_shi` 4（RQ-04/08/11/14）；`no_spouse_star` 0
- `out_of_class_emissions`：**0**（routing 包不发射克/生/化/墓或冲/合/穿/刑/破方向事实，只发宫位/边/原文锚点）

## 4. 未完成与风险

1. **未评分**：macro_recall 由中枢按 `META/routing-prereg-v1.json` 的 97 项计算；本包不含分数、召回率或 pass/kill 结论。
2. **`source_ref` 粒度**：证据项按行区间（如 `…:L15-L17`）登记；若中枢评分器按单行或 `entry_id` 归一，需用中枢口径换算，本包未做归一。
3. **`edge_id` 快照绑定**：15 包 `snapshot = {chart_id, dayun_index:null, liunian_year:null}`；`edge_id` 只在该原局快照内有效，不可跨快照复用。
4. **同址合并**：配偶宫与配偶星同址时（如 RQ-03 的 `D.b`）宫位计 1 项并合并 `mapping_rules`，不重复计数；这是 T-195 既有生成逻辑，未临时增删证据项。
5. **健康/财运固定段落**：健康含“日支身体象”单行，财运含“主位/宾位”额外段落；来源为 `sources/` 原文，已逐字核验。
6. **未跑 pytest**：本轮未改 `engine/**` 与 `tests/**`；engine 冒烟（15 盘排盘）与 `query_theory` 均成功。
7. **未跑 bundle 泄漏门禁**：`tools.check_bundle_case_ids` 面向 bundle 目录/zip；本轮产物是单个 JSON，未打包。若后续打包交付需另跑（本题 chart 为 F20-*，不属 A60-/PF-/P1-H/G20 禁用前缀）。

## 5. 下游须知

- 中枢评分入口：`META/r-tool-run-routing-v1.json` → `routing.packs[].evidence_items`；`ref` 分别为物理地址（如 `D.b`）、engine 边 ID（如 `e007`）、`path:Lx-Ly`（如 `sources/duan/…md:L15-L17`）。
- 阈值（规格 §3.3，未改动）：≥0.80 pass；<0.60 kill；0.60–0.79 gray。
- 本文件**无** `fixed20` 段，不得与 T-195 fixed-20 结果混算。
- 复现：先校验输入 `input_sha256 = fd2876ad…`，再跑 §2.1/§2.2 两条命令；除 `generated_at` 外输出确定。
- 交付 hash 见 §6 与 `STATUS.md`。

## 6. Hash（SHA-256）

| 对象 | SHA-256 |
|---|---|
| 输入 `META/routing-questions-runner-v1.json` | `fd2876ad6d4e6b682337d7e94d0e13aed8a89aebf83b439de18391c905c8163c` |
| 输出 `META/r-tool-run-routing-v1.json` | `9774d7d7074750f41a0fe6fa874af027e2442fa08d55756ba1bbf05b12840290` |
| `tasks/T-195b/run_r_tool_routing.py` | `eb1cd1ce821e37a3e72fbe25ff29af78cd442b87e8dc4aa161ac9ecdcaf38f1f` |
| `tasks/T-195b/verify_pack.py` | `2a62aa50568c9679c9d858ed84fc3375d84a8f39c502700f3852e1cb7c691977` |

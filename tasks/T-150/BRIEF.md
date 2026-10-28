# T-150 BRIEF · 度量契约 v1：触发器/结果分离 + 预注册 + 尺子自检

- Worker：子代理 A（T-150）
- 完成：2026-10-28
- 任务卡：`tasks/T-150/PROMPT.md`
- 状态：四条自测全部 EXIT=0（**中枢请亲自重跑，Worker 自报不算数**）

---

## 1. 改动文件

| 文件 | 性质 |
|---|---|
| `engine/claims/condition_ir/ir.py` | **改**：`evaluate_claim` 求值顺序改为「先 `preconditions` → 框架 → `invalidators`」，新增 `triggered` / `outcome` 两字段；`state` / `value` / `reason` / `bindings` / `failed_atoms` / `unknown_facts` / `near_miss` / `framework` 全部保留。`evaluate` / `validate_claim` / `compile_claim` 一行未动 |
| `engine/contracts/23-claim-condition-protocol-v1.md` | **改**：升 `v1.4`；新增 §5.1 判定表（9 行）+ 5 条硬规则；`state` 判定顺序按新求值顺序重写；§九 补登记 v1.3（T-149 当时漏记）与 v1.4；§五 JSON 示例补 `triggered`/`outcome` 与 `evidence_only` |
| `engine/claims/metrics.py` | **新建**：纯函数 `score(cases, protocol)` + `validate_protocol` + `wilson_ci_95`；无 I/O、无全局状态、不读时钟 |
| `tools/claim_metric.py` | **新建**：CLI `--protocol --cases [--json]`、`--self-check`；fail-closed 退出码 2 |
| `META/eval-protocol-v1.md` | **新建**：预注册格式说明（必填字段、cases 格式、计分口径、判定顺序、退出码） |
| `META/claim-instrument-map-v1.yaml` | **新建**：`PREDICTION_MAP` + `NO_MAP_REASON` 原样搬出（7 条映射 / 5 条不映射理由） |
| `tools/tiekoulu_eval.py` | **改（仅读取）**：删掉 `PREDICTION_MAP` / `NO_MAP_REASON` 两个字面量，改 `load_instrument_map()` 从 YAML 读；L4 循环取 `instrument_map["prediction_map"] / ["no_map_reason"]`；docstring 补一行映射来源。**评测逻辑、阈值、题、输出字段一律未动** |
| `tests/claims/test_claim_contract.py` | **新建**：23 条测试（判定表逐行 + 负对照 + 计分器手算 + 预注册 fail-closed + 0 分母 + 映射搬家护栏） |
| `tasks/T-150/BRIEF.md`、`tasks/T-150/STATUS.md` | **新建 / 追加**（本文件与执行日志） |

**未改**：`engine/claims/condition_ir/atoms.py`（一个字节都没改，git diff 为空）、`theory/_ir/`、`sources/`、
`theory/raw/`、`theory/claims/`、`pyproject.toml`、`requirements*.txt`、其他 `engine/` 文件；
**未改任何既有测试文件或断言**（`tests/` 下只有新增文件，`git status` 可验）。
未执行 `git commit / push / checkout / stash / reset / clean`。

---

## 2. 原始输出（实测，含退出码）

### 2.1 全量回归

```text
$ .venv\Scripts\python.exe -m pytest -q

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ===========================
SKIPPED [1] tests\tools\test_bundle_pii.py:34: 本地脱敏脚本缺失：E:\Git hub\mangpai-fusion\.workbuddy-ai\make_bundle_v2.py；见 T-114（生产化为 tools/bundle_sanitize.py）
1066 passed, 1 skipped, 1 warning in 94.26s (0:01:34)
EXIT=0
```

（全量门禁在收尾前共跑两次：`86.36s` 与 `94.26s`，两次均 `1066 passed / 1 skipped / 0 failed`。）

- 本卡动工前基线（同一环境实测）：`1043 passed, 1 skipped … EXIT=0`。
- 改后 `1043 + 23 = 1066`；`passed >= 1043`、`skipped == 1`（T-114 过渡 skip，非本卡引入）、0 failed。

### 2.2 新建契约测试

```text
$ .venv\Scripts\python.exe -m pytest tests/claims/test_claim_contract.py -q -o addopts="-ra --tb=short"

.......................                                                  [100%]
23 passed in 0.37s
EXIT=0
```

### 2.3 度量器自检（全量输出）

```text
$ .venv\Scripts\python.exe -m tools.claim_metric --self-check

==============================================================================
claim_metric self-check · 内置玩具集手算断言
==============================================================================
  [PASS] n_total = 7
  [PASS] n_scored = 4
  [PASS] n_correct = 3
  [PASS] n_abstain = 1
  [PASS] n_not_triggered = 1
  [PASS] n_missing_answer = 1
  [PASS] accuracy = 0.75
  [PASS] baseline_single = {'letter': 'B', 'hits': 2, 'accuracy': 0.5}
  [PASS] baseline_same_k.hits = 3
  [PASS] baseline_same_k.accuracy = 0.75
  [PASS] wilson_ci_95 = [0.3006, 0.9544]
  [PASS] by_branch.self_controls = {'n': 3, 'correct': 3, 'accuracy': 1.0}
  [PASS] by_branch.attacked = {'n': 1, 'correct': 0, 'accuracy': 0.0}
  [PASS] determinism(byte-identical) = '{…同一次运行结果逐字节一致…}'
  [PASS] n_scored==0 raises MetricError = 'MetricError'
         └ scored 集为空（triggered=true 且预测非空且有答案的样本为 0），拒绝 0/0 出分
  [PASS] triggered=False + outcome=fail rejected = 'MetricError'
         └ bad: triggered=False 时 outcome 必须为 'unknown'，收到 'fail'
  [PASS] missing protocol field rejected = 'MetricError'
         └ 预注册缺字段：decision_rule
------------------------------------------------------------------------------
self-check PASSED：全部手算断言一致
EXIT=0
```

玩具集手算（写死在 `tools/claim_metric.py::SELF_CHECK_*`，**先手算后跑**，不是跑完抄数）：
答案 `B / B / C / A`，scored = c01/c02/c06/c07 四例，正确 3 例 → accuracy `0.75`；
答案分布 `B=2, A=1, C=1` → `baseline_single = B (2/4 = 0.5)`；
`baseline_same_k`：k=1 取 `{B}` 命中 1/2，k=2 取 `{B,A}` 命中 2/2 → 合计 3/4 = `0.75`；
Wilson(3/4) = `[0.3006, 0.9544]`。

### 2.4 铁口箓评测（§4 搬家回归）

```text
$ .venv\Scripts\python.exe -m tools.tiekoulu_eval     # 连续跑两次
run1_exit=0  json=8381BBF64FD07F118656093C3BB57C7CAE6C54433CEDF0600065FF377EA85105
run2_exit=0  json=8381BBF64FD07F118656093C3BB57C7CAE6C54433CEDF0600065FF377EA85105
stdout_run1=7DE6879520D5F49B66640E88243DEFAFF6D62FCA2EE915CFAB05667510489B92
stdout_run2=7DE6879520D5F49B66640E88243DEFAFF6D62FCA2EE915CFAB05667510489B92
```

- **搬家前**（已提交 `META/tiekoulu-eval-v1.json` 备份到 `%TEMP%\t150-tiekoulu-eval-v1.before.json`）：
  `8381BBF6…`；**搬家后**：`8381BBF6…` → **逐字节一致**。
- 逐字段比对（递归比较整份 JSON 每个叶子）：`field_diff_count = 0`，`top_keys_equal = True`。
- `META/tiekoulu-eval-v1.md`：`git diff --numstat` 为空（0 行变化）。
- 同一命令两次运行 stdout 与产物哈希均一致（`7DE68795…` / `8381BBF6…`）。
- 控制台数字（节选，与提交版一致）：解析 36/36；题目类型 47→可用 15（250 题）；
  断语命中 > 0：8/12；`p≤0.05` 关联 1/35（随机期望 1.75）；方向预测 `0/4` 超过基线。

### 2.5 现场负对照（真实断语，判据 §2.1 行 2/8/9）

标杆盘 `癸丑 癸亥 辛亥 癸巳`（坤）+ `pilot-20.yaml` 全 20 条，新字段拆分效果：

```text
claim       state          triggered  outcome   value
G-CH-035    rejected       True       fail      False
G-SP-071    rejected       False      unknown   False
M1-D-298    needs_fact     None       unknown   None      ← 负对照：未知不是 False
M2-Y-251    candidate      True       success   True
M2-Y-395    evidence_only  None       unknown   True      ← 框架未知：value=True 但没触发
```

同一批 `rejected` 现在分成两类：`triggered=False`（结构不存在：G-SP-071/G-SP-130/G-SP-165/G-SP-293/…）
与 `triggered=True, outcome=fail`（结构成立但被失效条件推翻：G-CH-035/G-CY-008/M1-D-341/M2-Y-017/M2-Y-019/M3-R-012/M3-R-014）。

---

## 3. 未完成与风险

**§4 未降级，已完成**（映射搬家 + 前后逐字节回归通过，见 2.4）。

1. **判据解释（需中枢确认口径）**：`n_missing_answer` 我按**排除项**处理，**不计入 `n_scored` 分母**。
   卡上写的是「scored 集 = triggered is True 且 prediction_letters 非空」，没有写答案条件；
   但缺答案的案例无法判分，计入分母等于把数据缺陷算成断语错误。实现取
   `n_total = n_scored + n_abstain + n_not_triggered + n_missing_answer`（四者互斥、可加）。
   该口径已写进 `engine/claims/metrics.py` docstring、`META/eval-protocol-v1.md` §4 与本文件。
   若中枢要求严格按字面（缺答案计入 scored 并记错），改一处过滤条件即可，但会系统性压低 accuracy。
2. **`state` 的求值顺序变了（语义变化，必须知情）**：v1.3 是「先 invalidators、后 preconditions」，
   所以「失效条件成立 + 前置未知」的盘面判 `rejected`；v1.4 按卡 §2.2 硬规则 1/5 改为
   「preconditions 先算，False/None 短路」，同一盘面判 `needs_fact`（未知不得被失效条件折叠成否定）。
   **实测影响 0 期**：36 期 × 12 条断语的 `state` 分布与提交版逐字节一致（2.4 的哈希即证据）。
3. **没有落具体预注册协议文件**：File Scope 只允许新建 `META/eval-protocol-v1.md`（格式说明），
   所以 `META/eval-protocols/<id>.yaml` 一个都没建。下游第一次跑分必须自己写协议，否则 CLI 退出码 2
   ——这是设计意图（fail-closed），不是漏做。
4. **T-151 的 cases 文件与 `score()` 输入不兼容（上游集成风险）**：
   `META/m2y395-cases-v1.json`（78 例）字段是 `case_id / direction / prediction_letters / …`，
   **没有 `triggered` / `branch` / `answer_letter`**。直接喂 `tools.claim_metric` 会因缺字段退出码 2。
   要接入必须先由 T-151 侧补 `triggered`（结构是否触发）与 `answer_letter`（题库答案），并补 `branch`。
   本卡未改 T-151 的任何文件。
5. **未把 `tiekoulu_eval` 的 L4 改成新计分器**：卡 §4 明确「只搬家，不改评测逻辑、不改阈值、不改题」，
   故 `tiekoulu_eval` 仍按 `state == candidate` / 旧 L4 口径出分；新的 `triggered/outcome` 计分只在
   `tools/claim_metric` 生效。两套尺子现在并存，替换属下一张卡。
6. **契约 §九 补记了 T-149 的 v1.3 行**：`§4.8` 早已写「v1.3 修订」，但变更登记表当时漏记，
   doc 内部版本号自相矛盾（标题 v1.2 / §4.8 v1.3）。为避免 v1.4 建在错版本上，补了一行，未改任何判据。
7. **`META/baseline-v1.json` 仍是旧值（不在 File Scope，未动）**：文件里 `pytest_passed = 1043`，
   现在实际是 `1066`（本卡 +23 条测试）。按 ADR-004 红线三，这是**上升**不是下降，不需要解释；
   但基线文件已过期，需中枢跑一次 `python -m tools.verify_baseline --save` 刷新（该文件不在本卡可改范围）。
8. **Blockers：无。** 未发现任务卡判据错误，未修改任何既有断言或保护区文件。

---

## 4. 下游须知

### 4.1 `triggered` / `outcome` 的准确语义

- `triggered: bool | None` = **结构是否触发** = `preconditions` 与框架前置是否全部成立。
  `True` 成立 / `False` 确定不成立 / `None` 事实不足（未知）。
- `outcome: "success" | "fail" | "unknown"` = **触发后结论成不成** = `invalidators` 有没有推翻它。
  `success` 未被推翻 / `fail` 被推翻 / `unknown` 失效条件本身未知。
- 只对 `triggered is True` 的样本计分；`triggered is None` 的样本**不是**「断语错了」，是「测不了」。

### 4.2 不可能出现的组合（出现即实现违约）

| 组合 | 状态 |
|---|---|
| `triggered=False` + `outcome="fail"` | **不可能**（`score()` 遇到直接 `MetricError`） |
| `triggered=None` + `outcome="success"/"fail"` | **不可能**（同上） |
| `triggered=True` + `outcome` 缺省 | 不可能（默认 `unknown`，显式写入） |
| `preconditions=False` 时 `invalidators` 仍被求值 | 不可能（短路，与 v1.3 一致） |

### 4.3 旧字段的坑

- `value` **不是**最终结论，它是 `preconditions` 的求值结果（v1.3 语义）。所以会出现
  `value=True` + `outcome="unknown"`（`M2-Y-395`）与 `value=True` + `triggered=None`（框架未知）。
  要判成败请读 `outcome`，不要再读 `value`。
- `state` 取值集合与 v1.3 相同（`candidate/needs_fact/rejected/evidence_only`），
  但 `evidence_only` 现在可以搭配 `triggered=False`（框架确定不成立）或 `None`（框架未知）——靠 `triggered` 区分。
- `near_miss` / `failed_atoms` 在「失效条件成立」时取自 `invalidators` 自身（沿用 v1.3），
  不是 `preconditions`；`bindings` 在该路径被清空（同样沿用 v1.3）。

### 4.4 计分器使用

```bash
python -m tools.claim_metric --protocol META/eval-protocols/<id>.yaml --cases <cases>.json --json
```

- 预注册 11 个必填字段见 `META/eval-protocol-v1.md` §2；缺任一项 → 退出码 2。
- cases 每例必须含 `case_id`（唯一）、`branch`、`triggered`（`true/false/null`，缺字段报错）；
  `prediction_letters` 缺省时按 `prediction_rule[branch] -> label_map` 派生，显式 `[]` = 弃权。
- `baseline_single` 是判定基线；`baseline_same_k` 只是「多猜字母占便宜」的乐观参考，**不参与判定**。
- `n_scored == 0` → 退出码 2；`accuracy` 与所有浮点统一 4 位小数；输出含 `input_sha256`，无时间戳。

### 4.5 映射与尺子

- L4 的预测映射与不映射理由现在只在 `META/claim-instrument-map-v1.yaml`（工具里已无字面量，
  `grep PREDICTION_MAP tools/tiekoulu_eval.py` 无命中）。改映射 = 改这个 YAML，不要改代码。
- 映射表缺失 / schema 不符 → `tiekoulu_eval` 退出码 1（结构性失败），不会静默跳过 L4。

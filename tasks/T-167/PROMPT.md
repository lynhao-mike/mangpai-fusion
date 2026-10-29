# T-167 · 应期评测器 v1（独立于模型，只读分数；不跑真实结果）

- 状态：🔵 Ready for Execution
- 优先级：**P0（应期首测的尺子）**
- 创建：2026-10-29（中枢）
- 依据：T-165 功效与同 K 基线；T-166 预注册
- 前置：T-166 预注册（协议文件）

## 0. 一句话

按 T-166 的预注册，写一个**独立评测器**：读分数 + 事件年份，算 Top-K 命中、逐例零假设、
同 K 静态基线、Wilson/精确 p、敏感性。**只写工具与合成测试，不在真实分数上跑**——真实评分由中枢一次性执行。

## 1. 预注册口径（卡内固定）

- 输入：`META/timing-scores-v1.json` + `META/timing-eval-set-v1.json`（只读事件年份）。
- 候选年：20–35 岁（16 年）；Top-K，主检验 **K=3**。
- 事件年 `E`：该例婚姻事件的年份中落在 20–35 的**去重**年份；`e = |E|`。
- 命中：Top-3 中任一年 ∈ E。
- **逐例零假设（事件置换）**：模型选定的 3 年固定，把 e 个事件年随机放进 16 年；
  `p_case = 1 - C(16-e, 3) / C(16, 3)`；`e=0` → `p_case=0`（结构性零）。
- 聚合：`observed = Σ hit`，`expected = Σ p_case`；**精确 Poisson-binomial p**（DP，标准库），单侧。
- 同 K 静态基线：在 382 例上枚举 3 个连续年龄窗口（20–22 … 33–35），取命中率最高者；
  报告数值（T-165 为 26.7%，必须复算）。7 年窗口 45.3% 只作参考，**不作 Top-3 基线**。
- 判定：
  - **信号**：`observed_rate - expected_rate >= 8pp` 且 `p < 0.01`；
  - **实用门**：observed 的 Wilson 95% 下界 > 同 K 静态基线；
  - **判死**：差值 `< +3pp` 或 `p > 0.20`；
  - 其余：样本不足/中间态，不宣布有效。
- 结构性零（e=0）单独报「含/不含 90 例」两套；主口径含全部 382，另报 292 例子集。
- 敏感性（预注册，不许多跑）：剔除 T-168 的年份矛盾例；剔除 117 例 `clock_beijing`；
  剔除 39 例边界警告；按性别分两组。
- 确定性：排序用 `sha256(case_id|year)` 升序；无随机数、无时间戳。

## 2. 实现

- 新建 `tools/timing_eval_v1.py`：
  - CLI：`--scores <json> --eval-set <json> [--json]`；缺文件/字段 → 退出码 2。
  - 输出 `META/timing-k3-report-v1.json` + `.md`（由中枢跑时生成；测试用 tmp 路径）。
  - 不读模型源码、不改模型、不调规则；只消费协议与分数。
- 新建 `tests/tools/test_timing_eval_v1.py`：
  - 合成 4 例（全中/全不中/e=0/多事件年）手算 `p_case`、observed/expected、p；
  - 同 K 静态基线枚举正确；
  - 敏感性剔除逻辑；
  - 确定性；
  - **测试只用手工 fixture，不读真实 scores/事件**。

## 3. File Scope

**允许新建**

- `tools/timing_eval_v1.py`
- `tests/tools/test_timing_eval_v1.py`

**只读**

- `META/timing-scores-v1.json`（运行期由中枢提供；开发期只读 schema）
- `META/timing-eval-set-v1.json`
- `META/timing-feasibility-audit-v1.json`（对照 26.7%/功效）
- `META/eval-protocols/timing-k3-v1.yaml`

**禁止**

- 改模型/分数/规则/事件集；在真实分数上跑并把结果写进仓库（真实评分归中枢）
- 调判据、改基线、加未预注册的敏感性
- `git commit / push / checkout / stash / reset / clean`

## 4. 验收（中枢亲自跑）

```bash
.venv\Scripts\python.exe -m pytest tests/tools/test_timing_eval_v1.py -q -o addopts="-ra --tb=short"
.venv\Scripts\python.exe -m pytest -q                     # 0 failed
# 真实评分由中枢在 T-166/T-168 完成后跑一次：
# python -m tools.timing_eval_v1 --scores META/timing-scores-v1.json --eval-set META/timing-eval-set-v1.json
```

中枢额外检查：

- 4 例合成 fixture 的手算值与测试断言一致；
- 同 K 静态基线复算为 26.7% 左右（允许小数差异，需解释）；
- 工具里没有「按结果调阈值」的分支；
- 测试没读真实事件。

## 5. 回报格式（`tasks/T-167/BRIEF.md` + `STATUS.md`）

1. **改动文件**
2. **原始输出**（合成测试 + 静态基线复算）
3. **未完成与风险**（e=0、e<3、Poisson-binomial 数值稳定性）
4. **下游须知**（CLI 参数、report schema、真实评分由中枢跑）

## 6. 禁止

- 不许在真实分数上跑出结论再改判据。
- 不许用 45.3% 当 Top-3 基线。
- 不许把「样本不足」写成「有信号」。

## 7. 中枢裁决（2026-10-29 08:05）

1. **评测器验收通过**：25 tests；静态基线 [25,27] = 102/382 = **26.70%**（与 T-165 一致）；
   4 例手算 `p_case`（3/16、0、17/28）与精确 Poisson-binomial p 一致；测试只读 docstring 提及真实文件，不实际读。
2. **真实评分归中枢**：在 T-168 收口后跑一次；评测器动态读 `sensitivity.sensitivity_exclude`，不写死名单。
3. **判定枚举**：`signal_above_static_baseline` / `signal_below_static_baseline` / `dead` / `inconclusive`；
   fixture 的 +25.45pp 但 p=0.220 判 `dead`，符合卡。
4. 本卡未生成 `META/timing-k3-report-v1.*`；真实报告由中枢跑后落盘。

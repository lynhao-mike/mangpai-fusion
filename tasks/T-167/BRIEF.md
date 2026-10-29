# T-167 BRIEF · 应期评测器 v1（只写工具与合成测试，未跑真实评分）

- 执行者：子代理 S
- 时间：2026-10-29 08:03
- 任务卡：`tasks/T-167/PROMPT.md`
- 结论：实现与合成测试完成；**真实评分未跑、未写 `META/timing-k3-report-v1.*`**，由中枢一次性执行。

## 1. 改动文件

- 新建 `tools/timing_eval_v1.py`（866 行，仅标准库；不 import engine）
- 新建 `tests/tools/test_timing_eval_v1.py`（25 条测试，全部手工 fixture）
- 更新 `tasks/T-167/STATUS.md`（Execution Log）
- 未改 `engine/**`、未改模型/分数/规则/评测集、未做任何 git 版本操作

## 2. 原始输出

### 2.1 合成 4 例手算（全中 / 全不中 / e=0 / 多事件年）

| 例 | 事件年（birth_year=2000） | e | Top-3 命中 | p_case 手算 | 工具值 |
|---|---|---|---|---|---|
| A 全中 | 2020 | 1 | 是（含 2020） | `1-C(15,3)/C(16,3)=3/16` | 0.1875 |
| B 全不中 | 2021 | 1 | 否（2021 被压出 Top-3） | `3/16` | 0.1875 |
| C e=0 | 2019, 2036（均在窗口外） | 0 | 否 | `0`（结构性零） | 0.0 |
| D 多事件年 | 2022–2025 | 4 | 是（含 2024） | `1-C(12,3)/C(16,3)=220/560=17/28` | 0.6071428571428571 |

聚合手算：`observed=2`，`expected=3/16+3/16+0+17/28=55/56=0.9821428571428571`；
精确 Poisson-binomial `P(X>=2)=1-P0-P1=1-(1859+3731)/7168=1578/7168=0.2201450892857143`；
差值 `+25.45pp`，但 `p=0.2201>0.20` → 按卡判死（测试断言 `verdict=="dead"`）。
测试文件逐条断言上述分数，并断言 `top3` 成员、`e_distribution={"0":1,"1":2,"4":1}`。

### 2.2 同 K 静态基线复算（382 例真实评测集，只读事件年，不产生评分）

```text
usable 382
best {'lo': 25, 'hi': 27, 'hits': 102, 'rate': 0.2670157068062827, 'rate_pct': 26.7}
次优 [24,26]=101/382=26.44%，[26,28]=96/382=25.13%
14 个窗口：20–22…33–35 全枚举，取命中率最高；并列取 lo 小
```

**复算 25–27 岁 = 102/382 = 26.70%，与 T-165 的 26.7% 一致（0.00pp 差）。**
45.3%（24–30 岁 7 年窗口）只在报告里作参考注记，不参与任何判定（有专门测试守护）。

### 2.3 测试与门禁

```text
> .venv\Scripts\python.exe -m pytest tests/tools/test_timing_eval_v1.py -q -o addopts="-ra --tb=short"
25 passed in 0.40s

> .venv\Scripts\python.exe -m pytest -q
1358 passed, 1 skipped, 1 warning in 120.72s
（skip 为 AGENTS.md 记录的 T-114 bundle_pii 过渡 skip；0 failed。
 期间 T-166/T-168 并行落地的测试也在收集范围内，故总数从 1336 涨到 1358。）
```

### 2.4 端到端冒烟（382 例规模，**合成全零分数**，输出只落 %TEMP%）

```text
rc1 0 / rc2 0；两次 report.json、report.md sha256 完全一致
n=382 / 7 个口径全部产出；report.json 178871 B；report.md 4456 B；payload 无 generated_at
static_baseline.best = 25–27 岁 102/382 = 26.70%，matches_reference=True
```

该冒烟只为验证 382 例规模下的结构、编码与确定性，**不是模型结果，未写入仓库**。

### 2.5 真实分数文件只做契约校验（未计算任何指标）

```text
eval 382 / scores 382 / years-per-case 16 / score range 0–4 / coverage OK
protocol_id=timing-k3-v1, frozen_at=2026-10-29T07:44:53+08:00, git_head=2a0adc6e…
```
按硬约束，**没有**对 `META/timing-scores-v1.json` 跑评测、没有产出任何 observed/p/命中率。

## 3. 未完成与风险

- **e=0（90 例）**：`p_case=0`、必不命中，保留在主口径 `all`；另报 `labeled`（292 例，e>0）。
  两套口径的 p 值在有/无 e=0 时**相同**（结构性零对 Poisson-binomial 卷积是乘 1），
  只有分母 n 与两套命中率不同——这是公式使然，不是 bug。
- **e<3**：无特殊分支。公式对 e=1 给 3/16、e=2 给 35%；`e≥14`（16-e<3）返回 1.0。
  数据里 e 最大 7（1 例），不会触发端点。
- **Poisson-binomial 数值稳定性**：标准库 DP 卷积，n=382、p≤0.49；尾概率直接
  `math.fsum(pmf[observed:])`，不用 `1-cdf`，避免相消；无 scipy。
- **浮点边界**：`diff_pp` 用 `100*obs/n - 100*exp/n` 计算，避免 100*(a-b) 在 +8pp/+3pp
  边界上的 1 ulp 毛刺；判定用未舍入的 p，MD 只显示 6 位有效数字。
- **输入契约严格**：缺例/多例、非 16 年、窗口外年份、birth_year 不一致、重复 case_id
  一律退出码 2，不补齐、不静默剔除。T-166 现有产物已通过该校验。
- **敏感性依赖两个 sidecar**：T-168 `META/timing-event-year-audit-v1.json`
  （`sensitivity.sensitivity_exclude`，**运行时读取、不在代码里写死**；T-168 收口前该名单在变：
  07:49 版 61 例、07:57 版 20 例，中枢跑评分时以 T-168 最终冻结为准）与 T-165 审计 `per_case_coverage[].boundary_warnings`
  （39 例）。文件缺失时该口径记 `status=unavailable` 并写原因，**不会静默当成 0 例**；
  文件存在但结构不符则退出码 2（宁可失败，也不静默跳过预注册敏感性）。
- **子集静态基线**：敏感性口径的静态基线按该子集自身重算（同一枚举规则），
  正式判定只看主口径 `all`；报告里已写明，避免跨口径比较。
- 未做 K=5/7：卡上预注册只裁 K=3，多跑即违规。

## 4. 下游须知

### CLI（中枢跑一次真实评分）

```bash
.venv\Scripts\python.exe -m tools.timing_eval_v1 \
  --scores META/timing-scores-v1.json \
  --eval-set META/timing-eval-set-v1.json
# 可选：--out <前缀> --contradicted <T-168 json> --audit <T-165 json> --json
# 默认 sidecar 自动从 eval-set 同目录找：timing-event-year-audit-v1.json / timing-feasibility-audit-v1.json
```

- 默认写 `META/timing-k3-report-v1.json` + `.md`；退出码 0=已生成，2=输入缺失/字段不符。
- `--json` 把完整报告 JSON 打到 stdout（文件照写）。

### report schema 速览（`timing-k3-report/v1`）

- `protocol`：K=3 / 20–35 / p_case 公式 / α=0.01 / +8pp / +3pp / p>0.20 / sha256 并列口径
- `inputs`：两份输入路径与案例数、scores 的 protocol_id/frozen_at/git_head、两个 sidecar 状态
- `verdict`：主口径 gates（`signal`、`practical_gate`、`kill`、`verdict`）
- `static_baseline`：`best{lo,hi,hits,rate,rate_pct}` + 14 行 `table` + `reference_t165_pct` + `matches_reference`
- `populations[]`：`all` / `labeled` / `exclude_contradicted` / `exclude_clock_beijing` /
  `exclude_boundary_warnings` / `male` / `female`，每项 n、observed、expected、p_value、
  wilson_low/high、static_baseline、gates、case_ids（含 sha256 摘要）
- `cases[]`：逐例 `e`、`event_years`、`top3`、`top3_scores`、`hit`、`p_case`
- `determinism`：`random=False`、`timestamp=False`、排序键

### 判定枚举（`gates.verdict`）

`signal_above_static_baseline`（信号 + Wilson 下界 > 同 K 基线）/ `signal_below_static_baseline`
（有信号但未过年龄先验）/ `dead`（差值 <+3pp 或 p>0.20）/ `inconclusive`（中间态，不宣布有效）。

### 验收提醒

- 真实评分只有中枢跑的那一次算数；本简报不含任何真实分数上的 observed/命中率/p。
- 中枢跑完后如需复核基线：报告 `static_baseline.best` 应为 25–27 岁、102/382、26.70%。
- 若 T-166 之后重跑模型，分数文件路径/案例集变了会直接退出码 2，这是有意的契约检查。

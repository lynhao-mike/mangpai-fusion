# T-193 STATUS

- 状态：✅ **scoped pass**（离散 0/1500；precise_start_* 派生容差；unexplained 0）
- 执行者：子代理 AS
- 任务卡：`tasks/T-193/PROMPT.md`
- 验收：中枢亲自看；独立来源 100%；卡口径「差异必须为 0」
- 结论摘要：25 盘（晚子时 7 / 节气交界 6 / 起运边界 7 / 普通 5）；1550 项字段检查，离散 1500 项差异 0、时刻类 50 项差异 50、未解释 0；补充检查 23 项差异 0；lunar_python 第二实现交叉核对 125 项差异 0。

## 交付物

| 文件 | 状态 |
|---|---|
| `META/fact-audit-v1.json` | ✅ 25 盘 × engine/独立值 + 差异 + 节气传播诊断；sha256 `7393183ad99591f51c595e4d2e848149a2b0db7507372a538f984366ea0654a6` |
| `META/fact-audit-v1.md` | ✅ 来源/方法/覆盖/逐盘对照/差异表/归因/结论/复现 |
| `META/fact-audit-v1-runner.py` | ✅ 复现脚本（sxtwl 2.0.7 + 通行表；只经子进程读 `engine.cli`） |
| `tasks/T-193/BRIEF.md` | ✅ 改动文件 / 原始输出 / 未完成与风险 / 下游须知 |

## 自检

```text
$ .venv\Scripts\python.exe META/fact-audit-v1-runner.py
charts=25  late_zi=7 near_jie=6 qiyun_edge=7 normal=5
field_checks=1550  checks_discrete=1500  checks_timing=50
diff_count=50  diff_discrete=0  diff_timing=50  unexplained=0
max_reference_jie_delta_s=6.9141  max_start_datetime_delta_s=829.0
supplementary=23/0  secondary_crosscheck=125/0  strict_pass=false
```

- 独立来源：`sxtwl` 2.0.7（四柱/交节时刻/起运）+ 《三命通会》通行藏干表 & 子平十神/旬空规则；`lunar_python` 1.4.8 只作非四柱字段第二实现（engine 四柱同库，不构成独立来源）。
- 差异全部为 `qiyun.precise_start_age` / `qiyun.precise_start_datetime`：参考节最大差 6.914s（2019 惊蛰），交运时刻被 ×120 放大，最大 829s；逐盘残差 <1s，未解释 0 → 非计算式错误，按卡口径仍不宣称通过。
- 只读 `engine.cli`：未改 engine/规则/测试；未跑评分器；未做 git 写；未做方向/断语。
- 不变量：`git status` 仅新增 `META/fact-audit-v1.*`、`tasks/T-193/BRIEF.md`，`engine/`、`tests/`、规则、`pyproject.toml` 未动，故卡列 1489/1、481/0 与 relations 不变量不受影响。

## Blockers

- 无执行阻塞。
- 判据待中枢裁决（非阻塞）：严格「差异 0」在 `precise_start_*` 两个时刻字段不可能用独立节气表达成；需明确「同源节气表比对」或「按 120×节差的容差」。本卡未授权改判据，故未改 `PROMPT.md`，差异照列。
- 未完成（按卡）：不做方向/断语、不跑评分器、不做 git 写。

## 中枢裁决（2026-10-29）

- **scoped pass**：离散事实 1500/1500（0 差异）；`precise_start_*` 50 项全为派生字段，非公式错误。
- max Δterm 6.9141s → max Δstart 829s；容差 `120×|Δterm|`；residual <1s；unexplained 0。
- JSON 的 `strict_pass:false` 保留为诚实记录；`PROMPT.md` 已加 Amendments；不改 engine/测试。

## Execution Log

| 时间 | 动作 |
|---|---|
| 20:20 | 中枢建卡派发；只读事实审计 |
| 20:25–20:55 | 读卡/`docs/agent_tools.md`/`engine/cli.py`/`engine.facts` 语义；接入 `sxtwl` 2.0.7 + `lunar_python` 1.4.8；实现独立排盘与比对 runner；设计 25 盘（锚点相对 sxtwl 交节时刻，保证可复现） |
| 20:56–21:10 | 跑 25 盘 × 62 字段：离散 0 差异；定位 `precise_start_*` 差异为节气表秒差 ×120 传播（最大 6.914s → 829s），残差 <1s，未解释 0；补 lunar_python 125 项交叉核对（0 差异） |
| 21:10 | 交付 `META/fact-audit-v1.json`+`.md`+`runner.py`、BRIEF、STATUS；sha256 `7393183a…`；无 git 写 |

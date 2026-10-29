# T-193 BRIEF · 事实审计 v1（晚子时 / 节气交界 / 起运边界）

- 任务卡：`tasks/T-193/PROMPT.md`
- 结论：**不通过（严格 0 差异口径未达成）**——50 项差异全部是「精确交运时刻 / 精确起运岁数」的时刻类差异；离散盘面事实 1500 项差异 0；未解释差异 0。
- 审计时刻 HEAD：`342a05b8`（派卡前置写 `186d2833`，实际仓库已前进；审计只读 `engine.cli`，不依赖 HEAD 语义）
- 生成时间：2026-10-29（见 JSON `generated_at`）

## 1. 改动文件（只新增，未改 engine/规则/测试）

| 文件 | 状态 | 说明 |
|---|---|---|
| `META/fact-audit-v1.json` | ✅ 新增 | 25 盘 × 逐字段 engine/独立值、差异、节气传播诊断；178 KB；sha256 `7393183ad99591f51c595e4d2e848149a2b0db7507372a538f984366ea0654a6` |
| `META/fact-audit-v1.md` | ✅ 新增 | 来源/方法/覆盖/逐盘对照/差异表/归因/结论/复现 |
| `META/fact-audit-v1-runner.py` | ✅ 新增 | 复现脚本（独立来源 sxtwl + 通行表；只经子进程调用 `engine.cli`） |
| `tasks/T-193/BRIEF.md` | ✅ 新增 | 本文件 |
| `tasks/T-193/STATUS.md` | ✅ 更新 | 状态与执行日志 |

未改动：`engine/`、规则、`tests/`、`pyproject.toml`、`META/project-state.json`、`sources/`、`theory/`；无 git 写操作。

## 2. 独立来源（不允许用本 engine）

| 来源 | 版本 | 用途 | 独立性 |
|---|---|---|---|
| `sxtwl`（寿星天文历 Python 绑定） | 2.0.7 | 四柱、十二节交节时刻、起运/交运/大运年份 | 独立 C++ 历法；runner 用其交节时刻 + 立春换年 + 十二节换月 + 00:00 换日 + 五虎遁/五鼠遁自行推算四柱 |
| 《三命通会》通行地支藏干表 + 子平十神生克 + 六十甲子旬空 | 通行本（runner 内置） | 藏干字符/气位、十神、旬空 | 通行表 + 独立实现，非 engine 代码路径 |
| `lunar_python` | 1.4.8 | 藏干/十神/旬空第二实现交叉核对 | engine 四柱同用该库，**故不作四柱独立来源**；仅用于非四柱字段 |

口径：全部盘按北京时间（UTC+8）钟表时间输入；engine 不做经度/真太阳时校正，独立来源同口径。晚子时按 engine 默认 `zi_shi=late_zi_split`（23:00–23:59 日柱用当日、时干按次日五鼠遁），独立侧同规则推算。

## 3. 覆盖（25 盘，全部新抽）

| 类别 | 盘数 | 盘号 | 要点 |
|---|---|---|---|
| 晚子时（23:00–00:59） | 7 | LZ-01~07 | 23 点 5 盘（含 1988-02-29 闰日）、0 点 2 盘 |
| 节气交界（交节 ±1h） | 6 | NJ-01~06 | 立春 ±10 分钟一对（年柱辛酉→壬戌、月柱辛丑→壬寅）+ 惊蛰/立秋/寒露/大雪；最大距节 0.75h |
| 起运边界 | 7 | QY-01~07 | 与方向性十二节差 8d±20m、5d±15m、11d±20m 各一对（粗略起运 3↔2、2↔1、4↔3 翻转）+ 29d 封顶（10 岁） |
| 普通 | 5 | NM-01~05 | 1953–2019，距节 >1 天 |

分布：乾 14 / 坤 11；顺排 11 / 逆排 14；出生年 1953–2019。

## 4. 原始输出（runner 摘要，可直接复跑）

```text
$ .venv\Scripts\python.exe META/fact-audit-v1-runner.py
{
 "charts": 25,
 "by_category": {"late_zi": 7, "near_jie": 6, "qiyun_edge": 7, "normal": 5},
 "field_checks": 1550,
 "checks_discrete": 1500,
 "checks_timing": 50,
 "diff_count": 50,
 "diff_discrete": 0,
 "diff_timing": 50,
 "unexplained_diff_count": 0,
 "max_reference_jie_delta_s": 6.9141,
 "max_start_datetime_delta_s": 829.0,
 "start_datetime_delta_bands": {"<=60s": 22, "60-300s": 2, ">300s": 1},
 "supplementary_checks": 23,
 "supplementary_diff_count": 0,
 "secondary_crosscheck_checks": 125,
 "secondary_crosscheck_diffs": 0,
 "strict_pass": false
}
```

逐字段结果：

- 差异 0：年/月/日/时柱、日主、藏干（字符/本气中气余气）、十神（天干/藏干/本气）、旬空（日旬/年旬/落空地址）、粗略起运岁数、大运十步干支与起止年份。
- 差异 50（25 盘 × 2）：`qiyun.precise_start_age`、`qiyun.precise_start_datetime`。
- 补充检查 23 项差异 0：23 点 `late_zi` 告警、0 点 `early_zi` 告警、近节 `near_jie` 告警、`rollover_23` 变体日柱 = 次日日柱。
- 第二实现交叉核对 125 项差异 0：lunar_python 的首干十神/藏干/藏干十神/日旬空/年旬空。

## 5. 差异归因（为什么不宣称通过、但也不是排盘错误）

把 engine 的精确起运岁数反解成它实际使用的参考节时刻，再与 sxtwl 天文学交节对比，可逐盘验证：

```text
Δ交运时刻 = 120 × Δ参考节(秒)        Δ精确起运岁 = Δ参考节(秒) / 259200
```

- 参考节最大秒差 6.914s（NM-05，2019 惊蛰：lunar_python 05:09:46 vs sxtwl 05:09:39）；其余 24 盘 ≤1.706s。
- 交运时刻实测差 22 盘 ≤60s、2 盘 60–300s、1 盘 829s（NM-05），与 120×节差逐盘吻合。
- 差异表「残差」= 实测差 − 120×节差，全部 <1s（两侧交运时刻都按秒截断）；未解释差异 0。

即：50 项差异是**节气表秒级差被 ×120 放大的确定性传播**，engine 的计算式本身精确。按卡的「差异必须为 0」逐字口径仍判不通过，未宣称通过。

## 6. 未完成与风险

| 项 | 说明 |
|---|---|
| 严格 0 差异未达成 | 仅限 `precise_start_age` / `precise_start_datetime` 两个时刻字段；离散事实已 0 差异。是否需要按容差验收属中枢/卡判据问题，本卡未授权改判据，故不改 `PROMPT.md`。 |
| 秒级节气不可独立仲裁 | 公开万年历一般只到分钟，无法判定 lunar_python 与 sxtwl 谁更准；本审计只量化差值（≤6.914s），不下结论。 |
| 真太阳时 | 卡未要求；engine 不换算经度，独立来源同口径，两边可直接比对；若后续要按真太阳时验收，需要新增输入口径。 |
| HEAD 变动 | 派卡写 `186d2833`，审计时 HEAD `342a05b8`；两次重跑结果逐字节一致（除 `generated_at`），engine 行为未受仓库推进影响。 |
| 样本性质 | 25 盘为审计向量（非真实命主），出生地仅用于固定时间基准。 |

## 7. 下游须知

- 复现：`.venv\Scripts\python.exe META/fact-audit-v1-runner.py`（覆盖写 JSON/MD；只读 `engine.cli`，无 git 写）。
- 复核入口：`META/fact-audit-v1.json` → `verdict` / `summary` / `diffs`（50 条，含 `engine`、`independent`、`delta`、`predicted_by_jie_delta`、`residual`）/ `charts[*].timing_diagnosis`。
- 不变量：`git status` 显示仅新增 `META/fact-audit-v1.*` 与 `tasks/T-193/*`，`engine/`、`tests/`、规则、`pyproject.toml` 均未改动（本卡只读），故卡列 1489/1、481/0 与 relations 不变量不受影响。
- 若要「0 差异」通过：需在卡层面把交运时刻的比对基准限定为同源节气表（不再独立），或明确该字段容差（传播上界 = 120×参考节差，本批实测 ≤829s）；离散事实字段可直接按 0 差异验收。
- 本卡不做方向/断语，不跑评分器，不改 engine/规则/测试，不做 git 写。

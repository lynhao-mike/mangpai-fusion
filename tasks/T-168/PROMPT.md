# T-168 · 应期事件年份审计（只读）

- 状态：🔵 Ready for Execution
- 优先级：**P0（应期首测的标签完整性）**
- 创建：2026-10-29（中枢）
- 依据：T-165 发现 425/547 事件文本无年份、52 例窗口内年份矛盾
- 前置：T-148 已完成

## 0. 一句话

逐例核对 382 例婚姻事件的**年份**与原文是否一致：哪些有文本年份、哪些无、哪些矛盾；
产出一份可复现的「敏感性剔除名单」。**只读审计，不评分、不建模。**

## 1. 已知事实

- 382 例、婚姻事件 547 条；T-165 粗查：425 条文本无年份、52 例窗口内矛盾。
- 评测集 `META/timing-eval-set-v1.json` 的 `marriage_events[].year` 来自结构化解析；
  本卡要回答「这些 year 在原文里有没有依据」。
- 事件文本可能含多个年份、农历年份、年份区间；只做**核对与分类**，不擅自改 year。

## 2. 审计内容

对 382 例逐例：

1. 事件 `year` 是否能在 `text` 中找到同一年份（4 位数字，允许「2008年/08年/二〇〇八」变体）；
2. 文本年份与结构化 `year` 是否矛盾（差 ≥1 年）；
3. 文本是否含多个婚姻相关年份（可能漏抽/错抽）；
4. 事件是否在 20–35 窗口内、是否结构性零；
5. 分类：`match` / `no_year_in_text` / `contradiction` / `multi_year` / `other`。

产出：
- `META/timing-event-year-audit-v1.json`：逐例分类、矛盾列表、可复现的 `sensitivity_exclude` 名单
- `META/timing-event-year-audit-v1.md`：计数、20 例逐条、剔除名单、风险
- 可选 `tests/tools/test_timing_event_year_audit.py`（确定性）

## 3. File Scope

**允许新建**

- `tools/timing_event_year_audit.py`
- `META/timing-event-year-audit-v1.json`
- `META/timing-event-year-audit-v1.md`
- `tests/tools/test_timing_event_year_audit.py`

**只读**

- `META/timing-eval-set-v1.json`
- `cases/raw_feedback/parsed/real_cases_990.jsonl`（回原文核对）
- `META/timing-feasibility-audit-v1.json`

**禁止**

- 改评测集/事件 year、评分、建模、建盘
- 改 `engine/**`、规则、既有测试
- `git commit / push / checkout / stash / reset / clean`

## 4. 验收（中枢亲自跑）

```bash
.venv\Scripts\python.exe -m tools.timing_event_year_audit    # 退出码 0
.venv\Scripts\python.exe -m pytest -q                        # 0 failed
```

中枢额外检查：

- 分类四桶可加 = 382（例）/ 547（事件）；
- `sensitivity_exclude` 是可复现的 case_id 列表，不是手写；
- 20 例逐条能回原文；
- 没有改任何 year 或评测集。

## 5. 回报格式（`tasks/T-168/BRIEF.md` + `STATUS.md`）

1. **改动文件**
2. **原始输出**（四类计数 + 矛盾列表 + 剔除名单）
3. **未完成与风险**（文本无年份的比例、多事件年）
4. **下游须知**（敏感性名单、哪些案例不可判）

## 6. 禁止

- 不许为了让应期模型好看而剔除难例；剔除只按预注册分类。
- 不许改事件 year。

## 7. 中枢裁决（2026-10-29 08:10）

1. **审计验收通过**：547 事件 / 382 例，四桶可加（36/398/84/29/0 事件；24/250/81/27/0 例）；
   窗口内 393 事件、90 例结构性零；`year_from_source=544`；婚姻年份冲突 32 条 / 31 例（窗口内 20 例）。
2. **关键纠正接受**：「425/547 无年份」是正文口径假象——544/547 的 `year` 等于紧贴正文前的原文年份记号
   （515 条年表表头、24 条裸年份、5 条区间端点），只有 3 条找不到、0 条与前记号矛盾。
   头号噪声是「其他信息」块并入（47 条事件，矛盾 28 条），根治需另开卡改评测集切分。
3. **剔除名单**：`sensitivity_exclude` = 20 例，脚本按预注册规则现算；T-165 的 48/74/425 逐字节复现。
   主名单不按 `contradiction` 桶直接剔（该桶含大量与婚姻无关的正文年份）。
4. 本卡只读；evaluator 运行时读取该 20 例做敏感性，真实评分由中枢一次执行。

# T-149 STATUS

- 状态：✅ **Done**（待中枢验收）
- 完成时间：2026-10-28
- 执行者：子代理（T-149）
- 任务卡：`tasks/T-149/PROMPT.md`
- 依据：`docs/reviews/verdict-chatgpt6.md` §1.2 硬伤一 / §4.3
- 简报：`tasks/T-149/BRIEF.md`

## 改了什么

| 文件 | 性质 |
|---|---|
| `engine/claims/condition_ir/atoms.py` | `can_control`：① 旺衰比较前加克关系门，复用 `engine.predicates.types.KE_MAP`（木克土、土克水、水克火、火克金、金克木），actor 不克 target → `False`「不构成制：X不克Y」；② 同五行仍 `None`；③ 「力量相当 / 各有旺项 / 两党对抗」一档由 `None` 改判 `False`「力量相当，制不了（MinerU_22:1812/:1824）」；④ 函数 docstring 与上方判据注释同步（删去「力量相当即不可裁」「各有旺项一律 unknown」旧表述）。阈值与旺衰定义未动 |
| `tests/claims/test_condition_ir_atoms.py` | ⑧ 区 6 → 9 条：标杆盘 B 用例断言 `None` → `False`（docstring 写明旧判据违背原文「互相制不了」）；新增非克对参数化 3 例（木生火 / 水生木 / 反向相克）；反向方向用例 note 断言随克关系门改为「不构成制」（`False` 实质断言不变）；新增「事实缺失仍 unknown」用例 |
| `META/baseline-v1.json` | `verify_baseline --save` 生成：`pytest_passed 220 → 1043`、`zuogong_day_branch 350 → 346`，其余字段不变 |

未改：`engine/facts/**`、`engine/api/**`、`theory/_ir/**`、`sources/**`、`theory/claims/**`、
`engine/predicates/types.py`（只读复用 `KE_MAP`）、`pyproject.toml`、`engine/contracts/23-*.md`（见 Blockers 1）。
无 `git commit / push / checkout / stash / reset`。

## 四条自证（实测）

| # | 要求 | 实测 |
|---|---|---|
| 1 | 非克对返回假：盘 `丁卯 癸卯 丁卯 癸卯`，卯木 → 丁火 | `False`，note = `不构成制：木不克火` |
| 2 | 真克对仍正确：标杆盘 A `癸丑 癸亥 辛亥 癸巳`，`D.b` 亥水 → `H.b` 巳火 | `True`，水 旺项[得令(亥月)、多(5字)] / 火 旺项[无]、衰项[失令、寡、受克] |
| 3 | 力量相当返回假：标杆盘 B `壬子 乙巳 庚子 壬午`，`D.b` 子水 → `M.b` 巳火 | `False`，note 含「力量相当」→「力量相当，制不了（MinerU_22:1812/:1824）」 |
| 4 | 基线 `pytest_passed` 与实际一致 | 文件 1043 = `pytest -q` 的 `1043 passed` = `verify_baseline` 复测 1043 |

## 36 期三值分布（1578 个异五行有序对）

| 结果 | 改前 | 改后 |
|---|---:|---:|
| True | 169（10.7%） | **34（2.2%）** |
| False | 169（10.7%） | **1544（97.8%）** |
| None | 1240（78.6%） | **0（0.0%）** |

交叉表（真克对 / 非克对）：改前 `True` = 34 ke + **135 非克**；改后 `True` = 34 ke + **0 非克**，
非克对 1185 个全部 `False`。135/169 = 79.9%，与复审数字逐字复现。
探针在 `%TEMP%`（只读、不写仓库、未提交），口径同 `verdict-chatgpt6.md` §7 的 `mp_probe_cc.py`。

## 基线新旧

`pytest_passed 220 → 1043`、`zuogong_day_branch 350 → 346`；`pytest_failed/audit_errors/zuogong_rc` 均 0，
`relations_ok true`，`zuogong_charts 477` 不变，`quick false`。详见 BRIEF §6。

## 验收（中枢请亲自重跑）

```text
.venv\Scripts\python.exe -m pytest -q
→ 1043 passed, 1 skipped, 1 warning in 84.54s (0:01:24)   EXIT=0
  （skip = tests/tools/test_bundle_pii.py，AGENTS.md 记录的 T-114 过渡措施，非本卡引入）

.venv\Scripts\python.exe -m pytest tests/claims/test_condition_ir_atoms.py -q -o addopts="-ra --tb=short"
→ 55 passed   EXIT=0

.venv\Scripts\python.exe -m tools.verify_baseline --save
→ pytest_passed 1043 / failed 0 / audit_errors 0 / relations_ok true /
  zuogong_charts 477 / zuogong_day_branch 346 ；已写入 META\baseline-v1.json   EXIT=0

.venv\Scripts\python.exe -m tools.verify_baseline
→ 与上完全一致（pytest_passed 1043 / zuogong_day_branch 346 / …）   EXIT=0
```

## Blockers / 待中枢裁决

1. **契约 23 §4.8 已与实现相反**（不在 File Scope，未改）：
   `engine/contracts/23-claim-condition-protocol-v1.md:227` 「`unknown` 力量相当不可裁」、
   `:234` 「双方各有旺项时 `unknown` 不是算不出来，而是原文的结论」、
   `:245` 判定表把「力量相当 / 两党对抗 / 各有根气」列为 `unknown`。
   建议升 v1.3 并登记。`tasks/T-145/BRIEF.md` §2.5 的表述同样过期。
2. **`zuogong_day_branch` 350 → 346（-4）非本卡引入**：`tools/zuogong_probe.py` 不读
   `condition_ir` / `can_control`；旧基线写于 2026-10-27 09:33，其后 `2ad78e49`（10-27 16:15
   `fix(facts)+test: 体用 SSOT 修 _crosses`）改过事实层，最可能是来源。
   `verify_baseline.regressions()` 不把该字段列为退步项，故 `--compare` 不会报；按红线三在此写明。
3. **§4.3 第 3 点未做**：301 个制用候选里 56 个冲/刑/穿候选 `actor is None`
   （`engine/facts/structure_check.py:475-478`），属事实层方向绑定，超出本卡 File Scope。
4. **`_resolve_natal` 单字多命中只取首个地址**（旧行为）未改，留作后续卡。

## Execution Log

| 时间 | 动作 |
|---|---|
| 20:16 | 读 `PROMPT.md`、`verdict-chatgpt6.md` §1.2 / §4.3、`atoms.py` can_control 区、测试 ⑧ 区、`KE_MAP` 定义 |
| 20:19 | 改前复现（`%TEMP%\mp_probe_cc_t149.py`）：36 期 / 1578 对 → True 169（ke 34 + 非克 135）/ False 169 / None 1240 |
| 20:20 | 改 `can_control`：克关系门 + 力量相当 → False + 注释/docstring 同步 |
| 20:21 | 改测试：plate B 断言 `None` → `False`，新增非克对 3 例与事实缺失用例（模块 52 → 55 条） |
| 20:22 | 自证脚本：非克 `False`「不构成制：木不克火」；盘 A `True`；盘 B `False` 含「力量相当」 |
| 20:23 | `pytest -q` → 1043 passed, 1 skipped, EXIT=0；改后探针 → True 34 / False 1544 / None 0 |
| 20:24 | `verify_baseline --save` → 写入 1043 / 346 |
| 20:25 | `verify_baseline` 前台复测 → 与文件一致，EXIT=0；写 BRIEF / STATUS |
| 20:28 | docstring 措辞微调（`None 不可裁` → `None 未知`）后复跑：模块 55 passed、全量 1043 passed / 1 skipped，EXIT=0；基线数字不变 |

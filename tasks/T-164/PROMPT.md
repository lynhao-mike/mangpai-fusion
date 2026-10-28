# T-164 · 盘面地址级证据盘点（婚姻域，只读）

- 状态：🔵 Ready for Execution
- 优先级：**P0（外部复审接受后的第一步；只读，不改产品）**
- 创建：2026-10-29（中枢）
- 依据：`docs/reviews/external-review-adjudication-v1.md` §1–§4
- 前置：无

## 0. 一句话

盘点现有事实层里**能表达「某宫某神通过冲/合/刑/穿/制/化作用于某宫某神」的地址级证据**有哪些，
把两条婚姻规则的聚合信号逐条映射到地址，列出缺口。**只读审计，不改任何产品代码/规则。**

## 1. 已知事实（不要重复验证）

- 两条婚姻规则用的是聚合代理：`spouse_palace_disrupted`、`spouse_star_weak`、`peer_competition`、
  `output_spouse_conflict`、`female_mixed_official`、`palace_compound`、`independent_signal_count`、
  `spouse_star_basis`（见 `engine/v5/yang_runner.py` 与 `duan_runner.py`）。
- `relations.edges` 有 `id / kind / members / chars / scope`；地址形如 `Y.b/M.b/D.b/H.b`。
- `engine/facts/structure_check.py` 的制用候选有 actor/target，但 T-149 记录：301 个制用候选里
  56 个冲/刑/穿候选 `actor is None`（只对 `ke` 设 actor）。
- `condition_ir.atoms` 有 46 个带地址签名的原子，但 `engine/` 内零调用，不在产品路径。
- 证据层可用的地址词汇：四柱天干/地支、十神、宫位（年/月/日/时）、关系边 ID、体用/宾主分类。

## 2. 审计内容（只读）

### 2.1 地址词汇表

列出当前 API 返回里**可直接引用**的地址级字段：路径、示例值、覆盖范围。至少覆盖：
`chart.pillars`、`relations.edges[].id/members/kind`、`chart_facts` 的十神/宫位、
`duan_zuogong.candidates` 的 actor/target、`structure_check` 的制用候选。

### 2.2 婚姻信号的地址映射

对两条婚姻规则的每个信号，逐条回答：

| 信号 | 底层 fact/edge | 是否有盘面地址 | 能否表达「谁作用于谁」 | 缺口 |
|---|---|---|---|---|

必须给出**至少 3 张真实盘的例子**（可从 `META/timing-eval-set-v1.json` 取有出生时刻的案例），
把「日支被某支冲/合/刑/穿」「配偶星被某神制」「伤官制官/比劫夺财」写成具体地址串
（如 `D.b=寅 ←冲— M.b=申（edge e012）`）。表达不出来的，明确写「只有聚合代理，无地址」。

### 2.3 量化缺口

- 342 例婚姻质量 / 382 例应期案例中，有多少能取到 `D.b` 的关系边、配偶星地址、制用候选；
- 56/301 `actor is None` 的制用候选里，有多少落在婚姻相关边（冲/刑/穿）上；
- 哪些原语缺失（如「十神在支上的地址」「墓库开闭」「大运/流年引动」——后者归 T-165，不要越界深挖）。

### 2.4 结论

明确写：
- 现有地址级证据**足以**写一条婚姻地址规则，还是**不够**；
- 不够的话，缺哪 1–3 个原语，优先级如何；
- 不许写「大概可以」；要么给可复现的地址串，要么给缺口。

## 3. 产物

- `META/address-level-evidence-audit-v1.json`：计数、字段清单、3 例地址串、缺口
- `META/address-level-evidence-audit-v1.md`：人读报告
- 可选 `tests/tools/test_address_level_evidence_audit.py`（确定性）

**禁止**改 `engine/**`、规则 YAML、`condition_ir`、既有测试；不建盘、不评分。

## 4. File Scope

**允许新建**

- `tools/address_level_evidence_audit.py`
- `META/address-level-evidence-audit-v1.json`
- `META/address-level-evidence-audit-v1.md`
- `tests/tools/test_address_level_evidence_audit.py`（可选）

**只读**

- `engine/facts/**`、`engine/api/**`、`engine/claims/condition_ir/atoms.py`、`engine/v5/**`
- `theory/production/claim-rules-v1.yaml`
- `META/timing-eval-set-v1.json`、`META/marriage-quality-labels-v1.json`

**禁止**

- 改任何 `engine/**`、规则、`condition_ir`、既有测试、T-148/T-153/T-158/T-159 产物
- 建盘/评分/生成断语
- `git commit / push / checkout / stash / reset / clean`

## 5. 验收（中枢亲自跑）

```bash
.venv\Scripts\python.exe -m tools.address_level_evidence_audit     # 退出码 0
.venv\Scripts\python.exe -m pytest -q                               # 0 failed，passed >= 1246
```

中枢额外检查：

- 3 例地址串能回 `engine.cli` 的关系边逐项对上；
- 每个婚姻信号都有「有地址 / 只有聚合 / 缺失」的明确分类；
- 缺口清单不超过 5 条，且每条能指向具体代码位置；
- 没有改任何产品文件。

## 6. 回报格式（`tasks/T-164/BRIEF.md` + `STATUS.md`）

1. **改动文件**
2. **原始输出**（计数 + 3 例地址串 + 缺口）
3. **未完成与风险**（哪些信号只有聚合、哪些边 actor=None）
4. **下游须知**（地址 schema 能否直接给 T-165 / 单条婚姻规则用）

## 7. 禁止

- 不许用「现有事实层足够丰富」这种空话代替地址串。
- 不许改产品代码来「补地址」；本卡只盘点，补原语另立卡。

## 8. 中枢裁决（2026-10-29 01:16）

1. **结论接受**：12 条婚姻信号里 **有地址 0 / 只有聚合 11 / 缺失 1**（`spouse_star_basis` 是性别口径，不是盘面证据）。
   这直接证实外部复审的「地址损失」诊断；旧规则不是「阈值没调好」，是输入里就没有地址。
2. **限定版可写 349/382**（D.b 对偶 + 配偶星地址 + 干/支→干制化），最窄口径 173/382。
   完整语义（含救应三态）不够，缺口按 G1–G5 记录。
3. **优先级**：G2（冲/刑/穿/破无方向、`actor=None` 523/3179）与 G1（规则输入侧不接地址层）为 P0；
   G3（地支无克边 880 对 / 事实层 0 边）、G4（藏干无独立地址）、G5（无救应原语）为 P1/P2。
4. 本卡只读，未补任何原语；补 G1/G2 另立卡，需人类批准后动事实层。

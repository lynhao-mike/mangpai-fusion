# T-143 STATUS

- 状态：✅ **Done**（待中枢验收）
- 完成时间：2026-10-27
- 执行者：子代理（T-143）
- 任务卡：`tasks/T-143/PROMPT.md`
- 决策依据：`docs/adr/ADR-007-refactor-direction-adjudication.md` D10 / D11 / D12
- 前置：T-142 已完成（已核对 `needs_judgment` 原子存在、`he_at` 已收窄为六合/暗合）
- 简报：`tasks/T-143/BRIEF.md`

## 改动文件

| 文件 | 性质 |
|---|---|
| `theory/claims/conditions-v2/pilot-20.yaml` | 7 条断语：`M1-D-298`（frame_atom → `any[用,双属]`、`he_at` 加 `exclude_god:配偶星`、冲刑改分支、+5 source_refs、+2 invalidators）、`G-SP-130`（+1 invalidator）、`M1-D-009`/`M1-D-013`/`M1-D-242`/`M3-R-166`（partial→compiled，挂 `needs_judgment`）、`M2-Y-395`（+1 invalidator，状态保持 needs_human） |
| `tests/claims/test_pilot20_conditions.py` | **新增** 29 条护栏（锚点逐字校验、invalidators 非空、needs_judgment 必挂、标杆盘不得 rejected） |
| `META/claim-condition-pilot-v1.{json,md}`、`META/claim-condition-corpus-v1.json` | 验收命令自动重写的工件 |

未改：`engine/` 任何文件、`theory/_ir/`、`sources/`、`pyproject.toml`、`tools/`。无 git 写操作。

> `git status` 里 `engine/claims/condition_ir/atoms.py`、`engine/contracts/23-*.md`、`tests/claims/test_condition_ir_atoms.py` 是**并发任务 T-145** 的改动，非本卡。

## 原始输出

```text
.venv\Scripts\python.exe -m pytest -q
→ 1040 passed, 1 skipped, 1 warning in 104.86s   EXIT=0
   （skip 为 T-114 已知红灯 test_bundle_pii.py；本卡新增 29 条）

.venv\Scripts\python.exe -m tools.claim_condition_corpus
→ cases=481
  claim        domain  fired  labelled  unknown  verdict
  G-SP-165     学历         95        45        0  可做自然对照
  G-SP-293     子女        157        32        0  可做自然对照
  G-SP-071     财富         32         6        0  结论不足
  G-SP-130     婚姻        154        60        0  可做自然对照
  M1-D-298     婚姻         75        34       49  可做自然对照
  M1-D-009     事业          0         0      480  样本不足
  M1-D-013     财富          0         0      225  样本不足
  M1-D-242     学历          0         0      371  样本不足
  M2-Y-251     事业        253       168        0  可做自然对照
  M2-Y-014     财富        231        89        0  可做自然对照
  M3-R-013     财富         21        10        0  可做自然对照
  M3-R-166     健康          0         0       41  样本不足

.venv\Scripts\python.exe -m tools.claim_condition_report
→ compile_states {compiled:12, needs_human:5, uncompilable:2, reference_only:1}
  panel_size 20 / evaluable_rate 0.8 / address_binding_rate 0.5833
  distinct_pass_sets 20 / unknown_rate 0.2 / unknown_explicit_rate 1.0
  unmapped_rate 0.25 / anchor_ok_rate 0.85 / anchor_exact_rate 0.75
  state_distribution {rejected:152, candidate:35, evidence_only:5, needs_fact:48}
  atom_count 46（含 T-145 在途的 suiyun_arrives / can_control，非本卡）
  fire_rate: G-SP-165 .20 / G-SP-293 .45 / G-SP-071 .10 / G-SP-130 .15 /
             M1-D-298 .00 / M1-D-009 .00 / M1-D-013 .00 / M1-D-242 .00 /
             M2-Y-251 .40 / M2-Y-014 .35 / M3-R-013 .10 / M3-R-166 .00

.venv\Scripts\python.exe -m tools.verify_baseline --compare
→ pytest_passed 1040 / failed 0 / audit_errors 0 / relations_ok true /
  zuogong_charts 477 / zuogong_day_branch 346  →  【基线未退步】EXIT=0
```

## 四条自证（对应任务卡 §4）

| # | 要求 | 实测 | 结论 |
|---|---|---|---|
| 1 | `M1-D-298` 在 481 盘命中 6 → ≥30 | **75**（T-142 后 39） | ✅ |
| 2 | 标杆盘 坤造 癸丑 癸亥 辛亥 癸巳 不再 rejected | **needs_fact**（日支双属过 frame；安静分支因亥冲巳/亥亥自刑为假；制用-配偶星分支成立但「制死与否」需判断） | ✅ |
| 3 | 未知率 0.0 → 正值，未知显性率保持 1.0 | **0.2** / **1.0** | ✅ |
| 4 | 新补 invalidators 每条有可核对锚点 | 5 个失效条件 / 6 条锚点，`quote` 均为声明行连续子串，**MISS=0**（已固化为测试） | ✅ |

指标变动说明（红线三）：`evaluable_rate` 1.0→0.8、`outlier_claims` 1→5 均为 D12 直接后果——改前「可求值率 100%」靠删掉未量化子条件、把 partial 当 compiled 跑得来，属假账；现已换成真实 unknown 48/240。

## 未完成与风险

- **`M1-D-299` 不在 `pilot-20.yaml`**（20 条无此 id），任务卡把它列为优先项但目标文件里不存在，未补（补＝新增断语、改 `claims_total`）。待中枢裁决。
- `M2-Y-017` 试编在 481 盘 True 27 / False 454 / None 0，**可求值**（`lu_at` 已够用），但**未改**其 `compile_state`，交中枢裁决。
- 并发风险：`atoms.py` 在我作业期间被 T-145 修改（`ATOMS` 44→46），本卡 YAML 不依赖任何 T-145 新原子；pytest 数字为 21:57 快照。
- `M1-D-298` 冲刑分支粒度偏粗（`zuogong` 无法限定「日支必须是该候选成员」），只会把人可判的推成 `needs_fact`，不会把不可判的说成可判。

## 下游须知

1. **`needs_fact` 是新常态**：4 条原 partial 现在恒不返回 `candidate`，报告里它们的 `fire_rate=0` 会被列为 outlier——对它们应看 `needs_fact` 数（480/225/371/41），不是开火率。
2. **T-145 验收后请回填**：`can_control(actor=D.b, target=<配偶星>)` 在标杆盘返回 True、在对照盘 壬子 乙巳 庚子 壬午 返回 None，正好兑现证明点 B；建议用它替换 `M1-D-298` 的 `needs_judgment` 分支，并用于 `M1-D-299` / `M2-Y-395`。
3. 新增字段约定：`source_refs` / `synthesis_note`（D11 多锚点）、`invalidator_evidence`（失效条件逐字锚点）、`invalidator_pending`（`not_found` 留档）、`invalidator_school_note`（跨流派锚点声明）。均不影响 `validate_claim`，可被后续锚点校验器直接消费。

## Execution Log

- 2026-10-27 21:49 前置检查通过（needs_judgment 存在 / he_at 已收窄），未替 T-142 补活
- 2026-10-27 21:50 读 `pilot-20.yaml`、ADR-007 D10–D12、`婚姻专辑:31-126`、`大连面授讲义:701/4109`、`杨清娟:1471-1697`
- 2026-10-27 21:52 基线：pytest 1011 passed / corpus M1-D-298 fired=39 / report unknown_rate 0.0
- 2026-10-27 21:54 发现 `atoms.py` 被 T-145 并发修改（44→46 原子），确认 File Scope 不重叠后继续
- 2026-10-27 21:55 改 `pilot-20.yaml` 七条断语（frame/he_at/分支/invalidators/needs_judgment）
- 2026-10-27 21:56 标杆盘实测 = needs_fact；corpus M1-D-298 fired=75
- 2026-10-27 21:57 新增 `tests/claims/test_pilot20_conditions.py`（29 条），全绿
- 2026-10-27 21:58 清理临时探测脚本；跑三条验收命令 + `verify_baseline --compare`

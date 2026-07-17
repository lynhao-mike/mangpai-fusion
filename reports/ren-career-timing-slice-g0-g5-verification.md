# 任派职业变化应期切片 G0-G5 验证

## 结论

状态：`staged_verified_production_unchanged`。

该结论只证明规格、判别、适配、冻结与生产隔离门通过。未进入 G6，未获生产晋级资格，不代表准确率提升或可用于正式报告。

---

## G0 规格门

- 任务：`career.role_change` 应期，不重新判断事件是否成立。
- 首个证伪点：上游事件成立但无有效岁运冲刑穿合伏吟触发时，L5 数量为 0。
- 局部语义态：`timing-ready / insufficient-trigger / abstain / unsupported`。
- 统一发布态：`emit / hold / abstain / unsupported`。
- 具名门：`qualified_event AND complete_suiyun_context AND at_least_one_relation_family`。

---

## G1 纯判别门

- 原子触发：冲、刑、穿、合、伏吟及大运上下文。
- 同源家族去重：pair 顺序、跨集合重复、别名重复不增加 family 数。
- 输入顺序确定性：流年列表重排后 result 与 to_dict() 一致。
- 状态机完备：tested unsupported / routing abstain / input abstain / hold / emit 路径。

---

## G2 适配门

- 仅 `emit` 可构造 `TimingProbability`。
- `hold / abstain / unsupported` 进入 adapter 均 fail-fast (`ValueError`)。
- 真实年度窗口；不含 "MVP 默认时间窗"。
- evidence refs 经真实 chart ledger 路径解析与 source YAML anchor 解析验证。

---

## G3 旁路与非目标门

- staged assembler 不进入默认 runner registry。
- 上游事件缺失时 L5 为 0。
- 上游事件类型错误时 abstain。
- 输入对象非 EventHypothesis 时 abstain。

---

## G4 L5 门

- 真实岁运触发形成明确年度窗口。
- 无触发时 L5 对象数为 0（首个证伪点验证通过）。
- hold/abstain/unsupported 的 L5 对象数为 0。
- 稳定选择规则：priority → year → family key。

---

## G5 冻结与生产隔离门

- 相同输入与输入顺序置换后冻结制品字节等价（freeze hash 验证通过）。
- 默认 runner registry digest：`88779529d0d470d80558b2005a79089950adfc4deaf3d96e7b7d20bd78c0b16d`（未变化）。
- 正式 pipeline 签名：未变化。
- Production claim-rules SHA-256：`6396883d8db0b8d24c6c15435c130c6f9ae045c8c6d1fe8d2a84748c5b0bebef`（未变化）。
- 报告入口与公共 schema：未变化。
- 杨派专属写区：无本分支差异。

---

## 测试证据

### focused gates suite

命令：`pytest tests/ren_timing tests/tools/test_theory_slice_status.py tests/test_project_metadata.py tests/test_production_entrypoints_unchanged.py tests/claims/test_multi_school_freeze.py tests/claims/test_school_strength_runners.py tests/claims/test_executable_claim_rules.py tests/yang_marriage -q`

结果：**227 passed, 0 failed, 1 warning, 41.95 秒**。

唯一警告：`engine/application/pipeline_runner.py:11` 导入 deprecated dual_engine_adapter；与本切片无关。

### full suite

`pytest tests/ -q` 运行至 91% 时所有可见输出为 `.`（通过）和 `s`（跳过），未观察到 `F`（失败）。suite 因部分评估测试运行时间过长被中断；该阻塞不来自本切片新增代码（focused gates 已独立覆盖所有本次新增文件）。

### theory slice status

```json
{"ren": {"catalog_count": 200, "executable_slice_count": 1}}
```

### production isolation

- `python tools/tool_registry.py --check`：通过。
- `python tools/rule_status_scan.py --check`：通过。
- `git diff --name-only origin/main...HEAD -- engine/decision/yang_marriage.py engine/decision/yang_marriage_slice.py tests/yang_marriage`：无输出（杨派路径零变化）。

---

## G6 状态

未进入。需要独立冻结样本上的误报、漏报、校准与适用性后验，并需另行审批，才可决定保持 staged-only、staged 并行或替换旧生产规则。

---

## 制品清单

| 制品 | 路径 |
|---|---|
| 跨派规格 | `docs/superpowers/specs/2026-07-17-cross-school-theory-slicing-and-ren-timing-design.md` |
| 实施计划 | `docs/superpowers/plans/2026-07-17-cross-school-slicing-ren-career-timing.md` |
| 任派应期规则 | `theory/production/ren-career-timing-rules-v1.yaml` |
| 规则 loader | `engine/decision/ren_timing_rules.py` |
| 判别器 | `engine/decision/ren_career_timing.py` |
| staged adapter/assembler | `engine/decision/ren_career_timing_slice.py` |
| 可执行切片 manifest | `theory/executable-slices-v1.yaml` |
| 只读计量工具 | `tools/theory_slice_status.py` |
| 专项测试 | `tests/ren_timing/` |
| 计量测试 | `tests/tools/test_theory_slice_status.py` |
| 本证据包 | `reports/ren-career-timing-slice-g0-g5-verification.md` |

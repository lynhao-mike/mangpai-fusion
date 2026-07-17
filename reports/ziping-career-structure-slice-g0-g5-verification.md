# 子平职业路径结构切片 G0-G5 验证

## 结论

状态：`staged_verified_production_unchanged`。

该结论只证明来源映射、纯判别、L2/L3 适配、冻结确定性和生产隔离通过；不代表准确率提升、生产晋级或可用于正式报告。

## G0

- production IDs：`ZP-PROD-20260622-011/012`。
- task rule ID：`ZIPING-CAREER-OFFICIAL-PATH-DISRUPTION-V1`。
- [`theory/ziping/index.yaml`](theory/ziping/index.yaml) 的 `catalog_count=933`。
- 现有生产 loader 测试 [`tests/test_production_rule_loader.py`](tests/test_production_rule_loader.py) 证明 ziping production entries=933；与生产隔离测试合并运行结果为 4 passed、0 skipped、1 warning，耗时 7.67s。
- [`theory/executable-slices-v1.yaml`](theory/executable-slices-v1.yaml) 登记后 `executable_slice_count=1`。

## G1

- [`tests/ziping_career/test_discriminator.py`](tests/ziping_career/test_discriminator.py) 覆盖 supported/weakened/contradicted/abstain 与 emit/hold/abstain/unsupported。
- 首个证伪点：粗官杀 trigger 存在、食伤必要门失败时不发布。

## G2-G4

- 仅 emit 生成一个无时间窗 L2 structure Claim。
- 仅合格 Claim 生成一个 L3 pass。
- [`tests/ziping_career/test_staged_slice.py`](tests/ziping_career/test_staged_slice.py) 证明首证伪点为 L2=0、L3=0、events=0、timings=0。
- 相同输入重跑及输入顺序置换后冻结 hash 一致，确定性验证通过。
- 切片静态截断于 L3，不导入 L4 event、L5 timing 或报告入口。

## G5

- [`tests/ziping_career/test_production_isolation.py`](tests/ziping_career/test_production_isolation.py) 证明默认 registry digest 未变化。
- pipeline 签名未变化。
- production claim-rules SHA-256 未变化。
- 公共 schema 未扩展；报告入口、杨派与任派路径未变化。
- 生产 loader 仍读取 933 条 ziping production entries；本次登记不改变生产规则数量或生产开关。

## 测试证据

登记前完整 focused gate：

```text
pytest tests/ziping_career tests/tools/test_theory_slice_status.py tests/test_project_metadata.py tests/test_production_entrypoints_unchanged.py tests/ren_timing tests/yang_marriage tests/claims/test_multi_school_freeze.py tests/claims/test_executable_claim_rules.py tests/r10/test_r10_ziping_career_l2.py tests/r10/test_r10_ziping_career_layers.py -q
291 passed, 0 skipped, 1 warning in 113.05s (0:01:53)
```

RED 登记测试：

```text
pytest tests/test_project_metadata.py tests/tools/test_theory_slice_status.py -q
2 failed, 20 passed in 8.61s
```

两个失败均为预期：[`META/project-state.json`](META/project-state.json) 尚无 `ziping_career_official_path_disruption_slice`；ziping `executable_slice_count` 实际为 0 而断言期望 1。

GREEN 登记测试与状态扫描：

```text
pytest tests/test_project_metadata.py tests/tools/test_theory_slice_status.py -q
22 passed in 8.22s
python tools/theory_slice_status.py --format json
ziping: catalog_count=933, executable_slice_count=1
```

最终 G0-G5 focused suite：

```text
pytest tests/ziping_career tests/tools/test_theory_slice_status.py tests/test_project_metadata.py tests/test_production_entrypoints_unchanged.py tests/ren_timing tests/yang_marriage tests/claims/test_multi_school_freeze.py tests/claims/test_executable_claim_rules.py tests/r10/test_r10_ziping_career_l2.py tests/r10/test_r10_ziping_career_layers.py -q
293 passed, 0 skipped, 1 warning in 150.62s (0:02:30)
```

唯一 warning 为 [`engine/application/pipeline_runner.py`](engine/application/pipeline_runner.py) 导入 deprecated dual-engine adapter 的既有 `DeprecationWarning`。禁止据本报告推断未运行的全仓 full suite 已通过。

## G6

未进入。需要独立冻结样本后验和另行审批；本次未声明准确率提升、生产晋级或正式报告可用性。

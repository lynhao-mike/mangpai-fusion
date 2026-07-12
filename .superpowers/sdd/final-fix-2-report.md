# School Capability Blind Evaluation — Second Final Repair Report

## 任务范围

本轮仅完成第二次盲评最终修复的收口记录。功能实现已经通过最终审查，本报告不再修改代码、测试、模板、案例或运行数据；仅归档 TDD、回归、审查结论、问题映射和提交边界证据。

- 操作范围：隔离 worktree `f:/综合盲派/mangpai-fusion/.worktrees/school-capability-blind-evaluation`。
- 代码提交：`4c324d37b796dbba8937758d15b77afce47162fd`（`fix: complete second blind evaluation final repair`）。
- 本次文档提交只允许包含 `.superpowers/sdd/final-fix-2-report.md`。
- 不将既有未提交修改带入本次提交。

## 严格 TDD 证据

### RED

1. 初始任务修复按测试先行建立行为边界，首次运行得到 `7 failed`；失败覆盖审查要求尚未实现的契约，而非先写实现后补测试。
2. 审查修复阶段继续保持逐项 RED：三轮定向验证依次得到 `1 failed`、`5 failed`、`1 failed`，分别锁定单点契约、成组行为缺口及最终边界缺口。
3. 最终修复先新增 `tests/evaluation/test_final_fix_2.py` 并更新相关既有测试；定向运行曾得到 `10 failed, 13 passed`。这 10 个失败证明第二次最终审查列出的行为在修改实现前确实可复现，13 个通过项证明此前已满足的契约未被误判为缺口。
4. RED 覆盖 reviewer 必填、ordinal 融合取整、time-window 融合与未发生语义、portrait 融合及 utility 排除、multiclass 高风险成本、catalog schema、实验成员审计和六维 identity 校准门槛。

### GREEN

最终 evaluation 测试：

```text
python -m pytest tests/evaluation -q
```

结果：`144 passed`。第二次最终修复新增与更新的行为测试全部转绿。

## 无副作用回归与边界校验

相关无副作用回归：

```text
python -m pytest tests/test_project_metadata.py tests/test_decision_mvp.py tests/test_l1_learned_prior.py tests/test_l9_router_calibration.py tests/test_accuracy_report.py -q
```

结果：`129 passed, 1 warning`。该 warning 为仓库既有 deprecation warning，不是本轮引入。

此前最终审查还提供了独立相关回归证据：`86 passed, 1 warning`；warning 同样为既有 deprecated adapter 提示。两组证据均未发现本轮功能改动造成的副作用。

边界检查：

```text
git diff --check
```

结果：退出码 0，无空白错误。

## 最终审查结论

- Spec：**PASS**。
- Quality：**APPROVED**。
- 结论：第二次盲评最终修复满足规格与质量门槛，可以用独立文档提交归档。

## 最终问题 1–7 映射

1. **Revealed label reviewer 强制且非空**
   - `engine/evaluation/models.py`：`RevealedLabel` 契约加入 reviewer，并拒绝空白 reviewer。
   - `engine/evaluation/freeze.py`、`templates/school-capability-labels.json`、CLI 测试同步 reviewer schema 与反序列化要求。
   - `tests/evaluation/test_final_fix_2.py` 证明缺失或空白 reviewer 均失败。

2. **Ordinal 融合必须按 rank 平均并 round-half-up，成员变化必须影响结果**
   - `engine/evaluation/experiments.py`：ordinal 不再沿用不适用的通用融合；按 ordinal rank 聚合并使用确定性的半入取整。
   - 测试覆盖 low + medium 的 1.5 rank 融合，以及 leave-one-school-out 结果变化。

3. **Time-window 融合必须分别平均边界，并按融合窗口评分**
   - `engine/evaluation/experiments.py`：分别聚合 start/end boundary，形成可审计 fused window 后再调用正式 scorer。
   - `engine/evaluation/scoring.py`：统一窗口得分及未发生语义。
   - 测试覆盖 `[2019, 2021]` 与 `[2020, 2024]` 融合后对 2023 事件评分。

4. **未发生 time-window 的高风险假阳性成本与 abstain 安全语义**
   - `engine/evaluation/scoring.py`：事件未发生时，claim 计作 false positive；高风险成本按 2 倍处理，abstain utility 保持 0。
   - `mapping/school-capability-task-catalog-v1.yaml`：time-window label shape 明确要求 `occurred` 与 `year`。
   - 测试证明高风险 claim utility 为 `-2.0`，abstain 为 `0.0`。

5. **Portrait 融合确定性且不得进入 utility 聚合**
   - `engine/evaluation/experiments.py`：portrait 使用多数决；平票采用 lexical tie-break，保证结果稳定。
   - portrait row 的 utility 为 `None`，不进入 `mean_utility_by_group`。
   - 测试覆盖平票确定性和 utility 排除。

6. **Multiclass 高风险假阳性与 catalog 风险标签契约**
   - `engine/evaluation/scoring.py`：以 argmax 决策识别高风险 false positive，并施加双倍负成本。
   - `mapping/school-capability-task-catalog-v1.yaml`：health system risk 显式声明 `high_risk_labels: [high]`。
   - `templates/school-capability-case-manifest.json` 与相关 CLI/契约测试同步正式 schema。
   - 测试以 high=0.7、真实 low 验证 utility 为 `-1.4`。

7. **实验成员审计与六维 identity 校准门槛**
   - `engine/evaluation/models.py`、`engine/evaluation/experiments.py`、`engine/evaluation/report.py`：实验 row 显式记录 requested、contributing、excluded members，并在报告中保留可审计性。
   - `engine/evaluation/capability.py` 的既有六维 identity 口径由本轮测试锁定：校准至少要求同一 identity 下 5 个实际 binary claims，abstain 不得凑足门槛。
   - 测试证明 A identity 的 5 个 claims 可计算 calibration，B identity 的 4 claims + 1 abstain 仍为 `None`。

## 改动文件清单

代码提交 `4c324d37b796dbba8937758d15b77afce47162fd` 共包含以下 17 个文件：

- `engine/evaluation/experiments.py`
- `engine/evaluation/freeze.py`
- `engine/evaluation/models.py`
- `engine/evaluation/report.py`
- `engine/evaluation/scoring.py`
- `mapping/school-capability-task-catalog-v1.yaml`
- `templates/school-capability-case-manifest.json`
- `templates/school-capability-labels.json`
- `tests/evaluation/test_cli.py`
- `tests/evaluation/test_experiments.py`
- `tests/evaluation/test_final_findings.py`
- `tests/evaluation/test_final_fix_2.py`
- `tests/evaluation/test_freeze.py`
- `tests/evaluation/test_models.py`
- `tests/evaluation/test_scoring.py`
- `tools/README.md`
- `tools/school_capability_baseline.py`

本次报告提交新增且只新增：

- `.superpowers/sdd/final-fix-2-report.md`

## 禁区确认

- 未修改、未暂存、未提交 `.superpowers/sdd/task-1-report.md`。
- 未修改、未暂存、未提交 `.superpowers/sdd/task-4-report.md`。
- 未修改、未暂存、未提交 `.superpowers/sdd/final-fix-report.md`。
- 未修改、未暂存、未提交任何 `cases/**/manifest.json`；工作树中既有 case manifest 修改保持原状并明确排除在本次提交之外。
- 未修改、未暂存、未提交任何其他 case 文件、生产权重、规则数据或运行产物。
- 本次只执行精确暂存 `.superpowers/sdd/final-fix-2-report.md`，并以独立提交消息 `docs: record second blind evaluation final repair` 提交。

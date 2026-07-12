# Task 7 实现报告

## 完成内容

- 新增基线报告渲染器，固定输出九个评估章节，明确区分弱先验、历史盲评证据与未来前瞻证据。
- 当全部条件后验 `N_eff < 5`（包括无后验）时，建议固定为 `HOLD`；报告不输出“永久专长”，并明确标签泄漏、污染与样本限制。
- 新增只读 CLI：`audit`、`freeze`、`score`、`report`。
- 所有输出采用 UTF-8 临时同目录文件、flush + fsync、`os.replace` 原子替换。
- 对输出路径执行 `resolve()` 后边界检查，禁止写入 `cases/`、`theory/`、`META/`、`engine/expert-weights.yaml`、`engine/domain-weights.yaml`。
- `score` 在访问 labels 路径前显式执行 `verify_frozen_run()`，随后由 `reveal_labels()` 再校验 labels 的 freeze hash；不绕过身份或冻结校验。
- 本阶段 CLI `score` 明确只支持真实可序列化的 `binary_probability` 输入；其他 scoring method 显式报错。
- score JSON 契约显式包含 eligible case-task grid、claim probabilities、score weights 与 incremental gains 字段；拒绝缺项、重复 grid、非法权重、未知任务和 grid 外输出。
- 工具索引将该入口登记为只读能力评估，不是生产校准、规则更新或权重写入入口。

## TDD 证据

1. RED：`python -m pytest tests/evaluation/test_report.py tests/evaluation/test_cli.py -v`
   - 结果：收集阶段因 `engine.evaluation.report` 不存在而失败，符合预期。
2. 新测试 GREEN：`python -m pytest tests/evaluation/test_report.py tests/evaluation/test_cli.py -q`
   - 结果：`10 passed in 2.04s`。
3. 全 evaluation：`python -m pytest tests/evaluation/ -q`
   - 结果：`111 passed in 2.12s`。
4. 相关回归（按任务要求避开会改真实 cases 的 v5 测试）：
   - `python -m pytest tests/test_project_metadata.py tests/test_decision_mvp.py tests/test_l1_learned_prior.py tests/test_l9_router_calibration.py tests/test_accuracy_report.py -q`
   - 结果：`86 passed, 1 warning in 10.72s`；warning 为既有 deprecated adapter 提示。
5. 最终合并验证：evaluation + 上述相关回归。
   - 结果：`197 passed, 1 warning in 10.54s`。
6. fixture audit smoke：污染 fixture 输出 `development_only`。
7. fixture-only baseline report：`.pytest_cache/school-capability-baseline.md`，验证包含 `HOLD`。
8. `git diff --check`：退出码 0。
9. 生产状态检查：`git status --short cases theory META engine/expert-weights.yaml engine/domain-weights.yaml` 无输出。

## 提交与范围

- 功能提交：`1156bce feat: report blind school capability baseline`。
- 提交严格包含 brief 指定的五个文件：
  - `engine/evaluation/report.py`
  - `tools/school_capability_baseline.py`
  - `tests/evaluation/test_report.py`
  - `tests/evaluation/test_cli.py`
  - `tools/README.md`
- 未触碰工作树既有的 `.superpowers/sdd/task-1-report.md` 与 `.superpowers/sdd/task-4-report.md` 修改。
- 按用户明确要求，未运行可能改写真实 cases 的 v5 测试，也未对真实反馈执行 score。

## Task 7 定向修复追加

- `score` 新增显式 `--evaluation-config` 契约，严格承载 eligible grid、开发基线 prevalence、六维 metadata、evidence grade、evaluated_at 与 score weights；基线不从 evaluated labels 推导。
- `score` 真实调用 `run_four_group_experiment` 与 `build_capability_posteriors`，输出 individual scores、实验 rows/summary、六维增益、posteriors 与 `posteriors_computed: true`。
- `report` 拒绝缺失或非 list 的 posteriors；空 list 只有在显式 computed 标志为 true 时合法，并保持 HOLD。
- freeze 将 task catalog 与 rule snapshot 的完整 canonical JSON SHA256 纳入既有身份字符串；内容变化会改变 freeze hash，未改 FrozenBlindRun 持久模型。
- audit manifest 增加 UTC `generated_at`，并验证完整顶层 schema。
- 五维章节逐 posterior 展示 coverage、discrimination、accuracy、calibration、incremental gain、interval、N_eff 与 evidence。
- 所有 handler 在业务读取前固定解析输出目标；atomic writer 仅接收已验证绝对 Path，拒绝目标 symlink，并在 replace 前紧邻复核 parent resolve。此为 stdlib/Windows 下的常规路径防护，不声称完全抵抗恶意并发目录替换。

### TDD 与验证证据

1. RED：`python -m pytest tests/evaluation/test_cli.py tests/evaluation/test_report.py -q`，得到 7 个预期行为失败：manifest 时间戳、真实 score config/dataflow、freeze 内容摘要、posterior gate、symlink gate、五维展示。
2. GREEN：`python -m pytest tests/evaluation/ -q`，结果 `117 passed in 2.94s`。
3. 最终 evaluation + 相关回归：`203 passed, 1 warning in 12.15s`；warning 为既有 deprecated adapter 提示。
4. `git diff --check`：退出码 0。

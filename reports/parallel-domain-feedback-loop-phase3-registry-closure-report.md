# 多专家功能域反馈闭环 Phase 3 · 工具索引漂移收口报告

- 执行日期：2026-07-27
- 执行边界：本地工作区，只读验证与严格白名单文档写入
- 最终判定：**PASS / COMPLETE — EVIDENCE-BOUNDED FREEZE**
- 交付状态：**LOCAL ONLY / NOT PUSHED**

## 1. 目标与授权边界

本轮目标是修复两个早于 Phase 2 已存在、但未登记到 [`tools/README.md`](../tools/README.md) 的工具索引漂移，并为 Phase 2 只读扫描器补做逻辑新鲜静态审查、完整新鲜回归、真实只读扫描、证据复核与 bounded freeze。

本轮写集严格限于：

1. 在 [`tools/README.md`](../tools/README.md:102) 增加两个 as-of 工具的登记行；
2. 新建本报告。

本轮未修改 [`tools/as_of_integration.py`](../tools/as_of_integration.py)、[`tools/production_as_of_cli.py`](../tools/production_as_of_cli.py)、[`engine/asof/`](../engine/asof/)、[`tools/parallel_domain_weight_status_scan.py`](../tools/parallel_domain_weight_status_scan.py)、[`tests/test_parallel_domain_weight_status_scan.py`](../tests/test_parallel_domain_weight_status_scan.py)、生产 pipeline / routing / adjudication 文件、权重文件、真实日志或任何 `production_switch` 字段及语义。

## 2. 漂移根因与分类裁决

### 2.1 根因

修复前运行工具注册检查得到 exit code 1：

```text
tool registry check failed:
- UNINDEXED tool exists but is absent from tools/README.md: as_of_integration.py
- UNINDEXED tool exists but is absent from tools/README.md: production_as_of_cli.py
```

两个文件均是 G8 / G9-P1 的 pre-existing 历史交付物。问题是人工索引遗漏，不是 Phase 2 扫描器新增代码造成，也不需要修改 as-of 实现或注册检查逻辑。

### 2.2 分类依据

两个工具均登记为 `historical`，依据如下：

1. G8 契约把 [`as_of_integration.py`](../tools/as_of_integration.py:1) 定义为“单向薄编排入口”，见 [`as-of-life-state-g8-production-integration-spec.md`](../plans/as-of-life-state-g8-production-integration-spec.md:7)。
2. 同一契约明确默认 runner registry、[`run_pipeline()`](../plans/as-of-life-state-g8-production-integration-spec.md:43) 签名和公共 schema 不得改变，并明确“不把 as-of 接入默认 runner registry 或 `run_pipeline()`”，见 [`as-of-life-state-g8-production-integration-spec.md`](../plans/as-of-life-state-g8-production-integration-spec.md:212)。
3. G9-P1 契约把 [`production_as_of_cli.py`](../tools/production_as_of_cli.py:1) 定义为 G8 工具的“生产路径别名”，唯一差异是默认 `cases/`、`reports/` 目录约定，见 [`as-of-life-state-g9-p1-production-cli-alias-contract.md`](../plans/as-of-life-state-g9-p1-production-cli-alias-contract.md:11)。
4. G9-P1 明确“不默认开启 as-of 回放”，见 [`as-of-life-state-g9-p1-production-cli-alias-contract.md`](../plans/as-of-life-state-g9-p1-production-cli-alias-contract.md:18)。
5. G9 范围裁决明确：零 public schema 变更、零 HTTP API 变更；该能力仍由运营者手动调用，promotion 只是路径规范化，“不是真正的生产集成”，见 [`as-of-life-state-g9-production-promotion-scope-adjudication.md`](../plans/as-of-life-state-g9-production-promotion-scope-adjudication.md:31)。

因此，文件名中的 “production” 不能作为 `active` 分类依据。两者是已冻结、仍可显式手动运行、但未进入默认生产路径的历史阶段交付物；`historical` 与当前实际调用边界一致。

### 2.3 实际登记

[`tools/README.md`](../tools/README.md:102) 当前登记为：

- [`as_of_integration.py`](../tools/README.md:102)：G8 as-of 统一报告薄编排，运营者手动调用的旁路证明入口；未接入默认 runner、生产服务或 HTTP API。
- [`production_as_of_cli.py`](../tools/README.md:103)：G9-P1 生产目录约定 CLI 别名；只对齐目录并委托 G8 薄层，仍是手动旁路。

未修改其他工具登记内容。

## 3. 工具注册表修复验证

### 3.1 修复前

```text
command: python tools/tool_registry.py --check
exit_code: 1
result:
  UNINDEXED as_of_integration.py
  UNINDEXED production_as_of_cli.py
```

### 3.2 修复后

新鲜执行：

```text
command: python tools/tool_registry.py --format markdown
exit_code: 0
```

输出成功生成完整注册表；终端预览中的部分中文 docstring 有 Windows 控制台编码失真，但不影响条目解析、状态或退出码。

```text
command: python tools/tool_registry.py --check
exit_code: 0
result: tool registry check passed
```

程序化复核还确认两个目标条目均为 `historical`，且 [`check_registry()`](../tools/tool_registry.py:184) 返回空问题列表。没有新增 unindexed、missing 或 broken README reference 漂移。

## 4. Phase 2 逻辑新鲜静态审查

审查角色已显式重置；未采信 Phase 2 会话自评。审查输入限定为 Phase 2 CONTRACT、扫描器与测试原文、canonical 权重配置及既有统计实现。

裁决：**STATIC_REVIEW — PASS**。

逐项结论：

| CONTRACT 约束 | 新鲜审查结论 | 依据 |
|---|---|---|
| 扫描器只读 | PASS | 扫描器中未发现写模式 `open`、`write_text`、`write_bytes`、YAML dump、删除、替换或建目录操作 |
| 缺失日志按零样本处理 | PASS | [`_read_jsonl()`](../tools/parallel_domain_weight_status_scan.py:31) 对不存在路径返回空集合 |
| 跨全部历史行聚合 | PASS | [`aggregate_expert_domain_feedback()`](../tools/parallel_domain_weight_status_scan.py:47) 遍历全部 JSONL 行，按 `(domain, expert_system)` 聚合 `hit` / `miss` |
| 指标口径 | PASS | `N_eff = hits + misses`；Beta mean 使用 `(hits + 1) / (N_eff + 2)`；Wilson lower 使用既有 95% 口径 |
| canonical 阈值 | PASS | [`_minimum_effective_sample()`](../tools/parallel_domain_weight_status_scan.py:91) 从 profile 的 `feedback_overlay` / `constraints` 读取阈值，未硬编码生产阈值 |
| overlay 对账 | PASS | [`build_status_report()`](../tools/parallel_domain_weight_status_scan.py:128) 按相同 domain/expert key 对账 overlay N_eff |
| pending 判定 | PASS | 达到阈值后，overlay 缺失或日志 N_eff 高于 overlay N_eff 才标记 pending |
| CLI 格式 | PASS | [`main()`](../tools/parallel_domain_weight_status_scan.py:267) 支持 Markdown、JSON 与 `--check` |
| 检查退出码 | PASS | pending 非空返回 1；无 pending 返回 0 |
| 不自动 promotion | PASS | 仅构建观测报告，无 promotion 调用或权重更新调用 |
| 无生产路由耦合 | PASS | 在 `engine/` 中搜索扫描器模块名、[`build_status_report()`](../tools/parallel_domain_weight_status_scan.py:128) 和 `pending_promotion_review` 均无消费者 |
| synthetic fixture 隔离 | PASS | [`test_parallel_domain_weight_status_scan.py`](../tests/test_parallel_domain_weight_status_scan.py) 的写入均指向 `tmp_path`，不指向真实 `engine/logs/` |

审查未发现逻辑缺陷、写集越界、生产耦合或 CONTRACT 冲突，未触发 STOP。

## 5. 新鲜回归证据

所有命令均在仓库根目录新鲜执行；条件串联确保任一失败会阻止后续命令被误记为完整通过。

| 命令 | 新鲜结果 | Exit code |
|---|---:|---:|
| `python -m pytest tests/test_parallel_domain_weight_status_scan.py -q` | 3 passed | 0 |
| `python -m pytest tests/v1_3_acceptance -q` | 118 passed, 2 skipped, 1 warning | 0 |
| `python -m pytest tests/test_promote_expert_weight_feedback.py -q` | 5 passed, 1 warning | 0 |
| `python -m pytest tests/test_project_metadata.py -q` | 17 passed | 0 |
| `python tools/tool_registry.py --check` | tool registry check passed | 0 |

合计：**143 passed, 2 skipped**。

两项 skip 均为测试自身的既有显式条件：一个真实命理师报告 fixture 不存在，一个历史 legacy 模板已删除；本轮没有新增失败。warning 是 [`pipeline_runner.py`](../engine/application/pipeline_runner.py:11) 既有 deprecated adapter 警告，不是本轮新增失败。

## 6. 真实只读扫描证据

新鲜执行以下三个独立入口：

```text
python tools/parallel_domain_weight_status_scan.py --format markdown
python tools/parallel_domain_weight_status_scan.py --format json
python tools/parallel_domain_weight_status_scan.py --check
```

三者 exit code 均为 0。Markdown 与 JSON 的结构化结果一致：

```json
{
  "schema_version": "parallel-domain-weight-status/v1",
  "min_effective_sample_for_adjustment": 11.0,
  "expert_feedback_valid_rows": 0,
  "adjudication_accuracy_rows": 0,
  "adjudication_accuracy_valid_rows": 0,
  "feedback_overlay": {
    "version": "no-feedback-overlay",
    "entry_count": 0,
    "entries": []
  },
  "pending_promotion_review": [],
  "pending_promotion_review_count": 0
}
```

`--check` 输出：

```text
parallel domain weight status scan passed
```

该结果证明扫描器在当前真实零样本状态下可正常读取 canonical 配置、生成两种格式并正确返回无 pending 的 exit code 0。

## 7. 受保护文件前后复核

修复前建立大小与 SHA-256 基线；完成全部测试和真实扫描后重新计算。三项均逐字匹配：

| 受保护文件 | 修复前大小 | 修复后大小 | SHA-256 | 匹配 |
|---|---:|---:|---|---|
| [`expert_domain_feedback.jsonl`](../engine/logs/expert_domain_feedback.jsonl) | 0 | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | true |
| [`adjudication_accuracy.jsonl`](../engine/logs/adjudication_accuracy.jsonl) | 0 | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | true |
| [`expert-weights.yaml`](../engine/expert-weights.yaml) | 1542 | 1542 | `d8c8a90df1fe625a952ecc67ee6925812e28dbfe7200f4dbfc9f091d2e0fabae` | true |

这直接证明上述三份文件在本轮基线采集与最终复核之间没有可观测的字节变化。

## 8. Fresh Evidence Review

裁决：**EVIDENCE_REVIEW — PASS**。

理由：

1. CONTRACT、实施、逻辑新鲜静态审查、动态验证和证据复核均有独立且范围匹配的证据；
2. 所有要求的选择器均已新鲜运行，没有收集错误或未解释的新失败；
3. 注册表修复前后的退出码和具体漂移条目均已保留；
4. 真实扫描的 Markdown、JSON、`--check` 三种入口均有新鲜结果；
5. 受保护日志与权重配置通过前后哈希复核；
6. 没有证据被用于超出其直接证明范围的结论。

## 9. Freeze 边界

### 9.1 直接证明的范围

本轮证据直接证明：

1. 两个 pre-existing as-of 工具已按照 G8/G9-P1 原始契约的真实边界登记为 `historical`；
2. 当前工具注册表不存在这两个工具导致的 unindexed 漂移，且 [`tool_registry.py`](../tools/tool_registry.py) 的 `--check` 返回 0；
3. Phase 2 扫描器源码在新鲜静态审查中符合只读、全历史聚合、canonical 阈值、overlay 对账、pending 检查和无生产耦合约束；
4. 指定的 143 个新鲜测试实例通过，2 个既有条件测试明确跳过，没有新失败；
5. 当前真实日志为零样本时，Markdown、JSON 与 `--check` 三种入口均可正常完成，pending count 为 0；
6. 两份真实日志和 [`engine/expert-weights.yaml`](../engine/expert-weights.yaml) 在本轮受保护区间内没有可观测字节变化；
7. 本受控会话未执行 Git 或 GitHub 写操作。

### 9.2 不得推断的范围

本轮证据不得被解释为：

1. as-of 已接入默认 runner、[`ProductionAnalysisService`](../engine/application/production_service.py)、HTTP API 或任何默认生产入口；
2. G8/G9-P1/G10 as-of 生命周期已完成默认生产 promotion；
3. 多专家功能域反馈已自动 promotion、自动写权重或自动切换主裁判路由；
4. `production_switch` 已发生任何变化；
5. 当前零样本真实扫描证明了非零真实反馈、大样本积累、阈值边界或长期漂移条件下的生产表现；synthetic 测试只证明其覆盖的确定性行为；
6. 本地结果已同步到 GitHub、已创建提交、分支、PR、合并、部署或发布；
7. 指定回归集合之外的整个仓库或完整生产系统已被证明无缺陷。

as-of 默认生产入口切换、主裁判路由切换与 `production_switch` 变化均**未开始**，并且明确不属于本任务授权范围；后续如需推进，必须单独立项、建立新 CONTRACT 与取得显式授权。

## 10. 最终裁决与交付清单

**PASS / COMPLETE — EVIDENCE-BOUNDED FREEZE**

交付文件：

1. 修改：[`tools/README.md`](../tools/README.md:102)，仅新增两个 historical 登记行；
2. 新增：[`parallel-domain-feedback-loop-phase3-registry-closure-report.md`](parallel-domain-feedback-loop-phase3-registry-closure-report.md)。

本轮为 **LOCAL ONLY / NOT PUSHED**。没有执行 Git/GitHub 写操作；该陈述不表示或暗示 GitHub 已同步，只表示本受控执行没有发起 Git/GitHub 变更。

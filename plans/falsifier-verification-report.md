# Falsifier 验证报告 · pipeline 无状态性检查

> 本报告验证 [`plans/production-system-geju-judgment.md`](production-system-geju-judgment.md) 中的 Falsifier 条件。
> 验证时间：2026-06-20
> 检查范围：[`engine/application/pipeline_runner.py`](../engine/application/pipeline_runner.py) 及其依赖链

---

## 验证结论

❌ **Falsifier 条件触发：pipeline 不是无状态纯函数。**

[`run_pipeline_e2e`](../engine/application/pipeline_runner.py:163) 和 [`run_pipeline`](../engine/application/pipeline_runner.py:32) 都依赖文件系统副作用，无法作为"输入字符串 → 输出结构化数据"的纯计算函数使用。

---

## 关键证据

### 1. 强依赖文件路径输入

```python
# engine/application/pipeline_runner.py:163
def run_pipeline_e2e(
    input_md_path: Union[str, Path],  # ← 必须是文件路径，不接受字符串内容
    *,
    cases_dir: Optional[Union[str, Path]] = None,
    ...
) -> tuple[AnalysisOutput, PipelineTiming]:
```

**影响**：无法传入 canonical 字符串输入，必须先落盘为文件才能调用。

### 2. 执行中写入 cases/ 副作用

```python
# engine/application/pipeline_runner.py:269-271
try:
    findings_dir = _save_findings(output, cases_dir=cases_dir)  # ← 写入文件系统
    timing.write_to(findings_dir, case_id=output.case_id)
except Exception as e:
    ...
```

```python
# engine/infrastructure/findings_repository.py:54-63
(findings_dir / "energy.json").write_text(_dump(output.energy), encoding="utf-8")
(findings_dir / "picture.json").write_text(_dump(output.picture), encoding="utf-8")
(findings_dir / "gate_results.json").write_text(_dump(output.gate_results), encoding="utf-8")
(findings_dir / "support.json").write_text(_dump(output.support), encoding="utf-8")
(findings_dir / "analysis_output.json").write_text(_dump(output), encoding="utf-8")
```

**影响**：
- 执行路径强制写入 `cases/C-XXX/findings/` 五个 JSON 文件。
- 即使 `write_findings=False`，`run_pipeline_e2e` 仍在 L269-271 强制落盘。
- Worker 无法无状态运行，必须依赖共享磁盘上的 `cases/` 目录。

### 3. preflight 依赖路径读取

```python
# engine/application/pipeline_runner.py:221-224
with timing.step("preflight"):
    parsed = adapters.preflight.parse(
        Path(input_md_path),  # ← 读取文件
        Path(cases_index_path) if cases_index_path else None,
    )
```

**影响**：必须先有物理文件，才能进入 pipeline。

### 4. 其他模块的 cases/ 依赖

搜索结果显示以下模块也涉及 `cases/` 路径：

| 模块 | 副作用类型 | 影响范围 |
|---|---|---|
| [`engine/pangzheng/loader.py`](../engine/pangzheng/loader.py) | 读取 `cases/{case_id}/input.md` 神煞表格 | D4 高派执行 |
| [`engine/application/artifact_inventory.py`](../engine/application/artifact_inventory.py) | 写入 `reports/` 报告 | 可选（render 步骤） |
| [`engine/statement_runtime.py`](../engine/statement_runtime.py) | 写入 `cases/<case_id>/statement_records.json` | 反馈索引 |
| [`engine/yingqi/retrospective.py`](../engine/yingqi/retrospective.py) | 硬编码测试路径（非生产） | 仅测试 |

---

## 无法实现的目标设计

原计划的"内容寻址 + 无状态 Worker"架构依赖以下前提（现已证伪）：

```python
# 原计划（不可行）：
canonical_input = "乾造 庚申 戊寅 ..."
output = run_pipeline_e2e(canonical_input)  # ← 签名不匹配
artifacts.put(analysis_key, output.to_dict())  # ← 但 output 已写入 cases/
```

**问题**：
1. `run_pipeline_e2e` 不接受字符串输入。
2. 即使传入路径，执行中仍会写 `cases/`，无法隔离副作用。
3. Worker 必须共享 `cases/` 目录，无法独立部署。

---

## 降级方案对比

按 [`plans/production-system-geju-judgment.md`](production-system-geju-judgment.md) Falsifier 部分的应对策略：

| 方案 | 可行性 | 横向扩展 | 迁移成本 | 裁决 |
|---|---|---|---|---|
| **A. 重构 pipeline 为纯函数** | 高成本（需改 preflight + findings_repository + 所有读写逻辑） | ✅ 完美 | 极高 | ⚠️ 需单独立项 |
| **B. Workspace 隔离** | 可行（每 Worker 独立 workspace，完成后同步到中央存储） | ⚠️ 受限 | 中 | ✅ **推荐 MVP** |
| **C. 单 Worker + 队列** | 立即可行（保留现有副作用，用队列削峰） | ❌ 无法横向 | 低 | ✅ **最保守** |

---

## 推荐方案：B. Workspace 隔离

### 架构调整

```text
  SubmissionService
    ├─ canonical_input 落盘到临时 workspace
    ├─ enqueue(analysis_id, workspace_path)
    └─ 返回 202 {analysis_id, status: queued}
       ↓
  AnalysisWorker(workspace_root="/tmp/workspaces")
    ├─ 为每个 job 创建隔离 workspace: /tmp/workspaces/{analysis_id}/
    ├─ 写入 input.md 到 workspace/cases/fake-case-id/input.md
    ├─ run_pipeline_e2e(workspace/cases/.../input.md)
    │    └─ 副作用全部发生在隔离 workspace 内
    ├─ 读取 workspace/cases/.../findings/analysis_output.json
    ├─ 写入规范产物到 ArtifactStore
    └─ 清理 workspace（或保留用于审计）
```

### 关键改动

1. **不改 pipeline**：保留现有 [`run_pipeline_e2e`](../engine/application/pipeline_runner.py:163) 签名与副作用逻辑。
2. **隔离副作用**：每个 Worker 分配独立 workspace，互不干扰。
3. **规范产物提取**：从 `workspace/cases/.../findings/analysis_output.json` 读回结构化数据，写入 ArtifactStore。

### 横向扩展能力

- **单机多 Worker**：可行，每个 Worker 独立 workspace 目录。
- **多机 Worker**：受限，需要共享存储挂载或完成后推送到中央存储。
- **无状态副本**：❌ 不可行，仍依赖本地磁盘。

### 优势

- ✅ 零改动现有 pipeline 逻辑，风险最低。
- ✅ 立即可用，MVP 可在一周内交付。
- ✅ 保留未来重构空间（workspace 清理后可替换为纯函数）。

### 劣势

- ⚠️ 横向扩展受限于共享存储性能。
- ⚠️ 每次分析产生临时文件（可配置清理策略）。
- ⚠️ 无法真正做到"计算与状态解耦"。

---

## 推荐方案：C. 单 Worker + 队列（最保守）

如果近期没有多命理师并发需求，最简单的方案是：

```text
  SubmissionService
    ├─ 缓存查找
    └─ enqueue(analysis_id, input_path)
       ↓
  单个 AnalysisWorker
    ├─ 串行消费队列
    ├─ 直接调用 run_pipeline_e2e(input_path)
    │    └─ 副作用发生在共享 cases/ 目录
    └─ 记录元数据到 MetadataStore
```

**适用场景**：
- 单命理师或小团队。
- QPS < 1（推理耗时 3-10 秒，一天跑不到 1000 个命盘）。
- 不需要横向扩展。

**优势**：
- ✅ 完全复用现有逻辑，零改动。
- ✅ 一天可交付。
- ✅ 队列提供异步化与削峰。

**劣势**：
- ❌ 单点瓶颈，无法横向扩展。
- ❌ 一旦并发增长，必须重构。

---

## 长期方案：A. 重构 pipeline 为纯函数

要真正实现"内容寻址 + 无状态 Worker"，需要以下重构（独立立项）：

### 1. preflight 改为接受字符串输入

```python
# 新签名
def parse_input(canonical_input: str) -> ParsedInput:
    """不读文件，直接解析字符串内容。"""
```

### 2. findings_repository 改为返回数据而非写文件

```python
# 当前
def _save_findings(output: AnalysisOutput, cases_dir: Path) -> Path:
    ...  # 写文件

# 新设计
def serialize_findings(output: AnalysisOutput) -> dict[str, Any]:
    """返回所有 findings 的结构化数据，不写磁盘。"""
    return {
        "energy": output.energy,
        "picture": output.picture,
        ...
    }
```

### 3. pipeline 签名改为纯函数

```python
# 新签名
def run_pipeline_pure(canonical_input: str) -> AnalysisOutput:
    """纯计算：字符串 → 结构化输出，无副作用。"""
    parsed = parse_input(canonical_input)
    # ... D1-D4 计算
    return output  # 不写文件
```

### 4. 文件导出移到独立工具

```bash
# 按需导出
python -m tools.export_case --analysis-id AN-xxx --to cases/C-xxx/
```

**工作量估算**：2-3 周，需回归测试所有现有案例。

**收益**：解锁真正的横向扩展与内容寻址架构。

**风险**：影响面大，需要完整回归测试。

---

## 行动建议

| 阶段 | 方案 | 时间表 | 触发条件 |
|---|---|---|---|
| **MVP（立即）** | C. 单 Worker + 队列 | 1 天 | 无并发需求 |
| **V1（近期）** | B. Workspace 隔离 | 1 周 | 需要异步 + 有限横向扩展 |
| **V2（长期）** | A. 纯函数重构 | 2-3 周 | 真实高并发出现 |

### 决策树

```text
现在有多命理师并发需求吗？
  ├─ NO  → 用方案 C（单 Worker + 队列）
  └─ YES → 并发量级是多少？
            ├─ < 10 QPS  → 用方案 B（Workspace 隔离）
            └─ > 10 QPS  → 单独立项方案 A（纯函数重构）
```

---

## 结论

1. **原目标不可行**：[`run_pipeline_e2e`](../engine/application/pipeline_runner.py:163) 不是无状态纯函数，无法实现"内容寻址 + 无状态 Worker"的理想架构。

2. **立即可用方案**：方案 C（单 Worker + 队列）或方案 B（Workspace 隔离），根据并发需求选择。

3. **长期方向保留**：方案 A（纯函数重构）是正确的终态，但需要独立立项、充分测试。

4. **不要停止前进**：即使当前架构有限制，仍可通过 Workspace 隔离实现有限横向扩展 + 异步化 + 缓存。核心产品价值（规则迭代 + 版本隔离 + 反馈闭环）不受影响。

---

## 附录：需要重构的文件清单

如果选择方案 A（纯函数重构），以下文件需要改动：

| 文件 | 改动类型 | 优先级 |
|---|---|---|
| [`engine/application/pipeline_runner.py`](../engine/application/pipeline_runner.py) | 签名改为接受字符串输入 | P0 |
| [`engine/infrastructure/findings_repository.py`](../engine/infrastructure/findings_repository.py) | 改为返回数据而非写文件 | P0 |
| preflight 解析器（依赖 `tools/preflight.py`） | 改为接受字符串输入 | P0 |
| [`engine/pangzheng/loader.py`](../engine/pangzheng/loader.py) | 神煞表格从输入字符串解析 | P1 |
| [`engine/statement_runtime.py`](../engine/statement_runtime.py) | 移到外层可选写入 | P2 |
| [`tools/render_report.py`](../tools/render_report.py) | 改为纯函数（传 AnalysisOutput） | P2 |

预计改动行数：500-800 行，影响 10+ 测试案例。

---

**下一步**：根据本报告选择方案 B 或 C，我将继续实现对应的系统架构设计与代码。

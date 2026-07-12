# Task 2 实现报告

## 状态

完成。

## 变更文件

- `mapping/school-capability-task-catalog-v1.yaml`：新增 18 项统一盲测任务目录，覆盖婚姻、财富、事业、学业、健康、性格六个领域。
- `engine/evaluation/task_catalog.py`：新增严格目录加载器 `load_task_catalog()` 与唯一 ID 索引 `task_by_id()`。
- `tests/evaluation/test_task_catalog.py`：新增目录内容、空标签模式、重复 ID 和索引行为测试。

未提交 `.superpowers/sdd` 文件；未修改 brief 限定范围外的生产文件。工作树中既有 `.superpowers/sdd/task-1-report.md` 修改未纳入本提交。

## RED

命令：

```text
pytest tests/evaluation/test_task_catalog.py -v
```

结果：退出码 2；测试收集阶段按预期失败，错误为 `ModuleNotFoundError: No module named 'engine.evaluation.task_catalog'`，证明待实现 loader 缺失。

## GREEN

命令：

```text
pytest tests/evaluation/test_task_catalog.py -v
```

结果：退出码 0；4 passed。

提交前扩展验证命令：

```text
pytest tests/evaluation/test_task_catalog.py tests/evaluation/test_models.py -v
```

结果：退出码 0；12 passed in 0.17s。

附加检查：`git diff --check` 与 `git diff --cached --check` 均退出码 0。

## 提交

- 提交哈希：`fb5f7a5ea458174297d2e9590a214e3c032c931f`
- 提交信息：`feat: define school capability task catalog`

## 自审

- YAML 正好包含 brief 指定的 18 个 task_id。
- 每项完整映射 `BlindTask` 的十个字段。
- 性格与画像任务均使用 `portrait_agreement` 且 `quantifiable: false`。
- loader 使用已有 `yaml.safe_load`，未新增依赖。
- loader 校验 schema 版本、tasks 列表、任务映射、重复 ID、空领域、不支持的评分方法，以及可量化任务的非空标签模式。
- `task_by_id()` 对重复 ID 也执行防御性拒绝，避免静默覆盖。
- 提交仅包含 brief 指定的三个文件。

## 疑虑

无阻塞疑虑。轻微注意点：`BlindTask.__post_init__()` 已先于 loader 的显式检查拒绝空领域和空量化标签，因此相关异常文本部分来自模型契约；行为满足严格拒绝要求。

---

## Task 2 定向修复证据（2026-07-12）

### 修复范围

- `engine/evaluation/task_catalog.py`：在 `BlindTask.from_dict()` 前验证 `domain` 为非空字符串、`scoring_method` 属于支持集合、`label_schema` 为 mapping，保证畸形目录统一抛出语义清楚的 `ValueError`。
- `tests/evaluation/test_task_catalog.py`：新增非法 scorer、空/null/非字符串 domain、truthy 非 mapping label_schema，以及 `task_by_id()` 重复 ID 的回归测试。
- 未修改 `models.py` 或其他生产文件。

### RED 证据

命令：

```text
python -m pytest tests/evaluation/test_task_catalog.py -v
```

结果：退出码 1；10 项中 4 项失败。空字符串 domain 的异常文本不符合严格 loader 契约；null/整数 domain 泄漏 `AttributeError`；truthy list 类型的 `label_schema` 未被拒绝。非法 scorer 与 `task_by_id()` 重复 ID 测试已由既有防御逻辑通过。

### 最小实现

仅在构造 `BlindTask` 前增加三项字段检查；保留构造后的既有业务校验与重复 ID 检查，不改模型契约。

### GREEN 证据

命令：

```text
python -m pytest tests/evaluation/test_task_catalog.py tests/evaluation/test_models.py -v
```

结果：退出码 0；18 passed in 0.22s。

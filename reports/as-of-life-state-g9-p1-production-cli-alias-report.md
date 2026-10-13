# G9-P1 as-of 生产 CLI 别名验证报告

> 验证范围：G9-P1（保守）生产 CLI 别名
>
> 验证日期：2026-07-27（Asia/Shanghai）
>
> 结论状态：**PASS——G9-P1-A/B/C/D 全部满足；报告后新鲜复核通过，全仓仅保留两项允许的历史失败，无第三项失败**

## 一、验证目标与边界

G9-P1 只新增一个生产路径 CLI 别名，使未显式提供 `--cases-dir` / `--reports-dir` 时使用当前工作目录下的 `cases/` 与 `reports/`。除该默认目录解析外，参数集合、参数配对、账本加载、日期解析、报告生成、异常输出与退出码全部委托既有 `tools.as_of_integration` 行为。

P1 是范围裁决中已明确选择的保守方案。P2、P3 未被选择；本轮不修改公共程序 API、HTTP schema、生产服务、既有 as-of 算法或既有薄层。

## 二、写集与保护边界

本轮唯一写入白名单：

1. `plans/as-of-life-state-g9-p1-production-cli-alias-contract.md`
2. `tests/asof/test_g9_production_cli_alias.py`
3. `tools/production_as_of_cli.py`
4. `reports/as-of-life-state-g9-p1-production-cli-alias-report.md`

本轮实际新增测试、实现与本报告；冻结合同第 1–8 节未改写。

明确禁止修改：

- `tools/as_of_integration.py`；
- `engine/asof/` 下任何文件；
- `engine/application/production_service.py`、`tools/production_api.py`；
- 任何既有测试；
- G0–G8 冻结文档与报告；
- 其他任何未在白名单内的路径。

工作区在任务开始前已存在 modified/untracked 背景内容。本轮不清理、不覆盖、不归因这些背景噪音；最终以 `git status --short` 如实记录。

## 三、依赖方向与行为增量

```text
tools/production_as_of_cli.py
  └─> tools.as_of_integration
      ├─> _parser
      ├─> parse_iso_date
      ├─> load_ledger
      └─> generate_report
```

新增别名不导入 `engine.asof`、`engine.application.production_service`、`tools.production_api` 或其他生产模块。既有文件不反向导入新增别名。

唯一行为增量：

```python
cwd = Path.cwd()
default_cases_dir = cwd / "cases"
default_reports_dir = cwd / "reports"
```

`Path.cwd()` 在一次 `main()` 调用内只调用一次。显式目录保持 argparse 返回值原样透传；未显式提供时才使用上述默认值。

## 四、G9-P1-A：冻结合同

冻结合同第 2 节限定四文件写集，第 3 节冻结单向依赖，第 4 节冻结精确 CLI 行为，第 5 节登记 G9P1-F01–F06，第 6 节冻结最小测试选择器，第 7 节冻结 A→B→C→D Gate 顺序，第 8 节 logical fresh review verdict 为 `PASS`。

本轮重新读取范围裁决、冻结合同、既有薄层全文和生产服务目录约定，确认用户已明确选择 P1，P2/P3 未获授权；合同与执行指令无不可解决冲突。

G9-P1-A 判定：**PASS**。

## 五、G9-P1-B：TDD RED

首次运行：

```text
python -m pytest tests/asof/test_g9_production_cli_alias.py -q
```

首次 RED 原始 summary：

```text
FFFFFF                                                                   [100%]
6 failed in 0.97s
exit code 1
```

六个测试实例均在行为阶段调用测试 helper 导入目标模块时失败：

```text
ModuleNotFoundError: No module named 'tools.production_as_of_cli'
```

pytest 已完成收集并执行六个测试实例，不是 collection error。没有测试 helper 缺陷需要修订；首次 RED 未被覆盖或重新解释。

G9-P1-B 判定：**PASS（有效 RED：6 failed，exit code 1）**。

## 六、G9-P1-C：实现与首轮验证

### 6.1 最小实现

新增 `tools/production_as_of_cli.py`：

- 复用既有 `_parser()`，参数集合保持为 `input_md`、`--as-of`、`--ledger`、`--cases-dir`、`--reports-dir`；
- 保持 `--as-of` / `--ledger` 配对失败为 exit code 2；
- 一次调用 `Path.cwd()` 构造两个生产默认目录；
- 显式目录原样透传；
- 直接调用既有 `load_ledger()`、`parse_iso_date()` 与 `generate_report()`；
- 保持既有异常集合、`错误：{exc}` 输出、成功路径打印与退出码。

未新增依赖，未修改 Python 版本或 `pyproject.toml`。

### 6.2 首轮验证证据

| 检查 | 首轮结果 | Exit code | 判定 |
|---|---:|---:|---|
| `python -m pytest tests/asof/test_g9_production_cli_alias.py -q` | 6 passed，0 failed，0 skipped，1 warning | 0 | PASS |
| `python -m pytest tests/asof -q` | 118 passed，0 failed，1 skipped，1 warning | 0 | PASS |
| `python -m pytest tests/asof/test_production_isolation.py -q` | 4 passed，0 failed，0 skipped，1 warning | 0 | PASS |
| `git diff -- engine/asof` | 零输出 | 0 | PASS |
| `git diff -- tools/as_of_integration.py` | 零输出 | 0 | PASS |
| `python -m pytest -q` | 3119 passed，2 failed，7 skipped，1 warning | 1 | PASS（仅允许的历史失败） |

全仓命令完整运行 1288.60 秒并取得 summary。两项失败精确为：

1. `tests/evaluation/test_dataset.py::test_witness_trust_boundary_is_explicitly_documented`
2. `tests/evaluation/test_prospective_gate_workflow.py::test_handoff_names_first_legal_case_action_and_all_independent_holds`

没有第三项失败，因此未触发 STOP。

唯一 warning 是既有 `engine.application.dual_engine_adapter` deprecation warning。`tests/asof` 唯一 skip 是 G6 evidence gate：样例缺少显式十神与藏干十神字段，而推导被禁止；其余全仓 skip 均由测试自身显式 gate、历史模板或缺失历史报告条件产生。

G9-P1-C 首轮判定：**PASS（全仓仅两项允许的历史失败，无新增失败）**。

## 七、failure ledger 对照

| ID | 验证证据 | 结果 |
|---|---|---|
| G9P1-F01 | 默认目录测试断言真实 `generate_report()` 收到 `Path.cwd()/"cases"` 与 `Path.cwd()/"reports"`，并真实写出报告 | PASS |
| G9P1-F02 | 显式目录测试断言 argparse 返回对象被原样透传，未与默认值合并 | PASS |
| G9P1-F03 | 两个参数化实例分别只提供 `--as-of` 或 `--ledger`，均返回 2 且禁止调用 `generate_report()` | PASS |
| G9P1-F04 | 相同目录下先直接调用既有薄层、再调用别名，报告 `read_bytes()` 完全一致且无快照章节 | PASS |
| G9P1-F05 | AST 静态导入测试确认仅依赖 `tools.as_of_integration`，无三个禁止模块导入 | PASS |
| G9P1-F06 | 默认/显式目录测试以 spy 包裹真实 `generate_report()`；仅替换其既有 pipeline/render 下层依赖，没有伪造委托返回值 | PASS |

## 八、证据边界

### 8.1 直接证明

当前证据直接证明：

- 新别名的 CLI 参数集合与既有 parser 一致；
- 默认目录使用当前工作目录，显式目录不改写；
- 参数配对、错误码与报告生成委托既有薄层；
- 不提供 as-of 时，同目录结果与直接调用既有薄层逐字节一致；
- 新别名没有禁止的生产模块导入；
- `engine/asof/` 与 `tools/as_of_integration.py` 均无本轮 diff；
- as-of 全套与生产隔离测试通过；
- 全仓无两项已知历史失败之外的第三项失败。

### 8.2 不得推导

本轮不声称：

- HTTP API 或 `ProductionAnalysisService` 已接入 as-of；
- 事件账本可自动推导、核验、审批或持久化；
- 两项历史全仓失败已修复；
- P2、P3 或 G10 获得授权；
- GitHub 服务端发生部署、push、PR、release 或任何同步。

## 九、报告后最终新鲜复核

报告创建后按合同顺序重新执行全部六条验证命令，并在完整退出后取得以下新鲜证据：

| 检查 | 报告后新鲜结果 | Exit code | 判定 |
|---|---:|---:|---|
| `python -m pytest tests/asof/test_g9_production_cli_alias.py -q` | 6 passed，0 failed，0 skipped，1 warning，0.32s | 0 | PASS |
| `python -m pytest tests/asof -q` | 118 passed，0 failed，1 skipped，1 warning，0.92s | 0 | PASS |
| `python -m pytest tests/asof/test_production_isolation.py -q` | 4 passed，0 failed，0 skipped，1 warning，0.55s | 0 | PASS |
| `git diff -- engine/asof` | 零输出 | 0 | PASS |
| `git diff -- tools/as_of_integration.py` | 零输出 | 0 | PASS |
| `python -m pytest -q` | 3119 passed，2 failed，7 skipped，1 warning，1197.69s | 1 | PASS（仅允许的两项历史失败） |
| 四个白名单路径精确状态 | 四项均为 `??`；合同是任务前既有未跟踪权威输入且本轮未改写，测试、实现、报告为本轮新增 | 0 | PASS |
| 完整 `git status --short` | 已记录大量任务前 modified/untracked 背景噪音；未清理、未覆盖、不归因于 G9-P1 | 0 | PASS |
| G9-P1 临时文件检查 | 无 `*.g9p1.tmp`、`*.g9-p1.tmp` 或等价临时文件 | 0 | PASS |

报告后全仓失败节点仍精确为：

1. `tests/evaluation/test_dataset.py::test_witness_trust_boundary_is_explicitly_documented`
2. `tests/evaluation/test_prospective_gate_workflow.py::test_handoff_names_first_legal_case_action_and_all_independent_holds`

未出现第三项失败。两处冻结路径在报告创建后仍为零 diff；最终收口检查未发现 G9-P1 临时文件残留。

G9-P1-D 判定：**PASS / COMPLETE — EVIDENCE-BOUNDED FREEZE**。

## 十、本地状态与未授权范围

**LOCAL ONLY / NOT PUSHED**

本受控会话未执行任何 GitHub 服务端写操作。当前本地结果不等于 GitHub 同步。

**G9-P2、G9-P3、G10 均未授权且未启动。**

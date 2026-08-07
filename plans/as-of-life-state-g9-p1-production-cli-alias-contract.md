# G9-P1 · as-of 生产 CLI 别名合同

> **裁决来源：** [`plans/as-of-life-state-g9-production-promotion-scope-adjudication.md`](as-of-life-state-g9-production-promotion-scope-adjudication.md:29) 已裁决选用 P1（保守）方案：只新增一个生产路径 CLI 别名脚本，**不修改** `SubmitAnalysisRequest`、`ProductionAnalysisService`、`tools/production_api.py`、`engine/asof/` 或任何既有生产文件。
>
> **Gate：`CONTRACT`。** 本文经作者起草与一轮逻辑新鲜独立复核，verdict 见第 8 节。本文不授权实现；实现只能在 CONTRACT `PASS` 且获得执行方独立、精确、非继承授权后开始。

## 1. 目标与非目标

### 1.1 目标

新增 `tools/production_as_of_cli.py`，作为 [`tools/as_of_integration.py`](../tools/as_of_integration.py:1) 的**生产路径别名**：命令行调用方式与既有 CLI 相同，唯一差异是当 `--cases-dir` / `--reports-dir` 未提供时，默认解析为生产惯例目录（即当前工作目录下的 `cases/` 与 `reports/`，与 [`ProductionAnalysisService.workspace_root`](../engine/application/production_service.py:64) 的默认约定一致），而不是依赖 [`generate_report()`](../tools/as_of_integration.py:262) 内部以 `ROOT / "reports"`（模块所在仓库根）为唯一默认。

### 1.2 非目标（继承自范围裁决第 2.3 节，本合同重复冻结以避免遗漏）

- 不修改 [`SubmitAnalysisRequest`](../engine/application/production_service.py:41)、[`ProductionAnalysisService`](../engine/application/production_service.py:54) 或 [`tools/production_api.py`](../tools/production_api.py:1)；
- 不新增或扩展任何 public API / HTTP schema；
- 不建立账本自动推导、自动核验或自动审批；
- 不默认开启 as-of 回放：`--as-of` 未提供时行为必须与直接调用 [`tools/as_of_integration.py`](../tools/as_of_integration.py:1) 完全一致；
- 不修改 `engine/asof/` 或 [`tools/as_of_integration.py`](../tools/as_of_integration.py:1) 本身；
- 不做样本外后验校准、Beta 切换或统计学习。

## 2. 唯一写入白名单

1. `plans/as-of-life-state-g9-p1-production-cli-alias-contract.md`（本文件）
2. `tests/asof/test_g9_production_cli_alias.py`
3. `tools/production_as_of_cli.py`
4. `reports/as-of-life-state-g9-p1-production-cli-alias-report.md`

超出以上四个路径的任何修改均为越权，必须 STOP。

## 3. 依赖方向

```text
tools/production_as_of_cli.py
  └─> tools.as_of_integration（generate_report、parse_iso_date、load_ledger、_parser 等 public 符号）
```

`tools/production_as_of_cli.py` **只能**导入 [`tools.as_of_integration`](../tools/as_of_integration.py:1) 中已存在的符号；不得导入 `engine.asof`、`engine.application.production_service`、`tools.production_api` 或任何其他生产模块。既有文件不得反向导入本新增文件。

## 4. 精确行为规格

### 4.1 CLI 参数

与 [`_parser()`](../tools/as_of_integration.py:316) 完全一致的位置/可选参数：`input_md`、`--as-of`、`--ledger`、`--cases-dir`、`--reports-dir`。不新增、不删除、不改名任何参数。

### 4.2 默认目录解析（唯一行为差异）

```python
default_cases_dir = Path.cwd() / "cases"
default_reports_dir = Path.cwd() / "reports"
```

- 若命令行提供 `--cases-dir`，原样传递给 [`generate_report()`](../tools/as_of_integration.py:262)，不做任何改写；
- 若未提供，本别名脚本必须显式传入 `default_cases_dir`（而不是让 `generate_report()` 收到 `None` 后走其内部默认）；
- `--reports-dir` 同理，使用 `default_reports_dir`；
- `Path.cwd()` 只在本别名脚本内调用一次，用于构造上述两个默认值；不得在其他分支重复调用或缓存跨调用状态。

### 4.3 参数配对、账本加载、错误处理、退出码

全部**原样委托**给 [`tools.as_of_integration.main()`](../tools/as_of_integration.py:326) 的等价逻辑：`--as-of` 与 `--ledger` 必须成对提供（否则退出码 2）；`OSError`/`ValueError`/`KeyError`/`TypeError`/`json.JSONDecodeError` 统一捕获为退出码 2 并打印 `错误：{exc}`；成功时打印报告路径并退出码 0。本别名脚本不得重新实现这些逻辑的第二份拷贝——必须直接调用 [`tools.as_of_integration.parse_iso_date()`](../tools/as_of_integration.py:42)、[`tools.as_of_integration.load_ledger()`](../tools/as_of_integration.py:168)、[`tools.as_of_integration.generate_report()`](../tools/as_of_integration.py:262) 等既有 public 函数，只在默认目录解析这一点上插入差异。

### 4.4 `main(argv)` 精确顺序

1. 解析参数（复用 [`_parser()`](../tools/as_of_integration.py:316) 或等价 argparse 定义，参数集合必须逐一相同）；
2. 校验 `--as-of`/`--ledger` 成对；
3. 计算 `cases_dir` / `reports_dir`：命令行值优先，否则使用 4.2 的默认值；
4. 若提供 `--as-of`，调用 [`load_ledger()`](../tools/as_of_integration.py:168) 并解析日期；
5. 调用 [`generate_report()`](../tools/as_of_integration.py:262)，传入上述已解析的 `cases_dir`/`reports_dir`；
6. 异常处理与退出码与 4.3 一致。

## 5. failure ledger

| ID | 条件 | 必须结果 |
|---|---|---|
| G9P1-F01 | `--cases-dir`/`--reports-dir` 均未提供 | 必须使用 `Path.cwd()/"cases"` 与 `Path.cwd()/"reports"`，不得回退到 `generate_report()` 内部 `ROOT` 默认 |
| G9P1-F02 | `--cases-dir`/`--reports-dir` 已提供 | 原样传递，不改写、不与默认值合并 |
| G9P1-F03 | `--as-of` 与 `--ledger` 只提供一个 | 退出码 2，不调用 `generate_report()` |
| G9P1-F04 | 未提供 `--as-of` | 行为必须与直接调用 `python -m tools.as_of_integration` 在相同 `cases_dir`/`reports_dir` 下逐字节一致（不追加快照章节） |
| G9P1-F05 | 本文件导入 `engine.asof`、`engine.application.production_service` 或 `tools.production_api` | 合同违反；必须 STOP |
| G9P1-F06 | 测试通过 monkeypatch 伪造 `generate_report` 返回值而非验证真实委托调用 | 静态复核必须拒绝；测试必须验证真实委托语义（见第 6 节） |

## 6. 测试选择器最小要求

[`tests/asof/test_g9_production_cli_alias.py`](../tests/asof/test_g9_production_cli_alias.py:1) 至少覆盖：

1. 未提供 `--cases-dir`/`--reports-dir` 时，实际调用 [`tools.as_of_integration.generate_report()`](../tools/as_of_integration.py:262) 收到的 `cases_dir`/`reports_dir` 等于 `Path.cwd()/"cases"` 与 `Path.cwd()/"reports"`（可用 `monkeypatch` 拦截 `generate_report` 调用参数进行断言，但不得用来伪造返回值绕过真实调用路径存在性检查）；
2. 提供 `--cases-dir`/`--reports-dir` 时原样传递，不与默认值合并；
3. `--as-of` 与 `--ledger` 只提供一个时退出码为 2；
4. 端到端：不提供 `--as-of` 时，本别名脚本与直接调用 `tools.as_of_integration` 在相同临时目录下产生完全相同的报告文件内容；
5. 静态导入检查：本别名脚本源码不包含 `engine.asof`、`engine.application.production_service`、`tools.production_api` 的导入语句。

## 7. Gate 顺序（沿用 G8 的 A/B/C/D 命名）

- **G9-P1-A**：本合同（CONTRACT）；
- **G9-P1-B**：新增测试，首次运行必须因模块不存在而 RED；
- **G9-P1-C**：实现最小别名脚本，取得 GREEN、导入方向静态核验、既有 `tests/asof` 全套与生产隔离测试证据、全仓 sanity（允许且仅允许两项已知历史失败）；
- **G9-P1-D**：撰写验证报告并做报告后最终新鲜复核。

STOP 条件与 G8 完全一致：需要修改 `engine/asof/`、需要修改任何禁止路径、首次测试直接 PASS、全仓出现第三项失败、任何可能修改 GitHub 服务端状态的动作。

## 8. fresh independent read-only CONTRACT review

- **Reviewer role：** logical fresh Static Reviewer；不采纳作者自检。
- **审查输入：** 本文件、[`范围裁决文档`](as-of-life-state-g9-production-promotion-scope-adjudication.md:1)、[`tools/as_of_integration.py`](../tools/as_of_integration.py:1) 全文、[`ProductionAnalysisService`](../engine/application/production_service.py:54)。
- **副作用边界：** 仅本地文档读取；未执行 Python、pytest、Git 或 GitHub-mutating operation。

### 8.1 Observed facts

1. 第 2 节写集与范围裁决 P1 描述的"只新增一个 CLI 别名脚本"一致，未包含 `engine/application/production_service.py` 或 `tools/production_api.py`。
2. 第 3 节依赖方向单向指向 `tools.as_of_integration`，与 G8 已冻结的单向依赖模式（新增薄层只能向下依赖，不能被既有文件反向依赖）同构，未发现新增反向依赖风险。
3. 第 4.2 节的默认目录差异是本合同唯一定义的行为增量；其余全部行为（参数校验、账本加载、错误码、追加协议）明确要求委托而非重新实现，避免第二份逻辑拷贝产生的漂移风险。
4. 第 6 节测试要求同时验证正向委托（真实调用存在）与负向导入边界（源码级 import 检查），覆盖 G9P1-F01–F06。

### 8.2 Falsifier disposition

- 若本合同允许别名脚本重新实现账本加载或日期解析逻辑（产生第二份拷贝），应为 `REVISE`；第 4.3/4.4 已明确禁止。
- 若测试只能通过 mock 掉 `generate_report()` 返回值而不验证其接收参数，会导致 G9P1-F06 描述的假阳性风险；第 6.1 节已要求断言实际接收参数，falsifier 未成立。
- 若默认目录解析逻辑与 `ProductionAnalysisService.workspace_root` 的默认约定（`Path.cwd()`）不一致，会与"生产惯例目录"的目标矛盾；第 4.2 节已显式对齐 `Path.cwd()`。

### 8.3 Verdict

**Verdict：`PASS`。** 写集精确、依赖单向、唯一行为差异明确冻结、failure ledger 与测试选择器可机械对照、非目标边界与范围裁决一致。

不得推导：本 PASS 不证明实现已存在、测试已通过、全仓兼容或授予任何实现权限。

**唯一下一合法动作：** 取得独立执行授权后进入 G9-P1-B（新增测试并取得首次 RED）。

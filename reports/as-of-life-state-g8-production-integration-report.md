# G8 as-of 系统生产集成验证报告

> 验证范围：G8 as-of 生产薄接线层
>
> 验证日期：2026-07-26（Asia/Shanghai）
>
> 结论状态：**PASS——G8 生产薄接线、测试、隔离、冻结目录与收口证据全部满足；全仓仅保留两项已知历史失败，无第三项失败**

## 一、验证目标与边界

G8 的目标是在不修改既有生产源码和 `engine/asof/` 的前提下，新增一个工具层生产编排入口：运行既有生产 pipeline 与标准报告渲染器，并在调用方显式提供截止日及受控事件账本时，调用既有 as-of 状态回放能力，在统一报告末尾追加唯一的“截止状态快照”章节。

本轮写入白名单仅包含：

1. `plans/as-of-life-state-g8-production-integration-spec.md`
2. `tests/asof/test_g8_production_integration.py`
3. `tools/as_of_integration.py`
4. `reports/as-of-life-state-g8-production-integration-report.md`

明确禁止修改：

- `engine/asof/`；
- `engine/` 下任何既有生产文件；
- 既有 `tests/asof/` 测试；
- G0-G7 冻结文档；
- 案例原文与任何既有报告；
- 其他未授权路径。

本报告只归因上述四项 G8 文件。工作区存在大量任务开始前已有的 modified/untracked 背景内容，不清理、不覆盖，也不归因于 G8。

## 二、冻结的生产集成契约

### 2.1 单向依赖

```text
tools/as_of_integration.py
  ├─> engine.application.pipeline_runner.run_pipeline_e2e
  ├─> tools.render_report.render_from_output
  └─> engine.asof.state_ledger
```

G8 不建立任何反向依赖：生产 pipeline 与标准渲染器均不得导入 G8 薄层或 `engine.asof`；`engine/asof` 也不得导入生产 pipeline、报告、timing 或 F09。

### 2.2 时间与账本协议

- 截止日必须由调用方显式给出，不读取系统当前时间；
- CLI 日期仅接受规范 `YYYY-MM-DD`；
- 指定截止日时，事件账本、运尾、现实中心和账本 case ID 必须显式提供；
- 不从生产输入、known facts 或报告文本臆造事件证据；
- pipeline 返回后、渲染前验证账本 case ID 与生产输出 case ID 一致；
- 不指定截止日时，不调用 as-of 状态回放，也不允许夹带 as-of 上下文。

### 2.3 报告协议

- 标准渲染器先生成完整基础报告；
- as-of 薄层只在字符串末尾追加一个独立的 `## 截止状态快照` 章节；
- 原报告正文保持不变；
- 已有同名章节时原样返回，避免重复追加；
- 展示内容不包含 statement ID、内部推理索引或其他内部编号；
- 目标报告已存在且内容不同时拒绝覆盖；内容相同时视为幂等成功；
- 新报告通过同目录临时文件和原子替换写入，异常路径清理临时文件。

## 三、G8-A：规格门禁

规格先完成生产入口、参数成组约束、账本事实边界、追加公式、写盘保护和依赖方向的冻结。

逻辑复核发现并修订了三类契约问题：

1. “已有快照标题拒绝”与“重复调用幂等”冲突，最终冻结为已有标题时原样返回；
2. “不得回写 statement index”与标准渲染器既有副作用冲突，最终限定为 G8 薄层不自行修改 statement 制品；
3. 可空接口参数缺乏成组约束，最终冻结为指定截止日后必须显式提供完整账本上下文。

实现静态复核又发现 `ledger_case_id` 与冻结签名漂移；规格随后补入该参数及 pipeline 后、render 前的一致性校验。修订后的规格与实现签名一致。

G8-A 判定：**PASS**。

## 四、G8-B：TDD RED 门禁

首次运行命令：

```text
python -m pytest tests/asof/test_g8_production_integration.py -q
```

首次有效结果：

```text
11 failed in 0.40s
exit code 1
```

11 个实例均因 `ModuleNotFoundError: No module named 'tools.as_of_integration'` 失败。pytest 已完成测试收集，因此这是行为阶段的有效 RED，而不是 collection error。

RED 后静态检查发现测试 helper 的两个自身缺陷：`EvidenceRef` 参数数量错误，以及使用了不存在的 `VerificationStatus.UNVERIFIED`。修订 helper 后再次运行同一命令：

```text
11 failed in 0.38s
exit code 1
```

11 个实例仍全部因缺失 `tools.as_of_integration` 失败，证明测试修订未丢失 RED。

测试文件含 10 个测试函数，其中一个测试双参数化，静态预期实例数与动态收集数均为 11。

G8-B 判定：**PASS（有效 RED 已保留）**。

## 五、G8-C：实现与验证证据

### 5.1 最小实现

新增工具层入口完成以下职责：

- 调用 `run_pipeline_e2e(..., do_render=False, error_policy="strict")`；
- 调用标准 `render_from_output()`；
- 将受控 JSON ledger 显式适配为冻结的 as-of dataclass；
- 调用真实 `build_verified_state()`；
- 追加唯一快照章节；
- 拒绝覆盖不同内容的既有报告并原子写盘；
- 提供程序 API 和 `python -m tools.as_of_integration` CLI。

生产源码和 `engine/asof/` 均未为 G8 修改。

### 5.2 专用集成测试

命令：

```text
python -m pytest tests/asof/test_g8_production_integration.py -q
```

结果：

```text
11 passed
exit code 0
```

覆盖范围包括：规范日期、CLI 参数配对、账本透传、默认路径不调用 as-of、调用顺序、case ID 与截止日、真实状态回放过滤、章节唯一性与幂等性、空事实状态、case ID 不一致 fail-closed、拒绝覆盖及临时文件清理。

### 5.3 as-of 全套测试

命令：

```text
python -m pytest tests/asof -q
```

结果：

```text
112 passed, 1 skipped, 1 warning
exit code 0
```

唯一 skipped 是 G6 evidence gate：样例输入缺少显式十神及藏干十神字段，而推导被禁止。warning 是既有 `dual_engine_adapter` deprecation warning，不构成 G8 失败。

### 5.4 生产隔离测试

命令：

```text
python -m pytest tests/asof/test_production_isolation.py -q
```

结果：

```text
4 passed, 1 warning
exit code 0
```

四项隔离不变量均通过：默认 registry/pipeline/claim rules 未扩展、公共 schema 未扩展、`engine/asof` 未反向导入生产组件、生产 pipeline/report 未导入 `engine.asof`。

### 5.5 冻结目录差异

命令：

```text
git diff -- engine/asof
```

结果：零输出，exit code 0。

### 5.6 全仓 sanity

为恢复 provider 未回传的首次长运行尾部，先确认原 pytest 主进程已退出；pytest 缓存含跨阶段陈旧失败节点，不能替代本轮结果，因此重新运行同一条全仓命令取得完整新鲜证据：

```text
python -m pytest -q
```

结果：

```text
2 failed, 3113 passed, 7 skipped, 1 warning in 1352.25s
exit code 1
```

两项失败恰为任务开始前已登记的历史失败：

1. `tests/evaluation/test_dataset.py::test_witness_trust_boundary_is_explicitly_documented`
2. `tests/evaluation/test_prospective_gate_workflow.py::test_handoff_names_first_legal_case_action_and_all_independent_holds`

没有出现第三项失败，因此未触发 G8 STOP 条件。7 项 skipped 均由测试自身的显式 gate/历史模板或缺失历史报告条件产生；唯一 warning 仍为既有生产 adapter 的 deprecation warning。

G8-C 判定：**PASS（全仓存在两项已知历史失败；无 G8 新增失败）**。

## 六、独立证据复核

### 6.1 直接证明

现有证据直接证明：

- 新入口在默认路径不调用 as-of；
- 显式截止日路径按 pipeline → render → as-of 的冻结顺序工作；
- 截止日后、未确认及已失效事件不会进入展示状态；
- 快照章节只出现一次，基础报告正文不变；
- 账本 case ID 不一致时在渲染和写盘前失败；
- 不同内容的既有报告不会被覆盖；
- `engine/asof/` 无 G8 diff；
- as-of 全套与生产隔离测试通过；
- 全仓没有两项已知历史失败之外的第三项失败。

### 6.2 未证明与边界

本轮不声称：

- 普通生产输入能够自动生成完整事件账本；
- 未提供显式证据时系统能够推断现实事件；
- 两项历史全仓失败已修复；
- 既有 deprecation warning 已消除；
- GitHub 服务端存在任何部署、PR、push 或远端状态变化；
- G9 已获得授权或已经启动。

## 七、报告后最终新鲜复核

报告创建后逐项重新执行验证，结果如下：

| 检查 | 新鲜结果 | Exit code | 判定 |
|---|---:|---:|---|
| `python -m pytest tests/asof/test_g8_production_integration.py -q` | 11 passed，1 warning | 0 | PASS |
| `python -m pytest tests/asof -q` | 112 passed，1 skipped，1 warning | 0 | PASS |
| `python -m pytest tests/asof/test_production_isolation.py -q` | 4 passed，1 warning | 0 | PASS |
| `git diff -- engine/asof` | 零输出 | 0 | PASS |
| 四项授权路径状态 | 4 个授权文件均为新增文件 | 0 | PASS |
| G8 临时文件检查 | 无 `*.g8.tmp` 残留 | 0 | PASS |
| 完整工作区状态 | 已记录；其他 modified/untracked 项属于任务前背景，不归因于 G8 | 0 | PASS |

最终专用测试动态实例数为 11，与测试设计中的 10 个函数加 1 个额外参数化实例一致。报告后验证未产生 G8 临时文件，也未改变冻结的 `engine/asof/`。

G8-D 判定：**PASS**。

## 八、本地状态声明

**LOCAL ONLY / NOT PUSHED**

本轮未执行任何 GitHub 服务端写操作，未 push、未创建 PR、未修改远端对象。

**G9 未授权且未启动。**

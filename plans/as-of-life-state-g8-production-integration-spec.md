# G8 as-of 系统生产集成规格

> 状态：G8-A 冻结候选；仅授权本地生产集成验证，不授权 G9，不授权任何远端发布。

## 1. 目标

在不修改既有生产模块与 `engine/asof/` 的前提下，新增单向薄编排入口 `tools/as_of_integration.py`：

1. 复用既有生产 pipeline 与唯一标准报告渲染器；
2. 生产命令接受可选参数 `--as-of YYYY-MM-DD`；
3. 指定截止日时，用显式事件账本调用 `engine.asof.state_ledger.build_verified_state()`；
4. 把快照追加为统一报告末尾唯一的独立章节 `## 截止状态快照`；
5. 未指定截止日时，不执行 as-of 回放，也不增加该章节；
6. 既有报告正文逐字保持不变。

## 2. 授权与依赖边界

### 2.1 唯一写入白名单

- `plans/as-of-life-state-g8-production-integration-spec.md`
- `tests/asof/test_g8_production_integration.py`
- `tools/as_of_integration.py`
- `reports/as-of-life-state-g8-production-integration-report.md`

### 2.2 禁止修改

- `engine/asof/` 下任何文件；
- `engine/` 下任何既有生产文件；
- `tools/render_report.py`、`tools/batch_intake.py` 等既有工具；
- 既有测试、G0-G7 冻结文档、案例原文与既有报告。

### 2.3 单向依赖

依赖方向只能是：

```text
tools/as_of_integration.py
  ├─> engine.application.pipeline_runner.run_pipeline_e2e
  ├─> tools.render_report.render_from_output
  └─> engine.asof.state_ledger
```

既有生产 pipeline、报告渲染器与 `engine/asof/` 均不得反向依赖薄层。既有生产源码不得新增 `engine.asof` 导入。默认 runner registry、`run_pipeline()` 签名和公共 schema 均不得改变。

## 3. 公共程序接口

薄层冻结以下最小接口；命名可在实现前由测试精确锁定，但语义不得改变：

```python
def generate_report(
    input_md_path: str | Path,
    *,
    as_of_date: date | None = None,
    entries: tuple[EventLedgerEntry, ...] | None = None,
    daiyun_end: date | None = None,
    current_center: str | None = None,
    reasonable_range: tuple[str, ...] = (),
    ledger_case_id: str | None = None,
    cases_dir: str | Path | None = None,
    reports_dir: str | Path | None = None,
) -> Path:
    ...
```

行为：

1. 调用 `run_pipeline_e2e(input_md_path, cases_dir=..., do_render=False, error_policy="strict")` 获得生产 `AnalysisOutput`；
2. 调用 `render_from_output(output, variant="standard", lint_before=True, cases_dir=..., skip_findings_save=True)` 获得原始统一报告 Markdown；
3. `as_of_date is None` 时直接写原始 Markdown；此时 `entries`、`daiyun_end`、`current_center`、`ledger_case_id` 与非空 `reasonable_range` 均不得提供；
4. `as_of_date` 非空时，`entries`（允许空 tuple）、`daiyun_end`、非空 `current_center` 与非空 `ledger_case_id` 必须显式提供，缺少任一项均在调用 pipeline 与写盘前抛出 `ValueError`；
5. pipeline 返回后、渲染前必须验证 `ledger_case_id == output.case_id`；参数完整且一致时，构造 `AsOfRequest(output.case_id, as_of_date)` 并调用 `build_verified_state()`；
6. 追加快照章节后写入 `{reports_dir}/{case_id}-content-report.md`；
7. 返回最终报告路径。

`entries` 必须是已经通过 `engine.asof` 数据类校验的事实账本。薄层不得从普通命盘 Markdown、`known_facts` 或当前系统时间臆造事件、证据、状态或截止日。

## 4. CLI 契约

入口：

```text
python -m tools.as_of_integration INPUT_MD [--as-of YYYY-MM-DD]
    [--ledger LEDGER_JSON]
    [--cases-dir CASES_DIR]
    [--reports-dir REPORTS_DIR]
```

规则：

- `INPUT_MD` 必填；
- `--as-of` 可选，必须由 `date.fromisoformat()` 严格解析，并额外要求原文本等于 `parsed.isoformat()`，从而拒绝非规范日期文本；
- 未指定 `--as-of` 时禁止指定 `--ledger`；
- 指定 `--as-of` 时 `--ledger` 必填；
- 参数或账本错误返回非零 exit code，且不得写报告；
- 成功时打印最终报告路径并返回 0；
- 不读取 `date.today()`、`datetime.now()` 或其他隐式截止时间。

## 5. 账本 JSON 契约

账本是受控内部制品，不是从案例原文自动抽取。顶层对象必须包含：

```json
{
  "case_id": "C-...",
  "daiyun_end": "YYYY-MM-DD",
  "current_center": "非空现实中心",
  "reasonable_range": ["可选范围"],
  "entries": []
}
```

每个 `entries` 元素必须包含两个完整对象：

- `candidate`：覆盖 `LifeEventCandidate` 的全部构造字段；其嵌套 `AnnualInteractionTrace`、`EvidenceRef`、`SourceCitation` 也必须完整；
- `assessment`：覆盖 `EventImpactAssessment` 的必填字段，并可显式提供全部可选字段。

适配规则：

- 日期仅接受规范 `YYYY-MM-DD` 字符串；
- tuple 字段在 JSON 中必须为 array，加载后转换为 tuple；
- enum 字段按冻结枚举值构造，未知值报错；
- 禁止补造 evidence、citation、verification status、impact、persistence、scope 或 practitioner final；
- JSON `case_id` 必须与 pipeline 输出 `case_id` 相同，否则在回放与写盘前失败；
- 空 `entries` 合法，表示截止日没有可进入事实状态的已核验事件；
- `current_center` 必须为非空字符串；
- 所有原型数据类自身的 `ValueError` 保持可见，薄层不得降级吞错。

## 6. 截止状态章节

章节固定追加在原报告末尾，格式为：

```markdown
## 截止状态快照

- 截止日期：YYYY-MM-DD
- 当前现实中心：...
- 合理范围：...（空时为“无”）
- 已核验事件：...（空时为“无”）
- 当前有效状态：...（空时为“无”）
- 现实路径状态：...（空时为“无”）
- 决策动作：OUTPUT
```

路径状态以稳定、可审计顺序输出 `path_id=status（来源：source_event_id）`。列表项沿 `VerifiedState` / `RealityTrack` 返回顺序输出，不在展示层重新推断或排序事件优先级。

### 6.1 追加不变量

设生产原报告为 `base`，快照章节为 `section`：

```text
final = base.rstrip("\n") + "\n\n" + section.rstrip("\n") + "\n"
```

必须满足：

- `final` 在章节标记前的内容等于 `base.rstrip("\n") + "\n\n"`；
- 不重排、不替换、不删除任何既有标题或正文；
- 最终报告仅出现一次 `## 截止状态快照`；
- 若输入 Markdown 已含该标题，追加函数必须原样返回输入文本，不覆盖、不解析也不生成第二个章节；
- 对同一 `base` 与同一快照重复调用章节追加函数，结果必须幂等；
- 不把 `statement_id`、共识 ID、内部推理索引或 Agent 记录写入展示章节。

## 7. 失败关闭与原子写入

- 必须在所有 pipeline、渲染、账本加载、case_id 校验、回放和章节构造成功后才写最终报告；
- 最终报告使用同目录临时文件后 `Path.replace()` 原子替换；
- 临时文件名必须可预测地归属于目标报告，并在替换失败时尽力删除；
- 任何失败不得留下部分报告或临时文件；
- 不修改已有报告：若目标报告已存在且内容不同，薄层默认拒绝覆盖；仅当它等于本次完整期望内容时视为幂等成功。

该“拒绝覆盖”约束保护既有报告，并使本次 G8 测试只能在临时 `reports_dir` 中写盘。

## 8. 测试契约（G8-B）

新增测试不少于七项，至少覆盖：

1. CLI 接受规范 `--as-of`，拒绝无效或非规范日期；
2. `--as-of` 与 `--ledger` 的成对约束，以及默认路径不触发 as-of；
3. 程序入口按顺序调用生产 pipeline、标准渲染器和 `build_verified_state()`；
4. `AsOfRequest.case_id` 来自生产输出，截止日来自显式参数；
5. 截止日后、未确认或已失效事件不进入展示快照（用真实 `engine.asof` 回放验证）；
6. 快照章节只追加一次，原报告正文逐字不变且重复追加幂等；
7. 空事实状态按“无”展示，不伪造事件或状态；
8. ledger `case_id` 不一致时在写盘前失败；
9. 已存在且内容不同的报告拒绝覆盖；
10. 生产 pipeline、渲染或账本错误时不留报告与临时文件。

TDD 纪律：测试文件首次执行必须因 `tools.as_of_integration` 尚不存在或接口未实现而 RED；若首次直接通过，G8 立即停止并重新设计测试，不得把直接 PASS 计为有效 RED。

## 9. 验证 Gate

按顺序取得新鲜证据并记录 exit code：

```text
pytest tests/asof/test_g8_production_integration.py -q
pytest tests/asof -q
pytest tests/asof/test_production_isolation.py -q
git diff -- engine/asof
git diff -- plans/as-of-life-state-g8-production-integration-spec.md tests/asof/test_g8_production_integration.py tools/as_of_integration.py reports/as-of-life-state-g8-production-integration-report.md
git status --short
```

最终集成测试至少 `7 passed`；as-of 全套全通过；生产隔离必须 `4 passed`；`git diff -- engine/asof` 必须零输出。

若执行全仓 sanity，除以下两个历史失败外不得出现第三个失败：

- `tests/evaluation/test_dataset.py::test_witness_trust_boundary_is_explicitly_documented`
- `tests/evaluation/test_prospective_gate_workflow.py::test_handoff_names_first_legal_case_action_and_all_independent_holds`

## 10. 非目标

- 不把 as-of 接入默认 runner registry 或 `run_pipeline()`；
- 不扩展 `AnalysisOutput`、公共 schema 或报告模板；
- 不自动抽取、预测或补造事件账本；
- 不生成 hypothesis 分支、财富传播或新的命理规则；
- 不改变生产报告既有章节；
- as-of 薄层不自行修改或回写案例、反馈、statement 制品；标准 pipeline 与标准渲染器按既有契约产生的制品副作用不属于 G8 扩展；
- 不启动 G9，不提交、不推送、不发布。

## 11. STOP 条件

出现任一项立即停止：

- 需要修改 `engine/asof/`；
- 需要修改任一既有生产文件或禁止路径；
- 首次新增集成测试直接通过而没有 RED；
- 全仓出现两项已知失败之外的第三个失败；
- 无法在不臆造事件证据的情况下满足账本契约；
- 任何动作可能修改 GitHub 服务端状态。

## 12. G8-A 契约判定边界

本规格只冻结接线协议、失败语义、测试选择器和保护边界。它不证明实现正确、不证明测试通过、不证明全仓兼容，也不授权 G9。G8-A 只有在逻辑新鲜复核确认：目标唯一、白名单精确、依赖单向、输入显式、失败关闭、测试可证伪且无 STOP 条件激活后，才能判定 PASS 并进入 G8-B。

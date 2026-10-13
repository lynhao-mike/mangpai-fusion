# Unit11 · 第二真实案例 as-of 会话制品化证据报告

## 最终判定

**PASS / COMPLETE — EVIDENCE-BOUNDED FREEZE**

判定时间：2026-07-28（Asia/Shanghai）。

本结论仅覆盖 Unit11 冻结写集与本报告记录的新鲜本地证据，不外推为生产入口切换、所有案例泛化、规则准确率或未来预测准确率证明。

## 1. 交付边界

Unit11 新增一个**历史/手动 side path**：`tools/as_of_session_cli.py`。它是**手动 opt-in 旁路，不切换任何生产默认入口**。

完整调用链：

```text
显式 UTF-8 JSON
  → 既有 as-of dataclass / enum
  → engine.asof.session_runner.run_career_session()
  → engine.asof.archive_integration.archive_asof_state()
  → 既有 verified artifact
  → 本地归档读回与 digest 校验
```

没有修改既有 `engine/asof/*.py`，没有修改既有 `tests/asof/*.py`，没有网络、服务、Git 写操作或 GitHub mutation。

## 2. 第二真实案例证据

选定：`C-2026-RF000118-乾-己巳癸酉辛丑己丑`。

排除：

- Unit8/9：`C-2026-024-坤-己巳壬申辛亥壬辰`
- Unit10：`C-2026-RF000475-坤-戊辰辛酉己巳乙丑`

### 2.1 命盘事实来源

`cases/C-2026-RF000118-乾-己巳癸酉辛丑己丑/input.md`：

- 第 27–40 行：乾命与己巳、癸酉、辛丑、己丑四柱。
- 第 41–75 行：四支藏干。
- 第 76–120 行：连续 1–8 步大运。
- 第 139–144 行：辛日干在四支的十二长生。

### 2.2 现实核验来源

`cases/C-2026-RF000118-乾-己巳癸酉辛丑己丑/feedback.md` 第 34 行明确记录：2020 年 4 月跳槽华为，工资大幅提升，同时工作强度明显上升。

fixture 冻结一个 2020 年 `job_change` 候选；核验后唯一 confirmed ID 为 `career-2020-job-change`。2022 年股票研究、家庭事实及 2026/2027 未核验信息没有进入 ledger 成功语义、verified state 或 projection 主线。

## 3. 实现证据

### 3.1 严格输入

- 顶层、draft、候选、建议、裁决、投影和 archive 元数据均执行闭字段检查。
- 日期要求 `YYYY-MM-DD`。
- enum 使用既有封闭值域。
- `blind_input` 委托 `blind_chart_input_from_mapping()`。
- 每个冻结事件通过 `evaluate_event_candidate()` 候选门构造。
- verification 委托 `verification_input_from_mapping()`。
- `$computed` 仅在工具边界替换为同 identity、blind input、draft 构造的精确 freeze package digest；真实 64 位 digest 保持原值并由引擎校验。

### 3.2 runner 与 archive

专项测试以 monkeypatch 计数证明一次 callable 调用中：

- `run_career_session()` 恰好调用一次。
- `archive_asof_state()` 恰好调用一次。

工具没有定义新的 artifact schema。归档后重新读取目标 JSON，校验八字段集合、artifact ID、canonical payload SHA-256、`source_digest` 与 `payload_digest`。

### 3.3 CLI

成功输出结构化 JSON，包括 archive path、artifact ID、payload digest、case ID、as-of date、最终状态和是否生成 projection。

缺少 `draft` 的反例证明：

- `main()` 返回 1。
- stderr 返回结构化 JSON。
- `error_code=INVALID_VALUE`。
- 直接调用 callable 时原始 `SessionContractError` 与 `.code` 保持可见。

## 4. Fresh static review

审查覆盖：

- 闭字段与缺字段；
- 日期、枚举与 tuple 转换；
- freeze digest 绑定；
- 候选门不绕过；
- 可选 projection 的省略/显式数组语义；
- wealth binding 对 confirmed IDs 的顺序覆盖；
- callable 异常不吞；
- CLI 结构化错误；
- archive 路径覆盖与读回；
- 手动旁路声明；
- production import 隔离。

发现并修正两项：

1. CLI 最初捕获 `BaseException` 后显式重抛中断类；收窄为 `Exception`，避免过宽捕获。
2. 首轮测试将裸字符串 `2026` 当作未核验语义，误命中合法 case/session 元数据；根因是断言层级错误。修正为只检查 ledger、verified state 和 projection 的语义投影，并使用具体未核验短语。修正后专项 6/6 通过。

Gate 5 逻辑 fresh evidence review 另发现一项契约描述偏差：契约曾误写 fixture 冻结 2015、2019、2020、2021、2023 五个事件，而实际 fixture 与测试始终只冻结 2020 年事件。该项分类为 contract gap；已最小修正为“多个事件仅证明案例来源适合遴选，Unit11 只冻结 feedback 第 34 行的 2020 年事件”。修正不涉及代码、fixture、测试选择器或运行行为；复核后 contract、fixture 与本报告一致。

AST 新鲜扫描结果：`forbidden=[]`。测试同时冻结以下前缀不得导入：

- `engine.pipeline`
- `engine.v5.runner`
- `engine.v5.preprod`
- `tools.render_report`
- `tools.feedback*`
- `engine.asof.natal_capacity`
- `engine.asof.structural_track`
- `engine.asof.daiyun_context`

## 5. 新鲜验证结果

### 5.1 Smoke

```text
python -m py_compile tools\as_of_session_cli.py
run_and_archive_session(..., temporary archive root)
```

结果：`CREATED PROJECTED 1 1`，即一个 confirmed 事业事件和一个显式财富状态。

### 5.2 CLI

```text
python -m tools.as_of_session_cli cases\C-2026-RF000118-乾-己巳癸酉辛丑己丑\asof_session_input.json --archive-root .pytest_cache\unit11-cli-review
```

结果：返回码 0，`status=CREATED`，`session_state=PROJECTED`，`projection_created=true`。Windows cmd 展示中文时发生终端代码页乱码，但 JSON 文件、Python 读回、case identity 和测试断言均按 UTF-8 正确处理；不影响 artifact digest 或语义。

### 5.3 Unit11 专项

```text
pytest tests\asof\test_unit11_second_case_session_productization.py -q
```

最终结果：`6 passed in 0.57s`。

覆盖：完整链、CREATED/UNCHANGED、读回 digest、成功语义隔离、缺字段结构化错误、一次委托、真实来源与排除集、AST/手动旁路边界。

### 5.4 as-of 全量

```text
pytest tests\asof\ -q
```

结果：`467 passed, 1 skipped, 1 warning in 3.03s`。

唯一 skip 是既有 G6 证据门：案例缺少显式十神字段，禁止推导。唯一 warning 是既有 deprecated adapter 警告，非 Unit11 引入。

### 5.5 production isolation

```text
pytest tests\asof\test_production_isolation.py -q
```

结果：`4 passed, 1 warning in 0.59s`。

### 5.6 既有测试 SHA-256 保护

范围：`tests/asof/test_*.py`，排除新增 `test_unit11_second_case_session_productization.py`。

- 既有文件数：24。
- 实施前 ledger SHA-256：`7827c645aa20d4744202719b38492e5422bb5b165b60c5a5392d68d96fb1bc5e`。
- 实施后 ledger SHA-256：`7827c645aa20d4744202719b38492e5422bb5b165b60c5a5392d68d96fb1bc5e`。
- 判定：`changed=0`。

## 6. 制品语义

本地 verified artifact 使用既有 `engine.archive` 八字段格式，且 Unit11 读回确认：

- 最终 envelope：`PROJECTED`。
- confirmed event：仅 `career-2020-job-change`。
- active state：仅 `state:career-2020-job-change`。
- career mainline：只引用上述 active state。
- wealth binding：精确覆盖 confirmed IDs，显式边仅传播反馈确认的 2020 工资提升。
- family、education、marriage、health 保持既有 `NOT_IMPLEMENTED / ABSTAIN`。

仓库中 `.pytest_cache` 下的 smoke/CLI 制品只是验证临时输出，不属于冻结交付写集；正式使用时由操作者显式指定本地 archive root。

## 7. 冻结收益与边界

已证明：

1. 既有完整 as-of 会话链可以由磁盘 JSON 手动调用并归档。
2. 一个未被 Unit8/9/10 使用的真实案例可通过同一编排路径。
3. 真实反馈的 verified 信息与未核验信息保持隔离。
4. 不需要修改 engine、artifact schema 或生产默认入口。

未证明：

- 自动从 case 文本抽取盲断 draft；
- 对任意案例自动生成候选；
- 命理预测准确率；
- 生产 promotion；
- 网络或服务化运行。

因此 Unit11 在其冻结契约范围内达到 **PASS / COMPLETE — EVIDENCE-BOUNDED FREEZE**。

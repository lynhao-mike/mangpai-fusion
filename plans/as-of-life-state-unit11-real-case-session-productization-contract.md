# Unit11 · as-of 会话制品化与第二真实案例泛化证明契约

## 1. 冻结目标

Unit11 将既有 as-of 事业会话完整链产品化为一个**历史/手动旁路**：从显式结构化 JSON 构造既有领域对象，调用 `engine.asof.session_runner.run_career_session()`，再调用 `engine.asof.archive_integration.archive_asof_state()`，生成并读回校验既有 verified artifact。

本工具是**手动 opt-in 旁路，不切换任何生产默认入口**。它不接入生产 pipeline、报告渲染、反馈摄入、服务、网络或公开 schema。

## 2. 第二真实案例遴选冻结

### 2.1 排除集

以下案例已被 Unit8/9/10 使用，不得作为第二案例：

- `C-2026-024-坤-己巳壬申辛亥壬辰`（Unit8、Unit9）
- `C-2026-RF000475-坤-戊辰辛酉己巳乙丑`（Unit10）

### 2.2 选定案例

冻结选择：`C-2026-RF000118-乾-己巳癸酉辛丑己丑`。

选择依据：

1. `cases/C-2026-RF000118-乾-己巳癸酉辛丑己丑/input.md` 提供乾坤、四柱、逐支藏干、逐柱十二长生和连续 1–8 步大运。
2. `cases/C-2026-RF000118-乾-己巳癸酉辛丑己丑/feedback.md` 提供 2015、2019、2020、2021、2023 年多个明确到年的真实事业事件，足以证明案例来源适合第二案例遴选；为保持成功语义最小且可审计，Unit11 fixture 仅冻结其中第 34 行明确记载的 2020 年跳槽华为事件，其余事件不进入本单元 confirmed 事业成功语义。
3. 案例不在 Unit8/9/10 排除集中。
4. 正式 case 已归一化；不依赖含“待补”字段的 raw draft。

## 3. 唯一允许写集

除追加式修改 `handoff.md` 外，Unit11 仅允许新增：

- `plans/as-of-life-state-unit11-real-case-session-productization-contract.md`
- `tools/as_of_session_cli.py`
- `cases/C-2026-RF000118-乾-己巳癸酉辛丑己丑/asof_session_input.json`
- `tests/asof/test_unit11_second_case_session_productization.py`
- `reports/as-of-life-state-unit11-second-case-session-productization-report.md`

禁止修改既有 `engine/asof/*.py`、既有 `tests/asof/*.py`、生产入口、公开 schema、服务配置及任何其他文件。

## 4. JSON 输入契约

顶层是闭集对象，字段如下：

- `session_schema_version`
- `case_id`
- `as_of_date`
- `session_id`
- `blind_input`
- `draft`
- `verifications`
- `suggestions`
- `impact_adjudications`
- `fundamental_adjudication`
- `daiyun_end`
- `career_candidates`（可选；省略表示不触发投影，显式数组表示触发投影）
- `wealth_bindings`（可选；省略表示不触发投影，显式数组表示触发投影）
- `archive`

`archive` 为闭集对象：

- `archive_root`
- `artifact_id`
- `verified_at`
- `verifier`
- `verification_basis`

所有日期必须为严格 `YYYY-MM-DD`；`verified_at` 必须为带显式 UTC offset 的 RFC 3339；数组在进入既有 API 前转换为 tuple。

### 4.1 freeze hash 占位符

`verifications[*].freeze_package_sha256`、`suggestions[*].freeze_package_sha256`、`impact_adjudications[*].freeze_package_sha256` 与 `fundamental_adjudication.freeze_package_sha256` 必须显式存在。允许的唯一值为：

- 真实 64 位小写 SHA-256；或
- 字面量 `$computed`。

工具先以同一 JSON 中的 identity、`blind_input` 和 `draft` 构造与 runner 完全相同的冻结包并计算摘要，再将 `$computed` 替换为该摘要。若输入提供真实摘要，则保持原值并由既有引擎执行 hash 校验。该约定不削弱任何既有校验，也不要求调用者复制易漂移摘要。

## 5. 反序列化边界

工具必须：

1. 使用 `blind_chart_input_from_mapping()` 构造 `BlindChartInput`。
2. 使用 `evaluate_event_candidate()` 构造每个冻结候选；禁止直接伪造已通过候选门的 `LifeEventCandidate`。
3. 使用既有 dataclass/enum 构造 draft、建议、裁决、未来候选和财富绑定。
4. 使用 `verification_input_from_mapping()` 构造核验输入。
5. 对工具自有 mapping 执行闭字段、缺字段、精确类型和枚举校验。
6. 不导入 `engine.pipeline`、`engine.v5.runner`、`engine.v5.preprod`、`tools.render_report`、`tools.feedback*`、`engine.asof.natal_capacity`、`engine.asof.structural_track` 或 `engine.asof.daiyun_context`。

`EvidenceRef` 与 `SourceCitation` 仅作为既有候选 API 所需的显式证据对象；每项 source/locator/excerpt/line 必须来自 fixture，第二案例 fixture 中每个事实都能回指正式 case 文本。

## 6. 调用与归档契约

公开 callable：

`run_and_archive_session(input_path, *, archive_root=None)`

行为：

1. 从磁盘读取 UTF-8 JSON。
2. 构造领域对象和冻结摘要绑定。
3. **恰好一次**调用 `run_career_session()`。
4. **恰好一次**调用 `archive_asof_state()`。
5. 读回 `ArchiveResult.target`，用既有 archive artifact 约束校验字段、payload digest 和 artifact identity。
6. 返回包含 `session_result`、`archive_result` 与读回 artifact 的不可变结果对象。

`archive_root` callable 参数若提供，仅覆盖 JSON 中的本地归档根目录，便于测试隔离；不改变 artifact 元数据。

## 7. CLI 契约

最小 `argparse` 入口：

```text
python -m tools.as_of_session_cli INPUT_JSON [--archive-root PATH]
```

成功：

- 返回码 `0`；
- stdout 输出单行结构化 JSON，至少包含 `status`、`archive_path`、`artifact_id`、`payload_digest`、`case_id`、`as_of_date`、`session_state`、`projection_created`。

失败：

- 返回非零；
- stderr 输出单行结构化 JSON，至少包含 `status=error`、`error_code`、`error_type`、`message`；
- 对带 `.code` 的既有异常原样传播其 code；
- 文件、JSON 与 archive backend 异常映射为稳定工具错误码；
- `main()` 只将异常转成 CLI 返回码，`run_and_archive_session()` 不吞异常。

## 8. 第二案例字段溯源冻结

### 8.1 命盘输入

来源：`cases/C-2026-RF000118-乾-己巳癸酉辛丑己丑/input.md`。

- 乾命与出生信息：第 27–35 行。
- 四柱：第 36–40 行。
- 年支巳藏丙庚戊：第 41–51 行。
- 月支酉藏辛：第 52–55 行。
- 日支丑藏己癸辛：第 56–65 行。
- 时支丑藏己癸辛：第 66–75 行。
- 大运 1–8：第 76–120 行；JSON 将年份边界规范为连续半开式日期段 `1999-01-01`→`2009-01-01` 等，最后一段止于 `2079-01-01`。这是对原文 `1999-2009` 等边界的机械日期表达，不新增事实。
- 十二长生：第 139–144 行。

### 8.2 现实核验

来源：`cases/C-2026-RF000118-乾-己巳癸酉辛丑己丑/feedback.md`。

- 2015 进入银行软件开发中心、编制与待遇提升：第 30 行。
- 2019 工作之余创业，疫情后结束并亏损：第 33 行。
- 2020 四月跳槽华为、工资显著提升且工作强度增加：第 34 行。
- 2021 跳槽华润、工资下降且工作更安逸：第 35 行。
- 2023 跳槽回珠海、工资下降且工作清闲：第 37 行。

fixture 不把 2022 年股票研究、家庭事件或未核验未来信息写入 confirmed 事业成功语义。

## 9. 验收门

### 9.1 专项测试

新增测试至少证明：

1. 第二案例 JSON 可走完整 runner→archive 链，归档为 `CREATED`，读回 artifact 合法。
2. 相同输入与目标可得到既有 `UNCHANGED` 幂等语义。
3. 成功链的 confirmed IDs 只来自明确反馈，未核验/未纳入信息不污染 verified success semantics。
4. 删除必填顶层字段时，CLI 返回非零且 stderr 给出结构化稳定 error code。
5. 新工具 AST 不含禁用生产导入。
6. 新案例从未出现在 Unit8/9/10 测试文件中。
7. 工具确实调用既有 `run_career_session()` 与 `archive_asof_state()`，不定义新 artifact 格式。

### 9.2 回归与隔离

必须新鲜执行：

- `pytest tests/asof/test_unit11_second_case_session_productization.py -q`
- `pytest tests/asof/ -q`
- 仓库既有 production isolation 测试（按实际文件定位执行）

### 9.3 既有测试 SHA 保护

实施前后分别计算全部既有 `tests/asof/test_*.py`（排除新增 Unit11 文件）的 SHA-256 清单；验收要求 `changed=0`。报告记录命令、计数和摘要证据。

## 10. 静态复核与冻结判定

fresh static review 必须覆盖：闭字段、日期/枚举、摘要绑定、候选门、可选投影的 None/空数组语义、wealth binding 顺序、错误传播、路径覆盖、读回验证、禁用导入和手动旁路声明。

最终报告只能给出以下结论之一：

- `PASS / COMPLETE — EVIDENCE-BOUNDED FREEZE`
- `PARTIAL / BLOCKED`
- `FAIL`

只有专项、全量、隔离、SHA 保护、artifact 读回和静态边界均有新鲜证据时，才允许第一种结论。

## 11. 禁止事项

- 不修改既有 as-of 行为或签名。
- 不修改既有测试。
- 不切换生产默认入口。
- 不使用网络、外部服务、Git 写操作或 GitHub mutation。
- 不从真实反馈反向补造命盘结构或候选证据。
- 不将 2026-07-27 之前的旧 as-of 状态描述当作当前事实。

# 六源三领域分析引擎实施计划

**目标：** 基于已批准设计，交付命理师可直接调用的六源并行事业、财富、婚姻分析引擎；由已校正公历出生时间自动排盘，生成可审计 JSON run snapshot 与单份 Markdown 报告，并提供中文交互式和完整非交互式 CLI。

**范围与风险：** 本任务横跨 v5 学校契约、排盘适配、18 个领域切片、三段式仲裁、快照、报告与 CLI，必须分阶段保持契约一致。首期不建设 HTTP API，不做真太阳时或时区校正，不扩展其他领域，不新建 `DomainClaim`，不把自由语料摘要当作生产命题，不将双轨置信度表述为现实准确率。

**架构/顺序：** 先扩展六源学校契约并建立不可变 `(school, domain)` 切片注册表；再建立统一请求、排盘上下文与编排器；其后接通快照、报告和 CLI 端到端骨架；随后按事业、财富、婚姻依次把显式 abstain 槽位替换为可执行切片；最后通过专项测试、全量回归、输出 lint 和真实命盘 dry-run 收口。所有切片继续产出 `V5Claim`，统一交给现有结构图、三段式仲裁和预测账本处理。

**已确认决策：** 第六源统一使用 `ren_fuhong` 作为 v5 school ID；旧任务级 runner 中的 `ren` 仅作为兼容内部 ID，不进入新领域切片公开契约。领域内部使用英文稳定 ID `career`、`wealth`、`marriage`，进入 `V5Claim.domain` 和报告时映射为事业、财富、婚姻。

## 任务 1：六源与领域切片基础契约（P1）

- **文件：** 修改 `engine/v5/domain.py`、`tests/v5/test_v5_contracts.py`；新增 `engine/v5/domain_slices/__init__.py`、`engine/v5/domain_slices/contract.py`、`engine/v5/domain_slices/registry.py`、`tests/v5/test_domain_slice_contract.py`。
- **边界：** 扩展 `V5School`、`V5_SCHOOLS`、`V5_SCHOOL_ROLES` 加入 `ren_fuhong`；不得破坏既有 `V5Claim` JSON 往返。定义三领域、三种槽位状态、统一请求、排盘上下文、切片结果和 audit 数据；切片函数仅返回现有 `V5Claim`。
- **实现：** 请求验证乾/坤、无时区出生时间、`as_of_date`、非空合法领域和输出目录。上下文保存原始输入、四柱、完整大运、当前大运、未来三年干支、排盘器标识。注册表构造后不可变，拒绝重复注册并强制 18 槽位完整；每个槽位明确为 `implemented`、`abstain` 或 `unsupported`。
- **验证：** 先写契约测试，运行 `pytest tests/v5/test_v5_contracts.py tests/v5/test_domain_slice_contract.py -q`。
- **完成：** 六学校枚举和 18 槽位能稳定序列化、顺序确定、重复或缺槽失败关闭；任付红可合法创建 timing claim。

## 任务 2：排盘上下文与端到端编排骨架（P1）

- **文件：** 新增 `engine/v5/domain_slices/context.py`、`engine/v5/domain_slices/orchestrator.py`、`tests/v5/test_domain_analysis_orchestrator.py`；按需小幅修改 `engine/v5/runner.py`。
- **边界：** 复用 `engine.asof.birth_to_bazi.calc_bazi()`、`build_structure_graph()`、`arbitrate_claims()`、`build_prediction_ledger()` 和 `V5RunSnapshot`。不得让旧串行内部引擎取得全局编排权。学校调用顺序不得影响结果。
- **实现：** 将乾/坤映射为排盘器 M/F；从 `start_year` 区间确定 `as_of_date` 所在当前大运，无法确定则硬失败；计算从截止年起未来三年干支并形成 canonical chart。按领域和固定学校集合执行切片；单切片异常降级为带 audit 的 abstain；unsupported 不生成反对命题；全 abstain 领域生成固定“证据不足”仲裁结果。最终构建 `V5Output`/`V5RunSnapshot`，在 `canonical_input` 或结构化 metadata 中保存切片覆盖、状态和异常审计。
- **验证：** 运行 `pytest tests/v5/test_domain_analysis_orchestrator.py -q`，覆盖确定性、调用顺序不变、单切片异常、全 abstain、unsupported、timing 不抬高结构置信度、当前大运缺失硬失败。
- **完成：** 任意合法输入都能经过 18 个显式槽位形成确定性、可校验的 run snapshot；P1 仍明确不满足 production-ready。

## 任务 3：CLI、快照与 Markdown 报告骨架（P1）

- **文件：** 新增 `engine/v5/domain_analysis_report.py`、`tools/domain_analysis_cli.py`、`tests/v5/test_domain_analysis_report.py`、`tests/tools/test_domain_analysis_cli.py`；修改 `tools/README.md` 时仅登记为骨架/未就绪入口。
- **边界：** CLI 只做输入、交互和文件适配；业务逻辑留在 `engine/`。非交互模式缺参立即失败且不读 stdin；交互模式与参数模式必须构造同一个请求对象。输出目录必须解析到仓库允许范围内并防止路径穿越。
- **实现：** 无参数启动中文向导，逐项重试并在排盘摘要后确认；`analyze` 输出 `.run.json` 和 `.md`；`audit` 只读验证 schema、output hash、18 槽位覆盖、证据完整性和报告 hash 绑定。报告只呈现命盘、当前大运、未来三年、三个领域的融合结论、双轨置信度、六派摘要、冲突、少数意见、应期与风险提示，不泄露内部 ID。
- **验证：** 运行 `pytest tests/v5/test_domain_analysis_report.py tests/tools/test_domain_analysis_cli.py -q`；固定输入检查 JSON/Markdown 可追溯、取消不落盘、错误重试、非交互缺参、内部 token 禁显和报告绑定。
- **完成：** P1 端到端命令可用，所有领域显示显式 abstain/证据不足，且入口清楚标识为骨架而非 production-ready。

## 任务 4：事业域六源可执行切片（P2）

- **文件：** 新增 `engine/v5/domain_slices/career/__init__.py` 及按学校组织的切片模块；新增 `tests/v5/domain_slices/test_career_slices.py`；必要时从 `engine/v5/ziping_runner.py`、`engine/v5/ditiansui_runner.py`、`engine/v5/gao_runner.py`、`engine/v5/duan_runner.py`、`engine/v5/yang_runner.py`、`engine/v5/ren_runner.py` 提取无副作用公共能力。
- **边界：** 每派只依据本派结构化理论索引、production rules、确定性谓词和既有内部引擎产出；不得复制整段语料或凭模板补结论。任付红只提供当前大运/未来三年 timing claim，不参与结构合法性加权。
- **实现：** 子平与滴天髓提供结构/气势命题；高德臣提供工作转化与事件命题；段建业提供事业事件框架；杨清娟提供事业画像或在证据不足时 abstain；任付红提供可证伪时间窗。每个命题包含稳定 ID、规则/理论证据、反证口径、分账置信度和适用时间。
- **验证：** 每切片至少覆盖正向命中、反例不命中、缺数据 abstain、来源引用；另测六派融合、当前大运、未来三年和学校顺序不变。运行 `pytest tests/v5/domain_slices/test_career_slices.py tests/v5/test_domain_analysis_orchestrator.py -q`。
- **完成：** 事业域至少两个可执行来源且 lead school 可用，满足该领域 production-ready 的代码与测试门禁。

## 任务 5：财富与婚姻十二个可执行切片（P3）

- **文件：** 新增 `engine/v5/domain_slices/wealth/`、`engine/v5/domain_slices/marriage/` 下学校切片；新增 `tests/v5/domain_slices/test_wealth_slices.py`、`tests/v5/domain_slices/test_marriage_slices.py`；按需复用现有盲派与应期模块。
- **边界：** 财富与婚姻共享同一契约、注册表和仲裁，不创建领域专用 claim 类型。婚姻高风险断语必须保留少数意见和证伪口径；财富损失类结论不得从单一 timing 触发推导为原局定论。
- **实现：** 分别将六源的结构、事件、画像和应期能力接入；证据不足的学校保持显式 abstain，而不是为了凑齐六派生成低质量 claim。报告逐年区分当前大运背景和未来三年触发。
- **验证：** 每个切片四类基础测试，加上财富风险、婚姻冲突、全 abstain、timing 隔离和跨领域不串线测试。运行 `pytest tests/v5/domain_slices/test_wealth_slices.py tests/v5/domain_slices/test_marriage_slices.py -q`。
- **完成：** 财富和婚姻各至少两个可执行来源、lead school 可用，三个领域均满足 production-ready 代码门禁。

## 任务 6：生产收口与推荐入口（P4）

- **文件：** 修改 `tools/README.md`、`engine/README.md`、`engine/contracts/00-OVERVIEW.md`、`META/project-state.json`；按需扩展 `tools/output_linter.py` 或增加领域报告专用 lint 入口；生成三个临时 dry-run 产物但不提交用户案例数据。
- **边界：** 只有全部专项测试、全量回归、输出 lint 和三个真实命盘 dry-run 均通过后，才把 CLI 标记为命理师推荐入口。产品版本仍以 `VERSION` 为唯一事实源，项目状态只写入 `META/project-state.json`。
- **实现：** 文档登记交互/非交互/audit 命令和置信度语义；状态文件记录三个领域门禁结果，不手写易漂移规则数量；dry-run 覆盖乾、坤、节气或子时边界，并检查报告无内部 ID、无“准确率”误称、无全 abstain 补造结论。
- **验证：** 运行领域专项测试、`pytest tests/ -q`、相关 output linter、`python tools/tool_registry.py --check`、`python tools/rule_status_scan.py --check` 和三个 CLI dry-run；最终完成声明前应用 verification-before-completion 证据门禁。
- **完成：** 三领域均满足设计中的 production-ready 门禁，CLI 成为文档推荐入口，JSON 快照和 Markdown 报告可审计且回归通过。

## 风险与回退

- 扩展 `V5_SCHOOLS` 会改变既有默认 abstain 数量和快照 hash；必须同步更新精确断言测试，不能通过兼容别名隐藏变化。若既有五派流程出现回归，回退新增学校的默认全局注入，仅在领域编排器显式传入六源，直至兼容测试修复。
- `calc_bazi()` 的大运只有 `start_year`，当前大运区间需由相邻起年推导；边界语义必须用测试冻结。若无法可靠判定，按设计硬失败，不猜当前大运。
- 现有任务级 runner 使用 `ren`、`gao`、`duan`、`yang`，v5 公开契约使用全名；适配只允许发生在切片内部，禁止污染 snapshot 的 school ID。
- 现有 `engine/v5/runner.py` 较大，领域实现不得继续堆入该文件；仅抽取必要公共函数或通过小型适配器调用，避免扩大串行耦合。
- P1 的 18 个 abstain 槽位只验证链路。若后续切片尚未满足来源和证据门禁，保持该领域未就绪，不通过降低门槛强行发布。

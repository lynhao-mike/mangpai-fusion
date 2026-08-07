# 六源三领域命理分析引擎设计

日期：2026-07-31  
状态：已批准，待实施

## 1. 目标与范围

首期建设面向命理师直接调用的生产分析引擎，覆盖三个高频领域：

- 事业
- 财富
- 婚姻

采用六源并行：

- 子平
- 滴天髓
- 高德臣
- 段建业
- 杨清娟
- 任付红

每个流派在每个领域可以输出命题，也可以显式 abstain。分析时间范围为原局、当前大运和从 `as_of_date` 起未来三个公历流年。应期证据不足时必须 abstain，不得用模板补结论。

首期交付命理师可操作的中文交互式 CLI、非交互式 CLI 和单份 Markdown 报告，暂不建设 HTTP API。

## 2. 输入契约与排盘

命理师只需提供：

- 性别：乾或坤
- 已校正的公历出生年月日时分
- 分析截止日 `as_of_date`
- 待分析领域；默认事业、财富、婚姻
- 输出目录

系统调用现有 `engine.asof.birth_to_bazi.calc_bazi()` 自动生成四柱、起运信息和大运序列。出生时间按命理师已校正的本地民用时间处理，首期不做真太阳时校正或时区换算。

交互模式执行：

```text
python -m tools.domain_analysis_cli
```

中文向导依次提示性别、出生时间、分析截止日、领域和输出目录；逐项校验，错误时原地重试。生成前显示排盘摘要并要求确认。

非交互模式执行：

```text
python -m tools.domain_analysis_cli analyze \
  --gender 乾 \
  --birth "1990-01-01 12:30" \
  --as-of-date 2026-07-31 \
  --domains career wealth marriage \
  --out reports/domain-analysis \
  --non-interactive
```

非交互模式缺少任何必填参数时立即失败，不得等待标准输入。交互层与参数层必须构造同一个请求对象，不能维护两套执行逻辑。

JSON run snapshot 必须记录原始出生输入、排盘引擎标识、派生命盘、分析截止日和领域选择。

## 3. 核心架构

不新建平行的 `DomainClaim` 契约，直接复用：

- `engine.v5.domain.V5Claim`
- `engine.v5.domain.V5ArbitrationResult`
- `engine.v5.domain.V5RunSnapshot`
- `engine.v5.domain.V5Confidence`

新增领域切片注册层，按 `(school, domain)` 注册切片。首期能力矩阵为六个流派乘三个领域，共十八个切片槽位。每个槽位必须具有明确状态：

- `implemented`
- `abstain`
- `unsupported`

建议目录：

```text
engine/v5/domain_slices/
  __init__.py
  contract.py
  registry.py
  orchestrator.py
  career/
  wealth/
  marriage/
```

切片目录放在 `engine/v5/` 下，避免与现有 `engine/domain/` 的并行专家和权重职责混淆。

每个切片消费同一种领域分析上下文，产出零到多条 `V5Claim`。切片只能依据：

- 对应流派的结构化理论索引
- 已提升的 production rules
- 可审计的确定性谓词
- 现有流派内部引擎能力

禁止把整段语料交给生成模型自由发挥并直接形成生产命题。

任付红作为第六来源纳入学校契约和注册表，但主要产出 timing claim。任付红的应期证据不能反向证明或提高原局结构命题的置信度。

现有模块作为切片内部能力复用：

- `engine/energy/`
- `engine/picture/`
- `engine/yingqi/`
- `engine/pangzheng/`
- `engine/predicates/`

这些模块不再取得全局串行编排权。

## 4. 数据流

```text
性别 + 公历出生年月日时分 + as_of_date
  → 输入校验
  → calc_bazi 排盘
  → canonical chart + 当前大运 + 未来三年
  → (school, domain) 切片注册表
  → 十八个独立切片
  → V5Claim / abstain / unsupported
  → V5StructureGraph
  → 三段式仲裁
      1. structure_legality
      2. event_realization
      3. probability_timing
  → V5PredictionLedger
  → V5RunSnapshot JSON
  → 命理师 Markdown 报告
```

编排器按领域调用六源切片。学校顺序不得影响最终仲裁结果。少数意见、冲突和 abstain 必须保留在结构化 run 中。

## 5. 置信度语义

继续使用 `V5Confidence` 的双轨表示：星级加百分比。

百分比表示规则后验、证据完整度和跨派支持的合成值，不表示现实准确率，也不自动等同于事件发生概率。正式报告不额外插入大段“未经验证”声明，但禁止使用以下表述：

- 准确率为 X%
- 事件必然发生
- 置信度等于历史准确率

结构命题和应期命题分别计算置信度。timing claim 不得抬高 structure claim 的置信度。

只有命中可执行规则且证据引用完整的 claim 才能进入仲裁。纯语料摘要只能作为解释性附录，不参与置信度计算。

## 6. 错误与降级策略

以下情况是 run 级硬失败，不生成正式报告：

- 性别非法
- 出生日期时间非法
- 分析截止日非法
- 排盘失败
- 四柱缺失或非法
- 无法确定当前大运
- 输出路径不可安全创建

单个切片异常只将对应 `(school, domain)` 降级为 abstain，并在 run audit 中记录异常类型和切片身份，不允许静默吞错。

同一领域六源全部 abstain 时，领域结论固定为“证据不足”，不得用语料摘要或报告模板补造倾向。

若切片状态为 unsupported，报告只显示该流派在该领域未提供有效判断，不把 unsupported 当作反对证据。

## 7. Markdown 报告

报告为单份命理师内部报告，至少包括：

1. 性别、出生时间、四柱、分析截止日
2. 当前大运和未来三个流年
3. 事业分析
4. 财富分析
5. 婚姻分析
6. 三领域综合风险提示

每个领域显示：

- 融合判断
- 双轨置信度
- 六派依据摘要
- 冲突与少数意见
- 当前大运判断
- 未来三年逐年判断
- 应期 abstain
- 风险提示

Markdown 中禁止显示内部 claim ID、statement ID、runner trace 和规则索引。这些只进入 JSON run snapshot。报告证据可显示流派名、理论出处名称和可读摘录。

## 8. CLI

首期提供：

- 默认无参数中文交互向导
- `analyze`：生成 JSON run snapshot 和 Markdown 报告
- `audit`：只读检查既有 run 的 schema、证据完整性、切片覆盖和报告绑定

默认分析事业、财富、婚姻三个领域。`--domains` 可选择子集。

CLI 仅负责输入、文件适配和用户交互；排盘、切片编排、仲裁和报告视图位于 `engine/`，不得把领域业务逻辑写入 `tools/`。

## 9. 测试策略

### 9.1 排盘与输入测试

覆盖：

- 合法男女输入
- 非法性别
- 非法日期
- 闰日
- 节气边界
- 23:00 子时边界
- 男女顺逆运
- 相同输入的确定性排盘
- 非交互模式缺参立即失败
- 交互模式确认、取消和错误重试

边界时间不由 CLI 擅自改盘，只记录输入和排盘结果。

### 9.2 契约测试

覆盖：

- 六学校枚举
- 三领域枚举
- 十八槽位完整性
- claim、evidence、abstain 和 unsupported
- 稳定 ID
- JSON 序列化往返
- run snapshot hash 确定性

### 9.3 切片测试

每个切片至少覆盖：

- 正向命中
- 反例不命中
- 缺数据 abstain
- 理论和规则来源引用

测试验证的是“语料→结构化规则→谓词→命题”的实现一致性，不宣称验证命理理论的现实真伪。

### 9.4 仲裁性质测试

覆盖：

- 学校调用顺序不影响结果
- timing 不抬高 structure 置信度
- 冲突保留少数意见
- unsupported 不作为反对票
- 六源全 abstain 不造结论
- 缺证据 claim 不进入仲裁

### 9.5 CLI 与报告快照测试

固定命盘覆盖：

- 原局
- 当前大运
- 未来三年
- JSON 与 Markdown 可追溯
- Markdown 不泄露内部 ID
- 报告与 run snapshot hash 绑定
- 输出 linter

## 10. 实施分期

### P1：统一骨架

完成：

- 六源学校契约扩展
- 领域分析请求和上下文
- 十八槽位注册表
- 编排器
- 中文交互式与非交互式 CLI
- JSON run snapshot
- Markdown 报告骨架
- 十八个显式 abstain 切片

P1 只证明接口和端到端链路，不能作为正式分析能力。

### P2：事业域

完成六个事业切片，从各自语料和现有引擎中提升可执行命题，并完成事业域仲裁、当前大运和未来三年输出。

### P3：财富与婚姻域

分别完成六个财富切片和六个婚姻切片，复用同一契约、注册表、仲裁和报告视图。

### P4：生产收口

完成：

- 专项和全量回归
- 输出 linter
- 三个真实命盘 dry-run 验收
- 工具索引与契约文档更新
- 将 CLI 标记为命理师推荐入口

## 11. Production-ready 门禁

领域只有同时满足以下条件才可标记为 production-ready：

- 六源中至少两个切片产出可执行 claim
- 该领域 lead school 切片可用
- claim 全部具有规则或理论来源引用
- 结构、事件、应期置信度分账通过测试
- 全 abstain 不造结论
- CLI 和报告快照测试通过
- 输出 linter 通过

P1 的显式 abstain 占位切片不满足 production-ready 门禁。

## 12. 首期非目标

- HTTP API
- 真太阳时和时区校正
- 未知时辰的十二时辰并行分析
- 事业、财富、婚姻之外的领域
- 通用 YAML 规则 DSL
- 使用生成模型自由解释整段语料并直接输出生产命题
- 自动宣称现实准确率
- 自动修改理论库、权重或生产规则

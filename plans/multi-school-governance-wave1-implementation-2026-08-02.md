# 五派共同治理 Wave 1 实施前契约与详细实施计划

- 日期：2026-08-02
- 状态：待实施批准
- 上位设计：[`multi-school-governance-design-2026-08-02.md`](multi-school-governance-design-2026-08-02.md)
- 本文件权限：仅规划，不授权实现、提交、发布或生产切换
- 后续波次：Wave 2、Wave 3 只引用上位设计中的进入门、退出门和边界，不在本文展开函数级计划

> 路由：完整计划——存在跨模块接口、公共事实契约、仲裁语义和兼容性风险，必须先冻结 Wave 1 实施契约。

## 1. 实施前契约

### 1.1 目标

Wave 1 交付一个可并行于现有生产链运行的治理骨架，使后续垂直切片能够依赖以下稳定能力：

1. 不可变、可内容寻址的 L0/L1/L2A/L2B 事实快照；
2. 五派只读注册与任务级资格边界；
3. 不破坏现有 claim DTO 的新公共治理 claim 信封；
4. 严格有序的七步仲裁、同源折叠及完整性 fail-closed；
5. 仅允许注册模板的受限组合；
6. 新路径上的封闭 trigger 注册与显式流年语义；
7. 独立于旧三结构枚举的 30 格局冻结目录及兼容映射；
8. 旧 API、现有切片和生产规则加载行为不回归。

### 1.2 阻塞问题

无。按以下保守默认值规划：

- 新治理路径先以 shadow/staged 方式运行，不替换现有生产 orchestrator；
- 现有两个 claim 公共模型保持字段和语义不变；
- 滴天髓保留在旧路由和现有生产规则兼容层，不自动成为第六个同级 School View；
- 未注册学校、任务、claim 类型、能力版本、事实认证、组合模板或 trigger 一律弃权、拒绝或转完整性错误，不回退为均匀权重；
- Wave 1 不修改报告、反馈、学习写入或生产发布流程。

如果实施中发现必须违反任一默认值，立即停止对应任务并回到用户批准门，不以“兼容修复”为由扩大范围。

### 1.3 权威事实与依赖顺序

实施时依次服从：

1. [`multi-school-governance-design-2026-08-02.md`](multi-school-governance-design-2026-08-02.md)；
2. 现有公共字段冻结测试 [`test_static_isolation.py`](../tests/yang_marriage/test_static_isolation.py)；
3. 现有架构依赖守卫 [`test_architecture_dependencies.py`](../tests/test_architecture_dependencies.py)；
4. 旧三结构、杨派婚姻、任派应期及 staged arbitration 回归测试；
5. 本计划中的新增契约和测试。

发生冲突时，先保持现有公共接口，再通过新增 DTO、适配器或并行入口满足新设计；不得直接扩大旧 DTO 字段。

### 1.4 模块边界

#### 新增领域模块

建议新增 [`engine/governance/`](../engine/governance/) 包，内部只依赖 Python 标准库及稳定领域类型，不依赖 [`engine/application/`](../engine/application/)、[`engine/infrastructure/`](../engine/infrastructure/) 或 [`tools/`](../tools/)：

| 文件 | 单一职责 |
|---|---|
| [`engine/governance/contracts.py`](../engine/governance/contracts.py) | 事实、时间作用域、治理 claim、仲裁结果等不可变公共契约 |
| [`engine/governance/canonical.py`](../engine/governance/canonical.py) | 有界规范化 JSON、摘要和稳定 ID |
| [`engine/governance/registries.py`](../engine/governance/registries.py) | 事实认证、五派资格、能力角色、组合模板和 trigger 的只读注册表 |
| [`engine/governance/arbitration.py`](../engine/governance/arbitration.py) | 七步门禁、同源折叠、冲突分类和决策态 |
| [`engine/governance/structure_catalog.py`](../engine/governance/structure_catalog.py) | 30 格局目录的严格加载、校验和旧枚举投影 |
| [`engine/governance/__init__.py`](../engine/governance/__init__.py) | 经审查后的最小公共导出面 |

#### 新增应用适配层

建议新增：

| 文件 | 单一职责 |
|---|---|
| [`engine/application/governance_fact_builder.py`](../engine/application/governance_fact_builder.py) | 从现有解析结果构建 L0/L1 快照，不引入派别结论 |
| [`engine/application/governance_claim_adapters.py`](../engine/application/governance_claim_adapters.py) | 将旧 [`SchoolClaim`](../engine/decision/models.py:115) 与 [`Claim`](../engine/claims/domain.py:68) 显式、可审计地投影到新治理信封 |
| [`engine/application/governance_shadow_runner.py`](../engine/application/governance_shadow_runner.py) | 组合快照、适配器和仲裁器；只返回 shadow 结果，不写报告、不写反馈、不改生产权限 |

#### 新增数据契约

| 文件 | 单一职责 |
|---|---|
| [`theory/ziping/structure-catalog-v1.yaml`](../theory/ziping/structure-catalog-v1.yaml) | 30 格局稳定目录、来源状态、实现状态及旧三结构映射 |
| [`theory/multi-school-governance-v1.yaml`](../theory/multi-school-governance-v1.yaml) | 五派注册、任务资格、能力角色、组合模板和 trigger 发布清单的初始只读快照 |

注册数据可以拆成多个 YAML，但首版优先单文件，只有在审查表明确显示职责或发布周期不同后才拆分。

### 1.5 现有接口的冻结与兼容

以下现有接口不原位扩字段、不改默认语义：

- [`ChartFactLedger`](../engine/decision/models.py:43)；
- [`SchoolClaim`](../engine/decision/models.py:115)；
- [`Claim`](../engine/claims/domain.py:68)；
- [`build_yang_marriage_school_claims()`](../engine/decision/yang_marriage_claims.py:22)；
- [`build_route_plan()`](../engine/decision/l1_school_router.py:339)；
- [`arbitrate_staged()`](../engine/decision/l6_staged_arbitration.py:535)；
- [`rule_triggered()`](../engine/application/production_rule_triggers.py:25)；
- [`run_decision_mvp()`](../engine/decision/orchestrator.py:34)；
- [`TenGodStructureKind`](../engine/predicates/ten_god_structure_types.py:10)。

兼容策略：

1. 新治理契约使用新类型，不修改被静态测试冻结的字段列表；
2. 所有旧→新投影都显式记录来源模型、来源对象 ID、适配器版本和损失项；
3. 无法无损投影的字段不猜测，记录 issue 并输出 `conditional` 或 `abstain`；
4. 旧仲裁继续运行，新仲裁通过 shadow runner 并行运行；
5. 旧生产规则数量、允许专家体系和默认加载行为保持不变；
6. 新治理注册不得被现有 production loader 自动消费。

### 1.6 失败语义

| 条件 | 新路径行为 |
|---|---|
| 同一事实身份存在互斥载荷 | 抛出类型化完整性错误，停止该 arena |
| 事实、规则或认证引用不存在 | claim 不合格；按严重度输出 `abstain` 或完整性错误 |
| 学校/任务/claim 类型未注册 | `abstain`，不得使用均匀权重 |
| 版本不兼容 | `abstain`，记录版本 issue |
| 时间作用域不可比较 | 保留各 claim，输出 `conflict` 或 `conditional`，不互相计权 |
| 未知 trigger | 未激活并记录 closed-domain issue；不得返回真 |
| 未显式提供流年 | 不构建流年事实，不运行流年 trigger |
| 未注册组合模板 | 不组合；输出 `conflict` 或 `human_review` |
| 某 School View 运行失败 | 标记该派 unavailable，保留其他派结果 |
| claim 顺序变化 | 输出集合和摘要保持一致 |

### 1.7 非目标

Wave 1 明确不做：

- 不实现 30 个格局求值器；
- 不改造现有报告和反馈展示；
- 不自动发布学校角色、规则、事实认证或组合模板；
- 不迁移全部 V5 claim；
- 不删除旧 claim、旧 L6 或旧 production rule loader；
- 不把 [`evaluate_trigger()`](../engine/predicates/condition_evaluator.py:129) 的未知 trigger 放行语义改成全仓库行为变化；新路径绕开该入口；
- 不从历史标签或 known facts 构建事实、claim 或路由；
- 不声称合成测试或历史回放证明真实前瞻准确率。

### 1.8 完成定义

只有同时满足以下条件，Wave 1 才可标记完成：

1. 上位设计第 15.1 节八项退出门全部有新鲜证据；
2. 新增契约、注册表、仲裁和目录测试全部通过；
3. 新治理路径的未知 trigger、缺失年份和未注册能力均 fail closed；
4. 旧公共字段冻结测试保持通过；
5. 旧 staged arbitration、三结构、杨婚姻、任应期和 production loader 回归通过；
6. 全量 [`pytest`](../pyproject.toml) 通过，或所有失败均被证明为修改前已存在且与本波次无关；
7. 未修改报告、反馈、学习写入和生产发布入口；
8. 形成验证记录，列出命令、时间、退出码、测试数量和失败详情；
9. 未经另行批准，不进入 Wave 2 实现或 Wave 3 函数级规划。

## 2. 关键契约草案

本节冻结实现意图，不要求字段名逐字照抄；任何语义变化须重新批准。

### 2.1 事实契约

建议类型：

```python
FactLevel = Literal[
    "canonical_observation",
    "candidate_derived",
    "certified_technical",
    "certified_cross_school",
]
TemporalLayer = Literal["natal", "dayun", "liunian"]
```

建议不可变对象：

```python
@dataclass(frozen=True, slots=True)
class GovernanceFact:
    fact_id: str
    fact_kind: str
    fact_level: FactLevel
    temporal_scope: TemporalScope
    source_positions: tuple[str, ...]
    input_refs: tuple[str, ...]
    calculator_id: str
    calculator_version: str
    payload: FrozenJson
    content_digest: DigestRef
```

```python
@dataclass(frozen=True, slots=True)
class FactSnapshot:
    snapshot_id: str
    schema_version: str
    case_id: str
    facts: tuple[GovernanceFact, ...]
    input_digest: DigestRef
    content_digest: DigestRef
```

硬约束：

- 深层不可变，禁止 frozen dataclass 内嵌可变 list/dict；
- `fact_id` 由身份字段生成，不含派别观点和易变展示文本；
- `content_digest` 覆盖完整规范载荷；
- 输入顺序不影响快照摘要；
- natal、dayun、liunian 不能隐式互换；
- 只有显式年份才能产生 liunian 事实。

规范化和摘要优先复用 [`bounded_jcs_sha256()`](../engine/f09/canonical_json.py) 的设计与实现；若直接依赖会导致包边界过重，则提取最小无副作用公共 primitive，而不是再造不兼容 JSON 规范。

### 2.2 治理 claim 信封

建议新增 [`GovernanceClaim`](../engine/governance/contracts.py)，不替代两个旧 claim：

```python
ClaimKind = Literal["structure", "event", "timing", "support", "risk"]
ClaimStance = Literal["support", "oppose", "conditional", "abstain"]
```

字段至少覆盖上位设计第 7 节，并额外包含：

- `schema_version`；
- `source_claim_refs`；
- `adapter_id` / `adapter_version`；
- `independence_keys` 或可确定生成这些键的来源摘要；
- `issues`；
- `content_digest`。

适配器不得把旧 `metadata` 中不存在的语义伪装成认证事实。适配规则必须逐字段列出：无损、默认、降级或不可表达。

### 2.3 学校与能力注册

五个治理 School View 的 canonical ID 固定为：

```text
ziping
gao_dechen
duan_jianye
yang_qingjuan
ren_fuhong
```

别名只允许在输入边界归一化，例如 `gao`→`gao_dechen`；规范对象、摘要和仲裁只保存 canonical ID。

`ditiansui` 在 Wave 1 的状态：

```text
legacy_compatibility_source
```

它继续存在于 [`_DEFAULT_SCHOOLS`](../engine/decision/l1_school_router.py:19) 和现有生产规则路径，但不写入五派 peer registry，也不参与新仲裁 arena。未来若要升级，必须单独进行权威设计审批。

能力身份固定绑定：

```text
school × task × claim_kind × evidence_grade × version
```

缺任一维度时不可比较，不回退为全局学校权重。

### 2.4 七步仲裁结果

建议输出同时保留每一步的审计结果：

```python
@dataclass(frozen=True, slots=True)
class GateResult:
    gate: Literal[
        "qualification",
        "temporal",
        "evidence",
        "independence",
        "counterevidence",
        "applicability",
        "decision",
    ]
    status: Literal["passed", "conditional", "failed", "not_applicable"]
    claim_refs: tuple[str, ...]
    issue_codes: tuple[str, ...]
```

```python
DecisionState = Literal[
    "consensus",
    "complementary",
    "conflict",
    "conditional",
    "abstain",
    "human_review",
]
```

仲裁结果必须保留：

- 输入 claim refs；
- 折叠后的独立证据组；
- 少数 claim 和反证；
- 使用的能力角色快照；
- 使用的组合模板 ID/版本；
- 七步 gate trace；
- 决策态、理由代码和摘要。

### 2.5 同源折叠

独立性分组键至少由以下规范摘要构成：

```text
public fact refs
+ certified fact refs
+ source rule refs
+ source theory refs
+ derivation chain digest
```

折叠只消除重复独立票，不删除任何 claim。组内 claim 继续出现在审计轨迹和反证列表中。

### 2.6 受限组合

组合模板注册必须声明：

- 模板 ID 和版本；
- 可接受的组件 claim kinds、stances、tasks 和 temporal scopes；
- 输出 claim kind；
- 输出事件范围规则；
- 输出时间范围规则；
- evidence grade 上界；
- 必须保留的反证和 falsifier；
- human-review 条件。

组合函数不得接受任意回调或自然语言表达式。Wave 1 只需提供 registry、校验器和一个纯合成测试模板，不发布真实命理生产组合。

### 2.7 trigger 注册

新 trigger 必须为封闭 ID，并映射到无副作用、输入类型明确的 evaluator。注册内容至少包括：

- trigger ID；
- evaluator ID/version；
- 必需事实 kinds；
- 允许的 temporal layers；
- 缺失输入行为；
- 发布状态。

未知 trigger 返回未激活并产生 issue。`liunian` evaluator 必须验证显式 target year 事实存在，不能仅检查“解析对象非空”。

## 3. 详细实施任务

实施采用测试驱动顺序。每个任务完成后先运行窄测试，再进入下一任务；不得先批量写完源码再补测试。

### Task 0：建立 Wave 1 变更护栏和基线证据

**修改文件**

- 新增 [`tests/governance/test_wave1_baseline_contract.py`](../tests/governance/test_wave1_baseline_contract.py)
- 新增 [`tests/governance/__init__.py`](../tests/governance/__init__.py)

**步骤**

1. 写测试固定现有 [`SchoolClaim`](../engine/decision/models.py:115) 和 [`Claim`](../engine/claims/domain.py:68) 字段，避免 Wave 1 绕过杨婚姻静态隔离测试。
2. 写测试确认旧 [`TenGodStructureKind`](../engine/predicates/ten_god_structure_types.py:10) 仍只有当前三个值。
3. 写测试确认旧默认 production library 的专家体系和数量仍由现有测试负责，不在新治理注册中隐式扩展。
4. 写测试确认新 [`engine/governance/`](../engine/governance/) 包不被旧 orchestrator、报告和反馈模块导入。
5. 运行现有窄基线，保存测试数量和退出码。

**验证命令**

```bat
python -m pytest tests/yang_marriage/test_static_isolation.py tests/test_architecture_dependencies.py tests/test_production_rule_loader.py tests/decision/test_staged_arbitration.py tests/predicates/test_ten_god_structures.py tests/ren_timing -q
```

**完成条件**

- 基线通过；若不通过，记录为前置阻塞，不开始 Wave 1 源码变更。

### Task 1：冻结规范化摘要和稳定 ID primitive

**修改文件**

- 新增 [`tests/governance/test_canonical.py`](../tests/governance/test_canonical.py)
- 新增 [`engine/governance/canonical.py`](../engine/governance/canonical.py)
- 新增 [`engine/governance/__init__.py`](../engine/governance/__init__.py)

**先写失败测试**

1. 字典键顺序变化摘要不变；
2. tuple 成员顺序在有序语义下保持敏感；
3. 不支持的对象、NaN、Infinity、循环结构 fail closed；
4. 相同身份材料生成相同稳定 ID；
5. 内容变化改变 digest；
6. ID namespace 不同不会碰撞；
7. 规范输出不依赖本地时区或系统时间。

**实现**

- 优先薄封装现有 F09 JCS primitive；
- 提供 `canonical_digest()` 和 `stable_object_id()` 两个最小公共函数；
- 不导出任意 JSON 宽松序列化入口。

**验证命令**

```bat
python -m pytest tests/governance/test_canonical.py tests/f09 -q
```

### Task 2：实现深层不可变事实契约

**修改文件**

- 新增 [`tests/governance/test_fact_contracts.py`](../tests/governance/test_fact_contracts.py)
- 新增 [`engine/governance/contracts.py`](../engine/governance/contracts.py)

**先写失败测试**

1. 四个事实等级和三个时间层为封闭枚举；
2. payload 被深层冻结，调用方原始 dict/list 后续变化不影响事实；
3. `fact_id` 身份与 `content_digest` 内容职责分离；
4. 空 calculator version、空 source position、非法年份范围被拒绝；
5. liunian scope 必须含显式 target year；
6. natal scope 不允许伪装 dayun/liunian 字段；
7. 同一 `fact_id` 互斥内容被快照校验器判为完整性冲突；
8. facts 输入顺序变化不改变 snapshot digest；
9. 重复 fact ID 即使载荷相同也被拒绝，避免静默覆盖。

**实现**

- 定义 `TemporalScope`、`GovernanceFact`、`FactSnapshot`、`DigestRef` 复用边界和类型化异常；
- 快照构造统一排序；
- 提供 `validate_fact_snapshot()` 或构造期校验，不提供可变 append API。

**验证命令**

```bat
python -m pytest tests/governance/test_fact_contracts.py -q
```

### Task 3：构建现有命盘到 L0/L1 快照的应用适配器

**修改文件**

- 新增 [`tests/application/test_governance_fact_builder.py`](../tests/application/test_governance_fact_builder.py)
- 新增 [`engine/application/governance_fact_builder.py`](../engine/application/governance_fact_builder.py)

**先写失败测试**

1. 四柱、性别命式、大运区间和明确 target year 被投影为 L0；
2. 缺失 target year 时不存在 liunian 事实；
3. `captured_at` 和系统当前时间不生成流年；
4. 扎根、强度等模型输出只能是 L1，不能标记 L0；
5. 事实 payload 不含 school、结论、confidence 或 role；
6. 同输入同 calculator version 快照完全一致；
7. calculator version 变化保留事实身份策略并改变内容/版本绑定；
8. 大运补全结果不得改写 natal fact。

**实现**

- 从已有解析对象和 [`ChartFactLedger`](../engine/decision/models.py:43) 读取确定字段；
- 先覆盖最小 L0 集，不在此任务构建全部十神关系图；
- L1 仅适配已经有确定算法版本的结果；无法绑定版本的派生结果不进入快照。

**验证命令**

```bat
python -m pytest tests/application/test_governance_fact_builder.py tests/predicates/test_ten_god_structures.py -q
```

### Task 4：实现双认证事实注册表

**修改文件**

- 新增 [`tests/governance/test_fact_certification_registry.py`](../tests/governance/test_fact_certification_registry.py)
- 扩展 [`engine/governance/registries.py`](../engine/governance/registries.py)
- 新增/初始化 [`theory/multi-school-governance-v1.yaml`](../theory/multi-school-governance-v1.yaml)

**先写失败测试**

1. L2A 与 L2B 认证类型严格分离；
2. 注册项绑定 fact kind、calculator ID/version、schema version、发布状态和 digest；
3. candidate/proposed 状态不可作为 certified fact 消费；
4. 运行时 API 只读，不提供 promote/publish 写方法；
5. 重复 ID、重复身份不同内容、未知状态和相对路径逃逸被拒绝；
6. 未注册版本查询返回明确 unsupported，不回退相邻版本；
7. L2B 必须声明跨派审查引用，L2A 不伪造跨派共识。

**实现**

- 只实现加载、校验和查询；
- YAML 初始注册只列已能证明的最小项，其余保持 candidate 或缺席；
- 不自动扫描 theory 文件并视为已认证。

**验证命令**

```bat
python -m pytest tests/governance/test_fact_certification_registry.py -q
```

### Task 5：实现新治理 claim 信封和旧模型适配器

**修改文件**

- 新增 [`tests/governance/test_governance_claim.py`](../tests/governance/test_governance_claim.py)
- 新增 [`tests/application/test_governance_claim_adapters.py`](../tests/application/test_governance_claim_adapters.py)
- 扩展 [`engine/governance/contracts.py`](../engine/governance/contracts.py)
- 新增 [`engine/application/governance_claim_adapters.py`](../engine/application/governance_claim_adapters.py)

**先写失败测试：公共信封**

1. claim kind、stance、evidence grade 为封闭域；
2. `abstain` 必须有 reason issue；
3. 高风险 claim 必须有 counterevidence 或 falsifier；
4. 所有 refs 去重且稳定排序；
5. temporal scope 必填；
6. confidence 范围校验但不与 evidence grade 混合；
7. 引用不存在或版本不兼容时校验失败；
8. claim 输入顺序变化不改变 digest。

**先写失败测试：适配器**

1. 旧 [`SchoolClaim`](../engine/decision/models.py:115) 字段不变化；
2. 旧 [`Claim`](../engine/claims/domain.py:68) 字段不变化；
3. 适配器记录 adapter ID/version 和 source claim ref；
4. 旧 `metadata` 中的 stance/task 只能按显式映射读取；
5. 缺少时间作用域不能被猜为 natal；
6. 无法表达 `conditional`/`abstain` 的旧模型必须生成明确降级 issue；
7. 杨婚姻 pressure/abstention 不被适配器变成 event 支持票；
8. 别名学校 ID 只在边界转为 canonical ID。

**实现**

- 分别提供两个命名清晰的适配函数，不用鸭子类型自动猜模型；
- 返回治理 claim 或类型化 adaptation result，包含 loss/issues；
- 不修改 [`build_yang_marriage_school_claims()`](../engine/decision/yang_marriage_claims.py:22)。

**验证命令**

```bat
python -m pytest tests/governance/test_governance_claim.py tests/application/test_governance_claim_adapters.py tests/yang_marriage/test_static_isolation.py -q
```

### Task 6：实现五派只读注册与任务级能力资格

**修改文件**

- 新增 [`tests/governance/test_school_registry.py`](../tests/governance/test_school_registry.py)
- 扩展 [`engine/governance/registries.py`](../engine/governance/registries.py)
- 扩展 [`theory/multi-school-governance-v1.yaml`](../theory/multi-school-governance-v1.yaml)

**先写失败测试**

1. peer registry 恰好包含五个 canonical IDs；
2. `ditiansui` 查询返回 legacy compatibility 状态，不返回 peer role；
3. `gao`、`duan`、`yang`、`ren` 仅在输入边界归一化；
4. 能力查询必须提供完整五维身份；
5. 未注册能力返回 `abstain`，不回退全局学校权重或 uniform；
6. `evidence_only` 不得成为独立 winner；
7. registry 对调用方只读；
8. 学校注册不包含标签、报告、反馈或学习运行时依赖。

**实现**

- 借鉴 [`CapabilityRegistry.query()`](../engine/decision/capability_registry.py:100) 的只读查询模式；
- 不修改现有 capability snapshot schema；
- 通过显式 bridge 读取已发布的兼容能力项，无法补齐 version/claim kind 时不升级资格。

**验证命令**

```bat
python -m pytest tests/governance/test_school_registry.py tests/test_l1_learned_prior.py tests/decision/test_staged_arbitration.py -q
```

### Task 7：实现七步仲裁和同源证据折叠

**修改文件**

- 新增 [`tests/governance/test_arbitration_gates.py`](../tests/governance/test_arbitration_gates.py)
- 新增 [`tests/governance/test_arbitration_properties.py`](../tests/governance/test_arbitration_properties.py)
- 新增 [`engine/governance/arbitration.py`](../engine/governance/arbitration.py)
- 扩展 [`engine/governance/contracts.py`](../engine/governance/contracts.py)

**先写失败测试：七步顺序**

1. 未通过资格门的 claim 不进入后续权重比较；
2. 时间不兼容 claim 不互相支持或反对；
3. 引用/版本/阻断失败在证据门停止；
4. 同源 claim 被折叠成一个独立组但原 claim 均保留；
5. 强反证不会因支持 claim 数量增加而消失；
6. 未发布能力角色在适用性门弃权；
7. 只输出六种批准的 decision states。

**先写失败测试：性质**

1. claim 排列置换不改变结果和 digest；
2. 重复运行幂等；
3. 重复复制同源 claim 不提高独立证据强度；
4. 事实冲突 fail closed；
5. timing 窗口不平均、不自动取交集；
6. 少数观点和 counterevidence 永远保留；
7. 高风险冲突优先 `conditional`/`human_review`；
8. 空 arena 输出 `abstain`；
9. 不存在从 partial plan 回退 [`ApplicabilityPlan.uniform()`](../engine/decision/l6_staged_arbitration.py:161) 的路径。

**实现**

- 每个 gate 为纯函数，顶层函数固定顺序编排；
- 使用 reason/issue code，不通过自由文本判断冲突；
- 不复用旧 [`_weighted_sides()`](../engine/decision/l6_staged_arbitration.py:367) 的累加作为独立票模型；
- 旧 [`arbitrate_staged()`](../engine/decision/l6_staged_arbitration.py:535) 保持不变。

**验证命令**

```bat
python -m pytest tests/governance/test_arbitration_gates.py tests/governance/test_arbitration_properties.py tests/decision/test_staged_arbitration.py -q
```

### Task 8：实现受限组合模板注册与执行

**修改文件**

- 新增 [`tests/governance/test_composition_registry.py`](../tests/governance/test_composition_registry.py)
- 扩展 [`engine/governance/registries.py`](../engine/governance/registries.py)
- 扩展 [`engine/governance/arbitration.py`](../engine/governance/arbitration.py)
- 扩展 [`theory/multi-school-governance-v1.yaml`](../theory/multi-school-governance-v1.yaml)

**先写失败测试**

1. 未注册模板不能执行；
2. 模板版本不匹配不能执行；
3. 输出 evidence grade 不超过最强组件；
4. 输出 event kind 不扩大；
5. 输出 temporal scope 不扩大；
6. 所有组件、反证和 falsifier 均保留；
7. 组件缺失时输出 `conditional`/`conflict`，不补造 claim；
8. 组合结果可重放且顺序无关；
9. 模板不接受任意 Python callback、自然语言 predicate 或表达式求值。

**实现**

- 首版只实现数据驱动的封闭组合原语；
- 注册一个 synthetic-only 模板用于性质测试，状态不得为 production；
- 中央层只选择和约束组合，不生成新命理谓词。

**验证命令**

```bat
python -m pytest tests/governance/test_composition_registry.py tests/governance/test_arbitration_properties.py -q
```

### Task 9：实现新路径 fail-closed trigger 边界

**修改文件**

- 新增 [`tests/governance/test_trigger_registry.py`](../tests/governance/test_trigger_registry.py)
- 扩展 [`engine/governance/registries.py`](../engine/governance/registries.py)
- 扩展 [`theory/multi-school-governance-v1.yaml`](../theory/multi-school-governance-v1.yaml)

**先写失败测试**

1. 未知 trigger 未激活并产生 issue；
2. candidate/unpublished trigger 不执行；
3. 必需事实缺失时未激活；
4. liunian trigger 在无显式 target year 时未激活；
5. `as_of_date`、系统日期或非空 parsed object 不足以激活 liunian；
6. 自然语言条件不能被当作 evaluator ID；
7. evaluator 只能读取声明的 fact kinds；
8. 相同事实快照的结果确定且无副作用。

**实现**

- 建立封闭 evaluator registry；
- 可薄包装现有类型化 [`rule_triggered()`](../engine/application/production_rule_triggers.py:25) 中已安全的结构判断，但必须通过显式适配，不直接传入自由字符串；
- 不调用未知 trigger 放行的 [`evaluate_trigger()`](../engine/predicates/condition_evaluator.py:129)；
- 不改变旧 production trigger 行为。

**验证命令**

```bat
python -m pytest tests/governance/test_trigger_registry.py tests/test_production_rule_loader.py tests/predicates/test_ten_god_structures.py -q
```

### Task 10：冻结 30 格局目录和旧三结构投影

**修改文件**

- 新增 [`tests/governance/test_structure_catalog.py`](../tests/governance/test_structure_catalog.py)
- 新增 [`engine/governance/structure_catalog.py`](../engine/governance/structure_catalog.py)
- 新增 [`theory/ziping/structure-catalog-v1.yaml`](../theory/ziping/structure-catalog-v1.yaml)

**先写失败测试**

1. 目录恰好 30 个唯一稳定 ID；
2. 中文名、家族、必要角色、候选成立/清格/阻断/破坏类型、来源状态、实现状态字段完整；
3. 所有枚举和状态为封闭域；
4. 旧三结构映射完整且只映射到现有 [`TenGodStructureKind`](../engine/predicates/ten_god_structure_types.py:10)；
5. 未实现目录项不能被误标为 production evaluator；
6. 目录顺序变化不改变 digest；
7. 重命名展示文字不改变 stable structure ID，但属于内容版本变化；
8. 重复 ID、重复 canonical key、未知旧映射和缺来源状态 fail closed；
9. 目录加载不自动注册为公共事实或生产规则。

**实现**

- 目录作为分类与交付状态契约，不包含可执行自然语言；
- 现有三个 evaluator 通过兼容映射标注 current implementation；
- 其余条目明确为 catalog-only/candidate，不暗示已经验证；
- 不修改 [`TenGodStructureKind`](../engine/predicates/ten_god_structure_types.py:10)。

**资料审查门**

目录内容写入前，逐项核对已有 `.omo` 目录证据、子平语料来源和命名；若 30 项名单存在理论歧义，先冻结 stable family key 与 source status，将 disputed 名称标记为 review，而不是自行补齐理论定义。

**验证命令**

```bat
python -m pytest tests/governance/test_structure_catalog.py tests/predicates/test_ten_god_structures.py -q
```

### Task 11：组装 shadow runner 与端到端完整性检查

**修改文件**

- 新增 [`tests/application/test_governance_shadow_runner.py`](../tests/application/test_governance_shadow_runner.py)
- 新增 [`engine/application/governance_shadow_runner.py`](../engine/application/governance_shadow_runner.py)
- 审查后扩展 [`engine/governance/__init__.py`](../engine/governance/__init__.py)

**先写失败测试**

1. runner 接收显式输入、School View 结果和只读注册快照；
2. 构建事实快照、适配 claim、执行七步仲裁并返回可序列化 shadow result；
3. runner 不写文件、不写学习状态、不改 capability registry；
4. runner 不导入报告、反馈、L7–L9 或 production runner；
5. 单派失败时其他派结果保留，该派标记 unavailable；
6. 事实完整性冲突停止 arena；
7. 同输入、同版本输出 digest 一致；
8. 不显式传 target year 时全链不存在 liunian 事实和 timing 激活；
9. `ditiansui` 旧 claim 不进入五派 arena；
10. runner 不改变 [`run_decision_mvp()`](../engine/decision/orchestrator.py:34) 或 V5 默认输出。

**实现**

- runner 只做编排；
- 依赖以参数注入或只读 loader 注入；
- 不加入默认 pipeline registry；
- 结果包含所有版本、digest、gate trace 和 issues。

**验证命令**

```bat
python -m pytest tests/application/test_governance_shadow_runner.py tests/test_decision_mvp.py tests/test_decision_v5_adapter.py -q
```

### Task 12：扩展架构和静态隔离守卫

**修改文件**

- 扩展 [`tests/test_architecture_dependencies.py`](../tests/test_architecture_dependencies.py)
- 新增 [`tests/governance/test_static_isolation.py`](../tests/governance/test_static_isolation.py)

**先写失败测试**

1. governance 领域包不导入 application/infrastructure/tools；
2. governance 包不导入 reports、feedback、learning、V5 runner 或标签路径；
3. shadow runner 不被现有默认 pipeline、报告模板或反馈入口导入；
4. 新 registry YAML 不含历史 case ID、预测标签、样本命中结果或绝对路径；
5. School View adapter 不能写 FactSnapshot；
6. 新代码不读取系统时间决定流年；
7. 旧杨婚姻保护文件和公共字段保持不变。

**验证命令**

```bat
python -m pytest tests/test_architecture_dependencies.py tests/governance/test_static_isolation.py tests/yang_marriage/test_static_isolation.py -q
```

### Task 13：执行分层回归验证

**不新增业务功能。** 只修复由 Wave 1 引入且符合本契约的回归；若修复需要改变冻结接口或扩大范围，停止并请求批准。

**Gate A：治理单元测试**

```bat
python -m pytest tests/governance tests/application/test_governance_fact_builder.py tests/application/test_governance_claim_adapters.py tests/application/test_governance_shadow_runner.py -q
```

**Gate B：核心兼容测试**

```bat
python -m pytest tests/yang_marriage tests/ren_timing tests/decision/test_staged_arbitration.py tests/predicates/test_ten_god_structures.py tests/test_production_rule_loader.py tests/test_decision_mvp.py tests/test_decision_v5_adapter.py -q
```

**Gate C：架构和项目元数据**

```bat
python -m pytest tests/test_architecture_dependencies.py tests/test_project_metadata.py -q
```

**Gate D：全量测试**

```bat
python -m pytest tests/ -q
```

**Gate E：静态质量（仅使用仓库已有工具）**

先查明仓库当前正式 lint/type-check 入口；若 [`tools/README.md`](../tools/README.md) 未登记对应工具，不临时增加依赖。至少运行：

```bat
python tools/tool_registry.py --check
python tools/rule_status_scan.py --check
```

**验证记录**

在实施完成时新增一份日期化验证记录到 [`plans/`](../plans/)，至少记录：

- Git 工作树状态；
- Python/pytest 版本；
- 每条命令；
- 开始和结束时间；
- 退出码；
- passed/skipped/failed 数；
- 失败分类；
- 与 Wave 1 退出门的一一映射。

未运行的命令必须标记“未验证”，不得用推断替代证据。

### Task 14：Wave 1 结束审查与批准门

**审查清单**

1. 对照上位设计第 15.1 节逐项核验退出门；
2. 搜索是否修改了旧 claim 字段、旧三结构枚举、默认 router schools 或 production expert systems；
3. 搜索新路径是否调用未知 trigger 放行入口；
4. 搜索是否读取系统当前年或从 `as_of_date` 推断流年；
5. 搜索是否存在 global school weight 或 partial→uniform fallback；
6. 搜索是否将 Ditiansui 写为第六个 peer；
7. 搜索是否把 catalog-only 条目标成 production；
8. 搜索是否存在报告、反馈、学习写入或生产发布副作用；
9. 审查新增公共导出面是否最小；
10. 形成代码审查结果和新鲜验证证据。

**停止条件**

- Wave 1 完成后停止；
- 不自动开始 Wave 2；
- 不生成 Wave 2 函数级计划，直到用户确认 Wave 1 的实际接口和验证证据；
- 不开始 Wave 3 规划或实现。

## 4. 依赖与执行顺序

```text
Task 0 基线
  ↓
Task 1 canonical primitive
  ↓
Task 2 fact contracts
  ├─→ Task 3 fact builder
  └─→ Task 4 certification registry
          ↓
Task 5 governance claim + adapters
          ↓
Task 6 school/capability registry
          ↓
Task 7 seven-gate arbitration
          ↓
Task 8 constrained composition
          ↓
Task 9 fail-closed trigger
          ↓
Task 10 structure catalog
          ↓
Task 11 shadow runner
          ↓
Task 12 isolation guards
          ↓
Task 13 layered verification
          ↓
Task 14 review and stop gate
```

可并行范围仅限：

- Task 3 与 Task 4 可在 Task 2 契约冻结后并行；
- Task 9 与 Task 10 可在 Task 1/2 基础稳定后并行；
- 测试编写可并行，但公共类型和 YAML schema 必须先由单一 owner 冻结。

禁止并行修改同一公共契约文件，以免产生两个事实或 claim 语义源。

## 5. 建议提交边界

若用户后续授权使用 Git，建议按以下原子提交组织；当前计划不授权提交：

1. `test(governance): freeze wave1 compatibility baseline`
2. `feat(governance): add canonical immutable fact contracts`
3. `feat(governance): add fact builder and certification registry`
4. `feat(governance): add claim envelope and legacy adapters`
5. `feat(governance): add five-school capability registry`
6. `feat(governance): add seven-gate arbitration and source folding`
7. `feat(governance): add constrained composition and closed triggers`
8. `feat(ziping): freeze thirty-structure catalog`
9. `feat(governance): add isolated shadow runner`
10. `test(governance): add isolation and full regression gates`

每个提交必须通过对应窄测试；不得把测试、实现和无关格式化混在一个超大提交中。

## 6. Wave 2 / Wave 3 门禁路线图

### 6.1 Wave 2：杨派婚姻首切

只保留上位设计中的门禁：

- 进入门：[`multi-school-governance-design-2026-08-02.md`](multi-school-governance-design-2026-08-02.md) 第 15.2 节；
- 目标和边界：同文件第 15.2 节；
- 退出门：同文件第 15.2 节。

在 Wave 1 全部退出门和新鲜验证未通过前，不编写 Wave 2 的函数、文件或测试级实施计划。

### 6.2 Wave 3：杀印相生压力切片

只保留上位设计中的门禁：

- 进入门：[`multi-school-governance-design-2026-08-02.md`](multi-school-governance-design-2026-08-02.md) 第 15.3 节；
- 派别职责和边界：同文件第 15.3 节；
- 退出门：同文件第 15.3 节。

在 Wave 2 完成冻结、评分和显式发布治理验证前，不编写 Wave 3 的函数、文件或测试级实施计划。

## 7. 计划自审

### 7.1 与批准设计一致

- 五派同级，中央有限裁判；
- Ditiansui 未被静默升级为第六派；
- L0/L1/L2A/L2B 分离；
- claim 采用新增信封，不破坏两个旧模型；
- 仲裁严格七步且不使用学校票数平均；
- 同源证据折叠但不删除原 claim；
- 组合仅使用注册模板；
- trigger 在新路径 fail closed；
- 显式年份约束完整；
- 30 格局只冻结目录，不假装 30 个 evaluator 已交付；
- 新路径先 shadow，不改生产默认入口。

### 7.2 范围审查

- 未规划报告、反馈或学习写入改造；
- 未规划生产发布自动化；
- 未规划 Wave 2/3 函数级工作；
- 未授权代码实现、Git 提交或部署；
- 未以测试通过等同真实准确率提升。

### 7.3 主要风险及计划内控制

| 风险 | 控制 |
|---|---|
| 两个旧 claim 模型继续分叉 | 新增 canonical governance envelope；显式双适配器；冻结旧字段 |
| 新骨架变成第三套无人使用系统 | Wave 2 必须使用 Wave 1 实际接口；shadow runner 提供最小端到端链 |
| 同源 claim 形成伪多数 | 独立性分组键、性质测试、复制同源 claim 不增权 |
| 未注册能力被宽松回退 | 明确 `abstain`；禁止 partial→uniform fallback |
| Ditiansui 权威边界漂移 | 仅 legacy compatibility source；peer registry 精确五项测试 |
| 自由文本 trigger 再次进入生产 | 封闭 evaluator registry；未知 ID fail closed |
| 目录冻结被误解为规则完成 | 实现状态和发布状态分离；catalog-only 不可执行 |
| 新包违反 Clean Architecture | 新依赖守卫；应用适配器与领域契约分层 |
| 过早改变生产输出 | shadow runner 不注册到默认 pipeline；旧回归全保留 |

## 8. 最终批准门

本计划完成后，下一动作只能是以下二者之一：

1. 用户明确批准实施 Wave 1，然后按 Task 0 开始；
2. 用户要求修订计划，先修订并重新审查。

在明确实施批准前，不创建 [`engine/governance/`](../engine/governance/) 源码、不创建新 YAML 契约、不修改测试、不运行声称实施完成的验证。
# PI-225-R1：共享 gate 定义成员身份最小澄清

> `task_id`: PI-225-R1  
> `parent_task_id`: PI-200/PI-400  
> 授权：用户明确选择 A，授权最小 G2 契约澄清  
> 结论：`COMPLETED`  
> 性质：设计契约 amendment，待分离实例独立验收

## 1. 目的与授权结论

本次只澄清一个 G2 表达缺口：多个 `GateEvaluationRecord` 可以共享同一个真实、可机械解析的整体 `FrozenCardFieldRef`；每条记录同时通过版本化、摘要绑定的显式声明成员身份，稳定绑定到其 declared member，从而消除共享引用下的置换歧义。

用户明确选择集合级推荐方案：`GateEvaluationSet` 内含版本化 `GateMemberDeclarationSet`，每条 `GateEvaluationRecord` 以 `declared_member_id` 引用其中恰一成员，并使用不可变 `GateEvaluationBindingRef` 绑定成员身份与该记录的状态、证据及结构引用。

本次没有修改冻结 F09 六维、配置轴／风险轴／双轴、state／event／outcome、门满足条件、评分、排序、优先级或动作选择语义。正式冻结事实仍以 [`12-real-world-function-evidence-cards-v1.md`](../engine/contracts/12-real-world-function-evidence-cards-v1.md:265) 为准，声明性镜像仍以 [`real-world-function-evidence-cards-v1.yaml`](../mapping/real-world-function-evidence-cards-v1.yaml:437) 为准。

## 2. 问题边界

独立 G4 复评确认，冻结 F09 的六维共同存在于一个真实整体冻结声明中；为六维虚构六个正式子路径会破坏引用真实性，见 [`production-implementation-pi-400-r2-g4-technical-rereview.md`](production-implementation-pi-400-r2-g4-technical-rereview.md:114)。但原 `GateEvaluationRecord` 只有 `gate_definition_ref`，没有稳定 declared member identity；多个记录共享整体 ref 时，记录与成员之间存在不可机械区分的 `6!` 置换。

此次 amendment 只补 G2 通用身份协议，不扩大冻结对象模型，也不要求修改 [`FrozenCardFieldRef`](production-implementation-pi-210-normalized-evidence-model.md:340) 或 PI-230 trace 协议。最小方案在 PI-220 内闭合，因此没有触发越权阻断。

## 3. Schema 澄清

规范修改位于 [`production-implementation-pi-220-decision-interface.md`](production-implementation-pi-220-decision-interface.md:239)，新增或收紧以下对象：

1. `GateEvaluationSet.gate_definition_refs` 与 `records` 改为非空集合。
2. `GateEvaluationSet.member_declaration_set` 保存集合级 `GateMemberDeclarationSet`。
3. `GateMemberDeclarationSet` 明确：
   - `declaration_set_id`；
   - `declaration_source_id`；
   - `declaration_schema_version`；
   - `declaration_version`；
   - `content_digest: DigestRef`；
   - 非空 `members`。
4. `GateDeclaredMember` 明确：
   - 稳定 `declared_member_id`；
   - 非 null、类型保持的显式 `declared_member_value`；
   - 真实 `gate_definition_ref`。
5. `GateEvaluationRecord` 新增：
   - `declared_member_id`，只引用当前声明集中的成员；
   - `evaluation_binding_ref`，绑定完整记录 payload 与不可变获授权来源。
6. `GateEvaluationBindingRef` 明确：
   - `binding_id`；
   - `binding_schema_version`；
   - `binding_version`；
   - `canonical_record_digest`；
   - `immutable_source_digest`。

`declared_member_id` 不允许依赖 `gate_record_id` 字符串解析、数组位置、证据内容、issue path 或自然语言运行时解析。`declared_member_value` 是已授权声明源中的显式值，不是 evaluator 运行时猜测，也不承载卡片算法。

## 4. 机械不变量

规范不变量位于 [`production-implementation-pi-220-decision-interface.md`](production-implementation-pi-220-decision-interface.md:313)：

1. **定义 ref 去重与集合一致性**：`gate_definition_refs` 按 `FrozenCardFieldRef` 完整规范值去重；它必须等于成员 ref 与记录 ref 的各自去重集合。多个成员可共享一个真实整体 ref。
2. **声明身份完整性**：声明集 ID 恰一解析；来源 ID、schema version、declaration version 与 digest 全部匹配；成员 ID 和显式值均非空且唯一。
3. **record→member 一致性**：记录 candidate 与所属 set 一致；记录 ID 在当前 result 唯一；成员 ID 在当前声明集恰一命中；记录 ref 与成员 ref 逐值一致。
4. **全双射基数**：`records` 与 `members` 一一对应，`|records| = |members|`；重复、遗漏、未知成员、跨版本回退全部无效。
5. **evaluation binding 完整性**：每条 binding 恰一解析；版本、record digest、source digest 以及不可变来源 payload 与当前记录逐值一致。
6. **共享 ref 一致性**：同一成员在同一声明版本中只绑定一个规范 ref；set ref、member ref、record ref 任一不一致即 `BLOCKED`。
7. **失败安全状态**：声明、版本、摘要、绑定、重复、遗漏、未知成员或共享 ref 不一致均为 `BLOCKED`；不得以本地默认值、位置配对或 last-write-wins 恢复。

## 5. Permutation falsifier

设计级 falsifier 位于 [`production-implementation-pi-220-decision-interface.md`](production-implementation-pi-220-decision-interface.md:333)，至少覆盖：

- 交换两条记录的状态、证据、关系、路径或 reason code，但不同时交换其显式成员身份与获授权 binding：必须因 record digest／来源 payload 不匹配而失败。
- 仅交换或伪造 `declared_member_id`：必须因 member ref 或 binding 不一致、未知成员、重复或覆盖不完整而失败。
- 修改成员声明值、ref、声明版本或摘要：必须因声明来源完整性失败而失败。
- 仅改变数组顺序，同时完整保留每条记录的身份与 binding：结构语义必须不变。

因此映射由 `record → declared_member_id → versioned declaration member → real FrozenCardFieldRef` 唯一确定。共享同一个真实 ref 不再造成成员与记录之间的 `n!` 不可辨识置换；对 F09 的六个声明成员，即不再存在 `6!` 置换不可辨识性。

## 6. Fail-closed reason codes

PI-220 最小 reason code 目录增加四个纯结构 code，见 [`production-implementation-pi-220-decision-interface.md`](production-implementation-pi-220-decision-interface.md:782)：

- `GATE.MEMBER_DECLARATION_INVALID`；
- `GATE.MEMBER_CARDINALITY_INVALID`；
- `GATE.MEMBER_BINDING_MISMATCH`；
- `GATE.PERMUTATION_BINDING_INVALID`。

这些 code 只描述可机械核对的结构失败，不判断任一卡是否成立。

## 7. 兼容影响

### 7.1 规范兼容

- 这是 PI-220 的收紧 amendment：原本没有显式成员身份的 gate set，在声称逐成员完整性或共享整体 ref 时，不再满足澄清后的结构契约。
- `FrozenCardFieldRef` 形状和 PI-210 来源语义不变。
- PI-230 可继续通过 PI-220 record ID 追踪，不要求本任务修改其 schema。
- 原 reason code `GATE.STATE_UNKNOWN` 不变，本任务没有认可或映射未登记别名。

### 7.2 运行时与生产兼容

- 当前仅设计规范，没有 schema 实现、consumer、migration、validator、dispatcher 或 production wiring。
- 没有执行 YAML，没有切换 production-default，没有进入 G5。
- 本文不证明现有 PI-300 fixture 已兼容 amendment，也不关闭 G4 其他 finding。

## 8. 静态一致性检查

执行口径仅为文档静态交叉核对，不运行测试：

- 对照 PI-210 的 `DigestRef` 与 `FrozenCardFieldRef`，复用既有版本／摘要和真实字段引用语义；
- 对照 PI-220 原 gate set／record、reason code 和不变量，确保新增字段均为通用结构字段；
- 对照 PI-230 身份原则，确认不以数组序号、自由文本或路径冒充稳定身份；
- 对照冻结 F09 Markdown 与 YAML，确认未创建 F09 子路径、谓词、评分、排序、轴优先级或业务新枚举；
- 对照 G4 finding，确认共享真实整体 ref 与逐成员 record 可同时机械表达。

**结果：静态一致性检查完成；0 tests executed；0 YAML executed；0 production changes。**

## 9. 未解决风险

1. 本 amendment 尚未由分离实例独立验收，不能自称 G2 amendment PASS。
2. PI-300 当前六维 fixture 仍使用虚构子路径且缺少新成员声明／binding；本任务无权修改它，G4-H-01 不能由本文自动关闭。
3. G4-M-01 的 state／event／outcome 来源 locator 与 LOSSLESS 证明缺口未处理。
4. G4-M-02 的未登记 UNKNOWN reason code 漂移未处理。
5. 未来实现必须定义 canonical serialization 与声明源注册/解析机制；本任务只规定其必须稳定、版本化、摘要绑定和 fail closed，不选择具体实现。
6. 向后兼容需要后续独立设计或实现任务处理；不得用 legacy fallback 绕过成员身份校验。

## 10. 边界与非冻结语义变更声明

本次只修改 [`production-implementation-pi-220-decision-interface.md`](production-implementation-pi-220-decision-interface.md:239) 并创建本文。没有修改 PI-210、PI-230、PI-300、冻结契约、mapping、总控、handoff、评审记录、代码或测试。

本 amendment 不构成 F09 冻结业务语义变更，不解释资源、对象、配置轴、风险轴、归属、时态、单轴／双轴、state、event 或 outcome 如何判定。它也不构成 G2 自验、G4 通过、实现授权、生产 readiness 或 G5 入口。

## 11. 唯一下一动作

**独立 PI-295-R1 amendment acceptance。**

该验收必须由与 PI-225-R1 分离的实例执行，机械核对 schema、版本／摘要绑定、去重与全双射基数、重复／遗漏／未知成员、共享 ref 一致性及 permutation falsifier；在独立裁决前不得把本次 `COMPLETED` 解读为 amendment `PASS`。
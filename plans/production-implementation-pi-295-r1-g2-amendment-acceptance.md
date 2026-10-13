# PI-295-R1：G2 最小修订独立验收记录

## 1. 独立性与范围

- 任务：PI-295-R1；父任务：PI-200。
- 本记录对 PI-225-R1 对 PI-220 的最小结构澄清作独立、只读验收。
- 验收仅判断设计契约是否机械消除“多个 gate record 共用一个真实冻结字段引用”时的 record → member 置换歧义；不把设计充分性解释为实现、运行时校验或 G4 整改已经完成。
- 本次未修改被审材料、冻结契约、mapping、PI-300、control、handoff、代码或测试；唯一写入物是本记录。
- 本次未递归委派，未进入 G5，未执行 YAML，未运行测试。
- 直接证据范围：
  - [PI-210 归一化证据模型](production-implementation-pi-210-normalized-evidence-model.md:330)
  - [PI-220 决策接口](production-implementation-pi-220-decision-interface.md:239)
  - [PI-225-R1 最小澄清](production-implementation-pi-225-r1-shared-gate-member-identity-clarification.md:11)
  - [PI-230 可追溯绑定](production-implementation-pi-230-traceability-binding.md:112)
  - [PI-290-R3 G2 复验基线](production-implementation-pi-290-r3-g2-reacceptance.md:1)
  - [PI-400-R2 G4 技术复审](production-implementation-pi-400-r2-g4-technical-rereview.md:114)
  - [冻结 F09 Markdown 契约](../engine/contracts/12-real-world-function-evidence-cards-v1.md:265)
  - [F09 YAML 声明](../mapping/real-world-function-evidence-cards-v1.yaml:437)

## 2. 验收矩阵

| # | 验收维度 | 结论 | 机械证据与判断 |
|---:|---|---|---|
| 1 | Schema 完整性 | 满足 | PI-220 同时定义 declaration set、declared member、record member identity 与 immutable binding，并把它们纳入 gate set/record 必填结构；相应规范集中见 [PI-220 的修订 schema 与不变量](production-implementation-pi-220-decision-interface.md:239)。PI-225-R1 对该最小增量的摘要与规范一致，见 [PI-225-R1 schema 摘要](production-implementation-pi-225-r1-shared-gate-member-identity-clarification.md:23)。 |
| 2 | 真实冻结引用 | 满足 | PI-210 的 FrozenCardFieldRef 仍由 card、contract、version、field path、source state/value 与 locator 标识真实冻结字段，见 [PI-210 FrozenCardFieldRef](production-implementation-pi-210-normalized-evidence-model.md:333)。修订允许多个 member/record 共享同一个真实整体引用，不制造六个不存在的 F09 子路径；这正面规避了 [G4-H-01](production-implementation-pi-400-r2-g4-technical-rereview.md:114)。 |
| 3 | 稳定 member identity 来源 | 满足 | declared member identity 来自显式、版本化 declaration set，而不是数组位置、record id、证据文本、issue path 或自然语言推断；规范见 [PI-220 declaration identity 约束](production-implementation-pi-220-decision-interface.md:298)。这与 PI-230 禁止用数组顺序、渲染顺序、文件路径或自由文本充当稳定身份的原则一致，见 [PI-230 稳定身份原则](production-implementation-pi-230-traceability-binding.md:112)。 |
| 4 | Version/digest 绑定 | 满足 | declaration set 带 schema version、declaration version 与 content digest；每条 record 又以 canonical record digest 和 immutable source digest 绑定完整记录载荷与授权来源，见 [PI-220 绑定要求](production-implementation-pi-220-decision-interface.md:298)及[六项机械不变量](production-implementation-pi-220-decision-interface.md:313)。 |
| 5 | Cardinality 与 bijection | 满足 | 规范要求 records 与 declaration members 数量完全相等、每个 member 恰有一条 record、每条 record 恰解析到一个 member，形成全双射；违反即结构性阻断，见 [PI-220 双射不变量](production-implementation-pi-220-decision-interface.md:313)。 |
| 6 | Duplicate/omission/unknown-member 处理 | 满足 | 重复 declaration member、重复 record membership、成员遗漏、未知成员及跨 declaration-set 回退均被明确拒绝，见 [PI-220 member 校验与阻断条件](production-implementation-pi-220-decision-interface.md:313)。 |
| 7 | Permutation falsifier | 满足 | 六类反证覆盖 state/evidence 等载荷交换、仅 member id 交换、未知/重复 member、declaration value/ref/version/digest 变化，以及完整 record 重排的语义不变性；前五类必须阻断，最后一类不得改变语义，见 [PI-220 permutation falsifier](production-implementation-pi-220-decision-interface.md:333)与[PI-225-R1 反证摘要](production-implementation-pi-225-r1-shared-gate-member-identity-clarification.md:64)。因此匹配不再依赖位置，且非法置换不能保持有效绑定。 |
| 8 | Legacy fail-closed | 满足 | 缺少显式 declaration member identity 或 immutable binding 的旧结构不得宣称满足澄清后的结构完整性，也不得通过推断重建；PI-225-R1 明令禁止 legacy fallback，见 [PI-225-R1 未决风险与回退禁令](production-implementation-pi-225-r1-shared-gate-member-identity-clarification.md:113)。 |
| 9 | PI-210/PI-230 兼容性 | 满足 | 修订复用 PI-210 的 FrozenCardFieldRef 与 DigestRef，不改变 source state/value 语义；PI-230 继续追踪稳定的 PI-220 record identity，且不重算 gate decision。边界分别见 [PI-210 稳定声明身份规则](production-implementation-pi-210-normalized-evidence-model.md:429)、[PI-230 的 PI-220 追踪边界](production-implementation-pi-230-traceability-binding.md:329)及[PI-225-R1 兼容性声明](production-implementation-pi-225-r1-shared-gate-member-identity-clarification.md:86)。未发现对既有类型或追踪不变量的新回归。 |
| 10 | Reason-code 注册 | 满足 | 四个结构性原因码已进入 PI-220 最小目录：GATE.MEMBER_DECLARATION_INVALID、GATE.MEMBER_CARDINALITY_INVALID、GATE.MEMBER_BINDING_MISMATCH、GATE.PERMUTATION_BINDING_INVALID，见 [PI-220 reason-code 注册](production-implementation-pi-220-decision-interface.md:780)。 |
| 11 | 无 F09 业务语义变更 | 满足 | 冻结 Markdown 仍以一个整体声明承载资源、对象、配置轴、风险轴、归属与时态六个语义维度，见 [冻结 F09 现实硬门声明](../engine/contracts/12-real-world-function-evidence-cards-v1.md:269)；YAML 仍保持声明式表达并将 allocation/risk 合并为 allocation_axis_or_risk_axis，见 [F09 necessary_reality_gates](../mapping/real-world-function-evidence-cards-v1.yaml:437)。修订只增加结构身份和绑定，不增加 gate、轴、通过条件、评分、优先级、动作选择或输出语义，符合 [PI-225-R1 非语义变更边界](production-implementation-pi-225-r1-shared-gate-member-identity-clarification.md:122)。 |

## 3. Findings 与精确统计

### 3.1 验收结果统计

- 验收矩阵：11 项满足，0 项不满足。
- High findings：0。
- Medium findings：0。
- Critical ambiguities：0。
- Critical evidence gaps：0。
- New regressions：0。
- Low findings：0。
- Informational boundaries：2。

### 3.2 非阻断边界

1. 本验收只确认 G2 设计契约充分；不证明 declaration registry、canonical serializer、source resolver 或 runtime validator 已实现。PI-225-R1 将这些保留为后续实现事项，见 [PI-225-R1 未决实现边界](production-implementation-pi-225-r1-shared-gate-member-identity-clarification.md:113)。
2. 本验收不关闭 PI-300 或既有 G4 findings。尤其 [G4-H-01 的伪造六子路径问题](production-implementation-pi-400-r2-g4-technical-rereview.md:114)仍须由后续有界整改处理；本次通过的是 PI-220 局部契约澄清，而不是现有 fixture 或实现状态。

上述两项均为明确的阶段边界，不构成 amendment 本身的 High/Medium、关键歧义、关键证据缺失或新回归。

## 4. 执行声明

- Tests executed：0。
- YAML executed：0。
- Reviewed artifacts modified：0。
- New review records written：1，即[本独立验收记录](production-implementation-pi-295-r1-g2-amendment-acceptance.md:1)。

## 5. 唯一最终裁决

**PASS**

PI-225-R1 对 PI-220 的最小修订在设计契约层面机械消除了共享一个真实 FrozenCardFieldRef 时的 record → member 置换歧义，并保持 PI-210、PI-230 与冻结 F09 业务语义边界不变。

## 6. 唯一下一动作

PI-470-R2 有界整改。

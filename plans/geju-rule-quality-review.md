# 格局判断：子平 / 滴天髓生产规则可用性审查

## Thesis

当前子平（933 条）和滴天髓（1108 条）生产规则不是"规则"——它们是**原文堆叠**。`output.statement` 直接填入整段古籍原文加注释（平均 140-189 字符），中间还夹了 `滴天髓规则参与：` 前缀。这些"规则"在 v6 五派表中渲染为墙壁式的长文本，命理师不可能在实战中逐条阅读。

正确的目标模型是：每条规则有一个**简明的判断结论**（<100 字符，直接可读），原文保留在 `source.excerpt` 中作为证据备查；报告展示只输出判断结论，不输出原文。

## Confidence

- **Confidence level**: high
- **Why not certain**: 子平规则中有一小部分 `quantifiable=True` 的规则（如 `ZP-PROD-20260622-001`）statement 相对可用；但大部分 `quantifiable=False` 的规则是纯粹的文言文堆叠，无法在实战报告中直接使用。

## The Trap

- **Inherited constraint**: `output.statement` 被设计为"既当判断结论又当证据原文"，因为原始提取脚本把 `excerpt` 和 `statement` 填成一样的内容。
- **Is it real?**: partially
- **Why**: 生产和反馈系统已依赖 `statement` 字段存在、`output.falsifiable` 存在、`evidence` 链存在；但只要不删字段，只改内容就不会破坏契约。

## High-格局 Direction

最重要的发现是：问题不在 **v6 框架本身**，而在 **生产规则的内容质量**——不是五派裁判不好使，而是喂给五派裁判的"规则"不该是大段原文。

**量化的严重性**：

| 指标 | 子平 | 滴天髓 |
|---|---|---|
| 总规则数 | 933 | 1108 |
| quantifiable=True | ~20（估） | ~50（估） |
| 平均 statement 长度 | ~140 字符 | ~189 字符 |
| 可独立作为断语的规则 | ~5-10% | ~5-10% |
| 纯原文堆叠 | ~90%+ | ~90%+ |

这意味着当前 `run_v5()` 处理了 2000+ 条"规则"中，只有约 100-150 条真正能在分析中给出判断；其余都是噪声。当我们把 `build_ditiansui_production_claims()` 的 `limit` 从 12 调到 24 甚至不限时，输出密度不会线性提升——因为排在后面的规则更不可能有用。

## Frame-Opening Move

- **Move used**: kill the wrong concept + ten-times question
- **What it reveals**: "把古籍原文抄进系统"不是规则提取，是搬运。真正的问题是**我们没有对原文进行命理师级别的蒸馏**。如果我们要支持 10x 案例量、50x 规则数，当前每增加一条"规则"就意味着增加一条噪声。

## Bold Takes

- **删除 `output.statement` 的原文倾卸**：`statement` 字段应只保留 1-2 句可直接使用的判断结论（如"已土不宜木盛，身弱财旺需比劫护"），原文全部放入 `source.excerpt`。不能在报告里把 189 字符的文言注释放进五派表单元格。
- **重命名 `statement` 为 `conclusion`**：区分"规则结论"和"证据原文"；当前两用是混乱的根源。
- **停用 `quantifiable=False` 规则的生产渲染**：不可量化的规则不应出现在裁判器的正式命题池里；它们可以留在 knowledge base 中供 AI 引用，但不应该进入计算层。
- **合并重复的 STRUCTURE 规则**：滴天髓大量 rule_type=STRUCTURE 的规则实质上是同一段话的不同截取（"三 人道"段被截成 5 条规则）；应该合并为一条。

## Options

| Option | What it optimizes | Cost | Verdict |
|---|---|---|---|
| Conservative path | 保持现有 YAML 不变，只在 v6 `build_ditiansui_production_claims()` 中限制 `limit<=4` | 规则库永远是噪声，永远不敢开大 limit | reject |
| Clean target | 重写子平 / 滴天髓 YAML：删除重复，`statement` 缩到 <100 字符，`quantifiable=False` 的不进入命题池 | 需要人工 review 2041 条规则，估算 2-4 人天 | preferred |
| Staged clean path | 不改 YAML，在 v6 runner 中过滤：只渲染 `quantifiable=True` 的规则，`quantifiable=False` 的规则只留 1-2 条代表性 | 不需要改库，立即可做 | recommended for immediate |

## What Not To Do

- 不要把更多原文倒进 `statement`——停止当前"全量原文提取 → 直接进入 production"的流程。
- 不要试图在 report_view.py 中截断 statement 文本——那是治标不治本。
- 不要立即废弃子平 / 滴天髓规则库——它们作为 knowledge base 有长期价值，但必须和"生产规则池"分离。

## First Proof Point

最小的可验证改进不是重写 2000 条规则，而是：在 `build_ditiansui_production_claims()` 中加一个过滤——只输出 `quantifiable=True` 的规则。看看报告中的滴天髓列从 12 条巨长不的文言文变成几条简短结论的效果。如果效果可接受，再推广到子平。

## Falsifier

如果在执行 Staged clean path（只保留 quantifiable=True）后发现：
- 滴天髓列几乎全空（可量化规则太少，不足以填充五派表）
- 子平列因为缺少不可量化规则的"结构性心法"，分析师认为框架信息不足

那么 thesis 需要修正："不能一刀切删除所有 quantifiable=False 的规则；需要为结构性心法（如格局定义、气势判断）单独留一个展示层，但它们不进入裁判器的概率应期计算。"

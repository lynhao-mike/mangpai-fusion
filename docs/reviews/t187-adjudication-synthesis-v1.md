# T-187 两方裁决合成：A（分流）vs D（强制），建议 A+

> 依据：Opus 5.5（D，强制裁决双层）与 WB（A，分流引擎）；中枢复核 12/40、28/40、2/20。
> 状态：**建议草案，未冻结**；等人类/Gemini 4 决定。

## 1. 两方共识（不再争）

- T-187 的 kill 是**量具无效**，不是产品 kill；引擎党势方向层 kill 成立。
- 28/40 边错配；20 directed 只有 2 对；4 mutual 全打自刑边；真实精度 2/20。
- Agent 层没上场；盲输入缺 relation identity；source locator 泄漏；T-184 R4/R7/R8 与 coverage 门槛结构性矛盾。
- 不从 fresh-40 答案往引擎补规则；不在 dev-20/fresh-40 上调阈值；不把 nj 当合法逃票。
- 最小单元=锚定断言；主证明=新盲集系统级；3 张旧卡只演示。

## 2. 分歧

| | Opus · D | WB · A |
|---|---|---|
| 引擎 | 固定克/生/化/墓；冲/合/刑/穿候选 | 固定克/生/化/墓 + mutual；冲/合/穿/刑全归 Agent |
| Agent | 必须给 actor→target 或 mutual；nj 不是合法终态 | 可判断言给方向；ambiguous 可 nj 但必须带歧义 quote |
| 盲集 | fresh-60；E1 给边 + E2 选边 | anchor-40；relation identity；选边只作披露 |
| 阈值 | 45/60；kill <36 | 32/40 + Wilson；产品 kill <24/40 |
| 风险 | 对真歧义（穿制/合绊）逼出假确定 | 用 nj 逃票；产品仍可能只是“看边说话” |

## 3. 建议 A+（合成）

**A+ = 可判断言强制表态 + 真歧义才允许带引文的 nj；引擎党势层死，Agent 层必须上场。**

- 输入：一盘 + relation identity（a/b 字 + kind/mechanism）；不给 source locator。
- 引擎：只出事实 + 克/生/化/墓方向 + 有源 mutual；冲/合/穿/刑的 nj/mutual 只是候选。
- 标注：每条预标 `decidable` / `ambiguous`（穿制源冲突、合绊/保护、制净、Δ=0、表外无源）。
- Agent：
  - `decidable`：必须给 actor→target 或 mutual；给 nj = miss。
  - `ambiguous`：可给 nj，但必须带**冲突原文的逐字 quote**；否则算 miss。
  - 可判断言 nj 逃票 >25% → 产品级 kill。
- 主指标：decidable delivered-verdict 正确率；ambiguous 只记“分流正确率”，不混进方向精度。
- 新盲集：**anchor-40 先做**（≥25 盘、≤2/盘、双零重叠、标注/运行/裁判分离、先 hash）；若 40 能过，再 fresh-60 复测宣称；E2 选边只作披露，不当主门槛。
- 阈值：decidable correct ≥32/40 且 Wilson LB>50%；kill <24/40；ambiguous 分流正确率单独报；可判断言 nj 逃票 ≤25%；锚点失效 ≤10%；第三人可重推；3 次方向一致 ≥90%。
- 3 张卡：direction_known 3/3、rescue 明确、换盘拒绝 ≥90%、反事实敏感点。

## 4. 为什么不是纯 A / 纯 D

- 纯 A 的风险：Agent 用 nj 逃票，产品退化成“你告诉我看哪条边，我告诉你方向/不告诉”；WB 自己设了 nj 逃票 >25% 的 kill，说明这个风险真实。
- 纯 D 的风险：穿制原文自相矛盾（M1-D-024），逼 Agent 在真歧义上给确定方向，等于用假确定换通过率；Opus 的 D 没有给 ambiguous 留合法出口。
- A+ 把“必须表态”限制在 decidable，把“诚实分流”限制在 ambiguous 且必须带冲突原文；既不让 Agent 逃票，也不逼它撒谎。

## 5. 下一步（待确认，不跑）

1. 冻结 A+ 规格 + anchor-40 策展规则；先 hash，再跑。
2. 修 T-186 评分器：地址/字归一、relation identity、decidable/ambiguous 分栏、nj 逃票、Wilson；用合成样例先过。
3. 策展 anchor-40（换人、双零重叠、无 locator、先 hash）。
4. 未污染 Agent 跑一次；按预注册判；过则 fresh-60 复测宣称。

**不要做**：不复活引擎党势层；不为 PF-008/R8 调规则；不重计 dev-20/fresh-40；不让 Agent 靠 nj 逃票；不把 E2 选边当主门槛；不扩岁运/神煞。

## 6. 当前

- main `57552b78`；baseline 1489/481/374；T-187 产物保留；goal 仍 blocked。
- 本文件是建议，不是已冻结预注册；需要人类/Gemini 4 选 A / D / A+。

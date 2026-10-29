# T-183 · 固定五行缺陷修复 + E-08 评分器防覆盖

- 状态：🔵 Ready
- 优先级：**P0（零争议的确定性修复）**
- 依据：Opus 裁决 2026-10-29；T-178/T-180 审计
- 前置：main `f230e5b2`

## 0. 一句话

只修**固定五行**的三处确定性漏项：支克支、干克支、同对 `ke` 优先于 `wuhe`；
同时修 E-08（评分器默认覆盖冻结基线）。**不做党势、不做穿/合/冲方向、不为 H02/H05 写规则。**

## 1. 改动

1. `engine/facts/structure_check.py`
   - 新增 `_derived_zhi_ke(chart)`：地支本气五行相克，所有柱对；返回 `(克方, 被克方, dist)`；
     候选 `mode="制用"`, `relation_kind="zhi_ke"`, `actor=克方`；**不建 `RelationGraph.edges`**。
   - 新增 `_derived_gan_ke_zhi(chart)`：天干克地支，所有柱对；候选 `mode="制用"`,
     `relation_kind="gan_ke_zhi"`, `actor=天干`；不建 edges。
   - 同对天干同时有 `ke` 与 `wuhe` 时，`ke` 候选排在 `wuhe` 前（或去重时保 `ke`）；
     不改 `RelationGraph`，不改 `ke` 的 actor 规则（`members[0]`=克方）。
   - 不实现 H02/H05 的冲/穿方向；不实现党势；T-178 的合/冲/刑/穿 actor=None 保持。
2. `tools/p1_holdout_eval.py`（E-08）
   - 未传 `--out-json` 时**不写** `META/p1-holdout-baseline-v1.*`；只打印 stdout 或退出 2。
   - 目标文件已存在且未显式 `--force` 时拒绝覆盖；`--artifact-label` 保留。
   - 测试覆盖：默认不写、显式写、已存在拒绝、`--force` 允许。

## 2. 验证

- H03（丙辛，ke e002 actor=丙）、H06（午克酉）、H07（戊克子）转对；
- `pytest -q` 0 failed；`engine_audit` 481/0；`relations_audit` 全过；15KB 测试盘 <15,000B；
- dev-20 只作否决：显式 `--out-json META/p1-dev20-veto-v1.json --artifact-label dev20_veto`
  跑一次，确认 H03/H06/H07 与既有 8 条不回退；**不在 dev-20 上宣称提升**；
- 不跑官方 P1/系统级盲测；不碰 fresh-40。

## 3. 产物

- 分支 `p1/fixed5`（worktree `..\mangpai-fusion-fixed5`，从 `f230e5b2` 起）
- `structure_check.py`、`tools/p1_holdout_eval.py`、测试
- `tasks/T-183/BRIEF.md` + `STATUS.md`

## 4. 禁止

- 不写党势/比值/权重/浮点；不为 H02/H05 写专用规则；引擎不判穿制；
- 不改 hold-out/answers/分母；不跑官方 P1；不 push main。

# T-199 · 冲的胜负/方向 窄实验（段建业 22；离散谓词；≥50 例/留出≥10）

- 状态：🔵 Ready（重定向；合化版降为 T-200）
- 依据：22:L2872 显式判定句；WB/Gemini/Opus 综合；中枢合成（2026-10-30）
- 前置：main `b27aea91`

## 0. 一句话

只做一个决策：**原局单冲“谁去”**（A 胜/B 胜/不判）；规则表锁 **段建业 22**；
条件必须是**离散、有序、engine 可观测谓词**（得令/二冲三冲一/燥湿成势/透藏/合绊修正/冲库与冲支），
**禁任何单一整数党势公式**；案例池 ≥50、留出 ≥10；留出 ≥80% 且覆盖率达标才成立。

## 1. 范围（冻结）

- 决策：冲的胜负/方向（A 胜 / B 胜 / 不判）；一条冲边一结论；
- 书：段建业；**规则表锁 22**（M1-D 索引为基底）；案例从段建业全集按预注册顺序 22→23→21→19→28 逐卷扩容，触发条件=当前卷显式结论案例 <15；
- 案例池 ≥50；留出 ≥10（先封、hash）；规则作者只见训练/理论段；
- 通过：留出 ≥80% 已决 + 覆盖率 ≥70%；两轮上限；**弃权记 miss**，另报开火精度；
- 停：两轮不到 80%，或显式结论案例 <15（本书此决策暂不可形式化，换决策不换书，只许重来一次）；不调阈值、不删案例、不换留出。

## 2. Schema

```yaml
id: C-001
when:            # 全 engine 可观测离散谓词，禁整数党势公式
  pair: [子, 午]
  positions: [Y.b, D.b]
  adjacent: true|false
  month_order: ...
  erchong_sanchong: ...
  dry_wet: ...
  transparency: ...
  combine_bind: ...
  clash_ku_vs_branch: ...
  strength_version: "engine@<hash>"
then:
  verdict: A胜 | B胜 | 不判
  reason: ...
source_ref: sources/duan/MinerU_markdown_22:L2872
quote: "逐字原文"
scope: ...
```

- `when` 全 engine 可观测；文本条件只作 provenance；禁止“旺/有力/党势数字”；
- 不可离散化条件标 `unoperationalized`，永不触发、只披露；
- quote 必须映射到 engine 边/地址，否则不得触发；
- 同边两规则相反→`needs_anchor(rule_a, rule_b)`；书有带 quote 优先级才可解；
- 弃权在作者已判案例上记 miss，防弃权逃票。

## 3. 标签

- 只抽作者**显式冲句**“冲去/冲坏/冲不解/冲起/冲散”；禁由离婚/发财/升职反推；
- 读者 A/B 两个新会话独立抽，互不见产物/规则；分歧 >10% 由 C 第三方裁；人类抽查 20%；
- 每条 quote 必须在所引行逐字检出；κ≥0.85；歧义/两可→ambiguous，不进分母；
- 留出 ≥10 先封、hash；留出四柱不得出现在训练/规则举例；
- 禁为拟合训练案例临时造规则；规则只从 22 理论段/M1-D 导出。

## 4. 产物

- `META/t199-cases-train-v1.json` / `t199-cases-holdout-v1.json`（≥10，sealed+hash）
- `META/t199-rules-v1.yaml`（离散谓词）
- `tasks/T-199/run_rules.py`（四数/冲突/弃权/基线）
- `META/t199-report-v1.md`
- `tasks/T-199/BRIEF.md` + `STATUS.md`

## 5. 验收

- 留出 ≥10 只跑一次；≥80% 已决、覆盖率 ≥70%；
- 训练上规则复现 ≥80%；
- κ≥0.85；歧义率 ≤20%；
- 两轮不到即停；不改阈值/不删案例/不换留出；
- P1 卡冻结 R01；P2 不碰；不改 engine/保护区/旧卡/旧 timing。

# T-181 · 化用候选方向修复（只翻 mode=化用）

- 状态：🔵 Ready
- 优先级：**P0（defined16 里 4 条化 engine_wrong）**
- 依据：`META/p1-hua-actor-audit-v1.md`（T-180）；`docs/specs/actor-rules-v1.md` §4.8
- 前置：T-180 已验收；T-179 已合并

## 0. 一句话

只翻 `mode=化用` 候选：`members=(化者,被化者)`、`actor=化者`（化者=受生端）。
**不得全局翻 `sheng`/`生泄用`**（生者仍是 actor）。H12（财→杀）引擎未识别成化用，记缺口，不扩类。

## 1. 改动

1. `engine/facts/structure_check.py`：`mode=化用` 候选生成处，`members` 顺序改成 `(化者, 被化者)`，
   `actor=化者`；`target=被化者`。
   - 化者判定：化用谓词里的「受生端」（如巳/午/辰/寅）。
   - 只改 `mode=化用`；`sheng(main_qi)`、`生泄用`、`ke`、`muku` 不动。
2. 测试：
   - 用 T-180 的四条做 fixture：H09 巳/卯、H10 午/寅、H11 辰/巳 化者=受生端；`actor=化者`。
   - 既有断言旧 actor 的，按 T-179 反向契约规则改名/改断言（不删/skip/放宽），BRIEF 单列。
   - 新增：不全局翻 `sheng`/`生泄用`（生者仍 actor）。
3. 文档同步：
   - `docs/specs/single-chart-analysis-v1.md` L165 附近「化方向取引擎 actor」改为「化=化者（受生端）」；
   - `docs/specs/actor-rules-v1.md` §4.8 的陷阱句按 T-180 的替换文本改。
4. **H12**（子水→寅木，财→杀）：引擎 `化用` 只认官杀→印，识别不了财→杀；
   本卡**不扩类**，在测试里标 `known_gap`，BRIEF 记缺口。

## 2. 验证

- `pytest -q` 0 failed；481/0；relations 全过；
- 15KB 测试盘仍 <15,000 B；
- 四条化：H09–H11 方向应从 reversed → ok；H12 仍 reversed（known_gap）；
- 不跑 hold-out（P1 由中枢一次性跑）。

## 3. 产物

- 分支 `p1/hua`（worktree `..\mangpai-fusion-hua`，从 main `8a2029b7` 起）上的 commit
- 代码 diff（structure_check.py + 测试 + 两份 docs）
- `tasks/T-181/BRIEF.md` + `STATUS.md`

## 4. 禁止

- 不全局翻 sheng/生泄用；不扩 H12 类别；不改答案/hold-out；不跑 hold-out；不 push main。
- 不改断言换绿；契约变更按反向契约规则并单列。

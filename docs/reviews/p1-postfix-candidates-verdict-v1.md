# P1 post-fix 诊断裁决 v1（2026-10-29，T-179 合并后）

> 对象：`META/p1-holdout-postfix-candidates-v1.json`（工具 `artifact` 字段仍写 `pre_fix_baseline`，R4 待修；本表是 post-fix 诊断，非正式 P1）
> 结论：候选 70%→85%、方向 5%→25%；4 墓已修好；剩余失败是 **G3 支克（6 制）** 与 **化方向（4）**，不是评分器选错。

> **⚠️ 2026-10-29 13:40 更正（T-180）**：4 条化 **4/4 `engine_wrong`**，不是“待定约定”。
> 原文力向＝**被化者 → 化者**，化者恒为受生端；引擎 `化用` 候选把 actor 放在被化者（生者）上，反了。
> 4 化算 **`reversed`**，defined16 仍 **4/16**；冻结 v4 主分母 **20**，defined16 仅诊断。
> §5.2 的「暂定 16 / 化不进失败」**撤回**。H09–H11 可由 T-181 修；H12（财→杀）引擎识别不了，记 `known_gap`。
> 修复后推演：defined16 **7/16**、20 条 **8/20**，仍 <60%。

## 0. 一句话

T-179 把候选召回从 14/20 拉到 **17/20（85%）**、方向从 1/20 拉到 **5/20（25%）**；
但 16 条“制/化/墓”里只 ok 4 条（全是墓），**6 条制仍卡在支克无 ke、4 条化是 engine_wrong（化者=受生端）**。
P1 仍未通过；不调规则。

## 1. post-fix 数字（合并后 main）

| 指标 | pre-fix | post-fix |
|---|---:|---:|
| 边 strict | 8/20 = 40% | **8/20 = 40%** |
| muku 等价边 | 12/20 = 60% | **12/20 = 60%** |
| 候选 | 14/20 = 70% | **17/20 = 85%** |
| 方向 all20 | 1/20 = 5% | **5/20 = 25%** |
| 方向 defined16（H01–H16） | 0/16 = 0% | **4/16 = 25%** |
| 方向 rescue4（H17–H20） | — | 1/4 |
| 方向 branch-ke3（H06/H07/H19） | — | 0/3 |
| 分解 | — | ok 5 / reversed 5 / actor_none 7 / no_edge 3 |

## 2. 为什么 6 条“制”是 actor_none，不是评分器 bug

H01/H02/H03/H04/H05/H08（制）：
- `edge_hit=true`、`candidate_hit=true`，但候选只有 `chong`（如 H01 `chong[Y.b,D.b] actor=None`）；
- 引擎**没有** `ke` 边/候选——支与支的克仍不建（G3）。
- 评分器的“制=不过滤 kind”让 `chong` 算 candidate_hit；但方向取不到 actor → `actor_none`。
- **不是评分器选错，是事实层没有可用的 ke 方向。**

## 3. 4 条“化”是 engine_wrong，不是约定问题

H09–H12（T-180 审计 4/4）：
- 原文力向＝**被化者 → 化者**，化者恒为受生端（卯生巳→巳化；寅生午→午化；巳生辰→辰化；子生寅→寅化）；
- 答案 `a/actor` 取化者；引擎 `sheng` 候选 `actor=members[0]=生端=被化者`，反了；
- H09–H11 是 `mode=化用`，可只翻 `化用` 修复；H12 是 `mode=生泄用`（财→杀未被识别成化用），
  修复后仍 `reversed`，记 `known_gap`；
- 4 化算 **reversed**，不是 `pending`；不剔除、不改标 ok。

## 4. 16 条 defined 的构成

| 子集 | n | ok | 失败原因 |
|---|---:|---:|---|
| 墓（H13–H16） | 4 | 4 | 已修好 |
| 制（H01–H05/H08） | 6 | 0 | G3 支克无 ke，actor_none |
| 化（H09–H12） | 4 | 0 | engine_wrong reversed；T-181 修 H09–H11；H12 财→杀 known_gap |
| 制 no_edge（H06/H07） | 2 | 0 | G3 支克，no_edge |
| **defined16** | **16** | **4** | **4/16 = 25%** |

救应 4（H17–H20）：对称/复杂，1 ok，不进入引擎方向主分母。

## 5. 裁决

1. **不把 post-fix 当 P1 通过**；也不 kill。正式 P1 要等：
   - 化约定审计（T-180）；
   - 支克目标裁决（A/B/C）。
2. **方向主分母 = 20（v4）**；defined16（制/化/墓）只作诊断；4 化计入 reversed；
   H12 记 `known_gap`；4 救应对称，只作敏感性。不得剔除、不得改标 ok。
3. **G3 支克是 6 制 + 2 no_edge 的共同原因**；不补支克，defined16 最多 **8/16 = 50%**（墓4+化4），
   80% 目标（13/16）不可达；20 条最多 9/20（含 H17）。这与边 90% 的上限 17/20 是同一个根因。
4. **T-180 已完成**：4 化 engine_wrong；**T-181** 只翻 `mode=化用` 修 H09–H11；
   H12 不扩类。修复后推演 defined16 **7/16**、20 条 **8/20**，仍 <60%。
5. 正式 P1 等支克目标裁决（A/B/C）；不调规则、不换 hold-out、不拿 post-fix 反推。

## 6. 证据

- post-fix：`META/p1-holdout-postfix-candidates-v1.json` / `.md`
- 墓审计/规则表：`META/p1-muku-actor-audit-v1.*`、`docs/specs/actor-rules-v1.md`
- pre-fix：`META/p1-holdout-baseline-v1.*`
- 基线：1425 passed / 1 skipped；481/0；relations 全过

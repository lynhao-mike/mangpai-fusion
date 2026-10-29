# P1 post-fix 诊断裁决 v1（2026-10-29，T-179 合并后）

> 对象：`META/p1-holdout-postfix-candidates-v1.json`（`artifact=post_fix_candidates`，非正式 P1）
> 结论：候选 70%→85%、方向 5%→25%；4 墓已修好；剩余失败是 **G3 支克（6 制）** 与 **化约定（4）**，不是评分器选错。

## 0. 一句话

T-179 把候选召回从 14/20 拉到 **17/20（85%）**、方向从 1/20 拉到 **5/20（25%）**；
但 16 条“制/化/墓”里只 ok 4 条（全是墓），**6 条制仍卡在支克无 ke、4 条化卡在施力方约定**。
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

## 3. 4 条“化”是约定问题，不是数值噪声

H09–H12：
- 答案 `a` 在 `D.b/Y.b/H.b`，`b=M.b`；`actor=a`；
- 引擎 `sheng` 候选 `members=(M.b, X.b)`、`actor=M.b`（b 端）；
- 即答案把 `a` 当施力方，引擎把 `b` 当施力方——与墓同类：**先定“化者 vs 被化者”约定，再判 engine_wrong/label_wrong**。
- 在约定定稿前，这 4 条不能直接算 reversed；但也不能像 v2 那样直接剔出分母。

## 4. 16 条 defined 的构成

| 子集 | n | ok | 失败原因 |
|---|---:|---:|---|
| 墓（H13–H16） | 4 | 4 | 已修好 |
| 制（H01–H05/H08） | 6 | 0 | G3 支克无 ke，actor_none |
| 化（H09–H12） | 4 | 0 | 化约定未定，reversed |
| 制 no_edge（H06/H07） | 2 | 0 | G3 支克，no_edge |
| **defined16** | **16** | **4** | **4/16 = 25%** |

救应 4（H17–H20）：对称/复杂，1 ok，不进入引擎方向主分母。

## 5. 裁决

1. **不把 post-fix 当 P1 通过**；也不 kill。正式 P1 要等：
   - 化约定审计（T-180）；
   - 支克目标裁决（A/B/C）。
2. **方向主分母暂定 16（制/化/墓）**，但 4 化在约定定稿前不进“失败”统计，单独列 `definition_pending`；
   救应 4 只作卡层/敏感性。
3. **G3 支克是 6 制 + 2 no_edge 的共同原因**；不补支克，16 条里最多 10/16（墓4+化4+?），
   80% 目标（13/16）不可达。这与 20 条边 90% 的上限 17/20 是同一个根因。
4. **T-180 化审计**（只读）先行；它决定 4 条是 engine_wrong、label_wrong 还是 convention；
   定稿后再重冻方向口径（v4/v5），然后才跑正式 P1。
5. 不调规则、不换 hold-out、不拿 post-fix 反推。

## 6. 证据

- post-fix：`META/p1-holdout-postfix-candidates-v1.json` / `.md`
- 墓审计/规则表：`META/p1-muku-actor-audit-v1.*`、`docs/specs/actor-rules-v1.md`
- pre-fix：`META/p1-holdout-baseline-v1.*`
- 基线：1425 passed / 1 skipped；481/0；relations 全过

# T-183 STATUS

- 状态：✅ **已验收 / 已合并**（2026-10-29 15:40，中枢）
- 执行者：子代理 AG
- 任务卡：`tasks/T-183/PROMPT.md`
- 验收：中枢亲自跑；只修固定五行 + E-08
- 分支/commit：`p1/fixed5`（worktree `..\mangpai-fusion-fixed5`）@ 代码 `79367f1d`；
  BRIEF / STATUS / `META/p1-dev20-veto-v1.json` 在 `94ae564f`

## Execution Log

| 时间 | 动作 |
|---|---|
| 14:50 | 中枢建卡并派发；与 T-184/T-185 并行 |
| 14:52 | 读卡 + `structure_check.py`(411–539) + `relation_graph.py`(ke/wuhe) + `p1_holdout_eval.py` + 裁决文档；建 worktree `..\mangpai-fusion-fixed5`，分支 `p1/fixed5` 从 `f230e5b2` 起 |
| 15:00 | 实现 `_derived_zhi_ke` / `_derived_gan_ke_zhi` + 同对 ke 优先 wuhe；H03(ke e002 actor=丙) / H06(午克酉) / H07(戊克子) 事实层 actor 实测正确 |
| 15:05 | 上报 15KB 冲突（15,452 B > 15,000，仅剩 196 B 余量）与评分器 kind 可见性；中枢授权：facade 默认视图压缩 + kind 通用别名 |
| 15:12 | facade 削 `candidates[].tiyong`（14,654 B）；`CAND_KIND_ALIASES`（zhi_ke/gan_ke_zhi→ke，仅克）；E-08（默认不写 / 已存在拒绝 / `--force`）落地 |
| 15:18 | 全量 `pytest -q`：1443 passed / 1 skipped；`engine_audit` 481/0；`relations_audit` 全部通过；`verify_baseline --compare` 基线未退步 |
| 15:22 | dev-20 否决一次（`--artifact-label dev20_veto`）：方向 9/20 → 13/20（H01/H06/H07/H19 转 ok），既有 ok 无丢失，H03 仍 actor_none |
| 15:35 | 提交代码 `79367f1d`；写 BRIEF / STATUS |
| 15:40 | 中枢合并 `p1/fixed5`（STATUS add/add 冲突已解）；主仓 `verify_baseline` 1456/1、481/0、relations 全过；15KB 14,654；dev-20 13/20 只作否决；B3 知悉 |

## Blockers

| 编号 | 状态 | 内容 |
|---|---|---|
| B1 | ✅ 已裁决 | 15KB 测试盘与「所有柱对」不可兼得；中枢选 (a) facade 压缩：默认视图削 `candidates[].tiyong`，14,654 B，guard 断言未改。 |
| B2 | ✅ 已裁决 | `zhi_ke`/`gan_ke_zhi` 不在冻结候选 kind 映射里；中枢授权通用别名（归一 `ke`，只影响「克」），已落地并加测试。 |
| B3 | ⚠️ 残留（中枢知悉） | H03 仍 `actor_none`：冻结映射 `合 → {wuhe, liuhe}`，评分器不会匹配同一对上的 `ke` 候选；H04（合）、H05/H08（冲）同理。事实层已修（ke 排前 + actor=克方）。官方系统级评分器吃断言，不吃 candidate kind；dev-20 只作否决，B3 不阻塞 fresh-40。 |

## 备注

- 未跑官方 P1 / fresh-40；未改 hold-out/answers/分母；未 push main；未碰其他 worktree。
- 未做党势/比值/权重/浮点；未为 H02/H05 写冲穿方向；引擎不判穿制。

# T-179 BRIEF · 候选生成修复 v1（体-体/双属 + 同柱/邻柱生 + 墓向）

- 分支：`p1/candidates`（worktree `..\mangpai-fusion-p1cand`，基于 `edd79fec`）
- commit：`4bf238e7`（1 commit，4 files，+158/−29；未 push）
- 说明：执行期间 main 前进到 `44a01631`（docs/META），按卡仍以 `edd79fec` 为基；未 rebase。

## 1. 改动文件

| 文件 | 改动 |
|---|---|
| `engine/facts/structure_check.py` | ① 删 `_crosses` 的 4 处过滤（edges / `_derived_sheng` / `_derived_canggan_ke` / muku），体-体、双属-双属不再丢；② 新 `_derived_sheng_adjacent` + `mode="sheng"` 候选（同柱/相邻柱，`actor=生者`、`members[1]=被生者`，跨柱 >1 不新增）；③ 墓用候选改 `members=(库,入库方)`、`actor=库`（`结构层 relations.muku` 不动）；`mode` Literal 扩 `"sheng"`。不补 880 支克边、不改 `relations.edges`/排盘/边 ID/condition_ir。 |
| `engine/api/facade.py` | C（中枢 13:15 授权）：`compact_for_agent` 只压默认视图——削 `candidates.ten_gods`（可由 chart 地址还原）、`edges.layer/scope/distance`（由 members 还原）、`chart.pillars[].stem/branch.wuxing/yinyang`（由 char 还原）。全量视图（`analyze_facts`/`--full`）不变。 |
| `tests/facts/test_structure_check.py` | 2 条旧过滤断言按授权改反向契约（ADR-007 D1 被 T-179 取代）；新增 6 条测试（见 §2）。 |
| `tests/api/test_facade_zuogong_fields.py` | 同步 C 的投影：断言新削字段 + 验证 `ten_gods` 可由 chart 还原；**不是放宽**（比原断言多验还原路径）。 |

契约变更（diff 可见，BRIEF 单列）：
1. `test_zuogong_only_crosses_ti_yong` → `test_zuogong_includes_body_body_t179`（同一组 2 个参数，断言体-体进入候选）。
2. `test_zuogong_excludes_dual_x_dual` → `test_zuogong_includes_dual_dual_t179`。
3. `test_compact_for_agent_drops_only_restorable_fields` 更新为新投影（C 授权范围内的测试同步）。

## 2. 原始输出

### 2.1 测试/回放（worktree `..\mangpai-fusion-p1cand`）

```text
python -m pytest -q
1425 passed, 1 skipped, 1 warning in 127.10s (0:02:07)
# 基线（未改）：1420 passed, 1 skipped in 139.15s；+5 例 = 新增测试

python -m tools.engine_audit
案例 481；有问题 0；问题种类 0；口径说明 32
exit=0   # 481/0

python -m tools.relations_audit
缺边/假边/重复边：无；三合 515/515 = 100%、三会 495/495 = 100%
结论: 全部通过
exit=0

python -m tools.zuogong_probe
盘数 481；有宫制星候选 481 (100.0%)；actor=D.b 374 (77.8%)
exit=0   # verify_baseline 旧记录为 477，无下降
```

### 2.2 候选统计（382 盘 = `META/timing-eval-set-v1.json` `usable_for_timing`）

| 指标 | 改前 | 改后 | 变化 |
|---|---:|---:|---:|
| candidates 总数 | 5,685 | **9,941** | +4,256（**1.75×**，<2×） |
| `mode="sheng"` | 0 | **2,435** | 新增（占 24.5%） |
| `relation_kind=sheng`（含 `sheng(main_qi)`） | 1,403 | 4,870 | +3,467 |
| 体-体候选 | 0 | **1,739** | 新增 |
| 双属-双属候选 | 0 | **89** | 新增 |
| 体-体 或 双属-双属 | 0 | 1,828 | 新增 |
| `actor` 非空 | 4,443 | 8,396 | +3,953 |
| 远距离 sheng（distance>1） | 527 | **898** | +371；占总量 **9.0%** |
| 其中 `mode="sheng"` 远距离 | 0 | **0** | 跨柱不生成 ✅ |
| 单盘最大候选 | 25 | 36 | +11 |

按 mode：制用 3,179→3,788（+609）；化用 342→342（0）；生泄用 1,061→2,093（+1,032）；合用 719→762（+43）；墓用 384→521（+137）；sheng 0→2,435。
说明：同柱/邻支的 sheng 会与既有 `sheng(main_qi)`/天干 `sheng` 边**各留一条**（mode 不同：`化用`/`生泄用` vs `sheng`），这是 §1.1「保留现有 mode 语义」+ §1.2 新增的直接结果，是本轮候选增长的主因。

### 2.3 C1/C2/C3（T-169 三盘）

| 盘 | 候选 改前→改后 | mode=sheng | 体-体 | 夫妻宫（D.b）边不在候选：改前→改后 |
|---|---:|---:|---:|---|
| C1 `RF-2026-000125` 丁卯 壬子 辛丑 乙未 | 17 → **30** | 7 | 6 | `e013,e015,e016` → `e013`（e015 chong、e016 xing 两端皆体，按①进入；e013 sanhui kind 不在清单） |
| C2 `RF-2026-000438` 庚午 戊寅 己未 乙丑 | 13 → **23** | 3 | 8 | `e009,e010,e013,e014` → `e010`（e009 liuhe、e013 chong、e014 xing 进入；e010 sanhui kind 不在清单） |
| C3 `RF-2026-000894` 壬戌 己酉 庚子 戊子 | 8 → **22** | 8 | 10 | `e009` → `e009`（po 不在 `_ZHI_KINDS`，本卡不改 kind 清单） |

### 2.4 默认视图字节（15KB 护栏，C 的验收）

```text
测试盘 庚申 戊寅 壬子 辛丑（engine.cli all 默认视图）
改前            14,863 B / 16 候选
改后未压缩      16,428 B / 27 候选
C 压缩后        14,802 B / 27 候选   < 15,000 ✅（尺寸断言未改）

382 盘默认视图：max 21,500 → 21,298 B；median 15,453 → 15,423 B；>15KB 盘 257 → 242
岁运快照（DY3+2026，同盘）：21,006 → 20,016 B；候选 31 → 45
```

保留字段：`edge_id`、`mode`、`actor`、`members`（`members[1]`=target）、`tiyong`；另保留 `relation_kind`、`chart` 的 addr/char/十神。全量视图逐字段未动。

### 2.5 性能

- 382 盘 `analyze_facts + compact_for_agent` 循环：21.0s → 19.7s（噪声内，无退化）。
- 全量 pytest：139.15s → 127.10s（<2×）。
- 单盘 CLI 冷启动正常；候选生成仍是纯 Python 组合（同柱/邻柱 20 对上限）。

## 3. 未完成与风险

1. **契约变更 3 条测试**（§1）：2 条是中枢授权的反向契约，1 条是 C 的投影同步；均在 diff 可见，非放宽/删除/skip。
2. **候选爆炸**：总量 1.75×（阈值内），但 `mode="sheng"` 与既有 `sheng(main_qi)`/天干 sheng **同一关系双候选**（`化用/生泄用` + `sheng`）。若下游按「候选=关系」去重，会重复计数；是否合并留待中枢裁决（本轮按卡保留既有 mode 语义）。
3. **15KB 是测试盘护栏，不是全盘保证**：382 盘改前中位数已 15.4KB、257/382 超 15KB；C 压缩后 242/382 超（整体变小），快照仍 ~20KB。若产品要求全盘 <15KB，需要另立预算/裁剪任务。
4. **远距离 sheng**：527→898 条（占总量 9.0%），全部是既有 `_derived_sheng` 的 `sheng(main_qi)` 分支，按裁决不删；新增 `mode="sheng"` 远距离为 0。它们是 ①去过滤的直接结果，不是 ②扩距离。
5. **排序变化**：新 `mode="sheng"` 块插在 `_derived_sheng` 之后、`canggan_ke`/`muku` 之前，候选索引会变（edge_id/relations.edges 不变）；依赖候选下标的临时脚本需重跑。
6. **墓向变更**：按 T-178 审计 4/4 `engine_wrong` 改为 库→入库方；`relations.muku` 事实层（谁可入墓、是否 excluded）未动。**H13 仍 no_candidate**（体-体过滤在方向修复外，本轮只改候选生成；H13 的边是墓非边）。
7. **未跑 hold-out**；评分器合成 fixture 仍是旧墓向约定（中枢已知，待合并后更新；真实评分不受影响）。
8. `mode="sheng"` 消费者已查：`atoms.zuogong(kind=...)` 按 mode 等值过滤（新值不会被旧规则误命中，无 else 静默吞）；`address_level_evidence_audit` 按 Counter/`=="制用"` 分支；`p1_holdout_eval` 不用 mode；`facade._compact_zuogong` 透传。无未覆盖的 mode 分支。
9. 分支基于 `edd79fec`，未包含 main 的 T-178 文档（`docs/specs/actor-rules-v1.md` 等）；合并时需先并入 main 的 docs/META。

## 4. 下游须知

1. **合并顺序**：`p1/candidates` → main（T-178 docs 已在 main，无代码冲突）；**不要 push main**，由中枢合并后一次性跑 hold-out。
2. **T-178 接口**：墓用候选现在 `members=(库,入库方)`、`actor=库`。P1-H14–H16 若命中墓用候选，方向将从 `reversed` 变 `ok`；**P1-H13 仍 `no_candidate`**（体-体过滤之外的「墓不是边」口径），不要把它当 actor 修复失败。
3. **`mode="sheng"` 新枚举值**：`ZuogongCandidate.mode` Literal 已扩；没有 `target` 字段，**target 一律取 `members[1]`**（`actor=members[0]`）。下游若对 mode 做穷举映射，需加 `sheng` 分支。
4. **默认视图还原**：`candidates.ten_gods` ← `chart.pillars[].stem.ten_god` / `branch.main_ten_god`（D.s=日主）；`edges.layer/scope/distance` ← members 的地址前缀/后缀与柱序；`chart.pillars[].stem/branch.wuxing/yinyang` ← char 查表。需要原件用 `engine.cli all --full`。
5. **关系图未动**：`relations.edges` 边数/ID/kind/members 与改前逐字节一致；880 支克边仍 0；支克候选仍 0（测试覆盖）。
6. **复现命令**（worktree 内）：
   ```text
   .venv\Scripts\python.exe -m pytest -q      # 注：worktree 用主仓 .venv
   .venv\Scripts\python.exe -m tools.engine_audit
   .venv\Scripts\python.exe -m tools.relations_audit
   .venv\Scripts\python.exe -m tools.zuogong_probe
   .venv\Scripts\python.exe -m engine.cli all --pillars "庚申 戊寅 壬子 辛丑" --gender 乾 --json
   ```

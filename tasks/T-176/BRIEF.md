# T-176 BRIEF

- 任务卡：`tasks/T-176/PROMPT.md`
- 状态：已完成（三张卡 + 机器 JSON）；**pre-P1 能力展示，不是 P1 验证**
- 执行者：子代理 Z；完成时间 2026-10-29 12:15

---

## 1. 改动文件

| 文件 | 动作 | 说明 |
|---|---|---|
| `docs/demo/single-chart-cards-v1.md` | **新建** | 三张人读卡（五元组块）+ 盘面事实表 + 不能说什么 + 自检表 + 偏差自曝 + 复现命令，209 行 |
| `META/single-chart-cards-v1.json` | **新建** | 三张机器卡（`cards[]`，字段按规格 §3.2），含 `summary` 与 `known_schema_deviations` |
| `tasks/T-176/BRIEF.md` | **新建** | 本文件 |
| `tasks/T-176/STATUS.md` | **追加** | Execution Log 一行 |

未改：`engine/**`、规则 YAML、`tests/**`、`META/single-chart-cases-v1.json`、`docs/specs/**`。未做任何 git 写操作。临时探针脚本/JSON（`.tmp-*`）已删。

## 2. 原始输出

### 2.1 回归现状（未新增代码）

```
.venv\Scripts\python.exe -m pytest -q
... 1374 passed, 1 skipped, 1 warning in 135.87s (0:02:15)
```

0 failed；1 skipped 是 `tests/tools/test_bundle_pii.py` 的 T-114 过渡 skip（AGENTS.md 已记录）。

### 2.2 三张卡（卡 / 盘 / 边 / 方向）

| 卡 | case_id | chart_id（`--birth` 口径） | ① 地址（十神） | ② direction | direction_known | actor/target | ③ state | 救应 | ⑤ edge id | ⑤ 原文 |
|---|---|---|---|---|---|---|---|---|---|---|
| C1-01 | RF-2026-000125 | cf-5735e1472538ad92664b | D.b 偏印 + H.b 偏印 | 冲 | **false** | null / null | 破局 | 未判 | e015 chong、e016 xing | M1-D-298 `sources/duan/MinerU_markdown_婚姻专辑_2056044010230448128.md:48` |
| C2-01 | RF-2026-000438 | cf-f10b5515f2019638f42f | D.b 比肩 + H.b 比肩 | 冲 | **false** | null / null | 破局 | 未判 | e013 chong、e014 xing | M1-D-298 `…:48` |
| C3-01 | RF-2026-000894 | cf-8b541a506fc413884431 | M.b 劫财 + D.b 伤官 | 破 | **false** | null / null | 破局 | 未判 | e009 po | M1-D-300 `…:122` |

- **direction_known 计数：false 3 / true 0。** 原因不是写法，是 G2（冲/刑/穿/破 `actor=None`）。
- 每卡地址数：2 / 2 / 2；每卡边数：2 / 2 / 1（合计引用 5 条边：e015、e016、e013、e014、e009）。
- `rescue_judged=未判` 3/3；`pre_p1: true` 3/3；`snapshot.dayun_index/liunian_year` 全 null（原局快照）。
- `unknowns`：C1 `G2/G5/muku_open_close/suiyun_ten_god`；C2 同；C3 `G2/G5/no_spouse_star/boundary_zi_shi/suiyun_ten_god`。

### 2.3 逐卡回查（engine.cli 实测，非引用案例 JSON）

- C1 `--pillars "丁卯 壬子 辛丑 乙未" --gender 乾`：16 边；`e015 chong[D.b,H.b]`、`e016 xing[D.b,H.b] group=丑戌未 completeness=partial`；`tiyong D.b=体 H.b=体`；`D.b` 夫妻宫 4 边（e012 liuhe / e013 sanhui / e015 / e016），e013/e015/e016 不在 candidates。
- C2 `--pillars "庚午 戊寅 己未 乙丑" --gender 坤`：14 边；`e013 chong[D.b,H.b]`、`e014 xing[D.b,H.b] 丑戌未/partial`；`D.b=体 H.b=体`；夫妻宫 4 边全部不在 candidates。
- C3 `--pillars "壬戌 己酉 庚子 戊子" --gender 乾`：12 边；`e009 po[M.b,D.b]` 是 `D.b` 唯一关系边；`M.b=体 D.b=双属`；全盘无冲边、无六合边、无财星；`variants[zi_shi].alt_chart_id=cf-62995823c069f1deacba`。
- 边界回查：三盘原局快照 16/14/12 条边**全部 `scope=natal`**，DY/LN 边 0 条。
- 岁运回查（只写进 boundary，不产卡）：C1 DY5+2026 → 39 边，夫妻宫冲/刑变 `e031/e032`；C2 DY4+2026 → 39 边，变 `e028/e029`；C3 DY4+2026 → 34 边，`e009`→`e022`。
- 锚点回查：`:48` 原文=「夫妻宫位要安静，如有用，不能被刑坏，冲破，穿倒，或六合，暗合他星（配偶星以外的星），也不宜杂透，多现。」；`:122` 原文=「夫妻宫位有用，却被刑、冲、破、穿、或六合，暗合他星（配偶以外的星），或杂透，多现。」（`M1-D-300` 的 `raw_anchor` 记在 `:124`，`:124` 讲破坏程度/离异，本卡不引）。
- 机器自检（临时脚本，已删）：逐卡比对 chart_id / 四柱 / 十神 / tiyong / edge kind+members+group+completeness / basis / statement 地址 / 锚点原文行 / scene 禁词表 / unknowns ID 合法性 / snapshot 三字段 / pre_p1 → `ALL CHECKS PASS`。人读卡与机器卡的 `scene`/`statement`/`holds_when`/`fails_when` 逐字一致（已比对）。

### 2.4 chart_id 口径（重要）

`chart_id` 由输入形态派生：`--birth` 得卡里登记的 3 个 id；`--pillars` 得 `cf-ada5459163b88f49505e` / `cf-f835f14ca5091eec536d` / `cf-48de88b1324fbde0476f`，但**边号、kind/members、tiyong 完全一致**（三盘逐项比对过）。核对边号两种输入皆可，核对 chart_id 必须用 `--birth`。

## 3. 未完成与风险

1. **`scene_refs` 为空（规格 §2.4 要求 ≥2 张同 case_id 的卡）**：T-176 是一盘一卡，同盘没有第 2 张卡可引。按 §2.4 字面这三张卡不合格；L20/L21 不会命中，但「≥2」门槛未达。补卡会超出「3 张卡」范围，故未补。
2. **一盘一卡 ⇒ 单盘报告过不了 §5.3**（≥3 张通过 Linter 的关系型卡）。若 P1 走一盘一卡，§5.3 必须先改口径。
3. **§9.13 未决（最大风险）**：C1/C2 的「破局」只有 `edge` 依据 + 原文判据，没有 `structure_item`（婚姻域无结构项，G5）。若外部审计否掉这条路径，C1/C2 只能降级为假设（三态无第四种）。
4. **§9.5 未决**：C3 的判据是 `po`，`M1-D-143` 明确「破」不并入四类制法；且 §2.3 的破局判据文字只列冲/刑/穿，而 `basis.assert` 枚举含「目标受破」。本卡从枚举，需拍板。
5. **§2.4 与 §3.4 示例口径冲突**：原局快照无引动边，本卡按 §2.4 写 `none_observed` + 边数证据；示例卡用的是通配 `LN{year}.b`。两者需统一。
6. **C1/C2 共用 `M1-D-298:48`**：两盘结构同为夫妻宫冲+刑，锚点相同是事实，但不构成锚点独立性的证明。
7. **C3 的 `confidence=低`**：四柱不唯一（`boundary_zi_shi`）+ 夫妻宫只有一条 `po` 边 + `po` 是否算做功待审。
8. **未做的事**：没有跑 Linter（规格 §4.3 明确本版不实现）；没有用 `tools/query_theory` 复核锚点（直接读 `theory/duan/index.yaml` 的 `raw_file`+`raw_anchor` 再读原文行，路径更短且可回查）；没有写岁运卡（任务固定原局快照）。

## 4. 下游须知（P1 修复后应重跑哪些卡）

| 触发条件（P1 修复项） | 应重跑的卡 | 为什么 |
|---|---|---|
| **G2 修复**：冲/刑/穿/破 有 `actor`/`target` | **C1-01 / C2-01**（`e015`/`e016`、`e013`/`e014`） | 三张卡的 `direction_known` 会从 false 变 true，`t2` 与 `statement` 的「方向未定」句必须改写；`confidence` 可上调 |
| **§9.13 裁决**（edge-only 破局是否成立） | **C1-01 / C2-01**，连带 **C3-01** | 若不成立，C1/C2 降级为假设；C3 的 `目标受破` 也受同一条约束 |
| **§9.5 裁决**（`po` 是否算做功/是否可作破局依据） | **C3-01** | 现卡把 `e009 po` 当唯一依据 |
| **§9.6 无配偶星口径**（宫位代星是否允许） | **C3-01** | 现卡只能写「无配偶星地址」，若允许宫位代星，`t1/t4` 需补 |
| **`boundary_zi_shi` 处理口径**（是否必须并列 alt chart） | **C3-01** | 现卡只在 `boundary` 声明口径；若要求并列 `alt_chart_id` 的卡，需另出一张 |
| **`scene_refs` / 卡数口径**（每盘 ≥2 卡 or 改 §2.4/§5.3） | **三张全重跑** | 卡的 `scene_refs`、报告级门槛都变 |
| **引动口径统一**（§2.4 `none_observed` vs §3.4 通配） | **三张全重跑** | `activation` 字段写法会变 |
| **G5 救应原语落地** | **三张全重跑** | `rescue_judged` 可从「未判」变「已判」，三态可能变化 |

**给中枢的核对建议**：先跑 §2.3 的三条 `--pillars` 命令核边号，再跑 `--birth` 命令核 chart_id，最后读 `docs/demo/single-chart-cards-v1.md` §4 自检表逐行对。机器卡可直接 `json.load` 后按 §3.2 字段表逐项查。

# Golden-20 覆盖裁决 v1（2026-10-29，中枢）

> 对象：`META/golden-20-v1.json` / `META/golden-20-answers-v1.json`（T-170）
> 结论：**接受为「段派单派 golden-20 v1」，不是跨派金标。**

## 0. 一句话

20 例全部来自 `sources/duan/`，四类 6/4/5/5，137 条原文锚点逐字命中，盲测/答案物理分离；
**但跨派样本 = 0、化用只有 2/4 有原书应期、答案 `struct_refs` 全是 `book_text_only`（未绑引擎边）**。
所以它只能证明「段派教材例题的推演复原」，不能证明「四派融合」，也不能当「已绑定结构」金标。

## 1. 已验证

| 项 | 结果 |
|---|---|
| 例数 | **20 / 20** |
| 学校 | **duan 20 / yang 0 / ren 0 / ziping 0** |
| 四类 | 制用 6 / 化用 4 / 墓用 5 / 救应 5（均 ≥3，但化用应期见 §2） |
| 原文锚点 | **137 条**，逐字命中源文件行 |
| 盲测输入 | 仅 8 键：`case_id/school/four_pillars/gender/dayun_start_age/dayun_direction/dayun/source` |
| 答案泄漏 | 0（`original_analysis/core_work/adjudication/rescue/timing` 不在 blind 文本） |
| 快照 | 20/20 有 `chart_snapshot{chart_id, dayun_index:null, liunian_year:null}` |
| 结构引用 | `struct_refs.status` **全部 `book_text_only`**；`edge_ids`/`candidate_ids` 全空 |
| 测试 | `test_golden_20_schema.py` 7 passed；全量 1365 passed / 1 skipped |
| 四柱抽查 | G20-001/007/013/016/019 五例 `engine.cli all` rc=0，回读逐字一致 |

## 2. 三个代表性缺口（不许藏）

1. **跨派样本 = 0**：杨派/任派教材命例普遍不列大运干支表；按「每例必须有大运序列」的硬标准，
   当前语料产不出合规的跨派样本。**「四派融合」这个产品主张，本集完全没测。**
2. **化用应期不足**：4 例化用里只有 007/008 有原书大运吉凶；009（毛泽东造）、010（木匠造）原书只给结构判断。
   按「必须含应期」严卡，化用 = 2，未达 3 例线；原书自述「这种结构比较少」。
3. **未做结构绑定**：答案的 `struct_refs` 是 `book_text_only`，不是 `engine` 边。
   若把它当「已绑定结构」金标使用，会高估覆盖；评估时必须只拿它当**原书文本答案**。

另：18/20 起运年龄 null（原书未给）；G20-013 原书两套读法并存（已标弱对照）；
G20-014 OCR「屈」按正文自证复原为「辰」；G20-016「戍」=「戌」，引用保留原字。

## 3. 裁决

1. **接受为 `golden-20-duan-v1`**；文件名保留，文档与报告必须标 `duan-only`。
2. **75%/60% 门槛只对段派这 20 例成立**；不得外推为「四派融合已复原」。
3. **应期判据的保守口径**：3 例 `timing=null` 不能在全四标准上通过；
   主门槛按 **15/20**（缺应期按 fail 计），另报「17 例有原书应期」的次级通过率。
4. **`book_text_only` 不是「已绑定」**：评估器的「零幻觉」只查系统输出的地址/边是否回 `engine.cli`；
   不得要求答案侧有 edge id，也不得把答案的文本结构当引擎边。
5. **跨派主张另立卡**：若产品要声称「四派融合」，必须再做一套 **跨派 natal-only** 集
   （只测①–③：原局象/体用宾主/成败救应，不测应期），从 yang/ren/ziping 有出生时间或四柱的命例中选；
   没有这套，任何跨派结论都是超范围。

## 4. 对第一证明点的影响

- 可以继续用这套做 **段派盲推**：系统输出 vs 原书 `core_work/adjudication/rescue/timing`；
  四条硬标准里，「零幻觉」查系统自身地址，「主功/成败/应期」查原书文本。
- 不能把它当「全产品金标」；跨派、化用应期、结构绑定三项缺口必须在报告里逐条列出。
- 如果独立 Agent 认为「duan-only 不足以作为第一证明点」，则先补跨派 natal-only 集，再跑盲推；
  不要用这套的结果宣布整个产品通过。

## 5. 证据

- 盲测输入/答案：`META/golden-20-v1.json`、`META/golden-20-answers-v1.json`
- 清单/缺口：`META/golden-20-v1.md`
- 门禁：`tests/tools/test_golden_20_schema.py`（7 passed）
- 卡：`tasks/T-170/PROMPT.md`（§9 已并入 T-169 的 snapshot/candidate 约束）

# T-175 BRIEF · P1 hold-out 独立策展

## 1. 改动文件

| 文件 | 类型 | 说明 |
|---|---|---|
| `META/p1-holdout-v1.json` | 新建 | 盲测输入；20 例；只含 `case_id` / `four_pillars` / `gender` / `source` |
| `META/p1-holdout-answers-v1.json` | 新建 | 答案；20 条 `core_work_relations`；`a`/`b`/`kind`/`mechanism`/`actor`/`quote`/`source_ref` |
| `META/p1-holdout-v1.md` | 新建 | 清单 / 四类 / 非名人 / 非 dev / actor 支撑 / 缺口 / 评分口径 / 冻结哈希 |
| `tests/tools/test_p1_holdout_schema.py` | 新建（可选） | 7 项 schema/分离/非 dev/quote 逐字检查 |
| `tasks/T-175/BRIEF.md` | 新建 | 本简报 |
| `tasks/T-175/STATUS.md` | 追加 | Execution Log 一行 |

未改 `sources/`、`theory/`、`engine/`、规则、既有测试；未做 git 写操作。

## 2. 原始输出

```text
$ .venv\Scripts\python.exe -m pytest tests\tools\test_p1_holdout_schema.py -q -o addopts="-ra --tb=short"
.......                                                                  [100%]
7 passed in 0.13s
```

```text
case_count = 20
categories = 制 8 / 化 4 / 墓 4 / 救应 4
non-famous = 20/20（chart→quote 区间 18 个排除词命中 0）
non-dev = 20/20（四柱交集 0；source 行区间无重叠；内部重复 0）
hold-out 是否 <15 = 否（20 ≥ 15）；不适用例数不足条款，P1 可裁决
determinism = 重跑生成脚本 2 次，两个 JSON 的 SHA-256 完全一致；schema 测试多次运行均 7 passed
```

```text
blind    SHA-256 = 593f4dbea76a4959550c326eea31a8d9feae895cb9272028813982de96bbf045
answers  SHA-256 = b1075a394dc1954f27e7de1b06b38283174223e223e3d6b17993723bef37762f
dev 四柱集合 SHA-256 = 7128998489d45128efae0ad63cf8a71d6f8c30299d2acd6f4557510d5b145df4
holdout 四柱集合 SHA-256 = d8139e0d09749ded55672ec936097d1c22408dd3e72685a0266f612f56e732a3
```

来源分布：F22 10 例；F23 4 例；F19 2 例；F28 4 例。

## 3. 未完成与风险

1. **救应 4 例来源口径**：P1-H17～H20 全部来自《命理指要》（段建业早期传统子平著作，F28），不是盲派核心讲义。盲派核心原文极少用「救应」一词。若中枢只认盲派核心教材，这 4 例不合格；届时剩 16 例（仍 ≥15），但四类缺救应。**需要中枢裁定**：接受 F28 按 `mechanism` 评分，或另派 Agent 补盲派核心救应例替换。
2. **性别缺口**：H17/H18 原文未标，盲测写 `未注明`；H19/H20 按「县宰/侍郎」推定为乾（`gender_basis=inferred_from_occupation`）。P1 方向召回不依赖性别；大运相关指标需排除这 4 例或另定性别。
3. **每例只 1 条关系**：P1 分母 20 条，不是完整边集。不要拿 20 条冒充 33 条分母；若要测同例多关系，需重标并重算哈希。
4. **OCR**：quote 保留原文空格/错字（H18「已火」、H20 截断句）；a/b 已规范化。抽查请在 `source_ref` 行内检索，不要跨行拼接。
5. **非名人是启发式**：保留「副处/经理/厂长/县宰/侍郎/亿万富翁」等职业/财富描述；无人名、无中堂/首相/皇帝/名人/阎命标签。若口径更严需替换。
6. **来源集中度**：10/20 来自 F22；不影响正确性，但 P2 建议换一批书重策展。
7. **未写判定脚本/阈值 JSON**：按任务卡只交 3 个产物；阈值与匹配口径写在 MD §7.2，判定脚本留给 P1 评分任务。没有越权改 `tools/` 或 `engine/`。

## 4. 下游须知

- P1 评分输入：`META/p1-holdout-v1.json`；答案：`META/p1-holdout-answers-v1.json`。评分侧不得把答案文件喂给 engine 或分析 Agent。
- 方向召回：每条 `(a,b)` 是否命中且 `actor == a`；边召回：是否命中 `{a,b}`。分母均为 20。
- 救应类按 `mechanism` 匹配（制/化/冲/克/合），不要要求 engine 有 `kind=救应` 的边。
- 阈值（verdict §2.4）：方向 ≥80% 且边 ≥90% 才允许 golden-20 盲推；方向 <60% 进 kill；60–80% 只做局部修。
- 一次评分：先冻结两个 JSON 的 SHA-256；评分时不得换例、改 quote、改 `a`/`b`/`actor`、改阈值。
- 中枢抽查建议：随机抽 5 例，按 `source_ref` 打开原书行，核对 quote 逐字与 actor；重点看 H02（羊刃=酉）、H06（午火财制印）、H13/H14（墓库方向）、H18/H20（救应与截断 quote）。

# 五案反馈闭环补救清单（2026-06-11）

## 结论

本次补救判断：五个 RF 正式案例已经完成案例入库与摄入入口调用，但尚未完成有效反馈学习闭环。根因不是报告缺少规则依据，而是报告中的规则依据没有落入可被摄入器消费的结构化反馈位。

当前可安全自动补救的范围仅限两类：

1. 为案例目录新增旁路规则映射文件 [statement_rule_map.json](cases/C-2026-RF000345-乾-癸酉乙丑乙卯乙酉/statement_index.json:1) 的同名协议文件，即每案目录下的 `statement_rule_map.json`。
2. 在 [feedback.md](cases/C-2026-RF000345-乾-癸酉乙丑乙卯乙酉/feedback.md:1) 中追加“待人工标注”的断语反馈位。

不可自动补救的范围：不得自动填写 `[y]` 或 `[n]`。命中/失验必须由命理师或人工复核依据已知事实裁决后填写。

## 工具约束

- [tools.feedback_ingest.ingest()](tools/feedback_ingest.py:659) 会读取案例目录下的 [feedback.md](cases/C-2026-RF000345-乾-癸酉乙丑乙卯乙酉/feedback.md:1)，解析 `[S-...] [y/n/?/skip]` 标注。
- [tools.feedback_ingest.ingest()](tools/feedback_ingest.py:706) 会读取案例目录下的 [statement_index.json](cases/C-2026-RF000345-乾-癸酉乙丑乙卯乙酉/statement_index.json:1)。
- [tools.feedback_ingest.ingest()](tools/feedback_ingest.py:707) 会读取案例目录下的 `statement_rule_map.json`，并通过 [tools.feedback_ingest._merge_statement_rule_map()](tools/feedback_ingest.py:169) 合并规则映射。
- [tools.feedback_ingest.fanout_to_rules()](tools/feedback_ingest.py:235) 只有在断语反馈位能匹配索引且存在 `rule_ids` 时，才会形成规则级更新。
- [tools.feedback_ingest.fanout_to_parallel_feedback()](tools/feedback_ingest.py:301) 只有在索引提供 `reading_ids` / `adjudication_id` 等字段时，才会写入专家域与裁决准确率反馈日志；五案当前索引不具备这些字段。

## 当前断点

五案 [statement_index.json](cases/C-2026-RF000345-乾-癸酉乙丑乙卯乙酉/statement_index.json:1) 均为迁移事实索引，字段形态一致：

- `status` 为 `observed_fact`，例如 [C-2026-RF000345 的首条事实](cases/C-2026-RF000345-乾-癸酉乙丑乙卯乙酉/statement_index.json:9)。
- `rule_ids` 为空，例如 [C-2026-RF000345 的首条事实](cases/C-2026-RF000345-乾-癸酉乙丑乙卯乙酉/statement_index.json:11)。
- [feedback.md](cases/C-2026-RF000345-乾-癸酉乙丑乙卯乙酉/feedback.md:1) 只有占位提示，没有已标注的 `[S-...] [y/n/?/skip]` 行。

因此此前摄入结果表现为：

- `feedback_count = 0`
- `rule_count = 0`
- `iteration_triggered = false`
- 规则、应期、专家权重均未发生实际更新

## 可自动生成的补救材料

### 1. 旁路规则映射

每案可新增一个 `statement_rule_map.json`，建议只映射高置信、报告中明确列出规则依据且能对应已知事实年份/事项的断语。推荐格式：

```json
{
  "statements": {
    "S-RF000345-7304d7": {
      "rule_ids": ["MR-LAYER1", "MR-LAYER2", "MR-LAYER3", "M3-R-031.6"],
      "section": "报告应期判断：2023 事业/婚姻/健康复合应期",
      "year": 2023
    }
  }
}
```

该文件只提供“断语到规则”的结构化追溯，不表达命中或失验。

### 2. 待人工标注反馈位

每案可在 [feedback.md](cases/C-2026-RF000345-乾-癸酉乙丑乙卯乙酉/feedback.md:1) 追加如下类型行：

```md
- 反馈：[S-RF000345-7304d7] [ ] 2023：报告断语与已知事实待人工核验
```

但现有 [tools.feedback_ingest.parse_statement_feedback()](tools/feedback_ingest.py:136) 只解析 `[y]`、`[n]`、`[?]`、`[skip]`，所以 `[ ]` 只是人工待办，不会被摄入。人工复核后必须改为 `[y]`、`[n]`、`[?]` 或 `[skip]`。

## 五案候选补救点

### C-2026-RF000345

案例目录：[cases/C-2026-RF000345-乾-癸酉乙丑乙卯乙酉](cases/C-2026-RF000345-乾-癸酉乙丑乙卯乙酉/statement_index.json:1)

可映射候选：

- 2023 事业/婚姻/健康复合应期：事实断语 [S-RF000345-7304d7](cases/C-2026-RF000345-乾-癸酉乙丑乙卯乙酉/statement_index.json:176)，报告依据见 [2023 timing-only](reports/C-2026-RF000345-乾-癸酉乙丑乙卯乙酉-analyst-report.md:1077)，候选规则 `MR-LAYER1`、`MR-LAYER2`、`MR-LAYER3`、`M3-R-031.6`。
- 2024 财运/家庭房产线索：事实断语 [S-RF000345-000cf8](cases/C-2026-RF000345-乾-癸酉乙丑乙卯乙酉/statement_index.json:76)，报告依据见 [2024 财运 timing-only](reports/C-2026-RF000345-乾-癸酉乙丑乙卯乙酉-analyst-report.md:2767)，候选规则以报告该段明示规则为准。
- 2007 健康线索：事实断语 [S-RF000345-6a264e](cases/C-2026-RF000345-乾-癸酉乙丑乙卯乙酉/statement_index.json:26)，报告依据见 [2007 健康 timing-only](reports/C-2026-RF000345-乾-癸酉乙丑乙卯乙酉-analyst-report.md:3297)。

不建议直接映射：通用财运域规则汇总见 [财运规则汇总](reports/C-2026-RF000345-乾-癸酉乙丑乙卯乙酉-analyst-report.md:797)，但该行是域级规则集合，不是单条事件断语，应避免整包 fanout。

### C-2026-RF000441

案例目录：[cases/C-2026-RF000441-乾-癸亥己未己未庚午](cases/C-2026-RF000441-乾-癸亥己未己未庚午/statement_index.json:1)

可映射候选：

- 2006 事业线索：事实断语 [S-RF000441-84adcf](cases/C-2026-RF000441-乾-癸亥己未己未庚午/statement_index.json:66)，报告依据见 [2006 事业 timing-only](reports/C-2026-RF000441-乾-癸亥己未己未庚午-analyst-report.md:1009)，候选规则 `MR-LAYER1`、`MR-LAYER2`、`MR-LAYER3`、`M3-R-031.6`。
- 2022 婚姻/置业线索：事实断语 [S-RF000441-fcca32](cases/C-2026-RF000441-乾-癸亥己未己未庚午/statement_index.json:156)，报告依据见 [2022 婚姻 timing-only](reports/C-2026-RF000441-乾-癸亥己未己未庚午-analyst-report.md:2583)。

不建议直接映射：财运域汇总见 [财运规则汇总](reports/C-2026-RF000441-乾-癸亥己未己未庚午-analyst-report.md:735)，属于域级集合。

### C-2026-RF000864

案例目录：[cases/C-2026-RF000864-乾-己巳丙子乙卯甲申](cases/C-2026-RF000864-乾-己巳丙子乙卯甲申/statement_index.json:1)

可映射候选：

- 2007 事业线索：事实断语 [S-RF000864-5ed093](cases/C-2026-RF000864-乾-己巳丙子乙卯甲申/statement_index.json:16)，报告依据见 [2007 事业 timing-only](reports/C-2026-RF000864-乾-己巳丙子乙卯甲申-analyst-report.md:1029)。
- 2006 财运/学业终止/刑拘线索：事实断语 [S-RF000864-a331ef](cases/C-2026-RF000864-乾-己巳丙子乙卯甲申/statement_index.json:6)，报告依据见 [2006 财运 timing-only](reports/C-2026-RF000864-乾-己巳丙子乙卯甲申-analyst-report.md:2575)。
- 2023 婚姻/财务危机线索：事实断语 [S-RF000864-16b735](cases/C-2026-RF000864-乾-己巳丙子乙卯甲申/statement_index.json:176)，报告依据见 [2023 婚姻 timing-only](reports/C-2026-RF000864-乾-己巳丙子乙卯甲申-analyst-report.md:2609)。

不建议直接映射：财运域汇总见 [财运规则汇总](reports/C-2026-RF000864-乾-己巳丙子乙卯甲申-analyst-report.md:755)，属于域级集合。

### C-2026-RF000243

案例目录：[cases/C-2026-RF000243-坤-己卯己巳戊午丁巳](cases/C-2026-RF000243-坤-己卯己巳戊午丁巳/statement_index.json:1)

可映射候选：

- 2022 事业线索：事实断语 [S-RF000243-ba3d20](cases/C-2026-RF000243-坤-己卯己巳戊午丁巳/statement_index.json:146)，报告依据见 [2022 事业 timing-only](reports/C-2026-RF000243-坤-己卯己巳戊午丁巳-analyst-report.md:1015)。
- 2006 财运/伤灾线索：事实断语 [S-RF000243-61c196](cases/C-2026-RF000243-坤-己卯己巳戊午丁巳/statement_index.json:26)，报告依据见 [2006 财运 timing-only](reports/C-2026-RF000243-坤-己卯己巳戊午丁巳-analyst-report.md:2561)，该段低置信 `★2/50%`，建议人工优先复核，不建议自动进入高权重样本。
- 2023 婚姻线索：事实断语 [S-RF000243-097c5f](cases/C-2026-RF000243-坤-己卯己巳戊午丁巳/statement_index.json:156)，报告依据见 [2023 婚姻 timing-only](reports/C-2026-RF000243-坤-己卯己巳戊午丁巳-analyst-report.md:2595)。
- 2009 健康线索：事实断语 [S-RF000243-ca78f0](cases/C-2026-RF000243-坤-己卯己巳戊午丁巳/statement_index.json:46)，报告依据见 [2009 健康 timing-only](reports/C-2026-RF000243-坤-己卯己巳戊午丁巳-analyst-report.md:3001)。

不建议直接映射：财运域汇总见 [财运规则汇总](reports/C-2026-RF000243-坤-己卯己巳戊午丁巳-analyst-report.md:747)，属于域级集合。

### C-2026-RF000524

案例目录：[cases/C-2026-RF000524-坤-己巳丙寅戊戌丁巳](cases/C-2026-RF000524-坤-己巳丙寅戊戌丁巳/statement_index.json:1)

可映射候选：

- 2022 事业线索：事实断语 [S-RF000524-5134f2](cases/C-2026-RF000524-坤-己巳丙寅戊戌丁巳/statement_index.json:126)，报告依据见 [2022 事业 timing-only](reports/C-2026-RF000524-坤-己巳丙寅戊戌丁巳-analyst-report.md:1009)。
- 2021 财运线索：事实断语 [S-RF000524-52e122](cases/C-2026-RF000524-坤-己巳丙寅戊戌丁巳/statement_index.json:116)，报告依据见 [2021 财运 timing-only](reports/C-2026-RF000524-坤-己巳丙寅戊戌丁巳-analyst-report.md:2555)。
- 2024 婚姻/健康线索：事实断语 [S-RF000524-8c1f1f](cases/C-2026-RF000524-坤-己巳丙寅戊戌丁巳/statement_index.json:156)，报告依据见 [2024 婚姻 timing-only](reports/C-2026-RF000524-坤-己巳丙寅戊戌丁巳-analyst-report.md:2589)。
- 2022 健康线索：事实断语 [S-RF000524-e88f2d](cases/C-2026-RF000524-坤-己巳丙寅戊戌丁巳/statement_index.json:136)，报告依据见 [2022 健康 timing-only](reports/C-2026-RF000524-坤-己巳丙寅戊戌丁巳-analyst-report.md:2995)。

不建议直接映射：财运域汇总见 [财运规则汇总](reports/C-2026-RF000524-坤-己巳丙寅戊戌丁巳-analyst-report.md:735)，属于域级集合。

## 推荐执行顺序

1. 为五案分别生成 `statement_rule_map.json` 草案，只包含上述候选断语的 rule 映射。
2. 在五案 [feedback.md](cases/C-2026-RF000345-乾-癸酉乙丑乙卯乙酉/feedback.md:1) 追加待人工标注反馈位，但保持 `[ ]`，不进入自动摄入。
3. 人工复核每条候选断语，将 `[ ]` 改为 `[y]`、`[n]`、`[?]` 或 `[skip]`。
4. 逐案运行 [tools.feedback_ingest.ingest()](tools/feedback_ingest.py:659) 对应命令进行摄入。
5. 摄入后检查 [META/iteration-log.md](META/iteration-log.md:1)、[META/calibration](META/calibration/2026-06-08-after-C-2026-RF000345-乾-癸酉乙丑乙卯乙酉.snapshot.yaml:1)、[META/timings](META/timings/feedback_ingest-20260608T044823Z-C-2026-RF000345-乾-癸酉乙丑乙卯乙酉.json:1) 是否出现非零 `feedback_count` 与 `rule_count`。

## 重摄入命令草案

人工标注完成后执行：

```bash
python -m tools.feedback_ingest C-2026-RF000345-乾-癸酉乙丑乙卯乙酉
python -m tools.feedback_ingest C-2026-RF000441-乾-癸亥己未己未庚午
python -m tools.feedback_ingest C-2026-RF000864-乾-己巳丙子乙卯甲申
python -m tools.feedback_ingest C-2026-RF000243-坤-己卯己巳戊午丁巳
python -m tools.feedback_ingest C-2026-RF000524-坤-己巳丙寅戊戌丁巳
```

摄入后核验：

```bash
python tools/rule_status_scan.py --check
python tools/tool_registry.py --check
```

## 风险控制

- 不把报告域级规则汇总整包映射到单个事实断语，避免一条反馈污染过多规则。
- 不自动填写 `[y]` / `[n]`，避免把已知事实迁移误判为模型命中。
- 低置信断语优先人工复核，尤其是 [C-2026-RF000243 的 2006 财运线索](reports/C-2026-RF000243-坤-己卯己巳戊午丁巳-analyst-report.md:2561)。
- 当前五案索引没有 `reading_ids` / `adjudication_id`，即使规则反馈补通，也未必能直接驱动专家域权重日志；如需多流派权重动态调整，应补充并行域索引字段或重跑报告渲染链路。

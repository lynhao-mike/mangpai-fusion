# 五案反馈闭环集中复核清单 · 2026-06-11

> 用途：集中复核五个 RF 正式案例的应期规则反馈。请人工将“裁决”列从 `[待标注]` 改为 `[y]` / `[n]` / `[?]` / `[skip]` 后，再同步回对应 case 的 `feedback.md`。
>
> 安全约束：本文件不直接参与 `tools.feedback_ingest` 摄入；正式摄入只读取各 case 目录下的 `feedback.md` 与 `statement_rule_map.json`。

## 裁决口径

| 标记 | 含义 | 摄入口径 |
|---|---|---|
| `[y]` | 断语/应期与事实吻合 | hit |
| `[n]` | 断语/应期与事实不吻合 | miss |
| `[?]` | 信息不足，暂不计入命中/失验 | no_data |
| `[skip]` | 不适合作为本轮校准样本 | no_data |

## 复核清单

| case_id | statement_id | 事项 | 年份 | 已绑定规则 | 报告证据 | 事实摘要 | 裁决 |
|---|---|---|---:|---|---|---|---|
| C-2026-RF000345-乾-癸酉乙丑乙卯乙酉 | S-RF000345-7304d7 | 事业 | 2023 | MR-LAYER1, MR-LAYER2, MR-LAYER3, M3-R-031.6 | reports/C-2026-RF000345-乾-癸酉乙丑乙卯乙酉-analyst-report.md:1077 | 年初介绍女友后分开；申酉月工厂工作一个月被开除；伴随抑郁感。 | [待标注] |
| C-2026-RF000345-乾-癸酉乙丑乙卯乙酉 | S-RF000345-000cf8 | 财运 | 2024 | MR-LAYER1, MR-LAYER2, MR-LAYER3, M3-R-031.6 | reports/C-2026-RF000345-乾-癸酉乙丑乙卯乙酉-analyst-report.md:2767 | 在家休学养病，家里年底又盖房。 | [待标注] |
| C-2026-RF000345-乾-癸酉乙丑乙卯乙酉 | S-RF000345-6a264e | 健康 | 2007 | MR-LAYER1, MR-LAYER2, MR-LAYER3, M3-R-031.6 | reports/C-2026-RF000345-乾-癸酉乙丑乙卯乙酉-analyst-report.md:3297 | 升初中考进实验班，但严重流鼻血，后续身体转差。 | [待标注] |
| C-2026-RF000441-乾-癸亥己未己未庚午 | S-RF000441-84adcf | 事业 | 2006 | MR-LAYER1, MR-LAYER2, MR-LAYER3, M3-R-031.6 | reports/C-2026-RF000441-乾-癸亥己未己未庚午-analyst-report.md:1009 | 提早修完学分回港工作，但只是普通文职。 | [待标注] |
| C-2026-RF000441-乾-癸亥己未己未庚午 | S-RF000441-fcca32 | 婚姻 | 2022 | MR-LAYER1, MR-LAYER2, MR-LAYER3, M3-R-031.6 | reports/C-2026-RF000441-乾-癸亥己未己未庚午-analyst-report.md:2583 | 买老破小，有自己的家，老婆开心。 | [待标注] |
| C-2026-RF000864-乾-己巳丙子乙卯甲申 | S-RF000864-5ed093 | 事业 | 2007 | MR-LAYER1, MR-LAYER2, MR-LAYER3, M3-R-031.6 | reports/C-2026-RF000864-乾-己巳丙子乙卯甲申-analyst-report.md:1029 | 从北方农村老家来到杭州打工，年龄小无学历，底层工作折腾。 | [待标注] |
| C-2026-RF000864-乾-己巳丙子乙卯甲申 | S-RF000864-a331ef | 财运 | 2006 | MR-LAYER1, MR-LAYER2, MR-LAYER3, M3-R-031.1 | reports/C-2026-RF000864-乾-己巳丙子乙卯甲申-analyst-report.md:2575 | 学业终止、被开除、有破财，被刑拘一个月。 | [待标注] |
| C-2026-RF000864-乾-己巳丙子乙卯甲申 | S-RF000864-16b735 | 婚姻 | 2023 | MR-LAYER1, MR-LAYER2, MR-LAYER3, M3-R-031.1 | reports/C-2026-RF000864-乾-己巳丙子乙卯甲申-analyst-report.md:2609 | 股票彻底影响生活，夫妻经常吵架，积蓄亏完并欠外债。 | [待标注] |
| C-2026-RF000243-坤-己卯己巳戊午丁巳 | S-RF000243-ba3d20 | 事业 | 2022 | MR-LAYER1, MR-LAYER2, MR-LAYER3, M3-R-031.1 | reports/C-2026-RF000243-坤-己卯己巳戊午丁巳-analyst-report.md:1015 | 国考省考未过，论文难产，因家庭债务放弃机会去私企，情绪崩溃。 | [待标注] |
| C-2026-RF000243-坤-己卯己巳戊午丁巳 | S-RF000243-61c196 | 财运 | 2006 | MR-LAYER1 | reports/C-2026-RF000243-坤-己卯己巳戊午丁巳-analyst-report.md:2561 | 左脚卷进自行车后轮，大脚趾靠下处留疤。 | [待标注] |
| C-2026-RF000243-坤-己卯己巳戊午丁巳 | S-RF000243-097c5f | 婚姻 | 2023 | MR-LAYER1, MR-LAYER2, MR-LAYER3, M3-R-031.1 | reports/C-2026-RF000243-坤-己卯己巳戊午丁巳-analyst-report.md:2595 | 6 月离职休养，转施工单位文员，11 月恋爱但总吵架。 | [待标注] |
| C-2026-RF000243-坤-己卯己巳戊午丁巳 | S-RF000243-ca78f0 | 健康 | 2009 | MR-LAYER1, MR-LAYER2, MR-LAYER3, M3-R-031.3 | reports/C-2026-RF000243-坤-己卯己巳戊午丁巳-analyst-report.md:3001 | 被同学撞到左手骨折。 | [待标注] |
| C-2026-RF000524-坤-己巳丙寅戊戌丁巳 | S-RF000524-5134f2 | 事业 | 2022 | MR-LAYER1, MR-LAYER2, MR-LAYER3, M3-R-031.2 | reports/C-2026-RF000524-坤-己巳丙寅戊戌丁巳-analyst-report.md:1009 | 下半年调到其他分店，与团队相处开心，上司评价好。 | [待标注] |
| C-2026-RF000524-坤-己巳丙寅戊戌丁巳 | S-RF000524-52e122 | 财运 | 2021 | MR-LAYER1, MR-LAYER2, MR-LAYER3, M3-R-031.2 | reports/C-2026-RF000524-坤-己巳丙寅戊戌丁巳-analyst-report.md:2555 | 7 月离职，开始躺平，大半年以上无收入只有支出。 | [待标注] |
| C-2026-RF000524-坤-己巳丙寅戊戌丁巳 | S-RF000524-8c1f1f | 婚姻 | 2024 | MR-LAYER1, MR-LAYER2, MR-LAYER3, M3-R-031.2 | reports/C-2026-RF000524-坤-己巳丙寅戊戌丁巳-analyst-report.md:2589 | 腰椎不好、坐骨神经痛，单身，性格内向保守固执多虑。 | [待标注] |
| C-2026-RF000524-坤-己巳丙寅戊戌丁巳 | S-RF000524-e88f2d | 健康 | 2022 | MR-LAYER1, MR-LAYER2, MR-LAYER3, M3-R-031.2 | reports/C-2026-RF000524-坤-己巳丙寅戊戌丁巳-analyst-report.md:2995 | 身体开始出风疹，右边眉毛掉落，原因不明并持续。 | [待标注] |

## 同步步骤

1. 人工完成本文件“裁决”列。
2. 将每条裁决同步到对应 case 的 `feedback.md`，把 `[待标注]` 替换为 `[y]` / `[n]` / `[?]` / `[skip]`。
3. 逐案运行：

```bash
python -m tools.feedback_ingest C-2026-RF000345-乾-癸酉乙丑乙卯乙酉
python -m tools.feedback_ingest C-2026-RF000441-乾-癸亥己未己未庚午
python -m tools.feedback_ingest C-2026-RF000864-乾-己巳丙子乙卯甲申
python -m tools.feedback_ingest C-2026-RF000243-坤-己卯己巳戊午丁巳
python -m tools.feedback_ingest C-2026-RF000524-坤-己巳丙寅戊戌丁巳
```

## 预期影响

- 若裁决为 `[y]` 或 `[n]`，摄入链路会经 `statement_rule_map.json` 形成 rule fanout。
- `[?]` 与 `[skip]` 会登记为 no_data，不计入命中/失验统计。
- 当前五案尚未写入正式裁决，因此不应运行实际摄入。

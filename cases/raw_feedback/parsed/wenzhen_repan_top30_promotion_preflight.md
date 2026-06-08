# 问真 Top 30 staging · 正式转案预检报告

> 生成时间：2026-06-08T08:44:54.404465+00:00
> 用途：检查 staging 候选在创建正式 case 前是否存在命名冲突、证据缺口或字段缺失。
> 约束：本报告不创建正式 case；人工批准后仍需运行 `tools.preflight`。

## 汇总

- 候选数：30
- 可进入人工转案：4
- 阻断数：26
- 错误分布：{'formal_case_dir_conflict': 26}
- 警告分布：{}

## 预检表

| raw_id | 建议 case_id | 四柱 | 事件数 | 目标目录 | 状态 | 错误 | 警告 |
|---|---|---|---:|---|---|---|---|
| RF-2026-000345 | C-2026-RF000345-乾-癸酉乙丑乙卯乙酉 | 癸酉乙丑乙卯乙酉 | 19 | cases/C-2026-RF000345-乾-癸酉乙丑乙卯乙酉 | BLOCKED | formal_case_dir_conflict | - |
| RF-2026-000441 | C-2026-RF000441-乾-癸亥己未己未庚午 | 癸亥己未己未庚午 | 18 | cases/C-2026-RF000441-乾-癸亥己未己未庚午 | BLOCKED | formal_case_dir_conflict | - |
| RF-2026-000864 | C-2026-RF000864-乾-己巳丙子乙卯甲申 | 己巳丙子乙卯甲申 | 18 | cases/C-2026-RF000864-乾-己巳丙子乙卯甲申 | BLOCKED | formal_case_dir_conflict | - |
| RF-2026-000243 | C-2026-RF000243-坤-己卯己巳戊午丁巳 | 己卯己巳戊午丁巳 | 16 | cases/C-2026-RF000243-坤-己卯己巳戊午丁巳 | BLOCKED | formal_case_dir_conflict | - |
| RF-2026-000524 | C-2026-RF000524-坤-己巳丙寅戊戌丁巳 | 己巳丙寅戊戌丁巳 | 16 | cases/C-2026-RF000524-坤-己巳丙寅戊戌丁巳 | BLOCKED | formal_case_dir_conflict | - |
| RF-2026-000572 | C-2026-RF000572-乾-辛未丙申庚戌戊子 | 辛未丙申庚戌戊子 | 16 | cases/C-2026-RF000572-乾-辛未丙申庚戌戊子 | BLOCKED | formal_case_dir_conflict | - |
| RF-2026-000606 | C-2026-RF000606-乾-庚午己丑甲申辛未 | 庚午己丑甲申辛未 | 16 | cases/C-2026-RF000606-乾-庚午己丑甲申辛未 | BLOCKED | formal_case_dir_conflict | - |
| RF-2026-000868 | C-2026-RF000868-乾-壬申戊申庚辰丁亥 | 壬申戊申庚辰丁亥 | 16 | cases/C-2026-RF000868-乾-壬申戊申庚辰丁亥 | BLOCKED | formal_case_dir_conflict | - |
| RF-2026-000026 | C-2026-RF000026-乾-庚午戊寅壬寅丙午 | 庚午戊寅壬寅丙午 | 15 | cases/C-2026-RF000026-乾-庚午戊寅壬寅丙午 | BLOCKED | formal_case_dir_conflict | - |
| RF-2026-000108 | C-2026-RF000108-坤-乙丑甲申甲申辛未 | 乙丑甲申甲申辛未 | 15 | cases/C-2026-RF000108-坤-乙丑甲申甲申辛未 | BLOCKED | formal_case_dir_conflict | - |
| RF-2026-000448 | C-2026-RF000448-乾-庚辰甲申癸亥癸亥 | 庚辰甲申癸亥癸亥 | 15 | cases/C-2026-RF000448-乾-庚辰甲申癸亥癸亥 | BLOCKED | formal_case_dir_conflict | - |
| RF-2026-000592 | C-2026-RF000592-乾-丁卯壬寅壬寅戊申 | 丁卯壬寅壬寅戊申 | 15 | cases/C-2026-RF000592-乾-丁卯壬寅壬寅戊申 | BLOCKED | formal_case_dir_conflict | - |
| RF-2026-000771 | C-2026-RF000771-乾-癸亥壬戌壬午庚子 | 癸亥壬戌壬午庚子 | 15 | cases/C-2026-RF000771-乾-癸亥壬戌壬午庚子 | READY | - | - |
| RF-2026-000900 | C-2026-RF000900-乾-戊寅乙卯丙寅戊子 | 戊寅乙卯丙寅戊子 | 15 | cases/C-2026-RF000900-乾-戊寅乙卯丙寅戊子 | BLOCKED | formal_case_dir_conflict | - |
| RF-2026-000965 | C-2026-RF000965-坤-壬午乙巳甲午丙子 | 壬午乙巳甲午丙子 | 15 | cases/C-2026-RF000965-坤-壬午乙巳甲午丙子 | BLOCKED | formal_case_dir_conflict | - |
| RF-2026-000118 | C-2026-RF000118-乾-己巳癸酉辛丑己丑 | 己巳癸酉辛丑己丑 | 14 | cases/C-2026-RF000118-乾-己巳癸酉辛丑己丑 | BLOCKED | formal_case_dir_conflict | - |
| RF-2026-000373 | C-2026-RF000373-乾-丙子庚子辛巳己亥 | 丙子庚子辛巳己亥 | 14 | cases/C-2026-RF000373-乾-丙子庚子辛巳己亥 | BLOCKED | formal_case_dir_conflict | - |
| RF-2026-000417 | C-2026-RF000417-乾-丙寅丙申辛卯丁酉 | 丙寅丙申辛卯丁酉 | 14 | cases/C-2026-RF000417-乾-丙寅丙申辛卯丁酉 | BLOCKED | formal_case_dir_conflict | - |
| RF-2026-000531 | C-2026-RF000531-坤-乙亥庚辰己丑癸酉 | 乙亥庚辰己丑癸酉 | 14 | cases/C-2026-RF000531-坤-乙亥庚辰己丑癸酉 | BLOCKED | formal_case_dir_conflict | - |
| RF-2026-000990 | C-2026-RF000990-乾-庚午己丑戊寅癸亥 | 庚午己丑戊寅癸亥 | 14 | cases/C-2026-RF000990-乾-庚午己丑戊寅癸亥 | BLOCKED | formal_case_dir_conflict | - |
| RF-2026-000301 | C-2026-RF000301-乾-乙亥辛巳壬寅癸卯 | 乙亥辛巳壬寅癸卯 | 13 | cases/C-2026-RF000301-乾-乙亥辛巳壬寅癸卯 | BLOCKED | formal_case_dir_conflict | - |
| RF-2026-000514 | C-2026-RF000514-乾-癸亥己未甲子壬申 | 癸亥己未甲子壬申 | 13 | cases/C-2026-RF000514-乾-癸亥己未甲子壬申 | BLOCKED | formal_case_dir_conflict | - |
| RF-2026-000551 | C-2026-RF000551-乾-壬戌丙午甲申丁卯 | 壬戌丙午甲申丁卯 | 13 | cases/C-2026-RF000551-乾-壬戌丙午甲申丁卯 | READY | - | - |
| RF-2026-000865 | C-2026-RF000865-乾-辛未丙申戊午癸亥 | 辛未丙申戊午癸亥 | 13 | cases/C-2026-RF000865-乾-辛未丙申戊午癸亥 | BLOCKED | formal_case_dir_conflict | - |
| RF-2026-000894 | C-2026-RF000894-乾-壬戌己酉庚子戊子 | 壬戌己酉庚子戊子 | 13 | cases/C-2026-RF000894-乾-壬戌己酉庚子戊子 | READY | - | - |
| RF-2026-000989 | C-2026-RF000989-乾-庚午己丑戊寅丁巳 | 庚午己丑戊寅丁巳 | 13 | cases/C-2026-RF000989-乾-庚午己丑戊寅丁巳 | BLOCKED | formal_case_dir_conflict | - |
| RF-2026-000249 | C-2026-RF000249-坤-乙亥乙酉庚午戊寅 | 乙亥乙酉庚午戊寅 | 12 | cases/C-2026-RF000249-坤-乙亥乙酉庚午戊寅 | BLOCKED | formal_case_dir_conflict | - |
| RF-2026-000281 | C-2026-RF000281-乾-己巳乙亥己丑戊辰 | 己巳乙亥己丑戊辰 | 12 | cases/C-2026-RF000281-乾-己巳乙亥己丑戊辰 | BLOCKED | formal_case_dir_conflict | - |
| RF-2026-000408 | C-2026-RF000408-乾-辛亥甲午辛卯壬辰 | 辛亥甲午辛卯壬辰 | 12 | cases/C-2026-RF000408-乾-辛亥甲午辛卯壬辰 | BLOCKED | formal_case_dir_conflict | - |
| RF-2026-000684 | C-2026-RF000684-坤-己巳丙子戊申戊午 | 己巳丙子戊申戊午 | 12 | cases/C-2026-RF000684-坤-己巳丙子戊申戊午 | READY | - | - |

## 转案前硬性要求

- [ ] 人工确认该候选从 staging 转正式 case。
- [ ] 创建正式目录后补齐 `input.md`、`analysis.md`、`feedback.md`、`statement_index.json`。
- [ ] 正式 `input.md` 运行 `python -m tools.preflight <case>/input.md`。
- [ ] case 与报告/反馈文件互写关联路径。

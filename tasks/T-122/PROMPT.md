# T-122 · 学历四档人工标注（49 张真实盘）

- 状态：🟡 Waiting on Human
- 优先级：P0（T-117 B 类对照的前置）
- 创建：2026-10-26（中枢）
- 负责人：用户（你已确认「我来判」）

## 1. 输入

`META/education-label-sheet-v1.md`（自动生成，49 行，每行一个真实案例 + 学历相关原文摘录）。
重新生成：`python -m tools.education_label_sheet`。

## 2. 档位（你 2026-10-26 定）

| 档 | 定义 |
|---|---|
| A | 小学及以下 |
| B | 初高中 / 技校 / 中专 |
| C | 大专 / 本科 |
| D | 研究生及以上 |

判读口径：

1. 以**最高已取得学历**为准（在读不算，除非原文写「在读研究生」）。
2. 只写「读书好 / 聪明 / 有文化」→ 判不了，填 `?`。
3. 「中专后自考本科」→ C；「初中辍学」→ B（学段落在初中）。
4. 同一案例出现矛盾表述 → 填 `?` 并在备注写两句原文。

## 3. 输出格式

把结果写到 `theory/claims/labels/education-4tier.yaml`：

```yaml
schema: education-label/v1
labelled_by: <你的名字或代号>
labelled_at: "2026-10-26"
labels:
  C-2026-RF000001-坤-己卯辛未丙寅乙未: {grade: C, note: "原文：本科毕业"}
  C-2026-002-坤-壬戌庚戌戊辰丙辰: {grade: "?", note: "只写『学习一般』，无学历信息"}
```

## 4. 验收

```bash
python -m tools.claim_contrastive_check --labels theory/claims/labels/education-4tier.yaml
```

要求：覆盖 ≥40 条（49 行里允许 ≤9 条判不了），`?` 比例 ≤20%。

## 5. 下游

- T-117 B 类对照：印星空亡命中组 vs 对照组的 C+D 占比之差 + 95% CI。
- 若 CI 跨 0，该断语判「不可判」，不得写进报告结论。

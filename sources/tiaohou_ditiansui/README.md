# sources/tiaohou_ditiansui/ · 滴天髓调候派原始教案入口

> 用途：存放用户提供的滴天髓调候派原始资料、课程讲义、案例讲稿、图片转写稿、PDF 摘录与人工整理稿。

---

## 1. 目录定位

本目录只保存**原始或准原始材料**，不直接作为引擎可执行规则。

后续流程：

```text
sources/tiaohou_ditiansui/ 原始教案
  → 人工/AI 理论提取
  → theory/tiaohou_ditiansui/index.yaml 候选规则
  → 规则审校与状态标注
  → engine/tiaohou_ditiansui/ 可执行分析器
  → 多专家裁判模型
```

---

## 2. 建议投放格式

支持以下形式：

- `.md`：推荐，便于直接提取。
- `.txt`：可接受，适合转写稿。
- `.pdf`：可接受，后续需做文本抽取。
- `.docx`：可接受，后续需做文本抽取。
- `.png` / `.jpg`：仅用于图片资料，建议同时提供转写稿。

---

## 3. 建议命名规范

```text
DTS-YYYYMMDD-主题-序号.md
DTS-YYYYMMDD-寒暖总论-001.md
DTS-YYYYMMDD-燥湿病药-002.md
DTS-YYYYMMDD-五行调候-003.md
```

命名建议：

- `DTS`：滴天髓调候派。
- `YYYYMMDD`：资料提供或整理日期。
- `主题`：如 `寒暖总论`、`燥湿病药`、`五行调候`、`健康调候`、`性格气象`。
- `序号`：同日同主题多份材料时递增。

---

## 4. 原始材料头部建议

建议每份材料开头保留以下信息：

```yaml
source_meta:
  school: tiaohou_ditiansui
  title: 滴天髓调候派资料标题
  source_type: course_note
  provided_by: user
  provided_date: YYYY-MM-DD
  copyright_note: 仅用于本地理论提取与规则归档
  extraction_status: pending
```

---

## 5. 提取重点

滴天髓调候派提取时优先关注：

- 寒暖燥湿的判定条件。
- 五行气势、气候、流通、停滞。
- 病药关系、调候用神、通关用神。
- 健康、性格、婚姻、事业、财运中的气候映射。
- 大运流年对气候平衡的改变。
- 可证伪断语与案例验证点。

---

## 6. 禁止事项

- 不要把未经提取的原文直接写入 `theory/tiaohou_ditiansui/index.yaml`。
- 不要与盲派、子平材料混放。
- 不要在原始资料中手写命中率或规则状态，规则状态以后以 theory YAML 与反馈系统为准。

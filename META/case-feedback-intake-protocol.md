# 真实案例反馈语料入库协议 · v0.1

> 本协议用于处理大批量真实命例反馈材料，例如 `cases/实战案例反馈990个案例_part*.md`。
> 它不同于教材入库协议：教材进入 `sources/` 与 `theory/`，真实案例反馈先进入只读原文与结构化候选集，再经人工筛选后进入正式 `cases/C-.../`。

---

## 1. 定位

真实案例反馈语料的目标不是直接产出命理师报告，而是为以下工作提供材料：

1. 批量发现可回测的真实命例。
2. 提取出生信息、经历年表、职业、婚姻、健康、财务等反馈标签。
3. 给既有断语、规则、应期模型提供命中 / 未命中校准样本。
4. 从高质量样本中分批建立正式 case。

本协议只定义 S0–S3 的语料入口，不替代正式新案流程、报告生成流程和反馈摄入流程。

---

## 2. 与教材入库的边界

| 类型 | 入口 | 目标 | 是否进 `theory/` |
|---|---|---|---|
| 教材 / 讲义 / 经典文本 | `sources/inbox/` | 抽取理论规则 | 是 |
| 真实案例反馈 | `cases/raw_feedback/` | 抽取案例候选与反馈标签 | 否 |
| 正式个案 | `cases/C-YYYY-NNN-乾/坤-四柱/` | 分析、报告、反馈闭环 | 否 |

禁止把真实案例反馈文件按派别归入 `sources/{school}/`，也禁止未经清洗直接批量生成正式 case。

---

## 3. 推荐目录

```text
cases/
  raw_feedback/
    source/
      实战案例反馈990个案例_part1.md
      实战案例反馈990个案例_part2.md
      实战案例反馈990个案例_part3.md
    parsed/
      real_cases_990.jsonl
      real_cases_990-summary.json
```

说明：

- `source/` 保存原始文件，只读归档，不改写内容。
- `parsed/` 保存机器抽取结果，可重复生成。
- 正式 case 仍必须放在 `cases/C-.../`，不得放在 `raw_feedback/`。

---

## 4. S0–S3 流程

### S0 · 原文归档

1. 将原始 `.md` 放入 `cases/raw_feedback/source/`。
2. 保留原始文件名。
3. 不直接修改原文；如需脱敏，写入结构化结果而不是覆盖原文。

### S1 · 候选拆分

抽取工具按行与边界模式拆分候选案例：

- 性别触发：`男`、`女`、`男生`、`女生`、`乾`、`坤`。
- 日期触发：`阳历`、`公(阳)历`、`农历`、`农(阴)历`、`阴历`、`YYYY-MM-DD`、`YYYY 年 M 月 D 日`。
- 内容触发：`年表经历`、`经历`、`其他信息`、`问题`。

因原文存在同一行多个案例粘连，S1 只能生成候选，不保证每条均可立案。

### S2 · 字段抽取与脱敏

每条候选输出 JSONL 一行，建议字段：

```json
{
  "raw_id": "RF-2026-000001",
  "source_file": "实战案例反馈990个案例_part1.md",
  "line_start": 1,
  "line_end": 1,
  "gender": "女",
  "qian_kun": "坤",
  "calendar_type": "solar",
  "birth_datetime_raw": "1999 年 7 月 13 日 14:00 分",
  "true_solar_time_raw": "1999-07-13 13:36:00",
  "birth_place_raw": "广州市 荔湾区",
  "birth_place_sanitized": "广州市",
  "bazi_raw": "",
  "events": [],
  "questions": [],
  "profile": {
    "occupation": "",
    "income": "",
    "family": "",
    "health": "",
    "marriage": "",
    "children": "",
    "personality": ""
  },
  "quality_grade": "A",
  "quality_flags": [],
  "privacy_flags": [],
  "raw_text": "..."
}
```

### S3 · 质量分级

| 等级 | 标准 | 用途 |
|---|---|---|
| A | 性别、出生日期、出生时分、出生地或真太阳时清楚，经历可读 | 可人工转正式 case |
| B | 出生信息基本可用，但有少量缺失或歧义 | 可做事件反馈校准 |
| C | 文本可读但粘连、重复、字段缺失明显 | 仅待人工复核 |
| D | 日期异常、时辰不明、缺出生信息、疑似污染或重复 | 不进入校准 |

---

## 5. 隐私与敏感信息处理

真实案例可能包含健康、婚姻、收入、家庭矛盾、负债、心理疾病、事故等高度隐私内容。处理时必须遵守：

1. 结构化输出保留分析所需标签，不扩散个人可识别细节。
2. 地点默认脱敏到省 / 市级；区县、乡镇、街道可放入 `birth_place_raw`，但对外使用 `birth_place_sanitized`。
3. 姓名、微信、电话、账号、详细住址必须进入 `privacy_flags` 并在对外材料中移除。
4. 自伤、暴力、违法、疾病等内容只作为事件标签，不作为报告夸张描述。
5. `raw_text` 仅供内部追溯，不进入用户报告。

---

## 6. 与正式 case 的衔接

只有 A 级、且经人工复核的样本，才可以转入正式 case 流程：

1. 按 `templates/input-from-wenzhen.md` 补齐排盘信息。
2. 建立 `cases/C-YYYY-NNN-乾/坤-四柱/`。
3. 运行 `python -m tools.preflight cases/C-YYYY-NNN-乾-四柱/input.md`。
4. 再运行正式 pipeline 与 report 渲染。
5. 将原始 `raw_id` 写入 `analysis.md`、`feedback.md` 或 `statement_index.json` 的来源字段。

未转正式 case 的 B/C/D 样本不得进入 `cases-index.md`。

---

## 7. 推荐工具

使用 `tools/case_feedback_intake.py` 进行初步抽取：

```bash
python -m tools.case_feedback_intake --dry-run
python -m tools.case_feedback_intake
```

工具职责：

- 扫描 `cases/实战案例反馈990个案例_part*.md` 与 `cases/raw_feedback/source/*.md`。
- 生成 `cases/raw_feedback/parsed/real_cases_990.jsonl`。
- 生成 `cases/raw_feedback/parsed/real_cases_990-summary.json`。
- 输出质量分布、隐私标记分布和疑似重复数量。

工具不负责：

- 不移动正式 case。
- 不写 `cases-index.md`。
- 不跑 pipeline。
- 不生成 report。
- 不修改 `theory/`。

---

## 8. 推荐执行策略

1. 先 dry-run 抽取三份文件，确认候选数量和质量分布。
2. 抽样检查 A/B/C/D 各 10 条。
3. 调整拆分与字段抽取规则。
4. 首批只选 20–50 个 A 级案例人工转正式 case。
5. 后续每批处理后记录抽取日志与人工复核结论。

# C-2026-RF000029-乾-己卯丙子壬寅丙午 · 四柱口径输入（pillar-only）

> 来源：`cases/raw_feedback/parsed/real_cases_990.jsonl` 的 `RF-2026-000029`。
> 本文件由 `tools/rf_pillar_intake.py` 生成；**命主未提供可确认的出生时刻**，
> 故采用四柱直输口径。已知事件见 `feedback.md`，未写入本文件。

```yaml
schema_version: 1.2.0
case_meta:
  case_id: "C-2026-RF000029-乾-己卯丙子壬寅丙午"
  立案日期: 2026-10-17
  命主代号: "RF-2026-000029"
  策略: RF_PILLAR_ONLY_CANDIDATE
  来源: 真实案例反馈990个案例（四柱口径）

birth:
  性别: 男
  乾坤: 乾
  出生地脱敏: "出生城市"
  时间来源: none
  口径说明: "命主未提供出生时刻；本案例使用命主自报四柱直排，缺起运年份与人元司令。"

四柱:
  年柱: "己卯"
  月柱: "丙子"
  日柱: "壬寅"
  时柱: "丙午"

known_facts: []
提问:
  - "仅作为盲断候选；已知事件见 feedback.md。"
```

## 口径边界（必读）

- 本案例**没有人元司令**（`siling`）与**起运年龄/日期**：`engine.cli --pillars` 会返回
  `input_limitations.unavailable` 的 `qiyun`、`dayun_calendar`、`siling` 三项。
- 大运干支顺逆序列可用；**起止公历年份不可用**。
- 因此本案例**不得用于**依赖大运年份或人元司令的断言；流年只做原局引动。
- 对应写作规范见 `docs/analysis_human_touch.md` 与 `templates/report-v7-human.md`
  的「条件分支实断」条款。

# 问真 staging · 首批 5 个正式转案 dry-run 方案

> 生成时间：2026-06-07T15:45:23.433372+00:00
> 用途：供人工批准首批正式 case 创建；本方案不创建任何正式目录。

## 汇总

- 首批数量：5
- 来源 staging：`cases/raw_feedback/parsed/wenzhen_repan_top30_staging_manifest.jsonl`
- 必备文件：input.md, analysis.md, feedback.md, statement_index.json

## 首批清单

| 顺位 | raw_id | 建议 case_id | 乾坤 | 四柱 | 事件数 | 源草稿 |
|---:|---|---|---|---|---:|---|
| 1 | RF-2026-000345 | C-2026-RF000345-乾-癸酉乙丑乙卯乙酉 | 乾 | 癸酉乙丑乙卯乙酉 | 19 | cases/raw_feedback/case_drafts/RF-2026-000345/input.md |
| 2 | RF-2026-000441 | C-2026-RF000441-乾-癸亥己未己未庚午 | 乾 | 癸亥己未己未庚午 | 18 | cases/raw_feedback/case_drafts/RF-2026-000441/input.md |
| 3 | RF-2026-000864 | C-2026-RF000864-乾-己巳丙子乙卯甲申 | 乾 | 己巳丙子乙卯甲申 | 18 | cases/raw_feedback/case_drafts/RF-2026-000864/input.md |
| 4 | RF-2026-000243 | C-2026-RF000243-坤-己卯己巳戊午丁巳 | 坤 | 己卯己巳戊午丁巳 | 16 | cases/raw_feedback/case_drafts/RF-2026-000243/input.md |
| 5 | RF-2026-000524 | C-2026-RF000524-坤-己巳丙寅戊戌丁巳 | 坤 | 己巳丙寅戊戌丁巳 | 16 | cases/raw_feedback/case_drafts/RF-2026-000524/input.md |

## 逐案操作预案

### 1. RF-2026-000345 → C-2026-RF000345-乾-癸酉乙丑乙卯乙酉

- 目标目录：`cases/C-2026-RF000345-乾-癸酉乙丑乙卯乙酉`
- 来源草稿：`cases/raw_feedback/case_drafts/RF-2026-000345/input.md`
- 来源索引：`cases/raw_feedback/case_drafts/wenzhen-repan-index-male.md`
- 事件数：19 / 草稿事实数：19
- 目标文件：
  - `cases/C-2026-RF000345-乾-癸酉乙丑乙卯乙酉/input.md`
  - `cases/C-2026-RF000345-乾-癸酉乙丑乙卯乙酉/analysis.md`
  - `cases/C-2026-RF000345-乾-癸酉乙丑乙卯乙酉/feedback.md`
  - `cases/C-2026-RF000345-乾-癸酉乙丑乙卯乙酉/statement_index.json`
- 操作步骤：
  - [ ] 创建目录 cases/C-2026-RF000345-乾-癸酉乙丑乙卯乙酉
  - [ ] 生成 cases/C-2026-RF000345-乾-癸酉乙丑乙卯乙酉/input.md：从 staging 排盘与草稿 birth/known_facts 合并
  - [ ] 生成 cases/C-2026-RF000345-乾-癸酉乙丑乙卯乙酉/analysis.md：记录来源、转案说明与待分析占位
  - [ ] 生成 cases/C-2026-RF000345-乾-癸酉乙丑乙卯乙酉/feedback.md：迁移原 known_facts 并保留 raw_id 追踪
  - [ ] 生成 cases/C-2026-RF000345-乾-癸酉乙丑乙卯乙酉/statement_index.json：初始化 statement 追踪骨架
  - [ ] 运行 python -m tools.preflight cases/C-2026-RF000345-乾-癸酉乙丑乙卯乙酉/input.md


### 2. RF-2026-000441 → C-2026-RF000441-乾-癸亥己未己未庚午

- 目标目录：`cases/C-2026-RF000441-乾-癸亥己未己未庚午`
- 来源草稿：`cases/raw_feedback/case_drafts/RF-2026-000441/input.md`
- 来源索引：`cases/raw_feedback/case_drafts/wenzhen-repan-index-male.md`
- 事件数：18 / 草稿事实数：18
- 目标文件：
  - `cases/C-2026-RF000441-乾-癸亥己未己未庚午/input.md`
  - `cases/C-2026-RF000441-乾-癸亥己未己未庚午/analysis.md`
  - `cases/C-2026-RF000441-乾-癸亥己未己未庚午/feedback.md`
  - `cases/C-2026-RF000441-乾-癸亥己未己未庚午/statement_index.json`
- 操作步骤：
  - [ ] 创建目录 cases/C-2026-RF000441-乾-癸亥己未己未庚午
  - [ ] 生成 cases/C-2026-RF000441-乾-癸亥己未己未庚午/input.md：从 staging 排盘与草稿 birth/known_facts 合并
  - [ ] 生成 cases/C-2026-RF000441-乾-癸亥己未己未庚午/analysis.md：记录来源、转案说明与待分析占位
  - [ ] 生成 cases/C-2026-RF000441-乾-癸亥己未己未庚午/feedback.md：迁移原 known_facts 并保留 raw_id 追踪
  - [ ] 生成 cases/C-2026-RF000441-乾-癸亥己未己未庚午/statement_index.json：初始化 statement 追踪骨架
  - [ ] 运行 python -m tools.preflight cases/C-2026-RF000441-乾-癸亥己未己未庚午/input.md


### 3. RF-2026-000864 → C-2026-RF000864-乾-己巳丙子乙卯甲申

- 目标目录：`cases/C-2026-RF000864-乾-己巳丙子乙卯甲申`
- 来源草稿：`cases/raw_feedback/case_drafts/RF-2026-000864/input.md`
- 来源索引：`cases/raw_feedback/case_drafts/wenzhen-repan-index-male.md`
- 事件数：18 / 草稿事实数：18
- 目标文件：
  - `cases/C-2026-RF000864-乾-己巳丙子乙卯甲申/input.md`
  - `cases/C-2026-RF000864-乾-己巳丙子乙卯甲申/analysis.md`
  - `cases/C-2026-RF000864-乾-己巳丙子乙卯甲申/feedback.md`
  - `cases/C-2026-RF000864-乾-己巳丙子乙卯甲申/statement_index.json`
- 操作步骤：
  - [ ] 创建目录 cases/C-2026-RF000864-乾-己巳丙子乙卯甲申
  - [ ] 生成 cases/C-2026-RF000864-乾-己巳丙子乙卯甲申/input.md：从 staging 排盘与草稿 birth/known_facts 合并
  - [ ] 生成 cases/C-2026-RF000864-乾-己巳丙子乙卯甲申/analysis.md：记录来源、转案说明与待分析占位
  - [ ] 生成 cases/C-2026-RF000864-乾-己巳丙子乙卯甲申/feedback.md：迁移原 known_facts 并保留 raw_id 追踪
  - [ ] 生成 cases/C-2026-RF000864-乾-己巳丙子乙卯甲申/statement_index.json：初始化 statement 追踪骨架
  - [ ] 运行 python -m tools.preflight cases/C-2026-RF000864-乾-己巳丙子乙卯甲申/input.md


### 4. RF-2026-000243 → C-2026-RF000243-坤-己卯己巳戊午丁巳

- 目标目录：`cases/C-2026-RF000243-坤-己卯己巳戊午丁巳`
- 来源草稿：`cases/raw_feedback/case_drafts/RF-2026-000243/input.md`
- 来源索引：`cases/raw_feedback/case_drafts/wenzhen-repan-index-female.md`
- 事件数：16 / 草稿事实数：16
- 目标文件：
  - `cases/C-2026-RF000243-坤-己卯己巳戊午丁巳/input.md`
  - `cases/C-2026-RF000243-坤-己卯己巳戊午丁巳/analysis.md`
  - `cases/C-2026-RF000243-坤-己卯己巳戊午丁巳/feedback.md`
  - `cases/C-2026-RF000243-坤-己卯己巳戊午丁巳/statement_index.json`
- 操作步骤：
  - [ ] 创建目录 cases/C-2026-RF000243-坤-己卯己巳戊午丁巳
  - [ ] 生成 cases/C-2026-RF000243-坤-己卯己巳戊午丁巳/input.md：从 staging 排盘与草稿 birth/known_facts 合并
  - [ ] 生成 cases/C-2026-RF000243-坤-己卯己巳戊午丁巳/analysis.md：记录来源、转案说明与待分析占位
  - [ ] 生成 cases/C-2026-RF000243-坤-己卯己巳戊午丁巳/feedback.md：迁移原 known_facts 并保留 raw_id 追踪
  - [ ] 生成 cases/C-2026-RF000243-坤-己卯己巳戊午丁巳/statement_index.json：初始化 statement 追踪骨架
  - [ ] 运行 python -m tools.preflight cases/C-2026-RF000243-坤-己卯己巳戊午丁巳/input.md


### 5. RF-2026-000524 → C-2026-RF000524-坤-己巳丙寅戊戌丁巳

- 目标目录：`cases/C-2026-RF000524-坤-己巳丙寅戊戌丁巳`
- 来源草稿：`cases/raw_feedback/case_drafts/RF-2026-000524/input.md`
- 来源索引：`cases/raw_feedback/case_drafts/wenzhen-repan-index-female.md`
- 事件数：16 / 草稿事实数：16
- 目标文件：
  - `cases/C-2026-RF000524-坤-己巳丙寅戊戌丁巳/input.md`
  - `cases/C-2026-RF000524-坤-己巳丙寅戊戌丁巳/analysis.md`
  - `cases/C-2026-RF000524-坤-己巳丙寅戊戌丁巳/feedback.md`
  - `cases/C-2026-RF000524-坤-己巳丙寅戊戌丁巳/statement_index.json`
- 操作步骤：
  - [ ] 创建目录 cases/C-2026-RF000524-坤-己巳丙寅戊戌丁巳
  - [ ] 生成 cases/C-2026-RF000524-坤-己巳丙寅戊戌丁巳/input.md：从 staging 排盘与草稿 birth/known_facts 合并
  - [ ] 生成 cases/C-2026-RF000524-坤-己巳丙寅戊戌丁巳/analysis.md：记录来源、转案说明与待分析占位
  - [ ] 生成 cases/C-2026-RF000524-坤-己巳丙寅戊戌丁巳/feedback.md：迁移原 known_facts 并保留 raw_id 追踪
  - [ ] 生成 cases/C-2026-RF000524-坤-己巳丙寅戊戌丁巳/statement_index.json：初始化 statement 追踪骨架
  - [ ] 运行 python -m tools.preflight cases/C-2026-RF000524-坤-己巳丙寅戊戌丁巳/input.md


## 人工批准清单

- [ ] 确认首批 5 个 raw_id 均允许转正式 case。
- [ ] 确认目标目录命名策略 `C-2026-RFxxxxxx-乾/坤-四柱`。
- [ ] 确认转案时保留 raw_id、源草稿、源索引、复核包路径。
- [ ] 批准后再执行真实创建脚本或手工创建。

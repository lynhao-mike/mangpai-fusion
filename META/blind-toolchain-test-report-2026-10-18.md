# 盲测工具链回归测试报告（2026-10-18）

## 交付

- 新建 [tests/tools/test_blind_toolchain.py](../tests/tools/test_blind_toolchain.py)，**50 个测试**（含参数化展开），全绿。
- `python -m pytest tests/tools/test_blind_toolchain.py -q` → **50 passed**。
- `python -m pytest tests/tools/ -q` → 247 passed, 1 failed；唯一失败为既有测试
  `test_wp7_toolchain.py::test_all_rules_have_traceable_bodies[duan-M1-D--290]`
  （段派规则体不可追溯），与本批新增文件无关、非本次引入，未动。
- 未修改 tools/ 下任何被测工具；测试全部用 `tmp_path` + monkeypatch 替换各模块
  `CASES/PROBES/OUT` 常量，不依赖真实 `cases/`。

## 覆盖

| 工具 | 覆盖点 |
|---|---|
| blind_year_probe | _detect_columns 格式A/格式B、classify 前缀/关键词计票/mixed、load_events 两格式、pick_exam_years 平稳年不与记录年重叠 |
| blind_year_score | canon_polarity 吉凶平↔positive/negative/neutral、_same_person_groups 同生日同组、对照年 recorded=False → undetermined 不进分母 |
| blind_candidate_pick | tier_of 四档边界（7/6/4/3/<3）、pick 三层均衡配额与候选不足回填、collect_candidates 排除逻辑 |
| verify_year_judgments | 年份缺失/多余 FAIL、polarity 非法 FAIL、basis 无盘面引用 FAIL、骑墙词 FAIL、完全合法 PASS |
| blind_exam_generator | 同一 case_id 两次生成完全一致（种子确定性） |

## 发现的工具 bug（未修，仅记录）

1. **`blind_year_score._same_person_groups()`**：遍历 probes 目录名，却读 `CASES/<同名>/input.md` 取生日——两个目录名必须严格一致，probes 下多出的目录被静默跳过。耦合脆弱，当前数据可用。
2. **`blind_year_probe._detect_columns()`**：同一表头单元格同时含「事实/事件」与「域/类型」关键词时优先记为文本列，极端表头可能误判（边界隐患，现行数据未触发）。

## 与任务书描述不符的源码行为（以源码为准，测试按源码写）

1. `verify_year_judgments` 的 basis 无引用报错文案是「未引用边号或地址」；地址正则只认 `Y./M./D./H.` 与 `DY/LN` 模式，普通干支文字不算引用。
2. `verify_year_judgments` 额外校验「判平但 matters 非空 → FAIL」（任务书未列，合理增强）。
3. `blind_exam_generator.generate` 有门槛：生成题目 <3 时 SKIP 返回 False，确定性测试的 feedback 需覆盖学业+事业+流年事件。
4. 对照年（recorded=False）判凶时 verdict 为 `undetermined`、不进 incorrect 分母，只计 `control_false_positive`——与任务书一致，已覆盖测试。

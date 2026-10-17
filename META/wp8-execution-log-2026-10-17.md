# WP-8 执行留档 · 2026-10-17

> 本文件记录 WP-8「让八字分析说人话」改造的执行结果与仓库状态，供后续会话接续。
> 定稿提示词：[`plans/wp8-human-touch-reform-prompt-v9.md`](../plans/wp8-human-touch-reform-prompt-v9.md)（v2–v8 已删除，作废）。

## 1. 执行结果（全部完成）

| # | 交付物 | 状态 |
|---|---|---|
| 1 | `docs/analysis_human_touch.md` | v1（91 行）升级为 v7 契约版 |
| 2 | `templates/report-v7-human.md` | 新建 |
| 3 | `docs/agent_tools.md` | 五步 SOP 后新增 Step 6（六条义务 + 两句前置声明） |
| 4 | `AGENTS.md` | 导航图 +3 行；争议处理原则 +1 条 |
| 5 | `reports/README.md` | 统一为 v7 单报告默认唯一主产物架构 |
| 6 | `tools/human_touch_linter.py` | 零第三方依赖，含 `_contract_health()` 契约自检 |
| 7 | `tests/tools/test_human_touch_linter.py` | 正例×2 + 反例×12 + 契约测试×1 = 17 tests |
| 8 | `pyproject.toml` | `testpaths` 注册新测试文件 |
| 9 | `reports/1980-02-09-乾-庚申戊寅壬子辛丑-human-report.md` | 案例 A，0 ERROR |
| 10 | `reports/1980-02-09-四柱-庚申戊寅壬子辛丑-human-report.md` | 案例 B，0 ERROR |
| 11 | `reports/1984-11-05-乾-甲子甲戌癸卯壬戌-人情味分析.md` | 最小修复后 0 ERROR |

## 2. 验证结果

```
python -m tools.human_touch_linter <3 份报告>   → 全部 OK（0 ERROR）
python -m pytest tests/tools/test_human_touch_linter.py -q  → 17 passed
python -m pytest -q                             → 127 passed
```

红线核验：`engine/`、`tools/query_theory.py`、`tools/output_linter.py`、`tools/render_report.py`、`cases/` **零改动**。

## 3. 执行中对 v9 预扫描的 3 处修正（均按实跑）

| v9 预扫描 | 实测 | 处置 |
|---|---|---|
| 1984 报告"仅 3d 触发新规，检查 1 零命中" | L66/L68 有「很可能」「都可能」 | 正文两处改确定表述 |
| 案例 A/B 按模板写即可通过 | 案例 B L38「业务方向可能整体切换」触发检查 1 | 改为确定表述 |
| 正例 1 内嵌样例合法 | L34「关键应期与相处建议」行动词在后续句 | 动词调到同一行 |

三处均非 Linter 误报，是规范在生效。

## 4. 未提交清单（截至 2026-10-17）

修改 4 个文件 + 新建 7 项，均在工作区未提交：

```
 M AGENTS.md
 M docs/agent_tools.md
 M pyproject.toml
 M reports/README.md
?? docs/analysis_human_touch.md
?? templates/report-v7-human.md
?? tools/human_touch_linter.py
?? tests/tools/test_human_touch_linter.py
?? plans/wp8-human-touch-reform-prompt-v9.md
?? reports/1980-02-09-乾-庚申戊寅壬子辛丑-human-report.md
?? reports/1980-02-09-四柱-庚申戊寅壬子辛丑-human-report.md
?? reports/1984-11-05-乾-甲子甲戌癸卯壬戌-人情味分析.md
```

## 5. 遗留事项

- 上述改动尚未 `git add` / 提交。
- `tools/render_report.py` 仍只渲染 v6（WP-8 红线不改）；若需流水线也出 v7，须另立任务。
- `tools/output_linter.py` 未加人话规则转发；历史存量 v6 报告若接入会大面积报警，需先定"只查新增"策略。

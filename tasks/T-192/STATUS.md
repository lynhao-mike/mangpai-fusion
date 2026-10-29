# T-192 STATUS

- 状态：🟡 **交付待验收**（2026-10-29，子代理 AR）
- 执行者：子代理 AR
- 验收：中枢亲自看；归档/规格/泄漏；`python tasks\T-192\verify.py` + `python -m pytest -q`
- 边界：只按 T-192 卡；不做方向、不改 engine、不跑盲测、不做 git 写

## Execution Log

| 时间 | 动作 |
|---|---|
| 20:20 | 人类同意 R-tool+B；建卡派发 |
| 20:22 | 读 `tasks/T-192/PROMPT.md`、A+ 规格/notes、T-191 verdict、demo md、`META/single-chart-cards-v1.json`；核对工作区已有 dirty 文件（answers/holdout/_tmp_t190b，非本卡所为） |
| 20:25 | 建 `archive/adjudication_v1/`（README/ANCHOR/anchor/t191-runs/scorers/restricted）；`archive/demo/` 原样复制 3 卡；记录 17 项 sha256 |
| 20:28 | A+ 规格加 `DISPOSITION: KILLED`；notes §5 删除具体 case ID/端点/答案；demo 原件加 `STATUS: ARCHIVED_RESEARCH_ARTIFACT` |
| 20:30 | 生成 `labels-v1.json`（60 条）、`contamination-list-v1.json`（A60-020/046/050）；ANCHOR 60 行标 3 条 `contaminated` |
| 20:32 | 新增 `tools/check_bundle_case_ids.py`；合成 fixture 冒烟（dir/zip/缺失目标：0/1/2）通过；未扫真实 bundle |
| 20:33 | 写 `docs/specs/fact-evidence-pack-v1.md`（范围/输出/类外零发射/不断语/保护区/第一证明点） |
| 20:34 | 写 `tasks/T-192/verify.py`；首跑 11/12（BRIEF 未写），补 BRIEF 后待复跑 |
| 20:36 | 启动全仓 `python -m pytest -q`；写 BRIEF；待复跑 verify + 填回归结果 |
| 20:39 | 全仓回归 **1569 passed, 1 skipped**（151.10s，exit 0；skip 为 T-114 既有）；复跑 `verify.py` 待记录 |
| 20:40 | `verify.py` 复跑 **12/12 PASS**（exit 0）；删除一次性生成脚本；交付 BRIEF/STATUS，待中枢验收 |
| 20:50 | R 规格措辞修正（fixed 方向对错不计入门禁）后最终复跑 `verify.py` → **12/12 PASS**；无新增改动 |

## 待中枢决定

1. answers 三值 hash 不一致（冻结记录 `4c6ee69a…` / 工作区 `754caa14…` / HEAD `9fd63ada…`）：归档取工作区版本，未改答案。
2. 工作区进入本卡时的 dirty 文件（`META/p1-anchor-60-answers-final-v2.json` 等）非本卡改动；未回滚、未提交。
3. `tasks/T-191/BRIEF-r*.md` 仍含 notes §5 的旧方向复述；本卡按范围只修 notes §5，未改 T-191 原文。

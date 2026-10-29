# T-192 · BRIEF · 归档 + 泄漏修复 + R 规格

- 执行者：子代理 AR
- 日期：2026-10-29
- 状态：**交付待中枢验收**（只按 T-192 卡；不做方向、不改 engine、不跑盲测、不做 git 写）
- 验证：`python tasks\T-192\verify.py` → **12/12 PASS**；`python -m pytest -q` → 见 §2

## 1. 改动文件

| 文件 | 动作 | 说明 |
|---|---|---|
| `archive/adjudication_v1/README.md` | 新建 | 归档索引：A+ kill 五项指标、目录、污染、读取规则、完整性差异、验证 |
| `archive/adjudication_v1/ANCHOR.md` | 新建 | anchor-60 归档锚点：60 行 case_id/layer/chart_id；A60-020/046/050 标 `contaminated` |
| `archive/adjudication_v1/MANIFEST.sha256` | 新建 | 17 个归档文件的全量 sha256 |
| `archive/adjudication_v1/adjudication-a-plus-v1.md` | 复制 | A+ v1.3 规格副本（头部含 `DISPOSITION: KILLED`） |
| `archive/adjudication_v1/t191-a-plus-verdict-v1.md` | 复制 | T-191 裁决副本 |
| `archive/adjudication_v1/anchor/p1-anchor-60-blind-final-v2.json` | 复制 | blind final v2（sha256 `cc88d10e…`） |
| `archive/adjudication_v1/anchor/p1-anchor-60-final-v2.md` | 复制 | final v2 说明（含冻结 hash 记录） |
| `archive/adjudication_v1/t191-runs/p1-system-run-r1.json` | 复制 | T-191 三跑（r1） |
| `archive/adjudication_v1/t191-runs/p1-system-run-r2.json` | 复制 | T-191 三跑（r2） |
| `archive/adjudication_v1/t191-runs/p1-system-run-r3.json` | 复制 | T-191 三跑（r3） |
| `archive/adjudication_v1/scorers/p1_assertion_eval.py` | 复制 | T-186 评分器（只归档；主测试未移动） |
| `archive/adjudication_v1/scorers/p1_assertion_eval_v2.py` | 复制 | T-191 所用评分器（T-189b v2；只归档） |
| `archive/adjudication_v1/restricted/README.md` | 新建 | 受限区规则：runner 不可读、不得打包 |
| `archive/adjudication_v1/restricted/p1-anchor-60-answers-final-v2.json` | 复制 | 实际评分所用 final v2 答案 |
| `archive/adjudication_v1/restricted/p1-anchor-60-answers-B-v1.json` | 复制 | annotator B 答案（A/B 留证） |
| `archive/adjudication_v1/restricted/p1-anchor-60-answers-v1.json` | 复制 | annotator A 初版答案（历史） |
| `archive/adjudication_v1/restricted/labels-v1.json` | 新建 | 从 final v2 提取的 60 条评分标签（受限） |
| `archive/adjudication_v1/restricted/contamination-list-v1.json` | 新建 | A60-020/046/050：`contaminated` + 永久排除 |
| `archive/demo/README.md` | 新建 | 3 卡封存说明 |
| `archive/demo/single-chart-cards-v1.md` | 复制 | 3 卡原样副本（复制时未改内容） |
| `archive/demo/single-chart-cards-v1.json` | 复制 | 3 卡机器副本（复制时未改内容） |
| `docs/specs/adjudication-a-plus-v1.md` | 修改 | 头部加 `DISPOSITION: KILLED` |
| `docs/specs/adjudication-a-plus-v1-notes.md` | 修改 | §5 删除 3 条具体 case ID/端点/答案，只留「A/B 3 条分歧，细节在 restricted」 |
| `docs/demo/single-chart-cards-v1.md` | 修改 | 头部加 `STATUS: ARCHIVED_RESEARCH_ARTIFACT` |
| `META/single-chart-cards-v1.json` | 修改 | 头部加 `"STATUS": "ARCHIVED_RESEARCH_ARTIFACT"`（内容未改造） |
| `docs/specs/fact-evidence-pack-v1.md` | 新建 | R-tool 规格：范围/输出/类外零发射/不断语/保护区/第一证明点 |
| `tools/check_bundle_case_ids.py` | 新建 | 标准库 bundle 泄漏门禁：命中 `A60-/PF-/P1-H/G20` 即 exit 1 |
| `tasks/T-192/verify.py` | 新建 | 标准库验收：归档哈希/脱敏/状态/污染/合成扫描 fixture |
| `tasks/T-192/BRIEF.md` | 新建 | 本文件 |
| `tasks/T-192/STATUS.md` | 修改 | 状态 + Execution Log |

**未改**：`AGENTS.md`、`CLAUDE.md`、`templates/report-v7-human.md`、`docs/analysis_human_touch.md`、`engine/**`、任何答案内容（只复制）、`tests/**`、`pyproject.toml`、`requirements*.txt`、`theory/_ir/**`、`sources/**`、`META/project-state.json`、任何 `tasks/*/PROMPT.md`。未做 git 写操作。

## 2. 原始输出

### 2.1 归档验收

```text
> .venv\Scripts\python.exe tasks\T-192\verify.py
PASS required_files
PASS archive_manifest
PASS archive_copies
PASS demo_archive
PASS disposition_killed
PASS notes_section5_redaction
PASS anchor_contamination
PASS restricted_boundary
PASS archive_readme
PASS r_spec
PASS bundle_scanner_synthetic
PASS task_docs

PASS: 12/12 checks
```

### 2.2 bundle 扫描合成测试

`verify.py` 用临时目录/临时 zip 调 `python -m tools.check_bundle_case_ids`，**未扫任何真实 bundle**：

| fixture | 期望 | 实测 |
|---|---:|---:|
| 干净目录（仅 `A60 combat/PFAS/G20 summit/P1-H` 普通词） | 0 | 0 |
| 干净 zip | 0 | 0 |
| 目录含 `A60-001` | 1 | 1 |
| 目录含 `A60-CH01`（chart_id 也拦） | 1 | 1 |
| 目录含 `P1-H01` | 1 | 1 |
| zip 内容含 `PF-007` + 条目名 `G20-003.json` | 1 | 1 |
| 不存在的目标 | 2 | 2 |

命中时输出 `CASE_ID_FOUND <id> in <path>` + `FAIL: …`；干净时输出 `OK: …`。

### 2.3 回归

```text
> .venv\Scripts\python.exe -m pytest -q
SKIPPED [1] tests\tools\test_bundle_pii.py:34: （T-114 过渡 skip，既有）
1569 passed, 1 skipped, 1 warning in 151.10s (0:02:31)
```

- 退出码 0；skip 为 T-114 既有过渡 skip（`.workbuddy-ai/make_bundle_v2.py` 缺失），非本卡引入。
- 本卡未改测试/engine；新增工具未被 pytest 收集，回归数与 T-189b 验收时一致（1569/1）。

### 2.4 关键哈希

- 归档 blind：`cc88d10ea15ac68c72bcb82ac1ba982ab177e169e678897bfd6f2010aadb7292`
- 归档 answers（工作区形状）：`754caa14f4fcffb36385bebf636eef150ae8f6c967fa539463f42ddde6c189d2`
- 归档 A+ 规格：`95b06d41fa130ba63eb5562ebdfe8b37c713f89124f5f8fb91cc4ef85b6c79b3`
- demo md：`6695e45058eaf3b06f4063cf3a9b067df11ccce2776e42cf3018078ecd8761e7`
- demo json：`a644b900fd8adc53662a64f90e85fbaa53e26663a96e2dae4e21106556798e65`
- 全量：`archive/adjudication_v1/MANIFEST.sha256`

## 3. 未完成与风险

1. **answers 三值 hash 不一致（未修，按卡不动答案）**：
   - `META/p1-anchor-60-final-v2.md` 记录的冻结值：`4c6ee69a…`；
   - 工作区 `META/p1-anchor-60-answers-final-v2.json`（schema `p1-adjudication-answers/v2`，scorer v2 实际读取形状）：`754caa14…`；
   - 仓库 HEAD 版本（旧 schema `p1-anchor-60-answers/v1`）：`9fd63ada…`。
   归档取工作区版本，三值写进 README §5/ANCHOR/本 BRIEF，**未做合并或改写**；需中枢决定以哪个为冻结件。
2. **工作区进入 T-192 时已有未提交改动（非本卡所为）**：
   `META/p1-anchor-60-answers-final-v2.json`、`META/p1-holdout-baseline-v1.json`、`META/p1-holdout-baseline-v1.md`、`_tmp_t190b/`、`tasks/T-190b/verify_b.py`、`mangpai-fusion-offline-*.zip`。本卡只读/复制，未回滚、未提交。
   执行期间并发任务又产生 `META/fact-audit-v1.json`、`.tmp-t194/`、`_tmp_t193/`（T-193/T-194），同样非本卡改动。
3. **A/B 复核 BRIEF/STATUS 未复制进归档**：只归档 T-191 三份 run 输出。`tasks/T-191/BRIEF-r*.md` 含 notes §5 泄漏方向的复述（例如 A60-020 的取向），复制会二次扩散；需要时在受限区另行处理，本卡未动 T-191 原文。
4. **scanner 限制（已写入 docstring/规格）**：不展开目录内嵌套 zip；单文件/单条目 >64 MiB 直接 exit 2（fail closed）；前缀匹配较宽（`A60-CH01` 这类 chart_id 也会命中），这是有意的泄漏闸门。
5. **未跑真实 bundle 扫描**（按卡）；未跑盲测/评分器；未改 engine/答案/测试。
6. **3 张旧卡**：原件只加状态头，`archive/demo/` 保存复制前原样；未改卡内内容。
7. **notes §5 之外的旧泄漏面**：`tasks/T-191/BRIEF-r*.md` 仍可被读过的人检索到；本卡按范围只修 notes §5，未改 `tasks/` 原文。
8. **归档元数据**（`labels-v1.json` / `contamination-list-v1.json` / `ANCHOR.md`）由一次性脚本生成后删除；生成结果已固化，并由 `MANIFEST.sha256` 校验。

## 4. 下游须知

1. 中枢验收先跑 `.venv\Scripts\python.exe tasks\T-192\verify.py`，再跑 `python -m pytest -q`；不要只信本 BRIEF 文字。
2. `docs/specs/fact-evidence-pack-v1.md` 是 T-193/T-194 的前置规格；第一证明点冻结为：
   - T-193 事实审计 **差异 0/全部字段**；
   - T-194 fixed-20 **每条 ≥1 条目标固定类 + `out_of_class_emissions = 0`**；
   - T-194 分流召回 **≥80% pass / <60% kill / 60–79% 灰**，先写 `META/routing-prereg-v1.json`。
3. 任何 runner/演示 bundle 交付前必须跑 `python -m tools.check_bundle_case_ids <zip|dir>` 且 exit 0；`archive/adjudication_v1/restricted/` 永远不得打包。
4. 不要对 `archive/` 跑 case-id 扫描：`ANCHOR.md`/README 为治理有意保留 case_id 与 `contaminated` 标记。
5. R-tool 不套 `report-v7-human`，不输出冲/合/穿/刑方向或断语；3 张旧卡（C1/C2/C3）不进演示。
6. 污染 3 条（A60-020/046/050）永久排除；不要换 ID、改名或换层重新引入。

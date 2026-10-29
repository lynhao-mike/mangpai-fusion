# T-171 · Kill List 依赖审计（只读，不删除）

- 状态：🔵 Ready for Execution
- 优先级：**P0（清场前的安全检查）**
- 创建：2026-10-29（中枢）
- 依据：`docs/reviews/external-audit-adjudication-v2.md` §3
- 前置：无

## 0. 一句话

外部方向审计要求「删掉 85% 的旧层」；本卡先回答**谁在用谁**：哪些模块被 `engine/facts`、
`engine/api`、`engine/cli`、`tools/engine_audit`、`tools/relations_audit`、`tools/query_theory`
直接/间接 import；哪些可以安全归档；哪些一动就会打破 481 盘 0 错。
**只读审计，不移动、不删除任何文件。**

## 1. 审计对象（Kill List）

- 聚合规则/假断语层：`theory/production/claim-rules-v1.yaml`、`engine/claims/rule_loader.py`、
  `theory/claims/conditions-v2/pilot-20.yaml`、`engine/claims/condition_ir/`
- 旧架构层：`engine/v5/`、`engine/v2/`、`engine/f09/`、`engine/governance/`、`engine/learning/`、
  `engine/asof/`、`engine/decision/`、`engine/energy/`、`engine/picture/`、`engine/yingqi/`
- 已判死工具：`tools/timing_model_v1.py`、`tools/domain_labels_wealth_health*.py`、
  `tools/career_label_feasibility.py`、`tools/career_path_*.py`、`tools/m2y395_*.py`
- 脚手架测试：`tests/f09/`、`tests/governance/`、`tests/v5/`、`tests/asof/`、`tests/evaluation/`
- 过程文档：`plans/`（只列，不删）

## 2. 审计方法

1. 静态 import 图：从 `engine/facts`、`engine/api`、`engine/cli.py`、`tools/engine_audit.py`、
   `tools/relations_audit.py`、`tools/query_theory.py` 出发，递归解析 `from ... import`；
2. 反向引用：每个 Kill List 模块被谁 import（含测试、工具、文档脚本）；
3. 运行期依赖：`python -m engine.cli all` / `engine_audit` / `relations_audit` 是否实际走到；
4. 测试依赖：`tests/facts`、`tests/api` 等「尺子」是否 import 被删模块；
5. 按「安全归档 / 有引用（需先改） / 尺子在用 / 不可判」四类给出裁决。

## 3. 产物

- `META/kill-list-dependency-audit-v1.json`：模块清单、入边/出边、分类、建议顺序
- `META/kill-list-dependency-audit-v1.md`：人读报告、分批归档顺序、风险
- 可选 `tests/tools/test_kill_list_dependency_audit.py`（确定性）

## 4. File Scope

**允许新建**

- `tools/kill_list_dependency_audit.py`
- `META/kill-list-dependency-audit-v1.json`
- `META/kill-list-dependency-audit-v1.md`
- `tests/tools/test_kill_list_dependency_audit.py`（可选）

**只读**

- 全仓源码/测试/文档（`sources/` 只读，不解析原文）
- `pyproject.toml`、`AGENTS.md`、`docs/handoff-hub-v2.md`

**禁止**

- 移动/删除/重命名任何文件；改 `engine/**`、规则、测试、docs
- 跑模型/评分/建盘；`git commit / push / checkout / stash / reset / clean`

## 5. 验收（中枢亲自看）

1. 从 6 个硬入口出发的递归 import 图完整；
2. 每个 Kill List 模块有「被谁引用 / 是否被 facts/api/cli 依赖 / 建议」；
3. 明确列出「一动就破 481/0」的模块（若有）；
4. 给出分批归档顺序（先安全、再有引用、最后不可判）；
5. 没有改任何文件；`pytest -q` 不受影响。

## 6. 回报格式（`tasks/T-171/BRIEF.md` + `STATUS.md`）

1. **改动文件**
2. **原始输出**（模块数、四类计数、关键入边）
3. **未完成与风险**（动态 import、字符串引用、测试夹具）
4. **下游须知**（第一批可安全归档的模块、必须保留的模块）

## 7. 禁止

- 不许在本卡里删除/移动任何东西。
- 不许把「看起来没人用」当成「安全」——必须有 import/运行期证据。

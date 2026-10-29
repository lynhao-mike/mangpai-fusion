# T-195b · routing 干净重跑（fixed-20 不重跑）

- 状态：🔵 Ready
- 依据：T-195 fixed-20 已接受（20/20、类外0）；routing 因 `expected_evidence` 泄漏作废
- 前置：`META/routing-questions-runner-v1.json`（15 题、4 字段、hash `fd2876ad…`）

## 0. 一句话

干净会话只读 **sanitized runner 文件** + `tasks/T-195/run_r_tool.py` 的可见字段逻辑；
重跑 15 题证据包；**不读 expected_evidence/answers/prereg**；不测方向；不做 git 写。

## 1. 输入

- `META/routing-questions-runner-v1.json`：只含 `question_id/domain/question/chart`；**无 expected_evidence**；
- `docs/specs/fact-evidence-pack-v1.md`；
- `engine.cli`、`query_theory`、`sources/`；
- **禁止**：`META/routing-questions-v1.json`（含 expected）、`META/routing-prereg-v1.json`、任何 answers/fixed-20 answers/anchor/fresh/holdout/golden/`p1-system-run*`。

## 2. 任务

- 15 题各输出证据包：宫位、关系边 ID、source_ref 区间；只做证据，不做方向/断语/主次裁决；
- 复用 `tasks/T-195/run_r_tool.py` 的生成逻辑，但输入改 sanitized 文件；输出 `META/r-tool-run-routing-v1.json`；
- 不重跑 fixed-20；不评分；不自评。

## 3. 产物

- `META/r-tool-run-routing-v1.json`（15 包、证据项计数）
- `tasks/T-195b/BRIEF.md` + `STATUS.md`；hash
- 不跑评分器；不做 git 写。

## 4. 验收

- 读隔离：未读 expected/prereg/answers；BRIEF 声明；
- 15/15 包；证据项可解析；无方向/断语；
- 中枢用 `META/routing-prereg-v1.json` 的 97 项算 macro_recall：≥0.80 pass、<0.60 kill、0.60–0.79 gray。

# G10-R1 · F09 Production-Readiness Admission 与 Sanity Failure Closeout

- 记录日期：2026-07-27（Asia/Shanghai）
- 依据计划：[`g10-next-governance-milestone-plan.md`](g10-next-governance-milestone-plan.md)
- 本地状态：**`LOCAL ONLY / NOT PUSHED / NO GITHUB MUTATION`**
- 本次未执行任何 Git 命令，未执行任何 GitHub 读写或服务端操作。

## 1. G10.0 RECOVER 基线

按用户指定顺序读取 [`production-implementation-control.md`](production-implementation-control.md) §3、§8、[`g6-task9p-total-gate-upgrade-review.md`](g6-task9p-total-gate-upgrade-review.md)、[`g10-next-governance-milestone-plan.md`](g10-next-governance-milestone-plan.md)，并按仓库事实源纪律读取 [`README.md`](../README.md)、[`AGENTS.md`](../AGENTS.md)、[`META/project-state.json`](../META/project-state.json)、[`STATUS.md`](../STATUS.md)、[`tools/README.md`](../tools/README.md)。确认：

- Task 9-P total-Gate 现行裁决为 `PASS / COMPLETE — EVIDENCE-BOUNDED FREEZE`（§8.8），§8.7 历史 `REVISE` 保留不倒写；
- G6–G9 `COMPLETED` 只覆盖既列 F09 行为与隔离证据；
- 两个非 F09 sanity 失败在 §8.5 登记为未解决，本轮 RECOVER 时九份 Task 9-P 专项冻结文件未被观察到在既有裁决后修改（非 Git 文件元数据 + SHA-256 核对一致）。

## 2. G10.1 Production-readiness INVENTORY

十二证据域状态标记（`PROVEN` / `NOT_REQUIRED` / `REQUIRES_LOCAL_GATE` / `REQUIRES_EXTERNAL_DECISION` / `BLOCKED_BY_PROHIBITION` / `UNKNOWN`）：

| # | 证据域 | 状态 | 依据 |
|---|---|---|---|
| 1 | 行为范围 | `PROVEN`（有界） | [`tests/f09`](../tests/f09/) fresh 1172 passed；未执行部分不外推 |
| 2 | 全仓兼容 | `PROVEN`（本轮闭合） | 全仓 fresh `3121 passed, 7 skipped, 1 warning`，两个原失败已闭合 |
| 3 | skipped 场景 | `PROVEN`（已归因） | 7 个 skipped 均为已知静态类别：as-of 证据不足、report-v5/legacy 模板已删除、iron 断语/关键应期覆盖率条件跳过、真实报告文件缺失；无新增未知 skip |
| 4 | 配置与默认值 | `PROVEN`（有界） | [`tests/f09/test_production_isolation.py`](../tests/f09/test_production_isolation.py) 等隔离证据 |
| 5 | 持久化与恢复 | `PROVEN`（有界） | [`engine/f09/artifacts.py`](../engine/f09/artifacts.py) retry/idempotency/attempt ledger 静态与测试证据 |
| 6 | 运行环境 | `REQUIRES_EXTERNAL_DECISION` | 密钥、权限、外部服务非本地测试可证 |
| 7 | 观测性 | `PROVEN`（有界） | G10-R2 D1–D5 已由 [`g10-r2-f09-operator-diagnosability-report.md`](g10-r2-f09-operator-diagnosability-report.md)、[`f09-operator-diagnosability-runbook.md`](../docs/f09-operator-diagnosability-runbook.md) 与 [`test_operator_diagnosability_readiness.py`](../tests/f09/test_operator_diagnosability_readiness.py) 本地验收；仅覆盖合法 artifact root 下受控 phase observation 与 artifact attempt 联查，不外推部署、性能、外部环境或 F10 |
| 8 | 性能与资源 | `PROVEN`（有界，仅测量能力，无 SLO 判据） | G10-R3 已由 [`g10-r3-f09-performance-resource-observation-contract.md`](g10-r3-f09-performance-resource-observation-contract.md)、[`g10-r3-f09-performance-resource-observation-report.md`](g10-r3-f09-performance-resource-observation-report.md) 与 [`test_performance_resource_observation.py`](../tests/f09/test_performance_resource_observation.py) 两轮本地快照证明 cold/repeat 五阶段墙钟、`tracemalloc` 峰值及 artifact/observation I/O 计数能力；仅为当前本地固定 fixture 的数据快照，不构成性能达标、不达标、稳定性、容量、跨平台、部署环境或 F10 readiness 声明 |
| 9 | 安全与信任边界 | `PROVEN`（本轮闭合） | witness trust-boundary 文案已补齐并 fresh 验证 |
| 10 | 回滚与故障隔离 | `PROVEN`（有界） | no-rollback-overwrite、fail-closed validation 测试证据 |
| 11 | 版本与 provenance | `BLOCKED_BY_PROHIBITION` | 本任务禁止一切 Git 命令 |
| 12 | 部署/发布 | `REQUIRES_EXTERNAL_DECISION` | 外部能力，不由本地测试替代 |

`PROVEN + NOT_REQUIRED` 计数不自动推出生产就绪；材料性裁决见第 5 节。

## 3. G10.2 Sanity failure triage

### 3.1 失败 1：witness trust-boundary 文档缺口

- selector：`python -m pytest tests/evaluation/test_dataset.py::test_witness_trust_boundary_is_explicitly_documented -q`
- fresh 复现（修复前）：exit 1，1 failed，0.33s；断言缺失 [`tools/README.md`](../tools/README.md) 中 7 个精确术语。
- 归因：documentation contract gap，与 F09 无因果关系。
- 最小修复：仅在 [`tools/README.md:204`](../tools/README.md:204) 把既有小节标题改为「受信独立见证边界（Witness HMAC 可选审计）」，正文语义不变（原文已含全部 7 个术语的等价表述）。
- fresh 复现（修复后）：exit 0，1 passed，0.11s。

### 3.2 失败 2：prospective handoff 文档缺口

- selector：`python -m pytest tests/evaluation/test_prospective_gate_workflow.py::test_handoff_names_first_legal_case_action_and_all_independent_holds -q`
- fresh 复现（修复前）：exit 1，1 failed，0.87s；断言缺失首案 v004 动作与三个独立 HOLD 文案。
- 归因：documentation contract gap，与 F09 无因果关系。权威事实来源为 [`META/project-state.json`](../META/project-state.json:68)（首案父链 v004、feedback_release=released）、[`META/prospective-intake-protocol-v1.md`](../META/prospective-intake-protocol-v1.md:16)（三门禁隔离规则）与 [`docs/superpowers/specs/2026-07-16-single-case-immediate-freeze-feedback-design.md`](../docs/superpowers/specs/2026-07-16-single-case-immediate-freeze-feedback-design.md:126)（三个独立 HOLD 文案）。
- 最小修复：在 [`handoff.md`](../handoff.md:246) 追加「10. Prospective 首案短期交接」小节，不改写 §1–§9 历史，不改写 [`META/project-state.json`](../META/project-state.json)。
- fresh 复现（修复后）：exit 0，1 passed，1 warning（既有 deprecation，非本次引入），0.48s。

### 3.3 分账结论

两个失败独立建 ledger，修复互不依赖；均非 F09 缺陷、非测试缺陷、非环境故障。

## 4. G10.5–G10.7 实施与验证账本

写集：仅 [`tools/README.md`](../tools/README.md)、[`handoff.md`](../handoff.md)。未修改 [`engine/f09/`](../engine/f09/)、[`tests/f09/`](../tests/f09/)、两个失败对应测试断言，或任何九份 Task 9-P 专项冻结文件。

fresh STATIC_REVIEW（G10.6）：核对 7 个 witness 术语与 11 项 handoff 断言语义均逐字/逐义存在，且与权威事实源一致，未发现事实源竞争或写集扩张。裁决 `PASS`（High=0、Medium=0）。

fresh VERIFY 命令账本（工作目录均为 `f:/多流派新思路`）：

| # | 命令 | exit | 结果 | 耗时 |
|---|---|---|---|---|
| 1 | `python -m pytest tests/evaluation/test_dataset.py::test_witness_trust_boundary_is_explicitly_documented -q` | 0 | 1 passed | 0.11s |
| 2 | `python -m pytest tests/evaluation/test_prospective_gate_workflow.py::test_handoff_names_first_legal_case_action_and_all_independent_holds -q` | 0 | 1 passed, 1 warning | 0.48s |
| 3 | `python -m pytest tests/f09 -q` | 0 | 1172 passed | 130.81s |
| 4 | `python -m pytest -q`（经临时账本文件恢复读取，命令与输出见执行记录） | 0 | 3121 passed, 7 skipped, 1 warning | 1344.94s (0:22:24) |

命令 4 的完整输出曾因终端信道传输中断而缺失原始摘要；本记录已通过原命令的标准输出/退出码重定向文件恢复完整证据（`_g10_full_pytest_output.txt`、`_g10_full_pytest_exit.txt`），核对后删除，不作为交付物保留。

无 collection error、无 stale evidence 复用、无未记录的失败或重跑。

## 5. G10.8 独立 EVIDENCE_REVIEW 裁决

**`PASS`**：

- 两个非 F09 sanity 失败已各自 fresh 复现、精确归因、最小修复、fresh 验证通过；
- F09 全集 fresh 1172 passed，与 G6–G9 历史计数一致，未发现回归；
- 全仓 fresh 0 failed，7 个 skipped 全部归因为已知静态类别，无新增未解释 skip；
- 写集未越界，未触碰 F09 冻结源码/测试或九份专项文件。

明确未证明：全仓测试覆盖之外的行为、部署/发布、性能/安全基准、Git provenance、GitHub 同步、跨平台运行环境、F10 生产就绪。

## 6. 唯一最终裁决

### G10.9 — `PASS / COMPLETE — EVIDENCE-BOUNDED FREEZE`

F09 production-readiness 的本地材料性缺口（安全文档、全仓兼容）已冻结闭合；运行环境、部署/发布、性能基准、Git provenance 保持其原有状态类别（`REQUIRES_EXTERNAL_DECISION` / `BLOCKED_BY_PROHIBITION` / `UNKNOWN`），不因本轮闭合而被推定满足。两个非 F09 sanity 失败已分别 evidence-bounded 处置为已修复且 non-material to F09。

### G10.10 — `HOLD F10`

理由：F10 的业务目标、owner 和依赖尚未由现有冻结事实唯一确定（本轮未收集或裁决任何 F10 范围材料）；§7.1 条件 5 未满足。运行环境、性能、部署等外部能力缺口仍需业务决策，不构成 `REJECT`，但不满足 `GO`。用户可在明确 F10 范围材料后重新发起 G10.10 复核；本裁决不因本轮全仓绿而自动升级为 Go。

## 7. Non-inference boundaries（重申）

本记录不得用于推导：F09 完全生产就绪；部署、发布、性能、安全、跨平台或远端同步已证明；Git provenance 或 GitHub 同步状态；F10 已获准启动或实现；production-default 可变；F01–F12 冻结语义可重开；Task 9-P PASS 自动继承为本轮合同或实现授权。

## 8. 文件清单

已读取（节选，完整列表见各 Gate 记录）：[`production-implementation-control.md`](production-implementation-control.md)、[`g6-task9p-total-gate-upgrade-review.md`](g6-task9p-total-gate-upgrade-review.md)、[`g10-next-governance-milestone-plan.md`](g10-next-governance-milestone-plan.md)、[`README.md`](../README.md)、[`AGENTS.md`](../AGENTS.md)、[`META/project-state.json`](../META/project-state.json)、[`STATUS.md`](../STATUS.md)、[`tools/README.md`](../tools/README.md)、[`handoff.md`](../handoff.md)、[`META/prospective-intake-protocol-v1.md`](../META/prospective-intake-protocol-v1.md)、[`docs/superpowers/specs/2026-07-16-single-case-immediate-freeze-feedback-design.md`](../docs/superpowers/specs/2026-07-16-single-case-immediate-freeze-feedback-design.md)、两个失败对应测试文件、九份 Task 9-P 专项文件（仅元数据/哈希核对，未读正文）。

已修改：[`tools/README.md`](../tools/README.md)（标题补全）、[`handoff.md`](../handoff.md)（追加 §10）。

新建：本文件；随后对 [`production-implementation-control.md`](production-implementation-control.md) 做一处有限追加（§8.9）。

本地状态：**`LOCAL ONLY / NOT PUSHED / NO GITHUB MUTATION`**。

# G6 Task 9-P 总 Gate 收口 + 专项合同 roll-up 执行方案（供 terra 模型执行）

> 目的：消除只读审计发现的 traceability gap——[`production-implementation-control.md`](production-implementation-control.md) 的
> 2026-07-26 G6–G9 收口对 F09 行为/隔离证据成立，但九份 Task 8/Task 9/P-1/P-2 专项合同从未被逐项汇总进 Task 9-P 总 Gate
> 或 G6 收口记录。本方案只做两件事：**(1) 对九份专项末态执行一次 fresh 独立 roll-up 复核并产出 Task 9-P 总 Gate 裁决文件**，
> **(2) 把该裁决与九份文件的可点击引用写回总控表**。不重新设计、不重新实现、不推翻任何已冻结 unit 的内部结论。
>
> 工作目录固定：`f:/多流派新思路`。所有 pytest 从仓库根执行。Windows `cmd.exe`，禁用 `tail`/`grep`/`sed`。
> 永久禁止任何 GitHub service-side mutation（push、PR、Issue、Release、workflow dispatch 等）；本地 Git 只允许非破坏性操作，
> 且不得配置 push 目标。
>
> 执行纪律：本方案允许拆分为下列 Phase 内的最小子任务，但**不要求逐个子任务向用户申请批准**——除非命中下方 STOP 条件，
> 否则应在同一次会话内连续推进直到 Phase D 完成或触发 STOP。每个子任务完成后仅在本文件之外的执行记录/commit message
> 中留痕，不追加新的散文合同。

---

## 0. 已验证事实（复核输入，不得重新采信标题或早期章节）

九份专项合同的最后生效裁决（均已由独立只读审计核验，不得重新展开其内部证据）：

1. [`g6-task8-r40-preprod-authority-construction-seam-contract.md`](g6-task8-r40-preprod-authority-construction-seam-contract.md:150) → `PASS / COMPLETE — EVIDENCE-BOUNDED FREEZE`
2. [`g6-task8-r41-run-target-ref-capture-provisioning-seam-contract.md`](g6-task8-r41-run-target-ref-capture-provisioning-seam-contract.md:332) → `PASS / COMPLETE — EVIDENCE-BOUNDED FREEZE`
3. [`g6-task8-r42-feedback-owner-revalidation-call-count-contract.md`](g6-task8-r42-feedback-owner-revalidation-call-count-contract.md:226) → `PASS / COMPLETE — EVIDENCE-BOUNDED FREEZE`
4. [`g6-task9-application-orchestrator-contract.md`](g6-task9-application-orchestrator-contract.md:405) → `CONTRACT PASS`（document-only，非实现证据，已被 5 取代）
5. [`g6-task9-authority-adjudication.md`](g6-task9-authority-adjudication.md:359) → 历史 `BLOCKED`（已由 6 的前置完成推进，本身未改写）
6. [`g6-task9-versioned-producer-envelope-contract.md`](g6-task9-versioned-producer-envelope-contract.md:300) → `PASS / COMPLETE — EVIDENCE-BOUNDED FREEZE`
7. [`g6-task9p-prerequisite-authority-contract.md`](g6-task9p-prerequisite-authority-contract.md:892) → P-1 `PASS`；P-2 `BLOCKED`（历史，已由 8 推进）；Task 9-P 总 Gate `BLOCKED`（历史，尚无独立文档覆盖）
8. [`g6-task9p-p2-current-run-identity-authority-adjudication.md`](g6-task9p-p2-current-run-identity-authority-adjudication.md:1040) → `PASS / COMPLETE — EVIDENCE-BOUNDED FREEZE`（只关闭 P-2，明确不关闭 Task 9-P/G6）
9. [`g6-task9p-p2-upstream-contract-reconcile-adjudication.md`](g6-task9p-p2-upstream-contract-reconcile-adjudication.md:846) → `PASS`（仅第十轮 document-only reconcile 的 fresh review）

**核心缺口：** 没有任何独立文件把 1/2/3/6/8（五个 evidence-bounded freeze）与 7 的 P-1 `PASS` 一并汇总为 Task 9-P 总 Gate 的现行裁决。
[`production-implementation-control.md`](production-implementation-control.md:249) 的 G6–G9 收口只记录了测试计数，没有引用上述九份文件名。

**本方案唯一目标：** 补齐这一份缺失的汇总，而不是重新验证已冻结 unit 的内部正确性。

---

## 阶段 A（只读）：九单元 fresh 独立 roll-up 复核

**子任务 A1（只读，最小目标）：** 重读 0 节列出的九份文件的最终生效章节（行号已给出），确认：
- 5 是否被 6 完整取代（对比冻结 scope 与 write set，不得有交叉）；
- 7 的 P-2 `BLOCKED` 是否被 8 完整取代（对比冻结 scope）；
- 1/2/3/6/8 五个 freeze 的 write set 互斥、无重叠、无相互依赖悬空（例如 6 依赖 1/2 是否已在 6 文本内声明并核验）。

**子任务 A2（只读，最小目标）：** 核对九份文件之间的依赖图是否闭合，即：
```text
R40(1) ─┐
R41(2) ─┼→ Task9-versioned(6) ─→ P-2(8) ←── reconcile(9)
R42(3) ─┘                         ↑
                          P-1(7 内部)  
```
若发现任一 freeze 引用了另一个仍处于 `REVISE`/`BLOCKED` 且未被后继覆盖的前置，STOP 并返回父任务，不得继续 Phase B。

**A 阶段完成判据：** 依赖图机械闭合，5→6、7的P-2→8 的 supersession 均有文本证据支持，无悬空引用。

---

## 阶段 B（只读命令，不改任何文件）：fresh 回归确认无 stale drift

九份 freeze 时间点不同，之后 Task 10 vertical matrix 等工作可能已改变 `tests/f09` 总数。必须用当前源码重跑各 freeze 引用的
selector，确认未发生静默回归，而不是直接采信旧 freeze 里的计数。

```
:: R40 focused + 模块
python -m pytest tests/f09/test_feedback_eligibility.py -q

:: R41 模块
python -m pytest tests/f09/test_artifact_lifecycle.py -q

:: R40+R41 联合回归
python -m pytest tests/f09/test_feedback_eligibility.py tests/f09/test_artifact_lifecycle.py -q

:: Task 9 versioned + production isolation
python -m pytest tests/f09/test_application_opt_in.py tests/f09/test_production_isolation.py -q

:: P-2 current-run authority
python -m pytest tests/f09/test_current_run_authority.py -q

:: 完整 F09 回归（应与总控 2026-07-26 记录的 1172 一致或在其基础上因新增只增不减）
python -m pytest tests/f09 -q
```

**B 阶段 PASS 判据：**
- 以上全部命令 exit 0，无 failed/error；
- 完整 `tests/f09` 计数 ≥ 1172，且若不等于 1172 必须能用同一 session 内新增/删除的文件差异解释，否则 STOP 并归类为
  product defect / test defect / environment issue，不得直接改写为通过；
- 记录每条命令的 cwd、collected/passed 计数、exit code，作为 Phase C 文件的 fresh VERIFY ledger。

**STOP 条件：** 任一 selector 出现新失败、collection error，或计数无法解释的下降。命中时立即停止，不修复实现代码，
把发现退回对应 owner unit（R40/R41/R42/Task 9/P-2），不得在本 roll-up 任务内直接修改 `engine/f09/`。

---

## 阶段 C（document-only 写入）：产出 Task 9-P 总 Gate 裁决文件

**子任务 C1（写入，最小目标）：** 新建文件 `plans/g6-task9p-total-gate-roll-up-adjudication.md`，结构必须包含：

1. **Gate chain：** `ADMISSION（九单元依赖闭合）→ fresh VERIFY（Phase B ledger）→ fresh EVIDENCE_REVIEW → Task 9-P 总 Gate 裁决`。
2. **逐项 supersession 表：** 九份文件 × 现行状态 × 覆盖/被覆盖关系 × 对应本方案 0 节行号锚点。
3. **Fresh VERIFY ledger：** 完整抄录阶段 B 的命令、cwd、计数、exit code，标注执行时间戳。
4. **直接证明边界：** 只声明——九个 unit 的末态经本次 fresh 复核和回归确认相互闭合、无 stale 覆盖冲突、无 selector drift；
   Task 9-P 总 Gate 现按此九单元证据判定为 `PASS / COMPLETE — EVIDENCE-BOUNDED FREEZE`（若 A/B 均无阻断）或
   `BLOCKED`（若命中 STOP 条件，需写明具体阻断项）。
5. **不得推断边界（必须逐条写明，不得省略）：**
   - 不证明 Task 9 的完整应用编排实现（application orchestrator 仍只是 document-only contract，见 0 节第 4 项）已投产；
   - 不证明 Task 3–7、Task 10 之外的其余 Task 是否已各自独立 evidence-bounded freeze（本方案不核验它们）；
   - 不证明全仓 100% 绿色、部署、发布、性能、安全或生产就绪；
   - 不证明 Git provenance、远端同步或 GitHub 服务端状态；
   - 不自动升级 G6/G7/G8/G9 的既有记录范围，只补齐其未覆盖的专项合同 roll-up 层。
6. **唯一下一合法动作：** 明确写出——若 Task 9-P 总 Gate 本次为 `PASS`，下一动作是核验 Task 3–7/Task 10 是否仍需各自独立
   roll-up，或直接进入 G6 收口记录修订（阶段 D）；若为 `BLOCKED`，下一动作是把具体阻断项退回对应 owner unit。

**C 阶段完成判据：** 新文件存在、结构完整、每条裁决都有 Phase A/B 的证据锚点，且没有把任何未经本方案验证的范围写成已证明。

---

## 阶段 D（document-only 写入）：回写总控表

**子任务 D1（写入，最小目标）：** 编辑 [`production-implementation-control.md`](production-implementation-control.md) 第 4 节任务表，
在现有行之后追加以下条目（每行必须含可点击文件引用，状态取自阶段 C 的裁决，不得先写后验）：

- `PI-600-T8`：对应 R40/R41/R42（Task 8 三个 seam 单元），链接 0 节第 1/2/3 项文件；
- `PI-600-T9`：对应 Task 9 versioned producer/envelope（现行 Task 9 unit），链接 0 节第 6 项文件，并注明第 4 项旧合同已被取代；
- `PI-600-P1`：对应 Task 9-P prerequisite authority 的 P-1 部分，链接 0 节第 7 项文件；
- `PI-600-P2`：对应 P-2 current-run identity + upstream reconcile，链接 0 节第 8/9 项文件；
- `PI-600-T9P`：Task 9-P 总 Gate，链接阶段 C 新建的 [`g6-task9p-total-gate-roll-up-adjudication.md`](g6-task9p-total-gate-roll-up-adjudication.md)，
  状态取自该文件裁决，`evidence` 列填 Phase B 的 fresh VERIFY 摘要，`未证明边界` 列原样抄录阶段 C 第 5 点。

**子任务 D2（写入，最小目标）：** 在第 8 节 “G6–G9 有界收口记录” 的 8.1 结论后追加一段，注明：
> 本节 2026-07-26 记录只覆盖 F09 行为与隔离命令证据；九份 Task 8/9/P-1/P-2 专项合同到 Task 9-P 总 Gate 的文档级 roll-up
> 由 [`g6-task9p-total-gate-roll-up-adjudication.md`](g6-task9p-total-gate-roll-up-adjudication.md) 单独裁决，二者不得互相替代。

**D 阶段完成判据：** 总控表新增五行均可点击、状态与阶段 C 文件一致；8.1 后的追加说明未修改原有测试计数记录；
`git diff --name-only` 只包含本阶段 C/D 新增或修改的两个文件。

---

## 通用纪律（terra 必须遵守）

1. **写集闭合：** 全程只允许创建 `plans/g6-task9p-total-gate-roll-up-adjudication.md` 与编辑
   [`production-implementation-control.md`](production-implementation-control.md)；不得修改 `engine/f09/`、`tests/f09/` 或任何其他专项合同文件。
2. **不得覆写已冻结 unit：** 九份专项文件的内部裁决只能被引用，不得编辑、不得重新开 Gate。
3. **失败即停、不反复微调：** 阶段 B 任一命令异常，立即停止并归类，不得在本任务内修实现代码。
4. **证据优先：** 阶段 C 的每条裁决必须能追溯到阶段 A 的依赖闭合结论或阶段 B 的真实命令输出，不得用散文替代。
5. **GitHub 永久禁止：** 不 push、不建 PR/Issue/Release，不做任何服务端写操作；本地改动均为 `LOCAL ONLY / NOT PUSHED`。
6. **单次会话连续推进：** 除非命中 STOP 条件（阶段 A 依赖悬空、阶段 B 回归失败、发现需要修改 production 代码的缺陷、
   或用户另有明确指令），否则不在阶段之间停下来征询批准；四个阶段应在同一次会话内顺序完成。

---

## 一页速查（命令清单）

```
:: 阶段 B fresh 回归
python -m pytest tests/f09/test_feedback_eligibility.py -q
python -m pytest tests/f09/test_artifact_lifecycle.py -q
python -m pytest tests/f09/test_feedback_eligibility.py tests/f09/test_artifact_lifecycle.py -q
python -m pytest tests/f09/test_application_opt_in.py tests/f09/test_production_isolation.py -q
python -m pytest tests/f09/test_current_run_authority.py -q
python -m pytest tests/f09 -q

:: 阶段 D 收尾自检
git diff --name-only
```

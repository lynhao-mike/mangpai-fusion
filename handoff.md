# HANDOFF · 历史隔离增量批次与 HOLD 后门禁交接

> 写给一个完全没有上下文的新会话。
> 更新时间：2026-07-16（Asia/Shanghai）
> 本文件只作短期交接，不是长期事实源。当前事实必须回到 `AGENTS.md`、`META/project-state.json`、门禁制品及运行时检查确认。

---

## 1. 新会话先读什么

严格按以下顺序读取，不要从本交接文档反推长期事实：

1. `README.md`
2. `AGENTS.md`
3. `META/project-state.json`
4. `STATUS.md`
5. `tools/README.md`
6. `engine/README.md`
7. `engine/contracts/00-OVERVIEW.md`
8. `docs/superpowers/specs/2026-07-11-bazi-intelligence-platform-core-design.md`
9. `plans/bazi-intelligence-platform-roadmap.md`
10. `META/six-month-platform-gate-2026-07-15.md`
11. `META/six-month-capability-baseline-2026-07-15.md`
12. `reports/l1-routing-holdout-comparison.md`
13. `plans/upgrade-guides/6-month-execution-plan-2026-07.md`
14. `plans/upgrade-guides/post-gate-action-plan-2026-07-15.md`

其中第 14 项是本轮新增的直接执行依据；核心设计文档仍是目标架构“宪法”，门禁报告仍是当前 HOLD 判定事实源。

---

## 2. 我们在做什么任务

六个月平台工程任务 Task 1—14 已完成，但六个月生产候选门禁最终判定为 **HOLD**。post-gate 行动计划 Task 1—2 与 Task 3/4 所需工程前置已完成；prospective Task 3 已招募首案但首批未满 10，保持进行中/HOLD，Task 4 未启动。本轮历史增量评估不会补足 prospective/E3 缺口，也不授权切换生产入口。

当前五个证据缺口：

| # | 未满足条件 | 当前缺口 | GO 所需方向 |
|---|---|---|---|
| 1 | timing Claim 覆盖 | 历史输入缺逐年流年，四个 timing 任务 Claim 为 0；任/段 runner 正确 abstain | 新 prospective 输入必须包含真实逐年 `liunian_steps`，形成可审计 timing Claim |
| 2 | 独立效用 E2 | learned/static 选择变化为 0，平均效用相同 | 至少一个任务竞争样本 ≥5、选择变化 ≥1、learned 效用不低于 static |
| 3 | 校准 E3 | binary 校准样本为 0，后验 N_eff 为 0 | `career.role_change` 或 `marriage.divorce_or_remarriage` ≥20 条可评分正负例，`calibration_error < 0.2` |
| 4 | 高风险 E4 | 债务、离婚、健康任务没有 A 级双审标签，可评估记录为 0 | 三项任务均建立独立双审；冲突由第三人仲裁；假阳性不增加 |
| 5 | 前瞻证据 E6 | prospective/E3 完成案例为 0 | ≥30 个真实新命主完成 prediction-first 冻结评估链 |

门禁报告规定的最短路径是：

1. 采集至少 30 个真实 prospective 新案例；
2. 积累至少 20 条目标 binary 校准样本并达到误差门槛；
3. 建立真实多派竞争并让 learned 至少改变一次选择；
4. 重跑 L1 learned/static 留出门禁及八项平台总门禁。

---

## 3. 本会话已经完成什么

### 3.0 历史隔离增量批次扩展（2026-07-16）

本轮已完成：

- 以 `META/six-month-capability-baseline-2026-07-15.json` 的 64 个冻结 case ID 为父集合，按 `sex_marker + four_pillars` 与当前 `cases/shuru-input.md` 对照；
- 当前输入仍到 `P-2026-076`，原始 76 案，去重后 75 个 subject；`P-2026-010` 与 `P-2026-045` 为同盘，继续保留更完整的 `P-2026-045`；
- 确认增量共 11 案：`P-2026-066` 至 `P-2026-076`；
- Stage A dry-run 与正式冻结均只读取隔离命盘事实，形成 11 × 10 × 6 = 660 条输出，forbidden marker 为 0；父 Stage A freeze hash 为 `b5d09f6e5ec49e061c865d8f4a4ec3d934293cb0f6d5adfb98107c78aa478f68`；
- Stage B 从公开反馈提取 14 条候选标签，其中 4 条 `education.attainment_band` 不在十任务目录，最终接受 10 条低风险目录内标签，覆盖 4 个案例；无 A 级双审高风险标签，高风险可评分数保持 0；
- 通过正式 `school_capability_baseline.py freeze → score → report` 生成 4 个有目录内标签案例的独立正式子批次，freeze hash 为 `3abc2223f90116f5778eb5b2b360580c0a83125fb6747052a0ceedf64ba98ab7`；
- 新增归档：`META/six-month-capability-baseline-2026-07-16-incremental.json`、`.md`，分类保持 `historical_blind_candidate`，门禁 HOLD；
- 新增 L1 诊断：`META/l1-routing-holdout-audit-2026-07-16-incremental.json` 与 `reports/l1-routing-holdout-comparison-2026-07-16-incremental.md`；留出 1 个 subject、2 个可评分 case/task、1 个多派竞争 case/task、selection changes=0、static/learned mean utility 均为 -0.1，结论仍为 HOLD；
- 新增编排工具 `tools/school_capability_incremental.py`、专项测试 `tests/evaluation/test_historical_incremental_batch.py` 和实施计划 `docs/superpowers/plans/2026-07-16-historical-isolation-incremental-batch.md`。

旧 2026-07-15 基线未覆盖；任务开始时记录的 SHA-256 为：JSON `d3012a619054a137580cb4cfbd6c7481733841fa766de3e3c771c54123a1ac40`，Markdown `363ba24787319fb9524be45c0215be98498bed6ad75a6ff815a59f2feaefc4b0`。完成前必须复验一致。

### 3.1 已读取并核对当前事实源

本会话已按 `AGENTS.md` 必读顺序读取：

- `README.md`
- `AGENTS.md`
- `META/project-state.json`
- `STATUS.md`
- `tools/README.md`
- `engine/README.md`
- `engine/contracts/00-OVERVIEW.md`

并重点阅读：

- 核心设计宪法；
- 平台配套路线；
- 六个月 HOLD 门禁；
- 六个月能力历史隔离基线；
- L1 路由留出对照；
- 已完成的六个月执行计划。

### 3.2 已核实现有 CLI 与数据契约

已检查：

- `tools/school_capability_dataset.py`
  - `prospective-intake`
  - `prepare-blind`
  - `bind-labels`
  - `validate`
  - witness append/verify
- `tools/school_capability_baseline.py`
  - `audit/freeze/score/report`
- `tools/l1_routing_holdout_audit.py`
  - `--baseline` 与 `--batch/--scores` 两种输入
- `tools/feedback_ingest.py`
  - 正式反馈入口及 `--dry-run`
- `engine/evaluation` 的 label、freeze、calibration 与高风险评分契约。

关键核验结果：

1. `prospective-intake` 会拒绝 feedback、labels、report、known facts、重复 case、重复 subject、未知 task 和 symlink。
2. `prepare-blind` 只复制白名单 canonical chart、tasks、rule snapshot、manifest；目标目录必须不存在。
3. dataset GO 需要至少 30 个 eligible 且至少 30 个 labelled case，还要求 bundle root、reveal provenance 和独立 witness 链。
4. 现有 `META/school-capability-prospective-tasks-v1.json` 只含 structure + 四个 timing 任务，不能直接支撑本阶段 binary 校准及三项高风险任务。
5. 现有 L1 CLI 的 `--batch/--scores` 只接受历史兼容 schema；prospective frozen run 不能直接冒充 historical batch，必须规划显式、保留 prospective 身份的 adapter。

### 3.3 已产出正式后续行动计划

已创建：

- `plans/upgrade-guides/post-gate-action-plan-2026-07-15.md`

计划共 11 个任务、三阶段：

1. **数据采集期（建议 8—12 周）**
   - 冻结十任务 prospective CLI 目录和采集协议；
   - 实现三项高风险 A 级双审/仲裁工具；
   - 连续招募至少 36 个真实新命主，为 ≥30 完成案留失访缓冲；
   - 每 10 案执行 intake、blind bundle、staged freeze 和 witness；
   - 观察 outcome，形成真实正负例；
   - 绑定双审标签。
2. **校准验证期（建议 2—3 周）**
   - 构建 reviewed manifest 和完整数据门禁；
   - score/report；
   - 至少一个目标 binary 任务 n≥20 且 `calibration_error < 0.2`；
   - 建立 prospective→L1 审计显式适配与真实竞争证据。
3. **路由 GO 准备期（建议 1—2 周）**
   - 重跑 learned/static 严格留出；
   - learned 至少改变 1 个选择且效用不退化；
   - 重跑八项平台总门禁；
   - GO 也只形成独立切换提案，不直接切入口。

### 3.4 已完成计划自审与校验

已运行新鲜校验：

- 计划文件存在；
- 共 1008 行；
- 11 个 `Task`；
- 核心需求关键词无缺失；
- 未发现 `TBD`、`TODO`、`implement later` 等禁止占位；
- `git diff --check -- plans/upgrade-guides/post-gate-action-plan-2026-07-15.md` 通过；
- 已有链接目标检查未发现非预期缺失。

后续会话已实施 post-gate Task 1—2，并完成 Task 3/4 的工程前置：新十任务目录、正式六来源规则快照、短槽位唯一解析、包含安全 `intake.json` 的 canonical blind bundle、确定性 staged frozen run，以及一次生成/追加 `registered → prepared → freeze` 三事件段的 witness CLI。Task 3 已招募并取得授权记录 1 案；首案 raw section input 的 preflight 与单案 `prospective-intake --dry-run` 均通过。正式 prospective intake 仍为 0，未创建盲包、冻结、见证、观察、反馈或报告制品；Task 3 因首批未满 10 保持进行中/HOLD，Task 4 尚未启动。

---

## 4. 当前卡在哪里

### 4.1 Task 3 已有首案，仍卡在外部真实数据规模

当前采集状态以本节为短期交接快照；长期事实仍以正式 META 制品与运行时校验为准：

- 真实 prospective 招募数为 1，授权记录为 1；首案 preflight PASS，单案 intake dry-run PASS；
- 正式 prospective intake 仍为 0，真实 prospective/E3 完成案仍为 0；
- 真实 binary 校准 outcome 仍为 0；
- 高风险 A 级双审标签仍为 0；
- 现有历史输入缺逐年流年，因此 timing runner 正确 abstain；
- learned/static 没有数据支持的差异化选择。

代码或 agent 不能合法“生成”这批证据。必须有规则/路由冻结后才进入系统的真实新命主，以及冻结后到达的真实 outcome。

### 4.2 Task 3/4 工程前置已完成

1. `META/prospective-go-task-catalog-v1.json` 已从 YAML 任务事实源精确冻结十任务；`META/prospective-go-rule-snapshot-v1.json` 已固定六来源 runner 与任务目录摘要。旧五任务 prospective JSON 仍只作追溯，不能承担 binary/high-risk；历史文件中的 classification 必须按字段语义判读，不能因文件名含 prospective 就误判为当前 prospective 证据。
2. `prospective-intake` 已支持把现有 tasks-by-case 中 `P-GO-2026-NNN` 短槽位唯一解析至真实完整 case ID；无需生成按四柱改写的任务文件，歧义或未知槽位会拒绝。首案验证同时修复了 preflight 对 canonical raw section 格式的兼容，以及冻结十槽位表中未来尚未到达槽位的合法解析。
3. `prepare-blind` 的安全白名单为 `intake.json`、`tasks.json`、`rule-snapshot.json`、`bundle-manifest.json`、`cases/<case_id>/chart.json`。
4. `tools/school_capability_prospective.py` 已提供 `stage-frozen-run` 与 `witness-freeze-chain`：前者从已校验盲包生成确定性六来源三态冻结制品；后者一次安全生成/追加每案 `registered → prepared → freeze` 三事件段，不提前 reveal，HMAC key 仅从环境变量读取。
5. prospective→L1 审计 adapter 仍是后续 Task 9 的工程任务，不是当前真实采集 Task 3/4 的阻塞前置。

### 4.3 生产入口继续 HOLD

在总门禁 GO 前必须保持：

- `engine.application.pipeline_runner.run_pipeline()` 不变；
- `engine.claims.runner_registry.DEFAULT_RUNNER_REGISTRY` 不变；
- static 路由仍是默认；
- staged 路径只用于并跑和评估；
- 静态权重、生产规则和历史 run snapshot 不回写。

---

## 5. 下一步计划

新会话不要重复实施已完成的行动计划 Task 1—2 或 Task 3/4 工程前置，也不要把历史增量案例冒充 prospective。下一条合法动作是继续 Task 3，招募并取得 `P-GO-2026-002` 的真实授权新命主；首批未满 10 前保持 HOLD，不正式写 intake，不启动 Task 4，也不创建盲包、frozen run、witness、observation、feedback 或 report。若只做历史评估维护，必须保持历史与 prospective classification 隔离。

### 5.1 第一执行批次

按顺序：

1. 阅读 `plans/upgrade-guides/post-gate-action-plan-2026-07-15.md` 的 Global Constraints 与 Task 3；确认首案仅有 `input.md` 与一条合法招募授权日志，正式 intake 不存在。
2. 招募并取得 `P-GO-2026-002` 的真实授权新命主；按授权时间早于接收时间记录，不写 outcome 或 PII，不生成替代样本。
3. 对新案运行 preflight，并使用现有短槽位 `META/prospective-go/prospective-go-b01-tasks-by-case.json` 做单案 `prospective-intake --dry-run`；继续核验 subject hash 不与历史或其他可读 prospective intake 重复。
4. 首批未满 10 前不执行正式 `prospective-intake`，也不启动 Task 4 的 `prepare-blind`、`stage-frozen-run` 或 `witness-freeze-chain`。
5. 三项高风险任务继续使用 `tools/school_capability_review.py` 的独立双审/仲裁链；单审或历史公开反馈不得进入 A 级可评分集。保持历史与 prospective 制品路径完全隔离。

### 5.2 外部运营准备

代码实施可以先完成，但 GO 关键路径还需要：

- 明确招募渠道和命主授权；
- outcome custodian、intake operator、runner operator、reviewer A/B、adjudicator、witness 的人员隔离；
- 独立 witness HMAC key holder；
- 8—12 周观察窗及失访处理；
- 每周 4—6 个新命主的招募能力；
- 至少招募 36 个，为最终 ≥30 完成案留缓冲。

### 5.3 每阶段退出条件

- 数据采集 GO：≥30 唯一真实完成案、目标 binary ≥20 且正负都有、四项 timing 有完整流年与 Claim、三项高风险有 A 级双审。
- 校准验证 GO：至少一个目标 binary task n≥20 且 `calibration_error < 0.2`；高风险不退化；竞争任务 ≥5。
- 路由准备 GO：selection changes ≥1、learned utility ≥ static、校准不恶化、高风险假阳性不增加、八项总门禁全部通过。

---

## 6. 踩过的坑，绝对不要再踩

1. **不要把现有 `P-2026-*` 当 prospective。** 仓库里已有约 40 个 `P-2026-*` 目录，但门禁事实源把当前有效批次定为 `historical_blind_candidate`，不是 E3。目录前缀不能改变证据等级。

2. **不要复制历史案例凑 ≥30。** 990、Top30、问真补盘、同命主不同报告均不能升级为真实前瞻证据；`sex_marker + four_pillars` 重复必须拒绝。

3. **不要使用旧五任务 prospective JSON 承担本阶段。** `META/school-capability-prospective-tasks-v1.json` 缺少 `career.role_change`、`marriage.divorce_or_remarriage`、`wealth.debt`、`health.system_risk` 等任务。必须从 YAML 事实源冻结新的十任务 CLI 目录，并用测试逐字段防漂移。

4. **不要把 prospective frozen run 直接传给 L1 的 historical batch 接口。** 现有 `tools/l1_routing_holdout_audit.py --batch/--scores` 有严格历史 schema。必须通过显式 adapter，保留 prospective classification 和父制品摘要，不能改 schema 名冒充历史证据。

5. **不要为了 timing 覆盖强迫 runner 发言。** 缺 `liunian_steps` 或无触发时 abstain 是正确行为。应修复真实新案输入采集，而不是补造流年或覆写 frozen output。

6. **不要把失访/no_data 当负例。** `not_observed` 必须是预先定义观察窗完整结束后可核验的未发生；未知、未到期、来源冲突均不进入校准分母。

7. **不要把关系压力当离婚正例。** `marriage.divorce_or_remarriage` 只标真实发生的离婚或再婚；同理，正常信用消费不等于显著债务，健康风险不等于医学诊断。

8. **不要降低 A 级双审。** 债务、离婚、健康必须两名独立人类 reviewer；二人冲突必须第三名 adjudicator。单审、自动 reviewer、同一人换名字都不能生成 A 级。

9. **不要让 reviewer 看预测。** reviewer 只能看同一 observation packet，不能看 runner 输出、概率、报告或对方意见，否则标签泄漏，整批 STOP。

10. **不要在同一批上拟合校准又宣称同批 GO。** 若 error≥0.2，需要预注册训练/holdout 或追加新批复核。历史 frozen prediction 不得看标签后改写。

11. **不要修改 static baseline 制造 selection change。** learned 选择变化必须来自能力后验；不能通过改 coverage mapping、删竞争样本或把 unsupported 当 miss 得到。

12. **不要在 HOLD 期间切生产入口。** 不修改 `run_pipeline()`、`DEFAULT_RUNNER_REGISTRY` 或默认 routing mode。GO 也只是提交独立契约变更提案。

13. **不要使用 deprecated 工具。** 正式反馈入口使用 `tools/feedback_ingest.py`；不要恢复或调用 `calibrate.py`。

14. **不要覆盖旧制品。** blind bundle 目标目录必须不存在；freeze、labels、scores、capability snapshot 均用新批次/内容寻址文件，历史 run 保持字节不变。

15. **不要硬编码易漂移状态到稳定文档。** 当前 N_eff、规则数量、git HEAD、flagged/deprecated 清单使用运行时扫描或当次 JSON 制品。

16. **不要被 Windows cmd 编码乱码误导。** 之前用 Python 在 cmd 枚举中文 case 名时输出出现乱码，但数量命令 exit 0；中文路径核查优先使用文件工具或明确 UTF-8，不要据乱码改名/删除目录。

17. **不要从旧 handoff 或历史计划推断当前流程。** 本文件也是临时交接；事实冲突时以 `AGENTS.md` 矩阵和最新门禁 JSON/Markdown 为准。

---

## 7. 建议验证命令

Windows 10 默认 shell 为 `cmd.exe`，从仓库根运行：

```bat
python -m pytest tests -q
python tools/tool_registry.py --check
python tools/rule_status_scan.py --check
git diff --check
```

计划文档专项检查：

```bat
python -c "from pathlib import Path; p=Path(r'plans/upgrade-guides/post-gate-action-plan-2026-07-15.md'); s=p.read_text(encoding='utf-8'); print({'exists':p.exists(),'lines':len(s.splitlines()),'tasks':s.count('## Task ')})"
```

不要在新会话一开始就运行长期服务器或切换默认入口。

---

## 8. 新会话提示词

```text
你正在接手 mangpai-fusion 的 HOLD 后门禁行动实施。先不要修改代码。

请严格按 AGENTS.md 必读顺序读取当前事实源，然后重点阅读：
- handoff.md
- docs/superpowers/specs/2026-07-11-bazi-intelligence-platform-core-design.md
- plans/bazi-intelligence-platform-roadmap.md
- META/six-month-platform-gate-2026-07-15.md
- META/six-month-capability-baseline-2026-07-15.md
- reports/l1-routing-holdout-comparison.md
- plans/upgrade-guides/6-month-execution-plan-2026-07.md
- plans/upgrade-guides/post-gate-action-plan-2026-07-15.md

当前状态：六个月 Task 1—14 已完成，但平台门禁为 HOLD。根因是 timing Claim=0、learned/static 选择无差异、binary 校准样本=0、高风险 A 级双审标签=0、prospective/E3 完成案=0。不要把现有 P-2026-*、990、Top30 或其他历史 feedback-first 案例冒充 prospective。

Task 1—2 与 Task 3/4 工程前置已经完成，不要重复实现。Task 3 当前已有 1 个真实招募案和 1 条授权记录，首案 preflight 与单案 intake dry-run 已通过，但正式 intake 仍为 0；首批未满 10，状态保持进行中/HOLD，Task 4 未启动。你的第一合法动作是招募并取得 `P-GO-2026-002` 的真实授权新命主，继续 preflight 和单案 intake dry-run；不得正式写 intake 或创建 Task 4 制品。

硬约束：
- 不降低 ≥30 prospective、≥20 binary、calibration_error<0.2、竞争≥5、selection change≥1 或 A 级双审门槛；
- 不伪造新案、负例或逐年流年；
- 不修改 run_pipeline()、DEFAULT_RUNNER_REGISTRY、默认 static 路由或生产静态权重；
- 反馈只用 tools/feedback_ingest.py，不使用 calibrate.py；
- 高风险三任务必须两名独立人类 reviewer，冲突第三方仲裁；
- 所有写命令先 dry-run，历史冻结制品不可覆盖；
- 发现泄漏整批 STOP。

先汇报你从事实源确认的当前状态、Task 1 精确文件和测试顺序；确认无冲突后再实施。
```

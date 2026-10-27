# AGENTS.md · AI 导航入口

## 1. 项目定位与核心铁律

本仓库融合高德臣、段建业、杨清娟、任付红四派盲派理论及传统经典，为八字分析提供可追溯的盘面事实与理论证据。

- **确定性盘面事实**只从 `python -m engine.cli` 获取；**经典与流派理论**通过 `python -m tools.query_theory` 检索；**综合推理、证据权衡与最终裁决**由 Agent 完成。
- 严禁心算排盘或编造干支关系、长生、空亡、神煞、起运等事实。输入不完整、口径不明或工具未返回时，明确标示不确定，不补造结果。
- 引用结论时保留盘面地址 / 关系边 ID、理论出处 `source_ref` 与适用边界；工具列出的事实或候选不等于自动成立的命理结论。

## 2. 1 分钟快速导航图

```text
engine/facts/       四层确定性事实底座：排盘、关系图、能量事实、格局/段派候选
engine/api/         无状态事实 API
engine/cli.py       Agent JSON 入口：python -m engine.cli
 tools/query_theory.py  六源理论原子检索：python -m tools.query_theory
theory/ + sources/  四派盲派与传统经典的结构化索引、原文及提取语料
 docs/agent_tools.md 工具调用细节、地址编码、返回字段与六步推演 SOP
 docs/analysis_human_touch.md   人话写作与翻译规范（Linter 配套，含引擎契约清单）
 templates/report-v7-human.md   人话报告标准模板（单报告架构，默认产物）
 tools/human_touch_linter.py    防骑墙门禁：python -m tools.human_touch_linter <file.md>
```

按任务需要读取相关源码或语料；不要依据旧流程文档推断当前 Agent 工具入口。项目人类入口见 [`README.md`](README.md)，机器可读状态见 [`META/project-state.json`](META/project-state.json)。

## 3. 常用 CLI 命令速查

```bash
# 公历排盘并返回完整事实
python -m engine.cli all --birth "1980-02-15 02:30" --gender 乾 --json

# 四柱直接分析，叠加第 3 步大运及 2026 流年
python -m engine.cli all --pillars "庚申 戊寅 壬子 辛丑" --gender 乾 --dayun-index 3 --liunian 2026 --json

# 分项事实：chart / relations / strength / structures
python -m engine.cli chart --birth "1980-02-15 02:30" --gender 乾 --json

# 跨流派与经典检索（--schools 后名称以空格分隔）
python -m tools.query_theory --query "寅申冲 食神制杀" --top-k 5 --per-school-cap 2 --json
python -m tools.query_theory --query "夫妻宫 穿" --schools yang duan ren ziping --domain 婚姻 --top-k 5 --json

# 核心回归测试
pytest tests/
```

更多调用参数、字段说明与推演步骤见 [`docs/agent_tools.md`](docs/agent_tools.md)。

## 4. 多流派与多口径争议处理原则

- 对晚子时、阴干长生、土寄宫等争议口径，保留工具返回的 `boundary_warnings`、`variants` 及 profile 信息；有差异时并列呈现各口径及其影响，不悄然选边。
- 四派盲派证据与《子平真诠》《滴天髓》《穷通宝鉴》《三命通会》《千里命稿》可交叉验证，但须分清来源、适用条件与推理路径；不得用单一流派抹杀其他流派的有效证据。
- 对格局成败、做功含义、力量取舍等需要判断的项目，结合命主问题与岁运语境说明裁决理由；保留有依据的分歧，不把检索命中或结构候选写成确定断语。
- **举证与呈现分歧不等于骑墙和稀泥**：Agent 在展示各派依据后必须给出主次裁决与人话落点；「各有道理 / 尚难定论」视为任务未完成。

## 5. Agent 协作约定

### 验证命令

本项目验收统一使用以下命令，退出码 0 为通过：

```bash
# 核心回归测试（范围以 pyproject.toml 的 testpaths 为准，已隔离旧实验/回测目录）
python -m pytest -q

# 显式指定被 ignore 的路径时，需覆盖 addopts
python -m pytest tests/asof/test_daiyun_context.py -q -o addopts="-ra --tb=short"

# 引擎事实入口冒烟（确定性盘面事实的唯一来源）
python -m engine.cli all --pillars "庚申 戊寅 壬子 辛丑" --gender 乾 --json

# 人话报告门禁
python -m tools.human_touch_linter <file.md>
```

证据来源：[`pyproject.toml`](pyproject.toml) 的 `[tool.pytest.ini_options]`（testpaths 与 addopts）、[`AGENTS.md`](AGENTS.md) §2–§3、[`requirements-dev.txt`](requirements-dev.txt)。

若任务产出无法用上述命令判定，为该任务写一个只依赖标准库的 `verify.py`，以退出码表达验收结果；**不得为了让命令通过而修改测试或断言**。

### 已知红灯：默认 pytest 门禁（2026-10-26 记录）

`tests/tools/test_bundle_pii.py` 在**导入阶段**加载 `.workbuddy-ai/make_bundle_v2.py`。该目录被 `.gitignore` 忽略，且脚本已不存在，因此 `python -m pytest -q` 会在**收集阶段**失败（不是断言失败）。

判定除该文件之外的回归是否通过，用显式路径覆盖 addopts：

```bash
python -m pytest -q -o addopts="-ra --tb=short" tests/facts tests/api tests/predicates \
  tests/tools/test_query_theory.py tests/tools/test_human_touch_linter.py \
  tests/tools/test_blind_ledger.py tests/tools/test_anchor_span.py \
  tests/tools/test_blind_toolchain.py tests/tools/test_gao_split.py tests/test_project_metadata.py
```

修复方向（已授权）：把脱敏逻辑**生产化**为 `tools/bundle_sanitize.py`（跟踪任务 `tasks/T-114/PROMPT.md`），测试改为导入生产模块。

2026-10-26 过渡措施：该测试在脚本缺失时显式 `pytest.skip(..., allow_module_level=True)`，reason 带任务号，默认门禁恢复为 `220 passed, 1 skipped`。**skip 只让门禁可用，不等于已修**：禁止改成永久 skip，也禁止把该测试移出 `testpaths`。
另：`tools/blind_candidate_pick.py` 仍打印 `python .workbuddy-ai/make_bundle_v2.py …`，生产化后需同步改为新入口。

### 保护区（不得修改，除非任务卡明确授权）

> 中枢指挥官的完全自主重构权限见 [`docs/adr/ADR-004-hub-commander-authority.md`](docs/adr/ADR-004-hub-commander-authority.md)：`tests/` 已由该 ADR 降级为「可改，但不得改断言让失败变绿」；其余各项不变。

- ~~`tests/` 全部内容~~（ADR-004 降级：可改可重写，但不得删放宽判据让红变绿。`tests/governance/static_isolation_*.py` 是隔离性检查的判据本身，改动须说明理由）
- `pyproject.toml`、`requirements.txt`、`requirements-dev.txt`
- `theory/_ir/` 与 `sources/` 下的原文语料（只增不改，改动须走 ingestion-protocol）
- `templates/report-v7-human.md`、`docs/analysis_human_touch.md`（引擎契约与写作规范）
- `META/project-state.json`（机器可读状态，由维护流程更新）
- `AGENTS.md`、`CLAUDE.md`
- `tasks/` 下的 `PROMPT.md`（任务定义，只有中枢可写；Worker 只能写 `STATUS.md` / `BRIEF.md`）

### 重构基线尺子（ADR-004 红线三）

重构前后跑同一条命令对比，任一指标下降须在汇报中写明原因：

```bash
python -m tools.verify_baseline --compare
```

### 目录约定

- 任务卡：`tasks/<ID>/PROMPT.md` 与 `tasks/<ID>/STATUS.md`
- 简报：`tasks/<ID>/BRIEF.md`（Worker 写）
- 归档：`tasks/_archive/`（已废弃的任务卡，保留供追溯）
- 插件状态：`.taskswarm/`、`.agent-teams/`，已在 `.gitignore` 中忽略

### 运行方式：单会话中枢 + 子代理

本项目采用**中枢统一指挥 + 子代理执行**，不使用多会话人工中转。分工固定：

| 环节 | 承担者 | 说明 |
|---|---|---|
| 写卡 `tasks/<ID>/PROMPT.md` + `STATUS.md` | 中枢 | 任务规格唯一来源，Worker 只读 |
| 派活 | 中枢 | 通过 `subagent` 工具派发，子代理有独立上下文 |
| 执行 | 子代理 | 严格按卡执行，不扩大范围 |
| 写 `BRIEF.md` + 更新 `STATUS.md` | 子代理 | 四个字段：改动文件 / 原始输出 / 未完成与风险 / 下游须知 |
| 验收 | 中枢 | **亲自跑命令查 diff**，不信简报文字 |
| 决策 | 人类 | 产品口径、保护区授权、架构取舍 |

**中枢必须先问一句「这活你已经在别的会话干了吗」，再派子代理**，避免两个 Worker 同时改同一文件互相覆盖。

**验收铁律**：Worker 说"通过"不算数，中枢跑出退出码才算数。数字要现场跑，不能引述二手结论（含中枢自己上一轮的结论）。

### 执行规则

1. **只读任务卡 `File Scope` 中列出的文件。** 需要接口定义时读对应源文件，不要 `ls` 全仓库——上下文成本是模型单价的 5–10 倍。
2. **禁止修改测试或验收脚本使其通过。** 测试失败要改实现，不是改断言。
3. **版本操作**：`git commit` 与 `git push` 已获用户明确授权（2026-10-26）。执行前必须：跑 `python -m pytest -q`、只暂存与本轮改动相关的文件、提交信息写清范围。**仍然禁止** `checkout` / `stash` / `reset` / `clean` 等破坏性操作。
4. **任务完成后必须更新 `STATUS.md`**，并在 Execution Log 追加一行。
5. **发现任务卡本身有问题时**，写入 `PROMPT.md` 的 `Amendments` 段并在 `STATUS.md` 的 Blockers 记录，不要自行扩大范围。
6. **不得心算排盘或编造干支关系、长生、空亡、神煞、起运等事实**；这类事实只从 `python -m engine.cli` 取，理论证据只从 `python -m tools.query_theory` 取。

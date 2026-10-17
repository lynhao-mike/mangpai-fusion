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
 docs/agent_tools.md 工具调用细节、地址编码、返回字段与五步推演 SOP
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

# mangpai-fusion · Agent-Native 八字命理分析系统

整合高德臣、段建业、杨清娟、任付红四派盲派理论，以及《子平真诠》《滴天髓》《穷通宝鉴》《三命通会》《千里命稿》等传统经典，为 Agent 提供可追溯的盘面事实与理论证据。确定性事实由引擎生成，理论依据由检索器定位，综合推理与最终裁决由 LLM Agent 完成。

## Agent 入口

进入仓库后先阅读 [`AGENTS.md`](AGENTS.md)。工具字段、地址编码及五步推演规范见 [`docs/agent_tools.md`](docs/agent_tools.md)；机器可读项目状态见 [`META/project-state.json`](META/project-state.json)。

## 核心架构

1. **确定性盘面事实引擎**：[`engine/facts/`](engine/facts/) 及 `python -m engine.cli` 负责排盘和多口径并列（晚子时、阴干长生、土寄宫、起运）；生成带位置与完整度的干支关系图；核验任派墓库五细则；提供原子能量计数、人元司令、《穷通宝鉴》调候查表、独立神煞查表、子平八格要件核对及段派五类做功候选扫描。引擎输出事实与候选，不替代命理判断。
2. **六源理论原子检索器**：`python -m tools.query_theory` 毫秒级检索四派盲派及传统经典条目，返回明确出处，并支持跨派配额控制。
3. **Agent 五步推演 SOP**：LLM Agent 按需调用事实算子与理论检索器，依照 [`docs/agent_tools.md`](docs/agent_tools.md) 完成边界核验、事实提取、定向检索、冲突裁决和可追溯输出。

## 快速开始

公历排盘并返回完整事实：

```bash
python -m engine.cli all --birth "1980-02-15 02:30" --gender 乾 --json
```

按问题检索四派与经典理论：

```bash
python -m tools.query_theory --query "寅申冲 食神制杀" --top-k 5 --per-school-cap 2 --json
```

运行测试：

```bash
pytest
```

## 目录导航

- [`engine/facts/`](engine/facts/)：确定性盘面事实底座
- [`engine/api/`](engine/api/)：无状态事实 API
- [`theory/`](theory/) 与 [`sources/`](sources/)：六源理论索引与原文语料
- [`docs/agent_tools.md`](docs/agent_tools.md)：工具调用手册与五步推演 SOP
- [`tests/`](tests/)：回归与验收测试

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

## 外部体系旁证（可选）

紫微斗数等外部体系以 `evidence-envelope/v1` 挂在**旁证层**，不进入 `engine.cli` 事实层，也不作 `tools.query_theory` 的理论出处；分歧由 Agent 站队。分两级：**L1** 由紫微项目排盘引擎生成结构化盘面（在紫微体系内核验宫位星曜四化），**L2** 是 v4.0 解读文本（只做结论层对账）。Agent 调用手册见 [`docs/agent_tools.md`](docs/agent_tools.md) 的「工具 3」，设计与合规见 [`docs/ziwei-corroboration-bridge.md`](docs/ziwei-corroboration-bridge.md)。

```bash
# 本机先复制 config/ziwei.local.example.toml 为 config/ziwei.local.toml（已被忽略）
mkdir -p cases/_private/ziwei-demo
D=cases/_private/ziwei-demo
python -m engine.cli chart --birth "2001-12-31 06:00" --gender 坤 --json > "$D/bazi_chart.json"
python -m tools.ziwei_lookup --birth "2001-12-31 06:00" --gender 坤 --dim career,wealth --json > "$D/ziwei_l2.json"
python -m tools.cross_check --bazi "$D/bazi_chart.json" --ziwei "$D/ziwei_l2.json" --out "$D/对账.md"
python -m tools.ziwei_chart --birth "2001-12-31 06:00" --gender 坤 --json > "$D/ziwei_l1.json"
python -m tools.cross_check --bazi "$D/bazi_chart.json" --ziwei "$D/ziwei_l2.json" --json > "$D/cross.json"
python -m tools.ziwei_appendix --l1 "$D/ziwei_l1.json" --l2 "$D/ziwei_l2.json" --cross "$D/cross.json" --out "$D/旁证附录.md"

# 数据按年懒加载（缺省 dry-run；--download 才联网），清单见 config/dataset-manifest.json
python -m tools.ziwei_fetch --year 2001 --verify-only
python bridges/ziwei/verify.py --require-data --require-l1
```

`旁证附录.md` 是**独立文件**，不并入 v7 主报告、不参与其门禁；每行带 locator。上面不带 `--claims` / `--verdicts` 时，对账表是「待 Agent 裁决」的骨架（全部 `unverifiable`）；要让三态落定，需补八字侧结论（带 `source_ref` 与盘面地址）和裁决理由，格式见设计文档 §5 / §8。L1 需要紫微项目已 `npm install`（`tsx` / `iztro`），L2 只需 Node ≥ 22。附录若含解读原文片段，入库前须确认不含倪师《天纪》引文，否则放 `cases/_private/ziwei-*/`。

数据来源（CC BY 4.0）：本项目使用 **紫微斗数开源解读数据集 v4.0**（674,976 张命盘 × 13 维），来源 https://github.com/Renhuai123/ziwei-doushu ，作者 王多鱼AI。解读中引用的倪海厦《天纪》原话不在该授权范围内（CC BY-NC-SA 4.0、非商用），原文只留本地私有目录、不入库。

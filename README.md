# mangpai-fusion · 盲派四派融合八字分析系统

> 整合 **高德臣 / 段建业 / 杨清娟 / 任付红** 四派盲派理论，面向命理师实战调用，输出带证据链、派别归属与双轨置信度（★ 等级 + 百分比）的分析报告，并通过案例反馈持续校准规则。

---

## AI / LLM 快速入口

任意 AI agent 进入本仓库后，请优先读取 [`AGENTS.md`](AGENTS.md)。

- 产品版本：[`VERSION`](VERSION)
- 机器可读项目状态：[`META/project-state.json`](META/project-state.json)
- 工具唯一索引：[`tools/README.md`](tools/README.md)
- 稳定项目仪表盘：[`STATUS.md`](STATUS.md)
- 短期交接：[`handoff.md`](handoff.md)，只作临时下一步，不作长期事实源

---

## 一、定位与使用场景

本仓库**不是研究语料库**，而是一个**面向命理师的实战调用接口**。

典型流程：

```text
问真八字 APP 排盘
  → templates/input-from-wenzhen.md
  → cases/C-YYYY-NNN-{干支}/input.md
  → tools/preflight.py
  → engine/pipeline.py
  → tools/render_report.py
  → reports/*.md
  → cases/*/feedback.md
  → tools/feedback_ingest.py / tools/feedback_loop.py
  → theory/*/index.yaml + META/*
```

---

## 二、四派理论分工

| 派别 | 主导领域（Lead） | 副导领域（Co-lead） | 独门武器（Exclusive） |
|---|---|---|---|
| **高德臣** | 神煞 / 健康灾厄 / 学业子女 | 格局 / 应期 | 32字诀 / 命宫长生诀 / 词馆学堂 / 神煞应用宝典 |
| **段建业** | 格局定性 / 富贵层级 / 财运事业 | 婚姻 / 六亲 | 宾主体用 / 4 层签字律 / 做功路径 / 富贵 L0-L5 |
| **杨清娟** | 婚姻情感 / 调候改运 / 六亲画像 | 象法 | 五合明暗 / 人来印来 / 调候改运 / 暗合断 |
| **任付红** | 应期推断 / 是非判断 | 神煞 | 18 道法门 / 6 触发应期 / 操作清单 |

---

## 三、核心架构

### 共识金字塔

```text
┌─────────────────────────────────────────────────┐
│ 上层 · 独门层 EXCLUSIVE                         │
│   单派独有，按该派该规律历史命中率独立打分      │
├─────────────────────────────────────────────────┤
│ 中层 · 互补层 COMPLEMENTARY                     │
│   2~3 派同向，不同表述路径，相互增强            │
├─────────────────────────────────────────────────┤
│ 底层 · 共识层 CONSENSUS                         │
│   4 派全部认可的铁律                            │
└─────────────────────────────────────────────────┘
```

### 双轨制置信度

| ★ 等级 | 百分比 | 含义 |
|---|---|---|
| ★★★★★ | ≥ 90% | 铁断 |
| ★★★★ | 80-89% | 高置信 |
| ★★★ | 65-79% | 中置信 |
| ★★ | 50-64% | 倾向性 |
| ★ | < 50% | 存疑 |

输出格式示例：`★★★★ (87%)`。

---

## 四、目录导航

| 路径 | 定位 |
|---|---|
| [`AGENTS.md`](AGENTS.md) | AI agent 操作手册与事实源矩阵 |
| [`VERSION`](VERSION) | 产品版本唯一机器可读事实源 |
| [`META/project-state.json`](META/project-state.json) | 当前项目状态机器可读快照 |
| [`STATUS.md`](STATUS.md) | 稳定项目仪表盘 |
| [`handoff.md`](handoff.md) | 短期下一步交接，不作长期事实源 |
| [`theory/`](theory/) | 四派结构化规律库 |
| [`mapping/`](mapping/) | 跨派共识、互补、独门、冲突映射 |
| [`engine/`](engine/) | 核心 pipeline、契约与规则实现 |
| [`templates/`](templates/) | 输入、反馈、报告模板 |
| [`cases/`](cases/) | 实战案例库 |
| [`reports/`](reports/) | 正式报告归档 |
| [`predictions/`](predictions/) | 封存预测 |
| [`tools/`](tools/) | 自动化工具，索引见 [`tools/README.md`](tools/README.md) |
| [`META/`](META/) | 迭代状态、规则变更、仲裁与校准记录 |
| [`plans/`](plans/) | 架构方案与历史计划 |
| [`tests/`](tests/) | 回归与验收测试 |

---

## 五、常用工作流

### 新增案例

```bash
python -m tools.preflight cases/C-YYYY-NNN-干支/input.md
```

### 生成报告

```bash
python -m tools.render_report
python -m tools.output_linter reports/example-report.md
```

### 摄入反馈

```bash
python -m tools.feedback_ingest C-YYYY-NNN-干支
python -m tools.batch_review
```

### 查看工具与规则状态

```bash
python tools/tool_registry.py --format markdown
python tools/tool_registry.py --check
python tools/rule_status_scan.py --format markdown
python tools/rule_status_scan.py --check
```

### 跑测试

```bash
pytest tests/
pytest tests/test_project_metadata.py -q
```

---

## 六、版本与状态

- 产品版本以 [`VERSION`](VERSION) 为准。
- Python 包版本见 [`engine/__init__.py`](engine/__init__.py)，必须与 [`VERSION`](VERSION) 一致。
- 当前机器状态见 [`META/project-state.json`](META/project-state.json)。
- 历史变更见 [`META/rule-changelog.md`](META/rule-changelog.md)。
- 易漂移的规则数量、N_eff、flagged/deprecated 清单不要写入普通文档；需要时运行 [`tools/rule_status_scan.py`](tools/rule_status_scan.py)。

# 教材入库协议 · v1.0（多派别 Markdown 收件箱）

> 本协议是 [`META/ingestion-protocol.md`](ingestion-protocol.md) 的**前置闸门（S0）**。
> 它规定新教材如何从 `sources/inbox/` 流入只读语料库与既有 S1–S5 理论入库管线，
> 并最终接入四派规律库与**跨流派交叉核验**。本协议不改变 S1–S5，只在其上游补一个标准化入口。

---

## 一、为什么需要它

既有架构已具备：只读语料库 `sources/{school}/`、S1–S5 入库管线、结构化规律库
`theory/{school}/index.yaml`、跨派映射 `mapping/`、跨流派交叉核验
[`tools/cross_school_scan.py`](../tools/cross_school_scan.py)。

缺的是一个**指定的新教材投放口**与前置校验：派别是否合法、来源元数据是否齐备、
归档位置是否正确、S1 抽取记录是否已起骨架。本协议 + `sources/inbox/` +
[`tools/materials_intake.py`](../tools/materials_intake.py) 补齐这一段。

---

## 二、S0 · 教材入库（Intake）

```
sources/inbox/*.md                          ← 命理师投放 Markdown 教材
        │  tools/materials_intake.py（前置闸门：校验 + 归档 + 起骨架）
        ▼
sources/{school}/{file}.md                  ← 归档进只读语料库（已存在则跳过，不覆盖）
        │
theory/raw/{school}/extracted/*.md          ← S1 抽取记录骨架（自动生成，待人工填）
```

**步骤**

1. 命理师把教材 `.md` 放入 `sources/inbox/`，文件头建议带 front-matter
   （`school` / `title` 必填，`edition` / `pages` / `topic_hint` / `source_note` 选填）。
   约定详见 [`sources/inbox/README.md`](../sources/inbox/README.md)。
2. 运行 `python -m tools.materials_intake --dry-run` 预览，确认无误后去掉 `--dry-run` 正式入库。
3. 工具产出：
   - 教材归档到 `sources/{school}/`；
   - 在 `theory/raw/{school}/extracted/` 生成抽取记录骨架（含来源追溯链 + S2–S5 提示）；
   - 在 [`META/materials-intake-log.md`](materials-intake-log.md) 追加一条审计记录。

> **校验闸门**：派别须归一到 `gao/duan/yang/ren`（或中文 高/段/杨/任），否则该教材被标失败、
> 不归档、不起骨架，需修正 front-matter 后重跑。

> **路径说明**：抽取记录的实际落点是 `theory/raw/{school}/extracted/`（与仓库现状一致）。
> `ingestion-protocol.md` / `theory/SCHEMA.md` 早期示例中的 `META/extracted/` 为历史写法，以本协议为准。

---

## 三、衔接既有 S1–S5

入库（S0）完成后，按 [`META/ingestion-protocol.md`](ingestion-protocol.md) 继续：

| 阶段 | 动作 | 落点 |
|---|---|---|
| **S1 抽取** | 命理师 + LLM 把骨架填成候选规律（保留原文锚点） | `theory/raw/{school}/extracted/*.md` |
| **S2 归一** | 转写为 SCHEMA 结构化规律，ID = `{派别字母}-{TOPIC}-{序号}`（字母 G/D/Y/R，TOPIC 大写） | `theory/{school}/*.yaml` |
| **S3 打分** | 按 [`engine/confidence.yaml`](../engine/confidence.yaml) 算 `static`；初始 `status: candidate` | 同上 |
| **S4 跨派对照** | 登记同向 / 冲突 / 共识 / 独门关系 | `mapping/{consensus,complementary,exclusive,conflicts}.md` |
| **S5 入库** | git commit + 更新 [`rule-changelog.md`](rule-changelog.md) 与 [`source-trace.md`](source-trace.md) | git |

---

## 四、跨流派交叉核验

新教材规律进入 `theory/` 与 `mapping/` 后，即自动纳入既有的跨流派核验回路：

- **静态对照（S4）**：每条规律在 `cross_school` / `conflicts` 字段与 `mapping/` 中显式标注与其他派别的同向/冲突关系。
- **动态偏差扫描**：随实战案例反馈累积，运行
  `python -m tools.cross_school_scan`（每 10 案触发一次），对各领域统计 4 派 hit_rate，
  `max - min` 超阈值且持续则在 [`conflict-trends.md`](conflict-trends.md) 标系统性偏差。
  该工具**只产报告、不自动调权重**，由架构师人工 review 后再开 PR 改
  [`engine/domain-weights.yaml`](../engine/domain-weights.yaml)。

由此，新派别/新教材的规律与既有四派在同一核验框架内交叉验证，而非各自孤立。

---

## 五、扩展点：新增派别

收件箱默认复用 [`tools/rule_lifecycle.py`](../tools/rule_lifecycle.py) 的
`SCHOOL_DIR_MAP` / `SCHOOL_TO_CN`（高/段/杨/任）。新增第五派：

1. 在 `SCHOOL_DIR_MAP` / `SCHOOL_TO_CN` 注册派别标识与目录名；
2. 在 [`theory/SCHEMA.md`](../theory/SCHEMA.md) §三派别字母前缀表登记字母前缀（并在 `materials_intake.SCHOOL_PREFIX` 同步）；
3. 建 `sources/{new}/`、`theory/{new}/`、`theory/raw/{new}/extracted/`。

完成后，本收件箱即识别新派教材，S4 跨派对照与 `cross_school_scan` 自动纳入新派。

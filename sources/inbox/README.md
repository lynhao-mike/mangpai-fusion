# sources/inbox/ · 教材收件箱（多派别 Markdown 入口）

> 本目录是**新教材的指定投放口**。命理师把 Markdown 格式的教材丢进这里，
> 由 [`tools/materials_intake.py`](../../tools/materials_intake.py) 校验、归档进只读语料库
> `sources/{school}/`，并在 `theory/raw/{school}/extracted/` 生成 S1 抽取记录骨架，
> 从而无缝接入既有的 S1–S5 理论入库管线、四派规律库与跨流派交叉核验。

本目录是**暂存区**，不是长期语料源。教材一旦完成入库（intake）即被移入
`sources/{school}/`，本目录恢复为空（仅保留本 README 与 `.gitkeep`）。

---

## 一、它在架构中的位置

```text
sources/inbox/*.md                      ← 你在这里投放教材（本目录）
        │  tools/materials_intake.py（前置闸门）
        ▼
sources/{school}/{file}.md              ← 归档进只读原始语料库
        │
theory/raw/{school}/extracted/*.md      ← S1 抽取记录骨架（本工具自动生成）
        │  S1 抽取（命理师 + LLM，见 META/ingestion-protocol.md）
        ▼
theory/{school}/index.yaml              ← S2 归一为结构化规律（SCHEMA.md）
        │  S3 打分（engine/confidence.yaml）
        ▼
mapping/{consensus,complementary,exclusive,conflicts}.md   ← S4 跨派对照
        │  S5 入库（git + META/rule-changelog.md + source-trace.md）
        ▼
tools/cross_school_scan.py              ← 跨流派交叉核验（每 10 案触发）
```

> 本工具**只做前置闸门**：校验 + 归档 + 生成抽取骨架。它**不会**自动臆造规律。
> S1 的规律抽取仍由命理师 + LLM 按 [`META/ingestion-protocol.md`](../../META/ingestion-protocol.md) 完成。

---

## 二、教材文件格式（front-matter 约定）

每份投放的 `.md` 教材**建议**在文件开头加一段 YAML 风格 front-matter（被 `---` 包裹）。
缺失 front-matter 时，工具会尽量从文件名推断并提示补全。

```markdown
---
school: gao              # 必填 · 派别：gao|duan|yang|ren（或 高|段|杨|任）
title: 理法篇             # 必填 · 教材标题（用于命名抽取记录）
edition: 2018弟子班       # 选填 · 版本 / 班次 / 出处
pages: 31                # 选填 · 页数
topic_hint: lifa         # 选填 · 主题预判，取值见 theory/SCHEMA.md 的 topic 枚举
source_note: MinerU OCR 转译版   # 选填 · 原文版本说明
---

# 正文（教材内容）...
```

| 字段 | 必填 | 说明 |
|---|---|---|
| `school` | 是 | 派别标识，归一到 `gao/duan/yang/ren` 之一 |
| `title` | 是 | 教材标题；作为抽取记录文件名的篇章名 |
| `edition` | 否 | 版本 / 班次，写入抽取记录的"原文版本" |
| `pages` | 否 | 页数，附在版本说明后 |
| `topic_hint` | 否 | 主题预判（`lifa`/`geju`/`shensha`…），仅作 S2 参考 |
| `source_note` | 否 | 原文版本说明（如 OCR 转译版） |

> 当前默认仅识别既有四派（高/段/杨/任）。如需扩展新派别，见下文"扩展点"。

---

## 三、使用

```bash
# 预览将要发生的归档与抽取记录生成（不写盘）
python -m tools.materials_intake --dry-run

# 正式入库：把 inbox 全部教材归档 + 生成抽取记录骨架
python -m tools.materials_intake

# 仅处理指定文件
python -m tools.materials_intake --files sources/inbox/某教材.md

# 工具自检
python -m tools.materials_intake --smoke
```

入库后，按 [`META/materials-intake-protocol.md`](../../META/materials-intake-protocol.md)
继续 S1–S5，并在累计案例时运行 `python -m tools.cross_school_scan` 做跨流派交叉核验。

---

## 四、扩展点（新增派别）

本收件箱默认复用 [`tools/rule_lifecycle.py`](../../tools/rule_lifecycle.py) 的
`SCHOOL_DIR_MAP` / `SCHOOL_TO_CN`（高/段/杨/任 + 预留一/预留二）。

### 已预留的 2 个流派入口

| 占位标识 | 目录名 | ID 前缀 | 状态 |
|---|---|---|---|
| 预留一 | `ext1` | `E` | 🟡 待启用 — 确定派名后改此行 + 下列 3 处 |
| 预留二 | `ext2` | `F` | 🟡 待启用 — 同上 |

目录已建好（`sources/ext1/`、`theory/ext1/`、`theory/raw/ext1/extracted/` 及 ext2 同理），
front-matter 写 `school: ext1`（或 `school: 预留一`）即可被工具识别并归档。

**启用步骤（把占位改为真实派名）**：

1. `tools/rule_lifecycle.py` — 把 `"预留一": "ext1"` / `SCHOOL_TO_CN["ext1"]` 改为真实中文派名；
2. `theory/SCHEMA.md` §三 — 把 `E | 预留一` 行改为真实派名全称；
3. `tools/materials_intake.py` — 把 `SCHOOL_PREFIX["ext1"]` 旁注释改为真实派名（代码无需动，值 `E` 仍有效）；
4. 重命名目录（可选，若想把 `ext1` 改成拼音缩写，如 `li`）。

### 新增第 7+ 派（超出预留）

若需增加更多派别（超出已预留的 2 个），需要：

1. 在 `SCHOOL_DIR_MAP` / `SCHOOL_TO_CN` 注册派别标识与目录名；
2. 在 [`theory/SCHEMA.md`](../../theory/SCHEMA.md) 的派别字母前缀表登记 ID 前缀；
3. 在 `sources/{new}/`、`theory/{new}/`、`theory/raw/{new}/extracted/` 建目录；
4. 在 `tools/materials_intake.py` 的 `SCHOOL_PREFIX` 同步新前缀。

完成上述后，本工具即可识别新派别教材，跨派映射与交叉核验自动纳入新派。

# T-133 · 段派婚姻断语原文锚点提取（B1 前置）

- 状态：🔵 Ready for Execution
- 优先级：P1（B1 编译的前置）
- 创建：2026-10-27（中枢）
- 决策依据：ADR-003（断语条件化）、[`theory/claims/conditions-v2/pilot-20.yaml`](../../theory/claims/conditions-v2/pilot-20.yaml)

## 1. 背景

B1 要把段派婚姻断语编译成可求值条件。编译前必须先有**原文锚点**——每条判据都能指回具体的书、页、原句。没有锚点的判据不许进编译器。

本任务**只取锚点，不写编译、不改引擎、不碰语料原文**。

## 2. 五条判据

逐条取原文锚点：

1. 克者被合绊
2. 克者无根
3. 力量相当
4. 穿中带生不能制
5. 目标旺透得长生

**另有一条必须查证并如实标注**：「制净 / 制尽」——原文是否有稳定阈值？若原文只给定性描述（如「制尽则…」）而无量化标准，**标 `unmodeled`**，不许自己编阈值。这是硬要求，B1 不许出现自造阈值。

## 3. 取证方式（唯一合法入口）

```bash
.venv\Scripts\python.exe -m tools.query_theory --query "克者被合绊 制用" --schools duan --top-k 5 --json
```

只从 `query_theory` 取。**严禁凭记忆写原文、严禁改写原句、严禁补页码。**

## 4. File Scope

- **新建** `theory/claims/drafts/duan-marriage-anchors.yaml`
- **只读** `theory/`、`sources/`

**禁止修改** `theory/_ir/`、`sources/` 下任何文件（原文语料只增不改，这是红线二）。

## 5. 输出格式

每条锚点字段：

```yaml
- criterion: 克者被合绊
  source_ref: <query_theory 返回的引用串>
  quote: <原句，逐字>
  school: duan
  status: anchored        # anchored | unmodeled | not_found
  notes: <原文的适用边界，有就写，没有写空>
```

`not_found` 也是合法结果——找不到就如实标 `not_found`，**不许用相近段落顶替**。

## 6. 验收

```bash
.venv\Scripts\python.exe -m pytest -q                                   # 220 passed, 1 skipped 不变
git status --porcelain theory/_ir sources                                # 必须为空
git status --porcelain                                                   # 只允许出现本任务新建文件
```

外加：五条判据各有 `status`，无一条留空；`quote` 与 `source_ref` 一一对应。

## 7. 回报格式

五条判据各自的 `status` 与锚点数、「制净/制尽」的查证结论（有阈值/无阈值/原文未提），以及 `not_found` 的是哪几条、为什么找不到。

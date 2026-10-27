# T-131 · 上层故障只读盘点（A2 前置）

- 状态：🔵 Ready for Execution
- 优先级：P1
- 创建：2026-10-27（中枢）
- 决策依据：ADR-001（引擎=事实+候选）

## 1. 背景

底层（排盘、关系图）已体检干净，故障集中在上层。已知嫌疑：`tiyong`/`binzhu` 序列化成 `None`、冲/刑/穿边 actor 为 `None`、`engine/v5` 与现行实现双轨、大量测试只断言「不抛异常」、多处 `except Exception` 吞错。

本轮**只盘点不修**。目的是拿到一张带复现命令的故障清单，供中枢排 P0/P1。

## 2. 要做的事

1. **扫 `except Exception`**：列出位置、上下文、是否有 `pass` / `return None` / 吞掉后继续的迹象。
2. **扫「只断言不抛异常」的测试**：找出 `pytest.raises` 之外、只有 `assert result is not None` / 仅调用不校验 的用例。
3. **实测 `None` 字段**：对 `tiyong`、`binzhu`、冲/刑/穿边 `actor` 这几个字段，用 `engine.cli` 跑实际盘面，确认 `None` 是否真实出现、出现在什么条件下。
4. 按 P0（会让断语算错/算不出）/ P1（可维护性）分级。

**每条结论必须带一条可以直接复制执行的复现命令，并且写下你运行它时看到的原始输出片段。** 没有复现的条目不算数。

## 3. File Scope

- **只读** `engine/`、`tools/`、`tests/`
- **新建** `META/upper-layer-faults-v1.md`（唯一产物）

禁止修改任何 `.py` 文件、禁止改测试。

## 4. 验收

```bash
.venv\Scripts\python.exe -m pytest -q          # 必须仍是 220 passed, 1 skipped（证明只读）
git status --porcelain                          # 只允许出现 META/upper-layer-faults-v1.md
```

## 5. 回报格式

清单每条一行：`编号 | 文件:行 | 现象 | 复现命令 | 实测输出摘要 | P0/P1 | 影响哪类断语`。最后给总数与 P0 条数。

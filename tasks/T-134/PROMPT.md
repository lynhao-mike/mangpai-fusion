# T-134 · v5 边界闸门（ADR-006 第 2 条）

- 状态：🔵 Ready for Execution
- 优先级：P1
- 创建：2026-10-27（中枢）
- 决策依据：[`docs/adr/ADR-006-v5-retirement-strategy.md`](../../docs/adr/ADR-006-v5-retirement-strategy.md)

## 1. 背景

ADR-006 决定 `engine/v5` 冻结为「历史度量链」，不做一次性大迁移。冻结靠口头约定守不住，必须有机器判据：**白名单外的文件不许 import v5，白名单条目只减不增。**

## 2. 要做的事

1. 新增 `tools/v5_boundary_check.py`：
   - 扫描主工作区所有 `.py`（排除 `.venv/`、`.worktrees/`、`_archive/`），找 `engine.v5` / `from engine import v5` 的引用。
   - 与白名单 `META/v5-boundary-whitelist.json` 比对：白名单外新增引用 → 退出码 1。
   - 自检：白名单条目数不得大于快照数（防止靠加豁免绕过）→ 超出则退出码 1。
   - `--update` 只允许**删除**条目，不允许新增；尝试新增时报错退出非 0。
2. 生成白名单快照（当前实测 98 条：engine 36 / tools 12 / tests 53 / 其他 1）。
3. 补测试：断言「白名单外引用被判违规」「加豁免被判违规」两种情形，不许只断言不抛异常。

## 3. File Scope

- 新建 `tools/v5_boundary_check.py`
- 新建 `META/v5-boundary-whitelist.json`
- 新增测试文件（`tests/tools/` 下）

**禁止**修改 `engine/v5/` 下任何文件、禁止删改现有测试、禁止改 `pyproject.toml`、禁止 git 破坏性操作。

## 4. 验收

```bash
.venv\Scripts\python.exe -m tools.v5_boundary_check        # 退出码 0
.venv\Scripts\python.exe -m pytest -q                      # 0 failed，passed 数不少于 220
```

## 5. 回报格式

白名单条目数、闸门当前判定（通过/违规几条）、两种违规情形的测试是否都覆盖到、以及将来删掉一个 v5 调用点后需要怎么更新白名单（写清楚操作步骤）。

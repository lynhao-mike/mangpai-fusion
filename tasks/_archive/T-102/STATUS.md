# STATUS · T-102

| 字段 | 值 |
|---|---|
| 任务 | 在 `pyproject.toml` 建立 `slow` marker 机制（不动 testpaths） |
| 状态 | **BLOCKED-BY-T-101**（依赖未完成，暂不认领） |
| 依赖 | **T-101** |
| Review Level | 2 |
| 负责人 | 待认领（T-101 完成后） |
| 创建时间 | 2026-10-19 |

## Progress

- [ ] 确认 T-101 已 completed
- [ ] 复测 before 基线（记录机器信息）
- [ ] 改 `pyproject.toml`
- [ ] 复测 after 基线
- [ ] 说明为何本次不标注任何用例

## Blockers

- **T-101 未完成**。在 T-101 落地前启动本卡，会把 T-101 的编码失败混进 before/after
  计时基线，导致耗时对照不可比。

## Execution Log

| 时间 | 动作 | 结果 |
|---|---|---|
| 2026-10-19 18:34 | 中枢创建任务卡 | CREATED（blocked by T-101） |

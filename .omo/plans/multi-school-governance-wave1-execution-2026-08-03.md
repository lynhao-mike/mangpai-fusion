# 五派共同治理 Wave 1 执行清单

- 权威计划：`plans/multi-school-governance-wave1-implementation-2026-08-02.md`
- 上位设计：`plans/multi-school-governance-design-2026-08-02.md`
- 用户批准：2026-08-03，按权威计划执行 Wave 1
- 范围：仅 Wave 1；不得进入 Wave 2 或 Wave 3 规划/实现

## TODOs

- [x] Task 0：建立 Wave 1 变更护栏和基线证据
- [x] Task 1：冻结规范化摘要和稳定 ID primitive
- [x] Task 2：实现深层不可变事实契约
- [x] Task 3：构建现有命盘到 L0/L1 快照的应用适配器
- [x] Task 4：实现双认证事实注册表
- [x] Task 5：实现新治理 claim 信封和旧模型适配器
- [x] Task 6：实现五派只读注册与任务级能力资格
- [x] Task 7：实现七步仲裁和同源证据折叠
- [x] Task 8：实现受限组合模板注册与执行
- [x] Task 9：实现新路径 fail-closed trigger 边界
- [x] Task 10：冻结 30 格局目录和旧三结构投影
- [x] Task 11：组装 shadow runner 与端到端完整性检查
- [x] Task 12：扩展架构和静态隔离守卫
- [x] Task 13：执行分层回归验证并形成日期化验证记录

## Final Verification Wave

- [x] Task 14：完成 Wave 1 结束审查、全局评审与调试审计后停止

## 执行约束

- 每项任务的文件、TDD 顺序、验收条件和命令以权威计划对应 Task 为准。
- Task 0 基线通过前不得修改产品源码。
- Task 3/4 仅在 Task 2 完成后并行；Task 9/10 仅在 Task 8 的前置链稳定后并行。
- 禁止并行修改同一公共契约或 YAML schema。
- 所有实现、测试、真实表面 QA 和复核由独立子代理执行；根会话只维护编排状态、证据和勾选。
- 工作树已有大量用户改动；所有代理必须保留并绕开非本任务改动。

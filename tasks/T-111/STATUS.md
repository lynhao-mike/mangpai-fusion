# T-111: 六套引擎活性盘点 — Status

**Status:** 🔵 Ready for Execution
**Current Step:** Not Started
**Last Updated:** 2026-10-20
**Iteration:** 0
**Size:** M

> 任务卡由中枢写好，Worker 只读卡执行，**不要自己写 PROMPT.md**。
> 纯只读勘察。

---

### Step 1: 模块清单
**Status:** ⬜ Not Started

- [ ] engine/ 全模块 + 被谁 import + 测试覆盖 + 是否在 testpaths

### Step 2: 活性表
**Status:** ⬜ Not Started

- [ ] 6 套引擎各自：入口 / 真实调用链 / 最后修改时间
- [ ] 判定 活 / 半活 / 死

### Step 3: 核实 3 个论断
**Status:** ⬜ Not Started

- [ ] v5/runner.py 是否调 domain_slices 和 *_runner
- [ ] engine/facts 是否从未被 v5 使用
- [ ] governance shadow runner 由谁触发

### Step 4: 死代码量化
**Status:** ⬜ Not Started

- [ ] 死/半活模块行数 + 占 engine/ 比例

### Step 5: 建议
**Status:** ⬜ Not Started

---

## Execution Log

| Timestamp | Action | Outcome |
|---|---|---|
| 2026-10-20 | Task staged | 中枢写卡 |

---

## Blockers

*None*

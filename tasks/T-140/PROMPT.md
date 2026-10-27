# T-140 · 修通事实出口：facade 保留 tiyong / binzhu / distance / actor

- 状态：🔵 Ready for Execution
- 优先级：**P0（最高，阻塞一切断语求值）**
- 创建：2026-10-27（中枢）
- 决策依据：[`docs/adr/ADR-007-refactor-direction-adjudication.md`](../../docs/adr/ADR-007-refactor-direction-adjudication.md) D5

## 1. 为什么这是第一件事

`engine/claims/condition_ir/atoms.py:495` 的 `zuogong` 原子这样算 target：

```python
ty = tuple(c.get("tiyong") or ())
target = next((m for m, t in zip(members, ty) if t == "用"), members[-1] if members else None)
```

但 `engine/api/facade.py:93` 的 keep 白名单里**没有 `tiyong`**，所以 `c.get("tiyong")` 永远是空元组 → `zip()` 永远为空 → **target 永远回退到 `members[-1]`**。

含义：段派做功断语里「谁制谁」的 target 判定**当前是静默错的**。不修这个，后面所有断语都建在沙子上。

另有第二处：`facade.py:66-68` 的 `_compact()` 会把值为 `None` 的键整个丢弃，所以 `actor` 不是「值为 null」，而是**键不存在**，下游 `cand["actor"]` 会 `KeyError`。

## 2. 要做的事

1. **扩 keep 白名单**：
   ```python
   keep = ("mode", "relation_kind", "edge_id", "members", "ten_gods",
           "tiyong", "actor", "binzhu", "distance")
   ```
2. **让 `actor` 恒保留键**：值为 `None` 时输出 `"actor": null`，不允许被 `_compact()` 删掉。
   - 注意：`_compact()`（`:45-73`）对**整个 payload** 递归执行，第 66-68 行 `if compact in (None, [], {}): continue` 会删掉任何空值键。
   - 你必须自己追一遍调用链（`_compact_zuogong` 的输出之后还会不会再过 `_compact`），选一个**最小且正确**的改法（例如给 `_compact` 加 `keep_null_keys` 参数）。不要用哨兵字符串糊弄。
3. **确认正交性**：`tiyong`（体/用/双属）、`binzhu`（主/宾层级）、`distance`（柱序距离）、`actor`（生克发出方）全部由位置与五行生克决定，**不含吉凶结论**，符合 ADR-001「引擎只发事实」。若你发现其中任何一个含有判断成分，**停下来报告**，不要放出去。

## 3. File Scope

- `engine/api/facade.py`（唯一允许改的实现文件）
- 对应测试（`tests/api/` 下）

**禁止**：改 `engine/facts/` 下任何文件（另有任务在改）；改 `theory/_ir/`、`sources/`；改 `pyproject.toml`；git 破坏性操作。

## 4. 验收（中枢亲自跑）

```bash
.venv\Scripts\python.exe -m pytest -q              # 0 failed，passed 不少于 220
.venv\Scripts\python.exe -m tools.verify_baseline  # 四项不降
```

### ⚠️ 4.0 追加约束（2026-10-27 中枢裁决：**改分档，不改断言**）

**背景**：`tests/api/test_engine_reset_regression.py:171` 断言 `len(proc.stdout) < 15_000`。该盘现状 **14 904 B，余量仅 96 B**。按原卡扩 keep 后实测 18 556 B；即使只加 `tiyong` + `actor`（null）也约 15 300 B，**仍然超**。

**所以「D5 的任何正确修法都必然撞穿这条断言」这个判断成立。** 但**不许放宽 15 000**——那是改判据让红变绿（红线一）。

#### 根因：一个函数在服侍两个需求相反的调用方

| 调用方 | 需要什么 |
|---|---|
| `claim_condition_corpus` / `claim_condition_report` / `education_label_sheet` / `engine_audit` / `relations_audit` / `zuogong_probe` | **完整事实**（必须含 `tiyong`，否则 `zuogong` 原子 target 恒错） |
| `engine.cli`（Agent 入口） | **紧凑**（< 15KB，Agent 上下文预算） |

现在压缩逻辑写在 `analyze_facts` 内部（`facade.py:190 return _compact(payload, ...)`），于是「事实视图」被「Agent 视图」的预算绑死了。`engine/cli.py:18` 的注释自己写着「compact JSON，保证 analyze_facts 默认输出 < 15KB」——**预算是 CLI 的，压缩却做在 API 里**。

#### 裁决：事实视图与 Agent 视图分离

1. **`analyze_facts()` 返回完整事实**：保留 `tiyong` / `binzhu` / `distance` / `actor`（`actor` 无方向时为 `null` 且键不消失）。
   - 内部调用方（corpus / report / audit / probe）全部要吃这个完整版。
2. **`engine/cli.py` 负责 Agent 视图**：在 `_dump` 之前套一层**紧凑投影**（例如新增 `facade.compact_for_agent(payload)`），把 Agent 不需要的字段削掉，保证默认输出仍 < 15 000 B。
3. **`engine.cli all` 增加 `--full` 开关**：输出完整事实（不做紧凑投影），供审计/调试/验证使用。
4. **`test_cli_all_json_under_15kb` 一个字都不许改**，它必须继续通过。

这样：Agent 默认输出体积不变（仍约 14.9KB），事实层完整性恢复，D5 修复，且没有任何断言被放宽。

#### 如果 `binzhu` 仍然过大

`binzhu` 实测占 3370 B（4 层 × 每条候选重复），是紧凑投影里该被削掉的首选项。可选加分项：
- 默认视图不发 `binzhu`，`--full` 才发；或
- 发方向摘要 `{"1":"同在宾位","2":"正向"}` 这种紧凑形式。

**但这是次要优化。** 主修是分档。不要为了省字节去删 `tiyong`——那是 D5 要修的东西本身。

#### 验收追加

- `pytest -q` 必须 **0 failed**（当前是 1 failed / 219 passed，红的就是这条）。
- `test_cli_all_json_under_15kb` 必须通过，且**该文件未被修改**（用 `git diff -- tests/api/test_engine_reset_regression.py` 证明为空）。
- `engine.cli all --full` 的输出里，`duan_zuogong.candidates` 至少一条含 `tiyong` / `actor` 键。
- `python -c` 直接调 `analyze_facts`（不经 CLI）时，候选里必须有 `tiyong`。


**必须自证的三条**（把命令与原始输出贴进 BRIEF）：

1. 对 `癸丑 癸亥 辛亥 癸巳`（坤）跑 `engine.cli all`，`duan_zuogong.candidates` 里**至少一条**同时含 `tiyong` 与 `actor` 键，且 `actor` 明确是 `null` 或具体地址。
2. 同盘，`zuogong` 原子（`atom: zuogong`）的 target 判定不再恒等于 `members[-1]`：至少构造一个用例，使 target 不等于最后一个成员。
3. `binzhu` / `distance` 出现在候选里。

## 5. 回报格式

改了哪几行、`_compact` 的改法、actor 为 null 时最终 JSON 长什么样（贴真实片段）、target 判定修复前后的对比、两条验收命令的数字与退出码。

# T-145 STATUS

- 状态：✅ **Done**（待中枢验收）
- 完成时间：2026-10-27
- 执行者：子代理（T-145）
- 任务卡：`tasks/T-145/PROMPT.md`
- 决策依据：`docs/adr/ADR-007-refactor-direction-adjudication.md` D3 / D4
- 简报：`tasks/T-145/BRIEF.md`

## 前置检查

`engine/claims/condition_ir/atoms.py` 已含 `needs_judgment` 原子与 `_edges(ctx, scope="natal")`
的 natal 隔离 → **T-142 已完成**，未补做 T-142 的活。

## 改了什么

| 文件 | 性质 |
|---|---|
| `engine/claims/condition_ir/atoms.py` | ① 三个空壳岁运原子实装：`suiyun_edge` / `sanhe_with_suiyun` / `chong_kai_muku` 由恒 `unknown` 改为消费 `scope != natal` 的边；② 新增 `suiyun_arrives(at, via?)`（段派到位：通禄 / 现原身）；③ 新增 `can_control(actor, target)`（三值力量比较）；④ `liunian_present` 改从 `LN{year}` 节点反推（旧实现读恒为 null 的 `cycles.liunian`，永假）；⑤ `build_context` 增 `"nodes"`（读 `relations.nodes`）；⑥ `ATOMS` 44 → 46，`SIGNATURES` 同步（`suiyun_edge` 的 `layer?` 换 `scope?`、`sanhe_with_suiyun.zhi_set` 改可选、`chong_kai_muku` 增 `zhi?`）；⑦ 新增只读导入 `engine.predicates.types` 的五行表 |
| `engine/contracts/23-claim-condition-protocol-v1.md` | 原子表 44 → 46、版本 `v1.2`；§4.5 岁运 5 → 6 并补实装说明 + 原文边界（含「遁藏透干未实现」）；新增 §4.8 力量比较（`can_control` 判据表 + 原文行号 + 工程取值警示）；§八 Pass 0 44 → 46；§九 版本号 + 4 行变更登记 |
| `tests/claims/test_condition_ir_atoms.py` | 计数/签名断言 44 → 46；新增 ⑦ 岁运（10 条）与 ⑧ `can_control`（6 条）共 16 条回归 |

未改：`engine/facts/**`、`engine/api/facade.py`、`theory/claims/**`、`theory/_ir/`、`sources/`、
`pyproject.toml`、`templates/`、`META/project-state.json`。无 `git commit / push / checkout /
stash / reset`。

## 关键结果（两张标杆盘，成败唯一标准）

| 盘 | 判决 | `can_control` 实测 |
|---|---|---|
| A 坤造 癸丑 癸亥 辛亥 癸巳（制得住） | 制得住 | `can_control(亥,巳) = True`；水 旺项[得令、多(5字)]，火 旺项[] 衰项[失令、寡、受克] |
| A 反向 | 制不住 | `can_control(巳,亥) = False`（方向不乱） |
| B 壬子 乙巳 庚子 壬午（制不住） | 力量相当 | `can_control(子,巳) = None`；水 旺项[多(4字)] 失令，火 旺项[得令] 受克 → 各 1 项，不可裁 |

**未调任何阈值去凑**。A/B 的差异来自结构（2 旺项 vs 0 / 1 旺项 vs 1），不是阈值选边。

## 工程取值（非原文数值，已登记 BRIEF §5）

`DUO_MIN = 3`（多）· `GUA_MAX = 1`（寡）· `STRONG_MIN = 2`（旺项门槛）· 显性字数口径
（天干 + 地支本气，不含中气/余气）· 受克边种 `{chong, ke, stem_chong, chuan}`。全部集中在
`atoms.py` 常量区，改动须同步 BRIEF。

## 验收（中枢请亲自重跑）

```text
.venv\Scripts\python.exe -m pytest -q
→ 1011 passed, 1 skipped, 1 warning in 99.85s   EXIT=0   （本卡改动完成时）
→ 1040 passed, 1 skipped, 1 warning in 94.48s   EXIT=0   （并发会话 T-143 补入 29 条后，同命令复跑）
  （skip = tests/tools/test_bundle_pii.py，AGENTS.md 记录的 T-114 过渡措施，非本卡引入）

.venv\Scripts\python.exe -m tools.verify_baseline
→ pytest_passed 1040 / failed 0 / audit_errors 0 / relations_ok true /
  zuogong_charts 477 / zuogong_day_branch 346 / EXIT=0

.venv\Scripts\python.exe -m tools.verify_baseline --compare
→ 【基线未退步】 EXIT=0

.venv\Scripts\python.exe -m pytest tests/claims/test_condition_ir_atoms.py -q -o addopts="-ra --tb=short"
→ 52 passed   EXIT=0
```

> ⚠ **跑 `--compare` 必须前台执行**：先后两次以后台任务方式启动，内部 pytest 子进程返回
> `pytest_rc=1 / pytest_passed=0`（收集阶段失败，无 `N passed` 汇总行），触发误报「220 → 0 下降」。
> 同一命令前台复跑两次均为 1040 passed / 【基线未退步】。并发会话 T-143 正在改
> `theory/claims/conditions-v2/pilot-20.yaml` 并反复跑 pytest，判定为该窗口下的收集竞态，
> 与 T-145 改动无关（本卡只动 `atoms.py` / 契约 / 本卡测试）。

## Blockers / 待中枢裁决

1. **任务卡引文行号有偏差**（已在代码与契约里改为实测值）：
   `MinerU_22:1759` → 实测 `:1762`；`:1844` → `:1812`；`:1850` → `:1824`；
   `d01-deep-read.md:191-196`（12 种党势）**该区间不存在党势清单**，六党对实在 `MinerU_22:426/:428`。
2. **六党对聚合未实现**：若按原文把金并入水党、燥土并入火党，标杆盘 B 可能被判成「制得住」，
   与原文「力量相当」冲突。当前只用同五行字数计「多」。请裁决是否要扩到跨五行党势。
3. **「遁藏透干」（M1-D-059）未实现**：`suiyun_arrives` 只答 M1-D-042 的通禄 / 现原身。
   是否加为第三个 `via` 需裁定（它与原身表在寅/申 中气上不一致）。
4. `chong_kai_muku` 按卡只认 `scope ∈ {dayun, liunian}`，不计 `dayun+liunian` 三元边（实测该盘无）。
5. `engine/claims/condition_ir/__init__.py:6` 与 `docs/analysis-pipeline-explained.md:401` 仍写
   「42 个」，**不在本卡 File Scope**，未改，请中枢一并修正。

## 并发提示

`git status` 另有 4 个本卡未触碰的文件处于 modified / untracked，时间戳晚于本卡编辑，来自
并发会话 **T-143（断语层）**：

```
 M META/claim-condition-corpus-v1.json
 M META/claim-condition-pilot-v1.json
 M META/claim-condition-pilot-v1.md
 M theory/claims/conditions-v2/pilot-20.yaml
?? tests/claims/test_pilot20_conditions.py
```

提交时请勿与本卡改动混提。

## Execution Log

| 时间 | 动作 |
|---|---|
| 21:49 | 前置检查 T-142（`needs_judgment` / natal 隔离均在场）；读 PROMPT.md + ADR-007 D3/D4 |
| 21:52 | 核原文：到位（d01:287）、禄与原身（d02:271-287）、旺衰对句（MinerU_22:1762）、力量相当（:1812/:1824）、六党对（:426/:428） |
| 21:54 | 实装 5 个原子 + `build_context` 增 `nodes` + 原子表 46 |
| 21:55 | 实跑 A/B 标杆盘：A=True、B=unknown，方向与原文一致，未调阈值 |
| 21:56 | 岁运四原子实跑通过（e022/e024/e036/DY1.b） |
| 21:58 | 更新契约 23（§4.5 / §4.8 / §九）与测试（44→46，+16 条） |
| 22:00 | `pytest -q` → 1011 passed, 1 skipped, EXIT=0 |
| 22:05 | `verify_baseline` → 全项通过，EXIT=0 |
| 22:10 | 修正 note/契约中的原文行号为实测值，复跑 52 passed |

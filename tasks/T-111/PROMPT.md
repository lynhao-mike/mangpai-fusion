# T-111 · 六套并行引擎盘点：谁被调用、谁是死代码

## Review Level: 1

> 纯只读勘察，零写操作。目的是搞清楚仓库里到底有几套分析引擎、
> 哪套是活的、哪套是死的。

## Context

顾问指出仓库里并存 5~6 套分析实现，且互不连通：

1. `engine/facts/` —— CLI 四层确定性底座（质量最高，在 pytest testpaths 内）
2. `engine/application/pipeline_runner.py` —— 旧 D1-D4 流水线
3. `engine/v5/runner.py` —— 读 index.yaml 的 v5 主链
4. `engine/v5/{duan,gao,ren,yang}_runner.py` + `domain_slices/` —— 基于 ChartFeatureVector
   和 ExecutableClaimRule 的另一套 L2 runner，**v5/runner.py 根本没调它们**
5. `engine/governance/` —— shadow runner
6. `engine/f09/` 与 `engine/asof/`

**这个事实尚未核实。** 中枢没有独立验证过「v5/runner.py 不调用 domain_slices」。

## Objective

回答 5 个问题，为「该保留哪套、该废弃哪套」提供依据。

## Steps

### Step 1: 列全 engine/ 下的模块清单

按目录列出所有模块，标注：
- 被谁 import（给出具体文件:行号）
- 被哪些测试覆盖
- 是否在 `pyproject.toml` 的 testpaths 内

### Step 2: 判定每套引擎的「活性」

对上述 6 套，逐一回答：
- **入口是什么**（CLI / API / 被某模块调用）？
- **有真实的运行时调用链吗**（不是只有测试调用）？
- **最近一次被修改是什么时候**（`git log -1 --format=%ci -- <path>`）？

产出一张「活性表」：活 / 半活（只被测试调）/ 死（无人调）。

### Step 3: 重点核实顾问的三个具体论断

1. `engine/v5/runner.py` 是否真的不调用 `engine/v5/domain_slices/` 和
   `engine/v5/{duan,gao,ren,yang}_runner.py`？
   - 用 grep 搜 `domain_slices`、`gao_runner`、`duan_runner` 的 import
   - 如果被调用，说明调用点在哪
2. `engine/facts/` 的四层事实底座是否真的**从未被 v5 使用**？
   - v5 的 chart 从哪来？是不是 `engine/v5/preprod.py:build_chart_from_input` 自己解析的？
   - `build_chart_from_input` 与 `engine/facts/` 有没有任何交集？
3. `engine/governance/` 的 shadow runner 由谁触发？

### Step 4: 死代码的量化

如果能确定某些模块无人调用：
- 列出它们的代码行数（`wc -l`）
- 占 `engine/` 总行数的比例
- **注意**：只有测试覆盖、无生产调用的，算「半活」不算「死」

### Step 5: 给出建议

- 哪套应该成为唯一主链？
- 哪些可以安全废弃？废弃前需要做什么（比如确认没有 CLI 入口）？

## File Scope

**只读**：`engine/` 全部、`pyproject.toml`、`tools/`（只看谁 import engine。）
**只读 git**：`git log` / `git show` / `git grep` 允许。

**唯一可写**：`tasks/T-111/BRIEF.md`、`tasks/T-111/STATUS.md`

## Do NOT

- **禁止修改任何文件**（除上述两个）
- **禁止删除任何代码**
- **禁止执行任何 git 写操作**
- **禁止运行会写文件的脚本**
- read-only git 操作允许

## Completion Criteria

| # | 命令 | 期望 |
|---|---|---|
| 1 | `git status --porcelain` | 除 `tasks/T-111/` 外无新增改动 |
| 2 | `git diff --stat` | 空 |
| 3 | `tasks/T-111/BRIEF.md` | 含活性表（活/半活/死）、3 个论断的逐条核实结论、死代码行数 |

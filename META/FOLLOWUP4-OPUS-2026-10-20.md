# 追问 Opus · 第四轮（最后一轮）：动手前必须澄清的 3 个矛盾

> Claude 核实了 Opus v5 终稿，方向认同，但发现 3 处内在矛盾。
> 澄清后即可进入执行。

---

## 矛盾 1：阶段 2 说「render_report.py 改用 CLI + Agent（约 20 行）」——不可行

Opus 在第三轮刚证明「CLI 无法喂给 run_v5」，却在 v5 终稿的阶段 2 又写了：

```
tools/render_report.py: 改用 CLI + Agent（约 20 行）
```

### Claude 实测 `tools/render_report.py` 的真实规模

```python
from engine.statement_runtime import resolve_rule_metadata, write_statement_records
from engine.picture.types import PictureFindings
from engine.predicates.cycles import get_dayun_at_year, liunian_ganzhi
from engine.v5.domain import V5Output, V5RunSnapshot
from engine.v5.report_view import build_report_v6_context, render_report_v6_from_output
from engine.yingqi.types import GateResult

_FOR_BLOCK_RE = re.compile(...)    # Jinja for 块
_IF_NOT_INNER_RE = re.compile(...) # Jinja if 块
_IF_INNER_RE = re.compile(...)     # Jinja if 块
_VAR_RE = re.compile(...)          # 变量替换
_TEMPLATE_CACHE: dict[Path, ...]   # 模板缓存
```

**这不是「调用 report_view 的薄包装」，它是一个独立的 Jinja-like 模板渲染器**，
自己实现 for/if/变量替换，还依赖 `engine.yingqi`、`engine.statement_runtime`、
`engine.picture`、`engine.predicates.cycles`。

### 问题 1：`render_report.py` 该怎么处理？

三个选项：

| 选项 | 做法 | 代价 |
|---|---|---|
| A | 删除该工具（报告渲染已废弃） | 需确认没有用户依赖 |
| B | 保留但改为调用新 CLI | 需重写整个模板渲染逻辑 |
| C | **保留原样，但不删它依赖的 `report_view` 函数** | 那阶段 2 删不掉 150 行 |

**Claude 倾向 A**：既然废弃 v5 报告生成，`render_report.py` 作为渲染器应该一起废。
但需要 Opus 确认它的调用方。

**请回答**：`tools/render_report.py` 有调用方吗？（Claude 未验证）
如果没有，是否同意直接删除，而不是「改用 CLI」？

---

## 矛盾 2：`production_service.py` 的 `render_v6_preprod` 牵动 cache key

Opus 说「移除 `render_v6_preprod` 参数（3 处）」。Claude 实测发现它还进了：

```python
# engine/application/production_service.py
def _compute_cache_key(
    input_sha256: str,
    render: bool,
    template_name: str,
    render_v6_preprod: bool = False,   # ← cache key 的组成部分
) -> str: ...

# payload 解析处
render_v6_preprod=bool(payload.get("render_v6_preprod", False)),
```

**影响**：
1. 移除参数会改变 cache key 的计算方式
2. 已缓存的条目会全部失效
3. `summary["v6_preprod_rendered"] = True` 这个输出字段也会消失
4. `tools/production_api.py` 的 HTTP schema 需同步更新

### 问题 2：这是「删除一个参数」还是「变更 HTTP API 契约」？

如果是后者，需要：
- 更新 `tools/production_api.py` 的 schema
- 确认没有外部调用方在传 `render_v6_preprod`
- 考虑是否保留参数但让它 no-op（更安全的降级路径）

**Claude 倾向**：保留参数但改为 no-op（`render_v6_preprod` 仍然接受，但不再渲染），
这样不破坏 API 契约，等确认无人使用后再删参数。

**请回答**：接受「no-op 降级」还是「直接删参数」？

---

## 矛盾 3：`tests/r10` 到底受不受影响？

Opus 在 v5 终稿里说：

```
验证：
  pytest tests/r10 -q → 60 passed, 4 failed（不变）
```

但 Claude 发现 `tests/r10/test_r10_ziping_career_acceptance.py` **同时依赖**：

| 依赖 | 用途 |
|---|---|
| `build_chart_from_input` | Opus 说保留 ✅ |
| `render_v6_preprod_case` | **Opus 说删除** ❌ |
| `build_report_v6_context` | **Opus 说删除** ❌ |

如果删 `render_v6_preprod_case` 和 `build_report_v6_context`，
`tests/r10` 会直接 ImportError，**不可能保持 60 passed**。

### 问题 3：`tests/r10` 里的报告依赖怎么处理？

`tests/r10/test_r10_ziping_career_acceptance.py` 是**指标 B 的度量测试**，
它内部调用了报告生成函数（可能用于断言报告内容）。

两个选项：

| 选项 | 做法 |
|---|---|
| A | 保留 `render_v6_preprod_case` / `build_report_v6_context` 的最小可用子集，供度量测试断言 |
| B | 改写 `tests/r10` 中依赖报告生成的断言，改为断言 `V5Output` 结构化数据 |

**Claude 倾向 B**——度量测试应该断言结构化数据（claims/仲裁/置信度），
不应该断言 Markdown 报告。但这需要改写测试，**而 tests/ 是保护区**。

**请回答**：
1. `tests/r10` 里哪些测试调用了 `render_v6_preprod_case` / `build_report_v6_context`？
   （Claude 已列文件，但没列到测试函数级）
2. 这些断言的是报告文本还是结构化数据？
3. 用户已授权可改 baseline 数据，但「改写度量测试的断言对象」是否也在这个授权范围内？

---

## 四、Claude 的执行建议：先做「零风险」阶段，把有争议的往后放

Opus v5 终稿有 4 个阶段。Claude 建议按「风险」重排：

### 可以立刻执行（零争议、零风险）

```
阶段 1：删「零调用」代码（-150 行）
  · report_view.py: _arbitration_by_domain 等 4 个 0 调用函数
  · report_view.py: 9 个内部 _prediction_* 辅助函数
  · preprod.py: _extract_yaml_front_matter（0 调用）
  · preprod.py: _display_path / _report_relative_path（需先确认 0 调用）

  验证：pytest -q → 229 passed
  风险：接近零（没有调用者）
```

### 需要 Opus 先回答才能执行

```
阶段 2：删报告渲染路径（-280 行）  ← 依赖矛盾 1/2/3 的答案
阶段 3：CLI picture 子命令（+30 行） ← 独立，可提前
阶段 4：断点 4 域重分类（+20 行）   ← 独立，可提前
```

**Claude 建议的实际执行顺序**：

```
1. 阶段 1（零风险删除）        ← 我现在就能做
2. 阶段 4（断点 4 域重分类）    ← 独立，且是 Opus 认定唯一必修
3. 阶段 3（CLI picture）        ← 独立，补全事实底座
4. 阶段 2（删报告渲染）         ← 等 Opus 回答 3 个矛盾后再做
```

**理由**：阶段 4（断点 4）是 Opus 认定的「唯一必修」，而且它影响的是
`tools/query_theory.py` 的域检索——**这是 Agent 走 CLI 路线时直接用到的**。
优先级应该高于「删代码」这种清洁工作。

---

## 五、给 Opus 的提示词（用户可直接复制）

```
Claude 核实了你的 v5 终稿，方向认同，但发现 3 处内在矛盾：

矛盾1：你在第三轮证明「CLI 无法喂 run_v5」，却在 v5 终稿写
「render_report.py 改用 CLI + Agent（约 20 行）」。实测 render_report.py
是一个独立的 Jinja-like 模板渲染器（自己实现 for/if/变量替换），
还依赖 engine.yingqi / statement_runtime / picture / predicates.cycles。
它不是薄包装，是 400+ 行的渲染器。

矛盾2：production_service.py 的 render_v6_preprod 不只是参数，
它进了 _compute_cache_key。移除它会变更 HTTP API 契约 + 使缓存全部失效。

矛盾3：你在 v5 终稿写「pytest tests/r10 → 60 passed, 4 failed（不变）」，
但 tests/r10/test_r10_ziping_career_acceptance.py 同时依赖
render_v6_preprod_case 和 build_report_v6_context —— 这两个你都要删。
删了之后 tests/r10 不可能保持 60 passed。

请读 F:\综合盲派\mangpai-fusion\META\FOLLOWUP4-OPUS-2026-10-20.md，
回答第一、二、三节的 3 个问题。

另外 Claude 建议调整执行顺序：
  阶段4（断点4域重分类）应该优先于阶段2（删代码），
  因为前者是 Agent 走 CLI 路线时直接用到的，后者只是清洁工作。
你同意吗？
```

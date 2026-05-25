# v1.3 重构 Handoff · 2026-05-25

> 本文记录 v1.3 自迭代闭环落地后的状态，供下一个 session/agent 无损接续。
> 取代 v1.2 旧版。

---

## 一、当前状态：W4 验收进行中

**版本**：`VERSION` = `1.2.0`（待改为 `1.3.0`）
**主分支**：`main`，HEAD = `5eb1dfe`（W3 已合并）
**工作分支**：`feat/v1.3-w4-acceptance`（本地已建，未 push，有未提交文件）
**工作目录**：`/projects/sandbox/mangpai-fusion`

### W1-W3 已合并 main

| PR | 内容 | 关键产出 |
|---|---|---|
| #26 | 架构方案 D1-D8 锁定 | `plans/architecture-v1.3.md` |
| #27 | W1: D1+D2+D5 | statement_id / 双版报告 / feedback_ingest |
| #28 | W2: D6+D7 | batch_intake / batch_review / late_feedback / event_signature |
| #29 | W3: D3+D4+D8 | boundary_miner / veto_miner / iteration_report / 自动触发接入 |

### W4 当前进度

| 任务 | 状态 |
|---|---|
| 测试文件 5 个已建（syntax OK） | ✅ |
| H1 sid 稳定性 stdlib smoke | ✅ PASS |
| **H2 双版差分** | 🟡 **暴露 _render_template 嵌套 if bug** |
| H3 解析正确率 | ✅ 逻辑已验证（W1 /tmp 测试全 PASS） |
| H6 完整闭环 | ✅ 逻辑已验证（W3 /tmp 测试全 PASS） |
| 修 bug + 全量重跑 | 🔜 |
| VERSION → 1.3.0 + STATUS.md | 🔜 |
| commit + push + PR + merge + tag | 🔜 |

---

## 二、必须修的 Bug

### `_render_template` 嵌套 {% if %} 错配

**文件**：`tools/render_report.py` 约 L771-815（`_render_template` 函数 step 2 + step 3）

**根因**：非贪婪正则 `(.*?)` 遇嵌套 if 时，外层 if 的 body 被截断到内层的第一个 endif。

```
{% if gate_results %}          ← 外层 start
  ...
  {% if is_master %}反馈：[S-001] [ ]{% endif %}  ← 内层完整
  ...
{% endif %}                    ← 外层 end（但正则把内层 endif 当成外层的）
```

**现象**：client 模式（`is_master=False`）下泄漏 1 个反馈位（本应被 `{% if is_master %}` 隐藏）。

**修复方案**：把单次 `re.sub` 改为**内层优先 + while 循环**：

```python
# 关键：正则 body 中加负前瞻 (?:(?!\{%\s*if\b).)*?
# 确保匹配的 body 中不含嵌套 {% if %}，这样 endif 一定配对最内层
_if_not_inner = re.compile(
    r"\{%\s*if\s+not\s+(\w+)\s*%\}((?:(?!\{%\s*if\b).)*?)\{%\s*endif\s*%\}",
    re.DOTALL,
)
_if_inner = re.compile(
    r"\{%\s*if\s+(\w+)\s*%\}((?:(?!\{%\s*if\b).)*?)\{%\s*endif\s*%\}",
    re.DOTALL,
)

changed = True
while changed:
    changed = False
    def _expand_if_not(m):
        nonlocal changed; changed = True
        return m.group(2) if not ctx.get(m.group(1)) else ""
    out = _if_not_inner.sub(_expand_if_not, out)
    def _expand_if(m):
        nonlocal changed; changed = True
        return m.group(2) if ctx.get(m.group(1)) else ""
    out = _if_inner.sub(_expand_if, out)
```

**验证**：
```bash
# 修完后跑
python3 -c "
import sys, json, types, pathlib, re
# ... 桩 yaml ...
from tools.render_report import _render_template
tpl = pathlib.Path('templates/report-v1.3.md').read_text(encoding='utf-8')
ctx = {..., 'is_master': False, 'is_client': True, ...}  # client 模式
out = _render_template(tpl, ctx)
fb_re = re.compile(r'\[S-[\w-]+\]\s*\[\s*\]')
assert len(fb_re.findall(out)) == 0, 'client 不应有反馈位'
print('H2 fix verified')
"
```

---

## 三、W4 已建测试文件清单

| 文件 | H 指标 | 测试内容 |
|---|---|---|
| `tests/v1_3_acceptance/__init__.py` | — | 说明文档 |
| `tests/v1_3_acceptance/conftest.py` | — | Mock fixtures（MockEnergy/MockPicture/MockGate/MockParsed） |
| `tests/v1_3_acceptance/test_h1_statement_id_stable.py` | H1 | 5 次重跑 sid 一致 / 格式 / 跨案不撞 / 排序无关 / 集合变 ID 变 |
| `tests/v1_3_acceptance/test_h2_dual_variant.py` | H2 | master 有反馈位 / client 无 / client ★≤3 过滤 / master 保留弱项 / sid 子集关系 |
| `tests/v1_3_acceptance/test_h3_feedback_parsing.py` | H3 | 100 样本正确率≥99% / ?/skip→no_data / 重复取最后 / fanout 决断力优先 |
| `tests/v1_3_acceptance/test_h6_full_loop.py` | H6 | 10 案触发 / 异常 warn-only / 20 案 seq=2 / 重复不计数 |

pytest marker：`v1_3_acceptance`（已注册到 `pyproject.toml`）

---

## 四、v1.3 新增工具速查

| 工具 | 路径 | CLI |
|---|---|---|
| 结构化反馈摄入 | `tools/feedback_ingest.py` | `python3 -m tools.feedback_ingest C-XXXX` |
| 批量入库 | `tools/batch_intake.py` | `python3 -m tools.batch_intake` |
| 批量复盘 | `tools/batch_review.py` | `python3 -m tools.batch_review` |
| 应期延迟反馈 | `tools/late_feedback.py` | `python3 -m tools.late_feedback C-XXX --year 2027 --event marriage --hit yes` |
| 边界自动挖掘 | `tools/boundary_miner.py` | `python3 -m tools.boundary_miner [rule_id]` |
| 候选否决兜底 | `tools/veto_miner.py` | `python3 -m tools.veto_miner [rule_id]` |
| 迭代报告调度 | `tools/iteration_report.py` | `python3 -m tools.iteration_report [--seq N]` |

---

## 五、v1.3 新增模板 + 数据文件

| 文件 | 用途 |
|---|---|
| `templates/report-v1.3.md` | v1.3 双版报告模板（{% if is_master %} 控制反馈位） |
| `META/iteration-state.json` | D8 反馈完成案计数器 |
| `cases/_TEMPLATE/feedback.md` | v1.3 反馈模板（报告即反馈表） |
| `plans/architecture-v1.3.md` | D1-D8 决策面板完整文档 |

---

## 六、v1.3 决策面板速查（D1-D8 锁定）

| # | 决策 | 锁定值 |
|---|---|---|
| D1 | statement_id | `S-{case_seq}-{sha256(sorted_rule_ids)[:6]}` |
| D2 | 双版输出 | master 含反馈位 + 弱项；client 仅 ★4+ |
| D3 | boundary_miner | ≥5 miss + p<0.1 + lift≥2 + 回放验证 hit_rate 升 |
| D4 | veto_miner | ≥5 miss + n≥10 + posterior<40% + boundary 空 → flagged_for_review |
| D5 | 过后反馈 | [y]/[n]/[?]/[skip]；? 入库不计数 |
| D6 | 批量工作流 | batch_intake（inbox→pipeline）+ batch_review（pending→ingest） |
| D7 | 应期延迟 | ±1 年窗口；hit=1.0/0.5；统计独立隔离不污染画像 |
| D8 | 自迭代触发 | 每 10 **完成反馈案**（非入库）→ iteration_report |

---

## 七、沙箱约束提醒

- **无外网**（INTEGRATIONS_ONLY）→ pip install 全部失败
- **无 PyYAML** → 测试必须桩 yaml 模块（`sys.modules["yaml"] = fake_yaml`）
- **无 pytest** → 正式 pytest 跑不了；用 `/tmp/test_*.py` stdlib 脚本验证
- **git push** → 用 `mcp_sandbox_github_push_to_remote`（需参数：path, owner, repository_name, remote_branch_name）
- **PR 创建** → 用 `mcp_sandbox_github_create_pull_request`

---

## 八、新开对话的第一条指令

```
继续 W4 验收。当前分支 feat/v1.3-w4-acceptance（本地未 push）。

待办：
1. 修 tools/render_report.py _render_template 嵌套 if bug（handoff.md § 二 有完整方案）
2. 验证 H2 修复（client 反馈位 = 0）
3. 跑 H1+H2+H3+H6 全 PASS（stdlib smoke）
4. VERSION → 1.3.0 + STATUS.md 加 M10
5. commit + push + PR + 合 main + 打 tag v1.3.0

仓库：lynhao-mike/mangpai-fusion
分支：feat/v1.3-w4-acceptance
工作目录：/projects/sandbox/mangpai-fusion
```

---

**本 handoff 由 v1.3 W4 session 于 2026-05-25 写入。**
**W1-W3 已全部合并 main。W4 待修 1 个 bug + 验收 + tag。**

# R9 执行计划：L3 结构审查消费 v5 格局用忌神做一致性审查

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **执行模型要求：本计划由 claude-fable-5 执行**（涉及命理判断边界，不交廉价模型）。

**Goal:** 让 L3 结构审查从"只按 confidence 阈值"升级为"消费 v5 已算出的格局用忌神方向，对与格局明确矛盾的命题降级（weaken），对忌神方向单证且低置信的命题否决（reject）"。第一次让 L3 产出非零 reject/weaken，成为真正的结构关口而非通道。

**Architecture:** v5 已产出结构化格局裁决 metadata（`geju_type` / `favor_shishen` / `avoid_shishen` / `constraint_text`），但 [`_claims`](../../../engine/decision/v5_adapter.py:71) 构造 SchoolClaim 时丢弃了 metadata。R9 分三步：(1) 给 SchoolClaim 加可选 metadata 字段透传 v5 结构化数据；(2) 从格局裁决 claim 提取用忌神方向；(3) L3 [`_verdicts`](../../../engine/decision/v5_adapter.py:91) 用用忌神方向审查同域命题一致性。**这是消费 v5 已算出的命理结论，不是发明新命理。**

**Tech Stack:** Python 3、pytest。纯内存数据流，无外部依赖、无 IO。

## Global Constraints

- 事实源以 [`AGENTS.md`](../../../AGENTS.md) 为准；方向以 [`plans/layered-decision-system.md`](../../../plans/layered-decision-system.md) §18 Phase R6 与 [`plans/l0-l9-refactor-geju-judgment-2026-07-10.md`](../../../plans/l0-l9-refactor-geju-judgment-2026-07-10.md) 为准。
- **只消费 v5 已产出的格局裁决结论，绝不发明新的命局判断规则。** L3 的审查依据必须能追溯到某条 v5 格局裁决 claim 的 favor_shishen/avoid_shishen，不得凭空判定旺衰或用神。
- **reject 必须极度克制**：只有当命题明确依赖 avoid_shishen 方向（忌神）**且** confidence 低于阈值 **且** 无任何 favor 支撑时才 reject。有疑问一律 weaken 不 reject——错误 reject 会砍掉可能正确的命题，比漏放更危险。
- 不改 L1/L2/L4/L5/L6/L7、不改 v5 runner、不改 report 渲染。R9 只动 SchoolClaim schema（加可选字段）与 L3 `_verdicts`。
- 无格局裁决 claim（metadata 缺失）时，L3 必须回退到当前 confidence 阈值行为（零回归）。
- `validate_trace()` 必须仍返回空；L4 事件只绑定 pass/weaken 的 verdict（models.py 已有此校验），reject 的命题不进 L4。
- 每个任务结束跑绿相关测试；Windows cmd.exe：命令用 `&&` 串联，不用 `sed`/`grep`/`cat`；提交信息用中文。

## 背景事实（执行前必读，已实测确认）

1. v5 格局裁决 claim 的 metadata 结构（实测 C-2026-035）：
   ```json
   {"layer": "L3_geju_type", "geju_type": "正格",
    "favor_shishen": ["正官","七杀","正财","偏财","食神","伤官"],
    "avoid_shishen": ["正印","偏印","比肩","劫财"],
    "constraint_text": "取食神/伤官为用，日主偏旺方向调配"}
   ```
2. 全盘仅 **1 条** claim 带 `geju_type` metadata（子平 runner 产出），domain="事业"。旺衰判定 claim 也仅 1 条。
3. [`SchoolClaim`](../../../engine/decision/models.py:115) 当前无 metadata 字段；[`_claims`](../../../engine/decision/v5_adapter.py:80) 只搬 statement，丢弃 v5 claim.metadata。
4. L3 [`_verdicts(case_id, claims)`](../../../engine/decision/v5_adapter.py:91) 现状：structure_claim confidence>=0.4→pass 否则 weaken；event_claim→weaken；其他→unknown。**0 reject**。
5. `SchoolClaim` 无枚举约束，[`validate_trace`](../../../engine/decision/models.py:405) 只校验 verdict∈{pass,weaken,reject,unknown}、L4 event 只能绑 pass/weaken 的 verdict。
6. v5 claim 的十神信息在 statement 文本里（如"正印格""偏财"），可用关键词匹配判断命题涉及哪些十神。

---

### Task 1: SchoolClaim 增加可选 metadata 字段并透传（TDD）

**Files:**
- Modify: `engine/decision/models.py`（SchoolClaim）
- Modify: `engine/decision/v5_adapter.py`（`_claims`）
- Test: `tests/test_l3_geju_review.py`（新建）

**Interfaces:**
- SchoolClaim 增加 `metadata: dict[str, Any] = field(default_factory=dict)`，并在 to_dict 输出。
- `_claims` 把 v5 `claim.metadata` 透传到 SchoolClaim.metadata。

- [ ] **Step 1: 写失败测试**

新建 [`tests/test_l3_geju_review.py`](../../../tests/test_l3_geju_review.py)：

```python
from __future__ import annotations

from engine.decision.models import SchoolClaim


def test_school_claim_carries_metadata():
    c = SchoolClaim(
        claim_id="c1", school="ziping", role_granted_by_l1="lead",
        domain="事业", claim_type="structure", statement="正印格",
        metadata={"geju_type": "正格", "favor_shishen": ["食神"]},
    )
    assert c.metadata["geju_type"] == "正格"
    assert "metadata" in c.to_dict()
    assert c.to_dict()["metadata"]["geju_type"] == "正格"


def test_school_claim_metadata_defaults_empty():
    c = SchoolClaim(
        claim_id="c1", school="ziping", role_granted_by_l1="lead",
        domain="事业", claim_type="structure", statement="x",
    )
    assert c.metadata == {}
```

- [ ] **Step 2: 运行确认失败**

Run: `python -m pytest tests/test_l3_geju_review.py -v`
Expected: FAIL（SchoolClaim 不接受 metadata 关键字 → TypeError）。

- [ ] **Step 3: 给 SchoolClaim 加 metadata 字段**

在 [`engine/decision/models.py`](../../../engine/decision/models.py:125) 的 SchoolClaim 的 `dependencies` 字段之后加：

```python
    metadata: dict[str, Any] = field(default_factory=dict)
```

在其 to_dict 的 `"dependencies": list(self.dependencies),` 之后加：

```python
            "metadata": dict(self.metadata),
```

> 确认文件顶部已 `from typing import Any`；若无则不需要改（models.py 已使用 Any）。

- [ ] **Step 4: _claims 透传 metadata**

在 [`engine/decision/v5_adapter.py`](../../../engine/decision/v5_adapter.py:84) 的 SchoolClaim 构造里，`dependencies=[f"v5:{claim.claim_id}"],` 之后加：

```python
            metadata=dict(claim.metadata),
```

- [ ] **Step 5: 运行确认通过**

Run: `python -m pytest tests/test_l3_geju_review.py -v`
Expected: 2 PASS。

- [ ] **Step 6: 回归**

Run: `python -m pytest tests/test_decision_mvp.py tests/test_decision_v5_adapter.py -q`
Expected: 全绿。若 `test_decision_v5_adapter.py` 有 `to_dict()` 精确相等断言因新增 metadata 键失败，用 search 确认后更新该断言以包含 metadata 键——这是预期内更新。

- [ ] **Step 7: 提交**

```bash
git add engine/decision/models.py engine/decision/v5_adapter.py tests/test_l3_geju_review.py && git commit -m "feat: SchoolClaim 增加 metadata 字段并透传 v5 格局结构化数据"
```

---

### Task 2: 提取格局用忌神方向的纯函数（TDD）

**Files:**
- Modify: `engine/decision/v5_adapter.py`
- Test: `tests/test_l3_geju_review.py`（追加）

**Interfaces:**
- Produces: `_extract_geju_profile(claims: list[SchoolClaim]) -> dict | None`
  - 从 claims 里找带 `geju_type` metadata 的格局裁决 claim，返回 `{"geju_type", "favor": set[str], "avoid": set[str]}`。
  - 找不到返回 None（触发 L3 回退旧行为）。

- [ ] **Step 1: 写失败测试**

在 [`tests/test_l3_geju_review.py`](../../../tests/test_l3_geju_review.py) 末尾追加：

```python
def test_extract_geju_profile_reads_favor_avoid():
    from engine.decision.v5_adapter import _extract_geju_profile

    claims = [
        SchoolClaim(claim_id="c1", school="ziping", role_granted_by_l1="lead",
                    domain="事业", claim_type="structure", statement="格局大类裁决：正格",
                    metadata={"geju_type": "正格",
                              "favor_shishen": ["食神", "伤官"],
                              "avoid_shishen": ["正印", "比肩"]}),
        SchoolClaim(claim_id="c2", school="duan_jianye", role_granted_by_l1="lead",
                    domain="事业", claim_type="event", statement="做功"),
    ]
    profile = _extract_geju_profile(claims)
    assert profile is not None
    assert profile["geju_type"] == "正格"
    assert "食神" in profile["favor"]
    assert "正印" in profile["avoid"]


def test_extract_geju_profile_none_when_absent():
    from engine.decision.v5_adapter import _extract_geju_profile

    claims = [
        SchoolClaim(claim_id="c1", school="duan_jianye", role_granted_by_l1="lead",
                    domain="事业", claim_type="event", statement="做功"),
    ]
    assert _extract_geju_profile(claims) is None
```

- [ ] **Step 2: 运行确认失败**

Run: `python -m pytest tests/test_l3_geju_review.py::test_extract_geju_profile_reads_favor_avoid -v`
Expected: FAIL（ImportError）。

- [ ] **Step 3: 实现提取函数**

在 [`engine/decision/v5_adapter.py`](../../../engine/decision/v5_adapter.py) 的 `_verdicts` 定义之前新增：

```python
def _extract_geju_profile(claims: list[SchoolClaim]) -> dict | None:
    """从带 geju_type metadata 的格局裁决 claim 提取用忌神方向。

    R9：只消费 v5 已算出的格局结论，不自行判定旺衰/用神。找不到返回 None。
    """

    for claim in claims:
        meta = claim.metadata or {}
        if meta.get("geju_type"):
            return {
                "geju_type": str(meta.get("geju_type")),
                "favor": {str(x) for x in meta.get("favor_shishen", [])},
                "avoid": {str(x) for x in meta.get("avoid_shishen", [])},
            }
    return None
```

- [ ] **Step 4: 运行确认通过**

Run: `python -m pytest tests/test_l3_geju_review.py -v`
Expected: 全部 PASS。

- [ ] **Step 5: 提交**

```bash
git add engine/decision/v5_adapter.py tests/test_l3_geju_review.py && git commit -m "feat: 新增 _extract_geju_profile 提取 v5 格局用忌神方向"
```

---

### Task 3: L3 _verdicts 用格局用忌神做一致性审查（TDD）

**Files:**
- Modify: `engine/decision/v5_adapter.py`（`_verdicts`）
- Test: `tests/test_l3_geju_review.py`（追加）

**Interfaces:**
- 改 `_verdicts(case_id, claims)`：先 `_extract_geju_profile(claims)`；对每条命题，用 `_shishen_in_statement(statement)` 找出它涉及的十神：
  - 命题涉及 avoid 十神且不涉及 favor 十神 → 降一级（pass→weaken）；若原本已 weaken 且 confidence<0.3 → reject。
  - 其余保持现有 confidence 阈值逻辑。
  - profile 为 None 时完全走旧逻辑（零回归）。
- 新增辅助 `_shishen_in_statement(statement: str) -> set[str]`：从文本匹配十神名。

- [ ] **Step 1: 写失败测试**

在 [`tests/test_l3_geju_review.py`](../../../tests/test_l3_geju_review.py) 末尾追加：

```python
def test_verdicts_weaken_claim_against_geju_avoid():
    from engine.decision.v5_adapter import _verdicts

    claims = [
        SchoolClaim(claim_id="g", school="ziping", role_granted_by_l1="lead",
                    domain="事业", claim_type="structure", statement="格局大类裁决：正格",
                    confidence=0.65,
                    metadata={"geju_type": "正格", "favor_shishen": ["食神"], "avoid_shishen": ["正印"]}),
        # 一条依赖忌神(正印)、无 favor、confidence 偏低的结构命题
        SchoolClaim(claim_id="bad", school="ziping", role_granted_by_l1="lead",
                    domain="事业", claim_type="structure", statement="正印当权主贵", confidence=0.45),
    ]
    verdicts = {v.claim_id: v for v in _verdicts("C-T", claims)}
    # 依赖忌神的命题应被降级（不再是 pass）
    assert verdicts["bad"].verdict in {"weaken", "reject"}


def test_verdicts_zero_regression_without_geju_profile():
    from engine.decision.v5_adapter import _verdicts

    claims = [
        SchoolClaim(claim_id="s", school="ziping", role_granted_by_l1="lead",
                    domain="事业", claim_type="structure", statement="日主得令", confidence=0.6),
    ]
    # 无格局 profile → 走旧逻辑：structure confidence>=0.4 → pass
    verdicts = {v.claim_id: v for v in _verdicts("C-T", claims)}
    assert verdicts["s"].verdict == "pass"


def test_verdicts_favor_claim_stays_pass():
    from engine.decision.v5_adapter import _verdicts

    claims = [
        SchoolClaim(claim_id="g", school="ziping", role_granted_by_l1="lead",
                    domain="事业", claim_type="structure", statement="格局大类裁决：正格",
                    confidence=0.65,
                    metadata={"geju_type": "正格", "favor_shishen": ["食神"], "avoid_shishen": ["正印"]}),
        SchoolClaim(claim_id="good", school="ziping", role_granted_by_l1="lead",
                    domain="事业", claim_type="structure", statement="食神吐秀主聪明", confidence=0.6),
    ]
    verdicts = {v.claim_id: v for v in _verdicts("C-T", claims)}
    assert verdicts["good"].verdict == "pass"
```

- [ ] **Step 2: 运行确认失败**

Run: `python -m pytest tests/test_l3_geju_review.py::test_verdicts_weaken_claim_against_geju_avoid -v`
Expected: FAIL（当前 `_verdicts` 不看格局，"bad" 会因 confidence 0.45>=0.4 判 pass）。

- [ ] **Step 3: 改 _verdicts 实现**

在 [`engine/decision/v5_adapter.py`](../../../engine/decision/v5_adapter.py) 的 `_verdicts` 之前新增十神匹配辅助：

```python
_SHISHEN_NAMES = ("正官", "七杀", "正财", "偏财", "食神", "伤官", "正印", "偏印", "比肩", "劫财")


def _shishen_in_statement(statement: str) -> set[str]:
    text = statement or ""
    return {name for name in _SHISHEN_NAMES if name in text}
```

把 `_verdicts` 改为：

```python
def _verdicts(case_id: str, claims: list[SchoolClaim]) -> list[StructuralVerdict]:
    profile = _extract_geju_profile(claims)
    result: list[StructuralVerdict] = []
    for claim in claims:
        if claim.claim_type == "structure_claim":
            verdict = "pass" if claim.confidence >= 0.4 else "weaken"
        elif claim.claim_type == "event_claim":
            verdict = "weaken"
        else:
            verdict = "unknown"

        reason = "L3 只审查结构基础；事件、应期与旁证命题不得在本层直接定案。"
        blocking: list[str] = []

        # R9：用 v5 已算出的格局用忌神方向做一致性审查（不发明命理）。
        if profile and verdict in {"pass", "weaken"}:
            shishen = _shishen_in_statement(claim.statement)
            hits_avoid = shishen & profile["avoid"]
            hits_favor = shishen & profile["favor"]
            if hits_avoid and not hits_favor:
                reason = f"命题依赖格局忌神 {sorted(hits_avoid)}（{profile['geju_type']}），与用神方向不一致，降级。"
                blocking = [f"忌神方向：{sorted(hits_avoid)}"]
                if verdict == "pass":
                    verdict = "weaken"
                elif verdict == "weaken" and claim.confidence < 0.3:
                    verdict = "reject"

        result.append(
            StructuralVerdict(
                verdict_id=_stable_id("dsv", case_id, claim.claim_id),
                claim_id=claim.claim_id,
                verdict=verdict,  # type: ignore[arg-type]
                structural_reason=reason,
                blocking_factors=blocking,
                required_support=[] if verdict == "pass" else ["ziping", "ditiansui"],
                confidence=claim.confidence,
            )
        )
    return result
```

> 注意：保留原 `_verdicts` 对 structure_claim / event_claim / 其他的分支判断口径；只在其后叠加格局一致性审查。若原实现的 required_support / confidence 赋值与此处不同，以原有语义为准微调，但必须保证 profile=None 时逐字回退。

- [ ] **Step 4: 运行确认通过**

Run: `python -m pytest tests/test_l3_geju_review.py -v`
Expected: 全部 PASS。

- [ ] **Step 5: decision 回归**

Run: `python -m pytest tests/test_decision_mvp.py tests/test_decision_v5_adapter.py -q`
Expected: 全绿。若某测试断言"L3 全 pass / 0 reject"，用 search 确认后更新为兼容 weaken/reject——这是 R9 的预期效果，不是回归。特别检查 L4 event 是否仍只绑 pass/weaken 的 verdict（被 reject 的命题不应有 L4 event 绑定它）。

- [ ] **Step 6: 提交**

```bash
git add engine/decision/v5_adapter.py tests/test_l3_geju_review.py && git commit -m "feat: L3 用 v5 格局用忌神方向做一致性审查，产出非零 weaken/reject"
```

---

### Task 4: 重跑 C-2026-035 验证 + 文档状态更新

**Files:**
- Modify: `plans/layered-decision-system.md`

**Interfaces:**
- Produces: §18 记录 R9 已让 L3 成为真实结构关口（消费 v5 格局，非发明命理）。

- [ ] **Step 1: 重跑真实 case**

Run: `python tools/render_report_v6.py cases/C-2026-035-乾-戊辰癸亥甲戌庚午/input.md --output-dir reports`
Expected: 退出码 0。

- [ ] **Step 2: 验证 L3 产出非零降级且 trace 干净**

Run:
```bash
python -c "import json,pathlib,sys; d=json.loads(pathlib.Path('reports/C-2026-035-乾-戊辰癸亥甲戌庚午-v6-preprod-content-report.decision-run.json').read_text(encoding='utf-8')); sv=d['structural_verdicts']; from collections import Counter; c=Counter(v['verdict'] for v in sv); sys.stdout.buffer.write(('verdict dist: '+str(dict(c))).encode('utf-8')); sys.stdout.buffer.write(b'\n')"
```
Expected: 打印 verdict 分布。若格局 profile 生效，应出现 weaken（可能出现 reject）；无论如何 `python -c "...validate_trace..."` 需仍为空（用 Task 3 已有回归覆盖，或另跑 test_decision_v5_adapter）。

> 注意：C-2026-035 只有 1 条格局裁决（事业域正格），所以只有事业域命题会被一致性审查；其余域无 profile，保持旧行为。这是预期的——R9 覆盖度取决于 v5 产出多少格局裁决。

- [ ] **Step 3: 在 §18 追加 R9 状态**

在 [`plans/layered-decision-system.md`](../../../plans/layered-decision-system.md) §18 Phase R8 段之后新增：

```markdown
### Phase R9：L3 结构审查消费格局用忌神（一致性审查）

> 状态：已落地（L3 消费 v5 已算出的格局 favor/avoid 十神方向，对依赖忌神且无 favor 支撑的命题降级，低置信再 reject；无格局裁决时零回归，见 tests/test_l3_geju_review.py）。**这是消费 v5 已算出的格局结论做一致性审查，不是 L3 自行判定旺衰/用神**。当前覆盖度取决于 v5 产出的格局裁决数量（C-2026-035 仅事业域有格局裁决）。扩大 L3 真实审查覆盖（更多域产出格局裁决、旺衰独立校验）属后续与命局知识建模的工作。
```

- [ ] **Step 4: 提交**

```bash
git add plans/layered-decision-system.md && git commit -m "docs: 标记 R9 L3 格局一致性审查已落地"
```

---

## 验收总清单（全部完成后执行一次）

- [ ] `python -m pytest tests/test_l3_geju_review.py tests/test_decision_mvp.py tests/test_decision_v5_adapter.py -q` 全绿。
- [ ] SchoolClaim 带 metadata 且透传 v5 格局结构化字段。
- [ ] 无格局 profile 时 L3 逐字回退旧 confidence 阈值行为（零回归测试通过）。
- [ ] 依赖忌神且无 favor 的命题被降级；依赖 favor 的命题保持 pass。
- [ ] 重跑 C-2026-035 后 `validate_trace()` 仍为空；被 reject 的命题不绑定 L4 event。

## 证伪口径（对照架构 §18 与 geju 判断）

- 若 L3 开始**凭空**判定旺衰/用神（不依赖任何 v5 格局裁决 claim），违反"只消费不发明"原则，必须回到 Task 2/3 收回——L3 在真实命局知识建模到位前，只能消费 v5 结论。
- 若 reject 砍掉了后续被反馈证明正确的命题，说明 reject 阈值过激，须调回只 weaken——**漏放好过错砍**。
- R9 **只**让 L3 用格局做一致性审查，覆盖度受限于 v5 产出的格局裁决数量。它**不**代表 L3 已是完整命局审查——多域格局裁决、旺衰独立校验、五派结构交叉验证仍未做，属命局知识建模的独立大工程，应在积累真实反馈后用 geju 单独立项。

## Self-Review 记录

- Spec 覆盖：R9 目标（L3 从阈值通道升级为格局一致性关口）由 Task 1（metadata 透传）+ Task 2（提取用忌神）+ Task 3（一致性审查）+ Task 4（真实 case 验证）覆盖。
- Placeholder 扫描：无 TBD；每步给完整可粘贴代码；仅回归步骤要求 search 确认既有断言（已标注为预期内更新）。
- 类型一致：`_extract_geju_profile(claims) -> dict|None` 在 Task 2 定义、Task 3 消费一致；`_shishen_in_statement` 与 `_SHISHEN_NAMES` 前后一致；SchoolClaim.metadata 在 models 与 _claims 两处一致。
- 已知风险显式化：只消费不发明（Global Constraints + 证伪口径 + 文档三处）、reject 极度克制（Global Constraints + Task 3 双重条件 + 证伪口径"漏放好过错砍"）、零回归（Task 1/3 测试 + 验收）、覆盖度受限于 v5 格局裁决数量（Task 4 注 + 文档 + 证伪口径）。
- 已实测确认：v5 格局裁决 metadata 结构与字段值；全盘仅 1 条格局裁决 claim；SchoolClaim 无 metadata 字段、无枚举校验；L3 现状 0 reject。

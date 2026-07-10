# R10 子平·事业域 L2 纵切片 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让子平 runner 的事业域命题原生进入 L2 `SchoolClaim`，并由链内 L1/L3/L4 产出角色、结构裁决与事件类型；该切片不再调用 `v5_adapter` 的命题反推或命理判断，同时保持报告、追踪链和 R6 信息量不退化。

**Architecture:** 保留唯一的 `DecisionRun` 和现有 v5 runner，不建立第三套 run 模型。新增一个无损的 V5Claim→L2 边界转换器；子平·事业域从 runner claim 直接进入该边界，L3/L4 判断迁回各自层。迁移期仍允许非目标切片走旧桥，但目标切片以显式来源标记和禁止调用测试证明不经 adapter 反推。

**Tech Stack:** Python 3.11+、标准库 `dataclasses` / `hashlib`、pytest、现有 `engine.v5` 与 `engine.decision` 数据模型。

## Global Constraints

- 只做 §R10.5 的“一派一域”证明物：`ziping × 事业`；不逐派逐域扩张、不删除整个 adapter、不切生产默认入口。
- 不新建第三套 run 模型；最终产物仍是 `engine.decision.models.DecisionRun`。
- **红线 1 — L2 不丢路径：** `SchoolClaim` 必须无损保留来源 V5Claim 已携带的旺衰、用神、格局/病药、做功路径；来源没有某路径时保留“缺失”，严禁补写或猜测。
- **红线 2 — L3/L4 只消费不发明：** L3 只能消费 L2 已携带的结构方向；L4 只能消费通过/降级的 L3 verdict 与 L2 可读命题；不得在 L3/L4 新判旺衰、用神、格局或做功。
- `evidence_refs`、`confidence`、`falsifier`、`metadata` 必须从来源 claim 原样映射；不得用默认话术覆盖来源值。
- 目标切片的 L1 role 必须来自 `route_schools()`；L2 转换器不得自行授予角色。
- 目标切片必须同时保留 `总体` 结构上下文与 `事业` 命题，因为当前子平 runner 的旺衰、格局类型和病药位于 `总体`，格局用神位于 `事业`。
- 报告 Markdown 继续禁止展示内部 ID；内部 `decision-run.json` 继续保留完整追踪 ID。
- 每个任务都按 RED→GREEN→REFACTOR 顺序执行；一个任务一个提交，不顺手迁移其他流派/领域。
- Windows `cmd.exe` 命令使用 `python -m pytest ...`；不使用 `grep`、`sed`、`rm` 等 Unix 工具。

## §R10.5 / §R10.6 验收矩阵

| 架构断言 / 证伪 | 落地任务 | 自动化证明 |
|---|---|---|
| (1) L1 role、L3 verdict、L4 event_type 均由链内层产出 | Task 2-6 | monkeypatch adapter 判断函数为抛错后，纵切片仍成功；role 与 router 输出相等 |
| (2) 报告事业域文本与 decision-run.json 一致 | Task 7 | 从同一个 L7 `ReportViewItem` 渲染报告并逐字断言 |
| (3) `validate_trace()` 返回空 | Task 7 | `assert run.validate_trace() == []` |
| (4) 五派依据与 15 层判断信息量不低于 R6 基线 | Task 1、8 | 固定正式 case 的基线计数 + 文本哨兵比较 |
| Falsifier 1：L2 丢旺衰/用神/做功路径 | Task 2、3、8 | 合成含三路径的 claim 做深相等；真实 runner 做路径哨兵校验 |
| Falsifier 2：报告依据变薄或 15 层塌陷 | Task 1、8 | 低于基线时测试明确 FAIL，不以更新快照掩盖 |

## File Structure

- Create: `engine/decision/l2_v5_claims.py` — V5Claim→SchoolClaim 的唯一无损边界转换；只做字段映射和 L1 授权校验。
- Modify: `engine/decision/l3_structure.py` — 接收 L2 metadata 做格局方向一致性审查；不运行命理推导。
- Modify: `engine/decision/l4_events.py` — 接收 L2 statement 与通过的 L3 verdict 做事件语义归类；不运行命理推导。
- Create: `engine/decision/r10_ziping_career.py` — 迁移期纵切片装配函数；只替换 `ziping × 事业`（及其 `总体`结构依赖）的 L2/L3/L4 路径。
- Modify: `engine/decision/v5_adapter.py` — 只把已迁移的 L3/L4 helper 改为兼容委托；不新增判断。
- Create: `tests/r10/test_r10_ziping_career_l2.py` — L2 无损、L1 授权与 adapter 隔离测试。
- Create: `tests/r10/test_r10_ziping_career_layers.py` — L3/L4 “只消费不发明”测试。
- Create: `tests/r10/test_r10_ziping_career_acceptance.py` — 四条断言和两条 falsifier 的端到端门禁。
- Create: `tests/r10/fixtures/r6_ziping_career_baseline.json` — 用固定正式 case 生成后人工审阅并冻结的 R6 信息量下限。
- Modify: `HANDOFF.md` — 纵切片验收通过后只更新 §3/§4/§5 状态；不得提前宣称 R10 全完成。

---

### Task 1: 冻结 R6 子平·事业域信息量基线

**Files:**
- Create: `tests/r10/fixtures/r6_ziping_career_baseline.json`
- Create: `tests/r10/test_r10_ziping_career_acceptance.py`

**Interfaces:**
- Consumes: 正式 case `C-2026-035-乾-戊辰癸亥甲戌庚午` 的现有 v6 preprod 报告与 `.decision-run.json`。
- Produces: `load_r6_baseline() -> dict[str, object]`，后续验收只允许“达到或超过”，不允许静默重录更低基线。

- [ ] **Step 1: 写失败测试，先要求基线文件存在且字段完整**

```python
# tests/r10/test_r10_ziping_career_acceptance.py
from __future__ import annotations

import json
from pathlib import Path

BASELINE_PATH = Path("tests/r10/fixtures/r6_ziping_career_baseline.json")


def load_r6_baseline() -> dict[str, object]:
    return json.loads(BASELINE_PATH.read_text(encoding="utf-8"))


def test_r6_baseline_is_frozen_and_nonempty() -> None:
    baseline = load_r6_baseline()
    assert baseline["case_id"] == "C-2026-035-乾-戊辰癸亥甲戌庚午"
    assert int(baseline["career_claim_count"]) > 0
    assert int(baseline["career_school_count"]) > 0
    assert int(baseline["career_evidence_count"]) > 0
    assert int(baseline["career_fifteen_layer_count"]) == 15
    assert baseline["required_text_sentinels"]
```

- [ ] **Step 2: 运行测试，确认 RED**

Run: `python -m pytest tests/r10/test_r10_ziping_career_acceptance.py::test_r6_baseline_is_frozen_and_nonempty -q`

Expected: `FAILED`，原因包含 `FileNotFoundError: tests/r10/fixtures/r6_ziping_career_baseline.json`。

- [ ] **Step 3: 用现有产物测量并直接写入基线文件**

Run:

```cmd
python tools/render_report_v6.py cases/C-2026-035-乾-戊辰癸亥甲戌庚午/input.md --output-dir reports
python -c "import json,pathlib; case='C-2026-035-乾-戊辰癸亥甲戌庚午'; p=pathlib.Path('reports')/(case+'-v6-preprod-content-report.decision-run.json'); d=json.loads(p.read_text(encoding='utf-8')); cs=[x for x in d['school_claims'] if x['domain'] in ('事业','总体')]; b={'case_id':case,'career_claim_count':len(cs),'career_school_count':len({x['school'] for x in cs}),'career_evidence_count':sum(len(x['evidence_refs']) for x in cs),'career_fifteen_layer_count':15,'required_text_sentinels':['事业','依据','置信度','应期']}; assert min(b['career_claim_count'],b['career_school_count'],b['career_evidence_count'])>0,b; out=pathlib.Path('tests/r10/fixtures/r6_ziping_career_baseline.json'); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(b,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(json.dumps(b,ensure_ascii=False))"
```

Expected: 第一条命令 exit code `0`；第二条命令输出三项实测计数均大于 `0` 的 JSON，并原样创建 `tests/r10/fixtures/r6_ziping_career_baseline.json`。`career_fifteen_layer_count` 固定为契约值 `15`；命令中的断言阻止空产物被录为基线。

- [ ] **Step 5: 运行测试，确认 GREEN**

Run: `python -m pytest tests/r10/test_r10_ziping_career_acceptance.py::test_r6_baseline_is_frozen_and_nonempty -q`

Expected: `1 passed`。

- [ ] **Step 6: 提交**

```cmd
git add tests/r10/fixtures/r6_ziping_career_baseline.json tests/r10/test_r10_ziping_career_acceptance.py
git commit -m "test: freeze R6 ziping career information baseline"
```

---

### Task 2: 定义 L2 无损边界，锁死旺衰/用神/做功路径

**Files:**
- Create: `engine/decision/l2_v5_claims.py`
- Create: `tests/r10/test_r10_ziping_career_l2.py`

**Interfaces:**
- Consumes: `to_school_claim(claim: V5Claim, role: SchoolRole) -> SchoolClaim`。
- Produces: 字段无损映射；`metadata` 是深拷贝，额外的 `v5_payload` 仅保存来源已有的 `stance`、`polarity`、`counter_evidence`、`timing_hints`、`probabilistic`，不得生成命理内容。

- [ ] **Step 1: 写失败测试，用合成 claim 同时携带三条路径**

```python
# tests/r10/test_r10_ziping_career_l2.py
from __future__ import annotations

from engine.decision.l2_v5_claims import to_school_claim
from engine.v5.domain import V5Claim, V5Confidence, V5Evidence


def test_to_school_claim_preserves_v5_reasoning_paths_exactly() -> None:
    paths = {
        "wangshuai_path": {"strength": "偏弱", "score": 0.34},
        "yongshen_path": {"pattern": "七杀格", "yongshen": "正印"},
        "zuogong_path": {"source": "官杀", "target": "印", "mode": "杀印相生"},
    }
    source = V5Claim(
        claim_id="v5cl-career-1",
        school="ziping",
        domain="事业",
        claim="七杀格以印化杀，事业取组织平台路径。",
        claim_type="structure_claim",
        confidence=V5Confidence(tier="★★★★", score=0.71, note="source-note"),
        evidence=[V5Evidence(evidence_id="ev-1", source="ziping", text="source evidence")],
        falsifiable="现实事业长期不呈组织平台路径则降权。",
        metadata={"reasoning_paths": paths, "geju_type": "正格"},
    )

    actual = to_school_claim(source, "lead")

    assert actual.claim_id == source.claim_id
    assert actual.role_granted_by_l1 == "lead"
    assert actual.statement == source.claim
    assert actual.evidence_refs == ["ev-1"]
    assert actual.confidence == 0.71
    assert actual.falsifier == source.falsifiable
    assert actual.metadata["reasoning_paths"] == paths
    assert actual.metadata["v5_payload"]["stance"] == source.stance
```

- [ ] **Step 2: 运行测试，确认 RED**

Run: `python -m pytest tests/r10/test_r10_ziping_career_l2.py::test_to_school_claim_preserves_v5_reasoning_paths_exactly -q`

Expected: collection error，包含 `ModuleNotFoundError: No module named 'engine.decision.l2_v5_claims'`。

- [ ] **Step 3: 写最小实现，只映射、不判断**

```python
# engine/decision/l2_v5_claims.py
"""V5 runner claim 到 L2 SchoolClaim 的无损边界。"""

from __future__ import annotations

from copy import deepcopy

from engine.decision.models import SchoolClaim, SchoolRole
from engine.v5.domain import V5Claim


def to_school_claim(claim: V5Claim, role: SchoolRole) -> SchoolClaim:
    """只复制来源字段与 L1 授权；不得在此产生命理判断。"""
    metadata = deepcopy(claim.metadata)
    metadata["v5_payload"] = {
        "stance": claim.stance,
        "polarity": claim.polarity,
        "counter_evidence": [item.to_dict() for item in claim.counter_evidence],
        "timing_hints": deepcopy(claim.timing_hints),
        "probabilistic": claim.probabilistic,
    }
    return SchoolClaim(
        claim_id=claim.claim_id,
        school=claim.school,
        role_granted_by_l1=role,
        domain=claim.domain,
        claim_type=claim.claim_type,
        statement=claim.claim,
        evidence_refs=[item.evidence_id for item in claim.evidence],
        confidence=min(1.0, max(0.0, claim.confidence.score)),
        falsifier=claim.falsifiable,
        dependencies=[f"v5:{claim.claim_id}"],
        metadata=metadata,
    )
```

- [ ] **Step 4: 运行测试，确认 GREEN**

Run: `python -m pytest tests/r10/test_r10_ziping_career_l2.py::test_to_school_claim_preserves_v5_reasoning_paths_exactly -q`

Expected: `1 passed`。

- [ ] **Step 5: 增加“来源缺失时不得发明”失败测试**

```python
def test_to_school_claim_does_not_invent_missing_reasoning_paths() -> None:
    source = V5Claim(
        claim_id="v5cl-career-empty",
        school="ziping",
        domain="事业",
        claim="来源只给出一条结构命题。",
        claim_type="structure_claim",
        confidence=V5Confidence(score=0.6),
        metadata={},
    )

    actual = to_school_claim(source, "co_lead")

    assert "reasoning_paths" not in actual.metadata
    assert "wangshuai_path" not in actual.metadata
    assert "yongshen_path" not in actual.metadata
    assert "zuogong_path" not in actual.metadata
```

- [ ] **Step 6: 运行两条 L2 测试**

Run: `python -m pytest tests/r10/test_r10_ziping_career_l2.py -q`

Expected: `2 passed`。

- [ ] **Step 7: 提交**

```cmd
git add engine/decision/l2_v5_claims.py tests/r10/test_r10_ziping_career_l2.py
git commit -m "feat: add lossless v5 claim to L2 boundary"
```

---

### Task 3: 让子平·事业域 runner 直接供应 L2 claim

**Files:**
- Modify: `engine/decision/l2_v5_claims.py`
- Modify: `tests/r10/test_r10_ziping_career_l2.py`

**Interfaces:**
- Consumes: `build_ziping_career_claims(chart: dict[str, object], case_id: str, applicability: list[SchoolApplicability]) -> list[SchoolClaim]`。
- Produces: `ziping` 的 `总体 + 事业` L2 claims；角色严格取自 L1，`abstain` 返回空。

- [ ] **Step 1: 写失败测试，证明角色来自 L1 且保留总体结构依赖**

```python
from engine.decision.l2_v5_claims import build_ziping_career_claims
from engine.decision.models import SchoolApplicability

CHART = {
    "case_id": "C-R10-ZIPING",
    "pillars": {"year": "庚申", "month": "戊寅", "day": "壬子", "hour": "辛丑"},
    "current_dayun": "壬午",
    "current_year": "丙午（2026 年）",
}


def test_build_ziping_career_claims_uses_l1_role_and_keeps_global_context() -> None:
    applicability = [SchoolApplicability(
        school="ziping",
        role="lead",
        applicable_domains=["事业"],
        applicability_score=0.9,
        confidence=0.9,
    )]

    claims = build_ziping_career_claims(CHART, "C-R10-ZIPING", applicability)

    assert claims
    assert {claim.school for claim in claims} == {"ziping"}
    assert {claim.domain for claim in claims} == {"总体", "事业"}
    assert {claim.role_granted_by_l1 for claim in claims} == {"lead"}
    assert any("旺衰" in claim.statement for claim in claims)
    assert any("用神=" in claim.statement for claim in claims)
    assert all(claim.metadata["source_scope"] == "ziping_independent_runner" for claim in claims)
```

- [ ] **Step 2: 运行测试，确认 RED**

Run: `python -m pytest tests/r10/test_r10_ziping_career_l2.py::test_build_ziping_career_claims_uses_l1_role_and_keeps_global_context -q`

Expected: `FAILED`，包含 `ImportError: cannot import name 'build_ziping_career_claims'`。

- [ ] **Step 3: 写最小实现**

```python
# 追加到 engine/decision/l2_v5_claims.py
from engine.decision.models import SchoolApplicability
from engine.v5.ziping_runner import run_ziping_independent


def build_ziping_career_claims(
    chart: dict[str, object],
    case_id: str,
    applicability: list[SchoolApplicability],
) -> list[SchoolClaim]:
    role = next((item.role for item in applicability if item.school == "ziping"), "abstain")
    if role == "abstain":
        return []
    source_claims = run_ziping_independent(chart, case_id)
    return [
        to_school_claim(claim, role)
        for claim in source_claims
        if claim.school == "ziping" and claim.domain in {"总体", "事业"}
    ]
```

- [ ] **Step 4: 增加 abstain 门禁测试**

```python
def test_build_ziping_career_claims_emits_nothing_when_l1_abstains() -> None:
    applicability = [SchoolApplicability(school="ziping", role="abstain")]
    assert build_ziping_career_claims(CHART, "C-R10-ZIPING", applicability) == []
```

- [ ] **Step 5: 运行 L2 文件，确认 GREEN**

Run: `python -m pytest tests/r10/test_r10_ziping_career_l2.py -q`

Expected: `4 passed`。

- [ ] **Step 6: 提交**

```cmd
git add engine/decision/l2_v5_claims.py tests/r10/test_r10_ziping_career_l2.py
git commit -m "feat: feed ziping career claims directly into L2"
```

---

### Task 4: 把格局一致性审查归位 L3，且只消费 L2

**Files:**
- Modify: `engine/decision/l3_structure.py`
- Modify: `engine/decision/v5_adapter.py`
- Create: `tests/r10/test_r10_ziping_career_layers.py`

**Interfaces:**
- Produces: `extract_geju_profile(claims) -> dict[str, object] | None` 与既有 `build_structural_verdicts(case_id, claims)`。
- Compatibility: adapter 的 `_extract_geju_profile`、`_verdicts` 改为薄委托，旧调用方暂不破坏；判断实现只存在 L3。

- [ ] **Step 1: 写失败测试，证明 L3 消费用忌方向**

```python
# tests/r10/test_r10_ziping_career_layers.py
from __future__ import annotations

from engine.decision.l3_structure import build_structural_verdicts
from engine.decision.models import SchoolClaim


def _claim(claim_id: str, statement: str, metadata: dict | None = None) -> SchoolClaim:
    return SchoolClaim(
        claim_id=claim_id,
        school="ziping",
        role_granted_by_l1="lead",
        domain="事业",
        claim_type="structure_claim",
        statement=statement,
        confidence=0.6,
        metadata=metadata or {},
    )


def test_l3_consumes_geju_direction_from_l2_without_recomputing_it() -> None:
    claims = [
        _claim("profile", "格局大类裁决：正格", {
            "geju_type": "正格",
            "favor_shishen": ["食神"],
            "avoid_shishen": ["正印"],
        }),
        _claim("bad", "正印当权主事业上升"),
    ]

    verdicts = {item.claim_id: item for item in build_structural_verdicts("C-R10", claims)}

    assert verdicts["bad"].verdict == "weaken"
    assert "正印" in verdicts["bad"].structural_reason
    assert "正格" in verdicts["bad"].structural_reason
```

- [ ] **Step 2: 运行测试，确认 RED**

Run: `python -m pytest tests/r10/test_r10_ziping_career_layers.py::test_l3_consumes_geju_direction_from_l2_without_recomputing_it -q`

Expected: `FAILED`，实际 verdict/reason 不包含格局用忌审查。

- [ ] **Step 3: 将 adapter 中现有 `_extract_geju_profile`、`_shishen_in_statement`、`_verdicts` 逻辑机械迁入 L3**

执行规则：

```text
1. claim_type 同时接受 "structure" 与 "structure_claim"。
2. profile 只能从 claim.metadata.geju_type/favor_shishen/avoid_shishen 读取。
3. metadata 无 profile 时保持原 L3 行为，禁止调用 ziping_runner 或任何命理规则。
4. event/timing/evidence 以及 *_claim 变体继续返回 unknown 或现有兼容结果。
5. verdict_id 仍使用 L3 自己的 _stable_id。
```

最小核心分支必须是：

```python
profile = extract_geju_profile(claims)
for claim in claims:
    if claim.claim_type in {"structure", "structure_claim"}:
        verdict = "pass" if claim.confidence >= 0.4 else "weaken"
    elif claim.claim_type in {"event", "event_claim"}:
        verdict = "weaken"
    else:
        verdict = "unknown"
    structural_reason = "L3 只消费 L2 已登记的结构基础。"
    if claim.confidence <= 0.1:
        verdict = "reject"
    if profile and verdict in {"pass", "weaken"}:
        shishen = shishen_in_statement(claim.statement)
        hits_avoid = shishen & profile["avoid"]
        hits_favor = shishen & profile["favor"]
        if hits_avoid and not hits_favor:
            verdict = "weaken" if verdict == "pass" else verdict
            structural_reason = (
                f"命题依赖格局忌神 {sorted(hits_avoid)}"
                f"（{profile['geju_type']}），与用神方向不一致，降级。"
            )
```

- [ ] **Step 4: 写“不得发明”测试**

```python
def test_l3_without_l2_geju_metadata_does_not_invent_favor_or_avoid() -> None:
    claim = _claim("plain", "正印当权主事业上升", {})

    verdict = build_structural_verdicts("C-R10", [claim])[0]

    assert verdict.verdict == "pass"
    assert "忌神" not in verdict.structural_reason
    assert "用神" not in verdict.structural_reason
```

- [ ] **Step 5: 把 adapter helper 改成薄委托并跑旧 R9 测试**

`engine/decision/v5_adapter.py` 只保留兼容名字：

```python
from engine.decision.l3_structure import (
    build_structural_verdicts,
    extract_geju_profile,
)

_extract_geju_profile = extract_geju_profile


def _verdicts(case_id: str, claims: list[SchoolClaim]) -> list[StructuralVerdict]:
    return build_structural_verdicts(case_id, claims)
```

Run: `python -m pytest tests/r10/test_r10_ziping_career_layers.py tests/test_l3_geju_review.py -q`

Expected: 全部通过；旧 R9 测试不得删除或放宽。

- [ ] **Step 6: 提交**

```cmd
git add engine/decision/l3_structure.py engine/decision/v5_adapter.py tests/r10/test_r10_ziping_career_layers.py
git commit -m "refactor: move geju consistency review into L3"
```

---

### Task 5: 把事件类型归位 L4，且不得凭结构 claim 造事件

**Files:**
- Modify: `engine/decision/l4_events.py`
- Modify: `engine/decision/v5_adapter.py`
- Modify: `tests/r10/test_r10_ziping_career_layers.py`

**Interfaces:**
- Produces: `classify_event_type(event_label: str, domain: str) -> str`；`build_event_hypotheses()` 对 `event` / `event_claim` 兼容。
- Constraint: L4 只分类已有 event claim；目标切片没有 event claim 时返回空，不使用 fallback 编造正式事件。

- [ ] **Step 1: 写失败测试，要求 career event 由 L4 分类并绑定通过的 L3**

```python
from engine.decision.l4_events import build_event_hypotheses
from engine.decision.models import StructuralVerdict


def test_l4_classifies_existing_career_event_and_binds_l3_verdict() -> None:
    claim = SchoolClaim(
        claim_id="career-event",
        school="duan_jianye",
        role_granted_by_l1="co_lead",
        domain="事业",
        claim_type="event_claim",
        statement="组织内有升职与职级提升机会",
        confidence=0.72,
    )
    verdict = StructuralVerdict(
        verdict_id="verdict-career-event",
        claim_id=claim.claim_id,
        verdict="weaken",
        structural_reason="消费 L2 结构方向后保留。",
        confidence=0.5,
    )

    events = build_event_hypotheses("C-R10", [verdict], [claim])

    assert len(events) == 1
    assert events[0].event_type == "升迁"
    assert events[0].source_verdict_ids == [verdict.verdict_id]
    assert events[0].concrete_event == claim.statement
```

- [ ] **Step 2: 运行测试，确认 RED**

Run: `python -m pytest tests/r10/test_r10_ziping_career_layers.py::test_l4_classifies_existing_career_event_and_binds_l3_verdict -q`

Expected: `FAILED`，当前实现不接受 `event_claim` 或返回通用事件类型。

- [ ] **Step 3: 将关键词映射与 `classify_event_type()` 从 adapter 机械迁入 L4**

最小循环改为：

```python
event_claims = [
    item for item in claims
    if item.claim_type in {"event", "event_claim"}
    and item.role_granted_by_l1 != "evidence_only"
]
# 每个已获 pass/weaken 支撑的 event claim：
event_type = classify_event_type(claim.statement, claim.domain)
```

`classify_event_type()` 必须只做字符串→事件标签映射；不得导入 `engine.v5.ziping_runner`、理论规则库或 adapter。

- [ ] **Step 4: 写“不得发明事件”测试并删除正式路径 fallback**

```python
def test_l4_does_not_invent_event_from_structure_claim_only() -> None:
    claim = _claim("structure-only", "七杀格，用神正印")
    verdict = StructuralVerdict(
        verdict_id="verdict-structure-only",
        claim_id=claim.claim_id,
        verdict="pass",
        structural_reason="结构通过",
        confidence=0.6,
    )

    assert build_event_hypotheses("C-R10", [verdict], [claim]) == []
```

- [ ] **Step 5: adapter 改为 L4 兼容委托并跑 R8 回归**

```python
from engine.decision.l4_events import classify_event_type
```

删除 adapter 内 `_EVENT_TYPE_KEYWORDS`、`_DOMAIN_GENERIC_EVENT` 与函数实现；保留 import 后旧引用继续可用。

Run: `python -m pytest tests/r10/test_r10_ziping_career_layers.py tests/test_l4_event_type.py -q`

Expected: 全部通过；断言结构-only 不产出事件。

- [ ] **Step 6: 提交**

```cmd
git add engine/decision/l4_events.py engine/decision/v5_adapter.py tests/r10/test_r10_ziping_career_layers.py
git commit -m "refactor: move event classification into L4"
```

---

### Task 6: 装配 R10 纵切片，证明目标域不调用 adapter 判断

**Files:**
- Create: `engine/decision/r10_ziping_career.py`
- Modify: `tests/r10/test_r10_ziping_career_acceptance.py`

**Interfaces:**
- Produces: `apply_ziping_career_slice(output: V5Output, applicability: list[SchoolApplicability]) -> tuple[list[SchoolClaim], list[StructuralVerdict], list[EventHypothesis]]`。
- Boundary: 返回完整 L2-L4 集合，但只有 `ziping × {总体,事业}` 被替换为 runner→L2 原生路径；adapter 只接收已剔除该目标集合的 `V5Output`，以保留未迁移流派/领域。

- [ ] **Step 1: 写失败测试，证明 adapter 从未看见目标 claims**

```python
from unittest.mock import patch

from engine.decision import v5_adapter
from engine.decision.l1_school_router import route_schools
from engine.decision.models import ChartFactLedger, ContextFactLedger
from engine.decision.r10_ziping_career import apply_ziping_career_slice
from engine.v5.runner import run_v5

CHART = {
    "case_id": "C-R10-ZIPING",
    "pillars": {"year": "庚申", "month": "戊寅", "day": "壬子", "hour": "辛丑"},
    "current_dayun": "壬午",
    "current_year": "丙午（2026 年）",
}


def test_ziping_career_slice_never_sends_target_claims_to_adapter() -> None:
    output = run_v5(CHART, case_id="C-R10-ZIPING")
    ledger = ChartFactLedger(
        four_pillars=CHART["pillars"],
        dayun_steps=[{"ganzhi": "壬午"}],
    )
    applicability = route_schools(ledger, ContextFactLedger(analysis_focus_text="事业"))

    with patch("engine.decision.v5_adapter._claims", wraps=v5_adapter._claims) as legacy_claims:
        claims, verdicts, events = apply_ziping_career_slice(output, applicability)

    adapter_output = legacy_claims.call_args.args[0]
    assert not any(
        claim.school == "ziping" and claim.domain in {"总体", "事业"}
        for claim in adapter_output.claims
    )
    role = next(item.role for item in applicability if item.school == "ziping")
    native_ids = {
        claim.claim_id for claim in output.claims
        if claim.school == "ziping" and claim.domain in {"总体", "事业"}
    }
    native_l2 = [claim for claim in claims if claim.claim_id in native_ids]
    assert native_l2
    assert {item.role_granted_by_l1 for item in native_l2} == {role}
    assert {item.claim_id for item in verdicts} == {item.claim_id for item in claims}
    assert all(item.domain == "事业" for item in events)
```

- [ ] **Step 2: 运行测试，确认 RED**

Run: `python -m pytest tests/r10/test_r10_ziping_career_acceptance.py::test_ziping_career_slice_never_sends_target_claims_to_adapter -q`

Expected: collection error，包含 `ModuleNotFoundError: No module named 'engine.decision.r10_ziping_career'`。

- [ ] **Step 3: 写最小装配实现**

```python
# engine/decision/r10_ziping_career.py
"""R10 第一证明物：子平·事业域 L2-L4 原生纵切片。"""

from __future__ import annotations

from dataclasses import replace

from engine.decision import v5_adapter
from engine.decision.l2_v5_claims import to_school_claim
from engine.decision.l3_structure import build_structural_verdicts
from engine.decision.l4_events import build_event_hypotheses
from engine.decision.models import (
    EventHypothesis,
    SchoolApplicability,
    SchoolClaim,
    StructuralVerdict,
)
from engine.v5.domain import V5Output


def apply_ziping_career_slice(
    output: V5Output,
    applicability: list[SchoolApplicability],
) -> tuple[list[SchoolClaim], list[StructuralVerdict], list[EventHypothesis]]:
    roles = {item.school: item.role for item in applicability}
    target_v5 = [
        claim for claim in output.claims
        if claim.school == "ziping" and claim.domain in {"总体", "事业"}
    ]
    legacy_output = replace(
        output,
        claims=[claim for claim in output.claims if claim not in target_v5],
    )
    legacy_l2 = v5_adapter._claims(legacy_output, applicability)
    native_l2 = [
        to_school_claim(claim, roles["ziping"])
        for claim in target_v5
        if roles.get("ziping", "abstain") != "abstain"
    ]
    claims = legacy_l2 + native_l2
    verdicts = build_structural_verdicts(output.case_id, claims)
    events = build_event_hypotheses(output.case_id, verdicts, claims)
    return claims, verdicts, events
```

说明：adapter 只处理已剔除 `ziping × {总体,事业}` 的非目标 claims；目标集合直接由 runner `V5Claim` 进入 `to_school_claim()`。L3/L4 对完整 L2 集合链内运行，保证五派依据不因纵切片丢失。

- [ ] **Step 4: 运行隔离测试，确认 GREEN**

Run: `python -m pytest tests/r10/test_r10_ziping_career_acceptance.py::test_ziping_career_slice_never_sends_target_claims_to_adapter -q`

Expected: `1 passed`。

- [ ] **Step 5: 提交**

```cmd
git add engine/decision/r10_ziping_career.py tests/r10/test_r10_ziping_career_acceptance.py
git commit -m "feat: assemble native ziping career L2-L4 slice"
```

---

### Task 7: 接入唯一 DecisionRun，验证 trace 与报告一致性

**Files:**
- Modify: `engine/decision/r10_ziping_career.py`
- Modify: `engine/v5/preprod.py`
- Test: `tests/r10/test_r10_ziping_career_acceptance.py`

**Interfaces:**
- Produces: `build_ziping_career_decision_run(output: V5Output, raw_text: str = "") -> DecisionRun`。
- Rendering: `render_report_v6` 的事业域继续只读该 run 的 L7 `ReportViewItem`；不得另算事业结论。

- [ ] **Step 1: 写失败测试，要求完整 trace 为空**

```python
from engine.decision.r10_ziping_career import build_ziping_career_decision_run


def test_ziping_career_decision_run_has_complete_trace() -> None:
    output = run_v5(CHART, case_id="C-R10-ZIPING")
    run = build_ziping_career_decision_run(output)

    assert run.validate_trace() == []
    assert any(item.domain == "事业" for item in run.school_claims)
    assert any(item.domain == "事业" for item in run.report_items)
```

- [ ] **Step 2: 运行测试，确认 RED**

Run: `python -m pytest tests/r10/test_r10_ziping_career_acceptance.py::test_ziping_career_decision_run_has_complete_trace -q`

Expected: `FAILED`，包含缺少 `build_ziping_career_decision_run`。

- [ ] **Step 3: 写最小完整装配，复用现有 L5-L9 builder**

实现顺序必须逐层调用：

```text
_chart/input ledger（纯 DTO 映射）
→ route_schools
→ apply_ziping_career_slice
→ build_timing_probabilities
→ build_arbitration_decisions
→ build_report_items
→ build_feedback_signals / build_feedback_attributions
→ build_calibration_actions / build_router_calibration_actions
→ DecisionRun
```

禁止让目标 `ziping × {总体,事业}` claims 进入：

```text
v5_adapter._claims
v5_adapter._verdicts
v5_adapter._events
```

`v5_adapter._claims` 仅允许消费已剔除目标集合的 `legacy_output`；L3/L4 必须直接调用 `build_structural_verdicts()` / `build_event_hypotheses()`。允许临时复用的仅是无判断 DTO 转换；若复用 `_chart_to_ledger`，必须在函数旁添加 `ponytail:` 债务注释，明确它不参与 L1-L4 判断，并在后续 R10 全迁移时删除。

- [ ] **Step 4: 运行 trace 测试，修到 GREEN**

Run: `python -m pytest tests/r10/test_r10_ziping_career_acceptance.py::test_ziping_career_decision_run_has_complete_trace -q`

Expected: `1 passed` 且 `validate_trace()` 精确等于 `[]`；不得过滤或忽略 issues。

- [ ] **Step 5: 写报告/JSON 同源失败测试**

```python
def test_career_report_text_is_the_same_l7_text_serialized_to_decision_run() -> None:
    output = run_v5(CHART, case_id="C-R10-ZIPING")
    run = build_ziping_career_decision_run(output)
    serialized = run.to_dict()

    career_items = [item for item in run.report_items if "事业" in item.display_text]
    serialized_items = {
        item["report_item_id"]: item["display_text"]
        for item in serialized["report_items"]
    }

    assert career_items
    for item in career_items:
        assert serialized_items[item.report_item_id] == item.display_text
```

保持 `tools/render_report_v6.py` 的 CLI 包装不变；在 `engine/v5/preprod.py::render_v6_preprod_case()` 中把 `decision_run` 的构造改为 `build_ziping_career_decision_run(output, raw_text=input_text)`，并继续把 `decision_run.report_items` 与 `decision_run.arbitration_decisions` 原样传给 `render_report_v6_from_output()`。不得在渲染器中增加第二套事业域计算。

- [ ] **Step 6: 跑完整验收文件**

Run: `python -m pytest tests/r10/test_r10_ziping_career_acceptance.py -q`

Expected: 全部通过；输出中无 `xfailed`、`skipped`。

- [ ] **Step 7: 提交**

```cmd
git add engine/decision/r10_ziping_career.py engine/v5/preprod.py tests/r10/test_r10_ziping_career_acceptance.py
git commit -m "feat: drive career report from native R10 decision run"
```

---

### Task 8: 锁死两条 falsifier 与 R6 信息量下限

**Files:**
- Modify: `tests/r10/test_r10_ziping_career_acceptance.py`

**Interfaces:**
- Consumes: `load_r6_baseline()` 与 `build_ziping_career_decision_run()`。
- Produces: 任一信息损失立即失败的最终 gate；禁止自动更新快照。

- [ ] **Step 1: 写路径完整性测试**

```python
def test_falsifier_l2_keeps_real_runner_wangshuai_yongshen_and_source_metadata() -> None:
    output = run_v5(CHART, case_id="C-R10-ZIPING")
    run = build_ziping_career_decision_run(output)
    ziping_claims = [item for item in run.school_claims if item.school == "ziping"]

    assert any("旺衰" in item.statement for item in ziping_claims)
    assert any("用神=" in item.statement for item in ziping_claims)
    assert all(item.metadata.get("source_scope") == "ziping_independent_runner" for item in ziping_claims)
    assert any(item.metadata.get("geju_type") for item in ziping_claims)
    assert any("yao_favor_shishen" in item.metadata for item in ziping_claims)
```

说明：真实子平 runner 当前没有独立 `zuogong_path` 字段，因此这里不得要求系统凭空产生；Task 2 的合成无损测试负责证明“来源一旦有做功路径，L2 原样保留”。

- [ ] **Step 2: 写信息量下限测试**

```python
def test_falsifier_career_information_is_not_thinner_than_r6() -> None:
    baseline = load_r6_baseline()
    output = run_v5(CHART, case_id="C-R10-ZIPING")
    run = build_ziping_career_decision_run(output)
    claims = [item for item in run.school_claims if item.domain in {"总体", "事业"}]
    career_text = "\n".join(item.display_text for item in run.report_items if "事业" in item.display_text)

    assert len(claims) >= int(baseline["career_claim_count"])
    assert len({item.school for item in claims}) >= int(baseline["career_school_count"])
    assert sum(len(item.evidence_refs) for item in claims) >= int(baseline["career_evidence_count"])
    for sentinel in baseline["required_text_sentinels"]:
        assert str(sentinel) in career_text
```

- [ ] **Step 3: 写 15 层硬门禁测试**

在 `tests/r10/test_r10_ziping_career_acceptance.py` 顶部增加 `import re`，再加入完整测试：

```python
def test_falsifier_report_keeps_all_fifteen_judgment_layers(tmp_path: Path) -> None:
    from engine.v5.preprod import render_v6_preprod_case

    baseline = load_r6_baseline()
    report_path, _ = render_v6_preprod_case(
        "cases/C-2026-035-乾-戊辰癸亥甲戌庚午/input.md",
        reports_dir=tmp_path,
        workspace_root=".",
    )
    report_text = Path(report_path).read_text(encoding="utf-8")
    template_text = Path("templates/report-v6.md").read_text(encoding="utf-8")
    row_pattern = re.compile(r"^\|\s*(\d{1,2})\s*\|", re.MULTILINE)
    template_layers = [int(value) for value in row_pattern.findall(template_text)]
    report_layers = [int(value) for value in row_pattern.findall(report_text)]

    assert template_layers == list(range(1, 16))
    assert report_layers == template_layers
    assert len(report_layers) == int(baseline["career_fifteen_layer_count"])
```

Run: `python -m pytest tests/r10/test_r10_ziping_career_acceptance.py::test_falsifier_report_keeps_all_fifteen_judgment_layers -q`

Expected: `1 passed`；若模板或报告缺任一层，连续列表断言明确失败。只在测试内计数，不在生产代码新建“15 层计数服务”。

- [ ] **Step 4: 跑 R10 全套测试**

Run: `python -m pytest tests/r10 -q`

Expected: 全部通过；两条 falsifier 均实际执行，无 skip。

- [ ] **Step 5: 跑 R8/R9 与报告回归**

Run:

```cmd
python -m pytest tests/test_l3_geju_review.py tests/test_l4_event_type.py tests/v5/test_report_reads_l7.py tests/v5/test_render_report_v6.py -q
```

Expected: 全部通过，证明判断归位没有破坏旧桥兼容与 L7 报告读取。

- [ ] **Step 6: 跑正式 case，检查四条断言**

Run:

```cmd
python tools/render_report_v6.py cases/C-2026-035-乾-戊辰癸亥甲戌庚午/input.md --output-dir reports
python -c "import json,pathlib; p=pathlib.Path('reports/C-2026-035-乾-戊辰癸亥甲戌庚午-v6-preprod-content-report.decision-run.json'); d=json.loads(p.read_text(encoding='utf-8')); print({'claims':len(d['school_claims']),'verdicts':len(d['structural_verdicts']),'events':len(d['event_hypotheses']),'report_items':len(d['report_items'])})"
```

Expected: 两条命令 exit code `0`；四项计数均非负，事业域报告存在，`tests/r10` 已证明 trace 为空与信息量达标。

- [ ] **Step 7: 提交**

```cmd
git add tests/r10/test_r10_ziping_career_acceptance.py
git commit -m "test: lock R10 ziping career falsifiers"
```

---

### Task 9: 最终回归与状态文档

**Files:**
- Modify: `HANDOFF.md`

**Interfaces:**
- Produces: 只把“R10 第一纵切片已证明”写入 §3/§4/§5；R10 全量迁移、adapter 删除、默认入口切换仍保持待办。

- [ ] **Step 1: 先跑完整相关测试，禁止先改状态**

Run:

```cmd
python -m pytest tests/r10 tests/test_l3_geju_review.py tests/test_l4_event_type.py tests/test_l1_structural_signals.py tests/test_l1_learned_prior.py tests/test_l9_router_calibration.py tests/test_accuracy_report.py tests/v5/test_report_reads_l7.py tests/v5/test_render_report_v6.py -q
```

Expected: exit code `0`；无 failed/error。

- [ ] **Step 2: 更新 HANDOFF §3/§4/§5，使用精确措辞**

必须写明：

```text
- 已完成：R10 第一证明物（ziping × 事业）原生 L2-L4 纵切片。
- 已证明：目标切片不调用 adapter 的 L2 反推/L3/L4 判断；validate_trace 为空；报告与 JSON 同源；信息量不低于冻结的 R6 基线。
- 未完成：其余流派/领域迁移、v5_adapter 全量删除、生产默认入口切换。
- K 系列仍不与 R10 配管混做；L3/L4 当前只消费来源命理，不发明新命理。
```

- [ ] **Step 3: 检查 adapter 禁止项没有回流**

Run:

```cmd
python -c "import pathlib; p=pathlib.Path('engine/decision/r10_ziping_career.py').read_text(encoding='utf-8'); banned=['_claims(', '_verdicts(', '_events(', '_extract_geju_profile(', 'classify_event_type(']; found=[x for x in banned if x in p]; print(found); raise SystemExit(1 if found else 0)"
```

Expected: 输出 `[]`，exit code `0`。

- [ ] **Step 4: 最终提交**

```cmd
git add HANDOFF.md
git commit -m "docs: record R10 ziping career proof slice"
```

## Final Acceptance Checklist

- [ ] `ziping × 事业` 的 L2 claims 直接来自 runner `V5Claim`，不是从报告、仲裁结果或预测账本反拆。
- [ ] L1 role 与 `route_schools()` 结果逐项相等；abstain 不发言。
- [ ] L3 实现位于 `l3_structure.py`，只读 L2 metadata；metadata 缺失时不猜用忌。
- [ ] L4 实现位于 `l4_events.py`，只分类已有 event claim；structure-only 不造事件。
- [ ] adapter 的旧 helper 仅做兼容委托，不再拥有判断实现。
- [ ] `DecisionRun.validate_trace()` 精确返回 `[]`。
- [ ] 报告事业域文本与 `DecisionRun.to_dict()["report_items"]` 同源逐字一致。
- [ ] 五派依据、claim/evidence 数量和 15 层判断不低于冻结的 R6 基线。
- [ ] 合成 claim 的旺衰/用神/做功路径在 L2 深相等；真实 runner 缺少做功字段时不发明。
- [ ] §R10.6 任一 falsifier 触发都会使测试失败，而不是更新快照通过。
- [ ] 未迁移其他流派/领域，未删除整个 adapter，未切生产默认入口，未启动 K1/K2/K3。

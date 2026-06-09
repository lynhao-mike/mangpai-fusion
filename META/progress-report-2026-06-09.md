---

# 多流派并行功能域系统进度报告
> 生成时间：2026-06-09T12:53:37+08:00
> 报告范围：Phase 1-6 执行状态

---

## 1. 系统版本与里程碑

| 版本 | 状态 | 说明 |
|---|---|---|
| 1.3.0 / V1_quantifiable | landed | v1.4_status 条目 |
| 1.3.0 / V2_domain_restriction | landed | v1.4_status 条目 |
| 1.3.0 / V3_ingest_skip_strategy | landed | v1.4_status 条目 |
| 1.3.0 / V4_event_type_hypotheses | landed | v1.4_status 条目 |
| 1.3.0 / V5_industry_path | landed | v1.4_status 条目 |
| 1.3.0 / V6_wealth_framework | landed | v1.4_status 条目 |
| 1.3.0 / V8_cross_domain_backfill | landed | v1.4_status 条目 |
| 1.3.0 / V9_ziping_ditiansui_production_rules | landed | v1.4_status 条目 |
| 1.3.0 / parallel_domain_models | landed | v1.5_status 条目 |
| 1.3.0 / parallel_domain_orchestrator | landed_minimal | v1.5_status 条目 |
| 1.3.0 / pipeline_parallel_analysis_attachment | landed | v1.5_status 条目 |
| 1.3.0 / parallel_domain_report_section | landed | v1.5_status 条目 |
| 1.3.0 / parallel_domain_statement_index | landed | v1.5_status 条目 |

当前里程碑汇总：
- ✅ 已落地 (landed)：V1_quantifiable, V2_domain_restriction, V3_ingest_skip_strategy, V4_event_type_hypotheses, V5_industry_path, V6_wealth_framework, V8_cross_domain_backfill, V9_ziping_ditiansui_production_rules, parallel_domain_models, pipeline_parallel_analysis_attachment, parallel_domain_report_section, parallel_domain_statement_index
- 🔄 最小落地 (landed_minimal)：parallel_domain_orchestrator
- ⏳ 进行中 (in_progress)：未显式标记
- ❌ 待启动 (pending)：未显式标记
- 🚫 阻塞 (blocked)：未显式标记
- Last updated timestamp：2026-06-06
- 补充状态文件：META/changelog.md = MISSING；META/architecture-decisions.md = MISSING

---

## 2. 理论规则层状态

| 流派 | 候选规则数 | 生产 active 数 | 覆盖源文件 | 台账状态 |
|---|---:|---:|---|---|
| 子平格局派 | 57 | 57 | theory/raw/yaml/ziping_candidate_rules_2026-06-05.yaml | EXISTS；台账标注生产 active 截至 2026-06-08 为 57 条 |
| 滴天髓调候派 | 255 | 255 | theory/raw/yaml/tiaohou_ditiansui_candidate_rules_2026-06-05.yaml | EXISTS；台账标注生产 active 截至 2026-06-08 为 255 条 |

逐文件计数：

| file_path | total_count | active_count | review_draft_count |
|---|---:|---:|---:|
| theory/ziping/index.yaml | 57 | 57 | 0 |
| theory/tiaohou_ditiansui/index.yaml | 255 | 255 | 0 |
| theory/raw/yaml/ziping_candidate_rules_2026-06-05.yaml | 57 | 0 | 0 |
| theory/raw/yaml/tiaohou_ditiansui_candidate_rules_2026-06-05.yaml | 255 | 0 | 0 |

⚠️ 台账与生产层差异说明：台账文件本身为“审查态台账”，明确说明不被引擎加载，生产事实源仍是 `theory/ziping/index.yaml` 与 `theory/tiaohou_ditiansui/index.yaml`。候选 YAML 顶层 status 为 `review_draft`，但规则条目为 `candidate`，因此按条目口径 review_draft_count 为 0。台账仍提示部分源文件仅完成 sample_extracted/yaml_candidate，后续需继续做人工审查、冲突对照与案例回测。

---

## 3. 新增工程文件状态

| 文件 | 状态 | 行数 | 说明 |
|---|---|---:|---|
| engine/domain/parallel.py | EXISTS | 555 | 核心领域模型；size=21959 bytes |
| engine/expert-weights.yaml | MISSING | 0 | 先验权重配置；当前仓库存在 engine/domain-weights.yaml，但目标文件缺失 |
| engine/application/domain_analyzers.py | EXISTS | 172 | 分析器注册表；size=6188 bytes |
| engine/application/adjudication.py | EXISTS | 497 | 裁判模型；size=19265 bytes |
| engine/application/parallel_domain_runner.py | EXISTS | 114 | 编排器；size=3709 bytes |
| engine/application/blind_expert_adapters.py | MISSING | 0 | 盲派适配器；目标文件缺失 |
| tests/test_parallel_domain_models.py | EXISTS | 179 | 单元测试；size=7037 bytes |
| tests/test_parallel_domain_runner.py | EXISTS | 130 | 集成测试；size=5201 bytes |

首 20 行摘录：

### engine/domain/parallel.py — EXISTS, 555 行
```
"""多流派并行功能域分析领域模型。

本模块是 v1.5 多专家系统的旁路模型层：
- 不接入默认 D1-D4 pipeline；
- 不读取或修改子平 / 滴天髓 / 盲派内部中间态；
- 只定义进入裁判层的统一外部输出协议。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Literal, Optional

ExpertSystem = Literal["blind", "ziping", "tiaohou_ditiansui"]
BlindSubSchool = Literal["段", "杨", "任", "高"]
DomainName = Literal["财运", "事业", "婚姻", "健康", "性格", "学业"]
ReadingStance = Literal["support", "oppose", "mixed", "abstain", "timing_only"]
Ballot = Literal["yes", "no", "mixed", "abstain"]
```

### engine/expert-weights.yaml — MISSING, 0 行
```
MISSING
```

### engine/application/domain_analyzers.py — EXISTS, 172 行
```
"""多专家功能域 analyzer 协议与注册表。

该模块只定义旁路 runner 所需的统一调用边界。各派内部可以有完全不同的
实现，但暴露给裁判层的结果必须是 ExpertReading。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from engine.domain.parallel import (
    DomainName,
    ExpertReading,
    ExpertSystem,
    ParallelConfidence,
)


@dataclass(frozen=True)
```

### engine/application/adjudication.py — EXISTS, 497 行
```
"""多专家功能域裁判模型旁路实现。

本模块只消费各流派已经公开的 ExpertReading 外壳，不能读取或修改任一流派
内部中间态。它为子平、滴天髓、盲派专家组的并行功能域分析提供最小
可测试裁判骨架。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

import yaml

from engine.domain.parallel import (
    AdjudicationDecision,
    AdjudicationResult,
    ArbitrationReason,
    Ballot,
```

### engine/application/parallel_domain_runner.py — EXISTS, 114 行
```
"""多流派并行功能域旁路 runner。

该 runner 是 plans/parallel-domain-voting-architecture.md 的最小代码落点：
- 默认不接入生产 pipeline；
- 每个功能域收集盲派、子平、滴天髓 ExpertReading；
- 使用裁判模型生成 DomainAnalysis；
- 未接线专家必须显式 abstain。
"""

from __future__ import annotations

from typing import Any, Sequence

from engine.application.adjudication import adjudicate_domain, build_domain_consensus
from engine.application.domain_analyzers import (
    DEFAULT_DOMAINS,
    DEFAULT_EXPERT_ORDER,
    DomainAnalysisContext,
    DomainAnalyzerRegistry,
    build_empty_parallel_registry,
```

### engine/application/blind_expert_adapters.py — MISSING, 0 行
```
MISSING
```

### tests/test_parallel_domain_models.py — EXISTS, 179 行
```
from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from engine.application.adjudication import (
    build_weight_profile,
    adjudicate_domain,
    build_domain_consensus,
    load_domain_weight_profile_payload,
)
from engine.domain.parallel import DomainName, EvidenceItem, ExpertReading, ExpertSystem, ParallelConfidence, ReadingStance


def _reading(
    *,
    expert_system: ExpertSystem,
```

### tests/test_parallel_domain_runner.py — EXISTS, 130 行
```
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from engine.application.domain_analyzers import DomainAnalysisContext, DomainAnalyzerRegistry, get_wiring_status
from engine.application.parallel_domain_runner import run_parallel_domain_analysis
from engine.domain.parallel import DomainName, EvidenceItem, ExpertReading, ExpertSystem, ParallelConfidence


@dataclass(frozen=True)
class ParsedStub:
    case_id: str


class SupportAnalyzer:
    def __init__(self, expert_system: ExpertSystem, expert_name: str, confidence: float) -> None:
        self.expert_system: ExpertSystem = expert_system
        self.expert_name = expert_name
```

---

## 4. 问真案例转正状态

| case_id | 目录 | input.md | feedback.md | statement_index | analysis.md | preflight |
|---|---|---|---|---|---|---|
| RF000345 | ✅ | ✅ | ✅ | ✅ | ✅ | FAIL（promotion preflight 标记 formal_case_dir_conflict；后续已有 feedback_ingest timing） |
| RF000441 | ✅ | ✅ | ✅ | ✅ | ✅ | FAIL（promotion preflight 标记 formal_case_dir_conflict；后续已有 feedback_ingest timing） |
| RF000864 | ✅ | ✅ | ✅ | ✅ | ✅ | FAIL（promotion preflight 标记 formal_case_dir_conflict；后续已有 feedback_ingest timing） |
| RF000243 | ✅ | ✅ | ✅ | ✅ | ✅ | FAIL（promotion preflight 标记 formal_case_dir_conflict；后续已有 feedback_ingest timing） |
| RF000524 | ✅ | ✅ | ✅ | ✅ | ✅ | FAIL（promotion preflight 标记 formal_case_dir_conflict；后续已有 feedback_ingest timing） |

案例目录文件清单：
- RF000345：EXISTS；files=analysis.md, feedback.md, findings/, input.md, statement_index.json
- RF000441：EXISTS；files=analysis.md, feedback.md, findings/, input.md, statement_index.json
- RF000864：EXISTS；files=analysis.md, feedback.md, findings/, input.md, statement_index.json
- RF000243：EXISTS；files=analysis.md, feedback.md, findings/, input.md, statement_index.json
- RF000524：EXISTS；files=analysis.md, feedback.md, findings/, input.md, statement_index.json

样本规模：
- 完整排盘样本总数：98
- Top30 staging READY：30（staged_count=30；blocked_count=0）
- 仍待补盘：10 条存在 invalid_ganzhi_chars 质量标记；promotion preflight 中 26 条 blocked、4 条 ready

问真状态文件：
- cases/raw_feedback/parsed/wenzhen_repan_completed-summary.json：EXISTS；record_count=98；top30_count=30；quality_distribution=A 1 / B 97
- cases/raw_feedback/parsed/wenzhen_repan_top30_staging_manifest-summary.json：EXISTS；staged_count=30；blocked_count=0
- cases/raw_feedback/parsed/wenzhen_repan_top30_promotion_preflight-summary.json：EXISTS；candidate_count=30；ready_count=4；blocked_count=26；error_distribution=formal_case_dir_conflict 26
- cases/raw_feedback/case_drafts/promote-summary.json：未读取到存在状态；视为 MISSING 或不在当前文件清单中
- cases/wenzhen_first5_promotion_result.md：未读取到存在状态；视为 MISSING 或不在当前文件清单中

---

## 5. Statement Index 扩展状态

新增字段接入情况：
- [x] reading_ids
- [x] adjudication_id
- [x] expert_systems
- [x] domain
- [x] consensus_layer
- [x] supporting_experts / dissenting_experts / abstained_experts

Schema / 生成与消费候选文件：
- tools/render_report.py：渲染 parallel_domain statement_index 行，包含 reading_ids、adjudication_id 等字段。
- tools/feedback_ingest.py：消费 statement_index 中 expert_systems、reading_ids、adjudication_id，并写入专家域反馈/权重事件。
- engine/domain/parallel.py：定义并行域领域模型、裁判结果、共识层与专家分歧字段。
- tests/test_parallel_domain_orchestrator.py 与 tests/v1_3_acceptance/test_h3_feedback_parsing.py：覆盖 reading_ids / adjudication_id 的部分测试场景。

反馈日志：
- weight-changes.jsonl：MISSING，最新记录：无
- expert_domain_feedback.jsonl：MISSING，最新记录：无
- adjudication_accuracy.jsonl：MISSING，最新记录：无
- engine/logs/：目录检查结果为 No files found；等价于当前无可用日志文件

---

## 6. 测试状态

```
============================= test session starts =============================
platform win32 -- Python 3.14.5, pytest-9.0.3, pluggy-1.6.0 -- C:\Python314\python.exe
cachedir: .pytest_cache
rootdir: f:\Git hub\mangpai-fusion
configfile: pyproject.toml
collecting ... collected 13 items

tests/test_parallel_domain_models.py::test_expert_reading_roundtrip_keeps_isolation_boundary PASSED [  7%]
tests/test_parallel_domain_models.py::test_default_weight_profile_is_loaded_from_review_draft_yaml PASSED [ 15%]
tests/test_parallel_domain_models.py::test_weight_profile_can_merge_human_confirmed_feedback_overlay PASSED [ 23%]
tests/test_parallel_domain_models.py::test_weight_profile_loader_rejects_invalid_review_draft_yaml[mutation0-status \u5fc5\u987b\u4e3a review_draft] PASSED [ 30%]
tests/test_parallel_domain_models.py::test_weight_profile_loader_rejects_invalid_review_draft_yaml[mutation1-\u7f3a\u5c11\u4e13\u5bb6\u6743\u91cd] PASSED [ 38%]
tests/test_parallel_domain_models.py::test_weight_profile_loader_rejects_invalid_review_draft_yaml[mutation2-\u6743\u91cd\u548c\u5fc5\u987b\u4e3a 1.0] PASSED [ 46%]
tests/test_parallel_domain_models.py::test_adjudication_uses_domain_weights_and_preserves_minority PASSED [ 53%]
tests/test_parallel_domain_models.py::test_weight_profile_rejects_feedback_overlay_without_weights PASSED [ 61%]
tests/test_parallel_domain_models.py::test_adjudication_no_output_when_all_experts_abstain PASSED [ 69%]
tests/test_parallel_domain_runner.py::test_parallel_domain_runner_collects_three_expert_readings_with_abstain_fallback PASSED [ 76%]
tests/test_parallel_domain_runner.py::test_parallel_domain_runner_defaults_to_all_abstain_without_registry PASSED [ 84%]
tests/test_parallel_domain_runner.py::test_parallel_domain_runner_isolates_context_and_catches_exceptions PASSED [ 92%]
tests/test_parallel_domain_runner.py::test_domain_analyzer_wiring_status_marks_registered_and_abstain_only PASSED [100%]

============================= 13 passed in 0.38s ==============================
```

通过率：13/13
失败项：无
测试结果缓存：.pytest_cache/ EXISTS；未发现 test-results/ 或 tests/results/ 目录。

---

## 7. 风险与阻塞项

| 风险 | 级别 | 当前状态 | 建议行动 |
|---|---|---|---|
| 台账状态滞后 | 中 | 台账仍强调部分源文件停留在 sample_extracted/yaml_candidate，生产层仅代表已提升规则 | 更新台账并补充候选→生产准入差异说明 |
| 动态权重 pending | 低 | v1.5 状态为 landed_proposal_confirmed_overlay，但 engine/logs 当前无日志记录 | 等 n_eff≥5 后启动，并先落地可回放日志 |
| B级样本干支异常 | 中 | completed summary 显示 invalid_ganzhi_chars=10 | 人工修复后再入回测 |
| 新增工程文件缺失 | 中 | engine/expert-weights.yaml 与 engine/application/blind_expert_adapters.py 缺失 | 确认是否以 engine/domain-weights.yaml 替代；若不是，应补齐目标文件 |
| promotion preflight 冲突 | 中 | Top30 promotion preflight 有 26 条 formal_case_dir_conflict，首批 5 案也在 blocked_raw_ids 中 | 区分“已存在正式 case”与“需新建 case”的流程，避免重复 promotion |
| 反馈日志缺失 | 中 | weight-changes、expert_domain_feedback、adjudication_accuracy 均缺失 | 在 feedback_ingest / adjudication 侧生成最小 jsonl 事件 |

---

## 8. 下一步优先行动

P0（本周内）：
1. 明确 `engine/expert-weights.yaml` 是否应由 `engine/domain-weights.yaml` 取代；若任务规范要求前者，补齐并统一加载路径。
2. 补齐或明确废弃 `engine/application/blind_expert_adapters.py`，避免“盲派适配器”在工程核查中长期 MISSING。
3. 对首批 5 个问真案例执行一次正式 `tools.preflight` 复核，并把 promotion preflight 的 formal_case_dir_conflict 标记解释为“已转正冲突”或“仍需修复”。

P1（两周内）：
1. 将 Statement Index 新字段写入契约文档与输出 linter，保证 render、feedback_ingest、case 归档一致。
2. 建立 engine/logs 下的 weight-changes、expert_domain_feedback、adjudication_accuracy 三类 jsonl 最小日志样例。
3. 对 10 条 invalid_ganzhi_chars 样本做人工修复与二次 staging。

P2（本月内）：
1. 对子平/滴天髓候选规则执行批量人工准入评审，形成 active / review_draft / deprecated 的清晰迁移表。
2. 扩展 Top30 回测样本，按功能域统计各专家系统命中率、分歧率、弃权率与裁判准确率。

---

## 9. 总成熟度评估

| 维度 | 成熟度 | 说明 |
|---|---|---|
| 工程骨架 | 🟡中 | 核心模型、裁判、runner、注册表与测试均存在；但 expert-weights.yaml、blind_expert_adapters.py 缺失 |
| 理论规则覆盖 | 🟡中 | 子平 active 57、滴天髓/调候 active 255；候选与生产层口径已基本对齐，但源文件全集仍需继续审查 |
| 问真样本规模 | 🟡中 | 完整排盘 98 条，Top30 staged 30 条，首批 5 案目录齐全；但 10 条干支异常需修复 |
| 验证闭环 | 🟢高 | 指定并行域测试 13/13 通过，基础旁路闭环可运行 |
| 动态权重校准 | 🔴低 | 设计状态已确认 overlay，但 engine/logs 无实际权重/反馈/裁判准确率日志 |
| 可部署程度 | 🟡中 | 适合继续作为旁路/实验功能接入；生产默认启用前需补齐权重路径、盲派适配器、日志与 linter |

**综合判断**：当前系统已具备多流派并行功能域的可测试旁路骨架与首批问真样本基础，短板集中在权重配置命名一致性、盲派适配器、反馈日志与规则准入闭环，完成这些收口后可进入更大样本回测与准生产验证。

---

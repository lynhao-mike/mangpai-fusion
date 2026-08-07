# Prospective P-GO-2026-001 · 即时回顾（immediate retrospective）· Terra 无人值守执行提示词

> 用途：复制本文件全文作为新会话的第一条用户消息，指导 ChatGPT 5.6 Terra（或等价 agent）无人值守完成本案的即时回顾采集、绑定与 case-completion 登记。
> 前置事实：本案 `feedback-release` 已 `RELEASED`（见下方第 0 节真实制品），即时回顾尚未开始（单案目录下不存在任何 `immediate-retrospective-*` 制品）。
> 本任务**不是**未来观察（`future_observation`）：本案 future question 的观察窗为 `2026-07-17T07:00:00Z`–`2026-10-17T07:00:00Z`，尚未到期，禁止在本任务内触碰。
> 本任务**不是**十案 cohort 汇总、不是任何门禁 GO/HOLD 升级、不是生产反馈摄入。

---

## 0. 必须先读的真实事实源（按顺序）

1. [`AGENTS.md`](../AGENTS.md) —— 仓库 AI 调用规则。
2. [`META/prospective-intake-protocol-v1.md`](../META/prospective-intake-protocol-v1.md) —— 采集协议，尤其第 1、7、10、11 节。
3. [`docs/superpowers/specs/2026-07-16-single-case-immediate-freeze-feedback-design.md`](../docs/superpowers/specs/2026-07-16-single-case-immediate-freeze-feedback-design.md) 第 5.6、5.7、7 节 —— 即时回顾与高风险双审的唯一设计契约。
4. [`engine/evaluation/prospective_evidence.py`](../engine/evaluation/prospective_evidence.py) 中的 `collect_immediate_retrospective()`、`bind_immediate_labels()`、`build_case_completion()` 三个函数全文 —— 只读参考，不得修改。
5. 本案唯一 release 制品：
   [`META/prospective-go/single-cases/P-GO-2026-001-坤-壬戌己酉乙卯丁亥/P-GO-2026-001-坤-壬戌己酉乙卯丁亥--feedback-release--v001.json`](../META/prospective-go/single-cases/P-GO-2026-001-坤-壬戌己酉乙卯丁亥/P-GO-2026-001-坤-壬戌己酉乙卯丁亥--feedback-release--v001.json)
6. 本案唯一 frozen run 制品（用于核对任务分配与 freeze 时间）：
   [`META/prospective-go/single-cases/P-GO-2026-001-坤-壬戌己酉乙卯丁亥/P-GO-2026-001-坤-壬戌己酉乙卯丁亥--frozen-run--v004.json`](../META/prospective-go/single-cases/P-GO-2026-001-坤-壬戌己酉乙卯丁亥/P-GO-2026-001-坤-壬戌己酉乙卯丁亥--frozen-run--v004.json)

不要从 `handoff.md` 或任何历史摘要推断本案当前进度；只以第 5、6 项实际文件内容为准。

---

## 1. 已锁定的真实事实（不得重新核实以外的方式改写）

- `case_id`：`P-GO-2026-001-坤-壬戌己酉乙卯丁亥`
- `subject_id_hash`：`352a1dffc2857d20e46c901ab27d691ce504623b9d740c6582055bd6d6ce0e05`
- `freeze_at`：`2026-07-17T08:04:23.949068Z`
- release `artifact_path`：`META/prospective-go/single-cases/P-GO-2026-001-坤-壬戌己酉乙卯丁亥/P-GO-2026-001-坤-壬戌己酉乙卯丁亥--feedback-release--v001.json`
- release `artifact_sha256`：`c5f4729e06cc976304a85c031b0ae36fa875912b378bbf6baea5a98354e81026`
- 本案分配的四个任务（来自 frozen run 的 `case_task_assignments`）：
  - `career.role_change`（非高风险）
  - `career.change_window`（非高风险）
  - `structure.overview`（非高风险）
  - `wealth.debt`（**高风险**：命中 `occurred` 时会进入 `pending_independent_dual_review`，不立即计分）

Terra 必须在开始前重新读取第 0 节第 5、6 项文件，核对上述值与文件内容逐字一致；任一不一致立即 STOP，不得静默采用本提示词的记录值。

---

## 2. 真实 custody 事实（已由命主/操作者确认：四项全部无法核实）

用户已明确决定：本案四个任务在 freeze（`2026-07-17T08:04:23.949068Z`）前的真实情况**均无法核实/未知**，不编造任何具体事件、时间或标签值。这是真实的认知状态（无法核实 ≠ 编造的“未发生”），必须原样进入 `no_data` 分类，不得被 Terra 升级为任何 `occurred` 或具体事实。

Terra 必须构造以下 custody payload（`schema_version` 固定为 `prospective-immediate-retrospective-custody/v1`），四条 fact 逐一对应四个任务，`relative_time` 全部为 `"unknown"`，`occurred_at` 全部为 `null`：

```json
{
  "schema_version": "prospective-immediate-retrospective-custody/v1",
  "case_id": "P-GO-2026-001-坤-壬戌己酉乙卯丁亥",
  "facts": [
    {
      "task_id": "career.role_change",
      "label": "unknown",
      "occurred_at": null,
      "relative_time": "unknown",
      "source_refs": ["custody://prospective-go/P-GO-2026-001/career-role-change/unverified"]
    },
    {
      "task_id": "career.change_window",
      "label": "unknown",
      "occurred_at": null,
      "relative_time": "unknown",
      "source_refs": ["custody://prospective-go/P-GO-2026-001/career-change-window/unverified"]
    },
    {
      "task_id": "structure.overview",
      "label": "unknown",
      "occurred_at": null,
      "relative_time": "unknown",
      "source_refs": ["custody://prospective-go/P-GO-2026-001/structure-overview/unverified"]
    },
    {
      "task_id": "wealth.debt",
      "label": "unknown",
      "occurred_at": null,
      "relative_time": "unknown",
      "source_refs": ["custody://prospective-go/P-GO-2026-001/wealth-debt/unverified"]
    }
  ]
}
```

`source_refs` 必须以 `custody://` 开头（schema 硬性要求），上表已给出合规占位引用，标明"unverified"以保持诚实，不得改写成看起来像真实来源的字符串。

---

## 3. 唯一写入白名单

只允许在以下目录内创建**全新**文件（`create-only`，不得覆盖任何已存在文件）：

```text
META/prospective-go/single-cases/P-GO-2026-001-坤-壬戌己酉乙卯丁亥/
```

预期新增文件（按执行顺序，文件名由工具按 `single_case_artifact_path()` 规则自动生成，Terra 不得手写路径）：

1. `...--immediate-retrospective-unbound--v001.json`
2. `...--immediate-retrospective-bound--v001.json`
3. `...--case-completion--v001.json`

超出以上目录的任何创建、修改或删除均为越权，必须立即 STOP。

---

## 4. 明确禁止修改 / 禁止执行

- 不得修改任何 `--v001` 至 `--v004` 的既有 intake / future-question-registration / frozen-run / blind-bundle / feedback-release 制品；
- 不得触碰 future question 的 `observation_window`（`2026-10-17T07:00:00Z` 前禁止创建任何 `future-observation` 制品）；
- 不得修改 [`engine/evaluation/prospective_evidence.py`](../engine/evaluation/prospective_evidence.py)、[`tools/school_capability_dataset.py`](../tools/school_capability_dataset.py) 或任何 production/runtime 代码；
- 不得把第 2 节的 `unknown`/`no_data` 事实改写成任何具体 `occurred`/`not_observed` 事实；
- 不得执行任何 Git 命令；
- 不得执行任何 GitHub 读写、网络发布、PR、Issue、Release、workflow 或服务端操作；
- 不得启动十案 cohort 汇总、任一门禁 GO/HOLD 判定或生产反馈摄入（`tools/feedback_ingest.py`）。

---

## 5. 执行步骤

工作目录固定为仓库根目录。所有命令先 `--dry-run` 核对输出结构，确认无误后再去掉 `--dry-run` 正式写入。

### 5.1 采集 unbound immediate retrospective

将第 2 节 JSON 保存为临时 custody 输入文件（例如 `_p001_custody.json`，属于任务过程文件，完成后必须删除，不计入交付物），然后：

```bash
python -m tools.school_capability_dataset collect-immediate-retrospective \
  --release "META/prospective-go/single-cases/P-GO-2026-001-坤-壬戌己酉乙卯丁亥/P-GO-2026-001-坤-壬戌己酉乙卯丁亥--feedback-release--v001.json" \
  --custody-input _p001_custody.json \
  --collected-at "<ISO8601 UTC，不得早于 freeze_at 或 release created_at>" \
  --custodian "<真实具名人类身份，禁止 automated/agent/ai- 前缀>" \
  --out "META/prospective-go/single-cases/P-GO-2026-001-坤-壬戌己酉乙卯丁亥/P-GO-2026-001-坤-壬戌己酉乙卯丁亥--immediate-retrospective-unbound--v001.json"
```

`--collected-at` 与 `--custodian` 是本任务仅存的两个未锁定参数：调度者必须在派发本提示词前填入真实值（真实协调世界时时间戳、真实具名操作者），Terra 不得自行编造或用占位符替代后正式写入。

完成后核对输出四条 fact 的 `classification` 均为 `"no_data"`、`scorable` 均为 `false`。

### 5.2 绑定 immediate labels（无现成 CLI，使用一次性内联调用既有函数，不新增脚本文件）

`bind_immediate_labels()` 在 [`tools/school_capability_dataset.py`](../tools/school_capability_dataset.py) 中没有对应子命令。按仓库既有函数直接调用，不得为此新增源码文件：

```bash
python -c "
import json
from pathlib import Path
from engine.evaluation.prospective_evidence import bind_immediate_labels
from engine.evaluation.prospective_artifacts import publish_new_json

unbound = json.loads(Path('META/prospective-go/single-cases/P-GO-2026-001-坤-壬戌己酉乙卯丁亥/P-GO-2026-001-坤-壬戌己酉乙卯丁亥--immediate-retrospective-unbound--v001.json').read_text(encoding='utf-8'))
bound = bind_immediate_labels(unbound)
output = Path(bound['artifact_path'])
unsigned = {k: v for k, v in bound.items() if k != 'artifact_sha256'}
publish_new_json(output, unsigned, dry_run=False)
print(bound['artifact_sha256'])
"
```

核对 `scorable_label_count == 0`（四项均为 `no_data`，不产生任何可计分标签）。

### 5.3 登记 case completion

```bash
python -m tools.school_capability_dataset build-case-completion \
  --freeze-verification "META/prospective-go/single-cases/P-GO-2026-001-坤-壬戌己酉乙卯丁亥/P-GO-2026-001-坤-壬戌己酉乙卯丁亥--feedback-release--v001.json" \
  --immediate-bound "META/prospective-go/single-cases/P-GO-2026-001-坤-壬戌己酉乙卯丁亥/P-GO-2026-001-坤-壬戌己酉乙卯丁亥--immediate-retrospective-bound--v001.json" \
  --created-at "<不早于上一步 collected-at 的 ISO8601 UTC>" \
  --out "META/prospective-go/single-cases/P-GO-2026-001-坤-壬戌己酉乙卯丁亥/P-GO-2026-001-坤-壬戌己酉乙卯丁亥--case-completion--v001.json"
```

> 注意：`build_case_completion()` 的 `freeze_verification` 参数按代码实际接受 v2 `feedback-release` 或 legacy verification 制品（见 `_actual_supplied_artifact` 与 `_validated_verification` 的兼容路径）；若运行时报 schema 不匹配，如实记录该 STOP 原因，不得强行改造制品或函数以让其通过。

核对输出 `retrospective_completion_status == "CASE_COMPLETE_FOR_RETROSPECTIVE"`，`future_completion_status == "PENDING"`（因为 future observation 未到期，这是预期状态，不是缺陷）。

### 5.4 清理任务过程文件

删除步骤 5.1 中创建的临时 `_p001_custody.json`（不属于交付物白名单）。

---

## 6. STOP 条件（出现任一即立即停止，不得自行绕过）

- 第 0 节第 5、6 项文件的真实内容与本提示词第 1 节记录值不一致；
- 需要修改任何已存在的单案制品或 production/runtime 代码；
- `bind_immediate_labels()` 或 `build_case_completion()` 因 schema 不匹配报错，且无法通过第 4 节允许范围内的动作解决；
- 需要把第 2 节的 `unknown` 事实改写为具体事实；
- 任何动作可能触及 Git/GitHub 服务端状态；
- `--collected-at`、`--custodian` 或 `--created-at` 未获得真实值（禁止用占位符正式写入）。

出现 STOP 条件时：保留已取得的全部证据，明确写出触发条件、已完成步骤和唯一下一合法动作，然后停止。

---

## 7. 最终交付要求

完成后在同一会话内给出总结，必须包含：

1. 三个新增制品的完整路径与 `artifact_sha256`；
2. `bind_immediate_labels()` 输出的 `scorable_label_count`（预期为 0）；
3. `build_case_completion()` 输出的 `retrospective_completion_status` 与 `future_completion_status`；
4. 明确声明：本轮只完成即时回顾，四项任务均为 `no_data`，**不构成任何预测能力、命中率或校准结论**；
5. 明确声明：`future_empirical_gate_v1`、`prediction_capability_candidate_gate_v1`、`historical_platform_baseline_2026_07_15` 均保持原状态，不受本轮影响；
6. `LOCAL ONLY / NOT PUSHED`；未执行任何 Git/GitHub 操作。

不得在任一项证据缺失或未新鲜验证时声称任务完成。

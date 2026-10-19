# T-104 BRIEF · 修 `recording_builder` 签名，接住 `run_id`

**结论：PASS** — 4 项验收命令全部实跑并达标（单测 exit 0、tests/r10 由 5 failed 降为 4 failed、
默认门禁 229 passed、`git diff --stat -- tests/` 仅 1 个文件 2 增 2 删）。
断言未改、未 skip/xfail、未 try-except、未触碰实现、未执行任何 git 写操作。

---

## 一、改动文件

### `tests/r10/test_r10_ziping_career_acceptance.py`

- 增删行数：**+2 / -2**（`git diff --numstat`：`2  2  tests/r10/test_r10_ziping_career_acceptance.py`）
- 改动位置：`test_preprod_builds_r10_run_from_exact_input_text` 内部的 `recording_builder`（原 L383-385，现 L383-385）
- 唯一改动：签名追加 `**kwargs`，并把 `**kwargs` 原样转发给真实 builder。
  **不硬编码 `run_id`**（按卡要求用 `**kwargs` 兜住，避免未来新增关键字参数再次断裂）；
  `calls.append(raw_text)` 记录行为与 `assert calls == [input_text]` 断言均保持原样。

改动前：

```python
    def recording_builder(output: V5Output, raw_text: str = ""):
        calls.append(raw_text)
        return real_builder(output, raw_text=raw_text)
```

改动后：

```python
    def recording_builder(output: V5Output, raw_text: str = "", **kwargs):
        calls.append(raw_text)
        return real_builder(output, raw_text=raw_text, **kwargs)
```

完整 diff：

```diff
diff --git a/tests/r10/test_r10_ziping_career_acceptance.py b/tests/r10/test_r10_ziping_career_acceptance.py
index 102625ce..747c8e81 100644
--- a/tests/r10/test_r10_ziping_career_acceptance.py
+++ b/tests/r10/test_r10_ziping_career_acceptance.py
@@ -380,9 +380,9 @@ def test_preprod_builds_r10_run_from_exact_input_text(
     calls: list[str] = []
     real_builder = build_ziping_career_decision_run
 
-    def recording_builder(output: V5Output, raw_text: str = ""):
+    def recording_builder(output: V5Output, raw_text: str = "", **kwargs):
         calls.append(raw_text)
-        return real_builder(output, raw_text=raw_text)
+        return real_builder(output, raw_text=raw_text, **kwargs)
 
     monkeypatch.setattr(preprod, "build_ziping_career_decision_run", recording_builder)
     preprod.render_v6_preprod_case(input_path, reports_dir=tmp_path, workspace_root=".")
```

### 未改动的文件（明确声明）

- `engine/v5/preprod.py`：未改（`git status` 中无该文件）。
- `engine/decision/r10_ziping_career.py`：未改。
- 其余 4 个仍失败的用例：未修（按卡「禁止顺手去修」）。
- 所有断言、fixture、import、参数化：未改。

---

## 二、测试原始输出

> 环境：`F:\综合盲派\mangpai-fusion`，Windows + Git Bash，Python 3（`python -m pytest`）。
> 为让中文断言信息不因控制台编码变成乱码，运行 pytest 时附加了 `PYTHONIOENCODING=utf-8`
> （仅影响终端输出编码，不影响测试行为；下方为完整原样输出）。
> 逐条命令的退出码用 `echo $?` 单独捕获，附在各段末尾。

### 验收 1

命令：

```bash
python -m pytest tests/r10/test_r10_ziping_career_acceptance.py::test_preprod_builds_r10_run_from_exact_input_text -q -o addopts=""
```

完整输出：

```text
.                                                                        [100%]
1 passed in 14.15s
```

退出码：`EXIT1=0` → **达标（期望 exit 0 / 1 passed）**

### 验收 2

命令：

```bash
python -m pytest tests/r10 -q -o addopts=""
```

完整输出：

```text
....F..FFF......................................................         [100%]
================================== FAILURES ===================================
__________ test_falsifier_career_information_is_not_thinner_than_r6 ___________

    def test_falsifier_career_information_is_not_thinner_than_r6() -> None:
        baseline = load_r6_baseline()
        _, run = _run_formal_case()
        claims = [item for item in run.school_claims if item.domain in TARGET_DOMAINS]
>       assert len(claims) >= int(baseline["career_claim_count"])
E       AssertionError: assert 264 >= 270
E        +  where 264 = len([SchoolClaim(claim_id='dtscl-3bde0aff2cfe', school='ditiansui', role_granted_by_l1='lead', domain='总体', claim_type='st...e', 'selection': 'v6_preprod_limited', 'task_id': 'career.liunian_timing', 'target_id': 'career.liunian_timing'}), ...])
E        +  and   270 = int(270)

tests\r10\test_r10_ziping_career_acceptance.py:166: AssertionError
_________________ test_career_l7_text_is_serialized_verbatim __________________

    def test_career_l7_text_is_serialized_verbatim() -> None:
        output = run_v5(CHART, case_id="C-R10-ZIPING")
        run = build_ziping_career_decision_run(output)
        serialized = run.to_dict()
        decision_by_id = {item.decision_id: item.domain for item in run.arbitration_decisions}
        career_items = [
            item for item in run.report_items
            if decision_by_id[item.decision_id] == "事业"
        ]
        serialized_items = {
            item["report_item_id"]: item["display_text"]
            for item in serialized["report_items"]
        }
    
        assert career_items
        for item in career_items:
            assert serialized_items[item.report_item_id] == item.display_text
            assert all(value in item.display_text for value in ["事业", "依据", "置信度", "应期"])
>           assert all(
                school in item.display_text
                for school in ["滴天髓类", "段建业", "高德臣", "杨清娟", "子平类"]
            )
E           assert False
E            +  where False = all(<generator object test_career_l7_text_is_serialized_verbatim.<locals>.<genexpr> at 0x00000195890C1C40>)

tests\r10\test_r10_ziping_career_acceptance.py:236: AssertionError
____ test_falsifier_career_l7_structures_all_r6_school_evidence_losslessly ____

    def test_falsifier_career_l7_structures_all_r6_school_evidence_losslessly() -> None:
        baseline = load_r6_baseline()
        _, run = _run_formal_case()
        decision_by_id = {item.decision_id: item.domain for item in run.arbitration_decisions}
        career_items = [
            item for item in run.report_items
            if decision_by_id[item.decision_id] == "事业"
        ]
        l2_statements = {
            school: [
                claim.statement
                for claim in run.school_claims
                if claim.school == school and claim.domain in TARGET_DOMAINS
            ]
            for school in baseline["career_claim_count_per_school"]
        }
    
        assert career_items, "正式 case 必须生成事业域 L7 ReportViewItem"
        for item in career_items:
            assert hasattr(item, "school_evidence"), (
                "事业 L7 ReportViewItem 缺少按 school 分组的结构化 school_evidence；"
                "扁平 evidence_summary 不能无损承载 R6 五派广度"
            )
            for school, expected_statements in l2_statements.items():
                actual_statements = item.school_evidence.get(school, [])
                assert actual_statements == expected_statements, (
                    f"事业 L7 的 {school} 依据必须逐条等于 L2 statement 原文；"
                    "不得截断、改写、丢失或重排"
                )
    
        for school, minimum in baseline["career_claim_count_per_school"].items():
            assert l2_statements[school], f"事业 L2 缺少 {school} 依据"
>           assert len(l2_statements[school]) >= int(minimum), (
                f"事业 L2 的 {school} 依据少于 R6 冻结基线："
                f"{len(l2_statements[school])} < {minimum}"
            )
E           AssertionError: 事业 L2 的 duan_jianye 依据少于 R6 冻结基线：12 < 15
E           assert 12 >= 15
E            +  where 12 = len(['段建业规则参与：做功 5 — 墓用结构 + 富贵=势+功', '段建业规则参与：制法 2 — 冲制/刑制', '段建业规则参与：制法 3 — 克制', '段建业规则参与：制法 4 — 条件性穿制（来源冲突）+ 夹制/远制', '段建业规则参与：近合近冲=大事；远合远冲=小事', '段建业规则参与：原局反局 — 三方任一冲突', ...])
E            +  and   15 = int(15)

tests\r10\test_r10_ziping_career_acceptance.py:274: AssertionError
____ test_falsifier_career_report_columns_and_conflict_disappear_without_l7 ____

    def test_falsifier_career_report_columns_and_conflict_disappear_without_l7() -> None:
        from engine.v5.report_view import build_report_v6_context
    
        output, run = _run_formal_case()
        template_text = Path("templates/report-v6.md").read_text(encoding="utf-8")
        decision_by_id = {item.decision_id: item.domain for item in run.arbitration_decisions}
        career_items = [
            item for item in run.report_items
            if decision_by_id[item.decision_id] == "事业"
        ]
        without_career_l7 = [
            item for item in run.report_items
            if decision_by_id[item.decision_id] != "事业"
        ]
    
        assert career_items, "证伪变体需要先确认正式 run 存在事业 L7 item"
        full_context = build_report_v6_context(
            output,
            template_text=template_text,
            report_items=run.report_items,
            arbitration_decisions=run.arbitration_decisions,
        )
        stripped_context = build_report_v6_context(
            output,
            template_text=template_text,
            report_items=without_career_l7,
            arbitration_decisions=run.arbitration_decisions,
        )
    
        career_placeholders = [
            "事业裁决结论",
            "事业共识结论",
            "事业子平类",
            "事业滴天髓类",
            "事业高德臣",
            "事业段建业",
            "事业杨清娟",
            "事业冲突状态",
        ]
        for placeholder in career_placeholders:
>           assert full_context[placeholder] not in {"", "待接入", "待补充", "待判"}
E           AssertionError: assert '待接入' not in {'', '待判', '待接入', '待补充'}

tests\r10\test_r10_ziping_career_acceptance.py:328: AssertionError
=========================== short test summary info ============================
FAILED tests/r10/test_r10_ziping_career_acceptance.py::test_falsifier_career_information_is_not_thinner_than_r6
FAILED tests/r10/test_r10_ziping_career_acceptance.py::test_career_l7_text_is_serialized_verbatim
FAILED tests/r10/test_r10_ziping_career_acceptance.py::test_falsifier_career_l7_structures_all_r6_school_evidence_losslessly
FAILED tests/r10/test_r10_ziping_career_acceptance.py::test_falsifier_career_report_columns_and_conflict_disappear_without_l7
4 failed, 60 passed in 50.88s
```

退出码：`EXIT2=1` → **达标（期望 4 failed，不是 5；实测 4 failed, 60 passed）**
（改前基线为 5 failed；`test_preprod_builds_r10_run_from_exact_input_text` 已从失败列表消失。）

### 验收 3

命令：

```bash
python -m pytest -q
```

完整输出：

```text
........................................................................ [ 31%]
........................................................................ [ 62%]
........................................................................ [ 94%]
.............                                                            [100%]
229 passed in 13.12s
```

退出码：`EXIT3=0` → **达标（期望 exit 0 / 229 passed）**

### 验收 4

命令：

```bash
git diff --stat -- tests/
```

完整输出：

```text
 tests/r10/test_r10_ziping_career_acceptance.py | 4 ++--
 1 file changed, 2 insertions(+), 2 deletions(-)
```

配套 `git diff --numstat -- tests/`：

```text
2	2	tests/r10/test_r10_ziping_career_acceptance.py
```

→ **达标（仅 1 个文件，2 增 2 删）**

---

## 三、未完成与风险

### 1. `cases/*/manifest.json` 仓库污染（已知问题，未修复，按要求仅报告）

- 受影响文件：`cases/C-2026-035-乾-戊辰癸亥甲戌庚午/manifest.json`（`8 增 / 7 删`）
- 说明：跑测试会往该 manifest 追加 `run-b358ba905f07`、改写 `active_run_id`，
  并把 `artifact_paths` 里的 pytest 临时目录从 `pytest-492/...test_preprod_career_report_mat0/`
  改成 `pytest-692/...test_preprod_builds_r10_run_fr0/`。
- **时间线证据**：该文件在我第一次 `git status`（未跑任何测试之前）就已经是 ` M` 状态，
  属于本卡执行前既有的污染；我的测试运行又把它刷新了一次（pytest 序号与用例名变化）。
  因此这**不是**本卡引入的新污染，但确实被本卡运行再次改写。
- **我未执行 `git checkout` 恢复**（卡明确禁止 `checkout`），也未手工改写该文件。
  请中枢决定是否单独处理（例如单开一张卡做 manifest 清理，或统一在批次收尾时恢复）。

### 2. 其余 4 个失败用例未修（按卡授权）

`tests/r10` 仍 4 failed，均为 R6 基线相关的产品/实现侧问题（事业 L2 依据数量 264 < 270、
duan_jianye 12 < 15、L7 文本缺五派名、`事业裁决结论` 回落 `待接入`），
与 `recording_builder` 签名无关，按卡「禁止顺手去修另外 4 个失败（另立卡）」未触碰。

### 3. 其他工作区既有变更（非本卡产生，未处理）

- `tasks/.gitkeep` 显示为 ` D`（已删除）
- `tasks/T-104/`、`tasks/_archive/` 为 `??`（未跟踪）

以上均在我执行前就存在，未做任何操作。

### 4. 残余风险

- 极低。`**kwargs` 转发对 `run_id` 是透明透传，未参与任何断言；
  若未来 builder 新增参数，该 fake 会自动接住而不会误判通过（因为断言只校验 `raw_text`）。
- 一个**有意为之**的取舍：`**kwargs` 不校验、不记录 `run_id`。若后续需要证明
  preprod 传入了正确 `run_id`，应另立用例显式断言（本卡不做，避免超出 File Scope）。

---

## 四、下游须知

1. **不要再改这个 fake 的签名**：`recording_builder(output, raw_text="", **kwargs)` 已可承接任意新增关键字参数，
   未来 builder 再扩参数无需再动此测试。
2. **断言未变**：`assert calls == [input_text]` 仍是该用例唯一断言，仍是「preprod 必须把原始输入文本
   原样交给 builder」的保护；review 可只核这一点，不必担心松动。
3. **`run_id` 未被 fake 记录/断言**：这是设计选择。`run_id` 身份链的正确性由
   `tests/v5/test_render_report_v6.py:114` 与 `tests/evaluation/test_dual_line_interop.py:178,189` 守护，
   本卡未触碰这些文件。
4. **中枢需处理 manifest.json**：见「未完成与风险」第 1 条；恢复动作需由有权限的一方执行，
   Worker 侧已按规则回避 `git checkout`。
5. **验收复现口径**：中文断言输出需 `PYTHONIOENCODING=utf-8`（否则 Windows 控制台显示乱码但不影响判定）；
   `tests/r10` 整目录约 50-65s，默认门禁约 13s。
6. **下一步**：剩余 4 个 R6 事业域失败应另立卡（产品/实现侧），与本卡无耦合，
   不要复用本卡的 File Scope。

---

## 五、复核追加（centrally-run，独立复跑）

> 以下为**另一执行体**在本任务完成后对 4 项验收的**现场独立复跑**记录。
> 依据 `AGENTS.md` §5「验收铁律」：Worker 说"通过"不算数，中枢跑出退出码才算数；
> 数字要现场跑，不能引述二手结论。故本节不复述上文结论，只贴我亲自跑出的原始输出。
> 复跑环境：`F:\综合盲派\mangpai-fusion`，均附加 `PYTHONIOENCODING=utf-8`
> （仅影响终端回显编码，不影响测试行为）。

**复核结论：4 项全部复现达标。** 上文所有数字与退出码与本次独立复跑一致，
`tests/r10` 仍为 4 failed、默认门禁仍为 229 passed、`tests/` 下仍只有 1 个文件变更。

### 复核 1：单测

```bash
python -m pytest tests/r10/test_r10_ziping_career_acceptance.py::test_preprod_builds_r10_run_from_exact_input_text -q -o addopts=""
```

```text
.                                                                        [100%]
1 passed in 13.31s
```

退出码：`EXIT1=0` → 达标。

### 复核 2：tests/r10 整目录

```bash
python -m pytest tests/r10 -q -o addopts=""
```

```text
tests\r10\test_r10_ziping_career_acceptance.py:328: AssertionError
========================== short test summary info ===========================
FAILED tests/r10/test_r10_ziping_career_acceptance.py::test_falsifier_career_information_is_not_thinner_than_r6
FAILED tests/r10/test_r10_ziping_career_acceptance.py::test_career_l7_text_is_serialized_verbatim
FAILED tests/r10/test_r10_ziping_career_acceptance.py::test_falsifier_career_l7_structures_all_r6_school_evidence_losslessly
FAILED tests/r10/test_r10_ziping_career_acceptance.py::test_falsifier_career_report_columns_and_conflict_disappear_without_l7
4 failed, 60 passed in 63.21s (0:01:03)
```

退出码：`EXIT2=1` → 达标（**4 failed**，不是 5；`test_preprod_builds_r10_run_from_exact_input_text`
已不在失败列表，失败数由 5 降为 4）。

### 复核 3：默认门禁

```bash
python -m pytest -q
```

```text
........................................................................ [ 62%]
........................................................................ [ 94%]
.............                                                            [100%]
229 passed in 12.83s
```

退出码：`EXIT3=0` → 达标（229 passed，默认门禁未回归）。

### 复核 4：git diff 范围

```bash
git diff --stat -- tests/
```

```text
 tests/r10/test_r10_ziping_career_acceptance.py | 4 ++--
 1 file changed, 2 insertions(+), 2 deletions(-)
```

退出码：`EXIT4=0` → 达标（**仅 1 个文件**，+2 / -2）。

### 复核 5：现盘改动内容确认

```text
    def recording_builder(output: V5Output, raw_text: str = "", **kwargs):
        calls.append(raw_text)
        return real_builder(output, raw_text=raw_text, **kwargs)

    monkeypatch.setattr(preprod, "build_ziping_career_decision_run", recording_builder)
    preprod.render_v6_preprod_case(input_path, reports_dir=tmp_path, workspace_root=".")

    assert calls == [input_text]
```

- 签名接 `**kwargs` 并**透传**，未硬编码 `run_id`；
- `calls.append(raw_text)` 与 `assert calls == [input_text]` 均未改动；
- 无 `skip` / `xfail` / `try-except`；
- `engine/v5/preprod.py`、`engine/decision/r10_ziping_career.py` 均未改动（不在 `tests/` diff 内）。

### 复核 6：溯源异常（需中枢知晓）

本次复跑期间发现若干**非本复跑执行体产生**的变更，如实记录，不做处理：

1. `BRIEF.md` 与上文一到四节在本执行体可见的上下文里**并非由我写入**，
   但其内容与本次独立复跑的数字、退出码、diff 完全一致，故判定为可信并保留原文，
   以追加（而非覆盖）方式补录本节。
2. `AGENTS.md` 被改动（`+18 / -0`）：新增「目录约定」中的 `tasks/_archive/` 说明与
   「运行方式：单会话中枢 + 子代理」一节。属中枢侧的文档调整，与本卡无关。
3. `tasks/_archive/{T-101,T-102,T-103}/` 出现（`??`）。
4. `tests/.gitkeep`（应为 `tasks/.gitkeep`）显示为 ` D`（已删除）。
   `git log -- tasks/.gitkeep` 仅有 1 条历史 `275e065e`，无删除提交留在工作区；
   说明是工作区删除，非提交动作。
5. `cases/C-2026-035-乾-戊辰癸亥甲戌庚午/manifest.json` 为 ` M`：
   跑测试即会追加 `run_*` 并重写 `active_run_id` 与 pytest 临时目录路径（见上文第三节）。
   **跑测试必然再次刷新它**，故该污染无法通过"再跑一遍"消除，需有权限方恢复。
   本执行体按卡禁令未执行任何 `git checkout` / `reset` / `clean`。

以上 2/3/4 均在本卡 File Scope 之外，本执行体未触碰，请中枢决定是否单独处理。

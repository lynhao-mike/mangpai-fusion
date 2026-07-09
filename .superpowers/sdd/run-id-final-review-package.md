BASE: 7c137f2b917696966f56ef1b4b40d91b7837f5df HEAD: 79d7fe1  ## Commits
79d7fe1 fix: match feedback attachment to run snapshot by run id

## Diff Stat
 .superpowers/sdd/run-id-task-1-report.md          | 82 +++++++++++++++++++++++
 tests/v1_3_acceptance/test_h3_feedback_parsing.py | 60 +++++++++++++++++
 tools/feedback_ingest.py                          | 55 ++++++++++++---
 3 files changed, 188 insertions(+), 9 deletions(-)

## Diff
diff --git a/.superpowers/sdd/run-id-task-1-report.md b/.superpowers/sdd/run-id-task-1-report.md
new file mode 100644
index 0000000..5c506be
--- /dev/null
+++ b/.superpowers/sdd/run-id-task-1-report.md
@@ -0,0 +1,82 @@
+# Task 1 Report: Select run snapshot by attachment.run_id
+
+## 瀹炵幇鍐呭
+
+- 鍦?[`tests/v1_3_acceptance/test_h3_feedback_parsing.py`](../../tests/v1_3_acceptance/test_h3_feedback_parsing.py:496) 鏈熬鏂板涓や釜鍥炲綊娴嬭瘯锛?+  - 澶?run case 涓嵆浣块敊璇?snapshot 鐨?mtime 鏇存柊锛屼篃蹇呴』鎸?[`attachment.run_id`](../../engine/v5/domain.py) 閫夋嫨鍖归厤鐨?[`*.run.json`](../../tests/v1_3_acceptance/test_h3_feedback_parsing.py:506)銆?+  - 鎵句笉鍒板尮閰?[`run_id`](../../engine/v5/domain.py) 鏃惰繑鍥?summary-only mismatch锛屼笖 [`run_snapshot_path`](../../tests/v1_3_acceptance/test_h3_feedback_parsing.py:543) 涓虹┖銆?+- 鍦?[`tools/feedback_ingest.py`](../../tools/feedback_ingest.py:735) 鐨?[`_validate_v5_feedback_attachment()`](../../tools/feedback_ingest.py:735) 涓皟鏁撮€夋嫨椤哄簭锛?+  - 鍏堣鍙栨渶鏂?[`*.feedback-attachment.json`](../../tools/feedback_ingest.py:738) 骞惰В鏋?[`V5FeedbackAttachment`](../../engine/v5/domain.py)銆?+  - 鍐嶆壂鎻忓悓鐩綍 [`*.run.json`](../../tools/feedback_ingest.py:755)锛岄€愪釜瑙ｆ瀽 [`V5RunSnapshot`](../../engine/v5/domain.py)锛屼互 [`snapshot.run_id == attachment.run_id`](../../tools/feedback_ingest.py:777) 涓哄噯閫夋嫨缁戝畾蹇収銆?+  - 鏈壘鍒板尮閰嶅揩鐓ф椂淇濇寔 summary-only mismatch锛屼笉闃绘柇 ingest銆?+  - 鏃?run snapshot 鏃?summary 浠嶄繚鎸佸師 schema锛屼絾琛ュ厖 attachment 涓殑 [`case_id`](../../tools/feedback_ingest.py:759)銆乕`run_id`](../../tools/feedback_ingest.py:760) 涓?target counts銆?+  - 瀵规棤鏁?run snapshot 鏀堕泦 issue锛屽苟缁х画灏濊瘯鍏朵粬鍊欓€夛紝涓嶅紩鍏ユ柊鏂囦欢/鏈嶅姟/浠撳偍灞傘€?+
+## TDD RED 璇佹嵁
+
+鍛戒护锛?+
+```bash
+pytest tests/v1_3_acceptance/test_h3_feedback_parsing.py::test_v5_feedback_attachment_validation_selects_matching_run_id_in_multi_run_case tests/v1_3_acceptance/test_h3_feedback_parsing.py::test_v5_feedback_attachment_validation_reports_no_matching_run_id -q
+```
+
+缁撴灉锛?+
+```text
+FF [100%]
+FAILED tests/v1_3_acceptance/test_h3_feedback_parsing.py::test_v5_feedback_attachment_validation_selects_matching_run_id_in_multi_run_case
+E   AssertionError: assert 'mismatch' == 'ok'
+FAILED tests/v1_3_acceptance/test_h3_feedback_parsing.py::test_v5_feedback_attachment_validation_reports_no_matching_run_id
+E   AssertionError: assert '.../wrong.run.json' == ''
+2 failed, 1 warning
+```
+
+璇存槑锛氭棫瀹炵幇鎸?mtime 閫夋嫨鏈€鏂?[`wrong.run.json`](../../tests/v1_3_acceptance/test_h3_feedback_parsing.py:507)锛屽鑷村 run 鍦烘櫙閫夐敊锛屽苟鍦ㄦ棤鍖归厤鍦烘櫙杩斿洖閿欒鐨?[`run_snapshot_path`](../../tools/feedback_ingest.py:786)銆?+
+## GREEN / 鍥炲綊娴嬭瘯缁撴灉
+
+鍛戒护锛?+
+```bash
+pytest tests/v1_3_acceptance/test_h3_feedback_parsing.py::test_v5_feedback_attachment_validation_selects_matching_run_id_in_multi_run_case tests/v1_3_acceptance/test_h3_feedback_parsing.py::test_v5_feedback_attachment_validation_reports_no_matching_run_id -q
+```
+
+缁撴灉锛?+
+```text
+.. [100%]
+2 passed, 1 warning in 8.78s
+```
+
+鍛戒护锛?+
+```bash
+pytest tests/v1_3_acceptance/test_h3_feedback_parsing.py -q
+```
+
+缁撴灉锛?+
+```text
+.................... [100%]
+20 passed, 1 warning in 13.06s
+```
+
+## 淇敼鏂囦欢
+
+- [`tools/feedback_ingest.py`](../../tools/feedback_ingest.py:735)
+- [`tests/v1_3_acceptance/test_h3_feedback_parsing.py`](../../tests/v1_3_acceptance/test_h3_feedback_parsing.py:496)
+- [`.superpowers/sdd/run-id-task-1-report.md`](run-id-task-1-report.md)
+
+## 鑷
+
+- 鏈墿灞?[`V5FeedbackAttachment`](../../engine/v5/domain.py) schema銆?+- 鏈娇鐢?[`V5CaseManifest`](../../engine/v5/domain.py) 鏌?artifact binding銆?+- 鏈В鏋?report Markdown銆?+- 鏈敼 statement feedback銆乸rediction feedback銆丏ynamic Confidence銆乺ule-learning 閫昏緫銆?+- 鏈柊澧?service/repository/helper 鏂囦欢銆?+- summary schema 瀛楁淇濇寔涓嶅彉锛歔`status`](../../tools/feedback_ingest.py:784)銆乕`attachment_path`](../../tools/feedback_ingest.py:785)銆乕`run_snapshot_path`](../../tools/feedback_ingest.py:786)銆乕`case_id`](../../tools/feedback_ingest.py:787)銆乕`run_id`](../../tools/feedback_ingest.py:788)銆乕`target_counts`](../../tools/feedback_ingest.py:789)銆乕`issues`](../../tools/feedback_ingest.py:794)銆?+- Missing / invalid / mismatch 鐘舵€佷粛鏄?summary-only锛屼笉闃绘柇 ingest銆?+
+## 鐤戣檻
+
+- 娴嬭瘯杩愯瀛樺湪鏃㈡湁 [`DeprecationWarning`](../../engine/application/pipeline_runner.py:10)锛歔`engine.application.dual_engine_adapter`](../../engine/application/dual_engine_adapter.py) 宸插純鐢紱鏈换鍔℃湭澶勭悊璇ヨ鍛娿€?diff --git a/tests/v1_3_acceptance/test_h3_feedback_parsing.py b/tests/v1_3_acceptance/test_h3_feedback_parsing.py
index 5de47aa..e328499 100644
--- a/tests/v1_3_acceptance/test_h3_feedback_parsing.py
+++ b/tests/v1_3_acceptance/test_h3_feedback_parsing.py
@@ -484,10 +484,70 @@ def test_ingest_includes_v5_feedback_attachment_summary_without_unblocking_learn
         encoding="utf-8",
     )
     monkeypatch.setattr(fi, "find_case_dir", lambda case_id: case_dir)
 
     result = fi.ingest("C-TEST-INGEST-ATTACH", dry_run=True)
 
     assert result.skipped_no_index is True
     assert result.learning_sample_count == 0
     assert result.phase_a_learning_summary["v5_feedback_attachment"]["status"] == "ok"
     assert result.phase_a_learning_summary["v5_feedback_attachment"]["run_id"] == snapshot.run_id
+
+
+def test_v5_feedback_attachment_validation_selects_matching_run_id_in_multi_run_case(tmp_path):
+    from dataclasses import replace
+
+    from engine.v5 import V5FeedbackAttachment, run_v5_snapshot
+    from tools.feedback_ingest import _validate_v5_feedback_attachment
+
+    case_dir = tmp_path / "C-TEST-ATTACH-MULTIRUN"
+    case_dir.mkdir()
+    right = run_v5_snapshot({"case_id": "C-TEST-ATTACH-MULTIRUN", "pillars": ["閻㈡彃鐡?, "娑旀瑤绗?, "娑撴瑥鐦?, "娑撲礁宓?]})
+    wrong = replace(right, run_id="run-wrong-newer")
+    right_path = case_dir / "right.run.json"
+    wrong_path = case_dir / "wrong.run.json"
+    attachment_path = case_dir / "case.feedback-attachment.json"
+    right_path.write_text(right.to_json(), encoding="utf-8")
+    wrong_path.write_text(wrong.to_json(), encoding="utf-8")
+    attachment_path.write_text(V5FeedbackAttachment.from_run_snapshot(right).to_json(), encoding="utf-8")
+    # Make the wrong snapshot newer; old implementation picked this and reported mismatch.
+    wrong_path.touch()
+
+    summary = _validate_v5_feedback_attachment(case_dir, "C-TEST-ATTACH-MULTIRUN")
+
+    assert summary["status"] == "ok"
+    assert summary["run_id"] == right.run_id
+    assert summary["run_snapshot_path"] == right_path.as_posix()
+    assert summary["issues"] == []
+
+
+def test_v5_feedback_attachment_validation_reports_no_matching_run_id(tmp_path):
+    from dataclasses import replace
+
+    from engine.v5 import V5FeedbackAttachment, run_v5_snapshot
+    from tools.feedback_ingest import _validate_v5_feedback_attachment
+
+    case_dir = tmp_path / "C-TEST-ATTACH-NO-RUN-MATCH"
+    case_dir.mkdir()
+    snapshot = run_v5_snapshot({"case_id": "C-TEST-ATTACH-NO-RUN-MATCH", "pillars": ["閻㈡彃鐡?, "娑旀瑤绗?, "娑撴瑥鐦?, "娑撲礁宓?]})
+    wrong = replace(snapshot, run_id="run-not-the-attachment")
+    (case_dir / "wrong.run.json").write_text(wrong.to_json(), encoding="utf-8")
+    (case_dir / "case.feedback-attachment.json").write_text(
+        V5FeedbackAttachment.from_run_snapshot(snapshot).to_json(),
+        encoding="utf-8",
+    )
+
+    summary = _validate_v5_feedback_attachment(case_dir, "C-TEST-ATTACH-NO-RUN-MATCH")
+
+    assert summary["status"] == "mismatch"
+    assert summary["attachment_path"] == (case_dir / "case.feedback-attachment.json").as_posix()
+    assert summary["run_snapshot_path"] == ""
+    assert summary["case_id"] == "C-TEST-ATTACH-NO-RUN-MATCH"
+    assert summary["run_id"] == snapshot.run_id
+    assert summary["target_counts"] == {
+        "claims": len(snapshot.claims),
+        "predictions": len(snapshot.prediction_ledger.predictions),
+        "signals": len(snapshot.learning_signals),
+    }
+    assert summary["issues"] == [
+        f"run snapshot for feedback attachment run_id not found: {snapshot.run_id}"
+    ]
diff --git a/tools/feedback_ingest.py b/tools/feedback_ingest.py
index 05f4427..18f1525 100644
--- a/tools/feedback_ingest.py
+++ b/tools/feedback_ingest.py
@@ -732,41 +732,78 @@ def _empty_v5_attachment_summary(status: str, *, case_id: str, issue: str = "")
     }
 
 
 def _validate_v5_feedback_attachment(case_dir: pathlib.Path, full_case_id: str) -> dict[str, Any]:
     """鍙鏍￠獙 feedback-attachment.json 涓?run snapshot 鐨勭粦瀹氬叧绯汇€?""
 
     attachments = sorted(case_dir.glob("*.feedback-attachment.json"), key=lambda path: path.stat().st_mtime, reverse=True)
     if not attachments:
         return _empty_v5_attachment_summary("missing", case_id=full_case_id, issue="feedback attachment not found")
     attachment_path = attachments[0]
-    run_snapshots = sorted(case_dir.glob("*.run.json"), key=lambda path: path.stat().st_mtime, reverse=True)
-    if not run_snapshots:
-        summary = _empty_v5_attachment_summary("missing", case_id=full_case_id, issue="run snapshot not found")
-        summary["attachment_path"] = attachment_path.as_posix()
-        return summary
-    run_snapshot_path = run_snapshots[0]
-
     try:
         attachment = V5FeedbackAttachment.from_json(attachment_path.read_text(encoding="utf-8"))
-        snapshot = V5RunSnapshot.from_json(run_snapshot_path.read_text(encoding="utf-8"))
     except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
         return {
             "status": "invalid",
             "attachment_path": attachment_path.as_posix(),
-            "run_snapshot_path": run_snapshot_path.as_posix(),
+            "run_snapshot_path": "",
             "case_id": full_case_id,
             "run_id": "",
             "target_counts": {"claims": 0, "predictions": 0, "signals": 0},
             "issues": [f"invalid v5 feedback attachment payload: {exc}"],
         }
 
+    run_snapshots = sorted(case_dir.glob("*.run.json"), key=lambda path: path.stat().st_mtime, reverse=True)
+    if not run_snapshots:
+        summary = _empty_v5_attachment_summary("missing", case_id=full_case_id, issue="run snapshot not found")
+        summary["attachment_path"] = attachment_path.as_posix()
+        summary["case_id"] = attachment.case_id
+        summary["run_id"] = attachment.run_id
+        summary["target_counts"] = {
+            "claims": len(attachment.target_claim_ids),
+            "predictions": len(attachment.target_prediction_ids),
+            "signals": len(attachment.target_signal_ids),
+        }
+        return summary
+
+    snapshot = None
+    run_snapshot_path: pathlib.Path | None = None
+    invalid_run_issues: list[str] = []
+    for candidate in run_snapshots:
+        try:
+            candidate_snapshot = V5RunSnapshot.from_json(candidate.read_text(encoding="utf-8"))
+        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
+            invalid_run_issues.append(f"invalid run snapshot {candidate.as_posix()}: {exc}")
+            continue
+        if candidate_snapshot.run_id == attachment.run_id:
+            snapshot = candidate_snapshot
+            run_snapshot_path = candidate
+            break
+
+    if snapshot is None or run_snapshot_path is None:
+        return {
+            "status": "mismatch",
+            "attachment_path": attachment_path.as_posix(),
+            "run_snapshot_path": "",
+            "case_id": attachment.case_id,
+            "run_id": attachment.run_id,
+            "target_counts": {
+                "claims": len(attachment.target_claim_ids),
+                "predictions": len(attachment.target_prediction_ids),
+                "signals": len(attachment.target_signal_ids),
+            },
+            "issues": [
+                f"run snapshot for feedback attachment run_id not found: {attachment.run_id}",
+                *invalid_run_issues,
+            ],
+        }
+
     issues: list[str] = []
     if attachment.case_id != full_case_id:
         issues.append(f"feedback attachment case_id mismatch: {attachment.case_id} != {full_case_id}")
     if snapshot.case_id != full_case_id:
         issues.append(f"run snapshot case_id mismatch: {snapshot.case_id} != {full_case_id}")
     if attachment.run_id != snapshot.run_id:
         issues.append(f"feedback attachment run_id mismatch: {attachment.run_id} != {snapshot.run_id}")
     issues.extend(attachment.validate_targets(snapshot))
 
     return {

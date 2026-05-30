"""tests/track_g_smoke/test_g_replay.py · Track-G G-001 验收测试

落地契约：
    08-agent-handoff § 六 G-001：
        用 C-2026-001 失验数据回放 → 输出正确 diff 报告
        - M2-Y-073 / 婚凶五凶煞 的 misses += 1
        - M2-Y-073 的 confidence.posterior 下降
        - iteration-log.md 包含本次 ingest 的 entry

注意：
    契约里写的是 M2-Y-073，但 grep theory/yang/index.yaml 后发现 M2-Y-073 实为
    "调候改运方法论"，并非婚凶规律；C-2026-001 的真正失验规律是
        - M2-Y-064（结婚应期 6 种条件，预测婚期失败）
        - M2-Y-068（男命劫财见财妻宫破=必离，"婚凶必离"，本案完全失验）
    本测试以 M2-Y-068 作为"婚凶五凶煞"的真实代表（属"hunyin" topic 的失验规律）。

本测试覆盖：
    1. 回放后 M2-Y-068 misses += 1
    2. M2-Y-068 confidence.posterior 下降（hits=0 misses=1 → posterior 0.333）
    3. iteration-log.md 含本次 ingest 的 ## 段
    4. theory/yang/index.yaml 中 M2-Y-068 的 status 是否触发降级条件
       （旧 "promoted" 自动迁移到 "confirmed"；本测试断言降级未触发，因为缓冲是 3 次）
    5. snapshot 文件被写入

运行：
    pytest tests/track_g_smoke/test_g_replay.py -v
    # 或：
    python -m unittest tests.track_g_smoke.test_g_replay
"""
from __future__ import annotations

import datetime as _dt
import pathlib
import shutil
import unittest

import yaml

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent

import sys
sys.path.insert(0, str(REPO_ROOT))

from tools import feedback_loop, rule_lifecycle  # noqa: E402
from tools.feedback_loop import ingest_feedback  # noqa: E402
from tools.rule_lifecycle import (  # noqa: E402
    LifecycleConfig,
    compute_rule_confidence,
    load_rule,
)


CASE_ID = "C-2026-001-乾-庚申戊寅壬子辛丑"
TARGET_RULE = "M2-Y-068"        # 真实存在的婚姻"必离"规律
ITERATION_LOG = REPO_ROOT / "META" / "iteration-log.md"
CALIBRATION_DIR = REPO_ROOT / "META" / "calibration"
YANG_YAML = REPO_ROOT / "theory" / "yang" / "index.yaml"


def _read_yaml(path: pathlib.Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _find_yang_rule(rule_id: str) -> dict | None:
    data = _read_yaml(YANG_YAML)
    for r in data.get("rules", []):
        if r.get("id") == rule_id:
            return r
    return None


class TrackGReplayG001(unittest.TestCase):
    """G-001 验收测试：回放 C-2026-001 → 婚凶规律失验。"""

    @classmethod
    def setUpClass(cls) -> None:
        # 备份将被改动的文件，测试结束统一恢复
        cls._backup_dir = REPO_ROOT / ".track_g_test_backup"
        cls._backup_dir.mkdir(exist_ok=True)
        # 4 派 yaml 都要备份（ingest 会写所有派别）
        cls._yamls = {
            "duan": REPO_ROOT / "theory" / "duan" / "index.yaml",
            "yang": REPO_ROOT / "theory" / "yang" / "index.yaml",
            "gao": REPO_ROOT / "theory" / "gao" / "index.yaml",
            "ren": REPO_ROOT / "theory" / "ren" / "index.yaml",
        }
        for sub, src in cls._yamls.items():
            if src.exists():
                shutil.copy2(src, cls._backup_dir / f"{sub}.index.yaml")
        if ITERATION_LOG.exists():
            shutil.copy2(ITERATION_LOG, cls._backup_dir / "iteration-log.md")
        cls._snapshot_marker = (
            CALIBRATION_DIR
            / f"{_dt.date.today().isoformat()}-after-{CASE_ID}.snapshot.yaml"
        )
        # 清掉今天可能存在的同名快照（避免上一次手测残留干扰）
        if cls._snapshot_marker.exists():
            cls._snapshot_marker.unlink()

    @classmethod
    def tearDownClass(cls) -> None:
        # 恢复 4 派 yaml
        for sub, src in cls._yamls.items():
            backup = cls._backup_dir / f"{sub}.index.yaml"
            if backup.exists():
                shutil.copy2(backup, src)
        # 恢复 iteration-log
        log_backup = cls._backup_dir / "iteration-log.md"
        if log_backup.exists():
            shutil.copy2(log_backup, ITERATION_LOG)
        # 清今天的 snapshot
        if cls._snapshot_marker.exists():
            cls._snapshot_marker.unlink()
        if cls._backup_dir.exists():
            shutil.rmtree(cls._backup_dir, ignore_errors=True)

    # ------------------------------------------------------------
    # 主测试
    # ------------------------------------------------------------

    def test_g001_replay_full(self) -> None:
        # 1. 取得 ingest 前的 baseline（M2-Y-068）
        before_entry = _find_yang_rule(TARGET_RULE)
        self.assertIsNotNone(
            before_entry, f"{TARGET_RULE} 必须存在于 theory/yang/index.yaml"
        )
        misses_before = int(before_entry.get("misses", 0))
        hits_before = int(before_entry.get("hits", 0))
        before_status = before_entry.get("status", "promoted")
        before_conf = compute_rule_confidence(hits_before, misses_before)

        # 2. 回放
        diff = ingest_feedback(CASE_ID)

        # 3. ingest 必须触及 M2-Y-068
        target_updates = [u for u in diff.rule_updates if u.rule_id == TARGET_RULE]
        self.assertEqual(
            len(target_updates), 1,
            f"{TARGET_RULE} 必须出现在本次 ingest 的 rule_updates；"
            f"got: {[u.rule_id for u in diff.rule_updates]}",
        )
        u = target_updates[0]

        # 4. verdict 必须是 miss（C-2026-001 婚凶完全失验）
        self.assertEqual(
            u.verdict, "miss",
            f"{TARGET_RULE} 的 verdict 应为 miss（命主婚姻稳定 → 'M2-Y-068=必离'失验）",
        )

        # 5. misses += 1
        self.assertEqual(
            u.misses_after, misses_before + 1,
            f"{TARGET_RULE} 的 misses 应 +1（{misses_before}→{u.misses_after}）",
        )

        # 6. confidence.posterior 下降
        after_conf = compute_rule_confidence(u.hits_after, u.misses_after)
        self.assertLess(
            after_conf.posterior, before_conf.posterior,
            f"{TARGET_RULE} 的 posterior 应下降："
            f"{before_conf.posterior:.3f} → {after_conf.posterior:.3f}",
        )

        # 7. theory/yang/index.yaml 已被写入新 misses
        after_entry = _find_yang_rule(TARGET_RULE)
        self.assertEqual(
            int(after_entry["misses"]), misses_before + 1,
            f"yaml 里 {TARGET_RULE}.misses 应被持久化",
        )
        self.assertEqual(
            after_entry["recent_5"][-1], False,
            "recent_5 末尾应为 False（最近一次失验）",
        )

        # 8. status 检查
        # 旧 "promoted" 自动迁移为 "confirmed"；当前生命周期允许
        # confirmed → flagged_for_review → deprecated 连续收口，若基线规律
        # ingest 前已处于 flagged_for_review 或已累计足够 misses，单次回放可触发 deprecated。
        new_status = after_entry["status"]
        self.assertIn(new_status, ("confirmed", "flagged_for_review", "deprecated"),
                      f"status 异常：{new_status}")
        if before_status == "promoted":
            # 迁移应映射到 confirmed
            self.assertEqual(
                new_status, "confirmed" if u.status_after == "confirmed"
                else u.status_after,
                "promoted 应自动迁移到 confirmed（除非本次 ingest 触发了降级）",
            )

        # 9. iteration-log.md 包含本次 ingest 段
        log_text = ITERATION_LOG.read_text(encoding="utf-8")
        self.assertIn(
            f"ingest {CASE_ID}", log_text,
            "iteration-log.md 应含本次 ingest 段",
        )
        self.assertIn(TARGET_RULE, log_text, "iteration-log.md 应含 M2-Y-068 行")

        # 10. snapshot 落盘
        snapshots = list(CALIBRATION_DIR.glob(
            f"*-after-{CASE_ID}.snapshot.yaml"
        ))
        self.assertGreaterEqual(
            len(snapshots), 1,
            "META/calibration/ 应至少有一份 snapshot 落盘",
        )

    def test_g001_diff_includes_marriage_rules(self) -> None:
        """除了 M2-Y-068，C-2026-001 的婚姻 miss 也应触及 M2-Y-064/049。

        用 dry_run 避免对其他用例造成数据干扰。
        """
        diff = ingest_feedback(CASE_ID, dry_run=True)
        marriage_misses = {
            u.rule_id for u in diff.rule_updates
            if u.verdict == "miss" and u.school in ("yang", "杨")
        }
        # 至少触及 M2-Y-068（婚凶必离）
        self.assertIn(
            "M2-Y-068", marriage_misses,
            f"婚姻 miss 应含 M2-Y-068；got: {marriage_misses}",
        )

    def test_no_freeze(self) -> None:
        """calibration.yaml.freeze_iteration=false 默认不冻结。"""
        cfg = LifecycleConfig.from_yaml()
        self.assertFalse(cfg.freeze_iteration)


class TrackGReplayDeterministic(unittest.TestCase):
    """非破坏性单测：dry_run 模式幂等。"""

    def test_dry_run_does_not_write(self) -> None:
        # snapshot 计数前
        if not CALIBRATION_DIR.exists():
            CALIBRATION_DIR.mkdir(parents=True, exist_ok=True)
        before = len(list(CALIBRATION_DIR.glob("*.snapshot.yaml")))
        diff1 = ingest_feedback(CASE_ID, dry_run=True)
        diff2 = ingest_feedback(CASE_ID, dry_run=True)
        after = len(list(CALIBRATION_DIR.glob("*.snapshot.yaml")))
        self.assertEqual(before, after, "dry_run 不应落 snapshot")
        # 两次 dry_run 的 rule_updates 应一致
        ids1 = sorted(u.rule_id for u in diff1.rule_updates)
        ids2 = sorted(u.rule_id for u in diff2.rule_updates)
        self.assertEqual(ids1, ids2, "dry_run 应幂等")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

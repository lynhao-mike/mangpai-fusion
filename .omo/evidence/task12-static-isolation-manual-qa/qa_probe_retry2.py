from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

from tests.governance.static_isolation_content import governance_yaml_issues
from tests.governance.static_isolation_scanner import (
    GOVERNANCE_OUTWARD_IMPORTS,
    ROOT,
    fact_snapshot_write_issues,
    forbidden_import_issues,
    legacy_shadow_consumer_paths,
    school_view_adapter_paths,
    shadow_runner_consumer_issues,
    system_time_liunian_issues,
)


def row(scenario_id: str, criterion: str, exact_input: str, expected, actual) -> dict:
    return {
        "scenario_id": scenario_id,
        "criterion": criterion,
        "surface": "bounded Python CLI probe",
        "exact_input": exact_input,
        "expected": expected,
        "actual": actual,
        "exit": 0,
        "verdict": "PASS" if actual == expected else "FAIL",
    }


def main() -> int:
    temp = Path(tempfile.mkdtemp(prefix="task12-qa-"))
    rows: list[dict] = []
    try:
        package = temp / "engine" / "governance"
        package.mkdir(parents=True)
        rel_app = package / "bad_application.py"
        rel_infra = package / "bad_infrastructure.py"
        rel_tools = package / "bad_tools.py"
        rel_app.write_text("from ..application import governance_shadow_runner\n", encoding="utf-8")
        rel_infra.write_text("from ..infrastructure import adapters\n", encoding="utf-8")
        rel_tools.write_text("from ...tools import render_report\n", encoding="utf-8")
        rows.append(
            row(
                "S01",
                "relative imports ..application, ..infrastructure, ...tools",
                "forbidden_import_issues((bad_application,bad_infrastructure,bad_tools), GOVERNANCE_OUTWARD_IMPORTS)",
                [
                    "bad_application.py imports engine.application",
                    "bad_infrastructure.py imports engine.infrastructure",
                    "bad_tools.py imports tools",
                ],
                list(forbidden_import_issues((rel_app, rel_infra, rel_tools), GOVERNANCE_OUTWARD_IMPORTS)),
            )
        )

        required_entrypoints = {
            "tools/output_linter.py",
            "tools/domain_analysis_cli.py",
            "tools/batch_review.py",
            "tools/promote_expert_weight_feedback.py",
            "tools/domain_feedback.py",
        }
        discovered = {path.relative_to(ROOT).as_posix() for path in legacy_shadow_consumer_paths()}
        rows.append(
            row(
                "S02",
                "active report/feedback entrypoints are covered and clean",
                "legacy_shadow_consumer_paths(); shadow_runner_consumer_issues(paths)",
                {"required_present": True, "issues": []},
                {
                    "required_present": required_entrypoints <= discovered,
                    "issues": list(shadow_runner_consumer_issues(legacy_shadow_consumer_paths())),
                },
            )
        )

        fact_direct = temp / "bad_fact_direct.py"
        fact_alias = temp / "bad_fact_alias.py"
        fact_direct.write_text(
            "from engine.governance.contracts import FactSnapshot\n"
            "def adapt(x):\n"
            "    return FactSnapshot(x)\n",
            encoding="utf-8",
        )
        fact_alias.write_text(
            "from engine.governance import build_fact_snapshot as make_snapshot\n"
            "from engine.governance.contracts import FactSnapshot as Snapshot\n"
            "def adapt(x):\n"
            "    make_snapshot(x)\n"
            "    return Snapshot(x)\n",
            encoding="utf-8",
        )
        future_root = temp / "future"
        future_app = future_root / "engine" / "application"
        future_app.mkdir(parents=True)
        future_adapter = future_app / "governance_future_school_view_adapter.py"
        future_adapter.write_text("", encoding="utf-8")
        rows.append(
            row(
                "S03",
                "FactSnapshot direct and alias builders/constructors plus future adapter discovery",
                "fact_snapshot_write_issues((bad_fact_direct,bad_fact_alias)); school_view_adapter_paths(future_root)",
                {
                    "issues": [
                        "bad_fact_direct.py calls FactSnapshot",
                        "bad_fact_alias.py calls build_fact_snapshot",
                        "bad_fact_alias.py calls FactSnapshot",
                    ],
                    "future": ["governance_future_school_view_adapter.py"],
                },
                {
                    "issues": list(fact_snapshot_write_issues((fact_direct, fact_alias))),
                    "future": [path.name for path in school_view_adapter_paths(future_root)],
                },
            )
        )

        dt_direct = temp / "bad_datetime_direct_liunian.py"
        dt_alias = temp / "bad_datetime_alias_liunian.py"
        date_alias = temp / "bad_date_alias_liunian.py"
        time_direct = temp / "bad_time_direct_liunian.py"
        time_alias = temp / "bad_time_alias_liunian.py"
        dt_direct.write_text("from datetime import datetime\nliunian = datetime.now()\n", encoding="utf-8")
        dt_alias.write_text("from datetime import datetime as dt\nliunian = dt.now()\n", encoding="utf-8")
        date_alias.write_text("from datetime import date as d\nliunian = d.today()\n", encoding="utf-8")
        time_direct.write_text("import time\nliunian = time.time()\n", encoding="utf-8")
        time_alias.write_text("from time import time as now\nliunian = now()\n", encoding="utf-8")
        time_paths = (dt_direct, dt_alias, date_alias, time_direct, time_alias)
        rows.append(
            row(
                "S04",
                "datetime/date/time direct and alias forms including dt.now() and now()",
                "system_time_liunian_issues((datetime.now, dt.now, d.today, time.time, now))",
                [
                    f"{path.name} reads system time while mentioning liunian"
                    for path in time_paths
                ],
                list(system_time_liunian_issues(time_paths)),
            )
        )

        paths_yaml = temp / "bad_paths.yaml"
        paths_yaml.write_text(
            "drive: F:\\cases\\x.json\n"
            "unc: '\\\\server\\share\\case.json'\n"
            "unix: /opt/project/case.json\n",
            encoding="utf-8",
        )
        rows.append(
            row(
                "S05",
                "YAML drive, UNC, and /opt absolute paths",
                "governance_yaml_issues(bad_paths.yaml)",
                [
                    "bad_paths.yaml contains absolute path F:\\cases\\x.json",
                    "bad_paths.yaml contains absolute path \\\\server\\share\\case.json",
                    "bad_paths.yaml contains absolute path /opt/project/case.json",
                ],
                list(governance_yaml_issues(paths_yaml)),
            )
        )

        benign_py = temp / "benign_governance.py"
        benign_py.write_text(
            "from engine.governance.contracts import FactSnapshot\n"
            "def read(snapshot: FactSnapshot):\n"
            "    return snapshot\n",
            encoding="utf-8",
        )
        benign_yaml = temp / "benign.yaml"
        benign_yaml.write_text(
            "school: ziping\npath_hint: relative/config.yaml\nlabel: neutral\n",
            encoding="utf-8",
        )
        rows.append(
            row(
                "S06",
                "benign controls avoid false positives",
                "fact_snapshot_write_issues(read-only annotation); governance_yaml_issues(relative yaml); system_time_liunian_issues(no liunian clock)",
                {"fact": [], "yaml": [], "time": []},
                {
                    "fact": list(fact_snapshot_write_issues((benign_py,))),
                    "yaml": list(governance_yaml_issues(benign_yaml)),
                    "time": list(system_time_liunian_issues((benign_py,))),
                },
            )
        )

        malformed_py = temp / "malformed.py"
        malformed_yaml = temp / "malformed.yaml"
        malformed_py.write_text("def broken(:\n", encoding="utf-8")
        malformed_yaml.write_text("x: [unterminated\n", encoding="utf-8")
        actual = {}
        for key, action in (
            ("python", lambda: fact_snapshot_write_issues((malformed_py,))),
            ("yaml", lambda: governance_yaml_issues(malformed_yaml)),
        ):
            try:
                action()
                actual[key] = "NO_ERROR"
            except Exception as exc:  # noqa: BLE001 - QA records fail-closed exception class.
                actual[key] = type(exc).__name__
        rows.append(
            row(
                "S07",
                "malformed input fails closed",
                "fact_snapshot_write_issues(malformed.py); governance_yaml_issues(malformed.yaml)",
                {"python": "SyntaxError", "yaml": "ParserError"},
                actual,
            )
        )
    finally:
        removed = False
        if temp.exists():
            shutil.rmtree(temp)
            removed = not temp.exists()

    result = {
        "verdict": "PASS" if all(item["verdict"] == "PASS" for item in rows) else "FAIL",
        "scenario_count": len(rows),
        "rows": rows,
        "cleanup": {"temp_dir": str(temp), "removed": removed},
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

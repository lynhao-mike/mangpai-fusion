"""基础设施层 findings 仓储：负责把结构化输出落盘到 cases/*/findings。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional, Union

from engine.domain.analysis import AnalysisOutput

def _save_findings(
    output: "AnalysisOutput",
    *,
    cases_dir: Optional[Union[str, Path]] = None,
) -> Path:
    """把 D1-D4 + AnalysisOutput 落盘到 cases/C-XXX/findings/。

    与 ``tools/render_report.save_findings`` 等价的轻量副本——独立放在 engine
    层，避免 engine→tools 的分层倒置（pipeline.py 不允许 import tools.*）。

    写入文件：
        - energy.json
        - picture.json
        - gate_results.json
        - support.json
        - analysis_output.json

    Returns:
        findings/ 目录路径。
    """
    if cases_dir is None:
        cases_dir = Path(__file__).resolve().parents[2] / "cases"
    cases_root = Path(cases_dir)

    case_id = (output.case_id or "UNKNOWN").strip() or "UNKNOWN"
    findings_dir = cases_root / case_id / "findings"
    findings_dir.mkdir(parents=True, exist_ok=True)

    def _dump(obj: Any) -> str:
        if obj is None:
            return "null"
        if hasattr(obj, "to_json"):
            return obj.to_json(indent=2)
        if hasattr(obj, "to_dict"):
            return json.dumps(obj.to_dict(), ensure_ascii=False, indent=2)
        if isinstance(obj, list):
            return json.dumps(
                [(x.to_dict() if hasattr(x, "to_dict") else x) for x in obj],
                ensure_ascii=False,
                indent=2,
            )
        return json.dumps(obj, ensure_ascii=False, indent=2)

    (findings_dir / "energy.json").write_text(
        _dump(output.energy), encoding="utf-8")
    (findings_dir / "picture.json").write_text(
        _dump(output.picture), encoding="utf-8")
    (findings_dir / "gate_results.json").write_text(
        _dump(output.gate_results), encoding="utf-8")
    (findings_dir / "support.json").write_text(
        _dump(output.support), encoding="utf-8")
    (findings_dir / "analysis_output.json").write_text(
        _dump(output), encoding="utf-8")

    return findings_dir

save_findings = _save_findings

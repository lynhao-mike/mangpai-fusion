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
    """只落盘最终结论摘要。D1-D4 已在 analysis_output 内，不再各写一份。

    ponytail: 命盘事实与检索候选不进落盘；要完整追溯时读内存对象。
    写入文件：
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

    (findings_dir / "analysis_output.json").write_text(
        _dump(output), encoding="utf-8")

    return findings_dir

save_findings = _save_findings

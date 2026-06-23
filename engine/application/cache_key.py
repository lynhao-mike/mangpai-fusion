"""缓存键计算的纯应用服务。

把生产服务里的缓存键派生逻辑抽离为无副作用的纯函数，便于复用与单测，
并降低 [`ProductionAnalysisService`](engine/application/production_service.py) 的职责密度。

该模块只依赖 domain/版本常量与标准库，不触碰 IO、store 或 tools。
"""

from __future__ import annotations

import hashlib
import json

from engine import FINDINGS_SCHEMA_VERSION, PIPELINE_SCHEMA_VERSION, __version__

DEFAULT_TEMPLATE_NAME = "report-v5.md"


def compute_cache_key(
    *,
    input_sha256: str,
    render: bool,
    template_name: str,
    render_v6_preprod: bool = False,
) -> str:
    """根据输入指纹与渲染选项派生稳定缓存键。

    与历史实现完全等价：对包含引擎/契约版本、输入 sha256、render 与模板名的
    payload 做 sort_keys JSON 序列化后取 sha256，返回 64 位十六进制串。
    """
    payload = {
        "engine_version": __version__,
        "findings_schema_version": FINDINGS_SCHEMA_VERSION,
        "pipeline_schema_version": PIPELINE_SCHEMA_VERSION,
        "input_sha256": input_sha256,
        "render": bool(render),
        "template_name": template_name or DEFAULT_TEMPLATE_NAME,
        "render_v6_preprod": bool(render_v6_preprod),
    }
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()

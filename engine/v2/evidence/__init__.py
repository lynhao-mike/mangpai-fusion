"""V2 Evidence Builder 与适配器包。"""

from __future__ import annotations

from engine.v2.evidence.adapters import build_school_evidences
from engine.v2.evidence.builder import build_domain_evidences

__all__ = ["build_domain_evidences", "build_school_evidences"]

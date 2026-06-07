"""V2 领域模型包。"""

from __future__ import annotations

from engine.v2.domain.agents import DomainReasoningResult
from engine.v2.domain.evidence import DomainEvidence, SchoolEvidence
from engine.v2.domain.events import EventCandidate
from engine.v2.domain.output import V2AnalysisOutput
from engine.v2.domain.similarity import SimilarCase, SimilarCaseProfile

__all__ = [
    "DomainEvidence",
    "DomainReasoningResult",
    "EventCandidate",
    "SchoolEvidence",
    "SimilarCase",
    "SimilarCaseProfile",
    "V2AnalysisOutput",
]

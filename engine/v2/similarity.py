"""V2 案例相似度引擎。"""

from __future__ import annotations

from pathlib import Path

from engine.v2.domain.evidence import DomainEvidence
from engine.v2.domain.events import EventCandidate
from engine.v2.domain.similarity import SimilarCase, SimilarCaseProfile

DEFAULT_CASES_DIR = Path(__file__).resolve().parents[2] / "cases"


def find_similar_cases(
    *,
    case_id: str,
    domain_evidences: list[DomainEvidence],
    event_candidates: list[EventCandidate],
    corpus: list[SimilarCaseProfile] | None = None,
    cases_dir: str | Path | None = None,
    limit: int = 5,
) -> list[SimilarCase]:
    """基于领域、事件类型、标签和 case_id 干支重合度排序相似案例。"""
    profiles = corpus if corpus is not None else load_case_profiles(cases_dir=cases_dir)
    query = SimilarCaseProfile(
        case_id=case_id,
        domains=[item.domain for item in domain_evidences],
        event_types=[item.event_type for item in event_candidates],
        tags=[tag for event in event_candidates for tag in event.tags],
    )
    results = [_score_profile(query, profile) for profile in profiles if profile.case_id != case_id]
    ranked = sorted((item for item in results if item.score > 0), key=lambda item: (-item.score, item.case_id))
    return ranked[: max(limit, 0)]


def load_case_profiles(*, cases_dir: str | Path | None = None) -> list[SimilarCaseProfile]:
    """从 cases 目录读取轻量案例画像。"""
    root = Path(cases_dir) if cases_dir is not None else DEFAULT_CASES_DIR
    if not root.exists():
        return []
    profiles: list[SimilarCaseProfile] = []
    for path in sorted(root.iterdir()):
        if not path.is_dir() or not path.name.startswith("C-"):
            continue
        tags = _case_id_tokens(path.name)
        profiles.append(
            SimilarCaseProfile(
                case_id=path.name,
                tags=tags,
                metadata={"source": "cases_dir", "has_feedback": (path / "feedback.md").exists()},
            )
        )
    return profiles


def _score_profile(query: SimilarCaseProfile, profile: SimilarCaseProfile) -> SimilarCase:
    matched_domains = _intersection(query.domains, profile.domains)
    matched_event_types = _intersection(query.event_types, profile.event_types)
    query_tags = set(query.tags) | set(_case_id_tokens(query.case_id))
    profile_tags = set(profile.tags) | set(_case_id_tokens(profile.case_id))
    matched_tags = sorted(query_tags & profile_tags)

    score = 0.0
    score += 0.45 * _jaccard(query.domains, profile.domains)
    score += 0.35 * _jaccard(query.event_types, profile.event_types)
    score += 0.20 * _jaccard(sorted(query_tags), sorted(profile_tags))
    score = round(score, 4)

    reasons: list[str] = []
    if matched_domains:
        reasons.append(f"领域重合：{', '.join(matched_domains)}")
    if matched_event_types:
        reasons.append(f"事件类型重合：{', '.join(matched_event_types)}")
    if matched_tags:
        reasons.append(f"标签/干支重合：{', '.join(matched_tags[:8])}")

    return SimilarCase(
        case_id=profile.case_id,
        score=score,
        matched_domains=matched_domains,
        matched_event_types=matched_event_types,
        matched_tags=matched_tags,
        reasons=reasons,
        metadata=dict(profile.metadata),
    )


def _intersection(left: list[str], right: list[str]) -> list[str]:
    return sorted(set(left) & set(right))


def _jaccard(left: list[str], right: list[str]) -> float:
    lset = set(left)
    rset = set(right)
    if not lset or not rset:
        return 0.0
    return len(lset & rset) / len(lset | rset)


def _case_id_tokens(case_id: str) -> list[str]:
    parts = case_id.split("-")
    tokens: list[str] = []
    if len(parts) >= 4:
        tokens.append(parts[-2])
    suffix = parts[-1] if parts else ""
    if len(suffix) == 8:
        tokens.extend(suffix[index : index + 2] for index in range(0, 8, 2))
        tokens.extend(suffix[index] for index in range(8))
    return tokens

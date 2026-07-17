from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import Enum
from typing import Any

from engine.decision.models import ChartFactLedger, EventHypothesis
from engine.decision.ren_timing_rules import RenTimingRule, load_ren_timing_rules
from engine.features import ChartFeatureVector
from engine.predicates.relations import zhi_chong, zhi_chuan, zhi_liuhe, zhi_xing

_BRANCHES = frozenset("子丑寅卯辰巳午未申酉戌亥")


class RenTimingState(str, Enum):
    TIMING_READY = "timing-ready"
    INSUFFICIENT_TRIGGER = "insufficient-trigger"
    ABSTAIN = "abstain"
    UNSUPPORTED = "unsupported"


class PublicationState(str, Enum):
    EMIT = "emit"
    HOLD = "hold"
    ABSTAIN = "abstain"
    UNSUPPORTED = "unsupported"


@dataclass(frozen=True, slots=True)
class TriggerAtom:
    atom_id: str
    relation: str
    year: int
    liunian_ref: str
    target_ref: str
    target_kind: str
    left_branch: str
    right_branch: str
    rule_id: str
    source_ref: str
    priority: int
    confidence: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "atom_id": self.atom_id,
            "relation": self.relation,
            "year": self.year,
            "liunian_ref": self._normalized_liunian_ref(),
            "target_ref": self._normalized_target_ref(),
            "target_kind": self.target_kind,
            "left_branch": self.left_branch,
            "right_branch": self.right_branch,
            "rule_id": self.rule_id,
            "source_ref": self.source_ref,
            "priority": self.priority,
            "confidence": self.confidence,
        }

    def _normalized_liunian_ref(self) -> str:
        return f"liunian_steps[year={self.year},branch={self.left_branch}]"

    def _normalized_target_ref(self) -> str:
        if self.target_kind == "dayun":
            return f"{self._normalized_liunian_ref()}.dayun[branch={self.right_branch}]"
        return self.target_ref


@dataclass(frozen=True, slots=True)
class EvidenceFamily:
    family_key: str
    atoms: tuple[TriggerAtom, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "family_key": self.family_key,
            "atoms": [atom.to_dict() for atom in self.atoms],
        }


@dataclass(frozen=True, slots=True)
class RenTimingResult:
    task_id: str
    event_id: str
    local_state: RenTimingState
    publication_state: PublicationState
    evidence_families: tuple[EvidenceFamily, ...] = ()
    selected_family_key: str = ""
    input_blockers: tuple[str, ...] = ()
    failed_gates: tuple[str, ...] = ()
    routing_blockers: tuple[str, ...] = ()
    diagnostic_reasons: tuple[str, ...] = ()
    remediation: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "event_id": self.event_id,
            "local_state": self.local_state.value,
            "publication_state": self.publication_state.value,
            "evidence_families": [family.to_dict() for family in self.evidence_families],
            "selected_family_key": self.selected_family_key,
            "input_blockers": list(self.input_blockers),
            "failed_gates": list(self.failed_gates),
            "routing_blockers": list(self.routing_blockers),
            "diagnostic_reasons": list(self.diagnostic_reasons),
            "remediation": self.remediation,
        }


def _relation(left: str, right: str) -> str | None:
    if left not in _BRANCHES or right not in _BRANCHES:
        return None
    if zhi_chong(left, right):
        return "冲"
    if zhi_xing(left, right) is not None:
        return "刑"
    if zhi_chuan(left, right):
        return "穿"
    if left == right:
        return "伏吟"
    if zhi_liuhe(left, right) is not None or frozenset((left, right)) == frozenset(("午", "未")):
        return "合"
    return None


def _stable_id(*parts: object) -> str:
    raw = "|".join(str(part) for part in parts)
    return "ren-atom-" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:20]


def _ganzhi(value: object) -> str:
    text = str(value or "").strip()
    return text if len(text) == 2 and text[1] in _BRANCHES else ""


def _year(step: dict[str, Any]) -> int | None:
    value = step.get("year", step.get("年份"))
    return value if type(value) is int else None


def _family_key(year: int, relation: str, left: str, right: str, target_kind: str) -> str:
    return f"{year}:{relation}:{''.join(sorted((left, right)))}:{target_kind}"


def _extract_atoms(
    chart: ChartFactLedger, rules: tuple[RenTimingRule, ...]
) -> tuple[TriggerAtom, ...]:
    by_relation = {rule.relation: rule for rule in rules}
    atoms: dict[str, TriggerAtom] = {}

    for index, step in enumerate(chart.liunian_steps):
        year = _year(step)
        annual = _ganzhi(step.get("ganzhi") or step.get("干支") or step.get("liunian"))
        if year is None or not annual:
            continue
        left = annual[1]
        targets = [
            ("pillar", f"four_pillars.{name}", f"pillar:{name}", _ganzhi(value))
            for name, value in chart.four_pillars.items()
        ]
        dayun = _ganzhi(step.get("dayun") or step.get("大运"))
        if dayun:
            targets.append(
                (
                    "dayun",
                    f"liunian_steps.{index}.dayun",
                    f"dayun:{dayun}",
                    dayun,
                )
            )

        for target_kind, target_ref, target_identity, target in targets:
            if not target:
                continue
            right = target[1]
            relation = _relation(left, right)
            rule = by_relation.get(relation or "")
            if rule is None:
                continue
            family_key = _family_key(year, relation, left, right, target_kind)
            atom_id = _stable_id(family_key, target_identity, rule.rule_id)
            atoms[atom_id] = TriggerAtom(
                atom_id=atom_id,
                relation=relation,
                year=year,
                liunian_ref=f"liunian_steps.{index}",
                target_ref=target_ref,
                target_kind=target_kind,
                left_branch=left,
                right_branch=right,
                rule_id=rule.rule_id,
                source_ref=f"{rule.source_path}#{rule.source_anchor}",
                priority=rule.priority,
                confidence=rule.confidence,
            )

    return tuple(sorted(atoms.values(), key=lambda atom: (atom.year, atom.priority, atom.atom_id)))


def _reduce_families(atoms: tuple[TriggerAtom, ...]) -> tuple[EvidenceFamily, ...]:
    grouped: dict[str, dict[str, TriggerAtom]] = {}
    for atom in atoms:
        key = _family_key(
            atom.year,
            atom.relation,
            atom.left_branch,
            atom.right_branch,
            atom.target_kind,
        )
        grouped.setdefault(key, {})[atom.atom_id] = atom
    return tuple(
        EvidenceFamily(
            family_key=key,
            atoms=tuple(sorted(grouped[key].values(), key=lambda atom: atom.atom_id)),
        )
        for key in sorted(grouped)
    )


def discriminate_ren_career_timing(
    chart: ChartFactLedger,
    features: ChartFeatureVector,
    event: EventHypothesis | None,
    *,
    task_id: str = "career.role_change",
) -> RenTimingResult:
    del features  # Task 4 accepts the CFV contract but only extracts ledger relations.
    event_id = event.event_id if event else ""
    if task_id != "career.role_change":
        return RenTimingResult(
            task_id,
            event_id,
            RenTimingState.UNSUPPORTED,
            PublicationState.UNSUPPORTED,
        )
    if event is None or event.event_type != "career.role_change" or not event.event_id:
        return RenTimingResult(
            task_id,
            event_id,
            RenTimingState.ABSTAIN,
            PublicationState.ABSTAIN,
            routing_blockers=("qualified_career_event_required",),
            remediation="提供已通过事件资格且可追踪的 career.role_change 事件。",
        )

    blockers: list[str] = []
    if len(chart.four_pillars) != 4:
        blockers.append("complete_four_pillars_required")
    if not chart.dayun_steps:
        blockers.append("dayun_required")
    if not chart.liunian_steps:
        blockers.append("liunian_required")
    if blockers:
        return RenTimingResult(
            task_id,
            event.event_id,
            RenTimingState.ABSTAIN,
            PublicationState.ABSTAIN,
            input_blockers=tuple(blockers),
            remediation="补齐合法四柱、大运与候选流年事实。",
        )

    families = _reduce_families(_extract_atoms(chart, load_ren_timing_rules()))
    return RenTimingResult(
        task_id,
        event.event_id,
        RenTimingState.INSUFFICIENT_TRIGGER,
        PublicationState.HOLD,
        evidence_families=families,
        failed_gates=("timing_gate_not_evaluated",),
    )

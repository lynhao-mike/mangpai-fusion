from __future__ import annotations

import ast
import hashlib
from pathlib import Path

import pytest

from engine.decision import l3_structure, v5_adapter
from engine.decision.l3_structure import build_structural_verdicts
from engine.decision.models import SchoolClaim, StructuralVerdict


def _claim(
    claim_id: str,
    statement: str,
    metadata: dict | None = None,
    *,
    claim_type: str = "structure_claim",
    confidence: float = 0.6,
) -> SchoolClaim:
    return SchoolClaim(
        claim_id=claim_id,
        school="ziping",
        role_granted_by_l1="lead",
        domain="事业",
        claim_type=claim_type,
        statement=statement,
        confidence=confidence,
        metadata=metadata or {},
    )


def test_l3_consumes_geju_direction_from_l2_without_recomputing_it() -> None:
    claims = [
        _claim(
            "profile",
            "格局大类裁决：正格",
            {
                "geju_type": "正格",
                "favor_shishen": ["食神"],
                "avoid_shishen": ["正印"],
            },
        ),
        _claim("bad", "正印当权主事业上升"),
    ]

    verdicts = {
        item.claim_id: item
        for item in build_structural_verdicts("C-R10", claims)
    }

    assert verdicts["bad"].verdict == "weaken"
    assert "正印" in verdicts["bad"].structural_reason
    assert "正格" in verdicts["bad"].structural_reason


def test_l3_without_l2_geju_metadata_does_not_invent_favor_or_avoid() -> None:
    claim = _claim("plain", "正印当权主事业上升", {})

    verdict = build_structural_verdicts("C-R10", [claim])[0]

    assert verdict.verdict == "pass"
    assert "忌神" not in verdict.structural_reason
    assert "用神" not in verdict.structural_reason


def test_adapter_profile_alias_is_exact_l3_function() -> None:
    assert v5_adapter._extract_geju_profile is l3_structure.extract_geju_profile


def test_adapter_verdicts_is_pure_delegation(monkeypatch: pytest.MonkeyPatch) -> None:
    claims = [_claim("delegated", "食神生财")]
    sentinel = [
        StructuralVerdict(
            verdict_id="mutation-sentinel",
            claim_id="delegated",
            verdict="unknown",
            structural_reason="由测试替身返回",
        )
    ]
    calls: list[tuple[str, list[SchoolClaim]]] = []

    def fake_builder(case_id: str, received: list[SchoolClaim]) -> list[StructuralVerdict]:
        calls.append((case_id, received))
        return sentinel

    monkeypatch.setattr(v5_adapter, "build_structural_verdicts", fake_builder)

    assert v5_adapter._verdicts("C-DELEGATE", claims) is sentinel
    assert calls == [("C-DELEGATE", claims)]


@pytest.mark.parametrize(
    ("claim_type", "confidence", "expected"),
    [
        ("structure", 0.1, "reject"),
        ("structure", 0.4, "weaken"),
        ("structure", 0.5, "pass"),
        ("structure_claim", 0.1, "weaken"),
        ("structure_claim", 0.4, "pass"),
        ("structure_claim", 0.5, "pass"),
        ("event", 0.1, "reject"),
        ("event", 0.4, "unknown"),
        ("event", 0.5, "unknown"),
        ("event_claim", 0.1, "weaken"),
        ("event_claim", 0.4, "weaken"),
        ("event_claim", 0.5, "weaken"),
    ],
)
def test_l3_claim_type_threshold_compatibility(
    claim_type: str, confidence: float, expected: str
) -> None:
    claim = _claim(
        f"{claim_type}-{confidence}",
        "不含格局用忌的固定命题",
        claim_type=claim_type,
        confidence=confidence,
    )

    assert build_structural_verdicts("C-BOUNDARY", [claim])[0].verdict == expected


def test_fixed_verdict_id_and_adapter_match_direct_l3() -> None:
    claim = _claim("fixed-claim", "食神生财", confidence=0.5)
    expected_id = "dsv-" + hashlib.sha256(
        "C-FIXED|fixed-claim".encode("utf-8")
    ).hexdigest()[:12]

    direct = l3_structure.build_structural_verdicts("C-FIXED", [claim])
    adapted = v5_adapter._verdicts("C-FIXED", [claim])

    assert expected_id == "dsv-f627b1616169"
    assert direct[0].verdict_id == expected_id
    assert adapted == direct


def test_l3_import_gate_excludes_v5_runner_and_theory() -> None:
    source_path = Path(l3_structure.__file__)
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    imported_modules = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        node.module or ""
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    }

    forbidden = ("engine.v5", "runner", "theory")
    assert not {
        module
        for module in imported_modules
        if any(part in module for part in forbidden)
    }


@pytest.mark.parametrize(
    "fake_metadata",
    [
        {"geju": "正格", "favor_shishen": ["食神"], "avoid_shishen": ["正印"]},
        {"geju_type": "", "favor_shishen": ["食神"], "avoid_shishen": ["正印"]},
        {"geju_type_hint": "正格", "favor": ["食神"], "avoid": ["正印"]},
        {"structure_type": "正格", "useful_gods": ["食神"], "taboo_gods": ["正印"]},
    ],
)
def test_geju_profile_rejects_pseudo_fields(fake_metadata: dict[str, object]) -> None:
    assert l3_structure.extract_geju_profile(
        [_claim("fake-profile", "正印当权", fake_metadata)]
    ) is None


def test_geju_profile_reads_only_canonical_fields() -> None:
    profile = l3_structure.extract_geju_profile(
        [
            _claim(
                "canonical-profile",
                "格局大类裁决：正格",
                {
                    "geju_type": "正格",
                    "favor_shishen": ["食神"],
                    "avoid_shishen": ["正印"],
                    "favor": ["七杀"],
                    "avoid": ["正官"],
                },
            )
        ]
    )

    assert profile == {"geju_type": "正格", "favor": {"食神"}, "avoid": {"正印"}}

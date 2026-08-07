from __future__ import annotations

import ast
import importlib
import json
import subprocess
import sys
from dataclasses import replace
from pathlib import Path
from types import ModuleType
from typing import Any, cast

import pytest

from engine.application.governance_claim_adapter_values import AdaptationResult
from engine.decision.yang_marriage import (
    YangMarriageDiscrimination,
    YangMarriageFamilyEvidence,
)
from engine.governance import (
    AdapterProvenance,
    ClaimEvidenceGrade,
    ClaimIssueCode,
    ClaimKind,
    ClaimReferenceCategory,
    ClaimStance,
    GovernanceClaimContractError,
    GovernanceReferenceCatalog,
    ReferenceRegistration,
    TemporalLayer,
    stable_object_id,
)
from engine.governance.governance_claim_derivation import derivation_chain_digest

SOURCE_VERSION = (
    "sha256:e8be77f67246ff056770a35d618b4b3fc5694ba5fdec2f65c8d674708355e768"
)
SOURCE_REFS = (
    "theory/yang/index.yaml#M2-Y-068",
    "theory/yang/index.yaml#M2-Y-088",
)
CONCLUSION = (
    "杨派原局夫妻宫事件锚与独立配偶结构交互同向，"
    "支持存在离婚或再婚事件风险，但不作必然判断。"
)
MODULE_NAME = "engine.application.governance_yang_marriage_adapter"
MODULE_PATH = Path("engine/application/governance_yang_marriage_adapter.py")


def _adapter_module() -> ModuleType:
    return importlib.import_module(MODULE_NAME)


def _family(
    key: str,
    *,
    detail: str = "合成审计证据",
    canonical_pairs: tuple[tuple[str, str], ...] | None = None,
) -> YangMarriageFamilyEvidence:
    pairs = (
        (("午", "子"),)
        if canonical_pairs is None and key == "spouse_palace_event_anchor"
        else canonical_pairs or ()
    )
    return YangMarriageFamilyEvidence(
        family_key=cast(Any, key),
        matched=True,
        fact_refs=("four_pillars.day",),
        feature_refs=("chong_pairs",),
        canonical_pairs=pairs,
        reason_codes=(f"matched_{key}",),
        detail=detail,
    )


def _result(
    state: str = "event",
    *,
    sex_basis: str = "male_wealth",
    source_rule_refs: tuple[str, ...] = SOURCE_REFS,
    schema_version: str = "yang-marriage-discrimination/v1",
    case_id: str = "YM-W2-C1",
    family_detail: str = "合成审计证据",
    falsifier: str = "若独立复核未见离婚或再婚事件，则本判断被证伪。",
    anchor_pairs: tuple[tuple[str, str], ...] | None = None,
) -> YangMarriageDiscrimination:
    if state == "event":
        interaction = (
            "spouse_star_peer_interaction"
            if sex_basis == "male_wealth"
            else "spouse_star_output_interaction"
        )
        families = (
            _family(
                "spouse_palace_event_anchor",
                detail=family_detail,
                canonical_pairs=anchor_pairs,
            ),
            _family(interaction, detail=family_detail),
        )
        anchor_passed = True
        interaction_passed = True
        blockers: tuple[str, ...] = ()
        palace = "子"
    elif state == "pressure":
        families = (_family("spouse_palace_event_anchor", detail=family_detail),)
        anchor_passed = True
        interaction_passed = False
        blockers = ("missing_independent_spouse_interaction",)
        palace = "子"
    else:
        families = ()
        anchor_passed = False
        interaction_passed = False
        blockers = ("missing_or_unknown_sex", "incomplete_evidence")
        sex_basis = "unknown"
        palace = ""
    return YangMarriageDiscrimination(
        schema_version=schema_version,
        case_id=case_id,
        state=cast(Any, state),
        sex_basis=cast(Any, sex_basis),
        spouse_palace_branch=palace,
        families=families,
        event_anchor_passed=anchor_passed,
        independent_spouse_interaction_passed=interaction_passed,
        blocking_reason_codes=blockers,
        falsifier=falsifier,
        source_rule_refs=source_rule_refs,
    )


def _catalog(
    *,
    refs: tuple[str, ...] = SOURCE_REFS,
    version: str = SOURCE_VERSION,
) -> GovernanceReferenceCatalog:
    return GovernanceReferenceCatalog(
        tuple(
            ReferenceRegistration(ClaimReferenceCategory.SOURCE_RULE, ref, version)
            for ref in refs
        )
    )


def _adapt(
    result: object,
    catalog: GovernanceReferenceCatalog,
) -> AdaptationResult:
    function = _adapter_module().adapt_yang_marriage_discrimination
    return function(result, catalog)


@pytest.mark.parametrize("sex_basis", ("male_wealth", "female_official"))
def test_event_builds_exact_conservative_typed_claim(sex_basis: str) -> None:
    result = _result(sex_basis=sex_basis)

    adapted = _adapt(result, _catalog())

    assert adapted.issues == ()
    assert adapted.claim is not None
    claim = adapted.claim
    spec = claim.specification
    assert claim.school_id == "yang_qingjuan"
    assert claim.task_id == "marriage.divorce_or_remarriage"
    assert claim.claim_kind is ClaimKind.EVENT
    assert claim.stance is ClaimStance.SUPPORT
    assert claim.temporal_scope.layer is TemporalLayer.NATAL
    assert spec.conclusion == CONCLUSION
    assert claim.confidence == 0.60
    assert claim.evidence_grade is ClaimEvidenceGrade.INFERENTIAL
    assert claim.falsifier == result.falsifier
    assert claim.public_fact_refs == ()
    assert claim.certified_fact_refs == ()
    assert claim.school_reason_refs == ()
    assert claim.blockers == ()
    assert claim.counterevidence == ()
    assert tuple(ref.reference_id for ref in claim.source_rule_refs) == SOURCE_REFS
    assert all(
        ref.category is ClaimReferenceCategory.SOURCE_RULE
        and ref.version == SOURCE_VERSION
        for ref in claim.source_rule_refs
    )
    assert claim.adapter_provenance is not None
    assert claim.adapter_provenance.adapter_id == "yang_marriage_discrimination"
    assert claim.adapter_provenance.adapter_version == "yang-marriage-discrimination/v1"
    assert claim.adapter_provenance.source_claim_ref == str(
        stable_object_id("yang_marriage_discrimination", result.to_dict())
    )


@pytest.mark.parametrize(
    ("state", "refs", "catalog"),
    (
        ("pressure", SOURCE_REFS, _catalog()),
        ("pressure", ("altered",), _catalog(refs=())),
        ("pressure", (), _catalog(version="wrong")),
        ("abstain", SOURCE_REFS, _catalog()),
        ("abstain", ("altered",), _catalog(refs=())),
        ("abstain", (), _catalog(version="wrong")),
    ),
)
def test_non_event_state_precedes_reference_and_catalog_validation(
    state: str,
    refs: tuple[str, ...],
    catalog: GovernanceReferenceCatalog,
) -> None:
    result = _result(state, source_rule_refs=refs)

    adapted = _adapt(result, catalog)

    assert adapted.claim is None
    assert len(adapted.issues) == 1
    assert adapted.issues[0].code is ClaimIssueCode.INSUFFICIENT_EVIDENCE
    assert state in adapted.issues[0].detail
    if state == "abstain":
        assert all(code in adapted.issues[0].detail for code in result.blocking_reason_codes)


def test_wrong_concrete_type_is_a_typed_loss() -> None:
    class Lookalike:
        state = "event"
        source_rule_refs = SOURCE_REFS

    adapted = _adapt(Lookalike(), _catalog())

    assert adapted.claim is None
    assert len(adapted.issues) == 1
    assert adapted.issues[0].code is ClaimIssueCode.ADAPTER_INPUT_INVALID


@pytest.mark.parametrize(
    ("refs", "catalog"),
    (
        ((), _catalog(refs=())),
        ((SOURCE_REFS[0],), _catalog(version="wrong")),
        (
            SOURCE_REFS + ("theory/yang/index.yaml#M2-Y-999",),
            _catalog(refs=()),
        ),
        (
            (SOURCE_REFS[0], "theory/yang/index.yaml#M2-Y-999"),
            _catalog(version="wrong"),
        ),
    ),
)
def test_event_requires_exact_source_anchor_tuple_before_catalog(
    refs: tuple[str, ...],
    catalog: GovernanceReferenceCatalog,
) -> None:
    adapted = _adapt(_result(source_rule_refs=refs), catalog)

    assert adapted.claim is None
    assert len(adapted.issues) == 1
    assert adapted.issues[0].code is ClaimIssueCode.LEGACY_REFERENCE_INVALID


@pytest.mark.parametrize(
    "catalog",
    (
        _catalog(refs=()),
        _catalog(refs=(SOURCE_REFS[0],)),
        _catalog(refs=(SOURCE_REFS[1],)),
        GovernanceReferenceCatalog((
            ReferenceRegistration(
                ClaimReferenceCategory.SOURCE_RULE, SOURCE_REFS[0], "sha256:wrong"
            ),
            ReferenceRegistration(
                ClaimReferenceCategory.SOURCE_RULE, SOURCE_REFS[1], SOURCE_VERSION
            ),
        )),
        GovernanceReferenceCatalog((
            ReferenceRegistration(
                ClaimReferenceCategory.SOURCE_RULE, SOURCE_REFS[0], SOURCE_VERSION
            ),
            ReferenceRegistration(
                ClaimReferenceCategory.SOURCE_RULE, SOURCE_REFS[1], "sha256:wrong"
            ),
        )),
    ),
)
def test_event_catalog_rejections_are_typed_reference_losses(
    catalog: GovernanceReferenceCatalog,
) -> None:
    adapted = _adapt(_result(), catalog)

    assert adapted.claim is None
    assert len(adapted.issues) == 1
    assert adapted.issues[0].code is ClaimIssueCode.LEGACY_REFERENCE_REJECTED
    assert adapted.issues[0].detail.startswith("CLAIM.REFERENCE_")


@pytest.mark.parametrize(
    ("issue_code", "expected"),
    (
        ("CLAIM.REFERENCE_SYNTHETIC", ClaimIssueCode.LEGACY_REFERENCE_REJECTED),
        ("CLAIM.SYNTHETIC", ClaimIssueCode.LEGACY_CLAIM_REJECTED),
    ),
)
def test_constructor_contract_errors_are_classified_at_local_binding(
    monkeypatch: pytest.MonkeyPatch,
    issue_code: str,
    expected: ClaimIssueCode,
) -> None:
    module = _adapter_module()

    def reject(*_args: object, **_kwargs: object) -> None:
        raise GovernanceClaimContractError(issue_code, "synthetic", "forced rejection")

    monkeypatch.setattr(module, "build_governance_claim", reject)

    adapted = module.adapt_yang_marriage_discrimination(_result(), _catalog())

    assert adapted.claim is None
    assert tuple(issue.code for issue in adapted.issues) == (expected,)
    assert issue_code in adapted.issues[0].detail


def test_malformed_discriminator_is_rejected_before_adapter_invocation() -> None:
    with pytest.raises(ValueError, match="identity and falsifier are required"):
        _result(falsifier="")


def test_non_contract_constructor_exception_remains_visible(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _adapter_module()

    class SentinelError(RuntimeError):
        pass

    def explode(*_args: object, **_kwargs: object) -> None:
        raise SentinelError("visible sentinel")

    monkeypatch.setattr(module, "build_governance_claim", explode)

    with pytest.raises(SentinelError, match="visible sentinel"):
        module.adapt_yang_marriage_discrimination(_result(), _catalog())


def test_provenance_and_derivation_are_stable_and_payload_sensitive() -> None:
    base = _result(anchor_pairs=(("子", "午"), ("卯", "酉")))
    equivalent = replace(base, families=tuple(reversed(base.families)))
    pair_equivalent = _result(anchor_pairs=(("卯", "酉"), ("子", "午")))
    changed_schema = _result(schema_version="synthetic-schema/v2")
    changed_case = _result(case_id="YM-W2-C1-OTHER")
    changed_family = _result(family_detail="不同的完整家族证据")
    changed_falsifier = _result(falsifier="不同的可证伪条件。")

    claims = [
        _adapt(item, _catalog()).claim
        for item in (
            base,
            equivalent,
            pair_equivalent,
            changed_schema,
            changed_case,
            changed_family,
            changed_falsifier,
        )
    ]
    assert all(claim is not None for claim in claims)
    base_claim, equivalent_claim, pair_claim, *changed_claims = cast(Any, claims)
    assert base_claim.adapter_provenance == equivalent_claim.adapter_provenance
    assert base_claim.derivation_chain_digest == equivalent_claim.derivation_chain_digest
    assert base_claim.adapter_provenance == pair_claim.adapter_provenance
    assert base_claim.derivation_chain_digest == pair_claim.derivation_chain_digest
    assert all(
        claim.adapter_provenance.source_claim_ref
        != base_claim.adapter_provenance.source_claim_ref
        for claim in changed_claims
    )
    assert all(
        claim.derivation_chain_digest != base_claim.derivation_chain_digest
        for claim in changed_claims
    )
    assert changed_claims[0].adapter_provenance.adapter_version == (
        "yang-marriage-discrimination/v1"
    )


_BASE_DERIVATION_METADATA = (
    ("school_id", "yang_qingjuan"),
    ("task_id", "marriage.divorce_or_remarriage"),
    ("claim_kind", "event"),
    ("stance", "support"),
    ("temporal_layer", "natal"),
    ("evidence_grade", "inferential"),
    ("confidence", "0.60"),
    ("adapter_version", "yang-marriage-discrimination/v1"),
    ("source_version", SOURCE_VERSION),
    ("source_rule_ref_0", SOURCE_REFS[0]),
    ("source_rule_ref_1", SOURCE_REFS[1]),
)


@pytest.mark.parametrize("metadata_index", range(len(_BASE_DERIVATION_METADATA)))
def test_derivation_helper_binds_each_frozen_metadata_field(
    metadata_index: int,
) -> None:
    provenance = AdapterProvenance(
        "yang_marriage_discrimination",
        "yang-marriage-discrimination/v1",
        "yang_marriage_discrimination:synthetic",
    )
    baseline = derivation_chain_digest(
        (provenance.source_claim_ref,), provenance, _BASE_DERIVATION_METADATA
    )
    changed = list(_BASE_DERIVATION_METADATA)
    key, value = changed[metadata_index]
    changed[metadata_index] = (key, f"{value}-changed")

    assert derivation_chain_digest(
        (provenance.source_claim_ref,), provenance, tuple(changed)
    ) != baseline


def test_derivation_helper_binds_source_claim_order_and_provenance_version() -> None:
    provenance = AdapterProvenance(
        "yang_marriage_discrimination",
        "yang-marriage-discrimination/v1",
        "yang_marriage_discrimination:synthetic",
    )
    baseline = derivation_chain_digest(
        ("source-a", "source-b"), provenance, _BASE_DERIVATION_METADATA
    )
    changed_version = replace(provenance, adapter_version="synthetic/v2")

    assert derivation_chain_digest(
        ("source-b", "source-a"), provenance, _BASE_DERIVATION_METADATA
    ) != baseline
    assert derivation_chain_digest(
        ("source-a", "source-b"), changed_version, _BASE_DERIVATION_METADATA
    ) != baseline


def test_provenance_and_derivation_are_fresh_process_stable() -> None:
    local_claim = _adapt(_result(), _catalog()).claim
    assert local_claim is not None
    replay_claim = _adapt(_result(), _catalog()).claim
    assert replay_claim is not None
    assert replay_claim.claim_id == local_claim.claim_id
    assert replay_claim.content_digest == local_claim.content_digest
    script = f"""
import json
from engine.application.governance_yang_marriage_adapter import adapt_yang_marriage_discrimination
from tests.application.test_governance_yang_marriage_adapter import _catalog, _result
claim = adapt_yang_marriage_discrimination(_result(), _catalog()).claim
print(json.dumps({{
    'source': claim.adapter_provenance.source_claim_ref,
    'derivation': claim.derivation_chain_digest.value,
    'claim_id': claim.claim_id,
    'content': claim.content_digest.value,
}}, sort_keys=True))
"""

    completed = subprocess.run(
        [sys.executable, "-B", "-c", script],
        check=True,
        capture_output=True,
        text=True,
    )
    assert completed.stderr == ""
    fresh = json.loads(completed.stdout)

    assert fresh == {
        "claim_id": local_claim.claim_id,
        "content": local_claim.content_digest.value,
        "derivation": local_claim.derivation_chain_digest.value,
        "source": local_claim.adapter_provenance.source_claim_ref,
    }


def test_conclusion_and_falsifier_have_no_forbidden_semantic_expansion() -> None:
    result = _result()
    claim = _adapt(result, _catalog()).claim
    assert claim is not None
    forbidden_terms = ("100%", "必离", "多婚命", "流年", "大运", "婚姻质量")

    assert all(term not in claim.specification.conclusion for term in forbidden_terms)
    assert claim.falsifier == result.falsifier
    assert all(term not in claim.falsifier for term in forbidden_terms)


def test_adapter_module_is_isolated_and_has_no_forbidden_static_dependencies() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imported_modules = {
        node.module or ""
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    } | {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imported_symbols = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        for alias in node.names
    }
    imported_bindings = {
        (node.module or "", alias.name, alias.asname)
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        for alias in node.names
    }
    imported_aliases = {
        alias.asname
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
        if alias.asname is not None
    }
    called_names = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    called_attributes = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    loaded_names = {
        node.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)
    }
    allowed_imports = {
        "__future__",
        "typing",
        "engine.application.governance_claim_adapter_values",
        "engine.decision.yang_marriage",
        "engine.governance",
        "engine.governance.governance_claim_derivation",
    }
    allowed_import_bindings = {
        ("__future__", "annotations", None),
        ("typing", "Final", None),
        ("engine.application.governance_claim_adapter_values", "AdaptationResult", None),
        ("engine.application.governance_claim_adapter_values", "catalog_loss", None),
        ("engine.application.governance_claim_adapter_values", "loss", None),
        ("engine.decision.yang_marriage", "YangMarriageDiscrimination", None),
        ("engine.governance", "AdapterProvenance", None),
        ("engine.governance", "ClaimEvidenceGrade", None),
        ("engine.governance", "ClaimIssueCode", None),
        ("engine.governance", "ClaimKind", None),
        ("engine.governance", "ClaimReference", None),
        ("engine.governance", "ClaimReferenceCategory", None),
        ("engine.governance", "ClaimStance", None),
        ("engine.governance", "GovernanceClaimContractError", None),
        ("engine.governance", "GovernanceClaimSpec", None),
        ("engine.governance", "GovernanceReferenceCatalog", None),
        ("engine.governance", "TemporalLayer", None),
        ("engine.governance", "TemporalScope", None),
        ("engine.governance", "build_governance_claim", None),
        ("engine.governance", "stable_object_id", None),
        ("engine.governance.governance_claim_derivation", "derivation_chain_digest", None),
    }
    forbidden_prefixes = (
        "engine.pipeline",
        "engine.runtime",
        "engine.evaluation",
        "engine.registry",
        "pathlib",
        "os",
        "socket",
        "urllib",
        "http",
        "requests",
        "datetime",
        "time",
    )
    forbidden_segments = (
        "label",
        "feedback",
        "report",
        "score",
        "registry_loader",
        "runner",
        "pipeline",
    )

    assert imported_modules == allowed_imports
    assert imported_bindings == allowed_import_bindings
    assert not any(
        imported == prefix or imported.startswith(f"{prefix}.")
        for imported in imported_modules
        for prefix in forbidden_prefixes
    )
    imported_names = imported_modules | imported_symbols | imported_aliases
    assert not any(
        segment in imported
        for imported in imported_names
        for segment in forbidden_segments
    )
    assert called_names.isdisjoint(
        {"open", "hash", "id", "__import__"} | imported_symbols.intersection(forbidden_segments)
    )
    assert called_attributes.isdisjoint({"import_module"})
    assert loaded_names.isdisjoint(
        {"__builtins__", "getattr", "globals", "locals", "vars", "eval", "exec", "compile"}
    )
    assert not any(
        isinstance(node, ast.Subscript)
        and isinstance(node.value, ast.Name)
        and node.value.id in {"sys", "builtins", "importlib"}
        for node in ast.walk(tree)
    )


def test_first_import_has_no_forbidden_module_side_effect() -> None:
    script = f"""
import importlib
import json
import sys
for dependency in (
    "engine.application.governance_claim_adapter_values",
    "engine.decision.yang_marriage",
    "engine.governance",
    "engine.governance.governance_claim_derivation",
):
    importlib.import_module(dependency)
before = set(sys.modules)
import {MODULE_NAME}
added = sorted(set(sys.modules) - before)
print(json.dumps(added))
"""
    completed = subprocess.run(
        [sys.executable, "-B", "-c", script],
        check=True,
        capture_output=True,
        text=True,
    )
    assert completed.stderr == ""
    added = json.loads(completed.stdout)
    forbidden_prefixes = (
        "engine.pipeline",
        "engine.runtime",
        "engine.evaluation",
        "engine.registry",
    )
    forbidden_segments = (
        "labels",
        "feedback",
        "reports",
        "scores",
        "registry_loader",
        "runner",
    )

    assert not any(
        name == prefix or name.startswith(f"{prefix}.")
        for name in added
        for prefix in forbidden_prefixes
    )
    assert not any(segment in name for name in added for segment in forbidden_segments)

from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest

from engine.f09.contracts import (
    AbsentDeclarationBinding,
    DetectedIssue,
    DigestRef,
    EvidenceTrack,
    FieldMapping,
    FrozenDeclarationPresenceBindings,
    FrozenDeclarationRef,
    ImmutableJsonSourceBinding,
    MarkdownContractSourceBinding,
    NotApplicableDeclarationBinding,
    ObjectRef,
    ResolvedDeclarationBinding,
    RunTrack,
    SourceLocator,
    TransformationRecord,
    UnavailableDeclarationBinding,
    UnresolvableDeclarationBinding,
    UnversionedSourceBinding,
)


from engine.f09.evidence import (
    DeclarationObservation,
    EvidenceRecord,
    NormalizedEvidencePackage,
    _json_values_equal,
    build_f09_evidence_package,
    trace_to_sources,
    validate_for_pi220,
)


FROZEN_MARKDOWN = Path("engine/contracts/12-real-world-function-evidence-cards-v1.md")
FROZEN_SNAPSHOT = Path("plans/production-implementation-pi-300-f09-source-snapshots-v1.json")


class JsonIntSubclass(int):
    pass


class JsonFloatSubclass(float):
    pass


class JsonStringSubclass(str):
    pass


class JsonListSubclass(list):
    pass


class JsonDictSubclass(dict):
    pass


def digest():
    return DigestRef("sha256", "raw-bytes", "0" * 64)


def declaration_ref():
    return FrozenDeclarationRef(
        declaration_id="F09-output-precision",
        declaration_type="OUTPUT_PRECISION",
        card_id="F09",
        contract_version="pi-210",
        declaration_schema_version="declaration.v1",
        content_digest=digest(),
    )


def markdown_binding():
    return MarkdownContractSourceBinding(
        binding_kind="MARKDOWN_CONTRACT",
        binding_schema_version="source-binding.markdown.v1",
        source_snapshot_id="snapshot-1",
        source_schema_version="markdown-source.commonmark-0.31.2-mdff-v1",
        contract_version="pi-210",
        content_digest=digest(),
        captured_at="2026-07-20T00:00:00Z",
    )


def transformation_kwargs():
    return {
        "transformation_id": "transformation-1",
        "adapter_id": "adapter-1",
        "adapter_version": "1",
        "source_object_refs": (),
        "target_object_refs": (),
        "fidelity": "LOSSLESS",
        "field_mappings": (),
        "dropped_fields": (),
        "dropped_object_refs": (),
        "synthesized_fields": (),
        "issues": (),
        "transformed_at": "2026-07-20T00:00:00Z",
    }


def test_run_track_has_exactly_five_closed_values():
    assert tuple(member.value for member in RunTrack) == (
        "PRODUCTION_DEFAULT",
        "PARALLEL_DOMAIN",
        "STAGED_L6",
        "V5_V6_PREPROD",
        "MANUAL_IMPORT",
    )
    assert len(RunTrack.__members__) == 5


def test_frozen_contract_rejects_mutation():
    issue = DetectedIssue(issue_code="F09-ISSUE", field_path="package.field")

    with pytest.raises(FrozenInstanceError):
        issue.issue_code = "CHANGED"


@pytest.mark.parametrize("value", [None, 1, b"0" * 64])
def test_digest_value_rejects_non_string_before_shape_validation(value):
    with pytest.raises(TypeError, match="value must be a string"):
        DigestRef("sha256", "raw-bytes", value)


@pytest.mark.parametrize("value", ["0" * 63, "0" * 65, "A" * 64, "g" * 64])
def test_digest_value_requires_lowercase_64_hex(value):
    with pytest.raises(ValueError, match="value must be a lowercase 64-hex digest"):
        DigestRef("sha256", "raw-bytes", value)


def test_source_binding_three_members_construct_and_closed_consumer_accepts_them():
    bindings = (
        markdown_binding(),
        ImmutableJsonSourceBinding(
            binding_kind="IMMUTABLE_JSON_SNAPSHOT",
            binding_schema_version="source-binding.immutable-json.v1",
            source_snapshot_id="snapshot-2",
            source_schema_version="json.v1",
            contract_version="pi-210",
            content_digest=digest(),
            captured_at="2026-07-20T00:00:00Z",
        ),
        UnversionedSourceBinding(
            binding_kind="UNVERSIONED_SOURCE",
            binding_schema_version="source-binding.unversioned.v1",
            reason_code="SOURCE_IDENTITY_NOT_VERSIONED",
        ),
    )

    for binding in bindings:
        locator = SourceLocator("source-1", "INPUT_FIELD", "input.md", None, None, binding)
        assert locator.binding is binding


@pytest.mark.parametrize(
    "constructor",
    [
        lambda: MarkdownContractSourceBinding(
            "WRONG",
            "source-binding.markdown.v1",
            "snapshot-1",
            "markdown-source.commonmark-0.31.2-mdff-v1",
            "pi-210",
            digest(),
            "2026-07-20T00:00:00Z",
        ),
        lambda: MarkdownContractSourceBinding(
            "MARKDOWN_CONTRACT",
            "wrong",
            "snapshot-1",
            "markdown-source.commonmark-0.31.2-mdff-v1",
            "pi-210",
            digest(),
            "2026-07-20T00:00:00Z",
        ),
        lambda: MarkdownContractSourceBinding(
            "MARKDOWN_CONTRACT",
            "source-binding.markdown.v1",
            "snapshot-1",
            "wrong",
            "pi-210",
            digest(),
            "2026-07-20T00:00:00Z",
        ),
        lambda: ImmutableJsonSourceBinding(
            "WRONG",
            "source-binding.immutable-json.v1",
            "snapshot-2",
            "json.v1",
            "pi-210",
            digest(),
            "2026-07-20T00:00:00Z",
        ),
        lambda: ImmutableJsonSourceBinding(
            "IMMUTABLE_JSON_SNAPSHOT",
            "wrong",
            "snapshot-2",
            "json.v1",
            "pi-210",
            digest(),
            "2026-07-20T00:00:00Z",
        ),
        lambda: UnversionedSourceBinding(
            "WRONG", "source-binding.unversioned.v1", "SOURCE_IDENTITY_NOT_VERSIONED"
        ),
        lambda: UnversionedSourceBinding(
            "UNVERSIONED_SOURCE", "wrong", "SOURCE_IDENTITY_NOT_VERSIONED"
        ),
        lambda: UnversionedSourceBinding(
            "UNVERSIONED_SOURCE", "source-binding.unversioned.v1", "WRONG"
        ),
    ],
)
def test_source_binding_members_reject_invalid_discriminants(constructor):
    with pytest.raises(ValueError):
        constructor()


def test_source_binding_members_reject_invalid_digest_references():
    with pytest.raises(TypeError):
        MarkdownContractSourceBinding(
            "MARKDOWN_CONTRACT",
            "source-binding.markdown.v1",
            "snapshot-1",
            "markdown-source.commonmark-0.31.2-mdff-v1",
            "pi-210",
            "not-a-digest",
            "2026-07-20T00:00:00Z",
        )
    with pytest.raises(TypeError):
        ImmutableJsonSourceBinding(
            "IMMUTABLE_JSON_SNAPSHOT",
            "source-binding.immutable-json.v1",
            "snapshot-2",
            "json.v1",
            "pi-210",
            "not-a-digest",
            "2026-07-20T00:00:00Z",
        )


def test_source_locator_rejects_non_member_binding():
    with pytest.raises(TypeError, match="closed SourceBinding member"):
        SourceLocator("source-1", "INPUT_FIELD", "input.md", None, None, object())


def test_frozen_declaration_ref_accepts_closed_values():
    ref = declaration_ref()
    assert ref.declaration_type == "OUTPUT_PRECISION"
    assert ref.card_id == "F09"


@pytest.mark.parametrize(
    ("field", "value"),
    [("declaration_type", "OTHER"), ("card_id", "F13"), ("content_digest", "not-a-digest")],
)
def test_frozen_declaration_ref_rejects_invalid_discriminants_and_reference(field, value):
    kwargs = {
        "declaration_id": "declaration-1",
        "declaration_type": "OUTPUT_PRECISION",
        "card_id": "F09",
        "contract_version": "pi-210",
        "declaration_schema_version": "declaration.v1",
        "content_digest": digest(),
    }
    kwargs[field] = value
    with pytest.raises((TypeError, ValueError)):
        FrozenDeclarationRef(**kwargs)


def test_all_five_declaration_binding_branches_construct():
    ref = declaration_ref()
    bindings = (
        ResolvedDeclarationBinding("RESOLVED", ref),
        AbsentDeclarationBinding("ABSENT", "DECLARATION_NOT_PRESENT"),
        NotApplicableDeclarationBinding("NOT_APPLICABLE", "DECLARATION_NOT_APPLICABLE"),
        UnavailableDeclarationBinding("UNAVAILABLE", "DECLARATION_UNREAD", ("issue-1",)),
        UnresolvableDeclarationBinding("UNRESOLVABLE", ref, "BROKEN_REFERENCE", ("issue-2",)),
    )

    for binding in bindings:
        presence = FrozenDeclarationPresenceBindings(binding, binding)
        assert presence.output_precision_binding is binding
        assert presence.validation_plan_binding is binding


def test_each_declaration_binding_rejects_invalid_discriminant_or_reference():
    ref = declaration_ref()
    constructors = (
        lambda: ResolvedDeclarationBinding("WRONG", ref),
        lambda: ResolvedDeclarationBinding("RESOLVED", object()),
        lambda: AbsentDeclarationBinding("WRONG", "DECLARATION_NOT_PRESENT"),
        lambda: AbsentDeclarationBinding("ABSENT", "WRONG"),
        lambda: NotApplicableDeclarationBinding("WRONG", "DECLARATION_NOT_APPLICABLE"),
        lambda: NotApplicableDeclarationBinding("NOT_APPLICABLE", "WRONG"),
        lambda: UnavailableDeclarationBinding("WRONG", "DECLARATION_UNREAD", ("issue-1",)),
        lambda: UnavailableDeclarationBinding("UNAVAILABLE", "WRONG", ("issue-1",)),
        lambda: UnresolvableDeclarationBinding("WRONG", ref, "BROKEN_REFERENCE", ("issue-1",)),
        lambda: UnresolvableDeclarationBinding("UNRESOLVABLE", object(), "BROKEN_REFERENCE", ("issue-1",)),
        lambda: UnresolvableDeclarationBinding("UNRESOLVABLE", ref, "WRONG", ("issue-1",)),
    )

    for constructor in constructors:
        with pytest.raises((TypeError, ValueError)):
            constructor()


@pytest.mark.parametrize(
    "constructor",
    [
        lambda: UnavailableDeclarationBinding("UNAVAILABLE", "DECLARATION_UNREAD", ()),
        lambda: UnresolvableDeclarationBinding("UNRESOLVABLE", declaration_ref(), "BROKEN_REFERENCE", ()),
    ],
)
def test_unavailable_and_unresolvable_reject_empty_issue_ids(constructor):
    with pytest.raises(ValueError, match="issue_ids must be a nonempty tuple"):
        constructor()


@pytest.mark.parametrize("field", ["output_precision_binding", "validation_plan_binding"])
def test_presence_consumer_rejects_non_union_members(field):
    kwargs = {
        "output_precision_binding": AbsentDeclarationBinding("ABSENT", "DECLARATION_NOT_PRESENT"),
        "validation_plan_binding": NotApplicableDeclarationBinding(
            "NOT_APPLICABLE", "DECLARATION_NOT_APPLICABLE"
        ),
    }
    kwargs[field] = object()
    with pytest.raises(TypeError, match=f"{field} must be a closed FrozenDeclarationBinding member"):
        FrozenDeclarationPresenceBindings(**kwargs)


def test_required_constructor_fields_cannot_be_omitted():
    with pytest.raises(TypeError):
        DetectedIssue(issue_code="F09-ISSUE")
    with pytest.raises(TypeError):
        FrozenDeclarationRef(
            declaration_id="declaration-1",
            declaration_type="OUTPUT_PRECISION",
            card_id="F09",
            contract_version="pi-210",
            declaration_schema_version="declaration.v1",
        )


def test_source_locator_explicit_none_differs_from_omitted_optional_typed_fields():
    locator = SourceLocator(
        source_id="source-1",
        source_type="INPUT_FIELD",
        path="input.md",
        object_id=None,
        field_path=None,
        binding=markdown_binding(),
    )
    assert locator.object_id is None
    assert locator.field_path is None

    with pytest.raises(TypeError):
        SourceLocator(
            source_id="source-1",
            source_type="INPUT_FIELD",
            path="input.md",
            field_path=None,
            binding=markdown_binding(),
        )
    with pytest.raises(TypeError):
        SourceLocator(
            source_id="source-1",
            source_type="INPUT_FIELD",
            path="input.md",
            object_id=None,
            binding=markdown_binding(),
        )


def test_task1_fixture_uses_canonical_runtime_identities(canonical_contract_types):
    expected = {
        "RunTrack": RunTrack,
        "ObjectRef": ObjectRef,
        "FieldMapping": FieldMapping,
        "TransformationRecord": TransformationRecord,
        "DetectedIssue": DetectedIssue,
        "EvidenceRecord": EvidenceRecord,
        "DeclarationObservation": DeclarationObservation,
        "NormalizedEvidencePackage": NormalizedEvidencePackage,
    }
    assert canonical_contract_types == expected
    assert all(canonical_contract_types[name] is value for name, value in expected.items())


@pytest.mark.parametrize(
    "field",
    [
        "source_object_refs",
        "target_object_refs",
        "field_mappings",
        "dropped_fields",
        "dropped_object_refs",
        "synthesized_fields",
        "issues",
    ],
)
@pytest.mark.parametrize("mutable_container", [[], {}])
def test_transformation_record_rejects_mutable_top_level_containers(field, mutable_container):
    kwargs = transformation_kwargs()
    kwargs[field] = mutable_container

    with pytest.raises(TypeError, match="TransformationRecord collections must be tuples"):
        TransformationRecord(**kwargs)


def evidence_record(evidence_id, track, object_id, temporal_scope):
    return EvidenceRecord(
        evidence_id=evidence_id,
        track=track,
        locator=SourceLocator(
            source_id=f"source-{evidence_id}",
            source_type="THEORY_RULE",
            path="explicit-source",
            object_id=object_id,
            field_path="/value",
            binding=UnversionedSourceBinding(
                "UNVERSIONED_SOURCE",
                "source-binding.unversioned.v1",
                "SOURCE_IDENTITY_NOT_VERSIONED",
            ),
        ),
        value=evidence_id,
        temporal_scope=temporal_scope,
        transformation="LOSSLESS_COPY",
    )


def build_package(chart_records=(), hypothesis_records=()):
    return build_f09_evidence_package(
        case_id="CASE-1",
        track=RunTrack.STAGED_L6,
        markdown_path=FROZEN_MARKDOWN,
        snapshot_path=FROZEN_SNAPSHOT,
        chart_records=chart_records,
        hypothesis_records=hypothesis_records,
    )


def test_package_builder_preserves_three_tracks_without_promoting_hypothesis():
    chart = evidence_record(
        "chart-1", EvidenceTrack.CHART_STRUCTURE, "CHART-1", "NATAL_STATIC"
    )
    hypothesis = evidence_record(
        "hypothesis-1",
        EvidenceTrack.UNVERIFIED_HYPOTHESIS,
        "HYPOTHESIS-1",
        "UNVERIFIED",
    )

    package = build_package((chart,), (hypothesis,))

    assert package.records[0] is chart
    assert package.records[-1] is hypothesis
    assert {record.track for record in package.records} == set(EvidenceTrack)
    assert all(
        isinstance(record.locator.binding, ImmutableJsonSourceBinding)
        for record in package.records
        if record.track is EvidenceTrack.REALITY_FACT
    )
    assert validate_for_pi220(package) == "READY"


def test_state_event_and_temporal_scopes_remain_separate():
    package = build_package()
    reality = [record for record in package.records if record.track is EvidenceTrack.REALITY_FACT]

    assert {record.temporal_scope for record in reality if record.locator.object_id == "SOURCE-STATE-1"} == {"STATE_AS_OF"}
    assert {record.temporal_scope for record in reality if record.locator.object_id == "SOURCE-EVENT-1"} == {"EVENT_INTERVAL"}
    assert trace_to_sources(package, "SOURCE-STATE-1")
    assert all(locator.object_id == "SOURCE-STATE-1" for locator in trace_to_sources(package, "SOURCE-STATE-1"))


def test_reality_records_assign_gate_members_from_frozen_locator_semantics():
    package = build_package()
    members_by_id = {
        record.evidence_id: record.gate_members
        for record in package.records
        if record.track is EvidenceTrack.REALITY_FACT
    }

    assert members_by_id == {
        "SRCLOC-STATE-LEVEL": (),
        "SRCLOC-STATE-POSITION": ("RESOURCE", "ALLOCATION", "ATTRIBUTION"),
        "SRCLOC-STATE-AS-OF": ("TENSE",),
        "SRCLOC-EVENT-LEVEL": (),
        "SRCLOC-EVENT-CHANGE": ("ALLOCATION", "ATTRIBUTION"),
        "SRCLOC-EVENT-START": ("TENSE",),
        "SRCLOC-EVENT-END": ("TENSE",),
        "SRCLOC-EVENT-START-INCLUSIVE": ("TENSE",),
        "SRCLOC-EVENT-END-INCLUSIVE": ("TENSE",),
        "SRCLOC-OUTCOME-AXIS": ("ALLOCATION",),
        "SRCLOC-OUTCOME-ACTION": ("RESOURCE", "ALLOCATION"),
        "SRCLOC-OUTCOME-OBJECT": ("OBJECT",),
        "SRCLOC-OUTCOME-TENSE": ("TENSE",),
    }
    assert all("RISK" not in members for members in members_by_id.values())


def test_f09_output_precision_is_resolved_null_and_unresolved():
    precision = build_package().output_precision

    assert isinstance(precision.binding, ResolvedDeclarationBinding)
    assert precision.value is None
    assert precision.source_state == "BOTH_NULL_AND_UNRESOLVED"


def test_f09_not_applicable_validation_plan_is_invalid():
    package = build_package()
    invalid = replace(
        package,
        validation_plan=DeclarationObservation(
            NotApplicableDeclarationBinding(
                "NOT_APPLICABLE", "DECLARATION_NOT_APPLICABLE"
            ),
            None,
            "NOT_APPLICABLE",
        ),
    )

    assert validate_for_pi220(invalid) == "INVALID"


@pytest.mark.parametrize(
    "binding",
    [
        ResolvedDeclarationBinding("RESOLVED", declaration_ref()),
        AbsentDeclarationBinding("ABSENT", "DECLARATION_NOT_PRESENT"),
        NotApplicableDeclarationBinding(
            "NOT_APPLICABLE", "DECLARATION_NOT_APPLICABLE"
        ),
        UnavailableDeclarationBinding(
            "UNAVAILABLE", "DECLARATION_UNREAD", ("issue-1",)
        ),
        UnresolvableDeclarationBinding(
            "UNRESOLVABLE", declaration_ref(), "BROKEN_REFERENCE", ("issue-2",)
        ),
    ],
)
def test_declaration_observation_preserves_all_five_binding_branches(binding):
    observation = DeclarationObservation(binding, None, binding.presence)
    assert observation.binding is binding


def test_evidence_record_has_only_locator_binding_and_package_collections_are_tuples():
    record = evidence_record(
        "chart-1", EvidenceTrack.CHART_STRUCTURE, "CHART-1", "NATAL_STATIC"
    )
    package = build_package((record,), ())

    assert "binding" not in EvidenceRecord.__dataclass_fields__
    assert isinstance(package.records, tuple)
    assert isinstance(package.issues, tuple)
    with pytest.raises(FrozenInstanceError):
        record.value = "changed"


def test_trace_to_sources_is_deterministic_deduplicated_and_unknown_is_empty():
    first = evidence_record(
        "chart-1", EvidenceTrack.CHART_STRUCTURE, "CHART-1", "NATAL_STATIC"
    )
    duplicate = replace(first, evidence_id="chart-2")
    package = build_package((first, duplicate), ())

    assert trace_to_sources(package, "CHART-1") == (first.locator,)
    assert trace_to_sources(package, "missing") == ()


def test_trace_to_sources_keeps_same_coordinates_with_different_binding_identity():
    first = evidence_record(
        "chart-1", EvidenceTrack.CHART_STRUCTURE, "CHART-1", "NATAL_STATIC"
    )
    first_locator = replace(first.locator, binding=markdown_binding())
    second_locator = replace(
        first_locator,
        binding=replace(markdown_binding(), captured_at="2026-07-21T00:00:00Z"),
    )
    first = replace(first, locator=first_locator)
    second = replace(first, evidence_id="chart-2", locator=second_locator)
    package = build_package((first, second), ())

    assert trace_to_sources(package, "CHART-1") == (first_locator, second_locator)


def test_validator_recomputes_current_records_instead_of_trusting_ready_cache():
    package = build_package()
    reality_index = next(
        index
        for index, record in enumerate(package.records)
        if record.locator.object_id == "SOURCE-STATE-1"
    )
    records = list(package.records)
    records[reality_index] = replace(records[reality_index], temporal_scope="EVENT_INTERVAL")
    tampered = replace(
        package,
        records=tuple(records),
        issues=(),
        integrity_state="READY",
    )

    assert validate_for_pi220(tampered) == "BLOCKED"


def test_reality_fact_with_nonimmutable_source_is_blocked():
    package = build_package()
    reality_index = next(
        index
        for index, record in enumerate(package.records)
        if record.track is EvidenceTrack.REALITY_FACT
    )
    records = list(package.records)
    records[reality_index] = replace(
        records[reality_index],
        locator=replace(
            records[reality_index].locator,
            binding=UnversionedSourceBinding(
                "UNVERSIONED_SOURCE",
                "source-binding.unversioned.v1",
                "SOURCE_IDENTITY_NOT_VERSIONED",
            ),
        ),
    )
    tampered = replace(package, records=tuple(records), issues=(), integrity_state="READY")

    assert validate_for_pi220(tampered) == "BLOCKED"


@pytest.mark.parametrize(
    ("binding_field", "value"),
    [
        ("source_snapshot_id", "wrong-snapshot"),
        ("source_schema_version", "wrong-schema"),
        ("contract_version", "wrong-contract"),
        ("content_digest", digest()),
        ("captured_at", "2026-07-22T00:00:00Z"),
    ],
)
def test_reality_immutable_binding_identity_drift_is_blocked(
    binding_field, value
):
    package = build_package()
    reality_index = next(
        index
        for index, record in enumerate(package.records)
        if record.track is EvidenceTrack.REALITY_FACT
    )
    record = package.records[reality_index]
    records = list(package.records)
    records[reality_index] = replace(
        record,
        locator=replace(
            record.locator,
            binding=replace(record.locator.binding, **{binding_field: value}),
        ),
    )

    assert validate_for_pi220(
        replace(package, records=tuple(records), issues=(), integrity_state="READY")
    ) == "BLOCKED"


def test_reality_copied_value_drift_is_blocked_even_with_ready_cache():
    package = build_package()
    reality_index = next(
        index
        for index, record in enumerate(package.records)
        if record.track is EvidenceTrack.REALITY_FACT
    )
    records = list(package.records)
    records[reality_index] = replace(records[reality_index], value="tampered")

    assert validate_for_pi220(
        replace(package, records=tuple(records), issues=(), integrity_state="READY")
    ) == "BLOCKED"


def test_reality_boolean_copied_value_cannot_be_replaced_by_equal_number():
    package = build_package()
    reality_index = next(
        index
        for index, record in enumerate(package.records)
        if record.track is EvidenceTrack.REALITY_FACT
        and isinstance(record.value, bool)
    )
    records = list(package.records)
    records[reality_index] = replace(records[reality_index], value=1)

    assert validate_for_pi220(
        replace(package, records=tuple(records), issues=(), integrity_state="READY")
    ) == "BLOCKED"


def test_reality_string_copied_value_rejects_equal_builtin_subclass():
    package = build_package()
    reality_index = next(
        index
        for index, record in enumerate(package.records)
        if record.track is EvidenceTrack.REALITY_FACT
        and type(record.value) is str
    )
    records = list(package.records)
    records[reality_index] = replace(
        records[reality_index],
        value=JsonStringSubclass(records[reality_index].value),
    )

    assert validate_for_pi220(
        replace(package, records=tuple(records), issues=(), integrity_state="READY")
    ) == "BLOCKED"


@pytest.mark.parametrize(
    ("subclass_value", "builtin_value"),
    [
        (JsonIntSubclass(1), 1),
        (JsonFloatSubclass(1.5), 1.5),
        (JsonStringSubclass("value"), "value"),
        (JsonListSubclass([1]), [1]),
        (JsonDictSubclass({"key": 1}), {"key": 1}),
    ],
)
def test_json_value_equality_rejects_builtin_subclasses(
    subclass_value, builtin_value
):
    assert not _json_values_equal(subclass_value, builtin_value)


def test_json_value_equality_rejects_subclasses_symmetrically_and_nested_keys():
    assert not _json_values_equal(1, JsonIntSubclass(1))
    assert not _json_values_equal(
        {"outer": {JsonStringSubclass("key"): 1}},
        {"outer": {"key": 1}},
    )


@pytest.mark.parametrize(
    ("locator_field", "value"),
    [
        ("path", "plans/wrong-snapshot.json"),
        ("source_id", "wrong-source"),
        ("object_id", "SOURCE-EVENT-1"),
        ("field_path", "/value/wrong-field"),
        ("source_type", "THEORY_RULE"),
    ],
)
def test_reality_locator_identity_drift_is_blocked(locator_field, value):
    package = build_package()
    reality_index = next(
        index
        for index, record in enumerate(package.records)
        if record.track is EvidenceTrack.REALITY_FACT
    )
    record = package.records[reality_index]
    records = list(package.records)
    records[reality_index] = replace(
        record, locator=replace(record.locator, **{locator_field: value})
    )

    assert validate_for_pi220(
        replace(package, records=tuple(records), issues=(), integrity_state="READY")
    ) == "BLOCKED"


def test_reality_transformation_drift_is_blocked():
    package = build_package()
    reality_index = next(
        index
        for index, record in enumerate(package.records)
        if record.track is EvidenceTrack.REALITY_FACT
    )
    records = list(package.records)
    records[reality_index] = replace(
        records[reality_index], transformation="MDFF_V1_COPY"
    )

    assert validate_for_pi220(
        replace(package, records=tuple(records), issues=(), integrity_state="READY")
    ) == "BLOCKED"


@pytest.mark.parametrize(
    ("object_id", "wrong_scope"),
    [
        ("SOURCE-STATE-1", "EVENT_INTERVAL"),
        ("SOURCE-EVENT-1", "OUTCOME_CURRENT"),
        ("SOURCE-OUTCOME-1", "STATE_AS_OF"),
    ],
)
def test_state_event_and_outcome_temporal_scope_swaps_are_blocked(
    object_id, wrong_scope
):
    package = build_package()
    records = tuple(
        replace(record, temporal_scope=wrong_scope)
        if record.locator.object_id == object_id
        else record
        for record in package.records
    )

    assert validate_for_pi220(
        replace(package, records=records, issues=(), integrity_state="READY")
    ) == "BLOCKED"


@pytest.mark.parametrize(
    ("presence", "source_state", "expected"),
    [
        ("RESOLVED", "BOTH_NULL_AND_UNRESOLVED", "READY"),
        ("ABSENT", "ABSENT", "INVALID"),
        ("NOT_APPLICABLE", "NOT_APPLICABLE", "INVALID"),
        ("UNAVAILABLE", "UNAVAILABLE", "BLOCKED"),
        ("UNRESOLVABLE", "UNRESOLVABLE", "BLOCKED"),
    ],
)
def test_validator_consumes_all_five_output_declaration_branches(
    presence, source_state, expected
):
    package = build_package()
    resolved_ref = package.output_precision.binding.ref
    bindings = {
        "RESOLVED": ResolvedDeclarationBinding("RESOLVED", resolved_ref),
        "ABSENT": AbsentDeclarationBinding("ABSENT", "DECLARATION_NOT_PRESENT"),
        "NOT_APPLICABLE": NotApplicableDeclarationBinding(
            "NOT_APPLICABLE", "DECLARATION_NOT_APPLICABLE"
        ),
        "UNAVAILABLE": UnavailableDeclarationBinding(
            "UNAVAILABLE", "DECLARATION_UNREAD", ("issue-1",)
        ),
        "UNRESOLVABLE": UnresolvableDeclarationBinding(
            "UNRESOLVABLE", resolved_ref, "BROKEN_REFERENCE", ("issue-2",)
        ),
    }
    observation = DeclarationObservation(bindings[presence], None, source_state)

    assert validate_for_pi220(replace(package, output_precision=observation)) == expected


@pytest.mark.parametrize(
    ("presence", "source_state", "expected"),
    [
        ("RESOLVED", "RESOLVED", "READY"),
        ("ABSENT", "ABSENT", "INVALID"),
        ("NOT_APPLICABLE", "NOT_APPLICABLE", "INVALID"),
        ("UNAVAILABLE", "UNAVAILABLE", "BLOCKED"),
        ("UNRESOLVABLE", "UNRESOLVABLE", "BLOCKED"),
    ],
)
def test_validator_consumes_all_five_validation_plan_branches(
    presence, source_state, expected
):
    package = build_package()
    resolved_ref = package.validation_plan.binding.ref
    bindings = {
        "RESOLVED": ResolvedDeclarationBinding("RESOLVED", resolved_ref),
        "ABSENT": AbsentDeclarationBinding("ABSENT", "DECLARATION_NOT_PRESENT"),
        "NOT_APPLICABLE": NotApplicableDeclarationBinding(
            "NOT_APPLICABLE", "DECLARATION_NOT_APPLICABLE"
        ),
        "UNAVAILABLE": UnavailableDeclarationBinding(
            "UNAVAILABLE", "DECLARATION_UNREAD", ("issue-1",)
        ),
        "UNRESOLVABLE": UnresolvableDeclarationBinding(
            "UNRESOLVABLE", resolved_ref, "BROKEN_REFERENCE", ("issue-2",)
        ),
    }
    observation = DeclarationObservation(
        bindings[presence], package.validation_plan.value, source_state
    )

    assert validate_for_pi220(replace(package, validation_plan=observation)) == expected


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("declaration_id", "F09-wrong"),
        ("declaration_type", "VALIDATION_PLAN"),
        ("card_id", "F08"),
        ("contract_version", "wrong-contract"),
        ("declaration_schema_version", "wrong-schema"),
        ("content_digest", digest()),
    ],
)
def test_resolved_output_declaration_complete_identity_mismatch_is_invalid(field, value):
    package = build_package()
    ref = replace(package.output_precision.binding.ref, **{field: value})
    observation = DeclarationObservation(
        ResolvedDeclarationBinding("RESOLVED", ref),
        None,
        "BOTH_NULL_AND_UNRESOLVED",
    )

    assert validate_for_pi220(replace(package, output_precision=observation)) == "INVALID"


@pytest.mark.parametrize(
    ("value", "source_state"),
    [("not-null", "BOTH_NULL_AND_UNRESOLVED"), (None, "RESOLVED")],
)
def test_resolved_output_declaration_value_and_state_mismatch_is_invalid(
    value, source_state
):
    package = build_package()
    observation = replace(package.output_precision, value=value, source_state=source_state)

    assert validate_for_pi220(replace(package, output_precision=observation)) == "INVALID"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("declaration_id", "F09-wrong"),
        ("declaration_type", "OUTPUT_PRECISION"),
        ("card_id", "F08"),
        ("contract_version", "wrong-contract"),
        ("declaration_schema_version", "wrong-schema"),
        ("content_digest", digest()),
    ],
)
def test_resolved_validation_plan_complete_identity_mismatch_is_invalid(field, value):
    package = build_package()
    ref = replace(package.validation_plan.binding.ref, **{field: value})
    observation = replace(
        package.validation_plan,
        binding=ResolvedDeclarationBinding("RESOLVED", ref),
    )

    assert validate_for_pi220(replace(package, validation_plan=observation)) == "INVALID"


@pytest.mark.parametrize(
    ("value", "source_state"),
    [("wrong-value", "RESOLVED"), (None, "RESOLVED"), (None, "UNAVAILABLE")],
)
def test_resolved_validation_plan_value_and_state_mismatch_is_invalid(
    value, source_state
):
    package = build_package()
    observation = replace(package.validation_plan, value=value, source_state=source_state)

    assert validate_for_pi220(replace(package, validation_plan=observation)) == "INVALID"


@pytest.mark.parametrize("removal", ["one-field", "one-object", "all-reality"])
def test_missing_frozen_reality_records_are_blocked_even_with_ready_cache(removal):
    package = build_package()
    if removal == "one-field":
        removed_id = next(
            record.evidence_id
            for record in package.records
            if record.track is EvidenceTrack.REALITY_FACT
        )
        records = tuple(
            record for record in package.records if record.evidence_id != removed_id
        )
    elif removal == "one-object":
        records = tuple(
            record
            for record in package.records
            if record.locator.object_id != "SOURCE-EVENT-1"
        )
    else:
        records = tuple(
            record
            for record in package.records
            if record.track is not EvidenceTrack.REALITY_FACT
        )

    assert validate_for_pi220(
        replace(package, records=records, issues=(), integrity_state="READY")
    ) == "BLOCKED"


def test_extra_or_relabelled_reality_coordinate_is_blocked():
    package = build_package()
    reality = next(
        record for record in package.records if record.track is EvidenceTrack.REALITY_FACT
    )
    extra = replace(reality, evidence_id="SRCLOC-EXTRA")

    assert validate_for_pi220(
        replace(
            package,
            records=package.records + (extra,),
            issues=(),
            integrity_state="READY",
        )
    ) == "BLOCKED"


def test_hypothesis_with_immutable_binding_remains_unverified_hypothesis():
    package = build_package()
    reality = next(
        record for record in package.records if record.track is EvidenceTrack.REALITY_FACT
    )
    hypothesis = replace(
        reality,
        evidence_id="hypothesis-with-frozen-source",
        track=EvidenceTrack.UNVERIFIED_HYPOTHESIS,
        temporal_scope="UNVERIFIED",
    )

    rebuilt = build_package((), (hypothesis,))

    assert rebuilt.records[-1] is hypothesis
    assert rebuilt.records[-1].track is EvidenceTrack.UNVERIFIED_HYPOTHESIS
    assert validate_for_pi220(rebuilt) == "READY"


@pytest.mark.parametrize(
    ("chart_records", "hypothesis_records"),
    [
        ((evidence_record("wrong-chart", EvidenceTrack.REALITY_FACT, "X", "NOW"),), ()),
        ((), (evidence_record("wrong-hypothesis", EvidenceTrack.CHART_STRUCTURE, "X", "NOW"),)),
    ],
)
def test_input_collections_cannot_cross_track_boundaries(chart_records, hypothesis_records):
    with pytest.raises(ValueError):
        build_package(chart_records, hypothesis_records)

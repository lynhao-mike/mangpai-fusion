from __future__ import annotations

import math
import re
import subprocess
import sys

import pytest

from engine.governance import (
    CanonicalizationError,
    canonical_digest,
    stable_object_id,
)


_DIGEST_PATTERN = re.compile(r"[0-9a-f]{64}")
_STABLE_ID_PATTERN = re.compile(r"[a-z][a-z0-9_-]*:[0-9a-f]{64}")
_F09_EXPORTS = (
    "F09Observation",
    "F09RunExecutionResultV1",
    "F09RunRequest",
    "F09RunResult",
    "run_f09_slice",
    "run_f09_slice_with_execution_authority_v1",
)


def _run_fresh_python(code: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-c", code],
        check=False,
        capture_output=True,
        text=True,
    )


def test_governance_import_does_not_load_f09_application_fanout() -> None:
    # Given
    code = (
        "import sys\n"
        "allowed = {'engine.f09.canonical_json', 'engine.f09.contracts', "
        "'engine.f09.errors'}\n"
        "def fanout():\n"
        "    return tuple(sorted(name for name in sys.modules "
        "if name.startswith('engine.f09.') and name not in allowed))\n"
        "print(f'before={fanout()!r}')\n"
        "import engine.governance.canonical\n"
        "print(f'after={fanout()!r}')\n"
    )

    # When
    result = _run_fresh_python(code)

    # Then
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == ["before=()", "after=()"]


def test_f09_public_exports_resolve_to_application_objects() -> None:
    # Given
    code = (
        "import importlib\n"
        "import engine.f09 as package\n"
        "application = importlib.import_module('engine.f09.application')\n"
        "mismatches = tuple(name for name in package.__all__ "
        "if getattr(package, name) is not getattr(application, name))\n"
        "print(f'names={package.__all__!r}')\n"
        "print(f'mismatches={mismatches!r}')\n"
    )

    # When
    result = _run_fresh_python(code)

    # Then
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [
        f"names={_F09_EXPORTS!r}",
        "mismatches=()",
    ]


def test_canonical_digest_is_independent_of_dictionary_key_order() -> None:
    # Given
    first = {"b": 2, "a": 1}
    reordered = {"a": 1, "b": 2}

    # When
    first_digest = canonical_digest(first)
    reordered_digest = canonical_digest(reordered)

    # Then
    assert first_digest == reordered_digest
    assert _DIGEST_PATTERN.fullmatch(first_digest)


def test_canonical_digest_preserves_tuple_member_order() -> None:
    # Given
    first = ("earth", "metal")
    reordered = ("metal", "earth")

    # When
    first_digest = canonical_digest(first)
    reordered_digest = canonical_digest(reordered)

    # Then
    assert first_digest != reordered_digest


def test_canonical_digest_changes_with_content() -> None:
    # Given
    original = {"kind": "relation", "active": True, "weight": 1.5}
    changed = {"kind": "relation", "active": False, "weight": 1.5}

    # When
    original_digest = canonical_digest(original)
    changed_digest = canonical_digest(changed)

    # Then
    assert original_digest != changed_digest


def test_stable_object_id_repeats_for_the_same_identity_material() -> None:
    # Given
    identity = {"kind": "stem", "value": "jia"}

    # When
    first = stable_object_id("fact", identity)
    second = stable_object_id("fact", identity)

    # Then
    assert first == second
    assert _STABLE_ID_PATTERN.fullmatch(first)


def test_stable_object_id_isolated_by_namespace() -> None:
    # Given
    identity = {"kind": "stem", "value": "jia"}

    # When
    fact_id = stable_object_id("fact", identity)
    claim_id = stable_object_id("claim", identity)

    # Then
    assert fact_id != claim_id
    assert fact_id.startswith("fact:")
    assert claim_id.startswith("claim:")


@pytest.mark.parametrize("namespace", ("", "Fact", "fact:claim"))
def test_stable_object_id_rejects_invalid_namespace(namespace: str) -> None:
    # Given
    identity = {"kind": "stem", "value": "jia"}

    # When
    with pytest.raises(CanonicalizationError) as caught:
        stable_object_id(namespace, identity)

    # Then
    assert caught.value.issue_code == "CANONICAL.NAMESPACE_INVALID"


def test_digest_and_object_id_use_separate_domains() -> None:
    # Given
    identity = {"kind": "stem", "value": "jia"}

    # When
    digest = canonical_digest(identity)
    object_id = stable_object_id("fact", identity)

    # Then
    assert object_id.removeprefix("fact:") != digest


def test_list_and_tuple_material_have_distinct_digests() -> None:
    # Given
    list_material = ["earth", "metal"]
    tuple_material = ("earth", "metal")

    # When
    list_digest = canonical_digest(list_material)
    tuple_digest = canonical_digest(tuple_material)

    # Then
    assert list_digest != tuple_digest


def test_digest_and_id_ignore_timezone_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    # Given
    identity = {"kind": "branch", "value": "zi"}
    monkeypatch.setenv("TZ", "Pacific/Kiritimati")
    first = (canonical_digest(identity), stable_object_id("fact", identity))

    # When
    monkeypatch.setenv("TZ", "America/Adak")
    second = (canonical_digest(identity), stable_object_id("fact", identity))

    # Then
    assert first == second


@pytest.mark.parametrize(
    ("value", "expected_issue_code"),
    (
        (math.nan, "CANONICAL.NON_FINITE_NUMBER"),
        (math.inf, "CANONICAL.NON_FINITE_NUMBER"),
        (-math.inf, "CANONICAL.NON_FINITE_NUMBER"),
    ),
)
def test_canonical_digest_rejects_non_finite_numbers(
    value: float,
    expected_issue_code: str,
) -> None:
    # Given
    material = {"value": value}

    # When
    with pytest.raises(CanonicalizationError) as caught:
        canonical_digest(material)

    # Then
    assert caught.value.issue_code == expected_issue_code


def test_canonical_digest_rejects_unsupported_values() -> None:
    # Given
    class Unsupported:
        pass

    material = Unsupported()

    # When
    with pytest.raises(CanonicalizationError) as caught:
        canonical_digest(material)

    # Then
    assert caught.value.issue_code == "CANONICAL.TYPE_UNSUPPORTED"


def test_canonical_digest_rejects_cyclic_structures() -> None:
    # Given
    cyclic: dict[str, int | dict[str, int]] = {}
    cyclic["self"] = cyclic

    # When
    with pytest.raises(CanonicalizationError) as caught:
        canonical_digest(cyclic)

    # Then
    assert caught.value.issue_code == "CANONICAL.CYCLE_DETECTED"


def test_canonical_digest_rejects_a_self_referential_list_as_a_cycle() -> None:
    # Given
    cyclic = []
    cyclic.append(cyclic)

    # When
    with pytest.raises(CanonicalizationError) as caught:
        canonical_digest(cyclic)

    # Then
    assert caught.value.issue_code == "CANONICAL.CYCLE_DETECTED"

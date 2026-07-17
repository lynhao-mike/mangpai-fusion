from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from engine.decision.ren_timing_rules import load_ren_timing_rules


_SOURCE_PATH = "theory/ren/index.yaml"
_SOURCE_ANCHORS = {
    "冲": "M3-R-057",
    "刑": "M3-R-046",
    "穿": "M3-R-047",
    "伏吟": "M3-R-188",
    "合": "M3-R-057",
}


def _write_registry(tmp_path: Path, rules: str, *, top_level: str | None = None) -> Path:
    path = tmp_path / "registry.yaml"
    content = top_level or f"schema_version: ren-career-timing-rules/v1\nrules:\n{rules}"
    path.write_text(content, encoding="utf-8")
    return path


def _rule(
    *,
    rule_id: str = "REN-TEST",
    relation: str = "冲",
    priority: str = "10",
    confidence: str = "0.72",
    source_path: str = _SOURCE_PATH,
    source_anchor: str | None = None,
    extra: str = "",
) -> str:
    source_anchor = source_anchor or _SOURCE_ANCHORS.get(relation, "M3-R-055")
    return (
        f"  - rule_id: {rule_id}\n"
        f"    relation: {relation}\n"
        f"    priority: {priority}\n"
        f"    source_path: {source_path}\n"
        f"    source_anchor: {source_anchor}\n"
        f"    confidence: {confidence}\n"
        f"{extra}"
    )


def test_default_registry_is_deterministic_immutable_and_source_backed() -> None:
    first = load_ren_timing_rules()
    second = load_ren_timing_rules()

    assert first == second
    assert [item.relation for item in first] == ["冲", "刑", "穿", "伏吟", "合"]
    assert [item.priority for item in first] == sorted(item.priority for item in first)
    assert all(Path(item.source_path).is_file() for item in first)
    with pytest.raises(FrozenInstanceError):
        first[0].priority = 999  # type: ignore[misc]


@pytest.mark.parametrize(
    ("top_level", "message"),
    [
        ("schema_version: ren-career-timing-rules/v1\nrules: []\nextra: bad\n", "top-level fields"),
        ("schema_version: wrong\nrules: []\n", "schema_version"),
        ("schema_version: ren-career-timing-rules/v1\nrules: {}\n", "rules must be a list"),
    ],
)
def test_registry_rejects_invalid_top_level(tmp_path: Path, top_level: str, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        load_ren_timing_rules(_write_registry(tmp_path, "", top_level=top_level))


def test_registry_rejects_unknown_or_missing_rule_fields(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="rule fields"):
        load_ren_timing_rules(_write_registry(tmp_path, _rule(extra="    extra: bad\n")))

    missing = _rule().replace("    confidence: 0.72\n", "")
    with pytest.raises(ValueError, match="rule fields"):
        load_ren_timing_rules(_write_registry(tmp_path, missing))


def test_registry_rejects_unknown_relation(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="unsupported relation"):
        load_ren_timing_rules(_write_registry(tmp_path, _rule(relation="破")))


@pytest.mark.parametrize(
    ("rules", "message"),
    [
        (_rule() + _rule(relation="刑", priority="20"), "duplicate rule_id"),
        (_rule() + _rule(rule_id="REN-OTHER", priority="20"), "duplicate relation"),
    ],
)
def test_registry_rejects_duplicate_identity(tmp_path: Path, rules: str, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        load_ren_timing_rules(_write_registry(tmp_path, rules))


@pytest.mark.parametrize("priority", ["0", "-1", "1.5", "true", "null"])
def test_registry_rejects_invalid_priority(tmp_path: Path, priority: str) -> None:
    with pytest.raises(ValueError, match="priority"):
        load_ren_timing_rules(_write_registry(tmp_path, _rule(priority=priority)))


@pytest.mark.parametrize("confidence", ["-0.01", "1.01", "true", "null", "nan"])
def test_registry_rejects_invalid_confidence(tmp_path: Path, confidence: str) -> None:
    with pytest.raises(ValueError, match="confidence"):
        load_ren_timing_rules(_write_registry(tmp_path, _rule(confidence=confidence)))


@pytest.mark.parametrize(
    ("source_path", "source_anchor", "message"),
    [
        ("theory/ren/missing.yaml", _SOURCE_ANCHORS["冲"], "source path"),
        (_SOURCE_PATH, "M4-R-031", "source anchor"),
    ],
)
def test_registry_rejects_unresolvable_source_locator(
    tmp_path: Path, source_path: str, source_anchor: str, message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        load_ren_timing_rules(
            _write_registry(
                tmp_path,
                _rule(source_path=source_path, source_anchor=source_anchor),
            )
        )


def test_registry_sorts_by_priority_then_rule_id(tmp_path: Path) -> None:
    rules = (
        _rule(rule_id="REN-HE", relation="合", priority="20")
        + _rule(rule_id="REN-CHONG", relation="冲", priority="10")
    )
    loaded = load_ren_timing_rules(_write_registry(tmp_path, rules))
    assert [item.rule_id for item in loaded] == ["REN-CHONG", "REN-HE"]

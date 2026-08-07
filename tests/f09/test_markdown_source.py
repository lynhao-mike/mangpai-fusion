import hashlib
from pathlib import Path
from urllib.parse import quote

import pytest

from engine.f09.contracts import DigestRef, MarkdownContractSourceBinding, SourceLocator
from engine.f09.errors import F09SourceError
from engine.f09.markdown_source import (
    _canonical_bytes,
    _resolve_markdown_value,
    resolve_markdown_frozen_field,
)


FROZEN = Path("engine/contracts/12-real-world-function-evidence-cards-v1.md")
DIGEST = "30ea0f8b8a91f95bc0a52ff90188740c2cc2282fcab27cd20be70404253d7a2f"
REF = (
    "mdff:v1/heading/4.9%20F09%20%E8%B5%84%E6%9C%AC%E9%85%8D%E7%BD%AE"
    "%E4%B8%8E%E9%A3%8E%E9%99%A9%E6%89%BF%E6%8B%85/card/F09/item/"
    "%E7%8E%B0%E5%AE%9E%E7%A1%AC%E9%97%A8%E4%B8%8E%E5%8F%8C%E5%8D%A1"
)
EXPECTED = (
    "资源、对象、配置轴、风险轴、归属和时态分别过门；单轴仅限定成立，双轴才是强主。"
    "状态证明基准日持续位置，事件证明指定窗口变化；S1–S3、E1–E3 与动作、资本、责任后果正交。"
)


def _encoded(value: str) -> str:
    return quote(value, safe="-._~", encoding="utf-8", errors="strict")


def _ref(heading: str, card: str = "F09", label: str = "Label") -> str:
    return (
        f"mdff:v1/heading/{_encoded(heading)}/card/{_encoded(card)}/"
        f"item/{_encoded(label)}"
    )


def _digest(value: str = DIGEST) -> DigestRef:
    return DigestRef("sha256", "RAW-UTF8-NO-BOM-LF", value)


def _locator(
    path: Path | str,
    digest: DigestRef | None = None,
    *,
    object_id: object = "F09",
    field_path: object = REF,
    source_type: object = "FROZEN_CONTRACT_FIELD",
    source_id: object = "SRC-F09-REALITY-HARD-GATE",
    binding_changes: dict[str, object] | None = None,
) -> SourceLocator:
    content_digest = digest or _digest()
    binding_values = {
        "binding_kind": "MARKDOWN_CONTRACT",
        "binding_schema_version": "source-binding.markdown.v1",
        "source_snapshot_id": "REAL-WORLD-FUNCTION-EVIDENCE-CARDS-V1-2026-07-19",
        "source_schema_version": "markdown-source.commonmark-0.31.2-mdff-v1",
        "contract_version": "real-world-function-evidence-cards-v1",
        "content_digest": content_digest,
        "captured_at": "2026-07-19T00:00:00Z",
    }
    binding_values.update(binding_changes or {})
    return SourceLocator(
        source_id=source_id,  # type: ignore[arg-type]
        source_type=source_type,  # type: ignore[arg-type]
        path=str(path),
        object_id=object_id,  # type: ignore[arg-type]
        field_path=field_path,  # type: ignore[arg-type]
        binding=MarkdownContractSourceBinding(**binding_values),  # type: ignore[arg-type]
    )


def _resolve(
    tmp_path: Path,
    raw_text: str,
    ref: str,
    *,
    object_id: object = "F09",
):
    path = tmp_path / "parser-fixture.md"
    path.write_text(raw_text, encoding="utf-8", newline="")
    return _resolve_markdown_value(
        _canonical_bytes(str(path)), ref, object_id=object_id
    )


def _assert_source_error(call, issue_code: str) -> None:
    with pytest.raises(F09SourceError) as caught:
        call()
    assert caught.value.issue_code == issue_code


def test_frozen_f09_hard_gate_resolves_exact_copy_and_known_digest() -> None:
    observation = resolve_markdown_frozen_field(
        _locator(FROZEN), REF, expected_digest=_digest()
    )

    assert observation.ref == REF
    assert observation.copied_value == EXPECTED
    assert observation.locator == _locator(FROZEN)
    assert observation.transformation == "MDFF_V1_COPY"


def test_crlf_and_lf_sources_normalize_to_same_lf_digest_and_copy(tmp_path: Path) -> None:
    lf = FROZEN.read_bytes().replace(b"\r\n", b"\n")
    assert b"\r" not in lf
    assert hashlib.sha256(lf).hexdigest() == DIGEST
    crlf_path = tmp_path / "contract-crlf.md"
    lf_path = tmp_path / "contract-lf.md"
    crlf_path.write_bytes(lf.replace(b"\n", b"\r\n"))
    lf_path.write_bytes(lf)

    crlf = resolve_markdown_frozen_field(
        _locator(crlf_path), REF, expected_digest=_digest()
    )
    canonical = resolve_markdown_frozen_field(
        _locator(lf_path), REF, expected_digest=_digest()
    )

    assert crlf.copied_value == canonical.copied_value == EXPECTED


@pytest.mark.parametrize(
    "ref",
    [
        "mdff:v1/heading/F09 heading/card/F09/item/Label",
        "mdff:v1/heading/F09%E4%B8%AD%E6%96%87/card/F09/item/Label中文",
        "mdff:v1/heading/F09%20heading/card/F09/item/%e6%A0%87%E7%AD%BE",
        "mdff:v1/heading/%46%30%39/card/F09/item/Label",
        "mdff:v1/heading/F09%2/card/F09/item/Label",
        "mdff:v1/heading/F09%GG/card/F09/item/Label",
        "mdff:v1/heading/F09%C0%AF/card/F09/item/Label",
        "mdff:v1/heading/F09%ED%A0%80/card/F09/item/Label",
        "mdff:v1/heading/F09/card/F09/item/e%CC%81",
    ],
)
def test_noncanonical_percent_selector_round_trips_fail_closed(
    tmp_path: Path, ref: str
) -> None:
    _assert_source_error(
        lambda: _resolve(tmp_path, "## F09\n- Label：value\n", ref),
        "MARKDOWN.SELECTOR_NONCANONICAL",
    )


@pytest.mark.parametrize(
    "ref",
    [
        "mdff:v1/heading/F09/card/F09/item/Label/extra",
        "mdff:v2/heading/F09/card/F09/item/Label",
        "mdff:v1/head/F09/card/F09/item/Label",
        "mdff:v1/heading//card/F09/item/Label",
    ],
)
def test_invalid_selector_shape_fails_closed(tmp_path: Path, ref: str) -> None:
    _assert_source_error(
        lambda: _resolve(tmp_path, "## F09\n- Label：value\n", ref),
        "MARKDOWN.SELECTOR_NONCANONICAL",
    )


def test_atx_heading_uses_complete_source_text_and_closing_sequence(
    tmp_path: Path,
) -> None:
    heading = "4.9 F09 *资本* & 风险"
    copied = _resolve(
        tmp_path,
        f"   ### {heading} ###   \n- Label：exact\n### F10 Other\n- Label：wrong\n",
        _ref(heading),
    )
    assert copied == "exact"


@pytest.mark.parametrize(
    "raw_text",
    [
        "    ### F09 Target\n- Label：value\n",
        "###F09 Target\n- Label：value\n",
        "####### F09 Target\n- Label：value\n",
    ],
)
def test_non_atx_heading_forms_do_not_match(tmp_path: Path, raw_text: str) -> None:
    _assert_source_error(
        lambda: _resolve(tmp_path, raw_text, _ref("F09 Target")),
        "MARKDOWN.HEADING_UNRESOLVED",
    )


@pytest.mark.parametrize(
    "heading",
    [
        "No card token",
        "F09 and F10",
        "F08 Other",
        "XF09",
        "F09_qualifier",
    ],
)
def test_heading_card_token_must_be_unique_exact_and_ascii_bounded(
    tmp_path: Path, heading: str
) -> None:
    _assert_source_error(
        lambda: _resolve(
            tmp_path, f"## {heading}\n- Label：value\n", _ref(heading)
        ),
        "MARKDOWN.CARD_UNRESOLVED",
    )


def test_object_id_must_be_exact_nonempty_string_equal_to_card(tmp_path: Path) -> None:
    raw = "## F09 Target\n- Label：value\n"
    ref = _ref("F09 Target")
    for object_id, issue_code in [
        (None, "MARKDOWN.LOCATOR_INVALID"),
        ("", "MARKDOWN.LOCATOR_INVALID"),
        (9, "MARKDOWN.LOCATOR_INVALID"),
        ("F08", "MARKDOWN.LOCATOR_INVALID"),
    ]:
        _assert_source_error(
            lambda object_id=object_id: _resolve(
                tmp_path, raw, ref, object_id=object_id
            ),
            issue_code,
        )


def test_target_heading_must_be_unique(tmp_path: Path) -> None:
    raw = (
        "## F09 Target\n- Label：one\n"
        "# Boundary\n"
        "## F09 Target\n- Label：two\n"
    )
    _assert_source_error(
        lambda: _resolve(tmp_path, raw, _ref("F09 Target")),
        "MARKDOWN.HEADING_NONUNIQUE",
    )


def test_card_object_ends_at_next_same_or_higher_heading(tmp_path: Path) -> None:
    raw = (
        "## F09 Target\n"
        "### Detail\n"
        "- Label：inside lower heading\n"
        "## F10 Boundary\n"
        "- Label：outside\n"
    )
    assert _resolve(tmp_path, raw, _ref("F09 Target")) == "inside lower heading"


def test_same_label_in_unrelated_card_object_does_not_interfere(tmp_path: Path) -> None:
    raw = (
        "## F08 Other\n- Label：wrong before\n"
        "## F09 Target\n- Label：target\n"
        "## F10 Other\n- Label：wrong after\n"
    )
    assert _resolve(tmp_path, raw, _ref("F09 Target")) == "target"


def test_duplicate_label_in_target_card_object_fails_closed(tmp_path: Path) -> None:
    raw = "## F09 Target\n- Label：one\n- Label:two\n"
    _assert_source_error(
        lambda: _resolve(tmp_path, raw, _ref("F09 Target")),
        "MARKDOWN.LABEL_NONUNIQUE",
    )


def test_nested_list_label_does_not_participate(tmp_path: Path) -> None:
    raw = (
        "## F09 Target\n"
        "- Parent：outer\n"
        "  - Label：nested wrong\n"
        "- Label：direct value\n"
    )
    assert _resolve(tmp_path, raw, _ref("F09 Target")) == "direct value"


@pytest.mark.parametrize("indent", [" ", "  "])
def test_ordered_item_does_not_capture_less_indented_direct_item(
    tmp_path: Path, indent: str
) -> None:
    raw = f"## F09 Target\n1. parent\n{indent}- Label：direct\n"
    assert _resolve(tmp_path, raw, _ref("F09 Target")) == "direct"


def test_ordered_item_excludes_child_at_its_content_indent(tmp_path: Path) -> None:
    raw = "## F09 Target\n1. parent\n   - Label：nested\n- Other：direct\n"
    _assert_source_error(
        lambda: _resolve(tmp_path, raw, _ref("F09 Target")),
        "MARKDOWN.LABEL_UNRESOLVED",
    )


@pytest.mark.parametrize(
    ("marker", "padding"),
    [
        ("1.", " "),
        ("01.", "  "),
        ("001)", "   "),
        ("0001)", "    "),
        ("00001.", " "),
        ("000001)", "  "),
        ("0000001.", "   "),
        ("00000001)", "    "),
        ("000000001.", "\t"),
    ],
)
def test_numeric_start_one_ordered_item_interrupts_paragraph(
    tmp_path: Path, marker: str, padding: str
) -> None:
    raw = (
        "## F09 Target\nordinary paragraph\n"
        f"{marker}{padding}nonempty item\n<x-card>\n"
        "- Label：blocked\n"
    )
    _assert_source_error(
        lambda: _resolve(tmp_path, raw, _ref("F09 Target")),
        "MARKDOWN.LABEL_UNRESOLVED",
    )


@pytest.mark.parametrize(
    "ordered_line",
    [
        "2. non-one start",
        "2) non-one start",
        "01. ",
        "001)\t",
        "1.     over-four-column padding",
        "1) \t   over-four-column tab padding",
    ],
)
def test_invalid_ordered_paragraph_interruptor_keeps_paragraph_open(
    tmp_path: Path, ordered_line: str
) -> None:
    raw = (
        "## F09 Target\nordinary paragraph\n"
        f"{ordered_line}\n<x-card>\n"
        "- Label：direct\n"
    )
    assert _resolve(tmp_path, raw, _ref("F09 Target")) == "direct"


def test_ordered_item_uses_source_marker_width_and_tab_stop_for_content_indent(
    tmp_path: Path,
) -> None:
    raw = (
        "## F09 Target\n"
        "000000001.\tparent\n"
        "            - Label：nested\n"
        "   - Label：direct\n"
    )
    assert _resolve(tmp_path, raw, _ref("F09 Target")) == "direct"


def test_label_in_later_paragraph_does_not_participate(tmp_path: Path) -> None:
    raw = (
        "## F09 Target\n"
        "- Other：first paragraph\n"
        "\n"
        "  Label：later paragraph\n"
    )
    _assert_source_error(
        lambda: _resolve(tmp_path, raw, _ref("F09 Target")),
        "MARKDOWN.LABEL_UNRESOLVED",
    )


@pytest.mark.parametrize(
    "container",
    [
        "```\n- Label：fenced\n```",
        "~~~\n- Label：tilde fenced\n~~~",
        "<div>\n- Label：html\n\n",
        "<script>\n- Label：html\n</script>",
        "> quote\n> - Label：blockquote",
        "1. parent\n   - Label：ordered child",
        "    - Label：indented code",
        "-     Label：five-column marker padding",
        "- \t  Label：mixed five-column marker padding",
    ],
)
def test_unsupported_block_containers_do_not_supply_direct_items(
    tmp_path: Path, container: str
) -> None:
    raw = f"## F09 Target\n{container}\n- Other：direct\n"
    _assert_source_error(
        lambda: _resolve(tmp_path, raw, _ref("F09 Target")),
        "MARKDOWN.LABEL_UNRESOLVED",
    )


@pytest.mark.parametrize(
    ("padding", "continuation"),
    [
        (" ", "  "),
        ("  ", "   "),
        ("   ", "    "),
        ("    ", "     "),
        ("\t", "\t"),
        (" \t", "\t"),
        ("  \t", " \t"),
        ("\t ", "\t "),
    ],
)
def test_padding_one_through_four_columns_and_tab_stops_are_copied(
    tmp_path: Path, padding: str, continuation: str
) -> None:
    raw = f"## F09 Target\n-{padding}Label：first\n{continuation}second\n"
    assert _resolve(tmp_path, raw, _ref("F09 Target")) == "first second"


@pytest.mark.parametrize("delimiter", [".", ")"])
def test_ten_digit_ascii_ordered_lookalike_remains_in_direct_item_copy(
    tmp_path: Path, delimiter: str
) -> None:
    raw = f"## F09 Target\n- Label：first\n  1234567890{delimiter} kept\n"
    assert _resolve(tmp_path, raw, _ref("F09 Target")) == (
        f"first 1234567890{delimiter} kept"
    )


@pytest.mark.parametrize("marker", ["１.", "١)"])
def test_unicode_digit_ordered_lookalike_remains_in_direct_item_copy(
    tmp_path: Path, marker: str
) -> None:
    raw = f"## F09 Target\n- Label：first\n  {marker} kept\n"
    assert _resolve(tmp_path, raw, _ref("F09 Target")) == f"first {marker} kept"


@pytest.mark.parametrize(
    "marker",
    ["1.", "1)", "123456789.", "123456789)"],
)
def test_valid_ascii_ordered_marker_ends_direct_item_leaf_paragraph_copy(
    tmp_path: Path, marker: str
) -> None:
    raw = f"## F09 Target\n- Label：first\n  {marker} separate block\n"
    assert _resolve(tmp_path, raw, _ref("F09 Target")) == "first"


@pytest.mark.parametrize(
    "html",
    [
        "<script>\n- Label：blocked\n</script> trailing",
        "<pre>\n- Label：blocked\n</pre> trailing",
        "<style>\n- Label：blocked\n</style> trailing",
        "<textarea>\n- Label：blocked\n</textarea> trailing",
        "<!--\n- Label：blocked\n--> trailing",
        "<?target\n- Label：blocked\n?> trailing",
        "<!DOCTYPE\n- Label：blocked\n> trailing",
        "<![CDATA[\n- Label：blocked\n]]> trailing",
    ],
)
def test_explicit_html_terminator_releases_following_direct_item(
    tmp_path: Path, html: str
) -> None:
    raw = f"## F09 Target\n{html}\n- Label：direct\n"
    assert _resolve(tmp_path, raw, _ref("F09 Target")) == "direct"


@pytest.mark.parametrize("opening_tag", ["<hgroup>", "<x-card>"])
def test_blank_line_terminated_html_blocks_exclude_internal_items(
    tmp_path: Path, opening_tag: str
) -> None:
    raw = (
        f"## F09 Target\n{opening_tag}\n"
        "- Label：blocked\n\n"
        "- Label：direct\n"
    )
    assert _resolve(tmp_path, raw, _ref("F09 Target")) == "direct"


def test_type_six_html_can_interrupt_paragraph(tmp_path: Path) -> None:
    raw = (
        "## F09 Target\nordinary paragraph\n<hgroup>\n"
        "- Label：blocked\n\n"
        "- Label：direct\n"
    )
    assert _resolve(tmp_path, raw, _ref("F09 Target")) == "direct"


def test_type_seven_html_cannot_interrupt_paragraph(tmp_path: Path) -> None:
    raw = "## F09 Target\nordinary paragraph\n<x-card>\n- Label：direct\n"
    assert _resolve(tmp_path, raw, _ref("F09 Target")) == "direct"


@pytest.mark.parametrize(
    "paragraph_continuation",
    [
        "2. ordered-looking continuation",
        "    indented continuation",
    ],
)
def test_noninterrupting_paragraph_lines_do_not_enable_type_seven_html(
    tmp_path: Path, paragraph_continuation: str
) -> None:
    raw = (
        "## F09 Target\nordinary paragraph\n"
        f"{paragraph_continuation}\n<x-card>\n"
        "- Label：direct\n"
    )
    assert _resolve(tmp_path, raw, _ref("F09 Target")) == "direct"


@pytest.mark.parametrize("empty_item", ["- ", "+\t", "*    "])
def test_empty_bullet_item_does_not_enable_type_seven_html(
    tmp_path: Path, empty_item: str
) -> None:
    raw = (
        "## F09 Target\nordinary paragraph\n"
        f"{empty_item}\n<x-card>\n"
        "- Label：direct\n"
    )
    assert _resolve(tmp_path, raw, _ref("F09 Target")) == "direct"


@pytest.mark.parametrize("padding", [" ", "  ", "   ", "    ", "\t"])
def test_nonempty_bullet_item_enables_type_seven_html_after_paragraph(
    tmp_path: Path, padding: str
) -> None:
    raw = (
        "## F09 Target\nordinary paragraph\n"
        f"-{padding}Other：nonempty\n<x-card>\n"
        "- Label：blocked\n"
    )
    _assert_source_error(
        lambda: _resolve(tmp_path, raw, _ref("F09 Target")),
        "MARKDOWN.LABEL_UNRESOLVED",
    )


def test_direct_item_leaf_paragraph_ends_before_html_block_opener(
    tmp_path: Path,
) -> None:
    raw = "## F09 Target\n- Label：first\n<x-card>\n- Other：blocked\n"
    assert _resolve(tmp_path, raw, _ref("F09 Target")) == "first"


def test_indented_type_seven_html_remains_in_leaf_paragraph_copy(
    tmp_path: Path,
) -> None:
    raw = "## F09 Target\n- Label：first\n  <x-card>\n"
    assert _resolve(tmp_path, raw, _ref("F09 Target")) == "first <x-card>"


@pytest.mark.parametrize(
    "thematic_break",
    ["***", " ---", "  _ _ _", "   * * *"],
)
def test_thematic_break_ends_paragraph_and_enables_type_seven_html(
    tmp_path: Path, thematic_break: str
) -> None:
    raw = (
        "## F09 Target\nordinary paragraph\n"
        f"{thematic_break}\n<x-card>\n"
        "- Label：blocked\n"
    )
    _assert_source_error(
        lambda: _resolve(tmp_path, raw, _ref("F09 Target")),
        "MARKDOWN.LABEL_UNRESOLVED",
    )


def test_invalid_backtick_info_string_does_not_start_fenced_code(
    tmp_path: Path,
) -> None:
    raw = "## F09 Target\n``` bad`\n- Label：direct\n"
    assert _resolve(tmp_path, raw, _ref("F09 Target")) == "direct"


def test_malformed_type_six_slash_prefix_does_not_start_html_block(
    tmp_path: Path,
) -> None:
    raw = "## F09 Target\n<div/not-a-tag\n- Label：direct\n"
    assert _resolve(tmp_path, raw, _ref("F09 Target")) == "direct"


def test_lazy_continuation_with_ambiguous_source_span_fails_closed(tmp_path: Path) -> None:
    raw = "## F09 Target\n- Label：first\nlazy continuation\n"
    _assert_source_error(
        lambda: _resolve(tmp_path, raw, _ref("F09 Target")),
        "MARKDOWN.SOURCE_SPAN_AMBIGUOUS",
    )


def test_copy_trims_only_ascii_space_and_tab(tmp_path: Path) -> None:
    raw = "## F09 Target\n- Label： \u00a0kept\u3000 \n"
    assert _resolve(tmp_path, raw, _ref("F09 Target")) == "\u00a0kept\u3000"


def test_first_non_code_span_colon_is_the_label_delimiter(tmp_path: Path) -> None:
    raw = "## F09 Target\n- `not:delimiter` Label： value:kept \n"
    assert _resolve(
        tmp_path, raw, _ref("F09 Target", label="`not:delimiter` Label")
    ) == "value:kept"


@pytest.mark.parametrize(
    ("raw_text", "expected"),
    [
        (
            "## F09 Target\n- Label：first\n  second\n",
            "first second",
        ),
        (
            "## F09 Target\n- Label：first  \n  second\n",
            "first  \nsecond",
        ),
        (
            "## F09 Target\n- Label：first\\\n  second\n",
            "first\\\nsecond",
        ),
    ],
)
def test_mdff_copy_soft_and_hard_breaks(
    tmp_path: Path, raw_text: str, expected: str
) -> None:
    assert _resolve(tmp_path, raw_text, _ref("F09 Target")) == expected


def test_blank_line_ends_leaf_paragraph_copy(tmp_path: Path) -> None:
    raw = (
        "## F09 Target\n"
        "- Label：first\n"
        "\n"
        "  later paragraph must not copy\n"
    )
    assert _resolve(tmp_path, raw, _ref("F09 Target")) == "first"


@pytest.mark.parametrize(
    ("raw", "issue_code"),
    [
        (b"\xef\xbb\xbf# H\n", "MARKDOWN.BOM_FORBIDDEN"),
        (b"# H\rbody\n", "MARKDOWN.BARE_CR"),
        (b"# H\n\xff", "MARKDOWN.NONCANONICAL_ENCODING"),
    ],
)
def test_noncanonical_markdown_bytes_fail_closed(
    tmp_path: Path, raw: bytes, issue_code: str
) -> None:
    path = tmp_path / "invalid.md"
    path.write_bytes(raw)
    _assert_source_error(lambda: _canonical_bytes(str(path)), issue_code)


def test_digest_drift_fails_closed(tmp_path: Path) -> None:
    path = tmp_path / "drift.md"
    path.write_bytes(FROZEN.read_bytes() + b"\n")
    _assert_source_error(
        lambda: resolve_markdown_frozen_field(
            _locator(path), REF, expected_digest=_digest()
        ),
        "MARKDOWN.DIGEST_MISMATCH",
    )


def test_formal_markdown_digest_cannot_be_rebound_to_temporary_content(
    tmp_path: Path,
) -> None:
    raw = b"## F09 Target\n- Label:value\n"
    path = tmp_path / "forged.md"
    path.write_bytes(raw)
    forged = _digest(hashlib.sha256(raw).hexdigest())
    ref = _ref("F09 Target")
    _assert_source_error(
        lambda: resolve_markdown_frozen_field(
            _locator(path, forged, field_path=ref), ref, expected_digest=forged
        ),
        "MARKDOWN.IDENTITY_MISMATCH",
    )


def test_wrong_digest_canonicalization_fails_identity() -> None:
    wrong = DigestRef("sha256", "commonmark-0.31.2-mdff-v1", DIGEST)
    _assert_source_error(
        lambda: resolve_markdown_frozen_field(
            _locator(FROZEN, wrong), REF, expected_digest=wrong
        ),
        "MARKDOWN.IDENTITY_MISMATCH",
    )


def test_malformed_expected_digest_fails_as_source_error() -> None:
    _assert_source_error(
        lambda: resolve_markdown_frozen_field(
            _locator(FROZEN), REF, expected_digest=None  # type: ignore[arg-type]
        ),
        "MARKDOWN.IDENTITY_MISMATCH",
    )


@pytest.mark.parametrize("path", [None, 1, ""])
def test_malformed_locator_path_fails_as_source_error(path: object) -> None:
    locator = _locator(FROZEN)
    object.__setattr__(locator, "path", path)
    _assert_source_error(
        lambda: resolve_markdown_frozen_field(locator, REF, expected_digest=_digest()),
        "MARKDOWN.LOCATOR_INVALID",
    )


def test_exact_string_path_with_nul_fails_as_source_error() -> None:
    locator = _locator("invalid\0path.md")
    _assert_source_error(
        lambda: resolve_markdown_frozen_field(locator, REF, expected_digest=_digest()),
        "MARKDOWN.SOURCE_UNAVAILABLE",
    )


@pytest.mark.parametrize(
    ("mutation", "issue_code"),
    [
        (("source_id", "SRC-F09-DRIFT"), "MARKDOWN.LOCATOR_INVALID"),
        (("source_id", None), "MARKDOWN.LOCATOR_INVALID"),
        (("source_type", "FINDING_OBJECT"), "MARKDOWN.LOCATOR_INVALID"),
        (("field_path", "mdff:v1/heading/F09/card/F09/item/Other"), "MARKDOWN.LOCATOR_INVALID"),
        (("field_path", None), "MARKDOWN.LOCATOR_INVALID"),
    ],
)
def test_locator_source_type_and_field_path_are_jointly_bound(
    mutation: tuple[str, object], issue_code: str
) -> None:
    locator = _locator(FROZEN)
    object.__setattr__(locator, mutation[0], mutation[1])
    _assert_source_error(
        lambda: resolve_markdown_frozen_field(locator, REF, expected_digest=_digest()),
        issue_code,
    )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("source_snapshot_id", "drift"),
        ("source_schema_version", "drift"),
        ("contract_version", "drift"),
        ("captured_at", "2026-07-20T00:00:00Z"),
    ],
)
def test_complete_frozen_markdown_binding_identity_is_required(
    field: str, value: object
) -> None:
    locator = _locator(FROZEN)
    object.__setattr__(locator.binding, field, value)
    _assert_source_error(
        lambda: resolve_markdown_frozen_field(locator, REF, expected_digest=_digest()),
        "MARKDOWN.IDENTITY_MISMATCH",
    )


def test_explicit_null_text_is_copied_while_absent_and_unresolved_stay_distinct(
    tmp_path: Path,
) -> None:
    raw = (
        "# Root\n"
        "## F09 Cards\n"
        "- explicit-null：null\n"
        "- unresolved：UNRESOLVED\n"
    )
    assert _resolve(
        tmp_path, raw, _ref("F09 Cards", label="explicit-null")
    ) == "null"
    assert _resolve(
        tmp_path, raw, _ref("F09 Cards", label="unresolved")
    ) == "UNRESOLVED"
    _assert_source_error(
        lambda: _resolve(tmp_path, raw, _ref("F09 Cards", label="absent")),
        "MARKDOWN.LABEL_UNRESOLVED",
    )


@pytest.mark.parametrize(
    ("raw", "ref", "issue_code"),
    [
        (
            "# Root\n## F09 Present\n- Label:value\n",
            _ref("F09 Missing"),
            "MARKDOWN.HEADING_UNRESOLVED",
        ),
        (
            "# Root\n## F08 Present\n- Label:value\n",
            _ref("F08 Present", card="F09"),
            "MARKDOWN.CARD_UNRESOLVED",
        ),
        (
            "# Root\n## F09 Present\n- Other:value\n",
            _ref("F09 Present", label="Label"),
            "MARKDOWN.LABEL_UNRESOLVED",
        ),
    ],
    ids=("missing-heading", "card-drift", "missing-label"),
)
def test_contract_amendment_requires_distinct_selector_failure_codes(
    tmp_path: Path,
    raw: str,
    ref: str,
    issue_code: str,
) -> None:
    _assert_source_error(
        lambda: _resolve(tmp_path, raw, ref),
        issue_code,
    )

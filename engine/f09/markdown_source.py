import hashlib
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from engine.f09.contracts import (
    DigestRef,
    MarkdownContractSourceBinding,
    SourceLocator,
)
from engine.f09.errors import F09SourceError


_SOURCE_SCHEMA_VERSION = "markdown-source.commonmark-0.31.2-mdff-v1"
_DIGEST_CANONICALIZATION = "RAW-UTF8-NO-BOM-LF"
_SOURCE_SNAPSHOT_ID = "REAL-WORLD-FUNCTION-EVIDENCE-CARDS-V1-2026-07-19"
_SOURCE_ID = "SRC-F09-REALITY-HARD-GATE"
_SOURCE_DIGEST = "30ea0f8b8a91f95bc0a52ff90188740c2cc2282fcab27cd20be70404253d7a2f"
_CONTRACT_VERSION = "real-world-function-evidence-cards-v1"
_CAPTURED_AT = "2026-07-19T00:00:00Z"
_CARD_TOKEN = re.compile(r"(?<![A-Za-z0-9_])F(?:0[1-9]|1[0-2])(?![A-Za-z0-9_])")
_ATX = re.compile(r"^( {0,3})(#{1,6})(?:[\t ]+|$)(.*)$")
_DIRECT_ITEM = re.compile(r"^( {0,3})([-+*])([\t ]+)(.*)$")
_ORDERED_ITEM = re.compile(
    r"^( {0,3})(?P<number>[0-9]{1,9})(?P<delimiter>[.)])"
    r"(?:(?P<padding>[\t ]+)(?P<content>.*)|$)"
)
_FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
_THEMATIC_BREAK = re.compile(
    r"^ {0,3}(?:\*(?:[ \t]*\*){2,}|-(?:[ \t]*-){2,}|_(?:[ \t]*_){2,})[ \t]*$"
)
_HTML_BLANK_LINE_BLOCK = re.compile(
    r"^ {0,3}</?(?:address|article|aside|base|basefont|blockquote|body|caption|center|"
    r"col|colgroup|dd|details|dialog|dir|div|dl|dt|fieldset|figcaption|figure|"
    r"footer|form|frame|frameset|h[1-6]|head|header|hgroup|hr|html|iframe|legend|li|link|"
    r"main|menu|menuitem|nav|noframes|ol|optgroup|option|p|param|search|section|"
    r"summary|table|tbody|td|tfoot|th|thead|title|tr|track|ul)(?:[\t >]|/>|$)",
    re.IGNORECASE,
)
_HTML_RAW_TAG = re.compile(
    r"^ {0,3}<(?P<tag>script|pre|style|textarea)(?:[\t >]|$)", re.IGNORECASE
)
_HTML_EXPLICIT_END = (
    (re.compile(r"^ {0,3}<!--"), re.compile(r"-->")),
    (re.compile(r"^ {0,3}<\?"), re.compile(r"\?>")),
    (re.compile(r"^ {0,3}<!\[CDATA\["), re.compile(r"\]\]>")),
    (re.compile(r"^ {0,3}<![A-Z]"), re.compile(r">")),
)
_HTML_COMPLETE_TAG = re.compile(
    r"^ {0,3}(?:"
    r"</[A-Za-z][A-Za-z0-9-]*[\t ]*>|"
    r"<[A-Za-z][A-Za-z0-9-]*"
    r"(?:[\t ]+[A-Za-z_:][A-Za-z0-9_.:-]*"
    r"(?:[\t ]*=[\t ]*(?:[^\t \"'=<>`]+|'[^']*'|\"[^\"]*\"))?)*"
    r"[\t ]*/?>"
    r")[\t ]*$"
)
_UNRESERVED = frozenset(
    b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~"
)


@dataclass(frozen=True)
class FrozenFieldObservation:
    ref: str
    copied_value: object
    locator: SourceLocator
    transformation: Literal["MDFF_V1_COPY", "LOSSLESS_COPY"]


@dataclass(frozen=True)
class _Heading:
    line_index: int
    level: int
    text: str


@dataclass(frozen=True)
class _Item:
    label: str
    copied_value: str


def _reject(issue_code: str, field_path: str) -> None:
    raise F09SourceError(
        issue_code=issue_code,
        field_path=field_path,
        diagnostic="frozen Markdown source resolution rejected",
    )


def _canonical_bytes(path_text: str) -> bytes:
    try:
        path = Path(path_text)
        raw = path.read_bytes()
    except (OSError, ValueError, UnicodeError):
        _reject("MARKDOWN.SOURCE_UNAVAILABLE", path_text)
    if raw.startswith(b"\xef\xbb\xbf"):
        _reject("MARKDOWN.BOM_FORBIDDEN", path_text)
    without_crlf = raw.replace(b"\r\n", b"\n")
    if b"\r" in without_crlf:
        _reject("MARKDOWN.BARE_CR", path_text)
    try:
        text = without_crlf.decode("utf-8", errors="strict")
    except UnicodeError:
        _reject("MARKDOWN.NONCANONICAL_ENCODING", path_text)
    if text.encode("utf-8") != without_crlf:
        _reject("MARKDOWN.NONCANONICAL_ENCODING", path_text)
    return without_crlf


def _percent_encode(value: str) -> str:
    encoded: list[str] = []
    for octet in value.encode("utf-8"):
        if octet in _UNRESERVED:
            encoded.append(chr(octet))
        else:
            encoded.append(f"%{octet:02X}")
    return "".join(encoded)


def _decode_component(component: str) -> str:
    if not component:
        _reject("MARKDOWN.SELECTOR_NONCANONICAL", "/ref")
    octets = bytearray()
    index = 0
    while index < len(component):
        char = component[index]
        if ord(char) > 0x7F:
            _reject("MARKDOWN.SELECTOR_NONCANONICAL", "/ref")
        if char == "%":
            if index + 2 >= len(component):
                _reject("MARKDOWN.SELECTOR_NONCANONICAL", "/ref")
            pair = component[index + 1 : index + 3]
            if any(value not in "0123456789ABCDEF" for value in pair):
                _reject("MARKDOWN.SELECTOR_NONCANONICAL", "/ref")
            octets.append(int(pair, 16))
            index += 3
            continue
        encoded = ord(char)
        if encoded not in _UNRESERVED:
            _reject("MARKDOWN.SELECTOR_NONCANONICAL", "/ref")
        octets.append(encoded)
        index += 1
    try:
        decoded = bytes(octets).decode("utf-8", errors="strict")
    except UnicodeError:
        _reject("MARKDOWN.SELECTOR_NONCANONICAL", "/ref")
    if unicodedata.normalize("NFC", decoded) != decoded:
        _reject("MARKDOWN.SELECTOR_NONCANONICAL", "/ref")
    if _percent_encode(decoded) != component:
        _reject("MARKDOWN.SELECTOR_NONCANONICAL", "/ref")
    return decoded


def _parse_ref(ref: str) -> tuple[str, str, str]:
    if type(ref) is not str:
        _reject("MARKDOWN.SELECTOR_NONCANONICAL", "/ref")
    parts = ref.split("/")
    if (
        len(parts) != 7
        or parts[0] != "mdff:v1"
        or parts[1] != "heading"
        or parts[3] != "card"
        or parts[5] != "item"
    ):
        _reject("MARKDOWN.SELECTOR_NONCANONICAL", "/ref")
    return tuple(_decode_component(parts[index]) for index in (2, 4, 6))  # type: ignore[return-value]


def _atx_heading(line: str, line_index: int) -> _Heading | None:
    match = _ATX.fullmatch(line)
    if match is None:
        return None
    level = len(match.group(2))
    source = match.group(3).strip(" \t")
    closing = re.search(r"[\t ]+#+[\t ]*$", source)
    if closing is not None:
        source = source[: closing.start()].rstrip(" \t")
    return _Heading(line_index=line_index, level=level, text=source)


def _card_token(heading_text: str) -> str | None:
    encoded = heading_text.encode("utf-8")
    matches = tuple(_CARD_TOKEN.finditer(encoded.decode("latin-1")))
    if len(matches) != 1:
        return None
    return matches[0].group(0)


def _code_span_ranges(value: str) -> tuple[tuple[int, int], ...]:
    ranges: list[tuple[int, int]] = []
    cursor = 0
    while cursor < len(value):
        if value[cursor] != "`":
            cursor += 1
            continue
        run_end = cursor + 1
        while run_end < len(value) and value[run_end] == "`":
            run_end += 1
        delimiter = value[cursor:run_end]
        closer = value.find(delimiter, run_end)
        while closer >= 0:
            before_ok = closer == 0 or value[closer - 1] != "`"
            after = closer + len(delimiter)
            after_ok = after == len(value) or value[after] != "`"
            if before_ok and after_ok:
                ranges.append((cursor, after))
                cursor = after
                break
            closer = value.find(delimiter, closer + 1)
        else:
            cursor = run_end
    return tuple(ranges)


def _label_delimiter(first_line: str) -> int | None:
    ranges = _code_span_ranges(first_line)
    for index, char in enumerate(first_line):
        if char not in (":", "："):
            continue
        if not any(start <= index < end for start, end in ranges):
            return index
    return None


def _is_other_block(line: str, *, include_type_seven: bool = True) -> bool:
    if _atx_heading(line, -1) is not None:
        return True
    if (
        _HTML_RAW_TAG.match(line) is not None
        or any(start.match(line) is not None for start, _ in _HTML_EXPLICIT_END)
        or _HTML_BLANK_LINE_BLOCK.match(line) is not None
        or (
            include_type_seven
            and _HTML_COMPLETE_TAG.match(line) is not None
        )
    ):
        return True
    stripped = line.lstrip(" ")
    return (
        stripped.startswith((">", "```", "~~~"))
        or re.match(r"(?:[-+*]|[0-9]{1,9}[.)])(?:[\t ]+|$)", stripped) is not None
    )


def _columns(value: str, start: int = 0) -> int:
    column = start
    for char in value:
        column = column + (4 - column % 4) if char == "\t" else column + 1
    return column - start


def _strip_columns(line: str, width: int) -> str | None:
    column = 0
    index = 0
    while index < len(line) and line[index] in " \t" and column < width:
        char = line[index]
        next_column = column + (4 - column % 4) if char == "\t" else column + 1
        if next_column > width:
            return None
        column = next_column
        index += 1
    return line[index:] if column == width else None


def _blocked_lines(lines: tuple[str, ...]) -> frozenset[int]:
    blocked: set[int] = set()
    fence_char: str | None = None
    fence_length = 0
    html_end: re.Pattern[str] | None = None
    html_until_blank = False
    container_content_indent: int | None = None
    paragraph_open = False
    for index, line in enumerate(lines):
        leading = line[: len(line) - len(line.lstrip(" \t"))]
        leading_columns = _columns(leading)
        if not line.strip(" \t"):
            paragraph_open = False
        if container_content_indent is not None:
            if not line.strip(" \t"):
                blocked.add(index)
                continue
            if leading_columns >= container_content_indent:
                blocked.add(index)
                continue
            container_content_indent = None
        if fence_char is not None:
            paragraph_open = False
            blocked.add(index)
            closing = re.match(rf"^ {{0,3}}{re.escape(fence_char)}{{{fence_length},}}[ \t]*$", line)
            if closing is not None:
                fence_char = None
            continue
        fence = _FENCE.match(line)
        if fence is not None:
            marker = fence.group(1)
            if marker[0] == "`" and "`" in line[fence.end() :]:
                fence = None
            else:
                paragraph_open = False
                fence_char = marker[0]
                fence_length = len(marker)
                blocked.add(index)
                continue
        if html_end is not None:
            paragraph_open = False
            blocked.add(index)
            if html_end.search(line) is not None:
                html_end = None
            continue
        if html_until_blank:
            paragraph_open = False
            blocked.add(index)
            if not line.strip(" \t"):
                html_until_blank = False
            continue
        raw_tag = _HTML_RAW_TAG.match(line)
        if raw_tag is not None:
            paragraph_open = False
            html_end = re.compile(
                rf"</{re.escape(raw_tag.group('tag'))}>", re.IGNORECASE
            )
            blocked.add(index)
            if html_end.search(line) is not None:
                html_end = None
            continue
        explicit_end = next(
            (
                end
                for start, end in _HTML_EXPLICIT_END
                if start.match(line) is not None
            ),
            None,
        )
        if explicit_end is not None:
            paragraph_open = False
            html_end = explicit_end
            blocked.add(index)
            if html_end.search(line) is not None:
                html_end = None
            continue
        if _HTML_BLANK_LINE_BLOCK.match(line) is not None:
            paragraph_open = False
            html_until_blank = True
            blocked.add(index)
            continue
        if _HTML_COMPLETE_TAG.match(line) is not None:
            if paragraph_open:
                continue
            html_until_blank = True
            blocked.add(index)
            continue
        if re.match(r"^ {0,3}>", line) is not None:
            paragraph_open = False
            container_content_indent = leading_columns + 1
            blocked.add(index)
            continue
        if _THEMATIC_BREAK.match(line) is not None:
            paragraph_open = False
            blocked.add(index)
            continue
        direct_item = _DIRECT_ITEM.match(line)
        if direct_item is not None and paragraph_open:
            indent = _columns(direct_item.group(1))
            padding = _columns(direct_item.group(3), indent + 1)
            if not 1 <= padding <= 4 or not direct_item.group(4).strip(" \t"):
                continue
            paragraph_open = False
            continue
        ordered_item = _ORDERED_ITEM.match(line)
        if ordered_item is not None:
            number = ordered_item.group("number")
            padding_text = ordered_item.group("padding") or ""
            content = ordered_item.group("content") or ""
            marker_end = leading_columns + len(number) + 1
            padding = _columns(padding_text, marker_end)
            if paragraph_open and (
                int(number, 10) != 1
                or not 1 <= padding <= 4
                or not content.strip(" \t")
            ):
                continue
            paragraph_open = False
            container_content_indent = marker_end + (
                padding if 1 <= padding <= 4 else 1
            )
            blocked.add(index)
            continue
        if leading_columns >= 4:
            if paragraph_open:
                continue
            blocked.add(index)
            continue
        paragraph_open = (
            bool(line.strip(" \t"))
            and _atx_heading(line, index) is None
            and _DIRECT_ITEM.match(line) is None
        )
    return frozenset(blocked)


def _paragraph_lines(
    lines: tuple[str, ...], item_index: int, content_indent: int, first_line: str
) -> tuple[str, ...]:
    paragraph = [first_line]
    for line in lines[item_index + 1 :]:
        if not line.strip(" \t"):
            break
        continuation = _strip_columns(line, content_indent)
        if continuation is None:
            if not _is_other_block(line):
                _reject("MARKDOWN.SOURCE_SPAN_AMBIGUOUS", "/ref")
            break
        if _is_other_block(continuation, include_type_seven=False):
            break
        paragraph.append(continuation)
    return tuple(paragraph)


def _copy_paragraph(paragraph: tuple[str, ...], delimiter: int) -> str:
    copied_lines = (paragraph[0][delimiter + 1 :], *paragraph[1:])
    copied = copied_lines[0]
    for previous, following in zip(copied_lines, copied_lines[1:]):
        hard_break = previous.endswith("\\") or len(previous) - len(
            previous.rstrip(" ")
        ) >= 2
        copied += ("\n" if hard_break else " ") + following
    try:
        canonical = copied.strip(" \t").encode("utf-8").decode("utf-8", errors="strict")
    except UnicodeError:
        _reject("MARKDOWN.NONCANONICAL_ENCODING", "/ref")
    return canonical


def _direct_items(lines: tuple[str, ...]) -> tuple[_Item, ...]:
    items: list[_Item] = []
    direct_indent: int | None = None
    nested_until_dedent: int | None = None
    blocked = _blocked_lines(lines)
    for index, line in enumerate(lines):
        if not line.strip(" \t"):
            nested_until_dedent = None
            continue
        if index in blocked:
            continue
        match = _DIRECT_ITEM.fullmatch(line)
        if match is None:
            continue
        indent = _columns(match.group(1))
        if nested_until_dedent is not None:
            if indent > nested_until_dedent:
                continue
            nested_until_dedent = None
        if direct_indent is None:
            direct_indent = indent
        elif indent > direct_indent:
            nested_until_dedent = direct_indent
            continue
        elif indent < direct_indent:
            direct_indent = indent
        whitespace = match.group(3)
        width = _columns(whitespace, indent + 1)
        if not 1 <= width <= 4:
            continue
        padding = width
        first_line = match.group(4)
        delimiter = _label_delimiter(first_line)
        if delimiter is None:
            continue
        label = first_line[:delimiter].strip(" \t")
        if unicodedata.normalize("NFC", label) != label:
            continue
        content_indent = indent + 1 + padding
        paragraph = _paragraph_lines(lines, index, content_indent, first_line)
        items.append(
            _Item(label=label, copied_value=_copy_paragraph(paragraph, delimiter))
        )
    return tuple(items)


def _resolve_item(
    lines: tuple[str, ...], heading_text: str, card: str, label: str
) -> str:
    blocked = _blocked_lines(lines)
    headings = tuple(
        heading
        for index, line in enumerate(lines)
        if index not in blocked and (heading := _atx_heading(line, index)) is not None
    )
    targets = tuple(heading for heading in headings if heading.text == heading_text)
    if len(targets) > 1:
        _reject("MARKDOWN.HEADING_NONUNIQUE", "/ref")
    if len(targets) != 1:
        _reject("MARKDOWN.HEADING_UNRESOLVED", "/ref")
    target = targets[0]
    token = _card_token(target.text)
    if token is None or token != card:
        _reject("MARKDOWN.CARD_UNRESOLVED", "/ref")
    end = next(
        (
            heading.line_index
            for heading in headings
            if heading.line_index > target.line_index and heading.level <= target.level
        ),
        len(lines),
    )
    matching = tuple(
        item
        for item in _direct_items(lines[target.line_index + 1 : end])
        if unicodedata.normalize("NFC", item.label) == label
    )
    if len(matching) > 1:
        _reject("MARKDOWN.LABEL_NONUNIQUE", "/ref")
    if len(matching) != 1:
        _reject("MARKDOWN.LABEL_UNRESOLVED", "/ref")
    return matching[0].copied_value


def _resolve_markdown_value(
    canonical: bytes, ref: str, *, object_id: object
) -> str:
    heading, card, label = _parse_ref(ref)
    if type(object_id) is not str or object_id != card:
        _reject("MARKDOWN.LOCATOR_INVALID", "/locator/object_id")
    try:
        lines = tuple(canonical.decode("utf-8", errors="strict").split("\n"))
    except UnicodeError:
        _reject("MARKDOWN.NONCANONICAL_ENCODING", "/ref")
    return _resolve_item(lines, heading, card, label)


def resolve_markdown_frozen_field(
    locator: SourceLocator,
    ref: str,
    *,
    expected_digest: DigestRef,
) -> FrozenFieldObservation:
    if not isinstance(locator, SourceLocator):
        _reject("MARKDOWN.LOCATOR_INVALID", "/locator")
    if type(locator.path) is not str or not locator.path:
        _reject("MARKDOWN.LOCATOR_INVALID", "/locator/path")
    if type(locator.source_id) is not str or locator.source_id != _SOURCE_ID:
        _reject("MARKDOWN.LOCATOR_INVALID", "/locator/source_id")
    if locator.source_type != "FROZEN_CONTRACT_FIELD":
        _reject("MARKDOWN.LOCATOR_INVALID", "/locator/source_type")
    if type(locator.object_id) is not str or not locator.object_id:
        _reject("MARKDOWN.LOCATOR_INVALID", "/locator/object_id")
    if type(locator.field_path) is not str or locator.field_path != ref:
        _reject("MARKDOWN.LOCATOR_INVALID", "/locator/field_path")
    if not isinstance(locator.binding, MarkdownContractSourceBinding):
        _reject("MARKDOWN.BINDING_INVALID", "/locator/binding")
    if type(expected_digest) is not DigestRef:
        _reject("MARKDOWN.IDENTITY_MISMATCH", "/expected_digest")
    binding = locator.binding
    if (
        binding.binding_kind != "MARKDOWN_CONTRACT"
        or binding.binding_schema_version != "source-binding.markdown.v1"
        or binding.source_snapshot_id != _SOURCE_SNAPSHOT_ID
        or binding.source_schema_version != _SOURCE_SCHEMA_VERSION
        or binding.contract_version != _CONTRACT_VERSION
        or binding.captured_at != _CAPTURED_AT
        or expected_digest.algorithm != "sha256"
        or expected_digest.canonicalization != _DIGEST_CANONICALIZATION
        or expected_digest.value != _SOURCE_DIGEST
        or binding.content_digest != expected_digest
    ):
        _reject("MARKDOWN.IDENTITY_MISMATCH", "/locator/binding")

    canonical = _canonical_bytes(locator.path)
    actual = hashlib.sha256(canonical).hexdigest()
    if actual != _SOURCE_DIGEST:
        _reject("MARKDOWN.DIGEST_MISMATCH", locator.path)

    copied_value = _resolve_markdown_value(
        canonical, ref, object_id=locator.object_id
    )
    return FrozenFieldObservation(
        ref=ref,
        copied_value=copied_value,
        locator=locator,
        transformation="MDFF_V1_COPY",
    )


"""Structural inspection of PDF incremental revision chains.

This module performs bounded, read-only checks. It does not establish
document authenticity or cryptographic signature validity.
"""

from __future__ import annotations

import re
import zlib
from typing import Any

_STARTXREF = re.compile(rb"startxref\s+(\d+)\s+%%EOF\s*$")
_PREV = re.compile(rb"/Prev\s+(\d+)\b")
_XREF = re.compile(rb"xref(?:\s|$)")
_INDIRECT_OBJECT = re.compile(rb"(\d+)\s+(\d+)\s+obj\b")


class PDFRevisionError(ValueError):
    """Raised when a PDF revision structure is demonstrably malformed."""


def find_startxref(data: bytes) -> int:
    """Find the terminal startxref pointer."""
    match = _STARTXREF.search(data.rstrip())
    if not match:
        raise PDFRevisionError("Terminal startxref/EOF sequence not found.")

    offset = int(match.group(1))
    if offset < 0 or offset >= len(data):
        raise PDFRevisionError("Terminal startxref offset is outside the file.")

    return offset


def _read_integer(data: bytes, position: int) -> tuple[int, int]:
    match = re.match(rb"\s*(\d+)", data[position:])
    if not match:
        raise PDFRevisionError("Expected integer in cross-reference structure.")

    return int(match.group(1)), position + match.end()


def _parse_xref_table(data: bytes, offset: int) -> dict[str, Any]:
    """Parse traditional xref subsections and their entry syntax."""
    position = offset + 4
    entries = 0

    while True:
        while position < len(data) and data[position] in b" \t\r\n":
            position += 1

        if data[position:position + 7] == b"trailer":
            break

        first_object, position = _read_integer(data, position)
        count, position = _read_integer(data, position)

        if count > 1_000_000:
            raise PDFRevisionError("Unreasonable xref subsection size.")

        # Skip whitespace after the subsection header.
        while position < len(data) and data[position] in b" \t\r\n":
            position += 1

        for _ in range(count):
            line_end = data.find(b"\n", position)
            if line_end < 0:
                raise PDFRevisionError("Truncated xref table entry.")

            line = data[position:line_end].strip(b" \r")
            if not re.fullmatch(rb"\d{10}\s+\d{5}\s+[nf]", line):
                raise PDFRevisionError("Malformed xref table entry.")

            position = line_end + 1
            entries += 1

        if first_object < 0:
            raise PDFRevisionError("Invalid xref object number.")

    trailer_start = position + len(b"trailer")
    trailer_end = data.find(b"startxref", trailer_start)
    if trailer_end < 0:
        raise PDFRevisionError("Trailer is not followed by startxref.")

    trailer = data[trailer_start:trailer_end]
    prev_match = _PREV.search(trailer)

    return {
        "type": "TABLE",
        "offset": offset,
        "entry_count": entries,
        "previous_xref": int(prev_match.group(1)) if prev_match else None,
    }


def _parse_xref_stream(data: bytes, offset: int) -> dict[str, Any]:
    """Inspect a FlateDecode xref stream with bounded decompression."""
    match = _INDIRECT_OBJECT.match(data[offset:])
    if not match:
        raise PDFRevisionError("Xref stream offset does not point to an indirect object.")

    dictionary_start = data.find(b"<<", offset)
    dictionary_end = data.find(b">>", dictionary_start + 2)
    if dictionary_start < 0 or dictionary_end < 0:
        raise PDFRevisionError("Malformed xref stream dictionary.")

    dictionary = data[dictionary_start:dictionary_end + 2]

    if not re.search(rb"/Type\s*/XRef\b", dictionary):
        raise PDFRevisionError("Indirect object is not an xref stream.")

    prev_match = _PREV.search(dictionary)
    filter_match = re.search(rb"/Filter\s*/([A-Za-z0-9]+)", dictionary)

    if filter_match and filter_match.group(1) != b"FlateDecode":
        return {
            "type": "STREAM",
            "offset": offset,
            "previous_xref": int(prev_match.group(1)) if prev_match else None,
            "status": "UNSUPPORTED_FILTER",
        }

    if re.search(rb"/Filter\s*\[", dictionary):
        return {
            "type": "STREAM",
            "offset": offset,
            "previous_xref": int(prev_match.group(1)) if prev_match else None,
            "status": "UNSUPPORTED_FILTER",
        }

    width_match = re.search(rb"/W\s*\[\s*(\d+)\s+(\d+)\s+(\d+)\s*\]", dictionary)
    if not width_match:
        raise PDFRevisionError("Unsupported or malformed xref stream /W array.")

    widths = [int(width_match.group(i)) for i in range(1, 4)]
    if sum(widths) == 0 or sum(widths) > 16:
        raise PDFRevisionError("Invalid xref stream field widths.")

    stream_marker = data.find(b"stream", dictionary_end)
    if stream_marker < 0:
        raise PDFRevisionError("Xref stream has no stream body.")

    body_start = stream_marker + len(b"stream")
    if data[body_start:body_start + 2] == b"\r\n":
        body_start += 2
    elif data[body_start:body_start + 1] in (b"\r", b"\n"):
        body_start += 1
    else:
        raise PDFRevisionError("Invalid stream line ending.")

    length_match = re.search(rb"/Length\s+(\d+)\b", dictionary)
    if not length_match:
        return {
            "type": "STREAM",
            "offset": offset,
            "previous_xref": int(prev_match.group(1)) if prev_match else None,
            "status": "INDETERMINATE_LENGTH",
        }

    length = int(length_match.group(1))
    body_end = body_start + length

    if body_end > len(data):
        raise PDFRevisionError("Xref stream exceeds file boundaries.")

    encoded = data[body_start:body_end]

    try:
        decoded = zlib.decompress(encoded) if filter_match else encoded
    except zlib.error as exc:
        raise PDFRevisionError("Invalid FlateDecode xref stream.") from exc

    if len(decoded) > 16 * 1024 * 1024:
        raise PDFRevisionError("Decoded xref stream exceeds size limit.")

    index_match = re.search(rb"/Index\s*\[([^\]]+)\]", dictionary)
    size_match = re.search(rb"/Size\s+(\d+)\b", dictionary)

    if index_match:
        values = [int(value) for value in re.findall(rb"\d+", index_match.group(1))]
        if len(values) % 2:
            raise PDFRevisionError("Invalid xref stream /Index array.")
        entry_count = sum(values[i + 1] for i in range(0, len(values), 2))
    elif size_match:
        entry_count = int(size_match.group(1))
    else:
        raise PDFRevisionError("Xref stream has neither /Index nor /Size.")

    row_width = sum(widths)
    if entry_count * row_width != len(decoded):
        raise PDFRevisionError("Xref stream data length does not match /W and /Index.")

    return {
        "type": "STREAM",
        "offset": offset,
        "entry_count": entry_count,
        "previous_xref": int(prev_match.group(1)) if prev_match else None,
        "status": "PARSED",
    }


def parse_xref(data: bytes, offset: int) -> dict[str, Any]:
    """Dispatch parsing based on the object at the supplied offset."""
    if offset < 0 or offset >= len(data):
        raise PDFRevisionError("Xref offset is outside the file.")

    if _XREF.match(data[offset:]):
        return _parse_xref_table(data, offset)

    return _parse_xref_stream(data, offset)


def inspect_revision_chain(data: bytes) -> dict[str, Any]:
    """Inspect the terminal xref and follow its /Prev chain."""
    current = find_startxref(data)
    visited: set[int] = set()
    revisions: list[dict[str, Any]] = []
    status = "VALIDATED"

    while current is not None:
        if current in visited:
            raise PDFRevisionError("Cycle detected in /Prev revision chain.")

        if len(visited) >= 100:
            return {
                "status": "INDETERMINATE",
                "revisions": revisions,
                "warnings": ["Revision chain exceeds the 100-revision safety limit."],
            }

        visited.add(current)
        revision = parse_xref(data, current)
        revisions.append(revision)

        if revision.get("status") != "PARSED":
            status = "INDETERMINATE"

        current = revision["previous_xref"]

    return {
        "status": status,
        "revision_count": len(revisions),
        "revisions": revisions,
        "warnings": [
            "Structural checks do not establish authenticity or signature validity.",
            "Object references and complete PDF semantic consistency are not yet validated.",
        ],
    }

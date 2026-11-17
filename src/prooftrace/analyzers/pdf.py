"""Read-only PDF inspection and version comparison.

This module reports observable PDF artefacts. It does not validate digital signatures
or claim that a PDF's metadata timestamps are trustworthy.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

from pypdf import PdfReader

_EOF = re.compile(rb"%%EOF")
_STARTXREF = re.compile(rb"startxref\s+(\d+)")


def _revision_markers(data: bytes) -> list[dict[str, int]]:
    """Return lexical EOF/startxref markers; these are indicators, not proof of revisions."""
    eof_positions = [match.start() for match in _EOF.finditer(data)]
    xref_positions = [int(match.group(1)) for match in _STARTXREF.finditer(data)]
    markers = []
    for index, eof in enumerate(eof_positions):
        markers.append({
            "index": index + 1,
            "eof_offset": eof,
            "startxref_offset": xref_positions[index] if index < len(xref_positions) else -1,
        })
    return markers


def inspect_pdf(path: str | Path) -> dict[str, Any]:
    """Inspect basic PDF structure, metadata, text and signature-field presence."""
    file_path = Path(path)
    if not file_path.is_file():
        raise FileNotFoundError(file_path)

    raw = file_path.read_bytes()
    if not raw.startswith(b"%PDF-"):
        raise ValueError("Input does not begin with a PDF header.")

    reader = PdfReader(str(file_path), strict=False)
    if reader.is_encrypted:
        raise ValueError("Encrypted PDFs are not yet supported by this analyzer.")

    metadata = {}
    if reader.metadata:
        metadata = {str(key): str(value) for key, value in reader.metadata.items()}

    page_text = []
    for number, page in enumerate(reader.pages, start=1):
        try:
            page_text.append({"page": number, "text": page.extract_text() or ""})
        except Exception as exc:  # parser failures are recorded per page
            page_text.append({"page": number, "text": None, "error": str(exc)})

    fields = reader.get_fields() or {}
    signature_fields = [
        str(name) for name, field in fields.items()
        if str(field.get("/FT", "")) == "/Sig"
    ]

    revisions = _revision_markers(raw)
    return {
        "file": file_path.name,
        "size_bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "pdf_version": raw[5:8].decode("ascii", errors="replace"),
        "page_count": len(reader.pages),
        "metadata": metadata,
        "signature_fields": signature_fields,
        "signature_validation": "NOT_PERFORMED",
        "revision_markers": revisions,
        "revision_marker_count": len(revisions),
        "text_pages": page_text,
        "limitations": [
            "EOF markers are lexical indicators and do not by themselves prove valid incremental revisions.",
            "Digital signatures are detected by field presence only; cryptographic validation is not performed.",
            "PDF metadata timestamps are self-reported file data and are not trusted timestamps.",
            "Text extraction may omit scanned content, annotations, forms or visual layout information.",
        ],
    }


def compare_pdf_versions(first: str | Path, second: str | Path) -> dict[str, Any]:
    """Compare two PDFs by exact bytes, extracted page text and selected metadata."""
    left = inspect_pdf(first)
    right = inspect_pdf(second)

    left_text = [page.get("text") for page in left["text_pages"]]
    right_text = [page.get("text") for page in right["text_pages"]]
    max_pages = max(len(left_text), len(right_text))
    page_changes = []
    for index in range(max_pages):
        old = left_text[index] if index < len(left_text) else None
        new = right_text[index] if index < len(right_text) else None
        if old != new:
            page_changes.append({"page": index + 1, "before": old, "after": new})

    metadata_keys = sorted(set(left["metadata"]) | set(right["metadata"]))
    metadata_changes = {
        key: {"before": left["metadata"].get(key), "after": right["metadata"].get(key)}
        for key in metadata_keys
        if left["metadata"].get(key) != right["metadata"].get(key)
    }

    return {
        "same_bytes": left["sha256"] == right["sha256"],
        "before": {"file": left["file"], "sha256": left["sha256"], "size_bytes": left["size_bytes"]},
        "after": {"file": right["file"], "sha256": right["sha256"], "size_bytes": right["size_bytes"]},
        "page_count_changed": left["page_count"] != right["page_count"],
        "page_text_changes": page_changes,
        "metadata_changes": metadata_changes,
        "limitations": [
            "Text comparison does not detect every visual, structural or hidden-object change.",
            "Different hashes prove byte-level difference, not malicious or intentional alteration.",
            "This comparison does not establish which version is authentic without trusted provenance.",
        ],
    }
